#!/usr/bin/env python3
"""
範例：如何計算衛星位置

這個範例展示了在 Clean Architecture 中如何正確使用衛星服務
來計算衛星位置，而不是直接在實體上調用方法。
"""

from datetime import datetime

from src.infrastructure.container.container import get_container
from src.application.services.satellite_service import SatelliteService
from src.domain.repositories.satellite_repository import SatelliteRepository
from src.domain.value_objects.position import Position


def main():
    """主程式"""
    # 獲取依賴注入容器
    container = get_container()
    
    # 解析需要的服務
    satellite_service = container.resolve(SatelliteService)
    satellite_repository = container.resolve(SatelliteRepository)
    
    # 獲取衛星（這裡用第一顆活躍的衛星作為範例）
    satellites = satellite_repository.get_active_satellites()
    
    if not satellites:
        print("沒有找到活躍的衛星")
        return
    
    satellite = satellites[0]
    print(f"衛星名稱: {satellite.name}")
    print(f"衛星 ID: {satellite.satellite_id}")
    
    # 計算當前時間的衛星位置
    current_time = datetime.utcnow()
    
    try:
        # 使用服務來計算位置（正確的方式）
        position = satellite_service.calculate_position(satellite, current_time)
        print(f"\n衛星位置 (UTC {current_time.strftime('%Y-%m-%d %H:%M:%S')}):")
        print(f"  緯度: {position.latitude:.4f}°")
        print(f"  經度: {position.longitude:.4f}°")
        print(f"  高度: {position.elevation/1000:.2f} km")
        
        # 檢查從台北是否可見
        taipei_position = Position(
            latitude=25.0330,
            longitude=121.5654,
            elevation=10.0
        )
        
        is_visible = satellite_service.is_visible(
            satellite, taipei_position, current_time
        )
        
        if is_visible:
            azimuth, elevation, distance = satellite_service.get_pass_details(
                satellite, taipei_position, current_time
            )
            print(f"\n從台北觀察:")
            print(f"  可見: 是")
            print(f"  方位角: {azimuth:.2f}°")
            print(f"  仰角: {elevation:.2f}°")
            print(f"  距離: {distance:.2f} km")
        else:
            print("\n從台北觀察: 不可見")
            
    except NotImplementedError as e:
        # 如果錯誤地直接調用實體方法，會得到這個錯誤
        print(f"\n錯誤: {e}")
        print("請使用 SatelliteService 來計算衛星位置")


if __name__ == "__main__":
    print("=== 衛星位置計算範例 ===\n")
    main()