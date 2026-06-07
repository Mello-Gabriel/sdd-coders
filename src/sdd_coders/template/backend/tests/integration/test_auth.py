"""Authentication endpoint tests (register, login, refresh, logout, me)."""

from __future__ import annotations

import datetime as dt
import uuid

from app.core.config import get_settings
from app.core.security import ACCESS_TOKEN, REFRESH_TOKEN, create_token
from app.main import app
from app.models import RefreshToken, User
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

CREDENTIALS = {"email": "user@example.com", "password": "supersecret123"}


def _bare_client() -> AsyncClient:
    """A client with no cookie jar, for sending explicit Cookie headers."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _register(client: AsyncClient) -> str:
    response = await client.post("/auth/register", json=CREDENTIALS)
    assert response.status_code == 201
    return str(response.json()["id"])


async def _login(client: AsyncClient) -> None:
    response = await client.post("/auth/login", json=CREDENTIALS)
    assert response.status_code == 200


async def _set_active(owner_session: AsyncSession, user_id: str, *, active: bool) -> None:
    user = await owner_session.get(User, uuid.UUID(user_id))
    assert user is not None
    user.is_active = active
    await owner_session.commit()


# --- register --------------------------------------------------------------


async def test_register_creates_user(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json=CREDENTIALS)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == CREDENTIALS["email"]
    assert body["role"] == "user"
    assert body["is_active"] is True


async def test_register_duplicate_conflicts(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post("/auth/register", json=CREDENTIALS)
    assert response.status_code == 409


# --- login -----------------------------------------------------------------


async def test_login_sets_cookies(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post("/auth/login", json=CREDENTIALS)
    assert response.status_code == 200
    assert client.cookies.get("access_token") is not None
    assert client.cookies.get("refresh_token") is not None


async def test_login_wrong_password(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post(
        "/auth/login", json={"email": CREDENTIALS["email"], "password": "wrong-password"}
    )
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever12"}
    )
    assert response.status_code == 401


async def test_login_inactive_user(client: AsyncClient, owner_session: AsyncSession) -> None:
    user_id = await _register(client)
    await _set_active(owner_session, user_id, active=False)
    response = await client.post("/auth/login", json=CREDENTIALS)
    assert response.status_code == 401


# --- me --------------------------------------------------------------------


async def test_me_returns_current_user(client: AsyncClient) -> None:
    await _register(client)
    await _login(client)
    response = await client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == CREDENTIALS["email"]


async def test_me_without_cookie_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_invalid_token(client: AsyncClient) -> None:
    response = await client.get("/auth/me", headers={"Cookie": "access_token=garbage"})
    assert response.status_code == 401


async def test_me_wrong_token_type(client: AsyncClient) -> None:
    refresh = create_token(str(uuid.uuid4()), REFRESH_TOKEN, settings=get_settings())
    response = await client.get("/auth/me", headers={"Cookie": f"access_token={refresh}"})
    assert response.status_code == 401


async def test_me_inactive_user(client: AsyncClient, owner_session: AsyncSession) -> None:
    user_id = await _register(client)
    await _login(client)
    await _set_active(owner_session, user_id, active=False)
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_deleted_user(client: AsyncClient, owner_session: AsyncSession) -> None:
    user_id = await _register(client)
    await _login(client)
    await owner_session.execute(delete(User).where(User.id == uuid.UUID(user_id)))
    await owner_session.commit()
    response = await client.get("/auth/me")
    assert response.status_code == 401


# --- refresh ---------------------------------------------------------------


async def test_refresh_rotates_and_revokes_old(client: AsyncClient) -> None:
    await _register(client)
    await _login(client)
    old_refresh = client.cookies.get("refresh_token")
    response = await client.post("/auth/refresh")
    assert response.status_code == 200
    async with _bare_client() as bare:
        replay = await bare.post(
            "/auth/refresh", headers={"Cookie": f"refresh_token={old_refresh}"}
        )
    assert replay.status_code == 401


async def test_refresh_missing_cookie(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh")
    assert response.status_code == 401


async def test_refresh_invalid_token(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh", headers={"Cookie": "refresh_token=garbage"})
    assert response.status_code == 401


async def test_refresh_wrong_token_type(client: AsyncClient) -> None:
    access = create_token(str(uuid.uuid4()), ACCESS_TOKEN, settings=get_settings())
    response = await client.post("/auth/refresh", headers={"Cookie": f"refresh_token={access}"})
    assert response.status_code == 401


async def test_refresh_unknown_row(client: AsyncClient) -> None:
    token = create_token(str(uuid.uuid4()), REFRESH_TOKEN, settings=get_settings(), jti="ghost")
    response = await client.post("/auth/refresh", headers={"Cookie": f"refresh_token={token}"})
    assert response.status_code == 401


async def test_refresh_expired(client: AsyncClient, owner_session: AsyncSession) -> None:
    user_id = await _register(client)
    past = dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=1)
    owner_session.add(
        RefreshToken(jti="expired-jti", user_id=uuid.UUID(user_id), expires_at=past, revoked=False)
    )
    await owner_session.commit()
    token = create_token(user_id, REFRESH_TOKEN, settings=get_settings(), jti="expired-jti")
    response = await client.post("/auth/refresh", headers={"Cookie": f"refresh_token={token}"})
    assert response.status_code == 401


async def test_refresh_inactive_user(client: AsyncClient, owner_session: AsyncSession) -> None:
    user_id = await _register(client)
    await _login(client)
    await _set_active(owner_session, user_id, active=False)
    response = await client.post("/auth/refresh")
    assert response.status_code == 401


# --- logout ----------------------------------------------------------------


async def test_logout_revokes_refresh(client: AsyncClient) -> None:
    await _register(client)
    await _login(client)
    old_refresh = client.cookies.get("refresh_token")
    response = await client.post("/auth/logout")
    assert response.status_code == 204
    async with _bare_client() as bare:
        replay = await bare.post(
            "/auth/refresh", headers={"Cookie": f"refresh_token={old_refresh}"}
        )
    assert replay.status_code == 401


async def test_logout_without_cookie(client: AsyncClient) -> None:
    response = await client.post("/auth/logout")
    assert response.status_code == 204


async def test_logout_ignores_invalid_token(client: AsyncClient) -> None:
    response = await client.post("/auth/logout", headers={"Cookie": "refresh_token=garbage"})
    assert response.status_code == 204


async def test_logout_ignores_unknown_row(client: AsyncClient) -> None:
    token = create_token(str(uuid.uuid4()), REFRESH_TOKEN, settings=get_settings(), jti="no-row")
    response = await client.post("/auth/logout", headers={"Cookie": f"refresh_token={token}"})
    assert response.status_code == 204
