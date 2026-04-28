"""消息仓储"""
import json
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from aiModelStudy01.infrastructure.models import Message as MessageModel


class MessageRepository:
    """消息数据访问层"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> MessageModel:
        """创建消息"""
        message = MessageModel(
            session_id=session_id,
            role=role,
            content=content,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def get_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MessageModel]:
        """获取会话的所有消息（按时间升序）"""
        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_session_message_count(self, session_id: str) -> int:
        """获取会话消息数量"""
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.count(MessageModel.id)).where(
                MessageModel.session_id == session_id
            )
        )
        return result.scalar_one()

    async def delete_session_messages(self, session_id: str) -> int:
        """删除会话的所有消息"""
        result = await self._session.execute(
            delete(MessageModel).where(MessageModel.session_id == session_id)
        )
        return result.rowcount

    def deserialize_metadata(self, message: MessageModel) -> dict:
        """反序列化 metadata（问题 10：SQLite JSON 兼容性）"""
        if message.metadata_json:
            try:
                return json.loads(message.metadata_json)
            except json.JSONDecodeError:
                return {}
        return {}