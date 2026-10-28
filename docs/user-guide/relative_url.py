"""Liens de langue du guide, relatifs à la page courante.

Le même site statique est servi à la racine (`docs.bibliofelia.org`) et sous
un préfixe (`/docs/` sur une instance, `/bibliofelia/docs/` sur la Box).
MkDocs rend les liens de la page d'accueil en absolu (`/en/`). Depuis
`https://sanjuan.bibliofelia.org/docs/`, ce lien sort du guide et ouvre
l'application. Un lien relatif (`en/`) reste dans le préfixe, quel qu'il soit.
"""
from __future__ import annotations


def relative_href(href: str, page_url: str | None) -> str:
    """Rend `href` relatif à `page_url` quand il part de la racine du site.

    Les liens déjà relatifs (ceux des pages intérieures) sont laissés tels quels.
    `page_url` est le chemin MkDocs de la page (`""`, `"en/"`,
    `"premiers-pas/connexion/"`).
    """
    if not href or not href.startswith("/"):
        return href
    target = href[1:]
    current = page_url or ""
    if current in {".", "index.html"}:
        current = ""
    cur = [part for part in current.strip("/").split("/") if part]
    tgt = [part for part in target.strip("/").split("/") if part]
    shared = 0
    while shared < len(cur) and shared < len(tgt) and cur[shared] == tgt[shared]:
        shared += 1
    up = len(cur) - shared
    down = tgt[shared:]
    if up == 0 and not down:
        return "./"
    rel = "/".join([".."] * up + down)
    if href.endswith("/") or target == "":
        if not rel.endswith("/"):
            rel += "/"
    return rel
