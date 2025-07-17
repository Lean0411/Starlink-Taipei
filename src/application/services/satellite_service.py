"""
衛星應用服務 - 提供便利的衛星操作方法
"""

from datetime import datetime
from typing import Optional, Tuple

from ...domain.entities.satellite import Satellite
from ...domain.services.orbit_calculator import OrbitCalculator
from ...domain.value_objects.position import Position


class SatelliteService:
    """衛星應用服務
    
    這個服務封裝了衛星相關的業務邏輯，
    提供更方便的介面給應用層使用。
    """
    
    def __init__(self, orbit_calculator: OrbitCalculator):
        """初始化衛星服務
        
        Args:
            orbit_calculator: 軌道計算器實例
        """
        self.orbit_calculator = orbit_calculator
    
    def calculate_position(self, satellite: Satellite, time: datetime) -> Position:
        """計算衛星在特定時間的位置
        
        Args:
            satellite: 衛星實體
            time: 計算時間
            
        Returns:
            Position: 衛星位置
        """
        return self.orbit_calculator.calculate_position(satellite, time)
    
    def get_pass_details(
        self, 
        satellite: Satellite, 
        observer_position: Position, 
        time: datetime
    ) -> Optional[Tuple[float, float, float]]:
        """獲取衛星相對於觀測者的詳細資訊
        
        Args:
            satellite: 衛星實體
            observer_position: 觀測者位置
            time: 計算時間
            
        Returns:
            Optional[Tuple[float, float, float]]: (方位角, 仰角, 距離) 或 None（如果衛星不活躍）
        """
        if not satellite.is_active:
            return None
            
        return self.orbit_calculator.calculate_pass_details(
            satellite, observer_position, time
        )
    
    def is_visible(
        self, 
        satellite: Satellite, 
        observer_position: Position, 
        time: datetime,
        min_elevation: float = 25.0
    ) -> bool:
        """檢查衛星是否可見
        
        Args:
            satellite: 衛星實體
            observer_position: 觀測者位置
            time: 計算時間
            min_elevation: 最小仰角（度）
            
        Returns:
            bool: 是否可見
        """
        if not satellite.is_active:
            return False
            
        azimuth, elevation, distance = self.orbit_calculator.calculate_pass_details(
            satellite, observer_position, time
        )
        
        return elevation >= min_elevation
    
    def is_sunlit(self, satellite: Satellite, time: datetime) -> bool:
        """檢查衛星是否被太陽照射
        
        Args:
            satellite: 衛星實體
            time: 計算時間
            
        Returns:
            bool: 是否被太陽照射
        """
        return self.orbit_calculator.is_sunlit(satellite, time)