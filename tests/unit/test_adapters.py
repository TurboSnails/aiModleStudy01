"""适配器层测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from aiModelStudy01.adapters.llm.minimax import MiniMaxAdapter
from aiModelStudy01.core.models import ChatRequest, ChatMessage
from aiModelStudy01.core.const import MessageRole


@pytest.mark.asyncio
async def test_minimax_adapter_init():
    """测试 MiniMax 适配器初始化"""
    adapter = MiniMaxAdapter(
        api_key="test-key",
        base_url="https://api.minimaxi.com/anthropic",
        default_model="MiniMax-M2",
    )

    assert adapter.provider_name == "minimax"
    assert adapter.default_model == "MiniMax-M2"
    assert adapter._client is None  # 延迟初始化


@pytest.mark.asyncio
async def test_minimax_adapter_chat_request_validation():
    """测试聊天请求验证"""
    # 无效请求：空消息列表
    with pytest.raises(ValueError):
        ChatRequest(
            provider="minimax",
            messages=[],
        )

    # 有效请求
    request = ChatRequest(
        provider="minimax",
        messages=[ChatMessage(role=MessageRole.USER, content="Hello")],
    )
    assert len(request.messages) == 1
    assert request.max_tokens == 1000  # 默认值


@pytest.mark.asyncio
async def test_circuit_breaker_states():
    """测试熔断器状态转换"""
    from aiModelStudy01.adapters.llm.provider_manager import CircuitBreaker, CircuitState

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    # 初始状态：CLOSED
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # 记录失败，达到阈值后 OPEN
    cb.record_failure()
    cb.record_failure()
    assert cb.can_execute() is True  # 未达阈值

    cb.record_failure()  # 第3次失败
    assert cb.can_execute() is False
    assert cb.state == CircuitState.OPEN

    # 成功后重置
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True