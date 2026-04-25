import pytest

pytest.importorskip("slumber_audio")

from slumber_audio.player import AudioPlayer


def test_player_instantiates_with_no_device() -> None:
    player = AudioPlayer()
    assert player._device is None


def test_player_instantiates_with_device() -> None:
    player = AudioPlayer(device=0)
    assert player._device == 0


def test_player_stop_is_callable_when_not_playing() -> None:
    player = AudioPlayer()
    player.stop()
