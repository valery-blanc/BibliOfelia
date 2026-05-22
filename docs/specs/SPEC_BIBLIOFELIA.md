# SPEC_BIBLIOFELIA

Spécification détaillée du logiciel de gestion de bibliothèque BibliOfelia, application web auto-hébergée sur Ofelia Box (Raspberry Pi 5).

Version : 1.0 (cible v1)
Statut : draft pour Spec-Driven Development
Dernière modif spec : 2026-05-23 — Refonte UI design OFELIA (§3.2 Frontend, §10.2 Navigation/Écrans : tuiles, tile strip, page head, polices Bricolage Grotesque/DM Sans, ofelia.css, logo OFELIA) ; FEAT-021 (API scan-sessions + inventory-sessions : contrat aligné sur le client OfeliaScan — corps `{"items":[...]}`, champs `scanned_value`/`metadata_*`/`item_state`, idempotency `local_id`, finalize sync = create-or-add-copies, ownership contributor_api — §6.10) ; FEAT-020 (intégration keebee : déploiement sur la Ofelia Box via le wizard keebee, clone + build sur la Pi, routage nginx `/bibliofelia/`, réglage `SECURE_COOKIES`, statique servi par nginx — §4, §11) ; FEAT-018 (terminologie UI : l'EAN13 interne d'un exemplaire est nommé « code Ofelia » dans toute l'interface ; rapport d'inventaire enrichi du code Ofelia et de l'ISBN — §5.2/§6.5/§6.7) ; Sprint 4 : FEAT-011 (dashboard enrichi §6.6 + rapports + paramètres + gestion comptes), FEAT-012 (impression étiquettes + cartes §6.7), FEAT-013 (notifications offline §6.8), FEAT-014 (sauvegardes §8 + planification django-q2), FEAT-015 (wizard premier démarrage §11.3 + données démo §11.4), FEAT-017 (onglet « Avancé » + page Connexion OfeliaScan + « Mon compte » §6.6/§6.10/§10.2), BUG-006 (i18n : `accounts/` déplacé sous `i18n_patterns` + chaînes EN/ES/MG complétées) ; Sprint 3 : FEAT-016 — API OfeliaScan (§6.10 : auth JWT, /pairing/info, /isbn/{isbn}, /health) ; FEAT-019 — publication mDNS via service Avahi sur l'hôte (§6.10) ; SPEC-CORR-002 — /pairing/info renvoie `base_url` (URL absolue) ; Sprint 2 : FEAT-005 à FEAT-010 (§6.1 à §6.5, §10) ; i18n 4 langues (§6.9) ; BUG-002 à BUG-005 ; §6.10 réécrit comme contrat d'API (SPEC-CORR-001)

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
- Imprimante d'étiquettes : thermique USB (modèle à préciser, support CUPS requis)
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
| Impression | pycups | API Python pour CUPS |
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
- `parent` (FK self, nullable, pour hiérarchie simple)
- `default_loan_duration_days` (entier, nullable, override des règles)

Catégories de seed à l'install :
- Enfance : Albums, Premières lectures, Romans jeunesse
- Adultes : Romans, Nouvelles, Poésie, Théâtre
- Documentaires : Sciences, Histoire, Géographie, Pratique, Religions
- Périodiques

#### Tag
- `id` (PK)
- `name` (traduit)
- `color` (string hex, optionnel pour affichage)

#### Location
- `id` (PK)
- `code` (string court, ex. "A3", "JEU")
- `description` (texte)
- `parent` (FK self, nullable, pour ex. "Salle principale > Rayon A > Étagère 3")

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
- `record` (FK BibliographicRecord, CASCADE)
- `location` (FK Location, nullable)
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
- `preferred_language` (string ISO 639-1, default = langue de la box)
- `replaces_card_number` (string, nullable, pour traçabilité remplacement)
- `parent_account` (FK self, nullable, pour membres rattachés à un compte collectif)
- `photo` (FileField, nullable, optionnel)

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
- `Item(internal_id)` unique
- `Item(ean13)` unique
- `Item(status, location_id)` pour récolement
- `Member(card_number)` unique
- `Loan(member_id, status)` pour règles de prêt
- `Loan(due_date, status)` pour rapports retards
- FTS5 virtuel sur `(title, subtitle, summary, authors_concat)` via triggers sync (`catalog_record_fts`, migration `catalog/0002_fts5`). `authors_concat` est un `group_concat(full_name, ' ')` resynchronisé sur ajout/suppression M2M `BibliographicRecord.authors`.

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
- Bouton "Imprimer étiquette(s)" qui envoie au CUPS

#### Import batch depuis OfeliaScan
- Réception via API REST (cf. §6.10)
- File d'attente "à valider" avec aperçu de chaque entrée
- Validation manuelle ou en masse
- Notices créées en `metadata_quality = auto`

#### Recherche
- Barre de recherche globale sur toutes les pages
- Full-text via FTS5 sur titre, sous-titre, résumé, auteurs
- Recherche exacte sur ISBN (13 ou 10) si la requête ressemble à un ISBN
- Recherche exacte sur EAN13 d'exemplaire ou n° de carte membre
- Filtres : catégorie, langue, statut exemplaire, état, emplacement, document_type
- Tri : pertinence, titre, auteur, date d'ajout

#### Modification et suppression
- Édition libre de notice et exemplaire pour bibliothécaires
- Suppression : interdite si exemplaires liés actifs, sinon suppression logique (champ `discarded`)
- Historique conservé via django-auditlog

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
- Création d'un Member type "collectif" (école, famille)
- Possibilité d'attacher des membres "enfants" via `parent_account`
- Règles de prêt appliquées au compte collectif

#### Remplacement de carte
- Bouton "Remplacer la carte" sur la fiche
- Génère un nouveau `card_number`, stocke l'ancien dans `replaces_card_number`
- Ancien numéro désactivé pour l'identification mais conservé pour traçabilité

#### Renouvellement et expiration
- Tâche django-q2 quotidienne marque `expired` les cartes dont `expiration_date < today`
- Avertissement à la bibliothécaire au scan d'une carte expirante (< 30 jours)
- Renouvellement = mise à jour de `expiration_date` (1 clic)

### 6.3 Prêts et retours

#### Workflow de prêt
1. Bibliothécaire ouvre l'écran "Prêt"
2. Scan ou saisie de la carte membre
3. Affichage de la fiche membre, prêts actifs, messages en attente, alertes (retards, carte expirante)
4. Scan ou saisie des EAN13 des livres
5. Pour chaque livre, vérifications :
   - Exemplaire `available`
   - Pas de réservation prioritaire d'un autre usager (sinon alerte + override possible avec note)
   - Limite de prêts simultanés respectée pour la catégorie membre
   - Document type autorisé pour la catégorie
6. Confirmation, calcul de `due_date` à partir de la règle applicable
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

### 6.5 Récolement

> Libellé UI : depuis FEAT-017, l'écran est intitulé **« Inventaire »**
> (accessible via l'onglet Avancé). L'app, le code et les modèles
> conservent le nom `inventory` ; « récolement » reste le terme du domaine
> dans cette spec.

#### Lancement
- Page "Récolement"
- Création d'une session avec : périmètre (toutes locations / une location spécifique / une catégorie), date de début
- Génération d'un `session_id` à donner à OfeliaScan

#### Réception des scans
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
- Chaque exemplaire listé (manquants, hors périmètre) est identifié par son **code interne** (`OFL-…`), son **code Ofelia** (EAN13) et son **ISBN** lorsqu'il est connu (FEAT-018)
- Actions proposées pour chaque divergence (réintégrer, marquer perdu, déplacer, créer notice)

#### Historique
- Conservation des sessions clôturées
- Comparaison entre récolements pour suivi de la qualité du fonds

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
> - **Paramètres** (`/admin/settings/`, superadmin uniquement) : identité (nom, box_name mDNS, adresse, contact), langues (activées + défaut), sauvegardes (cf. §8 / FEAT-014), format étiquettes/cartes, ZeroTier. Catégories/Tags/Locations/MemberCategory restent éditées via `/admin/` Django pour l'instant (lien depuis l'index).
> - **Gestion comptes** (`/accounts/users/`) : CRUD + reset mot de passe (avec génération aléatoire 16 chars).
> - **Diagnostic** (`core:diagnostics`) : versions, dernière sauvegarde, file django-q2.
>
> Implémentation Sprint 4 (FEAT-017) — **navigation** :
> - Onglet **« Avancé »** (`core:advanced`) dans la barre de nav : page index regroupant Impression, Rapports, Inventaire et Administration, chaque lien explicité d'une phrase. C'est le point d'accès unique aux écrans hors-workflow.
> - Barre principale allégée : plus de « Tableau de bord » (le logo `house` y mène) ni de « Récolement » (→ Avancé / Inventaire).
> - Menu utilisateur (haut-droite) : « Mon compte » (auto-édition de son propre compte via `accounts:user_edit` ; formulaire restreint sans `role`/`is_active` pour les non-superadmins) + « Déconnexion ». L'entrée « Mode avancé/simple » (§10.3) n'est plus surfacée mais le mécanisme reste actif côté modèle.



#### Tableau de bord
- Prêts actifs (compteur + tendance 30 jours)
- Retards (compteur + détail)
- Top 10 livres les plus empruntés (mois, année)
- Membres actifs (mois, année)
- Croissance du fonds (mois, année)
- État système (espace disque, dernière sauvegarde, dernière sync, version)

#### Rapports
- Rapport annuel d'activité (PDF) : prêts, membres, fonds, top, retards, perdus
- Liste imprimable des retards
- Liste imprimable des inactifs (membres et livres)
- Export CSV/Excel des prêts par période
- Rapport pour bailleur (template paramétrable)

#### Paramètres
- Identité de la bibliothèque (nom, adresse, logo)
- Langues activées et langue par défaut
- Règles de prêt (par catégorie d'usager et type de document)
- Catégories de document
- Catégories d'usager
- Emplacements
- Tags
- Format d'étiquette et de carte
- Backup (chemin clé USB, fréquence, cloud)
- ZeroTier (statut, ID réseau)

#### Gestion des comptes
- Création d'utilisateurs bibliothécaires et admin
- Réinitialisation de mot de passe par admin
- Procédure physique de récupération si tous les admins sont bloqués : fichier sur clé USB de récupération avec hash de reset à présenter au boot

### 6.7 Impression d'étiquettes

> Implémentation Sprint 4 (FEAT-012) :
> - `apps/printing/services.py` : `render_item_labels_pdf(items)` (planche A4 24 étiquettes 70×36 mm par défaut, dimensions paramétrables via `Setting.label_format`) ; `render_member_cards_pdf(members)` (8/A4 par défaut, paramétrable 4/6/8/10).
> - Codes-barres : `python-barcode` → PNG en mémoire → ReportLab.
> - CUPS : `pycups` (installé uniquement dans l'image Linux Docker, optionnel) ; `submit_to_cups(pdf)` retourne `sent=False` silencieusement en dev Windows, le PDF est servi en fallback.
> - Routes : `printing:labels`, `printing:labels_pdf`, `printing:labels_send`, `printing:cards`, `printing:cards_pdf` (rôle LIBRARIAN/SUPERADMIN).



#### Étiquettes exemplaires
- Écran intitulé « **Étiquettes codes Ofelia** » (FEAT-018)
- Format thermique 50x25mm (paramétrable)
- Contenu : code Ofelia (EAN13) lisible humainement et code-barres, titre tronqué (30 caractères), code Location, internal_id
- File d'impression : génération de tous les exemplaires sélectionnés en un job CUPS
- Fallback PDF si imprimante absente : génération d'une planche A4 de 24 étiquettes

#### Cartes membres
- Format paramétrable, premier cible : 8 cartes par feuille A4
- Contenu : nom, n° de carte (EAN13 et lisible), date d'expiration, photo (si présente), nom de la bibliothèque, langue préférée pictogramme
- Impression sur papier ordinaire en v1, à plastifier

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
- Sélecteur de langue dans l'en-tête : `set_language` natif de Django, persistance par cookie `django_language`.
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
  `{"items": [{scanned_value, scanned_at}, ...]}`.
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
  - Réponse `200` : `{session_id, accepted, duplicates, rejected}`.
  - `409 session_closed` si pas `open`.
- `POST /inventory-sessions/{id}/close` — auth requise. Body vide.
  Réponse `200` : `{session_id, state: "closed", closed_at, scans_count}`.
  Le rapport (présents/manquants/mal rangés/inconnus) reste un workflow
  librarian côté web (FEAT-010).

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
7. **Avancé** : Inventaire, Rapports, Impression, Administration (onglet regroupeur)
   - **Inventaire** : sessions + détail session (libellé UI ; app/code = `inventory`)
   - **Rapports** : sélection + génération PDF/CSV
   - **Paramètres** : sections regroupées

> **Navigation (refonte UI 2026-05-23, design OFELIA)** :
>
> - **Topbar sticky** : logo OFELIA + nom de la bibliothèque + sélecteur de langue (pill) + aide + avatar utilisateur (dropdown Mon compte / Déconnexion). Page login : topbar allégée sans avatar.
> - **Accueil** : grille de **6 grosses tuiles colorées** (Catalogue=amber, Membres=sky, Prêt=orange, Retour=olive, Réservations=blush, Avancé=forest) avec illustrations SVG multicolores 64×64 OFELIA, responsive 1→2→4 colonnes (600/900 px). Bannière scan rapide. KPIs 6 cartes.
> - **Tile strip** (pages secondaires) : bande horizontale scrollable de chips colorés sous la topbar, permettant de naviguer entre toutes les sections sans repasser par l'accueil. Chip actif = couleur de section.
> - **Page head** : chaque page secondaire affiche l'illustration SVG de la section + titre + sous-titre + bouton d'action principal.
>
> Implémentation Sprint 4 (FEAT-017) + refonte UI (design handoff 2026-05-23).

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
> - Multi-step session-based dans `apps/setup/views.py` (8 étapes : langue, identité, langues activées, superadmin, imprimante, sauvegarde, ZeroTier, démo).
> - `apps/setup/services.py:apply_wizard()` persiste les choix dans `Setting.*` (`library_name`, `box_name`, `library_identity`, `languages_config`, `printer_config`, `backup_config`, `zerotier`), crée le superadmin, génère et **hashe** la `recovery_key` (§9.3 ; clé en clair affichée une seule fois), installe les schedules django-q2 + le service Avahi, et bascule `setup_completed=True`.
> - Routes : `setup:wizard`, `setup:step`, `setup:finalize` — non préfixées par la langue (hors `i18n_patterns`).
> - Détection auto CUPS / USB / ZeroTier : **différée** (saisie manuelle en v1).



À la première connexion web (route `/setup` accessible uniquement si pas encore configuré) :
1. Choix de la langue de l'interface
2. Nom et adresse de la bibliothèque
3. Langues additionnelles à activer
4. Création du compte superadmin
5. Configuration imprimante (détection CUPS auto, ou skip)
6. Configuration clé USB de backup (détection auto, ou skip)
7. Configuration ZeroTier (skip ou saisie network ID)
8. Choix d'importer ou non un jeu de données de démo
9. Récapitulatif et génération de la `recovery_key` à imprimer

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
| Imprimante non-CUPS | Bloque les étiquettes | Fallback PDF systématique |
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
pycups
httpx
gunicorn
nginx (partagé Edubox)
Docker + Docker Compose
ZeroTier (admin)
```
