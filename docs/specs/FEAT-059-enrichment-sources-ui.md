# FEAT-059 — Google Books dans les sources d'enrichissement + libellés

**Status:** DONE
**Date:** 2026-08-03

## Context

Sur `/fr/admin/enrichment/`, Val constate des cases à cocher pour OpenLibrary,
BNF et BNE, **mais pas pour Google Books**. Cause : `active_sources()` prenait
`False` comme valeur par défaut pour `google_books` —

```python
return [s for s in order if data.get(s, s in ("openlibrary", "bnf", "bne"))]
```

— héritage de l'époque où l'on croyait la clé d'API obligatoire (elle ne fait que
relever le quota, cf. BUG-023). Sur une instance neuve, qui n'a aucun réglage
`metadata.sources`, Google Books était donc invisible et jamais interrogé à
l'enrichissement. Il l'était en revanche au **scan** (`lookup_isbn_multi`
parcourt tout le registre `SOURCES`), d'où une incohérence entre les deux flux.

Deuxième défaut : les cases affichaient le **slug** brut (« bnf », « bne »).

## Behavior

- Toutes les sources connues sont actives par défaut. Une instance neuve propose
  les 6 cases (OpenLibrary, Google Books, BnF, BNE, Swisscovery, K10plus).
- Un opt-out explicite dans Paramètres → Sources de métadonnées est respecté.
- Les cases affichent le libellé lisible (`SOURCE_LABELS`), pas le slug, et un
  lien « Activer ou désactiver des sources » renvoie vers les paramètres.
- Le sous-titre de la page ne cite plus une liste figée de 4 sources.

## Technical spec

- `apps/core/forms.py:MetadataSourcesForm` :
  - `SOURCE_ORDER` (liste unique, alignée sur l'ordre de préférence de
    `lookup_isbn_multi`) remplace les listes en dur dupliquées ;
  - champs `*_enabled` générés/initialisés en boucle, `initial=True` partout ;
  - `save()` persiste un flag par source de `SOURCE_ORDER` ;
  - `active_sources()` → défaut `True` pour toute source non mentionnée.
- `apps/core/admin_views.py:enrichment_index` passe des couples
  `(slug, libellé)` ; `enrichment_start` valide contre `SOURCE_ORDER` au lieu
  d'un tuple en dur (sinon Swisscovery / K10plus seraient filtrés en silence).
- `templates/core/admin/enrichment_index.html` : boucle sur les couples.

## Impact on existing code

- Une instance existante qui avait explicitement décoché une source garde son
  choix (le réglage stocké prime).
- Sur la Box, `metadata.sources` contenait déjà les 4 sources à `True` ;
  Swisscovery et K10plus, absents de ce dict, deviennent actifs par le nouveau
  défaut.
- Tests : `apps/core/tests/test_metadata_sources_form.py` (4 cas).
