# FEAT-075 — Écrans d'étiquettes séparés + cote condensée

- **Statut** : DONE
- **Sprint** : 29
- **Demandé par** : Val (2026-08-22)
- **Sections spec impactées** : §6.7, §11.1 (menu Avancé)

## Contexte

Trois demandes qui portent toutes sur l'impression des étiquettes :

1. **Deux écrans au lieu d'un.** L'écran « Étiquettes codes Ofelia » portait
   aussi le bouton « Étiquettes de tranche » (FEAT-068). Deux étiquettes de
   nature différente — le code-barres à coller à l'intérieur, la cote à coller
   sur la tranche — partageaient un écran et un seul point d'entrée dans le menu
   Avancé. Val demande **deux pages** et **deux entrées de menu**, avec le
   **même fonctionnement général** (donc le même code de sélection).
2. **« Générer PDF » → « PDF A4 ».** Le libellé ne disait pas ce qui sortait ;
   à côté d'un bouton « Ruban 62 mm », « PDF A4 » nomme le format.
3. **Cote plus étroite.** Les cotes sortaient trop larges pour la tranche des
   livres minces. Demande : **40 % de largeur en moins, hauteur inchangée** —
   la lisibilité à un mètre du rayon tient à la hauteur des capitales, pas à
   leur largeur.

Le chiffre a été précisé en cours de route : 35 % dans la première demande,
**40 %** après essai sur une vraie tranche (Val, 2026-08-22). La planche A4 des
cotes, elle, a été demandée après coup — la première version n'offrait que le
ruban.

## Comportement

### Deux écrans

| Écran | Route | Boutons |
|---|---|---|
| **Étiquettes codes Ofelia** | `printing:labels` | « PDF A4 », « Ruban 62 mm (Brother QL) » |
| **Étiquettes de tranche** | `printing:spine_labels` | « PDF A4 », « Ruban 62 mm (Brother QL) » |

Même barre de filtres (emplacement, derniers ajouts), même table, même case
« tout cocher », même prise en charge du paramètre `?catalog_session=N`
(FEAT-046) : ce qui change, ce sont les boutons et deux colonnes.

L'écran des cotes affiche en plus **« Catégorie »** et **« Cote imprimée »** à
la place du code Ofelia, du code externe et de la provenance : le bibliothécaire
voit avant d'imprimer ce qui sortira, et repère les exemplaires dont la
catégorie n'a pas d'abréviation (`aucune`) au lieu de le découvrir sur le
message d'erreur.

**Planche A4 de cotes** — même grille que les étiquettes « code Ofelia »
(`item_label_format`, 80 × 40 mm par défaut, soit 3 × 7 = 21 par page), cadre de
découpe gris clair, cote centrée et condensée dans chaque cellule. Une seule
géométrie de planche à régler pour les deux sortes d'étiquettes.

La cote y est dessinée à **70 % de la taille qui remplirait la cellule**
(`SPINE_A4_SIZE_SCALE`), hauteur et largeur — une cellule A4 (70 × 42 mm sur les
instances) est plus grande qu'une étiquette de ruban, et remplie à ras bord la
cote sortait démesurée (Val, 2026-08-22). Le **découpage en lignes n'est pas
recalculé** : on réduit le dessin, on ne le remet pas en page. Mesures sur une
cellule 70 × 42 mm :

| Cote | Sans réduction | Avec réduction |
|---|---|---|
| `PER` | 38,3 × 22,4 mm | **26,8 × 15,6 mm** |
| `RO FI ADO` | 31,0 × 14,0 mm | **21,7 × 9,8 mm** |
| `BD JEUNESSE` | 38,4 × 8,6 mm | **26,9 × 6,0 mm** |

La réduction ne s'applique **qu'à la planche A4** : l'étiquette de ruban garde
sa taille pleine, verrouillée par `test_roll_label_keeps_its_full_size`.

Quand l'impression ruban est désactivée (`roll_printer_format.enabled = false`),
seul le bouton « PDF A4 » subsiste et un encadré dit où réactiver le ruban.

### Cote condensée

Le texte est dessiné à **60 % de sa largeur naturelle, à hauteur inchangée**.
La **taille de police ne change pas** : la condensation sert à écrire plus
étroit, pas plus gros. Les tailles ci-dessous sont exactement celles d'avant
FEAT-075. Mesures sur une étiquette 62 × 35 mm (zone utile 58 × 29 mm) :

