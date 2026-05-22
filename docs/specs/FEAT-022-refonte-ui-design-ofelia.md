# FEAT-022 — Refonte UI : système de design OFELIA (tuiles, tile strip, polices)

**Statut** : DONE — commit `30cdba0` (2026-05-23)
**Design source** : Claude Design handoff (bundle `design_handoff_top_nav_tiles/`)
**Section SPEC impactée** : §3.2 Frontend, §10.2 Écrans principaux, Annexe B Stack

---

## Contexte

L'interface initiale utilisait Pico.css (classless) + Inter, avec une navigation horizontale en barre de liens texte. Le designer a produit un prototype HTML/CSS/React via Claude Design, décrivant :
- 7 grosses tuiles colorées pour la navigation (style portail OFELIA)
- Un tile strip horizontal (chips) sur les pages internes
- Le système de design OFELIA Studio Ayer (palette, polices, tokens)
- Une priorité mobile (1 colonne sur téléphone, gros cibles tactiles)

L'implémentation porte ce design dans les templates Django sans React.

---

## Ce qui a changé

### CSS

- **Suppression** de `pico.min.css` et de l'essentiel de `bibliofelia.css`
- **Création** de `static/css/ofelia.css` (600 lignes) : tokens couleur OFELIA, reset, topbar, tile grid, tile strip, page head, cartes, badges, KPI, boutons pill, formulaires, responsive

### Polices (hors-ligne)

- **Bricolage Grotesque** — variable woff2, 3 subsets (latin, latin-ext, vietnamese) → titres, noms de sections, KPI, hero
- **DM Sans** — variable woff2, 2 subsets → corps, labels, boutons, badges
- Servies localement dans `static/fonts/` (contrainte hors-ligne)

### Template tag `{% illus %}`

7 illustrations SVG multicolores 64×64 (flat-vector, palette OFELIA exclusivement) définies inline dans `apps/core/templatetags/biblio_icons.py` :

| Section | Illustration |
|---|---|
| home | Maison-bibliothèque (toit burgundy, mur amber, porte orange, fenêtres sky) |
| catalogue | Pile de 3 livres (forest / orange / burgundy) |
| members | 3 enfants (amber, burgundy, sky) tenant un livre |
| lending | Livre orange avec flèche forest vers la droite |
| return | Livre forest avec grande flèche courbe orange vers la gauche |
| reserve | Livre blush avec marque-page burgundy + étoile amber |
| advanced | Engrenage burgundy + engrenage amber + clé forest |

### Topbar

Remplace l'ancien `<nav class="app-topbar">` :
- Logo OFELIA (`static/img/ofelia-logo.png`) + nom de bibliothèque + tagline
- Sélecteur de langue (pill)
- Bouton aide (masqué mobile)
- Avatar utilisateur → dropdown Mon compte / Déconnexion
- `base.html` : bloc `{% block tile_strip %}` pour injection du chip nav sur pages internes

### Accueil (dashboard)

- Hero : `Bonjour, <nom>.` + sous-titre
- **Tile grid** : 6 tuiles (toutes sections sauf Accueil), responsive 1→2→4 col (600/900 px), illustrations SVG sur fond blanc, hover translateY(-2px)
- Bannière scan rapide (gradient burgundy → prêt)
- Recherche globale (pill)
- KPIs 6 cartes avec filet de couleur gauche
- Actions rapides 4 boutons (Nouveau prêt, Retour, Nouvelle notice, Nouveau membre)
- Tendance 30j (SVG area chart)
- Activité + Top 10 + État système

### Pages secondaires (Catalogue, Membres, Prêt, Retour, Réservations, Avancé)

Chacune ajoute :
1. **Tile strip** (`templates/partials/_tile_strip.html`) : chips colorées scrollables, chip actif = couleur de section, `aria-current="page"`
2. **Page head** (`templates/partials/_page_head.html`) : illustration SVG + titre h1 + sous-titre + bouton d'action optionnel

### Login

Page standalone (ne dépend plus de `base.html`) :
- Topbar allégée : logo + langue + aide, sans avatar
- Illustration maison-bibliothèque inline
- Carte centrée avec champs `.field` alignés
- Bouton `Se connecter` pill pleine largeur (burgundy)

### Icônes Lucide ajoutées

17 icônes téléchargées depuis lucide-static v0.488.0 : `chevron-right`, `globe`, `file-text`, `shield`, `cloud`, `database`, `trending-up`, `trending-down`, `archive`, `chart-bar`, `id-card`, `bookmark`, `filter`, `activity`, `calendar-check`, `file-chart-line`, `file-bar-chart`.

---

## Responsive

| Breakpoint | Comportement |
|---|---|
| < 600 px | 1 col tuiles, 92 px min, liste cartes mobiles, `.hide-sm` masqué |
| ≥ 600 px | 2 col tuiles, padding 24 px, KPI 3 col |
| ≥ 700 px | Table catalogue visible, `grid-2` côte à côte |
| ≥ 900 px | 4 col tuiles (stack vertical 180 px), KPI 6 col |

---

## Déploiement

Le déploiement sur la Pi nécessite un `collectstatic` pour publier les nouveaux assets (polices, CSS, logo, icônes). L'`entrypoint.sh` de prod le fait automatiquement au démarrage du container.
