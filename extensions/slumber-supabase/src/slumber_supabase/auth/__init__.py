"""Supabase Auth: sign-in, sign-up, password change, session persistence."""

from slumber_supabase.auth.client import (
    SESSION_FILENAME,
    clear_saved_session,
    get_authenticated_client,
    get_client,
    get_session_path,
    load_session,
)
from slumber_supabase.auth.operations import (
    sign_in,
    sign_out,
    sign_up,
    update_password,
)

__all__ = [
    "SESSION_FILENAME",
    "clear_saved_session",
    "get_authenticated_client",
    "get_client",
    "get_session_path",
    "load_session",
    "sign_in",
    "sign_out",
    "sign_up",
    "update_password",
]
