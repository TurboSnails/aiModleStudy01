"""核心层测试"""
import pytest
from pydantic import ValidationError

from aiModelStudy01.core.const import Provider, MessageRole, ErrorCode
from aiModelStudy01.core.models import ChatRequest, ChatMessage, ChatResponse
from aiModelStudy01.core.exceptions import AppException


def test_provider_enum():
    """测试 Provider 枚举"""
    assert Provider.MINIMAX.value == "minimax"
    assert Provider.OPENAI.value == "openai"
    assert Provider.ANTHROPIC.value == "anthropic"


def test_message_role_enum():
    """测试 MessageRole 枚举"""
    assert MessageRole.USER.value == "user"
    assert MessageRole.ASSISTANT.value == "assistant"
    assert MessageRole.SYSTEM.value == "system"


def test_chat_message_validation():
    """测试 ChatMessage 验证"""
    # 有效消息
    msg = ChatMessage(role=MessageRole.USER, content="Hello")
    assert msg.content == "Hello"

    # 空内容应该被拒绝
    with pytest.raises(ValidationError):
        ChatMessage(role=MessageRole.USER, content="")


def test_chat_request_validation():
    """测试 ChatRequest 验证"""
    # 无消息列表
    with pytest.raises(ValidationError):
        ChatRequest(provider=Provider.MINIMAX, messages=[])

    # 有效请求
    request = ChatRequest(
        provider=Provider.MINIMAX,
        messages=[
            ChatMessage(role=MessageRole.SYSTEM, content="You are helpful"),
            ChatMessage(role=MessageRole.USER, content="Hi"),
        ],
        max_tokens=500,
        temperature=0.8,
    )

    assert len(request.messages) == 2
    assert request.max_tokens == 500
    assert request.temperature == 0.8
    assert request.stream is False


def test_chat_request_invalid_temperature():
    """测试无效 temperature"""
    with pytest.raises(ValidationError):
        ChatRequest(
            provider=Provider.MINIMAX,
            messages=[ChatMessage(role=MessageRole.USER, content="Hi")],
            temperature=3.0,  # 超出 0-2 范围
        )


def test_chat_response_from_error():
    """测试从错误创建 Response"""
    response = ChatResponse.from_error("Something went wrong", 500)
    assert response.error is True
    assert response.content == "Something went wrong"
    assert response.usage["error_code"] == 500


def test_app_exception_to_dict():
    """测试异常转字典"""
    error = AppException(
        code=ErrorCode.PROVIDER_UNAVAILABLE,
        message="Provider is down",
        status_code=503,
        request_id="req_123",
    )

    error_dict = error.to_dict()

    assert "error" in error_dict
    assert error_dict["error"]["code"] == "PROVIDER_UNAVAILABLE"
    assert error_dict["error"]["message"] == "Provider is down"
    assert error_dict["error"]["request_id"] == "req_123"