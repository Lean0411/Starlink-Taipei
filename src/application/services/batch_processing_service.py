"""
批次處理服務 - 優化大量衛星資料處理
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Any, Callable, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

from ...domain.entities.satellite import Satellite
from ...domain.value_objects.position import Position
from ...domain.services.orbit_calculator import OrbitCalculator


logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """批次處理結果"""
    successful: int
    failed: int
    total_time: float
    results: List[Any]
    errors: List[Dict[str, Any]]


class BatchProcessingService:
    """批次處理服務
    
    提供高效的批次處理能力，支援：
    - 並行處理
    - 批次大小優化
    - 錯誤處理
    - 進度追蹤
    """
    
    def __init__(
        self,
        orbit_calculator: OrbitCalculator,
        max_workers: Optional[int] = None,
        batch_size: int = 100
    ):
        """初始化批次處理服務
        
        Args:
            orbit_calculator: 軌道計算器
            max_workers: 最大工作執行緒數（預設為 CPU 核心數）
            batch_size: 批次大小
        """
        self.orbit_calculator = orbit_calculator
        self.max_workers = max_workers
        self.batch_size = batch_size
        self._executor = None
    
    def calculate_positions_batch(
        self,
        satellites: List[Satellite],
        time: datetime,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> BatchResult:
        """批次計算衛星位置
        
        Args:
            satellites: 衛星列表
            time: 計算時間
            progress_callback: 進度回調函數 (completed, total)
            
        Returns:
            BatchResult: 批次處理結果
        """
        start_time = datetime.now()
        results = []
        errors = []
        completed = 0
        
        # 使用執行緒池進行並行處理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 將衛星分批處理
            batches = self._create_batches(satellites, self.batch_size)
            
            # 提交批次任務
            future_to_batch = {
                executor.submit(self._process_position_batch, batch, time): batch
                for batch in batches
            }
            
            # 收集結果
            for future in future_to_batch:
                batch = future_to_batch[future]
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                    completed += len(batch)
                    
                    if progress_callback:
                        progress_callback(completed, len(satellites))
                        
                except Exception as e:
                    logger.error(f"批次處理錯誤: {e}")
                    for sat in batch:
                        errors.append({
                            "satellite_id": sat.satellite_id,
                            "error": str(e)
                        })
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return BatchResult(
            successful=len(results),
            failed=len(errors),
            total_time=total_time,
            results=results,
            errors=errors
        )
    
    def calculate_visibility_batch(
        self,
        satellites: List[Satellite],
        observer_position: Position,
        time: datetime,
        min_elevation: float = 25.0
    ) -> Dict[str, bool]:
        """批次計算衛星可見性
        
        Args:
            satellites: 衛星列表
            observer_position: 觀測者位置
            time: 計算時間
            min_elevation: 最小仰角
            
        Returns:
            Dict[str, bool]: 衛星 ID 到可見性的映射
        """
        visibility_map = {}
        
        # 使用執行緒池並行計算
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任務
            future_to_sat = {
                executor.submit(
                    self._calculate_visibility,
                    sat, observer_position, time, min_elevation
                ): sat
                for sat in satellites
            }
            
            # 收集結果
            for future in future_to_sat:
                sat = future_to_sat[future]
                try:
                    is_visible = future.result()
                    visibility_map[sat.satellite_id] = is_visible
                except Exception as e:
                    logger.error(f"可見性計算錯誤 {sat.satellite_id}: {e}")
                    visibility_map[sat.satellite_id] = False
        
        return visibility_map
    
    async def calculate_positions_batch_async(
        self,
        satellites: List[Satellite],
        time: datetime
    ) -> BatchResult:
        """異步批次計算衛星位置
        
        Args:
            satellites: 衛星列表
            time: 計算時間
            
        Returns:
            BatchResult: 批次處理結果
        """
        start_time = datetime.now()
        
        # 建立異步任務
        tasks = [
            self._calculate_position_async(sat, time)
            for sat in satellites
        ]
        
        # 並行執行所有任務
        results_with_errors = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 分離成功和失敗的結果
        results = []
        errors = []
        
        for i, result in enumerate(results_with_errors):
            if isinstance(result, Exception):
                errors.append({
                    "satellite_id": satellites[i].satellite_id,
                    "error": str(result)
                })
            else:
                results.append(result)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return BatchResult(
            successful=len(results),
            failed=len(errors),
            total_time=total_time,
            results=results,
            errors=errors
        )
    
    def _create_batches(self, items: List[Any], batch_size: int) -> List[List[Any]]:
        """將項目分成批次
        
        Args:
            items: 要分批的項目
            batch_size: 批次大小
            
        Returns:
            List[List[Any]]: 批次列表
        """
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i:i + batch_size])
        return batches
    
    def _process_position_batch(
        self,
        satellites: List[Satellite],
        time: datetime
    ) -> List[Tuple[str, Position]]:
        """處理一批衛星的位置計算
        
        Args:
            satellites: 衛星批次
            time: 計算時間
            
        Returns:
            List[Tuple[str, Position]]: (衛星ID, 位置) 列表
        """
        results = []
        for sat in satellites:
            try:
                position = self.orbit_calculator.calculate_position(sat, time)
                results.append((sat.satellite_id, position))
            except Exception as e:
                logger.error(f"計算衛星 {sat.satellite_id} 位置失敗: {e}")
                # 可以選擇拋出例外或繼續處理
                raise
        return results
    
    def _calculate_visibility(
        self,
        satellite: Satellite,
        observer_position: Position,
        time: datetime,
        min_elevation: float
    ) -> bool:
        """計算單個衛星的可見性
        
        Args:
            satellite: 衛星
            observer_position: 觀測者位置
            time: 計算時間
            min_elevation: 最小仰角
            
        Returns:
            bool: 是否可見
        """
        if not satellite.is_active:
            return False
            
        try:
            azimuth, elevation, distance = self.orbit_calculator.calculate_pass_details(
                satellite, observer_position, time
            )
            return elevation >= min_elevation
        except Exception:
            return False
    
    async def _calculate_position_async(
        self,
        satellite: Satellite,
        time: datetime
    ) -> Tuple[str, Position]:
        """異步計算衛星位置
        
        Args:
            satellite: 衛星
            time: 計算時間
            
        Returns:
            Tuple[str, Position]: (衛星ID, 位置)
        """
        # 在異步環境中運行同步計算
        loop = asyncio.get_event_loop()
        position = await loop.run_in_executor(
            None,
            self.orbit_calculator.calculate_position,
            satellite,
            time
        )
        return (satellite.satellite_id, position)
    
    def optimize_batch_size(
        self,
        satellites: List[Satellite],
        time: datetime,
        test_sizes: List[int] = None
    ) -> int:
        """優化批次大小
        
        通過測試不同的批次大小來找出最佳值
        
        Args:
            satellites: 測試用衛星列表
            time: 計算時間
            test_sizes: 要測試的批次大小列表
            
        Returns:
            int: 最佳批次大小
        """
        if test_sizes is None:
            test_sizes = [50, 100, 200, 500, 1000]
        
        # 只使用部分衛星進行測試
        test_satellites = satellites[:min(1000, len(satellites))]
        
        best_size = self.batch_size
        best_time = float('inf')
        
        for size in test_sizes:
            self.batch_size = size
            result = self.calculate_positions_batch(test_satellites, time)
            
            if result.total_time < best_time:
                best_time = result.total_time
                best_size = size
            
            logger.info(f"批次大小 {size}: {result.total_time:.2f} 秒")
        
        self.batch_size = best_size
        logger.info(f"最佳批次大小: {best_size}")
        
        return best_size