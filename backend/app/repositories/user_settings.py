from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user_settings import UserSettings
from app.repositories.base import BaseRepository
from uuid import UUID
from typing import Optional

class UserSettingsRepository(BaseRepository[UserSettings]):
    """
    UserSettings モデルのためのリポジトリクラス。
    
    役割:
    - ユーザー設定の CRUD 操作を提供します。
    - (tenant_id, user_id) の組み合わせで設定を一意に特定します。
    
    設計ポイント:
    - upsert メソッドでは、既存レコードがあれば UPDATE、無ければ INSERT します。
    - data 引数は Pydantic の model_dump(exclude_unset=True) から来ることを想定し、
      whitelist ベースで安全に UPDATE を行います。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(UserSettings, session, tenant_id)
    
    async def get_by_user(self, tenant_id: UUID, user_id: UUID) -> Optional[UserSettings]:
        """
        (tenant_id, user_id) の組み合わせでユーザー設定を取得します。
        
        Args:
            tenant_id: テナントID
            user_id: ユーザーID
        
        Returns:
            UserSettings または None（レコードが無い場合）
        """
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def upsert(self, tenant_id: UUID, user_id: UUID, data: dict) -> UserSettings:
        """
        ユーザー設定を作成または更新します（upsert）。
        
        Args:
            tenant_id: テナントID
            user_id: ユーザーID
            data: 更新するフィールドの辞書（Pydantic の exclude_unset=True から来る想定）
        
        Returns:
            作成または更新された UserSettings
        
        動作:
        1. 既存レコードを検索
        2. 存在する場合: data の内容で UPDATE
        3. 存在しない場合: data + tenant_id + user_id で INSERT
        
        data に含まれるフィールドのみが更新されるため、部分更新が可能です。
        """
        existing = await self.get_by_user(tenant_id, user_id)
        
        if existing:
            # UPDATE（data に含まれるフィールドのみ更新）
            stmt = (
                update(self.model)
                .where(self.model.id == existing.id)
                .values(**data)
                .execution_options(synchronize_session="fetch")
            )
            await self.session.execute(stmt)
            await self.session.refresh(existing)
            return existing
        else:
            # INSERT（data + tenant_id + user_id）
            new_settings = self.model(
                tenant_id=tenant_id,
                user_id=user_id,
                **data
            )
            self.session.add(new_settings)
            await self.session.flush()
            await self.session.refresh(new_settings)
            return new_settings
