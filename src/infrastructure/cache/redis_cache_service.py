"""
Redis 快取服務實作
"""

import json
import logging
from typing import Any, Optional, List, Dict
import asyncio
from datetime import datetime

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None
    RedisError = Exception

from ...domain.services.cache_service import CacheService
from ...domain.constants import RedisConstants


logger = logging.getLogger(__name__)


class RedisSerializationError(Exception):
    """Redis 序列化錯誤"""
    pass


class RedisCacheService(CacheService):
    """Redis 快取服務實作
    
    提供高效能的分散式快取功能，支援：
    - 自動序列化/反序列化
    - 批次操作
    - 模式匹配
    - 連線池管理
    """
    
    def __init__(
        self,
        host: str = RedisConstants.DEFAULT_HOST,
        port: int = RedisConstants.DEFAULT_PORT,
        db: int = RedisConstants.DEFAULT_DB,
        password: Optional[str] = RedisConstants.DEFAULT_PASSWORD,
        max_connections: int = RedisConstants.DEFAULT_MAX_CONNECTIONS
    ):
        """初始化 Redis 快取服務
        
        Args:
            host: Redis 主機
            port: Redis 埠號
            db: 資料庫索引
            password: 密碼（可選）
            max_connections: 最大連線數
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis 套件未安裝。請執行: pip install redis[hiredis]")
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self._client: Optional[Redis] = None
        self._connected = False
    
    async def _ensure_connected(self):
        """確保 Redis 連線"""
        if not self._connected or not self._client:
            await self._connect()
    
    async def _connect(self):
        """建立 Redis 連線"""
        try:
            self._client = await redis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                max_connections=self.max_connections,
                decode_responses=True
            )
            # 測試連線
            await self._client.ping()
            self._connected = True
            logger.info(f"成功連線到 Redis: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Redis 連線失敗: {e}")
            self._connected = False
            raise
    
    def _serialize(self, value: Any) -> str:
        """序列化值為 JSON
        
        Args:
            value: 要序列化的值
            
        Returns:
            str: JSON 字串
            
        Raises:
            RedisSerializationError: 序列化失敗
        """
        try:
            # 處理 datetime 物件
            if hasattr(value, '__dict__'):
                # 將物件轉換為字典
                value_dict = {}
                for key, val in value.__dict__.items():
                    if isinstance(val, datetime):
                        value_dict[key] = val.isoformat()
                    elif hasattr(val, '__dict__'):
                        # 遞迴處理巢狀物件
                        value_dict[key] = self._object_to_dict(val)
                    else:
                        value_dict[key] = val
                return json.dumps(value_dict)
            return json.dumps(value, default=str)
        except Exception as e:
            raise RedisSerializationError(f"序列化失敗: {e}")
    
    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """將物件轉換為字典"""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, val in obj.__dict__.items():
                if isinstance(val, datetime):
                    result[key] = val.isoformat()
                elif hasattr(val, '__dict__'):
                    result[key] = self._object_to_dict(val)
                else:
                    result[key] = val
            return result
        return str(obj)
    
    def _deserialize(self, value: str) -> Any:
        """從 JSON 反序列化值
        
        Args:
            value: JSON 字串
            
        Returns:
            Any: 反序列化的值
            
        Raises:
            RedisSerializationError: 反序列化失敗
        """
        try:
            return json.loads(value)
        except Exception as e:
            # 如果不是 JSON，返回原始字串
            return value
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        await self._ensure_connected()
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except RedisError as e:
            logger.error(f"Redis get 錯誤: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設定快取值"""
        await self._ensure_connected()
        try:
            serialized = self._serialize(value)
            if ttl:
                result = await self._client.setex(key, ttl, serialized)
            else:
                result = await self._client.set(key, serialized)
            return bool(result)
        except (RedisError, RedisSerializationError) as e:
            logger.error(f"Redis set 錯誤: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """刪除快取"""
        await self._ensure_connected()
        try:
            result = await self._client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis delete 錯誤: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """檢查快取是否存在"""
        await self._ensure_connected()
        try:
            return await self._client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis exists 錯誤: {e}")
            return False
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """批次獲取快取"""
        await self._ensure_connected()
        try:
            values = await self._client.mget(keys)
            return [
                self._deserialize(v) if v is not None else None
                for v in values
            ]
        except RedisError as e:
            logger.error(f"Redis mget 錯誤: {e}")
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """批次設定快取"""
        await self._ensure_connected()
        try:
            # 序列化所有值
            serialized_mapping = {
                k: self._serialize(v) for k, v in mapping.items()
            }
            
            if ttl:
                # 使用 pipeline 來設定 TTL
                async with self._client.pipeline() as pipe:
                    for key, value in serialized_mapping.items():
                        pipe.setex(key, ttl, value)
                    results = await pipe.execute()
                return all(results)
            else:
                return await self._client.mset(serialized_mapping)
        except (RedisError, RedisSerializationError) as e:
            logger.error(f"Redis mset 錯誤: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除符合模式的快取"""
        await self._ensure_connected()
        try:
            count = 0
            async for key in self._client.scan_iter(match=pattern):
                if await self._client.delete(key):
                    count += 1
            return count
        except RedisError as e:
            logger.error(f"Redis clear_pattern 錯誤: {e}")
            return 0
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """獲取快取剩餘過期時間"""
        await self._ensure_connected()
        try:
            ttl = await self._client.ttl(key)
            if ttl == -2:  # 鍵不存在
                return None
            return ttl
        except RedisError as e:
            logger.error(f"Redis get_ttl 錯誤: {e}")
            return None
    
    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """延長快取過期時間"""
        await self._ensure_connected()
        try:
            return await self._client.expire(key, ttl)
        except RedisError as e:
            logger.error(f"Redis extend_ttl 錯誤: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """檢查快取服務是否連線"""
        if not self._connected or not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except:
            self._connected = False
            return False
    
    async def close(self):
        """關閉快取連線"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis 連線已關閉")