"""
預測請求 DTO
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ...domain.entities.prediction import PredictionTimeScale
from .coverage_request import ObserverDTO


@dataclass
class PredictionRequest:
    """預測請求

    Attributes:
        observer: 觀測者資訊
        time_scale: 預測時間尺度
        start_time: 預測開始時間
        min_elevation: 最小仰角
        satellite_ids: 要分析的衛星ID列表（可選）
        min_satellites_for_window: 最佳窗口的最少衛星數
    """

    observer: ObserverDTO
    time_scale: PredictionTimeScale = PredictionTimeScale.MEDIUM_TERM
    start_time: Optional[datetime] = None
    min_elevation: float = 25.0
    satellite_ids: Optional[List[str]] = None
    min_satellites_for_window: int = 30

    def __post_init__(self):
        """驗證請求參數"""
        if self.start_time is None:
            self.start_time = datetime.now()

        if not -90 <= self.observer.latitude <= 90:
            raise ValueError("緯度必須在 -90 到 90 之間")

        if not -180 <= self.observer.longitude <= 180:
            raise ValueError("經度必須在 -180 到 180 之間")

        if not 0 <= self.min_elevation <= 90:
            raise ValueError("最小仰角必須在 0 到 90 之間")

        if self.min_satellites_for_window < 1:
            raise ValueError("最少衛星數必須大於 0")
