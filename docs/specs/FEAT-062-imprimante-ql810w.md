# FEAT-062 — Support imprimante Brother QL-810W (ruban continu 62 mm noir/rouge)

**Status:** IN PROGRESS (3e itération : étiquette 62 × 35 mm, une par page)
**Date:** 2026-08-18

## Contexte

Val a une **Brother QL-810Wc** chargée d'un **ruban continu 62 mm noir/rouge**
(type DK-22251), branchée en **USB sur le PC Bruxelles**. Il veut imprimer avec
elle les **étiquettes codes Ofelia** et les **cartes membres**.

Or tout l'existant (`apps/printing/services.py`, FEAT-038 + FEAT-039) ne sait
produire que des **planches A4** : étiquettes 70×42 mm en grille 3×7, cartes
membres 8 par feuille. Envoyer une planche A4 à une étiqueteuse à ruban ne
donne rien d'exploitable (mise à l'échelle, une seule étiquette utile par page).

### Contrainte matérielle constatée (2026-08-18)

- `Get-Printer` sur Bruxelles : `Brother QL-810W`, **port USB001**, non partagée.
- Scan du LAN depuis la Box (`192.168.0.0/24`, port 9100) : **un seul** hôte
  répond, `192.168.0.201` = **DCP-L3550CDW** (laser réseau). La QL-810W n'est
  **pas** joignable en réseau.

Conclusion : ni la Box (`192.168.0.147`) ni les instances Avignon ne peuvent
piloter la QL-810W directement (ni CUPS, ni raster `brother_ql` sur TCP 9100).
Le seul chemin qui fonctionne aujourd'hui — et qui fonctionne aussi bien sur la
Box que sur les instances hébergées — est le **navigateur du poste sur lequel
l'imprimante est installée**.

## Comportement

### Chemin d'impression

```
BibliOfelia (Box ou Avignon)
        |  PDF à la géométrie exacte du ruban, 1 étiquette par page
        v
  Navigateur du poste (Bruxelles)  --USB-->  QL-810W
        dialogue d'impression, pilote Brother
```

Décision Val 2026-08-18 : on construit **ce chemin uniquement**. Le backend
d'impression directe (raster `brother_ql`) est écarté — il imposerait de mettre
la QL en Wi-Fi et resterait inutilisable depuis les instances Avignon.

### Étiquettes codes Ofelia — ruban 62 × 35 mm

Page PDF = **62 mm de large × 35 mm de long**, **une étiquette par page**,
marges nulles. La longueur correspond à la coupe réglée dans le pilote Brother
de Val : une page = une étiquette = une coupe.

Deux retraits de sécurité, sans lesquels le pilote rogne le dessin :

- **2 mm à gauche et à droite** — la zone imprimable réelle d'un ruban 62 mm
  fait ~58,9 mm (`ROLL_INSET_MM`).
- **3 mm en tête et en pied de bande** — marge d'avance papier des QL sur ruban
  continu (`ROLL_FEED_INSET_MM`).

Le gabarit se cale sur la zone utile restante, pas sur les bords de page : si
Val raccourcit l'étiquette dans les réglages, le code-barres et le pied restent
placés correctement.

**Révision après le 1er test de Val (2026-08-18)** — l'étiquette est
**entièrement monochrome** et **typographiquement uniforme** :

- Bandeau : logo Ofelia **en niveaux de gris** à gauche
  (`_static_logo_grayscale`), nom de la bibliothèque à droite
- Titre, 2 lignes max, **pleine largeur** : le retour à la ligne est calculé
  sur la **largeur mesurée** du texte (`_wrap_to_width` + `pdfmetrics`) et non
  plus sur un quota de caractères — un titre étroit remplit désormais les
  58 mm utiles au lieu de casser au bout de 38 signes
- Auteurs, 1 ligne, **en italique** : seule différence typographique de
  l'étiquette
- Le bloc titre + auteurs est **centré verticalement** entre le bandeau et le
  code-barres, pour qu'un titre d'une seule ligne ne creuse pas un trou
- Code-barres EAN13 centré, noir
- Pied : code Ofelia (EAN13) à gauche, code Location à droite

Tous les textes — nom de la bibliothèque, titre, auteurs, code Ofelia,
emplacement — partagent la **même police et la même taille**
(`Helvetica-Bold` 7,5 pt, `Helvetica-BoldOblique` pour les auteurs).
L'**identifiant interne** (`internal_id`) a été **retiré** : il ne servait à
personne sur l'étiquette.

### Cartes membres — ruban 62 × 89 mm, dessin couché

