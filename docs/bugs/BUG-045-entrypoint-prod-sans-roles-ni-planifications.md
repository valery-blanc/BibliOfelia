# BUG-045 — Le conteneur de prod n'installe ni les rôles ni les planifications

**Status:** FIXED
**Date:** 2026-09-10
**Origine:** revue croisée BibliOfelia ⇄ keebee (dépôt `_review-ofelia`)

## Symptôme

Sur une Box installée de zéro, deux choses ne marchent pas — et aucune ne
se signale :

1. Les bibliothécaires s'authentifient mais n'ont **aucune permission** : tout
   écran protégé répond 403.
2. **Aucune sauvegarde horaire ne tourne**, jamais. Le tableau de bord n'alerte
   pas pour autant : il ne sait pas distinguer « la dernière sauvegarde date de
   plus de 24 h » de « il n'y a jamais eu de sauvegarde ».

## Cause

`scripts/dev-entrypoint.sh` lance `setup_roles` et `setup_schedules` ;
`scripts/entrypoint.sh` — celui de la prod, donc celui de la Box — ne les
lançait **ni l'un ni l'autre**.

- Sans `setup_roles`, aucun `Group` Django ne porte le nom d'un `Role`.
  `apps/accounts/signals.py` cherche le groupe correspondant au rôle de
  l'utilisateur et **passe son chemin en silence** s'il n'existe pas : l'usager
  est créé, connecté, et sans permissions.
- Sans `setup_schedules`, `apps/tasks/scheduling.install_schedules()` n'est
  jamais appelé, donc aucune ligne `Schedule` django-q2 n'existe. Le worker
  `qcluster` tourne, en bonne santé, et n'a simplement rien à exécuter :
  ni `apps.tasks.backup.run_backup` (horaire, §8), ni
  `apps.loans.services.expire_stale_reservations`, ni
  `apps.members.services.mark_expired_members` (quotidiennes).

C'est le défaut le plus contraire à la raison d'être de la Box : une machine
en site distant, sans maintenance, **qui croit sauvegarder et ne sauvegarde
rien**.

## Correctif

`scripts/entrypoint.sh` lance les deux commandes après `migrate` et
`seed_defaults`, avec `|| true` comme le fait l'entrypoint de dev. Les deux sont
idempotentes (`get_or_create` sur le nom).

Corollaire dans `apps/tasks/scheduling.py` : `install_schedules()` ne réécrit
plus `next_run` sur une planification existante. La commande tourne désormais à
**chaque démarrage du conteneur** ; réécrire `next_run = maintenant + 2 min`
aurait repoussé l'échéance à chaque redémarrage, et une Box qui redémarre
souvent (coupures de courant) n'aurait toujours jamais sauvegardé. `next_run`
n'est posé qu'à la création, ou s'il est nul.

Le worker n'est pas concerné : `docker-compose.yml` de keebee lui donne un
`entrypoint` explicite (`tini` + `qcluster`), il ne passe pas par ce script.
Les deux commandes tournent donc une fois, dans le conteneur web.

## Vérification après déploiement

```bash
docker logs edubox-bibliofelia | grep -E "rôles|planifications"
docker exec edubox-bibliofelia python manage.py shell -c \
  "from django_q.models import Schedule; print(list(Schedule.objects.values_list('name','next_run')))"
```

Trois planifications attendues, dont `bibliofelia.backup.hourly`.

## Section de spec

`SPEC_BIBLIOFELIA.md` §4.4 (séquence de démarrage) et §8 (sauvegardes).
