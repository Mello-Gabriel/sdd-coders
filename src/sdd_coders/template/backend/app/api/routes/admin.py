"""Admin area: user management and audit-log access. Guarded by require_admin."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminSession, AdminUser
from app.models import AuditLog, User
from app.schemas.admin import AuditRead, UserUpdate
from app.schemas.auth import UserRead
from app.services.audit import record_audit

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(session: AdminSession) -> list[UserRead]:
    rows = (await session.scalars(select(User).order_by(User.created_at))).all()
    return [UserRead.model_validate(user) for user in rows]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID, payload: UserUpdate, admin: AdminUser, session: AdminSession
) -> UserRead:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    before: dict[str, Any] = {"is_active": user.is_active, "role": user.role}
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        user.role = payload.role
    after: dict[str, Any] = {"is_active": user.is_active, "role": user.role}
    await record_audit(
        session,
        actor_id=admin.id,
        actor_role=admin.role,
        action="user_update",
        entity_type="user",
        entity_id=str(user.id),
        before=before,
        after=after,
    )
    return UserRead.model_validate(user)


@router.get("/audit")
async def list_audit(session: AdminSession) -> list[AuditRead]:
    rows = (await session.scalars(select(AuditLog).order_by(AuditLog.occurred_at))).all()
    return [AuditRead.model_validate(entry) for entry in rows]
