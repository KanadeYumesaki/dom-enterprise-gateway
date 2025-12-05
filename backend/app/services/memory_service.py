from uuid import UUID
from typing import Optional, List, Dict, Any

from app.repositories.memory import StructuredMemoryRepository, EpisodicMemoryRepository
from app.models.memory import StructuredMemory, EpisodicMemory
from app.schemas.auth import AuthenticatedUser # AuthenticatedUserの型ヒントのためにインポート

class MemoryService:
    """
    StructuredMemoryとEpisodicMemoryのCRUD操作を提供するサービス。
    """
    def __init__(
        self,
        structured_memory_repo: StructuredMemoryRepository,
        episodic_memory_repo: EpisodicMemoryRepository
    ):
        self.structured_memory_repo = structured_memory_repo
        self.episodic_memory_repo = episodic_memory_repo

    # StructuredMemoryに関する操作
    async def create_structured_memory(
        self, user_id: UUID, key: str, value: Dict[str, Any], description: Optional[str] = None
    ) -> StructuredMemory:
        """構造化メモリを作成します。"""
        return await self.structured_memory_repo.create({
            "user_id": user_id,
            "key": key,
            "value": value,
            "description": description
        })

    async def get_structured_memory_by_key(
        self, key: str, user_id: Optional[UUID] = None
    ) -> Optional[StructuredMemory]:
        """キーとオプションでユーザーIDに基づいて構造化メモリを取得します。"""
        return await self.structured_memory_repo.get_by_key(key, user_id)

    async def update_structured_memory(
        self, memory_id: UUID, new_value: Dict[str, Any], new_description: Optional[str] = None
    ) -> Optional[StructuredMemory]:
        """構造化メモリを更新します。"""
        update_data = {"value": new_value}
        if new_description is not None:
            update_data["description"] = new_description
        memory = await self.structured_memory_repo.get(memory_id)
        if memory:
            return await self.structured_memory_repo.update(memory, update_data)
        return None

    async def delete_structured_memory(self, memory_id: UUID) -> Optional[StructuredMemory]:
        """構造化メモリを削除します。"""
        return await self.structured_memory_repo.delete(memory_id)

    # EpisodicMemoryに関する操作
    async def create_episodic_memory(
        self, user_id: UUID, session_id: UUID, summary: str, decisions: Optional[List[str]] = None, assumptions: Optional[List[str]] = None
    ) -> EpisodicMemory:
        """エピソード記憶を作成します。"""
        return await self.episodic_memory_repo.create({
            "user_id": user_id,
            "session_id": session_id,
            "summary": summary,
            "decisions": decisions,
            "assumptions": assumptions
        })

    async def get_episodic_memory_by_session_id(self, session_id: UUID) -> Optional[EpisodicMemory]:
        """セッションIDに基づいてエピソード記憶を取得します。"""
        return await self.episodic_memory_repo.get_by_session_id(session_id)

    async def get_all_episodic_memories_by_user_id(self, user_id: UUID) -> List[EpisodicMemory]:
        """ユーザーIDに基づいてすべてのエピソード記憶を取得します。"""
        return await self.episodic_memory_repo.get_all_by_user_id(user_id)
