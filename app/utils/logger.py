#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# MIT License
# Copyright (c) 2025 Starlink Taipei Analysis Team
#
# This file is part of the Starlink Taipei Satellite Analysis System.

"""
統一日誌系統模組

提供結構化日誌記錄，支援 JSON 格式輸出和日誌輪轉。
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """自定義 JSON 格式化器，用於結構化日誌"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日誌記錄為 JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process,
        }
        
        # 添加額外的上下文信息
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'trace_id'):
            log_data['trace_id'] = record.trace_id
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        if hasattr(record, 'satellite_count'):
            log_data['satellite_count'] = record.satellite_count
            
        # 如果有異常信息，添加到日誌
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        # 過濾敏感信息
        log_data = self._filter_sensitive_data(log_data)
        
        return json.dumps(log_data, ensure_ascii=False)
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """過濾敏感資訊"""
        sensitive_keys = ['password', 'token', 'api_key', 'secret', 'credential']
        
        def filter_dict(d: dict) -> dict:
            filtered = {}
            for key, value in d.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    filtered[key] = '***FILTERED***'
                elif isinstance(value, dict):
                    filtered[key] = filter_dict(value)
                else:
                    filtered[key] = value
            return filtered
        
        return filter_dict(data)


class Logger:
    """統一的日誌管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logger()
            self._initialized = True
    
    def _setup_logger(self):
        """設置日誌系統"""
        # 創建日誌目錄
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # 設置根日誌器
        self.logger = logging.getLogger('starlink')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除現有的處理器
        self.logger.handlers.clear()
        
        # 控制台處理器（人類可讀格式）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # 文件處理器（JSON 格式，支援輪轉）
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'starlink.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        
        # 錯誤文件處理器（僅記錄錯誤和嚴重錯誤）
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'error.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        
        # 添加處理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        
        # 設置日誌級別從環境變數
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.set_level(log_level)
    
    def set_level(self, level: str):
        """設置日誌級別"""
        numeric_level = getattr(logging, level, logging.INFO)
        self.logger.setLevel(numeric_level)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """獲取日誌器實例"""
        if name:
            return logging.getLogger(f'starlink.{name}')
        return self.logger
    
    def add_context(self, **kwargs):
        """添加全局上下文信息到日誌"""
        for key, value in kwargs.items():
            logging.LoggerAdapter(self.logger, {key: value})


# 創建全局日誌實例
logger_instance = Logger()
get_logger = logger_instance.get_logger


# 便捷函數
def log_debug(message: str, **kwargs):
    """記錄除錯日誌"""
    logger = get_logger()
    logger.debug(message, extra=kwargs)


def log_info(message: str, **kwargs):
    """記錄資訊日誌"""
    logger = get_logger()
    logger.info(message, extra=kwargs)


def log_warning(message: str, **kwargs):
    """記錄警告日誌"""
    logger = get_logger()
    logger.warning(message, extra=kwargs)


def log_error(message: str, exc_info=None, **kwargs):
    """記錄錯誤日誌"""
    logger = get_logger()
    logger.error(message, exc_info=exc_info, extra=kwargs)


def log_critical(message: str, exc_info=None, **kwargs):
    """記錄嚴重錯誤日誌"""
    logger = get_logger()
    logger.critical(message, exc_info=exc_info, extra=kwargs)