"""基础设施层测试"""
import pytest
from unittest.mock import AsyncMock, patch

from aiModelStudy01.infrastructure.security import hash_password, verify_password, create_access_token, decode_token, create_token_for_user
from aiModelStudy01.core.const import Provider


@pytest.mark.asyncio
async def test_password_hash():
    """测试密码哈希"""
    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


@pytest.mark.asyncio
async def test_jwt_token_creation_and_decoding():
    """测试 JWT Token 创建和解码"""
    user_id = "user_123"
    username = "test_user"

    result = create_token_for_user(user_id, username)

    assert "access_token" in result
    assert "token_type" in result
    assert result["token_type"] == "bearer"
    assert "jti" in result

    # 解码验证
    payload = decode_token(result["access_token"])
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["username"] == username


@pytest.mark.asyncio
async def test_invalid_token_decoding():
    """测试无效 Token 解码"""
    payload = decode_token("invalid.token.here")
    assert payload is None


@pytest.mark.asyncio
async def test_provider_not_found_error():
    """测试 Provider 不存在异常"""
    from aiModelStudy01.core.exceptions import ProviderNotFoundError

    error = ProviderNotFoundError("unknown_provider")

    assert error.status_code == 404
    assert error.code.value == "PROVIDER_NOT_FOUND"
    assert "unknown_provider" in error.message


@pytest.mark.asyncio
async def test_session_not_found_error():
    """测试会话不存在异常"""
    from aiModelStudy01.core.exceptions import SessionNotFoundError

    error = SessionNotFoundError("session_abc")

    assert error.status_code == 404
    assert error.code.value == "SESSION_NOT_FOUND"
    assert "session_abc" in error.message