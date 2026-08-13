import pytest

pytest.importorskip("slumber_audio")

import ezmsg.core as ez

from slumber_audio.units import AudioPlayerSettings, AudioPlayerUnit, AudioPlayRequest


def test_unit_is_ezmsg_unit_subclass() -> None:
    assert issubclass(AudioPlayerUnit, ez.Unit)


def test_settings_default_volume() -> None:
    settings = AudioPlayerSettings.model_validate({})
    assert settings.volume == 1.0


def test_settings_default_file_path_is_none() -> None:
    settings = AudioPlayerSettings.model_validate({})
    assert settings.file_path is None


def test_settings_rejects_volume_below_zero() -> None:
    with pytest.raises(ValueError):
        AudioPlayerSettings.model_validate({"volume": -0.1})


def test_settings_rejects_volume_above_one() -> None:
    with pytest.raises(ValueError):
        AudioPlayerSettings.model_validate({"volume": 1.1})


def test_play_request_none_fields_by_default() -> None:
    request = AudioPlayRequest()
    assert request.file_path is None
    assert request.volume is None


def test_play_request_validates_volume_bounds() -> None:
    with pytest.raises(ValueError):
        AudioPlayRequest(volume=1.5)
