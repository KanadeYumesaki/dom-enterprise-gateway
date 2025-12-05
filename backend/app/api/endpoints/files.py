from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import Annotated, List
from uuid import UUID

from app.schemas.file import FileUploadResponse
from app.schemas.auth import AuthenticatedUser
from app.dependencies import get_current_user
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.services.file_service import FileService
from app.services.rag_service import RagService
from app.dependencies import get_knowledge_document_repository, get_file_service, get_rag_service

router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse, summary="ファイルをアップロードし、ナレッジドキュメントとして登録 (任意でEphemeral RAGへ)")
async def upload_file(
    file: Annotated[UploadFile, File(description="アップロードするファイル")],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
    knowledge_repo: Annotated[KnowledgeDocumentRepository, Depends(get_knowledge_document_repository)],
    rag_service: Annotated[RagService, Depends(get_rag_service)],
    session_id: Annotated[Optional[UUID], None] = None # Optional session_id for ephemeral RAG
):
    """
    ファイルをアップロードし、そのメタデータをナレッジドキュメントとしてデータベースに保存します。
    ファイルからテキストを抽出し、ベクトルストアにインデックス化します。
    `session_id`が指定された場合、そのセッションに紐づくEphemeral RAGにドキュメントを追加します。
    指定されない場合、グローバルRAGにドキュメントを追加します。
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file name provided."
        )

    # ファイルをストレージに保存し、仮のKnowledgeDocumentオブジェクトを取得
    knowledge_doc = await file_service.save_file(file, current_user.tenant_id, current_user.id)
    
    # テキストを抽出
    extracted_text = await file_service.extract_text_from_knowledge_document(knowledge_doc)

    # 抽出したテキストをLangChainのDocument形式に変換
    from langchain_core.documents import Document as LC_Document
    lc_document = LC_Document(
        page_content=extracted_text,
        metadata={
            "document_id": str(knowledge_doc.id),
            "tenant_id": str(knowledge_doc.tenant_id),
            "file_name": knowledge_doc.file_name,
            "file_type": knowledge_doc.file_type,
            "uploaded_by": str(knowledge_doc.uploaded_by_user_id),
            "session_id": str(session_id) if session_id else None # エフェメラルRAGの場合にセッションIDを追加
        }
    )

    # Ephemeral RAG または Global RAG にドキュメントを追加
    if session_id:
        await rag_service.add_documents_to_ephemeral_rag(session_id, [lc_document])
    else:
        await rag_service.add_documents_to_global_rag([lc_document])

    # KnowledgeDocumentメタデータをデータベースに保存
    db_knowledge_doc = await knowledge_repo.create(knowledge_doc.model_dump(exclude={"id"}))
    
    return FileUploadResponse.model_validate(db_knowledge_doc)
