"""領域服務的單元測試"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock
from src.domain.services.coverage_analyzer import CoverageAnalyzer
from src.domain.services.orbit_calculator import OrbitCalculator
from src.domain.entities.satellite import Satellite
from src.domain.entities.observer import Observer
from src.domain.entities.coverage import Coverage, CoverageWindow
from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements


class TestCoverageAnalyzer:
    """測試覆蓋分析器"""

    @pytest.fixture
    def mock_orbit_calculator(self):
        """模擬軌道計算器"""
        return Mock(spec=OrbitCalculator)

    @pytest.fixture
    def sample_satellites(self):
        """樣本衛星列表"""
        satellites = []
        for i in range(3):
            satellite = Satellite(
                satellite_id=f"SAT-{i}",
                name=f"Satellite-{i}",
                orbital_elements=OrbitalElements(
                    epoch=datetime.now(timezone.utc),
                    inclination=53.0,
                    raan=i * 120.0,
                    eccentricity=0.0001,
                    arg_perigee=0.0,
                    mean_anomaly=0.0,
                    mean_motion=15.06390000,  # 約 95 分鐘週期
                    bstar=0.00012345,
                ),
                is_active=True,
            )
            satellites.append(satellite)
        return satellites

    @pytest.fixture
    def sample_observer(self):
        """樣本觀察者"""
        return Observer(
            observer_id="taipei-101", name="台北101", position=Position(latitude=25.0330, longitude=121.5654, elevation=0.0)
        )

    def test_analyze_no_satellites(self, mock_orbit_calculator, sample_observer):
        """測試沒有衛星的分析"""
        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)

        coverage = analyzer.analyze_coverage(
            satellites=[],
            observer=sample_observer,
            start_time=start_time,
            duration_minutes=60,
            interval_minutes=60,
        )

        assert isinstance(coverage, Coverage)
        assert coverage.observer_name == "台北101"
        assert len(coverage.snapshots) > 0  # 會有時間系列快照

    def test_analyze_single_pass(self, mock_orbit_calculator, sample_satellites, sample_observer):
        """測試單次通過的分析"""
        # 設置模擬：第一顆衛星可見，其他不可見
        def mock_pass_details(satellite, observer_pos, time):
            if satellite.satellite_id == "SAT-0":
                return (180.0, 45.0, 500.0)  # 方位角, 仰角, 距離
            else:
                return (0.0, -10.0, 2000.0)  # 仰角為負，不可見
        
        mock_orbit_calculator.calculate_pass_details.side_effect = mock_pass_details
        mock_orbit_calculator.is_sunlit.return_value = True

        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)

        coverage = analyzer.analyze_coverage(
            satellites=sample_satellites,
            observer=sample_observer,
            start_time=start_time,
            duration_minutes=60,
            interval_minutes=60,
        )

        # 檢查快照而不是 coverage_windows
        assert len(coverage.snapshots) > 0
        # 第一顆衛星應該在某些時間點可見
        visible_snapshots = [s for s in coverage.snapshots if s.visible_count > 0]
        assert len(visible_snapshots) > 0

    def test_analyze_multiple_passes(self, mock_orbit_calculator, sample_satellites, sample_observer):
        """測試多次通過的分析"""
        # 設置模擬：多顆衛星在不同時間可見
        call_count = 0
        
        def mock_pass_details(satellite, observer_pos, time):
            nonlocal call_count
            call_count += 1
            # 模擬不同衛星在不同時間的可見性
            if satellite.satellite_id == "SAT-0":
                return (180.0, 45.0, 500.0)
            elif satellite.satellite_id == "SAT-1":
                return (90.0, 60.0, 400.0)
            else:
                return (0.0, -10.0, 2000.0)
        
        mock_orbit_calculator.calculate_pass_details.side_effect = mock_pass_details
        mock_orbit_calculator.is_sunlit.return_value = True

        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)

        coverage = analyzer.analyze_coverage(
            satellites=sample_satellites,
            observer=sample_observer,
            start_time=start_time,
            duration_minutes=60,
            interval_minutes=60,
        )

        # 檢查快照中的可見衛星
        assert len(coverage.snapshots) > 0
        visible_snapshots = [s for s in coverage.snapshots if s.visible_count > 0]
        assert len(visible_snapshots) > 0
        # 應該有多顆衛星可見
        max_visible = max(s.visible_count for s in coverage.snapshots)
        assert max_visible >= 2  # 至少有兩顆衛星同時可見

    def test_analyze_with_time_steps(self, mock_orbit_calculator, sample_satellites, sample_observer):
        """測試使用時間步長的分析"""

        # 每個時間段返回不同的通過
        def mock_calculate_pass(satellite, observer, start, end, elevation_mask):
            # 根據開始時間返回不同的結果
            if start.hour == 0:
                return [(start + timedelta(minutes=10), start + timedelta(minutes=20), 40.0)]
            elif start.hour == 1:
                return [(start + timedelta(minutes=5), start + timedelta(minutes=15), 50.0)]
            else:
                return []

        mock_orbit_calculator.calculate_pass_details.side_effect = mock_calculate_pass

        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 1, 1, 3, 0, 0, tzinfo=timezone.utc)  # 3小時

        coverage = analyzer.analyze_coverage(
            satellites=sample_satellites[:1],  # 只用一顆衛星
            observer=sample_observer,
            start_time=start_time,
            duration_minutes=180,  # 3小時
            interval_minutes=60,  # 每小時分析一次
        )

        # 應該有多個時間快照
        assert len(coverage.snapshots) == 4  # 0, 1, 2, 3 小時

    def test_coverage_overlap_handling(self, mock_orbit_calculator, sample_satellites, sample_observer):
        """測試覆蓋重疊處理"""
        # 設置所有衛星在不同時間段可見
        def mock_pass_details(satellite, observer_pos, time):
            minute = time.minute
            if satellite.satellite_id == "SAT-0" and 10 <= minute <= 30:
                return (180.0, 45.0, 500.0)
            elif satellite.satellite_id == "SAT-1" and 20 <= minute <= 40:
                return (90.0, 50.0, 450.0)
            elif satellite.satellite_id == "SAT-2" and 15 <= minute <= 25:
                return (270.0, 55.0, 400.0)
            else:
                return (0.0, -10.0, 2000.0)
        
        mock_orbit_calculator.calculate_pass_details.side_effect = mock_pass_details
        mock_orbit_calculator.is_sunlit.return_value = True

        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        coverage = analyzer.analyze_coverage(
            satellites=sample_satellites,
            observer=sample_observer,
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            interval_minutes=5,  # 每5分鐘分析一次
        )

        # 檢查在重疊時間段內的衛星可見性
        visible_snapshots = [s for s in coverage.snapshots if s.visible_count > 0]
        assert len(visible_snapshots) > 0
        
        # 在 20-25 分鐘時間段內，三顆衛星都可見
        overlapping_snapshots = [s for s in coverage.snapshots if 20 <= s.timestamp.minute <= 25]
        max_overlap = max(s.visible_count for s in overlapping_snapshots if s.visible_count > 0)
        assert max_overlap == 3  # 三顆衛星同時可見
