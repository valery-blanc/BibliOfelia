# BUG-013 — Sélecteur de langue cassé en prod (FORCE_SCRIPT_NAME)

**Status :** FIXED (v2 pérenne — 2026-05-26)
**Date :** 2026-05-24 (v1 partiel) → 2026-05-26 (v2 pérenne, Sprint 12)
**Sprint :** 9 (hotfix v1) → 12 (fix pérenne v2)
**Spec section :** SPEC §6.9 (i18n)

---

## Symptôme

En production (derrière nginx avec `FORCE_SCRIPT_NAME=/bibliofelia`), le
sélecteur de langue dans la topbar ne changeait pas la langue : la page se
rechargeait dans la même langue. Tapez `/es/` directement dans l'URL
fonctionnait (passait par le middleware locale).

## Cause racine

Le formulaire dans `templates/base.html` envoyait :

```html
<input type="hidden" name="next" value="{{ request.path }}">
```

`request.path` retourne le path **avec** le préfixe `SCRIPT_NAME`
(`/bibliofelia/fr/loans/lend/`).

Côté Django, la vue `set_language` appelle ensuite
`translate_url(next, lang_code)`. Cette fonction fait `resolve(next.path)`,
ne reconnaît pas le préfixe `/bibliofelia/` (pas dans les URL patterns),
attrape `Resolver404`, et **retourne l'URL inchangée**. Conséquence :
redirect vers `/bibliofelia/fr/...` → toujours FR.

## Diagnostic en shell Django (Pi) :

```
translate_url('/fr/loans/lend/', 'en') = '/bibliofelia/en/loans/lend/'  # OK
translate_url('/bibliofelia/fr/loans/lend/', 'en') = '/bibliofelia/fr/loans/lend/'  # KO
```

## Fix

Utiliser `{{ request.path_info }}` au lieu de `{{ request.path }}` —
`path_info` est le chemin **sans** `SCRIPT_NAME`, donc reconnu par
`resolve()` :

```html
<input type="hidden" name="next" value="{{ request.path_info }}">
```

Modifié dans :
- `templates/base.html`
- `templates/accounts/login.html`

## Validation

Test curl à travers nginx (sur la Pi) :
```
POST /bibliofelia/i18n/setlang/ language=en next=/fr/accounts/login/
→ 302 Location: /bibliofelia/en/accounts/login/   # OK
```

## Bug satellite : commentaire Django multi-ligne

Le commentaire `{# ... #}` ajouté à côté du fix s'étalait sur 2 lignes →
Django ne supporte **pas** le multi-ligne pour `{# #}` (doc :
[ref/templates/builtins#comment](https://docs.djangoproject.com/en/5.1/ref/templates/builtins/#comment)). Conséquence : la 2e ligne du commentaire
s'affichait comme texte brut dans la topbar.

Fix : commentaire ramené sur une seule ligne, ou bien utiliser
`{% comment %}...{% endcomment %}` pour du multi-ligne.

---

## Régression v2 (2026-05-26, Sprint 12) — fix pérenne

### Symptôme

Bug réapparu : à chaque déploiement, certaines pages perdent encore le
préfixe `/bibliofelia/` au changement de langue.

### Cause racine v2

Le fix v1 dépendait de `translate_url(next, lang)`. Cette fonction :
1. appelle `resolve(next)` pour trouver la vue ;
2. appelle `reverse(view, urlconf, args, kwargs)` qui **utilise le
   `script_prefix` courant** → URL avec préfixe ;
3. **si `resolve` lève `Resolver404`** (URL inconnue, page renommée par un
   déploiement, redirection intermédiaire, 404) → `translate_url` renvoie
   l'URL **inchangée**, donc sans préfixe.

À ce moment-là, `set_language` redirige vers `/fr/page-inconnue/` ; le
navigateur sort de l'app (nginx ne route plus `/bibliofelia/`).

Reproduction shell sur la Pi :
```python
translate_url('/fr/dashboard/', 'en')  # /fr/dashboard/  — pas de route nommée 'dashboard/'
translate_url('/fr/', 'en')            # /bibliofelia/en/  — OK
translate_url('/fr/page-inconnue/', 'en')  # /fr/page-inconnue/  — KO
```

### Fix v2 (pérenne)

Wrapper autour de `django.views.i18n.set_language` qui force le préfixe
`FORCE_SCRIPT_NAME` sur l'en-tête `Location` de la redirection, **quelle que
soit** la résolution. Indépendant des templates et des routes.

```python
# apps/core/i18n_views.py
from django.conf import settings
from django.views.i18n import set_language as _django_set_language

def set_language(request):
    response = _django_set_language(request)
    prefix = (settings.FORCE_SCRIPT_NAME or "").rstrip("/")
    if not prefix or "Location" not in response:
        return response
    location = response["Location"]
    if not location.startswith("/"):
        return response
    if location == prefix or location.startswith(prefix + "/"):
        return response  # déjà préfixée
    response["Location"] = prefix + location
    return response
```

Câblage dans `config/urls.py` : on remplace
`path("i18n/", include("django.conf.urls.i18n"))` par notre route nommée :

```python
from apps.core.i18n_views import set_language as core_set_language

urlpatterns = [
    ...
    path("i18n/setlang/", core_set_language, name="set_language"),
    ...
]
```

`{% url 'set_language' %}` continue à fonctionner — c'est le même nom.

### Tests

`apps/core/tests/test_i18n_setlang.py` couvre :
- URL inconnue → préfixe forcé
- URL connue → pas de double préfixe
- Sans `FORCE_SCRIPT_NAME` (dev) → comportement Django standard
- Reverse du nom continue à fonctionner
