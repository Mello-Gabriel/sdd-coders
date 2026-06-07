"""initial schema + RLS policies + grants

Revision ID: 0001
Revises:
Create Date: 2026-06-06

Creates all tables from the ORM metadata, then enables/forces Row-Level
Security and grants the least-privilege app role. The role itself is
provisioned out of band (see infra/ and rls.ensure_app_role for dev/test).
"""

from __future__ import annotations

from alembic import op
from app.db.rls import apply_rls, grant_app_privileges
from app.models import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind)
    apply_rls(bind)
    grant_app_privileges(bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
