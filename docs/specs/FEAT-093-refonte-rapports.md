# FEAT-093 — Refonte complète des rapports

**Status:** DONE
**Date:** 2026-09-09 → 2026-09-10
**Sprint:** 34

## Context

Les rapports actuels (`/reports/`) sont un reliquat du Sprint 2 : trois listes
imprimables, quatre exports CSV et un PDF annuel de huit lignes. Ils ne
racontent rien de ce que la bibliothèque fait réellement — ni le fonds, ni les
usagers, ni la fréquentation, ni le travail de l'équipe, ni l'argent — alors que
toutes ces données existent en base depuis les Sprints 28 à 33.

Trois publics les attendent :

- **les bénévoles et employés** de la bibliothèque, dont certains ont un faible
  niveau d'éducation, très peu l'habitude des ordinateurs et un accès Internet
  limité ;
- **les membres du comité** de l'association Ofelia ;
- **les donateurs et bailleurs de fonds**, à qui il faut pouvoir tendre un PDF.

Deux sources ont nourri la refonte : les copies d'écran d'un logiciel de
ludothèque (`docs/specs/Ecrans_ludotheque.pdf`, 21 pages : tableau de bord,
bilan annuel, fréquentation par âge, locations par jour d'ouverture, membres par
localité, caisse journalière, heures de travail) et la liste de chiffres
demandée par Val dans `temp.txt`.

Rien n'oblige à reproduire ces écrans tels quels : l'objectif est **l'accès
simple et ergonomique aux données**, pas la copie d'une interface Windows de
2005.

## Principes retenus

1. **Un écran = un sujet, avec un titre en français ordinaire.** « Le fonds »,
   « Les prêts », « L'argent » — pas « Statistiques bibliographiques ».
2. **La période se choisit en un clic.** Quatre gros boutons (mois en cours,
   année en cours, mois précédent, année précédente) et, en dessous, une saisie
   libre « entre … et … » pré-remplie sur les 12 derniers mois.
3. **Des graphes simples** — histogramme, camembert, et courbes quand plusieurs
   séries se suivent dans le temps. Rien d'autre. Chaque part d'un camembert
   porte son étiquette, **posée à l'extérieur et reliée par un trait**, jamais
   dans une légende séparée.
4. **Chaque écran s'exporte en PDF et en Excel**, et l'export contient
   exactement ce que l'écran affiche. Pas d'export sans écran, pas d'écran sans
   les deux exports. **Chaque sous-rapport s'exporte aussi seul.**
5. **La charte OFELIA partout**, écrans et PDF — couleurs de
   `static/css/ofelia.css` (bordeaux `#6B2138`), **polices du site** (Bricolage
   Grotesque, DM Sans) et **logo blanc** sur le bandeau.
6. **Aucune dépendance réseau.** Les graphes sont produits par le serveur ; la
   Box travaille hors ligne.

## Behavior

### Le hub `/reports/`

Deux groupes, pour séparer ce qu'on consulte tous les jours de ce qu'on
consulte une fois par mois :

**Tous les jours — les listes de travail**
| Écran | Ce qu'on y voit |
|---|---|
| Les retards | Prêts en retard, du plus ancien au plus récent |
| Les réservations à retirer | Livres mis de côté et qui attend |
| Les inactifs | Usagers et livres sans mouvement, triables par catégorie |

**Comprendre la bibliothèque — les chiffres**
| Écran | Ce qu'on y voit |
|---|---|
| Vue d'ensemble | Le bilan : tous les chiffres clés sur une page |
| Le fonds | Combien de livres, de quelle sorte, dans quel état, d'où ils viennent |
| Les prêts | Combien de prêts, les livres les plus et les moins empruntés |
| Les usagers | Combien de personnes, qui elles sont, qui arrive et qui part |
| La fréquentation | Qui vient à la bibliothèque et aux animations, par âge |
| Le travail de l'équipe | Les heures faites, par nature et par personne |
| L'argent | Ce qui a été facturé, encaissé, et ce qui reste dû |

### Le sélecteur de période

Présent en tête de chaque écran de chiffres, dans un cadre :

```
[ septembre 2026 ]  [ 2026 ]  [ août 2026 ]  [ 2025 ]

Entre  [01/09/2025]  et  [09/09/2026]   [ Valider ]
```

- Les quatre boutons portent le **libellé réel** de la période, pas « mois en
  cours » : un bénévole lit « août 2026 » et sait immédiatement de quoi on
  parle. Ils se recalculent à chaque affichage.
- Le bouton de la période affichée est mis en évidence.
- La saisie libre est pré-remplie sur `aujourd'hui − 365 jours` → `aujourd'hui`,
  qui est aussi **la période par défaut** quand on arrive sur l'écran sans rien
  choisir (libellé : « 12 derniers mois »).
- Contrat d'URL : `?p=month|prev_month|year|prev_year`, ou
  `?p=custom&start=YYYY-MM-DD&end=YYYY-MM-DD`. Une période invalide
  (fin avant début, date illisible) retombe sur les 12 derniers mois avec un
  message, sans page d'erreur.

Les trois listes de travail n'ont pas de période : elles décrivent
*aujourd'hui*. Elles gardent leur seul réglage (seuil de retard, nombre de jours
d'inactivité) et leurs deux exports.

### Les exports

Deux boutons en tête de chaque écran : **Imprimer (PDF)** et **Fichier Excel**.
Ils reprennent les paramètres de l'écran (période, seuil, catégorie), donc le
fichier obtenu correspond au dernier écran vu.

- **PDF** — A4 portrait, bandeau bordeaux avec le logo et le nom de la
  bibliothèque, titre de l'écran, période en toutes lettres, les compteurs, les
  graphes, les tableaux, pied de page « Édité par BibliOfelia le … ».
- **Excel** — un onglet « Résumé » avec les compteurs, puis un onglet par
  sous-rapport. Les graphes sortent en graphique Excel natif au-dessus de leurs
  données, de sorte qu'un membre du comité puisse recopier le camembert dans
  une présentation.

**Chaque sous-rapport a en plus ses propres exports**, en deux liens discrets
sous son titre (`?block=<clé>`) : un bénévole qui veut imprimer la seule liste
des impayés n'a pas à sortir les huit tableaux de l'écran.

## Contenu écran par écran

Les définitions ambiguës sont fixées ici et nulle part ailleurs.

### 1. Vue d'ensemble — `overview`

La page qu'on imprime pour un donateur. Elle ne montre rien qui ne soit
détaillé ailleurs ; elle rassemble.

**Aujourd'hui** (hors période) : livres prêtés en ce moment · livres
disponibles · livres en retard · usagers inscrits · familles · personnes
couvertes.

**Sur la période** : prêts · nouveaux livres · nouveaux usagers · participations
aux animations · heures de travail de l'équipe · recettes encaissées.

