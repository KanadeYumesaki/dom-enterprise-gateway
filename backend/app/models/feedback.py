from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.core.database import Base

class Feedback(Base):
    """
    ユーザーからのフィードバックを保存するモデル。
    LLMの応答に対する評価やコメントを記録します。
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('t_tenant.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('t_user.id'), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('t_chat_session.id'), nullable=True, index=True) # どのセッションでのフィードバックか
    message_id = Column(UUID(as_uuid=True), ForeignKey('t_chat_message.id'), nullable=True, index=True) # どのメッセージに対するフィードバックか
    rating = Column(Integer, nullable=False) # 例: -1 (👎), 0 (未評価), 1 (👍)
    comment = Column(Text, nullable=True) # 自由記述コメント
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Feedback(id='{self.id}', rating={self.rating}, user_id='{self.user_id}')>"
