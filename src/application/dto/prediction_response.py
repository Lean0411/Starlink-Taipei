"""
預測響應 DTO
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any

from ...domain.entities.prediction import Prediction, PredictionTimeScale


@dataclass
class PredictionPointDTO:
    """預測點 DTO"""
    timestamp: str
    predicted_satellites: int
    predicted_elevation: float
    coverage_probability: float
    uncertainty: Dict[str, float]
    confidence_interval: Dict[str, float]


@dataclass
class OptimalWindowDTO:
    """最佳觀測窗口 DTO"""
    start_time: str
    end_time: str
    avg_satellites: float
    max_elevation: float
    duration_minutes: int


@dataclass
class PredictionStatisticsDTO:
    """預測統計 DTO"""
    satellites: Dict[str, float]
    elevation: Dict[str, float]
    coverage: Dict[str, float]
    optimal_windows_count: int
    peak_hours: List[int]


@dataclass
class PredictionResponse:
    """預測響應
    
    Attributes:
        prediction_id: 預測ID
        time_scale: 預測時間尺度
        created_at: 創建時間
        observer_location: 觀測者位置
        start_time: 預測開始時間
        end_time: 預測結束時間
        total_satellites: 總衛星數
        analyzed_satellites: 分析的衛星數
        prediction_points: 預測點列表
        optimal_windows: 最佳觀測窗口列表
        statistics: 統計資訊
        metadata: 元資料
    """
    
    prediction_id: str
    time_scale: str
    created_at: str
    observer_location: Dict[str, float]
    start_time: str
    end_time: str
    total_satellites: int
    analyzed_satellites: int
    prediction_points: List[PredictionPointDTO] = field(default_factory=list)
    optimal_windows: List[OptimalWindowDTO] = field(default_factory=list)
    statistics: PredictionStatisticsDTO = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_domain(
        cls,
        prediction: Prediction,
        total_satellites: int,
        analyzed_satellites: int
    ) -> "PredictionResponse":
        """從領域實體創建響應 DTO
        
        Args:
            prediction: 預測實體
            total_satellites: 總衛星數
            analyzed_satellites: 分析的衛星數
            
        Returns:
            PredictionResponse: 響應 DTO
        """
        # 轉換預測點
        prediction_points = [
            PredictionPointDTO(
                timestamp=point.timestamp.isoformat(),
                predicted_satellites=point.predicted_satellites,
                predicted_elevation=point.predicted_elevation,
                coverage_probability=point.coverage_probability,
                uncertainty=point.uncertainty,
                confidence_interval=point.confidence_interval
            )
            for point in prediction.prediction_points
        ]
        
        # 轉換最佳窗口
        optimal_windows = [
            OptimalWindowDTO(
                start_time=window.start_time.isoformat(),
                end_time=window.end_time.isoformat(),
                avg_satellites=window.avg_satellites,
                max_elevation=window.max_elevation,
                duration_minutes=window.duration_minutes
            )
            for window in prediction.optimal_windows
        ]
        
        # 轉換統計資訊
        stats = prediction.statistics
        statistics = PredictionStatisticsDTO(
            satellites=stats.get("satellites", {}),
            elevation=stats.get("elevation", {}),
            coverage=stats.get("coverage", {}),
            optimal_windows_count=stats.get("optimal_windows_count", 0),
            peak_hours=stats.get("peak_hours", [])
        ) if stats else None
        
        # 提取觀測者位置（從元資料或使用預設值）
        observer_location = prediction.metadata.get("observer_location", {
            "latitude": 25.0330,
            "longitude": 121.5654,
            "altitude": 0.0
        })
        
        return cls(
            prediction_id=prediction.prediction_id,
            time_scale=prediction.time_scale.value,
            created_at=prediction.created_at.isoformat(),
            observer_location=observer_location,
            start_time=prediction.start_time.isoformat(),
            end_time=prediction.end_time.isoformat(),
            total_satellites=total_satellites,
            analyzed_satellites=analyzed_satellites,
            prediction_points=prediction_points,
            optimal_windows=optimal_windows,
            statistics=statistics,
            metadata=prediction.metadata
        )