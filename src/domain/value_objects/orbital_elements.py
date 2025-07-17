"""
軌道元素值物件 - 描述衛星軌道的參數
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OrbitalElements:
    """軌道元素值物件

    使用 TLE (Two-Line Element) 格式的軌道參數

    Attributes:
        epoch: 元素的時間戳記
        inclination: 軌道傾角（度）
        raan: 升交點赤經（度）
        eccentricity: 離心率
        arg_perigee: 近地點幅角（度）
        mean_anomaly: 平近點角（度）
        mean_motion: 平均運動（每日軌道數）
        bstar: 大氣阻力項
    """

    epoch: datetime
    inclination: float
    raan: float  # Right Ascension of Ascending Node
    eccentricity: float
    arg_perigee: float  # Argument of Perigee
    mean_anomaly: float
    mean_motion: float
    bstar: float = 0.0

    def __post_init__(self):
        """驗證軌道參數"""
        if not 0 <= self.inclination <= 180:
            raise ValueError("軌道傾角必須在 0 到 180 度之間")

        if not 0 <= self.raan <= 360:
            raise ValueError("升交點赤經必須在 0 到 360 度之間")

        if not 0 <= self.eccentricity < 1:
            raise ValueError("離心率必須在 0 到 1 之間（不含 1）")

        if not 0 <= self.arg_perigee <= 360:
            raise ValueError("近地點幅角必須在 0 到 360 度之間")

        if not 0 <= self.mean_anomaly <= 360:
            raise ValueError("平近點角必須在 0 到 360 度之間")

        if self.mean_motion <= 0:
            raise ValueError("平均運動必須大於 0")

    @property
    def period_minutes(self) -> float:
        """計算軌道週期（分鐘）

        Returns:
            float: 軌道週期
        """
        return 1440.0 / self.mean_motion  # 1440 分鐘 = 24 小時

    @property
    def is_low_earth_orbit(self) -> bool:
        """檢查是否為低地球軌道

        LEO 定義為週期小於 128 分鐘

        Returns:
            bool: 是否為 LEO
        """
        return self.period_minutes < 128
