"""
API 錯誤處理中間件
"""

import traceback
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ....application.exceptions import (
    ApplicationException,
    InvalidRequestError,
    ResourceNotFoundException,
    ValidationException,
)
from ....domain.exceptions import DomainException
from ....infrastructure.exceptions import InfrastructureException


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """統一錯誤處理中間件"""
    
    async def dispatch(self, request: Request, call_next):
        """處理請求並捕獲例外"""
        # 生成請求 ID
        request_id = str(uuid.uuid4())
        
        try:
            # 處理請求
            response = await call_next(request)
            return response
            
        except HTTPException:
            # FastAPI 的 HTTP 例外直接拋出
            raise
            
        except Exception as exc:
            # 處理其他所有例外
            error_response = self._handle_exception(exc, request_id)
            return JSONResponse(
                status_code=error_response["status_code"],
                content=error_response["content"]
            )
    
    def _handle_exception(self, exc: Exception, request_id: str) -> Dict[str, Any]:
        """處理例外並返回統一格式的錯誤回應
        
        Args:
            exc: 例外實例
            request_id: 請求 ID
            
        Returns:
            Dict[str, Any]: 包含 status_code 和 content 的字典
        """
        # 預設值
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "INTERNAL_ERROR"
        message = "內部伺服器錯誤"
        details = {}
        
        # 根據例外類型設定回應
        if isinstance(exc, ValidationException):
            status_code = status.HTTP_400_BAD_REQUEST
            error_code = exc.code
            message = exc.message
            details = exc.details
            
        elif isinstance(exc, InvalidRequestError):
            status_code = status.HTTP_400_BAD_REQUEST
            error_code = exc.code
            message = exc.message
            details = exc.details
            
        elif isinstance(exc, ResourceNotFoundException):
            status_code = status.HTTP_404_NOT_FOUND
            error_code = exc.code
            message = exc.message
            details = exc.details
            
        elif isinstance(exc, ApplicationException):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            error_code = exc.code
            message = exc.message
            details = exc.details
            
        elif isinstance(exc, DomainException):
            # 領域例外通常是業務邏輯錯誤
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            error_code = exc.code
            message = exc.message
            details = exc.details
            
        elif isinstance(exc, InfrastructureException):
            # 基礎設施例外可能是暫時性的
            if "CONNECTION" in exc.code:
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_code = exc.code
            message = exc.message
            details = exc.details
            
        else:
            # 未知例外
            details = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc() if self._is_debug_mode() else None
            }
        
        # 建立統一的錯誤回應
        content = {
            "status": "error",
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return {
            "status_code": status_code,
            "content": content
        }
    
    def _is_debug_mode(self) -> bool:
        """檢查是否為除錯模式
        
        Returns:
            bool: 是否為除錯模式
        """
        # TODO: 從配置讀取
        import os
        return os.getenv("DEBUG", "false").lower() == "true"


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """建立標準錯誤回應
    
    Args:
        status_code: HTTP 狀態碼
        error_code: 錯誤代碼
        message: 錯誤訊息
        details: 詳細資訊
        
    Returns:
        JSONResponse: 錯誤回應
    """
    content = {
        "status": "error",
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )