# FEAT-025 — Refonte design global (Sprint 8)

**Statut** : DONE — validé Val 2026-05-23 (Lot A pilote OK, puis Lot B+C+D livrés d'un bloc, validés OK).
**Demandeur** : Val
**Périmètre** : harmoniser 23 templates métiers sur le design system OFELIA déjà en place (FEAT-022).

## Contexte

FEAT-022 (validé Val 2026-05-23) a introduit le design system OFELIA dans
`static/css/ofelia.css` : topbar, footer, tuiles d'accueil, tilestrip, pagehead,
boutons `.btn`, tables `.table`/`.table-wrap`, cards, KPIs, badges, etc.

Seules trois pages avaient été refondues : `core/dashboard.html`,
`accounts/login.html`, le shell `templates/base.html`. **Toutes les autres
pages métiers utilisent encore l'ancien style Pico CSS** : `<table>` brut sans
classes, `role="button" class="secondary"`, `<header class="page-head">`
(classe inexistante dans ofelia.css), `.outline`, `.tag-pill`, etc.

Val remonte (2026-05-23, après validation de FEAT-024) :

> « il y a beaucoup de pages qui ne respectent pas le design général : elles
> n'ont pas la barre de navigation en haut [tilestrip], les tableaux sont
> moches (les données sont collées entre elles rien n'est visible), rien n'est
> aligné, les boutons sont de simples liens (ce devrait être de gros boutons
> arrondis) ».

URLs citées :
- `/bibliofelia/en/catalog/53/` → `templates/catalog/record_detail.html`
- `/bibliofelia/en/members/20/` → `templates/members/member_detail.html`
- `/bibliofelia/en/reports/` → `templates/reports/index.html`
- `/bibliofelia/en/admin/settings/` → `templates/core/admin/settings_index.html`

## Périmètre — templates à refondre

| Section | Templates |
|---|---|
| **Catalogue** (6) | `record_detail`, `record_list`, `record_form`, `_record_form`, `item_form`, `record_confirm_delete` |
| **Usagers** (4) | `member_detail`, `member_list`, `member_form`, `member_history` |
| **Prêts** (6) | `lend`, `return`, `consultation`, `mark_lost`, `reservations`, `reservation_form` |
| **Inventaire** (4) | `session_list`, `session_detail`, `session_form`, `session_report` |
| **Rapports** (5) | `index`, `overdue_list`, `inactive_list`, `reservations_pickup`, `period_error` |
| **Paramètres / Admin** (5) | `settings_index`, `settings_section`, `backup_restore`, `diagnostics`, `ofeliascan` |
| **Comptes** (3) | `user_list`, `user_form`, `password_reset` |
| **Impression** (2) | `labels_picker`, `cards_picker` |
| **Core** (2) | `advanced`, `help` |

Hors périmètre : `core/dashboard.html`, `accounts/login.html`, `setup/*`,
`admin/` Django (cf. mémoire `feedback_admin_django_scope`).

## Conventions de remplacement

| Ancien (Pico) | Nouveau (OFELIA) |
|---|---|
| `<header class="page-head"><h1>` | `{% include "partials/_tile_strip.html" with active="..." %}` + pagehead inline (icon + titre + sous-titre + action) |
| `<table>` brut | `<div class="table-wrap"><table class="table">` |
| `<a role="button" class="secondary">` | `<a class="btn btn--ghost">` |
| `<a role="button" class="btn-big">` | `<a class="btn btn--primary">` |
| `<button class="outline">` | `<button class="btn btn--ghost btn--sm">` |
| `<button type="submit">` (action principale) | `<button class="btn btn--primary">` |
| `class="action-row"` | wrapper inline-flex `style="display:flex;gap:8px;flex-wrap:wrap"` ou `.row-between` |
| `<dl class="record-meta">` | conservé tel quel — `.record-meta` est défini dans ofelia.css |
| `<span class="tag-pill">` | `<span class="badge">` |
| `<span class="status-{{ status }}">` | `<span class="badge badge--ok / --late / --soon / --info">` |
| `<form><div class="grid">` | `.card` + `.field` (cf. `partials/_field.html` mais classe `.field` au lieu de `.form-row`) |
| `<nav class="settings-nav">` | conservé (déjà défini ofelia.css) ou remplacé par `.list-row` |

## Tilestrip — mapping par page

| Template | `active` |
|---|---|
| catalog/* | `catalogue` |
| members/* | `members` |
| loans/lend.html | `lending` |
| loans/return.html | `return` |
| loans/reservations.html, reservation_form.html | `reservations` |
| loans/consultation.html, mark_lost.html | `lending` |
| inventory/* | `advanced` |
| reports/* | `advanced` |
| core/admin/*, accounts/*, printing/* | `advanced` |
| core/advanced.html | `advanced` |
| core/help.html | (aucun, ou `home`) |

## Découpage en lots

Décision Val 2026-05-23 : **Lot A seul d'abord, on décide ensuite**.

- **Lot A — 4 URLs citées** : `record_detail`, `member_detail`, `reports/index`, `settings_index`
- **Lot B — Listes** : record_list, member_list, user_list, reservations, session_list, overdue_list, inactive_list, reservations_pickup
- **Lot C — Formulaires** : record_form/_record_form, item_form, record_confirm_delete, member_form, user_form, reservation_form, session_form, password_reset
- **Lot D — Reste** : inventory/session_detail+report, loans (lend/return/consultation/mark_lost), settings_section/backup_restore/diagnostics/ofeliascan, printing/*, core/advanced, core/help, reports/period_error, member_history

## Lot A — détails

### record_detail.html
- tilestrip `active="catalogue"`
- pagehead inline : icon `book-open`, titre = `record.title`, sous-titre = `record.subtitle` ou « Notice catalogue », action principale = "Modifier" (librarian)
- Méta dans `.card`
- Tags en `.badge`
- Section Exemplaires : `.section-title` + `.table-wrap` + `.table`, statut en `.badge` (ok/late/soon)
- Actions Réserver / Supprimer en `.btn--ghost`

### member_detail.html
- tilestrip `active="members"`
- pagehead inline : icon `user`, titre = `last_name + first_name`, sous-titre = catégorie + n° de carte, badge statut à droite
- Alerts en `.msg msg-warning/error`
- Méta dans `.card`
- Section Prêts en cours : `.section-title` + `.table-wrap` + `.table`
- Actions (modifier / historique / renouveler carte / remplacer carte) en `.btn`

### reports/index.html
- tilestrip `active="advanced"`
- pagehead inline : icon `file-text`, titre « Rapports », sous-titre « Exports CSV, rapport annuel PDF, listes imprimables »
- 3 `.card` : Listes imprimables (3 `.list-row` cliquables), Export CSV (form + `.btn--primary`), Rapport annuel PDF (form + `.btn--primary`)

### settings_index.html
- tilestrip `active="advanced"`
- pagehead inline : icon `settings`, titre « Paramètres », sous-titre « Identité, langues, sauvegardes, OfeliaScan »
- Sections en `.list-row` cliquables (icône thématique + titre + chevron)
- Lien « ouvrir l'admin Django » dans une note muted en bas

## Implémentation (livré 2026-05-23)

### Helpers CSS ajoutés à `static/css/ofelia.css`

Bloc « Helpers formulaires » avant `/* ────────── Paramètres ────────── */` :

- `.req` : asterisque rouge pour champ requis
- `.help-hint` : small gris sous champ (`<small class="help-hint">`)
- `.field-error` : small rouge pour erreurs de champ
- `.form-control` : sélecteur d'input compatible `widget_tweaks` (`{{ field|add_class:"form-control" }}`)
- `details.advanced-section` : sections repliables stylées (chevron + cream summary + animation), utilisées pour le Mode avancé du Mode simple/avancé
- `.isbn-row` : flex row pour input ISBN + bouton « Récupérer » (HTMX)
- `.form-actions` : zone de boutons en bas de form avec séparateur top

### `templates/partials/_field.html`

Migré de `.form-row` (classe inexistante dans ofelia.css) vers `.field` (existe).

### Conventions appliquées partout

| Page type | Composant |
|---|---|
| Toutes les pages secondaires | `tile_strip` block avec `active=...` |
| En-tête | `pagehead` inline (icon coloré 56×56 + titre + sous-titre + action) |
| Listes de données | `.table-wrap` + `.table` avec `.badge` pour statuts |
| Listes de cliquables | `.list` + `.list-row` (icône + corps + chevron) |
| Formulaires | `.card` + `.field` + `.form-actions` |
| Actions principales | `.btn btn--primary` |
| Actions secondaires | `.btn btn--ghost` |
| Actions destructives | `.btn btn--primary` avec `style="background:#B83232;..."` |
| Tags | `.badge` (ok / late / soon / info / mut) |
| Statuts dans une table | `.badge` avec couleur selon valeur |
| Filter bar | `.filter-bar` avec inputs en `.field` |

### Templates refondus (23)

**Catalogue (5)** : record_detail, record_form, _record_form, item_form, record_confirm_delete
**Usagers (3)** : member_detail, member_form, member_history
**Comptes (3)** : user_list, user_form, password_reset
**Prêts (3)** : consultation, mark_lost, reservation_form
**Inventaire (4)** : session_list, session_detail, session_report, session_form
**Rapports (5)** : index, overdue_list, inactive_list, reservations_pickup, period_error
**Admin (5)** : settings_index, settings_section, backup_restore, diagnostics, ofeliascan
**Impression (2)** : labels_picker, cards_picker
**Core (1)** : help

Templates déjà OK (refondus à FEAT-022) : dashboard, login, advanced, lend, return, record_list, member_list, reservations, setup/*. Hors périmètre : /admin/ Django (cf. mémoire `feedback_admin_django_scope`).

### Mise en garde déploiement

Découvert pendant le Lot A : **les templates sont embarqués dans l'image Docker au build**, pas bind-mountés (seuls `/app/data`, `/app/media`, `/app/staticfiles` sont montés). `docker compose restart` ne suffit pas, il faut **rebuilder l'image** :

```bash
ssh ofelia@192.168.0.147 'cd /opt/edubox && sudo docker compose build bibliofelia && sudo docker compose up -d bibliofelia bibliofelia-worker'
```
