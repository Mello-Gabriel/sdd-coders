"""Authentication endpoints: register, login, refresh, logout, me, verify, reset."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import ACCESS_COOKIE, REFRESH_COOKIE, CurrentUser, ServiceSession, UserSession
from app.core.client_ip import get_client_ip
from app.core.config import get_settings
from app.core.limiter import limiter
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    RequestPasswordResetRequest,
    RequestVerificationRequest,
    ResetPasswordRequest,
    UserRead,
    VerifyEmailRequest,
)
from app.services.abuse import register_failure
from app.services.audit import record_audit
from app.services.auth import (
    authenticate,
    get_user_by_email,
    issue_tokens,
    register_user,
    revoke_refresh,
    rotate_tokens,
)
from app.services.turnstile import verify_turnstile
from app.services.verification import (
    change_password,
    reset_password,
    send_password_reset_email,
    send_verification_email,
    verify_email_token,
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
@limiter.limit("3/minute")
async def register(request: Request, payload: RegisterRequest, session: ServiceSession) -> UserRead:
    if not await verify_turnstile(payload.turnstile_token):
        await register_failure(get_client_ip(request), reason="captcha (register)")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Captcha inválido"
        )
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
    await send_verification_email(user)
    return UserRead.model_validate(user)


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request, payload: LoginRequest, response: Response, session: ServiceSession
) -> UserRead:
    user = await authenticate(session, payload.email, payload.password)
    if user is None:
        await register_failure(get_client_ip(request), reason="invalid credentials")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Check your inbox.",
        )
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
@limiter.limit("30/minute")
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


@router.post("/request-verification", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/hour")
async def request_verification(
    request: Request, payload: RequestVerificationRequest, session: ServiceSession
) -> Response:
    user = await get_user_by_email(session, payload.email)
    if user is not None and not user.email_verified:
        await send_verification_email(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email")
@limiter.limit("10/minute")
async def verify_email(
    request: Request, payload: VerifyEmailRequest, session: ServiceSession
) -> UserRead:
    user = await verify_email_token(session, payload.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )
    return UserRead.model_validate(user)


@router.post("/request-password-reset", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/hour")
async def request_password_reset(
    request: Request, payload: RequestPasswordResetRequest, session: ServiceSession
) -> Response:
    if not await verify_turnstile(payload.turnstile_token):
        await register_failure(get_client_ip(request), reason="captcha (reset)")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Captcha inválido"
        )
    await send_password_reset_email(session, payload.email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password_endpoint(
    request: Request, payload: ResetPasswordRequest, session: ServiceSession
) -> UserRead:
    user = await reset_password(session, payload.token, payload.new_password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )
    return UserRead.model_validate(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password_endpoint(
    payload: ChangePasswordRequest, session: UserSession, current_user: CurrentUser
) -> Response:
    success = await change_password(
        session, current_user, payload.current_password, payload.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