**Graphes** : prêts mois par mois (histogramme) ; le fonds par catégorie
(camembert).

**Les livres sortis à la fin de chaque mois** (histogramme) — pour chaque mois
de la période, le nombre de livres qui n'étaient pas rentrés le dernier jour du
mois. C'est le « graphe dans le passé » demandé par Val ; il se reconstitue
depuis `Loan.loan_date` et `return_date` seuls, sans stocker d'historique, ce
qui permet de remonter aussi loin que le journal des prêts. Le nombre de livres
disponibles à la même date se lit par différence avec le fonds, affiché juste
au-dessus ; le porter en seconde série sur les mêmes barres écrasait la
première, le fonds étant d'un ordre de grandeur au-dessus des prêts en cours.

**Tableau « Le bilan en un tableau »** : une ligne par chiffre, deux colonnes
(intitulé, valeur). C'est l'équivalent du *Bilan annuel* du logiciel de
ludothèque, en une seule page.

### 2. Le fonds — `collection`

**Compteurs** : exemplaires · disponibles · prêtés · mis de côté · en
réparation · perdus · pilonnés · notices.

**Graphes** : par catégorie (camembert) · par type de document (camembert) ·
par état (camembert) · par langue (histogramme).

**Tableaux**
- Nombre de livres par catégorie — nombre d'exemplaires, part du fonds, prêts
  sur la période, **rotation** (prêts ÷ exemplaires). Répond au « nb de livres
  par catégories » de Val et donne au comité l'usage réel de chaque rayon.
- Par emplacement.
- Par provenance et par source d'acquisition (achat / don / échange / inconnu).
- Nouveautés de la période — notices et exemplaires ajoutés, par catégorie
  (« nb de nouveaux livres sur une période »).
- Dons de la période — par donateur, du plus généreux au moins.
- Sorties de la période — exemplaires passés perdus ou pilonnés.

### 3. Les prêts — `loans`

**Compteurs** : prêts sur la période · retours · en retard aujourd'hui · part
des livres rendus en retard · **durée médiane** d'un prêt · renouvellements.

La médiane, pas la moyenne (avis Grok retenu) : un livre rendu au bout de deux
ans écrase une moyenne calculée sur trois cents prêts de trois semaines, et le
chiffre affiché ne décrit alors plus aucun prêt réel. Le libellé le dit sans
employer le mot — « la moitié des prêts durent moins que cela ».

**Graphes** : prêts mois par mois (histogramme) · par catégorie de livre
(camembert) · par catégorie d'usager (camembert).

**Tableaux**
- Prêts par jour d'ouverture — une ligne par jour où il s'est passé quelque
  chose : date, prêts, retours. Équivalent des *Locations par ouvertures*.
- **Les livres les plus empruntés** — top 20 sur la période.
- **Les livres les moins empruntés** — les 20 plus faibles **parmi ceux qui ont
  été empruntés au moins une fois** ; les livres jamais empruntés sont une autre
  question, comptés à part et renvoyés vers l'écran des inactifs. Sans cette
  distinction, « les moins empruntés » n'est qu'une liste de zéros.
- Un filtre **catégorie** (`?category=<id>`) s'applique aux deux classements.

### 4. Les usagers — `members`

**Compteurs** : usagers inscrits · cartes valides · familles · personnes
couvertes · nouveaux (période) · réinscriptions (période) · perdus (période).

**Définitions**
- **Famille** : un usager qui a au moins une personne rattachée
  (`MemberFamilyMember`). « Nb de familles et nb de personnes » de Val =
  nombre de titulaires ayant des rattachés, et nombre total de personnes
  couvertes (titulaires + rattachés).
- **Nouvel usager** : `registration_date` dans la période.
- **Réinscription** : un renouvellement de carte enregistré dans la période
  (voir *Impact — modèle* : cela demande une table).
- **Membre perdu** : `expiration_date` tombe dans la période **et** reste dans
  le passé aujourd'hui. Une carte renouvelée a par construction une expiration
  future : la soustraction suffit, sans historique.

**Graphes** : tranches d'âge (histogramme) · catégories d'usager (camembert) ·
langues parlées (histogramme).

**Tableaux**
- Par localité — code postal, localité, nombre. Équivalent du *Regroupement des
  membres par localités (NPA)*, utile pour montrer à un bailleur d'où viennent
  les gens.
- Par catégorie d'usager.
- Mouvement mois par mois — nouveaux, réinscriptions, perdus.
- Les 20 usagers qui ont le plus emprunté sur la période.

### 5. La fréquentation et les animations — `attendance`

L'animation **« Bibliothèque »** enregistre une simple venue à la bibliothèque :
c'est l'animation principale, et l'écran la présente comme telle, en tête et
séparée des autres.

**Compteurs** : venues à la bibliothèque · animations organisées · participations
de membres · non-membres adultes · non-membres enfants · heures d'animation.

**Graphes** : présences par tranche d'âge (camembert) · fréquentation mois par
mois (histogramme).

**Tableaux**
- Par animation — séances, participations de membres, non-membres, heures.
- **Présences par tranche d'âge et par animation** — tableau croisé : une ligne
  par animation, une colonne par tranche (0-5, 6-10, 11-15, 16-20, 21 et plus,
  âge inconnu), plus deux colonnes non-membres (adultes, enfants) que le modèle
  ne connaît qu'en gros. C'est la demande explicite de Val.

L'âge se calcule à la date de la séance, pas aujourd'hui : un enfant venu à
6 ans il y a trois ans doit rester dans la tranche 6-10 du rapport de cette
année-là.

### 6. Le travail de l'équipe — `team`

**Compteurs** : heures totales · personnes ayant travaillé · heures d'animation ·
nombre de saisies.

**Graphes** : heures par nature d'activité (histogramme) · heures mois par mois
(histogramme).

**Tableaux** — les trois états du logiciel de ludothèque, dans l'ordre :
- Heures par nature d'activité (saisies, heures).
- Heures par personne.
- Détail par mois : mois, personne, nature, heures.

### 7. L'argent — `money`

**Compteurs** : total facturé · encaissé · reste dû · espèces encaissées ·
sorties de caisse · solde de caisse sur la période.

**Graphes** : recettes par nature (camembert : cotisation, animation, amende,
autre) · encaissements mois par mois (histogramme).

**Tableaux**
- Recettes par nature.
- Encaissements par mode de paiement (espèces, virement, autre).
- Factures impayées — usager, n°, date, total, reste dû, jours de retard.
- **Jour par jour** — date, espèces, autres modes, sorties, solde du jour.
  Équivalent de la *Caisse journalière*.
- Mouvements de caisse de la période.

### 8-10. Les listes de travail

Reprises telles quelles dans le nouveau gabarit, avec PDF et Excel :

