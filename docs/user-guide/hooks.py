"""Filtre Jinja : liens de langue relatifs, pour un guide monté sous un préfixe."""
from __future__ import annotations

import sys
from pathlib import Path

from jinja2 import pass_context

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relative_url import relative_href  # noqa: E402


def on_env(env, config, files):
    @pass_context
    def rel_alt(context, href):
        page = context.get("page")
        page_url = getattr(page, "url", "") if page is not None else ""
        return relative_href(href or "", page_url)

    env.filters["rel_alt"] = rel_alt
    return env
