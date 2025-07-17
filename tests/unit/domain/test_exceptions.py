"""
領域層例外的單元測試
"""

import pytest

from src.domain.exceptions import (
    DomainException,
    SatelliteNotFoundError,
    InvalidTLEError,
    OrbitCalculationError,
    InvalidTimeRangeError,
    NoSatellitesAvailableError,
    InvalidPositionError,
    InsufficientDataError,
    ModelNotTrainedError
)


class TestDomainExceptions:
    """領域例外測試"""
    
    def test_domain_exception_basic(self):
        """測試基礎領域例外"""
        exc = DomainException("測試錯誤", code="TEST_ERROR", details={"key": "value"})
        
        assert str(exc) == "測試錯誤"
        assert exc.message == "測試錯誤"
        assert exc.code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
    
    def test_domain_exception_default_code(self):
        """測試預設錯誤代碼"""
        exc = DomainException("測試錯誤")
        assert exc.code == "DomainException"
        assert exc.details == {}
    
    def test_satellite_not_found_error(self):
        """測試找不到衛星錯誤"""
        exc = SatelliteNotFoundError("SAT123")
        
        assert "找不到衛星: SAT123" in str(exc)
        assert exc.code == "SATELLITE_NOT_FOUND"
        assert exc.details["satellite_id"] == "SAT123"
    
    def test_invalid_tle_error(self):
        """測試無效 TLE 錯誤"""
        exc = InvalidTLEError("格式錯誤", "1 12345U...")
        
        assert "無效的 TLE 資料: 格式錯誤" in str(exc)
        assert exc.code == "INVALID_TLE"
        assert exc.details["reason"] == "格式錯誤"
        assert exc.details["tle_data"] == "1 12345U..."
    
    def test_orbit_calculation_error(self):
        """測試軌道計算錯誤"""
        exc = OrbitCalculationError("SAT123", "數值溢出")
        
        assert "軌道計算失敗: 數值溢出" in str(exc)
        assert exc.code == "ORBIT_CALCULATION_ERROR"
        assert exc.details["satellite_id"] == "SAT123"
        assert exc.details["reason"] == "數值溢出"
    
    def test_invalid_time_range_error(self):
        """測試無效時間範圍錯誤"""
        exc = InvalidTimeRangeError("2024-01-01", "2023-12-31", "結束時間早於開始時間")
        
        assert "無效的時間範圍: 結束時間早於開始時間" in str(exc)
        assert exc.code == "INVALID_TIME_RANGE"
        assert exc.details["start_time"] == "2024-01-01"
        assert exc.details["end_time"] == "2023-12-31"
    
    def test_no_satellites_available_error(self):
        """測試沒有可用衛星錯誤"""
        exc = NoSatellitesAvailableError({"active": True, "region": "Taiwan"})
        
        assert "沒有符合條件的衛星可供分析" in str(exc)
        assert exc.code == "NO_SATELLITES_AVAILABLE"
        assert exc.details["filter_criteria"]["active"] is True
        assert exc.details["filter_criteria"]["region"] == "Taiwan"
    
    def test_invalid_position_error(self):
        """測試無效位置錯誤"""
        exc = InvalidPositionError(91.0, 121.5, "緯度超出範圍")
        
        assert "無效的位置: 緯度超出範圍" in str(exc)
        assert exc.code == "INVALID_POSITION"
        assert exc.details["latitude"] == 91.0
        assert exc.details["longitude"] == 121.5
    
    def test_insufficient_data_error(self):
        """測試資料不足錯誤"""
        exc = InsufficientDataError("至少需要 100 筆資料", "只有 50 筆資料")
        
        assert "資料不足以進行預測" in str(exc)
        assert exc.code == "INSUFFICIENT_DATA"
        assert exc.details["required"] == "至少需要 100 筆資料"
        assert exc.details["available"] == "只有 50 筆資料"
    
    def test_model_not_trained_error(self):
        """測試模型未訓練錯誤"""
        exc = ModelNotTrainedError("SCINet-SA")
        
        assert "模型 SCINet-SA 尚未訓練" in str(exc)
        assert exc.code == "MODEL_NOT_TRAINED"
        assert exc.details["model_name"] == "SCINet-SA"