"""MiniMax 模型适配器 - 解决 QA 问题 7（httpx 连接池泄漏）"""
import asyncio
from collections.abc import AsyncGenerator

import anthropic
from anthropic import AsyncAnthropic

from aiModelStudy01.core.base import LLMAdapter
from aiModelStudy01.core.const import Provider
from aiModelStudy01.core.exceptions import ProviderError, ProviderTimeoutError
from aiModelStudy01.core.models import ChatChunk, ChatRequest, ChatResponse


class MiniMaxAdapter(LLMAdapter):
    """MiniMax 模型适配器

    使用 context manager 管理客户端生命周期，避免连接池泄漏（问题 7）。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.minimaxi.com/anthropic",
        default_model: str = "MiniMax-M2",
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._default_model = default_model
        self._client: AsyncAnthropic | None = None

    async def _get_client(self) -> AsyncAnthropic:
        """延迟初始化客户端（解决连接池泄漏问题 7）"""
        if self._client is None:
            self._client = AsyncAnthropic(
                base_url=self._base_url,
                api_key=self._api_key,
                http_client=anthropic.DEFAULT_TIMEOUT,
            )
        return self._client

    async def close(self):
        """显式关闭客户端（问题 7）"""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def provider_name(self) -> str:
        return Provider.MINIMAX.value

    @property
    def default_model(self) -> str:
        return self._default_model

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            client = await self._get_client()
            await client.messages.create(
                model=self._default_model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """同步对话"""
        try:
            client = await self._get_client()
            model = request.model or self._default_model

            # 转换消息格式
            messages = [
                {"role": msg.role.value if hasattr(msg.role, 'value') else msg.role, "content": msg.content}
                for msg in request.messages
            ]

            response = await asyncio.wait_for(
                client.messages.create(
                    model=model,
                    max_tokens=request.max_tokens,
                    messages=messages,
                ),
                timeout=120,
            )

            # 解析响应
            text_content = ""
            thinking_content = ""
            for block in response.content:
                if getattr(block, "type", "") == "thinking":
                    thinking_content += getattr(block, "thinking", "")
                elif getattr(block, "type", "") == "text":
                    text_content += getattr(block, "text", "")

            content = text_content or thinking_content

            return ChatResponse(
                error=False,
                content=content,
                thinking=thinking_content,
                model=model,
                usage={
                    "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                    "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0,
                },
                provider=self.provider_name,
                response_id=getattr(response, "id", None),
            )

        except TimeoutError:
            raise ProviderTimeoutError(provider=self.provider_name, timeout=120)
        except Exception as e:
            raise ProviderError(provider=self.provider_name, message=str(e))

    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[ChatChunk, None]:
        """流式对话"""
        try:
            client = await self._get_client()
            model = request.model or self._default_model

            messages = [
                {"role": msg.role.value if hasattr(msg.role, 'value') else msg.role, "content": msg.content}
                for msg in request.messages
            ]

            async with client.messages.stream(
                model=model,
                max_tokens=request.max_tokens,
                messages=messages,
            ) as stream:
                async for text_event in stream.text_stream:
                    yield ChatChunk(type="content", content=text_event, done=False)

                await stream.get_final_message()
                yield ChatChunk(
                    type="done",
                    content="",
                    done=True,
                )

        except TimeoutError:
            yield ChatChunk(type="error", content=f"[{self.provider_name}] 请求超时")
        except Exception as e:
            yield ChatChunk(type="error", content=str(e))
