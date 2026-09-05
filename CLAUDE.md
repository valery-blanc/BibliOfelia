# CLAUDE.md — BibliOfelia

Guidance pour tout agent qui travaille sur ce repo (**Claude Code ou Grok**).
Dans ce fichier, « Claude » désigne l'agent de session, pas un produit.

## Projet

**BibliOfelia** — Logiciel de gestion de bibliothèque hors-ligne pour le projet Ofelia. Tourne sur la **Ofelia Box** (Raspberry Pi 5) en cohabitation avec [EduBox/keebee](../keebee).

- **Spec** : `docs/specs/SPEC_BIBLIOFELIA.md` (source de vérité)
- **Avancement** : `docs/tasks/TASKS.md`
- **Stack** : Django 5.1 LTS + SQLite WAL + DRF + django-q2 + HTMX + Pico.css, dans Docker.
- **Route nginx prod** : `/bibliofelia/` (PAS `/biblio/` qui est pris par Koha dans keebee)

## Chemins de fichiers

Toujours donner les chemins de fichiers au format Windows complet : `C:\dossier\sous-dossier\fichier.ext`

## Workflow obligatoire

Pour toute modification (bug fix ou feature), AVANT commit :

```
[code] → [docs] → [déploiement Pi] → [test user] → [confirmation OK] → [commit]
```

### Répartition des rôles (Claude / Val)

Claude exécute **toutes les tâches techniques** lui-même, sans demander à Val de
lancer des commandes : coder, `pytest`, `docker compose`, `makemigrations`,
migrations, déploiement, vérifications, préparation de l'environnement de test
(ex. positionner `setup_completed`). Si un outil est cassé, Claude le signale et
propose une réparation — mais ne délègue jamais le travail technique à Val.

Val intervient **uniquement** pour le test fonctionnel final de l'UI dans le
navigateur, puis donne (ou non) sa confirmation explicite avant le commit.
Concrètement : Claude lance `docker compose up`, prépare tout, et Val n'a plus
qu'à regarder l'écran.

