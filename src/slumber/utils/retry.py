"""Retry helpers for zero-argument callables (sync sleep vs asyncio.sleep)."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_sync(
    fn: Callable[[], T],
    *,
    retry_delay_s: float,
    attempts: int | None = None,
    on_failure: Callable[[BaseException], None],
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    on_attempts_exhausted: Callable[[BaseException], None] | None = None,
) -> T:
    """Call ``fn`` until it returns a value; block with :func:`time.sleep` between failures."""
    remaining = attempts
    while True:
        try:
            return fn()
        except BaseException as exc:
            if not isinstance(exc, retry_on):
                raise
            on_failure(exc)
            if remaining is not None:
                remaining -= 1
                if remaining < 0:
                    if on_attempts_exhausted is not None:
                        on_attempts_exhausted(exc)
                    raise exc
            time.sleep(retry_delay_s)


async def retry_async(
    fn: Callable[[], T],
    *,
    retry_delay_s: float,
    attempts: int | None = None,
    on_failure: Callable[[BaseException], None],
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    on_attempts_exhausted: Callable[[BaseException], None] | None = None,
) -> T:
    """Call ``fn`` until it returns a value; await :func:`asyncio.sleep` between failures."""
    remaining = attempts
    while True:
        try:
            return fn()
        except BaseException as exc:
            if not isinstance(exc, retry_on):
                raise
            on_failure(exc)
            if remaining is not None:
                remaining -= 1
                if remaining < 0:
                    if on_attempts_exhausted is not None:
                        on_attempts_exhausted(exc)
                    raise exc
            await asyncio.sleep(retry_delay_s)
