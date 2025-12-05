from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List, Optional
from uuid import UUID

from app.schemas.auth import AuthenticatedUser
from app.schemas.file import FileUploadResponse
from app.dependencies import get_current_user, get_current_admin_user # 管理者権限が必要
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.dependencies import get_knowledge_document_repository

router = APIRouter()

@router.get("/knowledge", response_model=List[FileUploadResponse], summary="ナレッジドキュメントの一覧と検索 (管理者用)")
async def list_knowledge_documents(
    current_admin_user: Annotated[AuthenticatedUser, Depends(get_current_admin_user)],
    knowledge_repo: Annotated[KnowledgeDocumentRepository, Depends(get_knowledge_document_repository)],
    skip: int = 0,
    limit: int = 100,
    search_query: Optional[str] = None
):
    """
    管理者向けに、ナレッジドキュメントの一覧表示と検索を提供します。
    検索クエリが指定された場合、ファイル名に基づいてフィルタリングします。
    """
    documents = await knowledge_repo.search(query=search_query, skip=skip, limit=limit)
    return [FileUploadResponse.model_validate(doc) for doc in documents]
