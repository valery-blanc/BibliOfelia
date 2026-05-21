# SPEC_BIBLIOFELIA

Spécification détaillée du logiciel de gestion de bibliothèque BibliOfelia, application web auto-hébergée sur Ofelia Box (Raspberry Pi 5).

Version : 1.0 (cible v1)
Statut : draft pour Spec-Driven Development
Dernière modif spec : 2026-05-21 — FEAT-002 (modèles de données implémentés, §5 verrouillé)

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
- Conteneurisation Docker Compose, services préfixés `bibliofelia-*`
- Réseau Docker partagé `ofelia-net` avec nginx en frontal

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
| Reactivité locale | Alpine.js 3.x | Petits composants (modals, accordéons) |
| CSS | Pico.css 2.x | Classless par défaut, micro-bundle, semantic HTML |
| Icônes | Lucide static SVG | Pack libre, embarqué localement |
| Polices | Inter (latine) | OFL, légère, lisible |

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

- `bibliofelia-web` : Django + gunicorn, expose port 8001 (interne)
- `bibliofelia-worker` : django-q2 worker
- `bibliofelia-backup` : cron + script rsync vers clé USB montée

Les conteneurs partagent un volume `bibliofelia-data` (SQLite + média) et un volume `bibliofelia-backup` (clé USB).

### 4.3 Routage nginx

- `/biblio/` → bibliofelia-web (interface web)
- `/biblio/api/` → bibliofelia-web (API REST OfeliaScan)
- `/biblio/static/` → fichiers statiques (servi par nginx directement)
- `/biblio/media/` → couvertures et fichiers uploadés

### 4.4 Démarrage et migrations

À chaque démarrage du conteneur web :

1. Vérification de la connectivité à la base
2. Exécution de `manage.py migrate`
3. Création des objets par défaut si base vide (catégories, règles, langue)
4. Démarrage de gunicorn

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
- Actions proposées pour chaque divergence (réintégrer, marquer perdu, déplacer, créer notice)

#### Historique
- Conservation des sessions clôturées
- Comparaison entre récolements pour suivi de la qualité du fonds

### 6.6 Administration et rapports

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

#### Étiquettes exemplaires
- Format thermique 50x25mm (paramétrable)
- Contenu : EAN13 lisible humainement et code-barres, titre tronqué (30 caractères), code Location, internal_id
- File d'impression : génération de tous les exemplaires sélectionnés en un job CUPS
- Fallback PDF si imprimante absente : génération d'une planche A4 de 24 étiquettes

#### Cartes membres
- Format paramétrable, premier cible : 8 cartes par feuille A4
- Contenu : nom, n° de carte (EAN13 et lisible), date d'expiration, photo (si présente), nom de la bibliothèque, langue préférée pictogramme
- Impression sur papier ordinaire en v1, à plastifier

### 6.8 Notifications offline

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
- Django i18n standard pour l'interface (`.po` files)
- django-modeltranslation pour les catégories, tags, paramètres traduisibles
- Sélecteur de langue par utilisateur connecté (préférence stockée)
- Membre peut avoir une `preferred_language` distincte, utilisée pour reçus et cartes
- Aucune dépendance à un service de traduction externe : tout est figé dans les fichiers .po

#### Extensibilité
- Ajout d'une langue = ajout d'un dossier `locale/<code>/` avec les `.po`
- Documentation pour traducteurs bénévoles
- Pas de hard-code de la liste des langues : pilotée par le paramètre `enabled_languages`

### 6.10 Webservice OfeliaScan (API REST)

Base URL : `http://<box-ip>/biblio/api/v1`

Authentification : JWT, refresh tokens longue durée (90 jours) pour adapter l'usage mobile.

#### Endpoints

##### Authentification
- `POST /auth/login` : `{username, password}` retourne `{access, refresh}`
- `POST /auth/refresh` : `{refresh}` retourne `{access}`
- `POST /auth/logout` : invalide le refresh token

##### Pairing
- `GET /pairing/info` : retourne `{box_name, version, library_name}` (auth non requise pour découverte)
- `POST /pairing/claim` : associe un appareil à un compte contributeur via QR code généré par l'admin web

##### Métadonnées
- `GET /isbn/{isbn}` : lookup ISBN, retourne `{title, authors, publisher, year, language, cover_url, source, cached}` ou 404
- Comportement : cache local de la box, fallback OpenLibrary si internet, mise en file si offline avec réponse `{cached: false, pending: true}`

