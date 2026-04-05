"""Tests for slumber doctor command."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from slumber.cli.doctor import (
    CheckStatus,
    check_environment,
    check_dependencies,
    check_supabase_connectivity,
    run_doctor,
)
from slumber.cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# check_environment unit tests
# ---------------------------------------------------------------------------


class TestCheckEnvironment:
    def test_required_vars_ok_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SUPABASE_URL and SUPABASE_ANON_KEY are OK when set."""
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

        with patch("slumber.cli.doctor.is_supabase_extra_installed", return_value=True):
            results = {r.name: r for r in check_environment()}

        assert results["SUPABASE_URL"].status == CheckStatus.OK
        assert results["SUPABASE_ANON_KEY"].status == CheckStatus.OK

    def test_supabase_env_skip_when_extra_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SUPABASE_URL / ANON_KEY are optional when the supabase extra is absent."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

        with patch(
            "slumber.cli.doctor.is_supabase_extra_installed", return_value=False
        ):
            results = {r.name: r for r in check_environment()}

        assert results["SUPABASE_URL"].status == CheckStatus.SKIP
        assert results["SUPABASE_URL"].required is False
        assert results["SUPABASE_ANON_KEY"].status == CheckStatus.SKIP

    def test_optional_vars_skip_when_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All optional vars are SKIP (required=False) when not set."""
        optional_vars = (
            "DATABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "STUDY_DIR",
            "STUDY_ID",
            "USER_ID",
            "PARTICIPANT_ID",
            "SLUMBER_SESSION_FILE",
            "SENTRY_DSN",
        )
        for var in optional_vars:
            monkeypatch.delenv(var, raising=False)

        results = {r.name: r for r in check_environment()}

        for var in optional_vars:
            assert results[var].status == CheckStatus.SKIP, f"{var} should be SKIP"
            assert results[var].required is False, f"{var} should not be required"

    def test_optional_vars_ok_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """All optional vars show OK when set."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/slumber")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key")
        monkeypatch.setenv("STUDY_ID", "my-study")
        monkeypatch.setenv("USER_ID", "uuid-123")
        monkeypatch.setenv("PARTICIPANT_ID", "sub-001")
        monkeypatch.setenv("SLUMBER_SESSION_FILE", "/tmp/session.json")

        results = {r.name: r for r in check_environment()}

        assert results["DATABASE_URL"].status == CheckStatus.OK
        assert results["SUPABASE_SERVICE_ROLE_KEY"].status == CheckStatus.OK
        assert results["STUDY_ID"].status == CheckStatus.OK
        assert results["USER_ID"].status == CheckStatus.OK
        assert results["PARTICIPANT_ID"].status == CheckStatus.OK
        assert results["SLUMBER_SESSION_FILE"].status == CheckStatus.OK

    def test_all_env_vars_are_checked(self) -> None:
        """check_environment covers all known env var names."""
        results = {r.name for r in check_environment()}
        expected = {
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "DATABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "STUDY_DIR",
            "STUDY_ID",
            "USER_ID",
            "PARTICIPANT_ID",
            "SLUMBER_SESSION_FILE",
            "SENTRY_DSN",
        }
        assert expected.issubset(results)


# ---------------------------------------------------------------------------
# check_supabase_connectivity unit tests
# ---------------------------------------------------------------------------


class TestCheckSupabaseConnectivity:
    def test_skip_when_extra_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Connectivity is SKIP when the supabase package is not installed."""
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

        with patch(
            "slumber.cli.doctor.is_supabase_extra_installed", return_value=False
        ):
            result = check_supabase_connectivity()

        assert result.status == CheckStatus.SKIP
        assert "slumber[supabase]" in result.message
        assert result.required is False

    def test_skip_when_env_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Connectivity check is SKIP when URL or key is not set."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

        with patch("slumber.cli.doctor.is_supabase_extra_installed", return_value=True):
            result = check_supabase_connectivity()

        assert result.status == CheckStatus.SKIP
        assert result.required is False

    @pytest.mark.supabase
    def test_ok_when_client_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Connectivity is OK when the Supabase client query returns without error."""
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

        with (
            patch("slumber.cli.doctor.is_supabase_extra_installed", return_value=True),
            patch("supabase.create_client") as mock_create,
        ):
            mock_client = mock_create.return_value
            mock_client.auth.get_user.return_value = None

            result = check_supabase_connectivity()

        assert result.status == CheckStatus.OK

    @pytest.mark.supabase
    def test_fail_when_client_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Connectivity is FAIL when the Supabase client raises an exception."""
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

        with (
            patch("slumber.cli.doctor.is_supabase_extra_installed", return_value=True),
            patch("supabase.create_client", side_effect=Exception("timeout")),
        ):
            result = check_supabase_connectivity()

        assert result.status == CheckStatus.FAIL
        assert "timeout" in result.message


# ---------------------------------------------------------------------------
# check_dependencies unit tests
# ---------------------------------------------------------------------------


class TestCheckDependencies:
    def test_ezmsg_ok_when_installed(self) -> None:
        """ezmsg shows OK when it can be imported (it's a declared dependency)."""
        with patch("slumber.cli.doctor.importlib.import_module", return_value=object()):
            results = {r.name: r for r in check_dependencies()}

        assert results["ezmsg"].status == CheckStatus.OK

    def test_ezmsg_fail_when_not_importable(self) -> None:
        """ezmsg shows FAIL (required) when it cannot be imported."""

        def _raise(name: str) -> None:
            if name == "ezmsg":
                raise ImportError("no module named ezmsg")

        with patch("slumber.cli.doctor.importlib.import_module", side_effect=_raise):
            results = {r.name: r for r in check_dependencies()}

        assert results["ezmsg"].status == CheckStatus.FAIL
        assert results["ezmsg"].required is True

    def test_sentry_sdk_skip_when_not_installed(self) -> None:
        """sentry_sdk shows SKIP (not required) when it cannot be imported."""

        def _raise(name: str) -> None:
            if name == "sentry_sdk":
                raise ImportError("no module named sentry_sdk")

        with patch("slumber.cli.doctor.importlib.import_module", side_effect=_raise):
            results = {r.name: r for r in check_dependencies()}

        assert results["sentry_sdk"].status == CheckStatus.SKIP
        assert results["sentry_sdk"].required is False

    def test_sentry_sdk_ok_when_installed(self) -> None:
        """sentry_sdk shows OK when it can be imported."""
        with patch("slumber.cli.doctor.importlib.import_module", return_value=object()):
            results = {r.name: r for r in check_dependencies()}

        assert results["sentry_sdk"].status == CheckStatus.OK
        assert results["sentry_sdk"].required is False

    def test_nicegui_skip_when_not_installed(self) -> None:
        """nicegui shows SKIP (not required) when it cannot be imported."""

        def _raise(name: str) -> None:
            if name == "nicegui":
                raise ImportError("no module named nicegui")

        with patch("slumber.cli.doctor.importlib.import_module", side_effect=_raise):
            results = {r.name: r for r in check_dependencies()}

        assert results["nicegui"].status == CheckStatus.SKIP
        assert results["nicegui"].required is False

    def test_nicegui_ok_when_installed(self) -> None:
        """nicegui shows OK when it can be imported."""
        with patch("slumber.cli.doctor.importlib.import_module", return_value=object()):
            results = {r.name: r for r in check_dependencies()}

        assert results["nicegui"].status == CheckStatus.OK
        assert results["nicegui"].required is False

    def test_supabase_ok_when_extra_installed(self) -> None:
        """supabase shows OK when is_supabase_extra_installed is true."""
        with patch("slumber.cli.doctor.is_supabase_extra_installed", return_value=True):
            results = {r.name: r for r in check_dependencies()}

        assert results["supabase"].status == CheckStatus.OK
        assert results["supabase"].required is False

    def test_supabase_skip_when_extra_not_installed(self) -> None:
        """supabase shows SKIP when the optional dependency is not present."""
        with patch(
            "slumber.cli.doctor.is_supabase_extra_installed", return_value=False
        ):
            results = {r.name: r for r in check_dependencies()}

        assert results["supabase"].status == CheckStatus.SKIP
        assert results["supabase"].required is False


# ---------------------------------------------------------------------------
# run_doctor integration
# ---------------------------------------------------------------------------


class TestRunDoctor:
    def test_failures_does_not_include_optional_skips(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DoctorReport.failures does not include optional checks with SKIP status."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with (
            patch("slumber.cli.doctor.is_supabase_extra_installed", return_value=True),
            patch("slumber.cli.doctor.check_supabase_connectivity") as mock_conn,
            patch("slumber.cli.doctor.check_dependencies", return_value=[]),
        ):
            mock_conn.return_value = __import__(
                "slumber.cli.doctor", fromlist=["CheckResult"]
            ).CheckResult(
                name="connectivity",
                status=CheckStatus.SKIP,
                message="skipped",
                required=False,
            )
            report = run_doctor()

        # Only required failures (SUPABASE_URL, SUPABASE_ANON_KEY) should be in failures
        failure_names = {f.name for f in report.failures}
        assert "SUPABASE_URL" not in failure_names  # optional
        assert "SUPABASE_ANON_KEY" not in failure_names  # optional
        assert "DATABASE_URL" not in failure_names  # optional


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


class TestDoctorCLI:
    def test_exits_0_when_no_failures(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """doctor exits 0 when all required checks pass."""
        with (
            patch("slumber.cli.doctor.check_environment", return_value=[]),
            patch(
                "slumber.cli.doctor.check_supabase_connectivity",
                return_value=__import__(
                    "slumber.cli.doctor", fromlist=["CheckResult"]
                ).CheckResult(name="connectivity", status=CheckStatus.OK, message="ok"),
            ),
            patch("slumber.cli.doctor.check_dependencies", return_value=[]),
        ):
            result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "No issues found" in result.output

    def test_exits_1_when_required_check_fails(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """doctor exits 1 when a required check fails."""
        from slumber.cli.doctor import CheckResult

        with (
            patch(
                "slumber.cli.doctor.check_environment",
                return_value=[
                    CheckResult(
                        name="SUPABASE_URL",
                        status=CheckStatus.FAIL,
                        message="not set",
                        required=True,
                    )
                ],
            ),
            patch(
                "slumber.cli.doctor.check_supabase_connectivity",
                return_value=CheckResult(
                    name="connectivity",
                    status=CheckStatus.SKIP,
                    message="skipped",
                    required=False,
                ),
            ),
            patch("slumber.cli.doctor.check_dependencies", return_value=[]),
        ):
            result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 1
        assert "1 issue" in result.output

    def test_shows_env_var_names_in_output(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """doctor output includes checked env var names."""
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
        for var in (
            "DATABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "STUDY_DIR",
            "SENTRY_DSN",
        ):
            monkeypatch.delenv(var, raising=False)

        with patch(
            "slumber.cli.doctor.check_supabase_connectivity",
            return_value=__import__(
                "slumber.cli.doctor", fromlist=["CheckResult"]
            ).CheckResult(
                name="connectivity",
                status=CheckStatus.SKIP,
                message="skipped",
                required=False,
            ),
        ):
            result = runner.invoke(app, ["doctor"])

        assert "SUPABASE_URL" in result.output
        assert "SUPABASE_ANON_KEY" in result.output
        assert "DATABASE_URL" in result.output


# ---------------------------------------------------------------------------
# Verbose flag
# ---------------------------------------------------------------------------


class TestVerboseFlag:
    def test_verbose_flag_accepted(self, runner: CliRunner) -> None:
        """--verbose flag is accepted without error."""
        with patch("slumber.cli.doctor.run_doctor") as mock_run:
            from slumber.cli.doctor import DoctorReport

            mock_run.return_value = DoctorReport()
            result = runner.invoke(app, ["--verbose", "doctor"])

        # Exit code 0 (no failures from empty report) or at least no parse error
        assert result.exit_code in (0, 1)
        assert "Error: No such option" not in (result.output or "")

    def test_v_short_flag_accepted(self, runner: CliRunner) -> None:
        """-v short flag is accepted without error."""
        with patch("slumber.cli.doctor.run_doctor") as mock_run:
            from slumber.cli.doctor import DoctorReport

            mock_run.return_value = DoctorReport()
            result = runner.invoke(app, ["-v", "doctor"])

        assert "Error: No such option" not in (result.output or "")
