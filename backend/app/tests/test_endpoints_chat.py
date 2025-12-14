import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4
from datetime import datetime
import json

from app.main import app
from app.schemas.auth import AuthenticatedUser
from app.schemas.chat import ChatSessionResponse, ChatMessageResponse
from app.repositories.chat import ChatSessionRepository, ChatMessageRepository
from app.services.dom_orchestrator import DomOrchestratorService
from app.dependencies import get_current_user
from app.dependencies import get_chat_session_repository, get_chat_message_repository, get_dom_orchestrator_service

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
def mock_chat_session_repo():
    return AsyncMock(spec=ChatSessionRepository)

@pytest.fixture
def override_get_chat_session_repository(mock_chat_session_repo):
    app.dependency_overrides[get_chat_session_repository] = lambda: mock_chat_session_repo
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_chat_message_repo():
    return AsyncMock(spec=ChatMessageRepository)

@pytest.fixture
def override_get_chat_message_repository(mock_chat_message_repo):
    app.dependency_overrides[get_chat_message_repository] = lambda: mock_chat_message_repo
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_dom_orchestrator_service():
    return AsyncMock(spec=DomOrchestratorService)

@pytest.fixture
def override_get_dom_orchestrator_service(mock_dom_orchestrator_service):
    app.dependency_overrides[get_dom_orchestrator_service] = lambda: mock_dom_orchestrator_service
    yield
    app.dependency_overrides.clear()

