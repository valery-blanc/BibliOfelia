"""Tags `{% icon %}` et `{% illus %}` : SVG locaux. SPEC §10.1.

Les icônes Lucide sont dans `static/icons/`. Les illustrations couleur OFELIA
(64×64 flat-vector) sont définies inline dans ce module.
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


# ────────── Illustrations multicolores OFELIA (64×64) ──────────
_ILLUS: dict[str, str] = {
    "home": (
        '<g>'
        '<rect x="4" y="52" width="56" height="4" rx="2" fill="#D1C360"/>'
        '<rect x="14" y="28" width="36" height="24" fill="#F3B84C"/>'
        '<path d="M6 30 L32 10 L58 30 Z" fill="#6B2138"/>'
        '<rect x="10" y="28" width="44" height="3" fill="#4E1829"/>'
        '<rect x="31" y="3" width="2" height="9" fill="#3D3530"/>'
        '<path d="M33 3 L44 6 L33 9 Z" fill="#3D8C5A"/>'
        '<path d="M27 52 L27 39 Q27 34 32 34 Q37 34 37 39 L37 52 Z" fill="#ED7538"/>'
        '<circle cx="34.5" cy="44" r="0.9" fill="#F3B84C"/>'
        '<rect x="17" y="34" width="8" height="8" rx="1" fill="#B7D9FF"/>'
        '<rect x="39" y="34" width="8" height="8" rx="1" fill="#B7D9FF"/>'
        '<path d="M21 34 V42 M17 38 H25 M43 34 V42 M39 38 H47" stroke="#fff" stroke-width="0.7"/>'
        '<rect x="44" y="46" width="10" height="6" rx="1" fill="#3D8C5A"/>'
        '<rect x="46" y="47" width="2" height="4" fill="#F3B84C"/>'
        '<rect x="49" y="47" width="2" height="4" fill="#F4BABA"/>'
        '</g>'
    ),
    "catalogue": (
        '<g>'
        '<rect x="4" y="44" width="56" height="12" rx="2" fill="#3D8C5A"/>'
        '<rect x="4" y="44" width="4" height="12" fill="#2E6B43"/>'
        '<rect x="10" y="46" width="48" height="8" fill="#F7F5F0"/>'
        '<rect x="10" y="46" width="48" height="2" fill="#EAE6DC"/>'
        '<rect x="8" y="28" width="48" height="14" rx="2" fill="#ED7538"/>'
        '<rect x="8" y="28" width="4" height="14" fill="#C4551C"/>'
        '<rect x="14" y="30" width="42" height="10" fill="#F7F5F0"/>'
        '<rect x="14" y="30" width="42" height="2" fill="#EAE6DC"/>'
        '<rect x="38" y="33" width="14" height="2" fill="#ED7538" opacity="0.5"/>'
        '<rect x="14" y="10" width="40" height="16" rx="2" fill="#6B2138"/>'
        '<rect x="50" y="10" width="4" height="16" fill="#4E1829"/>'
        '<rect x="18" y="14" width="2" height="8" fill="#F3B84C"/>'
        '<rect x="22" y="14" width="2" height="8" fill="#F3B84C"/>'
        '<circle cx="42" cy="18" r="3.4" fill="#F3B84C"/>'
        '<circle cx="42" cy="18" r="1.4" fill="#6B2138"/>'
        '</g>'
    ),
    "members": (
        '<g>'
        '<path d="M30 62 Q30 42 46 42 Q62 42 62 62 Z" fill="#B7D9FF"/>'
        '<circle cx="46" cy="30" r="10" fill="#9C6A3A"/>'
        '<ellipse cx="46" cy="25" rx="10" ry="7" fill="#3D3530"/>'
        '<path d="M2 60 Q2 42 16 42 Q30 42 30 60 Z" fill="#F3B84C"/>'
        '<circle cx="16" cy="32" r="9" fill="#F4BABA"/>'
        '<path d="M7 30 Q16 18 25 30 V34 H7 Z" fill="#7A4626"/>'
        '<path d="M14 64 Q14 42 32 42 Q50 42 50 64 Z" fill="#6B2138"/>'
        '<circle cx="32" cy="30" r="11" fill="#C99068"/>'
        '<path d="M21 27 Q32 13 43 27 V32 H21 Z" fill="#1F1A14"/>'
        '<rect x="25" y="44" width="14" height="9" rx="1" fill="#fff"/>'
        '<path d="M32 44 V53" stroke="#9A9088" stroke-width="0.6"/>'
        '<rect x="26" y="46" width="5" height="0.7" fill="#9A9088"/>'
        '<rect x="33" y="46" width="5" height="0.7" fill="#9A9088"/>'
        '<rect x="26" y="48" width="5" height="0.7" fill="#9A9088"/>'
        '<rect x="33" y="48" width="5" height="0.7" fill="#9A9088"/>'
        '</g>'
    ),
    "lending": (
        '<g>'
        '<rect x="6" y="20" width="34" height="26" rx="2.5" fill="#ED7538"/>'
        '<rect x="6" y="20" width="6" height="26" fill="#6B2138"/>'
        '<rect x="14" y="24" width="24" height="3" fill="#F3B84C"/>'
        '<rect x="14" y="29" width="20" height="1.6" fill="#fff" opacity="0.7"/>'
        '<rect x="14" y="32.5" width="22" height="1.6" fill="#fff" opacity="0.7"/>'
        '<rect x="14" y="36" width="16" height="1.6" fill="#fff" opacity="0.7"/>'
        '<path d="M44 28 L44 38 L52 38 L52 42 L62 33 L52 24 L52 28 Z" fill="#3D8C5A"/>'
        '<path d="M50 12 l1.2 3 3 1.2 -3 1.2 -1.2 3 -1.2-3 -3-1.2 3-1.2 z" fill="#F3B84C"/>'
        '<circle cx="56" cy="50" r="1.4" fill="#F4BABA"/>'
        '</g>'
    ),
    "return": (
        '<g>'
        '<path d="M40 14 L20 14 Q8 14 8 26 L8 36" stroke="#ED7538" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
        '<path d="M8 38 L2 30 M8 38 L14 30" stroke="#ED7538" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
        '<rect x="24" y="24" width="34" height="26" rx="2.5" fill="#3D8C5A"/>'
        '<rect x="24" y="24" width="6" height="26" fill="#2E6B43"/>'
        '<rect x="32" y="28" width="24" height="3" fill="#F3B84C"/>'
        '<rect x="32" y="33" width="20" height="1.6" fill="#fff" opacity="0.7"/>'
        '<rect x="32" y="36.5" width="22" height="1.6" fill="#fff" opacity="0.7"/>'
        '<rect x="32" y="40" width="16" height="1.6" fill="#fff" opacity="0.7"/>'
        '</g>'
    ),
    "reserve": (
        '<g>'
        '<rect x="14" y="8" width="36" height="50" rx="2" fill="#F4BABA"/>'
        '<rect x="14" y="8" width="5" height="50" fill="#D47878"/>'
        '<rect x="22" y="20" width="22" height="2" fill="#fff" opacity="0.6"/>'
        '<rect x="22" y="26" width="24" height="2" fill="#fff" opacity="0.6"/>'
        '<rect x="22" y="32" width="18" height="2" fill="#fff" opacity="0.6"/>'
        '<rect x="22" y="38" width="22" height="2" fill="#fff" opacity="0.6"/>'
        '<rect x="22" y="44" width="14" height="2" fill="#fff" opacity="0.6"/>'
        '<path d="M34 8 L34 30 L40 25 L46 30 L46 8 Z" fill="#6B2138"/>'
        '<path d="M50 6 l2 5 5.2 .6 -3.9 3.5 1 5.2 -4.4-2.6 -4.4 2.6 1-5.2 -3.9-3.5 5.2-.6 z" fill="#F3B84C"/>'
        '</g>'
    ),
    "advanced": (
        '<g>'
        '<g transform="translate(40 38)">'
        '<g fill="#6B2138">'
        '<rect x="-3" y="-22" width="6" height="7"/>'
        '<rect x="-3" y="15" width="6" height="7"/>'
        '<rect x="-22" y="-3" width="7" height="6"/>'
        '<rect x="15" y="-3" width="7" height="6"/>'
        '<rect x="-3" y="-22" width="6" height="7" transform="rotate(45)"/>'
        '<rect x="-3" y="15" width="6" height="7" transform="rotate(45)"/>'
        '<rect x="-22" y="-3" width="7" height="6" transform="rotate(45)"/>'
        '<rect x="15" y="-3" width="7" height="6" transform="rotate(45)"/>'
        '</g>'
        '<circle r="16" fill="#6B2138"/>'
        '<circle r="6" fill="#F7F5F0"/>'
        '</g>'
        '<g transform="translate(16 18)">'
        '<g fill="#F3B84C">'
        '<rect x="-2" y="-13" width="4" height="4.5"/>'
        '<rect x="-2" y="8.5" width="4" height="4.5"/>'
        '<rect x="-13" y="-2" width="4.5" height="4"/>'
        '<rect x="8.5" y="-2" width="4.5" height="4"/>'
        '<rect x="-2" y="-13" width="4" height="4.5" transform="rotate(45)"/>'
        '<rect x="-2" y="8.5" width="4" height="4.5" transform="rotate(45)"/>'
        '<rect x="-13" y="-2" width="4.5" height="4" transform="rotate(45)"/>'
        '<rect x="8.5" y="-2" width="4.5" height="4" transform="rotate(45)"/>'
        '</g>'
        '<circle r="10" fill="#F3B84C"/>'
        '<circle r="3.5" fill="#F7F5F0"/>'
        '</g>'
        '<g transform="translate(8 50) rotate(-35)">'
        '<rect x="0" y="-2" width="22" height="4" rx="1.5" fill="#3D8C5A"/>'
        '<path d="M22 -3.5 L26 -3 L27 0 L26 3 L22 3.5 Z" fill="#3D8C5A"/>'
        '<circle cx="24" cy="0" r="1.4" fill="#F7F5F0"/>'
        '</g>'
        '</g>'
    ),
}


@register.simple_tag
def illus(name: str, css_class: str = "") -> str:
    """Illustration multicolore OFELIA 64×64 inline."""
    inner = _ILLUS.get(name, "")
    if not inner:
        return ""
    classes = "illus"
    if css_class:
        classes += f" {escape(css_class)}"
    return mark_safe(  # noqa: S308 — SVG maîtrisé, défini dans ce module
        f'<svg class="{classes}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" '
        f'aria-hidden="true" focusable="false">{inner}</svg>'
    )
