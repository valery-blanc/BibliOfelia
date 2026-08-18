# BUG-023 — Google Books en quota dépassé sur les instances hébergées

**Status:** FIXED
**Date:** 2026-08-03

## Symptôme

Sur `grand-saconnex.bibliofelia.org` et `sanjuan.bibliofelia.org`, Google Books
répondait **429 Too Many Requests dès le premier appel**, à chaque scan, y
compris après le back-off adaptatif de BUG-019 (3 réessais, puis abandon en
`SourceRateLimited`). Effet visible : ~14 s perdues par livre scanné, et aucune
métadonnée Google Books.

## Reproduction

```
docker exec bo-grand-saconnex-web python -c "…google_books.lookup('9782882415417')"
→ HTTP 429 ×4 puis SourceRateLimited('google_books')
```

## Cause racine

Les deux instances Avignon ont été créées par le wizard (FEAT-056 phase 4) et
n'ont donc **aucun réglage de sources** : `metadata.google_books_api_key` est
vide. Sans clé, l'API Google Books applique un quota **partagé par adresse IP** —
et l'IP publique d'Avignon `31.164.198.65` est mutualisée avec les autres sites
hébergés. Le quota anonyme est donc épuisé en permanence.

La clé existait déjà mais uniquement sur la Box (posée à FEAT-050 itér. 2) :
c'est un `Setting` en base, donc **par instance**, pas une variable d'image.

## Fix appliqué

1. Clé `metadata.google_books_api_key` posée sur les deux instances (même clé
   que la Box), plus `metadata.sources` avec les 6 sources activées.
2. `MetadataSourcesForm` : l'aide du champ ne dit plus que la clé est
   « obligatoire pour activer Google Books » (faux — elle relève le quota) mais
   explique le quota par IP et le message « quota atteint ».
3. FEAT-059 (même sprint) rend Google Books actif par défaut, donc une future
   instance neuve l'interrogera d'emblée.

Vérifié après fix : `google_books.lookup("9782882415417")` → « Muses » (200).

## Reste à savoir

Google Books renvoie parfois un **503** transitoire, et son index `isbn:` ignore
certains ISBN (constat déjà noté à FEAT-050) : ce n'est pas un quota, la source
est simplement muette pour ce livre. Les autres sources prennent le relais.

## Section spec impactée

`SPEC_BIBLIOFELIA.md` §6.11 (sources de métadonnées : réglage par instance) et
§11.7 (hébergement multi-instances : réglages à poser sur une instance neuve).
