"""AI Model Gateway 核心模块

统一 DTO、异常定义、适配器抽象接口。
"""
from aiModelStudy01.core.base import LLMAdapter
from aiModelStudy01.core.const import ErrorCode, MessageRole, Provider
from aiModelStudy01.core.exceptions import (
    AppException,
    AuthenticationError,
    ProviderError,
    ProviderNotFoundError,
    RateLimitError,
    SessionForbiddenError,
    SessionNotFoundError,
    TokenExpiredError,
    ValidationError,
)
from aiModelStudy01.core.models import (
    AuthTokenRequest,
    AuthTokenResponse,
    ChatChunk,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    MessageResponse,
    SessionResponse,
)

__all__ = [
    # 基类
    "LLMAdapter",
    # 常量
    "ErrorCode",
    "MessageRole",
    "Provider",
    # 异常
    "AppException",
    "AuthenticationError",
    "TokenExpiredError",
    "ProviderError",
    "ProviderNotFoundError",
    "SessionNotFoundError",
    "SessionForbiddenError",
    "RateLimitError",
    "ValidationError",
    # 模型
    "AuthTokenRequest",
    "AuthTokenResponse",
    "ChatChunk",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ErrorResponse",
    "HealthResponse",
    "MessageResponse",
    "SessionResponse",
]