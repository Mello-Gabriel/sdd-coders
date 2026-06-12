"""Add email_verified to users and create ip_bans table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.create_table(
        "ip_bans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ip_address", sa.String(45), nullable=False, index=True),
        sa.Column("violation_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("banned_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_permanent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_ip_bans_ip_address", "ip_bans", ["ip_address"])


def downgrade() -> None:
    op.drop_index("ix_ip_bans_ip_address", table_name="ip_bans")
    op.drop_table("ip_bans")
    op.drop_column("users", "email_verified")
