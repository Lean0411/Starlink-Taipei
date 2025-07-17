"""
衛星實體 - 領域核心實體
這是領域層的核心實體，不依賴任何外部套件
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..value_objects.orbital_elements import OrbitalElements
from ..value_objects.position import Position


@dataclass
class Satellite:
    """衛星實體

    Attributes:
        satellite_id: 衛星唯一識別碼
        name: 衛星名稱
        orbital_elements: 軌道元素
        launch_date: 發射日期
        is_active: 是否活躍
    """

    satellite_id: str
    name: str
    orbital_elements: OrbitalElements
    launch_date: Optional[datetime] = None
    is_active: bool = True

    def calculate_position_at(self, time: datetime) -> Position:
        """計算衛星在特定時間的位置

        Args:
            time: 要計算的時間點

        Returns:
            Position: 衛星位置
            
        Note:
            這個方法需要由應用層或基礎設施層的服務來實現。
            在 Clean Architecture 中，實體不應包含複雜的計算邏輯。
            請使用 OrbitCalculator 服務來計算位置。
        """
        # 這是一個標記方法，提醒開發者使用領域服務
        raise NotImplementedError(
            "Position calculation should be done by domain service. "
            "Use OrbitCalculator.calculate_position(satellite, time) instead."
        )

    def is_visible_from(self, observer_position: Position, time: datetime) -> bool:
        """檢查衛星是否從觀測點可見

        Args:
            observer_position: 觀測者位置
            time: 觀測時間

        Returns:
            bool: 是否可見
        """
        # 簡單的業務規則檢查
        if not self.is_active:
            return False

        # 詳細的可見性計算應由領域服務處理
        raise NotImplementedError("Visibility calculation should be done by domain service")

    def __eq__(self, other) -> bool:
        if not isinstance(other, Satellite):
            return False
        return self.satellite_id == other.satellite_id

    def __hash__(self) -> int:
        return hash(self.satellite_id)
