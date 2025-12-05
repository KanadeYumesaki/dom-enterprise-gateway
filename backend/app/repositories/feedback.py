from sqlalchemy.ext.asyncio import AsyncSession
from app.models.feedback import Feedback
from app.repositories.base import BaseRepository
from uuid import UUID
from typing import Optional, List

class FeedbackRepository(BaseRepository[Feedback]):
    """
    Feedbackモデルのためのリポジトリクラス。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(Feedback, session, tenant_id)

    async def get_by_session_id(self, session_id: UUID) -> List[Feedback]:
        """セッションIDに基づいてフィードバックのリストを取得します。"""
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.session_id == session_id).order_by(self.model.created_at.desc())
        stmt = self._add_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_message_id(self, message_id: UUID) -> Optional[Feedback]:
        """メッセージIDに基づいて単一のフィードバックを取得します。"""
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.message_id == message_id)
        stmt = self._add_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
