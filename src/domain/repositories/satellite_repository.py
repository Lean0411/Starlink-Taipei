"""
衛星資料庫介面 - 領域層的 Repository 介面
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.satellite import Satellite


class SatelliteRepository(ABC):
    """衛星資料庫抽象介面
    
    定義了獲取和管理衛星資料的方法
    具體實作會在基礎設施層
    """
    
    @abstractmethod
    async def get_all_satellites(self) -> List[Satellite]:
        """獲取所有衛星
        
        Returns:
            List[Satellite]: 衛星列表
        """
        pass
    
    @abstractmethod
    async def get_active_satellites(self) -> List[Satellite]:
        """獲取所有活躍的衛星
        
        Returns:
            List[Satellite]: 活躍衛星列表
        """
        pass
    
    @abstractmethod
    async def get_satellite_by_id(self, satellite_id: str) -> Optional[Satellite]:
        """根據 ID 獲取衛星
        
        Args:
            satellite_id: 衛星 ID
            
        Returns:
            Optional[Satellite]: 衛星實體，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_satellites_by_name_pattern(self, pattern: str) -> List[Satellite]:
        """根據名稱模式獲取衛星
        
        Args:
            pattern: 名稱模式（支援通配符）
            
        Returns:
            List[Satellite]: 符合模式的衛星列表
        """
        pass
    
    @abstractmethod
    async def update_satellite_tle(self, satellite_id: str, tle_data: dict) -> bool:
        """更新衛星的 TLE 資料
        
        Args:
            satellite_id: 衛星 ID
            tle_data: 新的 TLE 資料
            
        Returns:
            bool: 是否更新成功
        """
        pass
    
    @abstractmethod
    async def get_last_update_time(self) -> Optional[datetime]:
        """獲取最後更新時間
        
        Returns:
            Optional[datetime]: 最後更新時間，如果沒有則返回 None
        """
        pass