- **Les retards** — seuil en jours réglable, du plus ancien au plus récent.
- **Les réservations à retirer** — avec la date limite de retrait.
- **Les inactifs** — usagers et exemplaires sans mouvement depuis N jours,
  **avec tri et filtre par catégorie** (demande explicite de Val ; la catégorie
  du livre pour les exemplaires, la catégorie d'usager pour les usagers).

## Technical spec

### Le point d'architecture

La règle « pas d'écran sans export, pas d'export sans écran » n'est pas tenable
si écran et export sont écrits séparément : au troisième écran, l'un des deux
diverge. Un écran produit donc **un objet** décrivant son contenu, et trois
moteurs le rendent.

```
services/stats.py  ──►  ReportPage  ──┬──► templates/reports/_page.html   (HTML)
   (une fonction                      ├──► reports/pdf.py                 (PDF)
    par écran)                        └──► reports/excel.py               (Excel)
```

`apps/reports/pages.py` :

```python
@dataclass
class Period:
    start: date
    end: date
    label: str          # « août 2026 », « 2025 », « 12 derniers mois »
    key: str            # month | prev_month | year | prev_year | custom

@dataclass
class Kpi:
    label: str
    value: str
    hint: str = ""
    color: str = "burgundy"     # jeton de la charte OFELIA

@dataclass
class Column:
    label: str
    align: str = "left"         # left | right

@dataclass
class Table:
    title: str
    columns: list[Column]
    rows: list[list]
    total_row: list | None = None
    empty_text: str = ""

@dataclass
class Chart:
    title: str
    kind: str                   # bar | pie
    labels: list[str]
    values: list[float]
    unit: str = ""

@dataclass
class ReportPage:
    slug: str
    title: str
    subtitle: str
    kpis: list[Kpi]
    blocks: list[Chart | Table]     # l'ordre de la liste est l'ordre affiché
    period: Period | None = None
    filters_html: str = ""          # réglages propres à l'écran (seuil, catégorie)
```

Ajouter un écran = écrire une fonction `build_<slug>(period, **params) -> ReportPage`
et une ligne dans le registre. L'écran, le PDF et le fichier Excel suivent sans
une ligne de plus.

### Les graphes

`apps/reports/charts.py` produit du **SVG écrit par le serveur** :
`bar_svg(chart)` et `pie_svg(chart)`. Pas de JavaScript, pas de bibliothèque —
la contrainte hors-ligne interdit un CDN, et une bibliothèque locale (Chart.js,
250 Ko) coûterait plus cher que deux fonctions de tracé pour deux formes de
graphe. Le SVG s'imprime proprement et se relit à la loupe.

Palette : les jetons de la charte pris dans l'ordre — bordeaux, orange, forêt,
ambre, ciel, olive, rose, puis rotation. Chaque part d'un camembert porte son
libellé et son pourcentage ; un camembert de plus de 8 parts regroupe la queue
en « Autres », sinon il devient l'illisible roue de couleurs du logiciel de
ludothèque.

Côté PDF, les mêmes `Chart` sont tracés avec `reportlab.graphics.charts`
(`VerticalBarChart`, `Pie`), déjà disponible. Côté Excel, `openpyxl.chart`
(`BarChart`, `PieChart`), déjà dépendance de l'import/export catalogue.

### Les URL

```
/reports/                       hub
/reports/<slug>/                écran      (+ ?p=… & réglages)
/reports/<slug>.pdf             export PDF   (mêmes paramètres)
/reports/<slug>.xlsx            export Excel (mêmes paramètres)
```

Une seule vue `report_view`, une seule `report_pdf`, une seule `report_xlsx`,
qui résolvent le `slug` dans le registre. Les anciennes URL
(`/reports/overdue/`, `/reports/inactive/`, `/reports/reservations-pickup/`)
sont conservées et redirigent, pour ne pas casser les liens du guide
utilisateur et des favoris.

Les exports CSV existants (`catalog.csv`, `loans.csv`,
`active-loans-reservations.csv`, `inactive-members.csv`, `inactive-items.csv`)
**restent** : ce sont des exports de données brutes destinés à la reprise dans
un tableur, pas des rapports. Ils sont regroupés dans le hub sous « Sortir les
données brutes », clairement distingués des rapports.

### Rôles

Consultation : `LIBRARIAN`, `SUPERADMIN`, `READONLY` — comme aujourd'hui.
Les exports PDF et Excel suivent la même règle que l'écran qu'ils reproduisent
(donc `READONLY` y a droit, contrairement aux exports CSV bruts réservés au
bibliothécaire).

## Impact on existing code

### Modèle — une table nouvelle

`members.CardRenewal` : `member`, `renewed_on`, `previous_expiration`,
`new_expiration`, `user`.

Sans elle, « nombre de réinscriptions sur une période » n'est **pas
calculable** : `Member.expiration_date` est écrasée à chaque renouvellement
(FEAT-092) et ne laisse aucune trace. Les deux contournements envisagés ont été
écartés — déduire la réinscription de `expiration_date − validité` ment dès
qu'une date a été corrigée à la main ; la déduire des factures de cotisation
ignore les catégories gratuites, qui n'émettent pas de facture.

Écriture depuis le bouton *Renouveler* de `/members/<pk>/edit/`. L'historique
antérieur au sprint est perdu par construction : l'écran des usagers le dit
(« comptées depuis le 09/09/2026 ») plutôt que d'afficher un zéro trompeur.

« Membres perdus » ne demande aucune table : voir la définition plus haut.

### Fichiers touchés

| Fichier | Nature |
|---|---|
| `apps/reports/pages.py` | **nouveau** — les dataclasses |
| `apps/reports/periods.py` | **nouveau** — sélecteur de période |
| `apps/reports/charts.py` | **nouveau** — SVG histogramme / camembert |
| `apps/reports/excel.py` | **nouveau** — `render_report_xlsx` |
| `apps/reports/builders/*.py` | **nouveau** — une fonction par écran |
| `apps/reports/pdf.py` | réécrit — `render_report_pdf` générique, charte OFELIA |
| `apps/reports/services.py` | complété — agrégations des dix écrans |
| `apps/reports/views.py` | réécrit — trois vues génériques + redirections |
| `apps/reports/urls.py` | réécrit |
| `templates/reports/index.html` | réécrit — hub à deux groupes |
| `templates/reports/_page.html`, `_period.html`, `_chart.html`, `_kpis.html`, `_table.html` | **nouveaux** |
| `templates/reports/{overdue_list,inactive_list,reservations_pickup}.html` | supprimés — absorbés par `_page.html` |
| `apps/members/models.py` + migration | `CardRenewal` |
| `apps/members/views.py` | le renouvellement écrit `CardRenewal` |
| `static/css/bibliofelia.css` | classes des graphes et du sélecteur de période |
| `docs/specs/SPEC_BIBLIOFELIA.md` | §6.6 réécrite |
| `docs/user-guide/` | hors sprint — à replanifier une fois les écrans validés |

### Ce que la refonte ne fait pas

- Le **tableau de bord** d'accueil (`/`) n'est pas touché : c'est un écran
  d'action, pas un rapport. Il gagnera au plus un lien vers la vue d'ensemble.
- L'écran **Statistiques d'activité** de `closing/` est absorbé par
  *Le travail de l'équipe* et *La fréquentation* ; son URL redirige.
- Pas de rapport « valeur d'achat du fonds » ni de « cartes prépayées » du
  logiciel de ludothèque : BibliOfelia ne stocke pas de prix d'achat par
  exemplaire ni de porte-monnaie prépayé, et rien ne dit qu'il devrait.
- Pas de nouvelle saisie quotidienne demandée aux bénévoles : tout se calcule
  sur les données déjà saisies.

---

## Avis consultatifs Grok — ce qui a été retenu

Deux consultations, conformément à la demande de Val : d'abord les **données
manquantes**, ensuite l'**ergonomie des écrans** une fois la maquette écrite.
L'avis était consultatif ; ce qui suit dit ce qui a été gardé, et ce qui a été
écarté et pourquoi.

### Consultation 1 — les données qui manquaient

**Retenu**

| Proposition | Où elle atterrit |
|---|---|
| Taux d'usagers réellement actifs | Compteur « Usagers venus » sur *Les usagers*, distinct de « personnes touchées » |
| Enfants desservis, deux compteurs distincts | Tranches d'âge sur *Les usagers* et *La fréquentation*, personnes rattachées comptées à part |
| Rotation calculée sur les exemplaires **en circulation** | Colonne « Prêts par livre » de *Le fonds* — corrige un calcul qui aurait fait baisser un rayon parce qu'on y a pilonné des livres |
| Stock dormant avec filtre d'ancienneté | « Les livres qui n'ont jamais servi », restreint aux exemplaires en rayon depuis plus d'un an |
| Cartes expirant sous 30 jours | Tableau d'action sur *Les usagers* |
| Fonds et public rapprochés langue par langue | Tableau « Les langues : le fonds et le public » sur *Le fonds* |
| Sort des réservations | Tableau « Les réservations de la période » sur *Les prêts* |
| Prêts par provenance | Colonne ajoutée à « D'où viennent les livres » |
| Consultations sur place | Compteur sur *La fréquentation* — la table `InHouseConsultation` existait et n'apparaissait dans aucun rapport |
| Médiane plutôt que moyenne pour la durée de prêt | Compteur « Durée d'un prêt » |
| Afficher les valeurs manquantes au lieu de les écarter | « âge inconnu » dans les graphes, « n usagers sans localité » sous les tableaux |
| Comparaison avec la période précédente | Chaque compteur de période de *Vue d'ensemble* |
| Ne jamais valoriser le bénévolat en argent | Écrit noir sur blanc dans *Le travail de l'équipe* |

**Écarté**

- **Croisement public × fonds en carte de chaleur** — illisible pour le public
  visé ; c'est exactement le genre d'écran qu'on n'ouvre jamais deux fois.
- **Conversion animation → adhésion** — une corrélation présentée à un bailleur
  se lit comme une causalité. Le risque dépasse l'apport.
- **Présents non-emprunteurs**, **pipeline de cotisations détaillé** — justes,
  mais ils ajoutent deux tableaux à des écrans déjà denses pour une question
  qu'on se pose une fois par an.
- **Durée de blocage d'un exemplaire en réparation** — `Item` n'horodate pas
  ses changements de statut ; le calcul serait un proxy présenté comme une
  mesure.

### Consultation 2 — l'ergonomie

**Retenu**

- **Les raccourcis de période s'appliquent au clic.** Ce sont des liens ;
  « Valider » ne subsiste que pour la saisie libre, repliée derrière « Choisir
  d'autres dates ». Trois modes de saisie simultanés, c'était deux de trop.
- **Un cinquième bouton « 12 derniers mois »**, pour que la période par défaut
  soit elle aussi représentée — sans lui, aucun bouton n'est allumé à
  l'arrivée, ce qui laisse croire à un réglage manquant.
- **Le hub dit quoi faire** : trois cartes d'action avec un verbe et le nombre
  en attente, au-dessus des écrans de chiffres.
- **Chaque compteur porte une phrase**, pas seulement un nombre.
- **Un sommaire d'ancres** en tête des écrans à plus de deux blocs.
- **Les listes de travail ouvrent sur « Imprimer »**, Excel en second ; elles
  affichent le **téléphone**, sans lequel il faut rouvrir chaque fiche.
- **Les seuils sont des boutons** (0/7/14/30 j, 180/365/730 j), pas un champ
  à taper.
- **Le tableau-bilan passe en fin** de la vue d'ensemble : c'est un livrable,
  pas la lecture du matin. Les factures impayées passent au contraire **en
  tête** de *L'argent* — c'est une liste de travail.
- **L'histogramme des langues** devient un simple tableau sur *Les usagers*.
- **Règles mobiles** : sous 600 px, deux compteurs par ligne, raccourcis de
  période en 2×2, camembert et légende empilés, exports pleine largeur.
- **La légende des camemberts sort du SVG** et devient du HTML : enfermée dans
  le dessin, elle rétrécit avec lui et devient illisible sur un téléphone.
- **Nombres** : espace fine insécable pour les milliers, pourcentages sans
  décimale, jamais de case vide (`—`).

**Écarté**

- **Supprimer l'histogramme « livres sortis à la fin de chaque mois »**, jugé
  redondant. C'est une demande explicite de Val (« + graphe dans le passé ») ;
  il est conservé, déplacé sous l'histogramme des prêts.
- **Ne laisser qu'un graphe visible par écran, le reste derrière des ancres.**
  Pour ce public, faire disparaître des données derrière une interaction coûte
  plus cher que de faire défiler. Compromis retenu : le sommaire d'ancres, mais
  tout le contenu reste visible.
- **Scinder *Le fonds*** en deux écrans. Un onzième menu pour une question
  qu'on se pose deux fois par an ; les mouvements sont un bloc distinct sur le
  même écran.

## Fix applied

Livré au Sprint 34. Fichiers créés : `apps/reports/{pages,periods,charts,
format,excel}.py`, `apps/reports/builders/` (huit modules + le registre),
`apps/reports/templatetags/report_tags.py`, `templates/reports/{page,_period,
_filters}.html`, `apps/members/migrations/0008_cardrenewal.py`,
`scripts/translations_sprint34.py`. Réécrits : `apps/reports/{pdf,views,urls}.py`,
`templates/reports/index.html`, `apps/members/{models,services}.py`,
`static/css/bibliofelia.css`. Supprimés : `apps/reports/forms.py` et les trois
gabarits de liste, absorbés par `page.html`.

**Tests : 937 passed** (894 → 937, +43), dont un test paramétré qui parcourt le
registre et exige de chaque écran son HTML, son PDF et son fichier Excel — sur
un jeu de données et sur une base vide. Gate i18n : `scripts/i18n_check.py` = 0,
312 chaînes traduites en EN/ES/MG.

Deux défauts trouvés par ces tests et corrigés avant livraison : les anciennes
adresses `overdue/` et `inactive/` redirigeaient **vers elles-mêmes** en boucle
(leur slug n'avait pas changé, la redirection était de trop), et le calcul de
largeur de colonne de l'export Excel plantait sur un tableau vide. Un
troisième, trouvé à la relecture : compter les présences dans le même
`annotate` que la somme des minutes multipliait la durée d'une animation par
son nombre de participants — un test le verrouille désormais.

---

## Corrections après le premier essai (temp2.txt, 2026-09-09)

Val a testé les dix écrans déployés et rendu onze remarques. Toutes ont été
appliquées.

### 1. Les camemberts portent leurs étiquettes sur les tranches

« Adultes Documentaire 35 (34 %) » s'écrit **dans** la part, plus dans une
légende sous le graphe — à l'écran comme dans le PDF et dans le fichier Excel.

Les grandes parts reçoivent leur texte à l'intérieur, en blanc ou en noir selon
la luminance de la couleur de fond ; celles de moins de 8 % du total, où le
texte ne tiendrait pas, sont reliées par un trait à une étiquette posée à
l'extérieur, empilée pour ne pas chevaucher ses voisines. Le texte se coupe en
deux lignes **sur la parenthèse**, jamais sur la dernière espace : « (34 %) »
se retrouverait sinon scindé en « (34 » et « %) ».

Bénéfice non demandé mais décisif : un camembert étiqueté reste lisible imprimé
en noir et blanc, là où une légende par couleur ne sert plus à rien.

Côté PDF, reportlab place les étiquettes lui-même (`sideLabels`) et écarte
celles qui se chevaucheraient. Côté Excel, `DataLabelList` affiche nom, valeur
et pourcentage sur les parts.

### 2. Périodes et seuils sont de vrais boutons

Un style unique, `.chip-btn`, pour tout ce qui se clique et se met en évidence
quand il est actif (`.chip-btn--on`, fond bordeaux) : les cinq périodes, les
seuils de retard, les durées d'inactivité et le menu des sous-rapports. Le
fonctionnement n'a pas changé — ce sont toujours des liens appliqués au clic.

### 3. Le hub en couleurs

Chaque écran porte la couleur de son sujet, comme la page Avancé : rouge alerte
pour les retards, ambre pour ce qui attend, vert pour le fonds, bleu pour les
usagers. La couleur est déclarée **une seule fois**, dans le registre
(`ReportSpec.tint_bg` / `tint_fg`), et sert au fond de l'icône, à la barre
latérale de la carte et à la pastille de comptage.

Les fonds des cartes étaient déjà blancs (`--paper`) sur les deux pages : rien
à corriger de ce côté.

### 4. Les données brutes ont rejoint les écrans qui les montrent

Les trois menus « Sortir les données brutes » du hub ont disparu. Ils sont
devenus des **sous-rapports** :

| Ancien menu du hub | Devenu |
|---|---|
| Catalogue complet | « Le catalogue complet », sous *Le fonds* |
| Prêts et réservations en cours | « Prêts et réservations en cours », sous *Les prêts* |
| Export CSV des prêts par période | « Le détail des prêts de la période », sous *Les prêts* |

Ils ont donc maintenant un écran, et leurs exports PDF et Excel comme les
autres. Les **CSV** restent offerts au bas de ces deux écrans, dans une section
« Sortir toutes les colonnes » : ils sortent vingt-trois colonnes là où le
tableau en montre sept, ce que ni le PDF ni le tableur mis en page ne font.

### 5. Un menu de sous-rapports en tête de chaque écran

Le sommaire liste les sous-rapports de la page sous forme de boutons et y mène
par ancre. Il donne aussi, d'un coup d'œil, la liste de ce que l'écran
contient.

### 6. Chaque sous-rapport s'exporte seul

Deux liens discrets sous chaque titre : PDF et Excel du seul tableau. Un
bénévole qui veut imprimer la liste des impayés n'a plus à sortir les huit
tableaux de l'écran.

Contrat d'URL : `/reports/<slug>.pdf?block=<clé>`. La clé est dérivée du
**titre** du sous-rapport, pas de sa position — un index changerait de sens dès
qu'on réordonne un écran, et un lien partagé par courriel pointerait alors sur
un autre tableau. Une clé inconnue rend l'écran entier plutôt qu'une erreur.

### 7. Tableau et graphe côte à côte

Un tableau et le graphe des **mêmes** données sont désormais un seul
sous-rapport : `Table.chart`. Ils s'affichent moitié-moitié au-dessus de
900 px, empilés en dessous, et le PDF fait de même. Le fichier Excel les met
sur la même feuille, graphe à droite des données.

Garde-fou : un tableau de plus de quatre colonnes garde la pleine largeur et
pose son graphe en dessous. À moitié de page, ses colonnes deviendraient
illisibles — c'est le cas du tableau croisé âge × animation.

### 8. Les graphes ajoutés

| Écran | Sous-rapport | Graphe |
|---|---|---|
| Vue d'ensemble | Le bilan en un tableau | histogramme |
| Les usagers | Qui arrive, qui reste, qui part | **courbes**, trois séries |
| Les usagers | D'où viennent les usagers | camembert |
| Le fonds | Les rayons | camembert |
| Le travail de l'équipe | Le temps par nature de travail | camembert |
| La fréquentation | Ce qui a été organisé | camembert |
| La fréquentation | Les présences par âge et par animation | camembert |

Le graphe en courbes est une **troisième forme** ajoutée au moteur (`kind =
"line"`), tracée en SVG côté serveur comme les deux autres, avec ses repères
horizontaux gradués et sa légende. Trois colonnes de chiffres ne montrent pas
qu'une courbe passe au-dessus de l'autre ; c'est pourtant le seul moment où
l'on voit qu'on perd plus de monde qu'on n'en gagne.

### 9. Le bilan sur une seule période

Le tableau « Le bilan en un tableau » n'a plus qu'une colonne de chiffres :
celle choisie en haut de l'écran. La comparaison avec la période précédente
reste sur les compteurs, où elle se lit d'un coup d'œil ; dans un tableau de
quatorze lignes, une seconde colonne se confondait avec la première.

Son graphe ne reprend que **les cinq chiffres de la période**. Y verser les
livres au catalogue écraserait tout le reste, et mêler des heures, de l'argent
et des livres sur un même axe ne veut rien dire.

### 10. Le travail de l'équipe : un sous-rapport au lieu de deux

« Les heures par nature de travail » (barres) et « Le temps par nature de
travail » (tableau) disaient la même chose deux fois. Un seul sous-rapport,
tableau et **camembert** côte à côte : la question posée est « à quoi passe-t-on
le temps ? », c'est-à-dire un partage d'un tout, ce que des barres ne montrent
pas.

### Vérifications

**980 tests** (937 → 980, +43), dont un nouveau fichier
`test_report_corrections.py` qui verrouille chacune de ces onze corrections.
Deux tests parcourent le registre et exigent de **chaque** écran, puis de
**chaque sous-rapport**, ses exports PDF et Excel.

Gate i18n = 0, 340 chaînes EN/ES/MG.

Contrôle de rendu sur la Box (953 exemplaires) : 30 points HTML/PDF/Excel à
200, étiquettes vérifiées dans le SVG **et** dans le texte du PDF produit
(« Adultes Documentaire 11 (1 %) »), ancienne légende absente, exports d'un
sous-rapport seul à 96 Ko contre 278 Ko pour l'écran entier.

Un défaut trouvé et corrigé en route : la coupure du texte des étiquettes sur
la dernière espace scindait « (34 %) » en deux lignes.

## La charte OFELIA dans le PDF (retours de Val, 2026-09-09)

Le premier PDF reprenait les couleurs de la charte, mais rien d'autre : logo
timbre-poste, titre discret, texte en Helvetica, et un en-tête de tableau
**noir sur bordeaux**, illisible. Six corrections.

### Les polices du site, vraiment

Le site compose en **Bricolage Grotesque** (titres) et **DM Sans** (texte),
servis en `.woff2` — un format que reportlab ne sait pas lire. D'où
`scripts/build_pdf_fonts.py`, qui produit les `.ttf` équivalents dans
`static/fonts/pdf/` :

1. **décompression** du woff2 ;
2. **fusion des sous-ensembles** — Google Fonts découpe chaque famille par
   plage Unicode (`latin`, `latin-ext`, `vietnamese`). Un titre de livre peut
   contenir n'importe quelle lettre, et reportlab ne sait pas retomber sur une
   autre police : un glyphe absent se dessine en carré noir. On fusionne donc
   toutes les plages ;
3. **fixation de la graisse** — ce sont des polices variables (400→800), que
   reportlab n'instancie pas ; il prendrait le même dessin pour le gras et pour
   le maigre. Un fichier par graisse utilisée.

Deux pièges rencontrés, tous deux consignés dans le script :

- la fusion échouait sur un `VarStore` résiduel (`GDEF`, `HVAR`, `STAT`) — ces
  tables sont retirées après instanciation, avec `GSUB`/`GPOS` qui ne servent à
  rien ici puisque reportlab n'applique ni ligature ni crénage OpenType ;
- **l'espace fine insécable U+202F**, séparateur de milliers de tous les
  rapports et de tous les montants, n'est dans aucun sous-ensemble Google.
  Sans alias, « 1 234 » sortait « 1□234 » sur chaque page de chiffres. Le
  script la fait pointer sur une espace voisine et **échoue** si un caractère
  des quatre langues manque encore — mieux vaut un échec à la fabrication qu'un
  carré noir dans un document tendu à un donateur.

Les `.ttf` sont versionnés (114 Ko à trois) : le script ne tourne pas au
déploiement, et la Box n'a pas besoin de fontTools. Si les fichiers manquent,
`_register_fonts()` journalise et retombe sur Helvetica — un rapport moins joli
vaut mieux qu'un rapport absent.

### Le bandeau

Logo **blanc** (`static/img/ofelia-logo-white.png`, fourni par Val) sur 70 mm,
titre du rapport en Bricolage Grotesque **24 pt**, nom de la bibliothèque à
droite, et la période précédée d'une **icône de calendrier** dessinée au trait
— les icônes du site sont des SVG que reportlab ne pose pas directement, et
cinq traits coûtent moins qu'un convertisseur.

La hauteur du bandeau **se calcule** à partir de ce qu'il contient (marge,
logo, interligne, corps du titre, marge). Une hauteur écrite à la main s'était
désaccordée du premier changement de taille : au premier essai, le titre
chevauchait le logo. Un test verrouille l'absence de recouvrement.

### Les en-têtes de tableau, en blanc

C'est le défaut que Val a vu en premier. Le `TEXTCOLOR` de la table ne suffit
pas : **la couleur portée par le style d'un `Paragraph` l'emporte**, et
l'en-tête sortait en noir sur fond bordeaux. Il a fallu un style dédié
(`head`), plus une variante `head_narrow` pour les tableaux posés en
demi-page.

### Les largeurs de colonne, mesurées

Des proportions fixes (« la première colonne prend 42 % ») ne tiennent pas : la
règle qui laisse respirer un titre de livre coupe « Réinscriptions » en deux
dans un tableau de quatre colonnes posé à côté de son graphe. Deux tours de
réglage à l'aveugle ont suffi à montrer l'impasse.

`_column_widths()` mesure donc, pour chaque colonne, la largeur de son en-tête
et de ses valeurs — deux largeurs : la **naturelle**, celle qui éviterait tout
retour à la ligne, et la **minimale**, celle du plus long mot insécable. S'il
reste de la place, elle se distribue au prorata ; s'il en manque, on rogne sur
l'écart entre les deux, jamais en dessous du mot le plus long. Un retour à la
ligne se fait alors sur une espace (« septembre / 2025 »), plus au milieu d'un
mot.

### Les libellés d'axe

reportlab n'écourte rien : « septembre 2025 » douze fois de suite devient une
bouillie grise. `_axis_labels()` ampute le mois et **garde l'année**, qui
distingue deux barres identiques d'une année sur l'autre — la même règle que
le SVG de l'écran.

### Vérifications

**993 tests** (980 → 993, +13), dont `test_report_pdf_charter.py` : polices
présentes et enregistrées, U+202F couverte *vue par reportlab*, en-têtes
blancs, titre plus grand que le corps, bandeau assez haut pour le logo et le
titre, largeurs de colonne qui remplissent la page sans écraser personne.

Contrôle à l'œil sur la Box (953 exemplaires) : les trois PDF rendus en image
et relus — logo blanc en grand, titre en grand, calendrier, en-têtes blancs sur
bordeaux, camemberts étiquetés sur les tranches, tableau et graphe côte à côte.

## Second retour de Val (2026-09-09) — et la cause commune des « pas fait »

Sur onze points, cinq étaient annoncés livrés et vus **KO** : boutons de
période, couleurs du hub, sommaire des sous-rapports, mise côte à côte sur le
web. Le code les produisait bien — les classes étaient dans le HTML servi. Mais
tout le bloc CSS des rapports avait été écrit dans **`static/css/bibliofelia.css`**,
que seuls les deux gabarits du wizard d'installation référencent. `base.html`,
dont héritent tous les écrans de l'application, ne charge que **`ofelia.css`**.

Le bloc a été déplacé dans `ofelia.css`, et un test le verrouille : chaque
classe posée par les gabarits de rapport doit être habillée par une règle de la
feuille effectivement chargée, et aucune ne doit rester dans celle qui ne l'est
pas. C'est la leçon de la journée — vérifier qu'un fichier est *servi* ne dit
pas qu'il est *chargé*.

### Les corrections de fond

**Camemberts : toutes les étiquettes à l'extérieur.** Écrire dans la tranche ne
marchait pas — un texte blanc sur une part claire, ou débordant sur le fond
blanc de la page, devient invisible. Toutes les étiquettes sortent maintenant
du disque et rejoignent leur part par un trait terminé d'une pastille de
couleur, exactement comme le PDF. Le texte est toujours en encre foncée sur
fond blanc, quelle que soit la couleur de la part.

**Deux géométries de graphe.** Un SVG s'étire à la largeur de son conteneur :
le même dessin posé sur une demi-page était réduit d'un tiers et son texte
devenait illisible. Les graphes appariés à un tableau sont donc tracés en
version **compacte** — disque plus petit, moins de marge, étiquettes plus
courtes — de sorte que le texte fasse la même taille à l'écran dans les deux
cas. Le camembert pleine largeur a aussi gagné de la marge : « Adolescent
(14-17 ans) 20 (91 %) » se voyait tronquer par le bord de la carte.

**Toutes les séries d'une courbe sont tracées**, y compris celles restées à
zéro. Les écarter laissait une légende qui annonçait trois courbes pour un
dessin qui n'en montrait qu'une. Une courbe plate sur l'axe dit « on n'a perdu
personne » : c'est une information.

**Le bilan reprend toutes ses lignes.** Le graphe de la vue d'ensemble ne
montrait que cinq des quatorze chiffres du tableau ; il les reprend tous, à une
exception assumée — l'argent encaissé. Un montant n'est pas un nombre de
livres : la même barre dirait « 240 » pour 240 francs et pour 240 prêts. Il
reste dans le tableau et dans son compteur, où sa devise est écrite.

**« Cartes perdues » devient « Usagers perdus »**, compteur, colonne et courbe.

### Ce qui n'était pas un défaut

*La fréquentation*, *Le travail de l'équipe* et *L'argent* paraissaient sans
graphes : la Box n'a **aucune** animation, aucune saisie de temps et aucune
facture. Les écrans affichaient donc leurs états vides, correctement. Vérifié
en construisant les trois écrans sur un jeu de données de démonstration, dans
une transaction annulée — la base de la bibliothèque n'a pas été touchée :
*Fréquentation* rend bien ses deux camemberts, *Équipe* le sien.

### Vérifications

**1002 tests** (993 → 1002, +9), dont `test_report_layout.py` : la feuille de
style chargée porte les classes des rapports, le graphe compact est plus étroit
que le plein format, une étiquette de camembert tient dans son cadre sans être
tronquée, une série à zéro est quand même tracée.

Gate i18n = 0, 344 chaînes EN/ES/MG.

Contrôle à l'œil, cette fois **par capture du navigateur** (Playwright contre la
Box) et non plus seulement par lecture du HTML : hub, écran du fonds, écran des
usagers, en grand écran et en téléphone. Un compte de capture temporaire a été
créé puis supprimé.