# Test Cases
@pytest.mark.asyncio
async def test_create_chat_session_success(
    override_get_current_user,
    override_get_chat_session_repository,
    mock_current_user,
    mock_chat_session_repo
):
    """
    チャットセッション作成APIの成功ケースをテストします。
    """
    session_id = uuid4()
    mock_chat_session_repo.create.return_value = ChatSessionResponse(
        id=session_id,
        user_id=mock_current_user.id,
        tenant_id=mock_current_user.tenant_id,
        title="New Chat",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    response = client.post("/api/v1/chat/sessions", json={"title": "New Chat"})
    assert response.status_code == 201
    assert response.json()["title"] == "New Chat"
    mock_chat_session_repo.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_chat_sessions_success(
    override_get_current_user,
    override_get_chat_session_repository,
    mock_current_user,
    mock_chat_session_repo
):
    """
    チャットセッション一覧取得APIの成功ケースをテストします。
    """
    session_id_1 = uuid4()
    session_id_2 = uuid4()
    mock_sessions = [
        ChatSessionResponse(id=session_id_1, user_id=mock_current_user.id, tenant_id=mock_current_user.tenant_id, title="Session 1", is_active=True, created_at=datetime.now(), updated_at=datetime.now()),
        ChatSessionResponse(id=session_id_2, user_id=mock_current_user.id, tenant_id=mock_current_user.tenant_id, title="Session 2", is_active=True, created_at=datetime.now(), updated_at=datetime.now()),
    ]
    mock_chat_session_repo.get_by_user_id.return_value = mock_sessions

    response = client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["title"] == "Session 1"
    mock_chat_session_repo.get_by_user_id.assert_awaited_once_with(mock_current_user.id)

@pytest.mark.asyncio
async def test_get_chat_sessions_allows_null_updated_at(
    override_get_current_user,
    override_get_chat_session_repository,
    mock_current_user,
    mock_chat_session_repo
):
    """
    updated_at が null のセッションでもレスポンスバリデーションエラーにならないことを確認します。
    """
    session_id = uuid4()
    mock_chat_session_repo.get_by_user_id.return_value = [
        ChatSessionResponse(
            id=session_id,
            user_id=mock_current_user.id,
            tenant_id=mock_current_user.tenant_id,
            title="Legacy Session",
            is_active=True,
            created_at=datetime.now(),
            updated_at=None,
        )
    ]

    response = client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    assert response.json()[0]["updated_at"] is None
    mock_chat_session_repo.get_by_user_id.assert_awaited_once_with(mock_current_user.id)

@pytest.mark.asyncio
async def test_send_chat_message_success(
    override_get_current_user,
    override_get_chat_session_repository,
    override_get_chat_message_repository,
    mock_current_user,
    mock_chat_session_repo,
    mock_chat_message_repo
):
    """
    チャットメッセージ送信APIの成功ケースをテストします（ユーザーメッセージ保存のみ）。
    """
    session_id = uuid4()
    # Mock for existing session check
    mock_chat_session_repo.get.return_value = ChatSessionResponse(
        id=session_id, user_id=mock_current_user.id, tenant_id=mock_current_user.tenant_id, title="Existing Session", is_active=True, created_at=datetime.now(), updated_at=datetime.now()
    )
    # Mock for user message saving
    user_message_id = uuid4()
    mock_chat_message_repo.create.return_value = ChatMessageResponse(
        id=user_message_id, session_id=session_id, role="user", content="Hello", created_at=datetime.now(), updated_at=datetime.now()
    )

    message_payload = {"session_id": str(session_id), "content": "Hello", "role": "user"}
    response = client.post("/api/v1/chat/send", json=message_payload)
    
    assert response.status_code == 200
    assert response.json()["role"] == "user"
    assert response.json()["content"] == "Hello"

    mock_chat_session_repo.get.assert_awaited_once_with(session_id)
    mock_chat_message_repo.create.assert_awaited_once_with({
        "session_id": session_id,
        "role": "user",
        "content": "Hello"
    })

@pytest.mark.asyncio
async def test_send_chat_message_unauthorized_session(
    override_get_current_user,
    override_get_chat_session_repository,
    mock_current_user,
    mock_chat_session_repo
):
    """
    チャットメッセージ送信APIのセッション権限なしケースをテストします。
    """
    session_id = uuid4()
    # Mock for existing session check (user_id mismatch)
    mock_chat_session_repo.get.return_value = ChatSessionResponse(
        id=session_id, user_id=uuid4(), tenant_id=mock_current_user.tenant_id, title="Other User's Session", is_active=True, created_at=datetime.now(), updated_at=datetime.now()
    )

    message_payload = {"session_id": str(session_id), "content": "Hello", "role": "user"}
    response = client.post("/api/v1/chat/send", json=message_payload)
    
    assert response.status_code == 404
    assert "Chat session not found or not authorized." in response.json()["detail"]
    mock_chat_session_repo.get.assert_awaited_once_with(session_id)

@pytest.mark.asyncio
async def test_stream_chat_response_success(
    override_get_current_user,
    override_get_chat_session_repository,
    override_get_chat_message_repository,
    override_get_dom_orchestrator_service,
    mock_current_user,
    mock_chat_session_repo,
    mock_chat_message_repo,
    mock_dom_orchestrator_service
):
    """
    チャット応答ストリーミングAPIの成功ケースをテストします (research_mode=False)。
    """
    session_id = uuid4()
    # Mock for existing session check
    mock_chat_session_repo.get.return_value = ChatSessionResponse(
        id=session_id, user_id=mock_current_user.id, tenant_id=mock_current_user.tenant_id, title="Existing Session", is_active=True, created_at=datetime.now(), updated_at=datetime.now()
    )
    # Mock for last user message
    mock_chat_message_repo.get_by_session_id.return_value = [
        ChatMessageResponse(id=uuid4(), session_id=session_id, role="user", content="Test prompt", created_at=datetime.now(), updated_at=datetime.now())
    ]
    
    # Mock for DomOrchestratorService streaming response (IC-5 light format)
    async def mock_orchestrator_stream():
        yield "**Decision**\nTest Decision.\n\n"
        yield "**Why**\nTest Why.\n\n"
        yield "**Next 3 Actions**\nTest Action 1, Test Action 2, Test Action 3.\n\n"
    mock_dom_orchestrator_service.process_chat_message.return_value = mock_orchestrator_stream()
    
    # Mock for assistant message saving
    mock_chat_message_repo.create.return_value = ChatMessageResponse(
        id=uuid4(), session_id=session_id, role="assistant", content="Formatted response", created_at=datetime.now(), updated_at=datetime.now()
    )

    response = client.get(f"/api/v1/chat/stream/{session_id}?research_mode=false") # research_mode=falseを明示的に渡す
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    full_response_content = ""
    for chunk in response.iter_bytes():
        full_response_content += chunk.decode("utf-8")
    
    expected_stream_parts = [
        "**Decision**\nTest Decision.\n\n",
        "**Why**\nTest Why.\n\n",
        "**Next 3 Actions**\nTest Action 1, Test Action 2, Test Action 3.\n\n",
        "[STREAM_END]"
    ]
    expected_stream = "".join(expected_stream_parts)
    
    assert full_response_content == expected_stream

    mock_chat_session_repo.get.assert_awaited_once_with(session_id)
    mock_chat_message_repo.get_by_session_id.assert_awaited_once_with(session_id)
    mock_dom_orchestrator_service.process_chat_message.assert_called_once_with("Test prompt", str(session_id), False) # Falseを検証
    mock_chat_message_repo.create.assert_awaited_once_with({
        "session_id": session_id,
        "role": "assistant",
        "content": expected_stream.replace("[STREAM_END]", "")
    })

@pytest.mark.asyncio
async def test_stream_chat_response_research_mode_on(
    override_get_current_user,
    override_get_chat_session_repository,
    override_get_chat_message_repository,
    override_get_dom_orchestrator_service,
    mock_current_user,
    mock_chat_session_repo,
    mock_chat_message_repo,
    mock_dom_orchestrator_service
):
    """
    チャット応答ストリーミングAPIの成功ケースをテストします (research_mode=True)。
    """
    session_id = uuid4()
    # Mock for existing session check
    mock_chat_session_repo.get.return_value = ChatSessionResponse(
        id=session_id, user_id=mock_current_user.id, tenant_id=mock_current_user.tenant_id, title="Existing Session", is_active=True, created_at=datetime.now(), updated_at=datetime.now()
    )
    # Mock for last user message
    mock_chat_message_repo.get_by_session_id.return_value = [
        ChatMessageResponse(id=uuid4(), session_id=session_id, role="user", content="Research prompt", created_at=datetime.now(), updated_at=datetime.now())
    ]
    
    # Mock for DomOrchestratorService streaming response (IC-5 light format)
    async def mock_orchestrator_stream():
        yield "**Decision**\nResearch Decision.\n\n"
        yield "**Why**\nResearch Why.\n\n"
        yield "**Next 3 Actions**\nResearch Action 1, Research Action 2, Research Action 3.\n\n"
    mock_dom_orchestrator_service.process_chat_message.return_value = mock_orchestrator_stream()
    
    # Mock for assistant message saving
    mock_chat_message_repo.create.return_value = ChatMessageResponse(
        id=uuid4(), session_id=session_id, role="assistant", content="Formatted research response", created_at=datetime.now(), updated_at=datetime.now()
    )

    response = client.get(f"/api/v1/chat/stream/{session_id}?research_mode=true") # research_mode=trueを渡す
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    full_response_content = ""
    for chunk in response.iter_bytes():
        full_response_content += chunk.decode("utf-8")
    
    expected_stream_parts = [
        "**Decision**\nResearch Decision.\n\n",
        "**Why**\nResearch Why.\n\n",
        "**Next 3 Actions**\nResearch Action 1, Research Action 2, Research Action 3.\n\n",
        "[STREAM_END]"
    ]
    expected_stream = "".join(expected_stream_parts)
    
    assert full_response_content == expected_stream

    mock_chat_session_repo.get.assert_awaited_once_with(session_id)
    mock_chat_message_repo.get_by_session_id.assert_awaited_once_with(session_id)
    mock_dom_orchestrator_service.process_chat_message.assert_called_once_with("Research prompt", str(session_id), True) # Trueを検証
    mock_chat_message_repo.create.assert_awaited_once_with({
        "session_id": session_id,
        "role": "assistant",
        "content": expected_stream.replace("[STREAM_END]", "")
    })

@pytest.mark.asyncio
async def test_stream_chat_response_unauthorized_session(
    override_get_current_user,
    override_get_chat_session_repository,
    mock_current_user,
    mock_chat_session_repo
):
    """
    チャット応答ストリーミングAPIのセッション権限なしケースをテストします。
    """
    session_id = uuid4()
    # Mock for existing session check (user_id mismatch)
    mock_chat_session_repo.get.return_value = ChatSessionResponse(
        id=session_id, user_id=uuid4(), tenant_id=mock_current_user.tenant_id, title="Other User's Session", is_active=True, created_at=datetime.now(), updated_at=datetime.now()
    )

    # get_rag_serviceの依存関係をオーバーライドして、実物のRagService初期化を防ぐ
    from app.dependencies import get_rag_service
    mock_rag_service = AsyncMock()
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    
    try:
        response = client.get(f"/api/v1/chat/stream/{session_id}")
    finally:
        app.dependency_overrides.pop(get_rag_service, None)
    assert response.status_code == 200 # StreamingResponseはHTTP 200を返し、エラーをボディに含める
    assert "ERROR: Unauthorized access or session not found." in response.text
    mock_chat_session_repo.get.assert_awaited_once_with(session_id)
