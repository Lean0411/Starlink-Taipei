"""
快取服務介面 - 定義快取操作的抽象介面
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
from datetime import timedelta


class CacheService(ABC):
    """快取服務介面
    
    定義快取的基本操作，支援不同的快取實作（Redis、記憶體等）
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取值
        
        Args:
            key: 快取鍵
            
        Returns:
            Optional[Any]: 快取值，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設定快取值
        
        Args:
            key: 快取鍵
            value: 快取值
            ttl: 過期時間（秒），None 表示永不過期
            
        Returns:
            bool: 是否設定成功
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """刪除快取
        
        Args:
            key: 快取鍵
            
        Returns:
            bool: 是否刪除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """檢查快取是否存在
        
        Args:
            key: 快取鍵
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """批次獲取快取
        
        Args:
            keys: 快取鍵列表
            
        Returns:
            List[Optional[Any]]: 快取值列表，不存在的鍵返回 None
        """
        pass
    
    @abstractmethod
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """批次設定快取
        
        Args:
            mapping: 鍵值對映射
            ttl: 過期時間（秒）
            
        Returns:
            bool: 是否全部設定成功
        """
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """清除符合模式的快取
        
        Args:
            pattern: 鍵模式（支援萬用字元）
            
        Returns:
            int: 刪除的鍵數量
        """
        pass
    
    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """獲取快取剩餘過期時間
        
        Args:
            key: 快取鍵
            
        Returns:
            Optional[int]: 剩餘秒數，-1 表示永不過期，None 表示鍵不存在
        """
        pass
    
    @abstractmethod
    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """延長快取過期時間
        
        Args:
            key: 快取鍵
            ttl: 新的過期時間（秒）
            
        Returns:
            bool: 是否延長成功
        """
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """檢查快取服務是否連線
        
        Returns:
            bool: 是否已連線
        """
        pass
    
    @abstractmethod
    async def close(self):
        """關閉快取連線"""
        pass