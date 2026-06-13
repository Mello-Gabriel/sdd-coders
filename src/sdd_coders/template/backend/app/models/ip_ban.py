"""IP ban record model."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IpBan(Base):
    """Tracks IP bans with escalating durations."""

    __tablename__ = "ip_bans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(45), index=True, nullable=False)
    violation_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # Strikes accumulated within the current window before a ban is issued.
    # See app.services.abuse.register_failure.
    failed_attempts: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    window_start: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    banned_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_permanent: Mapped[bool] = mapped_column(default=False, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.UTC),
        nullable=False,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.UTC),
        onupdate=lambda: dt.datetime.now(dt.UTC),
        nullable=False,
    )
