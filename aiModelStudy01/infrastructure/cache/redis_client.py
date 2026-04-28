"""Redis 缓存层 - 解决 QA 问题 2（缓存穿透）"""
import json

import redis.asyncio as redis

from aiModelStudy01.infrastructure.config import get_settings

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """获取 Redis 客户端（延迟初始化）"""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis():
    """关闭 Redis 连接"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def health_check_redis() -> bool:
    """Redis 健康检查"""
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        return False


# ============ 会话缓存（解决 QA 问题 2）============

SESSION_NOT_FOUND_TTL = 60  # "会话不存在"标记的 TTL


async def cache_get_session(session_id: str) -> dict | str | None:
    """从缓存获取会话"""
    client = await get_redis()
    data = await client.get(f"session:{session_id}")
    if data:
        return json.loads(data)
    return None


async def cache_set_session(session_id: str, data: dict, ttl: int = 3600):
    """缓存会话数据"""
    client = await get_redis()
    await client.setex(f"session:{session_id}", ttl, json.dumps(data))


async def cache_set_session_not_found(session_id: str):
    """设置"会话不存在"标记（解决 QA 问题 2：缓存穿透）"""
    client = await get_redis()
    await client.setex(f"session_not_found:{session_id}", SESSION_NOT_FOUND_TTL, "1")


async def cache_is_session_not_found(session_id: str) -> bool:
    """检查是否是"会话不存在"标记"""
    client = await get_redis()
    return await client.exists(f"session_not_found:{session_id}") > 0


async def cache_delete_session(session_id: str):
    """删除会话缓存"""
    client = await get_redis()
    await client.delete(f"session:{session_id}", f"session_not_found:{session_id}")


# ============ Token 黑名单（解决 QA 问题 12）============

async def add_token_to_blacklist(jti: str, expires_in: int):
    """将 Token 加入黑名单"""
    client = await get_redis()
    await client.setex(f"token_blacklist:{jti}", expires_in, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """检查 Token 是否在黑名单中"""
    client = await get_redis()
    return await client.exists(f"token_blacklist:{jti}") > 0


# ============ 限流（问题 11）============

async def check_rate_limit(user_id: str, limit: int, window: int) -> tuple[bool, int]:
    """检查限流

    Returns:
        (is_allowed, remaining) - 是否允许请求，剩余请求数
    """
    client = await get_redis()
    key = f"rate_limit:{user_id}"

    current = await client.get(key)
    if current is None:
        await client.setex(key, window, "1")
        return True, limit - 1

    count = int(current)
    if count >= limit:
        return False, 0

    await client.incr(key)
    return True, limit - count - 1


async def get_rate_limit_ttl(user_id: str) -> int:
    """获取限流剩余时间"""
    client = await get_redis()
    return await client.ttl(f"rate_limit:{user_id}")
