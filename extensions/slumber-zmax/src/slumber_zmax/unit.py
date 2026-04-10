from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Annotated

import ezmsg.core as ez
from loguru import logger
from pydantic import BeforeValidator, ConfigDict, Field, IPvAnyAddress

from slumber.plugins.units import Settings
from slumber.utils.retry import retry_async
from slumber.utils.pydantic import coerce_enum_by_name
from somnio.data.timeseries import Sample
from somnio.devices.zmax import (
    ConnectionClosedError,
    DataType,
    LEDColor,
    DEFAULT_IP,
    DEFAULT_PORT,
    LED_MAX_INTENSITY,
    LED_MIN_INTENSITY,
    SAMPLE_RATE,
    STIMULATION_MAX_DURATION_S,
    STIMULATION_MAX_REPETITIONS,
    STIMULATION_MIN_DURATION_S,
    STIMULATION_MIN_REPETITIONS,
    ZMax as ZMaxClient,
)


NOMINAL_SAMPLE_PERIOD_NS = int(1e9 / SAMPLE_RATE)

_ZMAX_STREAM_RETRY_ON: tuple[type[BaseException], ...] = (
    TimeoutError,
    ConnectionClosedError,
    ValueError,
)

_ZMAX_CONNECT_RETRY_ON: tuple[type[BaseException], ...] = (ConnectionError,)


class ZMaxStimulationSignal(Settings):
    """Validated stimulation signal for ZMax.

    Durations follow :meth:`somnio.devices.zmax.ZMax.stimulate_sequential` (seconds,
    quantized to ``STIMULATION_TIME_UNIT_S`` on the wire).
    """

    vibration: bool = True
    led_color: Annotated[LEDColor, BeforeValidator(coerce_enum_by_name(LEDColor))] = (
        LEDColor.OFF
    )
    on_duration_s: float = Field(
        ge=STIMULATION_MIN_DURATION_S, le=STIMULATION_MAX_DURATION_S
    )
    off_duration_s: float = Field(
        ge=STIMULATION_MIN_DURATION_S, le=STIMULATION_MAX_DURATION_S
    )
    repetitions: int = Field(
        ge=STIMULATION_MIN_REPETITIONS, le=STIMULATION_MAX_REPETITIONS
    )
    led_intensity: int = Field(
        LED_MAX_INTENSITY,
        ge=LED_MIN_INTENSITY,
        le=LED_MAX_INTENSITY,
    )
    alternate_eyes: bool = False


