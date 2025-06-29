"""
軌道計算領域服務 - 純領域邏輯，不依賴外部套件
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Tuple

from ..entities.satellite import Satellite
from ..value_objects.position import Position


class OrbitCalculator(ABC):
    """軌道計算器抽象介面
    
    這是領域服務的介面，具體實作會在基礎設施層
    """
    
    @abstractmethod
    def calculate_position(self, satellite: Satellite, time: datetime) -> Position:
        """計算衛星在特定時間的位置
        
        Args:
            satellite: 衛星實體
            time: 計算時間
            
        Returns:
            Position: 衛星位置
        """
        pass
    
    @abstractmethod
    def calculate_pass_details(
        self, 
        satellite: Satellite, 
        observer_position: Position,
        time: datetime
    ) -> Tuple[float, float, float]:
        """計算衛星相對於觀測者的詳細資訊
        
        Args:
            satellite: 衛星實體
            observer_position: 觀測者位置
            time: 計算時間
            
        Returns:
            Tuple[float, float, float]: (方位角, 仰角, 距離)
        """
        pass
    
    @abstractmethod
    def is_sunlit(self, satellite: Satellite, time: datetime) -> bool:
        """檢查衛星是否被太陽照射
        
        Args:
            satellite: 衛星實體
            time: 計算時間
            
        Returns:
            bool: 是否被太陽照射
        """
        pass