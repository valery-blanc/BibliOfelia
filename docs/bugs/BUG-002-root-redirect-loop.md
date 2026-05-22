# BUG-002 — Boucle de redirection sur la racine `/`

**Statut** : FIXED
**Date** : 2026-05-21
**Sprint** : 2 (Task #5, découvert en câblant le layout UI)

## Symptôme

Une fois le wizard d'installation marqué terminé (`Setting setup_completed = True`),
ouvrir la racine `/` provoque une boucle de redirection HTTP infinie
(`ERR_TOO_MANY_REDIRECTS`). L'application est alors inaccessible.

Le bug était masqué tant que `setup_completed` valait `False` : le
`SetupRequiredMiddleware` redirige alors `/` vers `/setup/` avant que la boucle
ne s'exprime.

## Cause racine

`config/urls.py` préfixait les URL avec :

```python
urlpatterns = [path("", RedirectView.as_view(pattern_name="core:dashboard"))] + urlpatterns
```

Or `core:dashboard` est déjà servi à la racine via `i18n_patterns(...,
prefix_default_language=False)` : `reverse("core:dashboard")` rend `/`. Le
`RedirectView` placé sur `path("")` redirige donc `/` vers `/`, indéfiniment.

## Fix

Suppression du `RedirectView` et de son import dans `config/urls.py`. La racine
`/` est servie directement par `apps.core.urls` (dashboard) via `i18n_patterns`.

## Section spec impactée

§4.3 (routage) — aucun changement de comportement attendu, juste suppression
d'une redirection redondante et fautive. Pas d'incrément de version spec.