class ZMaxUnitSettings(Settings):
    """Settings for the ZMax unit."""

    ip: IPvAnyAddress = Field(
        DEFAULT_IP, description="IP address of the ZMax USB server."
    )
    port: int = Field(
        DEFAULT_PORT, ge=0, le=65535, description="TCP port of the ZMax server."
    )
    timeout_s: float | None = Field(
        1.0,
        ge=0.0,
        description=(
            "Socket timeout in seconds. "
            "If 0 is given, the socket is put in non-blocking mode. "
            "If None is given, the socket is put in blocking mode."
        ),
    )

    data_types: list[
        Annotated[DataType, BeforeValidator(coerce_enum_by_name(DataType))]
    ] = Field(
        default_factory=lambda: list(DataType),
        min_length=1,
        description="Data types to collect. Available: "
        + ", ".join(DataType.__members__.keys()),
    )

    data_collection_enabled: bool = Field(
        True, description="Whether to collect data from the ZMax server."
    )
    data_collection_enabled_check_interval: float = Field(
        1.0,
        gt=0.0,
        description="Polling interval while collection is disabled.",
    )

    retry_attempts: int | None = Field(
        None,
        ge=0,
        description="Connect/read attempts before raising an error (None = infinite).",
    )
    retry_delay_s: float = Field(
        0.25, ge=0.0, description="Delay between connect/read attempts."
    )

    timestamp_pll_alpha: float = Field(
        0.01,
        ge=0.0,
        le=1.0,
        description="Low-pass update rate for synthetic dt (0 disables).",
    )
    timestamp_pll_min_period_factor: float = Field(
        0.5,
        gt=0.0,
        description="Clamp lower bound for PLL period updates as a factor of nominal.",
    )
    timestamp_pll_max_period_factor: float = Field(
        2.0,
        gt=0.0,
        description="Clamp upper bound for PLL period updates as a factor of nominal.",
    )
    timestamp_resync_threshold_s: float = Field(
        1.0,
        ge=0.0,
        description="Resync synthetic clock if it lags monotonic by this many seconds.",
    )
    epoch_anchor_refresh_interval_s: float | None = Field(
        60.0,
        gt=0.0,
        description="How often to refresh the epoch<->monotonic anchor (None disables).",
    )
    epoch_anchor_slew_alpha: float = Field(
        0.01,
        ge=0.0,
        le=1.0,
        description="How aggressively to slew the anchor toward wall clock at refresh.",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def channel_names(self) -> tuple[str, ...]:
        """Channel names for emitted samples (aligned to ``data_types``)."""
        return tuple(dt.name for dt in self.data_types)

    @property
    def units(self) -> tuple[str, ...]:
        """SI units per channel for emitted samples (aligned to ``data_types``)."""
        return tuple(dt.value.unit for dt in self.data_types)


class ZMaxUnitState(ez.State):
    zmax: ZMaxClient | None = None
    data_collection_enabled: bool

    last_monotonic_ns: int | None = None
    next_monotonic_ns: int | None = None
    estimated_sample_period_ns: float = float(NOMINAL_SAMPLE_PERIOD_NS)

    epoch_anchor_ns: int | None = None
    monotonic_anchor_ns: int | None = None
    last_anchor_refresh_monotonic_ns: int | None = None


class ZMaxUnit(ez.Unit):
    """ZMax unit plugin."""

    SETTINGS = ZMaxUnitSettings
    STATE = ZMaxUnitState

    INPUT_DATA_COLLECTION_ENABLED = ez.InputStream(bool)
    INPUT_STIMULATION_SIGNAL = ez.InputStream(ZMaxStimulationSignal)
    OUTPUT_SAMPLE = ez.OutputStream(Sample)

    async def initialize(self) -> None:
        self.STATE.zmax = ZMaxClient(
            ip=str(self.SETTINGS.ip),
            port=self.SETTINGS.port,
            socket_timeout=self.SETTINGS.timeout_s,
        )
        self.STATE.data_collection_enabled = self.SETTINGS.data_collection_enabled
        await self._connect_with_retry()

    async def shutdown(self) -> None:
        self.STATE.data_collection_enabled = False
        if self.STATE.zmax is not None:
            try:
                self.STATE.zmax.disconnect()
            except Exception as exc:
                logger.warning("Error disconnecting ZMax: {}", exc)

    @ez.subscriber(INPUT_DATA_COLLECTION_ENABLED)
    async def set_data_collection_enabled(self, enabled: bool) -> None:
        if enabled != self.STATE.data_collection_enabled:
            logger.info("Data collection is {}.", "enabled" if enabled else "disabled")
        self.STATE.data_collection_enabled = enabled

    @ez.publisher(OUTPUT_SAMPLE)
    async def publish_sample(self) -> AsyncGenerator:
        while True:
            if not self.STATE.data_collection_enabled:
                await asyncio.sleep(
                    self.SETTINGS.data_collection_enabled_check_interval
                )
                continue

            if not self.STATE.zmax.is_connected():
                await self._connect_with_retry()

            attempts_remaining = self.SETTINGS.retry_attempts

            def _on_read_failure(exc: BaseException) -> None:
                logger.warning(
                    "ZMax read error (will retry in {}s): {}",
                    self.SETTINGS.retry_delay_s,
                    exc,
                )

            values = await retry_async(
                lambda: self.STATE.zmax.read_numpy(self.SETTINGS.data_types),
                retry_delay_s=self.SETTINGS.retry_delay_s,
                attempts=attempts_remaining,
                retry_on=_ZMAX_STREAM_RETRY_ON,
                on_failure=_on_read_failure,
            )
            yield (
                self.OUTPUT_SAMPLE,
                Sample(
                    values=values,
                    timestamp=self._get_current_timestamp_ns(),
                    channel_names=self.SETTINGS.channel_names,
                    units=self.SETTINGS.units,
                ),
            )

    async def _connect_with_retry(self) -> None:
        def _on_connect_failure(exc: BaseException) -> None:
            logger.warning(
                "Failed to connect to ZMax at {}:{} (will retry in {}s): {}",
                self.SETTINGS.ip,
                self.SETTINGS.port,
                self.SETTINGS.retry_delay_s,
                exc,
            )

        await retry_async(
            self.STATE.zmax.connect,
            retry_delay_s=self.SETTINGS.retry_delay_s,
            attempts=self.SETTINGS.retry_attempts,
            retry_on=_ZMAX_CONNECT_RETRY_ON,
            on_failure=_on_connect_failure,
        )

    @ez.subscriber(INPUT_STIMULATION_SIGNAL)
    async def stimulate(self, signal: ZMaxStimulationSignal) -> None:
        if not self.STATE.zmax.is_connected():
            logger.warning("ZMax not connected; stimulation ignored.")
            return

        try:
            self.STATE.zmax.stimulate_sequential(**signal.model_dump())
        except Exception as exc:
            logger.warning("ZMax stimulation failed: {}", exc)

    def _get_current_timestamp_ns(self) -> int:
        """Generate a stable epoch timestamp for the next sample.

        This ports the legacy "synthetic monotonic clock" approach:
        - Use monotonic time to advance a synthetic sample clock (reduces jitter).
        - Anchor monotonic to epoch time and periodically slew anchor toward wall clock.
        """
        now_mono = time.monotonic_ns()

        if self.STATE.epoch_anchor_ns is None:
            self.STATE.last_monotonic_ns = now_mono
            self.STATE.next_monotonic_ns = now_mono

            self.STATE.epoch_anchor_ns = time.time_ns()
            self.STATE.monotonic_anchor_ns = now_mono
            self.STATE.last_anchor_refresh_monotonic_ns = now_mono
            return self.STATE.epoch_anchor_ns

        observed_dt = now_mono - (self.STATE.last_monotonic_ns or now_mono)
        low = self.SETTINGS.timestamp_pll_min_period_factor * NOMINAL_SAMPLE_PERIOD_NS
        high = self.SETTINGS.timestamp_pll_max_period_factor * NOMINAL_SAMPLE_PERIOD_NS
        if low <= observed_dt <= high and self.SETTINGS.timestamp_pll_alpha > 0.0:
            a = self.SETTINGS.timestamp_pll_alpha
            self.STATE.estimated_sample_period_ns = (
                1.0 - a
            ) * self.STATE.estimated_sample_period_ns + a * observed_dt

        self.STATE.last_monotonic_ns = now_mono
        self.STATE.next_monotonic_ns = int(
            (self.STATE.next_monotonic_ns or now_mono)
            + self.STATE.estimated_sample_period_ns
        )

        resync_threshold_ns = int(self.SETTINGS.timestamp_resync_threshold_s * 1e9)
        if (
            resync_threshold_ns > 0
            and now_mono - self.STATE.next_monotonic_ns > resync_threshold_ns
        ):
            self.STATE.next_monotonic_ns = now_mono

        if self.SETTINGS.epoch_anchor_refresh_interval_s is not None and now_mono - (
            self.STATE.last_anchor_refresh_monotonic_ns or now_mono
        ) >= int(self.SETTINGS.epoch_anchor_refresh_interval_s * 1e9):
            predicted_epoch_now = int(self.STATE.epoch_anchor_ns) + (
                now_mono - int(self.STATE.monotonic_anchor_ns)
            )
            wall_now = time.time_ns()
            error = wall_now - predicted_epoch_now
            a = self.SETTINGS.epoch_anchor_slew_alpha
            if a > 0.0:
                self.STATE.epoch_anchor_ns = int(
                    int(self.STATE.epoch_anchor_ns) + a * error
                )
            self.STATE.last_anchor_refresh_monotonic_ns = now_mono

        return int(self.STATE.epoch_anchor_ns) + (
            int(self.STATE.next_monotonic_ns) - int(self.STATE.monotonic_anchor_ns)
        )
