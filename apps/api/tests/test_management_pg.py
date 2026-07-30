"""Integration tests against a real PostgreSQL database.

Exercises the Postgres-backed control plane + data plane end to end:
project creation, key issuance, Protect via the issued key, log persistence,
rule updates, Analyze, analytics, and tenant isolation.

Skipped automatically unless ``SECUREAI_TEST_DATABASE_URL`` is set.
"""

from __future__ import annotations

import asyncio
import os
import uuid

import jwt
import pytest
from fastapi.testclient import TestClient

TEST_DB = os.environ.get("SECUREAI_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DB, reason="SECUREAI_TEST_DATABASE_URL not set")

JWT_SECRET = "test-secret"
USER1 = "11111111-1111-1111-1111-111111111111"
ORG1 = "a1111111-1111-1111-1111-111111111111"
USER2 = "22222222-2222-2222-2222-222222222222"
ORG2 = "a2222222-2222-2222-2222-222222222222"


def _token(user_id: str, email: str) -> str:
    return jwt.encode(
        {"sub": user_id, "email": email, "aud": "authenticated"},
        JWT_SECRET,
        algorithm="HS256",
    )


async def _reset_and_seed(url: str) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    from src.infrastructure.db.models import Base, Membership, Organization, UserModel

    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    u1, u2 = uuid.UUID(USER1), uuid.UUID(USER2)
    o1, o2 = uuid.UUID(ORG1), uuid.UUID(ORG2)
    async with AsyncSession(engine) as s:
        s.add_all(
            [
                UserModel(id=u1, email="u1@example.com"),
                UserModel(id=u2, email="u2@example.com"),
                Organization(id=o1, name="Org1", slug="org1", owner_id=u1),
                Organization(id=o2, name="Org2", slug="org2", owner_id=u2),
            ]
        )
        await s.flush()  # ensure orgs exist before membership FKs
        s.add_all(
            [
                Membership(org_id=o1, user_id=u1, role="owner"),
                Membership(org_id=o2, user_id=u2, role="owner"),
            ]
        )
        await s.commit()
    await engine.dispose()


@pytest.fixture(scope="module")
def client():
    os.environ["SECUREAI_DATABASE_URL"] = TEST_DB
    os.environ["SECUREAI_SUPABASE_JWT_SECRET"] = JWT_SECRET
    os.environ["SECUREAI_DEV_SEED"] = "false"
    os.environ["SECUREAI_ENVIRONMENT"] = "test"

    from src.core.config import get_settings

    get_settings.cache_clear()
    asyncio.run(_reset_and_seed(TEST_DB))

    from src.main import create_app

    with TestClient(create_app()) as c:
        yield c


def h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_control_plane_and_data_plane_flow(client):
    t1 = _token(USER1, "u1@example.com")

    # Create project (auto-seeds 12 protect rules)
    r = client.post("/v1/projects", json={"name": "Demo App"}, headers=h(t1))
    assert r.status_code == 201, r.text
    project_id = r.json()["id"]

    assert any(p["id"] == project_id for p in client.get("/v1/projects", headers=h(t1)).json())

    rules = client.get(f"/v1/projects/{project_id}/protect-rules", headers=h(t1)).json()
    assert len(rules) == 12

    # Issue a Protect key (raw returned once)
    r = client.post(
        f"/v1/projects/{project_id}/api-keys",
        json={"keyType": "protect", "name": "server"},
        headers=h(t1),
    )
    assert r.status_code == 201
    protect_key = r.json()["apiKey"]
    assert protect_key.startswith("sk_protect_")

    # Use it against the data plane
    r = client.post(
        "/v1/protect",
        json={"text": "山田花子さんの email は taro@example.com"},
        headers=h(protect_key),
    )
    assert r.status_code == 200
    assert "taro@example.com" not in r.json()["maskedText"]

    # The request was logged (metadata only)
    logs = client.get(f"/v1/projects/{project_id}/logs", headers=h(t1)).json()
    assert len(logs) >= 1
    assert logs[0]["endpoint"] == "protect"
    assert logs[0]["entityCounts"].get("EMAIL_ADDRESS") == 1

    # Analytics reflects it
    summary = client.get(f"/v1/projects/{project_id}/analytics/summary", headers=h(t1)).json()
    assert summary["requests"] >= 1
    assert summary["protectCount"] >= 1

    # Disable the EMAIL rule -> data plane stops masking it
    new_rules = [{"entityType": r_["entityType"], "enabled": r_["entityType"] != "EMAIL_ADDRESS",
                  "action": r_["action"], "priority": r_["priority"]} for r_ in rules]
    client.put(f"/v1/projects/{project_id}/protect-rules", json={"rules": new_rules}, headers=h(t1))
    r = client.post("/v1/protect", json={"text": "taro@example.com"}, headers=h(protect_key))
    assert r.json()["maskedText"] == "taro@example.com"


def test_analyze_flow_with_echo_provider(client):
    t1 = _token(USER1, "u1@example.com")
    project_id = client.post("/v1/projects", json={"name": "Analyze App"}, headers=h(t1)).json()["id"]

    client.post(
        f"/v1/projects/{project_id}/providers",
        json={"providerType": "echo", "displayName": "Dev Echo"},
        headers=h(t1),
    )
    analyze_key = client.post(
        f"/v1/projects/{project_id}/api-keys",
        json={"keyType": "analyze"},
        headers=h(t1),
    ).json()["apiKey"]

    r = client.post(
        "/v1/analyze",
        json={"text": "顧客 田中太郎さん (taro@example.com) を要約"},
        headers=h(analyze_key),
    )
    assert r.status_code == 200
    body = r.json()
    assert "taro@example.com" not in body["analysis"]
    assert "田中太郎" not in body["analysis"]


def test_tenant_isolation(client):
    t1 = _token(USER1, "u1@example.com")
    t2 = _token(USER2, "u2@example.com")
    project_id = client.post("/v1/projects", json={"name": "Private"}, headers=h(t1)).json()["id"]

    # User2 (different org) must not access user1's project.
    assert client.get(f"/v1/projects/{project_id}", headers=h(t2)).status_code == 403
    assert (
        client.post(
            f"/v1/projects/{project_id}/api-keys",
            json={"keyType": "protect"},
            headers=h(t2),
        ).status_code
        == 403
    )


def test_requires_auth(client):
    assert client.get("/v1/projects").status_code == 401
    assert client.post("/v1/projects", json={"name": "x"}).status_code == 401
