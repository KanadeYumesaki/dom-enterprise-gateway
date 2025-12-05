from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeDocument
from app.repositories.base import BaseRepository
from uuid import UUID
from typing import Optional, List

class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    """
    ナレッジドキュメントモデルのためのリポジトリクラス。
    """
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        super().__init__(KnowledgeDocument, session, tenant_id)

    async def get_by_filepath(self, file_path: str) -> Optional[KnowledgeDocument]:
        """ファイルパスに基づいてナレッジドキュメントを取得します。"""
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.file_path == file_path)
        stmt = self._add_tenant_filter(stmt)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(self, query: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[KnowledgeDocument]:
        """
        ファイル名に基づいてナレッジドキュメントを検索します。
        """
        from sqlalchemy import select
        stmt = select(self.model)
        if query:
            stmt = stmt.where(self.model.file_name.ilike(f"%{query}%")) # 大文字小文字を区別しない部分一致検索
        
        stmt = self._add_tenant_filter(stmt)
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
