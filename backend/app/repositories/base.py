from typing import Generic, TypeVar, Type, List, Optional
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base # Baseをインポート

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    基底リポジトリクラス。
    一般的なCRUD操作と非同期DBセッション管理を提供します。
    テナントIDによる自動フィルタリングをサポートします。
    """
    def __init__(self, model: Type[ModelType], session: AsyncSession, tenant_id: Optional[UUID] = None):
        self.model = model
        self.session = session
        self.tenant_id = tenant_id

    def _add_tenant_filter(self, stmt):
        """テナントIDが設定されている場合、クエリにテナントフィルタを追加します。"""
        if self.tenant_id and hasattr(self.model, 'tenant_id'):
            return stmt.where(self.model.tenant_id == self.tenant_id)
        return stmt

    async def get(self, id: UUID) -> Optional[ModelType]:
        """IDに基づいて単一のレコードを取得します。テナントIDでフィルタリングします。"""
        stmt = select(self.model).where(self.model.id == id)
        stmt = self._add_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """複数のレコードを取得します。テナントIDでフィルタリングします。"""
        stmt = select(self.model).offset(skip).limit(limit)
        stmt = self._add_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj_in: dict) -> ModelType:
        """新しいレコードを作成します。tenant_idが設定されていれば自動で追加します。"""
        if self.tenant_id and hasattr(self.model, 'tenant_id') and 'tenant_id' not in obj_in:
            obj_in['tenant_id'] = self.tenant_id
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        """既存のレコードを更新します。"""
        # tenant_idが変更されないように保護するロジックを追加することも可能
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> Optional[ModelType]:
        """IDに基づいてレコードを削除します。テナントIDでフィルタリングします。"""
        db_obj = await self.get(id) # get()メソッドが既にテナントIDでフィルタリングするため、ここで再度フィルタリングは不要
        if db_obj:
            await self.session.delete(db_obj)
            await self.session.commit()
        return db_obj
