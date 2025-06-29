#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
工具模組

提供日誌記錄、錯誤處理等通用功能。
"""

from .errors import (BaseStarlinkException, ConfigurationError,
                     DataValidationError, ErrorContext, NetworkError,
                     PermissionDeniedError, RateLimitError,
                     ResourceNotFoundError, SatelliteCalculationError,
                     TLEDataError, handle_errors, validate_input)
from .logger import (get_logger, log_critical, log_debug, log_error, log_info,
                     log_warning)

__all__ = [
    # Logger
    "get_logger",
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "log_critical",
    # Errors
    "BaseStarlinkException",
    "DataValidationError",
    "SatelliteCalculationError",
    "NetworkError",
    "ConfigurationError",
    "TLEDataError",
    "ResourceNotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "handle_errors",
    "validate_input",
    "ErrorContext",
]
