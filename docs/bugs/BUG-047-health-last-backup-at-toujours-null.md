# BUG-047 — `/health` renvoie toujours `last_backup_at: null`

**Status:** FIXED
**Date:** 2026-09-10
**Origine:** revue croisée BibliOfelia ⇄ keebee (dépôt `_review-ofelia`)

## Symptôme

`GET /bibliofelia/api/v1/health` renvoie `"last_backup_at": null` en
permanence — y compris juste après une sauvegarde réussie.

## Cause

`apps/api/views.py::HealthView` lisait `Setting.get("last_backup_at")`.
**Rien n'écrit jamais cette clé.** L'unique écrivain,
`apps/tasks/backup.py::_persist`, enregistre sous la clé **`last_backup`**, et y
range un dictionnaire `{at, status, db_path, size_bytes, …}`.

`apps/reports/services.py` utilise déjà le bon motif
(`Setting.get("last_backup", {}) or {}` puis `.get("at")`) : les deux lectures
du même fait avaient divergé.

Conséquence : tout moniteur externe qui interroge `/health` — c'est le rôle que
lui donne §6.10 — conclut que la Box n'a **jamais** sauvegardé et ne peut donc
jamais alerter sur une sauvegarde qui vieillit. Cumulé à
[BUG-045](BUG-045-entrypoint-prod-sans-roles-ni-planifications.md), où les
sauvegardes ne tournaient effectivement pas, la panne était complètement
invisible de l'extérieur.

## Correctif

`HealthView` lit `Setting.get("last_backup", {}) or {}` puis `.get("at")`.

**Le nom du champ exposé ne change pas** : `last_backup_at` reste
`last_backup_at` dans la réponse JSON. Le contrat d'API est celui d'OfeliaScan
(§6.10, et `SPEC_BIBLIOFELIA.md` ligne « `GET /health` … `last_backup_at`? ») —
seule la valeur était fausse, pas le contrat.

## Section de spec

`SPEC_BIBLIOFELIA.md` §6.10 (contrat d'API, endpoint `/health`).
