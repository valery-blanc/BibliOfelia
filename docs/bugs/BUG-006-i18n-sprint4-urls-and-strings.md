# BUG-006 — i18n cassée sur les URLs Sprint 4 + chaînes non traduites

Statut : FIXED (2026-05-22)
Signalé par : Val (test fonctionnel Sprint 4)

## Symptômes

1. `http://localhost:8001/fr/accounts/users/` → **404** (alors que
   `/accounts/users/` répond).
2. Quelle que soit la langue choisie via le sélecteur, l'UI Sprint 4
   reste en français.

## Cause racine

### Symptôme 1 — 404 sur `/fr/accounts/users/`

Dans `config/urls.py`, l'include `apps.accounts.urls` était placé **hors**
`i18n_patterns(...)` (héritage des routes login/logout natives Django).
Du coup les nouvelles routes user CRUD ajoutées par FEAT-011
(`accounts:user_list`, `user_create`, `user_edit`, `user_password_reset`)
n'avaient pas de préfixe de langue.

### Symptôme 2 — Pas de traduction

Les nouveaux templates Sprint 4 contenaient ~150 nouvelles chaînes
`{% trans %}` / `gettext_lazy` non extraites dans les `.po`, et les
fichiers `.mo` n'étaient pas régénérés. `makemessages` indiquait au
final pour `en/es/mg` : **120 untranslated + 74 fuzzy**.

## Fix

### 1. URLs

`config/urls.py` : déplacer `accounts/` **sous** `i18n_patterns`
(login/logout incluses). Le `LocaleMiddleware` redirige automatiquement
`/accounts/login/` → `/<lang>/accounts/login/`. L'attribut
`prefix_default_language=True` (BUG-005) garde le préfixe `/fr/`
explicite pour la langue par défaut.

### 2. Traductions

- `python manage.py makemessages -a` pour extraire les nouvelles chaînes.
- Script one-shot `scripts/patch_translations.py` (supprimé après usage)
  appliquant un dictionnaire FR → EN/ES/MG sur ~215 entrées (Sprint 4 +
  fuzzy restants du Sprint 2). Bug corrigé en cours de route :
  `_join` faisait `.encode('utf-8').decode('unicode_escape')` qui
  casse l'UTF-8 (`é` → `Ã©`) ; remplacé par une désérialisation des
  seuls échappements ASCII (`\\n`, `\\t`, `\\"`, `\\\\`).
- Patch manuel des deux plurals fuzzy (`%(count)s prêt en retard.` et
  `%(count)s réservation à retirer.`) — mon script ne gérait pas les
  `msgstr[0]/msgstr[1]`.
- `python manage.py compilemessages` final.

État après fix : **503 traduit / 0 fuzzy / 0 untranslated** par locale
(`en/es/mg`). `fr` reste à 0 traduit (normal : c'est la langue source,
Django renvoie `msgid` quand `msgstr` est vide).

Le malgache reste une première passe à faire relire par un locuteur
natif (cf. SPEC §6.9, déjà noté pour BUG-005).

## Vérification

- `manage.py check` : 0 issue.
- pytest : 139 passed (aucune régression).
- `/fr/accounts/users/` → 200 ; bascule langue via sélecteur → l'UI
  Sprint 4 (dashboard, paramètres, rapports, comptes, impression,
  setup completed) s'affiche traduite.

## Suivi

Ce bug fait partie du commit groupé Sprint 4 (pas de commit séparé) —
trouvé pendant le test de Val, corrigé avant validation finale.
