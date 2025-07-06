"""
領域值物件的單元測試
"""

from datetime import datetime
import pytest

from src.domain.value_objects.position import Position
from src.domain.value_objects.orbital_elements import OrbitalElements
from src.domain.value_objects.time_range import TimeRange


class TestPosition:
    """位置值物件測試"""
    
    def test_position_creation(self):
        """測試位置建立"""
        pos = Position(latitude=25.0330, longitude=121.5654, elevation=10.0)
        
        assert pos.latitude == 25.0330
        assert pos.longitude == 121.5654
        assert pos.elevation == 10.0
    
    def test_position_equality(self):
        """測試位置相等性"""
        pos1 = Position(25.0330, 121.5654, 10.0)
        pos2 = Position(25.0330, 121.5654, 10.0)
        pos3 = Position(25.0330, 121.5654, 20.0)
        
        assert pos1 == pos2
        assert pos1 != pos3
        assert pos1 != "not a position"
    
    def test_position_hash(self):
        """測試位置雜湊值"""
        pos1 = Position(25.0330, 121.5654, 10.0)
        pos2 = Position(25.0330, 121.5654, 10.0)
        
        assert hash(pos1) == hash(pos2)
        
        # 可以用作字典鍵
        position_dict = {pos1: "Taipei"}
        assert position_dict[pos2] == "Taipei"
    
    def test_position_representation(self):
        """測試位置字串表示"""
        pos = Position(25.0330, 121.5654, 10.0)
        repr_str = repr(pos)
        
        assert "Position" in repr_str
        assert "25.0330" in repr_str
        assert "121.5654" in repr_str
        assert "10.0" in repr_str


class TestOrbitalElements:
    """軌道元素值物件測試"""
    
    def test_orbital_elements_creation(self):
        """測試軌道元素建立"""
        epoch = datetime(2024, 1, 1, 12, 0, 0)
        oe = OrbitalElements(
            epoch=epoch,
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        assert oe.epoch == epoch
        assert oe.inclination == 53.0
        assert oe.raan == 100.0
        assert oe.eccentricity == 0.001
        assert oe.arg_perigee == 90.0
        assert oe.mean_anomaly == 0.0
        assert oe.mean_motion == 15.0
    
    def test_orbital_elements_optional_fields(self):
        """測試可選欄位"""
        epoch = datetime(2024, 1, 1)
        oe = OrbitalElements(
            epoch=epoch,
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0,
            norad_id=12345,
            classification="U",
            element_set_number=999,
            revolution_number=50000,
            mean_motion_dot=0.00001,
            mean_motion_ddot=0.0,
            bstar=0.00005
        )
        
        assert oe.norad_id == 12345
        assert oe.classification == "U"
        assert oe.element_set_number == 999
        assert oe.revolution_number == 50000
        assert oe.mean_motion_dot == 0.00001
        assert oe.mean_motion_ddot == 0.0
        assert oe.bstar == 0.00005
    
    def test_orbital_elements_equality(self):
        """測試軌道元素相等性"""
        epoch = datetime(2024, 1, 1)
        oe1 = OrbitalElements(
            epoch=epoch,
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        oe2 = OrbitalElements(
            epoch=epoch,
            inclination=53.0,
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        oe3 = OrbitalElements(
            epoch=epoch,
            inclination=53.1,  # 不同的傾角
            raan=100.0,
            eccentricity=0.001,
            arg_perigee=90.0,
            mean_anomaly=0.0,
            mean_motion=15.0
        )
        
        assert oe1 == oe2
        assert oe1 != oe3


class TestTimeRange:
    """時間範圍值物件測試"""
    
    def test_time_range_creation(self):
        """測試時間範圍建立"""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 13, 0, 0)
        
        time_range = TimeRange(start=start, end=end)
        
        assert time_range.start == start
        assert time_range.end == end
    
    def test_time_range_duration(self):
        """測試時間範圍持續時間"""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 13, 30, 0)
        
        time_range = TimeRange(start=start, end=end)
        
        assert time_range.duration_seconds == 5400  # 90 分鐘
        assert time_range.duration_minutes == 90
        assert time_range.duration_hours == 1.5
    
    def test_time_range_contains(self):
        """測試時間範圍包含判斷"""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 13, 0, 0)
        
        time_range = TimeRange(start=start, end=end)
        
        # 測試包含的時間點
        assert time_range.contains(datetime(2024, 1, 1, 12, 30, 0))
        assert time_range.contains(start)  # 包含開始時間
        assert time_range.contains(end)    # 包含結束時間
        
        # 測試不包含的時間點
        assert not time_range.contains(datetime(2024, 1, 1, 11, 59, 59))
        assert not time_range.contains(datetime(2024, 1, 1, 13, 0, 1))
    
    def test_time_range_overlaps(self):
        """測試時間範圍重疊判斷"""
        range1 = TimeRange(
            start=datetime(2024, 1, 1, 12, 0, 0),
            end=datetime(2024, 1, 1, 13, 0, 0)
        )
        
        # 完全重疊
        range2 = TimeRange(
            start=datetime(2024, 1, 1, 12, 0, 0),
            end=datetime(2024, 1, 1, 13, 0, 0)
        )
        assert range1.overlaps(range2)
        
        # 部分重疊
        range3 = TimeRange(
            start=datetime(2024, 1, 1, 12, 30, 0),
            end=datetime(2024, 1, 1, 13, 30, 0)
        )
        assert range1.overlaps(range3)
        
        # 不重疊
        range4 = TimeRange(
            start=datetime(2024, 1, 1, 13, 1, 0),
            end=datetime(2024, 1, 1, 14, 0, 0)
        )
        assert not range1.overlaps(range4)
    
    def test_time_range_validation(self):
        """測試時間範圍驗證"""
        # 正常情況
        time_range = TimeRange(
            start=datetime(2024, 1, 1, 12, 0, 0),
            end=datetime(2024, 1, 1, 13, 0, 0)
        )
        assert time_range.is_valid()
        
        # 開始時間等於結束時間（零持續時間）
        time_range_zero = TimeRange(
            start=datetime(2024, 1, 1, 12, 0, 0),
            end=datetime(2024, 1, 1, 12, 0, 0)
        )
        assert time_range_zero.is_valid()  # 仍然有效
        assert time_range_zero.duration_seconds == 0
    
    def test_time_range_equality(self):
        """測試時間範圍相等性"""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 13, 0, 0)
        
        range1 = TimeRange(start=start, end=end)
        range2 = TimeRange(start=start, end=end)
        range3 = TimeRange(
            start=start,
            end=datetime(2024, 1, 1, 13, 1, 0)  # 不同結束時間
        )
        
        assert range1 == range2
        assert range1 != range3
        assert range1 != "not a time range"