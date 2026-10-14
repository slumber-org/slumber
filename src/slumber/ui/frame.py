"""AppFrame: header, body, and footer chrome for a GUI run."""

from __future__ import annotations

from typing import Any

from slumber.ui.theme import POWERED_BY, add_component_css
from slumber.ui.widgets import logo_mark

FRAME_CSS = """
.slumber-frame {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  background: var(--slumber-page-bg);
  color: var(--slumber-text);
  font-size: var(--slumber-fs);
  line-height: 1.5;
}
.slumber-frame-header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  height: var(--slumber-header-h);
  flex-shrink: 0;
  padding: 0 var(--slumber-pad);
  background: var(--slumber-surface);
}
.slumber-frame-header-start { display: flex; align-items: center; gap: 12px; min-width: 0; }
.slumber-frame-logo { display: flex; flex-shrink: 0; }
.slumber-frame-study, .slumber-frame-phase {
  min-width: 0;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.slumber-frame-study { font-size: 1.1em; }
.slumber-frame-phase { max-width: 40vw; color: var(--slumber-secondary); }
.slumber-frame-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
}
.slumber-frame-footer {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
  padding: 8px var(--slumber-pad);
}
.slumber-frame-caption { font-size: 12px; color: var(--slumber-secondary); opacity: 0.75; }
@media (max-width: 799px) {
  .slumber-frame-phase { max-width: 30vw; }
}
"""


class AppFrame:
    """One frame per run: header, body slot, and footer.

    The header holds the logo, the study title and an optional phase title. Mounted
    once; on every phase start :meth:`apply_frame` applies the study frame
    merged with the phase override (e.g. hide the header and footer during sleep).
    The look comes from the theme's ``.slumber-frame`` classes.
    """

    def __init__(
        self,
        *,
        study_name: str,
        logo_url: str | None = None,
    ) -> None:
        self._study_name = study_name
        self._logo_url = logo_url
        # TODO: [refactor] type NiceGUI slots via TYPE_CHECKING (Element / Label), like
        # widgets/buttons.py — keep runtime imports lazy for optional nicegui.
        self._header: Any | None = None
        self._logo_slot: Any | None = None
        self._title_label: Any | None = None
        self._phase_label: Any | None = None
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

        add_component_css(FRAME_CSS)
        with ui.element("div").classes("slumber-frame"):
            self._header = ui.element("header").classes("slumber-frame-header")
            with self._header:
                with ui.element("div").classes("slumber-frame-header-start"):
                    self._logo_slot = ui.element("div").classes("slumber-frame-logo")
                    with self._logo_slot:
                        logo_mark(self._logo_url, size="header")
                    self._title_label = ui.label().classes("slumber-frame-study")
                self._phase_label = ui.label().classes("slumber-frame-phase")
                # Empty third column so the phase title stays centred.
                ui.element("div")
            self._body = ui.element("main").classes("slumber-frame-body")
            self._footer = ui.element("footer").classes("slumber-frame-footer")
            with self._footer:
                ui.label(POWERED_BY).classes("slumber-frame-caption")

        self._mounted = True
        _set_truncated_text(self._title_label, self._study_name)

    def apply_frame(
        self,
        frame: dict[str, Any],
        *,
        phase_title: str | None = None,
        logo_url: str | None = None,
    ) -> None:
        """Show or hide chrome and update the header from merged settings.

        Args:
            frame: Merged study + phase frame. ``header: false`` or
                ``footer: false`` hides that region; a header dict may set
                ``title`` and ``show_phase_title``.
            phase_title: Title of the active phase, shown when
                ``show_phase_title`` is true.
            logo_url: Served URL of the header logo; ``None`` keeps the
                current logo.
        """
        if not self._mounted:
            raise RuntimeError("AppFrame.mount() must be called first.")

        header = frame.get("header")
        header_settings = header if isinstance(header, dict) else {}
        self._header.set_visibility(header is not False)
        _set_truncated_text(
            self._title_label, str(header_settings.get("title") or self._study_name)
        )
        show_phase_title = bool(header_settings.get("show_phase_title"))
        _set_truncated_text(
            self._phase_label, phase_title if show_phase_title and phase_title else ""
        )
        if logo_url is not None and logo_url != self._logo_url:
            self._logo_url = logo_url
            self._logo_slot.clear()
            with self._logo_slot:
                logo_mark(logo_url, size="header")
        self._footer.set_visibility(frame.get("footer") is not False)

    def clear_body(self) -> None:
        """Remove all children from the body slot."""
        if self._body is not None:
            self._body.clear()


def _set_truncated_text(label: Any, text: str) -> None:
    """Set a label that may be cut off with an ellipsis; hovering shows the full text."""
    label.set_text(text)
    label.props["title"] = text
