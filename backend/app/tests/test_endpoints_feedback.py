import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.main import app
from app.schemas.auth import AuthenticatedUser
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.dependencies import get_current_user
from app.services.feedback_service import FeedbackService
from app.dependencies import get_feedback_service

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
def mock_feedback_service():
    return AsyncMock(spec=FeedbackService)

@pytest.fixture
def override_get_feedback_service(mock_feedback_service):
    app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
    yield
    app.dependency_overrides.clear()

# Test Cases
@pytest.mark.asyncio
async def test_submit_feedback_success(
    override_get_current_user,
    override_get_feedback_service,
    mock_current_user,
    mock_feedback_service
):
    """
    フィードバック送信APIの成功ケースをテストします。
    """
    feedback_id = uuid4()
    session_id = uuid4()
    message_id = uuid4()
    feedback_data = FeedbackCreate(
        session_id=session_id,
        message_id=message_id,
        rating=1,
        comment="Great response!"
    )
    mock_feedback_service.create_feedback.return_value = FeedbackResponse(
        id=feedback_id,
        tenant_id=mock_current_user.tenant_id,
        user_id=mock_current_user.id,
        session_id=session_id,
        message_id=message_id,
        rating=feedback_data.rating,
        comment=feedback_data.comment,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    response = client.post("/api/v1/feedback", json=feedback_data.model_dump())
    assert response.status_code == 201
    assert response.json()["rating"] == 1
    assert response.json()["comment"] == "Great response!"
    mock_feedback_service.create_feedback.assert_awaited_once_with(
        user_id=mock_current_user.id,
        tenant_id=mock_current_user.tenant_id,
        feedback_in=feedback_data
    )

@pytest.mark.asyncio
async def test_get_feedback_for_session_success(
    override_get_current_user,
    override_get_feedback_service,
    mock_current_user,
    mock_feedback_service
):
    """
    セッションIDによるフィードバック取得の成功ケースをテストします。
    """
    session_id = uuid4()
    feedback_1 = FeedbackResponse(
        id=uuid4(), tenant_id=mock_current_user.tenant_id, user_id=mock_current_user.id, session_id=session_id,
        rating=1, comment="Good", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    feedback_2 = FeedbackResponse(
        id=uuid4(), tenant_id=mock_current_user.tenant_id, user_id=mock_current_user.id, session_id=session_id,
        rating=-1, comment="Bad", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_feedback_service.get_feedback_by_session_id.return_value = [feedback_1, feedback_2]

    response = client.get(f"/api/v1/feedback/{session_id}")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["comment"] == "Good"
    mock_feedback_service.get_feedback_by_session_id.assert_awaited_once_with(session_id)

@pytest.mark.asyncio
async def test_get_feedback_for_message_success(
    override_get_current_user,
    override_get_feedback_service,
    mock_current_user,
    mock_feedback_service
):
    """
    メッセージIDによるフィードバック取得の成功ケースをテストします。
    """
    message_id = uuid4()
    feedback = FeedbackResponse(
        id=uuid4(), tenant_id=mock_current_user.tenant_id, user_id=mock_current_user.id, session_id=uuid4(),
        message_id=message_id, rating=1, comment="Very helpful", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_feedback_service.get_feedback_by_message_id.return_value = feedback

    response = client.get(f"/api/v1/feedback/message/{message_id}")
    assert response.status_code == 200
    assert response.json()["comment"] == "Very helpful"
    mock_feedback_service.get_feedback_by_message_id.assert_awaited_once_with(message_id)

@pytest.mark.asyncio
async def test_get_feedback_for_message_not_found(
    override_get_current_user,
    override_get_feedback_service,
    mock_feedback_service
):
    """
    メッセージIDによるフィードバックが見つからない場合のテスト。
    """
    message_id = uuid4()
    mock_feedback_service.get_feedback_by_message_id.return_value = None

    response = client.get(f"/api/v1/feedback/message/{message_id}")
    assert response.status_code == 200 # Optional[FeedbackResponse]なのでNoneを返す場合は200
    assert response.json() is None
    mock_feedback_service.get_feedback_by_message_id.assert_awaited_once_with(message_id)

@pytest.mark.asyncio
async def test_get_feedback_for_message_unauthorized(
    override_get_current_user,
    override_get_feedback_service,
    mock_feedback_service
):
    """
    メッセージIDによるフィードバック取得で権限がない場合のテスト。
    """
    message_id = uuid4()
    # 別のテナントのフィードバックを返すようにモック
    unauthorized_feedback = FeedbackResponse(
        id=uuid4(), tenant_id=uuid4(), user_id=uuid4(), session_id=uuid4(),
        message_id=message_id, rating=1, comment="Not yours", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_feedback_service.get_feedback_by_message_id.return_value = unauthorized_feedback

    response = client.get(f"/api/v1/feedback/message/{message_id}")
    assert response.status_code == 200
    assert response.json() is None # 権限がない場合はNoneが返されるべき
    mock_feedback_service.get_feedback_by_message_id.assert_awaited_once_with(message_id)
