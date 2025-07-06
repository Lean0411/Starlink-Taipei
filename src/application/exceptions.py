"""
應用層例外定義 - 處理用例相關的例外
"""

from typing import Any, Dict, Optional

from ..domain.exceptions import DomainException


class ApplicationException(Exception):
    """應用層基礎例外類別"""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """初始化應用例外
        
        Args:
            message: 錯誤訊息
            code: 錯誤代碼
            details: 詳細資訊
            cause: 原始例外
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause


class ValidationException(ApplicationException):
    """驗證例外"""
    pass


class InvalidRequestError(ValidationException):
    """無效的請求"""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            message=f"無效的請求參數 {field}: {reason}",
            code="INVALID_REQUEST",
            details={
                "field": field,
                "value": value,
                "reason": reason
            }
        )


class ResourceNotFoundException(ApplicationException):
    """資源未找到例外"""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} 未找到: {resource_id}",
            code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class UseCaseException(ApplicationException):
    """用例執行例外"""
    pass


class CoverageAnalysisError(UseCaseException):
    """覆蓋率分析錯誤"""
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"覆蓋率分析失敗: {reason}",
            code="COVERAGE_ANALYSIS_ERROR",
            details=details or {}
        )


class PredictionError(UseCaseException):
    """預測錯誤"""
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"預測失敗: {reason}",
            code="PREDICTION_ERROR",
            details=details or {}
        )


class ExternalServiceException(ApplicationException):
    """外部服務例外"""
    pass


class TLEFetchError(ExternalServiceException):
    """TLE 資料獲取錯誤"""
    
    def __init__(self, source: str, reason: str):
        super().__init__(
            message=f"從 {source} 獲取 TLE 資料失敗: {reason}",
            code="TLE_FETCH_ERROR",
            details={
                "source": source,
                "reason": reason
            }
        )


class NetworkError(ExternalServiceException):
    """網路錯誤"""
    
    def __init__(self, url: str, status_code: Optional[int] = None, reason: str = ""):
        super().__init__(
            message=f"網路請求失敗: {url}",
            code="NETWORK_ERROR",
            details={
                "url": url,
                "status_code": status_code,
                "reason": reason
            }
        )


def convert_domain_exception(domain_exception: DomainException) -> ApplicationException:
    """將領域例外轉換為應用例外
    
    Args:
        domain_exception: 領域例外
        
    Returns:
        ApplicationException: 對應的應用例外
    """
    # 根據領域例外類型進行轉換
    exception_mapping = {
        "SATELLITE_NOT_FOUND": ResourceNotFoundException,
        "INVALID_TLE": ValidationException,
        "ORBIT_CALCULATION_ERROR": CoverageAnalysisError,
        "INVALID_TIME_RANGE": InvalidRequestError,
        "NO_SATELLITES_AVAILABLE": CoverageAnalysisError,
        "INVALID_POSITION": InvalidRequestError,
        "INSUFFICIENT_DATA": PredictionError,
        "MODEL_NOT_TRAINED": PredictionError,
    }
    
    exception_class = exception_mapping.get(
        domain_exception.code, 
        ApplicationException
    )
    
    if exception_class in [ResourceNotFoundException]:
        # 特殊處理資源未找到
        return ResourceNotFoundException(
            resource_type="Satellite",
            resource_id=domain_exception.details.get("satellite_id", "unknown")
        )
    elif exception_class in [InvalidRequestError]:
        # 特殊處理無效請求
        field = list(domain_exception.details.keys())[0] if domain_exception.details else "unknown"
        value = list(domain_exception.details.values())[0] if domain_exception.details else None
        return InvalidRequestError(
            field=field,
            value=value,
            reason=domain_exception.message
        )
    else:
        # 通用轉換
        return exception_class(
            message=domain_exception.message,
            code=domain_exception.code,
            details=domain_exception.details,
            cause=domain_exception
        )