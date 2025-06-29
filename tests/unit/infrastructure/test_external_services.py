"""外部服務的單元測試"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from src.infrastructure.external_services.skyfield_orbit_calculator import SkyfieldOrbitCalculator
from src.domain.entities.satellite import Satellite
from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements


class TestSkyfieldOrbitCalculator:
    """測試 Skyfield 軌道計算器"""
    
    @pytest.fixture
    def sample_satellite(self):
        """樣本衛星"""
        return Satellite(
            satellite_id="47562",
            name="STARLINK-1234",
            orbital_elements=OrbitalElements(
                semi_major_axis=6778.137,  # km
                eccentricity=0.0001,
                inclination=53.0,
                right_ascension=100.0,
                argument_of_perigee=0.0,
                mean_anomaly=0.0,
                epoch=datetime(2025, 1, 1, tzinfo=timezone.utc)
            ),
            is_active=True
        )
    
    @patch('skyfield.api.load')
    def test_calculate_position(self, mock_load, sample_satellite):
        """測試計算衛星位置"""
        # 模擬 Skyfield 對象
        mock_ts = Mock()
        mock_timescale = Mock()
        mock_time = Mock()
        mock_ts.timescale = mock_timescale
        mock_timescale.utc.return_value = mock_time
        mock_load.return_value = mock_ts
        
        # 模擬衛星對象
        mock_sat = Mock()
        mock_geocentric = Mock()
        mock_sat.at.return_value = mock_geocentric
        
        # 模擬位置數據
        mock_subpoint = Mock()
        mock_subpoint.latitude.degrees = 25.0
        mock_subpoint.longitude.degrees = 121.5
        mock_subpoint.elevation.km = 400.0
        mock_geocentric.subpoint.return_value = mock_subpoint
        
        with patch.object(SkyfieldOrbitCalculator, '_create_skyfield_satellite', return_value=mock_sat):
            calculator = SkyfieldOrbitCalculator()
            position = calculator.calculate_position(
                sample_satellite,
                datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            )
            
            assert isinstance(position, Position)
            assert position.latitude == 25.0
            assert position.longitude == 121.5
            assert position.altitude == 400.0
    
    @patch('skyfield.api.load')
    def test_calculate_pass_empty_list(self, mock_load, sample_satellite):
        """測試計算通過 - 空列表情況"""
        mock_ts = Mock()
        mock_load.return_value = mock_ts
        
        # 模擬沒有找到通過
        with patch.object(SkyfieldOrbitCalculator, '_find_passes', return_value=[]):
            calculator = SkyfieldOrbitCalculator()
            observer_pos = Position(latitude=25.0330, longitude=121.5654, altitude=0.0)
            
            passes = calculator.calculate_pass(
                sample_satellite,
                observer_pos,
                datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                25.0
            )
            
            assert passes == []
    
    @patch('skyfield.api.load')
    def test_calculate_pass_with_results(self, mock_load, sample_satellite):
        """測試計算通過 - 有結果情況"""
        mock_ts = Mock()
        mock_timescale = Mock()
        mock_ts.timescale = mock_timescale
        mock_load.return_value = mock_ts
        
        # 模擬時間對象
        mock_rise_time = Mock()
        mock_rise_time.utc_datetime.return_value = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        mock_set_time = Mock()
        mock_set_time.utc_datetime.return_value = datetime(2025, 1, 1, 1, 10, 0, tzinfo=timezone.utc)
        
        # 模擬通過數據
        mock_passes = [(mock_rise_time, mock_set_time, 45.0)]
        
        with patch.object(SkyfieldOrbitCalculator, '_find_passes', return_value=mock_passes):
            calculator = SkyfieldOrbitCalculator()
            observer_pos = Position(latitude=25.0330, longitude=121.5654, altitude=0.0)
            
            passes = calculator.calculate_pass(
                sample_satellite,
                observer_pos,
                datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                25.0
            )
            
            assert len(passes) == 1
            assert passes[0][0] == datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
            assert passes[0][1] == datetime(2025, 1, 1, 1, 10, 0, tzinfo=timezone.utc)
            assert passes[0][2] == 45.0
    
    def test_create_skyfield_satellite(self):
        """測試創建 Skyfield 衛星對象"""
        with patch('skyfield.api.load') as mock_load:
            mock_ts = Mock()
            mock_load.return_value = mock_ts
            
            calculator = SkyfieldOrbitCalculator()
            
            # TLE 格式
            tle_lines = [
                "STARLINK-1234",
                "1 47562U 21009A   25001.50000000  .00001234  00000-0  12345-4 0  9999",
                "2 47562  53.0540  100.1234   0001500  90.0000 270.1234  15.06390000123456"
            ]
            
            with patch('skyfield.api.EarthSatellite') as mock_earth_satellite:
                mock_sat = Mock()
                mock_earth_satellite.return_value = mock_sat
                
                result = calculator._create_skyfield_satellite(tle_lines)
                
                assert result == mock_sat
                mock_earth_satellite.assert_called_once()
    
    def test_orbital_elements_to_tle(self, sample_satellite):
        """測試軌道要素轉換為 TLE"""
        with patch('skyfield.api.load'):
            calculator = SkyfieldOrbitCalculator()
            
            # 這個測試主要驗證方法不會崩潰
            # 實際的 TLE 生成邏輯複雜，需要更詳細的驗證
            tle = calculator._orbital_elements_to_tle(sample_satellite)
            
            assert len(tle) == 3
            assert sample_satellite.name in tle[0]
            assert tle[1].startswith("1 ")
            assert tle[2].startswith("2 ")
    
    @patch('skyfield.api.load')
    def test_calculate_visibility(self, mock_load, sample_satellite):
        """測試計算可見性"""
        # 設置模擬
        mock_ts = Mock()
        mock_timescale = Mock()
        mock_time = Mock()
        mock_ts.timescale = mock_timescale
        mock_timescale.utc.return_value = mock_time
        mock_load.return_value = mock_ts
        
        # 模擬位置和高度角
        mock_difference = Mock()
        mock_topocentric = Mock()
        mock_alt_az = (Mock(degrees=30.0), Mock(degrees=180.0), Mock(km=1000.0))
        mock_topocentric.altaz.return_value = mock_alt_az
        mock_difference.at.return_value = mock_topocentric
        
        with patch.object(SkyfieldOrbitCalculator, '_create_skyfield_satellite') as mock_create:
            mock_sat = Mock()
            mock_sat.__sub__ = Mock(return_value=mock_difference)
            mock_create.return_value = mock_sat
            
            calculator = SkyfieldOrbitCalculator()
            observer_pos = Position(latitude=25.0330, longitude=121.5654, altitude=0.0)
            
            is_visible, elevation = calculator.calculate_visibility(
                sample_satellite,
                observer_pos,
                datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                25.0
            )
            
            assert is_visible is True  # 30度 > 25度
            assert elevation == 30.0