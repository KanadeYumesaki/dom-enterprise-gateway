import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.models.tenant import Tenant
from app.models.user import User
from app.core.database import Base

@pytest.fixture
def mock_session():
    """非同期セッションのモックフィクスチャ"""
    mock = AsyncMock(spec=AsyncSession)
    mock.execute.return_value.scalar_one_or_none = MagicMock()
    return mock

@pytest.fixture
def base_repo_no_tenant(mock_session):
    """tenant_idなしのBaseRepositoryフィクスチャ"""
    return BaseRepository(model=Tenant, session=mock_session, tenant_id=None)

@pytest.fixture
def base_repo_with_tenant(mock_session):
    """tenant_idありのBaseRepositoryフィクスチャ"""
    return BaseRepository(model=User, session=mock_session, tenant_id=uuid4()) # Userモデルはtenant_idを持つ

@pytest.fixture
def tenant_repo(mock_session):
    """TenantRepositoryのフィクスチャ (通常はtenant_idなしでテスト)"""
    return TenantRepository(session=mock_session, tenant_id=None)

@pytest.fixture
def user_repo_no_tenant(mock_session):
    """tenant_idなしのUserRepositoryフィクスチャ"""
    return UserRepository(session=mock_session, tenant_id=None)

@pytest.fixture
def user_repo_with_tenant(mock_session):
    """tenant_idありのUserRepositoryフィクスチャ"""
    return UserRepository(session=mock_session, tenant_id=uuid4())

# BaseRepositoryのテスト
@pytest.mark.asyncio
async def test_base_repository_get_no_tenant_filter(base_repo_no_tenant, mock_session):
    """BaseRepository.get() (tenant_idなし)のテスト"""
    test_id = uuid4()
    mock_tenant = Tenant(id=test_id, name="Test Tenant")
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_tenant

    tenant = await base_repo_no_tenant.get(test_id)
    assert tenant == mock_tenant
    # select文にtenant_idのwhere句がないことを確認 (引数が一つだけ)
    # assert mock_session.execute.call_args[0][0].compare(select(Tenant).where(Tenant.id == test_id))
    # 文字列比較で代用
    actual_query = str(mock_session.execute.call_args[0][0])
    expected_query = str(select(Tenant).where(Tenant.id == test_id))
    assert actual_query == expected_query

@pytest.mark.asyncio
async def test_base_repository_get_with_tenant_filter(base_repo_with_tenant, mock_session):
    """BaseRepository.get() (tenant_idあり)のテスト"""
    test_id = uuid4()
    mock_user = User(id=test_id, tenant_id=base_repo_with_tenant.tenant_id, email="a@b.com", hashed_password="pw")
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

    user = await base_repo_with_tenant.get(test_id)
    assert user == mock_user
    # select文にtenant_idのwhere句があることを確認
    actual_query = str(mock_session.execute.call_args[0][0])
    expected_query = str(select(User).where(User.id == test_id, User.tenant_id == base_repo_with_tenant.tenant_id))
    assert actual_query == expected_query

@pytest.mark.asyncio
async def test_base_repository_create_with_tenant_auto_assign(base_repo_with_tenant, mock_session):
    """BaseRepository.create()でtenant_idが自動割り当てされるテスト"""
    user_data = {"email": "new@user.com", "hashed_password": "pw"}
    mock_user = User(id=uuid4(), tenant_id=base_repo_with_tenant.tenant_id, **user_data)
    
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.return_value = None

    # create実行時、obj_inにtenant_idがないが、リポジトリのtenant_idが自動で付与される
    user = await base_repo_with_tenant.create(user_data)
    assert user.email == user_data["email"]
    assert user.tenant_id == base_repo_with_tenant.tenant_id
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

# TenantRepositoryのテスト
@pytest.mark.asyncio
async def test_tenant_repository_get_by_name(tenant_repo, mock_session):
    """TenantRepository.get_by_name()のテスト (tenant_idフィルタなし)"""
    test_name = "Unique Tenant"
    mock_tenant = Tenant(id=uuid4(), name=test_name)
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_tenant

    tenant = await tenant_repo.get_by_name(test_name)
    assert tenant == mock_tenant
    # select文にtenant_idのwhere句がないことを確認
    actual_query = str(mock_session.execute.call_args[0][0])
    expected_query = str(select(Tenant).where(Tenant.name == test_name))
    assert actual_query == expected_query


# UserRepositoryのテスト
@pytest.mark.asyncio
async def test_user_repository_get_by_email_with_tenant(user_repo_with_tenant, mock_session):
    """UserRepository.get_by_email() (tenant_idあり)のテスト"""
    test_email = "test@example.com"
    mock_user = User(id=uuid4(), tenant_id=user_repo_with_tenant.tenant_id, email=test_email, hashed_password="pw")
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

    user = await user_repo_with_tenant.get_by_email(test_email)
    assert user == mock_user
    # select文にtenant_idのwhere句があることを確認
    actual_query = str(mock_session.execute.call_args[0][0])
    expected_query = str(select(User).where(User.email == test_email, User.tenant_id == user_repo_with_tenant.tenant_id))
    assert actual_query == expected_query

@pytest.mark.asyncio
async def test_user_repository_get_by_email_no_tenant(user_repo_no_tenant, mock_session):
    """UserRepository.get_by_email() (tenant_idなし)のテスト"""
    test_email = "test@example.com"
    mock_user = User(id=uuid4(), tenant_id=uuid4(), email=test_email, hashed_password="pw")
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

    user = await user_repo_no_tenant.get_by_email(test_email)
    assert user == mock_user
    # select文にtenant_idのwhere句がないことを確認
    actual_query = str(mock_session.execute.call_args[0][0])
    expected_query = str(select(User).where(User.email == test_email))
    assert actual_query == expected_query
