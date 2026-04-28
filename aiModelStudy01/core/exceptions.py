"""业务异常定义 - 统一错误响应格式（解决 QA 问题 21）"""
from typing import Any

from aiModelStudy01.core.const import ErrorCode


class AppException(Exception):
    """应用层基础异常"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.request_id = request_id
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """统一错误响应格式"""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
                "request_id": self.request_id,
            }
        }


class AuthenticationError(AppException):
    """认证错误"""

    def __init__(self, message: str = "认证失败", **kwargs):
        super().__init__(
            code=ErrorCode.AUTH_TOKEN_INVALID,
            message=message,
            status_code=401,
            **kwargs,
        )


class TokenExpiredError(AuthenticationError):
    def __init__(self, **kwargs):
        super().__init__(
            message="Token 已过期",
            code=ErrorCode.AUTH_TOKEN_EXPIRED,
            **kwargs,
        )


class ProviderError(AppException):
    """AI 提供商错误"""

    def __init__(self, provider: str, message: str, **kwargs):
        super().__init__(
            code=ErrorCode.PROVIDER_UNAVAILABLE,
            message=f"[{provider}] {message}",
            status_code=503,
            details={"provider": provider},
            **kwargs,
        )


class ProviderNotFoundError(AppException):
    """提供商不存在"""

    def __init__(self, provider: str):
        super().__init__(
            code=ErrorCode.PROVIDER_NOT_FOUND,
            message=f"未知的 AI 提供商: {provider}",
            status_code=404,
            details={"provider": provider},
        )


class ProviderTimeoutError(ProviderError):
    def __init__(self, provider: str, timeout: int):
        super().__init__(
            provider=provider,
            message=f"请求超时 ({timeout}s)",
            code=ErrorCode.PROVIDER_TIMEOUT,
        )


class SessionNotFoundError(AppException):
    def __init__(self, session_id: str):
        super().__init__(
            code=ErrorCode.SESSION_NOT_FOUND,
            message=f"会话不存在: {session_id}",
            status_code=404,
            details={"session_id": session_id},
        )


class SessionForbiddenError(AppException):
    """访问其他用户的会话"""

    def __init__(self, session_id: str, user_id: str):
        super().__init__(
            code=ErrorCode.SESSION_FORBIDDEN,
            message="无权访问此会话",
            status_code=403,
            details={"session_id": session_id},
        )


class RateLimitError(AppException):
    def __init__(self, limit: int, window: int):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="请求过于频繁，请等待后再试",
            status_code=429,
            details={"limit": limit, "window_seconds": window},
        )


class ValidationError(AppException):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=400,
            details={"field": field} if field else {},
        )
