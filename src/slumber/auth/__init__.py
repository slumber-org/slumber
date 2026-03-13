"""Supabase Auth integration: sign-in, sign-up, password change, session persistence."""

from slumber.auth.client import (
    SESSION_FILENAME,
    get_client,
    get_authenticated_client,
    get_session_path,
    load_session,
    clear_saved_session,
)
from slumber.auth.operations import (
    sign_in,
    sign_up,
    sign_out,
    update_password,
)

__all__ = [
    "SESSION_FILENAME",
    "get_client",
    "get_authenticated_client",
    "get_session_path",
    "load_session",
    "clear_saved_session",
    "sign_in",
    "sign_up",
    "sign_out",
    "update_password",
]
