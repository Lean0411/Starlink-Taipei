"""
領域實體的單元測試
"""

from datetime import datetime
import pytest

from src.domain.entities.satellite import Satellite
from src.domain.entities.observer import Observer
from src.domain.entities.coverage_analysis import (
    CoverageSnapshot, CoverageStatistics, OptimalWindow, CoverageAnalysis
)
from src.domain.value_objects.orbital_elements import OrbitalElements
from src.domain.value_objects.position import Position


class TestSatellite:
    """衛星實體測試"""
    
    def test_satellite_creation(self):
        """測試衛星建立"""
        orbital_elements = OrbitalElements(
            epoch=datetime(2024, 1, 1),
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        satellite = Satellite(
            satellite_id="SAT123",
            name="Test Satellite",
            orbital_elements=orbital_elements,
            launch_date=datetime(2023, 1, 1),
            is_active=True
        )
        
        assert satellite.satellite_id == "SAT123"
        assert satellite.name == "Test Satellite"
        assert satellite.orbital_elements == orbital_elements
        assert satellite.launch_date == datetime(2023, 1, 1)
        assert satellite.is_active is True
    
    def test_satellite_calculate_position_not_implemented(self):
        """測試衛星位置計算未實作"""
        orbital_elements = OrbitalElements(
            epoch=datetime(2024, 1, 1),
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        satellite = Satellite(
            satellite_id="SAT123",
            name="Test Satellite",
            orbital_elements=orbital_elements
        )
        
        with pytest.raises(NotImplementedError) as exc_info:
            satellite.calculate_position_at(datetime.now())
        
        assert "OrbitCalculator.calculate_position" in str(exc_info.value)
    
    def test_satellite_equality(self):
        """測試衛星相等性"""
        orbital_elements = OrbitalElements(
            epoch=datetime(2024, 1, 1),
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        sat1 = Satellite("SAT123", "Test 1", orbital_elements)
        sat2 = Satellite("SAT123", "Test 2", orbital_elements)
        sat3 = Satellite("SAT456", "Test 3", orbital_elements)
        
        assert sat1 == sat2  # 相同 ID
        assert sat1 != sat3  # 不同 ID
        assert sat1 != "not a satellite"
    
    def test_satellite_hash(self):
        """測試衛星雜湊值"""
        orbital_elements = OrbitalElements(
            epoch=datetime(2024, 1, 1),
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        sat1 = Satellite("SAT123", "Test", orbital_elements)
        sat2 = Satellite("SAT123", "Test", orbital_elements)
        
        assert hash(sat1) == hash(sat2)
        
        # 可以放入集合
        satellite_set = {sat1, sat2}
        assert len(satellite_set) == 1


class TestObserver:
    """觀測者實體測試"""
    
    def test_observer_creation(self):
        """測試觀測者建立"""
        position = Position(latitude=25.0330, longitude=121.5654, elevation=10.0)
        observer = Observer(
            observer_id="OBS1",
            name="Taipei Observer",
            position=position,
            min_elevation=25.0
        )
        
        assert observer.observer_id == "OBS1"
        assert observer.name == "Taipei Observer"
        assert observer.position == position
        assert observer.min_elevation == 25.0
    
    def test_observer_default_min_elevation(self):
        """測試預設最小仰角"""
        position = Position(latitude=25.0330, longitude=121.5654, elevation=10.0)
        observer = Observer(
            observer_id="OBS1",
            name="Taipei Observer",
            position=position
        )
        
        assert observer.min_elevation == 10.0  # 預設值


class TestCoverageAnalysis:
    """覆蓋率分析實體測試"""
    
    def test_coverage_snapshot_creation(self):
        """測試覆蓋快照建立"""
        positions = {
            "SAT1": Position(0, 0, 500000),
            "SAT2": Position(10, 20, 550000)
        }
        
        snapshot = CoverageSnapshot(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            visible_satellites=["SAT1", "SAT2"],
            satellite_positions=positions
        )
        
        assert snapshot.timestamp == datetime(2024, 1, 1, 12, 0, 0)
        assert snapshot.visible_count == 2
        assert "SAT1" in snapshot.visible_satellites
        assert "SAT2" in snapshot.visible_satellites
    
    def test_coverage_statistics_from_snapshots(self):
        """測試從快照計算統計"""
        snapshots = [
            CoverageSnapshot(
                timestamp=datetime(2024, 1, 1, 12, 0),
                visible_satellites=["SAT1", "SAT2"],
                satellite_positions={}
            ),
            CoverageSnapshot(
                timestamp=datetime(2024, 1, 1, 12, 1),
                visible_satellites=["SAT1", "SAT2", "SAT3"],
                satellite_positions={}
            ),
            CoverageSnapshot(
                timestamp=datetime(2024, 1, 1, 12, 2),
                visible_satellites=["SAT2"],
                satellite_positions={}
            ),
            CoverageSnapshot(
                timestamp=datetime(2024, 1, 1, 12, 3),
                visible_satellites=[],
                satellite_positions={}
            )
        ]
        
        stats = CoverageStatistics.from_snapshots(snapshots, 60)
        
        assert stats.duration_minutes == 60
        assert stats.average_visible_count == 1.5  # (2+3+1+0)/4
        assert stats.max_visible_count == 3
        assert stats.min_visible_count == 0
        assert stats.coverage_percentage == 75.0  # 3/4 * 100
        assert stats.total_snapshots == 4
    
    def test_coverage_statistics_empty_snapshots(self):
        """測試空快照的統計"""
        stats = CoverageStatistics.from_snapshots([], 60)
        
        assert stats.duration_minutes == 60
        assert stats.average_visible_count == 0.0
        assert stats.max_visible_count == 0
        assert stats.min_visible_count == 0
        assert stats.coverage_percentage == 0.0
        assert stats.total_snapshots == 0
    
    def test_optimal_window(self):
        """測試最佳觀測窗口"""
        window = OptimalWindow(
            start_time=datetime(2024, 1, 1, 12, 0),
            end_time=datetime(2024, 1, 1, 13, 30),
            avg_satellites=25.5,
            max_elevation=85.0
        )
        
        assert window.duration_minutes == 90
        assert window.avg_satellites == 25.5
        assert window.max_elevation == 85.0
    
    def test_coverage_analysis_creation(self):
        """測試覆蓋率分析建立"""
        position = Position(25.0330, 121.5654, 10.0)
        observer = Observer("OBS1", "Taipei", position)
        
        analysis = CoverageAnalysis(
            observer=observer,
            start_time=datetime(2024, 1, 1, 12, 0),
            end_time=datetime(2024, 1, 1, 13, 0),
            analyzed_satellites=["SAT1", "SAT2", "SAT3"]
        )
        
        assert analysis.coverage_id is not None
        assert len(analysis.coverage_id) == 36  # UUID 格式
        assert analysis.observer == observer
        assert analysis.start_time == datetime(2024, 1, 1, 12, 0)
        assert analysis.end_time == datetime(2024, 1, 1, 13, 0)
        assert len(analysis.analyzed_satellites) == 3
    
    def test_coverage_analysis_add_snapshot(self):
        """測試添加快照"""
        analysis = CoverageAnalysis()
        
        snapshot = CoverageSnapshot(
            timestamp=datetime(2024, 1, 1, 12, 0),
            visible_satellites=["SAT1"],
            satellite_positions={}
        )
        
        analysis.add_snapshot(snapshot)
        
        assert len(analysis.snapshots) == 1
        assert analysis.snapshots[0] == snapshot
    
    def test_coverage_analysis_auto_statistics(self):
        """測試自動計算統計"""
        snapshots = [
            CoverageSnapshot(
                timestamp=datetime(2024, 1, 1, 12, 0),
                visible_satellites=["SAT1", "SAT2"],
                satellite_positions={}
            )
        ]
        
        analysis = CoverageAnalysis(
            start_time=datetime(2024, 1, 1, 12, 0),
            end_time=datetime(2024, 1, 1, 13, 0),
            snapshots=snapshots
        )
        
        assert analysis.statistics is not None
        assert analysis.statistics.duration_minutes == 60
        assert analysis.statistics.average_visible_count == 2.0