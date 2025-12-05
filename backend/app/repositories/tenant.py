from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant
from app.repositories.base import BaseRepository
from uuid import UUID
from typing import Optional

class TenantRepository(BaseRepository[Tenant]):
    """
    テナントモデルのためのリポジトリクラス。
    テナント固有のデータ操作をここに定義します。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(Tenant, session, tenant_id)

    async def get_by_name(self, name: str) -> Optional[Tenant]:
        """名前でテナントを取得します。"""
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.name == name)
        # テナントの取得自体はテナント分離の対象外
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
