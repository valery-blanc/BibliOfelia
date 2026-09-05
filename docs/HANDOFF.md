# HANDOFF — reprise du projet par un autre agent

> Document de passation. À lire **avant** toute action sur BibliOfelia.
> Dernière mise à jour : 2026-09-04 (Sprints 31 et 32 commités).

## 0. Avertissement — trois des quatre sources sont hors dépôt

Cloner `BibliOfelia` ne suffit pas. Le contexte du projet est réparti sur
**deux dépôts et deux emplacements non versionnés** :

| Source | Emplacement | Versionné ? |
|---|---|---|
| Code + docs projet | `C:\WORK\BibliOfelia\` | ✅ `github.com/valery-blanc/BibliOfelia` |
| Infra + skills | `C:\Users\Val\.claude\skills\` | ✅ `github.com/valery-blanc/claude_skills` |
| Mémoire du projet | `C:\Users\Val\.claude\projects\C--WORK-BibliOfelia\memory\` | ❌ **local uniquement, aucun dépôt** |
| Instructions globales | `C:\Users\Val\.claude\CLAUDE.md` | ❌ **local uniquement** (363 octets) |

La mémoire (50 fichiers, 272 Ko) contient l'essentiel de ce qui **n'est pas
déductible du code** : arbitrages de Val, pièges rencontrés, pannes passées.
Elle n'est sauvegardée nulle part. Un agent qui travaille sur une autre machine
doit la recevoir par copie explicite.

---

## 1. Ordre de lecture

### Niveau 1 — obligatoire, dans le dépôt BibliOfelia (~5 700 lignes)

| Fichier | Lignes | Pourquoi |
|---|---|---|
| `C:\WORK\BibliOfelia\CLAUDE.md` | 228 | Workflow non négociable : `code → docs → déploiement → test Val → commit`. Répartition des rôles Claude/Val, gate i18n, cadence sprint et `/clear`. |
| `C:\WORK\BibliOfelia\docs\tasks\TASKS.md` | 2 359 | Source de vérité de l'avancement. **Commencer par la fin** (Sprint 31, ligne 2084+), pas par le début. |
| `C:\WORK\BibliOfelia\docs\specs\SPEC_BIBLIOFELIA.md` | 3 033 | Comportement réel de l'application. Lire **la section du sprint en cours**, pas l'intégralité. |
| `C:\WORK\BibliOfelia\README.md` | 77 | Stack technique + démarrage dev. |

Tous versionnés sur GitHub.

### Niveau 2 — hors dépôt, à récupérer explicitement

**Mémoire** — `C:\Users\Val\.claude\projects\C--WORK-BibliOfelia\memory\`

- `MEMORY.md` — l'index, **à lire en entier**. Claude Code le charge
  tout seul ; **Grok doit le lire à la main** au démarrage (règle dans
  `CLAUDE.md`, § Mémoire partagée). Ne pas utiliser `~\.grok\memory\`
  pour ce projet.
- les 20 `feedback_*.md` — les règles de travail que Val a posées et le
  raisonnement derrière : gate i18n, `/admin/` jamais pour les bibliothécaires,
  tester sur cible déployée (le dev local est cassé), pièges gabarits Django +
  i18n, « ne pas conclure trop vite »
- `project_sprint28|29|30_decisions.md` et les `project_box_*.md` — arbitrages
  clos et historique des pannes de la Box
- `user_role.md` — qui est Val

**Infra** — `C:\Users\Val\.claude\skills\infra.md` (914 lignes)

Indispensable dès qu'on touche au réseau ou au déploiement : machines, double
NAT, SSH directionnel, failover Fez ⇄ Avignon, règle ZeroTier. Versionné dans
`claude_skills`.

### Niveau 3 — skills, seulement si l'agent agit

Dans `C:\Users\Val\.claude\skills\`, tous versionnés dans `claude_skills` :

| Skill | Lignes | Quand |
|---|---|---|
| `vb-connectAll\SKILL.md` | 466 | Accès serveurs, clés SSH, API tierces |
| `vb-clear\SKILL.md` | 268 | Procédure complète de fin de sprint |
| `vb-impl-tempspec\SKILL.md` | 204 | Implémenter depuis `temp.txt` (cf. §4) |
| `vb-deployFez\SKILL.md` | 120 | Déploiement sur le nœud actif |
| `vb-deployAvignon\SKILL.md` | 104 | Déploiement sur le nœud de secours |

Les autres (`vb-release`, `vb-releaseToPlaystore`, `vb-pushtotest`,
`vb-android-launcher-icon`, `vb-rebuild-serverless`) concernent d'autres projets
— hors sujet ici. Le dossier `vb-deployANQA\` est **vide** : vestige, à ignorer.

### Niveau 4 — contextuel, à la demande uniquement

Ne **pas** faire lire en bloc les 90 `docs\specs\FEAT-*.md` ni les 30
`docs\bugs\BUG-*.md`. Seuls comptent ceux du sprint courant : `FEAT-083` à
`FEAT-088` et `BUG-041`.

`docs\user-guide\` (262 fichiers versionnés, dont les captures d'écran en
4 langues) : uniquement pour un travail de documentation utilisateur.

---

## 2. Ce qui est versionné sur GitHub — détail

### Dépôt `valery-blanc/BibliOfelia` (remote `origin`)

Versionné : `CLAUDE.md`, `README.md`, tout `docs\` (376 fichiers suivis),
`apps\`, `config\`, `templates\`, `static\`, `locale\**\*.po`, `scripts\`,
`Dockerfile`, `docker-compose*.yml`, `requirements*.txt`, `pyproject.toml`.

**Non versionné** (`.gitignore`), donc absent d'un clone :

- `temp.txt`, `temp_*.txt`, `temp[0-9]*.txt` — notes de travail locales (§4)
- `.env`, `data/`, `media/`, `db.sqlite3*`, `backup/`, `secrets/`, `*.key`
- `locale\**\*.mo` — les traductions compilées : **à régénérer**
  (`compilemessages`), sinon l'interface retombe en français
- `docs\user-guide\site\` et `docs\user-guide\preview\` — sorties MkDocs
- `_snapshots\`, `_test-etiquettes\`

### Dépôt `valery-blanc/claude_skills`

22 fichiers suivis, aucun `.gitignore` : `infra.md`, `README.md`,
`bootstrap_infra.py`, `shared\` (`settings.json`, `statusline-command.sh`,
`sync_config.ps1`) et les 13 `vb-*\SKILL.md`.

⚠️ `shared\sync_config.ps1` tourne au `SessionStart` et **écrase**
`~\.claude\settings.json`. Modifier ce fichier localement ne sert à rien : il
faut le modifier dans le dépôt et pousser.

### Dans aucun dépôt

La mémoire et le `CLAUDE.md` global. Les récupérer à la main :

```powershell
# Mémoire du projet (non versionnée — copie manuelle obligatoire)
robocopy "C:\Users\Val\.claude\projects\C--WORK-BibliOfelia\memory" "<destination>\memory" /E