Page PDF = **62 mm de large × 89 mm de long**. Cette longueur n'est pas
arbitraire : le pilote Brother déclare son format continu « 62mm » à Windows en
**62 × 89,9 mm**. En restant juste en dessous, la page tombe sur le format natif
du pilote — plus rien à saisir dans le dialogue système — tout en logeant les
85,6 mm de la carte (marge d'avance ramenée à 1,7 mm, `ROLL_CARD_FEED_INSET_MM`). Le dessin est **tourné à 90°**
pour produire une carte de **85,6 × 54 mm**, soit le format carte bancaire
exact : l'étiquette se colle sur un carton puis se plastifie.

Mise en page reprise de FEAT-038 (identité visuelle inchangée) :

- Fond crème `rgb(248, 238, 229)`
- Logo OFELIA centré en filigrane
- Photo du membre en haut-gauche (20 mm) si présente
- Bloc droit : nom de la bibliothèque, « Carte de membre » (**rouge** si
  bichromie), nom prénom, catégorie, « Valide jusqu'au … »
- Code-barres EAN13 + numéro de carte en bas-droite — **toujours noir**
- Langue préférée en bas-gauche

### Bichromie noir/rouge — cartes membres uniquement

Le pilote Windows de la QL-810W imprime en rouge les éléments **rouge pur**
(255, 0, 0) du document quand un ruban DK-22251 est chargé. Le PDF dessine donc
ses accents en `Color(1, 0, 0)`. Réglage `two_color` : décoché, tout sort en
noir.

Depuis les retours de Val, **les étiquettes n'utilisent plus le rouge du tout**
(le code Location y était rouge). `_accent()` ne sert donc plus qu'à la mention
« Carte de membre » des cartes. Le **code-barres n'est jamais rouge**, sur
aucune sortie : une barre rouge n'est plus lue par une douchette.

### Déclenchement

Chaque écran de sélection (`printing:labels`, `printing:cards`) gagne un bouton
**« Ruban 62 mm (Brother QL) »** à côté de « Générer PDF ». Il ouvre le PDF
directement dans un nouvel onglet (`formtarget="_blank"`), le bibliothécaire
imprime depuis le visualiseur.

**Une page intermédiaire a existé puis été retirée** (demande Val, 2026-08-18) :
elle embarquait le PDF dans une `iframe` et appelait `print()` pour ouvrir le
dialogue tout seul. Val la trouvait inutile — le visualiseur PDF et le dialogue
d'impression restent de toute façon à traverser, et eux ne peuvent pas être
supprimés : le dialogue d'impression est imposé par le navigateur (aucune page
web ne peut imprimer sans validation de l'utilisateur), et celui du pilote
Brother par Windows.

## Spec technique

- **Setting `roll_printer_format`** (JSON) :
  `{enabled, tape_width_mm, label_length_mm, card_length_mm, two_color, show_logo}`
  — défauts `{true, 62, 35, 89, true, true}`.
- `apps/core/forms.py` : `RollPrinterFormatForm` (KEY = `roll_printer_format`).
- `apps/core/admin_views.py` : section `printing_roll`
  → « Impressions — Ruban continu (Brother QL) ».
- `seed_defaults.py` : seed du nouveau setting.
- `apps/printing/services.py` :
  - `_roll_settings()` — lecture + défauts
  - `render_item_labels_roll_pdf(items)` — 1 page par exemplaire
  - `render_member_cards_roll_pdf(members)` — 1 page par membre, dessin tourné
  - `_draw_roll_item_label(...)`, `_draw_roll_member_card(...)`
  - `_accent(two_color)` — rouge pur ou noir (cartes uniquement)
  - `_text_width`, `_fit_to_width`, `_wrap_to_width` — mise en page mesurée à
    la vraie largeur du texte (`reportlab.pdfbase.pdfmetrics`)
  - `_static_logo_grayscale(name)` — logo converti en gris, alpha conservé
    (Pillow) : l'étiqueteuse thermique ne connaît pas la couleur
  - réutilise `_barcode_image`, `_library_name`
- `apps/printing/views.py` : `labels_roll_pdf`, `cards_roll_pdf`.
- `apps/printing/urls.py` : `labels-roll.pdf`, `cards-roll.pdf`.
- `templates/printing/labels_picker.html` + `cards_picker.html` : bouton ruban
  (`formtarget="_blank"`), affiché seulement si `roll_printer_format.enabled`.

### Réglage côté Windows (poste Bruxelles)

Le PDF donne la géométrie ; le pilote doit être accordé une fois :

1. Panneau de configuration → Imprimantes → **Brother QL-810W** → Options
   d'impression → format de papier **62 mm** (ruban continu), longueur au choix.
2. Dans le dialogue Chrome : **Échelle 100 %** (pas « Ajuster à la page »),
   marges **Aucune**.
3. Coupe automatique activée si l'on veut une étiquette détachée par page.

## Impact sur l'existant

- Si le ruban configuré est trop étroit ou trop court pour une carte 85,6 × 54,
  le dessin est réduit homothétiquement plutôt que débordé.
- **Aucune modification** des rendus A4 existants (`render_item_labels_pdf`,
  `render_member_cards_pdf`) : les deux formats coexistent.
- `submit_to_cups()` reste en place, inchangé et non utilisé par ce chemin.
- Nouveau `Setting` seedé ; instances existantes prennent les défauts via
  `_roll_settings()` sans migration.
- Tests : `apps/printing/tests/test_roll_printing.py`.
- SPEC §6.7 à mettre à jour.
- Guide utilisateur : `impressions/etiquettes.md` et `impressions/cartes.md`
  (×4 langues).

## Orientation du dialogue — piste du groupage, abandonnée

**Symptôme initial (Val, 2026-08-18)** : il fallait basculer le dialogue
d'impression sur « portrait ». Sans ça, la sortie était tournée de 90° et seuls
les 36 premiers millimètres du texte étaient imprimés.

**Cause** : Chrome déduit l'orientation par défaut des **dimensions de la page
PDF**. Une étiquette plus large que haute → « paysage ». Aucun attribut PDF ne
permet d'imposer l'orientation (`/Rotate` change les dimensions apparentes et
casserait le calage 1:1).

**Piste essayée puis abandonnée** : empiler 2 étiquettes sur une page de
62 × 72 mm, plus haute que large, pour que Chrome ouvre en portrait tout seul.
Au test, ça ne marche pas : **la QL est réglée pour couper tous les 35 mm** et
ne peut pas honorer une page plus longue — elle a essayé de faire tenir les
2 étiquettes sur une seule. Val a par ailleurs constaté que « portrait » était
**déjà sélectionné** dans son dialogue (mémorisé d'une impression précédente).

**Décision** : une étiquette = une page = une coupe, 62 × 35 mm. Le code de
groupage et le réglage `portrait_pages` ont été retirés. Si le dialogue revient
en paysage, le geste reste un clic — et il est documenté dans le guide.

Les cartes membres ne sont pas concernées par l'orientation : 62 × 89 mm est
déjà plus haut que large.

## Réduire les manipulations dans le dialogue d'impression

**Constat Val (2026-08-18, après validation du contenu)** : pour chaque
impression il faut passer par « use system dialog » puis « more settings » afin
de choisir l'orientation portrait et la hauteur (35 mm pour les livres, 90 pour
les cartes). L'imprimante ne déduit pas la longueur de coupe de la forme du
document.

C'est exact et ce n'est pas contournable côté serveur : la **longueur de coupe
et l'orientation sont des propriétés du pilote Windows** (DEVMODE), pas du PDF.
Un document ne peut que proposer une géométrie.

Deux leviers, dans l'ordre de rentabilité :

1. **Aligner la carte sur le format natif du pilote** (fait) — l'inventaire des
   formats exposés par le pilote (`System.Drawing.Printing.PrinterSettings`,
   interrogé sur Bruxelles) montre un format continu « 62mm » à
   **62 × 89,9 mm**. La carte passe donc de 92 à **89 mm** : plus de hauteur à
   saisir pour les cartes, et la page reste portrait.
2. **Deux objets imprimante Windows sur le même pilote et le même port**, par
   exemple « Brother QL-810W — Étiquettes » (62 mm, 35 mm, portrait) et
   « Brother QL-810W — Cartes » (62 mm, 89 mm, portrait), chacun avec ses
   *Printing Defaults*. Chrome mémorise ses réglages **par destination** :
   choisir l'imprimante suffit alors, sans passer par le dialogue système.
   C'est ce qui explique le symptôme — en alternant étiquettes et cartes sur la
   **même** imprimante, les réglages mémorisés sont écrasés à chaque fois.

Le second levier se crée avec `Add-Printer -Name … -DriverName 'Brother
QL-810W' -PortName USB001` ; les *Printing Defaults* (orientation, longueur) se
règlent ensuite une fois dans l'interface du pilote — l'API PowerShell ne les
expose pas. **Non fait : ça touche le poste de Val, en attente de son accord.**
