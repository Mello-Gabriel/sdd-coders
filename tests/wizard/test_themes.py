"""Tests for the UI theme catalog and its alignment with the template."""

from __future__ import annotations

import jinja2
import yaml  # type: ignore[import-untyped]

from sdd_coders.scaffold import TEMPLATE_DIR
from sdd_coders.wizard.themes import DEFAULT_THEME, THEME_KEYS, is_valid_theme


def test_is_valid_theme() -> None:
    assert is_valid_theme("blue")
    assert is_valid_theme(DEFAULT_THEME)
    assert not is_valid_theme("chartreuse")


def test_default_theme_is_a_known_key() -> None:
    assert DEFAULT_THEME in THEME_KEYS


def test_copier_choices_match_catalog() -> None:
    spec = yaml.safe_load((TEMPLATE_DIR / "copier.yml").read_text(encoding="utf-8"))
    choices = spec["ui_theme"]["choices"]
    assert set(choices.values()) == set(THEME_KEYS)
    assert spec["ui_theme"]["default"] == DEFAULT_THEME


def test_globals_css_renders_for_every_theme() -> None:
    src = (TEMPLATE_DIR / "frontend" / "app" / "globals.css.jinja").read_text(encoding="utf-8")
    template = jinja2.Template(src, keep_trailing_newline=True)
    for key in THEME_KEYS:
        rendered = template.render(ui_theme=key)
        assert "--primary:" in rendered
        # No unrendered Jinja syntax should survive into the CSS.
        assert "{{" not in rendered
        assert "{%" not in rendered
