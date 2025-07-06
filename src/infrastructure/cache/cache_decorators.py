"""
快取裝飾器 - 簡化快取的使用
"""

import functools
import hashlib
import json
import logging
from typing import Callable, Any, Optional
from datetime import datetime

from ...domain.services.cache_service import CacheService


logger = logging.getLogger(__name__)


def _generate_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """生成快取鍵
    
    Args:
        prefix: 鍵前綴
        func_name: 函數名稱
        args: 位置參數
        kwargs: 關鍵字參數
        
    Returns:
        str: 快取鍵
    """
    # 建立參數的雜湊值
    cache_data = {
        "args": args,
        "kwargs": kwargs
    }
    
    # 將參數轉換為可序列化的格式
    def make_serializable(obj):
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return str(obj)
    
    cache_str = json.dumps(cache_data, default=make_serializable, sort_keys=True)
    cache_hash = hashlib.md5(cache_str.encode()).hexdigest()
    
    return f"{prefix}{func_name}:{cache_hash}"


def cached(
    cache_service: CacheService,
    ttl: int,
    prefix: str = "",
    key_func: Optional[Callable] = None
):
    """快取裝飾器
    
    Args:
        cache_service: 快取服務實例
        ttl: 快取過期時間（秒）
        prefix: 快取鍵前綴
        key_func: 自定義鍵生成函數
        
    Returns:
        裝飾器函數
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成快取鍵
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(prefix, func.__name__, args, kwargs)
            
            # 嘗試從快取獲取
            try:
                cached_value = await cache_service.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"快取命中: {cache_key}")
                    return cached_value
            except Exception as e:
                logger.warning(f"快取讀取失敗: {e}")
            
            # 執行函數
            result = await func(*args, **kwargs)
            
            # 儲存到快取
            try:
                await cache_service.set(cache_key, result, ttl)
                logger.debug(f"快取儲存: {cache_key}")
            except Exception as e:
                logger.warning(f"快取儲存失敗: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步函數的快取（需要在異步環境中運行）
            import asyncio
            
            async def _async_call():
                # 生成快取鍵
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = _generate_cache_key(prefix, func.__name__, args, kwargs)
                
                # 嘗試從快取獲取
                try:
                    cached_value = await cache_service.get(cache_key)
                    if cached_value is not None:
                        logger.debug(f"快取命中: {cache_key}")
                        return cached_value
                except Exception as e:
                    logger.warning(f"快取讀取失敗: {e}")
                
                # 執行函數
                result = func(*args, **kwargs)
                
                # 儲存到快取
                try:
                    await cache_service.set(cache_key, result, ttl)
                    logger.debug(f"快取儲存: {cache_key}")
                except Exception as e:
                    logger.warning(f"快取儲存失敗: {e}")
                
                return result
            
            # 獲取或建立事件迴圈
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(_async_call())
        
        # 根據函數類型返回適當的包裝器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_invalidate(
    cache_service: CacheService,
    pattern: str
):
    """快取失效裝飾器
    
    在函數執行後清除符合模式的快取
    
    Args:
        cache_service: 快取服務實例
        pattern: 要清除的快取鍵模式
        
    Returns:
        裝飾器函數
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # 清除快取
            try:
                count = await cache_service.clear_pattern(pattern)
                logger.debug(f"清除 {count} 個快取項目: {pattern}")
            except Exception as e:
                logger.warning(f"清除快取失敗: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # 在異步環境中清除快取
            import asyncio
            
            async def _clear_cache():
                try:
                    count = await cache_service.clear_pattern(pattern)
                    logger.debug(f"清除 {count} 個快取項目: {pattern}")
                except Exception as e:
                    logger.warning(f"清除快取失敗: {e}")
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(_clear_cache())
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator