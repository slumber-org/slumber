"""Tests for slumber doctor command (local checks only)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from slumber.cli.doctor import (
    CheckStatus,
    check_dependencies,
    check_environment,
    run_doctor,
)
from slumber.cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCheckEnvironment:
    def test_optional_vars_skip_when_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for var in ("STUDY_DIR", "PARTICIPANT_ID"):
            monkeypatch.delenv(var, raising=False)

        results = {r.name: r for r in check_environment()}

        for var in ("STUDY_DIR", "PARTICIPANT_ID"):
            assert results[var].status == CheckStatus.SKIP
            assert results[var].required is False

    def test_optional_vars_ok_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("STUDY_DIR", "/tmp/study")
        monkeypatch.setenv("PARTICIPANT_ID", "sub-001")

        results = {r.name: r for r in check_environment()}

        assert results["STUDY_DIR"].status == CheckStatus.OK
        assert results["PARTICIPANT_ID"].status == CheckStatus.OK

    def test_all_env_vars_are_checked(self) -> None:
        results = {r.name for r in check_environment()}
        assert results == {"STUDY_DIR", "PARTICIPANT_ID"}


class TestCheckDependencies:
    def test_ezmsg_ok_when_installed(self) -> None:
        with patch("slumber.cli.doctor.importlib.import_module", return_value=object()):
            results = {r.name: r for r in check_dependencies()}

        assert results["ezmsg"].status == CheckStatus.OK

    def test_ezmsg_fail_when_not_importable(self) -> None:
        def _raise(name: str) -> None:
            if name == "ezmsg":
                raise ImportError("no module named ezmsg")

        with patch("slumber.cli.doctor.importlib.import_module", side_effect=_raise):
            results = {r.name: r for r in check_dependencies()}

        assert results["ezmsg"].status == CheckStatus.FAIL
        assert results["ezmsg"].required is True

    def test_nicegui_skip_when_not_installed(self) -> None:
        def _raise(name: str) -> None:
            if name == "nicegui":
                raise ImportError("no module named nicegui")

        with patch("slumber.cli.doctor.importlib.import_module", side_effect=_raise):
            results = {r.name: r for r in check_dependencies()}

        assert results["nicegui"].status == CheckStatus.SKIP
        assert results["nicegui"].required is False

    def test_nicegui_ok_when_installed(self) -> None:
        with patch("slumber.cli.doctor.importlib.import_module", return_value=object()):
            results = {r.name: r for r in check_dependencies()}

        assert results["nicegui"].status == CheckStatus.OK
        assert results["nicegui"].required is False


class TestRunDoctor:
    def test_failures_does_not_include_optional_skips(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("STUDY_DIR", raising=False)
        monkeypatch.delenv("PARTICIPANT_ID", raising=False)

        with patch("slumber.cli.doctor.check_dependencies", return_value=[]):
            report = run_doctor()

        failure_names = {f.name for f in report.failures}
        assert "STUDY_DIR" not in failure_names
        assert "PARTICIPANT_ID" not in failure_names


class TestDoctorCLI:
    def test_exits_0_when_no_failures(self, runner: CliRunner) -> None:
        with (
            patch("slumber.cli.doctor.check_environment", return_value=[]),
            patch("slumber.cli.doctor.check_dependencies", return_value=[]),
        ):
            result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "No issues found" in result.output

    def test_exits_1_when_required_check_fails(self, runner: CliRunner) -> None:
        from slumber.cli.doctor import CheckResult

        with (
            patch(
                "slumber.cli.doctor.check_environment",
                return_value=[],
            ),
            patch(
                "slumber.cli.doctor.check_dependencies",
                return_value=[
                    CheckResult(
                        name="ezmsg",
                        status=CheckStatus.FAIL,
                        message="not installed",
                        required=True,
                    )
                ],
            ),
        ):
            result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 1
        assert "1 issue" in result.output

    def test_shows_env_var_names_in_output(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("STUDY_DIR", "/tmp/study")
        monkeypatch.delenv("PARTICIPANT_ID", raising=False)

        result = runner.invoke(app, ["doctor"])

        assert "STUDY_DIR" in result.output
        assert "PARTICIPANT_ID" in result.output
        assert "ezmsg" in result.output


class TestVerboseFlag:
    def test_verbose_flag_accepted(self, runner: CliRunner) -> None:
        with patch("slumber.cli.doctor.run_doctor") as mock_run:
            from slumber.cli.doctor import DoctorReport

            mock_run.return_value = DoctorReport()
            result = runner.invoke(app, ["--verbose", "doctor"])

        assert result.exit_code in (0, 1)
        assert "Error: No such option" not in (result.output or "")

    def test_v_short_flag_accepted(self, runner: CliRunner) -> None:
        with patch("slumber.cli.doctor.run_doctor") as mock_run:
            from slumber.cli.doctor import DoctorReport

            mock_run.return_value = DoctorReport()
            result = runner.invoke(app, ["-v", "doctor"])

        assert "Error: No such option" not in (result.output or "")
