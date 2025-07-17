"""
支援快取的覆蓋率分析器
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional

from ..entities.satellite import Satellite
from ..entities.observer import Observer
from ..entities.coverage_analysis import CoverageAnalysis, OptimalWindow
from ..services.coverage_analyzer import CoverageAnalyzer
from ..services.cache_service import CacheService
from ..constants import RedisConstants

logger = logging.getLogger(__name__)


class CachedCoverageAnalyzer(CoverageAnalyzer):
    """支援快取的覆蓋率分析器
    
    在分析器基礎上添加快取層，避免重複計算
    """
    
    def __init__(self, orbit_calculator, cache_service: CacheService):
        """初始化快取覆蓋率分析器
        
        Args:
            orbit_calculator: 軌道計算器
            cache_service: 快取服務
        """
        super().__init__(orbit_calculator)
        self.cache_service = cache_service
    
    def _generate_analysis_key(
        self,
        satellites: List[Satellite],
        observer: Observer,
        start_time: datetime,
        duration_minutes: int,
        interval_minutes: int
    ) -> str:
        """生成分析快取鍵
        
        Args:
            satellites: 衛星列表
            observer: 觀測者
            start_time: 開始時間
            duration_minutes: 持續時間
            interval_minutes: 時間間隔
            
        Returns:
            str: 快取鍵
        """
        # 建立唯一識別符
        key_parts = [
            observer.observer_id,
            str(int(start_time.timestamp())),
            str(duration_minutes),
            str(interval_minutes),
            # 衛星 ID 的雜湊值
            hashlib.md5(
                ",".join(sorted([s.satellite_id for s in satellites])).encode()
            ).hexdigest()[:8]
        ]
        
        return f"{RedisConstants.COVERAGE_PREFIX}{'_'.join(key_parts)}"
    
    async def analyze_coverage_cached(
        self,
        satellites: List[Satellite],
        observer: Observer,
        start_time: datetime,
        duration_minutes: int,
        interval_minutes: int = 1
    ) -> CoverageAnalysis:
        """分析衛星覆蓋率（支援快取）
        
        Args:
            satellites: 衛星列表
            observer: 觀測者
            start_time: 開始時間
            duration_minutes: 持續時間（分鐘）
            interval_minutes: 時間間隔（分鐘）
            
        Returns:
            CoverageAnalysis: 覆蓋率分析結果
        """
        # 生成快取鍵
        cache_key = self._generate_analysis_key(
            satellites, observer, start_time, duration_minutes, interval_minutes
        )
        
        # 嘗試從快取獲取
        try:
            cached_analysis = await self.cache_service.get(cache_key)
            if cached_analysis:
                logger.info(f"覆蓋率分析快取命中: {cache_key}")
                # 重建 CoverageAnalysis 物件
                return self._reconstruct_analysis(cached_analysis)
        except Exception as e:
            logger.warning(f"覆蓋率分析快取讀取失敗: {e}")
        
        # 執行分析
        logger.info(f"執行覆蓋率分析: {len(satellites)} 顆衛星")
        analysis = self.analyze_coverage(
            satellites, observer, start_time, duration_minutes, interval_minutes
        )
        
        # 儲存到快取
        try:
            # 將分析結果轉換為可序列化格式
            serializable_analysis = self._make_serializable(analysis)
            await self.cache_service.set(
                cache_key,
                serializable_analysis,
                ttl=RedisConstants.COVERAGE_ANALYSIS_TTL
            )
            logger.info(f"覆蓋率分析已快取: {cache_key}")
        except Exception as e:
            logger.warning(f"覆蓋率分析快取儲存失敗: {e}")
        
        return analysis
    
    async def find_optimal_windows_cached(
        self,
        coverage: CoverageAnalysis,
        min_satellites: int = 30,
        min_duration_minutes: int = 30
    ) -> List[OptimalWindow]:
        """尋找最佳觀測窗口（支援快取）
        
        Args:
            coverage: 覆蓋率分析結果
            min_satellites: 最少衛星數
            min_duration_minutes: 最短持續時間（分鐘）
            
        Returns:
            List[OptimalWindow]: 最佳觀測窗口列表
        """
        # 生成快取鍵
        cache_key = (
            f"{RedisConstants.WINDOW_PREFIX}"
            f"{coverage.observer.observer_id}_"
            f"{int(coverage.start_time.timestamp())}_"
            f"{min_satellites}_{min_duration_minutes}"
        )
        
        # 嘗試從快取獲取
        try:
            cached_windows = await self.cache_service.get(cache_key)
            if cached_windows:
                logger.debug(f"最佳窗口快取命中: {cache_key}")
                return self._reconstruct_windows(cached_windows)
        except Exception as e:
            logger.warning(f"最佳窗口快取讀取失敗: {e}")
        
        # 尋找最佳窗口
        windows = self.find_optimal_windows(coverage, min_satellites, min_duration_minutes)
        
        # 儲存到快取
        try:
            serializable_windows = [self._window_to_dict(w) for w in windows]
            await self.cache_service.set(
                cache_key,
                serializable_windows,
                ttl=RedisConstants.OPTIMAL_WINDOW_TTL
            )
            logger.debug(f"最佳窗口已快取: {cache_key}")
        except Exception as e:
            logger.warning(f"最佳窗口快取儲存失敗: {e}")
        
        return windows
    
    def _make_serializable(self, analysis: CoverageAnalysis) -> dict:
        """將分析結果轉換為可序列化格式"""
        return {
            "observer": {
                "observer_id": analysis.observer.observer_id,
                "name": analysis.observer.name,
                "position": {
                    "latitude": analysis.observer.position.latitude,
                    "longitude": analysis.observer.position.longitude,
                    "altitude": analysis.observer.position.altitude
                },
                "min_elevation": analysis.observer.min_elevation
            },
            "start_time": analysis.start_time.isoformat(),
            "end_time": analysis.end_time.isoformat(),
            "analyzed_satellites": analysis.analyzed_satellites,
            "snapshots": [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "visible_satellites": s.visible_satellites,
                    "satellite_positions": {
                        sat_id: {
                            "latitude": pos.latitude,
                            "longitude": pos.longitude,
                            "altitude": pos.altitude
                        } if pos else None
                        for sat_id, pos in s.satellite_positions.items()
                    }
                }
                for s in analysis.snapshots
            ],
            "statistics": {
                "total_snapshots": analysis.statistics.total_snapshots,
                "average_visible_count": analysis.statistics.average_visible_count,
                "max_visible_count": analysis.statistics.max_visible_count,
                "min_visible_count": analysis.statistics.min_visible_count,
                "coverage_percentage": analysis.statistics.coverage_percentage
            }
        }
    
    def _reconstruct_analysis(self, data: dict) -> CoverageAnalysis:
        """從序列化資料重建分析結果"""
        from ..value_objects.position import Position
        from ..entities.coverage_analysis import CoverageSnapshot, CoverageStatistics
        
        # 重建觀測者
        observer = Observer(
            observer_id=data["observer"]["observer_id"],
            name=data["observer"]["name"],
            position=Position(
                data["observer"]["position"]["latitude"],
                data["observer"]["position"]["longitude"],
                data["observer"]["position"]["altitude"]
            ),
            min_elevation=data["observer"]["min_elevation"]
        )
        
        # 重建分析結果
        analysis = CoverageAnalysis(
            observer=observer,
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            analyzed_satellites=data["analyzed_satellites"]
        )
        
        # 重建快照
        for snapshot_data in data["snapshots"]:
            positions = {}
            for sat_id, pos_data in snapshot_data["satellite_positions"].items():
                if pos_data:
                    positions[sat_id] = Position(
                        pos_data["latitude"],
                        pos_data["longitude"],
                        pos_data["altitude"]
                    )
                else:
                    positions[sat_id] = None
            
            snapshot = CoverageSnapshot(
                timestamp=datetime.fromisoformat(snapshot_data["timestamp"]),
                visible_satellites=snapshot_data["visible_satellites"],
                satellite_positions=positions
            )
            analysis.snapshots.append(snapshot)
        
        # 重建統計資料
        stats_data = data["statistics"]
        analysis.statistics = CoverageStatistics(
            total_snapshots=stats_data["total_snapshots"],
            average_visible_count=stats_data["average_visible_count"],
            max_visible_count=stats_data["max_visible_count"],
            min_visible_count=stats_data["min_visible_count"],
            coverage_percentage=stats_data["coverage_percentage"]
        )
        
        return analysis
    
    def _window_to_dict(self, window: OptimalWindow) -> dict:
        """將最佳窗口轉換為字典"""
        return {
            "start_time": window.start_time.isoformat(),
            "end_time": window.end_time.isoformat(),
            "avg_satellites": window.avg_satellites,
            "max_elevation": window.max_elevation
        }
    
    def _reconstruct_windows(self, data: List[dict]) -> List[OptimalWindow]:
        """從序列化資料重建最佳窗口列表"""
        windows = []
        for window_data in data:
            window = OptimalWindow(
                start_time=datetime.fromisoformat(window_data["start_time"]),
                end_time=datetime.fromisoformat(window_data["end_time"]),
                avg_satellites=window_data["avg_satellites"],
                max_elevation=window_data["max_elevation"]
            )
            windows.append(window)
        return windows
    
    async def clear_analysis_cache(self, observer_id: Optional[str] = None):
        """清除分析快取
        
        Args:
            observer_id: 特定觀測者 ID，如果為 None 則清除所有
        """
        if observer_id:
            pattern = f"{RedisConstants.COVERAGE_PREFIX}{observer_id}_*"
        else:
            pattern = f"{RedisConstants.COVERAGE_PREFIX}*"
        
        try:
            count = await self.cache_service.clear_pattern(pattern)
            logger.info(f"清除 {count} 個覆蓋率分析快取項目")
        except Exception as e:
            logger.error(f"清除分析快取失敗: {e}")