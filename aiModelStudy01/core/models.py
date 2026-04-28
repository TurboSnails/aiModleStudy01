"""统一 DTO 模型（解决 QA 问题 1 - 类型安全）"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from aiModelStudy01.core.const import MessageRole, Provider

# ============ 请求模型 ============

class ChatMessage(BaseModel):
    """对话消息"""
    role: MessageRole
    content: str
    name: str | None = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("消息内容不能为空")
        return v


class ChatRequest(BaseModel):
    """对话请求 - 统一结构"""
    provider: Provider
    model: str | None = None  # 可选，覆盖默认模型
    messages: list[ChatMessage]
    max_tokens: int = Field(default=1000, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = False

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v: list[ChatMessage]) -> list[ChatMessage]:
        if not v:
            raise ValueError("消息列表不能为空")
        return v


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    provider: Provider
    model: str | None = None
    title: str | None = None


class AuthTokenRequest(BaseModel):
    """获取 Token 请求"""
    username: str
    password: str


# ============ 响应模型 ============

class ChatChunk(BaseModel):
    """流式响应块"""
    type: str = "content"  # content | thinking | done
    content: str = ""
    thinking: str | None = None
    done: bool = False


class ChatResponse(BaseModel):
    """对话响应"""
    error: bool = False
    content: str = ""
    thinking: str = ""
    model: str = ""
    usage: dict[str, int] = {}
    provider: str = ""
    response_id: str | None = None

    @classmethod
    def from_error(cls, text: str, status_code: int) -> "ChatResponse":
        return cls(error=True, content=text, usage={"error_code": status_code})


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    user_id: str
    provider: Provider
    model: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime
    metadata: dict[str, Any] = {}


class AuthTokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ErrorResponse(BaseModel):
    """错误响应 - 统一格式"""
    error: dict[str, Any]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    database: str = "unknown"
    redis: str = "unknown"


# ============ 数据库模型 ============

class SessionDB(BaseModel):
    """数据库会话模型"""
    id: str
    user_id: str
    provider: str
    model: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageDB(BaseModel):
    """数据库消息模型"""
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any] = {}
