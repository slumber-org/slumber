"""Optional Sentry integration: initialize when SENTRY_DSN is set, no-op otherwise."""

from __future__ import annotations

import os

from loguru import logger

from slumber.constants import SENTRY_DSN_ENV


def init_sentry(study_id: str) -> bool:
    """Initialize Sentry if SENTRY_DSN is set; no-op otherwise.

    Reads SENTRY_DSN from the environment. When set, imports sentry_sdk,
    calls sentry_sdk.init(), and sets the study_id tag so all events are
    tagged with the running study. When the DSN is not set (or sentry_sdk
    is not installed), this function does nothing and returns False.

    Args:
        study_id: Study identifier set as a Sentry tag on all events.

    Returns:
        True if Sentry was initialized, False if skipped.
    """
    dsn = os.environ.get(SENTRY_DSN_ENV, "").strip()
    if not dsn:
        return False

    try:
        import sentry_sdk

        sentry_sdk.init(dsn=dsn)
        sentry_sdk.set_tag("study_id", study_id)
        logger.debug("Sentry initialized for study_id={!r}.", study_id)
        return True
    except ImportError:
        logger.warning(
            "{} is set but sentry-sdk is not installed. Skipping Sentry init.",
            SENTRY_DSN_ENV,
        )
        return False
