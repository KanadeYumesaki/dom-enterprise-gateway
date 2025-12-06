import pytest
from uuid import uuid4
from app.schemas.user_settings import UserSettingsRead, UserSettingsUpdate, UserSettingsBase
from app.services.user_settings import UserSettingsService
from app.schemas.auth import AuthenticatedUser

pytestmark = pytest.mark.asyncio

class TestUserSettingsService:
    """
    UserSettingsService のユニットテスト。
    
    テスト観点:
    - デフォルト設定の返却
    - 部分更新ロジック
    - upsert（作成/更新）の挙動
    """
    
    async def test_get_or_default_returns_default_when_no_record(self, async_session, test_user):
        """
        レコードが無い場合にデフォルト設定が返ることを確認。
        """
        service = UserSettingsService(async_session, test_user.tenant_id)
        
        result = await service.get_or_default(test_user)
        
        assert result.theme == "light"  # デフォルト値
        assert result.language == "ja"  # デフォルト値
        assert result.font_size == "medium"  # デフォルト値
        assert result.has_seen_onboarding == False
        assert result.user_id == test_user.id
        assert result.tenant_id == test_user.tenant_id
    
    async def test_update_creates_new_record(self, async_session, test_user):
        """
        初回更新時に新しいレコードが作成されることを確認。
        """
        service = UserSettingsService(async_session, test_user.tenant_id)
        
        payload = UserSettingsUpdate(theme="dark", font_size="large")
        result = await service.update(test_user, payload)
        
        assert result.theme == "dark"
        assert result.font_size == "large"
        assert result.language == "ja"  # 未指定フィールドはデフォルト値
        assert result.user_id == test_user.id
    
    async def test_update_partial_update_preserves_other_fields(self, async_session, test_user):
        """
        部分更新時に、他のフィールドが維持されることを確認。
        """
        service = UserSettingsService(async_session, test_user.tenant_id)
        
        # 初回: theme と language を設定
        first_update = UserSettingsUpdate(theme="dark", language="en")
        await service.update(test_user, first_update)
        
        # 2回目: font_size のみ変更
        second_update = UserSettingsUpdate(font_size="small")
        result = await service.update(test_user, second_update)
        
        # theme と language は維持されているはず
        assert result.theme == "dark"
        assert result.language == "en"
        assert result.font_size == "small"  # 新しく設定された値
    
    async def test_get_or_default_returns_existing_record(self, async_session, test_user):
        """
        レコードがある場合、そのレコードが返ることを確認。
        """
        service = UserSettingsService(async_session, test_user.tenant_id)
        
        # まず作成
        payload = UserSettingsUpdate(theme="dark", has_seen_onboarding=True)
        await service.update(test_user, payload)
        
        #取得
        result = await service.get_or_default(test_user)
        
        assert result.theme == "dark"
        assert result.has_seen_onboarding == True

@pytest.fixture
async def test_user(async_session):
    """
    テスト用のAuthenticatedUserを作成。
    """
    from app.models.tenant import Tenant
    from app.models.user import User
    
    # テナント作成
    tenant = Tenant(name=f"test_tenant_{uuid4()}")
    async_session.add(tenant)
    await async_session.flush()
    
    # ユーザー作成
    user = User(
        tenant_id=tenant.id,
        email=f"test_{uuid4()}@example.com",
        hashed_password="dummy_hash",
        is_active=True,
        is_admin=False
    )
    async_session.add(user)
    await async_session.flush()
    
    # AuthenticatedUser に変換
    auth_user = AuthenticatedUser(
        id=user.id,
        tenant_id=tenant.id,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin
    )
    
    yield auth_user
    
    # クリーンアップ
    await async_session.rollback()
