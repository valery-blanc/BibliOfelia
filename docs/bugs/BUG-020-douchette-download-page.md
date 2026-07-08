# BUG-020 — Scan douchette ouvre la page de téléchargement du navigateur

**Status:** FIXED
**Date:** 2026-07-08

## Symptom

Sur le PC **Bruxelles** (qui affiche le site BibliOfelia), une **douchette USB**
(lecteur de code-barres en mode clavier HID) est branchée. Quand l'utilisateur
clique dans un champ qui accepte les codes-barres (barre de recherche du
dashboard, champs titre/auteur/ISBN…) puis scanne un livre :

- la redirection vers la **fiche catalogue** correspondante se fait bien ;
- **mais** la **page de téléchargement du navigateur** s'ouvre aussi (Firefox /
  Chrome : `Ctrl+J`).

## Reproduction steps

1. Depuis Bruxelles, ouvrir le site (`/bibliofelia/`), champ de recherche.
2. Cliquer dans le champ, scanner un livre avec la douchette.
3. → redirection correcte vers la fiche **+ ouverture parasite** de la page des
   téléchargements.

## Root cause

La douchette est un **clavier HID** : elle « tape » les chiffres du code très
vite puis envoie un **terminateur**. Le terminateur est le vrai piège : la
plupart des douchettes envoient **CR + LF**, or en événements clavier
navigateur :

- **CR = Ctrl+M** → interprété comme `Entrée` (valide / navigue) ;
- **LF = Ctrl+J** → interprété par le navigateur comme le **raccourci « page des
  téléchargements »** (Firefox/Chrome) — l'ouverture parasite constatée ;
- selon la config, un **Tab** de suffixe → changement de champ / d'onglet.

Point critique : un `<input>` texte **ne consomme pas** ces raccourcis
(Ctrl+J/Ctrl+T…), donc ils fuient **même quand le focus est dans le champ**. Le
comportement était erratique (« tantôt ajoute un livre, tantôt ouvre les
téléchargements, tantôt change d'onglet, souvent plusieurs à la fois ») selon le
timing exact des événements.

Aggravé par un bug d'ordre dans la 1ʳᵉ version du wedge (`scan-wedge.js`) : le
test `if (ev.ctrlKey) return;` (sans `preventDefault`) s'exécutait **avant** la
fenêtre de garde post-scan → le `LF`=Ctrl+J était laissé passer à chaque scan.

## Fix applied

Résolu par **FEAT-054** (`static/js/scan-wedge.js`, itération 2) : un écouteur
clavier global (« keyboard-wedge ») en **phase de capture** détecte la signature
d'un scan (rafale de frappes ≤ 50 ms) et **avale toute la salve** — chiffres ET
terminateurs de contrôle CR/LF/Tab — via `preventDefault()` +
`stopImmediatePropagation()`. Ordre corrigé : la **fenêtre de garde** post-scan
(~300 ms, qui absorbe le `LF` traînant après le `CR`) est testée **en premier**,
avant tout autre branchement ; en pleine rafale, **tout** est supprimé (y compris
un Ctrl-combo inséré par la douchette). Le code capté est ensuite routé : champ
de scan primaire (`data-wedge-primary` / bouton `.js-scan-handoff`) → remplir +
submit ; sinon → `core:search` (fiche notice via `classify_query`, ou fiche
membre `291`).

Effet de bord positif : le scan fonctionne désormais **sans cliquer** dans un
champ (cf. FEAT-054, 2ᵉ question de `temp.txt`).

Validé par Val 2026-07-08 (scan recherche, catalogage douchette, prêt/retour :
plus de page téléchargements ni de changement d'onglet).

## Spec section impacted

`SPEC_BIBLIOFELIA.md` §6.1 (recherche / scan) — comportement du scan douchette.
Détails d'implémentation : `docs/specs/FEAT-054-douchette-keyboard-wedge.md`.
