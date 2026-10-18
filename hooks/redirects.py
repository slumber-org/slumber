"""Emit stable external redirect pages after the MkDocs build.

Destinations are configured in ``mkdocs.yml`` under ``extra.redirects``.
Public paths stay fixed (``/survey/``, ``/updates/``); only the YAML values change.
"""

from __future__ import annotations

import html
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("mkdocs.hooks.redirects")

_REDIRECT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex, nofollow">
  <meta http-equiv="refresh" content="0; url={url_attr}">
  <link rel="canonical" href="{url_attr}">
  <title>{title_escaped}</title>
  <script>window.location.replace({url_js});</script>
</head>
<body>
  <p>{title_escaped}: <a href="{url_attr}">{url_escaped}</a></p>
  <p>If you are not redirected automatically, use the link above.</p>
</body>
</html>
"""

_TITLES = {
    "survey": "Researcher questionnaire",
    "updates": "Project updates signup",
}


def on_post_build(config: dict[str, Any], **kwargs: Any) -> None:
    """Write redirect HTML pages into the built site directory."""
    redirects = (config.get("extra") or {}).get("redirects") or {}
    if not redirects:
        logger.warning("No extra.redirects configured; skipping redirects")
        return

    site_dir = Path(config["site_dir"])
    for slug, destination in redirects.items():
        if not isinstance(destination, str) or not destination.startswith(
            ("http://", "https://")
        ):
            raise ValueError(
                f"redirects[{slug!r}] must be an absolute http(s) URL, "
                f"got: {destination!r}"
            )

        page_dir = site_dir / str(slug)
        page_dir.mkdir(parents=True, exist_ok=True)
        title = _TITLES.get(str(slug), str(slug).replace("-", " ").title())
        content = _REDIRECT_TEMPLATE.format(
            title_escaped=html.escape(title),
            url_attr=html.escape(destination, quote=True),
            url_escaped=html.escape(destination),
            url_js=json.dumps(destination),
        )
        (page_dir / "index.html").write_text(content, encoding="utf-8")
        logger.info("Redirect: /%s/ -> %s", slug, destination)
