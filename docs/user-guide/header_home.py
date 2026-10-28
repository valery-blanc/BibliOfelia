"""Où l'icône OFELIA du guide doit mener.

Le même HTML est servi à trois endroits :

- ``/docs/…`` sur une instance (San Juan, Grand-Saconnex)
- ``/bibliofelia/docs/…`` sur la Box
- à la racine de ``docs.bibliofelia.org``

L'accueil du guide est déjà le lien relatif du logo Material. L'application,
elle, dépend du préfixe : on la déduit du chemin au chargement. Le français
du guide n'a pas de segment ``fr`` ; l'application, si (``/fr/``).
"""

PUBLIC_HOME = "https://bibliofelia.org/"
LANGS = frozenset({"en", "es", "mg"})


def app_href(pathname: str) -> str:
    parts = pathname.split("/")
    try:
        docs_at = parts.index("docs")
    except ValueError:
        return PUBLIC_HOME
    prefix = [part for part in parts[1:docs_at] if part]
    rest = [part for part in parts[docs_at + 1 :] if part]
    lang = rest[0] if rest and rest[0] in LANGS else "fr"
    head = "/" + "/".join(prefix) if prefix else ""
    return f"{head}/{lang}/"
