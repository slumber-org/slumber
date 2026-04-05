"""Tests for configure_run_logging."""

from pathlib import Path
from unittest.mock import patch


from slumber.runtime import RunContext, configure_run_logging
from slumber.schemas.study import RunLoggingConfig, Study


def _ctx() -> RunContext:
    return RunContext(
        study_id="s1",
        run_id="r001",
        condition_id="ctrl",
        participant_id="001",
        session_id="ses01",
    )


def _study(handlers: list[dict], level: str = "INFO") -> Study:
    return Study(
        study_id="s1",
        name="S1",
        logging=RunLoggingConfig(level=level, handlers=handlers),
    )


class TestApplyRunLogging:
    def test_returns_empty_list_when_no_handlers(self, tmp_path: Path) -> None:
        ids = configure_run_logging(_study([]), _ctx(), tmp_path)
        assert ids == []

    def test_returns_one_id_per_handler(self, tmp_path: Path) -> None:
        with patch(
            "slumber.runtime.logging.logger.add", side_effect=[10, 20]
        ) as mock_add:
            ids = configure_run_logging(
                _study([{"sink": "a.log"}, {"sink": "b.log"}]), _ctx(), tmp_path
            )
        assert ids == [10, 20]
        assert mock_add.call_count == 2

    def test_relative_sink_resolved_to_run_dir(self, tmp_path: Path) -> None:
        with patch("slumber.runtime.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(_study([{"sink": "app.log"}]), _ctx(), tmp_path)
        assert mock_add.call_args.kwargs["sink"] == tmp_path / "app.log"

    def test_placeholder_expanded_in_sink(self, tmp_path: Path) -> None:
        with patch("slumber.runtime.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(_study([{"sink": "{run_id}.log"}]), _ctx(), tmp_path)
        assert mock_add.call_args.kwargs["sink"] == tmp_path / "r001.log"

    def test_run_dir_placeholder_in_sink(self, tmp_path: Path) -> None:
        with patch("slumber.runtime.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study([{"sink": "{run_dir}/out.log"}]), _ctx(), tmp_path
            )
        assert mock_add.call_args.kwargs["sink"] == tmp_path / "out.log"

    def test_absolute_sink_not_modified(self, tmp_path: Path) -> None:
        abs_sink = tmp_path / "abs" / "run.log"
        with patch("slumber.runtime.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(_study([{"sink": str(abs_sink)}]), _ctx(), tmp_path)
        assert mock_add.call_args.kwargs["sink"] == abs_sink

    def test_study_level_used_when_handler_has_no_level(self, tmp_path: Path) -> None:
        with patch("slumber.runtime.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study([{"sink": "run.log"}], level="WARNING"), _ctx(), tmp_path
            )
        assert mock_add.call_args.kwargs["level"] == "WARNING"

    def test_handler_level_not_overridden_by_study_level(self, tmp_path: Path) -> None:
        with patch("slumber.runtime.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study([{"sink": "run.log", "level": "DEBUG"}], level="WARNING"),
                _ctx(),
                tmp_path,
            )
        assert mock_add.call_args.kwargs["level"] == "DEBUG"

    def test_non_string_sink_not_modified(self, tmp_path: Path) -> None:
        import sys

        with patch("slumber.runtime.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(_study([{"sink": sys.stdout}]), _ctx(), tmp_path)
        assert mock_add.call_args.kwargs["sink"] is sys.stdout
