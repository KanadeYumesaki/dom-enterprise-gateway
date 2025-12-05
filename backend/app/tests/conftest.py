import os
import pytest
from unittest.mock import MagicMock
import fastapi.dependencies.utils

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
    # Ensure DATABASE_URL is set if not already (though config.py has default)
    if "DATABASE_URL" not in os.environ:
         os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:password@localhost:5432/test_db"
