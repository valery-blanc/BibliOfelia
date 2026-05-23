# BUG-011 — `scan-handoff` POST échoue silencieusement (CSRF token)

Statut : **FIXED** (2026-05-23)
Sévérité : haute (FEAT-023 inopérante en production)
Section spec : §6.10 « Handoff single-scan »

## Symptôme

Val (logué en superadmin sur la Pi) clique sur un bouton « Scanner » →
**rien ne se passe**. OfeliaScan n'est pas appelée, aucun message d'erreur
visible. Le bouton reprend son état normal sans avoir tenté le deep-link.

## Reproduction

1. Login en superadmin/librarian sur `http://192.168.0.147/bibliofelia/`.
2. Clic sur « Scanner un livre » dans `/loans/lend/`.
3. Le bouton clignote brièvement « En attente d'OfeliaScan… » puis
   redevient cliquable.
4. Console navigateur : silencieuse (avant le fix), pas d'indication
   visuelle utile pour l'utilisateur.

## Cause racine

`CSRF_COOKIE_HTTPONLY = True` dans `config/settings/base.py` (ligne 168)
empêche tout JS de lire le cookie `csrftoken`. La fonction
`getCookie('csrftoken')` du `scan-handoff.js` initial renvoyait donc une
chaîne vide → le header `X-CSRFToken` du `POST /api/v1/scan-handoff` était
absent → `SessionAuthentication` (DRF) refusait avec `403 CSRF Failed`.

Les tests Pytest ne l'ont pas attrapé car `APIClient.force_authenticate()`
**désactive CSRF**. Bug invisible en CI, révélé au premier clic prod.

C'est exactement le même problème que pour HTMX, déjà traité dans
`templates/base.html` ligne 12 par
`hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'`.

## Fix

Aligner `scan-handoff.js` sur le pattern HTMX : **lire le token rendu par
le template**, pas le cookie.

1. `templates/base.html` : injecter `csrf_token` dans la config JSON
   chargée par le JS.
   ```html
   <script id="scan-handoff-config" type="application/json">
   {"createUrl": "{% url 'api:scan-handoff-create' %}", "csrfToken": "{{ csrf_token }}"}
   </script>
   ```
2. `static/js/scan-handoff.js` : remplacer `getCookie('csrftoken')` par
   `cfg.csrfToken` dans `jsonHeaders()`. Suppression de la fonction
   `getCookie` devenue inutile.
3. Logs console.error + message d'erreur enrichi (status code, message)
   pour diagnostiquer plus vite si un futur problème CSRF/auth survient.

## Pourquoi ne pas baisser `CSRF_COOKIE_HTTPONLY` ?

Garder le cookie HttpOnly est une bonne pratique défense en profondeur
(XSS ne peut pas exfiltrer le token). Le template rendu côté serveur
fournit la même valeur, sans exposer le cookie au JS. La SPEC §9 conserve
le réglage.

## Doc

- `SPEC §6.10 « Handoff single-scan »` : précision CSRF via `csrf_token`
  template tag (et non cookie).
- `docs/specs/FEAT-023-scan-handoff-ofeliascan.md` : section « CSRF »
  mise à jour.
- `TASKS.md` : entrée BUG-011 sous Sprint 7.
