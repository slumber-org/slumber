"""Auth operations: sign-in, sign-up, sign-out, password change.

All operations use the Supabase client (anon key). Sign-in and sign-up
persist the session to the session file so subsequent CLI commands use
the authenticated user.
"""

from __future__ import annotations

from loguru import logger

from slumber_supabase.auth.client import (
    clear_saved_session,
    get_authenticated_client,
    get_client,
    load_session,
    save_session_from_response,
)


def sign_in(email: str, password: str) -> object:
    """Sign in with email and password; persist session to file.

    Args:
        email: User email.
        password: User password.

    Returns:
        Auth response from Supabase (has .session with tokens).

    Raises:
        Exception: On auth failure (e.g. invalid credentials).
    """
    client = get_client()
    response = client.auth.sign_in_with_password({"email": email, "password": password})
    save_session_from_response(response)
    return response


def sign_up(email: str, password: str) -> object:
    """Sign up a new user with email and password; persist session if returned.

    Args:
        email: User email.
        password: User password.

    Returns:
        Auth response from Supabase (may require email confirmation).

    Raises:
        Exception: On sign-up failure.
    """
    client = get_client()
    response = client.auth.sign_up({"email": email, "password": password})
    save_session_from_response(response)
    return response


def sign_out() -> None:
    """Sign out: clear persisted session and optionally call Supabase sign_out.

    If a session file exists, create a client with it and call Supabase sign_out
    to invalidate the server-side session, then clear the local file.
    """
    try:
        tokens = load_session()
        if tokens:
            client = get_client()
            client.auth.set_session(tokens[0], tokens[1])
            client.auth.sign_out()
    # TODO: [refactor] catch typed auth/SDK errors instead of Exception
    except Exception as exc:  # noqa: BLE001
        logger.warning("Remote sign-out skipped: {}", exc)
    clear_saved_session()


def update_password(new_password: str) -> None:
    """Update the current user's password (must be signed in).

    Uses the persisted session to get an authenticated client, then
    calls Supabase update_user. Session file is not updated; user may
    need to sign in again with the new password.

    Args:
        new_password: New password to set.

    Raises:
        ValueError: If not logged in (no session file).
        Exception: On Supabase update failure.
    """
    client = get_authenticated_client()
    client.auth.update_user({"password": new_password})
