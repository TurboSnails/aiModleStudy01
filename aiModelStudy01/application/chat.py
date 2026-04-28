"""对话用例 - 解决 QA 问题 9（流式消息丢失风险）"""
from typing import AsyncGenerator

from aiModelStudy01.adapters.llm.provider_manager import get_provider_manager
from aiModelStudy01.core.const import MessageRole
from aiModelStudy01.core.exceptions import ValidationError, RateLimitError
from aiModelStudy01.core.models import ChatChunk, ChatRequest, ChatResponse, ChatMessage
from aiModelStudy01.infrastructure.cache.redis_client import check_rate_limit, get_rate_limit_ttl
from aiModelStudy01.infrastructure.config import get_settings
from aiModelStudy01.infrastructure.repositories.message_repo import MessageRepository
from aiModelStudy01.infrastructure.repositories.session_repo import SessionRepository


class ChatUseCase:
    """对话用例

    职责：
    1. 编排对话流程
    2. 处理流式响应的消息持久化（问题 9）
    3. 限流检查（问题 11）
    """

    def __init__(
        self,
        session_repo: SessionRepository,
        message_repo: MessageRepository,
        user_id: str,
    ):
        self._session_repo = session_repo
        self._message_repo = message_repo
        self._user_id = user_id
        self._settings = get_settings()
        self._provider_manager = get_provider_manager()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """单轮对话"""
        # 限流检查（问题 11）
        await self._check_rate_limit()

        # 验证 session 归属（问题 3）
        session = await self._session_repo.get_by_id(request.provider.value, self._user_id)
        if not session:
            # 创建新会话
            session = await self._session_repo.create(
                user_id=self._user_id,
                provider=request.provider.value,
                model=request.model or self._provider_manager.get_adapter(request.provider.value).default_model,
                title=self._extract_title(request.messages),
            )

        # 持久化用户消息
        await self._message_repo.create(
            session_id=session.id,
            role=MessageRole.USER.value,
            content=request.messages[-1].content if request.messages else "",
        )

        # 调用 LLM（带熔断器）
        adapter = self._provider_manager.get_adapter(request.provider.value)
        response = await self._provider_manager.chat_with_circuit_break(
            request.provider.value, request
        )

        # 持久化助手消息
        await self._message_repo.create(
            session_id=session.id,
            role=MessageRole.ASSISTANT.value,
            content=response.content,
            metadata={"model": response.model, "usage": response.usage},
        )

        # 更新会话时间戳
        await self._session_repo.touch(session.id, self._user_id)

        return response

    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[ChatChunk, None]:
        """流式对话

        注意：消息先流式返回客户端，再异步持久化（问题 9）。
        这确保用户能立即看到响应，但如果持久化失败，消息可能丢失。
        """
        # 限流检查
        await self._check_rate_limit()

        # 获取或创建会话
        session = await self._session_repo.get_by_id(request.provider.value, self._user_id)
        if not session:
            model = request.model or self._provider_manager.get_adapter(request.provider.value).default_model
            session = await self._session_repo.create(
                user_id=self._user_id,
                provider=request.provider.value,
                model=model,
                title=self._extract_title(request.messages),
            )

        # 持久化用户消息
        user_content = request.messages[-1].content if request.messages else ""
        user_msg = await self._message_repo.create(
            session_id=session.id,
            role=MessageRole.USER.value,
            content=user_content,
        )

        # 流式调用 LLM
        adapter = self._provider_manager.get_adapter(request.provider.value)
        collected_content = []
        collected_thinking = []

        try:
            async for chunk in adapter.chat_stream(request):
                if chunk.type == "content":
                    collected_content.append(chunk.content)
                    yield chunk
                elif chunk.type == "thinking":
                    collected_thinking.append(chunk.content)
                    yield chunk
                elif chunk.type == "done":
                    yield chunk
                elif chunk.type == "error":
                    yield chunk

            # 流式结束后，异步持久化助手消息
            full_content = "".join(collected_content)
            full_thinking = "".join(collected_thinking)
            if full_content or full_thinking:
                await self._message_repo.create(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT.value,
                    content=full_content,
                    metadata={
                        "model": request.model or adapter.default_model,
                        "thinking": full_thinking,
                    },
                )

        except Exception as e:
            # 流式出错时，yield 错误信息
            yield ChatChunk(type="error", content=str(e))
            # 已流式返回的消息无法撤回，但错误已经告知客户端

        # 更新会话时间戳
        await self._session_repo.touch(session.id, self._user_id)

    async def _check_rate_limit(self):
        """限流检查（问题 11）"""
        if not self._settings.rate_limit_enabled:
            return

        is_allowed, remaining = await check_rate_limit(
            self._user_id,
            self._settings.rate_limit_requests_per_minute,
            60,  # 60 秒窗口
        )

        if not is_allowed:
            ttl = await get_rate_limit_ttl(self._user_id)
            raise RateLimitError(
                limit=self._settings.rate_limit_requests_per_minute,
                window=60,
            )

    def _extract_title(self, messages: list[ChatMessage]) -> str:
        """从消息中提取会话标题"""
        if not messages:
            return "新会话"

        first_user_msg = next(
            (m.content for m in messages if m.role == MessageRole.USER),
            None
        )

        if first_user_msg:
            # 取前 50 个字符作为标题
            return first_user_msg[:50] + ("..." if len(first_user_msg) > 50 else "")
        return "新会话"