# Skills + infra
git clone git@github.com:valery-blanc/claude_skills.git ~/.claude/skills
```

---

## 3. État du dépôt au 2026-09-05

**Sprint 33 commité** (validé Val 2026-09-05) : FEAT-092, BUG-044.

**Sprints 31 et 32 sont commités** (validés Val 2026-09-04) : `apps/finance/`,
`apps/closing/`, migration `members/0007`, specs FEAT-083 → FEAT-090,
BUG-041 → BUG-043.

Reste hors sprint :

```
[x] Déploiement Box (Canaima) — fait le 2026-09-04
[x] Guide utilisateur FEAT-091 — 7 écrans ×4 langues + captures, OK Val 2026-09-04
[x] Sprint 33 (FEAT-092 / BUG-044) — OK Val 2026-09-05
[ ] Unité systemd d'extinction (keebee/ofeliabox, FEAT-086)
[ ] SMTP Grand-Saconnex (Avancé → Paramètres → Email)
```

---

## 4. `temp.txt` et `temp2.txt` — ne pas lire par défaut

Ces deux fichiers sont le **bloc-notes de Val**, pas une source de vérité.

- Ils sont **gitignorés** (`.gitignore`, lignes 72-74) : absents d'un clone.
- Entre deux demandes, ils peuvent être **vides ou contenir des données
  périmées** — typiquement les notes du sprint précédent, déjà implémentées.
- Les lire spontanément fait donc courir le risque de ré-implémenter du travail
  déjà livré, ou de partir sur une intention abandonnée.

**Règle** : ne les ouvrir que sur demande explicite de Val, en pratique lors
d'un `/vb-impl-tempspec`. Le reste du temps, l'intention en vigueur est dans
`docs\tasks\TASKS.md` et `docs\specs\`.

---

## 5. Les cinq règles qu'on ne devine pas en lisant le code

1. **Jamais de commit avant confirmation explicite de Val.** Le workflow
   s'arrête au test fonctionnel, quel que soit l'état vert des tests.
2. **Gate i18n bloquant** : `python scripts\i18n_check.py` doit retourner `0`
   avant tout commit. Aucune chaîne FR en dur sans `{% trans %}` ou `_()`.
3. **Le dev local est cassé** (ni Docker ni dépendances sur le poste). Tests,
   `makemessages` et vérifications tournent dans un conteneur sur Fez ; Val
   teste sur la Box ou sur une instance `bibliofelia.org`.
4. **Claude fait tout le travail technique lui-même** — coder, tester,
   `docker compose`, migrer, déployer. Val n'intervient que pour regarder
   l'écran et valider.
5. **Le nœud de secours doit être resynchronisé après chaque déploiement.** Un
   secours au code périmé annule le déploiement à la première bascule.
