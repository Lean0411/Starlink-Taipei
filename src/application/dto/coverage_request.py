"""
覆蓋率分析請求 DTO
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CoverageRequest:
    """覆蓋率分析請求

    Attributes:
        observer_latitude: 觀測者緯度
        observer_longitude: 觀測者經度
        observer_elevation: 觀測者高度（公尺）
        start_time: 分析開始時間
        duration_minutes: 分析持續時間（分鐘）
        interval_minutes: 時間間隔（分鐘）
        min_elevation: 最小仰角（度）
        satellite_filter: 衛星篩選條件
    """

    observer_latitude: float
    observer_longitude: float
    observer_elevation: float = 0.0
    start_time: Optional[datetime] = None
    duration_minutes: int = 60
    interval_minutes: int = 1
    min_elevation: float = 25.0
    satellite_filter: Optional[str] = None

    def __post_init__(self):
        """驗證請求參數"""
        if self.start_time is None:
            self.start_time = datetime.now()

        if not -90 <= self.observer_latitude <= 90:
            raise ValueError("緯度必須在 -90 到 90 之間")

        if not -180 <= self.observer_longitude <= 180:
            raise ValueError("經度必須在 -180 到 180 之間")

        if self.duration_minutes <= 0:
            raise ValueError("持續時間必須大於 0")

        if self.interval_minutes <= 0:
            raise ValueError("時間間隔必須大於 0")

        if not 0 <= self.min_elevation <= 90:
            raise ValueError("最小仰角必須在 0 到 90 之間")

