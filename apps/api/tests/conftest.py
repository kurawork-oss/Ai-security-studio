from __future__ import annotations

import os

os.environ["SECUREAI_ENVIRONMENT"] = "test"
os.environ["SECUREAI_DEV_SEED"] = "true"
os.environ["SECUREAI_DEV_PROVIDER_TYPE"] = "echo"
os.environ["SECUREAI_DEV_PROTECT_KEY"] = "sk_protect_test_0000000000000000"
os.environ["SECUREAI_DEV_ANALYZE_KEY"] = "sk_analyze_test_0000000000000000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.core.config import get_settings  # noqa: E402
from src.main import create_app  # noqa: E402

PROTECT_KEY = os.environ["SECUREAI_DEV_PROTECT_KEY"]
ANALYZE_KEY = os.environ["SECUREAI_DEV_ANALYZE_KEY"]


@pytest.fixture(scope="session")
def client() -> TestClient:
    get_settings.cache_clear()
    return TestClient(create_app())


def auth(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}
