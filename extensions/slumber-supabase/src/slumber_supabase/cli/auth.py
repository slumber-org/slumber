"""Auth commands: login, signup, logout, password-change."""

from __future__ import annotations

import typer

from slumber_supabase.utils import exit_unless_supabase_extra_installed

auth_app = typer.Typer(
    name="auth",
    help="Supabase Auth: sign in, sign up, sign out, change password.",
)


@auth_app.command("login")
def auth_login(
    email: str = typer.Option(..., "--email", "-e", prompt=True, help="User email."),
    password: str | None = typer.Option(
        None,
        "--password",
        "-p",
        hide_input=True,
        prompt=True,
        help="User password.",
    ),
) -> None:
    """Sign in with email and password; store session for other commands."""
    exit_unless_supabase_extra_installed()
    from slumber_supabase.auth import sign_in

    try:
        sign_in(email, password)
        typer.echo("Signed in successfully.")
    except Exception as e:
        typer.echo(f"Login failed: {e}", err=True)
        raise typer.Exit(1) from e


@auth_app.command("signup")
def auth_signup(
    email: str = typer.Option(..., "--email", "-e", prompt=True, help="User email."),
    password: str | None = typer.Option(
        ...,
        "--password",
        "-p",
        hide_input=True,
        prompt=True,
        confirmation_prompt=True,
        help="User password.",
    ),
) -> None:
    """Sign up a new user with email and password."""
    exit_unless_supabase_extra_installed()
    from slumber_supabase.auth import sign_up

    try:
        sign_up(email, password)
        typer.echo("Sign-up successful.")
    except Exception as e:
        typer.echo(f"Sign-up failed: {e}", err=True)
        raise typer.Exit(1) from e


@auth_app.command("logout")
def auth_logout() -> None:
    """Sign out and clear the stored session."""
    exit_unless_supabase_extra_installed()
    from slumber_supabase.auth import sign_out

    sign_out()
    typer.echo("Signed out.")


@auth_app.command("password-change")
def auth_password_change(
    new_password: str | None = typer.Option(
        None,
        "--new-password",
        hide_input=True,
        prompt=True,
        confirmation_prompt=True,
        help="New user password.",
    ),
) -> None:
    """Change the current user's password (must be signed in)."""
    exit_unless_supabase_extra_installed()
    from slumber_supabase.auth import update_password

    try:
        update_password(new_password)
        typer.echo(
            "Password updated. You may need to sign in again with the new password."
        )
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Password change failed: {e}", err=True)
        raise typer.Exit(1) from e


@auth_app.command("status")
def auth_status() -> None:
    """Show whether you are signed in (and with which user)."""
    exit_unless_supabase_extra_installed()
    from slumber_supabase.auth.client import get_authenticated_client

    try:
        client = get_authenticated_client()
        session = client.auth.get_session()
        if session and session.user:
            email = getattr(session.user, "email", None) or "(no email)"
            typer.echo(f"Signed in as {email}")
        else:
            typer.echo("Not signed in.")
    except ValueError:
        typer.echo("Not signed in.")