### Le camembert des rayons (dernier retour, 2026-09-09)

Un seul graphe sortait du cadre, celui du sous-rapport « Les rayons : ce qu'on
a et ce qui sort ». Deux causes, toutes deux corrigées.

**Le gabarit envoyait le mauvais dessin.** Ce tableau a cinq colonnes : il passe
donc en pleine largeur (`block-pair--wide`) et son graphe avec lui. Mais le
gabarit lui passait la version **compacte** quoi qu'il arrive — un dessin conçu
pour une demi-page, étiré à la largeur entière, dont les libellés grossissent
d'autant. Le choix de la géométrie suit désormais le même critère que la mise
en page.

**La marge des étiquettes était posée au jugé.** Une valeur fixe finit toujours
par être trop courte pour un libellé un peu long. Elle se **mesure** maintenant
sur les étiquettes réellement écrites, au corps réellement utilisé — même
démarche que les largeurs de colonne du PDF.

Au passage, la constante qui décrit la place du trait de rappel ne comptait que
deux de ses trois segments : l'écart entre le coude et la pastille manquait,
soit huit points de marge en moins. Les trois segments sont maintenant nommés
et additionnés.

Deux tests verrouillent l'ensemble : aucune étiquette ne quitte son cadre, dans
les deux géométries et sur des libellés volontairement longs ; et la marge
s'élargit bien quand les libellés s'allongent.

