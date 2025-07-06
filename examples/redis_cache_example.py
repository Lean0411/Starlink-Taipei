#!/usr/bin/env python3
"""
Redis 快取範例 - 展示如何使用快取來優化效能
"""

import asyncio
import time
import sys
import os
from datetime import datetime

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.container.container import get_container
from src.domain.entities.observer import Observer
from src.domain.value_objects.position import Position
from src.application.services.cached_satellite_service import CachedSatelliteService
from src.domain.services.cached_coverage_analyzer import CachedCoverageAnalyzer


async def demonstrate_position_cache():
    """示範位置計算快取"""
    print("=== 位置計算快取示範 ===\n")
    
    # 獲取依賴
    container = get_container()
    cache_service = container.resolve("cache_service")
    orbit_calculator = container.resolve("orbit_calculator")
    satellite_repo = container.resolve("satellite_repository")
    
    # 建立快取衛星服務
    cached_service = CachedSatelliteService(orbit_calculator, cache_service)
    
    # 載入衛星
    print("載入衛星資料...")
    satellites = satellite_repo.get_active_satellites()[:10]  # 使用前 10 顆
    print(f"使用 {len(satellites)} 顆衛星進行測試\n")
    
    # 計算時間
    calc_time = datetime.utcnow()
    
    # 第一次計算（無快取）
    print("第一次計算（無快取）...")
    start = time.time()
    positions1 = await cached_service.calculate_positions_batch_cached(satellites, calc_time)
    time1 = time.time() - start
    print(f"完成時間: {time1:.3f} 秒")
    print(f"成功計算: {len([p for p in positions1.values() if p is not None])} 個位置\n")
    
    # 第二次計算（有快取）
    print("第二次計算（有快取）...")
    start = time.time()
    positions2 = await cached_service.calculate_positions_batch_cached(satellites, calc_time)
    time2 = time.time() - start
    print(f"完成時間: {time2:.3f} 秒")
    print(f"效能提升: {time1/time2:.1f}x\n")
    
    # 檢查快取統計
    stats = await cached_service.get_cache_stats()
    print(f"快取統計: {stats}")


async def demonstrate_coverage_cache():
    """示範覆蓋率分析快取"""
    print("\n\n=== 覆蓋率分析快取示範 ===\n")
    
    # 獲取依賴
    container = get_container()
    cache_service = container.resolve("cache_service")
    orbit_calculator = container.resolve("orbit_calculator")
    satellite_repo = container.resolve("satellite_repository")
    
    # 建立快取分析器
    cached_analyzer = CachedCoverageAnalyzer(orbit_calculator, cache_service)
    
    # 建立觀測者（台北）
    observer = Observer(
        observer_id="TAIPEI",
        name="Taipei Observer",
        position=Position(25.0330, 121.5654, 10.0),
        min_elevation=25.0
    )
    
    # 載入衛星
    print("載入衛星資料...")
    satellites = satellite_repo.get_active_satellites()[:50]  # 使用前 50 顆
    print(f"使用 {len(satellites)} 顆衛星進行測試\n")
    
    # 分析參數
    start_time = datetime.utcnow()
    duration_minutes = 30
    interval_minutes = 5
    
    # 第一次分析（無快取）
    print("第一次分析（無快取）...")
    start = time.time()
    analysis1 = await cached_analyzer.analyze_coverage_cached(
        satellites, observer, start_time, duration_minutes, interval_minutes
    )
    time1 = time.time() - start
    print(f"完成時間: {time1:.3f} 秒")
    print(f"平均可見衛星: {analysis1.statistics.average_visible_count:.1f}")
    print(f"覆蓋率: {analysis1.statistics.coverage_percentage:.1f}%\n")
    
    # 第二次分析（有快取）
    print("第二次分析（有快取）...")
    start = time.time()
    analysis2 = await cached_analyzer.analyze_coverage_cached(
        satellites, observer, start_time, duration_minutes, interval_minutes
    )
    time2 = time.time() - start
    print(f"完成時間: {time2:.3f} 秒")
    print(f"效能提升: {time1/time2:.1f}x\n")
    
    # 尋找最佳窗口（使用快取）
    print("尋找最佳觀測窗口...")
    start = time.time()
    windows = await cached_analyzer.find_optimal_windows_cached(analysis2)
    window_time = time.time() - start
    print(f"找到 {len(windows)} 個最佳窗口，耗時: {window_time:.3f} 秒")
    
    if windows:
        print("\n前 3 個最佳窗口:")
        for i, window in enumerate(windows[:3]):
            print(f"  {i+1}. {window.start_time.strftime('%H:%M')} - {window.end_time.strftime('%H:%M')}")
            print(f"     平均衛星數: {window.avg_satellites:.1f}")


async def demonstrate_cache_invalidation():
    """示範快取失效"""
    print("\n\n=== 快取失效示範 ===\n")
    
    # 獲取依賴
    container = get_container()
    cache_service = container.resolve("cache_service")
    orbit_calculator = container.resolve("orbit_calculator")
    
    # 建立快取服務
    cached_service = CachedSatelliteService(orbit_calculator, cache_service)
    cached_analyzer = CachedCoverageAnalyzer(orbit_calculator, cache_service)
    
    # 檢查快取狀態
    print("檢查快取連線狀態...")
    is_connected = await cache_service.is_connected()
    print(f"快取服務已連線: {is_connected}")
    
    # 清除特定衛星的位置快取
    print("\n清除特定衛星的位置快取...")
    await cached_service.clear_position_cache("STARLINK-1234")
    
    # 清除所有覆蓋率分析快取
    print("清除所有覆蓋率分析快取...")
    await cached_analyzer.clear_analysis_cache()
    
    print("\n快取清除完成！")


async def main():
    """主程式"""
    try:
        # 示範位置快取
        await demonstrate_position_cache()
        
        # 示範覆蓋率快取
        await demonstrate_coverage_cache()
        
        # 示範快取失效
        await demonstrate_cache_invalidation()
        
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理資源
        container = get_container()
        cache_service = container.resolve("cache_service")
        await cache_service.close()


if __name__ == "__main__":
    print("Redis 快取整合範例")
    print("==================\n")
    print("提示: 確保 Redis 服務正在運行")
    print("如果沒有 Redis，系統會自動使用記憶體快取\n")
    
    asyncio.run(main())