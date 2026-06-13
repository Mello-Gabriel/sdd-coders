"""Schemas for the data-subject (LGPD) endpoints under /me."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.auth import UserRead
from app.schemas.project import ProjectRead


class ConsentWrite(BaseModel):
    """Payload to record a consent decision."""

    analytics: bool = False
    marketing: bool = False


class ConsentRead(BaseModel):
    """A recorded consent decision."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    analytics: bool
    marketing: bool
    created_at: dt.datetime


class DataExport(BaseModel):
    """Everything we hold about the authenticated user (LGPD access right)."""

    user: UserRead
    projects: list[ProjectRead]
    consents: list[ConsentRead]
    audit: list[dict[str, Any]]
