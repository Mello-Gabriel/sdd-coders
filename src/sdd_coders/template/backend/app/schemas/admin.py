"""Admin request/response schemas."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserUpdate(BaseModel):
    """Admin update of a user's status or role."""

    is_active: bool | None = None
    role: Literal["user", "admin"] | None = None


class AuditRead(BaseModel):
    """One audit-log record (admin-only read)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    occurred_at: dt.datetime
    actor_id: uuid.UUID | None
    actor_role: str
    action: str
    entity_type: str
    entity_id: str | None
