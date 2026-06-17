"""Curated UI theme presets selectable at project creation.

A theme only swaps the shadcn/Tailwind *primary* token set (kept against the same
neutral base), so picking one changes the whole app's accent without adding any
component — which keeps the generated frontend's 100% test gate untouched. The CSS
values live in ``frontend/app/globals.css.jinja`` (the source of truth); this catalog
holds the keys, labels and a representative swatch for the CLI/GUI and validation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    key: str
    label: str
    swatch: str  # representative primary colour (hex) for the GUI preview


THEMES: tuple[Theme, ...] = (
    Theme("blue", "Blue", "#2563eb"),
    Theme("neutral", "Neutral (preto)", "#18181b"),
    Theme("violet", "Violet", "#7c3aed"),
    Theme("emerald", "Emerald", "#059669"),
    Theme("rose", "Rose", "#e11d48"),
)

DEFAULT_THEME = "blue"
THEME_KEYS: tuple[str, ...] = tuple(theme.key for theme in THEMES)


def is_valid_theme(key: str) -> bool:
    return key in THEME_KEYS
