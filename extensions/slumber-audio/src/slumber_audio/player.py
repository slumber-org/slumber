"""Core audio playback logic using sounddevice and soundfile."""

from __future__ import annotations

from pathlib import Path

import sounddevice as sd
import soundfile as sf


class AudioPlayer:
    """Synchronous audio player wrapping sounddevice and soundfile.

    Args:
        device: sounddevice output device index or name. ``None`` uses the
            system default.
    """

    def __init__(self, device: int | str | None = None) -> None:
        self._device = device

    def play(self, file_path: Path, volume: float = 1.0) -> None:
        """Load and play an audio file, blocking until playback completes.

        Args:
            file_path: Path to the audio file (WAV, FLAC, OGG, etc.).
            volume: Amplitude scale factor. ``1.0`` is original level; ``0.0``
                is silence. Values above ``1.0`` may clip.
        """
        data, sample_rate = sf.read(str(file_path))
        sd.play(data * volume, sample_rate, device=self._device)
        sd.wait()

    def stop(self) -> None:
        """Stop any in-progress playback immediately."""
        sd.stop()
