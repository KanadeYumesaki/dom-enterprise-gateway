from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.core.database import Base

class StructuredMemory(Base):
    """
    構造化メモリモデル。テナント、ユーザー、プロジェクトに紐づく設定、プロファイル、方針などの構造化された情報を保持します。
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('t_tenant.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('t_user.id'), nullable=True, index=True) # ユーザーに紐づかないグローバルな構造化メモリもありうる
    key = Column(String, nullable=False, index=True) # メモリのキー (例: "user_preference", "project_policy")
    value = Column(JSON, nullable=False) # JSON形式で値を保存
    description = Column(Text, nullable=True) # メモリの目的や内容の説明
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<StructuredMemory(id='{self.id}', key='{self.key}', tenant_id='{self.tenant_id}')>"

class EpisodicMemory(Base):
    """
    エピソード記憶モデル。チャットセッションの要約、決まったこと、今後の前提などを保持します。
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('t_tenant.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('t_user.id'), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('t_chat_session.id'), nullable=False, index=True)
    summary = Column(Text, nullable=False) # セッションの要約
    decisions = Column(JSON, nullable=True) # 決定事項 (JSONリストなど)
    assumptions = Column(JSON, nullable=True) # 今後の前提 (JSONリストなど)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<EpisodicMemory(id='{self.id}', session_id='{self.session_id}', summary='{self.summary[:30]}...')>"
