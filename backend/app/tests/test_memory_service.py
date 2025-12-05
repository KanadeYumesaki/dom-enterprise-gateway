import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from app.services.memory_service import MemoryService
from app.repositories.memory import StructuredMemoryRepository, EpisodicMemoryRepository
from app.models.memory import StructuredMemory, EpisodicMemory
from app.schemas.auth import AuthenticatedUser

@pytest.fixture
def mock_structured_memory_repo():
    return AsyncMock(spec=StructuredMemoryRepository)

@pytest.fixture
def mock_episodic_memory_repo():
    return AsyncMock(spec=EpisodicMemoryRepository)

@pytest.fixture
def memory_service(mock_structured_memory_repo, mock_episodic_memory_repo):
    return MemoryService(mock_structured_memory_repo, mock_episodic_memory_repo)

@pytest.fixture
def mock_user():
    return AuthenticatedUser(id=uuid4(), tenant_id=uuid4(), email="test@example.com", is_active=True, is_admin=False)

@pytest.fixture
def mock_structured_memory_data(mock_user):
    return {
        "user_id": mock_user.id,
        "key": "user_preference",
        "value": {"theme": "dark"},
        "description": "User's UI preferences"
    }

@pytest.fixture
def mock_episodic_memory_data(mock_user):
    return {
        "user_id": mock_user.id,
        "session_id": uuid4(),
        "summary": "Meeting about project A, decided to use new framework.",
        "decisions": ["Use new framework"],
        "assumptions": ["Framework performs well"]
    }

@pytest.mark.asyncio
async def test_create_structured_memory(memory_service, mock_structured_memory_repo, mock_user, mock_structured_memory_data):
    """StructuredMemoryの作成テスト"""
    mock_structured_memory_repo.create.return_value = StructuredMemory(
        id=uuid4(), tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_structured_memory_data
    )
    memory = await memory_service.create_structured_memory(
        user_id=mock_user.id,
        key=mock_structured_memory_data["key"],
        value=mock_structured_memory_data["value"],
        description=mock_structured_memory_data["description"]
    )
    assert memory.key == mock_structured_memory_data["key"]
    mock_structured_memory_repo.create.assert_awaited_once_with(mock_structured_memory_data)

@pytest.mark.asyncio
async def test_get_structured_memory_by_key(memory_service, mock_structured_memory_repo, mock_user, mock_structured_memory_data):
    """キーによるStructuredMemory取得テスト"""
    mock_memory = StructuredMemory(id=uuid4(), tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_structured_memory_data)
    mock_structured_memory_repo.get_by_key.return_value = mock_memory
    memory = await memory_service.get_structured_memory_by_key(mock_structured_memory_data["key"], mock_user.id)
    assert memory == mock_memory
    mock_structured_memory_repo.get_by_key.assert_awaited_once_with(mock_structured_memory_data["key"], mock_user.id)

@pytest.mark.asyncio
async def test_update_structured_memory(memory_service, mock_structured_memory_repo, mock_user, mock_structured_memory_data):
    """StructuredMemoryの更新テスト"""
    memory_id = uuid4()
    original_memory = StructuredMemory(id=memory_id, tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_structured_memory_data)
    updated_data = {"value": {"theme": "light"}, "description": "Updated preferences"}
    updated_memory = StructuredMemory(id=memory_id, tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_structured_memory_data)
    updated_memory.value = updated_data["value"]
    updated_memory.description = updated_data["description"]

    mock_structured_memory_repo.get.return_value = original_memory
    mock_structured_memory_repo.update.return_value = updated_memory

    memory = await memory_service.update_structured_memory(memory_id, updated_data["value"], updated_data["description"])
    assert memory.value == updated_data["value"]
    assert memory.description == updated_data["description"]
    mock_structured_memory_repo.get.assert_awaited_once_with(memory_id)
    mock_structured_memory_repo.update.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_structured_memory(memory_service, mock_structured_memory_repo, mock_user, mock_structured_memory_data):
    """StructuredMemoryの削除テスト"""
    memory_id = uuid4()
    mock_memory = StructuredMemory(id=memory_id, tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_structured_memory_data)
    mock_structured_memory_repo.delete.return_value = mock_memory
    deleted_memory = await memory_service.delete_structured_memory(memory_id)
    assert deleted_memory == mock_memory
    mock_structured_memory_repo.delete.assert_awaited_once_with(memory_id)

@pytest.mark.asyncio
async def test_create_episodic_memory(memory_service, mock_episodic_memory_repo, mock_user, mock_episodic_memory_data):
    """EpisodicMemoryの作成テスト"""
    mock_episodic_memory_repo.create.return_value = EpisodicMemory(
        id=uuid4(), tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_episodic_memory_data
    )
    memory = await memory_service.create_episodic_memory(
        user_id=mock_user.id,
        session_id=mock_episodic_memory_data["session_id"],
        summary=mock_episodic_memory_data["summary"],
        decisions=mock_episodic_memory_data["decisions"],
        assumptions=mock_episodic_memory_data["assumptions"]
    )
    assert memory.summary == mock_episodic_memory_data["summary"]
    mock_episodic_memory_repo.create.assert_awaited_once_with(mock_episodic_memory_data)

@pytest.mark.asyncio
async def test_get_episodic_memory_by_session_id(memory_service, mock_episodic_memory_repo, mock_user, mock_episodic_memory_data):
    """セッションIDによるEpisodicMemory取得テスト"""
    mock_memory = EpisodicMemory(id=uuid4(), tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_episodic_memory_data)
    mock_episodic_memory_repo.get_by_session_id.return_value = mock_memory
    memory = await memory_service.get_episodic_memory_by_session_id(mock_episodic_memory_data["session_id"])
    assert memory == mock_memory
    mock_episodic_memory_repo.get_by_session_id.assert_awaited_once_with(mock_episodic_memory_data["session_id"])

@pytest.mark.asyncio
async def test_get_all_episodic_memories_by_user_id(memory_service, mock_episodic_memory_repo, mock_user, mock_episodic_memory_data):
    """ユーザーIDによる全EpisodicMemory取得テスト"""
    mock_memory_1 = EpisodicMemory(id=uuid4(), tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_episodic_memory_data)
    mock_memory_2 = EpisodicMemory(id=uuid4(), tenant_id=mock_user.tenant_id, created_at=datetime.now(), **mock_episodic_memory_data)
    mock_episodic_memory_repo.get_all_by_user_id.return_value = [mock_memory_1, mock_memory_2]
    memories = await memory_service.get_all_episodic_memories_by_user_id(mock_user.id)
    assert len(memories) == 2
    mock_episodic_memory_repo.get_all_by_user_id.assert_awaited_once_with(mock_user.id)
