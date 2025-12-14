from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.core.database import Base

class UserSettings(Base):
    """
    ユーザー設定モデル。
    
    役割:
    - ユーザーごとのUI設定（テーマ・言語・フォントサイズ）を保存します。
    - オンボーディングツアーの表示状態を管理します。
    - P1で拡張予定のLLMプロファイル設定フィールドを用意します。
    
    いつ使うか:
    - Settings画面でユーザー設定を取得・更新する際に使用。
    - 各セッションでユーザーの設定を反映する際に参照。
    
    テーブル設計:
    - (tenant_id, user_id) の組み合わせで1レコード（ユニーク制約）。
    - created_at / updated_at は既存モデル（Tenant, User, ChatSession）と同じパターンを踏襲。
    - Alembic マイグレーション alembic/versions/XXXX_add_user_settings_table.py で作成されます。
    """
    __tablename__ = "t_user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('t_tenant.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('t_user.id'), nullable=False, index=True)
    
    # UI設定
    theme = Column(String, default="light", nullable=False)
    language = Column(String, default="ja", nullable=False)
    font_size = Column(String, default="medium", nullable=False)
    llm_profile = Column(String, nullable=True)  # P1拡張用: LLMプロファイル選択
    
    # オンボーディング
    has_seen_onboarding = Column(Boolean, default=False, nullable=False)
    onboarding_skipped = Column(Boolean, default=False, nullable=False)
    
    # タイムスタンプ（既存モデルと同じパターン）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now(), nullable=False)
    
   # ユニーク制約: (tenant_id, user_id) の組み合わせで1レコード
    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', name='uq_user_settings_tenant_user'),
    )
    
    # Relationships
    tenant = relationship("Tenant", backref="user_settings")
    user = relationship("User", backref="settings")
    
    def __repr__(self):
        return f"<UserSettings(id='{self.id}', user_id='{self.user_id}', theme='{self.theme}')>"
