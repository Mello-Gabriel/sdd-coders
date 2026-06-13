"""Data-subject (LGPD) endpoints: consent, export, delete — with RLS isolation."""

from __future__ import annotations

import uuid

from app.main import app
from app.models import Project, RefreshToken, User
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import fetch_user_id

PW = "supersecret123"


async def _auth(client: AsyncClient, owner_session: AsyncSession, email: str) -> str:
    creds = {"email": email, "password": PW}
    await client.post("/auth/register", json=creds)
    user_id = await fetch_user_id(owner_session, email)
    user = await owner_session.get(User, uuid.UUID(user_id))
    assert user is not None
    user.email_verified = True
    await owner_session.commit()
    await client.post("/auth/login", json=creds)
    return user_id


async def test_set_and_get_consent(client: AsyncClient, owner_session: AsyncSession) -> None:
    await _auth(client, owner_session, "c@example.com")
    created = await client.post("/me/consent", json={"analytics": True, "marketing": False})
    assert created.status_code == 201
    assert created.json()["analytics"] is True
    latest = await client.get("/me/consent")
    assert latest.status_code == 200
    assert latest.json()["analytics"] is True


async def test_get_consent_none_when_absent(
    client: AsyncClient, owner_session: AsyncSession
) -> None:
    await _auth(client, owner_session, "c2@example.com")
    response = await client.get("/me/consent")
    assert response.status_code == 200
    assert response.json() is None


async def test_consent_is_rls_isolated(owner_session: AsyncSession) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as a:
        await _auth(a, owner_session, "owner-a@example.com")
        await a.post("/me/consent", json={"analytics": True, "marketing": True})
    async with AsyncClient(transport=transport, base_url="http://test") as b:
        await _auth(b, owner_session, "owner-b@example.com")
        # B has never set consent — must not see A's row.
        assert (await b.get("/me/consent")).json() is None


async def test_data_export_includes_everything(
    client: AsyncClient, owner_session: AsyncSession
) -> None:
    await _auth(client, owner_session, "export@example.com")
    await client.post("/projects", json={"name": "Proj", "description": "d"})
    await client.post("/me/consent", json={"analytics": True, "marketing": False})
    export = await client.get("/me/data-export")
    assert export.status_code == 200
    body = export.json()
    assert body["user"]["email"] == "export@example.com"
    assert len(body["projects"]) == 1
    assert len(body["consents"]) == 1
    # The register + project-create actions are in the user's audit trail.
    actions = {entry["action"] for entry in body["audit"]}
    assert {"register", "create"} <= actions


async def test_delete_me_anonymises_and_revokes(
    client: AsyncClient, owner_session: AsyncSession
) -> None:
    user_id = await _auth(client, owner_session, "gone@example.com")
    await client.post("/projects", json={"name": "Doomed", "description": ""})
    response = await client.delete("/me")
    assert response.status_code == 204

    user = await owner_session.get(User, uuid.UUID(user_id))
    assert user is not None
    assert user.is_active is False
    assert user.email == f"deleted-{user_id}@anon.invalid"

    projects = (
        await owner_session.scalars(select(Project).where(Project.owner_id == uuid.UUID(user_id)))
    ).all()
    assert projects == []

    tokens = (
        await owner_session.scalars(
            select(RefreshToken).where(RefreshToken.user_id == uuid.UUID(user_id))
        )
    ).all()
    assert all(t.revoked for t in tokens)
