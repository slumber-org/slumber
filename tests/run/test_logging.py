"""Tests for configure_run_logging."""

from pathlib import Path
from unittest.mock import patch

from slumber.config.paths import run_placeholders
from slumber.run import RunContext, configure_run_logging
from slumber.schemas.study import LoggingConfig, Study


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
        study_name="S1",
        logging=LoggingConfig(level=level, handlers=handlers),
    )


def _placeholders(study_dir: Path, run_dir: Path) -> dict[str, str]:
    return run_placeholders(
        study_dir,
        study_id="s1",
        study_name="S1",
        assets_dir="assets",
        run_dir=run_dir,
        run_id="r001",
        condition_id="ctrl",
        participant_id="001",
        session_id="ses01",
    )


class TestConfigureRunLogging:
    def test_returns_empty_list_when_no_handlers(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        ids = configure_run_logging(
            _study([]),
            _ctx(),
            run_dir,
            study_dir=tmp_path,
            placeholders=_placeholders(tmp_path, run_dir),
        )
        assert ids == []

    def test_returns_one_id_per_handler(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        with patch("slumber.run.logging.logger.add", side_effect=[10, 20]) as mock_add:
            ids = configure_run_logging(
                _study(
                    [
                        {"sink": "{run_dir}/a.log"},
                        {"sink": "{run_dir}/b.log"},
                    ]
                ),
                _ctx(),
                run_dir,
                study_dir=tmp_path,
                placeholders=_placeholders(tmp_path, run_dir),
            )
        assert ids == [10, 20]
        assert mock_add.call_count == 2

    def test_run_dir_placeholder_in_sink(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        with patch("slumber.run.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study([{"sink": "{run_dir}/app.log"}]),
                _ctx(),
                run_dir,
                study_dir=tmp_path,
                placeholders=_placeholders(tmp_path, run_dir),
            )
        assert mock_add.call_args.kwargs["sink"] == run_dir / "app.log"

    def test_placeholder_expanded_in_sink(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        with patch("slumber.run.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study([{"sink": "{run_dir}/{run_id}.log"}]),
                _ctx(),
                run_dir,
                study_dir=tmp_path,
                placeholders=_placeholders(tmp_path, run_dir),
            )
        assert mock_add.call_args.kwargs["sink"] == run_dir / "r001.log"

    def test_absolute_sink_not_modified(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        abs_sink = tmp_path / "abs" / "run.log"
        with patch("slumber.run.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study([{"sink": str(abs_sink)}]),
                _ctx(),
                run_dir,
                study_dir=tmp_path,
                placeholders=_placeholders(tmp_path, run_dir),
            )
        assert mock_add.call_args.kwargs["sink"] == abs_sink

    def test_study_level_used_when_handler_has_no_level(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        with patch("slumber.run.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study([{"sink": "{run_dir}/run.log"}], level="WARNING"),
                _ctx(),
                run_dir,
                study_dir=tmp_path,
                placeholders=_placeholders(tmp_path, run_dir),
            )
        assert mock_add.call_args.kwargs["level"] == "WARNING"

    def test_handler_level_not_overridden_by_study_level(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        with patch("slumber.run.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study(
                    [{"sink": "{run_dir}/run.log", "level": "DEBUG"}],
                    level="WARNING",
                ),
                _ctx(),
                run_dir,
                study_dir=tmp_path,
                placeholders=_placeholders(tmp_path, run_dir),
            )
        assert mock_add.call_args.kwargs["level"] == "DEBUG"

    def test_non_string_sink_not_modified(self, tmp_path: Path) -> None:
        import sys

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        with patch("slumber.run.logging.logger.add", return_value=1) as mock_add:
            configure_run_logging(
                _study([{"sink": sys.stdout}]),
                _ctx(),
                run_dir,
                study_dir=tmp_path,
                placeholders=_placeholders(tmp_path, run_dir),
            )
        assert mock_add.call_args.kwargs["sink"] is sys.stdout
