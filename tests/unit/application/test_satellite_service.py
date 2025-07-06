"""
衛星服務的單元測試
"""

from datetime import datetime
from unittest.mock import Mock, MagicMock
import pytest

from src.application.services.satellite_service import SatelliteService
from src.domain.entities.satellite import Satellite
from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements


class TestSatelliteService:
    """衛星服務測試"""
    
    @pytest.fixture
    def mock_orbit_calculator(self):
        """模擬軌道計算器"""
        return Mock()
    
    @pytest.fixture
    def satellite_service(self, mock_orbit_calculator):
        """建立衛星服務實例"""
        return SatelliteService(mock_orbit_calculator)
    
    @pytest.fixture
    def test_satellite(self):
        """測試用衛星"""
        orbital_elements = OrbitalElements(
            epoch=datetime(2024, 1, 1),
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        return Satellite(
            satellite_id="SAT123",
            name="Test Satellite",
            orbital_elements=orbital_elements,
            is_active=True
        )
    
    def test_calculate_position(self, satellite_service, mock_orbit_calculator, test_satellite):
        """測試計算衛星位置"""
        # 準備
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        expected_position = Position(10.0, 20.0, 500000.0)
        mock_orbit_calculator.calculate_position.return_value = expected_position
        
        # 執行
        position = satellite_service.calculate_position(test_satellite, test_time)
        
        # 驗證
        assert position == expected_position
        mock_orbit_calculator.calculate_position.assert_called_once_with(test_satellite, test_time)
    
    def test_get_pass_details_active_satellite(self, satellite_service, mock_orbit_calculator, test_satellite):
        """測試獲取活躍衛星的通過詳情"""
        # 準備
        observer_position = Position(25.0330, 121.5654, 10.0)
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        expected_details = (120.5, 45.3, 850.2)  # 方位角, 仰角, 距離
        mock_orbit_calculator.calculate_pass_details.return_value = expected_details
        
        # 執行
        details = satellite_service.get_pass_details(test_satellite, observer_position, test_time)
        
        # 驗證
        assert details == expected_details
        mock_orbit_calculator.calculate_pass_details.assert_called_once_with(
            test_satellite, observer_position, test_time
        )
    
    def test_get_pass_details_inactive_satellite(self, satellite_service, mock_orbit_calculator, test_satellite):
        """測試獲取非活躍衛星的通過詳情"""
        # 準備
        test_satellite.is_active = False
        observer_position = Position(25.0330, 121.5654, 10.0)
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # 執行
        details = satellite_service.get_pass_details(test_satellite, observer_position, test_time)
        
        # 驗證
        assert details is None
        mock_orbit_calculator.calculate_pass_details.assert_not_called()
    
    def test_is_visible_above_min_elevation(self, satellite_service, mock_orbit_calculator, test_satellite):
        """測試衛星在最小仰角以上時可見"""
        # 準備
        observer_position = Position(25.0330, 121.5654, 10.0)
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_orbit_calculator.calculate_pass_details.return_value = (120.5, 30.0, 850.2)  # 仰角 30 度
        
        # 執行
        is_visible = satellite_service.is_visible(
            test_satellite, observer_position, test_time, min_elevation=25.0
        )
        
        # 驗證
        assert is_visible is True
    
    def test_is_visible_below_min_elevation(self, satellite_service, mock_orbit_calculator, test_satellite):
        """測試衛星在最小仰角以下時不可見"""
        # 準備
        observer_position = Position(25.0330, 121.5654, 10.0)
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_orbit_calculator.calculate_pass_details.return_value = (120.5, 20.0, 850.2)  # 仰角 20 度
        
        # 執行
        is_visible = satellite_service.is_visible(
            test_satellite, observer_position, test_time, min_elevation=25.0
        )
        
        # 驗證
        assert is_visible is False
    
    def test_is_visible_inactive_satellite(self, satellite_service, mock_orbit_calculator, test_satellite):
        """測試非活躍衛星不可見"""
        # 準備
        test_satellite.is_active = False
        observer_position = Position(25.0330, 121.5654, 10.0)
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # 執行
        is_visible = satellite_service.is_visible(test_satellite, observer_position, test_time)
        
        # 驗證
        assert is_visible is False
        mock_orbit_calculator.calculate_pass_details.assert_not_called()
    
    def test_is_sunlit(self, satellite_service, mock_orbit_calculator, test_satellite):
        """測試衛星是否被太陽照射"""
        # 準備
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_orbit_calculator.is_sunlit.return_value = True
        
        # 執行
        is_sunlit = satellite_service.is_sunlit(test_satellite, test_time)
        
        # 驗證
        assert is_sunlit is True
        mock_orbit_calculator.is_sunlit.assert_called_once_with(test_satellite, test_time)