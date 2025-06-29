"""領域實體的單元測試"""

import pytest
from datetime import datetime, timezone
from src.domain.entities.satellite import Satellite
from src.domain.entities.observer import Observer
from src.domain.entities.coverage import Coverage, CoverageWindow
from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements


class TestSatellite:
    """測試衛星實體"""
    
    def test_satellite_creation(self):
        """測試衛星實體創建"""
        orbital_elements = OrbitalElements(
            epoch=datetime.now(timezone.utc),
            inclination=53.0,  # degrees
            raan=0.0,  # Right Ascension of Ascending Node
            eccentricity=0.0001,
            arg_perigee=0.0,  # Argument of Perigee
            mean_anomaly=0.0,
            mean_motion=15.06390000,  # 約 95 分鐘軌道週期
            bstar=0.00012345
        )
        
        satellite = Satellite(
            satellite_id="STARLINK-1234",
            name="Starlink-1234",
            orbital_elements=orbital_elements,
            launch_date=datetime(2021, 1, 1, tzinfo=timezone.utc),
            is_active=True
        )
        
        assert satellite.satellite_id == "STARLINK-1234"
        assert satellite.name == "Starlink-1234"
        assert satellite.is_active is True
        assert satellite.launch_date.year == 2021
        assert satellite.orbital_elements.inclination == 53.0
    
    def test_satellite_inactive(self):
        """測試非活躍衛星"""
        orbital_elements = OrbitalElements(
            epoch=datetime.now(timezone.utc),
            inclination=53.0,
            raan=0.0,
            eccentricity=0.0001,
            arg_perigee=0.0,
            mean_anomaly=0.0,
            mean_motion=15.06390000,
            bstar=0.00012345
        )
        
        satellite = Satellite(
            satellite_id="STARLINK-DEAD",
            name="Starlink-Dead",
            orbital_elements=orbital_elements,
            is_active=False
        )
        
        assert satellite.is_active is False
        assert satellite.launch_date is None


class TestObserver:
    """測試觀察者實體"""
    
    def test_observer_creation(self):
        """測試觀察者創建"""
        observer = Observer(
            observer_id="taipei-101",
            name="台北101",
            position=Position(
                latitude=25.0330,
                longitude=121.5654,
                elevation=0.0
            )
        )
        
        assert observer.name == "台北101"
        assert observer.position.latitude == 25.0330
        assert observer.position.longitude == 121.5654
        assert observer.position.elevation == 0.0
    
    def test_observer_with_altitude(self):
        """測試有高度的觀察者"""
        observer = Observer(
            observer_id="yushan-station",
            name="玉山氣象站",
            position=Position(
                latitude=23.4700,
                longitude=120.9570,
                elevation=3845.0  # 玉山高度
            )
        )
        
        assert observer.position.elevation == 3845.0


class TestCoverage:
    """測試覆蓋實體"""
    
    def test_coverage_creation(self):
        """測試覆蓋實體創建"""
        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        coverage = Coverage(
            observer_name="台北101",
            start_time=start_time,
            end_time=end_time,
            elevation_mask=25.0
        )
        
        assert coverage.observer_name == "台北101"
        assert coverage.start_time == start_time
        assert coverage.end_time == end_time
        assert coverage.elevation_mask == 25.0
        assert coverage.coverage_windows == []
    
    def test_add_coverage_window(self):
        """測試添加覆蓋視窗"""
        coverage = Coverage(
            observer_name="台北101",
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            elevation_mask=25.0
        )
        
        window = CoverageWindow(
            satellite_id="STARLINK-1234",
            start_time=datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 1, 10, 0, tzinfo=timezone.utc),
            max_elevation=45.0
        )
        
        coverage.add_coverage_window(window)
        
        assert len(coverage.coverage_windows) == 1
        assert coverage.coverage_windows[0].satellite_id == "STARLINK-1234"
        assert coverage.coverage_windows[0].duration_minutes == 10.0
    
    def test_coverage_statistics(self):
        """測試覆蓋統計"""
        coverage = Coverage(
            observer_name="台北101",
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc),  # 1小時
            elevation_mask=25.0
        )
        
        # 添加兩個覆蓋視窗
        coverage.add_coverage_window(CoverageWindow(
            satellite_id="STARLINK-1234",
            start_time=datetime(2025, 1, 1, 0, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 0, 20, 0, tzinfo=timezone.utc),
            max_elevation=45.0
        ))
        
        coverage.add_coverage_window(CoverageWindow(
            satellite_id="STARLINK-5678",
            start_time=datetime(2025, 1, 1, 0, 30, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 0, 45, 0, tzinfo=timezone.utc),
            max_elevation=60.0
        ))
        
        stats = coverage.get_statistics()
        
        assert stats["total_windows"] == 2
        assert stats["unique_satellites"] == 2
        assert stats["total_coverage_minutes"] == 25.0  # 10 + 15 分鐘
        assert stats["coverage_percentage"] == pytest.approx(41.67, rel=0.01)  # 25/60 * 100


class TestCoverageWindow:
    """測試覆蓋視窗"""
    
    def test_coverage_window_duration(self):
        """測試覆蓋視窗持續時間計算"""
        window = CoverageWindow(
            satellite_id="STARLINK-1234",
            start_time=datetime(2025, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 10, 45, 30, tzinfo=timezone.utc),
            max_elevation=55.0
        )
        
        assert window.duration_minutes == pytest.approx(15.5, rel=0.01)
        assert window.max_elevation == 55.0