"""值物件的單元測試"""

import pytest
from datetime import datetime, timezone
from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements


class TestPosition:
    """測試位置值物件"""
    
    def test_position_creation(self):
        """測試位置創建"""
        position = Position(
            latitude=25.0330,
            longitude=121.5654,
            elevation=0.0
        )
        
        assert position.latitude == 25.0330
        assert position.longitude == 121.5654
        assert position.elevation == 0.0
    
    def test_position_validation(self):
        """測試位置驗證"""
        # 有效的位置
        Position(latitude=90.0, longitude=180.0, elevation=0.0)
        Position(latitude=-90.0, longitude=-180.0, elevation=0.0)
        Position(latitude=0.0, longitude=0.0, elevation=0.0)
        
        # 無效的緯度
        with pytest.raises(ValueError):
            Position(latitude=91.0, longitude=0.0, elevation=0.0)
        
        with pytest.raises(ValueError):
            Position(latitude=-91.0, longitude=0.0, elevation=0.0)
        
        # 無效的經度
        with pytest.raises(ValueError):
            Position(latitude=0.0, longitude=181.0, elevation=0.0)
        
        with pytest.raises(ValueError):
            Position(latitude=0.0, longitude=-181.0, elevation=0.0)
        
        # 無效的高度
        with pytest.raises(ValueError):
            Position(latitude=0.0, longitude=0.0, elevation=-501.0)
    
    def test_position_distance_to(self):
        """測試位置間距離計算"""
        taipei = Position(latitude=25.0330, longitude=121.5654, elevation=0.0)
        tokyo = Position(latitude=35.6762, longitude=139.6503, elevation=0.0)
        
        # 台北到東京的距離約為 2100 公里
        distance = taipei.distance_to(tokyo)
        assert 2000 < distance < 2200  # 允許一些誤差
    
    def test_position_equality(self):
        """測試位置相等性"""
        pos1 = Position(latitude=25.0330, longitude=121.5654, elevation=0.0)
        pos2 = Position(latitude=25.0330, longitude=121.5654, elevation=0.0)
        pos3 = Position(latitude=25.0331, longitude=121.5654, elevation=0.0)
        
        assert pos1 == pos2
        assert pos1 != pos3
    
    def test_position_to_radians(self):
        """測試位置轉換為弧度"""
        position = Position(latitude=0.0, longitude=180.0, elevation=0.0)
        lat_rad, lon_rad = position.to_radians()
        
        assert lat_rad == pytest.approx(0.0, abs=1e-6)
        assert lon_rad == pytest.approx(3.14159, rel=0.001)  # π


class TestOrbitalElements:
    """測試軌道要素值物件"""
    
    def test_orbital_elements_creation(self):
        """測試軌道要素創建"""
        epoch = datetime.now(timezone.utc)
        elements = OrbitalElements(
            epoch=epoch,
            inclination=53.0,  # degrees
            raan=100.0,  # Right Ascension of Ascending Node
            eccentricity=0.0001,
            arg_perigee=50.0,  # Argument of Perigee
            mean_anomaly=45.0,
            mean_motion=15.06390000,  # 約 95 分鐘週期
            bstar=0.00012345
        )
        
        assert elements.epoch == epoch
        assert elements.inclination == 53.0
        assert elements.raan == 100.0
        assert elements.eccentricity == 0.0001
        assert elements.arg_perigee == 50.0
        assert elements.mean_anomaly == 45.0
        assert elements.mean_motion == 15.06390000
        assert elements.bstar == 0.00012345
    
    def test_orbital_period_calculation(self):
        """測試軌道週期計算"""
        # 低地球軌道衛星
        leo_elements = OrbitalElements(
            epoch=datetime.now(timezone.utc),
            inclination=53.0,
            raan=0.0,
            eccentricity=0.0001,
            arg_perigee=0.0,
            mean_anomaly=0.0,
            mean_motion=15.06390000,  # LEO 典型值
            bstar=0.0
        )
        
        # LEO 衛星的軌道週期約為 90-100 分鐘
        period = leo_elements.period_minutes
        assert pytest.approx(period, rel=0.01) == 95.5  # 1440 / 15.06390000
    
    def test_orbital_elements_validation(self):
        """測試軌道要素驗證"""
        # 有效的軌道要素
        OrbitalElements(
            epoch=datetime.now(timezone.utc),
            inclination=45.0,
            raan=180.0,
            eccentricity=0.5,
            arg_perigee=90.0,
            mean_anomaly=270.0,
            mean_motion=1.0,
            bstar=0.0
        )
        
        # 無效的傾角
        with pytest.raises(ValueError):
            OrbitalElements(
                epoch=datetime.now(timezone.utc),
                inclination=181.0,  # > 180
                raan=0.0,
                eccentricity=0.0,
                arg_perigee=0.0,
                mean_anomaly=0.0,
                mean_motion=1.0,
                bstar=0.0
            )
        
        # 無效的離心率
        with pytest.raises(ValueError):
            OrbitalElements(
                epoch=datetime.now(timezone.utc),
                inclination=0.0,
                raan=0.0,
                eccentricity=1.0,  # >= 1
                arg_perigee=0.0,
                mean_anomaly=0.0,
                mean_motion=1.0,
                bstar=0.0
            )
        
        # 無效的平均運動
        with pytest.raises(ValueError):
            OrbitalElements(
                epoch=datetime.now(timezone.utc),
                inclination=0.0,
                raan=0.0,
                eccentricity=0.0,
                arg_perigee=0.0,
                mean_anomaly=0.0,
                mean_motion=0.0,  # <= 0
                bstar=0.0
            )
    
    def test_is_low_earth_orbit(self):
        """測試低地球軌道判斷"""
        # LEO 衛星（週期 < 128 分鐘）
        leo_elements = OrbitalElements(
            epoch=datetime.now(timezone.utc),
            inclination=53.0,
            raan=0.0,
            eccentricity=0.0001,
            arg_perigee=0.0,
            mean_anomaly=0.0,
            mean_motion=15.0,  # 96 分鐘週期
            bstar=0.0
        )
        assert leo_elements.is_low_earth_orbit is True
        
        # GEO 衛星（週期 = 24 小時）
        geo_elements = OrbitalElements(
            epoch=datetime.now(timezone.utc),
            inclination=0.0,
            raan=0.0,
            eccentricity=0.0,
            arg_perigee=0.0,
            mean_anomaly=0.0,
            mean_motion=1.0,  # 1440 分鐘週期
            bstar=0.0
        )
        assert geo_elements.is_low_earth_orbit is False