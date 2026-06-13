"""Authentication endpoint tests (register, login, refresh, logout, me, verify, reset)."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from app.core.config import get_settings
from app.core.security import ACCESS_TOKEN, REFRESH_TOKEN, create_token
from app.main import app
from app.models import RefreshToken, User
from app.services.email import MemoryProvider, get_email_provider
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

CREDENTIALS = {"email": "user@example.com", "password": "supersecret123"}


def _bare_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def _clear_email_outbox() -> None:
    provider = get_email_provider()
    if isinstance(provider, MemoryProvider):
        provider.clear()


async def _register(client: AsyncClient) -> str:
    response = await client.post("/auth/register", json=CREDENTIALS)
    assert response.status_code == 201
    return str(response.json()["id"])


async def _set_verified(
    owner_session: AsyncSession, user_id: str, *, verified: bool = True
) -> None:
    user = await owner_session.get(User, uuid.UUID(user_id))
    assert user is not None
    user.email_verified = verified
    await owner_session.commit()


async def _set_active(owner_session: AsyncSession, user_id: str, *, active: bool) -> None:
    user = await owner_session.get(User, uuid.UUID(user_id))
    assert user is not None
    user.is_active = active
    await owner_session.commit()


async def _register_and_login(client: AsyncClient, owner_session: AsyncSession) -> str:
    user_id = await _register(client)
    await _set_verified(owner_session, user_id)
    response = await client.post("/auth/login", json=CREDENTIALS)
    assert response.status_code == 200
    return user_id


# --- register --------------------------------------------------------------


async def test_register_creates_user(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json=CREDENTIALS)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == CREDENTIALS["email"]
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert body["email_verified"] is False


async def test_register_sends_verification_email(client: AsyncClient) -> None:
    await client.post("/auth/register", json=CREDENTIALS)
    provider = get_email_provider()
    assert isinstance(provider, MemoryProvider)
    assert len(provider.outbox) == 1
    assert "verify" in provider.outbox[0].html.lower()


async def test_register_duplicate_conflicts(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post("/auth/register", json=CREDENTIALS)
    assert response.status_code == 409


# --- login -----------------------------------------------------------------


async def test_login_sets_cookies(client: AsyncClient, owner_session: AsyncSession) -> None:
    user_id = await _register(client)
    await _set_verified(owner_session, user_id)
    response = await client.post("/auth/login", json=CREDENTIALS)
    assert response.status_code == 200
    assert client.cookies.get("access_token") is not None
    assert client.cookies.get("refresh_token") is not None


async def test_login_blocked_when_not_verified(client: AsyncClient) -> None:
    await _register(client)
    response = await client.post("/auth/login", json=CREDENTIALS)
    assert response.status_code == 403
    assert "verified" in response.json()["detail"].lower()


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


async def test_me_returns_current_user(client: AsyncClient, owner_session: AsyncSession) -> None:
    await _register_and_login(client, owner_session)
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
    user_id = await _register_and_login(client, owner_session)
    await _set_active(owner_session, user_id, active=False)
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_deleted_user(client: AsyncClient, owner_session: AsyncSession) -> None:
    user_id = await _register_and_login(client, owner_session)
    await owner_session.execute(delete(User).where(User.id == uuid.UUID(user_id)))
    await owner_session.commit()
    response = await client.get("/auth/me")
    assert response.status_code == 401


# --- refresh ---------------------------------------------------------------


async def test_refresh_rotates_and_revokes_old(
    client: AsyncClient, owner_session: AsyncSession
) -> None:
    await _register_and_login(client, owner_session)
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
    user_id = await _register_and_login(client, owner_session)
    await _set_active(owner_session, user_id, active=False)
    response = await client.post("/auth/refresh")
    assert response.status_code == 401


# --- logout ----------------------------------------------------------------


async def test_logout_revokes_refresh(client: AsyncClient, owner_session: AsyncSession) -> None:
    await _register_and_login(client, owner_session)
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


# --- email verification ----------------------------------------------------


async def test_request_verification_no_op_for_unknown_email(client: AsyncClient) -> None:
    response = await client.post("/auth/request-verification", json={"email": "ghost@example.com"})
    assert response.status_code == 204


async def test_request_verification_sends_email(client: AsyncClient) -> None:
    await _register(client)
    provider = get_email_provider()
    assert isinstance(provider, MemoryProvider)
    provider.clear()
    response = await client.post("/auth/request-verification", json={"email": CREDENTIALS["email"]})
    assert response.status_code == 204
    assert len(provider.outbox) == 1


async def test_request_verification_already_verified(
    client: AsyncClient, owner_session: AsyncSession
) -> None:
    user_id = await _register(client)
    await _set_verified(owner_session, user_id)
    provider = get_email_provider()
    assert isinstance(provider, MemoryProvider)
    provider.clear()
    response = await client.post("/auth/request-verification", json={"email": CREDENTIALS["email"]})
    assert response.status_code == 204
    assert len(provider.outbox) == 0


async def test_verify_email_token_marks_verified(client: AsyncClient) -> None:
    await _register(client)
    provider = get_email_provider()
    assert isinstance(provider, MemoryProvider)
    email = provider.outbox[0]
    token = email.html.split("token=")[1].split("'")[0]
    response = await client.post("/auth/verify-email", json={"token": token})
    assert response.status_code == 200
    assert response.json()["email_verified"] is True


async def test_verify_email_invalid_token(client: AsyncClient) -> None:
    response = await client.post("/auth/verify-email", json={"token": "garbage"})
    assert response.status_code == 400


# --- password reset --------------------------------------------------------


async def test_request_password_reset_no_op_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/request-password-reset", json={"email": "ghost@example.com"}
    )
    assert response.status_code == 204


async def test_request_password_reset_sends_email(client: AsyncClient) -> None:
    await _register(client)
    provider = get_email_provider()
    assert isinstance(provider, MemoryProvider)
    provider.clear()
    response = await client.post(
        "/auth/request-password-reset", json={"email": CREDENTIALS["email"]}
    )
    assert response.status_code == 204
    assert len(provider.outbox) == 1
    assert "reset" in provider.outbox[0].html.lower()


async def test_reset_password_updates_credentials(
    client: AsyncClient, owner_session: AsyncSession
) -> None:
    user_id = await _register(client)
    await _set_verified(owner_session, user_id)
    provider = get_email_provider()
    assert isinstance(provider, MemoryProvider)
    provider.clear()
    await client.post("/auth/request-password-reset", json={"email": CREDENTIALS["email"]})
    token = provider.outbox[0].html.split("token=")[1].split("'")[0]
    response = await client.post(
        "/auth/reset-password", json={"token": token, "new_password": "newPassword999"}
    )
    assert response.status_code == 200
    login = await client.post(
        "/auth/login", json={"email": CREDENTIALS["email"], "password": "newPassword999"}
    )
    assert login.status_code == 200


async def test_reset_password_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/reset-password", json={"token": "garbage", "new_password": "newPassword999"}
    )
    assert response.status_code == 400


# --- change password -------------------------------------------------------


async def test_change_password(client: AsyncClient, owner_session: AsyncSession) -> None:
    await _register_and_login(client, owner_session)
    response = await client.post(
        "/auth/change-password",
        json={"current_password": CREDENTIALS["password"], "new_password": "changedPass999"},
    )
    assert response.status_code == 204
    await client.post("/auth/logout")
    login = await client.post(
        "/auth/login", json={"email": CREDENTIALS["email"], "password": "changedPass999"}
    )
    assert login.status_code == 200


async def test_change_password_wrong_current(
    client: AsyncClient, owner_session: AsyncSession
) -> None:
    await _register_and_login(client, owner_session)
    response = await client.post(
        "/auth/change-password",
        json={"current_password": "wrongpassword", "new_password": "newPass999"},
    )
    assert response.status_code == 400


async def test_change_password_unauthenticated(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/change-password",
        json={"current_password": CREDENTIALS["password"], "new_password": "newPass999"},
    )
    assert response.status_code == 401


async def test_register_captcha_rejected(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_TURNSTILE_ENABLED", "true")
    get_settings.cache_clear()
    resp = await client.post(
        "/auth/register",
        json={"email": "cap@example.com", "password": "pass123456", "turnstile_token": ""},
    )
    get_settings.cache_clear()
    assert resp.status_code == 422


async def test_request_password_reset_captcha_rejected(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_TURNSTILE_ENABLED", "true")
    get_settings.cache_clear()
    resp = await client.post(
        "/auth/request-password-reset",
        json={"email": "cap@example.com", "turnstile_token": ""},
    )
    get_settings.cache_clear()
    assert resp.status_code == 422
