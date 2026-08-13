"""Tests for UI backend settings validation in validate_study_plugins."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from slumber.config.plugins import validate_study_plugins
from slumber.plugins import EntryPointGroup
from slumber.plugins.ui.base import UIBackend
from slumber.plugins.ui.headless import HeadlessUIBackend
from slumber.plugins.ui.nicegui.config import NiceGUISettings
from slumber.runtime.run import RunContext
from slumber.schemas.condition import Condition
from slumber.schemas.study import UI, Study


class DummyNiceGUIBackend(UIBackend):
    """Backend stub exposing the NiceGUI settings model."""

    ui_settings_model = NiceGUISettings

    def run(
        self,
        study: Study,
        condition: Condition,
        context: RunContext,
    ) -> None:
        """Not used in these tests."""
        raise NotImplementedError


def _registry_with_ui_backend(backend_key: str, backend_class: type) -> MagicMock:
    reg = MagicMock()

    def get_plugin(group: EntryPointGroup, key: str):
        if group != EntryPointGroup.UI_BACKENDS:
            raise LookupError(f"Unexpected group: {group!r}")
        if key != backend_key:
            raise LookupError(f"Unexpected backend key: {key!r}")
        return backend_class

    reg.get_plugin.side_effect = get_plugin
    return reg


def test_headless_rejects_non_empty_ui_settings() -> None:
    study = Study(study_id="x", name="Y", ui=UI(backend="headless", settings={"a": 1}))
    study._conditions = []
    reg = _registry_with_ui_backend("headless", HeadlessUIBackend)

    with pytest.raises(ValueError, match=r"does not support ui\.settings"):
        validate_study_plugins(study, registry=reg)


def test_settings_model_validation_error_is_reported() -> None:
    study = Study(
        study_id="x",
        name="Y",
        ui=UI(backend="nicegui", settings={"port": "not-an-int"}),
    )
    study._conditions = []
    reg = _registry_with_ui_backend("nicegui", DummyNiceGUIBackend)

    with pytest.raises(ValueError, match=r"UI backend 'nicegui' settings invalid"):
        validate_study_plugins(study, registry=reg)


def test_settings_model_accepts_empty_settings() -> None:
    study = Study(study_id="x", name="Y", ui=UI(backend="nicegui", settings={}))
    study._conditions = []
    reg = _registry_with_ui_backend("nicegui", DummyNiceGUIBackend)

    validate_study_plugins(study, registry=reg)
