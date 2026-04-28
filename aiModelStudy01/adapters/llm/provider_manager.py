"""模型提供商管理器 - 解决 QA 问题 8（Provider 无熔断/fallback）"""
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from aiModelStudy01.core.base import LLMAdapter
from aiModelStudy01.core.const import Provider
from aiModelStudy01.core.exceptions import ProviderNotFoundError, ProviderError, ProviderTimeoutError
from aiModelStudy01.infrastructure.config import get_settings

if TYPE_CHECKING:
    from aiModelStudy01.adapters.llm.minimax import MiniMaxAdapter
    from aiModelStudy01.adapters.llm.openai import OpenAIAdapter
    from aiModelStudy01.adapters.llm.anthropic import AnthropicAdapter


class CircuitState:
    """熔断器状态"""
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 断开，快速失败
    HALF_OPEN = "half_open"  # 尝试恢复


class CircuitBreaker:
    """熔断器实现（问题 8）"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._failure_count = 0
        self._last_failure_time = 0
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        return self._state

    def record_failure(self):
        """记录失败"""
        self._failure_count += 1
        self._last_failure_time = 0  # will be set on next check

    def record_success(self):
        """记录成功"""
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        import time
        current_time = time.time()

        if self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_failure_time = current_time
                return False
            return True

        elif self._state == CircuitState.OPEN:
            if current_time - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                return True
            return False

        elif self._state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self.half_open_max_calls:
                return False
            self._half_open_calls += 1
            return True

        return False

    def __repr__(self):
        return f"<CircuitBreaker state={self._state} failures={self._failure_count}>"


class ProviderManager:
    """模型提供商管理器

    职责：
    1. 统一管理多个 Provider 的适配器
    2. 实现熔断器模式（问题 8）
    3. 提供 fallback 机制（问题 8）
    4. Provider 选择逻辑
    """

    def __init__(self):
        self._adapters: dict[str, LLMAdapter] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._fallback_provider: str | None = None
        self._default_provider: str | None = None
        self._settings = get_settings()

    def register_adapter(self, provider: Provider, adapter: LLMAdapter, is_default: bool = False):
        """注册适配器"""
        self._adapters[provider.value] = adapter
        self._circuit_breakers[provider.value] = CircuitBreaker()

        if is_default or self._default_provider is None:
            self._default_provider = provider.value

    def set_fallback_provider(self, provider: Provider):
        """设置备用 Provider（问题 8 fallback）"""
        if provider.value not in self._adapters:
            raise ProviderNotFoundError(provider.value)
        self._fallback_provider = provider.value

    def get_adapter(self, provider: str) -> LLMAdapter:
        """获取适配器 - 不返回 None，明确抛出异常（问题 8）"""
        if provider not in self._adapters:
            raise ProviderNotFoundError(provider)
        return self._adapters[provider]

    def get_circuit_breaker(self, provider: str) -> CircuitBreaker:
        """获取熔断器"""
        return self._circuit_breakers.get(provider, CircuitBreaker())

    def _update_circuit_state(self, provider: str, success: bool):
        """更新熔断器状态"""
        cb = self.get_circuit_breaker(provider)
        if success:
            cb.record_success()
        else:
            cb.record_failure()

    async def chat_with_circuit_break(
        self, provider: str, request, **kwargs
    ):
        """带熔断的聊天请求（问题 8）"""
        cb = self.get_circuit_breaker(provider)

        if not cb.can_execute():
            # 尝试 fallback
            if self._fallback_provider and self._fallback_provider != provider:
                return await self.chat_with_circuit_break(
                    self._fallback_provider, request, **kwargs
                )
            raise ProviderError(
                provider=provider,
                message="Provider 当前不可用（熔断器断开），请稍后重试",
            )

        adapter = self.get_adapter(provider)
        try:
            response = await adapter.chat(request, **kwargs)
            self._update_circuit_state(provider, success=True)
            return response
        except ProviderTimeoutError:
            self._update_circuit_state(provider, success=False)
            raise
        except Exception as e:
            self._update_circuit_state(provider, success=False)
            raise ProviderError(provider=provider, message=str(e))

    async def get_available_providers(self) -> list[str]:
        """获取当前可用的 Providers"""
        available = []
        for provider in self._adapters:
            cb = self.get_circuit_breaker(provider)
            if cb.can_execute():
                adapter = self._adapters[provider]
                try:
                    if await adapter.health_check():
                        available.append(provider)
                except Exception:
                    pass
        return available


# 全局 Provider 管理器
_provider_manager: ProviderManager | None = None


def get_provider_manager() -> ProviderManager:
    """获取全局 Provider 管理器"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
        _initialize_providers(_provider_manager)
    return _provider_manager


def _initialize_providers(manager: ProviderManager):
    """初始化所有注册的 Providers"""
    from aiModelStudy01.adapters.llm.minimax import MiniMaxAdapter
    from aiModelStudy01.adapters.llm.openai import OpenAIAdapter
    from aiModelStudy01.adapters.llm.anthropic import AnthropicAdapter

    settings = get_settings()

    # MiniMax
    if settings.minimax_api_key:
        manager.register_adapter(
            Provider.MINIMAX,
            MiniMaxAdapter(
                api_key=settings.minimax_api_key,
                base_url=settings.minimax_base_url,
                default_model=settings.minimax_model,
            ),
            is_default=True,
        )

    # OpenAI
    if settings.openai_api_key:
        manager.register_adapter(
            Provider.OPENAI,
            OpenAIAdapter(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                default_model=settings.openai_model,
            ),
        )

    # Anthropic
    if settings.anthropic_api_key:
        manager.register_adapter(
            Provider.ANTHROPIC,
            AnthropicAdapter(
                api_key=settings.anthropic_api_key,
                base_url=settings.anthropic_base_url,
                default_model=settings.anthropic_model,
            ),
        )


async def close_all_providers():
    """关闭所有 Provider 的客户端连接"""
    manager = get_provider_manager()
    for adapter in manager._adapters.values():
        await adapter.close()