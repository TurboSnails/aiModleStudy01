"""会话管理用例"""
from aiModelStudy01.core.const import Provider
from aiModelStudy01.core.exceptions import SessionNotFoundError, SessionForbiddenError
from aiModelStudy01.core.models import SessionResponse, MessageResponse
from aiModelStudy01.infrastructure.repositories.message_repo import MessageRepository
from aiModelStudy01.infrastructure.repositories.session_repo import SessionRepository


class SessionUseCase:
    """会话管理用例"""

    def __init__(
        self,
        session_repo: SessionRepository,
        message_repo: MessageRepository,
        user_id: str,
    ):
        self._session_repo = session_repo
        self._message_repo = message_repo
        self._user_id = user_id

    async def create_session(
        self,
        provider: Provider,
        model: str | None = None,
        title: str | None = None,
    ) -> SessionResponse:
        """创建新会话"""
        session = await self._session_repo.create(
            user_id=self._user_id,
            provider=provider.value,
            model=model or "",
            title=title or "新会话",
        )

        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            provider=Provider(session.provider),
            model=session.model,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0,
        )

    async def get_session(self, session_id: str) -> SessionResponse:
        """获取会话详情"""
        session = await self._session_repo.get_by_id(session_id, self._user_id)

        if not session:
            raise SessionNotFoundError(session_id)

        message_count = await self._message_repo.get_session_message_count(session_id)

        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            provider=Provider(session.provider),
            model=session.model,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
        )

    async def list_sessions(self, limit: int = 50, offset: int = 0) -> list[SessionResponse]:
        """获取用户的所有会话"""
        sessions = await self._session_repo.get_user_sessions(
            self._user_id, limit=limit, offset=offset
        )

        result = []
        for session in sessions:
            message_count = await self._message_repo.get_session_message_count(session.id)
            result.append(SessionResponse(
                id=session.id,
                user_id=session.user_id,
                provider=Provider(session.provider),
                model=session.model,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count,
            ))

        return result

    async def get_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MessageResponse]:
        """获取会话的历史消息"""
        # 验证会话归属（问题 3：租户隔离）
        session = await self._session_repo.get_by_id(session_id, self._user_id)
        if not session:
            raise SessionNotFoundError(session_id)

        messages = await self._message_repo.get_by_session(
            session_id, limit=limit, offset=offset
        )

        return [
            MessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                metadata=self._message_repo.deserialize_metadata(msg),
            )
            for msg in messages
        ]

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        session = await self._session_repo.get_by_id(session_id, self._user_id)
        if not session:
            raise SessionNotFoundError(session_id)

        # 删除消息
        await self._message_repo.delete_session_messages(session_id)

        # 删除会话
        return await self._session_repo.delete(session_id, self._user_id)

    async def update_session_title(self, session_id: str, title: str) -> SessionResponse:
        """更新会话标题"""
        session = await self._session_repo.get_by_id(session_id, self._user_id)
        if not session:
            raise SessionNotFoundError(session_id)

        await self._session_repo.update_title(session_id, self._user_id, title)
        session.title = title

        message_count = await self._message_repo.get_session_message_count(session_id)

        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            provider=Provider(session.provider),
            model=session.model,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
        )