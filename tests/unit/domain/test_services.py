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

        coverage = analyzer.analyze(
            satellites=[],
            observer=sample_observer,
            start_time=start_time,
            end_time=end_time,
            time_step_minutes=60,
            elevation_mask=25.0,
        )

        assert isinstance(coverage, Coverage)
        assert coverage.observer_name == "台北101"
        assert len(coverage.coverage_windows) == 0
        assert coverage.get_statistics()["total_windows"] == 0

    def test_analyze_single_pass(self, mock_orbit_calculator, sample_satellites, sample_observer):
        """測試單次通過的分析"""
        # 設置模擬：只有一顆衛星有一次通過
        mock_orbit_calculator.calculate_pass.side_effect = [
            # 第一顆衛星有一次通過
            [(datetime(2025, 1, 1, 0, 10, 0, tzinfo=timezone.utc), datetime(2025, 1, 1, 0, 20, 0, tzinfo=timezone.utc), 45.0)],
            # 其他衛星沒有通過
            [],
            [],
        ]

        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)

        coverage = analyzer.analyze(
            satellites=sample_satellites,
            observer=sample_observer,
            start_time=start_time,
            end_time=end_time,
            time_step_minutes=60,
            elevation_mask=25.0,
        )

        assert len(coverage.coverage_windows) == 1
        window = coverage.coverage_windows[0]
        assert window.satellite_id == "SAT-0"
        assert window.duration_minutes == 10.0
        assert window.max_elevation == 45.0

    def test_analyze_multiple_passes(self, mock_orbit_calculator, sample_satellites, sample_observer):
        """測試多次通過的分析"""
        # 設置模擬：多顆衛星有多次通過
        mock_orbit_calculator.calculate_pass.side_effect = [
            # 第一顆衛星有兩次通過
            [
                (
                    datetime(2025, 1, 1, 0, 10, 0, tzinfo=timezone.utc),
                    datetime(2025, 1, 1, 0, 20, 0, tzinfo=timezone.utc),
                    45.0,
                ),
                (
                    datetime(2025, 1, 1, 0, 40, 0, tzinfo=timezone.utc),
                    datetime(2025, 1, 1, 0, 50, 0, tzinfo=timezone.utc),
                    50.0,
                ),
            ],
            # 第二顆衛星有一次通過
            [(datetime(2025, 1, 1, 0, 30, 0, tzinfo=timezone.utc), datetime(2025, 1, 1, 0, 35, 0, tzinfo=timezone.utc), 60.0)],
            # 第三顆衛星沒有通過
            [],
        ]

        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)

        coverage = analyzer.analyze(
            satellites=sample_satellites,
            observer=sample_observer,
            start_time=start_time,
            end_time=end_time,
            time_step_minutes=60,
            elevation_mask=25.0,
        )

        assert len(coverage.coverage_windows) == 3

        stats = coverage.get_statistics()
        assert stats["total_windows"] == 3
        assert stats["unique_satellites"] == 2
        assert stats["total_coverage_minutes"] == 25.0  # 10 + 10 + 5

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

        mock_orbit_calculator.calculate_pass.side_effect = mock_calculate_pass

        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 1, 1, 3, 0, 0, tzinfo=timezone.utc)  # 3小時

        coverage = analyzer.analyze(
            satellites=sample_satellites[:1],  # 只用一顆衛星
            observer=sample_observer,
            start_time=start_time,
            end_time=end_time,
            time_step_minutes=60,  # 每小時分析一次
            elevation_mask=25.0,
        )

        # 應該有兩個時間段的覆蓋（0-1小時和1-2小時）
        assert len(coverage.coverage_windows) == 2

    def test_coverage_overlap_handling(self, mock_orbit_calculator, sample_satellites, sample_observer):
        """測試覆蓋重疊處理"""
        # 設置重疊的通過時間
        mock_orbit_calculator.calculate_pass.side_effect = [
            # 第一顆衛星
            [(datetime(2025, 1, 1, 0, 10, 0, tzinfo=timezone.utc), datetime(2025, 1, 1, 0, 30, 0, tzinfo=timezone.utc), 45.0)],
            # 第二顆衛星 - 部分重疊
            [(datetime(2025, 1, 1, 0, 20, 0, tzinfo=timezone.utc), datetime(2025, 1, 1, 0, 40, 0, tzinfo=timezone.utc), 50.0)],
            # 第三顆衛星 - 完全重疊
            [(datetime(2025, 1, 1, 0, 15, 0, tzinfo=timezone.utc), datetime(2025, 1, 1, 0, 25, 0, tzinfo=timezone.utc), 55.0)],
        ]

        analyzer = CoverageAnalyzer(mock_orbit_calculator)

        coverage = analyzer.analyze(
            satellites=sample_satellites,
            observer=sample_observer,
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            time_step_minutes=60,
            elevation_mask=25.0,
        )

        # 所有通過都應該被記錄
        assert len(coverage.coverage_windows) == 3

        # 檢查覆蓋百分比計算是否正確處理重疊
        stats = coverage.get_statistics()
        # 實際覆蓋時間是 0:10-0:40 = 30分鐘
        # 但總覆蓋分鐘數應該是所有窗口的總和
        assert stats["total_coverage_minutes"] == 50.0  # 20 + 20 + 10
