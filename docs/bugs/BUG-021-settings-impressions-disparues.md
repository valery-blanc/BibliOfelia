# BUG-021 — La catégorie « Impressions » a disparu de /admin/settings/

**Status:** FIXED
**Date:** 2026-07-09
**Section spec impactée:** §6.6 (Paramètres)

## Symptôme

Dans **Avancé → Paramètres** (`/admin/settings/`), les sections **Impressions —
Cartes membres** et **Impressions — Étiquettes codes Ofelia** ont disparu. Il
n'est **plus possible de régler la taille des étiquettes** (largeur/hauteur mm,
lignes de titre/auteur, logo) ni le format des cartes membres (nombre par A4,
photo, logo).

## Reproduction

1. Se connecter en superadmin.
2. Aller sur `/admin/settings/`.
3. La liste ne montre que : Identité, Langues, Durées prêts & réservations,
   Sauvegardes. Aucune entrée « Impressions ».

## Cause racine

**FEAT-047** (« nettoyage UI Paramètres/Avancé », Sprint 17) a retiré du registre
`FORMS` de `apps/core/admin_views.py` les entrées `printing_cards` et
`printing_labels`, en les jugeant « redondantes ou gérées ailleurs ». Or elles
n'étaient **gérées nulle part ailleurs** : ces deux formulaires
(`MemberCardFormatForm` → `Setting card_format`, `ItemLabelFormatForm` →
`Setting item_label_format`, FEAT-038/039) étaient le **seul** point d'entrée UI
pour configurer le format d'impression. Les classes de formulaire, les `Setting`
et les valeurs seed sont restées en place — seul l'accès UI a été coupé. Le rendu
d'impression (`apps/printing/services.py`) continuait donc d'utiliser les valeurs
par défaut (ou celles déjà stockées) sans possibilité de les modifier.

## Fix

Restauration des deux sections dans `apps/core/admin_views.py` (`FORMS`) et dans
`templates/core/admin/settings_index.html` (icônes + sous-titres), à leur libellé
d'origine :

- `printing_cards` → **Impressions — Cartes membres** (`MemberCardFormatForm`) ;
- `printing_labels` → **Impressions — Étiquettes codes Ofelia**
  (`ItemLabelFormatForm`).

Les sections ZeroTier et Sources de métadonnées, également retirées par FEAT-047,
**ne sont pas** restaurées (hors périmètre de ce bug ; elles n'ont pas d'usage
courant bibliothécaire). Aucune migration. Les 4 chaînes d'UI (2 libellés + 2
sous-titres) supprimées des `.po` par `makemessages --no-obsolete` sont
réintroduites et retraduites via `scripts/translations_sprint24.py` (traductions
reprises de l'historique git pré-FEAT-047) → gate `i18n_check.py` = 0.

## Vérification

- `/admin/settings/` réaffiche les deux sections Impressions.
- La section « Étiquettes codes Ofelia » permet de nouveau de régler
  largeur/hauteur (mm), caractères/lignes de titre, lignes d'auteurs, logo, et
  ces valeurs sont reprises à l'impression des étiquettes.
