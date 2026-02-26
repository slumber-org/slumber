from typing import Any
import yaml


class BlankLineDumper(yaml.SafeDumper):
    """Dumper that inserts blank lines between top-level objects."""

    def write_line_break(self, data: Any = None) -> None:
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()
