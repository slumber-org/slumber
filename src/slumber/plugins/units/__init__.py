"""Helpers for writing `slumber.units` plugins.

The `slumber.units` entry-point group maps a string key (unit_type) to a
callable that accepts `settings` (a dict or None) and returns an ezmsg Unit
instance.
"""

from slumber.plugins.units.utils import Settings, build_unit_from_settings

__all__ = ["Settings", "build_unit_from_settings"]
