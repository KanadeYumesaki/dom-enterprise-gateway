from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository
from uuid import UUID
from typing import Optional

class UserRepository(BaseRepository[User]):
    """
    ユーザーモデルのためのリポジトリクラス。
    ユーザー固有のデータ操作をここに定義します。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(User, session, tenant_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """メールアドレスでユーザーを取得します。"""
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.email == email)
        # Authの初期ユーザー作成時にはtenant_idでフィルタリングしない可能性があるため、
        # ここでは直接tenant_idフィルタリングは行わない。
        # _add_tenant_filterはsuper()で呼ばれるため、必要に応じて適用される。
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
