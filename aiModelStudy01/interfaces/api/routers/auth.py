"""认证路由"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aiModelStudy01.core.models import AuthTokenRequest, AuthTokenResponse, ErrorResponse
from aiModelStudy01.infrastructure import hash_password, verify_password, create_token_for_user
from aiModelStudy01.infrastructure.repositories.session_repo import SessionRepository
from aiModelStudy01.interfaces.api.deps import get_current_user_id, SessionRepo

router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer()


@router.post(
    "/token",
    response_model=AuthTokenResponse,
    summary="获取访问令牌",
    responses={
        200: {"description": "登录成功"},
        401: {"description": "用户名或密码错误"},
    },
)
async def get_token(
    request: AuthTokenRequest,
    session_repo: SessionRepo,
):
    """用户名密码登录，获取 JWT Token

    注意：生产环境应使用更安全的认证方式
    """
    from sqlalchemy import select
    from aiModelStudy01.infrastructure.models import User

    result = await session_repo._session.execute(
        select(User).where(User.username == request.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    return create_token_for_user(user.id, user.username)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="注册用户",
)
async def register(
    request: AuthTokenRequest,
    session_repo: SessionRepo,
):
    """注册新用户"""
    from sqlalchemy import select
    from aiModelStudy01.infrastructure.models import User

    result = await session_repo._session.execute(
        select(User).where(User.username == request.username)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 创建用户
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
    )
    session_repo._session.add(user)
    await session_repo._session.flush()

    return {"message": "注册成功", "username": user.username}