1. Coder le changement.
2. Mettre à jour **`docs/specs/SPEC_BIBLIOFELIA.md`** (source de vérité), créer `docs/bugs/BUG-XXX-*.md` ou `docs/specs/FEAT-XXX-*.md` si pertinent.
3. Cocher `[x]` dans `docs/tasks/TASKS.md`.
4. Déployer sur la Pi (Task #18 : intégration keebee).
5. Demander à l'utilisateur de tester.
6. **N'AUCUN commit avant confirmation explicite.**
7. Une fois OK : commit unique groupant code + docs + TASKS.md.

### Task Tracking (détail)

Pour toute tâche impliquant > 3 fichiers ou > 3 étapes :
1. AVANT de commencer : créer ou mettre à jour la checklist dans `docs/tasks/TASKS.md`
2. Marquer chaque sous-étape `[ ]` (todo), `[x]` (done), ou `[!]` (bloqué)
3. Mettre à jour la checklist APRÈS chaque sous-étape terminée
4. Si la session est interrompue, la checklist est la source de vérité pour reprendre

### Mémoire partagée Claude / Grok (OBLIGATOIRE)

Val utilise **Claude Code et Grok indifféremment** sur ce projet. Il n'y a
**qu'une** mémoire : celle de Claude Code, hors git.

Dossier : `C:\Users\Val\.claude\projects\C--WORK-BibliOfelia\memory\`
Index : `C:\Users\Val\.claude\projects\C--WORK-BibliOfelia\memory\MEMORY.md`

- **Claude Code** charge `MEMORY.md` tout seul au démarrage.
- **Grok ne le fait pas.** `/memory on` est un **autre** store
  (`~\.grok\memory\`), off par défaut, et **par session**. Ne pas s'en
  servir pour BibliOfelia : les décisions y seraient invisibles à Claude.

Au début de **chaque** session Grok, et après `/clear`, **avant tout
autre travail** :

1. Lire `MEMORY.md` **en entier**.
2. Lire les fiches liées pertinentes (sprint en cours, Box, i18n,
   déploiement) listées dans cet index.
3. Enchaîner ensuite la checklist « Resuming Work » ci-dessous.

Toute décision non triviale se **écrit** dans ces fichiers (nouvelle
fiche + ligne dans `MEMORY.md`), jamais dans `~\.grok\memory\`.

### Resuming Work

Au début d'une nouvelle session ou après `/clear`, TOUJOURS :
1. Lire `docs/tasks/TASKS.md` pour vérifier l'avancement
2. Lire `C:\Users\Val\.claude\projects\C--WORK-BibliOfelia\memory\MEMORY.md`
   (et les mémoires liées) pour les décisions structurantes — **Grok :
   cette lecture n'est pas optionnelle, voir § Mémoire partagée**
3. Lire la section pertinente de `docs/specs/SPEC_BIBLIOFELIA.md` selon le sprint en cours
4. Identifier le premier item non coché de TASKS.md
5. Annoncer à Val : sprint en cours + premier item à traiter + attendre son `go` avant de coder

Prompt-type de reprise à coller après `/clear` :

```
On reprend BibliOfelia. Lis C:\Users\Val\.claude\projects\C--WORK-BibliOfelia\memory\MEMORY.md
(en entier, fiches liées du sprint), docs/tasks/TASKS.md, et la section
Workflow de CLAUDE.md. Annonce-moi le sprint en cours et le premier item non
coché, puis attends mon go pour démarrer.
```

### Cadence sprint par sprint et `/clear`

Le projet avance **sprint par sprint** (cf. `docs/tasks/TASKS.md`). À la fin de chaque sprint, **c'est Claude qui annonce à Val quand faire `/clear`**, pas l'inverse.

Procédure de fin de sprint :

1. Le sprint est terminé côté code + docs.
2. Lancer l'app pour test (`docker compose -f docker-compose.dev.yml up --build` ou déploiement Pi).
3. Demander à Val de tester et **attendre sa confirmation explicite**.
4. Une fois Val OK :
   a. Commit unique groupant code + docs + TASKS.md
   b. Push sur `origin/main`
   c. Vérifier que `MEMORY.md` est à jour (toute décision non triviale prise pendant le sprint)
   d. Vérifier que `SPEC_BIBLIOFELIA.md` reflète le comportement réel du code
   e. Cocher `[x]` toutes les sous-étapes du sprint dans `TASKS.md`
5. **Seulement après les étapes 4a-4e** : dire à Val « OK, tout est sauvegardé, tu peux faire `/clear` puis lancer le sprint suivant avec le prompt de reprise ».

Ne JAMAIS suggérer un `/clear` si un seul de ces éléments est en suspens. Si Val propose `/clear` au milieu d'un sprint, l'avertir que des décisions de conversation seraient perdues et demander confirmation explicite.

### Documentation Synchronization (OBLIGATOIRE)

À chaque modification (bug fix ou feature), peu importe la formulation (message direct, fichier temp_*.txt, oral), TOUJOURS :

1. **Créer ou mettre à jour `docs/bugs/BUG-XXX-*.md`** ou **`docs/specs/FEAT-XXX-*.md`** correspondant.
2. **Mettre à jour `docs/specs/SPEC_BIBLIOFELIA.md`** — OBLIGATOIRE, SANS EXCEPTION. Source de vérité de l'app. Doit refléter à tout moment le comportement réel du code (section concernée, version en en-tête FEAT-XXX/BUG-XXX, structure du projet si fichiers ajoutés/supprimés, cas limites). Si la feature est trop petite pour un § dédié, intégrer dans la section la plus proche.
3. **Mettre à jour `docs/tasks/TASKS.md`** — toujours, sans condition : ajouter l'entrée si elle n'existe pas, cocher `[x]` les étapes terminées.

S'applique MÊME pour les petites modifs en chat. Si trop petit pour un BUG/FEAT dédié, au minimum mettre à jour la SPEC si le comportement change.

### Traductions i18n (OBLIGATOIRE — gate avant commit)

**Règle pérenne (Sprint 12)** : aucune chaîne FR ne doit rester en dur dans une page sans `{% trans %}` ou `_()` (gettext), et aucune chaîne traduisible ne doit rester sans traduction EN/ES/MG.

Workflow obligatoire **avant chaque commit** :

```powershell
# 1) Extraire les nouvelles chaînes des templates et du code Python
docker compose -f docker-compose.dev.yml exec -T web python manage.py makemessages -a --no-obsolete -l en -l es -l mg

# 2) Pour chaque chaîne FR ajoutée pendant le sprint :
#    - ajouter une entrée dans scripts/translations_sprint<NN>.py (FR → EN/ES/MG)
#    - rejouer : `python scripts/translations_sprint<NN>.py`

# 3) Vérification bloquante — exit code != 0 si une chaîne manque
python scripts/i18n_check.py

# 4) Compiler les .mo (re-fait au boot Docker via dev-entrypoint.sh) :
docker compose -f docker-compose.dev.yml exec -T web python manage.py compilemessages
```

**Le commit ne doit JAMAIS se faire si `i18n_check.py` retourne != 0.**

Outils :
- `scripts/i18n_check.py` — audit pass/fail (stdlib, sans Docker)
- `scripts/translations_sprint<NN>.py` — dict du sprint courant (créer un nouveau fichier par sprint)
- `scripts/apply_translations.py` — backlog historique (Sprints 1-11)
- `scripts/list_untranslated.py` — liste détaillée des chaînes manquantes en EN

### Bug Fix Workflow

1. Documenter dans `docs/bugs/BUG-XXX-short-name.md` (symptôme, reproduction, logs/traceback, section spec impactée)
2. Analyser la cause racine AVANT d'écrire le fix (Plan Mode)
3. Implémenter le fix
4. Doc complète : `BUG-XXX-*.md` → statut `FIXED` + fix décrit ; **`SPEC_BIBLIOFELIA.md` OBLIGATOIRE** → section comportement corrigé ; `TASKS.md` → cocher `[x]`
5. Lancer l'app : `docker compose -f docker-compose.dev.yml up --build` (ou déployer sur la Pi pour Task #18+)
6. Demander à l'utilisateur de tester et **attendre confirmation explicite** — NE PAS committer avant
7. **Avant commit** : passer le gate i18n (`python scripts/i18n_check.py` → 0)
8. Une fois confirmé : commit unique groupant code + docs + TASKS.md : `"FIX BUG-XXX: description courte"`

### Feature Evolution Workflow

1. Spec dans `docs/specs/FEAT-XXX-short-name.md` (contexte, comportement, spec technique, impact)
2. Analyser l'impact sur l'existant (Plan Mode) : risques, conflits, lacunes
3. Décomposer en tâches dans `docs/tasks/TASKS.md`
4. Implémenter
5. Doc complète : `FEAT-XXX-*.md` → `DONE` + implémentation décrite ; **`SPEC_BIBLIOFELIA.md` OBLIGATOIRE** → intégrer le nouveau comportement, incrémenter la version ; `TASKS.md` → cocher `[x]`
6. Lancer l'app et vérifier
7. Demander à l'utilisateur de tester et **attendre confirmation explicite** — NE PAS committer avant
8. **Avant commit** : passer le gate i18n (`python scripts/i18n_check.py` → 0)
9. Une fois confirmé : commit unique `"FEAT-XXX: description courte"`
10. Mettre à jour `CLAUDE.md` si des règles d'architecture ont changé

## Connexion Pi

Voir `C:\WORK\keebee\CLAUDE.md` — `ssh -i ~/.ssh/id_ed25519_pi ofelia@192.168.0.147`. Chemin d'install sur la Pi : `/opt/edubox/`.

## Infrastructure — accès serveurs

Pour les détails complets (clés SSH, API tierces, services locaux), lancer le skill `/vb-connectAll`. Résumé :

| Serveur | IP | Rôle | Connexion |
|---|---|---|---|
| **Ofelia Box** (Pi 5) | `192.168.0.147` | Cible de déploiement BibliOfelia + EduBox/keebee | `ssh -i ~/.ssh/id_ed25519_pi ofelia@192.168.0.147` |
| **ANQA** | `192.168.0.133` | Windows — build, GPU (RTX 5070 Ti) | `ssh -i ~/.ssh/id_ed25519_claude Val@192.168.0.133` |
| **Fez** | `192.168.0.221` | Debian 24/7 — **nœud actif** : Traefik + instances BibliOfelia (`bo-sanjuan-*`, `bo-grand-saconnex-*`, `bibliofelia-docs`) | `ssh fez` |
| **Avignon** | `192.168.0.222` | Debian 24/7 — **nœud de secours** du couple failover (aucun conteneur BibliOfelia en marche) | `ssh avignon` |
| **Tulear** | `192.168.0.200` | Windows — poste de travail : hub repos `C:\WORK`, hub clés SSH | `ssh -i ~/.ssh/id_ed25519_claude val@192.168.0.200` (alias `ssh tulear`) |
| **GitHub** | `github.com` | Compte `valery-blanc` | `ssh -i ~/.ssh/id_ed25519_github git@github.com` |

Repo BibliOfelia : `https://github.com/valery-blanc/BibliOfelia` (remote `origin`).

### ⚠️ Failover Fez ⇄ Avignon (depuis le 2026-08-08)

Les instances hébergées **ne tournent plus sur Avignon**. Le couple Fez/Avignon
est en failover automatique (projet GQQFM, FEAT-113/114) : **le nœud actif porte
les conteneurs**, l'autre est en attente. Au 2026-08-18, l'actif est **Fez**.

- Rôle du nœud : `cat /home/val/gqqfm-cluster-role` (`active` / `standby`).
- Source de vérité infra : `~/.claude/skills/infra.md` — **à lire avant toute
  opération de déploiement**, la répartition peut avoir basculé.
- Sur chaque nœud : `~/BibliOfelia` (copie de fichiers, **pas un clone git**) et
  `~/docker/bibliofelia-instances/{sanjuan,grand-saconnex}/`.

**Déployer une instance** (procédure vérifiée FEAT-062) :

```bash
tar -czf /tmp/x.tgz <fichiers> && scp /tmp/x.tgz fez:/tmp/
ssh fez 'cd ~/BibliOfelia && tar -xzf /tmp/x.tgz'
ssh fez 'cd ~/BibliOfelia && docker build --target prod -t ofelia/bibliofelia:avignon .'
ssh fez 'cd ~/docker/bibliofelia-instances/<instance> && docker compose up -d web worker'
# guide en ligne : cd ~/docker/bibliofelia-docs && docker compose build docs && docker compose up -d docs
```

Puis **refaire le sync + le build sur le nœud de secours** : un secours qui a du
code périmé annulerait le déploiement à la première bascule. Le tag d'image
`ofelia/bibliofelia:avignon` (nom historique, conservé) est **partagé par les
deux instances** : rebuilder sans recréer une instance la laisse sur l'ancienne
image jusqu'à son prochain `compose up`.

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

## Création de skills personnalisés

Les skills Claude Code de Val suivent ces conventions :

- **Nom** : toujours préfixé `vb-` (ex: `vb-init`, `vb-release`) pour éviter les conflits avec les skills officiels
- **Structure** : un dossier par skill dans `~/.claude/skills/`, contenant un fichier `SKILL.md`
  ```
  ~/.claude/skills/vb-monSkill/SKILL.md   ✅
  ~/.claude/skills/vb-monSkill.md         ❌ (fichier plat non détecté)
  ```
- **Invocation** : `/vb-monSkill`
