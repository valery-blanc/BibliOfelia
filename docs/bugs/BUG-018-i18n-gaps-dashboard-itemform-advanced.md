# BUG-018 — Chaînes non traduites : alerte dashboard, formulaire « Ajouter des exemplaires », libellé Administration Django

**Status:** DONE
**Date:** 2026-05-30

## Symptom

En navigation espagnole (et EN/MG), plusieurs chaînes restaient en français ou
en anglais :

- **A. Tableau de bord** — l'alerte de relance affichait le texte FR figé
  « 1 membre à appeler pour qu'il vienne chercher son livre » au lieu d'être
  traduit.
- **B. Formulaire « Ajouter des exemplaires »** (`ItemBulkCreateForm`) — les
  libellés `Location`, `State`, `Acquisition date`, `Acquisition source`,
  `Donor`, `Notes` apparaissaient en **anglais** (noms de champs Django bruts).
- **C. Scanner caméra** — symptôme rapporté « ⏳ En attente d'OfeliaScan… » +
  bouton « Annuler » en français en UI espagnole.
- **D. Avancé → Administration Django** — la description mentionnait
  « (réservé Claude / support distant) ». À remplacer par « réservé au support
  technique » (changement de libellé + traduction).

## Root cause

- **A.** Le `blocktrans count` du dashboard était bien marqué traduisible, mais
  les `msgstr[0]`/`msgstr[1]` étaient **vides** dans `en`/`es`/`mg`. Le script
  `apply_translations.py` ne traite pas les entrées plurielles (`msgstr[N]`),
  d'où l'oubli. (Le gate `i18n_check.py` ne couvre pas non plus les pluriels —
  voir « Limites connues ».)
- **B.** Le modèle `Item` ne définit pas de `verbose_name` sur ses champs, et
  `ItemForm.Meta` ne fournissait pas de `labels`. Django génère donc les
  libellés à partir des noms de champs (anglais), non traduisibles.
- **C.** Faux positif : FEAT-044 a **retiré** tout le handoff OfeliaScan du flux
  de scan du site. Le texte « En attente d'OfeliaScan… » n'existe plus dans le
  code ; le bouton « Annuler » de la modale caméra (`#scan-mode-i18n` →
  `t("cancel", …)`) est déjà traduit (`Cancel`/`Cancelar`/`Foano`). Le symptôme
  provenait d'une **build périmée de la Box** (templates/JS embarqués au build —
  cf. `MEMORY/project_pi_templates_baked`). Correctif = rebuild.
- **D.** Simple chaîne source à modifier puis traduire.

## Fix applied

- **A.** Renseigné `msgstr[0]`/`msgstr[1]` du `blocktrans` dashboard dans
  `locale/{en,es,mg}/LC_MESSAGES/django.po` (édition directe, le script de batch
  ne gérant pas les pluriels).
- **B.** Ajouté un dict `labels` traduit (`_()`) à `ItemForm.Meta`
  (`apps/catalog/forms.py`) : Emplacement, État, Date d'acquisition, Source
  d'acquisition, Donateur, Notes. Hérité par `ItemBulkCreateForm`. Ajouté au
  passage `format="%Y-%m-%d"` au `DateInput` de `acquisition_date` (même classe
  de bug que BUG-015, non couverte à l'époque).
- **C.** Aucun changement de code nécessaire (déjà propre) → rebuild Box.
- **D.** `templates/core/advanced.html` : « (réservé Claude / support distant) »
  → « (réservé au support technique) ».
- Traductions EN/ES/MG des nouvelles chaînes via
  `scripts/translations_sprint17.py`. Gate `i18n_check.py` → 0.

## Limites connues

`i18n_check.py` et `apply_translations.py` ignorent les entrées plurielles
(`msgstr[N]`). Les traductions plurielles doivent être saisies à la main dans
les `.po`. À industrialiser si d'autres `blocktrans count` apparaissent.

## Spec section impacted

`SPEC §6.1` (formulaire exemplaires), `§7` (dashboard / relances), `§10`
(Avancé / Administration Django), `§i18n` (gate traductions).
