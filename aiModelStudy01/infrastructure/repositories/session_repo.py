"""会话仓储 - 解决 QA 问题 3（租户数据隔离）"""
from collections.abc import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aiModelStudy01.infrastructure.models import Session as SessionModel


class SessionRepository:
    """会话数据访问层 - 强制租户隔离"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        user_id: str,
        provider: str,
        model: str,
        title: str = "新会话",
    ) -> SessionModel:
        """创建新会话"""
        session = SessionModel(
            user_id=user_id,
            provider=provider,
            model=model,
            title=title,
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def get_by_id(self, session_id: str, user_id: str) -> SessionModel | None:
        """获取会话 - 必须包含 user_id 过滤（问题 3：租户隔离）"""
        result = await self._session.execute(
            select(SessionModel).where(
                SessionModel.id == session_id,
                SessionModel.user_id == user_id,  # 强制租户隔离
            )
        )
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[SessionModel]:
        """获取用户的所有会话"""
        result = await self._session.execute(
            select(SessionModel)
            .where(SessionModel.user_id == user_id)
            .order_by(SessionModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def update_title(self, session_id: str, user_id: str, title: str) -> bool:
        """更新会话标题"""
        result = await self._session.execute(
            update(SessionModel)
            .where(
                SessionModel.id == session_id,
                SessionModel.user_id == user_id,
            )
            .values(title=title)
        )
        return result.rowcount > 0

    async def delete(self, session_id: str, user_id: str) -> bool:
        """删除会话 - 强制租户校验"""
        result = await self._session.execute(
            delete(SessionModel).where(
                SessionModel.id == session_id,
                SessionModel.user_id == user_id,
            )
        )
        return result.rowcount > 0

    async def touch(self, session_id: str, user_id: str) -> bool:
        """更新会话时间戳（保持活跃）"""
        from datetime import datetime
        result = await self._session.execute(
            update(SessionModel)
            .where(
                SessionModel.id == session_id,
                SessionModel.user_id == user_id,
            )
            .values(updated_at=datetime.utcnow())
        )
        return result.rowcount > 0
