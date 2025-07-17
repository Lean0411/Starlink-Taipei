"""
基礎設施層例外定義 - 處理外部系統相關的例外
"""

from typing import Any, Dict, Optional


class InfrastructureException(Exception):
    """基礎設施層基礎例外類別"""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """初始化基礎設施例外
        
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
        
        
class DatabaseException(InfrastructureException):
    """資料庫相關例外"""
    pass


class ConnectionError(DatabaseException):
    """資料庫連接錯誤"""
    
    def __init__(self, database: str, reason: str):
        super().__init__(
            message=f"無法連接到資料庫 {database}: {reason}",
            code="DB_CONNECTION_ERROR",
            details={
                "database": database,
                "reason": reason
            }
        )


class QueryError(DatabaseException):
    """查詢錯誤"""
    
    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"查詢執行失敗: {reason}",
            code="DB_QUERY_ERROR",
            details={
                "query": query[:100] + "..." if len(query) > 100 else query,
                "reason": reason
            }
        )


class ExternalAPIException(InfrastructureException):
    """外部 API 相關例外"""
    pass


class APIConnectionError(ExternalAPIException):
    """API 連接錯誤"""
    
    def __init__(self, api_name: str, url: str, reason: str):
        super().__init__(
            message=f"無法連接到 {api_name} API: {reason}",
            code="API_CONNECTION_ERROR",
            details={
                "api_name": api_name,
                "url": url,
                "reason": reason
            }
        )


class APIResponseError(ExternalAPIException):
    """API 回應錯誤"""
    
    def __init__(self, api_name: str, status_code: int, response: Any):
        super().__init__(
            message=f"{api_name} API 返回錯誤: {status_code}",
            code="API_RESPONSE_ERROR",
            details={
                "api_name": api_name,
                "status_code": status_code,
                "response": str(response)[:500]
            }
        )


class CacheException(InfrastructureException):
    """快取相關例外"""
    pass


class CacheConnectionError(CacheException):
    """快取連接錯誤"""
    
    def __init__(self, cache_type: str, reason: str):
        super().__init__(
            message=f"無法連接到 {cache_type} 快取: {reason}",
            code="CACHE_CONNECTION_ERROR",
            details={
                "cache_type": cache_type,
                "reason": reason
            }
        )


class FileSystemException(InfrastructureException):
    """檔案系統相關例外"""
    pass


class FileNotFoundError(FileSystemException):
    """檔案未找到"""
    
    def __init__(self, file_path: str):
        super().__init__(
            message=f"檔案未找到: {file_path}",
            code="FILE_NOT_FOUND",
            details={"file_path": file_path}
        )


class FileAccessError(FileSystemException):
    """檔案存取錯誤"""
    
    def __init__(self, file_path: str, operation: str, reason: str):
        super().__init__(
            message=f"無法 {operation} 檔案 {file_path}: {reason}",
            code="FILE_ACCESS_ERROR",
            details={
                "file_path": file_path,
                "operation": operation,
                "reason": reason
            }
        )


class ConfigurationException(InfrastructureException):
    """配置相關例外"""
    
    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"配置錯誤 {config_key}: {reason}",
            code="CONFIGURATION_ERROR",
            details={
                "config_key": config_key,
                "reason": reason
            }
        )