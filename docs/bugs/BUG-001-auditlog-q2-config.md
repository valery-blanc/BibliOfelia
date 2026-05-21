# BUG-001 — Crash au boot Django : auditlog + django-q config

**Statut** : FIXED
**Date** : 2026-05-21
**Sprint** : 0 (squelette, Task #1)

## Symptôme

`docker compose -f docker-compose.dev.yml up` crashe au démarrage de `web` et `worker`.

```
ValueError: In order to use setting 'AUDITLOG_EXCLUDE_TRACKING_MODELS',
setting 'AUDITLOG_INCLUDE_ALL_MODELS' must set to 'True'
```

Warning non bloquant en plus :
```
UserWarning: Retry and timeout are misconfigured. Set retry larger than timeout.
```

## Reproduction

1. `git clone https://github.com/valery-blanc/BibliOfelia`
2. `docker compose -f docker-compose.dev.yml up --build`
3. Le container `web` (Django runserver) et `worker` (qcluster) sortent immédiatement avec le ValueError ci-dessus.

## Cause racine

- `AUDITLOG_EXCLUDE_TRACKING_MODELS` n'a de sens que si `AUDITLOG_INCLUDE_ALL_MODELS=True` (sinon on n'a rien à exclure). Or la spec §9.6 demande d'auditer **uniquement** Member, BibliographicRecord, Item, Loan, Setting, User → ces modèles seront `auditlog.register()` explicitement à Task #4, donc `AUDITLOG_INCLUDE_ALL_MODELS` doit rester à `False` et `AUDITLOG_EXCLUDE_TRACKING_MODELS` ne doit pas être défini.
- `Q_CLUSTER.retry` (défaut 60) < `Q_CLUSTER.timeout` (réglé à 90) → django-q risque de relancer des tâches avant leur fin. Fix : `retry: 120` (> timeout).

## Fix

Dans `config/settings/base.py` :
- Supprimer `AUDITLOG_EXCLUDE_TRACKING_MODELS`
- Ajouter `"retry": 120` dans `Q_CLUSTER`

## Section spec impactée

§3.1 (django-q2), §9.6 (audit) — pas de changement de comportement, juste config correcte. Pas d'incrément de version spec.
