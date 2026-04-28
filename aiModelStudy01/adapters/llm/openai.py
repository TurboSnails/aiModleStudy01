"""OpenAI 模型适配器"""
import asyncio
from typing import AsyncGenerator

import httpx
from openai import AsyncOpenAI

from aiModelStudy01.core.base import LLMAdapter
from aiModelStudy01.core.const import Provider
from aiModelStudy01.core.exceptions import ProviderError, ProviderTimeoutError
from aiModelStudy01.core.models import ChatChunk, ChatRequest, ChatResponse


class OpenAIAdapter(LLMAdapter):
    """OpenAI 模型适配器"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o-mini",
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._default_model = default_model
        self._client: AsyncOpenAI | None = None

    async def _get_client(self) -> AsyncOpenAI:
        """延迟初始化客户端"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                http_client=httpx.AsyncClient(timeout=120.0),
            )
        return self._client

    async def close(self):
        """显式关闭客户端"""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def provider_name(self) -> str:
        return Provider.OPENAI.value

    @property
    def default_model(self) -> str:
        return self._default_model

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            await client.chat.completions.create(
                model=self._default_model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False

    async def chat(self, request: ChatRequest) -> ChatResponse:
        try:
            client = await self._get_client()
            model = request.model or self._default_model

            messages = [
                {"role": msg.role.value if hasattr(msg.role, 'value') else msg.role, "content": msg.content}
                for msg in request.messages
            ]

            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    messages=messages,
                ),
                timeout=120,
            )

            choice = response.choices[0]
            content = choice.message.content or ""

            return ChatResponse(
                error=False,
                content=content,
                model=model,
                usage={
                    "input_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                    "output_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                },
                provider=self.provider_name,
                response_id=response.id,
            )

        except asyncio.TimeoutError:
            raise ProviderTimeoutError(provider=self.provider_name, timeout=120)
        except Exception as e:
            raise ProviderError(provider=self.provider_name, message=str(e))

    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[ChatChunk, None]:
        try:
            client = await self._get_client()
            model = request.model or self._default_model

            messages = [
                {"role": msg.role.value if hasattr(msg.role, 'value') else msg.role, "content": msg.content}
                for msg in request.messages
            ]

            stream = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    messages=messages,
                    stream=True,
                ),
                timeout=120,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield ChatChunk(
                        type="content",
                        content=chunk.choices[0].delta.content,
                        done=False,
                    )

            yield ChatChunk(type="done", content="", done=True)

        except asyncio.TimeoutError:
            yield ChatChunk(type="error", content=f"[{self.provider_name}] 请求超时")
        except Exception as e:
            yield ChatChunk(type="error", content=str(e))