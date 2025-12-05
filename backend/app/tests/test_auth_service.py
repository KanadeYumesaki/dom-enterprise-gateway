import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from jose import jwt as python_jose_jwt

from app.services.auth import AuthService
from app.schemas.auth import AuthenticatedUser
from app.repositories.user import UserRepository
from app.repositories.tenant import TenantRepository
from app.models.tenant import Tenant
from app.models.user import User
from app.core.config import settings

# フィクスチャ
@pytest.fixture
def mock_user_repository():
    """tenant_idなしで初期化されるUserRepositoryのモックフィクスチャ"""
    mock = AsyncMock(spec=UserRepository)
    mock.tenant_id = None # システムリポジリとしてtenant_idはNone
    return mock

@pytest.fixture
def mock_tenant_repository():
    """tenant_idなしで初期化されるTenantRepositoryのモックフィクスチャ"""
    mock = AsyncMock(spec=TenantRepository)
    mock.tenant_id = None # システムリポジリとしてtenant_idはNone
    return mock

@pytest.fixture
def auth_service(mock_user_repository, mock_tenant_repository):
    return AuthService(mock_user_repository, mock_tenant_repository)

@pytest.fixture
def mock_settings():
    """settingsをモックするフィクスチャ"""
    with patch('app.services.auth.settings') as mock_s:
        mock_s.OIDC_ISSUER = "https://mock-issuer.com"
        mock_s.OIDC_CLIENT_ID = "mock_client_id"
        mock_s.INITIAL_ADMIN_EMAIL = "admin@example.com"
        mock_s.PROJECT_NAME = "DOM Enterprise Gateway" # PROJECT_NAMEも必要
        yield mock_s

# テストケース
@pytest.mark.asyncio
async def test_get_jwks_uri_success(auth_service, mock_settings):
    """JWKS URIの取得成功テスト"""
    with patch('httpx.AsyncClient') as MockAsyncClient:
        # Clientのモック
        mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        
        # Responseのモック (AsyncMockではなくMagicMockを使うか、明示的にメソッドを定義)
        mock_response = MagicMock()
        mock_response.json.return_value = {"jwks_uri": "https://mock-issuer.com/jwks"}
        mock_response.raise_for_status.return_value = None
        
        # getメソッドの戻り値を設定
        mock_client_instance.get.return_value = mock_response

        jwks_uri = await auth_service.get_jwks_uri()
        assert jwks_uri == "https://mock-issuer.com/jwks"
        mock_client_instance.get.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_jwks_uri_failure(auth_service, mock_settings):
    """JWKS URIの取得失敗テスト"""
    with patch('httpx.AsyncClient') as MockAsyncClient:
        mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        
        mock_response = MagicMock()
        mock_response.json.return_value = {} # jwks_uriがない場合
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance.get.return_value = mock_response

        with pytest.raises(ValueError, match="jwks_uri not found"):
            await auth_service.get_jwks_uri()

@pytest.mark.asyncio
async def test_verify_id_token_no_client_id(auth_service, mock_settings):
    """OIDC_CLIENT_IDが設定されていない場合のテスト"""
    mock_settings.OIDC_CLIENT_ID = None
    with pytest.raises(ValueError, match="OIDC_CLIENT_ID is not configured"):
        await auth_service.verify_id_token("dummy_token")

@pytest.mark.asyncio
async def test_verify_id_token_success_new_user_and_tenant(auth_service, mock_user_repository, mock_tenant_repository, mock_settings):
    """有効なIDトークンで新規ユーザーとテナントが作成される場合のテスト"""
    # モック設定
    mock_tenant_repository.get_by_name.return_value = None
    created_tenant = Tenant(id=uuid4(), name=mock_settings.PROJECT_NAME)
    mock_tenant_repository.create.return_value = created_tenant
    mock_user_repository.get_by_email.return_value = None
    created_user = User(
        id=uuid4(),
        tenant_id=created_tenant.id,
        email="test@example.com",
        hashed_password="OIDC_USER_DUMMY_PASSWORD",
        is_active=True,
        is_admin=False
    )
    mock_user_repository.create.return_value = created_user

    # get_jwks_client自体をモックしてHTTP通信をスキップ
    mock_jwks_client = MagicMock()
    mock_jwks_client.find_by_kid.return_value = "mock_public_key"
    
    with patch.object(auth_service, 'get_jwks_client', new_callable=AsyncMock) as mock_get_jwks_client:
        mock_get_jwks_client.return_value = mock_jwks_client

        # JWTモック
        with patch('app.services.auth.python_jose_jwt') as mock_python_jose_jwt, \
             patch('app.services.auth.JsonWebToken') as MockJsonWebToken:
            
            # python-jose_jwt.get_unverified_headerのモック
            mock_python_jose_jwt.get_unverified_header.return_value = {"kid": "mock_kid"}

            # JsonWebToken.decodeのモック
            mock_jwt_decoder_instance = MockJsonWebToken.return_value
            auth_service._jwt_decoder = mock_jwt_decoder_instance # Mock injection

            claims_data = {"email": "test@example.com", "sub": "mock_sub", "iss": mock_settings.OIDC_ISSUER, "aud": mock_settings.OIDC_CLIENT_ID, "exp": 12345, "iat": 12345}
            mock_claims = MagicMock()
            mock_claims.__getitem__.side_effect = claims_data.__getitem__
            mock_claims.validate.return_value = None
            mock_jwt_decoder_instance.decode.return_value = mock_claims

            # 実行
            authenticated_user = await auth_service.verify_id_token("mock_id_token")

            # アサート
            assert isinstance(authenticated_user, AuthenticatedUser)
            assert authenticated_user.email == "test@example.com"
            mock_tenant_repository.get_by_name.assert_awaited_once_with(mock_settings.PROJECT_NAME)
            mock_tenant_repository.create.assert_awaited_once_with({"name": mock_settings.PROJECT_NAME})
            mock_user_repository.get_by_email.assert_awaited_once_with("test@example.com")
            mock_user_repository.create.assert_awaited_once_with({
                "tenant_id": created_tenant.id,
                "email": "test@example.com",
                "hashed_password": "OIDC_USER_DUMMY_PASSWORD",
                "is_admin": False
            })
            assert not authenticated_user.is_admin # 初期管理者でないことを確認

