# BUG-046 — La restauration laisse le journal WAL de l'ancienne base, et `restore.sh` suppose un `.gz`

**Status:** FIXED
**Date:** 2026-09-10
**Origine:** revue croisée BibliOfelia ⇄ keebee (dépôt `_review-ofelia`)

## Symptôme

Deux façons de rater une restauration, toutes deux silencieuses ou tardives :

1. **Par l'interface ou la commande** (`restore_from_file`) : la restauration
   annonce « OK », puis la base contient un mélange — des enregistrements qu'on
   voulait justement annuler réapparaissent, ou SQLite finit par répondre
   `database disk image is malformed`.
2. **Par le script** (`scripts/restore.sh`) : pointé sur la sauvegarde produite
   par l'application elle-même, il échoue sur
   `gzip: … not in gzip format` — **après** avoir vidé la base vivante.

## Cause

**1. Les journaux `-wal` / `-shm` survivaient au remplacement.**
La base tourne en WAL (`config/settings/base.py`, `PRAGMA journal_mode=WAL`) :
à côté de `bibliofelia.sqlite3` vivent `bibliofelia.sqlite3-wal` et
`-shm`, qui contiennent les transactions pas encore fusionnées.
`restore_from_file` faisait `os.replace(tmp, target)` sur le **seul** fichier
principal. À la réouverture, SQLite trouvait un journal orphelin et le rejouait
**par-dessus la base restaurée**.

Même cause pour la copie de sécurité prise avant écrasement : un `shutil.copy2`
du seul fichier principal produisait un filet de sécurité **incomplet**.

**2. `restore.sh` décompressait sans regarder.**
`apps/tasks/backup.py::run_backup` — la tâche horaire, le bouton « Sauvegarder
maintenant » et `manage.py run_backup` — écrit des `.sqlite3` **non compressés**
dans `/backup/db/hourly/`. Seul `scripts/backup.sh` (conteneur de sauvegarde
keebee) gzippe. Le script faisait `gunzip -c "$SRC" > "$DEST"` sans condition :
la redirection **tronque la cible avant** que gunzip ne s'exécute, donc la
sauvegarde la plus courante du système laissait la base vivante vide.

## Correctif

`apps/tasks/backup.py` :
- nouvelle fonction `_drop_wal_sidecars()`, appelée juste après `os.replace` ;
- la copie de sécurité passe par `sqlite3.Connection.backup()` (copie cohérente,
  WAL compris), avec repli sur `copy2` si SQLite refuse.

`scripts/restore.sh`, réécrit :
- le format est **détecté** (`gzip -t`), plus jamais supposé ;
- l'archive est extraite dans un fichier temporaire et son
  `PRAGMA integrity_check` est vérifié **avant** de toucher à la base vivante —
  une archive illisible ne détruit plus rien ;
- la copie de sécurité utilise `sqlite3 … ".backup"` et non `cp` ;
- les journaux `-wal` / `-shm` sont supprimés après la bascule.

## Cas limite couvert

Restaurer par-dessus une base ouverte reste déconseillé (la docstring de
`restore_from_file` le dit déjà : couper le service d'abord). Le correctif ne
protège pas de la concurrence, il supprime la corruption **certaine** qui
survenait même à l'arrêt.

## Section de spec

`SPEC_BIBLIOFELIA.md` §8.3 (restauration).
