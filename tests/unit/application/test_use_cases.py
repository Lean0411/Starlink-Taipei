"""應用層用例的單元測試"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from src.application.use_cases.analyze_coverage_use_case import AnalyzeCoverageUseCase
from src.application.dto.coverage_request import CoverageRequest, ObserverDTO
from src.application.dto.coverage_response import CoverageResponse
from src.domain.entities.satellite import Satellite
from src.domain.entities.observer import Observer
from src.domain.entities.coverage import Coverage, CoverageWindow
from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements


class TestAnalyzeCoverageUseCase:
    """測試覆蓋分析用例"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """模擬依賴"""
        satellite_repo = Mock()
        coverage_analyzer = Mock()
        return satellite_repo, coverage_analyzer
    
    @pytest.fixture
    def sample_request(self):
        """樣本請求"""
        return CoverageRequest(
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            time_step_minutes=60,
            elevation_mask=25.0,
            observer=ObserverDTO(
                latitude=25.0330,
                longitude=121.5654,
                altitude=0.0
            )
        )
    
    def test_execute_success(self, mock_dependencies, sample_request):
        """測試成功執行覆蓋分析"""
        satellite_repo, coverage_analyzer = mock_dependencies
        
        # 設置模擬衛星
        mock_satellites = [
            Satellite(
                satellite_id=f"STARLINK-{i}",
                name=f"Starlink-{i}",
                orbital_elements=OrbitalElements(
                    semi_major_axis=6778.137,
                    eccentricity=0.0001,
                    inclination=53.0,
                    right_ascension=i * 30.0,
                    argument_of_perigee=0.0,
                    mean_anomaly=0.0,
                    epoch=datetime.now(timezone.utc)
                ),
                is_active=True
            )
            for i in range(3)
        ]
        satellite_repo.get_active_satellites.return_value = mock_satellites
        
        # 設置模擬覆蓋結果
        mock_coverage = Coverage(
            observer_name="Observer",
            start_time=sample_request.start_time,
            end_time=sample_request.end_time,
            elevation_mask=sample_request.elevation_mask
        )
        
        # 添加覆蓋視窗
        mock_coverage.add_coverage_window(CoverageWindow(
            satellite_id="STARLINK-0",
            start_time=datetime(2025, 1, 1, 0, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 0, 20, 0, tzinfo=timezone.utc),
            max_elevation=45.0
        ))
        
        coverage_analyzer.analyze.return_value = mock_coverage
        
        # 執行用例
        use_case = AnalyzeCoverageUseCase(satellite_repo, coverage_analyzer)
        response = use_case.execute(sample_request)
        
        # 驗證結果
        assert isinstance(response, CoverageResponse)
        assert response.total_satellites == 3
        assert response.analyzed_satellites == 3
        assert len(response.coverage_windows) == 1
        assert response.coverage_windows[0].satellite_id == "STARLINK-0"
        assert response.statistics.total_windows == 1
        assert response.statistics.unique_satellites == 1
    
    def test_execute_with_no_satellites(self, mock_dependencies, sample_request):
        """測試沒有衛星的情況"""
        satellite_repo, coverage_analyzer = mock_dependencies
        
        # 沒有活躍衛星
        satellite_repo.get_active_satellites.return_value = []
        
        use_case = AnalyzeCoverageUseCase(satellite_repo, coverage_analyzer)
        response = use_case.execute(sample_request)
        
        assert response.total_satellites == 0
        assert response.analyzed_satellites == 0
        assert len(response.coverage_windows) == 0
        assert response.statistics.total_windows == 0
    
    def test_execute_with_time_steps(self, mock_dependencies):
        """測試多個時間步長的分析"""
        satellite_repo, coverage_analyzer = mock_dependencies
        
        # 創建包含多個時間步長的請求
        request = CoverageRequest(
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 3, 0, 0, tzinfo=timezone.utc),  # 3小時
            time_step_minutes=60,  # 每小時一個步長
            elevation_mask=25.0,
            observer=ObserverDTO(
                latitude=25.0330,
                longitude=121.5654,
                altitude=0.0
            )
        )
        
        # 設置模擬衛星
        mock_satellites = [
            Satellite(
                satellite_id="STARLINK-1",
                name="Starlink-1",
                orbital_elements=OrbitalElements(
                    semi_major_axis=6778.137,
                    eccentricity=0.0001,
                    inclination=53.0,
                    right_ascension=0.0,
                    argument_of_perigee=0.0,
                    mean_anomaly=0.0,
                    epoch=datetime.now(timezone.utc)
                ),
                is_active=True
            )
        ]
        satellite_repo.get_active_satellites.return_value = mock_satellites
        
        # 設置包含多個覆蓋視窗的結果
        mock_coverage = Coverage(
            observer_name="Observer",
            start_time=request.start_time,
            end_time=request.end_time,
            elevation_mask=request.elevation_mask
        )
        
        # 在不同時間添加覆蓋視窗
        for hour in range(3):
            mock_coverage.add_coverage_window(CoverageWindow(
                satellite_id="STARLINK-1",
                start_time=datetime(2025, 1, 1, hour, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2025, 1, 1, hour, 20, 0, tzinfo=timezone.utc),
                max_elevation=40.0 + hour * 5
            ))
        
        coverage_analyzer.analyze.return_value = mock_coverage
        
        use_case = AnalyzeCoverageUseCase(satellite_repo, coverage_analyzer)
        response = use_case.execute(request)
        
        assert len(response.coverage_windows) == 3
        assert response.statistics.total_windows == 3
        assert response.statistics.total_coverage_minutes == 30.0  # 3 * 10分鐘
    
    def test_observer_conversion(self, mock_dependencies, sample_request):
        """測試觀察者 DTO 到領域實體的轉換"""
        satellite_repo, coverage_analyzer = mock_dependencies
        satellite_repo.get_active_satellites.return_value = []
        
        # 設置一個 spy 來捕獲傳遞給 analyzer 的參數
        analyzer_call_args = None
        def capture_args(*args, **kwargs):
            nonlocal analyzer_call_args
            analyzer_call_args = args
            return Coverage(
                observer_name="Observer",
                start_time=sample_request.start_time,
                end_time=sample_request.end_time,
                elevation_mask=sample_request.elevation_mask
            )
        
        coverage_analyzer.analyze.side_effect = capture_args
        
        use_case = AnalyzeCoverageUseCase(satellite_repo, coverage_analyzer)
        use_case.execute(sample_request)
        
        # 驗證觀察者轉換
        observer_arg = analyzer_call_args[1]  # 第二個參數是 observer
        assert isinstance(observer_arg, Observer)
        assert observer_arg.position.latitude == 25.0330
        assert observer_arg.position.longitude == 121.5654
        assert observer_arg.position.altitude == 0.0