**Incident sans rapport, corrigé au passage** : une réécriture par `perl -pi`
avait laissé un octet latin-1 dans un commentaire de `charts.py`, ce qui faisait
échouer l'audit i18n à la lecture du fichier. C'est exactement le piège que
`CLAUDE.md` décrit — le code multi-ligne qui édite des fichiers s'écrit dans un
fichier, il ne se passe pas en ligne de commande.

### Les deux dernières features (`temp.txt`, 2026-09-09)

**1. « Les rayons » troque son camembert pour un double histogramme.**
Deux barres par rayon — les livres qu'on possède, les prêts de la période —
groupées, jamais empilées : additionner des livres et des prêts ne veut rien
dire. Le camembert ne montrait que le fonds, et un rayon volumineux qui ne sort
pas y avait exactement l'air d'un rayon volumineux qui tourne. Côte à côte,
l'écart se voit d'un coup d'œil.

Cela a demandé de savoir grouper dans les **trois** moteurs : `bar_series()`
traite un histogramme simple comme le cas particulier d'un groupé à une série,
de sorte que le tracé n'a qu'un seul chemin de code ; reportlab groupe et pose
une légende ; `openpyxl` sort un `BarChart` en `grouping="clustered"`.

**2. Le bilan retrouve sa colonne de comparaison, et perd son graphe.**