| Cote | Taille | Lignes | Largeur avant | Largeur après | Hauteur capitale |
|---|---|---|---|---|---|
| `PER` | 79,5 pt | 1 | 57,7 mm | **34,6 mm** | 20,2 mm |
| `RO FI ADO` | 44,5 pt | 2 | 41,9 mm | **25,1 mm** | 11,3 mm |
| `BD JEUNESSE` | 30,5 pt | 2 | 57,4 mm | **34,4 mm** | 7,7 mm |
| `BANDES DESSINEES JEUNESSE` | 27,5 pt | 3 | 55,5 mm | **33,3 mm** | 7,0 mm |

**Piège évité, et commis une fois** : la première implémentation accordait à
`spine_layout()` une largeur gonflée (`inner_w / SPINE_WIDTH_SCALE`), ce qui la
faisait choisir une police plus grande — le texte sortait plus haut et pas plus
étroit, l'inverse de la demande. `spine_layout()` doit recevoir la largeur utile
**réelle** ; la condensation n'intervient qu'au tracé. Un test
(`test_font_size_is_computed_on_the_real_width_not_a_widened_one`) verrouille ce
point en relisant la taille de police dans le flux PDF.

## Spec technique

- `apps/printing/views.py` :
  - `_picker_context(request)` — la sélection d'exemplaires, extraite de
    `labels_picker` et partagée par les deux écrans ;
  - `labels_picker` et `spine_labels_picker` n'ajoutent que titre, icône,
    `form_action` et `picker_url`.
- `apps/printing/urls.py` : route `spine-labels/` → `printing:spine_labels`.
- Templates : `printing/_picker_base.html` (base commune) ;
  `printing/labels_picker.html` et `printing/spine_labels_picker.html`
  n'overrident que `picker_buttons`, `picker_notice`, `extra_head`,
  `extra_cells`.
- `apps/printing/services.py` : `SPINE_WIDTH_SCALE = 0.60` ;
  `SPINE_A4_SIZE_SCALE = 0.70` ; `_draw_spine_text()` (partagé ruban / A4)
  encadre le tracé d'un `saveState()` / `scale(0.60, 1)` / `restoreState()` et
  accepte un `size_scale` qui réduit le dessin entier ;
  `render_spine_labels_pdf(items)` pour la planche A4. `spine_layout()` est **inchangée** : elle raisonne toujours sur
  la largeur utile réelle, donc la taille de police retenue est la même qu'avant
  FEAT-075.
- `apps/printing/views.py` : `_printable_spine_items()` (garde « aucune cote »
  partagée), vues `spine_labels_pdf` et `spine_labels_roll_pdf`.
- `apps/printing/urls.py` : route `spine-labels.pdf` → `printing:spine_labels_pdf`.

**Pourquoi une transformation du canvas et pas une police étroite ?** ReportLab
n'embarque aucune variante *condensed* : les 14 polices Type1 standard n'en ont
pas, et `fonts-dejavu-core` (le seul jeu présent dans l'image Docker) non plus.
Ajouter `fonts-dejavu-extra` pour `DejaVuSansCondensed` aurait alourdi l'image
pour ne gagner qu'environ 10 % de largeur — loin des 40 % demandés, et
approximatif là où la transformation est exacte. La contrainte hors-ligne
interdisant tout téléchargement de police, la transformation est la seule
solution à la fois exacte et sans dépendance.

**Effet de bord accepté** : les jambages deviennent 40 % plus fins
horizontalement, aspect classique d'une fausse condensation. Sur une étiqueteuse
thermique, à ces corps (27 à 96 pt), c'est invisible à l'œil.

## Impact sur l'existant

- Le bouton « Étiquettes de tranche » **disparaît** de l'écran des codes
  Ofelia : chaque écran imprime sa sorte d'étiquette. Les liens
  « Imprimer les étiquettes de ce lot » des sessions de catalogage continuent de
  pointer sur l'écran des codes Ofelia.
- `printing:spine_labels_roll_pdf` renvoie désormais sur `printing:spine_labels`
  en cas d'erreur (sélection vide, aucune abréviation), plus sur l'écran des
  codes Ofelia.
- `templates/printing/cards_picker.html` : « Générer PDF » → « PDF A4 » aussi,
  pour que le même bouton ne porte pas deux noms selon l'écran.
- Aucune migration, aucun changement de réglage.

## Tests

`apps/printing/tests/test_spine_labels.py` — écran dédié, colonne « Cote
imprimée », absence du bouton de tranche sur l'écran des codes Ofelia, encadré
d'explication quand le ruban est désactivé, planche A4 (format de page, 21 par
page, exemplaires sans cote ignorés, garde « aucune cote »), taille de police
inchangée et calculée sur la largeur réelle, largeur tracée à 60 %, matrice
`.6 0 0 1 0 0 cm` présente dans le flux PDF décodé.
