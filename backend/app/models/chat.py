from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.core.database import Base
from app.models.user import User
from app.models.tenant import Tenant

class ChatSession(Base):
    """
    チャットセッションモデル。
    ユーザーとテナントに紐づき、一連のチャットメッセージを保持します。
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('t_user.id'), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('t_tenant.id'), nullable=False, index=True)
    title = Column(String, nullable=True) # セッションのタイトル
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    tenant = relationship("Tenant", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession(id='{self.id}', user_id='{self.user_id}', title='{self.title}')>"

class ChatMessage(Base):
    """
    チャットメッセージモデル。
    特定のチャットセッションに属する個々のメッセージを保持します。
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('t_chat_session.id'), nullable=False, index=True)
    role = Column(String, nullable=False) # 例: "user", "assistant", "system"
    content = Column(Text, nullable=False)
    raw_llm_response = Column(JSON, nullable=True) # LLMからの生の応答（JSON形式）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id='{self.id}', session_id='{self.session_id}', role='{self.role}')>"

# Add back_populates to User and Tenant for chat_sessions
User.chat_sessions = relationship("ChatSession", back_populates="user")
Tenant.chat_sessions = relationship("ChatSession", back_populates="tenant")
