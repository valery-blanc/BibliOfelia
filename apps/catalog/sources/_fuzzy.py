"""Score de confiance fuzzy local pour le catalogage Excel (FEAT-050, passe 2).

Les sources strictes (BNF, BNE) renvoient des candidats bruyants ; on réordonne
localement avec ``rapidfuzz`` pour ne garder que le meilleur appariement et lui
attribuer un score de confiance 0-100.
"""
from __future__ import annotations

from rapidfuzz import fuzz, utils

# Passe 2 : si le meilleur score est sous ce plancher, on n'écrit rien (trop
# incertain pour annoter l'Excel sans induire le bibliothécaire en erreur).
CONFIDENCE_FLOOR = 60
# Cellules CONFIDENCE colorées en orange dans l'Excel (signal de relecture).
HIGHLIGHT_BELOW = 75


def score(
    query_title: str,
    query_author: str,
    cand_title: str,
    cand_authors: str,
) -> int:
    """Score 0-100 entre la ligne saisie et un candidat source.

    ``utils.default_process`` met en minuscules, retire la ponctuation et les
    accents — comparaison robuste aux fautes de frappe et à la casse.
    """
    q = utils.default_process(f"{query_title or ''} | {query_author or ''}")
    c = utils.default_process(f"{cand_title or ''} | {cand_authors or ''}")
    if not q or not c:
        return 0
    return int(fuzz.WRatio(q, c))


def best_candidate(
    query_title: str,
    query_author: str,
    candidates: list[dict],
) -> tuple[dict | None, int]:
    """Renvoie ``(meilleur_candidat, score)`` ou ``(None, 0)`` si la liste est
    vide. Chaque candidat doit exposer ``title`` et ``authors_text``."""
    best: dict | None = None
    best_score = -1
    for cand in candidates:
        s = score(
            query_title,
            query_author,
            cand.get("title", ""),
            cand.get("authors_text", ""),
        )
        if s > best_score:
            best_score = s
            best = cand
    if best is None:
        return None, 0
    return best, max(0, best_score)
