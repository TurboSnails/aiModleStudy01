"""测试配置"""
import pytest
import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from aiModelStudy01.infrastructure.database import Base
from aiModelStudy01.infrastructure.models import User
from aiModelStudy01.infrastructure.security import hash_password


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """测试数据库（内存 SQLite）"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """测试用户"""
    user = User(
        username="test_user",
        password_hash=hash_password("test_password"),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_session(test_db: AsyncSession, test_user: User):
    """测试会话"""
    from aiModelStudy01.infrastructure.models import Session

    session = Session(
        user_id=test_user.id,
        provider="minimax",
        model="MiniMax-M2",
        title="测试会话",
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    return session