# BUG-017 — Tableau exemplaires tronqué sans scroll horizontal en mobile

**Status :** IN PROGRESS
**Date :** 2026-05-27
**Sprint :** 13 (cleanup)

## Symptôme

Sur la fiche notice `/catalog/<id>/` (et plus généralement sur tout
`.table-wrap`), le tableau des exemplaires est **tronqué à droite** en
version mobile : la colonne « Actions » (Modifier / Pilonner / Supprimer)
n'est pas accessible, et il n'y a **pas de scroll horizontal**.

## Reproduction

1. Ouvrir `/bibliofelia/fr/catalog/<id>/` sur écran ≤ 599 px.
2. Constater : la dernière colonne dépasse, mais le tableau ne se laisse
   pas défiler horizontalement.

## Cause racine

`static/css/ofelia.css` (l. 702-708) :

```css
.table-wrap {
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  overflow: hidden;   /* ← bloque tout scroll */
  background: var(--paper);
  box-shadow: var(--shadow-sm);
}
.table { width: 100%; … }
```

`overflow: hidden` + `width: 100%` sur la table → les colonnes sont
compressées (et tronquent visuellement quand le contenu dépasse la
cellule), sans permettre de scroller.

## Fix appliqué

`.table-wrap` passe à `overflow-x: auto` (`overflow-y: hidden` pour
préserver le clip vertical). Sur les vrais petits écrans, la table a une
`min-width` qui garantit un scroll utile au lieu de compresser les
colonnes :

```css
.table-wrap { overflow-x: auto; overflow-y: hidden; … }
@media (max-width: 599px) {
  .table-wrap .table { min-width: 540px; }
}
```

Le `border-radius` reste appliqué au wrap (les coins inférieurs ne sont
plus clippés mais ce n'est pas visible à l'œil).

## Spec section impactée

`SPEC §10.1` (design system) — tables responsives.
