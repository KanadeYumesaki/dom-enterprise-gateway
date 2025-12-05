import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4, UUID

from app.main import app
from app.schemas.auth import AuthenticatedUser
from app.services.auth import AuthService
from app.dependencies import get_auth_service
from app.dependencies import get_current_user, get_current_admin_user, oauth2_scheme

# TestClientインスタンス
client = TestClient(app)

# フィクスチャ
@pytest.fixture
def mock_auth_service():
    return AsyncMock(spec=AuthService)

@pytest.fixture
def override_get_auth_service(mock_auth_service):
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_authenticated_user():
    return AuthenticatedUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="test@example.com",
        is_active=True,
        is_admin=False
    )

@pytest.fixture
def override_get_current_user(mock_authenticated_user):
    app.dependency_overrides[get_current_user] = lambda: mock_authenticated_user
    yield
    app.dependency_overrides.clear()

# テストケース
def test_read_current_user_success(override_get_current_user, mock_authenticated_user):
    """
    認証済みユーザー情報取得APIの成功ケースをテストします。
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == mock_authenticated_user.email
    assert UUID(response.json()["id"]) == mock_authenticated_user.id

def test_read_current_user_unauthorized(mock_auth_service, override_get_auth_service):
    """
    Authorizationヘッダーがない場合の認証失敗ケースをテストします。
    AuthServiceのverify_id_tokenが例外を発生させる場合をシミュレートします。
    """
    mock_auth_service.verify_id_token.side_effect = Exception("Invalid token")
    
    # OAuth2PasswordBearerがトークンを見つけられない、またはverify_id_tokenが失敗する場合
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Could not validate credentials" in response.json()["detail"]

def test_read_current_user_inactive_user(mock_auth_service, override_get_auth_service):
    """
    非アクティブユーザーの認証失敗ケースをテストします。
    """
    inactive_user = AuthenticatedUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="inactive@example.com",
        is_active=False,
        is_admin=False
    )
    mock_auth_service.verify_id_token.return_value = inactive_user

    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Inactive user" in response.json()["detail"]

# get_current_admin_userのテスト（ここでは/adminエンドポイントがないため、単体でテスト）
@pytest.mark.asyncio
async def test_get_current_admin_user_success():
    """
    admin権限を持つユーザーのテスト。
    """
    admin_user = AuthenticatedUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="admin@example.com",
        is_active=True,
        is_admin=True
    )

    
    # NOTE: get_current_admin_userはget_current_userに依存するため、
    # TestClientで呼び出すには直接ルーティングを定義するか、DIを適切にモックする必要があります。
    # ここでは、直接関数をテストする形にしています。
    admin_result = await get_current_admin_user(admin_user)
    assert admin_result == admin_user

@pytest.mark.asyncio
async def test_get_current_admin_user_forbidden():
    """
    admin権限を持たないユーザーのテスト。
    """
    non_admin_user = AuthenticatedUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="user@example.com",
        is_active=True,
        is_admin=False
    )
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(non_admin_user)
    assert exc_info.value.status_code == 403
    assert "Not enough privileges" in exc_info.value.detail
