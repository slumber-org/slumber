"""Supabase client factory and session file handling.

Session is persisted to a JSON file so CLI commands can reuse the authenticated
user (e.g. participant create after auth login). Use SUPABASE_URL and
SUPABASE_ANON_KEY from environment; optional SUPABASE_SERVICE_ROLE_KEY for
admin operations. Session file path is SLUMBER_SESSION_FILE or
~/.config/<package>/session.json (package name from top-level __name__).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from slumber.constants import (
    SESSION_FILE_ENV,
    SUPABASE_ANON_KEY_ENV,
    SUPABASE_SERVICE_ROLE_KEY_ENV,
    SUPABASE_URL_ENV,
)

if TYPE_CHECKING:
    from supabase import Client

SESSION_FILENAME = "session.json"
# Keep the historical session directory name used when auth lived under slumber.
_PACKAGE_NAME = "slumber"


def _get_session_path() -> Path:
    """Return path to session file from env or default."""
    path = os.getenv(SESSION_FILE_ENV, "").strip()
    if path:
        return Path(path)
    return Path.home() / ".config" / _PACKAGE_NAME / SESSION_FILENAME


def get_session_path() -> Path:
    """Return the path used for persisting the auth session.

    Returns:
        Path to the session JSON file (default: ~/.config/<package>/session.json).
    """
    return _get_session_path()


def _env_supabase_url() -> str:
    """Return SUPABASE_URL from environment; raise if missing."""
    url = os.getenv(SUPABASE_URL_ENV, "").strip()
    if not url:
        raise ValueError(
            "SUPABASE_URL is not set. Set it to your Supabase project URL "
            "(e.g. https://<project-ref>.supabase.co)."
        )
    return url


def _env_anon_key() -> str:
    """Return SUPABASE_ANON_KEY from environment; raise if missing."""
    key = os.getenv(SUPABASE_ANON_KEY_ENV, "").strip()
    if not key:
        raise ValueError(
            "SUPABASE_ANON_KEY is not set. Set it to your Supabase anon key."
        )
    return key


def get_client(*, use_service_role: bool = False) -> Client:
    """Create a Supabase client with anon key (or service role if requested).

    Args:
        use_service_role: If True, use SUPABASE_SERVICE_ROLE_KEY instead of
            SUPABASE_ANON_KEY. Use only for admin operations; keep secret.

    Returns:
        Supabase Client instance.

    Raises:
        ValueError: If required env vars are missing.
    """
    from supabase import create_client

    url = _env_supabase_url()
    if use_service_role:
        key = os.getenv(SUPABASE_SERVICE_ROLE_KEY_ENV, "").strip()
        if not key:
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY is not set. Required when "
                "use_service_role=True."
            )
    else:
        key = _env_anon_key()
    return create_client(url, key)


def _save_session(access_token: str, refresh_token: str) -> None:
    """Write session tokens to the session file."""
    path = _get_session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"access_token": access_token, "refresh_token": refresh_token}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(json.dumps(data))
    path.chmod(0o600)
    logger.debug("Saved session to {}", path)


def load_session() -> tuple[str, str] | None:
    """Load session tokens from the session file if present."""
    path = _get_session_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        access = data.get("access_token")
        refresh = data.get("refresh_token")
        if access and refresh:
            return (access, refresh)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load session from {}: {}", path, e)
    return None


def clear_saved_session() -> None:
    """Remove the persisted session file if it exists."""
    path = _get_session_path()
    if path.is_file():
        path.unlink()
        logger.debug("Cleared session file {}", path)


def get_authenticated_client() -> Client:
    """Return a Supabase client with the persisted session applied.

    Loads access_token and refresh_token from the session file, creates a
    client with the anon key, and sets the session so requests run as the
    logged-in user (RLS applies).

    Returns:
        Supabase Client with session set.

    Raises:
        ValueError: If session file is missing/invalid or env vars missing.
    """
    session_tokens = load_session()
    if not session_tokens:
        raise ValueError(
            "Not logged in. Run 'slumber auth login' with email and password."
        )
    client = get_client()
    access_token, refresh_token = session_tokens
    client.auth.set_session(access_token, refresh_token)
    return client


def save_session_from_response(response: object) -> None:
    """Extract session from auth response and persist to file.

    Args:
        response: Response from sign_in_with_password or sign_up; must have
            .session with .access_token and .refresh_token.
    """
    session = getattr(response, "session", None)
    if session is None:
        return
    access = getattr(session, "access_token", None)
    refresh = getattr(session, "refresh_token", None)
    if access and refresh:
        _save_session(access, refresh)
    else:
        logger.warning("Auth response had no session tokens; not saving")
