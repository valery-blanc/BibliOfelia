# BUG-010 — Entrypoint Docker prod non exécutable au rebuild

Statut : **FIXED** (2026-05-23)
Sévérité : haute (conteneur prod en boucle de redémarrage)
Section spec : §11.2 (Dockerfile prod)

## Symptôme

À chaque rebuild sur la Pi (`docker compose up -d --build bibliofelia`),
le conteneur démarre en boucle avec :

```
[FATAL tini (7)] exec /app/scripts/entrypoint.sh failed: Permission denied
```

Healthcheck KO → `bibliofelia-worker` refuse aussi de démarrer (dépend de
`bibliofelia` healthy).

## Reproduction

1. Cloner le repo sur Windows (git config `core.fileMode=false` par défaut).
2. `docker buildx build --target prod .` ou `docker compose up --build`.
3. `docker run … bibliofelia` → echec `Permission denied`.

## Cause racine

Le repo est édité sous Windows, où git ne conserve pas l'exec bit
(`100644` dans `git ls-files --stage scripts/entrypoint.sh`). Le `COPY .
/app` du Dockerfile copie le fichier tel quel → mode `644` dans l'image →
tini ne peut pas l'exécuter.

Pourquoi ça marchait avant : la première mise en service de la Pi avait
sans doute été faite depuis une image construite ailleurs (build manuel,
ou via un clone qui avait préservé le bit pour une raison X). Le rebuild
FEAT-023 est le premier qui révèle le problème, mais tous les rebuilds à
partir de Windows auraient le même comportement.

## Fix

`Dockerfile` (cible `dev` ET `prod`) : ajout d'un `chmod +x
/app/scripts/*.sh` après le `COPY . /app`. Le build redevient idempotent
quelle que soit la plateforme source.

```dockerfile
COPY . /app
RUN chmod +x /app/scripts/*.sh \
    && mkdir -p /app/data /app/media /app/staticfiles \
    && ...
```

Pas de `git update-index --chmod=+x` sur le repo : Val travaille sous
Windows, le bit serait re-perdu au prochain checkout. Le `chmod` côté
image est la solution robuste.

## Doc

- `SPEC §11.2` : pas de modification (le Dockerfile reste un détail
  d'implémentation, le comportement spec inchangé).
- `TASKS.md` : entrée BUG-010 ajoutée sous Sprint 7.
