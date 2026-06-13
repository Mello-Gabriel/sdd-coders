"""Admin endpoints: user management and audit-log access (require_admin)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from app.main import app
from app.models import User
from app.services.email import MemoryProvider, get_email_provider
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import fetch_user_id

PW = "supersecret123"
ADMIN_EMAIL = "admin@example.com"


async def _set_verified(session: AsyncSession, user_id: str) -> None:
    user = await session.get(User, uuid.UUID(user_id))
    assert user is not None
    user.email_verified = True
    await session.commit()


async def _auth(client: AsyncClient, email: str, owner_session: AsyncSession) -> str:
    await client.post("/auth/register", json={"email": email, "password": PW})
    user_id = await fetch_user_id(owner_session, email)
    await _set_verified(owner_session, user_id)
    await client.post("/auth/login", json={"email": email, "password": PW})
    return user_id


@pytest_asyncio.fixture
async def admin_client(owner_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """An authenticated admin client (registered, promoted via owner, logged in)."""
    provider = get_email_provider()
    if isinstance(provider, MemoryProvider):
        provider.clear()
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    await client.post("/auth/register", json={"email": ADMIN_EMAIL, "password": PW})
    admin_id = uuid.UUID(await fetch_user_id(owner_session, ADMIN_EMAIL))
    user = await owner_session.get(User, admin_id)
    assert user is not None
    user.role = "admin"
    user.email_verified = True
    await owner_session.commit()
    await client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": PW})
    try:
        yield client
    finally:
        await client.aclose()


async def test_non_admin_forbidden(client: AsyncClient, owner_session: AsyncSession) -> None:
    await _auth(client, "user@example.com", owner_session)
    response = await client.get("/admin/users")
    assert response.status_code == 403


async def test_list_users_as_admin(
    client: AsyncClient, admin_client: AsyncClient, owner_session: AsyncSession
) -> None:
    await _auth(client, "member@example.com", owner_session)
    response = await admin_client.get("/admin/users")
    assert response.status_code == 200
    emails = {row["email"] for row in response.json()}
    assert {ADMIN_EMAIL, "member@example.com"} <= emails


async def test_update_user_is_active(
    client: AsyncClient, admin_client: AsyncClient, owner_session: AsyncSession
) -> None:
    member_id = await _auth(client, "member@example.com", owner_session)
    response = await admin_client.patch(f"/admin/users/{member_id}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_update_user_role(
    client: AsyncClient, admin_client: AsyncClient, owner_session: AsyncSession
) -> None:
    member_id = await _auth(client, "member@example.com", owner_session)
    response = await admin_client.patch(f"/admin/users/{member_id}", json={"role": "admin"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


async def test_update_user_missing_returns_404(admin_client: AsyncClient) -> None:
    response = await admin_client.patch(f"/admin/users/{uuid.uuid4()}", json={"is_active": False})
    assert response.status_code == 404


async def test_list_audit_as_admin(admin_client: AsyncClient) -> None:
    response = await admin_client.get("/admin/audit")
    assert response.status_code == 200
    actions = {entry["action"] for entry in response.json()}
    assert "register" in actions
