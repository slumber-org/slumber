"""Tests for DAG, Component, and Connection schemas."""

import pytest
from pydantic import ValidationError

from slumber.schemas import Component, Connection, DAG


class TestComponent:
    """Tests for Component schema."""

    def test_valid_minimal(self) -> None:
        comp = Component(name="MASTER", unit_type="Master")
        assert comp.name == "MASTER"
        assert comp.unit_type == "Master"
        assert comp.settings is None

    def test_valid_with_settings(self) -> None:
        comp = Component(
            name="ZMAX",
            unit_type="ZMaxDataReceiver",
            settings={"data_collection_enabled": True},
        )
        assert comp.settings is not None
        assert comp.settings["data_collection_enabled"] is True

    def test_name_uppercase_underscore_required(self) -> None:
        with pytest.raises(ValidationError):
            Component(name="lowercase", unit_type="SomeUnit")

    def test_name_valid(self) -> None:
        comp = Component(name="SLEEP_SCORING", unit_type="SleepScoring")
        assert comp.name == "SLEEP_SCORING"

    def test_unit_alias(self) -> None:
        comp = Component(name="MASTER", unit="Master")
        assert comp.unit_type == "Master"


class TestConnection:
    """Tests for Connection schema."""

    def test_valid(self) -> None:
        conn = Connection(
            output_stream="ZMAX/OUTPUT_SAMPLE",
            input_stream="QUEUE/INPUT",
        )
        assert conn.output_stream == "ZMAX/OUTPUT_SAMPLE"
        assert conn.input_stream == "QUEUE/INPUT"

    def test_invalid_stream_format_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Connection(
                output_stream="no_slash",
                input_stream="A/B",
            )
        with pytest.raises(ValidationError):
            Connection(
                output_stream="A/B",
                input_stream="A/B/C",
            )


class TestDAG:
    """Tests for DAG schema."""

    def test_valid_minimal(self) -> None:
        dag = DAG(
            components=[Component(name="MASTER", unit_type="Master")],
            connections=[],
            process_components=[],
        )
        assert len(dag.components) == 1
        assert dag.has_component("MASTER")
        assert dag.component_names == {"MASTER"}

    def test_connections_coerced_from_tuples(self) -> None:
        dag = DAG(
            components=[
                Component(name="A", unit_type="UnitA"),
                Component(name="B", unit_type="UnitB"),
            ],
            connections=[
                ["A/OUT", "B/IN"],
            ],
            process_components=[],
        )
        assert len(dag.connections) == 1
        assert dag.connections[0].output_stream == "A/OUT"
        assert dag.connections[0].input_stream == "B/IN"

    def test_duplicate_component_names_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            DAG(
                components=[
                    Component(name="MASTER", unit_type="Master"),
                    Component(name="MASTER", unit_type="Other"),
                ],
                connections=[],
                process_components=[],
            )
        assert "unique" in str(exc_info.value).lower()

    def test_connection_references_unknown_component_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            DAG(
                components=[Component(name="MASTER", unit_type="Master")],
                connections=[
                    Connection(output_stream="UNKNOWN/OUT", input_stream="MASTER/IN")
                ],
                process_components=[],
            )
        assert "unknown" in str(exc_info.value).lower() or "UNKNOWN" in str(
            exc_info.value
        )

    def test_process_components_must_exist(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            DAG(
                components=[Component(name="MASTER", unit_type="Master")],
                connections=[],
                process_components=["NOT_PRESENT"],
            )
        assert "unknown" in str(exc_info.value).lower() or "NOT_PRESENT" in str(
            exc_info.value
        )

    def test_process_components_valid(self) -> None:
        dag = DAG(
            components=[
                Component(name="MASTER", unit_type="Master"),
                Component(name="WORKER", unit_type="Worker"),
            ],
            connections=[],
            process_components=["WORKER"],
        )
        assert dag.process_components == ["WORKER"]

    def test_components_min_length(self) -> None:
        with pytest.raises(ValidationError):
            DAG(components=[], connections=[], process_components=[])
