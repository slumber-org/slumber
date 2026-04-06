"""Tests for the task renderer dispatch."""

from __future__ import annotations

from slumber.plugins.ui.nicegui.renderers import (
    _RENDERERS,
    get_renderer,
    register_renderer,
    render_placeholder,
)
from slumber.schemas.procedure import Step


def _dummy_renderer(step: Step, container: object) -> None:
    pass


class TestRendererDispatch:
    def test_placeholder_is_default(self) -> None:
        assert get_renderer("unknown_task_type") is render_placeholder

    def test_register_and_get(self) -> None:
        register_renderer("test_task", _dummy_renderer)
        assert get_renderer("test_task") is _dummy_renderer
        _RENDERERS.pop("test_task", None)

    def test_register_overrides(self) -> None:
        register_renderer("override_test", _dummy_renderer)

        def other(step: Step, container: object) -> None:
            pass

        register_renderer("override_test", other)
        assert get_renderer("override_test") is other
        _RENDERERS.pop("override_test", None)