La période de comparaison change de définition (règle Val) :

| Période regardée | Comparée à | Titre de la colonne |
|---|---|---|
| septembre 2026 | septembre 2025 | `septembre 2025` |
| 2026 | 2025 | `2025` |
| août 2026 | août 2025 | `août 2025` |
| 12 derniers mois | 10/09/2024 → 09/09/2025 | `10/09/24 – 09/09/25` |
| dates libres | le bloc de même durée qui précède | `jj/mm/aa – jj/mm/aa` |

Une période **nommée** se compare à la même un an plus tôt : une bibliothèque
ne fait pas le même mois en pleine rentrée et en plein été ; d'une année sur
l'autre, si. Une période **libre** se compare au bloc de même durée qui la
précède — on ne peut pas décaler d'un an une fenêtre dont on ignore l'intention.

Les huit premières lignes du tableau décrivent **aujourd'hui** : leur colonne de
comparaison reste vide plutôt que de répéter deux fois la même valeur. Le graphe
disparaît : quatorze grandeurs hétérogènes — des livres, des heures, de
l'argent — ne se lisent pas sur un axe commun.

**Deux écarts avec la note de `temp.txt`, tous deux assumés :**

- La formule littérale `start - (end - start)` → `start` faisait **chevaucher**
  les deux périodes d'une journée, comptée des deux côtés. Le bloc s'arrête
  donc la veille du début. C'est ce qui rend exactement l'exemple donné :
  10/09/2024 → 09/09/2025.
