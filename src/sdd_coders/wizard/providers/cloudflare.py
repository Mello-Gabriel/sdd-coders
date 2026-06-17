"""Cloudflare client: verify the API token and auto-resolve the Zone ID.

Used only for validation + discovery — the actual DNS/WAF resources are created by
Terraform, which receives the token via ``TF_VAR_*`` from the wizard's environment.
"""

from __future__ import annotations

import httpx

_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareClient:
    def __init__(self, token: str, *, client: httpx.Client | None = None) -> None:
        self._token = token
        self._client = client or httpx.Client(timeout=15.0)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def verify(self) -> bool:
        """True if the token is valid and active."""
        resp = self._client.get(f"{_BASE}/user/tokens/verify", headers=self._headers())
        if resp.status_code != httpx.codes.OK:
            return False
        body = resp.json()
        return bool(body.get("success")) and body.get("result", {}).get("status") == "active"

    def zone_id(self, domain: str) -> str:
        """Resolve the Zone ID for ``domain`` (kills the manual dashboard lookup)."""
        resp = self._client.get(
            f"{_BASE}/zones", params={"name": domain}, headers=self._headers()
        )
        resp.raise_for_status()
        result = resp.json().get("result", [])
        if not result:
            raise LookupError(f"no Cloudflare zone found for '{domain}'")
        return str(result[0]["id"])
