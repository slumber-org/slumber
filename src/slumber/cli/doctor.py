"""slumber doctor: local environment and dependency checks."""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from enum import Enum

import typer

from slumber.constants import PARTICIPANT_ID_ENV, STUDY_DIR_ENV

_ENV_CHECKS: list[tuple[str, str, bool]] = [
    (
        STUDY_DIR_ENV,
        "optional; default study folder path for study commands",
        False,
    ),
    (
        PARTICIPANT_ID_ENV,
        "optional; used when run layout includes {participant_id}",
        False,
    ),
]

_DEPS: list[tuple[str, bool]] = [
    ("ezmsg", True),
    ("nicegui", False),
]

_DEP_DESCRIPTIONS: dict[str, str] = {
    "ezmsg": "data acquisition backbone",
    "nicegui": "optional; participant UI (pip install slumber[nicegui] or uv sync --extra nicegui)",
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
    dependencies: list[CheckResult] = field(default_factory=list)

    @property
    def failures(self) -> list[CheckResult]:
        """All required checks that failed."""
        all_checks = self.env + self.dependencies
        return [c for c in all_checks if c.required and c.status == CheckStatus.FAIL]


def check_environment() -> list[CheckResult]:
    """Check that expected local environment variables are present.

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
            installed = True
        except ImportError:
            installed = False
        if installed:
            results.append(
                CheckResult(
                    name=package,
                    status=CheckStatus.OK,
                    message="installed",
                    required=required,
                )
            )
        else:
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
        DoctorReport with results for env and dependencies.
    """
    return DoctorReport(
        env=check_environment(),
        dependencies=check_dependencies(),
    )


def doctor_command() -> None:
    """Check local environment variables and optional dependencies."""
    report = run_doctor()

    _print_section("Environment", report.env, name_width=28)
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
