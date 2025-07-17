"""
覆蓋率分析請求 DTO
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ObserverDTO:
    """觀測者 DTO"""

    latitude: float
    longitude: float
    altitude: float = 0.0


@dataclass
class CoverageRequest:
    """覆蓋率分析請求

    Attributes:
        start_time: 分析開始時間
        end_time: 分析結束時間
        time_step_minutes: 時間步長（分鐘）
        elevation_mask: 最小仰角（度）
        observer: 觀測者資訊
    """

    start_time: datetime
    end_time: datetime
    time_step_minutes: int = 60
    elevation_mask: float = 25.0
    observer: ObserverDTO = None

    def __post_init__(self):
        """驗證請求參數"""
        if self.observer is None:
            self.observer = ObserverDTO(latitude=25.0330, longitude=121.5654, altitude=0.0)

        if not -90 <= self.observer.latitude <= 90:
            raise ValueError("緯度必須在 -90 到 90 之間")

        if not -180 <= self.observer.longitude <= 180:
            raise ValueError("經度必須在 -180 到 180 之間")

        if self.time_step_minutes <= 0:
            raise ValueError("時間步長必須大於 0")

        if not 0 <= self.elevation_mask <= 90:
            raise ValueError("最小仰角必須在 0 到 90 之間")
