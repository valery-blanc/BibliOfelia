# FEAT-048 — Réorganisation des menus du guide utilisateur

**Statut** : DONE (en attente test Val + commit)
**Date** : 2026-05-31
**Demande** : Val (chat)

## Contexte

Le guide utilisateur (site MkDocs Material, `docs/user-guide/`, 4 langues) avait
un menu trop fragmenté (11 rubriques de premier niveau) et un **top menu
instable** : avec `navigation.tabs`, les entrées d'une seule page (Accueil, FAQ,
Glossaire) masquaient le menu de gauche tandis que les sections l'affichaient,
faisant « sauter » la mise en page d'une page à l'autre.

## Décisions (Val)

1. **Regroupements** :
   - *Accueil* + *Premiers pas* → **Premiers pas** (Accueil devient la 1re sous-page)
   - *Catalogue* + *Inventaire* → **Catalogue**
   - *Prêts et retours* + *Réservations* → **Prêts** (7 pages)
   - *Cas courants* → réécrits en Q/R dans la **FAQ**
2. **OfeliaScan** : retiré du menu, **fichiers conservés** pour une éventuelle
   réintégration (« je verrai ce que j'en fais plus tard »).
3. **Top menu** : suppression de `navigation.tabs` → un seul menu latéral stable,
   identique sur toutes les pages.
4. **Menu de gauche** : police réduite pour voir davantage de sous-chapitres.

## Implémentation

### Navigation (`mkdocs.yml`)

- Nouvelle arborescence à **8 rubriques** : Premiers pas, Catalogue, Usagers,
  Prêts, Impressions, Rapports, FAQ, Glossaire.
- `Inventaire/{recolement,catalogage-scan}` déplacés sous **Catalogue** (fichiers
  toujours dans `docs/inventaire/`, seul le nav change).
- `Réservations/*` remontés sous **Prêts** (fichiers toujours dans
  `docs/reservations/`).
- Retrait de `- navigation.tabs` des `features`.
- Pages OfeliaScan sorties du nav via :
  ```yaml
  not_in_nav: |
    /ofeliascan/
  ```
  (mkdocs ≥ 1.5) — supprime le warning « not in nav » sous `--strict` tout en
  gardant les pages accessibles par URL (`/bibliofelia/docs/ofeliascan/…`).
- `nav_translations` réduites à 9 entrées/langue (ajout `Prets` → Loans /
  Préstamos / Fampindramana ; retrait Inventaire, Reservations, OfeliaScan
  mobile, Cas courants, Prets et retours).

### Cas courants → FAQ (×4 langues)

- Nouvelle section **« Cas difficiles »** dans `faq.md` avec 4 Q/R :
  - livre perdu / abîmé — ancre `#livre-perdu`
  - suppression d'une notice — ancre `#supprimer-notice`
  - carte perdue / volée — ancre `#carte-perdue`
  - retard prolongé — ancre `#retard`
- Ancres **stables et identiques dans les 4 langues** via `attr_list`
  (`### … { #livre-perdu }`), pour des liens robustes indépendants de la
  slugification du titre traduit.
- Les 12 fichiers `cas-courants/*.md` supprimés.
- ~28 liens internes repointés `cas-courants/<x>.md` → `faq.md#<x>` (24 fichiers,
  script ponctuel `repoint.py`). Le remplacement par sous-chaîne couvre aussi les
  `../cas-courants/…` (→ `../faq.md#…`).

### Page d'accueil (`index.md` ×4)

Sommaire réécrit pour refléter les 8 rubriques (suppression des références à
OfeliaScan mobile, Cas courants, Réservations, « Prêts et retours »).

### Thème (`stylesheets/extra.css`)

- `.md-nav` : `font-size` 0.78 → **0.68rem**, `line-height: 1.35`.
- Interligne des liens resserré (`margin` 0.32em) → plus de sous-chapitres
  visibles d'un coup d'œil.
- `.md-nav__title` 0.85 → 0.74rem.

### Déploiement (`scripts/deploy_pi.sh`)

`rsync` est absent en Git Bash sous Windows. Ajout d'un **fallback** : si `rsync`
introuvable, transfert par `tar -czf - | ssh … tar -xzf -` après purge de la
cible (`rm -rf $PI_TARGET/* …`) pour reproduire la sémantique `--delete`.

## Vérifications

- `mkdocs build --strict` : **0 warning**, 4 langues, 9 éléments de nav traduits.
- Doc équilibrée : **32 pages × 4 langues**.
- Gate app `scripts/i18n_check.py` → **0** (inchangé, la réorg n'ajoute aucune
  chaîne gettext).
- Smoke test HTTP sur la Box : pages clés 200 (FR/EN/ES/MG), anciennes URLs
  `cas-courants/*` → 404, ancres FAQ présentes, `ofeliascan/activer` toujours
  joignable hors-nav, sommaire d'accueil sans rubrique obsolète.

## Impact / limites

- Aucune chaîne d'app, aucune migration.
- Les pages OfeliaScan restent servies (accessibles par URL directe) mais
  invisibles dans la navigation jusqu'à décision de Val.
- Le résidu de build `site/ofeliascan/recolement` observé provenait d'un build
  antérieur non nettoyé ; un build propre (`rm -rf site`) ne le génère plus et le
  transfert tar purge la cible.
