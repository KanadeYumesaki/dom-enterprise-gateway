import json
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.core.config import settings
from app.main import app
from app.schemas.auth import AuthenticatedUser
from app.services.auth import AuthService
from app.dependencies import get_auth_service, get_current_admin_user, get_current_user

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
def test_dev_login_callback_and_me(monkeypatch):
    monkeypatch.setattr(settings, "DEV_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "SESSION_SECRET", "test-secret")

    # login -> state cookie & redirect
    login_res = client.get("/api/v1/auth/login", params={"redirect_uri": "/auth/callback"}, follow_redirects=False)
    assert login_res.status_code == 302
    state_cookie = login_res.cookies.get("auth_state")
    assert state_cookie
    redirected = login_res.headers["location"]
    assert "code=dev" in redirected and f"state={state_cookie}" in redirected

    # callback -> session cookie
    callback_res = client.get(
        "/api/v1/auth/callback",
        params={"state": state_cookie, "code": "dev"},
        cookies=login_res.cookies,
    )
    assert callback_res.status_code == 200
    body = callback_res.json()
    assert body["email"] == "dev@example.com"
    assert "session" in callback_res.cookies

    # me should return user with session cookie
    me_res = client.get("/api/v1/auth/me", cookies=callback_res.cookies)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "dev@example.com"

def test_logout_clears_session(monkeypatch):
    monkeypatch.setattr(settings, "DEV_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "SESSION_SECRET", "test-secret")

    login_res = client.get("/api/v1/auth/login", params={"redirect_uri": "/auth/callback"}, follow_redirects=False)
    state_cookie = login_res.cookies.get("auth_state")
    callback_res = client.get(
        "/api/v1/auth/callback",
        params={"state": state_cookie, "code": "dev"},
        cookies=login_res.cookies,
    )
    client.cookies.update(callback_res.cookies)

    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 204

    me_after = client.get("/api/v1/auth/me")
    assert me_after.status_code == 401
    assert me_after.json()["detail"] == "Could not validate credentials"

def test_login_returns_501_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "DEV_AUTH_ENABLED", False)
    res = client.get("/api/v1/auth/login", params={"redirect_uri": "/auth/callback"}, follow_redirects=False)
    assert res.status_code == 501

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
