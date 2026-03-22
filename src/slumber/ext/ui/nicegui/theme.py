"""Color palette and theming constants for the NiceGUI UI.

These colors match the docs palette in ``docs/stylesheets/extra.css``
and are derived from the SLUMBER logo (indigo moon + amber EEG traces).

Palette
-------
Indigo family (moon shades, sleep state):
    INDIGO_LIGHT    #7B7FC4  — light lavender, top of moon / sleep accent
    INDIGO          #3D4A8A  — primary brand, deep moon body
    INDIGO_DARK     #2A2F52  — dark indigo, borders and secondary surfaces

Amber family (EEG traces, awake state):
    AMBER           #E8A45A  — warm amber, EEG traces / awake accent

Surfaces (dark theme):
    SURFACE_DARK    #121528  — deepest background
    SURFACE         #151833  — page background
    SURFACE_MID     #1A1F3C  — cards and panels
    SURFACE_LIGHT   #2A2F52  — borders and dividers

Text:
    TEXT_PRIMARY     #FFFFFE  — main body text
    TEXT_SECONDARY   #94A1B2  — subdued / helper text

Status:
    POSITIVE         #34D399  — success / completed
    NEGATIVE         #F87171  — error / destructive
"""

from __future__ import annotations


INDIGO_LIGHT = "#7B7FC4"
INDIGO = "#3D4A8A"
INDIGO_DARK = "#2A2F52"
AMBER = "#E8A45A"

SURFACE_DARK = "#121528"
SURFACE = "#151833"
SURFACE_MID = "#1A1F3C"
SURFACE_LIGHT = "#2A2F52"

TEXT_PRIMARY = "#FFFFFE"
TEXT_SECONDARY = "#94A1B2"

POSITIVE = "#34D399"
NEGATIVE = "#F87171"

COLORS = {
    "primary": INDIGO,
    "secondary": INDIGO_DARK,
    "accent": AMBER,
    "dark": SURFACE_DARK,
    "dark-page": SURFACE,
    "positive": POSITIVE,
    "negative": NEGATIVE,
    "info": INDIGO_LIGHT,
    "warning": AMBER,
}

PRIMARY = INDIGO
SLEEP_INDIGO = INDIGO_LIGHT
AWAKE_AMBER = AMBER
ACCENT_LAVENDER = INDIGO_LIGHT
