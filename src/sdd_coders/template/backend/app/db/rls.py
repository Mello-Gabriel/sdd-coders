"""Row-Level Security policies, the application role and table grants.

These functions are the single source of truth for the database's security
posture (constitution §5). They are called by the Alembic migration (for real
databases) and by the test fixtures, so policies are never duplicated.

All functions take a synchronous :class:`~sqlalchemy.Connection`; async callers
use ``await conn.run_sync(apply_rls)``.
"""

from __future__ import annotations

from sqlalchemy import Connection, text

#: Name of the least-privilege role the application connects as (no BYPASSRLS).
APP_ROLE = "app_user"

_RLS_STATEMENTS: tuple[str, ...] = (
    # --- users -------------------------------------------------------------
    "ALTER TABLE users ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE users FORCE ROW LEVEL SECURITY",
    (
        "CREATE POLICY users_self ON users USING "
        "(id = nullif(current_setting('app.current_user_id', true), '')::uuid)"
    ),
    (
        "CREATE POLICY users_admin ON users USING "
        "(current_setting('app.current_role', true) = 'admin')"
    ),
    (
        "CREATE POLICY users_service ON users "
        "USING (current_setting('app.current_role', true) = 'service') "
        "WITH CHECK (current_setting('app.current_role', true) = 'service')"
    ),
    # --- projects ----------------------------------------------------------
    "ALTER TABLE projects ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE projects FORCE ROW LEVEL SECURITY",
    (
        "CREATE POLICY projects_owner ON projects USING "
        "(owner_id = nullif(current_setting('app.current_user_id', true), '')::uuid)"
    ),
    (
        "CREATE POLICY projects_admin ON projects USING "
        "(current_setting('app.current_role', true) = 'admin')"
    ),
    # --- refresh_tokens ----------------------------------------------------
    "ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE refresh_tokens FORCE ROW LEVEL SECURITY",
    (
        "CREATE POLICY rt_owner ON refresh_tokens USING "
        "(user_id = nullif(current_setting('app.current_user_id', true), '')::uuid)"
    ),
    (
        "CREATE POLICY rt_service ON refresh_tokens "
        "USING (current_setting('app.current_role', true) = 'service') "
        "WITH CHECK (current_setting('app.current_role', true) = 'service')"
    ),
    # --- audit_log (append-only) ------------------------------------------
    "ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE audit_log FORCE ROW LEVEL SECURITY",
    (
        "CREATE POLICY audit_admin_select ON audit_log FOR SELECT "
        "USING (current_setting('app.current_role', true) = 'admin')"
    ),
    (
        "CREATE POLICY audit_service_select ON audit_log FOR SELECT "
        "USING (current_setting('app.current_role', true) = 'service')"
    ),
    "CREATE POLICY audit_insert ON audit_log FOR INSERT WITH CHECK (true)",
    # --- consents (append-only history; owner reads own, admin reads all) --
    "ALTER TABLE consents ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE consents FORCE ROW LEVEL SECURITY",
    (
        "CREATE POLICY consents_owner ON consents USING "
        "(user_id = nullif(current_setting('app.current_user_id', true), '')::uuid)"
    ),
    (
        "CREATE POLICY consents_admin ON consents FOR SELECT "
        "USING (current_setting('app.current_role', true) = 'admin')"
    ),
)

# audit_log intentionally omits UPDATE/DELETE grants → append-only.
# consents likewise omits UPDATE/DELETE → append-only history.
_GRANT_STATEMENTS: tuple[str, ...] = (
    "GRANT USAGE ON SCHEMA public TO app_user",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON users TO app_user",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON projects TO app_user",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON refresh_tokens TO app_user",
    "GRANT SELECT, INSERT ON audit_log TO app_user",
    "GRANT SELECT, INSERT ON consents TO app_user",
    # ip_bans: not user-specific data; middleware reads/writes without RLS context.
    # DELETE is needed for lazy retention cleanup of expired non-permanent bans.
    "GRANT SELECT, INSERT, UPDATE, DELETE ON ip_bans TO app_user",
    "GRANT USAGE, SELECT ON SEQUENCE ip_bans_id_seq TO app_user",
)

_ENSURE_ROLE = """
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user LOGIN PASSWORD 'app_pass'
      NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
END $$;
"""


def ensure_app_role(connection: Connection) -> None:
    """Create the least-privilege ``app_user`` role if it does not exist.

    The dev password is for local/test only; production provisions the role and
    password out of band (see ``infra/`` and ``.env``).
    """
    connection.execute(text(_ENSURE_ROLE))


def apply_rls(connection: Connection) -> None:
    """Enable + force RLS and (re)create every policy."""
    for statement in _RLS_STATEMENTS:
        connection.execute(text(statement))


def grant_app_privileges(connection: Connection) -> None:
    """Grant the application role table-level privileges (RLS still applies)."""
    for statement in _GRANT_STATEMENTS:
        connection.execute(text(statement))
