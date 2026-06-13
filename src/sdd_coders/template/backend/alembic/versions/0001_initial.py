"""initial schema + RLS policies + grants

Revision ID: 0001
Revises:
Create Date: 2026-06-06

Creates every table with explicit DDL (never ``metadata.create_all`` — the live
ORM metadata drifts over time and would make this migration non-deterministic),
then enables/forces Row-Level Security and grants the least-privilege app role.
The role itself is provisioned out of band (see infra/ and rls.ensure_app_role
for dev/test). Policies and grants live in ``app.db.rls`` (single source of truth).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from app.db.rls import apply_rls, grant_app_privileges
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_TIMESTAMP = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", _TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", _TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", _TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", _TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("jti", sa.String(64), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", _TIMESTAMP, nullable=False),
        sa.Column("created_at", _TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("occurred_at", _TIMESTAMP, nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_role", sa.String(20), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("before", postgresql.JSONB(), nullable=True),
        sa.Column("after", postgresql.JSONB(), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
    )
    op.create_index("ix_audit_log_occurred_at", "audit_log", ["occurred_at"])

    op.create_table(
        "ip_bans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("violation_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_start", _TIMESTAMP, nullable=True),
        sa.Column("banned_until", _TIMESTAMP, nullable=True),
        sa.Column("is_permanent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", _TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", _TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ip_bans_ip_address", "ip_bans", ["ip_address"])

    op.create_table(
        "consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("analytics", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("marketing", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", _TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_consents_user_id", "consents", ["user_id"])
    op.create_index("ix_consents_created_at", "consents", ["created_at"])

    bind = op.get_bind()
    apply_rls(bind)
    grant_app_privileges(bind)


def downgrade() -> None:
    for table in (
        "consents",
        "ip_bans",
        "audit_log",
        "refresh_tokens",
        "projects",
        "users",
    ):
        op.drop_table(table)
