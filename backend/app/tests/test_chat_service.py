import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from app.services.chat_service import ChatService
from app.repositories.chat import ChatSessionRepository, ChatMessageRepository
from app.services.memory_service import MemoryService
from app.services.dom_orchestrator import DomOrchestratorService
from app.models.chat import ChatSession, ChatMessage
from app.schemas.auth import AuthenticatedUser
from app.schemas.chat import ChatSessionResponse

@pytest.fixture
def mock_chat_session_repo():
    return AsyncMock(spec=ChatSessionRepository)

@pytest.fixture
def mock_chat_message_repo():
    return AsyncMock(spec=ChatMessageRepository)

@pytest.fixture
def mock_memory_service():
    return AsyncMock(spec=MemoryService)

@pytest.fixture
def mock_dom_orchestrator_service():
    return AsyncMock(spec=DomOrchestratorService)

@pytest.fixture
def chat_service(
    mock_chat_session_repo,
    mock_chat_message_repo,
    mock_memory_service,
    mock_dom_orchestrator_service
):
    return ChatService(
        mock_chat_session_repo,
        mock_chat_message_repo,
        mock_memory_service,
        mock_dom_orchestrator_service
    )

@pytest.fixture
def mock_user():
    return AuthenticatedUser(id=uuid4(), tenant_id=uuid4(), email="test@example.com", is_active=True, is_admin=False)

@pytest.fixture
def mock_session(mock_user):
    return ChatSession(
        id=uuid4(),
        user_id=mock_user.id,
        tenant_id=mock_user.tenant_id,
        title="Test Session",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def mock_messages(mock_session):
    return [
        ChatMessage(id=uuid4(), session_id=mock_session.id, role="user", content="Hello", created_at=datetime.now(), updated_at=datetime.now()),
        ChatMessage(id=uuid4(), session_id=mock_session.id, role="assistant", content="Hi there!", created_at=datetime.now(), updated_at=datetime.now()),
    ]

@pytest.mark.asyncio
async def test_reset_session_success(
    chat_service,
    mock_chat_session_repo,
    mock_chat_message_repo,
    mock_memory_service,
    mock_dom_orchestrator_service,
    mock_user,
    mock_session,
    mock_messages
):
    """セッションリセットの成功テスト"""
    # Mock setup
    mock_chat_session_repo.get.return_value = mock_session
    mock_chat_message_repo.get_by_session_id.return_value = mock_messages
    mock_dom_orchestrator_service.summarize_chat_history.return_value = "Test session summary."
    mock_memory_service.create_episodic_memory.return_value = AsyncMock() # EpisodicMemory object
    mock_chat_session_repo.update.return_value = AsyncMock() # Updated old session
    
    new_session_id = uuid4()
    mock_chat_session_repo.create.return_value = ChatSession(
        id=new_session_id,
        user_id=mock_user.id,
        tenant_id=mock_user.tenant_id,
        title="Reset Session from Test Session",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    result = await chat_service.reset_session(mock_session.id, mock_user.id, mock_user.tenant_id)

    # Assertions
    mock_chat_session_repo.get.assert_awaited_once_with(mock_session.id)
    mock_chat_message_repo.get_by_session_id.assert_awaited_once_with(mock_session.id)
    mock_dom_orchestrator_service.summarize_chat_history.assert_awaited_once_with(mock_messages)
    mock_memory_service.create_episodic_memory.assert_awaited_once()
    mock_chat_session_repo.update.assert_awaited_once_with(mock_session, {"is_active": False})
    mock_chat_session_repo.create.assert_awaited_once()
    
    assert isinstance(result, ChatSessionResponse)
    assert result.user_id == mock_user.id
    assert result.tenant_id == mock_user.tenant_id
    assert result.id == new_session_id


@pytest.mark.asyncio
async def test_reset_session_not_found(
    chat_service,
    mock_chat_session_repo,
    mock_user
):
    """セッションが見つからない場合のリセット失敗テスト"""
    mock_chat_session_repo.get.return_value = None

    with pytest.raises(ValueError, match="Chat session not found or not authorized."):
        await chat_service.reset_session(uuid4(), mock_user.id, mock_user.tenant_id)
    mock_chat_session_repo.get.assert_awaited_once()

@pytest.mark.asyncio
async def test_reset_session_summary_save_failure(
    chat_service,
    mock_chat_session_repo,
    mock_chat_message_repo,
    mock_memory_service,
    mock_dom_orchestrator_service,
    mock_user,
    mock_session,
    mock_messages
):
    """セッション要約の保存失敗テスト（Resetインバリアント）"""
    mock_chat_session_repo.get.return_value = mock_session
    mock_chat_message_repo.get_by_session_id.return_value = mock_messages
    mock_dom_orchestrator_service.summarize_chat_history.return_value = "Test session summary."
    mock_memory_service.create_episodic_memory.side_effect = Exception("DB error during save")

    with pytest.raises(ValueError, match="Failed to save session summary to episodic memory."):
        await chat_service.reset_session(mock_session.id, mock_user.id, mock_user.tenant_id)
    
    mock_chat_session_repo.get.assert_awaited_once()
    mock_chat_message_repo.get_by_session_id.assert_awaited_once()
    mock_dom_orchestrator_service.summarize_chat_history.assert_awaited_once()
    mock_memory_service.create_episodic_memory.assert_awaited_once()
    mock_chat_session_repo.update.assert_not_awaited() # 保存失敗時は古いセッションは更新されない
    mock_chat_session_repo.create.assert_not_awaited() # 新しいセッションも作成されない
