"""Eye-movement detection pipeline unit."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import ezmsg.core as ez
from loguru import logger
from pydantic import Field
from slumber.pipeline.units import Settings
from somnio.data.annotations import Event
from somnio.data.timeseries import TimeSeries
from somnio.tasks.eye_movement import detect_lr_eye_movements
from somnio.tasks.eye_movement.defaults import (
    HIGH_CUTOFF_HZ,
    LOW_CUTOFF_HZ,
    MAX_AMPLITUDE_RATIO,
    MAX_EVENT_DURATION_S,
    MAX_EVENT_GAP_S,
    MAX_EVENT_SKEWNESS,
    MAX_PEAK_AMPLITUDE_UV,
    MIN_AMPLITUDE_RATIO,
    MIN_CORRELATION,
    MIN_EVENT_DURATION_S,
    MIN_EVENT_SKEWNESS,
    MIN_PEAK_AMPLITUDE_UV,
    MIN_PEAK_GAP_S,
    RELATIVE_BASELINE,
    RELATIVE_PEAK_PROMINENCE,
)


class EyeMovementDetectionSettings(Settings):
    left_channel: str = Field(
        ...,
        description="Channel name for the left EOG electrode.",
    )
    right_channel: str = Field(
        ...,
        description="Channel name for the right EOG electrode.",
    )
    preprocess: bool = Field(
        default=True,
        description=(
            "Apply a bandpass FIR filter before detection. "
            "Set to False if the signal is already filtered."
        ),
    )
    low_cutoff_hz: float = Field(
        default=LOW_CUTOFF_HZ,
        gt=0.0,
        description="FIR low passband edge in Hz (preprocess=True only).",
    )
    high_cutoff_hz: float = Field(
        default=HIGH_CUTOFF_HZ,
        gt=0.0,
        description="FIR high passband edge in Hz (preprocess=True only).",
    )
    min_peak_amplitude_uv: float = Field(
        default=MIN_PEAK_AMPLITUDE_UV,
        gt=0.0,
        description="Minimum amplitude at a peak in µV.",
    )
    max_peak_amplitude_uv: float = Field(
        default=MAX_PEAK_AMPLITUDE_UV,
        gt=0.0,
        description="Maximum amplitude at a peak in µV.",
    )
    min_peak_gap_s: float = Field(
        default=MIN_PEAK_GAP_S,
        ge=0.0,
        description="Minimum time between consecutive peaks in seconds.",
    )
    relative_peak_prominence: float = Field(
        default=RELATIVE_PEAK_PROMINENCE,
        gt=0.0,
        description="Peak prominence threshold relative to min_peak_amplitude_uv².",
    )
    min_event_duration_s: float = Field(
        default=MIN_EVENT_DURATION_S,
        ge=0.0,
        description="Minimum primitive event duration in seconds.",
    )
    max_event_duration_s: float = Field(
        default=MAX_EVENT_DURATION_S,
        gt=0.0,
        description="Maximum primitive event duration in seconds.",
    )
    min_event_skewness: float = Field(
        default=MIN_EVENT_SKEWNESS,
        description="Lower bound on normalised peak offset within the event window.",
    )
    max_event_skewness: float = Field(
        default=MAX_EVENT_SKEWNESS,
        description="Upper bound on normalised peak offset.",
    )
    relative_baseline: float = Field(
        default=RELATIVE_BASELINE,
        gt=0.0,
        description="Boundary-walk threshold as a fraction of min_peak_amplitude_uv².",
    )
    merge: bool = Field(
        default=True,
        description="Merge temporally close primitive events into sequences.",
    )
    max_event_gap_s: float = Field(
        default=MAX_EVENT_GAP_S,
        ge=0.0,
        description=(
            "Maximum gap between primitive events in seconds to merge into one sequence."
        ),
    )
    accepted_pattern: str | None = Field(
        default=None,
        description=(
            "Regex that must fully match the sequence label. "
            "None disables pattern filtering."
        ),
    )
    min_correlation: float = Field(
        default=MIN_CORRELATION,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum magnitude of the negative Pearson correlation between "
            "left and right channels. Sequences where corr > -min_correlation "
            "are rejected."
        ),
    )
    min_amplitude_ratio: float = Field(
        default=MIN_AMPLITUDE_RATIO,
        gt=0.0,
        description="Lower bound on std(left) / std(right).",
    )
    max_amplitude_ratio: float = Field(
        default=MAX_AMPLITUDE_RATIO,
        gt=0.0,
        description="Upper bound on std(left) / std(right).",
    )


class EyeMovementDetectionUnit(ez.Unit):
    """Eye-movement detection unit plugin.

    Receives a pre-windowed :class:`~somnio.data.timeseries.TimeSeries` from
    an upstream buffering unit, runs left/right eye-movement detection via
    :func:`somnio.tasks.eye_movement.detect_lr_eye_movements`, and emits the
    resulting events on two output streams.

    Streams:
        INPUT_TIMESERIES: Buffered TimeSeries containing EOG channels.
        OUTPUT_SEQUENCES: Validated sequence events (``list[Event]``).
        OUTPUT_PRIMITIVES: All primitive events before sequence merging
            (``list[Event]``).
    """

    SETTINGS = EyeMovementDetectionSettings

    INPUT_TIMESERIES = ez.InputStream(TimeSeries)
    OUTPUT_SEQUENCES = ez.OutputStream(list[Event])
    OUTPUT_PRIMITIVES = ez.OutputStream(list[Event])

    @ez.subscriber(INPUT_TIMESERIES)
    @ez.publisher(OUTPUT_SEQUENCES)
    @ez.publisher(OUTPUT_PRIMITIVES)
    async def on_timeseries(self, ts: TimeSeries) -> AsyncGenerator:
        """Detect eye movements from a TimeSeries.

        Args:
            ts: Buffered EOG TimeSeries from an upstream unit.

        Yields:
            ``(OUTPUT_SEQUENCES, list[Event])`` when sequences are detected.
            ``(OUTPUT_PRIMITIVES, list[Event])`` when primitive events are detected.
        """

        sequences, primitives = detect_lr_eye_movements(
            ts,
            self.SETTINGS.left_channel,
            self.SETTINGS.right_channel,
            preprocess=self.SETTINGS.preprocess,
            low_cutoff_hz=self.SETTINGS.low_cutoff_hz,
            high_cutoff_hz=self.SETTINGS.high_cutoff_hz,
            min_peak_amplitude_uv=self.SETTINGS.min_peak_amplitude_uv,
            max_peak_amplitude_uv=self.SETTINGS.max_peak_amplitude_uv,
            min_peak_gap_s=self.SETTINGS.min_peak_gap_s,
            relative_peak_prominence=self.SETTINGS.relative_peak_prominence,
            min_event_duration_s=self.SETTINGS.min_event_duration_s,
            max_event_duration_s=self.SETTINGS.max_event_duration_s,
            min_event_skewness=self.SETTINGS.min_event_skewness,
            max_event_skewness=self.SETTINGS.max_event_skewness,
            relative_baseline=self.SETTINGS.relative_baseline,
            merge=self.SETTINGS.merge,
            max_event_gap_s=self.SETTINGS.max_event_gap_s,
            accepted_pattern=self.SETTINGS.accepted_pattern,
            min_correlation=self.SETTINGS.min_correlation,
            min_amplitude_ratio=self.SETTINGS.min_amplitude_ratio,
            max_amplitude_ratio=self.SETTINGS.max_amplitude_ratio,
        )

        if sequences:
            logger.debug("Emitting {} eye-movement sequence(s).", len(sequences))
            yield self.OUTPUT_SEQUENCES, sequences

        if primitives:
            logger.debug(
                "Emitting {} primitive eye-movement event(s).", len(primitives)
            )
            yield self.OUTPUT_PRIMITIVES, primitives
