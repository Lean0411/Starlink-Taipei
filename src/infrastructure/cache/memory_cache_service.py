"""
記憶體快取服務實作 - 作為 Redis 的後備選項
"""

import asyncio
import time
from typing import Any, Optional, List, Dict
from collections import OrderedDict
import logging
import fnmatch

from ...domain.services.cache_service import CacheService


logger = logging.getLogger(__name__)


class CacheEntry:
    """快取項目"""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def remaining_ttl(self) -> Optional[int]:
        """獲取剩餘 TTL"""
        if self.ttl is None:
            return -1
        remaining = self.ttl - (time.time() - self.created_at)
        return max(0, int(remaining))


class MemoryCacheService(CacheService):
    """記憶體快取服務實作
    
    使用 OrderedDict 實作 LRU 快取，支援過期時間
    適合作為 Redis 不可用時的後備方案
    """
    
    def __init__(self, max_size: int = 10000):
        """初始化記憶體快取
        
        Args:
            max_size: 最大快取項目數
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        logger.info(f"初始化記憶體快取，最大大小: {max_size}")
    
    def _evict_expired(self):
        """清除過期項目"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def _evict_lru(self):
        """清除最近最少使用的項目"""
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            # 移到最後（LRU）
            self._cache.move_to_end(key)
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設定快取值"""
        async with self._lock:
            # 清除過期項目
            self._evict_expired()
            
            # 確保有空間
            if key not in self._cache:
                self._evict_lru()
            
            # 設定新值
            self._cache[key] = CacheEntry(value, ttl)
            self._cache.move_to_end(key)
            
            return True
    
    async def delete(self, key: str) -> bool:
        """刪除快取"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """檢查快取是否存在"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            if entry.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """批次獲取快取"""
        results = []
        for key in keys:
            value = await self.get(key)
            results.append(value)
        return results
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """批次設定快取"""
        async with self._lock:
            # 清除過期項目
            self._evict_expired()
            
            # 確保有足夠空間
            new_keys = [k for k in mapping if k not in self._cache]
            while len(self._cache) + len(new_keys) > self.max_size:
                self._cache.popitem(last=False)
            
            # 設定所有值
            for key, value in mapping.items():
                self._cache[key] = CacheEntry(value, ttl)
                self._cache.move_to_end(key)
            
            return True
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除符合模式的快取"""
        async with self._lock:
            matching_keys = [
                key for key in self._cache
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in matching_keys:
                del self._cache[key]
            
            return len(matching_keys)
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """獲取快取剩餘過期時間"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            return entry.remaining_ttl()
    
    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """延長快取過期時間"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None or entry.is_expired():
                return False
            
            # 建立新的快取項目
            self._cache[key] = CacheEntry(entry.value, ttl)
            self._cache.move_to_end(key)
            
            return True
    
    async def is_connected(self) -> bool:
        """檢查快取服務是否連線（記憶體快取始終連線）"""
        return True
    
    async def close(self):
        """關閉快取連線（清空快取）"""
        async with self._lock:
            self._cache.clear()
            logger.info("記憶體快取已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取快取統計資訊"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": 0.0  # 可以實作更詳細的統計
        }