- Pour que cet exemple tombe juste, « 12 derniers mois » devait être une fenêtre
  de **365** jours, pas 366. `default_period` part désormais du lendemain du
  même jour l'an dernier, et non d'`aujourd'hui − 365 jours`, qui donnait un
  jour de trop une fois les bornes comptées.

**Un défaut trouvé au rendu** : le séparateur `→` sortait en **carré noir** dans
le PDF. Les polices du site sont des sous-ensembles Google Fonts, qui couvrent
la ponctuation générale mais **pas** le bloc des flèches, et reportlab ne sait
pas retomber sur une autre police. Remplacé par un tiret demi-cadratin, et un
test parcourt désormais tout ce que les rapports composent — libellés de
période, séparateurs de milliers, symboles, accents des quatre langues — pour
vérifier que chaque caractère existe dans les trois polices.

**1018 tests** (1006 → 1018, +12).

### Le guide utilisateur (2026-09-10)

Val : « la liste de tous les rapports et sous-rapports catégorisés, avec à
chaque fois un lien vers le rapport ou le sous-rapport, comme ça les
utilisateurs pourront rechercher dans la doc et cliquer pour aller directement
au rapport ».

**Une page, quatre langues, cinquante liens.** `Rapports → Tous les rapports`
(`docs/user-guide/docs/rapports/liste{,.en,.es,.mg}.md`) liste les dix écrans
groupés en deux familles, et sous chacun **tous** ses tableaux et graphes. Un
lien par ligne, ouvert dans un nouvel onglet, avec l'ancre du sous-rapport.
Comme la recherche de MkDocs indexe la page, chercher « impayés » ou
« donateurs » dans le guide mène en deux clics au tableau correspondant.

