#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
統一錯誤處理系統

定義自定義異常類別和錯誤處理裝飾器。
"""

import functools
import time
import uuid
from typing import Any, Callable, Dict

from .logger import log_error, log_info, log_warning


class BaseStarlinkException(Exception):
    """Starlink 系統基礎異常類別"""

    error_code: str = "UNKNOWN_ERROR"
    user_message: str = "系統發生未知錯誤"
    http_status: int = 500

    def __init__(self, message: str = None, details: Dict[str, Any] = None):
        self.message = message or self.user_message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class DataValidationError(BaseStarlinkException):
    """數據驗證錯誤"""

    error_code = "DATA_VALIDATION_ERROR"
    user_message = "輸入數據驗證失敗"
    http_status = 400


class SatelliteCalculationError(BaseStarlinkException):
    """衛星計算錯誤"""

    error_code = "SAT_CALC_001"
    user_message = "衛星計算失敗，請稍後重試"
    http_status = 500


class NetworkError(BaseStarlinkException):
    """網路連接錯誤"""

    error_code = "NETWORK_ERROR"
    user_message = "網路連接失敗，請檢查您的網路設定"
    http_status = 503


class ConfigurationError(BaseStarlinkException):
    """配置錯誤"""

    error_code = "CONFIG_ERROR"
    user_message = "系統配置錯誤，請聯繫管理員"
    http_status = 500


class TLEDataError(BaseStarlinkException):
    """TLE 數據錯誤"""

    error_code = "TLE_DATA_ERROR"
    user_message = "衛星軌道數據獲取失敗"
    http_status = 503


class ResourceNotFoundError(BaseStarlinkException):
    """資源未找到錯誤"""

    error_code = "RESOURCE_NOT_FOUND"
    user_message = "請求的資源不存在"
    http_status = 404


class PermissionDeniedError(BaseStarlinkException):
    """權限拒絕錯誤"""

    error_code = "PERMISSION_DENIED"
    user_message = "您沒有權限執行此操作"
    http_status = 403


class RateLimitError(BaseStarlinkException):
    """速率限制錯誤"""

    error_code = "RATE_LIMIT_EXCEEDED"
    user_message = "請求過於頻繁，請稍後再試"
    http_status = 429


def handle_errors(  # noqa: C901
    retry_count: int = 0,
    retry_delay: float = 1.0,
    log_performance: bool = True,
    include_trace_id: bool = True,
):
    """
    統一的錯誤處理裝飾器

    Args:
        retry_count: 重試次數
        retry_delay: 重試延遲（秒）
        log_performance: 是否記錄性能指標
        include_trace_id: 是否包含追踪 ID
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成追踪 ID
            trace_id = str(uuid.uuid4()) if include_trace_id else None
            start_time = time.time()

            # 記錄函數調用
            extra_data = {"trace_id": trace_id} if trace_id else {}
            log_info(f"開始執行: {func.__name__}", **extra_data)

            last_exception = None
            for attempt in range(retry_count + 1):
                try:
                    # 執行函數
                    result = func(*args, **kwargs)

                    # 記錄成功執行
                    if log_performance:
                        duration = time.time() - start_time
                        log_info(
                            f"成功執行: {func.__name__}",
                            duration=duration,
                            **extra_data,
                        )

                    return result

                except BaseStarlinkException as e:
                    # 處理自定義異常
                    last_exception = e
                    log_error(
                        f"自定義錯誤 in {func.__name__}: {e.error_code}",
                        exc_info=True,
                        error_code=e.error_code,
                        **extra_data,
                    )

                    if attempt < retry_count:
                        log_warning(
                            f"重試 {func.__name__} (嘗試 {attempt + 1}/{retry_count})",
                            **extra_data,
                        )
                        time.sleep(retry_delay * (attempt + 1))
                    else:
                        raise

                except Exception as e:
                    # 處理未預期的異常
                    last_exception = e
                    log_error(
                        f"未預期錯誤 in {func.__name__}: {str(e)}",
                        exc_info=True,
                        **extra_data,
                    )

                    if attempt < retry_count:
                        log_warning(
                            f"重試 {func.__name__} (嘗試 {attempt + 1}/{retry_count})",
                            **extra_data,
                        )
                        time.sleep(retry_delay * (attempt + 1))
                    else:
                        # 包裝為自定義異常
                        raise BaseStarlinkException(
                            f"執行 {func.__name__} 時發生錯誤",
                            details={"original_error": str(e)},
                        )

            # 如果所有重試都失敗
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def validate_input(**validators):
    """
    輸入驗證裝飾器

    使用範例:
    @validate_input(lat=(-90, 90), lon=(-180, 180), duration=(1, 1440))
    def analyze_satellites(lat, lon, duration):
        pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 獲取函數參數
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 驗證每個參數
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]

                    # 範圍驗證
                    if isinstance(validator, tuple) and len(validator) == 2:
                        min_val, max_val = validator
                        if not (min_val <= value <= max_val):
                            raise DataValidationError(
                                f"參數 {param_name} 必須在 {min_val} 到 {max_val} 之間",
                                details={
                                    "parameter": param_name,
                                    "value": value,
                                    "min": min_val,
                                    "max": max_val,
                                },
                            )

                    # 類型驗證
                    elif isinstance(validator, type):
                        if not isinstance(value, validator):
                            raise DataValidationError(
                                f"參數 {param_name} 必須是 {validator.__name__} 類型",
                                details={
                                    "parameter": param_name,
                                    "value": value,
                                    "expected_type": validator.__name__,
                                },
                            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


class ErrorContext:
    """錯誤上下文管理器"""

    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context

    def __enter__(self):
        log_info(f"開始操作: {self.operation}", **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            log_error(
                f"操作失敗: {self.operation}",
                exc_info=(exc_type, exc_val, exc_tb),
                **self.context,
            )
            # 不抑制異常
            return False
        else:
            log_info(f"操作成功: {self.operation}", **self.context)
