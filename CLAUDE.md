# CLAUDE.md — BibliOfelia

Guidance Claude Code pour ce repo.

## Projet

**BibliOfelia** — Logiciel de gestion de bibliothèque hors-ligne pour le projet Ofelia. Tourne sur la **Ofelia Box** (Raspberry Pi 5) en cohabitation avec [EduBox/keebee](../keebee).

- **Spec** : `docs/specs/SPEC_BIBLIOFELIA.md` (source de vérité)
- **Avancement** : `docs/tasks/TASKS.md`
- **Stack** : Django 5.1 LTS + SQLite WAL + DRF + django-q2 + HTMX + Pico.css, dans Docker.
- **Route nginx prod** : `/bibliofelia/` (PAS `/biblio/` qui est pris par Koha dans keebee)

## Workflow obligatoire

Pour toute modification (bug fix ou feature), AVANT commit :

```
[code] → [docs] → [déploiement Pi] → [test user] → [confirmation OK] → [commit]
```

1. Coder le changement.
2. Mettre à jour **`docs/specs/SPEC_BIBLIOFELIA.md`** (source de vérité), créer `docs/bugs/BUG-XXX-*.md` ou `docs/specs/FEAT-XXX-*.md` si pertinent.
3. Cocher `[x]` dans `docs/tasks/TASKS.md`.
4. Déployer sur la Pi (Task #18 : intégration keebee).
5. Demander à l'utilisateur de tester.
6. **N'AUCUN commit avant confirmation explicite.**
7. Une fois OK : commit unique groupant code + docs + TASKS.md.

## Connexion Pi

Voir `C:\WORK\keebee\CLAUDE.md` — `ssh -i ~/.ssh/id_ed25519_pi ofelia@192.168.0.147`.

## Commandes utiles

```powershell
# Dev local
docker compose -f docker-compose.dev.yml up --build
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.dev.yml exec web python manage.py test
docker compose -f docker-compose.dev.yml exec web python manage.py makemessages -l fr
```

## Conventions de code

- `black` (line-length 100), `isort` (profile=black), `ruff`
- `pytest --cov=apps` (cible 70%)
- Migrations : un fichier par PR, jamais éditer une migration appliquée.
- Pas de dépendance CDN — tout sert en local (contrainte hors-ligne).