##### Sessions de scan (catalogage)
- `POST /scan-sessions` : crée une session de catalogage, retourne `session_id`
- `POST /scan-sessions/{id}/items` : ajoute des items scannés en batch
  - body : `[{isbn, title, authors, language, location_code, state, copy_count, scanned_at, notes}, ...]`
- `GET /scan-sessions/{id}` : statut, nombre d'items, statut de validation
- `POST /scan-sessions/{id}/finalize` : clôt la session côté Android, déclenche la file de validation côté web

##### Récolement
- `POST /inventory-sessions` : `{scope_location_id, scope_category_id, name}`
- `POST /inventory-sessions/{id}/items` : `[{ean13, scanned_at}, ...]`
- `GET /inventory-sessions/{id}/status` : compteur en temps réel
- `POST /inventory-sessions/{id}/close` : clôt côté Android, le rapport est généré côté web

##### Items
- `GET /items/{ean13}` : retourne notice + état exemplaire pour vérification scan
- `GET /search?q=...` : recherche pour autocomplétion mobile

##### Diagnostic
- `GET /health` : statut système (espace disque, version, dernière sauvegarde)
- `GET /sync/status` : queue des tâches en attente

#### Codes d'erreur et résilience
- Tous les endpoints idempotents là où c'est possible (utilisation d'`Idempotency-Key`)
- Format d'erreur : `{error: {code, message, details}}`
- Throttling : 60 req/min par token
- Pagination cursor-based sur les listes

---

## 7. Connectivité et synchronisation

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

- django-auditlog actif sur Member, BibliographicRecord, Item, Loan, Setting, User
- Conservation : 5 ans
- Export possible pour rapport ou investigation

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

1. **Dashboard** : KPIs, raccourcis vers actions fréquentes
2. **Prêt** : scan carte → scan livres → valider (workflow linéaire, gros boutons)
3. **Retour** : scan livres → valider
4. **Catalogue** : recherche + liste + détail notice/exemplaire
5. **Usagers** : recherche + liste + détail
6. **Réservations** : à honorer + en attente
7. **Récolement** : sessions + détail session
8. **Rapports** : sélection + génération PDF/CSV
9. **Paramètres** : sections regroupées

### 10.3 Mode "accès simple" vs "avancé"

Pour respecter le principe d'ergonomie pour usagers peu formés sans frustrer les avancés :

- Mode simple par défaut : les options avancées sont cachées sous des sections repliables "Options avancées"
- Possibilité par utilisateur de cocher "Toujours afficher les options avancées" dans son profil

### 10.4 Aide contextuelle

- Tooltips sur les champs
- Page d'aide dédiée par écran, accessible via icône "?" en haut à droite
- Vidéos courtes (optionnelles, externalisées plus tard)

---

## 11. Déploiement et mise en service

### 11.1 Image Docker

- Image multi-arch (arm64 pour Pi 5, amd64 pour dev et test)
- Publiée sur registry Ofelia (à définir : GitHub Container Registry ou Harbor self-hosted)
- Tags : `latest`, `vX.Y.Z`, `stable`

### 11.2 Docker Compose

Snippet à intégrer au `docker-compose.yml` d'Edubox :

```yaml
services:
  bibliofelia-web:
    image: ofelia/bibliofelia:stable
    restart: unless-stopped
    volumes:
      - bibliofelia-data:/app/data
      - bibliofelia-media:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=bibliofelia.settings.prod
      - SECRET_KEY_FILE=/run/secrets/bibliofelia_secret
    networks:
      - ofelia-net
    depends_on:
      - bibliofelia-worker

  bibliofelia-worker:
    image: ofelia/bibliofelia:stable
    restart: unless-stopped
    command: python manage.py qcluster
    volumes:
      - bibliofelia-data:/app/data
      - bibliofelia-media:/app/media
    networks:
      - ofelia-net

  bibliofelia-backup:
    image: ofelia/bibliofelia-backup:stable
    restart: unless-stopped
    volumes:
      - bibliofelia-data:/app/data:ro
      - bibliofelia-media:/app/media:ro
      - /mnt/usb-backup:/backup
    environment:
      - BACKUP_HOURLY=true

volumes:
  bibliofelia-data:
  bibliofelia-media:

networks:
  ofelia-net:
    external: true
```

### 11.3 Wizard de premier démarrage

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

- Endpoint `/biblio/api/v1/health` JSON avec métriques système
- Page admin `/biblio/admin/diagnostics` regroupant logs récents, statut backups, statut queue
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
Pico.css 2.x
python-barcode + ReportLab
pycups
httpx
gunicorn
nginx (partagé Edubox)
Docker + Docker Compose
ZeroTier (admin)
```
