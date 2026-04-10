"""Tests for :mod:`slumber.utils.retry`."""

from __future__ import annotations

import asyncio

import pytest

from slumber.utils.retry import retry_async, retry_sync


def test_retry_sync_returns_fn_value() -> None:
    attempts = {"n": 0}

    def op() -> str:
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise OSError("fail once")
        return "ok"

    assert (
        retry_sync(
            op,
            retry_delay_s=0,
            attempts=None,
            on_failure=lambda _exc: None,
        )
        == "ok"
    )


def test_retry_sync_returns_after_eventual_success() -> None:
    attempts = {"n": 0}

    def op() -> None:
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise OSError("fail once")

    retry_sync(
        op,
        retry_delay_s=0,
        attempts=None,
        on_failure=lambda _exc: None,
    )
    assert attempts["n"] == 2


def test_retry_sync_reraises_when_attempts_exhausted() -> None:
    def op() -> None:
        raise OSError("always")

    with pytest.raises(OSError, match="always"):
        retry_sync(
            op,
            retry_delay_s=0,
            attempts=0,
            on_failure=lambda _exc: None,
        )


def test_retry_on_non_matching_exception_propagates_without_retry() -> None:
    called: list[bool] = []

    def on_failure(_exc: BaseException) -> None:
        called.append(True)

    def op() -> None:
        raise ValueError("no retry")

    with pytest.raises(ValueError, match="no retry"):
        retry_sync(
            op,
            retry_delay_s=0,
            attempts=5,
            on_failure=on_failure,
            retry_on=(OSError,),
        )
    assert called == []


def test_on_attempts_exhausted_runs_instead_of_plain_reraise() -> None:
    def op() -> None:
        raise OSError("always")

    def exhausted(exc: BaseException) -> None:
        raise RuntimeError("wrapped") from exc

    with pytest.raises(RuntimeError, match="wrapped"):
        retry_sync(
            op,
            retry_delay_s=0,
            attempts=0,
            on_failure=lambda _exc: None,
            on_attempts_exhausted=exhausted,
        )


def test_retry_async_returns_fn_value() -> None:
    attempts = {"n": 0}

    def op() -> str:
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise OSError("fail once")
        return "ok"

    async def run() -> str:
        return await retry_async(
            op,
            retry_delay_s=0,
            attempts=None,
            on_failure=lambda _exc: None,
        )

    assert asyncio.run(run()) == "ok"


def test_retry_async_returns_after_eventual_success() -> None:
    attempts = {"n": 0}

    def op() -> None:
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise OSError("fail once")

    async def run() -> None:
        await retry_async(
            op,
            retry_delay_s=0,
            attempts=None,
            on_failure=lambda _exc: None,
        )

    asyncio.run(run())
    assert attempts["n"] == 2


def test_retry_async_reraises_when_attempts_exhausted() -> None:
    def op() -> None:
        raise OSError("always")

    async def run() -> None:
        await retry_async(
            op,
            retry_delay_s=0,
            attempts=0,
            on_failure=lambda _exc: None,
        )

    with pytest.raises(OSError, match="always"):
        asyncio.run(run())
