"""FEAT-095 — lecture des emplacements cochés dans un filtre de recherche."""
from __future__ import annotations


def selected_location_ids(params) -> list[int]:
    """Ids d'emplacements demandés. Vide = pas de filtre (« Tous emplacements »).

    Accepte l'id numérique (`?location=3&location=7`) et, pour les signets
    d'impression antérieurs à FEAT-095, le code (`?location=A1`).
    """
    if hasattr(params, "getlist"):
        raw = [v for v in params.getlist("location") if v not in ("", None)]
    else:
        value = params.get("location") if params else None
        if not value:
            raw = []
        elif isinstance(value, (list, tuple)):
            raw = [v for v in value if v not in ("", None)]
        else:
            raw = [value]
    if not raw:
        return []
    ids: list[int] = []
    codes: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text.isdigit():
            ids.append(int(text))
        else:
            codes.append(text)
    if codes:
        from .models import Location

        ids.extend(
            Location.objects.filter(code__in=codes).values_list("pk", flat=True)
        )
    seen: set[int] = set()
    unique: list[int] = []
    for pk in ids:
        if pk not in seen:
            seen.add(pk)
            unique.append(pk)
    return unique
