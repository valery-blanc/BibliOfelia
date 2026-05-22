# FEAT-005 — UI base (layout, recherche globale, icônes)

Statut : **DONE — tests écrits, non exécutés** (2026-05-21)
Sprint : 2 (UI et workflows métier)
Task : #5 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.1 (recherche), §6.9 (i18n UI), §10 (ergonomie)

## Contexte

Sprint 1 a livré le domaine (modèles, i18n, rôles). L'UI était encore au stade
placeholder (`base.html` avec liens morts). FEAT-005 pose le socle UI sur lequel
se branchent les Tasks #6 à #10.

## Périmètre

### Assets locaux (contrainte hors-ligne, aucun CDN)

- `static/fonts/inter-latin-wght-normal.woff2` + `inter-latin-ext-wght-normal.woff2`
  — police Inter variable (`@font-face` dans `bibliofelia.css`).
- `static/icons/*.svg` — 31 icônes Lucide (lucide-static), inlinées par tag.

### Tag d'icône (`apps/core/templatetags/biblio_icons.py`)

`{% icon "name" css_class size %}` lit `static/icons/<name>.svg`, en extrait le
contenu interne (cache `lru_cache`) et émet un `<svg>` normalisé
(`stroke=currentColor`, taille `1em` par défaut). Nom inconnu → chaîne vide.
Garde-fou anti-traversée de chemin.

### Layout (`templates/base.html` + `static/css/bibliofelia.css`)

- Barre de navigation par rôle : Catalogue/Usagers pour tous ; Prêt/Retour/
  Réservations/Récolement réservés à `user.is_librarian` ; lien Administration
  pour `user.is_superadmin` uniquement.
- Barre de recherche globale présente sur toutes les pages connectées.
- Sélecteur de langue (`set_language` Django, cookie) — 4 langues.
- Compteurs de notification (retards, réservations prêtes) en badge de nav.
- Icône d'aide « ? » → page `core:help`.
- Bascule mode simple / avancé (menu utilisateur).

### Recherche globale (`apps/core/search.py` + `core:search`)

`classify_query` aiguille la requête :
- EAN13 `290…` → fiche notice de l'exemplaire ;
- EAN13 `291…` → fiche usager ;
- ISBN-10/13 → fiche notice ;
- texte → liste catalogue filtrée (FTS5 `catalog_record_fts`).

`fts_search` interroge la table virtuelle FTS5 en recherche par préfixe sur
chaque terme, classée par pertinence (`rank`).

### Préférences UI

- `core:toggle_advanced` bascule `User.always_show_advanced` (SPEC §10.3). Les
  formulaires affichent leurs `<details class="advanced-section">` ouverts ou
  fermés selon cette préférence.

## Écarts / décisions

- **Sélecteur de langue** : `set_language` natif de Django, persistance par
  cookie `django_language`. La préférence par compte (`User.default_language`)
  n'est pas câblée — réglages Task #11.
- **i18n complété en cours de sprint** (suite au test de Val, cf. BUG-005) : les
  4 langues sont traduites (`fr`/`en`/`es`/`mg`, ~300 chaînes), et le routage
  passe en `i18n_patterns(prefix_default_language=True)` — toutes les URLs de
  l'interface portent un préfixe de langue (`/fr/…`, `/en/…`), sans quoi le
  cookie était ignoré sur les pages non préfixées. Malgache à faire relire par
  un locuteur natif.
- **Aide contextuelle** : une page d'aide générale unique (`core:help`) au lieu
  d'une page par écran. Suffisant pour la v1.
- `config/settings/test.py` retire `SetupRequiredMiddleware` du `MIDDLEWARE`
  pour permettre les tests unitaires de vues hors parcours wizard.
- Voir aussi `BUG-002` (boucle racine) et `BUG-005` (i18n), corrigés ce sprint.

## Tests (`apps/core/tests/`)

- `test_search.py` : classification (item/member/isbn/texte), normalisation,
  expression MATCH, FTS5 (titre, insensible aux accents, vide).
- `test_ui.py` : tag icône, recherche → redirections, `toggle_advanced`,
  login requis.

> ⚠️ La suite n'a pas pu être exécutée : l'environnement de dev (Docker/pytest)
> était indisponible au moment de l'écriture. À lancer avant commit :
> `docker compose -f docker-compose.dev.yml run --rm web pytest`.
