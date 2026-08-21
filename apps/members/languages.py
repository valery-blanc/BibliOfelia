"""Langues parlées par les usagers (FEAT-065), adossées à la liste gérée.

**FEAT-070** : la liste des 22 langues n'est plus figée ici. Elle vit dans
`catalog.Language`, partagée avec la langue des documents, et se complète depuis
l'écran Avancé → Langues. Ce module n'est plus qu'un adaptateur : il donne aux
formulaires usagers la forme qu'ils attendent.

Les codes restent figés une fois écrits en base ; seuls les libellés sont
traduits, et les menus sont triés par libellé dans la langue de l'interface.
"""
from __future__ import annotations


def spoken_language_choices() -> list[tuple[str, object]]:
    """Choix pour les cases à cocher, triés par libellé traduit.

    Callable et non constante : la liste est modifiable en base, la figer à
    l'import rendrait invisible toute langue ajoutée depuis le démarrage.
    """
    from apps.catalog.languages import language_choices

    return language_choices(include_blank=False)


def labels_for(codes) -> list[str]:
    """Libellés traduits des `codes`, dans l'ordre alphabétique des libellés.

    Un code inconnu (import, ancienne saisie, langue supprimée de la liste) est
    restitué tel quel plutôt qu'escamoté : on ne perd jamais une donnée qu'on ne
    sait pas nommer.
    """
    from apps.catalog.models import Language

    selected = [c for c in (codes or []) if c]
    if not selected:
        return []
    known = {lang.code: str(lang) for lang in Language.objects.filter(code__in=selected)}
    labels = [known[code] for code in selected if code in known]
    labels.sort(key=str.lower)
    return labels + [str(code) for code in selected if code not in known]


def display(codes, other: str = "") -> str:
    """Langues d'une personne en une ligne : cochées puis champ libre."""
    parts = labels_for(codes)
    other = (other or "").strip()
    if other:
        parts.append(other)
    return ", ".join(parts)
