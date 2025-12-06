"""Create t_user_settings table

Revision ID: 001_add_user_settings
Revises: 
Create Date: 2025-12-06 15:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_user_settings'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    t_user_settings テーブルを作成します。
    
    このテーブルはユーザーごとの設定（テーマ、言語、フォントサイズ、オンボーディング状態）を保存します。
    """
    op.create_table(
        't_user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('theme', sa.String(), nullable=False, server_default='light'),
        sa.Column('language', sa.String(), nullable=False, server_default='ja'),
        sa.Column('font_size', sa.String(), nullable=False, server_default='medium'),
        sa.Column('llm_profile', sa.String(), nullable=True),
        sa.Column('has_seen_onboarding', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('onboarding_skipped', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['t_tenant.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['t_user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'user_id', name='uq_user_settings_tenant_user')
    )
    op.create_index(op.f('ix_t_user_settings_id'), 't_user_settings', ['id'], unique=False)
    op.create_index(op.f('ix_t_user_settings_tenant_id'), 't_user_settings', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_t_user_settings_user_id'), 't_user_settings', ['user_id'], unique=False)


def downgrade() -> None:
    """
    t_user_settings テーブルを削除します（ロールバック）。
    """
    op.drop_index(op.f('ix_t_user_settings_user_id'), table_name='t_user_settings')
    op.drop_index(op.f('ix_t_user_settings_tenant_id'), table_name='t_user_settings')
    op.drop_index(op.f('ix_t_user_settings_id'), table_name='t_user_settings')
    op.drop_table('t_user_settings')
