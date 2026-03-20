from __future__ import annotations

import sys

from loguru import logger


def configure_cli_logging(*, verbose: bool = False) -> None:
    """Configure loguru for CLI use.

    Replaces the default loguru handler with a stderr handler at WARNING
    level (quiet by default). When ``verbose=True``, level is set to DEBUG
    so internal framework messages are visible.

    Args:
        verbose: If True, log at DEBUG level; otherwise WARNING.
    """
    logger.remove()
    level = "DEBUG" if verbose else "WARNING"
    logger.add(sys.stderr, level=level, format="{level}: {message}")
