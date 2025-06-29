"""
觀測者實體 - 代表地面觀測站或使用者
"""

from dataclasses import dataclass

from ..value_objects.position import Position


@dataclass
class Observer:
    """觀測者實體

    Attributes:
        observer_id: 觀測者唯一識別碼
        name: 觀測者名稱
        position: 觀測者位置
        min_elevation: 最小仰角限制（度）
    """

    observer_id: str
    name: str
    position: Position
    min_elevation: float = 25.0  # 預設最小仰角

    def __post_init__(self):
        """驗證觀測者參數"""
        if not 0 <= self.min_elevation <= 90:
            raise ValueError(f"最小仰角必須在 0 到 90 度之間，但收到 {self.min_elevation}")

    def can_observe(self, elevation: float) -> bool:
        """檢查是否能觀測到特定仰角的物體

        Args:
            elevation: 物體仰角（度）

        Returns:
            bool: 是否可觀測
        """
        return elevation >= self.min_elevation

    @classmethod
    def taipei_observer(cls) -> "Observer":
        """創建台北觀測者的工廠方法

        Returns:
            Observer: 台北觀測者實例
        """
        return cls(
            observer_id="taipei-default",
            name="台北觀測站",
            position=Position(latitude=25.0330, longitude=121.5654, elevation=10.0),
        )

