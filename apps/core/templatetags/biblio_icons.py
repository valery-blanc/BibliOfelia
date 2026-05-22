"""Tag `{% icon "name" %}` : inline un SVG Lucide local. SPEC §10.1.

Les SVG sont stockés dans `static/icons/` (téléchargés depuis lucide-static,
contrainte hors-ligne : aucun CDN). Le contenu interne est mis en cache.
"""
from __future__ import annotations

import re
from functools import lru_cache

from django import template
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

_ICON_DIR = settings.BASE_DIR / "static" / "icons"
_INNER_RE = re.compile(r"<svg[^>]*>(.*)</svg>", re.DOTALL)


@lru_cache(maxsize=256)
def icon_inner(name: str) -> str:
    """Retourne le contenu interne (paths) d'un SVG Lucide, ou '' si absent."""
    if not name or "/" in name or "\\" in name:
        return ""
    path = _ICON_DIR / f"{name}.svg"
    if not path.is_file():
        return ""
    match = _INNER_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else ""


@register.simple_tag
def icon(name: str, css_class: str = "", size: str = "1em") -> str:
    inner = icon_inner(name)
    if not inner:
        return ""
    classes = f"icon icon-{escape(str(name))}"
    if css_class:
        classes += f" {escape(css_class)}"
    return mark_safe(  # noqa: S308 — contenu SVG local maîtrisé
        f'<svg class="{classes}" width="{escape(size)}" height="{escape(size)}" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
        f'focusable="false">{inner}</svg>'
    )
