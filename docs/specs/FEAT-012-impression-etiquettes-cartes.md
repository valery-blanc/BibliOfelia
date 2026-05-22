# FEAT-012 — Impression étiquettes + cartes membres

Statut : DONE (validé Val 2026-05-22)
SPEC : §6.7

## Contexte

Imprimer les étiquettes exemplaires (avec EAN13 lisible + code-barres,
titre tronqué, location, internal_id) et les cartes membres (8/A4 par
défaut). Cible Pi 5 + imprimante thermique USB via CUPS ; fallback PDF
pour dev Windows et pour le mode « sans imprimante ».

## Implémentation

### `apps/printing/services.py`

- `render_item_labels_pdf(items)` : génère un PDF A4 (3 col × 8 lignes
  par défaut = 24 étiquettes, dimensions 70 × 36 mm). Si le format est
  personnalisé via `Setting.label_format` (`item_width_mm`,
  `item_height_mm`), les colonnes/lignes sont recalculées
  automatiquement. Chaque étiquette comporte :
  titre tronqué, auteurs, code-barres EAN13 (image PNG en mémoire via
  `python-barcode`), EAN13 lisible, code Location, internal_id.
- `render_member_cards_pdf(members)` : grille 2 colonnes × N lignes
  selon `card_per_a4` (4, 6, 8 ou 10). Chaque carte : nom complet,
  catégorie, expiration, langue préférée (pictogramme = code 2
  lettres), code-barres + numéro EAN13.
- `submit_to_cups(pdf, title)` : envoi optionnel via `pycups`
  (paquet présent dans l'image Linux uniquement). En dev Windows ou en
  l'absence de CUPS, retourne `sent=False` et le PDF est servi en
  fallback.

### `apps/printing/views.py`

- `labels_picker` : sélection des exemplaires (filtre par emplacement
  + bouton « derniers ajouts »).
- `labels_pdf` : génère et renvoie le PDF en `inline`.
- `labels_send` : tente CUPS, fallback PDF si non disponible.
- `cards_picker` / `cards_pdf` : équivalent pour les usagers.

### Templates

- `templates/printing/labels_picker.html` : tableau avec checkboxes,
  bouton « PDF » + bouton « CUPS ».
- `templates/printing/cards_picker.html` : idem pour les cartes.

### Accès

`@require_role(Role.LIBRARIAN, Role.SUPERADMIN)` sur toutes les vues.

## Décisions

- **Format paramétrable mais valeurs par défaut intactes** : tant que
  le wizard (FEAT-015) ne renseigne pas `Setting.label_format`, les
  réglages par défaut s'appliquent (70 × 36 mm × 24 étiquettes/A4).
- **EAN13 image** : `python-barcode` produit un PNG en mémoire que
  ReportLab insère via `ImageReader` (pas de fichier temporaire).
- **pycups optionnel** : non importé au top-level pour ne pas bloquer
  le dev Windows ; importé dans `submit_to_cups` et la branche échoue
  silencieusement en retournant `PrintResult(sent=False)`.
