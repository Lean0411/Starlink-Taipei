"""預測用例的單元測試"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from src.application.use_cases.predict_coverage_use_case import PredictCoverageUseCase
from src.application.dto.prediction_request import PredictionRequest
from src.application.dto.coverage_request import ObserverDTO
from src.application.dto.prediction_response import PredictionResponse
from src.domain.entities.satellite import Satellite
from src.domain.entities.prediction import Prediction, PredictionPoint, OptimalWindow, PredictionTimeScale
from src.domain.value_objects.orbital_elements import OrbitalElements


class TestPredictCoverageUseCase:
    """測試預測覆蓋用例"""

    @pytest.fixture
    def mock_dependencies(self):
        """模擬依賴"""
        satellite_repo = Mock()
        prediction_service = Mock()
        return satellite_repo, prediction_service

    @pytest.fixture
    def sample_request(self):
        """樣本請求"""
        return PredictionRequest(
            observer=ObserverDTO(latitude=25.0330, longitude=121.5654, altitude=10.0),
            time_scale=PredictionTimeScale.MEDIUM_TERM,
            start_time=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            min_elevation=25.0,
            min_satellites_for_window=30,
        )

    def test_execute_success(self, mock_dependencies, sample_request):
        """測試成功執行預測"""
        satellite_repo, prediction_service = mock_dependencies

        # 設置模擬衛星
        mock_satellites = [
            Satellite(
                satellite_id=f"STARLINK-{i}",
                name=f"Starlink-{i}",
                orbital_elements=OrbitalElements(
                    epoch=datetime.now(timezone.utc),
                    inclination=53.0,
                    raan=i * 30.0,
                    eccentricity=0.0001,
                    arg_perigee=0.0,
                    mean_anomaly=0.0,
                    mean_motion=15.06390000,
                    bstar=0.00012345,
                ),
                is_active=True,
            )
            for i in range(5)
        ]
        satellite_repo.get_active_satellites.return_value = mock_satellites

        # 設置模擬預測結果
        mock_prediction = Prediction(
            prediction_id="pred-123",
            observer_name="預測觀測者",
            time_scale=PredictionTimeScale.MEDIUM_TERM,
            created_at=datetime.now(timezone.utc),
            start_time=sample_request.start_time,
            end_time=datetime(2025, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        )

        # 添加預測點
        for i in range(3):
            point = PredictionPoint(
                timestamp=datetime(2025, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                predicted_satellites=30 + i * 5,
                predicted_elevation=40.0 + i * 5,
                coverage_probability=75.0 + i * 5,
                uncertainty={"satellites": 2.0, "elevation": 1.5, "coverage": 3.0},
                confidence_interval={"lower": 28 + i * 5, "upper": 32 + i * 5},
            )
            mock_prediction.add_prediction_point(point)

        # 添加最佳窗口
        window = OptimalWindow(
            start_time=datetime(2025, 1, 1, 0, 30, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 1, 1, 30, 0, tzinfo=timezone.utc),
            avg_satellites=35.0,
            max_elevation=50.0,
            duration_minutes=60,
        )
        mock_prediction.add_optimal_window(window)

        # 計算統計
        mock_prediction.calculate_statistics()

        prediction_service.predict_coverage.return_value = mock_prediction

        # 執行用例
        use_case = PredictCoverageUseCase(satellite_repo, prediction_service)
        response = use_case.execute(sample_request)

        # 驗證結果
        assert isinstance(response, PredictionResponse)
        assert response.prediction_id == "pred-123"
        assert response.time_scale == "medium_term"
        assert response.total_satellites == 5
        assert response.analyzed_satellites == 5
        assert len(response.prediction_points) == 3
        assert len(response.optimal_windows) == 1
        assert response.optimal_windows[0].duration_minutes == 60

    def test_execute_with_satellite_filter(self, mock_dependencies, sample_request):
        """測試帶衛星過濾的預測"""
        satellite_repo, prediction_service = mock_dependencies

        # 設置請求包含衛星ID過濾
        sample_request.satellite_ids = ["STARLINK-1", "STARLINK-3"]

        # 設置模擬衛星
        all_satellites = [
            Satellite(
                satellite_id=f"STARLINK-{i}",
                name=f"Starlink-{i}",
                orbital_elements=OrbitalElements(
                    epoch=datetime.now(timezone.utc),
                    inclination=53.0,
                    raan=i * 30.0,
                    eccentricity=0.0001,
                    arg_perigee=0.0,
                    mean_anomaly=0.0,
                    mean_motion=15.06390000,
                    bstar=0.00012345,
                ),
                is_active=True,
            )
            for i in range(5)
        ]
        satellite_repo.get_active_satellites.return_value = all_satellites

        # 設置模擬預測結果
        mock_prediction = Prediction(
            prediction_id="pred-456",
            observer_name="預測觀測者",
            time_scale=PredictionTimeScale.MEDIUM_TERM,
            created_at=datetime.now(timezone.utc),
            start_time=sample_request.start_time,
            end_time=datetime(2025, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        )

        prediction_service.predict_coverage.return_value = mock_prediction

        # 執行用例
        use_case = PredictCoverageUseCase(satellite_repo, prediction_service)
        use_case.execute(sample_request)

        # 驗證過濾功能
        # 檢查 predict_coverage 是否使用過濾後的衛星列表調用
        call_args = prediction_service.predict_coverage.call_args
        filtered_satellites = call_args[1]["satellites"]
        assert len(filtered_satellites) == 2
        assert all(sat.satellite_id in ["STARLINK-1", "STARLINK-3"] for sat in filtered_satellites)

    def test_execute_with_no_satellites(self, mock_dependencies, sample_request):
        """測試沒有衛星的情況"""
        satellite_repo, prediction_service = mock_dependencies

        # 沒有活躍衛星
        satellite_repo.get_active_satellites.return_value = []

        # 設置空預測
        mock_prediction = Prediction(
            prediction_id="pred-empty",
            observer_name="預測觀測者",
            time_scale=PredictionTimeScale.MEDIUM_TERM,
            created_at=datetime.now(timezone.utc),
            start_time=sample_request.start_time,
            end_time=datetime(2025, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        )

        prediction_service.predict_coverage.return_value = mock_prediction

        use_case = PredictCoverageUseCase(satellite_repo, prediction_service)
        response = use_case.execute(sample_request)

        assert response.total_satellites == 0
        assert response.analyzed_satellites == 0
        assert len(response.prediction_points) == 0
        assert len(response.optimal_windows) == 0
