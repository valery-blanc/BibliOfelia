# FEAT-014 — Sauvegardes locales + cloud

Statut : DONE (validé Val 2026-05-22)
SPEC : §8

## Contexte

Garantir la durabilité des données : copie horaire cohérente de la BD
SQLite vers une clé USB locale, rotation 24h/7j/4w/12m, rsync du dossier
media en quotidien, vérification d'intégrité automatique, et option
cloud rclone chiffrée si une bande passante est ponctuellement
disponible.

## Implémentation

### `apps/tasks/backup.py`

- `run_backup(force_daily, force_cloud) -> BackupResult` :
  1. Lit `Setting.backup_config` (USB path, hourly, cloud).
  2. `sqlite3.Connection.backup()` (API Python native — copie cohérente
     même sous écriture concurrente via WAL).
  3. `PRAGMA integrity_check` ; supprime l'archive si ≠ `ok`.
  4. Rotation : copie l'archive vers `daily/weekly/monthly` à 02h /
     lundi 02h / 1er du mois 02h (override via `force_daily`).
  5. `_rsync_media` à 02h : `rsync -a --delete` si dispo (Linux), sinon
     `shutil.copytree` (Windows dev).
  6. Push cloud (rclone) à 03h si activé.
  7. Capture toute erreur et la reflète dans `BackupResult.error`.
  8. Persiste l'état dans `Setting.last_backup` (timestamp, statut,
     taille, error). Le dashboard l'utilise (alerte si > 24 h).
- `restore_from_file(path)` : décompresse si `.gz`, vérifie l'intégrité,
  backup de la BD courante (suffixe `.pre-restore.<ts>`), puis swap.

### Planification django-q2 (`apps/tasks/scheduling.py`)

Schedules installés par `python manage.py setup_schedules` (idempotent) :

| Nom                            | Func                                       | Fréquence |
|--------------------------------|--------------------------------------------|-----------|
| `bibliofelia.backup.hourly`    | `apps.tasks.backup.run_backup`             | H         |
| `bibliofelia.members.expire_cards` | `apps.members.services.mark_expired_members` | D    |
| `bibliofelia.reservations.expire`  | `apps.loans.services.expire_stale_reservations` | D |

`dev-entrypoint.sh` appelle `setup_schedules` au boot dev.

### Commandes manage.py

- `python manage.py run_backup [--force-daily] [--force-cloud]`
- `python manage.py restore_backup <path> [--yes]`

### UI (intégrée à FEAT-011)

- `core:backup_now` (POST) : bouton « Sauvegarder maintenant » dans
  `/admin/settings/backup/`.
- `core:backup_restore` (GET/POST) : upload d'un fichier `.sqlite3` /
  `.sqlite3.gz` à restaurer (sécurisé `@require_role(SUPERADMIN)` +
  vérification d'intégrité avant swap).
- `core:diagnostics` : affiche l'état django-q2 + dernière sauvegarde.

## Décisions

- **sqlite3 API Python plutôt que sous-process** : portable Windows/Linux,
  pas de dépendance au binaire `sqlite3` côté container web.
- **rsync optionnel** : `shutil.copytree` en fallback Windows pour que le
  dev local fonctionne ; la prod (Pi) a `rsync`.
- **Chiffrement** : géré par `rclone crypt` côté config rclone (passphrase
  hors BibliOfelia, conformément à la spec « stockage côté client »).
- **Cohabitation avec `scripts/backup.sh`** : le shell script reste
  l'option « container backup dédié » du déploiement keebee. Le worker
  django-q2 fait la même chose côté container web. Les deux écrivent dans
  les mêmes dossiers (`db/hourly/`, etc.) et la rotation est idempotente.
