"""Tests for EyeMovementDetectionUnit and EyeMovementDetectionSettings."""

from __future__ import annotations

import ezmsg.core as ez
import pytest
from pydantic import ValidationError

pytest.importorskip("slumber_somnio")


from slumber_somnio.units.eye_movement import (
    EyeMovementDetectionSettings,
    EyeMovementDetectionUnit,
)

# ---------------------------------------------------------------------------
# Settings validation
# ---------------------------------------------------------------------------


def test_settings_requires_left_and_right_channel() -> None:
    with pytest.raises(ValidationError):
        EyeMovementDetectionSettings.model_validate({})


def test_settings_defaults_match_somnio_defaults() -> None:
    from somnio.tasks.eye_movement.defaults import (
        HIGH_CUTOFF_HZ,
        LOW_CUTOFF_HZ,
        MAX_AMPLITUDE_RATIO,
        MAX_EVENT_GAP_S,
        MIN_AMPLITUDE_RATIO,
        MIN_CORRELATION,
        MIN_PEAK_AMPLITUDE_UV,
    )

    settings = EyeMovementDetectionSettings.model_validate(
        {"left_channel": "EOG_L", "right_channel": "EOG_R"}
    )
    assert settings.left_channel == "EOG_L"
    assert settings.right_channel == "EOG_R"
    assert settings.preprocess is True
    assert settings.low_cutoff_hz == LOW_CUTOFF_HZ
    assert settings.high_cutoff_hz == HIGH_CUTOFF_HZ
    assert settings.min_peak_amplitude_uv == MIN_PEAK_AMPLITUDE_UV
    assert settings.min_correlation == MIN_CORRELATION
    assert settings.min_amplitude_ratio == MIN_AMPLITUDE_RATIO
    assert settings.max_amplitude_ratio == MAX_AMPLITUDE_RATIO
    assert settings.max_event_gap_s == MAX_EVENT_GAP_S
    assert settings.merge is True
    assert settings.accepted_pattern is None


def test_settings_rejects_negative_amplitude() -> None:
    with pytest.raises(ValidationError):
        EyeMovementDetectionSettings.model_validate(
            {
                "left_channel": "EOG_L",
                "right_channel": "EOG_R",
                "min_peak_amplitude_uv": -1.0,
            }
        )


# ---------------------------------------------------------------------------
# Unit class structure
# ---------------------------------------------------------------------------


def test_unit_is_ezmsg_unit_subclass() -> None:
    assert issubclass(EyeMovementDetectionUnit, ez.Unit)


def test_unit_has_expected_streams() -> None:
    assert hasattr(EyeMovementDetectionUnit, "INPUT_TIMESERIES")
    assert hasattr(EyeMovementDetectionUnit, "OUTPUT_SEQUENCES")
    assert hasattr(EyeMovementDetectionUnit, "OUTPUT_PRIMITIVES")
