"""
位置值物件 - 不可變的位置表示
"""

from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2


@dataclass(frozen=True)
class Position:
    """地理位置值物件

    Attributes:
        latitude: 緯度（度）
        longitude: 經度（度）
        elevation: 高度（公尺）
    """

    latitude: float
    longitude: float
    elevation: float = 0.0

    def __post_init__(self):
        """驗證位置參數"""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"緯度必須在 -90 到 90 之間，但收到 {self.latitude}")

        if not -180 <= self.longitude <= 180:
            raise ValueError(f"經度必須在 -180 到 180 之間，但收到 {self.longitude}")

        if self.elevation < -500:  # 允許負高度（如死海）
            raise ValueError(f"高度不能低於 -500 公尺，但收到 {self.elevation}")

    def distance_to(self, other: "Position") -> float:
        """計算到另一個位置的大圓距離（公里）

        使用 Haversine 公式計算球面距離

        Args:
            other: 另一個位置

        Returns:
            float: 距離（公里）
        """
        R = 6371.0  # 地球半徑（公里）

        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def to_radians(self) -> tuple[float, float]:
        """轉換為弧度

        Returns:
            tuple: (緯度弧度, 經度弧度)
        """
        return radians(self.latitude), radians(self.longitude)

