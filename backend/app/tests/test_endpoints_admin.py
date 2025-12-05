import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from app.main import app
from app.schemas.auth import AuthenticatedUser
from app.schemas.file import FileUploadResponse
from app.dependencies import get_current_user, get_current_admin_user
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.dependencies import get_knowledge_document_repository

# TestClientインスタンス
client = TestClient(app)

# Fixtures for mocking dependencies
@pytest.fixture
def mock_admin_user():
    return AuthenticatedUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="admin@example.com",
        is_active=True,
        is_admin=True
    )

@pytest.fixture
def mock_non_admin_user():
    return AuthenticatedUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="user@example.com",
        is_active=True,
        is_admin=False
    )

@pytest.fixture
def override_get_current_admin_user(mock_admin_user):
    app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def override_get_current_user_non_admin(mock_non_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_non_admin_user
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

# Test Cases
@pytest.mark.asyncio
async def test_list_knowledge_documents_success(
    override_get_current_admin_user,
    override_get_knowledge_document_repository,
    mock_admin_user,
    mock_knowledge_document_repository
):
    """
    管理者によるナレッジドキュメント一覧取得の成功ケースをテストします。
    """
    mock_docs = [
        FileUploadResponse(
            id=uuid4(), tenant_id=mock_admin_user.tenant_id, file_name="doc1.pdf", file_path="/path/doc1.pdf",
            file_type="application/pdf", file_size="1MB", uploaded_by_user_id=mock_admin_user.id,
            is_active=True, created_at=datetime.now(), updated_at=datetime.now()
        ),
        FileUploadResponse(
            id=uuid4(), tenant_id=mock_admin_user.tenant_id, file_name="report.docx", file_path="/path/report.docx",
            file_type="application/docx", file_size="2MB", uploaded_by_user_id=mock_admin_user.id,
            is_active=True, created_at=datetime.now(), updated_at=datetime.now()
        )
    ]
    mock_knowledge_document_repository.search.return_value = mock_docs

    response = client.get("/api/v1/admin/knowledge")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["file_name"] == "doc1.pdf"
    mock_knowledge_document_repository.search.assert_awaited_once_with(query=None, skip=0, limit=100)

@pytest.mark.asyncio
async def test_list_knowledge_documents_search(
    override_get_current_admin_user,
    override_get_knowledge_document_repository,
    mock_admin_user,
    mock_knowledge_document_repository
):
    """
    管理者によるナレッジドキュメント検索の成功ケースをテストします。
    """
    mock_docs = [
        FileUploadResponse(
            id=uuid4(), tenant_id=mock_admin_user.tenant_id, file_name="project_spec.pdf", file_path="/path/spec.pdf",
            file_type="application/pdf", file_size="1MB", uploaded_by_user_id=mock_admin_user.id,
            is_active=True, created_at=datetime.now(), updated_at=datetime.now()
        )
    ]
    mock_knowledge_document_repository.search.return_value = mock_docs

    response = client.get("/api/v1/admin/knowledge?search_query=spec")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["file_name"] == "project_spec.pdf"
    mock_knowledge_document_repository.search.assert_awaited_once_with(query="spec", skip=0, limit=100)

@pytest.mark.asyncio
async def test_list_knowledge_documents_unauthorized(
    override_get_current_user_non_admin,
    override_get_knowledge_document_repository,
    mock_knowledge_document_repository # Add missing fixture
):
    """
    非管理者ユーザーによるナレッジドキュメント一覧取得の失敗ケースをテストします。
    """
    response = client.get("/api/v1/admin/knowledge")
    assert response.status_code == 403
    assert "Not enough privileges" in response.json()["detail"]
    mock_knowledge_document_repository.search.assert_not_awaited() # searchは呼ばれない
