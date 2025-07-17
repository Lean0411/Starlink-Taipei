"""
Redis 快取整合測試
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock

from src.infrastructure.cache.redis_cache_service import RedisCacheService, REDIS_AVAILABLE
from src.infrastructure.cache.memory_cache_service import MemoryCacheService
from src.application.services.cached_satellite_service import CachedSatelliteService
from src.domain.services.cached_coverage_analyzer import CachedCoverageAnalyzer
from src.domain.entities.satellite import Satellite
from src.domain.entities.observer import Observer
from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements


@pytest.fixture
async def cache_service():
    """建立快取服務（優先 Redis，後備記憶體）"""
    if REDIS_AVAILABLE:
        try:
            service = RedisCacheService()
            if await service.is_connected():
                yield service
                await service.close()
                return
        except Exception:
            pass
    
    # 使用記憶體快取作為後備
    service = MemoryCacheService()
    yield service
    await service.close()


@pytest.fixture
def mock_orbit_calculator():
    """模擬軌道計算器"""
    calculator = AsyncMock()
    
    # 模擬計算位置
    calculator.calculate_position.return_value = Position(
        latitude=45.0,
        longitude=-120.0,
        altitude=550000.0
    )
    
    # 模擬計算通過細節
    calculator.calculate_pass_details.return_value = (180.0, 45.0, 1000.0)
    
    return calculator


@pytest.fixture
def sample_satellite():
    """建立測試衛星"""
    return Satellite(
        satellite_id="STARLINK-TEST",
        name="Test Satellite",
        norad_id="12345",
        orbital_elements=OrbitalElements(
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            argument_of_perigee=90.0,
            mean_anomaly=45.0,
            mean_motion=15.0,
            epoch=datetime.utcnow()
        ),
        is_active=True
    )


@pytest.fixture
def sample_observer():
    """建立測試觀測者"""
    return Observer(
        observer_id="TAIPEI-TEST",
        name="Test Observer",
        position=Position(25.0330, 121.5654, 10.0),
        min_elevation=25.0
    )


@pytest.mark.asyncio
async def test_cached_satellite_service_position(
    cache_service,
    mock_orbit_calculator,
    sample_satellite
):
    """測試衛星位置快取"""
    # 建立快取服務
    cached_service = CachedSatelliteService(mock_orbit_calculator, cache_service)
    
    calc_time = datetime.utcnow()
    
    # 第一次計算（應該呼叫計算器）
    position1 = await cached_service.calculate_position_cached(sample_satellite, calc_time)
    assert position1 is not None
    assert mock_orbit_calculator.calculate_position.call_count == 1
    
    # 第二次計算（應該從快取獲取）
    position2 = await cached_service.calculate_position_cached(sample_satellite, calc_time)
    assert position2 is not None
    assert position1.latitude == position2.latitude
    assert position1.longitude == position2.longitude
    assert position1.altitude == position2.altitude
    # 不應該再次呼叫計算器
    assert mock_orbit_calculator.calculate_position.call_count == 1


@pytest.mark.asyncio
async def test_cached_satellite_service_batch(
    cache_service,
    mock_orbit_calculator,
    sample_satellite
):
    """測試批次位置計算快取"""
    # 建立多個衛星
    satellites = []
    for i in range(5):
        sat = Satellite(
            satellite_id=f"STARLINK-TEST-{i}",
            name=f"Test Satellite {i}",
            norad_id=f"1234{i}",
            orbital_elements=sample_satellite.orbital_elements,
            is_active=True
        )
        satellites.append(sat)
    
    cached_service = CachedSatelliteService(mock_orbit_calculator, cache_service)
    calc_time = datetime.utcnow()
    
    # 第一次批次計算
    positions1 = await cached_service.calculate_positions_batch_cached(satellites, calc_time)
    assert len(positions1) == 5
    assert all(pos is not None for pos in positions1.values())
    assert mock_orbit_calculator.calculate_position.call_count == 5
    
    # 重置呼叫計數
    mock_orbit_calculator.calculate_position.reset_mock()
    
    # 第二次批次計算（應該全部從快取獲取）
    positions2 = await cached_service.calculate_positions_batch_cached(satellites, calc_time)
    assert len(positions2) == 5
    # 不應該呼叫計算器
    assert mock_orbit_calculator.calculate_position.call_count == 0


@pytest.mark.asyncio
async def test_cached_coverage_analyzer(
    cache_service,
    mock_orbit_calculator,
    sample_satellite,
    sample_observer
):
    """測試覆蓋率分析快取"""
    # 建立快取分析器
    cached_analyzer = CachedCoverageAnalyzer(mock_orbit_calculator, cache_service)
    
    satellites = [sample_satellite]
    start_time = datetime.utcnow()
    
    # 第一次分析
    analysis1 = await cached_analyzer.analyze_coverage_cached(
        satellites,
        sample_observer,
        start_time,
        duration_minutes=10,
        interval_minutes=1
    )
    
    assert analysis1 is not None
    assert len(analysis1.snapshots) > 0
    
    # 第二次分析（應該從快取獲取）
    analysis2 = await cached_analyzer.analyze_coverage_cached(
        satellites,
        sample_observer,
        start_time,
        duration_minutes=10,
        interval_minutes=1
    )
    
    assert analysis2 is not None
    # 應該返回相同的結果
    assert len(analysis1.snapshots) == len(analysis2.snapshots)
    assert analysis1.statistics.average_visible_count == analysis2.statistics.average_visible_count


@pytest.mark.asyncio
async def test_cache_invalidation(
    cache_service,
    mock_orbit_calculator,
    sample_satellite
):
    """測試快取失效"""
    cached_service = CachedSatelliteService(mock_orbit_calculator, cache_service)
    
    calc_time = datetime.utcnow()
    
    # 計算位置（儲存到快取）
    await cached_service.calculate_position_cached(sample_satellite, calc_time)
    
    # 清除快取
    await cached_service.clear_position_cache(sample_satellite.satellite_id)
    
    # 重置呼叫計數
    mock_orbit_calculator.calculate_position.reset_mock()
    
    # 再次計算（應該重新計算而不是從快取獲取）
    await cached_service.calculate_position_cached(sample_satellite, calc_time)
    assert mock_orbit_calculator.calculate_position.call_count == 1


@pytest.mark.asyncio
async def test_cache_ttl():
    """測試快取過期時間"""
    # 使用記憶體快取以便控制測試
    cache_service = MemoryCacheService()
    
    # 設定短 TTL
    await cache_service.set("test_key", "test_value", ttl=1)
    
    # 立即獲取應該成功
    value = await cache_service.get("test_key")
    assert value == "test_value"
    
    # 等待過期
    await asyncio.sleep(1.1)
    
    # 應該返回 None
    value = await cache_service.get("test_key")
    assert value is None
    
    await cache_service.close()


@pytest.mark.asyncio
async def test_cache_pattern_clear():
    """測試模式匹配清除"""
    cache_service = MemoryCacheService()
    
    # 設定多個相關的鍵
    await cache_service.set("prefix:key1", "value1")
    await cache_service.set("prefix:key2", "value2")
    await cache_service.set("other:key3", "value3")
    
    # 清除符合模式的鍵
    count = await cache_service.clear_pattern("prefix:*")
    assert count == 2
    
    # 檢查結果
    assert await cache_service.get("prefix:key1") is None
    assert await cache_service.get("prefix:key2") is None
    assert await cache_service.get("other:key3") == "value3"
    
    await cache_service.close()