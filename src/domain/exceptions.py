"""
領域層例外定義 - 所有領域相關的例外
"""

from typing import Any, Dict, Optional


class DomainException(Exception):
    """領域層基礎例外類別"""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """初始化領域例外
        
        Args:
            message: 錯誤訊息
            code: 錯誤代碼
            details: 詳細資訊
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


class SatelliteException(DomainException):
    """衛星相關例外"""
    pass


class SatelliteNotFoundError(SatelliteException):
    """找不到衛星"""
    
    def __init__(self, satellite_id: str):
        super().__init__(
            message=f"找不到衛星: {satellite_id}",
            code="SATELLITE_NOT_FOUND",
            details={"satellite_id": satellite_id}
        )


class InvalidTLEError(SatelliteException):
    """無效的 TLE 資料"""
    
    def __init__(self, reason: str, tle_data: Optional[str] = None):
        super().__init__(
            message=f"無效的 TLE 資料: {reason}",
            code="INVALID_TLE",
            details={"reason": reason, "tle_data": tle_data}
        )


class OrbitCalculationError(SatelliteException):
    """軌道計算錯誤"""
    
    def __init__(self, satellite_id: str, reason: str):
        super().__init__(
            message=f"軌道計算失敗: {reason}",
            code="ORBIT_CALCULATION_ERROR",
            details={"satellite_id": satellite_id, "reason": reason}
        )


class CoverageException(DomainException):
    """覆蓋率分析相關例外"""
    pass


class InvalidTimeRangeError(CoverageException):
    """無效的時間範圍"""
    
    def __init__(self, start_time: str, end_time: str, reason: str):
        super().__init__(
            message=f"無效的時間範圍: {reason}",
            code="INVALID_TIME_RANGE",
            details={
                "start_time": start_time,
                "end_time": end_time,
                "reason": reason
            }
        )


class NoSatellitesAvailableError(CoverageException):
    """沒有可用的衛星"""
    
    def __init__(self, filter_criteria: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="沒有符合條件的衛星可供分析",
            code="NO_SATELLITES_AVAILABLE",
            details={"filter_criteria": filter_criteria or {}}
        )


class ObserverException(DomainException):
    """觀測者相關例外"""
    pass


class InvalidPositionError(ObserverException):
    """無效的位置"""
    
    def __init__(self, latitude: float, longitude: float, reason: str):
        super().__init__(
            message=f"無效的位置: {reason}",
            code="INVALID_POSITION",
            details={
                "latitude": latitude,
                "longitude": longitude,
                "reason": reason
            }
        )


class PredictionException(DomainException):
    """預測相關例外"""
    pass


class InsufficientDataError(PredictionException):
    """資料不足"""
    
    def __init__(self, required_data: str, available_data: str):
        super().__init__(
            message=f"資料不足以進行預測",
            code="INSUFFICIENT_DATA",
            details={
                "required": required_data,
                "available": available_data
            }
        )


class ModelNotTrainedError(PredictionException):
    """模型未訓練"""
    
    def __init__(self, model_name: str):
        super().__init__(
            message=f"模型 {model_name} 尚未訓練",
            code="MODEL_NOT_TRAINED",
            details={"model_name": model_name}
        )