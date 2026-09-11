# BUG-048 — Les archives de sauvegarde traînent un journal WAL non vide

**Status:** FIXED
**Date:** 2026-09-10
**Origine:** vérification sur la Box après le correctif BUG-046

## Symptôme

Aucun. La sauvegarde annonce `Backup OK`, l'archive passe son
`PRAGMA integrity_check`, et sa taille est plausible. Le défaut ne se voit qu'en
listant le répertoire — ou, bien plus tard, en restaurant une copie promue.

Mesuré sur la Box le 2026-09-10, avant correctif :

```
bibliofelia-20260910T191838Z.sqlite3       6 430 720
bibliofelia-20260910T191838Z.sqlite3-shm      32 768
bibliofelia-20260910T191838Z.sqlite3-wal     140 112   ← non vide
```

## Cause

**`with sqlite3.connect(...)` ne ferme pas la connexion.** Contrairement à la
quasi-totalité des gestionnaires de contexte de la bibliothèque standard, celui
de `sqlite3.Connection` valide (ou annule) la transaction et s'arrête là. Les
trois connexions ouvertes par `run_backup` — source, destination, contrôle
d'intégrité — restaient donc ouvertes, et l'archive conservait à côté d'elle un
journal WAL non fusionné.

Ce n'est pas cosmétique : **`_rotate` promeut l'archive vers `daily/`,
`weekly/` et `monthly/` par un `shutil.copy2` du seul fichier principal.** Une
copie promue pouvait donc être amputée de ce que contenait le journal — et
c'est précisément la copie qu'on garde 400 jours.

Même famille que [BUG-046](BUG-046-restauration-journal-wal-et-gunzip.md) : on
avait traité le journal du **côté restauration**, pas du côté production.

## Correctif

`apps/tasks/backup.py::run_backup` :

- les trois connexions passent par `contextlib.closing` — elles sont
  effectivement fermées ;
- après le contrôle d'intégrité, `PRAGMA wal_checkpoint(TRUNCATE)` fusionne le
  journal dans le fichier principal et le vide ;
- `_drop_wal_sidecars(out)` retire les fichiers résiduels, y compris sur le
  chemin d'échec (une archive rejetée ne doit pas laisser de débris).

L'archive devient **un fichier unique et autonome** : copiable, promouvable,
transportable sur une clé sans bagage.

## Tests

`apps/tasks/tests/test_backup_restore.py::TestRunBackup` — trois tests, dont
celui qui compte : l'archive est copiée **seule** ailleurs, puis relue. C'est ce
que fait `_rotate`, et ce que fera l'opérateur qui emporte le fichier.

Vérifié sur Fez : le test **échoue** sur le code d'avant
(`bibliofelia-….sqlite3-wal` présent) et passe sur le code corrigé.

## Vérification sur la Box

```
$ docker exec edubox-bibliofelia-worker python manage.py run_backup
Backup OK → /backup/db/hourly/bibliofelia-20260910T192104Z.sqlite3 (6434816 octets)

$ docker exec edubox-bibliofelia-worker ls /backup/db/hourly/
bibliofelia-20260910T192104Z.sqlite3          ← un seul fichier
```

## Section de spec

`SPEC_BIBLIOFELIA.md` §8.1.