**La page est générée, jamais écrite à la main** —
`scripts/build_reports_guide.py`. Deux raisons :

1. l'ancre d'un sous-rapport est l'**empreinte de son titre** (`pages._key`),
   qu'aucun humain ne peut recopier ;
2. ce titre est **traduit**, donc l'ancre diffère dans chaque langue. Le script
   construit les dix écrans une fois par langue, sous `translation.override`,
   et relève les clés telles que l'écran les produira.

Le script se relance après tout ajout, retrait ou renommage de rapport. Et un
test le rappelle : `test_the_guide_page_lists_every_report_and_sub_report`
vérifie dans les deux sens — chaque sous-rapport figure au guide, et aucune
ancre du guide ne pointe dans le vide. Renommer un tableau sans rejouer le
script fait donc échouer la suite, au lieu de casser un lien en silence.

**« Exports CSV » devient « Imprimer et enregistrer un rapport »** : l'ancienne
page décrivait quatre exports CSV posés sur le hub, qui n'existent plus sous
cette forme. Elle explique désormais les deux boutons d'écran, les exports par
sous-rapport, et les CSV toutes-colonnes rapatriés au bas du *Fonds* et des
*Prêts*.

**Vérifications** : `mkdocs build --strict` sans erreur ; page publiée en 200
dans les quatre langues sur `docs.bibliofelia.org` **et** sur la Box ; et les
**50 ancres suivies une à une** dans un navigateur authentifié — 0 lien cassé.

**1020 tests** (1018 → 1020, +2).

### La recherche du guide ne trouvait pas les pages neuves (2026-09-10)

Val : « je ne retrouve pas les rapports dans le moteur de recherche : est-ce
qu'il faut réindexer ? »

**Non.** L'index est reconstruit à chaque `mkdocs build` et il était correct sur
les deux serveurs — la page et ses cinquante liens y figuraient. Le défaut était
ailleurs, dans nginx :

```nginx
location /bibliofelia/docs/ {
    expires 1d;          # s'applique aussi à search/search_index.json
}
```

`search_index.json` et les pages HTML gardent un **nom stable** et changent de
contenu à chaque mise à jour du guide. Servis avec `expires 1d`, le navigateur
d'un lecteur qui avait ouvert le guide avant la mise à jour gardait l'ancien
index — et donc l'ancienne recherche — pendant vingt-quatre heures. Le symptôme
touchait **toute** mise à jour du guide, pas seulement celle-ci.

Remplacé par `add_header Cache-Control "no-cache"` sur le bloc. L'ETag rend un
304 sans corps : sur le réseau local, la révalidation ne coûte rien. Une
exception pour les seuls assets aurait demandé une `location` imbriquée avec
`alias` et expression régulière — un montage que nginx ne réassemble pas sans
capture, qui aurait échangé un défaut visible contre un défaut discret.

⚠️ **Le fichier vit dans keebee**, pas dans BibliOfelia
(`nginx/conf.d/ofelia-locations.inc`). Corrigé aux **deux** endroits : sans
cela, le prochain déploiement keebee aurait rétabli le cache d'un jour. C'est le
même piège que la variable `TZ`.

⚠️ **La copie de la Box diverge du dépôt keebee** — 204 lignes contre 236. Le
bloc du guide y a donc été patché **en place**, jamais écrasé par la version du
dépôt : on ignore ce que les 32 lignes d'écart contiennent.

**Un défaut de rédaction trouvé en vérifiant** : la phrase d'introduction citait
« impayés » et « donateurs » comme exemples de recherche. Ces mots ne figurent
nulle part dans la liste — seulement dans ma phrase. Un lecteur qui les tapait
tombait sur le haut de la page au lieu du tableau. Remplacés dans les quatre
langues par des mots qui existent vraiment : « factures », « dons »,
« présences ».

Vérifié sur navigateur neuf, après correction : « retards » mène à
`rapports/liste/#les-retards`, « heures » à `#le-travail-de-lequipe`, et le terme
cherché est surligné sur la page.
