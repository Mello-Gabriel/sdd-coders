"""Project request/response schemas."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Payload to create a project."""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)


class ProjectUpdate(BaseModel):
    """Partial update; only provided fields change."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)


class ProjectRead(BaseModel):
    """Public representation of a project."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str
    created_at: dt.datetime
    updated_at: dt.datetime
