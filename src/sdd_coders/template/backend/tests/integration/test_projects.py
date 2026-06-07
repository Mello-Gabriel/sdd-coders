"""Project CRUD over HTTP, with RLS isolation enforced by Postgres."""

from __future__ import annotations

import uuid

from app.main import app
from httpx import ASGITransport, AsyncClient

PW = "supersecret123"


async def _auth(client: AsyncClient, email: str = "a@example.com") -> None:
    creds = {"email": email, "password": PW}
    await client.post("/auth/register", json=creds)
    await client.post("/auth/login", json=creds)


async def _create(
    client: AsyncClient, name: str = "Alpha", description: str = ""
) -> dict[str, str]:
    response = await client.post("/projects", json={"name": name, "description": description})
    assert response.status_code == 201
    body: dict[str, str] = response.json()
    return body


async def test_create_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/projects", json={"name": "X"})
    assert response.status_code == 401


async def test_create_and_get(client: AsyncClient) -> None:
    await _auth(client)
    created = await _create(client, name="Alpha", description="d")
    response = await client.get(f"/projects/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Alpha"


async def test_list_projects(client: AsyncClient) -> None:
    await _auth(client)
    await _create(client, name="P1")
    await _create(client, name="P2")
    response = await client.get("/projects")
    assert response.status_code == 200
    assert {p["name"] for p in response.json()} == {"P1", "P2"}


async def test_get_missing_returns_404(client: AsyncClient) -> None:
    await _auth(client)
    response = await client.get(f"/projects/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_update_name_only(client: AsyncClient) -> None:
    await _auth(client)
    created = await _create(client, name="Old", description="keep")
    response = await client.patch(f"/projects/{created['id']}", json={"name": "New"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New"
    assert body["description"] == "keep"


async def test_update_description_only(client: AsyncClient) -> None:
    await _auth(client)
    created = await _create(client, name="Keep", description="old")
    response = await client.patch(f"/projects/{created['id']}", json={"description": "new"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Keep"
    assert body["description"] == "new"


async def test_update_missing_returns_404(client: AsyncClient) -> None:
    await _auth(client)
    response = await client.patch(f"/projects/{uuid.uuid4()}", json={"name": "X"})
    assert response.status_code == 404


async def test_delete_project(client: AsyncClient) -> None:
    await _auth(client)
    created = await _create(client)
    response = await client.delete(f"/projects/{created['id']}")
    assert response.status_code == 204
    assert (await client.get(f"/projects/{created['id']}")).status_code == 404


async def test_delete_missing_returns_404(client: AsyncClient) -> None:
    await _auth(client)
    response = await client.delete(f"/projects/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_rls_isolation_between_users(client: AsyncClient) -> None:
    await _auth(client, "a@example.com")
    created = await _create(client, name="Secret")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as other:
        await _auth(other, "b@example.com")
        assert (await other.get(f"/projects/{created['id']}")).status_code == 404
        assert (await other.get("/projects")).json() == []
