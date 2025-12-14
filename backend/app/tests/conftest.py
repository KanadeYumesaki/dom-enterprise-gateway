import os
from unittest.mock import MagicMock

import fastapi.dependencies.utils
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base

# Patch ensure_multipart_is_installed to avoid RuntimeError when python-multipart is missing during collection
# This is a workaround because we cannot add python-multipart to pyproject.toml per constraints.
fastapi.dependencies.utils.ensure_multipart_is_installed = MagicMock()


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """
    Set dummy environment variables for testing to ensure Settings are initialized correctly.
    """
    os.environ["OIDC_CLIENT_ID"] = "test-client-id"
    os.environ["OIDC_CLIENT_SECRET"] = "test-client-secret"
    os.environ["INITIAL_ADMIN_EMAIL"] = "admin@example.com"
    os.environ["DEV_AUTH_ENABLED"] = "true"
    os.environ["SESSION_SECRET"] = "test-session-secret"
    # Ensure DATABASE_URL is set if not already (though config.py has default)
    if "DATABASE_URL" not in os.environ:
         os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:password@localhost:5432/test_db"


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """
    Shared async engine for lightweight SQLite-backed tests.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)

    # Import models to register metadata before creating tables
    import app.models.tenant  # noqa: F401
    import app.models.user  # noqa: F401
    import app.models.user_settings  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """
    Provides an AsyncSession bound to the in-memory SQLite engine for service/repository tests.
    """
    async_session_maker = sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()