@pytest.mark.asyncio
async def test_verify_id_token_success_existing_user_and_tenant(auth_service, mock_user_repository, mock_tenant_repository, mock_settings):
    """有効なIDトークンで既存ユーザーとテナントが使用される場合のテスト"""
    # 既存のテナントとユーザーをモック
    existing_tenant = Tenant(id=uuid4(), name=mock_settings.PROJECT_NAME)
    existing_user = User(
        id=uuid4(),
        tenant_id=existing_tenant.id,
        email="existing@example.com",
        hashed_password="OIDC_USER_DUMMY_PASSWORD",
        is_active=True,
        is_admin=False
    )
    mock_tenant_repository.get_by_name.return_value = existing_tenant
    mock_user_repository.get_by_email.return_value = existing_user

    mock_jwks_client = MagicMock()
    mock_jwks_client.find_by_kid.return_value = "mock_public_key"

    with patch.object(auth_service, 'get_jwks_client', new_callable=AsyncMock) as mock_get_jwks_client:
        mock_get_jwks_client.return_value = mock_jwks_client

        # JWTモック
        with patch('app.services.auth.python_jose_jwt') as mock_python_jose_jwt, \
             patch('app.services.auth.JsonWebToken') as MockJsonWebToken:
            
            mock_python_jose_jwt.get_unverified_header.return_value = {"kid": "mock_kid"}

            mock_jwt_decoder_instance = MockJsonWebToken.return_value
            auth_service._jwt_decoder = mock_jwt_decoder_instance # Mock injection

            claims_data = {"email": "existing@example.com", "sub": "mock_sub_existing", "iss": mock_settings.OIDC_ISSUER, "aud": mock_settings.OIDC_CLIENT_ID, "exp": 12345, "iat": 12345}
            mock_claims = MagicMock()
            mock_claims.__getitem__.side_effect = claims_data.__getitem__
            mock_claims.validate.return_value = None
            mock_jwt_decoder_instance.decode.return_value = mock_claims

            # 実行
            authenticated_user = await auth_service.verify_id_token("mock_id_token")

            # アサート
            assert isinstance(authenticated_user, AuthenticatedUser)
            assert authenticated_user.email == "existing@example.com"
            assert authenticated_user.id == existing_user.id
            mock_tenant_repository.get_by_name.assert_awaited_once_with(mock_settings.PROJECT_NAME)
            mock_tenant_repository.create.assert_not_awaited()
            mock_user_repository.get_by_email.assert_awaited_once_with("existing@example.com")
            mock_user_repository.create.assert_not_awaited()

@pytest.mark.asyncio
async def test_verify_id_token_admin_user_creation(auth_service, mock_user_repository, mock_tenant_repository, mock_settings):
    """初期管理者メールアドレスと一致する場合、is_adminがTrueになるテスト"""
    mock_settings.INITIAL_ADMIN_EMAIL = "admin@example.com"
    
    mock_tenant_repository.get_by_name.return_value = Tenant(id=uuid4(), name=mock_settings.PROJECT_NAME)
    mock_user_repository.get_by_email.return_value = None
    created_user = User(
        id=uuid4(),
        tenant_id=mock_tenant_repository.get_by_name.return_value.id,
        email="admin@example.com",
        hashed_password="OIDC_USER_DUMMY_PASSWORD",
        is_active=True,
        is_admin=True
    )
    mock_user_repository.create.return_value = created_user

    mock_jwks_client = MagicMock()
    mock_jwks_client.find_by_kid.return_value = "mock_public_key"

    with patch.object(auth_service, 'get_jwks_client', new_callable=AsyncMock) as mock_get_jwks_client:
        mock_get_jwks_client.return_value = mock_jwks_client

        with patch('app.services.auth.python_jose_jwt') as mock_python_jose_jwt, \
             patch('app.services.auth.JsonWebToken') as MockJsonWebToken:
            
            mock_python_jose_jwt.get_unverified_header.return_value = {"kid": "mock_kid"}

            mock_jwt_decoder_instance = MockJsonWebToken.return_value
            auth_service._jwt_decoder = mock_jwt_decoder_instance # Mock injection
            
            claims_data = {"email": "admin@example.com", "sub": "mock_sub_admin", "iss": mock_settings.OIDC_ISSUER, "aud": mock_settings.OIDC_CLIENT_ID, "exp": 12345, "iat": 12345}
            mock_claims = MagicMock()
            mock_claims.__getitem__.side_effect = claims_data.__getitem__
            mock_claims.validate.return_value = None
            mock_jwt_decoder_instance.decode.return_value = mock_claims

            authenticated_user = await auth_service.verify_id_token("mock_id_token_admin")
            assert authenticated_user.is_admin is True
            mock_user_repository.create.assert_awaited_once_with({
                "tenant_id": mock_tenant_repository.get_by_name.return_value.id,
                "email": "admin@example.com",
                "hashed_password": "OIDC_USER_DUMMY_PASSWORD",
                "is_admin": True
            })

# その他のエラーケース（kidがない、公開鍵が見つからない、トークン検証失敗など）も追加可能