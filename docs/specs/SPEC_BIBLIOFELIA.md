# SPEC_BIBLIOFELIA

Spécification détaillée du logiciel de gestion de bibliothèque BibliOfelia, application web auto-hébergée sur Ofelia Box (Raspberry Pi 5).

Version : 1.0 (cible v1)
Statut : draft pour Spec-Driven Development
Dernière modif spec : 2026-08-22 — **Sprint 29 CLOS** (validé Val 2026-08-22) : **FEAT-075** — **deux écrans d'étiquettes** au lieu d'un : « Étiquettes codes Ofelia » (PDF A4 ou ruban) et « Étiquettes de tranche » (ruban seul, colonnes *Catégorie* et *Cote imprimée*), même sélection d'exemplaires partagée (`_picker_context` + `printing/_picker_base.html`) ; le bouton « Générer PDF » devient « **PDF A4** » ; les cotes de tranche sont **condensées à 60 % en largeur, hauteur inchangée** (`SPINE_WIDTH_SCALE`) pour tenir sur les tranches minces, et disposent elles aussi d'une **planche A4**. — **FEAT-076** — nouveau chapitre **« Méta-données »** dans le menu Avancé (emplacements, langues, catégories, provenances, enrichissement), extrait du chapitre Inventaire. — **FEAT-077** — **logo compact** dans la topbar (`ofelia-logo-small.png`, l'emblème seul : ~30 px de large au lieu de ~104) et **date + heure de la Box** à droite du « Bonjour » sur l'accueil, la Box perdant son horloge à chaque extinction (pas de pile RTC). L'heure affichée est **celle du serveur**, rafraîchie à partir de l'horodatage rendu — jamais celle du poste, sans quoi un poste à l'heure masquerait une Box déréglée. `TIME_ZONE` devient réglable : variable d'environnement **`TZ`** par instance (défaut `UTC` inchangé, c'est ainsi que la Box prend le fuseau du Pi), surchargeable par un réglage **Avancé → Paramètres → Fuseau horaire**. L'heure est suivie de l'abréviation du fuseau (`CEST`, `-03`…). Cf. §6.6, §6.7, §10.1, §10.2.

Modif précédente : 2026-08-22 — **Sprint 29, 1re vague** : **FEAT-074** — **suppression du chemin d'impression CUPS**. Le bouton « Imprimer (CUPS) » de l'écran d'étiquettes renvoyait un **403 CSRF** (POST forcé sur un formulaire `method="get"` sans jeton) et n'a donc jamais fonctionné ; sur le fond, `submit_to_cups()` suppose une imprimante visible depuis le serveur, alors que l'étiqueteuse est sur le poste du bibliothécaire et le serveur hors de la bibliothèque. Vue, route, `submit_to_cups()`, réglages `CUPS_*`, `pycups`/`libcups2` et l'étape « Imprimante » du wizard sont retirés ; le PDF (planche A4 ou ruban 62 mm) devient l'unique chemin d'impression. Le wizard passe de **8 à 7 étapes**. Cf. §2.1, §6.7, §11.3.

Modif précédente : 2026-08-21 — **Sprint 28, 3e vague** : **BUG-028** — libellés de formulaire en anglais dans une interface française (« Title », « Language »… sur la fiche notice, et tout le formulaire usager) : Django fabriquait le libellé depuis le nom du champ, hors de portée de `gettext` et donc du gate i18n. 41 `verbose_name=_()` posés + garde-fou `test_form_labels.py`. — **FEAT-073** — catalogue : la case « Chercher les exemplaires » devient deux boutons **« Rechercher des notices »** / **« Rechercher des exemplaires »** ; **deux cases de sélection** (résultats visibles / tous les résultats de la recherche, pages suivantes comprises) remplacent le « Tout cocher » qui ne prenait que la page courante ; la **provenance s'affiche en toutes lettres**. Cf. §6.1, §6.9.

Modif précédente : 2026-08-20 — **Sprint 28, 2e vague** : **BUG-027** — provenance absente de la fiche notice, du picker d'impression et de la liste des colonnes d'import Excel (le champ du formulaire d'exemplaire, lui, était bien là : c'est la liste vide qui trompait l'œil). — **FEAT-069** — **affectation en masse directement dans le catalogue** : menus déroulants « Ne pas modifier » + bouton « Affecter » dans la barre d'action (catégorie et emplacement côté notices, provenance côté exemplaires), les 3 pages de confirmation d'affectation disparaissent. — **FEAT-070** — **liste de langues gérée** (`catalog.Language`), partagée par la langue des documents et les langues parlées ; codes internationaux principaux sans variante régionale, menus triés par libellé traduit, écran Avancé → Langues, et normalisation des codes hérités de la BnF (`fre-fre` → `fr`). — **FEAT-071** — **catégories officielles Ofelia** (5 tranches d'âge × 4 types, code = cote) + commande `migrate_categories` qui retire le préfixe de langue des catégories existantes et remappe les anciennes. — **FEAT-072** — **gestion des familles** en remplacement des enfants : adultes comme enfants, année de naissance plutôt qu'âge, et colonne « Famille » sur la carte de membre. Cf. §5.2, §6.1, §6.2, §6.7, §6.12.

---

## 1. Vue d'ensemble

BibliOfelia est un logiciel de gestion de bibliothèque destiné à équiper de petites bibliothèques communautaires (jusqu'à 3000 ouvrages) dans des zones rurales d'Afrique, de Madagascar et d'Amérique du Sud, dans le cadre du projet Ofelia.

L'application tourne sur la même Ofelia Box que les autres services du projet (anciennement Edubox), un Raspberry Pi 5 (4 Go de RAM) qui fait office de serveur local. Elle est utilisée par des bibliothécaires bénévoles avec peu de formation informatique, doit fonctionner intégralement hors-ligne, et synchronise certaines tâches (récupération de métadonnées, sauvegardes cloud, mises à jour) quand une connexion internet ponctuelle est disponible via ZeroTier.

Une application Android compagnon, OfeliaScan, permet de scanner les codes-barres ISBN en masse pour alimenter le catalogue et réaliser le récolement annuel.

### 1.1 Objectifs

- Catalogage simple et rapide d'un fonds physique (notices + exemplaires)
- Gestion des prêts, retours, réservations et usagers
- Récolement assisté
- Statistiques d'usage pour les rapports aux bailleurs
- Utilisable par des personnes peu formées, en plusieurs langues
- Fonctionnement intégral hors-ligne
- Résilient aux coupures de courant et aux pannes matérielles

### 1.2 Non-objectifs (v1)

- Catalogage de ressources numériques (livres au format epub/pdf)
- Intégration avec d'autres bibliothèques (réseau, prêt entre bibliothèques)
- Support des écritures non latines (arabe en particulier)
- Import/export aux formats bibliothéconomiques standards (MARC, ONIX)
- Interface mobile pour les usagers finaux

---

## 2. Contexte et contraintes

### 2.1 Matériel cible

- Raspberry Pi 5, 4 Go de RAM
- Stockage : carte SD (système) + clé USB (sauvegardes)
- Onduleur : Waveshare UPS HAT (E) ou équivalent (partagé avec Edubox)
- Imprimante d'étiquettes : Brother QL-810W (ruban continu 62 mm), branchée sur le **poste du bibliothécaire** — le serveur produit un PDF, le poste l'imprime (FEAT-062, FEAT-074)
- Périphériques : aucun en v1 côté librairie (écran et douchette en v2)

### 2.2 Réseau

- Wi-Fi local généré par l'Ofelia Box (mode AP)
- Pas de connexion internet permanente
- Connexion internet ponctuelle via partage mobile ou liaison satellite
- Accès distant pour administration via ZeroTier quand internet disponible

### 2.3 Volumétrie cible

| Entité | Volume max |
|--------|-----------|
| Notices bibliographiques | 3 000 |
| Exemplaires | 4 500 (notices + multi-copies) |
| Usagers actifs | 500 |
| Prêts actifs simultanés | 200 |
| Prêts historiques sur 5 ans | 50 000 |
| Réservations en attente | 30 |

Pas de limite codée en dur, ces chiffres dimensionnent uniquement les choix techniques.

### 2.4 Profils utilisateurs (du logiciel)

- **Bibliothécaire** : utilisateur principal, gère prêts/retours/usagers/catalogage
- **Administrateur** : configure les règles, accède aux rapports, gère les comptes
- **Contributeur OfeliaScan** : compte technique pour l'app Android, droits limités au catalogage et au récolement via API
- **Support distant** : accès via ZeroTier, lecture seule sauf intervention exceptionnelle

### 2.5 Cohabitation avec Edubox

BibliOfelia partage le Raspberry Pi avec les autres services Ofelia (Moodle, Kolibri, Koha alternatif éventuel, captive portal, etc.). Conséquences :

- Pas de monopolisation de ressources (RAM, CPU)
- Routage via le reverse-proxy nginx existant d'Edubox
- Réutilisation du backup, de la stack ZeroTier, et de l'UPS
- Conteneurisation Docker Compose, conteneurs préfixés `edubox-bibliofelia*`
- Réseau Docker partagé `edubox-net` avec nginx en frontal

---

## 3. Stack technique recommandée

### 3.1 Backend

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Langage | Python 3.12 | Maturité, écosystème, compatibilité Raspberry Pi |
| Framework | Django 5.x LTS | i18n natif (exigence dure), admin auto, ORM mûr, sécurité par défaut |
| Base de données | SQLite 3 (mode WAL) | Backup = copie de fichier, pas de service séparé, performances suffisantes |
| Recherche | SQLite FTS5 | Intégré, suffisant pour 3000 notices, pas de service externe |
| API REST | Django REST Framework | Standard de fait, sérialisation, auth, throttling |
| Auth API | JWT (djangorestframework-simplejwt) | Stateless, adapté mobile, refresh tokens |
| Tâches async | django-q2 | Léger, compatible SQLite (broker SQLite), suffisant à cette échelle |
| ORM extensions | django-modeltranslation | Traduction des données (catégories, tags) |
| Audit | django-auditlog | Traçabilité automatique des modifications |
| Génération barcode | python-barcode | EAN-13 vectoriel et PNG |
| Génération PDF | ReportLab | Étiquettes et cartes membres |
| HTTP client | httpx | Lookup ISBN async vers OpenLibrary |

### 3.2 Frontend

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Rendu | Server-side (Django templates) | Faible latence sur Pi, simplicité, SEO inutile |
| Interactivité | HTMX 2.x | Interactions sans SPA, suffit largement |
| Réactivité locale | Alpine.js 3.x | Petits composants (modals, accordéons) |
| CSS | `static/css/ofelia.css` — système de design OFELIA Studio Ayer | Tokens couleur OFELIA, mobile-first, grille tuiles, tile strip, badges, cartes |
| Icônes | Lucide static SVG | Pack libre, embarqué localement (`static/icons/`) |
| Polices | Bricolage Grotesque (titres/marque) + DM Sans (corps/UI) | OFL, servies en local (woff2 variables, `static/fonts/`) — contrainte hors-ligne |
| Logo | `static/img/ofelia-logo.png` | Logo officiel OFELIA, topbar + login |

> **Refonte UI (2026-05-23, design handoff Claude Design)** : Pico.css et Inter remplacés
> par le système de design OFELIA (Studio Ayer). Les templates utilisent les partials
> `templates/partials/_tile_strip.html` (navigation chips) et `_page_head.html`
> (en-tête de page avec illustration SVG). Les illustrations 7 sections (64×64
> flat-vector, palette OFELIA) sont définies dans le tag `{% illus %}` de
> `apps/core/templatetags/biblio_icons.py`.

Aucune dépendance CDN externe : tous les assets sont servis depuis la box.

### 3.3 Infrastructure

| Composant | Choix |
|-----------|-------|
| Conteneurisation | Docker + Docker Compose |
| Process manager | gunicorn (workers sync, 3 workers max) |
| Reverse proxy | nginx (déjà fourni par Edubox) |
| TLS | Certificat auto-signé local, généré à l'install |
| Sauvegarde | rsync + sqlite3 .backup vers clé USB |
| Sync cloud | rclone vers stockage S3-compatible, via ZeroTier |
| Logs | journald + rotation logrotate |
| Monitoring | endpoint /health JSON exposé pour Edubox dashboard |

### 3.4 Justification des écarts au "standard"

- **SQLite et pas PostgreSQL** : pour cette volumétrie, SQLite WAL gère facilement les accès concurrents d'une poignée de bibliothécaires. La sauvegarde devient triviale (copie de fichier atomique), et on supprime un processus à maintenir.
- **Django et pas FastAPI** : FastAPI imposerait de reconstruire admin, i18n, auth, migrations. Django les fournit. Le surcoût async de Django est négligeable face à cette charge.
- **HTMX et pas React** : pas de besoin SPA, le SSR est plus rapide sur Pi, le bundle plus petit, et un seul développeur peut maintenir le tout.

---

## 4. Architecture

### 4.1 Vue d'ensemble

```
                 ┌────────────────────────────────────┐
                 │            Ofelia Box (Pi 5)        │
                 │                                     │
   Wi-Fi local   │  ┌────────────┐    ┌────────────┐  │
  ──────────────▶│  │   nginx    │───▶│ bibliofelia│  │
                 │  │ (reverse)  │    │  (Django)  │  │
                 │  └────────────┘    └─────┬──────┘  │
                 │                          │         │
                 │                  ┌───────▼───────┐ │
                 │                  │ SQLite (WAL)  │ │
                 │                  └───────────────┘ │
                 │                          ▲         │
                 │                  ┌───────┴───────┐ │
                 │                  │  django-q2    │ │
                 │                  │  (worker)     │ │
                 │                  └───────────────┘ │
                 │                          │         │
                 │   USB ────┐      ┌───────▼───────┐ │
                 │   key  ───┴─────▶│ backup script │ │
                 │                  └───────────────┘ │
                 │                                     │
                 │            ┌─────────────┐          │
   ZeroTier ─────│───────────▶│ ssh / admin │          │
                 │            └─────────────┘          │
                 └────────────────────────────────────┘
```

### 4.2 Conteneurs

- `edubox-bibliofelia` (service `bibliofelia`) : Django + gunicorn, expose le
  port 8001 (interne), healthcheck sur `/api/v1/pairing/info`.
- `edubox-bibliofelia-worker` (service `bibliofelia-worker`) : worker django-q2
  (`qcluster`). Démarre une fois le conteneur web `healthy` ; il n'exécute pas
  `entrypoint.sh` pour éviter une course aux migrations sur SQLite.

Les conteneurs partagent les volumes `bibliofelia-data` (SQLite),
`bibliofelia-media` (couvertures, uploads) et `bibliofelia-static` (statique
collecté, monté en lecture seule dans nginx). La sauvegarde est assurée par le
worker (planification django-q2, FEAT-014) — pas de conteneur backup dédié.

### 4.3 Routage nginx

L'application est servie sous `/bibliofelia/`. nginx retire le préfixe avant de
proxifier (`proxy_pass http://bibliofelia:8001/;`) ; `FORCE_SCRIPT_NAME=/bibliofelia`
fait que Django reconstruit liens et redirections avec le préfixe (FEAT-020).

- `/bibliofelia/` → conteneur web (interface web + API REST OfeliaScan)
- `/bibliofelia/static/` → `alias` nginx sur le volume `bibliofelia-static`
- `/bibliofelia/media/` → `alias` nginx sur le volume `bibliofelia-media`

### 4.4 Démarrage et migrations

À chaque démarrage du conteneur web (`scripts/entrypoint.sh`) :

1. Vérification de la connectivité à la base
2. Exécution de `manage.py migrate`
3. Création des objets par défaut si base vide (catégories, règles, langue)
4. `compilemessages` (traductions) puis `collectstatic` (statique frais)
5. Démarrage de gunicorn

Aucune intervention manuelle requise pour les mises à jour mineures.

---

## 5. Modèle de données

### 5.1 Diagramme conceptuel

```
Author ────┐
           │ M2M
           ▼
BibliographicRecord ◄── M2M ── Tag
       │  │
       │  └── FK ── Category
       │
       │ 1..N
       ▼
     Item ──────── FK ──────► Location
       │
       │ 1..N
       ▼
     Loan ── FK ──► Member ── FK ──► MemberCategory
       
Reservation ── FK ──► BibliographicRecord
              └── FK ──► Member
```

### 5.2 Entités

#### Author
- `id` (PK)
- `full_name` (texte, indexé)
- `birth_year` (entier, nullable)
- `death_year` (entier, nullable)
- `notes` (texte)

#### Category
- `id` (PK)
- `code` (string, ex. "ENF-ROM", "DOC-SCI")
- `name` (traduit via modeltranslation : fr, en, es, mg)
- `abbreviation` (string 20 car., **non traduite**) — cote imprimée sur la tranche du livre (FEAT-067). Depuis FEAT-071, **le code et la cote sont identiques** dans le seed : `AD FIC`, `EN ALB`…
- `parent` (FK self, nullable) — plus utilisé par le seed depuis FEAT-071 : une tranche d'âge n'est pas un rayon
- `default_loan_duration_days` (entier, nullable, override des règles)

**Catégories officielles Ofelia (FEAT-071)** — 5 tranches d'âge × 4 types de
document, soit 20 catégories sans hiérarchie :

| | Fiction | Documentaire | Album | Bande dessinée |
|---|---|---|---|---|
| Adultes | `AD FIC` | `AD DOC` | `AD ALB` | `AD BD` |
| Jeunesse | `JE FIC` | `JE DOC` | `JE ALB` | `JE BD` |
| Adolescents | `ADO FIC` | `ADO DOC` | `ADO ALB` | `ADO BD` |
| Enfants | `EN FIC` | `EN DOC` | `EN ALB` | `EN BD` |
| Petite enfance | `PE FIC` | `PE DOC` | `PE ALB` | `PE BD` |

Reprise des bases existantes : `python manage.py migrate_categories`
(`--dry-run` disponible) retire le préfixe de langue des catégories
grand-saconnex (`FR AD FIC` → `AD FIC`, fusion si la cible existe), remappe les
anciennes catégories du seed (`ADU-ROM` → `AD FIC`, `DOC-*` → `AD DOC`…) puis
les supprime. Toute catégorie qu'elle ne sait pas reclasser est **laissée
intacte** et signalée.

> **FEAT-042 (Sprint 13)** — `seed_defaults` fournit les 4 langues (FR/EN/ES/MG) pour les 16 Categories du seed et les 5 MemberCategory (cf. table dans `docs/specs/FEAT-042-default-category-translations.md`). À la création, les 4 colonnes `name_<lang>` sont remplies. Sur les installations existantes, la commande est idempotente : elle backfille uniquement les colonnes vides — toute traduction manuelle saisie via `/admin/` est préservée.

#### Tag
- `id` (PK)
- `name` (traduit)
- `color` (string hex, optionnel pour affichage)

#### Location
- `id` (PK)
- `code` (string court, ex. "A3", "JEU")
- `description` (texte)
- `parent` (FK self, nullable, pour ex. "Salle principale > Rayon A > Étagère 3")

#### Language (FEAT-070)
- `id` (PK)
- `code` (string court unique : `fr`, `en`, `pt`…)
- `name` (traduit via modeltranslation : fr, en, es, mg)

Liste **unique** pour la langue d'un document et les langues parlées d'un
usager : deux listes de langues dans la même application, c'est une de trop.
**Codes internationaux principaux, sans variante régionale** — `fr` couvre le
français de France, du Canada et de Suisse ; `pt` le portugais et le brésilien.
Extensible depuis Avancé → Langues et depuis `/admin/` : figer la liste dans le
code rendrait certains livres incatalogables.

`BibliographicRecord.language` reste un `CharField` libre : les sources en ligne
renvoient des codes de toutes sortes, et un code hors liste doit rester
stockable — il s'affiche alors brut. Les menus sont triés par **libellé traduit**,
donc l'ordre change avec la langue de l'interface.

#### Provenance (FEAT-064)
- `id` (PK)
- `code` (string court unique, ex. "OFELIA", "BM-GE", "DON-DUPONT")
- `label` (texte, nom lisible affiché dans les listes)
- `notes` (texte : contact, date de restitution prévue, conditions du dépôt)

D'où vient un exemplaire. Liste gérée plutôt que texte libre : « Bibl. Genève »
et « Bibliothèque Genève » saisis à la main donneraient deux provenances
distinctes, et un filtre qui ment le jour d'un rendu de fonds coûte cher.
`Item.provenance` est en **PROTECT** : une provenance encore portée par des
exemplaires ne peut pas être supprimée.

Affichage (FEAT-073) : `__str__` renvoie le **nom complet seul** (`label or
code`). Le code reste la clé de saisie — colonne `PROVENANCE` de l'import Excel
— et le repli quand aucun nom n'a été renseigné.

#### BibliographicRecord
- `id` (PK)
- `title` (texte, indexé, FTS5)
- `subtitle` (texte, nullable, indexé FTS5)
- `authors` (M2M Author)
- `publisher` (texte, nullable)
- `publication_year` (entier, nullable)
- `language` (string ISO 639-1, ex. "fr", "en", "es", "mg")
- `isbn_13` (string, nullable, unique si non-null, indexé)
- `isbn_10` (string, nullable, indexé)
- `issn` (string 8 car. normalisé sans tiret, nullable, **unique si non-null**, indexé) — périodiques (FEAT-052)
- `summary` (texte, indexé FTS5)
- `cover_image` (FileField, nullable)
- `category` (FK Category, nullable)
- `tags` (M2M Tag)
- `series_name` (texte, nullable)
- `series_volume` (string, nullable)
- `document_type` (enum : book, magazine_issue, newspaper, comic, audio_cd, other)
- `created_at`, `updated_at`, `created_by`
- `metadata_source` (enum : manual, openlibrary, scan_app, import)
- `metadata_quality` (enum : verified, auto, partial) pour distinguer les saisies manuelles validées des import auto à vérifier

Une notice peut exister sans ISBN (livre ancien, scolaire local, auto-édité).

#### Item
- `id` (PK)
- `internal_id` (string, généré, unique, format `OFL-YYYYMMDD-NNNN`)
- `ean13` (string, 13 chiffres, généré à partir de internal_id avec checksum, distinct de l'ISBN)
- `external_code` (string 20 car. alphanumériques, **unique si non vide**) — code Ofelia externe (FEAT-063)
- `record` (FK BibliographicRecord, CASCADE)
- `location` (FK Location, nullable)
- `provenance` (FK Provenance, nullable, PROTECT) — FEAT-064
- `state` (enum : new, good, worn, damaged)
- `acquisition_date` (date, default now)
- `acquisition_source` (enum : purchase, donation, exchange, unknown)
- `donor` (string, nullable)
- `notes` (texte)
- `status` (enum : available, on_loan, reserved_for_pickup, in_repair, lost, discarded)
- `created_at`, `updated_at`

L'EAN13 imprimé sur l'étiquette est dérivé de l'`internal_id`, pas de l'ISBN. Ainsi chaque exemplaire a un code unique même si plusieurs partagent le même ISBN. Préfixe interne 290 (zone "in-store" non attribuée par GS1) pour éviter toute collision avec un vrai code commercial.

Format EAN13 :
- Caractère 1 à 3 : `290` (préfixe Ofelia, in-store)
- Caractère 4 à 12 : numéro séquentiel de l'exemplaire (000000001 à 999999999)
- Caractère 13 : checksum standard EAN-13

**Terminologie UI (FEAT-018)** : ce code EAN13 interne (champ `Item.ean13`) est désigné « **code Ofelia** » dans toute l'interface utilisateur. Le terme technique « EAN13 » n'apparaît plus comme libellé visible ; il reste le nom du champ modèle et de la norme du code-barres. À ne pas confondre avec le « code interne » (`Item.internal_id`, format `OFL-AAAAMMJJ-NNNN`), qui est un identifiant lisible distinct.

**Non-réutilisation des codes Ofelia (FEAT-043)** : un `internal_id` (et l'EAN13 dérivé) imprimé sur une étiquette physique ne doit jamais être réattribué à un nouvel exemplaire. À chaque suppression d'`Item` (unitaire, bulk-delete, CASCADE depuis `BibliographicRecord`, admin), une ligne est insérée dans `RetiredItemCode` (tombstone : `internal_id` PK, `ean13`, `record_title_snapshot`, `retired_at`, `retired_by`, `reason ∈ {item_delete, bulk_delete}`) via un signal `pre_delete`. `Item._assign_codes()` calcule le `MAX(internal_id)` du jour en **union `Item ∪ RetiredItemCode`** ; un code retiré n'est donc jamais réattribué, même si tous les items du jour sont supprimés. Migration `catalog/0007_retired_item_codes`.

**Code Ofelia externe (FEAT-063)** : certains livres arrivent avec un code déjà
attribué hors de BibliOfelia (autre bibliothèque, donateur, catalogage
antérieur). `external_code` permet de l'enregistrer et de le **scanner ou le
saisir indifféremment du code Ofelia**, partout : recherche globale, recherche
du catalogue, prêt, retour, récolement, API. Saisie tolérante — espaces, tirets
et points retirés, minuscules passées en majuscules, de sorte que
`bcf-1329 8781x` et `BCF13298781X` soient le même code. Unicité partielle
(`item_external_code_unique_not_blank`) : le code désigne un exemplaire et un
seul, mais reste facultatif.

Ordre de résolution d'un code saisi (`apps/catalog/lookup.py:find_item`) :
code Ofelia (290…) d'abord, puis code externe. Le code maison garde donc la
priorité — un code externe qui aurait la forme d'un EAN13 Ofelia ne peut pas
détourner le scan d'une étiquette de la bibliothèque. Au récolement, le pointage
est stocké sous le **code Ofelia** de l'exemplaire retrouvé, quelle que soit
l'étiquette lue : scanner les deux étiquettes du même livre ne compte qu'une
fois.

#### MemberCategory
- `id` (PK)
- `code` (string, ex. "ADULTE", "ENFANT", "ECOLE")
- `name` (traduit)
- `max_concurrent_loans` (entier)
- `default_loan_duration_days` (entier)
- `allowed_document_types` (M2M ou JSON liste enum)
- `card_validity_months` (entier, ex. 12)

Seed :
- Enfant (< 14 ans) : 3 prêts, 21 jours
- Adolescent (14-17 ans) : 5 prêts, 21 jours
- Adulte : 5 prêts, 21 jours
- Enseignant : 15 prêts, 60 jours
- Collectif (école/famille) : 20 prêts, 30 jours

#### Member
- `id` (PK)
- `card_number` (string, généré, unique, format EAN13 avec préfixe 291)
- `first_name`, `last_name`
- `birth_date` (date, nullable)
- `category` (FK MemberCategory)
- `contact_phone` (string, nullable)
- `address` (texte, nullable)
- `registration_date` (date)
- `expiration_date` (date, calculée à l'inscription, ajustable)
- `status` (enum : active, suspended, expired, closed)
- `notes` (texte)
- `preferred_language` (string ISO 639-1, default = langue de la box) — dans quelle langue **écrire** à l'usager
- `spoken_languages` (JSON, liste de codes) — langues que l'usager **parle** (FEAT-065)
- `spoken_languages_other` (string 200 car.) — langues hors liste, séparées par des virgules, non vérifiées
- `replaces_card_number` (string, nullable, pour traçabilité remplacement)
- `photo` (FileField, nullable, optionnel)

> **FEAT-066** — `parent_account` (compte collectif parent) a été **supprimé** :
> les enfants d'un usager inscrit ne sont pas eux-mêmes des usagers, ils
> n'empruntent pas et n'ont pas de carte. Ils sont désormais décrits par
> `MemberChild`.

#### MemberFamilyMember (FEAT-072, ex-`MemberChild` FEAT-066)
- `id` (PK)
- `member` (FK Member, **CASCADE**)
- `first_name` (string 80)
- `gender` (enum : f = Fille, m = Garçon, x = Autre ; facultatif)
- `is_adult` (booléen)
- `birth_year` (entier, nullable) — pour un enfant ; l'âge est calculé
- `languages` (JSON, mêmes codes que `Member.spoken_languages`)
- `languages_other` (string 200)

Une carte sert souvent à toute une maisonnée : conjoint, grands-parents,
enfants. D'où **`MemberFamilyMember`** et non plus « enfant ». Ces personnes ne
sont pas des usagers — pas de carte, pas d'emprunt à leur nom — et supprimer
l'usager supprime sa famille.

**Année de naissance plutôt qu'âge** : un âge saisi une fois devient faux
l'année suivante. L'âge affiché (`année courante − birth_year`) est une
approximation assumée : la bibliothèque a besoin de « environ 7 ans », pas de la
date d'anniversaire.

**Langues parlées (FEAT-065)** : depuis FEAT-070, elles viennent de la table
`catalog.Language` — même liste que la langue des documents, extensible. Un code
inconnu (import, ancienne saisie, langue retirée) est restitué tel quel plutôt
qu'escamoté. « Persan » et « Farsi » sont deux entrées distinctes parce que la
liste demandée les distingue.

#### Loan
- `id` (PK)
- `item` (FK Item)
- `member` (FK Member)
- `loan_date` (datetime)
- `due_date` (date)
- `return_date` (datetime, nullable)
- `renewal_count` (entier, default 0)
- `librarian` (FK User)
- `status` (enum : active, returned, overdue, lost, written_off)
- `notes` (texte)

#### InHouseConsultation (consultation sur place)
- `id` (PK)
- `item` (FK Item, nullable, possible de compter sans identifier le livre)
- `member` (FK Member, nullable)
- `date` (date)
- `count` (entier, default 1, permet saisie groupée)

#### Reservation
- `id` (PK)
- `record` (FK BibliographicRecord)
- `member` (FK Member)
- `created_at`
- `expires_at` (date, default = créé + paramètre `reservation_expiry_days`)
- `status` (enum : pending, ready_for_pickup, fulfilled, expired, cancelled)
- `ready_since` (date, nullable, date à laquelle un exemplaire a été mis de côté)
- `fulfilled_by_item` (FK Item, nullable)
- `fulfilled_by_loan` (FK Loan, nullable)

#### Setting (paramètres globaux)
- `key` (PK string)
- `value` (JSON)
- `description` (texte)

Clés attendues :
- `default_language`
- `enabled_languages` (liste)
- `library_name`
- `library_address`
- `reservation_expiry_days` (default 7)
- `pickup_hold_days` (default 5)
- `overdue_grace_days` (default 0)
- `backup_usb_path`
- `cloud_backup_enabled`
- `printer_label_format`
- `printer_card_format`

#### User (django.contrib.auth.User étendu)
- Standard Django
- `role` (enum : superadmin, librarian, contributor_api, readonly)
- `default_language`

#### Audit
- Via django-auditlog, pas de modèle custom (enregistrement explicite des modèles audités → Task #4).

#### Écarts d'implémentation (FEAT-002)

- Les champs `CharField` "nullable" dans la spec sont implémentés `blank=True` (chaîne vide), convention Django pour éviter le double état null/empty. Concerne notamment `BibliographicRecord.subtitle`, `Member.replaces_card_number`.
- `Item.internal_id` et `Item.ean13` sont générés dans `Item.save()` au premier `pk` connu (compteur quotidien pour `internal_id`, préfixe `290`+pk pour `ean13`).
- `Member.card_number` généré dans `Member.save()` avec préfixe `291`+pk.
- `Member.expiration_date` auto-calculé à la création (`registration_date + category.card_validity_months`).
- Tokenizer FTS5 : `unicode61 remove_diacritics 2` (recherche tolérante aux accents).

### 5.3 Index et performance

Index dédiés :
- `BibliographicRecord(isbn_13)` unique
- `BibliographicRecord(isbn_10)`
- `BibliographicRecord(issn)` unique si non-null (FEAT-052 — « 1 notice par ISSN »)
- `Item(internal_id)` unique
- `Item(ean13)` unique
- `Item(status, location_id)` pour récolement
- `Member(card_number)` unique
- `Loan(member_id, status)` pour règles de prêt
- `Loan(due_date, status)` pour rapports retards
- FTS5 virtuel sur `(title, subtitle, summary, authors_concat)` via triggers sync (`catalog_record_fts`, migration `catalog/0002_fts5`). `authors_concat` est un `group_concat(full_name, ' ')` resynchronisé sur ajout/suppression M2M `BibliographicRecord.authors`.

#### ExcelCatalogJob (FEAT-050)
Travail de catalogage à partir d'un fichier Excel (migration `catalog/0009_excel_catalog_job`).
- `mode` (`verify` / `import`), `state` (`pending`/`running`/`finished`/`failed`)
- `uploaded_file`, `result_file` (`media/excel_jobs/AAAA/MM/`)
- `scan_session` (FK `ScanSession`, SET_NULL — mode IMPORT uniquement)
- `total`, `processed`, `matched_by_isbn`, `matched_by_ta`, `not_found`, `errors`, `rate_limited` (BUG-019 — lignes incomplètes pour cause de quota 429 ; migration `catalog/0010`)
- `report` (JSON list — avertissements par ligne)
- `created_at`, `finished_at`, `created_by` (User, SET_NULL)
- Logique : `apps/catalog/excel_catalog.py` (cf. §6.12). Tâche django-q2
  `run_excel_catalog_job(job_id)` idempotente (garde `state != PENDING`).

---

## 6. Fonctionnalités détaillées

### 6.1 Catalogage

#### Saisie d'une nouvelle notice
- Formulaire web simple, champs essentiels visibles, champs avancés repliables
- Champ ISBN avec bouton "Récupérer" qui appelle OpenLibrary en async
- Si la box a internet, lookup direct ; sinon, tâche en file d'attente, l'utilisateur peut continuer
- Saisie manuelle complète possible si pas d'ISBN ou pas de réponse OpenLibrary

#### Saisie d'exemplaire
- Bouton "Ajouter un exemplaire" depuis une notice
- Champ `nombre de copies` (1 par défaut, jusqu'à 20) pour création groupée
- Chaque exemplaire reçoit un internal_id et un EAN13 calculé
- Bouton "Imprimer étiquette(s)" qui ouvre le PDF d'étiquettes (FEAT-074)

#### Import batch depuis OfeliaScan
- Réception via API REST (cf. §6.10)
- File d'attente "à valider" avec aperçu de chaque entrée
- Validation manuelle ou en masse
- Notices créées en `metadata_quality = auto`

#### Catalogage en scan caméra continu (FEAT-046)

Depuis `/catalog/scan/`, un bibliothécaire démarre un **lot** (catégorie +
emplacement par défaut, surchargeables ligne par ligne), puis scanne en rafale
les codes-barres ISBN (EAN-13 `978…`/`979…`) avec la **caméra du navigateur**
(même moteur continu que le récolement FEAT-045 : double moteur
html5-qrcode/Quagga, EAN-13 + clé de contrôle + préfixe + consensus, bande de
décodage centrale assombrie, HTTPS/localhost requis). Réutilise les modèles
`ScanSession`/`ScanItem` et le service `finalize_scan_session()` d'OfeliaScan
(cf. §6.10) ; nouveaux champs `Item.catalog_session`, `ScanItem.category`,
`ScanSession.default_location`/`default_category` (migration `catalog/0008`).

- **Lookup multi-sources** : à chaque nouveau scan, `lookup_isbn_multi()`
  interroge **en parallèle** OpenLibrary + Google Books + BnF + BNE (les sources
  FEAT-031) et retient le 1er titre non vide (ordre OL → Google Books → BnF →
  BNE). La BnF couvre les livres FR là où OpenLibrary seule échoue. Le titre des
  notices SRU (BnF/BNE), qui colle la mention de responsabilité par ` / `, est
  coupé au premier ` / ` (« Le Bélier / Vincent Villeminot ; ill… » → « Le
  Bélier »). Google Books n'est interrogé que si une clé API est configurée.
- **Pendant le scan** : titre + auteur affichés si le lookup les trouve, sinon
  `ISBN <code> · <langue>`.
- **Exemplaires multiples** : un même ISBN re-présenté après **> 3 s** ajoute un
  exemplaire (`copy_count++`, « exemplaire X » affiché en gros) ; une re-lecture
  ≤ 3 s (livre tenu en vue) est ignorée. Endpoint `POST /catalog/scan/<pk>/add/`
  (JSON `{action: created|incremented|ignored|rejected, …}`). Les codes Ofelia
  (290) et cartes membres (291) sont **refusés**. La vue est en
  `non_atomic_requests` (autocommit) pour que la ligne créée soit immédiatement
  visible des POST concurrents (sinon le lookup HTTP, lent, tient la transaction
  ouverte sous `ATOMIC_REQUESTS` → doublons d'ISBN).
- **Périodiques ISSN (FEAT-052)** : un code-barres **préfixe 977** (revue/magazine)
  est accepté en catalogage (le scanner caméra n'autorise le 977 qu'ici, via
  `allowIssn`). `scan_add` en extrait l'ISSN (`issn_from_ean13`), pose
  `scan_kind=issn` et interroge les sources ISSN (`lookup_issn_multi` → BnF/BNE).
  À la finalisation, la notice est matchée/créée par **ISSN** avec
  `document_type=magazine_issue` ; deux numéros d'une même revue → **une seule
  notice** (ISSN unique). Le n° de livraison se note à la main dans `series_volume`.
- **Hub** `/catalog/scan/<pk>/` : tableau des titres détectés. Titre / auteur /
  langue sont **en lecture seule** (issus du lookup ; auteur au-dessus du titre,
  colonne large). Catégorie / emplacement / état se modifient **uniquement par
  lot** : on coche des lignes (ou « tout cocher »), on choisit les valeurs dans
  le panneau « Modifier les lignes cochées », puis « Appliquer ». Le nombre
  d'exemplaires et la suppression de ligne restent unitaires. Table en scroll
  horizontal sur mobile.
- **« Envoyer au catalogue »** (`scan_session_commit` → `finalize_scan_session`) :
  une notice existante (match ISBN) reçoit **seulement** de nouveaux exemplaires
  (elle n'est pas modifiée) ; une notice nouvelle est créée avec la catégorie du
  lot. Chaque exemplaire créé est rattaché à la session (`Item.catalog_session`).
- **Impression ciblée** : `printing:labels?catalog_session=<pk>` ne liste que les
  exemplaires du lot (pré-cochés) — réimpression sans les livres déjà catalogués.
- **Consulter un lot validé (FEAT-058)** : la liste `/catalog/scan/` propose
  « Voir le lot » sur chaque lot validé (à côté de « Étiquettes »), et le hub d'un
  lot finalisé affiche ses livres **en lecture seule** — auteur/titre/ISBN, langue,
  catégorie, emplacement, nombre d'exemplaires, plus un lien « Voir la notice »
  par ligne (`ScanItem.processing_result["record_id"]`). Aucune réouverture : un
  lot validé ne se re-finalise pas (pas de risque de recréer des exemplaires déjà
  matérialisés) ; les notices restent modifiables individuellement.

#### Catalogage à la douchette USB (FEAT-054)

Variante du catalogage caméra pour les postes équipés d'une **douchette USB**
(lecteur de code-barres en mode clavier HID). Entrée **Avancé → Inventaire →
« Catalogage par douchette »** (`catalog:scan_douchette_create`). Réutilise
intégralement `ScanSession`/`ScanItem`/`scan_add`/`finalize_scan_session` — seule
la **méthode de saisie** change (pas de caméra). Le champ `ScanSession.input_mode`
(`mobile`/`camera`/`douchette`, migration `catalog/0012`) mémorise le mode : le
hub `/catalog/scan/<pk>/` masque alors le bouton caméra et rend le champ ISBN
`data-wedge-primary autofocus`. Le **keyboard-wedge global** (`scan-wedge.js`,
cf. §6.1 Recherche) capte chaque scan douchette, remplit ce champ et le soumet
au serveur (`scan_add`) — mêmes règles created / incremented (« exemplaire X ») /
rejected (290-291) que le catalogage caméra. Aucun clic requis : on scanne les
livres en rafale, la liste live et le tableau éditable se remplissent.

La page ne se rechargeant jamais dans ce mode (scans en AJAX), le tableau rendu
par le serveur devient périmé dès le premier scan : un bouton **« Terminer et voir
le lot »** recharge la page pour éditer la liste puis l'envoyer au catalogue.
**BUG-024** : ce bouton n'est affiché que lorsqu'il sert à quelque chose — masqué
(`#cat-refresh-wrap[hidden]`) si le serveur vient de rendre les lignes, réaffiché
par `scan-cataloging.js` au premier scan `created`/`incremented` suivant (un scan
`ignored`/`rejected` ne change pas la liste, donc ne le réaffiche pas).

#### Recherche
- Barre de recherche globale sur toutes les pages
- Full-text via FTS5 sur titre, sous-titre, résumé, auteurs
- Recherche exacte sur ISBN (13 ou 10) si la requête ressemble à un ISBN
- Recherche exacte sur EAN13 d'exemplaire ou n° de carte membre
- **Code Ofelia externe (FEAT-063)** : un code externe se saisit ou se scanne
  exactement comme un code Ofelia, ici comme partout ailleurs. Il n'a aucune
  forme reconnaissable, `classify_query` le classe donc en « texte » et c'est
  `find_item()` qui tranche, avant le repli plein texte. Un code d'exemplaire ou
  une carte qui ne correspond à rien ne retombe **pas** en plein texte : la
  liste est vide, plutôt que bruitée.
- **Scan douchette USB (FEAT-054)** : le module `static/js/scan-wedge.js` (chargé
  partout pour les utilisateurs connectés) écoute le clavier au niveau du document
  en **phase de capture** ; il reconnaît la signature d'une douchette (rafale de
  frappes ≤ 35 ms, ≥ 3 caractères, terminée par `Entrée`), capte le code entier et
  **neutralise toute la salve** (plus de fuite vers un raccourci navigateur —
  corrige BUG-020, où le suffixe ouvrait `Ctrl+J`). **Aucun clic requis.** Routage :
  champ de scan primaire présent (`input[data-wedge-primary]` sur prêt/retour/
  catalogage douchette, ou champ d'un bouton `.js-scan-handoff[data-scan-target]`)
  → remplissage + submit ; sinon → `core:search?q=<code>` (via `classify_query`,
  fiche notice ou membre). Le wedge se retire quand le modal caméra est ouvert et
  ignore textarea/contenteditable/password et les combinaisons `Ctrl/Alt/Meta`
  (la frappe humaine, lente, n'est jamais captée).
- Filtres dans la page catalogue (`catalog:record_list`) : catégorie, type de document, langue, **emplacement** (FEAT-051 — sélecteur `Location` ; une notice est retenue si **au moins un** de ses exemplaires est dans l'emplacement choisi : `records.filter(items__location_id=location).distinct()`), **tag** (recherche substring case-insensitive sur le nom — `science` matche « Science Fiction » et « science populaire »), recherche texte/ISBN/EAN13/**ISSN** dans la barre principale (route via `classify_query` : `isbn` → `Q(isbn_13=v) | Q(isbn_10=v)`, `item` → `items__ean13=v`, `issn` (EAN13 977 ou ISSN saisi `1828-552X`, FEAT-052) → `issn=v`, sinon FTS5).
- Tri : pertinence, titre, auteur, date d'ajout
- **Filtre provenance (FEAT-064)** : en mode notice, retient les notices ayant
  **au moins un** exemplaire de cette provenance ; en mode exemplaire, filtre
  directement les lignes affichées.
- **Recherche par exemplaire (FEAT-064, FEAT-073)** — deux boutons ferment la
  barre de filtres : **« Rechercher des notices »** et **« Rechercher des
  exemplaires »** (`?mode=items`). Ils postent les mêmes filtres, seul le mode de
  résultat change. Groupés dans `.search-modes` pour rester côte à côte quand la
  barre passe à la ligne, et colorés en bordeaux (mode courant) / olive. Sans clic, la page
  affiche les notices, sans filtre. En mode exemplaire : une ligne **par
  exemplaire** au lieu d'une ligne par notice.
  3 exemplaires d'une même notice = 3 lignes. La colonne « Ex. » (nombre
  d'exemplaires), qui n'a plus de sens ligne à ligne, cède la place à **Code
  Ofelia**, **Code Ofelia externe** et **Provenance**. Les autres filtres et la
  recherche plein texte continuent de s'appliquer (le FTS reste indexé sur les
  notices : on filtre ensuite `record_id__in`). Sans la case, le catalogue se
  comporte exactement comme avant.
  C'est le seul écran qui montre qu'un même titre a un exemplaire acheté par la
  bibliothèque **et** un exemplaire prêté par une autre — et donc le chemin
  prévu pour ne rendre que les seconds.
- Pagination (25/page) : les liens Précédent/Suivant conservent **tous** les filtres actifs (FEAT-051). La vue expose `base_qs` = querystring courante privée de `page` (`request.GET.copy()` → `pop('page')` → `urlencode()`) ; le template construit `?{{ base_qs }}&page=N`. Avant FEAT-051, seuls `q` et `q_tag` étaient repris (les sélecteurs catégorie/type/langue/emplacement étaient perdus au changement de page).

#### Modification et suppression
- Édition libre de notice et exemplaire pour bibliothécaires
- **Pilonner un exemplaire** (`item_discard`) : passage du statut à `DISCARDED`, exemplaire conservé en base. Cas d'usage : livre abîmé sortant du fonds. Bloqué si statut `ON_LOAN` ou `RESERVED_FOR_PICKUP`.
- **Supprimer définitivement un exemplaire** (FEAT-027 — `item_delete`) : DELETE hard. Cas d'usage : doublon, EAN13 mal saisi, vol. Aucun blocage : si l'exemplaire est prêté, le prêt actif passe à `LoanStatus.LOST` (`return_date=now`) ; si réservé, la réservation correspondante passe à `CANCELLED` ; les prêts passés sont supprimés en cascade (CASCADE manuel car `Loan.item=PROTECT`). Bouton à côté de "Pilonner" sur la fiche notice. Rôle librarian + superadmin.
- **Supprimer une notice** (`record_delete`) : interdite si exemplaires actifs (AVAILABLE / ON_LOAN / RESERVED / IN_REPAIR), sinon DELETE en cascade.
- **Suppression en masse** (FEAT-026 — `record_bulk_delete`) : checkboxes sur `record_list.html` (visibles librarian + superadmin depuis FEAT-041) + barre d'action sticky. Bouton « Supprimer » réservé au superadmin → page de confirmation listant pour chaque notice le nombre d'exemplaires, de prêts actifs et de réservations actives impactés. Aucun blocage : prêts actifs → `LOST`, résa actives → `CANCELLED`, puis suppression en transaction unique (Item.record=CASCADE).
- **Actions en masse — affectation directe (FEAT-069, remplace FEAT-041)** : la
  barre d'action porte désormais des **menus déroulants** et un bouton
  **Affecter**, sans page intermédiaire. Chaque menu vaut « Ne pas modifier »
  par défaut, et propose « — (vider) » pour retirer une affectation.
  - Fenêtre **« X notices sélectionnées »** : menus **Catégorie** et
    **Emplacement**. La catégorie s'applique aux notices, l'emplacement à tous
    leurs exemplaires.
  - Fenêtre **« X exemplaires sélectionnés »** : menu **Provenance**.

- **Sélection étendue (FEAT-073)** — deux cases distinctes au-dessus de la
  liste :
  - **« Sélectionner les N résultats visibles »** — la page courante ;
  - **« Sélectionner les N résultats de la recherche »** — toutes les pages.
    N'apparaît qu'à partir de 2 pages.

  Cocher l'une décoche l'autre, et cocher une ligne annule la sélection étendue :
  ce sont des intentions distinctes. L'ancien « Tout cocher » ne prenait que les
  25 lignes visibles sans le dire — croire qu'on a tout sélectionné avant une
  suppression est un piège.

  Quand « tous les résultats » est actif, l'action porte sur **la recherche** :
  le formulaire transmet les filtres (`back_qs`) et le serveur reconstruit le
  même queryset (`_selected_pks`). Les pages de confirmation réinjectent les
  identifiants en clair — ce qui est confirmé est exactement ce qui sera
  supprimé — mais **plafonnent l'affichage** à 100 lignes, avec un « … et N
  autres non affichés ici ».

  Chaque information se pilote au niveau où elle appartient (décision Val
  2026-08-20). Sentinelle `keep` en interne : sans elle, « ne pas modifier » et
  « vider » seraient indiscernables. Le retour se fait sur le catalogue **avec
  les filtres actifs** (`back_qs`). Les **suppressions** en masse gardent leur
  page de confirmation : une suppression mérite qu'on relise la liste.

  <details><summary>Comportement FEAT-041 remplacé (Sprint 13)</summary>

- ~~**Actions en masse — catégorie / emplacement** (FEAT-041, Sprint 13) : la même barre d'action expose 2 boutons supplémentaires accessibles aux librarians :
  - « Affecter une catégorie » → page de confirmation avec sélecteur de `Category` (option vide = retirer la catégorie) → `BibliographicRecord.objects.filter(pk__in=ids).update(category_id=...)`.
  - « Affecter un emplacement » → page de confirmation avec sélecteur de `Location` (option vide = retirer l'emplacement) → `Item.objects.filter(record_id__in=ids).update(location_id=...)` : tous les exemplaires des notices sélectionnées sont déplacés en un seul UPDATE.
  Les exemplaires DISCARDED/LOST ne sont pas exclus (réorganisation libre).~~

  </details>
- **Suppression en masse d'exemplaires (FEAT-064)** : en mode « Chercher les
  exemplaires », les cases cochent des `Item` et la barre d'action expose :
  - « Supprimer les exemplaires sélectionnés » (**superadmin**) → page de
    confirmation annonçant les prêts en cours et les mises de côté touchés.
    Même traitement que la suppression unitaire (FEAT-027) : prêts en cours
    clos en `LOST`, réservations servies annulées, historique de prêts et de
    consultations effacé, **tombstone** du code Ofelia (FEAT-043,
    `reason=bulk_delete`). Les notices, elles, restent au catalogue.
- Historique conservé via django-auditlog

#### Gestion des emplacements (FEAT-032)

Les emplacements (`catalog.Location` : `code`, `description`, `parent` FK self) sont les zones physiques de rangement utilisées au catalogage (`Item.location`) et au récolement (`InventorySession.scope_location`). Jusqu'au Sprint 9, ils n'étaient gérables que via `/admin/catalog/location/` (réservé superadmin / debug Claude). FEAT-032 expose une UI librarian dédiée :

- **Route** : `/catalog/locations/` (liste), `/new/`, `/<pk>/edit/`, `/<pk>/delete/`. Namespace `catalog:location_list` etc. Permission `librarian + superadmin` via `@require_role(*WRITE_ROLES)`.
- **Accès** : carte « Emplacements » dans `templates/core/advanced.html` section *Inventaire* (icône `map-pin`, style olive cohérent avec la section).
- **Liste** : table code / description / parent / nombre d'exemplaires rattachés / actions Éditer + Supprimer. Tri par code croissant.
- **Formulaire** : `LocationForm` ModelForm (`code` required max 20, `description` textarea optionnel, `parent` select optionnel excluant `self`). Validation `(code, parent)` unique côté form (en plus de la contrainte DB) pour erreur lisible.
- **Suppression** : page de confirmation listant le nombre d'exemplaires rattachés et de sous-emplacements. SET_NULL côté `Item.location` et `InventorySession.scope_location` — les exemplaires perdent leur emplacement (affichés « — »), les sessions de récolement passées conservent leur historique. Aucun blocage.
- **Comportement OfeliaScan inchangé** : `_resolve_location` (`apps/api/services.py:44`) reste un `filter(code=…).first()` silencieux — si OfeliaScan envoie un `location_code` inconnu, l'exemplaire est créé sans emplacement, pas de 400 ni de log. OfeliaScan est responsable de n'envoyer que des codes valides via le picker (`GET /api/locations`, cf. §6.10).

Pas de migration : modèle `Location` inchangé depuis FEAT-002 (Sprint 1).

#### Gestion des catégories (FEAT-067)

Jusqu'ici les catégories n'existaient que dans le seed et dans `/admin/`, hors
de portée des bibliothécaires : la cote de rayon n'aurait été saisissable par
personne sur le terrain.

- **Route** : `/catalog/categories/` (liste), `/new/`, `/<pk>/edit/`, `/<pk>/delete/`.
- **Accès** : carte « Catégories » dans `templates/core/advanced.html`.
- **Liste** : code / nom / abréviation / parent / nombre de notices (lien vers le
  catalogue filtré) / Éditer + Supprimer.
- **Formulaire** : `CategoryForm` (`code` requis, `name` requis, `abbreviation`,
  `parent` — jamais soi-même —, `default_loan_duration_days`).
- **Suppression** : aucune notice n'est supprimée. Les notices concernées perdent
  leur catégorie (`SET_NULL`, comportement déjà en place) ; l'écran de
  confirmation annonce combien.
- **Seed** : les 16 catégories reçoivent une abréviation par défaut
  (`ENF-ALB` → `ENF ALB`…), posée à la création et backfillée si vide. Une cote
  ajustée à la main n'est **jamais** écrasée par un redémarrage.

#### Gestion des langues (FEAT-070)

- **Route** : `/catalog/languages/` (liste), `/new/`, `/<pk>/edit/`, `/<pk>/delete/`.
- **Accès** : carte « Langues » dans `templates/core/advanced.html`, et
  `LanguageAdmin` dans `/admin/`.
- **Liste** : nom / code / nombre de notices (lien vers le catalogue filtré),
  triée par libellé traduit.
- **Suppression** : aucune notice n'est touchée. Les notices gardent leur code,
  qui s'affiche brut au lieu du libellé traduit ; l'écran l'annonce.
- **Seed** : 22 langues, traduites en 4 langues, backfillées si vides.
- **Reprise** : la migration `catalog/0017` normalise les codes hérités des
  sources en ligne (`fre-fre` → `fr`) — 94 notices concernées sur la Box, qui
  n'apparaissaient dans aucun filtre.

#### Gestion des provenances (FEAT-064)

- **Route** : `/catalog/provenances/` (liste), `/new/`, `/<pk>/edit/`, `/<pk>/delete/`.
- **Accès** : carte « Provenances » dans `templates/core/advanced.html`.
- **Liste** : code / nom complet / notes / nombre d'exemplaires (lien vers la
  recherche par exemplaire filtrée sur cette provenance) / Éditer + Supprimer.
- **Suppression gardée** : refusée tant qu'un exemplaire porte la provenance
  (`Item.provenance` en PROTECT). L'écran indique combien d'exemplaires sont
  concernés et propose de les voir. C'est le garde-fou qui évite d'effacer par
  erreur la seule trace de « à qui appartient ce livre ».
- **Affectation en masse** : provenance par défaut d'un lot de catalogage
  (`ScanSession.default_provenance`, appliquée à tous les exemplaires du lot),
  colonne Excel `PROVENANCE`, ou action de masse depuis le catalogue.

### 6.2 Gestion des usagers

#### Inscription
- Formulaire prénom/nom obligatoires, autres champs optionnels
- Choix de la catégorie
- Calcul automatique de `expiration_date` selon `card_validity_months`
- Génération de `card_number`
- Aperçu de la carte (PDF) avec bouton "Imprimer"

#### Carte membre
- PDF A4 avec 8 cartes pré-découpées ou format individuel
- Contient : nom, n° de carte, EAN13 du n° de carte, date d'expiration, langue de l'usager, nom de la bibliothèque, photo (si présente)
- Format paramétrable via `printer_card_format`
- Première version : impression papier ordinaire à plastifier soi-même

#### Historique de prêt
- Vue dédiée par usager : prêts en cours, historique complet, livres lus dans la bibliothèque
- Statistiques personnelles (nombre de prêts par catégorie)

#### Compte collectif
- Création d'un Member type "collectif" (école, famille) via `MemberCategory`
- Règles de prêt appliquées au compte collectif

> **FEAT-066** — le rattachement d'usagers entre eux (`parent_account`) a été
> retiré : il n'a jamais servi. Un compte collectif reste une catégorie
> d'usager ; les enfants d'un usager sont décrits sur sa fiche (ci-dessous).

#### Langues parlées (FEAT-065)

Champ **« Langues parlées »** sur la fiche usager, à ne pas confondre avec
`preferred_language`, qui ne dit que dans quelle langue lui écrire. Plusieurs
langues par personne, cochées dans un encadré alimenté par la **liste gérée des
langues** (22 au départ, extensible — cf. §6.1 *Gestion des langues*, FEAT-070),
plus un champ libre **« Autres langues »** (séparées par des virgules, aucune
vérification). Les cases sont triées par libellé dans la langue de l'interface.

Des cases à cocher plutôt qu'un `<select multiple>` : sur un téléphone ce
dernier se manipule mal, et il ne faut pas savoir qu'on maintient Ctrl pour
cocher deux langues. La fiche affiche les langues cochées (traduites) suivies
du champ libre.

#### Famille rattachée (FEAT-072, ex-« Enfants » FEAT-066)

Section **« Famille »** du formulaire usager : autant de lignes que de personnes
partageant la carte — conjoint, grands-parents, enfants. Chacune avec
**prénom**, **sexe** (facultatif), **Adulte ou enfant**, une **année de
naissance** pour les enfants (l'âge est calculé et affiché), et les mêmes
**langues** que l'usager (cases + champ libre).

Choisir « Adulte » efface l'année de naissance : garder une donnée qui ne sera
jamais affichée ne rend service à personne.

- Ajout et retrait de lignes sans quitter le formulaire (JS, sans dépendance).
- Une ligne dont le prénom est vide est **ignorée** à l'enregistrement : le
  formulaire propose toujours une ligne libre, la laisser vide ne doit pas
  produire d'erreur. Le bouton « Retirer » vide la ligne — ce qui, pour une
  ligne déjà enregistrée, vaut suppression.
- Supprimer un usager supprime sa famille (CASCADE) : ce ne sont que des
  données descriptives de sa fiche.
- **Carte de membre** : les prénoms apparaissent dans une **colonne « Famille »
  à droite** de la carte (planche A4 et ruban), un par ligne, tronquée par « … »
  si la place manque. Sur la planche A4, le bloc texte se décale à gauche
  **uniquement** quand il y a une famille — sinon la colonne tronquait le nom du
  titulaire ; une carte sans famille garde exactement le rendu du Sprint 27.

#### Remplacement de carte
- Bouton "Remplacer la carte" sur la fiche
- Génère un nouveau `card_number`, stocke l'ancien dans `replaces_card_number`
- Ancien numéro désactivé pour l'identification mais conservé pour traçabilité

#### Renouvellement et expiration
- Tâche django-q2 quotidienne marque `expired` les cartes dont `expiration_date < today`
- Avertissement à la bibliothécaire au scan d'une carte expirante (< 30 jours)
- Renouvellement = mise à jour de `expiration_date` (1 clic)

#### Désactivation / réactivation (FEAT-028)
- Bouton **« Désactiver »** sur la fiche membre (rôle librarian + superadmin) : passe `MemberStatus.ACTIVE` → `SUSPENDED`. Le membre reste consultable, son historique est préservé, mais aucun nouveau prêt ne peut lui être enregistré (`loans.services.check_item_loanable` refuse toute member dont `status != ACTIVE`).
- Bouton **« Réactiver »** quand le membre est `SUSPENDED`, `EXPIRED` ou `CLOSED` : repasse en `ACTIVE`. Si l'`expiration_date` est dépassée, elle est recalculée à `today + card_validity_months` (équivalent renew implicite).
- Action atomique sans page de confirmation (réversible en 1 clic).

#### UI fiche & édition (FEAT-037 + BUG-015)
- Les `DateInput` du `MemberForm` (birth_date, registration_date, expiration_date) sont rendus au format ISO `%Y-%m-%d` pour que le widget HTML5 `<input type="date">` accepte la valeur existante en édition. Avant BUG-015, les inputs apparaissaient vides → effacement involontaire au submit.
- `registration_date` est initialisée à `date.today` côté form lors de la création.
- JS minimal sur `member_form.html` : au `change` de `registration_date`, `expiration_date` est mise à `registration_date + 1 an` (l'utilisateur peut écraser ensuite). Côté serveur, `Member.save()` reste autoritaire si `expiration_date` est vide (calcul via `MemberCategory.card_validity_months`).
- La photo du membre (`Member.photo`, `FileField`) est affichée sur la fiche `members:detail` (dans le `pagehead` à la place de l'icône user) et sur le formulaire d'édition en miniature au-dessus du champ upload.

#### Suppression d'un membre (FEAT-029)
- Bouton **« Supprimer le membre »** sur la fiche membre, rôle superadmin uniquement. Page de confirmation listant les impacts (prêts en cours, réservations actives, prêts passés, comptes rattachés).
- En exploitation normale, on désactive plutôt qu'on supprime (cf. FEAT-028). La suppression cible le nettoyage post-install (notices de démo non couvertes par `manage.py remove_demo`) et les membres fantômes.
- Comportement à la confirmation (transaction atomique) :
  - Réservations actives → `CANCELLED`.
  - Prêts actifs → `RETURNED` + `return_date=now` + exemplaires repassés en `AVAILABLE`.
  - Dépendants (`parent_account=member`) → `parent_account=NULL` (SET_NULL natif).
  - CASCADE manuel : `member.loans.all().delete()`, `member.reservations.all().delete()`, `member.consultations.all().delete()` (les FK sont `PROTECT`, on cascade explicitement dans la vue).
  - `member.delete()`.

### 6.3 Prêts et retours

#### Workflow de prêt
1. Bibliothécaire ouvre l'écran "Prêt"
2. Scan ou saisie de la carte membre (BUG-014 : la touche **Entrée** dans le champ texte soumet bien la saisie manuelle ; le bouton « Scanner » est `type="button"` et un submit caché reprend l'implicit submission HTML)
3. Affichage de la fiche membre, prêts actifs, messages en attente, alertes (retards, carte expirante)
4. Scan ou saisie des EAN13 des livres (idem BUG-014)
5. Pour chaque livre, vérifications :
   - Exemplaire `available`
   - Pas de réservation prioritaire d'un autre usager (sinon alerte + override possible avec note)
   - Limite de prêts simultanés respectée pour la catégorie membre
   - Document type autorisé pour la catégorie
6. Confirmation, calcul de `due_date` à partir de la règle applicable (FEAT-035 : ordre de priorité = `Category.default_loan_duration_days` → `MemberCategory.default_loan_duration_days` → `Setting.default_loan_days` (défaut 21) → constante `DEFAULT_LOAN_DAYS=21`)
7. Création des Loan, mise à jour des Item.status
8. Impression d'un reçu papier (optionnel, paramètre activable)

#### Workflow de retour
1. Bibliothécaire ouvre l'écran "Retour"
2. Scan des EAN13 des livres
3. Pour chaque exemplaire : recherche du Loan actif, marquage `returned`, mise à jour Item.status
4. Si l'exemplaire a une réservation en attente : passage en `reserved_for_pickup`, alerte affichée
5. Si retour en retard : note automatique, statistique
6. Validation finale

#### Renouvellement
- Depuis la fiche membre ou la liste des prêts en cours
- 2 renouvellements max par défaut (paramètre)
- Refus si réservation en attente sur la notice
- Nouvelle `due_date` calculée

#### Consultation sur place
- Page dédiée "Consultation"
- Saisie : usager (optionnel), nombre de livres consultés
- Création d'une entrée InHouseConsultation
- Pas de modification d'Item.status

#### Déclaration de livre perdu
- Depuis la fiche d'un prêt actif ou de l'exemplaire
- Workflow : bibliothécaire marque "perdu"
- Item.status passe à `lost`, Loan.status à `lost`
- Membre voit son historique annoté
- Aucune facturation automatique (à décider par la bibliothèque)

#### Retour différé d'un livre déclaré perdu
- Possible depuis l'écran de retour : si on scanne un EAN13 d'un Item `lost`, on propose la "réintégration"
- Loan.status `lost` reste, mais Item.status repasse à `available`
- Audit log conserve la trace

### 6.4 Réservations

#### Création
- Depuis la fiche notice : bouton "Réserver pour..."
- Choix du membre
- Création de Reservation `pending` avec `expires_at` = aujourd'hui + `reservation_expiry_days`

#### Satisfaction d'une réservation
- À chaque retour d'exemplaire, le système cherche les réservations `pending` sur la notice
- FIFO par `created_at`
- La plus ancienne devient `ready_for_pickup`, l'Item est `reserved_for_pickup`, `ready_since = today`
- Message à afficher au membre concerné lors de sa prochaine venue

#### Liste à honorer
- Tableau "Réservations prêtes" pour la bibliothécaire
- Bouton "Imprimer" pour avoir la liste papier
- Si non retirée après `pickup_hold_days`, la réservation passe `expired` et l'Item redevient `available`. Si une autre réservation `pending` existe, elle prend la place.

#### UI et paramètres (FEAT-034)
- Sur la fiche notice (`catalog:record_detail`), chaque exemplaire en statut `reserved_for_pickup` affiche le n° de carte + nom du membre qui le retient, et la date avant laquelle il doit être retiré (`ready_since + pickup_hold_days`). La fiche affiche aussi la **liste d'attente** complète (réservations `pending` + `ready_for_pickup`) avec position FIFO, membre, date de réservation et statut.
- Sur la page **Retour** (`loans:return_items`), une section « Réservations à relancer » liste les mises de côté dont l'expiration est ≤ aujourd'hui+2 jours, avec un badge « N jours de retard » / « Expire aujourd'hui » / « Encore N jours » → le bibliothécaire peut contacter le membre avant que la réservation ne bascule au suivant.
- Les paramètres `default_loan_days`, `reservation_expiry_days` et `pickup_hold_days` sont exposés dans `/settings/loans/` (« Durées prêts & réservations »), sous la section Paramètres.

#### Verrouillage exemplaire ↔ réservation (rappel)

Une fois `satisfy_reservations_for_item` exécuté pour un exemplaire, ce couple exemplaire ↔ réservation est **fixe** (`reservation.fulfilled_by_item = item`, `item.status = RESERVED_FOR_PICKUP`). Aucun autre membre ne peut emprunter cet exemplaire spécifique (`check_item_loanable` refuse si le membre courant ≠ réservant). Si un autre exemplaire de la même notice se libère, il est attribué à la **2ᵉ position** de la file FIFO, pas à la 1ʳᵉ déjà servie.

#### Flag « notifié » (FEAT-036)

`Reservation.notified_at` (DateTimeField nullable) trace l'instant où le bibliothécaire a contacté le membre par téléphone (membres sans internet) pour lui dire que son livre est prêt. Posé via `POST /loans/reservations/<pk>/notify/`, action idempotente exposée :
- sur `/loans/reservations/` (section « Prêtes à retirer »), bouton **« Notifier »** par ligne ; remplacé par un badge « ✓ Notifié le … » une fois posé.
- sur le **dashboard**, dans un cadre dédié « Notifications à faire » placé entre la grille de tuiles et la bannière scan, listant jusqu'à 5 réservations prêtes non notifiées avec bouton « Notifier » direct.

La page Réservations enrichit la section « Prêtes à retirer » : titre, code Ofelia de l'exemplaire mis de côté, nom + n° de carte du membre, date+heure de réservation (`created_at`), date+heure de mise de côté (lue depuis `fulfilled_by_loan.return_date` quand disponible, sinon `ready_since` à 00:00), date limite de retrait (`ready_since + pickup_hold_days`). Police corps de ligne portée à 16-17 px pour la lisibilité de la liste d'appels téléphoniques.

### 6.5 Récolement

> Libellé UI : depuis FEAT-017, l'écran est intitulé **« Inventaire »**
> (accessible via l'onglet Avancé). L'app, le code et les modèles
> conservent le nom `inventory` ; « récolement » reste le terme du domaine
> dans cette spec.

#### Lancement (FEAT-045 — scan caméra continu)

Depuis FEAT-045, le récolement se fait à la **caméra du navigateur** (le scan
OfeliaScan reste disponible via l'API pour le récolement de masse mobile).

- Page `/inventory/new/` : périmètre réduit à **Tout le fonds** (défaut) ou
  **Un emplacement**. Le scope *Catégorie* est retiré de l'UI (l'énum
  `InventoryScope.CATEGORY` et le champ `scope_category` restent en base pour ne
  pas casser les sessions historiques et `build_report`). Le champ Emplacement
  est grisé tant que le scope est « Tout le fonds », obligatoire dès « Un
  emplacement ».
- Le bouton **« Lancer l'inventaire »** crée la session (`open`) et redirige
  vers `/inventory/<pk>/report/?scan=1`.

#### Pointage caméra (page rapport)

La page `/inventory/<pk>/report/` est désormais le **seul** écran de pointage
(l'ancienne page détail `/inventory/<pk>/` et son `session_detail.html` sont
**supprimés**) :

- Bouton **« Lancer l'inventaire »** / **« Continuer l'inventaire »**
  (`.js-scan-inventory`) → caméra en **mode continu** (`scan-camera.js`,
  `opts.continuous`/`onCode`) : viseur ouvert en permanence, chaque code Ofelia
  confirmé (checksum + préfixe + consensus 2 lectures) déclenche **bip +
  vibration** + un POST.
- **Dé-duplication** : chaque code n'est compté qu'une fois par session (set
  client pré-rempli des scans déjà en base → re-présenter un exemplaire déjà
  pointé est ignoré en silence). Les codes Ofelia étant **par exemplaire**, deux
  copies d'un même titre ont deux codes distincts et sont toutes deux comptées.
- Pendant le scan, le viseur affiche le dernier exemplaire trouvé sous la forme
  **« Titre — Auteur · exemplaire N »**, où N (`copy_index` renvoyé par
  l'endpoint) est le rang de l'exemplaire de cette notice pointé dans la session.
- Endpoint `POST /inventory/<pk>/scan/` (JSON) : enregistre le pointage
  (idempotent via `unique(session, ean13)`), répond
  `{ok, created, known, ean, item:{internal_id, title, author, copy_index,
  location_code}, counts:{expected, scanned}}`. `known=false` si l'EAN ne matche
  aucun `Item` (un code **doit appartenir au catalogue** pour être validé — pas
  d'ajout). HTTP 409 si la session est clôturée.
- `scan-inventory.js` (chargé sur la page rapport) câble le bouton, poste chaque
  code, met à jour le compteur et la liste des derniers scans, et **recharge la
  page** à la fermeture du viseur pour rafraîchir les divergences.
- **Saisie manuelle** : un champ de repli (hors caméra, utile en LAN HTTP) poste
  au même endpoint.
- **Pointage à la douchette USB (FEAT-055)** : le champ de saisie manuelle porte
  `data-wedge-primary autofocus`. Le wedge global (`static/js/scan-wedge.js`,
  §6.1) reconnaît la rafale HID d'une douchette, **remplit ce champ et soumet le
  formulaire** (`inv-manual-form`) — le handler AJAX de `scan-inventory.js`
  intercepte le submit et poste au même endpoint `inventory:add_scan`, **sans
  quitter la page** ni ouvrir la caméra. Aucun clic requis (écoute globale).
  Réutilise donc entièrement le backend et le rendu live existants (compteur,
  liste des derniers scans, dé-duplication). Le wedge se retire quand le modal
  caméra est ouvert (`scan-camera-open`) : pas de double pointage. Avant FEAT-055,
  un scan douchette sur la page rapport n'ayant **aucun champ primaire** était
  routé par le fallback du wedge vers `core:search?q=<code>` → la page de
  récolement était quittée et l'exemplaire jamais pointé.
- Affichage en temps réel du nombre d'exemplaires pointés / attendus.

> Contrainte : la caméra exige un contexte sécurisé (HTTPS). En LAN HTTP, seuls
> le repli saisie manuelle **et la douchette USB** (keyboard-wedge, indépendant de
> la caméra) fonctionnent (HTTPS local box = chantier keebee séparé).

#### Réception des scans OfeliaScan (API, inchangé)
- OfeliaScan envoie progressivement les EAN13 scannés à `POST /api/inventory/{session_id}/items`
- Le serveur enregistre chaque scan avec horodatage et appareil
- Affichage en temps réel du nombre d'exemplaires pointés / attendus

#### Rapport
- Bouton "Clôturer le récolement" (réversible jusqu'à validation finale)
- Génération du rapport :
  - Exemplaires pointés présents (OK)
  - Exemplaires attendus non pointés (manquants)
  - Exemplaires pointés non attendus dans le périmètre (mauvaise location)
  - Exemplaires pointés inconnus du système (à enregistrer)
- **Liste par notice (FEAT-045)** : les exemplaires attendus sont regroupés par notice, **triés par auteur puis titre** ; chaque notice affiche son auteur, son titre et **tous ses codes Ofelia** sous forme de pastilles — **vert** = exemplaire trouvé, **rouge** (barré) = manquant. La colonne « Statut » et l'action « Marquer perdu » ont été **retirées** (l'endpoint `inventory:resolve_missing` n'existe plus).
- Les sections **Hors périmètre** (mauvaise location) et **Codes inconnus du système** restent affichées sous la liste par notice.

#### Historique
- Conservation des sessions clôturées
- Comparaison entre récolements pour suivi de la qualité du fonds

#### Réassignation automatique au récolement (FEAT-033)

Insight : pendant un récolement scopé sur une `Location` X, si un exemplaire est scanné, il est *physiquement* à cet endroit (le bibliothécaire le tient en main, à cet endroit). Donc si le catalogue dit qu'il est ailleurs, c'est le catalogue qui se trompe — le scan terrain est la source de vérité.

- **Déclenchement** : à chaque pointage (`record_scan` côté UI web ET `InventorySessionItemsView` côté API OfeliaScan), si `session.scope_type == LOCATION` et `session.scope_location` est défini, on force `item.location = session.scope_location` (sauf si déjà identique). Comportement **systématique**, pas de toggle utilisateur, pas de flag OfeliaScan.
- **Champ compteur** : `InventorySession.relocate_count` (PositiveIntegerField, migration `inventory/0003_inventorysession_relocate_count.py`) incrémenté en `F('relocate_count') + 1` pour rester atomic.
- **Effets de bord** :
  - Les *mal-rangés* (`misplaced` dans le rapport) disparaissent en pratique : un livre scanné en A1 alors qu'il était catalogué en B2 devient *présent* en A1 (et apparaîtra comme manquant dans une éventuelle session future sur B2).
  - Les exemplaires sans emplacement (`location=None`) reçoivent automatiquement une location au passage (effet « baptême »).
- **Pas de relocate** pour `scope_type=all` ou `scope_type=category` (pas de location-cible évidente), ni pour un EAN scanné qui ne matche aucun Item (`item=None`).
- **Idempotence** : si le scan est rejoué (même EAN, même session), `get_or_create` retourne `created=False` mais `maybe_relocate` est appelé quand même — si l'item est déjà à la bonne location → no-op (counter inchangé).
- **Rapport** : bandeau d'information en tête de `templates/inventory/session_report.html` quand `session.relocate_count > 0` : « N exemplaires ont été déplacés automatiquement vers <code> pendant cette session ». Pas de modification du calcul de `build_report` (qui reflète déjà l'état du catalogue après relocate).
- **Risque accepté** : si un bibliothécaire scanne par erreur des livres apportés d'un autre rayon, ils seront catalogués dans le scope de la session. Acceptable car c'est exactement le comportement souhaité dans 95 % des cas (rangement physique = source de vérité).
- **API inchangée** côté contrat : OfeliaScan continue à envoyer `{"items": [{"scanned_value": "...", "scanned_at": "..."}]}` au POST batch. La relocate est un effet de bord serveur, transparent pour le mobile.

#### Écarts d'implémentation Sprint 2 (FEAT-005 à FEAT-010)

État réel du code livré au Sprint 2 (les écrans §6.1 à §6.5 sont opérationnels) :

- **§6.1 Catalogage** — Notices et exemplaires : CRUD complet, recherche FTS5
  filtrée, lookup ISBN OpenLibrary (synchrone). La mise en file d'attente du
  lookup quand la box est hors-ligne est différée (dépend de la détection de
  connectivité §7.3). L'import batch OfeliaScan dépend de l'API REST (Task #16).
  La suppression logique d'exemplaire = statut `discarded` (pas de champ booléen
  séparé) ; une notice se supprime réellement, à condition de n'avoir aucun
  exemplaire actif.
- **§6.2 Usagers** — Inscription, fiche, historique, remplacement de carte,
  renouvellement, expiration : opérationnels. Les cartes de remplacement
  utilisent une plage de séquence haute pour éviter les collisions. L'aperçu /
  impression de la carte PDF relève de l'impression (Task #12). Le compte
  collectif accepte tout usager comme parent (pas de filtre de catégorie).
- **§6.3 Prêts/Retours** — Workflow de prêt en 3 étapes (panier en session),
  retour, renouvellement, livre perdu, consultation sur place : opérationnels.
  Le retour est traité au scan (pas de validation finale différée). Le reçu
  papier relève de l'impression (Task #12). La vérification « exemplaire
  disponible » s'appuie sur la table `Loan` (vérité), pas sur le cache
  `Item.status`, pour interdire tout double prêt (BUG-003).
- **§6.4 Réservations** — Création, satisfaction FIFO au retour, liste à
  honorer, annulation, expiration : opérationnels.
- **§6.5 Récolement** — Sessions, périmètre, pointage (web manuel), rapport de
  divergences, clôture/réouverture/validation : opérationnels. La réception des
  scans depuis OfeliaScan dépend de l'API REST (Task #16). L'action de divergence
  fournie en v1 est « marquer perdu ». Le périmètre « attendu » se limite aux
  exemplaires censés être physiquement présents (statut `available` ou
  `reserved_for_pickup`) : un exemplaire prêté n'est pas « manquant » (BUG-004).
- **Tâches quotidiennes** — `expire_members` et `expire_reservations` sont des
  commandes de gestion ; leur planification django-q2 (`Schedule`) sera créée au
  paramétrage de premier démarrage (Task #15).

### 6.6 Administration et rapports

> Implémentation Sprint 4 (FEAT-011) :
> - **Dashboard** (`core:dashboard`) : KPI + tendance prêts 30j (sparkline) + Top 10 mois/année + activité (usagers actifs, croissance fonds) + état système (version, disque libre, dernière sauvegarde alerte > 24 h, ZeroTier).
> - **Rapports** (`apps/reports/`) : index `reports:index` ; listes imprimables `reports:overdue`, `reports:reservations_pickup`, `reports:inactive` (CSS `@media print`) ; export CSV `reports:loans_csv` (période paramétrable) ; PDF annuel `reports:annual_pdf` (ReportLab).
> - **Paramètres** (`/admin/settings/`, superadmin uniquement) : identité (nom, box_name mDNS, adresse, contact), langues (activées + défaut), durées prêts & réservations, sauvegardes (cf. §8 / FEAT-014), + lien Diagnostic. Catégories/Tags/Locations/MemberCategory restent éditées via `/admin/` Django pour l'instant (lien depuis l'index).
>   - **FEAT-047 (Sprint 18)** : sections retirées des Paramètres — *Impressions cartes/étiquettes* (`printing_cards`/`printing_labels` : impression sous Avancé→Impression, format = valeurs seed désormais), *ZeroTier* (géré au niveau de la box keebee), *Sources de métadonnées* (`sources` : choix des sources sous Avancé→Enrichissement), et lien *Comptes utilisateurs* (doublon de Avancé→Administration). Les forms restent dans `apps/core/forms.py` (MetadataSourcesForm toujours utilisée par l'enrichissement) mais ne sont plus dans le dict `FORMS`.
> - **Gestion comptes** (`/accounts/users/`) : CRUD + reset mot de passe (avec génération aléatoire 16 chars).
> - **Diagnostic** (`core:diagnostics`) : versions, dernière sauvegarde, file django-q2.
>
> Implémentation Sprint 4 (FEAT-017) — **navigation** :
> - Onglet **« Avancé »** (`core:advanced`) dans la barre de nav : page index regroupant Impression, Rapports, Inventaire, Méta-données et Administration, chaque lien explicité d'une phrase. C'est le point d'accès unique aux écrans hors-workflow.
> - **FEAT-076 (Sprint 29)** : chapitre **« Méta-données »** (bleu `--sky`, icône `database`) extrait du chapitre Inventaire — emplacements, langues, catégories, provenances, enrichissement des métadonnées. Ce sont des listes de référence, réglées une fois puis consommées par les menus déroulants du catalogue ; l'Inventaire ne garde que les sessions de travail (récolement, catalogage par scan / douchette / Excel).
> - Barre principale allégée : plus de « Tableau de bord » (le logo `house` y mène) ni de « Récolement » (→ Avancé / Inventaire).
> - Menu utilisateur (haut-droite) : « Mon compte » (auto-édition de son propre compte via `accounts:user_edit` ; formulaire restreint sans `role`/`is_active` pour les non-superadmins) + « Déconnexion ». L'entrée « Mode avancé/simple » (§10.3) n'est plus surfacée mais le mécanisme reste actif côté modèle.



#### Tableau de bord
- Prêts actifs (compteur + tendance 30 jours)
- Retards (compteur + détail)
- Top 10 livres les plus empruntés (mois, année)
- Membres actifs (mois, année)
- Croissance du fonds (mois, année)
- État système (espace disque, dernière sauvegarde, dernière sync, version)
- **Relances à faire (FEAT-035)** : en bas du dashboard, liste des 10 prêts en retard les plus anciens avec titre, membre (lien fiche), date d'échéance et nombre de jours de retard. Lien « Voir tout » vers `/loans/return/` qui liste tous les retards. Visible des `librarian` / `superadmin` uniquement.

#### Rapports
- Rapport annuel d'activité (PDF) : prêts, membres, fonds, top, retards, perdus
- Liste imprimable des retards
- Liste imprimable des inactifs (membres et livres)
- Export CSV/Excel des prêts par période
- Rapport pour bailleur (template paramétrable)

##### Exports CSV (FEAT-040, Sprint 13)

- **Catalogue complet** (`reports:catalog_csv`) : 1 ligne par exemplaire avec
  l'ensemble des champs de la notice (sauf image) + champs de l'exemplaire.
  Colonnes : `item_internal_id, item_ean13, item_state, item_status,
  item_location_code, item_acquisition_date, item_acquisition_source,
  item_donor, record_id, record_title, record_subtitle, record_authors,
  record_publisher, record_publication_year, record_language, record_isbn_13,
  record_isbn_10, record_category, record_tags, record_document_type,
  record_series_name, record_series_volume, record_summary`. Itère en
  streaming (`iterator(chunk_size=500)`).
- **Prêts et réservations en cours** (`reports:active_loans_reservations_csv`) :
  2 sections concaténées dans un même CSV, discriminées par la colonne `kind`
  (`loan` pour les prêts ACTIVE/OVERDUE, `reservation` pour les réservations
  PENDING/READY_FOR_PICKUP). Colonnes communes : `kind, id, status,
  created_at, member_card, member_name, record_title, item_internal_id,
  due_or_expiry_date` (vide quand non applicable).
- **Inactifs** (`reports:inactive_members_csv` + `reports:inactive_items_csv`) :
  filtres `?days=` identiques à la page HTML ; colonne `last_activity` rendue
  soit en `YYYY-MM-DD`, soit en chaîne traduite `Aucune activité`. Boutons
  visibles à côté du bouton « Imprimer » sur `/reports/inactive/`.

Toutes les vues d'export utilisent le rôle `LIBRARIAN` + `SUPERADMIN`
(cohérent avec `loans_csv`) ; `READONLY` peut continuer de lire la page HTML
mais pas exporter.

#### Paramètres
- Identité de la bibliothèque (nom, adresse, logo)
- Langues activées et langue par défaut
- Règles de prêt (par catégorie d'usager et type de document)
- Catégories de document
- Catégories d'usager
- Emplacements
- Tags
- Format d'étiquette et de carte
- **Fuseau horaire (FEAT-077)** — liste des fuseaux IANA, première entrée
  « Fuseau du système » qui laisse la main à la machine. Deux niveaux : la
  variable d'environnement **`TZ`** de l'instance donne le défaut (défaut `UTC` ;
  c'est ainsi que la Box prend le fuseau du Raspberry Pi), le réglage des
  Paramètres le surcharge sans redéploiement. `Setting.timezone` +
  `apps.core.middleware.TimezoneMiddleware`, qui active le fuseau à chaque
  requête. Un fuseau invalide est ignoré avec un log — jamais fatal. Le réglage
  vaut pour **toutes** les dates de l'application, pas seulement l'heure de
  l'accueil.
- Backup (chemin clé USB, fréquence, cloud)
- ZeroTier (statut, ID réseau)

#### Gestion des comptes
- Création d'utilisateurs bibliothécaires et admin
- Réinitialisation de mot de passe par admin
- Procédure physique de récupération si tous les admins sont bloqués : fichier sur clé USB de récupération avec hash de reset à présenter au boot

### 6.7 Impression d'étiquettes

> Implémentation Sprint 4 (FEAT-012), refonte Sprint 12 (FEAT-038 + FEAT-039) :
> - `apps/printing/services.py` : `render_item_labels_pdf(items)` (80×40 mm par défaut, planche A4 3×7 = 21 étiquettes ; dimensions paramétrables via `Setting.item_label_format`) ; `render_member_cards_pdf(members)` (8/A4 par défaut, paramétrable via `Setting.card_format`).
> - Codes-barres : `python-barcode` → PNG en mémoire → ReportLab.
> - **FEAT-074 (Sprint 29) : plus aucun envoi direct à une imprimante.** Le chemin CUPS (`submit_to_cups()`, route `printing:labels_send`, bouton « Imprimer (CUPS) », réglages `CUPS_HOST`/`CUPS_PORT`, paquets `pycups`/`libcups2`) est **supprimé** : il renvoyait un 403 CSRF depuis l'écran, et il supposait une imprimante visible depuis le serveur — or l'étiqueteuse est sur le poste du bibliothécaire et le serveur est hébergé hors de la bibliothèque. **L'unique chemin d'impression est le PDF servi au navigateur.**
> - Routes : `printing:labels`, `printing:labels_pdf`, `printing:cards`, `printing:cards_pdf` (rôle LIBRARIAN/SUPERADMIN).
> - FEAT-062 (Sprint 27) : ruban continu Brother QL-810W — `render_item_labels_roll_pdf(items)` et `render_member_cards_roll_pdf(members)` (une sortie par page, `Setting.roll_printer_format`), routes `printing:labels_roll_pdf` et `printing:cards_roll_pdf`, section de réglages `printing_roll`. Les planches A4 ci-dessus sont inchangées, les deux formats coexistent.
> - Paramétrage : sections **Impressions — Cartes membres** (`printing_cards` → `card_format`) et **Impressions — Étiquettes codes Ofelia** (`printing_labels` → `item_label_format`) dans `/admin/settings/`. Migration douce depuis l'ancien `label_format` via `_card_settings()` / `_item_label_settings()`. **BUG-021** : FEAT-047 avait retiré ces deux sections du registre `FORMS` (`admin_views.py`) en les croyant redondantes — or c'était le **seul** accès UI au format d'impression → restaurées (les `Setting`, formulaires et valeurs seed n'avaient jamais bougé).

#### Étiquettes exemplaires (FEAT-039)
- Écran intitulé « **Étiquettes codes Ofelia** » (FEAT-018)
- Format par défaut : 80×40 mm (planche A4 3×7 = 21 étiquettes), paramétrable
- Layout cellule :
  - Logo Ofelia (`static/img/ofelia-logo.png`) en haut-gauche
  - Titre wrap 2 lignes max (50 caractères cumulés par défaut), wrap par mots, dernière ligne tronquée avec `…` si débordement
  - Auteurs (1 ligne max, 50 caractères) sous le titre
  - Code-barres EAN13 centré, ~40 % de la hauteur cellule
  - Bas : `internal_id` à gauche, code Ofelia (EAN13) au centre, code Location à droite, nom bibliothèque en bas-droite (italique 5.5 pt)
- Setting `item_label_format` (JSON) : `{width_mm, height_mm, title_max_chars, title_lines, show_logo}`
- Génération de tous les exemplaires sélectionnés dans un seul PDF, imprimé depuis le poste client (FEAT-074)

#### Cartes membres (FEAT-038)
- Format par défaut : 8 cartes par feuille A4 (paramétrable 4/6/8/10)
- Fond crème `rgb(248, 238, 229)` sur toute la cellule
- Layout :
  - Logo OFELIA (`static/img/ofelia-grandes-lettres.png`) centré en filigrane (alpha ~0.18 si ReportLab le supporte)
  - Photo du membre (`member.photo`) en haut-gauche, vignette 22 mm si présente
  - Bloc texte côté droit (haut → bas) : nom de la bibliothèque (Helvetica-Bold 12), « Carte de membre », nom prénom (13 pt bold), catégorie, « Valide jusqu'au JJ/MM/AAAA »
  - Code-barres EAN13 bas-droite avec n° de carte sous le code
  - Langue préférée en bas-gauche (Helvetica-Bold 9, code ISO 2 lettres)
- Setting `card_format` (JSON) : `{per_a4, show_logo, show_photo}`
- Impression sur papier ordinaire en v1, à plastifier

#### Deux écrans d'étiquettes (FEAT-075)

Depuis le Sprint 29, les deux sortes d'étiquettes ont chacune leur écran et leur
entrée dans le menu Avancé → Impression :

| Écran | Route | Boutons |
|---|---|---|
| **Étiquettes codes Ofelia** | `printing:labels` | « PDF A4 », « Ruban 62 mm (Brother QL) » |
| **Étiquettes de tranche** | `printing:spine_labels` | « PDF A4 », « Ruban 62 mm (Brother QL) » |

La sélection d'exemplaires est **la même des deux côtés** : filtres emplacement
et derniers ajouts, table, case « tout cocher », prise en charge de
`?catalog_session=N` (FEAT-046). Elle vit dans `views._picker_context()` et dans
le gabarit `printing/_picker_base.html` ; chaque écran n'override que ses
boutons et ses colonnes de fin de ligne.

Le libellé « Générer PDF » devient « **PDF A4** » sur les écrans d'impression
(étiquettes et cartes membres) : à côté d'un bouton « Ruban 62 mm », c'est le
format qui distingue les sorties.

#### Ruban continu Brother QL-810W (FEAT-062)

Support d'une étiqueteuse à ruban continu, en plus des planches A4 qui restent
inchangées. Le matériel de référence est une **Brother QL-810Wc** chargée d'un
ruban **62 mm noir/rouge** (DK-22251).

**Chemin d'impression** — l'imprimante est branchée en **USB sur le poste du
bibliothécaire** : ni la Box ni les instances Avignon ne peuvent lui parler
(constat 2026-08-18 : scan du LAN en 9100 depuis la Box → seul le laser
DCP-L3550CDW répond, la QL n'est pas en réseau). Le serveur produit donc un PDF
à la géométrie exacte du ruban et c'est le **navigateur du poste** qui l'envoie
au pilote Brother. **FEAT-074** : c'est désormais le seul chemin possible, l'envoi
serveur → imprimante ayant été retiré. Le format et l'orientation se règlent une
fois pour toutes dans les **options d'impression du pilote Brother** côté poste
(et non dans la fenêtre de propriétés ouverte depuis le dialogue de Chrome, qui
ne vaut que pour le job en cours).

**Géométrie** — une étiquette (ou une carte) par page, marges nulles, avec deux
retraits de sécurité sans lesquels le pilote rogne le dessin :

- `ROLL_INSET_MM = 2` à gauche et à droite (zone imprimable réelle ≈ 58,9 mm
  sur un ruban de 62 mm)
- `ROLL_FEED_INSET_MM = 3` en tête et en pied de bande (avance papier des QL
  sur ruban continu)

| Sortie | Page PDF | Contenu |
|---|---|---|
| Étiquette code Ofelia | 62 × 35 mm, 1 par page | logo gris + nom de la bibliothèque, titre (2 lignes pleine largeur), auteurs en italique, code-barres EAN13, code Ofelia + code Location |
| Carte membre | 62 × 89 mm | carte 85,6 × 54 mm (format carte bancaire) **dessinée à 90°** en travers du ruban |

Le gabarit se cale sur la zone utile, pas sur les bords de page : si la longueur
est réduite dans les réglages, le code-barres et le pied restent placés. Une
carte qui ne rentre pas dans le ruban configuré est réduite homothétiquement
plutôt que débordée.

**Étiquettes : monochromes et typographiquement uniformes** (révision après le
1er test de Val, 2026-08-18) — tous les textes partagent la même police et la
même taille (`Helvetica-Bold` 7,5 pt) ; seuls les **auteurs** s'en distinguent
par l'**italique** (`Helvetica-BoldOblique`). Le logo Ofelia est converti en
**niveaux de gris** (`_static_logo_grayscale`, alpha conservé). L'**identifiant
interne a été retiré**. Le titre est coupé sur la **largeur mesurée** du texte
(`_wrap_to_width` + `pdfmetrics`) et non sur un quota de caractères : il occupe
donc toute la largeur utile. Le bloc titre + auteurs est centré verticalement
entre le bandeau et le code-barres.

**Bichromie — cartes membres seulement** : le pilote Windows n'imprime en rouge
que le **rouge pur** (255, 0, 0) du document. Seule la mention « Carte de
membre » l'utilise. Le **code-barres n'est jamais rouge** — une barre rouge
n'est plus lue par une douchette. Réglage `two_color` décoché → tout en noir.

**Déclenchement** — bouton « Ruban 62 mm (Brother QL) » sur `printing:labels` et
`printing:cards` (masqué si `roll_printer_format.enabled` est faux), qui ouvre
le PDF directement dans un nouvel onglet. Une page intermédiaire à
auto-impression a existé puis été retirée à la demande de Val : le visualiseur
PDF et le dialogue d'impression restent de toute façon obligatoires (aucune
page web ne peut lancer une impression sans validation de l'utilisateur).

**Une étiquette = une page = une coupe.** La QL de Val est réglée pour couper
tous les 35 mm : elle ne peut pas honorer une page plus longue. Un essai de
groupage (2 étiquettes sur une page de 62 × 72 mm, pour que Chrome ouvre le
dialogue en portrait — il déduit l'orientation des dimensions de la page) a été
**abandonné au test** : l'imprimante tentait de faire tenir les 2 étiquettes
dans une seule coupe. Le geste « portrait » dans le dialogue reste donc à la
charge du bibliothécaire quand le navigateur ne l'a pas mémorisé ; il est
documenté dans le guide. Les cartes (62 × 89 mm) sont déjà portrait.

**Longueurs alignées sur le pilote** — la longueur de coupe et l'orientation
sont des propriétés du pilote Windows, pas du PDF : le serveur ne peut que
proposer une géométrie. L'étiquette (35 mm) suit la coupe réglée par le
bibliothécaire ; la carte (89 mm) se cale **juste sous le format continu natif
du pilote Brother** (62 × 89,9 mm, relevé sur le poste) pour n'avoir aucune
hauteur à saisir. Pour supprimer aussi la saisie côté étiquettes, la voie est
Windows : **deux objets imprimante** sur le même pilote et le même port, l'un
réglé en 35 mm, l'autre en 89 mm — Chrome mémorise ses réglages par
destination.

**Setting `roll_printer_format`** (JSON) :
`{enabled, tape_width_mm, label_length_mm, card_length_mm, two_color, show_logo}`,
défauts `{true, 62, 35, 89, true, true}`, section **Impressions — Ruban continu
(Brother QL)** (`printing_roll`) dans `/admin/settings/`.

**Réglage du poste Windows** (une fois) : format de papier **62 mm** dans les
options du pilote Brother, **échelle 100 %** et marges **aucune** dans le
dialogue du navigateur.

**Routes** : `printing:labels_roll_pdf`, `printing:cards_roll_pdf`,
`printing:spine_labels_roll_pdf` (rôle LIBRARIAN/SUPERADMIN). La page
intermédiaire `printing:roll_print` a été retirée en fin de Sprint 27 : les
boutons ouvrent le PDF directement (`formtarget="_blank"`).

#### Colonne « Famille » sur la carte de membre (FEAT-072)

Les prénoms des personnes rattachées à la carte (§6.2) s'impriment dans une
colonne à droite, un par ligne, sur la planche A4 comme sur le ruban. La liste
est tronquée par « … » quand la place manque — mieux vaut une ellipse qu'un
prénom écrit par-dessus le code-barres. `family_column_lines()` porte cette
logique, extraite du dessin parce qu'un flux PDF ReportLab ne se relit pas de
façon fiable en test.

#### Étiquettes de tranche (FEAT-068)

Écran **Avancé → Impression → Étiquettes de tranche** (`printing:spine_labels`,
FEAT-075 ; c'était un troisième bouton de l'écran des codes Ofelia jusqu'au
Sprint 29). Même ruban et même géométrie que les étiquettes de livres — **62 × 35
mm, une étiquette par page** — mais un seul contenu : l'**abréviation de la
catégorie** de la notice (FEAT-067), centrée horizontalement et verticalement,
découpée en lignes sur les espaces. Pour « Romans fiction pour adolescents »
(cote `RO FI ADO`) :

```
|--------------------------|
|          RO FI           |
|           ADO            |
|--------------------------|
```

- `spine_layout(text, inner_w, inner_h)` cherche la plus grande taille de police
  (96 pt → 10 pt, pas de 0,5) qui tienne en largeur **et** en hauteur utiles.
  Une cote courte comme `PER` remplit donc l'étiquette — c'est tout l'intérêt
  d'une cote de rayon, se lire à un mètre sans sortir le livre. Un mot unique
  trop large est rétréci, jamais coupé.
- Monochrome, comme les étiquettes de livres.
- Un exemplaire dont la notice n'a pas de catégorie, ou dont la catégorie n'a
  pas d'abréviation, n'a rien à imprimer : il est ignoré. Si **aucun**
  exemplaire sélectionné n'a de cote, l'écran le dit au lieu de sortir un PDF
  vide.
- Le bouton ruban suit le réglage `roll_printer_format.enabled`, comme les
  autres sorties ruban. **FEAT-075** : quand il est désactivé, la **planche A4**
  reste disponible et un encadré dit où réactiver le ruban.
- **FEAT-075 — planche A4 de cotes** : `render_spine_labels_pdf(items)`, même
  grille que les étiquettes « code Ofelia » (`item_label_format`, 80 × 40 mm par
  défaut soit 3 × 7 = 21 par page), cadre de découpe gris clair, cote centrée et
  condensée par cellule. Route `printing:spine_labels_pdf`. Une seule géométrie
  de planche à régler pour les deux sortes d'étiquettes. La cote y est dessinée
  à **70 % de la taille qui remplirait la cellule** (`SPINE_A4_SIZE_SCALE`),
  hauteur et largeur, sans recalculer le découpage en lignes : une cellule A4
  est plus grande qu'une étiquette de ruban et la cote y sortait démesurée. Le
  ruban, lui, garde sa taille pleine.
- **FEAT-075 — cote condensée** : le texte est tracé à **60 % de sa largeur
  naturelle, à hauteur inchangée** (`SPINE_WIDTH_SCALE = 0.60`), pour tenir sur
  la tranche d'un livre mince. La **taille de police ne change pas** :
  `spine_layout()` reçoit la largeur utile **réelle** — jamais une largeur
  gonflée par la condensation, ce qui reviendrait à écrire plus gros au lieu de
  plus étroit — et `_draw_spine_text()` encadre le tracé d'un `scale(0.60, 1)`.
  Sur une étiquette 62 × 35 mm, `RO FI ADO` passe de 41,9 mm à **25,1 mm** de
  large, hauteur de capitale inchangée à 11,3 mm. ReportLab n'embarquant aucune
  police *condensed* (ni les 14 Type1 standard, ni `fonts-dejavu-core`), la
  transformation du canvas est la seule solution exacte sans ajouter une police
  à l'image Docker — contrainte hors-ligne.
- **FEAT-075 — écran dédié** : la table affiche **Catégorie** et **Cote
  imprimée** à la place du code Ofelia, du code externe et de la provenance, de
  sorte que l'absence d'abréviation (`aucune`) se voie avant l'impression.

### 6.8 Notifications offline

> Implémentation Sprint 4 (FEAT-013) :
> - `apps/members/notifications.py:member_alerts(member)` retourne une liste `MemberAlert(level, message)` (niveaux `info`/`warning`/`error`) selon retards, réservations à retirer, carte expirée ou expirante ≤ 30 j.
> - Bandeau affiché à l'identification : `templates/loans/lend.html` (workflow prêt) + `templates/members/member_detail.html` (fiche usager). Classes CSS `msg-info/msg-warning/msg-error`.
> - `apps/members/notifications.py:navbar_counts()` alimente la barre de nav (retards + réservations prêtes).
> - Liste imprimable des réservations à retirer : `reports:reservations_pickup`.



Le système n'envoie ni email ni SMS. Les notifications sont des éléments d'interface :

- Bandeau "Messages pour cet usager" affiché à l'identification de la carte (retards, réservations prêtes, carte expirante)
- Liste imprimable des retards (par défaut, exemplaires en retard > 7 jours)
- Liste imprimable des réservations prêtes pour relance manuelle
- Compteur permanent dans la barre de navigation des items urgents

### 6.9 Multilingue (i18n)


**Libellés de formulaire (BUG-028)** — un `ModelForm` sans `labels` ni
`verbose_name` laisse Django **fabriquer** le libellé depuis le nom du champ
Python (`publication_year` → « Publication year »). Cette chaîne n'existe pas
dans le code : `makemessages` ne la voit pas, `i18n_check.py` non plus, et la
page sort en anglais sans que rien ne proteste. Tout champ affiché porte donc un
`verbose_name=_()` sur le modèle.

`apps/core/tests/test_form_labels.py` verrouille la règle : il parcourt tous les
`ModelForm` du projet et échoue si un libellé n'est pas un objet de traduction
*lazy*. C'est le pendant du gate `.po` — celui-ci vérifie que les chaînes sont
**traduites**, celui-là qu'elles sont bien **extraites**.
#### Langues v1
- Français (default)
- Anglais
- Espagnol
- Malgache

Implémentation :
- Django i18n standard pour l'interface (`.po` files dans `locale/<lang>/LC_MESSAGES/`, compilés en `.mo` au boot du container via `dev-entrypoint.sh` ; les `.mo` sont gitignorés).
- **Les 4 langues sont livrées traduites** (Sprint 2 BUG-005 + Sprint 4 BUG-006) : `fr`, `en`, `es`, `mg` — **503 chaînes** par locale (chiffre courant). Le malgache est une première passe, à faire relire par un locuteur natif.
- `django-modeltranslation` pour les champs traduits du domaine : `Category.name`, `Tag.name`, `MemberCategory.name` (colonnes `name_<lang>` ajoutées via migrations `*_translation_fields.py` + backfill `name → name_fr` via migration `*_backfill_translation_fr.py`).
- Fallback configuré : `MODELTRANSLATION_FALLBACK_LANGUAGES = ('fr',)` → si un champ traduit est vide pour la langue active, la valeur française est utilisée.
- Code de langue `mg` (Malagasy) absent de `django.conf.locale.LANG_INFO` ; enregistré explicitement dans `config/settings/base.py` (sinon `KeyError` dans `modeltranslation.admin.TranslationAdmin`).
- **Routage** : `i18n_patterns(prefix_default_language=True)` dans `config/urls.py` — toutes les URLs de l'interface portent un préfixe de langue (`/fr/…`, `/en/…`, `/es/…`, `/mg/…`), **y compris `accounts/`** (login/logout + gestion comptes, depuis BUG-006). Indispensable pour que le sélecteur de langue et le cookie de préférence soient respectés sur toutes les pages (cf. BUG-005). La racine `/` redirige vers `/<langue>/`. Seuls `setup/`, `admin/`, `api/v1/`, `i18n/` restent hors `i18n_patterns` (paths techniques sans i18n).
- Sélecteur de langue dans l'en-tête : `set_language` natif de Django, persistance par cookie `django_language`. Le champ caché `next` du formulaire utilise `{{ request.path_info }}` (chemin **sans** le préfixe `FORCE_SCRIPT_NAME=/bibliofelia` ajouté par nginx en prod) — sinon `translate_url` ne sait pas resolve le chemin et le préfixe de langue reste inchangé.
- Traductions maintenues via `scripts/apply_translations.py` (dict Python → batch d'application aux 4 `.po`, suppression des `#, fuzzy`). Approche utile pour les vagues de chaînes nouvelles : on évite l'édition manuelle des `.po` et le mauvais recyclage par `msgmerge` (fuzzy avec traductions d'autres msgid).
- Membre peut avoir une `preferred_language` distincte, utilisée pour reçus et cartes (Sprint 3).
- Aucune dépendance à un service de traduction externe : tout est figé dans les fichiers .po.

#### Extensibilité
- Ajout d'une langue = ajout d'un dossier `locale/<code>/` avec les `.po`
- Documentation pour traducteurs bénévoles
- Pas de hard-code de la liste des langues : pilotée par le paramètre `enabled_languages`

### 6.10 Webservice OfeliaScan (API REST)

Contrat d'API entre la box BibliOfelia et l'application Android OfeliaScan.
Les schémas JSON ci-dessous sont **figés** par `docs/specs/SPEC-CORR-001-contrat-api-box.md` (2026-05-22). OfeliaScan les implémente déjà : BibliOfelia doit s'y conformer à la lettre.

#### Conventions générales

- **Base URL** : `http://<box-ip>/bibliofelia/api/v1/` — le slash final est significatif (le client concatène des chemins relatifs). OfeliaScan ne code aucun chemin en dur : il découvre la base URL via mDNS / `/pairing/info` (SPEC-CORR-002).
- **Encodage** : JSON UTF-8, `Content-Type: application/json`.
- **Nommage des champs JSON** : `snake_case`.
- **Dates** : chaînes ISO 8601 UTC (`2026-05-22T14:30:00Z`).
- **Authentification** : JWT Bearer (`Authorization: Bearer <access_token>`) sur tous les endpoints, **sauf** `GET /pairing/info` et la publication mDNS, accessibles sans token pour permettre la découverte avant appairage.
- **Champs additionnels** : la box peut renvoyer des champs non listés ; le client les ignore. Les champs marqués **requis** doivent toujours être présents.
- **Format d'erreur** (uniforme) : `{"error": {"code": "<code>", "message": "...", "details": {}}}`. Codes HTTP : `401` (identifiants), `403` (accès refusé), `404` (introuvable), `5xx` (erreur box).

#### Authentification

- `POST /auth/login` — auth non requise. Requête `{"username", "password"}`. Réponse `200` :
  `{"access_token", "refresh_token", "token_type": "Bearer", "expires_in": <int s>}` (les 4 champs requis). `401` si identifiants invalides.
- `POST /auth/refresh` — auth non requise. Requête `{"refresh_token"}`. Réponse `200` : mêmes 4 champs que `/auth/login` (un **nouveau** `refresh_token` est émis → rotation des refresh tokens activée).
- `POST /auth/logout` — auth requise, corps vide. Réponse `204`. Met le(s) refresh token(s) de l'utilisateur sur liste noire.

> SimpleJWT renvoie `{access, refresh}` par défaut : BibliOfelia fournit un serializer/vue **personnalisé** émettant les noms OAuth 2.0 (`access_token`, `refresh_token`, `token_type`, `expires_in`). Activer `ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION` et l'app `rest_framework_simplejwt.token_blacklist`.

#### Pairing

- `GET /pairing/info` — **auth non requise** (découverte). Réponse `200` :
  `{"box_name", "library_name", "version", "base_url"}` (les 4 requis). `base_url` est l'**URL absolue complète** de la base de l'API, slash final inclus (`http://<box>/…/api/v1/`) ; OfeliaScan l'utilise telle quelle. La box la reconstruit depuis la requête entrante (ou réglage `API_BASE_URL`). Amendé par `SPEC-CORR-002`.
- `POST /pairing/claim` — appairage par QR code. Hors périmètre du contrat SPEC-CORR-001 (différé).

#### Métadonnées

- `GET /isbn/{isbn}` — auth requise. Réponse `200` :
  `{"isbn", "title", "authors": [...], "publisher", "publication_year", "language", "cover_url", "source", "cached"}`.
  Seul `isbn` est requis (ré-émis tel quel) ; les autres peuvent être `null`/`[]`. **Le champ est `publication_year`, pas `year`.** `404` si ISBN introuvable.
- Comportement : cache local de la box, fallback OpenLibrary si internet.

#### Diagnostic

- `GET /health` — auth requise. Réponse `200` : `{"status": "ok"|"degraded", "version"?, "disk_free_mb"?, "last_backup_at"?}`. Seul `status` est requis.
- `GET /sync/status` — queue des tâches en attente.

#### Catalogue des emplacements (lecture seule) — FEAT-032

- `GET /locations` — auth requise (Bearer JWT, throttle scope `scan`). Réponse `200` :
  `{"locations": [{"code": "A1", "description": "Salle adulte", "parent_code": null}, ...]}`. Ordre par `code` croissant. Pas de pagination (fonds < 100 emplacements attendus). `parent_code` est `null` ou le code d'un autre emplacement (même liste, arbo à plat — au client de regrouper si besoin).
- **Lecture seule** : OfeliaScan ne peut pas créer/modifier/supprimer d'emplacement. La création se fait depuis l'UI librarian (`/catalog/locations/`, cf. §6.1).
- **Usage** : OfeliaScan appelle cet endpoint au démarrage / à l'ouverture du picker, met en cache, et propose un picker à l'utilisateur au catalogage (champ `location_code` des `ScanItem`) et au récolement (champ `scope_location_code` à la création de session).
- **Tolérance** : si OfeliaScan envoie un `location_code` inconnu au catalogage, l'exemplaire est créé sans emplacement, silencieusement (pas de 400, pas de log). Comportement délibéré pour ne pas bloquer un scan terrain si le picker a une version cache obsolète. Pour le récolement (`scope_location_code`), au contraire, un code inconnu renvoie **400 `unknown_location`** car une session sans scope valide n'a pas de sens.

#### Sessions de scan (catalogage) — FEAT-021 / Task #20

Contrat **aligné sur le client OfeliaScan déjà déployé** (la SPEC initiale
proposait un schéma simplifié ; le client envoie le schéma documenté ci-dessous
et c'est lui qui fait foi). Permissions : un user `contributor_api` ne voit
et n'agit que sur ses propres sessions (404 sur celles des autres) ;
librarian/superadmin voient tout.

- `POST /scan-sessions` — auth requise. Body `{"label"?: string}`.
  Réponse `201` : `{session_id, state: "open", created_at}`.
- `POST /scan-sessions/{id}/items` — auth requise. Body **enveloppé** :
  `{"items": [{local_id, scan_kind, scanned_value?, metadata_title?,
   metadata_authors?, metadata_language?, metadata_publisher?, metadata_year?,
   location_code?, item_state?, copy_count?, scanned_at, notes?}, ...]}`.
  - `scan_kind ∈ {ean13, isbn, manual}`.
  - `local_id` : idempotency par session (rejouer un POST renvoie
    `duplicates += 1`, jamais d'erreur).
  - Réponse `200` : `{session_id, accepted, duplicates, rejected: [{local_id, reason}]}`.
  - `409 session_closed` si la session est finalisée.
- `POST /scan-sessions/{id}/finalize` — auth requise. Body vide.
  Traitement **synchrone** dans une transaction :
  - lookup `BibliographicRecord` par `isbn_13` puis `isbn_10` (normalisés
    depuis `scanned_value`) ;
  - si trouvé → `+copy_count Item`s ajoutés au record existant ;
  - sinon → nouveau `BibliographicRecord` créé avec les `metadata_*`
    (`metadata_source=scan_app`), puis `+copy_count Item`s ;
  - `location_code` résolu via `Location.code` ; `item_state` validé sinon
    fallback `good` ; marqueur `[ScanSession:UUID]` ajouté aux `notes`.
  - **Placeholder titre** : si OfeliaScan envoie un ISBN sans `metadata_title`, la notice est créée avec `title = "ISBN:<isbn> - <dd.mm.aaaa hh.mn>"` (language-neutral, pas de gettext). Ce placeholder est reconnu et écrasé par l'enrichissement FEAT-031 même en mode FILL_MISSING (préfixes détectés : `"ISBN:"` + legacy `"Sans titre — session "` pour rétrocompat). Constante : `apps/catalog/enrichment.py:_PLACEHOLDER_TITLE_PREFIXES`.
  - **Génération `internal_id`** : `OFL-YYYYMMDD-NNNN` calculée par `Item._assign_codes()` via `MAX(internal_id)+1` (pas `count()+1` qui collisionnait quand la séquence avait des trous — sessions échouées, suppressions d'exemplaires). FEAT-043 : le `MAX` est calculé en union `Item ∪ RetiredItemCode` pour ne jamais réattribuer un code retiré (étiquettes imprimées).
  - Réponse `200` : `{session_id, state: "finalized", finalized_at,
    summary: {items_processed, records_created, records_matched, copies_added, errors}}`.

#### Récolement — FEAT-021 / Task #20

Contrat **aligné sur le client OfeliaScan**. La session est créée
directement par OfeliaScan (`mobile_created=True` côté `InventorySession`),
ce qui la distingue dans l'UI librarian de récolement (FEAT-010).

- `POST /inventory-sessions` — auth requise. Body :
  `{"label"?, "scope_type"?: "all"|"location"|"category",
   "scope_location_code"?, "scope_category_code"?}`.
  Réponse `201` : `{session_id, state: "open", started_at}`.
  `400 unknown_location` / `unknown_category` si le code ne correspond à
  rien.
- `POST /inventory-sessions/{id}/items` — auth requise. Body **enveloppé** :
  `{"items": [{scanned_value, scanned_at, location_code?}, ...]}`.
  - `scanned_value` normalisé (`normalize_code`) puis résolu en `Item` :
    1. `Item.ean13` (code interne Ofelia `290…`) — workflow normal, un
       sticker par exemplaire, aucune ambiguïté.
    2. Fallback `BibliographicRecord.isbn_13` puis `isbn_10` (ISBN commercial
       scanné depuis la couverture, quand les étiquettes ne sont pas encore
       collées). Pour les ISBN multi-exemplaires, on exclut les EAN déjà
       présents dans la session et on avance sur le prochain exemplaire non
       encore pointé : N scans du même ISBN → N exemplaires distincts marqués
       présents. (BUG-008)
  - `InventoryScan.ean13` stocke le code interne de l'exemplaire résolu
    (ou le `scanned_value` brut si inconnu) ; contrainte UNIQUE `(session,
    ean13)` → doublons vrais comptés (`duplicates`).
  - `location_code` (optionnel) : si fourni et résolu via `Location.code`,
    met à jour `Item.location` de l'exemplaire résolu. Ignoré si le code
    emplacement est inconnu (pas de `400` — l'item est quand même accepté).
    Envoyé par OfeliaScan FEAT-025 quand l'utilisateur saisit un code
    emplacement au moment de l'envoi.
  - Réponse `200` : `{session_id, accepted, duplicates, rejected}`.
  - `409 session_closed` si pas `open`.
- `POST /inventory-sessions/{id}/close` — auth requise. Body vide.
  Réponse `200` : `{session_id, state: "closed", closed_at, scans_count}`.
  Le rapport (présents/manquants/mal rangés/inconnus) reste un workflow
  librarian côté web (FEAT-010).

#### Handoff single-scan — FEAT-023 / Task #21

Distinct du flux bulk ci-dessus : protocole **single-scan + retour de
valeur** entre la page web BibliOfelia (cookie de session) et OfeliaScan
(JWT). Permet aux boutons « Scanner » du site (prêt, retour, dashboard) de
déclencher un scan unique dans OfeliaScan et de récupérer immédiatement la
valeur dans le champ correspondant. Voir `docs/specs/FEAT-023-scan-handoff-ofeliascan.md`
pour le contrat Android complet.

- `POST /scan-handoff` — auth requise. Permission : `librarian`/`superadmin`
  (un `contributor_api` reçoit `403 forbidden`). Body :
  `{"target_kind"?: "auto"|"book"|"card"}` (défaut `auto`).
  Réponse `201` : `{token, state: "pending", target_kind, value: "",
  value_kind: "", created_at, expires_at, completed_at: null, deep_link, android_intent_url}`.
  Deux URLs sont renvoyées pour maximiser la compatibilité :
  - `deep_link = ofeliascan://scan-one?token=<UUID>&kind=<target_kind>` — scheme custom, utilisable par Firefox Android, Safari iOS, et tout navigateur qui sait suivre les schemes natifs.
  - `android_intent_url = intent://scan-one?token=<UUID>&kind=<target_kind>#Intent;scheme=ofeliascan;package=<OFELIASCAN_ANDROID_PACKAGE>;end` — forme `intent://` utilisée par Chrome / Samsung Browser / Edge Android (le scheme custom y est souvent bloqué silencieusement par la politique anti-deeplink-spam). Le package est réglé via `OFELIASCAN_ANDROID_PACKAGE` (défaut `org.zitoon.ofeliascan`).

  TTL 5 minutes, single-use.
- `GET /scan-handoff/{token}` — auth requise. Permission : créateur du
  handoff (sinon `404`, pas de fuite d'existence) ; superadmin voit tout.
  Réponse `200` : même schéma sans `deep_link` ; `state` calculé à la volée
  `pending|completed|cancelled|expired` (état `expired` = `pending` après TTL).
- `POST /scan-handoff/{token}` — callback OfeliaScan (JWT). Tout user JWT
  authentifié peut soumettre : le token UUID **est** la capability
  (single-use, TTL court, transmis via deep-link LAN). Body :
  `{"value", "kind": "ean13|isbn|card|item|manual"}` **ou**
  `{"cancelled": true}` si l'utilisateur abandonne. `value` normalisé
  (`normalize_code`). Réponses :
  - `200` : handoff `completed` (ou `cancelled`) — renvoie l'état complet.
  - `409 already_completed` : un POST précédent a déjà terminé le handoff.
  - `410 expired` : `expires_at < now`.
  - `404` : token inconnu.

Côté navigateur : `static/js/scan-handoff.js` détecte `.js-scan-handoff` au
clic, lit les attributs `data-scan-target` / `data-scan-kind` /
`data-scan-autosubmit` / `data-scan-dispatch-url`, POST le handoff, ouvre
l'URL adaptée au navigateur (UA-sniff : Chrome/Samsung/Edge Android →
`android_intent_url`, sinon `deep_link`), poll toutes les 700 ms (timeout
client 120 s), puis injecte la valeur dans l'input cible + soumet le
formulaire englobant — ou redirige vers `core:search?q=<value>` pour le
mode dashboard (la recherche globale `classify_query` dispatch ensuite).
CSRF : le token est rendu par le template `{% csrf_token %}` et injecté dans la config JSON `#scan-handoff-config` (le cookie `csrftoken` est `HttpOnly`, donc illisible par le JS — même contrainte que HTMX, traitée de la même façon dans `base.html`). Le JS pose ensuite l'en-tête `X-CSRFToken` sur le POST de création (BUG-011).

Boutons câblés (v1) : `loans/lend.html` (scan carte membre + scan livre),
`loans/return.html` (scan livre rendu), `core/dashboard.html` (banner
« Scanner une carte ou un livre »). Le récolement n'a jamais été câblé
sur ce handoff ; depuis FEAT-045 il dispose de son propre scan caméra
continu (cf. §6.5).

Fallback hors OfeliaScan : sur iOS ou Android sans l'app, `window.location`
échoue silencieusement, le timeout client de 120 s relâche le bouton, et
le champ texte reste utilisable pour la saisie manuelle (= comportement
pré-FEAT-023, pas de régression). Le scanner caméra navigateur est
adressé séparément par FEAT-024 ci-dessous.

#### Scanner caméra navigateur — FEAT-044 (mode unique, révise FEAT-024)

**Révision Val 2026-05-30** : les 4 boutons « Scanner » du site (dashboard,
prêt-carte, prêt-livre, retour) utilisent **uniquement la caméra du
navigateur**. Le handoff OfeliaScan a été **retiré de ce flux** ; OfeliaScan
reste réservé au catalogage et au récolement en masse (FEAT-021, §6.10 plus
haut). Voir `docs/specs/FEAT-044-scanner-camera-unique.md` (révise
`FEAT-024-scanner-camera-navigateur.md`).

Au clic sur `.js-scan-handoff` :
- caméra disponible (HTTPS + `getUserMedia` + module chargé) → **modal viseur**.
- caméra indisponible → **message d'erreur explicite** sous le bouton avec la
  raison exacte (`HTTPS requis`, `permission refusée`, `aucune caméra`,
  `caméra occupée`, `scanner non chargé`) + invitation à **saisir le code à la
  main**. Plus de redirection silencieuse vers OfeliaScan.

Contrainte HTTPS : `getUserMedia` exige `window.isSecureContext` (HTTPS ou
`localhost`) — règle navigateur incontournable. En **HTTP LAN** la caméra ne
peut pas démarrer (message d'erreur affiché). Val accède à la box via le
**domaine HTTPS externe**, où la caméra fonctionne. Faire marcher la caméra en
LAN nécessiterait un HTTPS local sur la box (cert/mkcert nginx) — chantier
keebee séparé, hors périmètre. **Aucun certificat auto-signé** sur les
téléphones.

**Double moteur de décodage** (selon les capacités du navigateur) : si
`BarcodeDetector` natif est dispo (Chrome/Edge Android, Chrome desktop) →
`html5-qrcode` v2.3.8 (`static/js/html5-qrcode.min.js`) avec
`useBarCodeDetectorIfSupported` (quasi natif) ; sinon (Safari iOS, Firefox
Android) → **QuaggaJS** (`static/js/quagga.min.js`, @ericblade/quagga2 v1.8.4,
MIT, vendoré local), spécialisé 1D/EAN, plus robuste que le repli ZXing-JS.
Chrome Android = navigateur recommandé. URLs des libs injectées par le template
via `{% static %}` dans `#scan-camera-config` (résout préfixe `FORCE_SCRIPT_NAME`
+ hash `ManifestStaticFilesStorage` — sinon 404 en prod). Modal viseur 480 px
desktop / full-screen mobile, caméra arrière, **haute résolution 1920×1080**.

**Fiabilité** : **EAN-13 uniquement** ; une lecture n'est acceptée que si clé de
contrôle EAN-13 valide **et** préfixe `290/291/978/979` (+ `977` en catalogage
seulement, cf. FEAT-052 : `isAcceptableCode(v, allowIssn)`), **et** confirmée par
2 lectures identiques (consensus) — élimine confusions de chiffres et formats
parasites. **iOS** : `getUserMedia` appelé dans le geste (priming) avant le
lazy-load (sinon `NotAllowedError`). **Mobile** : garde anti « ghost-click »
(600 ms) empêchant le tap d'ouverture de refermer le modal.

À la détection, `BibliOfelia.scan.applyResult(btn, {value})` aiguille selon les
attributs : `data-scan-dispatch-url` (dashboard) → `core:search?q=<code>` →
`global_search`/`classify_query` redirige `290…` → **notice**, `291…` →
**fiche membre**, ISBN → notice ; `data-scan-target` (+ `data-scan-autosubmit`)
→ remplit le champ et soumet le formulaire courant. Décodage 100 % local, aucune
image envoyée au serveur, aucun endpoint Django, aucune migration.

`scan-handoff.js` réécrit (retrait OfeliaScan), `scan-camera.js` réécrit (double
moteur). `base.html` : `#scan-handoff-config` supprimé, `#scan-camera-config`
(`libUrl`+`quaggaUrl`) et 9 chaînes d'erreur ajoutés. Les endpoints
`/scan-handoff[/{token}]` (FEAT-023) restent en place mais ne sont plus appelés.

**Entrées câblées** : dashboard (bannière, remontée au-dessus des tuiles),
prêt-carte, prêt-livre, retour, **recherche catalogue** (`input[name=q]`),
**recherche membres** (`input[name=q]`), **champ ISBN du formulaire notice**
(`input[name=isbn_13]`) — petit bouton rond `.scan-inline-btn` à côté du champ.
Un ISBN-10 (texte) n'étant pas un code-barres, il se saisit à la main ; la
caméra ne lit que l'EAN-13 « Bookland » `978…` présent sur les livres.
Récolement et catalogage de masse hors périmètre (OfeliaScan).

#### Items

- `GET /items/{ean13}` : notice + état exemplaire pour vérification scan.
- `GET /search?q=...` : recherche pour autocomplétion mobile.

#### Résilience

- Endpoints idempotents là où c'est possible (`Idempotency-Key`).
- Throttling par scope (`auth`, `scan`, `isbn`) — déjà configuré dans `settings/base.py` (FEAT-004).
- Pagination cursor-based sur les listes.

#### Découverte mDNS / DNS-SD

La box **publie un service DNS-SD** pour qu'OfeliaScan la découvre sur le réseau local :

- Type de service : `_bibliofelia._tcp.`, domaine `.local`, port HTTP de l'API.
- Nom d'instance = `box_name` (= celui de `/pairing/info`).
- Enregistrements TXT recommandés : `library_name`, `version`, `api_base` (le *chemin* de l'API ; distinct du `base_url` — URL absolue — de `/pairing/info` ; non exploités par OfeliaScan v1).
- Implémentation (FEAT-019) : `avahi-daemon` sur l'hôte Raspberry Pi (pas dans le conteneur Docker). Le fichier `/etc/avahi/services/bibliofelia.service` est généré par la commande `manage.py generate_avahi_service` (à partir des `Setting` `box_name`/`library_name` et des réglages `BIBLIOFELIA_VERSION`/`API_BASE_PATH`/`MDNS_SERVICE_PORT`) ; le dossier `/etc/avahi/services/` est monté depuis l'hôte. `avahi-daemon`, géré par systemd, surveille ce dossier et recharge automatiquement. Le wizard de premier démarrage (§11.3) régénère le fichier avec le nom réel de la bibliothèque. Choix d'archi retenu pour sa robustesse (service géré par systemd, fichier statique, découplé du conteneur applicatif).

#### Implémentation (FEAT-016)

État : auth JWT, `/pairing/info`, `/isbn/{isbn}`, `/health`, le format
d'erreur, et **les sessions de scan + récolement** (FEAT-021 / Task #20)
sont implémentés dans `apps/api/`. Restent à faire : `/items/{ean13}`,
`/search`, `/sync/status` (raffinements ultérieurs).

- Les routes sont définies **sans slash final** (`apps/api/urls.py`), conforme
  au contrat (OfeliaScan concatène les chemins relatifs).
- `POST /auth/login` et `/auth/refresh` : serializers personnalisés
  (`apps/api/serializers.py`) émettant les noms OAuth 2.0.
- `version` (de `/pairing/info` et `/health`) provient du réglage
  `BIBLIOFELIA_VERSION` ; `base_url` est reconstruit depuis la requête entrante
  (ou réglage `API_BASE_URL` si défini) ; `box_name` / `library_name` du modèle
  `Setting` (renseignés par le wizard, §11.3).
- `/health` exige une authentification (contrat §6.10). Le healthcheck Docker
  utilise donc `/api/v1/pairing/info` (public) comme sonde de vivacité.

#### Gestion des identifiants OfeliaScan (FEAT-017)

Page d'administration **Connexion OfeliaScan** (`core:ofeliascan`,
`/admin/ofeliascan/`, accès SUPERADMIN, lien dans l'onglet Avancé) :

- Affiche l'**adresse de la box** (nom d'hôte, IP locale, hôte courant,
  chemin de l'API) — secours si la découverte mDNS échoue.
- Gère les **identifiants** que l'API accepte sur `POST /auth/login` :
  comptes Django de rôle `contributor_api`. Création (login + mot de
  passe) et révocation (`is_active=False` → SimpleJWT rejette).
- `Setting["ofeliascan_credentials"]` stocke `[{username, password,
  created_at}]` avec le **mot de passe en clair** (demande explicite :
  le bibliothécaire doit le relire pour le saisir dans l'app mobile —
  modèle « mot de passe Wi-Fi affiché »). Le compte Django garde un
  hash Argon2 ; le clair n'est qu'une copie de commodité.

### 6.11 Enrichissement métadonnées multi-sources (FEAT-031)

Tâche asynchrone qui interroge des sources externes pour compléter ou
écraser les métadonnées du catalogue.

**Pourquoi** : OpenLibrary unitaire (lookup ISBN à la création de notice)
couvre mal certains fonds. Au lieu de re-saisir chaque notice, on lance un
batch qui itère sur le périmètre choisi.

**Sources branchées (`apps/catalog/sources/`)** :

| Clé              | Module                  | Spécificité                                                     |
|------------------|-------------------------|-----------------------------------------------------------------|
| `openlibrary`    | `openlibrary.py`        | Gratuit, sans clé, bonne couverture FR/EN.                      |
| `google_books`   | `google_books.py`       | Clé API **facultative** (Google Cloud, gratuite) mais recommandée : sans clé le quota est partagé par adresse IP → 429 permanent sur un serveur mutualisé (BUG-023). Couverture mondiale, notamment IT/PT. |
| `bnf`            | `bnf.py` (SRU XML)      | Sans clé. Spécifique livres francophones.                       |
| `bne`            | `bne.py` (SRU Alma)     | Sans clé. Spécifique livres hispanophones.                      |
| `swisscovery`    | `swisscovery.py` (SRU Alma) | **FEAT-060** — sans clé. Réseau des bibliothèques suisses (SLSP), fr/de/it : seule source couvrant les éditeurs suisses (Zoé, romands…). |
| `k10plus`        | `k10plus.py` (SRU)      | **FEAT-060** — sans clé. Catalogue collectif DE/AT/CH (successeur GVK/SWB), livres germanophones. |

Écartées après test des endpoints (FEAT-060) : **DNB** (Allemagne, exige un
`accessToken` — K10plus couvre le même besoin), **SBN/ICCU** (Italie, pas
d'endpoint SRU public), **PORBASE/BNP** (Portugal, SRU en 404). Pour l'italien et
le portugais, la couverture repose donc sur Google Books avec sa clé.

Chaque module expose `lookup(isbn) -> dict | None` (clés normalisées :
`title`, `subtitle`, `authors_text`, `publisher`, `publication_year`,
`language`, `summary`, `subjects` (list), `cover_url` (str)). Les sources
SRU (BnF, BNE, Swisscovery, K10plus) ne renvoient pas de `cover_url`.

**Parsing SRU (BUG-022)** : les catalogues SRU servent le Dublin Core **imbriqué**
dans un wrapper à l'intérieur de `<srw:recordData>` (`<oai_dc:dc>` pour la BnF et
K10plus, `<srw_dc:dc>` pour les catalogues Alma). Les champs doivent donc être
cherchés **en descendant** (`.//dc:title`) et non en enfant direct : sinon toutes
les notices remontent vides (titre `''`) et sont silencieusement jetées, BnF et
BNE devenant inertes sur les 3 chemins (`lookup`, `lookup_issn`, `search`). Le
parsing Alma est porté une seule fois par `sources/_alma_sru.py`
(`AlmaSruSource`), partagé par BNE et Swisscovery, et nettoie le bruit MARC des
zones auteur (préfixe de liaison `880-01`, autorité `(IDREF)…`, code de rôle
final `aut`). K10plus a son propre parseur : ni `dc:creator` ni `dc:publisher`,
tout est en `dc:contributor` suffixé du rôle (`(Verlag)` → éditeur).

**Champs alimentés par l'enrichissement :**
- Texte/scalaires : `title` (écrase aussi le placeholder OfeliaScan `ISBN:<isbn> - <dd.mm.aaaa hh.mn>`), `subtitle`, `publisher`, `publication_year`, `language`, `summary`.
- Auteurs : split `;` côté source → `Author.get_or_create(full_name=…)` + `record.authors.add(…)`. En FILL_MISSING : seulement si pas d'auteur. En OVERWRITE : `record.authors.clear()` puis re-création.
- Tags (depuis subjects) : cap **10 max par notice**, longueur **≤ 40 caractères**, dedup insensible à la casse. En FILL_MISSING : seulement si la notice n'a aucun tag. En OVERWRITE : `record.tags.clear()` puis ajout.
- Cover : téléchargé via httpx (timeout 10s, **max 2 MB**, follow_redirects), stocké dans `record.cover_image` → `media/covers/<isbn>.jpg`. En FILL_MISSING : seulement si pas de cover. En OVERWRITE : remplace.

**Configuration** : `Paramètres → Sources de métadonnées` (`MetadataSourcesForm`,
section `sources` dans `core:settings_index`) — toggle on/off par source +
champ pour la clé Google Books (persistance dans `Setting["metadata.sources"]`
et `Setting["metadata.google_books_api_key"]`).

**Sources actives par défaut (FEAT-059)** : `MetadataSourcesForm.SOURCE_ORDER`
est la liste de référence (et l'ordre de préférence). `active_sources()` considère
toute source **non mentionnée** dans le réglage comme **active** : une instance
neuve, qui n'a aucun `Setting["metadata.sources"]`, propose donc les 6 cases à
cocher sur la page d'enrichissement. Avant FEAT-059, `google_books` valait `False`
par défaut → absent des cases sur les instances neuves alors qu'il était bien
interrogé au scan (`lookup_isbn_multi` parcourt tout le registre), incohérence
entre les deux flux. Les cases affichent le libellé de `SOURCE_LABELS`, pas le
slug. Ces réglages étant en base, ils sont **par instance** : une instance créée
par le wizard doit recevoir la clé Google Books (cf. §11.7).

**Lancement** : `Avancé → Enrichissement métadonnées` (`core:enrichment_index`,
rôle **librarian + superadmin** depuis FEAT-049 — auparavant superadmin
uniquement ; les 3 vues `enrichment_index`/`enrichment_start`/`enrichment_detail`
et le lien dans `advanced.html` sont ouverts aux bibliothécaires, READONLY exclu).
Formulaire :
- **Mode** : `fill_missing` (défaut, ne touche pas les champs déjà remplis)
  ou `overwrite` (remplace).
- **Sources** : sous-ensemble des sources actives.
- **Périmètre** : toutes les notices avec un ISBN / notices sans auteur /
  notices sans éditeur / liste d'ISBN libre (textarea).

Le formulaire crée un `EnrichmentJob` (`PENDING`) et le pousse dans la file
django-q2 (`async_task("apps.catalog.enrichment.run_enrichment_job", job.pk)`).
Redirection vers la page de détail qui auto-rafraîchit toutes les 3 s tant
que l'état est `pending` ou `running` (meta refresh, pas HTMX pour rester
simple).

**Tâche `run_enrichment_job(job_id)`** (`apps/catalog/enrichment.py`) :
1. **Garde idempotence** : si `state != PENDING` (ex. re-enqueue par django-q2), `return` immédiat — évite le double-traitement.
2. Passe `state=RUNNING`.
3. Construit le queryset via `build_queryset(scope_filter)` (filtre toujours à `isbn_13` ou `isbn_10` non NULL).
4. Pour chaque notice : `_try_sources()` interroge **toutes les sources actives en parallèle** (`ThreadPoolExecutor`, 1 thread/source) et renvoie `{source_name: data | None}` préservant l'ordre demandé.
5. `merge_record(record, responses, source_order, mode)` fusionne **field-by-field** : pour chaque champ, prend la 1re source non vide dans `source_order`. Permet par exemple un `summary` depuis Google Books quand OpenLibrary répond mais sans description. Le badge `metadata_source` reflète la 1re source contributrice dans l'ordre préféré ; `metadata_quality=AUTO` à chaque écriture.
6. Compteurs `processed/updated/skipped/errors` sauvegardés tous les 5 items + à la fin. `report` (JSONField) accumule une entrée par notice modifiée (`{record_id, isbn, changes: {field: source_name}}`) ou en erreur.
7. Final : `state=FINISHED` (ou `FAILED` si exception non gérée).

**Quota / 429 (BUG-019)** : l'API Google Books gratuite est plafonnée (~100 req/100 s, ~1000/jour). `apps/catalog/sources/google_books.py` applique un **throttle adaptatif thread-safe** (partagé verify + enrichissement) : **aucun bridage en régime normal**, puis ≥ `_MIN_INTERVAL_SLOW = 1,2 s` entre requêtes pendant `_SLOW_WINDOW = 100 s` après un 429 (`_note_rate_limited`), avec retour automatique à pleine vitesse — évite de pénaliser le cas où le quota est disponible. En complément, **back-off** sur 429 (`_get_json`, `_MAX_RETRIES_429 = 3`, respecte `Retry-After`, plafond 30 s) ; si le 429 persiste, la source lève `SourceRateLimited` (déf. `apps/catalog/sources/__init__.py`) pour distinguer « quota atteint, réessayer plus tard » de « rien trouvé » (`None`). Côté enrichissement : `_safe_call` mappe `SourceRateLimited` sur un sentinel interne, `_try_sources(..., with_rate_limit=True)` renvoie `(responses, rate_limited)` (le sentinel n'échappe jamais ; une source rate-limitée vaut `None` dans le dict). Une notice **sans donnée ET rate-limitée** est comptée dans `EnrichmentJob.rate_limited` (et non `skipped`), avec une entrée rapport `{record_id, isbn, rate_limited: true}` → un re-run ultérieur (quota disponible) la complète. La page détail affiche un **bandeau ambre** « Quota Google Books atteint — relancez demain » quand `rate_limited > 0`. Le quota **journalier** épuisé n'est pas récupérable dans le job (relancer le lendemain, réinit. minuit Pacific).

**Économie quota / vitesse (BUG-019)** : en mode FILL_MISSING, `run_enrichment_job` **saute** (sans interroger les sources) les notices déjà complètes — titre réel (≠ placeholder) ET au moins un auteur (`_record_is_complete`). Les re-runs ne retapent donc que les notices restées incomplètes (ex. celles rate-limitées au run précédent), ce qui accélère et préserve le quota. Compromis assumé : couverture/résumé/éditeur d'une notice déjà titrée+auteurée ne sont pas recomplétés en FILL_MISSING (utiliser OVERWRITE pour forcer la réinterrogation complète).

**Enqueue** : `async_task(..., q_options={"timeout": 3600, "retry": 7200, "ack_failure": True})` — désactive le re-enqueue automatique de django-q2 (`Q_CLUSTER.retry=120` global) qui provoquait des `processed > total` en doublonnant les workers sur une tâche batch.

**Rapport** : la page détail liste les notices traitées avec, pour chaque champ modifié, la source qui l'a fourni (badge `field ← source`).

**Modèle `EnrichmentJob`** : `started_at`, `finished_at`, `state` (PENDING /
RUNNING / FINISHED / FAILED), `mode`, `sources` (JSON list), `scope_filter`
(JSON dict), `total`, `processed`, `updated`, `skipped`, `errors`,
`rate_limited` (BUG-019 — notices non complétées pour cause de quota 429,
rejouables), `report` (JSON list), `created_by` (User, SET_NULL).

### 6.12 Catalogage Excel (FEAT-050, FEAT-053)

Deux outils sous **Avancé → Inventaire → Catalogage Excel**
(`catalog:excel_catalog_index`, rôle **librarian + superadmin**) pour traiter un
fonds existant fourni sous forme de tableur `.xlsx`. Les jobs s'exécutent en
tâche django-q2 (`apps.catalog.excel_catalog.run_excel_catalog_job`).

**Pourquoi** : beaucoup de bibliothèques Ofelia arrivent avec un inventaire
Excel (ID maison, titre, auteur, ISBN parfois incomplet). FEAT-031 ne couvre
que des notices déjà créées par ISBN ; FEAT-050 comble le trou en amont
(fichier brut à vérifier) et en aval (import direct).

**Validation d'upload** (`validate_xlsx`, côté vue, avant création du job) :
`.xlsx` uniquement (refus explicite `.xls`/`.csv`/`.ods`), **5 Mo** max,
**10 000 lignes** max, colonnes obligatoires présentes (insensible casse +
accents). En cas d'erreur → `messages.error`, pas de job créé.

**Mode VERIFY** — fichier `.xlsx` avec colonnes `ID`, `TITLE`, `AUTHOR`, `ISBN` :
1. **Passe 1 (par ISBN)** : pour chaque ISBN valide, `_try_sources` interroge les
   4 sources en parallèle ; la 1re réponse avec un titre alimente
   `TITLE_FOUND_BY_ISBN` / `AUTHOR_FOUND_BY_ISBN` / `SOURCE_BY_ISBN`. ISBN de
   longueur ∉ {10,13} → `SOURCE_BY_ISBN = ISBN_INVALID`.
2. **Passe 2 (par titre + auteur)** : **toutes les lignes ayant un titre**, y
   compris celles résolues par ISBN en passe 1 (les ISBN sont saisis à la main
   → recoupement systématique pour détecter les fautes de saisie).
   `search(title, author)` sur les 4 sources (parallèle), agrégation des
   candidats, réordonnancement local par `rapidfuzz.fuzz.WRatio`
   (`apps/catalog/sources/_fuzzy.py`). Le meilleur candidat ≥ **seuil 60**
   alimente `ISBN_FOUND_BY_TA` / `TITLE_FOUND_BY_TA` / `AUTHOR_FOUND_BY_TA` +
   `CONFIDENCE` (0-100). Sous 60 → rien écrit. Si l'ISBN trouvé ≠ ISBN du
   fichier (score ≥ 75) → cellule `ISBN_FOUND_BY_TA` colorée en orange.
3. **Sortie** : copie de l'Excel + 8 colonnes ajoutées en queue, en-têtes en
   gras, cellules `CONFIDENCE < 75` en fond orange. Stockée dans
   `media/excel_jobs/AAAA/MM/verify-<job>.xlsx`, téléchargeable depuis la page
   de détail. **Aucun effet de bord** sur la base.
4. **Quota / 429 (BUG-019)** : `_pass1_by_isbn` et `_search_all` propagent un
   drapeau `rate_limited` si une source lève `SourceRateLimited` (quota Google
   Books, cf. §6.11). `run_verify_job` compte `ExcelCatalogJob.rate_limited` et,
   pour une ligne non résolue par ISBN à cause du quota, écrit
   `SOURCE_BY_ISBN = RATE_LIMITED`. La page détail affiche un bandeau ambre
   « Quota Google Books atteint — relancez demain » quand `rate_limited > 0`.

**Mode IMPORT** — fichier `.xlsx` avec colonne `ISBN` (seule obligatoire) et
des colonnes **optionnelles** d'affectation de la fiche/exemplaire :
- `LOCATION` — code d'emplacement (warning si inconnu).
- `CATEGORY` — nom de catégorie existante (`name__iexact`, warning si inconnu).
- **`TITLE`** (FEAT-053) — titre de la fiche. Sur une notice **neuve**, il est
  posé directement (évite le placeholder `ISBN:…`) ; absent → placeholder
  conservé (comportement FEAT-050).
- **`AUTHOR`** (FEAT-053) — auteur(s), séparés par `;` (remplacement).
- **`TYPE`** (FEAT-053) — type de document : code interne (`book`,
  `magazine_issue`, `comic`, `newspaper`, `audio_cd`, `other`) ou libellé FR
  (`Livre`, `BD / manga`, `Revue`/`Magazine`, `Journal`, `CD audio`, `Autre`) —
  warning `TYPE_UNKNOWN` si non reconnu.
- **`EDITOR`** (FEAT-053) → `publisher`.
- **`YEAR`** (FEAT-053) → `publication_year` (entier ; warning `YEAR_INVALID`).
- **`LANGUAGE`** (FEAT-053) → `language` (code, ex. `fr`).
- **`TAGS`** (FEAT-053) → tags, séparés par `,` (remplacement ; cap 10 tags ×
  40 car., aligné sur l'enrichissement).
- **`EXTERNAL_CODE`** (FEAT-063) → code Ofelia externe de l'exemplaire. Alias
  d'en-tête acceptés : `CODE_EXTERNE`, `CODE EXTERNE`, `CODE_OFELIA_EXTERNE`,
  `OFELIA_EXT`, `EXTERNALCODE`. Normalisé comme à la saisie. Avertissements :
  `EXTERNAL_CODE_INVALID` (non alphanumérique ou > 20 car.),
  `EXTERNAL_CODE_DUPLICATE` (code déjà porté par un exemplaire du catalogue, ou
  répété dans le fichier). Dans les deux cas le code est ignoré et **le reste de
  la ligne est importé**. Si la ligne crée plusieurs exemplaires, le code va sur
  le premier — il en désigne un seul.
- **`PROVENANCE`** (FEAT-064) → provenance de l'exemplaire, résolue par **code
  ou libellé** (alias d'en-tête `ORIGINE`). Inconnue → `PROVENANCE_UNKNOWN`,
  l'import continue sans elle.
- **`CATEGORY_ABBR`** (FEAT-067) → abréviation (cote) de la catégorie résolue par
  la colonne `CATEGORY`. Depuis FEAT-071, les catégories du seed ont déjà une
  cote égale à leur code : cette colonne ne sert qu'aux catégories créées à la
  main. Alias : `ABBREVIATION`, `ABREVIATION`,
  `CATEGORIE_ABREGEE`, `CATEGORY_ABBREVIATION`, `CAT_ABBR`. Sans catégorie
  résolue, la cote n'a pas de cible → `CATEGORY_ABBR_ORPHAN` (la ligne s'importe
  quand même).
- **`CONDITION`** (FEAT-053) → **état de l'exemplaire** (`Item.state`) : code
  (`new`/`good`/`worn`/`damaged`) ou libellé FR (`Neuf`/`Bon`/`Usé`/`Abîmé`) —
  warning `CONDITION_UNKNOWN` si non reconnu.

**Sémantique overwrite (FEAT-053)** : une colonne **présente ET remplie** écrase
le champ correspondant de la notice — **y compris une notice déjà existante**
(matchée par ISBN). Une **cellule vide laisse l'existant intact** (la colonne ne
« vide » jamais un champ). `AUTHOR` et `TAGS` **remplacent** l'existant (pas de
fusion). Décision Val (2026-07-03). *NB : c'est une extension volontaire du
périmètre initial FEAT-050, qui excluait la mise à jour de notices existantes.*

Pipeline :
1. Crée une **`ScanSession` virtuelle** (`label = "Import Excel — <date>"`,
   state OPEN) — réutilise `job.scan_session` si déjà présent (ré-exécution
   admin idempotente).
2. Un `ScanItem` par ligne valide : `local_id = "excel-<job>-<row>"`
   (`update_or_create` → idempotent via unique `(session, local_id)`),
   `scanned_value` = ISBN normalisé, `metadata_title = ""` (placeholder posé
   par `_create_record`), `location_code` résolu (warning si inconnu),
   `category` résolue par `name__iexact` (warning si inconnu). Les overrides
   FEAT-053 de la ligne sont mémorisés (indexés par `local_id`).

   **Lignes non importables (BUG-025)** — l'import étant indexé par ISBN, une
   ligne sans ISBN exploitable ne peut pas produire de notice. Deux cas, tous
   deux **comptés** (`total`, `processed`, `errors++`) et **tracés** dans
   `report` avec un `label` « Auteur — Titre » identifiant le livre :
   `ISBN_INVALID` (longueur ∉ {10,13}) et `ISBN_MISSING` (cellule ISBN vide sur
   une ligne par ailleurs remplie). Seules les lignes **entièrement vides** sont
   ignorées en silence — `openpyxl` en compte régulièrement après les données.
   Avant le fix, `ISBN_MISSING` sortait par un `continue` muet **avant**
   l'incrément de `total` : la ligne était absente des compteurs comme du
   rapport, et le fichier « perdait » un livre sans la moindre erreur (constaté :
   105 lignes → 104 notices, `errors = 0`). La page de détail affiche désormais
   un **bandeau rouge « N lignes non importées »** dès `errors > 0`, en plus du
   tableau des avertissements.
3. `finalize_scan_session(session)` (pipeline FEAT-021) matérialise notices +
   exemplaires (matching ISBN existant → ajoute un exemplaire). La session
   apparaît dans **Catalogage par scan** (`/catalog/scan/`).
4. **Passe d'override FEAT-053** (`_apply_import_overrides`, transaction dédiée) :
   pour chaque ligne, via `ScanItem.processing_result` (`record_id` +
   `copies_created`), on écrase les champs de la notice et l'état des
   exemplaires du lot. `finalize_scan_session` et le flux caméra/OfeliaScan
   restent **inchangés** (l'override est spécifique à l'import Excel).
5. Enrichissement métadonnées **non automatique** (lancer un job FEAT-031
   ensuite si besoin).

**Sources — `search(title, author, limit=5)`** : ajouté à chaque module de
`apps/catalog/sources/` (en plus de `lookup(isbn)`). OpenLibrary
(`/search.json`), Google Books (`intitle:/inauthor:`, **clé API facultative** —
interrogé en anonyme si non configurée, quota par IP ; idem `lookup(isbn)`),
BNF/BNE (SRU `title`/`author`, ISBN extrait des `dc:identifier`). Enregistré
dans `sources.SEARCHES`. La passe 2 ne trace pas la source du candidat fusionné
(`SOURCE_BY_TA` laissée vide) ; le `CONFIDENCE` suffit au tri humain.

**Modèle `ExcelCatalogJob`** : voir §5.2.

### 7.1 Modes de fonctionnement

| Mode | Disponibilité internet | Comportement |
|------|-----------------------|--------------|
| Offline | Aucune | 100% fonctionnel, lookups ISBN mis en file |
| Online ponctuel | Quelques heures/jour | Worker django-q2 traite la file (ISBN, backup cloud, updates) |
| Online ZeroTier | Admin distant | Pas d'impact utilisateurs, accès SSH/HTTPS admin |

### 7.2 File de tâches asynchrones (django-q2)

Tâches typiques :
- `enrich_record_from_openlibrary(record_id)` : récupère métadonnées et couverture
- `backup_to_cloud()` : nightly si internet disponible
- `check_software_updates()` : weekly
- `expire_reservations()` : daily
- `expire_member_cards()` : daily
- `generate_overdue_report()` : weekly

Toutes les tâches sont idempotentes et reschedulables.

### 7.3 Détection de connectivité

Job léger ping vers `8.8.8.8` ou serveur Ofelia toutes les 5 minutes. Statut exposé dans `/health` et dans la barre de nav admin.

---

## 8. Sauvegarde et restauration

> Implémentation Sprint 4 (FEAT-014) :
> - `apps/tasks/backup.py:run_backup()` utilise l'API Python `sqlite3.Connection.backup()` (copie cohérente même sous WAL), vérifie `PRAGMA integrity_check`, gère la rotation 24h/7j/35j/400j, lance `rsync` ou `shutil.copytree` pour `media/`, et `rclone sync` si `backup_config.cloud_enabled`.
> - `Setting.last_backup` (timestamp/statut/taille/error) → exploité par le dashboard pour alerter si > 24 h.
> - `apps/tasks/scheduling.py:install_schedules()` enregistre 3 Schedule django-q2 (backup horaire, expire cartes quotidien, expire réservations quotidien). Installé au boot dev par `dev-entrypoint.sh` (commande `setup_schedules`).
> - Commandes : `manage.py run_backup [--force-daily|--force-cloud]`, `manage.py restore_backup <path> [--yes]`.
> - UI : bouton « Sauvegarder maintenant » + upload de restauration dans `/admin/settings/backup/` (superadmin).
> - Cohabitation avec `scripts/backup.sh` (container backup keebee) : mêmes dossiers cibles ; les deux peuvent tourner, la rotation est idempotente.



### 8.1 Sauvegarde locale

- Toutes les heures : `sqlite3 db.sqlite3 ".backup"` vers la clé USB
- Quotidiennement : rsync incrémental du dossier media (couvertures)
- Rotation : 24 horaires, 7 quotidiennes, 4 hebdomadaires, 12 mensuelles
- Vérification d'intégrité quotidienne (`sqlite3 ... "PRAGMA integrity_check"`)
- Alerte dans le tableau de bord si la sauvegarde a échoué depuis > 24h

### 8.2 Sauvegarde cloud (optionnelle)

- rclone vers stockage S3-compatible (Backblaze B2, Wasabi, ou serveur Ofelia central)
- Chiffrement côté client (rclone crypt)
- Déclenchement quand internet détecté, max 1 fois par jour
- Quota cible : moins de 1 Go par bibliothèque

### 8.3 Restauration

- Script `bibliofelia-restore.sh` packagé avec l'image
- Trois modes :
  - Restauration depuis clé USB (montée automatiquement)
  - Restauration depuis cloud (si ZeroTier disponible)
  - Restauration depuis fichier uploadé via interface web (admin)
- Procédure documentée dans le wizard d'installation

### 8.4 Cycle de vie matériel

- Carte SD : changement recommandé tous les 2 ans
- Procédure de migration documentée : flash nouvelle SD, restauration depuis clé USB

---

## 9. Sécurité

### 9.1 Authentification

- bcrypt via Django par défaut
- Session cookies HTTPOnly, Secure, SameSite=Lax
- Throttling de login (django-axes)
- Pas de "remember me" par défaut, session de 8h

### 9.2 Autorisation

Rôles :

| Rôle | Catalogage | Prêts | Usagers | Rapports | Paramètres | API |
|------|-----------|-------|---------|----------|------------|-----|
| Superadmin | Y | Y | Y | Y | Y | Y |
| Librarian | Y | Y | Y | Y (lecture) | N | N |
| Contributor_api | Catalogage uniquement | N | N | N | N | Y |
| Readonly | Lecture | Lecture | Lecture | Lecture | N | N |

Implémentation (FEAT-004) :
- Un `Group` Django par rôle, créé par `python manage.py setup_roles` (idempotent, appelé dans `dev-entrypoint.sh`). Mapping perms dans `apps/accounts/groups.py`.
- Signal `post_save` sur `User` (`apps/accounts/signals.py`) : synchronise `role`, `is_staff`, et l'appartenance au Group.
  - `is_superuser=True` force `role=SUPERADMIN` (cas `createsuperuser`).
  - Seul `superadmin` a `is_staff=True` → seul rôle qui peut accéder à `/admin/` Django.
  - Les autres rôles utiliseront l'UI custom (Sprint 2+).
- Helpers : `apps.accounts.permissions.require_role(*roles)` (décorateur vue Django) et `HasRole` (permission DRF, lit `view.required_roles`).
- Librarian ne peut pas `delete` les modèles porteurs d'historique (`BibliographicRecord`, `Loan`, `Member`) ; passe par `status=closed` ou escalade superadmin.

#### Suppression d'un compte utilisateur (FEAT-030)
- Action superadmin uniquement, depuis `accounts:user_list` (bouton « Supprimer » sur chaque ligne sauf soi-même) → page de confirmation listant les références historiques préservées.
- **Garde-fous bloquants** :
  1. Interdit de supprimer son propre compte (`request.user.pk == user.pk`).
  2. Interdit de supprimer le dernier SUPERADMIN actif (`User.objects.filter(is_active, role=SUPERADMIN | is_superuser).exclude(pk=user.pk).count() == 0`).
- Historique préservé via les FK `SET_NULL` natives : `loans.librarian`, `catalog.BibliographicRecord.created_by`, `catalog.ScanSession.created_by`, `catalog.EnrichmentJob.created_by`. L'auditlog conserve la trace de l'action (acteur devient NULL).

### 9.3 Reset administrateur

Procédure physique en cas d'oubli total :
1. Génération à l'install d'une `recovery_key` aléatoire
2. Stockée chiffrée sur disque + imprimée sur papier (à conserver hors box)
3. Procédure de boot spécial : présentation de la clé via fichier sur clé USB nommé `recovery.key`
4. Au boot, si présent et valide, prompt de création d'un nouveau superadmin
5. La clé est consommée et régénérée

### 9.4 Données personnelles

- Stockées localement uniquement
- Pas de cloud sans opt-in explicite
- Champ "Effacer définitivement le membre" pour droit à l'oubli (préservation de l'anonymisation des prêts historiques pour les statistiques)
- Audit log de toute consultation de fiche membre par staff (paramétrable)

### 9.5 Réseau

- HTTPS local avec certificat auto-signé généré au premier boot
- Affichage clair pour l'utilisateur la première fois (procédure de confiance)
- Pas d'exposition externe sauf via ZeroTier
- Firewall (iptables ou nftables) configuré : seuls 80, 443, 22 (via ZeroTier uniquement)

### 9.6 Audit

- django-auditlog actif sur Member, BibliographicRecord, Item, Loan, Setting, User (enregistrement explicite dans `apps/core/apps.py:ready()`, FEAT-004).
- Le middleware `AuditlogMiddleware` attache l'`actor` (request.user) automatiquement.
- Conservation : 5 ans → commande de purge périodique (différée Task #13/#14).
- Export possible pour rapport ou investigation (Task #11).

---

## 10. Ergonomie

### 10.1 Principes

- Icônes + texte (les usagers savent lire)
- Couleurs sémantiques : vert disponible, orange réservé, rouge prêt en retard
- Police lisible (minimum 16px)
- Boutons d'action principaux de taille généreuse (44px min, accessibilité tactile)
- Confirmation explicite des actions destructives
- Messages d'erreur en langage naturel, sans jargon technique
- Cohérence des libellés entre les écrans

### 10.2 Écrans principaux

1. **Accueil / Dashboard** : grille de tuiles colorées + KPIs + actions rapides + tendance
2. **Prêt** : scan carte → scan livres → valider (workflow linéaire, gros boutons)
3. **Retour** : scan livres → valider
4. **Catalogue** : recherche + liste + détail notice/exemplaire
5. **Membres** : recherche + liste + détail (libellé UI : « Membres »)
6. **Réservations** : à honorer + en attente
7. **Avancé** : Impression, Rapports, Inventaire, Méta-données, Administration (onglet regroupeur)
   - **Inventaire** : sessions + détail session (libellé UI ; app/code = `inventory`)
   - **Rapports** : sélection + génération PDF/CSV
   - **Paramètres** : sections regroupées

> **Navigation (refonte UI 2026-05-23, design OFELIA)** :
>
> - **Topbar sticky** : logo OFELIA (**FEAT-077** : `ofelia-logo-small.png`, l'emblème seul, ~30 px de large ; `ofelia-logo.png` reste réservé aux impressions) + nom de la bibliothèque + sélecteur de langue (pill) + aide + avatar utilisateur (dropdown Mon compte / Déconnexion). Page login : topbar allégée sans avatar.
> - **Accueil (FEAT-077)** : le hero porte à droite du « Bonjour, <nom> » la **date et l'heure de la Box**, alignées sur le bloc de salutation (heure en bordeaux, date en dessous ; le bloc passe à la ligne sur mobile). La Box n'a pas de pile RTC : hors ligne, elle repart sur une heure fausse à chaque extinction, et prêts, retards et sauvegardes en dépendent. Le gabarit publie l'horodatage serveur dans `data-clock` et le script n'utilise l'horloge du navigateur que pour mesurer le temps écoulé depuis le chargement (rafraîchissement toutes les 15 s) — un poste bien à l'heure ne peut donc pas masquer une Box déréglée. L'heure est suivie de l'**abréviation du fuseau** (`CEST`, `-03`… — certaines zones IANA, dont l'Argentine, n'ont pas de sigle littéral et s'écrivent par leur décalage). Corollaire : le fuseau est réglable (§6.6), faute de quoi une bibliothèque hors UTC croirait sa Box déréglée en permanence.
> - **Accueil** : grille de **6 grosses tuiles colorées** (Catalogue=amber, Membres=sky, Prêt=orange, Retour=olive, Réservations=blush, Avancé=forest) avec illustrations SVG multicolores 64×64 OFELIA, responsive 1→2→4 colonnes (600/900 px). Bannière scan rapide. KPIs 6 cartes.
> - **Tile strip** (pages secondaires) : bande horizontale scrollable de chips colorés sous la topbar, permettant de naviguer entre toutes les sections sans repasser par l'accueil. Chip actif = couleur de section.
> - **Page head** : chaque page secondaire affiche l'illustration SVG de la section + titre + sous-titre + bouton d'action principal.
>
> Implémentation Sprint 4 (FEAT-017) + refonte UI (design handoff 2026-05-23, FEAT-022).
>
> **Sprint 8 / FEAT-025 (2026-05-23)** : le design OFELIA est étendu à **toutes les pages métiers** (catalogue, usagers, prêts, inventaire, rapports, comptes, paramètres, impression, aide). Conventions appliquées partout : pagehead avec icône colorée + titre + sous-titre + action principale ; tilestrip de navigation contextuelle (chip actif coloré selon la section : `catalogue`, `members`, `lending`, `return`, `reservations`, `advanced`) ; tables stylées (`.table-wrap` + `.table` + `.badge` pour les statuts) ; boutons `.btn btn--primary` (action principale bordeaux) / `.btn btn--ghost` (action secondaire contour) / `.btn btn--accent` (orange) / `.btn--sm` (petits boutons inline) — minimum 44 px (`.btn--sm` 36 px) ; formulaires emballés dans `.card` avec `.field` + `.form-actions` (séparateur visuel pour les boutons en bas). Helpers CSS ajoutés à `static/css/ofelia.css` : `.req` (asterisque rouge), `.help-hint` (small gris), `.field-error` (small rouge), `.form-control` (input class pour widget_tweaks `add_class:"form-control"`), `details.advanced-section` (sections repliables stylées du Mode avancé), `.isbn-row` (input + bouton inline pour le lookup ISBN), `.form-actions` (zone de boutons avec séparateur).

### 10.3 Mode "accès simple" vs "avancé"

Pour respecter le principe d'ergonomie pour usagers peu formés sans frustrer les avancés :

- Mode simple par défaut : les options avancées sont cachées sous des sections repliables "Options avancées"
- Possibilité par utilisateur de cocher "Toujours afficher les options avancées" dans son profil

### 10.4 Aide contextuelle

- Tooltips sur les champs
- Page d'aide dédiée par écran, accessible via icône "?" en haut à droite
- Vidéos courtes (optionnelles, externalisées plus tard)

> Implémentation Sprint 2 (FEAT-005) : icône « ? » dans l'en-tête → page d'aide
> unique (`core:help`) regroupant les rubriques principales. Le découpage par
> écran sera affiné ultérieurement. Le mode simple/avancé (§10.3) est piloté par
> `User.always_show_advanced`, basculable depuis le menu utilisateur.

---

## 11. Déploiement et mise en service

### 11.1 Image Docker

- Image multi-arch (`Dockerfile`, cible `prod`) — arm64 pour la Pi 5, amd64
  pour dev et test.
- **Pas de registry** : keebee clone le dépôt GitHub BibliOfelia au moment de
  l'installation et build l'image directement sur la Pi (même mécanisme que
  Digistorm — FEAT-020). Internet requis uniquement pendant l'installation.

### 11.2 Docker Compose

BibliOfelia est installé via le **wizard de keebee** (case à cocher
« BibliOfelia »). keebee intègre deux services à son propre
`docker-compose.yml` ; cf. `keebee/docs/specs/FEAT-029-bibliofelia.md` et le
fichier `docker-compose.yml` de ce dépôt (référence). Forme des services :

```yaml
services:
  bibliofelia:                       # conteneur edubox-bibliofelia
    build: { context: ./bibliofelia, target: prod }
    restart: unless-stopped
    volumes:
      - /opt/edubox/data/bibliofelia/data:/app/data
      - /opt/edubox/data/bibliofelia/media:/app/media
      - bibliofelia-static:/app/staticfiles
      - /etc/avahi/services:/etc/avahi/services      # mDNS — FEAT-019
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
      SECRET_KEY: ${BIBLIOFELIA_SECRET_KEY}          # généré par le wizard
      ALLOWED_HOSTS: "*"
      FORCE_SCRIPT_NAME: /bibliofelia
      STATIC_URL: /bibliofelia/static/
      MEDIA_URL: /bibliofelia/media/
      API_BASE_PATH: /bibliofelia/api/v1/
      SECURE_COOKIES: "false"                        # AP WiFi en HTTP
    networks: [edubox-net]

  bibliofelia-worker:                # conteneur edubox-bibliofelia-worker
    build: { context: ./bibliofelia, target: prod }
    entrypoint: ["/usr/bin/tini", "--"]
    command: ["python", "manage.py", "qcluster"]
    depends_on:
      bibliofelia: { condition: service_healthy }
    networks: [edubox-net]
```

nginx (keebee) sert `/bibliofelia/static/` et `/bibliofelia/media/` par
`alias`, et proxifie le reste vers `bibliofelia:8001` en retirant le préfixe.

### 11.3 Wizard de premier démarrage

> Implémentation Sprint 4 (FEAT-015) :
> - Multi-step session-based dans `apps/setup/views.py` (**7 étapes** depuis FEAT-074 : langue, identité, langues activées, superadmin, sauvegarde, ZeroTier, démo — l'étape « imprimante » ne configurait que CUPS et a été retirée avec lui).
> - `apps/setup/services.py:apply_wizard()` persiste les choix dans `Setting.*` (`library_name`, `box_name`, `library_identity`, `languages_config`, `backup_config`, `zerotier`), crée le superadmin, génère et **hashe** la `recovery_key` (§9.3 ; clé en clair affichée une seule fois), installe les schedules django-q2 + le service Avahi, et bascule `setup_completed=True`.
> - Routes : `setup:wizard`, `setup:step`, `setup:finalize` — non préfixées par la langue (hors `i18n_patterns`).
> - Détection auto USB / ZeroTier : **différée** (saisie manuelle en v1).



À la première connexion web (route `/setup` accessible uniquement si pas encore configuré) :
1. Choix de la langue de l'interface
2. Nom et adresse de la bibliothèque
3. Langues additionnelles à activer
4. Création du compte superadmin
5. Configuration clé USB de backup (détection auto, ou skip)
6. Configuration ZeroTier (skip ou saisie network ID)
7. Choix d'importer ou non un jeu de données de démo
8. Récapitulatif et génération de la `recovery_key` à imprimer

### 11.4 Données de démo

> Implémentation Sprint 4 (FEAT-015) :
> - `apps/setup/demo.py` : `install_demo()` crée 50 notices, 80 exemplaires, 20 usagers, jusqu'à 15 prêts en cours. Objets marqués `[DEMO]` dans `notes` / `summary` / `description` selon le modèle.
> - `remove_demo()` + commande `manage.py remove_demo` suppriment proprement (via marqueur).
> - Activable depuis le wizard (`Step8DemoForm`).
> - **BUG-007 (2026-05-22)** : les notices sans ISBN sont créées avec `isbn_13=None` (et non `""`) — la contrainte UNIQUE partielle `WHERE isbn_13 IS NOT NULL` n'autorise les doublons que pour `NULL`.



- Set de seed : 50 notices fictives, 80 exemplaires, 20 membres, 15 prêts en cours
- Activable/désactivable depuis les paramètres
- Suppression complète possible en un clic après formation

### 11.5 Mise à jour logicielle

#### Mode connecté
- Worker vérifie weekly si nouvelle version disponible
- Notification dans le tableau de bord admin
- Bouton "Mettre à jour" : pull de la nouvelle image, restart container, exécution migrations
- Rollback automatique si santé KO après 5 min

#### Mode déconnecté
- Téléchargement de l'image tarball sur clé USB depuis un poste connecté
- Procédure d'import : copie sur clé USB nommée `bibliofelia-update.tar`, branchement, validation depuis interface web

### 11.6 Diagnostic et support

- Endpoint `/bibliofelia/api/v1/health` JSON avec métriques système
- Page admin `/bibliofelia/admin/diagnostics` regroupant logs récents, statut backups, statut queue
- Export de "bundle de diagnostic" zip (logs + config sans secrets) pour support à distance
- Accès SSH via ZeroTier réservé au support central

### 11.7 Hébergement multi-instances — domaine bibliofelia.org (FEAT-056)

Depuis FEAT-056 (2026-07-18), BibliOfelia n'est plus seulement embarqué sur la Box :
des instances centralisées sont hébergées sur le serveur **Avignon** derrière un
reverse-proxy **Traefik** (TLS Let's Encrypt), sous le domaine **bibliofelia.org**
(registrar/DNS Infomaniak, IP publique unique partagée `31.164.198.65`).

Topologie des adresses :

| Adresse | Cible | Nature |
|---|---|---|
| `canaima.bibliofelia.org` | Ofelia Box (Pi) via Traefik → `192.168.0.147:80` | La Box à sa nouvelle adresse (remplace `ofelia.zitoon.com`, conservée en parallèle) |
| `sanjuan.bibliofelia.org` | Instance BibliOfelia sur Avignon | Bibliothèque San Juan (BD/volumes isolés) |
| `grand-saconnex.bibliofelia.org` | Instance BibliOfelia sur Avignon | Bibliothèque Grand-Saconnex (BD/volumes isolés) |
| `docs.bibliofelia.org` | Guide MkDocs statique (Avignon) | Miroir **en ligne** du guide ; la doc **locale embarquée sur la Box** reste servie hors-ligne sous `/bibliofelia/docs/` (inchangée) |
| `bibliofelia.org` + `www` | 301 permanent → `ofeliainternational.org/what-we-do/` | Redirection (SEO-safe) |
| `mail.bibliofelia.org` | docker-mailserver (Avignon) | 3 boîtes `no-reply@`/`info@`/`admin@` ; SPF/DKIM/DMARC validés, envoi+réception |

Différences d'une instance Avignon vs la Box :
- sert à la **racine `/`** de son sous-domaine (pas de `FORCE_SCRIPT_NAME=/bibliofelia`) ;
- pile isolée `web` (gunicorn) + `worker` (django-q2) + `nginx` (sert `/static`, `/media`,
  proxifie le reste), volumes SQLite/media/static propres, `SECRET_KEY` unique,
  `CSRF_TRUSTED_ORIGINS=https://<sous-domaine>`, `SECURE_COOKIES=true` (Traefik/nginx
  transmettent `X-Forwarded-Proto`) ;
- première connexion → wizard `/setup/` (langue, nom de la bibliothèque, compte admin).

**Guide utilisateur (FEAT-057)** : le bouton « ? » de la topbar pointe sur
`<préfixe app>/docs/`. Sur la Box c'est `/bibliofelia/docs/` (guide embarqué servi
par nginx keebee, hors-ligne) ; sur une instance Avignon c'est `/docs/`, servi par
le nginx d'instance qui **proxifie le conteneur `bibliofelia-docs`** déjà en place
pour `docs.bibliofelia.org` (réseau Docker partagé `web`). Les deux `proxy_pass`
du fichier (`/docs/` → conteneur docs, `/` → `web:8001`) passent par
`resolver 127.0.0.11` + une **variable d'upstream** : sans cela nginx résout les
IP des conteneurs au démarrage et sert des 502 dès qu'un conteneur est recréé
après lui — une instance distante ne doit pas dépendre de l'ordre de redémarrage.
Conf versionnée :
`deploy/avignon/instance-nginx.conf` — fichier **partagé par toutes les instances**,
> ⚠️ **Depuis le 2026-08-08, les instances ne tournent plus sur Avignon.** Le
> couple Avignon/Fez est en failover automatique : c'est le **nœud actif** qui
> porte Traefik, `bo-sanjuan-*`, `bo-grand-saconnex-*` et `bibliofelia-docs`.
> Au 2026-08-18 l'actif est **Fez** (`192.168.0.221`), Avignon est le secours et
> n'a aucun conteneur BibliOfelia. Le rôle se lit dans
> `/home/val/gqqfm-cluster-role`. Tout déploiement d'instance vise le nœud
> actif, puis se répète sur le secours (sinon une bascule ramène le code
> périmé). Procédure dans `CLAUDE.md` § « Failover Fez ⇄ Avignon ».

déployé à `~/docker/bibliofelia-instances/nginx.conf`. Limite connue : les liens
« vers l'app » écrits en dur dans le guide (`/bibliofelia/<lang>/…`) ne
fonctionnent que sur la Box.

**Réglages à poser sur une instance neuve** (ils sont en base, donc par instance —
le wizard ne les demande pas) : `metadata.google_books_api_key`, sans quoi Google
Books répond 429 en permanence derrière l'IP mutualisée d'Avignon (BUG-023). Les
sources sont, elles, actives par défaut depuis FEAT-059.

L'app ne possède pas encore de fonction d'envoi d'email ; le serveur mail est prêt et
sera câblé (relais submission `192.168.0.222:587`, compte `no-reply@`) le jour où une
telle fonctionnalité (emails de confirmation) sera développée. Détails et procédures :
`docs/specs/FEAT-056-hebergement-multi-instances.md`.

---

## 12. Tests et qualité

### 12.1 Tests automatisés

- Tests unitaires Django (pytest-django) : modèles, règles métier, services
- Tests d'intégration : workflows complets de prêt/retour, validation API
- Tests API : Postman/Bruno collection versionnée
- Coverage cible : 70% en v1

### 12.2 Tests utilisateurs (UAT)

- Réalisés sur l'Ofelia Box réelle dès que possible
- Scénarios documentés couvrant les 10 workflows principaux
- Scénarios de coupure (réseau, courant) à vérifier

### 12.3 CI

- GitHub Actions ou Gitea Actions
- Tests à chaque push
- Build d'image multi-arch sur tag
- Pas de déploiement auto en production : push manuel

---

## 13. Documentation

### 13.1 Documentation utilisateur

- Manuel bibliothécaire (PDF) en français, anglais, espagnol, malgache
- Guides courts par tâche (inscription, prêt, retour, récolement)
- Vidéos courtes (à produire plus tard)

### 13.2 Documentation administrateur

- Installation Ofelia Box from scratch
- Configuration ZeroTier
- Sauvegardes et restauration
- Mise à jour
- Diagnostic et récupération

### 13.3 Documentation développeur

- README architecture
- Conventions de code (Black, isort, ruff)
- Procédures de release
- Schéma de données

---

## 14. Évolutions v2 et au-delà

### 14.1 Cibles v2 confirmées

- Support arabe et RTL
- Import/export MARC, Koha, SLiMS
- Écran connecté local (HDMI) avec interface kiosque
- Douchette USB code-barre dédiée au desktop
- Cartes membres PVC (impression dédiée)
- Sync différentielle plus fine avec OfeliaScan
- Mode prêt mobile via OfeliaScan
- Catalogue OPAC public en lecture seule (kiosque ou web local)

### 14.2 Cibles plus lointaines

- Catalogue de ressources numériques (epub, pdf hébergés)
- Intégration avec Kolibri / Moodle d'Edubox pour usage scolaire
- Fédération entre plusieurs bibliothèques Ofelia
- Statistiques agrégées au niveau projet Ofelia (anonymisées)
- Application Android usager (consultation catalogue, réservation à distance)

---

## 15. Risques et points d'attention

| Risque | Impact | Mitigation |
|--------|--------|-----------|
| Carte SD corrompue | Perte de données | Sauvegarde horaire USB + cloud, restauration scriptée |
| Coupure courant fréquente | Corruption SQLite | UPS Waveshare + WAL mode + journaling |
| Imprimante inaccessible depuis le serveur (USB sur le poste, serveur hors du LAN) | Bloque les étiquettes | **Impression PDF systématique** depuis le poste client — plus aucun envoi serveur → imprimante (FEAT-074) |
| Réseau partagé peu fiable | API OfeliaScan flaky | Idempotency keys + retry côté client |
| Métadonnées OpenLibrary incomplètes pour livres locaux | Catalogage manuel | Workflow saisie manuelle clair, pas de blocage |
| Personnel changeant | Perte de savoir | Doc multilingue, mode simple par défaut |
| Mot de passe admin perdu | Bloque l'usage | Procédure recovery_key |
| Conflit ressources avec Edubox | Lenteurs | Limites Docker (cpu, memory), monitoring |

---

## Annexe A : Glossaire

- **Notice (bibliographique)** : enregistrement décrivant un ouvrage (titre, auteur, ISBN…), indépendamment du nombre d'exemplaires physiques.
- **Exemplaire** : copie physique d'un ouvrage présente dans la bibliothèque. Plusieurs exemplaires peuvent être rattachés à une même notice.
- **Récolement** : inventaire physique du fonds, comparaison avec le catalogue.
- **OPAC** : Online Public Access Catalog, catalogue consultable par les usagers.
- **Ofelia Box** : Raspberry Pi 5 hébergeant les services du projet Ofelia (anciennement Edubox).

## Annexe B : Stack résumé

```
Python 3.12
Django 5.x LTS
SQLite 3 (WAL, FTS5)
Django REST Framework
django-q2
django-modeltranslation
django-auditlog
django-axes
HTMX 2.x + Alpine.js 3.x
ofelia.css (système de design OFELIA Studio Ayer — remplace Pico.css)
Bricolage Grotesque + DM Sans (woff2 locaux — remplace Inter)
python-barcode + ReportLab
openpyxl (catalogage Excel FEAT-050)
rapidfuzz (matching titre+auteur FEAT-050)
httpx
gunicorn
nginx (partagé Edubox)
Docker + Docker Compose
ZeroTier (admin)
```
