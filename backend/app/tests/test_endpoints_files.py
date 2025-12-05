import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID, uuid4
from io import BytesIO
from datetime import datetime
import unittest

from app.main import app
from app.schemas.auth import AuthenticatedUser
from app.schemas.file import FileUploadResponse
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.services.file_service import FileService
from app.services.rag_service import RagService
from app.dependencies import get_current_user
from app.dependencies import get_knowledge_document_repository, get_file_service, get_rag_service
from app.core.config import settings

# TestClientインスタンス
client = TestClient(app)

# Fixtures for mocking dependencies
@pytest.fixture
def mock_current_user():
    return AuthenticatedUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="test@example.com",
        is_active=True,
        is_admin=False
    )

@pytest.fixture
def override_get_current_user(mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_file_service():
    return AsyncMock(spec=FileService)

@pytest.fixture
def override_get_file_service(mock_file_service):
    app.dependency_overrides[get_file_service] = lambda: mock_file_service
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_knowledge_document_repository():
    return AsyncMock(spec=KnowledgeDocumentRepository)

@pytest.fixture
def override_get_knowledge_document_repository(mock_knowledge_document_repository):
    app.dependency_overrides[get_knowledge_document_repository] = lambda: mock_knowledge_document_repository
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_rag_service():
    return AsyncMock(spec=RagService)

@pytest.fixture
def override_get_rag_service(mock_rag_service):
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    yield
    app.dependency_overrides.clear()

# Test Cases
@pytest.mark.asyncio
async def test_upload_file_global_rag_success(
    override_get_current_user,
    override_get_file_service,
    override_get_knowledge_document_repository,
    override_get_rag_service,
    mock_current_user,
    mock_file_service,
    mock_knowledge_document_repository,
    mock_rag_service
):
    """
    ファイルをアップロードし、グローバルRAGに登録する成功ケースをテストします。
    """
    file_content = b"This is a test document."
    mock_file = BytesIO(file_content)
    file_name = "test.txt"
    file_id = uuid4()

    mock_file_service.save_file.return_value = MagicMock(
        id=file_id,
        tenant_id=mock_current_user.tenant_id,
        file_name=file_name,
        file_path="/path/to/test.txt",
        file_type="text/plain",
        file_size=str(len(file_content)),
        uploaded_by_user_id=mock_current_user.id,
        is_active=True
    )
    mock_file_service.extract_text_from_knowledge_document.return_value = file_content.decode("utf-8")
    mock_knowledge_document_repository.create.return_value = FileUploadResponse(
        id=file_id,
        tenant_id=mock_current_user.tenant_id,
        file_name=file_name,
        file_path="/path/to/test.txt",
        file_type="text/plain",
        file_size=str(len(file_content)),
        uploaded_by_user_id=mock_current_user.id,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_rag_service.add_documents_to_global_rag.return_value = None

    response = client.post(
        "/api/v1/files/upload",
        files={"file": (file_name, mock_file, "text/plain")}
    )

    assert response.status_code == 200
    assert response.json()["file_name"] == file_name
    mock_file_service.save_file.assert_awaited_once()
    mock_file_service.extract_text_from_knowledge_document.assert_awaited_once()
    mock_rag_service.add_documents_to_global_rag.assert_awaited_once()
    mock_knowledge_document_repository.create.assert_awaited_once()
    mock_rag_service.add_documents_to_ephemeral_rag.assert_not_awaited() # Ephemeralは呼ばれないことを確認

@pytest.mark.asyncio
async def test_upload_file_ephemeral_rag_success(
    override_get_current_user,
    override_get_file_service,
    override_get_knowledge_document_repository,
    override_get_rag_service,
    mock_current_user,
    mock_file_service,
    mock_knowledge_document_repository,
    mock_rag_service
):
    """
    ファイルをアップロードし、Ephemeral RAGに登録する成功ケースをテストします。
    """
    file_content = b"This is a session-specific document."
    mock_file = BytesIO(file_content)
    file_name = "session_doc.md"
    file_id = uuid4()
    session_id = uuid4()

    mock_file_service.save_file.return_value = MagicMock(
        id=file_id,
        tenant_id=mock_current_user.tenant_id,
        file_name=file_name,
        file_path="/path/to/session_doc.md",
        file_type="text/markdown",
        file_size=str(len(file_content)),
        uploaded_by_user_id=mock_current_user.id,
        is_active=True
    )
    mock_file_service.extract_text_from_knowledge_document.return_value = file_content.decode("utf-8")
    mock_knowledge_document_repository.create.return_value = FileUploadResponse(
        id=file_id,
        tenant_id=mock_current_user.tenant_id,
        file_name=file_name,
        file_path="/path/to/session_doc.md",
        file_type="text/markdown",
        file_size=str(len(file_content)),
        uploaded_by_user_id=mock_current_user.id,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_rag_service.add_documents_to_ephemeral_rag.return_value = None

    response = client.post(
        f"/api/v1/files/upload?session_id={session_id}",
        files={"file": (file_name, mock_file, "text/markdown")}
    )

    assert response.status_code == 200
    assert response.json()["file_name"] == file_name
    mock_file_service.save_file.assert_awaited_once()
    mock_file_service.extract_text_from_knowledge_document.assert_awaited_once()
    mock_rag_service.add_documents_to_ephemeral_rag.assert_awaited_once_with(
        session_id, pytest.approx(unittest.mock.ANY, abs=0) 
    )
    # Use ANY from unittest.mock
    from unittest.mock import ANY
    mock_rag_service.add_documents_to_ephemeral_rag.assert_awaited_once_with(session_id, ANY)
    mock_knowledge_document_repository.create.assert_awaited_once()
    mock_rag_service.add_documents_to_global_rag.assert_not_awaited() # Globalは呼ばれないことを確認

@pytest.mark.asyncio
async def test_upload_file_no_filename(
    override_get_current_user,
    override_get_file_service,
    override_get_knowledge_document_repository,
    override_get_rag_service,
):
    """
    ファイル名がない場合のアップロード失敗ケースをテストします。
    """
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("", BytesIO(b"content"), "text/plain")}
    )
    assert response.status_code in [400, 422]
    # assert "No file name provided." in response.json()["detail"] # Detail might vary for 422

@pytest.mark.asyncio
async def test_upload_file_validation_error(
    override_get_current_user,
    override_get_file_service,
    override_get_knowledge_document_repository,
    override_get_rag_service,
    mock_file_service
):
    """
    ファイルバリデーションエラー時のアップロード失敗ケースをテストします。
    """
    mock_file_service.save_file.side_effect = HTTPException(
        status_code=413, detail="File size exceeds the limit."
    )

    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("large_file.txt", BytesIO(b"a"* (settings.MAX_FILE_SIZE_MB * 1024 * 1024 + 1)), "text/plain")}
    )
    assert response.status_code == 413
    assert "File size exceeds the limit." in response.json()["detail"]
    mock_file_service.save_file.assert_awaited_once() # validate_fileはsave_file内で呼ばれる

# TODO: unauthorized access (get_current_user)のテストはtest_endpoints_authに任せる
