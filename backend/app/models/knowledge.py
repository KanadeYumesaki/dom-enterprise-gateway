from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.core.database import Base

class KnowledgeDocument(Base):
    """
    ナレッジドキュメントモデル。RAGのソースとなるドキュメントのメタデータを保持します。
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('t_tenant.id'), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False, unique=True) # ストレージ内のパス
    file_type = Column(String, nullable=True)
    file_size = Column(String, nullable=True) # バイト単位ではなく文字列で保存
    uploaded_by_user_id = Column(UUID(as_uuid=True), ForeignKey('t_user.id'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<KnowledgeDocument(id='{self.id}', file_name='{self.file_name}', tenant_id='{self.tenant_id}')>"
