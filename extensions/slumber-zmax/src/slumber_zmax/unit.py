"""ZMax unit plugin.

This module is intentionally minimal scaffolding. The full implementation will
wrap `somnio.devices.zmax.ZMax` and expose it as an ezmsg Unit registered under
the `slumber.units` entry-point group.
"""

from __future__ import annotations


class ZMax:  # TODO: subclass the appropriate ezmsg Unit base
    """Receive ZMax streams and publish into a SLUMBER DAG."""

    # TODO: implement unit + settings model
