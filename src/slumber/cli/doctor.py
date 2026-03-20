"""slumber doctor: environment, connectivity, and dependency checks."""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from enum import Enum

import typer
from supabase import create_client

from slumber.constants import (
    DATABASE_URL_ENV,
    PARTICIPANT_ID_ENV,
    SENTRY_DSN_ENV,
    SESSION_FILE_ENV,
    STUDY_DIR_ENV,
    STUDY_ID_ENV,
    SUPABASE_ANON_KEY_ENV,
    SUPABASE_SERVICE_ROLE_KEY_ENV,
    SUPABASE_URL_ENV,
    USER_ID_ENV,
)


_ENV_CHECKS: list[tuple[str, str, bool]] = [
    # --- Required ---
    (SUPABASE_URL_ENV, "required for all Supabase operations", True),
    (SUPABASE_ANON_KEY_ENV, "required for auth and API access", True),
    # --- Optional: backend / admin ---
    (DATABASE_URL_ENV, "optional; required for slumber db upgrade (migrations)", False),
    (
        SUPABASE_SERVICE_ROLE_KEY_ENV,
        "optional; required for admin commands: participant, session, condition sync",
        False,
    ),
    # --- Optional: CLI convenience defaults ---
    (
        STUDY_DIR_ENV,
        "optional; default study folder path for study/condition commands",
        False,
    ),
    (
        STUDY_ID_ENV,
        "optional; default study ID for participant and session commands",
        False,
    ),
    (USER_ID_ENV, "optional; default auth user UUID for participant commands", False),
    (
        PARTICIPANT_ID_ENV,
        "optional; default participant ID for session commands",
        False,
    ),
    (
        SESSION_FILE_ENV,
        "optional; override default session file path (~/.config/slumber/session.json)",
        False,
    ),
    # --- Optional: monitoring ---
    (
        SENTRY_DSN_ENV,
        "optional; enables Sentry error monitoring during study runs",
        False,
    ),
]

_DEPS: list[tuple[str, bool]] = [
    ("ezmsg", True),
    ("sentry_sdk", False),
]

_DEP_DESCRIPTIONS: dict[str, str] = {
    "ezmsg": "data acquisition backbone",
    "sentry_sdk": "optional; enables Sentry run monitoring (pip install slumber[sentry] or uv sync --extra sentry)",
}


class CheckStatus(str, Enum):
    """Outcome of a single doctor check."""

    OK = "ok"
    FAIL = "fail"
    SKIP = "skip"  # optional; not set / not installed


_STATUS_SYMBOL = {
    CheckStatus.OK: "✓",
    CheckStatus.FAIL: "✗",
    CheckStatus.SKIP: "—",
}


_STATUS_COLOR = {
    CheckStatus.OK: typer.colors.GREEN,
    CheckStatus.FAIL: typer.colors.RED,
    CheckStatus.SKIP: typer.colors.YELLOW,
}


@dataclass
class CheckResult:
    """Result of one doctor check."""

    name: str
    status: CheckStatus
    message: str
    required: bool = True


@dataclass
class DoctorReport:
    """Aggregated results from all doctor checks."""

    env: list[CheckResult] = field(default_factory=list)
    connectivity: list[CheckResult] = field(default_factory=list)
    dependencies: list[CheckResult] = field(default_factory=list)

    @property
    def failures(self) -> list[CheckResult]:
        """All required checks that failed."""
        all_checks = self.env + self.connectivity + self.dependencies
        return [c for c in all_checks if c.required and c.status == CheckStatus.FAIL]


def check_environment() -> list[CheckResult]:
    """Check that expected environment variables are present.

    Returns:
        List of CheckResult, one per env var.
    """
    results = []
    for var, description, required in _ENV_CHECKS:
        value = os.getenv(var, "").strip()
        if value:
            results.append(
                CheckResult(
                    name=var, status=CheckStatus.OK, message="set", required=required
                )
            )
        elif required:
            results.append(
                CheckResult(
                    name=var,
                    status=CheckStatus.FAIL,
                    message=f"not set ({description})",
                    required=True,
                )
            )
        else:
            results.append(
                CheckResult(
                    name=var,
                    status=CheckStatus.SKIP,
                    message=f"not set ({description})",
                    required=False,
                )
            )
    return results


def check_supabase_connectivity() -> CheckResult:
    """Try to reach the Supabase project and execute a lightweight query.

    Skipped when SUPABASE_URL or SUPABASE_ANON_KEY are not set.

    Returns:
        CheckResult for the connectivity check.
    """
    url = os.getenv(SUPABASE_URL_ENV, "").strip()
    key = os.getenv(SUPABASE_ANON_KEY_ENV, "").strip()

    if not url or not key:
        return CheckResult(
            name="connectivity",
            status=CheckStatus.SKIP,
            message="skipped (SUPABASE_URL or SUPABASE_ANON_KEY not set)",
            required=False,
        )

    try:
        client = create_client(url, key)
        client.auth.get_user()
        return CheckResult(name="connectivity", status=CheckStatus.OK, message="ok")
    except Exception as exc:
        return CheckResult(
            name="connectivity",
            status=CheckStatus.FAIL,
            message=f"connection error: {exc}",
            required=True,
        )


def check_dependencies() -> list[CheckResult]:
    """Check whether declared packages are importable.

    Returns:
        List of CheckResult, one per package.
    """
    results = []
    for package, required in _DEPS:
        description = _DEP_DESCRIPTIONS[package]
        try:
            importlib.import_module(package)
            results.append(
                CheckResult(
                    name=package,
                    status=CheckStatus.OK,
                    message="installed",
                    required=required,
                )
            )
        except ImportError:
            results.append(
                CheckResult(
                    name=package,
                    status=CheckStatus.FAIL if required else CheckStatus.SKIP,
                    message=f"not installed ({description})",
                    required=required,
                )
            )
    return results


def _print_check(result: CheckResult, *, name_width: int = 30) -> None:
    symbol = _STATUS_SYMBOL[result.status]
    color = _STATUS_COLOR[result.status]
    name_col = result.name.ljust(name_width)
    typer.echo(f"  {typer.style(symbol, fg=color)} {name_col} {result.message}")


def _print_section(
    title: str, checks: list[CheckResult], *, name_width: int = 30
) -> None:
    typer.echo(f"\n{typer.style(title, bold=True)}")
    for check in checks:
        _print_check(check, name_width=name_width)


def run_doctor() -> DoctorReport:
    """Run all doctor checks and return the report.

    Returns:
        DoctorReport with results for env, connectivity, and dependencies.
    """
    report = DoctorReport(
        env=check_environment(),
        connectivity=[check_supabase_connectivity()],
        dependencies=check_dependencies(),
    )
    return report


def doctor_command() -> None:
    """Check environment variables, Supabase connectivity, and optional dependencies."""
    report = run_doctor()

    _print_section("Environment", report.env, name_width=28)
    _print_section("Supabase", report.connectivity, name_width=28)
    _print_section("Dependencies", report.dependencies, name_width=28)

    typer.echo("")
    failures = report.failures
    if not failures:
        typer.echo(typer.style("✓ No issues found.", fg=typer.colors.GREEN))
    else:
        count = len(failures)
        typer.echo(
            typer.style(f"✗ Doctor found {count} issue(s).", fg=typer.colors.RED)
        )
        raise typer.Exit(1)
