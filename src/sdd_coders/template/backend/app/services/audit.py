"""Audit logging service (constitution §7). Append-only by RLS + grants."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def record_audit(  # noqa: PLR0913 - an audit record legitimately has many fields
    session: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> None:
    """Insert one immutable audit record into the session's transaction."""
    session.add(
        AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            request_id=request_id,
        )
    )
