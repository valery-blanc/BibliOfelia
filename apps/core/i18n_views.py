"""Vue `set_language` durcie pour BibliOfelia.

BUG-013 (récurrent) : `django.views.i18n.set_language` redirige vers
`/<lang>/path/` sans préfixe `FORCE_SCRIPT_NAME`. En production, l'app est
montée sous `/bibliofelia/` derrière nginx ; sans préfixe, le navigateur sort
de l'app.

`translate_url` ajoute le préfixe **seulement si** la route cible se résout.
Quand l'URL courante ne matche aucune route (page renommée par un déploiement,
404, redirection intermédiaire), `translate_url` retourne l'URL inchangée :
le préfixe n'est jamais inséré et le bug se reproduit.

Ce wrapper rend la solution indépendante de la résolution : on force le
préfixe sur l'en-tête `Location` à la sortie, quelle que soit l'URL.
"""
from __future__ import annotations

import re

from django.conf import settings
from django.views.i18n import set_language as _django_set_language


def _swap_lang_code(path: str, new_lang: str) -> str:
    """Remplace `/<xx>/...` par `/<new_lang>/...` si `<xx>` est une langue activée."""
    enabled = {code for code, _ in settings.LANGUAGES}
    m = re.match(r"^/([a-z]{2,3})(/|$)", path)
    if not m or m.group(1) not in enabled:
        return path
    return f"/{new_lang}{m.group(2)}" + path[m.end():]


def set_language(request):
    response = _django_set_language(request)
    location = response.get("Location", "")
    if not location.startswith("/"):
        return response  # URL absolue, vide, ou pas de redirection

    # 1) Forcer le changement de code de langue même si translate_url n'a pas
    #    résolu la route (URL renommée, 404, page intermédiaire).
    new_lang = request.POST.get("language") if request.method == "POST" else None
    if new_lang:
        location = _swap_lang_code(location, new_lang)

    # 2) Forcer le préfixe FORCE_SCRIPT_NAME pour que la redirection reste
    #    dans l'app derrière nginx.
    prefix = (settings.FORCE_SCRIPT_NAME or "").rstrip("/")
    if prefix and location != prefix and not location.startswith(prefix + "/"):
        location = prefix + location

    response["Location"] = location
    return response
