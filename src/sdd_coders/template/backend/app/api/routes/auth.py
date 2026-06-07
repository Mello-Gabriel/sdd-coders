"""Authentication endpoints: register, login, refresh, logout, me."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import ACCESS_COOKIE, REFRESH_COOKIE, CurrentUser, ServiceSession
from app.core.config import get_settings
from app.schemas.auth import LoginRequest, RegisterRequest, UserRead
from app.services.audit import record_audit
from app.services.auth import (
    authenticate,
    get_user_by_email,
    issue_tokens,
    register_user,
    revoke_refresh,
    rotate_tokens,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    settings = get_settings()
    secure = settings.environment != "development"
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.access_token_ttl_seconds,
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.refresh_token_ttl_seconds,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: ServiceSession) -> UserRead:
    if await get_user_by_email(session, payload.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = await register_user(session, payload.email, payload.password)
    await record_audit(
        session,
        actor_id=user.id,
        actor_role="user",
        action="register",
        entity_type="user",
        entity_id=str(user.id),
    )
    return UserRead.model_validate(user)


@router.post("/login")
async def login(payload: LoginRequest, response: Response, session: ServiceSession) -> UserRead:
    user = await authenticate(session, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access, refresh = await issue_tokens(session, user)
    _set_auth_cookies(response, access, refresh)
    await record_audit(
        session,
        actor_id=user.id,
        actor_role=user.role,
        action="login",
        entity_type="user",
        entity_id=str(user.id),
    )
    return UserRead.model_validate(user)


@router.post("/refresh")
async def refresh(request: Request, response: Response, session: ServiceSession) -> UserRead:
    token = request.cookies.get(REFRESH_COOKIE)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )
    result = await rotate_tokens(session, token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    user, access, new_refresh = result
    _set_auth_cookies(response, access, new_refresh)
    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, session: ServiceSession) -> Response:
    token = request.cookies.get(REFRESH_COOKIE)
    if token is not None:
        await revoke_refresh(session, token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")
    return response


@router.get("/me")
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
