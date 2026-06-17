"""Resend client: validate the API key before it is pushed to Coolify."""

from __future__ import annotations

import httpx

_BASE = "https://api.resend.com"


class ResendClient:
    def __init__(self, api_key: str, *, client: httpx.Client | None = None) -> None:
        self._api_key = api_key
        self._client = client or httpx.Client(timeout=15.0)

    def verify(self) -> bool:
        """True if the API key authenticates against Resend."""
        resp = self._client.get(
            f"{_BASE}/domains", headers={"Authorization": f"Bearer {self._api_key}"}
        )
        return resp.status_code == httpx.codes.OK
