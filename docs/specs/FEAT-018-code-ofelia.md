# FEAT-018 — Terminologie « code Ofelia » + rapport d'inventaire enrichi

Statut : DONE (validé Val 2026-05-22)
SPEC : §5.2, §6.5, §6.7

## Contexte

Demande de Val (modification d'affichage). L'identifiant EAN13 interne d'un
exemplaire (champ `Item.ean13`, préfixe 290) est un code propre au projet
Ofelia. Le libellé technique « EAN13 » affiché dans l'interface n'est pas
parlant pour les bibliothécaires. Il est désormais appelé « **code Ofelia** »
partout dans l'UI.

En parallèle, le rapport d'inventaire (`/inventory/<pk>/report/`) n'affichait
que le code interne (`OFL-…`) des exemplaires en écart. Val veut y voir aussi
le code Ofelia et l'ISBN pour faciliter l'identification physique du document.

## Comportement

### Renommage du libellé « EAN13 » → « code Ofelia »

Modification purement d'affichage : le champ modèle `Item.ean13`, le préfixe
`ITEM_EAN13_PREFIX`, la norme du code-barres et les helpers `apps/core/ean.py`
sont inchangés. Seuls les libellés visibles changent.

- `templates/catalog/record_detail.html` — en-tête de colonne du tableau des
  exemplaires.
- `templates/printing/labels_picker.html` — en-tête de colonne.
- `templates/reports/inactive_list.html` — en-tête de colonne.
- `templates/core/advanced.html` — description de l'outil d'impression
  (« code Ofelia + titre + emplacement »).

À ne pas confondre avec le « code interne » (`Item.internal_id`, format
`OFL-AAAAMMJJ-NNNN`), qui reste un identifiant distinct conservant son libellé.

### Page d'impression des étiquettes

`templates/printing/labels_picker.html` : le titre de la page (et l'onglet
navigateur) devient « **Étiquettes codes Ofelia** ». Le lien d'accès depuis
l'onglet « Avancé » (`templates/core/advanced.html`) est aligné.

### Page de session d'inventaire (`/inventory/<pk>/`)

`templates/inventory/session_detail.html` :
- titre de section « Pointer un exemplaire » → « **Scanner ou saisir le code
  Ofelia d'un document** » ;
- placeholder du champ de saisie « Scanner le code-barres » → « **Scanner le
  code Ofelia** ».

### Rapport d'inventaire (`/inventory/<pk>/report/`)

`templates/inventory/session_report.html` :
- tableau des **exemplaires manquants** : ajout des colonnes « Code Ofelia »
  (`item.ean13`) et « ISBN » (`item.record.isbn_13`, `—` si absent) ;
- liste des **exemplaires hors périmètre** : ajout du code Ofelia et de l'ISBN
  en ligne.

Aucune modification de `apps/inventory/services.py` : `build_report()` charge
déjà `record` via `select_related`, l'ISBN est donc disponible sans requête
supplémentaire.

## i18n

Nouvelles chaînes traduites EN/ES/MG (0 fuzzy, 0 untranslated) :
« Code Ofelia », « ISBN », « Étiquettes codes Ofelia », « Scanner ou saisir le
code Ofelia d'un document », « Scanner le code Ofelia », et la description de
l'outil d'impression. `makemessages -a --no-obsolete` + `compilemessages`.

## Impact

- Aucune migration, aucun changement de modèle ou d'API.
- Tests inchangés : `apps/inventory`, `apps/printing`, `apps/core/tests/test_ui.py`
  — 22 passed.
