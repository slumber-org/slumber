"""Supabase integration: auth, REST helpers, ORM models, and shared utilities.

CLI and other entrypoints should call :func:`exit_unless_supabase_extra_installed`
(or a Typer callback from :mod:`slumber_supabase.utils`) before importing
:mod:`slumber_supabase.auth`, :mod:`slumber_supabase.backend`, or
:mod:`slumber_supabase.models`. Non-interactive code can use
:func:`is_supabase_extra_installed` only.
"""

from __future__ import annotations

from slumber_supabase.utils import (
    SUPABASE_INSTALL_HINT,
    exit_unless_supabase_extra_installed,
    get_database_url,
    is_supabase_extra_installed,
)

__all__ = [
    "SUPABASE_INSTALL_HINT",
    "exit_unless_supabase_extra_installed",
    "get_database_url",
    "is_supabase_extra_installed",
]
