from sqlalchemy.ext.asyncio import AsyncSession
from app.models.memory import StructuredMemory, EpisodicMemory
from app.repositories.base import BaseRepository
from uuid import UUID
from typing import Optional, List

class StructuredMemoryRepository(BaseRepository[StructuredMemory]):
    """
    StructuredMemoryモデルのためのリポジトリクラス。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(StructuredMemory, session, tenant_id)

    async def get_by_key(self, key: str, user_id: Optional[UUID] = None) -> Optional[StructuredMemory]:
        """
        キーとオプションでユーザーIDに基づいて構造化メモリを取得します。
        """
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.key == key)
        if user_id:
            stmt = stmt.where(self.model.user_id == user_id)
        stmt = self._add_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

class EpisodicMemoryRepository(BaseRepository[EpisodicMemory]):
    """
    EpisodicMemoryモデルのためのリポジトリクラス。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(EpisodicMemory, session, tenant_id)

    async def get_by_session_id(self, session_id: UUID) -> Optional[EpisodicMemory]:
        """
        セッションIDに基づいてエピソード記憶を取得します。
        """
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.session_id == session_id)
        stmt = self._add_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_user_id(self, user_id: UUID) -> List[EpisodicMemory]:
        """
        ユーザーIDに基づいてすべてのエピソード記憶を取得します。
        """
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.desc())
        stmt = self._add_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalars().all()
