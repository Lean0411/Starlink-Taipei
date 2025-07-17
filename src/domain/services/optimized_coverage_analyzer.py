"""
優化的覆蓋率分析器 - 使用批次處理提升效能
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

from ..entities.satellite import Satellite
from ..entities.observer import Observer
from ..entities.coverage_analysis import CoverageAnalysis, CoverageSnapshot, OptimalWindow
from ..value_objects.position import Position
from .coverage_analyzer import CoverageAnalyzer
from ...application.services.batch_processing_service import BatchProcessingService


logger = logging.getLogger(__name__)


class OptimizedCoverageAnalyzer(CoverageAnalyzer):
    """優化的覆蓋率分析器
    
    使用批次處理和並行計算來提升大量衛星的分析效能
    """
    
    def __init__(self, orbit_calculator, batch_processor: Optional[BatchProcessingService] = None):
        """初始化優化的覆蓋率分析器
        
        Args:
            orbit_calculator: 軌道計算器
            batch_processor: 批次處理服務（可選）
        """
        super().__init__(orbit_calculator)
        self.batch_processor = batch_processor or BatchProcessingService(
            orbit_calculator,
            batch_size=500  # 針對 7500+ 顆衛星優化的批次大小
        )
    
    def analyze_coverage(
        self,
        satellites: List[Satellite],
        observer: Observer,
        start_time: datetime,
        duration_minutes: int,
        interval_minutes: int = 1
    ) -> CoverageAnalysis:
        """分析衛星覆蓋率（優化版本）
        
        Args:
            satellites: 衛星列表
            observer: 觀測者
            start_time: 開始時間
            duration_minutes: 持續時間（分鐘）
            interval_minutes: 時間間隔（分鐘）
            
        Returns:
            CoverageAnalysis: 覆蓋率分析結果
        """
        logger.info(f"開始優化覆蓋率分析，衛星數量: {len(satellites)}")
        
        # 篩選活躍衛星
        active_satellites = [s for s in satellites if s.is_active]
        logger.info(f"活躍衛星數量: {len(active_satellites)}")
        
        # 建立分析結果
        analysis = CoverageAnalysis(
            observer=observer,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration_minutes),
            analyzed_satellites=[s.satellite_id for s in active_satellites]
        )
        
        # 計算時間點
        current_time = start_time
        time_points = []
        while current_time <= analysis.end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=interval_minutes)
        
        # 批次處理所有時間點
        total_points = len(time_points)
        for i, time_point in enumerate(time_points):
            if i % 10 == 0:  # 每10個時間點記錄一次進度
                logger.info(f"處理進度: {i}/{total_points} ({i/total_points*100:.1f}%)")
            
            # 批次計算可見性
            visibility_map = self.batch_processor.calculate_visibility_batch(
                active_satellites,
                observer.position,
                time_point,
                observer.min_elevation
            )
            
            # 獲取可見衛星
            visible_satellites = [
                sat_id for sat_id, is_visible in visibility_map.items()
                if is_visible
            ]
            
            # 如果有可見衛星，計算它們的位置
            positions = {}
            if visible_satellites:
                visible_sats = [s for s in active_satellites if s.satellite_id in visible_satellites]
                position_results = self.batch_processor.calculate_positions_batch(
                    visible_sats,
                    time_point
                )
                
                for sat_id, position in position_results.results:
                    positions[sat_id] = position
            
            # 建立快照
            snapshot = CoverageSnapshot(
                timestamp=time_point,
                visible_satellites=visible_satellites,
                satellite_positions=positions
            )
            
            analysis.add_snapshot(snapshot)
        
        # 更新統計資訊
        analysis.update_statistics()
        
        logger.info(f"覆蓋率分析完成，平均可見衛星數: {analysis.statistics.average_visible_count:.1f}")
        
        return analysis
    
    def find_optimal_windows_optimized(
        self,
        coverage: CoverageAnalysis,
        min_satellites: int = 30,
        min_duration_minutes: int = 30,
        merge_gap_minutes: int = 10
    ) -> List[OptimalWindow]:
        """尋找最佳觀測窗口（優化版本）
        
        使用滑動窗口演算法來快速識別最佳觀測時段
        
        Args:
            coverage: 覆蓋率分析結果
            min_satellites: 最少衛星數
            min_duration_minutes: 最短持續時間（分鐘）
            merge_gap_minutes: 合併間隔（分鐘）
            
        Returns:
            List[OptimalWindow]: 最佳觀測窗口列表
        """
        if not coverage.snapshots:
            return []
        
        # 使用滑動窗口找出候選窗口
        candidate_windows = []
        window_start = None
        window_satellites = []
        
        for i, snapshot in enumerate(coverage.snapshots):
            if snapshot.visible_count >= min_satellites:
                if window_start is None:
                    window_start = i
                    window_satellites = []
                window_satellites.append(snapshot.visible_count)
            else:
                if window_start is not None:
                    # 窗口結束，檢查是否符合條件
                    window_duration = i - window_start
                    if window_duration >= min_duration_minutes:
                        candidate_windows.append({
                            'start': window_start,
                            'end': i - 1,
                            'satellites': window_satellites
                        })
                    window_start = None
                    window_satellites = []
        
        # 處理最後一個窗口
        if window_start is not None:
            window_duration = len(coverage.snapshots) - window_start
            if window_duration >= min_duration_minutes:
                candidate_windows.append({
                    'start': window_start,
                    'end': len(coverage.snapshots) - 1,
                    'satellites': window_satellites
                })
        
        # 合併相近的窗口
        merged_windows = self._merge_windows(
            candidate_windows,
            coverage.snapshots,
            merge_gap_minutes
        )
        
        # 轉換為 OptimalWindow 物件
        optimal_windows = []
        for window in merged_windows:
            start_snapshot = coverage.snapshots[window['start']]
            end_snapshot = coverage.snapshots[window['end']]
            
            # 計算窗口內的統計資料
            window_snapshots = coverage.snapshots[window['start']:window['end']+1]
            avg_satellites = sum(s.visible_count for s in window_snapshots) / len(window_snapshots)
            
            # 計算最大仰角（簡化版本）
            max_elevation = 90.0  # 需要實際計算
            
            optimal_windows.append(OptimalWindow(
                start_time=start_snapshot.timestamp,
                end_time=end_snapshot.timestamp,
                avg_satellites=avg_satellites,
                max_elevation=max_elevation
            ))
        
        # 按平均衛星數排序
        optimal_windows.sort(key=lambda w: w.avg_satellites, reverse=True)
        
        return optimal_windows
    
    def _merge_windows(
        self,
        windows: List[Dict],
        snapshots: List[CoverageSnapshot],
        merge_gap_minutes: int
    ) -> List[Dict]:
        """合併相近的窗口
        
        Args:
            windows: 候選窗口列表
            snapshots: 快照列表
            merge_gap_minutes: 合併間隔
            
        Returns:
            List[Dict]: 合併後的窗口
        """
        if not windows:
            return []
        
        merged = [windows[0]]
        
        for current in windows[1:]:
            last = merged[-1]
            
            # 檢查時間間隔
            gap_snapshots = current['start'] - last['end'] - 1
            
            if gap_snapshots <= merge_gap_minutes:
                # 合併窗口
                last['end'] = current['end']
                last['satellites'].extend(current['satellites'])
            else:
                # 新增為獨立窗口
                merged.append(current)
        
        return merged
    
    def optimize_for_large_constellation(self):
        """針對大型星座優化設置
        
        調整批次大小和並行參數以處理 7500+ 顆衛星
        """
        # 根據衛星數量動態調整批次大小
        if hasattr(self.batch_processor, 'batch_size'):
            self.batch_processor.batch_size = 500
        
        # 增加工作執行緒數（如果系統支援）
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        if hasattr(self.batch_processor, 'max_workers'):
            self.batch_processor.max_workers = min(cpu_count * 2, 32)
        
        logger.info(f"優化設置完成: 批次大小=500, 工作執行緒={self.batch_processor.max_workers}")