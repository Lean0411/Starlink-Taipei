#!/usr/bin/env python3
"""
核心功能測試 - 測試預測服務的基本功能
"""

import sys
sys.path.append('.')

from datetime import datetime, timezone
from src.domain.entities.prediction import PredictionTimeScale
from src.domain.entities.satellite import Satellite
from src.domain.entities.observer import Observer
from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements
from src.infrastructure.external_services.skyfield_orbit_calculator import SkyfieldOrbitCalculator
from src.infrastructure.external_services.orbit_prediction_service import OrbitPredictionService


def create_test_satellite():
    """創建測試衛星"""
    return Satellite(
        satellite_id="TEST-SAT-1",
        name="Test Satellite 1",
        orbital_elements=OrbitalElements(
            epoch=datetime.now(timezone.utc),
            inclination=53.0,
            raan=100.0,
            eccentricity=0.0001,
            arg_perigee=0.0,
            mean_anomaly=0.0,
            mean_motion=15.06390000,  # 約 95 分鐘軌道週期
            bstar=0.00012345
        ),
        is_active=True
    )


def test_prediction_service():
    """測試預測服務"""
    print("=== 測試預測服務 ===\n")
    
    # 創建依賴
    orbit_calculator = SkyfieldOrbitCalculator()
    prediction_service = OrbitPredictionService(orbit_calculator)
    
    # 創建測試數據
    satellites = [create_test_satellite() for _ in range(3)]
    observer = Observer(
        observer_id="taipei-test",
        name="台北測試站",
        position=Position(
            latitude=25.0330,
            longitude=121.5654,
            elevation=10.0
        ),
        min_elevation=25.0
    )
    
    print("1. 測試短期預測（1小時）")
    try:
        prediction = prediction_service.predict_coverage(
            satellites=satellites,
            observer=observer,
            time_scale=PredictionTimeScale.SHORT_TERM
        )
        
        print(f"   ✓ 預測ID: {prediction.prediction_id}")
        print(f"   ✓ 時間範圍: {prediction.duration_hours} 小時")
        print(f"   ✓ 預測點數: {len(prediction.prediction_points)}")
        print(f"   ✓ 平均衛星數: {prediction.average_satellites:.1f}")
        print(f"   ✓ 覆蓋可用性: {prediction.coverage_availability:.1f}%")
        
        if prediction.optimal_windows:
            print(f"   ✓ 最佳觀測窗口: {len(prediction.optimal_windows)} 個")
            for i, window in enumerate(prediction.optimal_windows[:3]):
                print(f"      窗口 {i+1}: {window.duration_minutes} 分鐘, 平均 {window.avg_satellites:.1f} 顆衛星")
    except Exception as e:
        print(f"   ✗ 錯誤: {e}")
    
    print("\n2. 測試不確定性計算")
    try:
        base_time = datetime.now(timezone.utc)
        
        # 1小時後的不確定性
        uncertainty_1h = prediction_service.calculate_prediction_uncertainty(
            prediction_time=datetime.now(timezone.utc).replace(hour=(datetime.now().hour + 1) % 24),
            base_time=base_time
        )
        print(f"   ✓ 1小時後不確定性: {uncertainty_1h}")
        
        # 24小時後的不確定性
        uncertainty_24h = prediction_service.calculate_prediction_uncertainty(
            prediction_time=datetime.now(timezone.utc).replace(day=datetime.now().day + 1),
            base_time=base_time
        )
        print(f"   ✓ 24小時後不確定性: {uncertainty_24h}")
        
    except Exception as e:
        print(f"   ✗ 錯誤: {e}")
    
    print("\n=== 測試完成 ===")


def test_domain_entities():
    """測試領域實體"""
    print("\n=== 測試領域實體 ===\n")
    
    # 測試位置值物件
    print("1. 測試位置值物件")
    try:
        pos1 = Position(latitude=25.0330, longitude=121.5654, elevation=10.0)
        pos2 = Position(latitude=35.6762, longitude=139.6503, elevation=0.0)
        distance = pos1.distance_to(pos2)
        print(f"   ✓ 台北到東京距離: {distance:.0f} km")
    except Exception as e:
        print(f"   ✗ 錯誤: {e}")
    
    # 測試軌道要素
    print("\n2. 測試軌道要素")
    try:
        orbital = OrbitalElements(
            epoch=datetime.now(timezone.utc),
            inclination=53.0,
            raan=100.0,
            eccentricity=0.0001,
            arg_perigee=0.0,
            mean_anomaly=0.0,
            mean_motion=15.06390000,
            bstar=0.00012345
        )
        print(f"   ✓ 軌道週期: {orbital.period_minutes:.1f} 分鐘")
        print(f"   ✓ 是否為LEO: {orbital.is_low_earth_orbit}")
    except Exception as e:
        print(f"   ✗ 錯誤: {e}")


if __name__ == "__main__":
    test_domain_entities()
    print("\n" + "="*50 + "\n")
    test_prediction_service()