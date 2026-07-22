"""Coolify client: verify the token, discover application UUIDs, push env vars.

Pushing env vars here means production runtime secrets go straight into Coolify and
never touch the generated repo or the developer's disk.
"""

from __future__ import annotations

import httpx


class CoolifyClient:
    def __init__(self, base_url: str, token: str, *, client: httpx.Client | None = None) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._client = client or httpx.Client(timeout=20.0)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def verify(self) -> bool:
        """True if the API token authenticates against this Coolify instance."""
        resp = self._client.get(f"{self._base}/api/v1/version", headers=self._headers())
        return resp.status_code == httpx.codes.OK

    def list_applications(self) -> list[dict[str, str]]:
        """Return ``[{'uuid':..., 'name':...}, ...]`` for all applications."""
        resp = self._client.get(f"{self._base}/api/v1/applications", headers=self._headers())
        resp.raise_for_status()
        apps = resp.json()
        return [{"uuid": str(a["uuid"]), "name": str(a.get("name", ""))} for a in apps]

    def resolve_uuids(self, names: dict[str, str]) -> dict[str, str]:
        """Map logical keys to UUIDs by matching ``names`` against existing app names."""
        by_name = {app["name"]: app["uuid"] for app in self.list_applications()}
        resolved: dict[str, str] = {}
        for key, app_name in names.items():
            if app_name in by_name:
                resolved[key] = by_name[app_name]
        return resolved

    def set_env(self, uuid: str, env: dict[str, str]) -> None:
        """Bulk-set environment variables on an application."""
        payload = {
            "data": [
                {"key": key, "value": value, "is_preview": False} for key, value in env.items()
            ]
        }
        resp = self._client.patch(
            f"{self._base}/api/v1/applications/{uuid}/envs/bulk",
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()
