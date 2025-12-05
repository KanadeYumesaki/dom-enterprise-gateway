from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import ChatSession, ChatMessage
from app.repositories.base import BaseRepository
from uuid import UUID
from typing import List, Optional

class ChatSessionRepository(BaseRepository[ChatSession]):
    """
    チャットセッションモデルのためのリポジトリクラス。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(ChatSession, session, tenant_id)

    async def get_by_user_id(self, user_id: UUID) -> List[ChatSession]:
        """ユーザーIDに基づいてチャットセッションのリストを取得します。"""
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.user_id == user_id)
        stmt = self._add_tenant_filter(stmt) # tenant_idフィルタも適用
        result = await self.session.execute(stmt)
        return result.scalars().all()

class ChatMessageRepository(BaseRepository[ChatMessage]):
    """
    チャットメッセージモデルのためのリポジトリクラス。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(ChatMessage, session, tenant_id)

    async def get_by_session_id(self, session_id: UUID) -> List[ChatMessage]:
        """セッションIDに基づいてチャットメッセージのリストを取得します。"""
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.session_id == session_id).order_by(self.model.created_at)
        stmt = self._add_tenant_filter(stmt) # tenant_idフィルタも適用
        result = await self.session.execute(stmt)
        return result.scalars().all()
