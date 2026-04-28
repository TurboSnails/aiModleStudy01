"""抽象接口定义 - 适配器基类（解决 QA 问题 1, 16）"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator

from aiModelStudy01.core.models import ChatRequest, ChatResponse, ChatChunk


class LLMAdapter(ABC):
    """LLM 适配器抽象基类

    所有模型适配器必须实现此接口，保证类型安全（问题 1）。
    插件系统通过继承此基类实现 AOP 拦截（问题 16）。
    """

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """同步对话，返回统一响应结构"""
        ...

    @abstractmethod
    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[ChatChunk, None]:
        """流式对话，yield 统一 chunk 结构"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """检查 Provider 是否可用"""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称"""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """默认模型"""
        ...