"""
軌道預測服務實作 - 使用物理模型和統計方法進行預測
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.domain.entities.observer import Observer
from src.domain.entities.prediction import OptimalWindow, Prediction, PredictionPoint, PredictionTimeScale
from src.domain.entities.satellite import Satellite
from src.domain.services.orbit_calculator import OrbitCalculator
from src.domain.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)


class OrbitPredictionService(PredictionService):
    """基於軌道計算的預測服務實作"""

    # 預測配置
    PREDICTION_CONFIGS = {
        PredictionTimeScale.SHORT_TERM: {"hours": 1, "interval_minutes": 5},
        PredictionTimeScale.MEDIUM_TERM: {"hours": 24, "interval_minutes": 30},
        PredictionTimeScale.LONG_TERM: {"hours": 168, "interval_minutes": 60},  # 7天
    }

    def __init__(self, orbit_calculator: OrbitCalculator):
        """初始化預測服務

        Args:
            orbit_calculator: 軌道計算器
        """
        self.orbit_calculator = orbit_calculator
        self.model_weights = {"physics": 0.7, "statistical": 0.3}  # 物理模型權重  # 統計模型權重

    def predict_coverage(
        self,
        satellites: List[Satellite],
        observer: Observer,
        time_scale: PredictionTimeScale,
        start_time: Optional[datetime] = None,
    ) -> Prediction:
        """預測衛星覆蓋"""
        if start_time is None:
            start_time = datetime.now()

        config = self.PREDICTION_CONFIGS[time_scale]

        # 計算預測時間範圍
        end_time = start_time + timedelta(hours=config["hours"])

        # 創建預測實體
        prediction = Prediction(
            prediction_id=str(uuid.uuid4()),
            observer_name=observer.name,
            time_scale=time_scale,
            created_at=datetime.now(),
            start_time=start_time,
            end_time=end_time,
        )

        # 生成預測時間點
        current_time = start_time
        while current_time <= end_time:
            prediction_point = self._predict_at_time(satellites, observer, current_time, start_time)
            prediction.add_prediction_point(prediction_point)
            current_time += timedelta(minutes=config["interval_minutes"])

        # 計算統計資訊
        prediction.calculate_statistics()

        # 找出最佳觀測窗口
        optimal_windows = self.find_optimal_windows(prediction)
        for window in optimal_windows:
            prediction.add_optimal_window(window)

        return prediction

    def _predict_at_time(
        self, satellites: List[Satellite], observer: Observer, prediction_time: datetime, base_time: datetime
    ) -> PredictionPoint:
        """預測特定時間點的覆蓋情況"""
        visible_satellites = []
        max_elevation = 0.0

        # 使用軌道計算器預測每顆衛星的位置和可見性
        for satellite in satellites:
            try:
                # 檢查是否可見
                is_visible, elevation = self.orbit_calculator.calculate_visibility(
                    satellite, observer.position, prediction_time, observer.min_elevation
                )

                if is_visible:
                    visible_satellites.append(satellite)
                    max_elevation = max(max_elevation, elevation)

            except Exception as e:
                logger.warning(f"無法預測衛星 {satellite.name}: {e}")
                continue

        # 計算不確定性
        uncertainty = self.calculate_prediction_uncertainty(prediction_time, base_time)

        # 計算覆蓋概率（基於可見衛星數量）
        coverage_probability = min(100, len(visible_satellites) * 2.5)

        # 應用不確定性到預測結果
        predicted_count = len(visible_satellites)
        confidence_interval = {
            "lower": max(0, predicted_count - int(uncertainty["satellites"])),
            "upper": predicted_count + int(uncertainty["satellites"]),
        }

        return PredictionPoint(
            timestamp=prediction_time,
            predicted_satellites=predicted_count,
            predicted_elevation=max_elevation,
            coverage_probability=coverage_probability,
            uncertainty=uncertainty,
            confidence_interval=confidence_interval,
        )

    def find_optimal_windows(
        self, prediction: Prediction, min_satellites: int = 30, min_duration_minutes: int = 30
    ) -> List[OptimalWindow]:
        """找出最佳觀測窗口"""
        optimal_windows = []
        current_window = None

        for point in prediction.prediction_points:
            if point.predicted_satellites >= min_satellites:
                if current_window is None:
                    # 開始新窗口
                    current_window = {
                        "start": point.timestamp,
                        "end": point.timestamp,
                        "satellites": [point.predicted_satellites],
                        "elevations": [point.predicted_elevation],
                    }
                else:
                    # 延續當前窗口
                    current_window["end"] = point.timestamp
                    current_window["satellites"].append(point.predicted_satellites)
                    current_window["elevations"].append(point.predicted_elevation)
            else:
                # 結束當前窗口
                if current_window:
                    duration = (current_window["end"] - current_window["start"]).total_seconds() / 60
                    if duration >= min_duration_minutes:
                        window = OptimalWindow(
                            start_time=current_window["start"],
                            end_time=current_window["end"],
                            avg_satellites=sum(current_window["satellites"]) / len(current_window["satellites"]),
                            max_elevation=max(current_window["elevations"]),
                            duration_minutes=int(duration),
                        )
                        optimal_windows.append(window)
                    current_window = None

        # 處理最後一個窗口
        if current_window:
            duration = (current_window["end"] - current_window["start"]).total_seconds() / 60
            if duration >= min_duration_minutes:
                window = OptimalWindow(
                    start_time=current_window["start"],
                    end_time=current_window["end"],
                    avg_satellites=sum(current_window["satellites"]) / len(current_window["satellites"]),
                    max_elevation=max(current_window["elevations"]),
                    duration_minutes=int(duration),
                )
                optimal_windows.append(window)

        # 按平均衛星數排序
        optimal_windows.sort(key=lambda w: w.avg_satellites, reverse=True)

        return optimal_windows

    def calculate_prediction_uncertainty(self, prediction_time: datetime, base_time: datetime) -> Dict[str, float]:
        """計算預測不確定性

        不確定性隨預測時間增加而增大
        """
        hours_ahead = (prediction_time - base_time).total_seconds() / 3600

        # 基礎不確定性
        base_uncertainty = {"satellites": 2.0, "elevation": 2.5, "coverage": 5.0}

        # 時間因子（最多5倍不確定性）
        time_factor = min(hours_ahead / 24.0, 5.0)

        # 計算最終不確定性
        uncertainty = {
            "satellites": base_uncertainty["satellites"] * (1 + time_factor),
            "elevation": base_uncertainty["elevation"] * (1 + time_factor * 0.5),
            "coverage": base_uncertainty["coverage"] * (1 + time_factor * 0.3),
        }

        return uncertainty
