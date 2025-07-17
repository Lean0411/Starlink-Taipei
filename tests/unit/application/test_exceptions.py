"""
應用層例外的單元測試
"""

import pytest

from src.application.exceptions import (
    ApplicationException,
    InvalidRequestError,
    ResourceNotFoundException,
    CoverageAnalysisError,
    PredictionError,
    TLEFetchError,
    NetworkError,
    convert_domain_exception
)
from src.domain.exceptions import (
    DomainException,
    SatelliteNotFoundError,
    InvalidTLEError,
    NoSatellitesAvailableError
)


class TestApplicationExceptions:
    """應用層例外測試"""
    
    def test_application_exception_basic(self):
        """測試基礎應用例外"""
        cause = ValueError("原始錯誤")
        exc = ApplicationException(
            "應用錯誤",
            code="APP_ERROR",
            details={"key": "value"},
            cause=cause
        )
        
        assert str(exc) == "應用錯誤"
        assert exc.message == "應用錯誤"
        assert exc.code == "APP_ERROR"
        assert exc.details == {"key": "value"}
        assert exc.cause == cause
    
    def test_invalid_request_error(self):
        """測試無效請求錯誤"""
        exc = InvalidRequestError("latitude", 91.0, "必須在 -90 到 90 之間")
        
        assert "無效的請求參數 latitude: 必須在 -90 到 90 之間" in str(exc)
        assert exc.code == "INVALID_REQUEST"
        assert exc.details["field"] == "latitude"
        assert exc.details["value"] == 91.0
        assert exc.details["reason"] == "必須在 -90 到 90 之間"
    
    def test_resource_not_found_error(self):
        """測試資源未找到錯誤"""
        exc = ResourceNotFoundException("CoverageAnalysis", "12345")
        
        assert "CoverageAnalysis 未找到: 12345" in str(exc)
        assert exc.code == "RESOURCE_NOT_FOUND"
        assert exc.details["resource_type"] == "CoverageAnalysis"
        assert exc.details["resource_id"] == "12345"
    
    def test_coverage_analysis_error(self):
        """測試覆蓋率分析錯誤"""
        exc = CoverageAnalysisError(
            "衛星資料不足",
            details={"satellites_needed": 10, "satellites_found": 5}
        )
        
        assert "覆蓋率分析失敗: 衛星資料不足" in str(exc)
        assert exc.code == "COVERAGE_ANALYSIS_ERROR"
        assert exc.details["satellites_needed"] == 10
        assert exc.details["satellites_found"] == 5
    
    def test_prediction_error(self):
        """測試預測錯誤"""
        exc = PredictionError(
            "模型載入失敗",
            details={"model": "SCINet-SA", "error": "file not found"}
        )
        
        assert "預測失敗: 模型載入失敗" in str(exc)
        assert exc.code == "PREDICTION_ERROR"
        assert exc.details["model"] == "SCINet-SA"
        assert exc.details["error"] == "file not found"
    
    def test_tle_fetch_error(self):
        """測試 TLE 獲取錯誤"""
        exc = TLEFetchError("Celestrak", "網路連接超時")
        
        assert "從 Celestrak 獲取 TLE 資料失敗: 網路連接超時" in str(exc)
        assert exc.code == "TLE_FETCH_ERROR"
        assert exc.details["source"] == "Celestrak"
        assert exc.details["reason"] == "網路連接超時"
    
    def test_network_error(self):
        """測試網路錯誤"""
        exc = NetworkError(
            "https://api.example.com/data",
            status_code=503,
            reason="Service Unavailable"
        )
        
        assert "網路請求失敗: https://api.example.com/data" in str(exc)
        assert exc.code == "NETWORK_ERROR"
        assert exc.details["url"] == "https://api.example.com/data"
        assert exc.details["status_code"] == 503
        assert exc.details["reason"] == "Service Unavailable"
    
    def test_network_error_without_status_code(self):
        """測試沒有狀態碼的網路錯誤"""
        exc = NetworkError("https://api.example.com/data", reason="Connection timeout")
        
        assert exc.details["status_code"] is None
        assert exc.details["reason"] == "Connection timeout"


class TestDomainExceptionConversion:
    """領域例外轉換測試"""
    
    def test_convert_satellite_not_found(self):
        """測試衛星未找到例外轉換"""
        domain_exc = SatelliteNotFoundError("SAT123")
        app_exc = convert_domain_exception(domain_exc)
        
        assert isinstance(app_exc, ResourceNotFoundException)
        assert app_exc.details["resource_type"] == "Satellite"
        assert app_exc.details["resource_id"] == "SAT123"
    
    def test_convert_invalid_tle(self):
        """測試無效 TLE 例外轉換"""
        domain_exc = InvalidTLEError("格式錯誤", "invalid data")
        app_exc = convert_domain_exception(domain_exc)
        
        assert isinstance(app_exc, ApplicationException)
        assert app_exc.code == "INVALID_TLE"
        assert app_exc.message == "無效的 TLE 資料: 格式錯誤"
        assert app_exc.cause == domain_exc
    
    def test_convert_no_satellites_available(self):
        """測試沒有衛星可用例外轉換"""
        domain_exc = NoSatellitesAvailableError({"region": "Taiwan"})
        app_exc = convert_domain_exception(domain_exc)
        
        assert isinstance(app_exc, CoverageAnalysisError)
        assert app_exc.code == "NO_SATELLITES_AVAILABLE"
        assert app_exc.details["filter_criteria"]["region"] == "Taiwan"
    
    def test_convert_generic_domain_exception(self):
        """測試通用領域例外轉換"""
        domain_exc = DomainException("未知錯誤", code="UNKNOWN", details={"info": "test"})
        app_exc = convert_domain_exception(domain_exc)
        
        assert isinstance(app_exc, ApplicationException)
        assert app_exc.code == "UNKNOWN"
        assert app_exc.message == "未知錯誤"
        assert app_exc.details == {"info": "test"}
        assert app_exc.cause == domain_exc