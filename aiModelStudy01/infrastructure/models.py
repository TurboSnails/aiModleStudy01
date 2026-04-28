"""数据库实体定义"""
import uuid

from sqlalchemy import Column as SAColumn
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from aiModelStudy01.infrastructure.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = SAColumn(String(36), primary_key=True, default=generate_uuid)
    username = SAColumn(String(100), unique=True, nullable=False, index=True)
    password_hash = SAColumn(String(255), nullable=False)
    created_at = SAColumn(DateTime, default=func.now())
    updated_at = SAColumn(DateTime, default=func.now(), onupdate=func.now())

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """会话表"""
    __tablename__ = "sessions"

    id = SAColumn(String(36), primary_key=True, default=generate_uuid)
    user_id = SAColumn(String(36), ForeignKey("users.id"), nullable=False, index=True)
    provider = SAColumn(String(50), nullable=False)
    model = SAColumn(String(100), nullable=False)
    title = SAColumn(String(255), default="新会话")
    created_at = SAColumn(DateTime, default=func.now())
    updated_at = SAColumn(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """消息表 - 支持 JSON 元数据（问题 10）"""
    __tablename__ = "messages"

    id = SAColumn(String(36), primary_key=True, default=generate_uuid)
    session_id = SAColumn(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    role = SAColumn(String(20), nullable=False)  # system/user/assistant
    content = SAColumn(Text, nullable=False)
    metadata_json = SAColumn(Text, nullable=True)  # SQLite 兼容：存为 TEXT
    created_at = SAColumn(DateTime, default=func.now())

    session = relationship("Session", back_populates="messages")
