# FEAT-091 — Guide utilisateur : caisse, tarifs, activités, bouclement

**Status:** DONE (validé Val 2026-09-04)
**Date:** 2026-09-04

## Contexte

Les Sprints 31 et 32 ont ajouté sept écrans (caisse, factures, tarifs
et catégories d'usagers, activités, animations, statistiques,
bouclement) plus des changements visibles sur la fiche usager, le
renouvellement, le scan caméra et le prêt/retour. Le guide MkDocs
(`docs/user-guide/`) n'en parlait pas : la FAQ affirmait encore
« BibliOfelia ne gère ni amende ni facturation », le scan caméra
« EAN-13 uniquement », le renouvellement « à tout moment ».

## Comportement documenté

Nouvelle section **Caisse** (4 pages × FR/EN/ES/MG) :

- `caisse/caisse.md` — tiroir, encaissement, cotisation / amende /
  animation, PDF, file d'emails (Box vs instance hébergée), devise
- `caisse/tarifs.md` — catégories + autres tarifs, changement de
  catégorie (BUG-042)
- `caisse/activites.md` — activités vs animations, présences (scan
  ou 4 derniers chiffres), stats / CSV
- `caisse/bouclement.md` — cinq étapes, emails selon le lieu,
  extinction Box seulement (et honnête si le service n'est pas là)

Pages mises à jour : accueil, dashboard, fiche, inscription,
renouvellement (fenêtre 30 jours, BUG-041), carte / impressions
(bouton 62 mm FEAT-090), scan caméra (tous les linéaires FEAT-087),
prêt (ancienne carte + deux codes FEAT-080/081), retour (qui
rapporte), FAQ (amendes, SMTP), glossaire.

Captures prises le 2026-09-04 **depuis Tulear**, Playwright contre
`https://sanjuan.bibliofelia.org` (compte temporaire `lea`, supprimé
ensuite). Pas de Docker de dev. L'instance Sanjuan est vide (0
notices) et affichée en COP ; le bouclement hébergé n'a pas l'étape
5 d'extinction. Fiche usager réelle non recapturée (données perso).

## Impact

`docs/user-guide/` uniquement (sources MkDocs). Pas de chaîne Django,
pas de gate `i18n_check.py`. Build : `mkdocs build --strict`.
