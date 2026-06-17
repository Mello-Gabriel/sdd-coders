"""Pure input validators for the wizard.

Each returns the normalized value or raises ``ValueError`` with a user-facing
message. They never touch I/O, so they are trivially testable and reusable by both
the GUI (live field validation) and the headless pipeline.
"""

from __future__ import annotations

import ipaddress
import re

_SLUG = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
_DOMAIN = re.compile(r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?<!-)(\.[a-z0-9-]{1,63})+$")
_GA_ID = re.compile(r"^G-[A-Z0-9]{6,}$")


def validate_slug(value: str) -> str:
    """A safe kebab-case identifier (also blocks path traversal like ``../etc``)."""
    if not _SLUG.match(value):
        raise ValueError(
            "use lowercase letters, digits and hyphens; start with a letter (2-63 chars)"
        )
    return value


def validate_domain(value: str) -> str:
    """An apex domain like ``example.com`` (no scheme, no path)."""
    normalized = value.strip().lower().rstrip(".")
    if not _DOMAIN.match(normalized):
        raise ValueError("enter a bare domain like 'example.com' (no http://, no path)")
    return normalized


def validate_url(value: str) -> str:
    """An ``https://`` (or ``http://``) URL with a host."""
    normalized = value.strip().rstrip("/")
    if not re.match(r"^https?://[^\s/]+", normalized):
        raise ValueError("enter a full URL like 'https://coolify.example.com'")
    return normalized


def validate_ip(value: str) -> str:
    """A literal IPv4/IPv6 address."""
    candidate = value.strip()
    try:
        ipaddress.ip_address(candidate)
    except ValueError as exc:
        raise ValueError("enter a valid IP address") from exc
    return candidate


def validate_ga_id(value: str) -> str:
    """A GA4 measurement id like ``G-XXXXXXXXXX``."""
    normalized = value.strip().upper()
    if not _GA_ID.match(normalized):
        raise ValueError("enter a GA4 measurement id like 'G-XXXXXXXXXX'")
    return normalized


def validate_nonempty(value: str) -> str:
    """A required free-form value (e.g. an API token) — only rejects blanks."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("this value is required")
    return stripped
