"""ezmsg unit for audio playback."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import suppress
from dataclasses import field
from pathlib import Path

import ezmsg.core as ez
from loguru import logger
from pydantic import BaseModel, Field
from slumber.plugins.units import Settings

from slumber_audio.player import AudioPlayer


class AudioPlayRequest(BaseModel):
    """Message that triggers audio playback.

    Both fields are optional overrides — ``None`` falls back to the unit's
    settings defaults, so callers only need to specify what they want to
    change.

    Args:
        file_path: Audio file to play. Overrides ``AudioPlayerSettings.file_path``.
        volume: Amplitude scale factor (0.0–1.0). Overrides
            ``AudioPlayerSettings.volume``.
    """

    file_path: Path | None = None
    volume: float | None = Field(default=None, ge=0.0, le=1.0)


class AudioPlayerSettings(Settings):
    """Settings for the audio player unit.

    Args:
        file_path: Default audio file path. May be overridden per-request.
        volume: Default amplitude scale factor (0.0–1.0).
        device: sounddevice output device index or name. ``None`` uses the
            system default.
    """

    file_path: Path | None = None
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    device: int | str | None = None


class AudioPlayerState(ez.State):
    player: AudioPlayer = field(default_factory=AudioPlayer)
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)


class AudioPlayerUnit(ez.Unit):
    """Audio playback unit plugin.

    Plays audio files on demand. Delegates all playback to
    :class:`slumber_audio.player.AudioPlayer` so the core logic is usable
    independently of ezmsg.

    Streams:
        INPUT_PLAY: Receive an :class:`AudioPlayRequest` to start playback.
        INPUT_STOP: Send ``True`` to cancel in-progress playback immediately.
        OUTPUT_DONE: Emits ``True`` after each playback completes or is stopped.
    """

    SETTINGS = AudioPlayerSettings
    STATE = AudioPlayerState

    INPUT_PLAY = ez.InputStream(AudioPlayRequest)
    INPUT_STOP = ez.InputStream(bool)
    OUTPUT_DONE = ez.OutputStream(bool)

    async def initialize(self) -> None:
        self.STATE.player = AudioPlayer(device=self.SETTINGS.device)
        self.STATE.stop_event = asyncio.Event()

    @ez.subscriber(INPUT_STOP)
    async def on_stop(self, stop: bool) -> None:
        """Cancel in-progress playback when ``True`` is received."""
        if stop:
            self.STATE.stop_event.set()

    @ez.subscriber(INPUT_PLAY)
    @ez.publisher(OUTPUT_DONE)
    async def on_play_request(self, request: AudioPlayRequest) -> AsyncGenerator:
        """Play audio from a request, respecting settings defaults.

        Runs the blocking ``player.play()`` in a thread executor so the ezmsg
        event loop remains free. If ``INPUT_STOP`` fires during playback,
        ``player.stop()`` is called and the thread is allowed to return cleanly.

        Yields:
            ``True`` on ``OUTPUT_DONE`` after every play attempt (complete or stopped).
        """
        file_path = request.file_path or self.SETTINGS.file_path
        volume = request.volume if request.volume is not None else self.SETTINGS.volume

        if file_path is None:
            logger.warning("No file_path in request or settings")
            return

        self.STATE.stop_event.clear()

        loop = asyncio.get_running_loop()
        play_future = loop.run_in_executor(
            None, self.STATE.player.play, file_path, volume
        )
        stop_future: asyncio.Future = asyncio.ensure_future(
            self.STATE.stop_event.wait()
        )

        done, pending = await asyncio.wait(
            {play_future, stop_future},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if stop_future in done:
            self.STATE.player.stop()
            await play_future

        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        yield self.OUTPUT_DONE, True
