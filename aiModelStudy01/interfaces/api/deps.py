"""FastAPI 依赖注入 - 解决 QA 问题 3（租户隔离）"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from aiModelStudy01.infrastructure import decode_token
from aiModelStudy01.infrastructure.cache.redis_client import is_token_blacklisted
from aiModelStudy01.infrastructure.database import get_db
from aiModelStudy01.infrastructure.repositories.message_repo import MessageRepository
from aiModelStudy01.infrastructure.repositories.session_repo import SessionRepository

# HTTP Bearer 认证
security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """从 JWT Token 获取当前用户 ID（问题 12：Token 黑名单检查）"""
    token = credentials.credentials

    # 解码 Token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token",
        )

    # 检查 Token 是否在黑名单（问题 12）
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效",
        )

    # 检查 Token 是否过期
    exp = payload.get("exp")
    if exp:
        from datetime import datetime, timezone
        if datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已过期",
            )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token",
        )

    return user_id


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async for session in get_db():
        yield session


def get_session_repo(
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> SessionRepository:
    """获取会话仓储"""
    return SessionRepository(db)


def get_message_repo(
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> MessageRepository:
    """获取消息仓储"""
    return MessageRepository(db)


# 类型别名
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
SessionRepo = Annotated[SessionRepository, Depends(get_session_repo)]
MessageRepo = Annotated[MessageRepository, Depends(get_message_repo)]