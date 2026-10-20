"""AppFrame: persistent header, body, and footer chrome for a GUI run."""

from __future__ import annotations

from typing import Any

from slumber.ui.theme import (
    BRAND,
    PAGE_BG,
    POWERED_BY,
    SECONDARY,
    SURFACE,
    SURFACE_BORDER,
)
from slumber.ui.widgets import logo_mark


class AppFrame:
    """One frame per run: header (logo, title), body slot, footer.

    Study ``ui.settings.frame`` is the default; :meth:`apply_frame` applies the
    merged phase override (e.g. hide header/footer during sleep).
    """

    def __init__(
        self,
        *,
        study_name: str,
        logo_url: str | None = None,
        frame: dict[str, Any] | None = None,
    ) -> None:
        self._study_name = study_name
        self._logo_url = logo_url
        self._default_frame = dict(frame or {})
        # TODO: [refactor] type NiceGUI slots via TYPE_CHECKING (Element / Label), like
        # widgets/buttons.py — keep runtime imports lazy for optional nicegui.
        self._header: Any | None = None
        self._title_label: Any | None = None
        self._body: Any | None = None
        self._footer: Any | None = None
        self._mounted = False

    @property
    def body(self) -> Any:
        """NiceGUI body container where layouts mount."""
        if self._body is None:
            raise RuntimeError("AppFrame.mount() must be called first.")
        return self._body

    @property
    def mounted(self) -> bool:
        """Whether the frame elements exist in the page."""
        return self._mounted

    def mount(self) -> None:
        """Build header, body, and footer into the current NiceGUI page."""
        from nicegui import ui

        with ui.column().classes(
            f"w-full h-screen m-0 p-0 bg-[{PAGE_BG}] flex flex-col"
        ):
            self._header = ui.row().classes(
                f"w-full items-center gap-3 px-6 py-3 bg-[{SURFACE}] "
                f"border-b border-[{SURFACE_BORDER}] shrink-0"
            )
            with self._header:
                logo_mark(self._logo_url, size="header")
                self._title_label = ui.label(self._study_name).classes(
                    f"text-h6 font-bold text-[{BRAND}]"
                )

            self._body = ui.column().classes(
                "w-full flex-1 min-h-0 overflow-auto p-0 m-0"
            )

            self._footer = ui.row().classes("w-full justify-center pt-2 pb-6 shrink-0")
            with self._footer:
                ui.label(POWERED_BY).classes(
                    f"text-caption text-[{SECONDARY}] opacity-60"
                )

        self._mounted = True
        self.apply_frame(self._default_frame)

    def apply_frame(self, frame: dict[str, Any]) -> None:
        """Show/hide chrome and update header title/logo from merged settings.

        Args:
            frame: Merged study + phase frame dict. ``header: false`` or
                ``footer: false`` hides that region; a header dict may set
                ``title`` (``logo`` path is resolved by the GUI backend).
        """
        if not self._mounted:
            self._default_frame = dict(frame)
            return

        header = frame.get("header")
        footer = frame.get("footer")

        if self._header is not None:
            if header is False:
                self._header.set_visibility(False)
            else:
                self._header.set_visibility(True)
                if isinstance(header, dict) and self._title_label is not None:
                    title = header.get("title")
                    if title:
                        self._title_label.set_text(str(title))

        if self._footer is not None:
            self._footer.set_visibility(footer is not False)

    def clear_body(self) -> None:
        """Remove all children from the body slot."""
        if self._body is not None:
            self._body.clear()
