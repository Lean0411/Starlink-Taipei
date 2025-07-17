"""
預測實體 - 表示衛星覆蓋預測結果
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class PredictionTimeScale(Enum):
    """預測時間尺度"""

    SHORT_TERM = "short_term"  # 1小時
    MEDIUM_TERM = "medium_term"  # 24小時
    LONG_TERM = "long_term"  # 7天


@dataclass
class PredictionPoint:
    """單個預測時間點"""

    timestamp: datetime
    predicted_satellites: int
    predicted_elevation: float
    coverage_probability: float
    uncertainty: Dict[str, float]
    confidence_interval: Dict[str, float]

    @property
    def is_high_coverage(self) -> bool:
        """是否為高覆蓋率時段"""
        return self.coverage_probability >= 80.0

    @property
    def reliability_score(self) -> float:
        """可靠性分數（基於不確定性）"""
        avg_uncertainty = sum(self.uncertainty.values()) / len(self.uncertainty)
        return max(0, 100 - avg_uncertainty * 10)


@dataclass
class OptimalWindow:
    """最佳觀測窗口"""

    start_time: datetime
    end_time: datetime
    avg_satellites: float
    max_elevation: float
    duration_minutes: int

    @property
    def is_extended_window(self) -> bool:
        """是否為延長窗口（超過1小時）"""
        return self.duration_minutes >= 60

    def overlaps_with(self, other: "OptimalWindow") -> bool:
        """檢查是否與另一個窗口重疊"""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)


@dataclass
class Prediction:
    """預測結果實體

    Attributes:
        prediction_id: 預測唯一識別碼
        observer_name: 觀測者名稱
        time_scale: 預測時間尺度
        created_at: 預測創建時間
        start_time: 預測開始時間
        end_time: 預測結束時間
        prediction_points: 預測時間點列表
        optimal_windows: 最佳觀測窗口列表
        statistics: 統計資訊
        metadata: 額外元資料
    """

    prediction_id: str
    observer_name: str
    time_scale: PredictionTimeScale
    created_at: datetime
    start_time: datetime
    end_time: datetime
    prediction_points: List[PredictionPoint] = field(default_factory=list)
    optimal_windows: List[OptimalWindow] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_hours(self) -> float:
        """預測時長（小時）"""
        return (self.end_time - self.start_time).total_seconds() / 3600

    @property
    def average_satellites(self) -> float:
        """平均預測衛星數"""
        if not self.prediction_points:
            return 0.0
        return sum(p.predicted_satellites for p in self.prediction_points) / len(self.prediction_points)

    @property
    def coverage_availability(self) -> float:
        """覆蓋可用性百分比"""
        if not self.prediction_points:
            return 0.0
        high_coverage_count = sum(1 for p in self.prediction_points if p.is_high_coverage)
        return (high_coverage_count / len(self.prediction_points)) * 100

    def get_peak_hours(self) -> List[int]:
        """獲取峰值小時"""
        hourly_data = {}
        for point in self.prediction_points:
            hour = point.timestamp.hour
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(point.predicted_satellites)

        # 計算每小時平均值
        hourly_avg = {hour: sum(sats) / len(sats) for hour, sats in hourly_data.items()}

        # 返回前3個最高的小時
        sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:3]]

    def add_prediction_point(self, point: PredictionPoint) -> None:
        """添加預測點"""
        self.prediction_points.append(point)

    def add_optimal_window(self, window: OptimalWindow) -> None:
        """添加最佳觀測窗口"""
        self.optimal_windows.append(window)

    def calculate_statistics(self) -> Dict[str, Any]:
        """計算並更新統計資訊"""
        if not self.prediction_points:
            return {}

        satellites = [p.predicted_satellites for p in self.prediction_points]
        elevations = [p.predicted_elevation for p in self.prediction_points]
        coverages = [p.coverage_probability for p in self.prediction_points]

        self.statistics = {
            "satellites": {
                "mean": sum(satellites) / len(satellites),
                "max": max(satellites),
                "min": min(satellites),
                "std": self._calculate_std(satellites),
            },
            "elevation": {"mean": sum(elevations) / len(elevations), "max": max(elevations), "min": min(elevations)},
            "coverage": {"mean": sum(coverages) / len(coverages), "availability_percentage": self.coverage_availability},
            "optimal_windows_count": len(self.optimal_windows),
            "peak_hours": self.get_peak_hours(),
        }

        return self.statistics

    def _calculate_std(self, values: List[float]) -> float:
        """計算標準差"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance**0.5
