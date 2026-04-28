"""JWT 安全模块 - 解决 QA 问题 5, 12（Secret 安全 + Token 注销）"""
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from aiModelStudy01.infrastructure.config import get_settings


def hash_password(password: str) -> str:
    """哈希密码（使用 bcrypt 直接）"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """创建 JWT Access Token

    Returns:
        tuple[token, jti] - token 字符串和 jti（用于注销）
    """
    import uuid

    settings = get_settings()
    jti = str(uuid.uuid4())

    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(minutes=settings.jwt_expiration_minutes)
    )
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "iat": now,
    })

    token = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, jti


def decode_token(token: str) -> dict[str, Any] | None:
    """解码 JWT Token"""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def create_token_for_user(user_id: str, username: str) -> dict[str, Any]:
    """为用户创建完整的 token 响应"""
    settings = get_settings()
    token, jti = create_access_token(
        data={"sub": user_id, "username": username},
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.jwt_expiration_minutes * 60,
        "jti": jti,
    }
