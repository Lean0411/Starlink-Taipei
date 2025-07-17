#!/usr/bin/env python3
"""
效能測試 - 比較優化前後的處理速度
"""

import time
from datetime import datetime, timedelta
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.container.container import get_container
from src.domain.entities.observer import Observer
from src.domain.value_objects.position import Position
from src.domain.services.coverage_analyzer import CoverageAnalyzer
from src.domain.services.optimized_coverage_analyzer import OptimizedCoverageAnalyzer
from src.application.services.batch_processing_service import BatchProcessingService


def test_performance():
    """測試效能提升"""
    print("=== 衛星覆蓋率分析效能測試 ===\n")
    
    # 獲取依賴
    container = get_container()
    satellite_repo = container.resolve("satellite_repository")
    orbit_calculator = container.resolve("orbit_calculator")
    
    # 建立觀測者（台北）
    observer = Observer(
        observer_id="TAIPEI",
        name="Taipei Observer",
        position=Position(25.0330, 121.5654, 10.0),
        min_elevation=25.0
    )
    
    # 設定分析參數
    start_time = datetime.utcnow()
    duration_minutes = 60  # 1小時
    interval_minutes = 1   # 每分鐘
    
    print("載入衛星資料...")
    satellites = satellite_repo.get_active_satellites()
    print(f"活躍衛星數量: {len(satellites)}\n")
    
    # 測試不同數量的衛星
    test_sizes = [100, 500, 1000, 2000]
    
    for size in test_sizes:
        if size > len(satellites):
            continue
            
        test_satellites = satellites[:size]
        print(f"\n--- 測試 {size} 顆衛星 ---")
        
        # 1. 測試原始分析器
        print("使用原始分析器...")
        original_analyzer = CoverageAnalyzer(orbit_calculator)
        
        start = time.time()
        try:
            result1 = original_analyzer.analyze_coverage(
                test_satellites,
                observer,
                start_time,
                duration_minutes,
                interval_minutes
            )
            time1 = time.time() - start
            print(f"  完成時間: {time1:.2f} 秒")
            print(f"  平均可見衛星: {result1.statistics.average_visible_count:.1f}")
        except Exception as e:
            print(f"  錯誤: {e}")
            time1 = None
        
        # 2. 測試優化分析器
        print("使用優化分析器...")
        batch_processor = BatchProcessingService(orbit_calculator, batch_size=100)
        optimized_analyzer = OptimizedCoverageAnalyzer(orbit_calculator, batch_processor)
        
        start = time.time()
        try:
            result2 = optimized_analyzer.analyze_coverage(
                test_satellites,
                observer,
                start_time,
                duration_minutes,
                interval_minutes
            )
            time2 = time.time() - start
            print(f"  完成時間: {time2:.2f} 秒")
            print(f"  平均可見衛星: {result2.statistics.average_visible_count:.1f}")
            
            if time1:
                speedup = time1 / time2
                print(f"  \033[92m效能提升: {speedup:.2f}x\033[0m")
        except Exception as e:
            print(f"  錯誤: {e}")
    
    # 測試批次大小優化
    print("\n\n--- 批次大小優化測試 ---")
    if len(satellites) >= 1000:
        test_satellites = satellites[:1000]
        print(f"使用 {len(test_satellites)} 顆衛星進行測試")
        
        batch_processor = BatchProcessingService(orbit_calculator)
        print("尋找最佳批次大小...")
        
        optimal_size = batch_processor.optimize_batch_size(
            test_satellites,
            start_time,
            [50, 100, 200, 500, 1000]
        )
        
        print(f"\n最佳批次大小: {optimal_size}")
    
    # 測試最大規模
    print("\n\n--- 最大規模測試 ---")
    print(f"測試所有 {len(satellites)} 顆衛星...")
    
    batch_processor = BatchProcessingService(orbit_calculator, batch_size=500)
    optimized_analyzer = OptimizedCoverageAnalyzer(orbit_calculator, batch_processor)
    optimized_analyzer.optimize_for_large_constellation()
    
    start = time.time()
    try:
        # 只分析 30 分鐘以加快測試
        result = optimized_analyzer.analyze_coverage(
            satellites,
            observer,
            start_time,
            30,  # 30 分鐘
            5    # 每 5 分鐘
        )
        total_time = time.time() - start
        
        print(f"\n完成！")
        print(f"  總時間: {total_time:.2f} 秒")
        print(f"  處理速度: {len(satellites) / total_time:.1f} 顆衛星/秒")
        print(f"  平均可見衛星: {result.statistics.average_visible_count:.1f}")
        print(f"  最大可見衛星: {result.statistics.max_visible_count}")
        print(f"  覆蓋率: {result.statistics.coverage_percentage:.1f}%")
        
        # 尋找最佳觀測窗口
        windows = optimized_analyzer.find_optimal_windows_optimized(result)
        if windows:
            print(f"\n找到 {len(windows)} 個最佳觀測窗口:")
            for i, window in enumerate(windows[:3]):  # 顯示前3個
                print(f"  {i+1}. {window.start_time.strftime('%H:%M')} - {window.end_time.strftime('%H:%M')}")
                print(f"     平均衛星數: {window.avg_satellites:.1f}")
                print(f"     持續時間: {window.duration_minutes} 分鐘")
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_performance()