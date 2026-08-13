import ezmsg.core as ez
import pytest

pytest.importorskip("slumber_somnio")

from somnio.devices.zmax import DataType as ZMaxDataType
from somnio.devices.zmax.enums import LEDColor

from slumber_somnio.units.zmax import ZMaxStimulationSignal, ZMaxUnit, ZMaxUnitSettings


def test_settings_coerces_data_types_from_strings() -> None:
    settings = ZMaxUnitSettings.model_validate(
        {
            "ip": "127.0.0.1",
            "port": 8000,
            "timeout_s": 1.0,
            "data_types": ["EEG_RIGHT", "EEG_LEFT"],
        }
    )
    assert settings.data_types == [ZMaxDataType.EEG_RIGHT, ZMaxDataType.EEG_LEFT]
    assert settings.channel_names == ("EEG_RIGHT", "EEG_LEFT")
    assert len(settings.units) == 2


def test_settings_rejects_unknown_data_type() -> None:
    with pytest.raises(ValueError, match="Unknown DataType"):
        ZMaxUnitSettings.model_validate({"data_types": ["NOT_A_REAL_CHANNEL"]})


def test_unit_is_ezmsg_unit_subclass() -> None:
    assert issubclass(ZMaxUnit, ez.Unit)


def test_stimulation_signal_coerces_led_color_from_string() -> None:
    signal = ZMaxStimulationSignal.model_validate(
        {
            "vibration": True,
            "led_color": "GREEN",
            "on_duration_s": 1.0,
            "off_duration_s": 1.0,
            "repetitions": 2,
            "led_intensity": 50,
            "alternate_eyes": False,
        }
    )
    assert signal.led_color == LEDColor.GREEN
