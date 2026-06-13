"""Data-subject endpoints (LGPD): export, delete, and consent self-service.

All run in the authenticated user's RLS context, so a user can only ever touch
their own rows. The audit export reads through a service-context session because
audit_log is admin/service-read-only.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ACCESS_COOKIE, REFRESH_COOKIE, CurrentUser, UserSession
from app.core.db import SERVICE_CONTEXT, session_scope
from app.models import AuditLog, Consent, Project, User
from app.schemas.auth import UserRead
from app.schemas.me import ConsentRead, ConsentWrite, DataExport
from app.schemas.project import ProjectRead
from app.services.audit import record_audit
from app.services.auth import revoke_all_refresh

router = APIRouter(prefix="/me", tags=["me"])

# Refresh cookie is scoped to /auth (see auth routes); mirror that on deletion.
_REFRESH_PATH = "/auth"


async def _latest_consent(session: AsyncSession, user_id: uuid.UUID) -> Consent | None:
    return (
        await session.scalars(
            select(Consent).where(Consent.user_id == user_id).order_by(Consent.created_at.desc())
        )
    ).first()


@router.get("/consent")
async def get_consent(user: CurrentUser, session: UserSession) -> ConsentRead | None:
    consent = await _latest_consent(session, user.id)
    return ConsentRead.model_validate(consent) if consent else None


@router.post("/consent", status_code=status.HTTP_201_CREATED)
async def set_consent(
    payload: ConsentWrite, user: CurrentUser, session: UserSession
) -> ConsentRead:
    consent = Consent(user_id=user.id, analytics=payload.analytics, marketing=payload.marketing)
    session.add(consent)
    await session.flush()
    return ConsentRead.model_validate(consent)


@router.get("/data-export")
async def data_export(user: CurrentUser, session: UserSession) -> DataExport:
    projects = (await session.scalars(select(Project).order_by(Project.created_at))).all()
    consents = (await session.scalars(select(Consent).order_by(Consent.created_at))).all()
    # audit_log is admin/service-read-only → read the user's own actions via the
    # service context, exposing only non-sensitive fields.
    async with session_scope(SERVICE_CONTEXT) as svc:
        rows = (
            await svc.scalars(
                select(AuditLog).where(AuditLog.actor_id == user.id).order_by(AuditLog.occurred_at)
            )
        ).all()
        audit = [
            {
                "action": r.action,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "occurred_at": r.occurred_at.isoformat(),
            }
            for r in rows
        ]

    return DataExport(
        user=UserRead.model_validate(user),
        projects=[ProjectRead.model_validate(p) for p in projects],
        consents=[ConsentRead.model_validate(c) for c in consents],
        audit=audit,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: CurrentUser, session: UserSession) -> Response:
    db_user = await session.get(User, user.id)
    if db_user is None:  # pragma: no cover - CurrentUser guarantees the row exists
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    # Anonymise rather than hard-delete: keeps referential integrity and any
    # legally-required audit trail while removing the personal data.
    db_user.email = f"deleted-{db_user.id}@anon.invalid"
    db_user.is_active = False
    await session.execute(delete(Project).where(Project.owner_id == user.id))
    await revoke_all_refresh(session, user.id)
    await record_audit(
        session,
        actor_id=user.id,
        actor_role=user.role,
        action="delete_account",
        entity_type="user",
        entity_id=str(user.id),
    )
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path=_REFRESH_PATH)
    return response
