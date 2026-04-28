"""对话路由 - 解决 QA 问题 18（SSE Content-Type）"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from aiModelStudy01.application import ChatUseCase, SessionUseCase
from aiModelStudy01.core.exceptions import AppException, ProviderError
from aiModelStudy01.core.models import ChatRequest, ChatResponse, ErrorResponse
from aiModelStudy01.interfaces.api.deps import (
    CurrentUserId,
    MessageRepo,
    SessionRepo,
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="发起对话",
    responses={
        200: {"description": "对话成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        401: {"model": ErrorResponse, "description": "未认证"},
        429: {"model": ErrorResponse, "description": "请求过于频繁"},
        503: {"model": ErrorResponse, "description": "AI 提供商不可用"},
    },
)
async def chat(
    request: ChatRequest,
    user_id: CurrentUserId,
    session_repo: SessionRepo,
    message_repo: MessageRepo,
):
    """单轮对话"""
    use_case = ChatUseCase(
        session_repo=session_repo,
        message_repo=message_repo,
        user_id=user_id,
    )

    try:
        response = await use_case.chat(request)
        return response
    except AppException as e:
        raise e


@router.post(
    "/stream",
    summary="发起流式对话",
    responses={
        200: {"description": "流式对话成功"},
        401: {"description": "未认证"},
        429: {"description": "请求过于频繁"},
        503: {"description": "AI 提供商不可用"},
    },
)
async def chat_stream(
    request: ChatRequest,
    user_id: CurrentUserId,
    session_repo: SessionRepo,
    message_repo: MessageRepo,
):
    """流式对话（Server-Sent Events）

    问题 18：SSE Content-Type 规范化
    """
    use_case = ChatUseCase(
        session_repo=session_repo,
        message_repo=message_repo,
        user_id=user_id,
    )

    async def event_generator():
        try:
            async for chunk in use_case.chat_stream(request):
                yield {
                    "event": chunk.type,
                    "data": chunk.content,
                }
                if chunk.done:
                    break
        except AppException as e:
            yield {"event": "error", "data": e.message}

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )