"""会话路由"""
from typing import Annotated

from fastapi import APIRouter, HTTPException, status

from aiModelStudy01.application import SessionUseCase
from aiModelStudy01.core.const import Provider
from aiModelStudy01.core.exceptions import SessionNotFoundError
from aiModelStudy01.core.models import (
    CreateSessionRequest,
    MessageResponse,
    SessionResponse,
)
from aiModelStudy01.interfaces.api.deps import CurrentUserId, SessionRepo, MessageRepo

router = APIRouter(prefix="/session", tags=["Session"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建会话",
)
async def create_session(
    request: CreateSessionRequest,
    user_id: CurrentUserId,
    session_repo: SessionRepo,
    message_repo: MessageRepo,
):
    """创建新会话"""
    use_case = SessionUseCase(
        session_repo=session_repo,
        message_repo=message_repo,
        user_id=user_id,
    )

    return await use_case.create_session(
        provider=request.provider,
        model=request.model,
        title=request.title,
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="获取会话",
    responses={
        200: {"description": "会话详情"},
        403: {"description": "无权访问"},
        404: {"description": "会话不存在"},
    },
)
async def get_session(
    session_id: str,
    user_id: CurrentUserId,
    session_repo: SessionRepo,
    message_repo: MessageRepo,
):
    """获取会话详情"""
    use_case = SessionUseCase(
        session_repo=session_repo,
        message_repo=message_repo,
        user_id=user_id,
    )

    try:
        return await use_case.get_session(session_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "",
    response_model=list[SessionResponse],
    summary="获取会话列表",
)
async def list_sessions(
    user_id: CurrentUserId,
    session_repo: SessionRepo,
    message_repo: MessageRepo,
    limit: int = 50,
    offset: int = 0,
):
    """获取用户的所有会话"""
    use_case = SessionUseCase(
        session_repo=session_repo,
        message_repo=message_repo,
        user_id=user_id,
    )

    return await use_case.list_sessions(limit=limit, offset=offset)


@router.get(
    "/{session_id}/messages",
    response_model=list[MessageResponse],
    summary="获取历史消息",
)
async def get_messages(
    session_id: str,
    user_id: CurrentUserId,
    session_repo: SessionRepo,
    message_repo: MessageRepo,
    limit: int = 100,
    offset: int = 0,
):
    """获取会话的历史消息"""
    use_case = SessionUseCase(
        session_repo=session_repo,
        message_repo=message_repo,
        user_id=user_id,
    )

    return await use_case.get_messages(
        session_id=session_id,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除会话",
)
async def delete_session(
    session_id: str,
    user_id: CurrentUserId,
    session_repo: SessionRepo,
    message_repo: MessageRepo,
):
    """删除会话"""
    use_case = SessionUseCase(
        session_repo=session_repo,
        message_repo=message_repo,
        user_id=user_id,
    )

    try:
        await use_case.delete_session(session_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{session_id}/title",
    response_model=SessionResponse,
    summary="更新会话标题",
)
async def update_session_title(
    session_id: str,
    title: str,
    user_id: CurrentUserId,
    session_repo: SessionRepo,
    message_repo: MessageRepo,
):
    """更新会话标题"""
    use_case = SessionUseCase(
        session_repo=session_repo,
        message_repo=message_repo,
        user_id=user_id,
    )

    try:
        return await use_case.update_session_title(session_id, title)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))