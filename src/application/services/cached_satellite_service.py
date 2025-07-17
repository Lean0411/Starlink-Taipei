"""
支援快取的衛星服務
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities.satellite import Satellite
from ...domain.entities.observer import Observer
from ...domain.value_objects.position import Position
from ...domain.services.cache_service import CacheService
from ...domain.constants import RedisConstants
from ..services.satellite_service import SatelliteService
from ...infrastructure.cache.cache_decorators import cached

logger = logging.getLogger(__name__)


class CachedSatelliteService(SatelliteService):
    """支援快取的衛星服務
    
    在 SatelliteService 基礎上添加快取層，
    大幅提升重複計算的效能
    """
    
    def __init__(self, orbit_calculator, cache_service: CacheService):
        """初始化快取衛星服務
        
        Args:
            orbit_calculator: 軌道計算器
            cache_service: 快取服務
        """
        super().__init__(orbit_calculator)
        self.cache_service = cache_service
    
    async def calculate_position_cached(
        self,
        satellite: Satellite,
        time: datetime
    ) -> Optional[Position]:
        """計算衛星位置（支援快取）
        
        Args:
            satellite: 衛星實體
            time: 計算時間
            
        Returns:
            Optional[Position]: 衛星位置，如果計算失敗則返回 None
        """
        # 生成快取鍵
        cache_key = f"{RedisConstants.POSITION_PREFIX}{satellite.satellite_id}:{int(time.timestamp())}"
        
        # 嘗試從快取獲取
        try:
            cached_position = await self.cache_service.get(cache_key)
            if cached_position:
                # 重建 Position 物件
                if isinstance(cached_position, dict):
                    return Position(
                        latitude=cached_position.get('latitude', 0),
                        longitude=cached_position.get('longitude', 0),
                        altitude=cached_position.get('altitude', 0)
                    )
                logger.debug(f"快取命中: {satellite.satellite_id} at {time}")
                return cached_position
        except Exception as e:
            logger.warning(f"快取讀取失敗: {e}")
        
        # 計算位置
        try:
            position = self.calculate_position(satellite, time)
            
            # 儲存到快取
            if position:
                await self.cache_service.set(
                    cache_key,
                    position,
                    ttl=RedisConstants.SATELLITE_POSITION_TTL
                )
                logger.debug(f"位置已快取: {satellite.satellite_id} at {time}")
            
            return position
        except Exception as e:
            logger.error(f"計算衛星位置失敗: {e}")
            return None
    
    async def calculate_positions_batch_cached(
        self,
        satellites: List[Satellite],
        time: datetime
    ) -> Dict[str, Optional[Position]]:
        """批次計算衛星位置（支援快取）
        
        Args:
            satellites: 衛星列表
            time: 計算時間
            
        Returns:
            Dict[str, Optional[Position]]: 衛星 ID 到位置的映射
        """
        results = {}
        uncached_satellites = []
        
        # 生成所有快取鍵
        cache_keys = []
        key_to_satellite = {}
        
        for sat in satellites:
            cache_key = f"{RedisConstants.POSITION_PREFIX}{sat.satellite_id}:{int(time.timestamp())}"
            cache_keys.append(cache_key)
            key_to_satellite[cache_key] = sat
        
        # 批次獲取快取
        try:
            cached_values = await self.cache_service.mget(cache_keys)
            
            for i, (key, value) in enumerate(zip(cache_keys, cached_values)):
                sat = key_to_satellite[key]
                
                if value is not None:
                    # 從快取恢復位置
                    if isinstance(value, dict):
                        position = Position(
                            latitude=value.get('latitude', 0),
                            longitude=value.get('longitude', 0),
                            altitude=value.get('altitude', 0)
                        )
                        results[sat.satellite_id] = position
                    else:
                        results[sat.satellite_id] = value
                    logger.debug(f"批次快取命中: {sat.satellite_id}")
                else:
                    uncached_satellites.append(sat)
        except Exception as e:
            logger.warning(f"批次快取讀取失敗: {e}")
            uncached_satellites = satellites
        
        # 計算未快取的衛星位置
        if uncached_satellites:
            logger.info(f"計算 {len(uncached_satellites)} 個未快取的衛星位置")
            
            new_cache_entries = {}
            
            for sat in uncached_satellites:
                try:
                    position = self.calculate_position(sat, time)
                    results[sat.satellite_id] = position
                    
                    # 準備快取項目
                    if position:
                        cache_key = f"{RedisConstants.POSITION_PREFIX}{sat.satellite_id}:{int(time.timestamp())}"
                        new_cache_entries[cache_key] = position
                except Exception as e:
                    logger.error(f"計算衛星 {sat.satellite_id} 位置失敗: {e}")
                    results[sat.satellite_id] = None
            
            # 批次儲存到快取
            if new_cache_entries:
                try:
                    await self.cache_service.mset(
                        new_cache_entries,
                        ttl=RedisConstants.SATELLITE_POSITION_TTL
                    )
                    logger.info(f"批次快取 {len(new_cache_entries)} 個衛星位置")
                except Exception as e:
                    logger.warning(f"批次快取儲存失敗: {e}")
        
        return results
    
    async def is_visible_cached(
        self,
        satellite: Satellite,
        observer: Observer,
        time: datetime
    ) -> bool:
        """檢查衛星是否可見（支援快取）
        
        Args:
            satellite: 衛星實體
            observer: 觀測者
            time: 觀測時間
            
        Returns:
            bool: 是否可見
        """
        # 可見性變化較快，使用較短的快取時間
        cache_key = (
            f"{RedisConstants.KEY_PREFIX}visibility:"
            f"{satellite.satellite_id}:{observer.observer_id}:{int(time.timestamp())}"
        )
        
        # 嘗試從快取獲取
        try:
            cached_visibility = await self.cache_service.get(cache_key)
            if cached_visibility is not None:
                logger.debug(f"可見性快取命中: {satellite.satellite_id}")
                return bool(cached_visibility)
        except Exception as e:
            logger.warning(f"可見性快取讀取失敗: {e}")
        
        # 計算可見性
        is_visible = self.is_visible(satellite, observer, time)
        
        # 儲存到快取（使用較短的 TTL）
        try:
            await self.cache_service.set(
                cache_key,
                is_visible,
                ttl=30  # 30 秒
            )
        except Exception as e:
            logger.warning(f"可見性快取儲存失敗: {e}")
        
        return is_visible
    
    async def clear_position_cache(self, satellite_id: Optional[str] = None):
        """清除位置快取
        
        Args:
            satellite_id: 特定衛星 ID，如果為 None 則清除所有
        """
        if satellite_id:
            pattern = f"{RedisConstants.POSITION_PREFIX}{satellite_id}:*"
        else:
            pattern = f"{RedisConstants.POSITION_PREFIX}*"
        
        try:
            count = await self.cache_service.clear_pattern(pattern)
            logger.info(f"清除 {count} 個位置快取項目")
        except Exception as e:
            logger.error(f"清除位置快取失敗: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計資訊
        
        Returns:
            Dict[str, Any]: 快取統計
        """
        try:
            # 這需要根據具體的快取實作來調整
            return {
                "connected": await self.cache_service.is_connected(),
                "type": type(self.cache_service).__name__
            }
        except Exception as e:
            logger.error(f"獲取快取統計失敗: {e}")
            return {"error": str(e)}