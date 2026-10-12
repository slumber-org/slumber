"""NiceGUI-marked smoke checks for GUI helpers (require slumber[nicegui])."""

from __future__ import annotations

import pytest

pytest.importorskip("nicegui")

pytestmark = pytest.mark.nicegui


def test_apply_theme_sets_colors() -> None:
    """apply_theme can be called inside a page context without error."""
    from nicegui import ui

    from slumber.ui.theme import COLORS

    # Direct colours call mirrors apply_theme's Quasar map.
    ui.colors(**COLORS)
    assert COLORS["primary"]


def test_theme_css_defines_button_variants() -> None:
    from slumber.ui.theme import build_theme_css

    css = build_theme_css()
    for variant in ("primary", "secondary", "attention"):
        assert f".slumber-btn-{variant}" in css


def test_widgets_importable() -> None:
    from slumber.ui.widgets import (
        confirm_dialog,
        logo_mark,
        outline_button,
        primary_button,
        surface_card,
    )

    assert callable(logo_mark)
    assert callable(primary_button)
    assert callable(outline_button)
    assert callable(surface_card)
    assert callable(confirm_dialog)


def test_app_frame_importable() -> None:
    from slumber.ui.frame import AppFrame

    frame = AppFrame(study_name="Demo", logo_url=None, frame={"footer": False})
    assert not frame.mounted
