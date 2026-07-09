# SPEC_BIBLIOFELIA

Spécification détaillée du logiciel de gestion de bibliothèque BibliOfelia, application web auto-hébergée sur Ofelia Box (Raspberry Pi 5).

Version : 1.0 (cible v1)
Statut : draft pour Spec-Driven Development
Dernière modif spec : 2026-07-09 — **FEAT-055 (en test)** : **Récolement (inventaire) à la douchette USB** — le champ de saisie manuelle de la page rapport (`templates/inventory/session_report.html`, `inv-manual-form`) porte désormais `data-wedge-primary autofocus` : le wedge global (FEAT-054, `scan-wedge.js`) reconnaît une rafale HID de douchette, **remplit ce champ et soumet le formulaire** ; le handler AJAX de `scan-inventory.js` intercepte le submit et poste au même endpoint `inventory:add_scan` — pointage **sans quitter la page**, sans caméra, sans clic. Réutilise intégralement le backend, la dé-duplication, le compteur et la liste live existants. Le wedge se retire quand le modal caméra est ouvert (`scan-camera-open`) → pas de double pointage. **Corrige** le comportement pré-FEAT-055 où un scan douchette sur la page rapport (aucun champ primaire) tombait dans le fallback du wedge → `core:search?q=<code>` et **quittait** la page de récolement sans jamais pointer l'exemplaire. Aucune migration, aucune nouvelle chaîne d'app (attribut HTML seul). Guide utilisateur : section « Avec une douchette USB » ajoutée à `inventaire/recolement.md` + nouvelle page `inventaire/catalogage-douchette.md` (×4 langues). Cf. §6.5, FEAT-055. — **BUG-021 (en test)** : **Sections « Impressions » disparues de `/admin/settings/`** — FEAT-047 avait retiré `printing_cards`/`printing_labels` du registre `FORMS` (`apps/core/admin_views.py`) en les croyant redondantes, supprimant le **seul** accès UI au réglage du **format des étiquettes** (largeur/hauteur mm, lignes titre/auteur, logo) et des cartes membres. Formulaires (`MemberCardFormatForm`/`ItemLabelFormatForm`), `Setting` (`card_format`/`item_label_format`) et valeurs seed intacts → **restauration** des deux sections (registre + `settings_index.html` icônes/sous-titres). ZeroTier/Sources non restaurées (hors périmètre). 4 chaînes UI retraduites (`translations_sprint24.py`, reprises de l'historique git). Cf. §6.6, BUG-021. — **FEAT-054 + BUG-020 (en test)** : **Support douchette USB (keyboard-wedge) + catalogage douchette**. Une **douchette USB** (lecteur de code-barres en mode clavier HID) branchée sur le poste qui affiche BibliOfelia émettait ses frappes vers le champ focalisé, mais une touche de la salve (suffixe/CR) fuyait vers un raccourci navigateur → ouverture parasite de la page des téléchargements (`Ctrl+J`) — **BUG-020**. Nouveau module `static/js/scan-wedge.js` (chargé partout pour les utilisateurs connectés via `base.html`, config `#scan-wedge-config`) : écouteur clavier **global en phase de capture** qui reconnaît la signature d'un scan (rafale de frappes espacées de ≤ 35 ms, ≥ 3 caractères, terminée par `Entrée`), bufferise le code, **neutralise toute la salve** (`preventDefault`+`stopImmediatePropagation`) + fenêtre de garde 300 ms **testée en premier** dans le handler → plus aucune fuite vers les raccourcis navigateur (corrige BUG-020). Cause racine : le terminateur douchette **CR+LF** = `Ctrl+M`(Entrée) + **`Ctrl+J`(page téléchargements)** — un `<input>` texte ne consomme pas ces raccourcis, d'où la fuite même focus dans le champ. La frappe humaine (lente, irrégulière) n'est jamais captée. **Aucun clic requis** : l'écoute étant globale, le scan est capté quel que soit l'élément focalisé (2ᵉ demande Val). **Routage contextuel** du code capté : si un champ de scan primaire est présent (`input[data-wedge-primary]`, ou champ désigné par un bouton `.js-scan-handoff[data-scan-target]`) → on le remplit + submit (**prêt** carte/livre, **retour**, **catalogage douchette**) ; sinon → navigation `core:search?q=<code>` → fiche notice (290/ISBN/977) ou fiche membre (291). Le wedge se met en retrait quand le modal caméra est ouvert (`body.scan-camera-open`) et ignore textarea/contenteditable/password et les combinaisons `Ctrl/Alt/Meta`. **Catalogage douchette** : nouvelle entrée **Avancé → Inventaire → « Catalogage par douchette »** parallèle au catalogage caméra (FEAT-046), réutilisant `ScanSession`+`scan_add` — nouveau champ `ScanSession.input_mode` (`mobile`/`camera`/`douchette`, migration `catalog/0012`, défaut `camera` ; l'API OfeliaScan crée en `mobile`), route `catalog:scan_douchette_create`, hub `scan_session.html` en mode douchette (bouton caméra masqué, champ ISBN `data-wedge-primary autofocus`). Tests : 3 cas dans `test_cataloging.py`. i18n `translations_sprint23.py`. Cf. §6.1 (Recherche + « Catalogage à la douchette USB »), FEAT-054, BUG-020. — **FEAT-053 (en test)** : **Import Excel — affectation des métadonnées de la fiche** — le mode IMPORT (§6.12) reconnaît 9 colonnes optionnelles supplémentaires : `TITLE` (titre ; sur une notice neuve, évite le placeholder `ISBN:…`), `AUTHOR` (auteurs `;`-séparés, remplacement), `CATEGORY`, `TYPE` (code ou libellé FR → `DocumentType`), `EDITOR` (→ `publisher`), `YEAR` (→ `publication_year`), `LANGUAGE`, `TAGS` (`,`-séparés, remplacement, cap 10×40) et `CONDITION` (→ `Item.state`). **Sémantique** : colonne présente + cellule remplie → écrase le champ de la notice **même déjà existante** (matchée par ISBN) ; cellule vide → l'existant est conservé ; `AUTHOR`/`TAGS` remplacent sans fusionner (décision Val). Extension volontaire du périmètre FEAT-050 (qui excluait la mise à jour de notices existantes). Implémentation `apps/catalog/excel_catalog.py` : résolveurs `_resolve_document_type`/`_resolve_item_state` (alias FR normalisés via `_norm`), `_parse_row_overrides` (ne retient que les cellules non vides ; warnings `TYPE_UNKNOWN`/`CONDITION_UNKNOWN`/`YEAR_INVALID`) et **passe d'override post-finalize** `_apply_import_overrides` (transaction dédiée, via `ScanItem.processing_result` → `record_id`/`copies_created`) — `finalize_scan_session` et le flux caméra/OfeliaScan **inchangés**. Formulaire `_import_form.html` documente les colonnes ; 6 tests ajoutés (`test_excel_catalog.py`) ; i18n `translations_sprint22.py`. Cf. §6.12, FEAT-053. — **FEAT-052 (en test)** : **Support des périodiques ISSN (code-barres 977)** — les revues/magazines se cataloguent comme les livres. Nouveau helper `apps/core/issn.py` (`validate_issn`, `normalize_issn`, `issn_from_ean13` : un EAN-13 `977` + 7 chiffres + variante + clé → ISSN normalisé 8 car., ex. `9771828552248` → `1828552X`). `BibliographicRecord.issn` (nullable, **unique si non-null** → « 1 notice par ISSN » : deux numéros d'une même revue retombent sur la même notice) + propriété `issn_display` (`1828-552X`) ; `ScanKind.ISSN` ; migration `catalog/0011_issn_periodical`. Lookup ISSN multi-sources SRU **BnF** (`bib.issn`) + **BNE** (`alma.issn`) via `ISSN_SOURCES` + `lookup_issn_multi()` (OpenLibrary/Google Books n'indexent pas l'ISSN) — si rien trouvé, titre saisi à la main. `scan_add` branche le préfixe 977 → `scan_kind=issn` + `lookup_issn_multi` ; `finalize_scan_session` matche/crée par ISSN avec `document_type=MAGAZINE_ISSUE`. Formulaire notice : champ `issn` + `clean_issn` (clé validée, `NULL` si vide) ; affiché sur `record_detail`. Scanner JS : `isAcceptableCode(v, allowIssn)` — le **977 n'est accepté qu'en catalogage** (`scan-cataloging.js` passe `allowIssn:true`) ; prêt/retour/adhésion/récolement inchangés (un magazine s'y prête via son code Ofelia 290). API : `ScanKind.choices` inclut `issn` (additif ; OfeliaScan n'émet pas encore d'ISSN, contrat inchangé). **Recherche** : `classify_query` gagne un `kind="issn"` (EAN13 977 → ISSN extrait, ou ISSN saisi `1828-552X`) ; `record_list` filtre sur `issn`, `global_search` redirige vers la fiche — sinon une revue cataloguée restait introuvable. Tests : `test_issn.py` + `test_search.py` + cas 977 dans `test_cataloging.py`/`test_forms.py`. i18n `translations_sprint21.py`. Cf. §5.2, §5.3, §6.1, FEAT-052. — **BUG-019 (en test)** : **Enrichissement — titres manquants à cause du quota Google Books (429)**. L'API Google Books gratuite est plafonnée (~100 req/100 s, ~1000/jour) ; en batch l'enrichissement recevait des 429 attrapés silencieusement (`None` = « rien trouvé ») → notices laissées avec leur placeholder `ISBN:…`. Fix robustesse dans `apps/catalog/sources/google_books.py` : **throttle adaptatif** thread-safe (pleine vitesse en régime normal ; ≥ 1,2 s entre requêtes pendant ~100 s seulement après un 429, partagé verify+enrichissement) + **back-off** sur 429 (`_get_json`, 3 réessais, respecte `Retry-After`) → lève `SourceRateLimited` (nouvelle exception `apps/catalog/sources/__init__.py`) si le 429 persiste. En FILL_MISSING, `run_enrichment_job` **saute** les notices déjà complètes (titre réel + auteur, `_record_is_complete`) → re-runs rapides, quota préservé. `enrichment.py` : `_try_sources(..., with_rate_limit=True)` ; une notice sans donnée ET rate-limitée est comptée dans `EnrichmentJob.rate_limited` (au lieu de `skipped`) + entrée rapport dédiée → rejouable. `excel_catalog.py` : `_pass1_by_isbn`/`_search_all` propagent le drapeau, `run_verify_job` compte `ExcelCatalogJob.rate_limited` et marque `SOURCE_BY_ISBN=RATE_LIMITED`. Migration `catalog/0010`. UI : bandeau ambre « Quota Google Books atteint — relancez demain » sur `enrichment_detail.html` + `excel_catalog/detail.html`. Limite : quota journalier épuisé → relancer le lendemain. Cf. §6.11, §6.12, BUG-019. — **FEAT-051 (en test)** : **Filtre emplacement dans le catalogue** — la barre de filtre de `catalog:record_list` gagne un sélecteur « Tous emplacements / <code> » alimenté par `Location.objects.all()` ; sélectionner un emplacement restreint la liste aux notices ayant au moins un exemplaire dans cet emplacement (`records.filter(items__location_id=location).distinct()`). Param GET `location`, repris dans `selected.location`. **Pagination corrigée** : les liens Précédent/Suivant conservent désormais **tous** les filtres actifs (q, category, document_type, language, location, q_tag) via `base_qs` (querystring sans `page`) — auparavant seuls `q`/`q_tag` étaient préservés. Aucune migration ; 1 chaîne i18n (« Tous emplacements » → EN/ES/MG via `translations_sprint20.py`). Cf. §6.1. — **Sprint 20 / FEAT-050 (déployé Pi, en test Val)** : **Catalogage Excel** — deux outils sous **Avancé → Inventaire → Catalogage Excel** (`catalog:excel_catalog_index`, librarian + superadmin). (1) **VERIFY** : annote un `.xlsx` (colonnes `ID`/`TITLE`/`AUTHOR`/`ISBN`) avec ce que les 4 sources connaissent — passe 1 par ISBN (`_try_sources`), passe 2 par titre+auteur (`search()` ajouté à chaque source + ré-ordonnancement `rapidfuzz` `apps/catalog/sources/_fuzzy.py`, seuil 60, `CONFIDENCE` 0-100, cellules <75 en orange) — et produit un fichier annoté téléchargeable, sans effet de bord BD. (2) **IMPORT** : matérialise une colonne `ISBN` (+ `LOCATION`/`CATEGORY` optionnelles par ligne) en notices + exemplaires via une **`ScanSession` virtuelle** + `finalize_scan_session()` (pipeline FEAT-021/046). Nouveau modèle `ExcelCatalogJob` + migration `catalog/0009_excel_catalog_job` ; service `apps/catalog/excel_catalog.py` (tâche django-q2 `run_excel_catalog_job`, validation `.xlsx`/5 Mo/10 000 lignes) ; 5 vues + 5 routes `/catalog/excel-catalog/...` ; templates `templates/catalog/excel_catalog/` ; icône `file-spreadsheet.svg` ; deps `openpyxl==3.1.5` + `rapidfuzz==3.10.1`. Tests : 16 cas (`test_excel_catalog.py`), suite 362 passed ; gate i18n (`translations_sprint20.py`, 35 entrées × EN/ES/MG) → 0. Cf. §5.2 (`ExcelCatalogJob`), §6.12, Annexe B. — **Sprint 18 / FEAT-049** : **Enrichissement métadonnées ouvert aux bibliothécaires** — les vues `core:enrichment_index`/`enrichment_start`/`enrichment_detail` passent de `@require_role(SUPERADMIN)` à `@require_role(LIBRARIAN, SUPERADMIN)` et le lien « Enrichissement métadonnées » de `advanced.html` perd son garde `{% if user.is_superadmin %}` (il vit déjà dans la section `{% if user.is_librarian %}`). READONLY reste exclu (403, lien masqué). Aucune migration, aucune nouvelle chaîne i18n — cf. §6.11. Embarqué dans le commit FEAT-047 (mêmes fichiers `admin_views.py`/`advanced.html`). — **FEAT-048 (guide, en test)** : réorganisation des menus du **guide utilisateur** (`docs/user-guide/`, MkDocs Material 4 langues) — menu ramené à **8 rubriques** (Premiers pas ⊃ Accueil, Catalogue ⊃ Inventaire, Usagers, Prêts ⊃ Réservations, Impressions, Rapports, FAQ, Glossaire) ; **OfeliaScan** retiré du nav mais pages conservées (`not_in_nav: /ofeliascan/`) ; **Cas courants** réécrits en 4 Q/R « Cas difficiles » dans `faq.md` (×4 langues, ancres `attr_list` stables `#livre-perdu`/`#supprimer-notice`/`#carte-perdue`/`#retard`), 12 fichiers `cas-courants/*` supprimés, ~28 liens repointés `→ faq.md#…` ; suppression de `navigation.tabs` (top menu instable → menu latéral unique stable) ; police du menu latéral réduite (0.68rem) ; `deploy_pi.sh` gagne un fallback `tar|ssh` quand `rsync` absent (Git Bash Windows). Aucune chaîne d'app, aucune migration ; build `--strict` 0 warning, 32 pages × 4 langues, gate `i18n_check.py` → 0. — **FEAT-047 (en test)** : nettoyage UI — `/admin/settings/` allégé (retrait des sections Impressions cartes/étiquettes, ZeroTier, Sources de métadonnées + lien Comptes utilisateurs, tous redondants ou gérés ailleurs ; défauts seed conservés — cf. §6.6) ; page `/advanced/` catégorie Rapports réduite au seul lien « Tous les rapports » (les autres listes sont accessibles depuis cette page) ; icône « Emplacements » corrigée (le template appelait `map-pin` absent → nouvelle icône étagère `library.svg`, appliquée aussi à `location_list`/`location_form`/`session_report`). Aucune migration, aucune nouvelle chaîne i18n. — **Sprint 17 / FEAT-046 (en test)** : catalogage en **scan caméra continu** (lot `/catalog/scan/`, réutilise `ScanSession`/`ScanItem` + `finalize_scan_session`, `Item.catalog_session` pour l'impression ciblée des étiquettes, règle « >3 s = exemplaire supplémentaire », migration `catalog/0008` — cf. §6.1). — **FEAT-045 (en test)** : récolement en **scan caméra continu** (remplacement d'OfeliaScan pour le récolement courant ; OfeliaScan conservé pour le récolement de masse via API). `/inventory/new/` : scope réduit à *Tout le fonds* / *Un emplacement* (scope Catégorie retiré de l'UI, énum/champ conservés en base), emplacement obligatoire si LOCATION, redirige vers `/inventory/<pk>/report/?scan=1`. La page rapport devient le seul écran de pointage : bouton « Lancer/Continuer l'inventaire » (`.js-scan-inventory`) → caméra en **mode continu** (`scan-camera.js` `opts.continuous`/`onCode` : viseur permanent, bip + compteur live + cooldown 1,8 s + bouton « Terminer ») ; chaque code confirmé est posté à `POST /inventory/<pk>/scan/` (JSON `{ok, created, known, ean, item, counts}`, 409 si clôturée) ; `scan-inventory.js` met à jour compteur + liste live et recharge la page à la fermeture ; champ de saisie manuelle en repli. **Dé-dup client** (codes par exemplaire, set pré-rempli des scans en base) + **bip/vibration** sur nouvelle trouvaille + affichage « Titre — Auteur · exemplaire N » (`copy_index`) dans le viseur. **Rapport** refait : liste **par notice** triée auteur/titre, tous les codes Ofelia en pastilles vert (trouvé)/rouge (manquant) ; colonne Statut et action « Marquer perdu » retirées (endpoint `resolve_missing` supprimé). Ancienne page détail `/inventory/<pk>/` + `session_detail.html` **supprimés** (route `detail` retirée, redirections `create`/`reopen` → `report`, liste → `report`). Aucune migration. Caméra = HTTPS requis (§6.5). Traductions via `scripts/translations_sprint18.py`, gate `i18n_check.py` → 0. — **Correctifs i18n (BUG-018)** : (A) traduction plurielle EN/ES/MG de l'alerte de relance du dashboard (`blocktrans count` « N membre(s) à appeler… » dont les `msgstr[N]` étaient vides — saisie directe dans les `.po`, `apply_translations.py`/`i18n_check.py` ne couvrant pas les pluriels) ; (B) libellés du formulaire « Ajouter des exemplaires » (`ItemForm.Meta.labels` traduits via `_()` : Emplacement/État/Date d'acquisition/Source d'acquisition/Donateur/Notes — restaient en anglais faute de `verbose_name` sur `Item` ; +`format="%Y-%m-%d"` sur le `DateInput` de `acquisition_date`, même classe que BUG-015) ; (C) faux positif « En attente d'OfeliaScan… » = build périmée de la Box (handoff retiré par FEAT-044, bouton « Annuler » de la modale caméra déjà traduit Cancel/Cancelar/Foano) → rebuild ; (D) libellé Avancé→Administration Django « (réservé Claude / support distant) » → « (réservé au support technique) ». Traductions via `scripts/translations_sprint17.py`, gate `i18n_check.py` → 0. — **Sprint 16 (en test)** : FEAT-044 — scanner caméra navigateur en **mode unique** sur les 4 boutons « Scanner » du site (dashboard, prêt-carte, prêt-livre, retour). Retrait du handoff OfeliaScan de ce flux (OfeliaScan conservé pour catalogage + récolement en masse). `static/js/scan-handoff.js` réécrit (caméra = unique chemin ; échec → message d'erreur explicite + saisie manuelle, plus de redirection silencieuse) ; `templates/base.html` perd `#scan-handoff-config`, gagne 9 chaînes d'erreur dans `#scan-mode-i18n`. Routage notice/membre déjà assuré par `global_search`/`classify_query` (aucune modif serveur). Contrainte : caméra exige HTTPS (`getUserMedia`) — OK via domaine externe, KO en LAN HTTP (HTTPS local box = chantier keebee séparé). — **Sprint 15 (clos)** : guide utilisateur bibliothécaires sous forme de site statique MkDocs Material, 22 pages × 4 langues (FR/EN/ES/MG), thème OFELIA réutilisant `static/css/ofelia.css` + polices `Bricolage Grotesque`/`DM Sans` + logos `static/img/`. Captures pilotées par Playwright (24 écrans/langue, helper `capture_annotated.py` avec encadrés/pastilles pixel-perfect via `boxes_from_selectors`). Données démo enrichies (`apps/setup/demo.py::install_demo` rendu idempotent + nouvelle `install_doc_extras()` : 2 réservations PENDING + 3 prêts forcés en retard + 1 carte expirée). Commande `apps/setup/management/commands/seed_demo.py` (avec `--reset`, compte `demo_librarian` automatique). Bouton `?` de la topbar BibliOfelia branché sur `docs_url = FORCE_SCRIPT_NAME + '/docs/'` via context processor `apps/core/context_processors.py`, `templates/base.html` met `target="_blank"`, ancien `/help/` redirige 302 vers `docs_url`. Site déployé via nginx à `/bibliofelia/docs/` (volume `/var/lib/bibliofelia-docs` mounté en read-only sur le container `nginx-proxy` de keebee, location nginx déclarée AVANT `/bibliofelia/` pour ne pas être attrapée par le proxy Django). Traductions MG livrées avec bandeau d'avertissement « relecture par locuteur natif nécessaire » sur `index.mg.md`. Glossaire refondu pour distinguer ISBN-13, ISBN-10, code Ofelia (290/291), code interne (`OFL-YYYYMMDD-NNNN`), n° de membre. Termes techniques évités (FTS5/Tombstone/UTF-8 remplacés par formulations en langage simple) à la demande de Val (lecteurs cibles : bibliothécaires peu familiers du jargon informatique). — **Sprint 14 (clos)** : FEAT-043 (tombstones des codes Ofelia : nouveau modèle `RetiredItemCode` + signal `pre_delete` sur `Item` + `_assign_codes()` calcule le `MAX` en union `Item ∪ RetiredItemCode` ; un `internal_id` retiré n'est plus jamais réattribué — protège les étiquettes imprimées ; migration `catalog/0007_retired_item_codes` — §5.2 Item) ; libellé bouton catalogue « Supprimer la sélection » → « Supprimer les notices sélectionnées » et warning bulk-delete enrichi (suppressions définitives explicites — §6.1) ; sélecteur de langue : block `lang_next` overridable dans `base.html` (default `request.path_info`), override `/<lang>/catalog/` sur les pages confirm bulk POST-only → plus de 405 sur changement de langue ; pages d'erreur Ofelia génériques (400/403/404/405/500) — `templates/errors/_error_page.html` layout partagé, `templates/{400,403,404,405}.html` étendent ce layout (topbar + tile_strip vides + bouton « Page précédente » via Referer + bouton « Accueil »), `templates/500.html` standalone car `handler500` n'exécute pas les context processors ; `apps/core/middleware.py:MethodNotAllowedPrettyMiddleware` substitue toute 405 par notre template (Django ne fournit pas de `handler405`). — **Sprint 13 (clos)** : BUG-016 (sélection multiple `/catalog/` désormais disponible en version mobile — refonte `record_list.html` : un seul `<form>` enveloppe la vue desktop ET la vue mobile, cards mobiles dotées d'une checkbox leading + ligne « Tout cocher » — §6.1) ; BUG-017 (`.table-wrap` `overflow: hidden` → `overflow-x: auto / overflow-y: hidden` + `min-width: 560px` sur la table en ≤ 599 px : les tables de fiche notice/exemplaires sont désormais scrollables horizontalement en mobile — §10.1) ; FEAT-040 (exports CSV `/reports/` : catalogue complet 1 ligne/exemplaire toutes métadonnées notice sauf image, prêts+réservations en cours 2 sections `kind=loan/reservation`, inactifs usagers+exemplaires avec colonne « Dernière activité » ou « Aucune activité » sur `/reports/inactive/` — §6.6 nouveau paragraphe « Exports CSV ») ; FEAT-041 (sélection multiple `/catalog/` ouverte aux librarians ; 2 nouveaux boutons d'action de masse : « Affecter une catégorie » et « Affecter un emplacement » ; suppression reste superadmin — §6.1 paragraphe « Actions en masse ») ; FEAT-042 (`seed_defaults` fournit les 4 langues sur 16 Categories + 5 MemberCategories ; backfill idempotent : ne remplit `name_<lang>` que si vide, préserve toute traduction manuelle via /admin/ — §5.2). — **Sprint 12 (clos)** : FEAT-038 (refonte cartes membres : fond crème `rgb(248,238,229)`, logo OFELIA `static/img/ofelia-grandes-lettres.png` centré en filigrane, photo membre haut-gauche, bloc info à droite, langue bas-gauche — §6.7) ; FEAT-039 (refonte étiquettes livres : **70×42 mm par défaut** (planche A4 3×7 = 21 étiquettes), titre wrap 2 lignes 50 caractères, **auteurs wrap 2 lignes** 35 caractères/ligne, logo `static/img/ofelia-logo.png` en haut-gauche — §6.7) ; **paramétrage scindé** en 2 sections distinctes regroupées en catégorie « Impressions » : `printing_cards` (Setting `card_format`) + `printing_labels` (Setting `item_label_format`), remplaçant l'ancien formulaire `labels` unique — §6.6. Migration douce depuis ancien `label_format`. BUG-013 v2 (régression du sélecteur de langue à chaque déploiement quand l'URL courante ne se résout pas — page renommée, 404, intermédiaire) : wrapper `apps/core/i18n_views.py:set_language` qui force `FORCE_SCRIPT_NAME` sur l'en-tête `Location` ET échange le code de langue par substitution si `translate_url` n'a pas résolu — §6.9. **Gate i18n pérenne** : `scripts/i18n_check.py` exit != 0 si une chaîne EN/ES/MG manque ; intégré au workflow obligatoire (CLAUDE.md) — aucun commit sans gate vert ; 207 chaînes EN/ES/MG appliquées via `scripts/translations_sprint12.py` couvrant Sprints 10-12 + libellés `FORMS` `admin_views` enrobés `gettext_lazy` (trap : `makemessages` ignore les alias non standard). — **Sprint 11 (clos)** : BUG-015 (dates remises à 0 sur `/members/<pk>/edit/` : `forms.DateInput` rendu au format locale `25 mai 2026` incompatible avec `<input type="date">` → ajout `format="%Y-%m-%d"` aux 3 widgets dates du `MemberForm` — §6.2) ; FEAT-037 (UI fiche & édition membre : photo affichée dans le `pagehead` de `members:detail` et en miniature sur `member_form.html` ; JS recalcul `expiration_date = registration_date + 1 an` au change de `registration_date` — §6.2 nouveau paragraphe « UI fiche & édition ») ; FEAT-036 (flag `Reservation.notified_at` + endpoint `POST /loans/reservations/<pk>/notify/` ; page Réservations enrichie — code Ofelia, date+heure de réservation et de mise de côté, date limite de retrait, police 16-17 px ; cadre « Notifications à faire » sur le dashboard entre tuiles et bannière scan avec bouton Notifier direct ; migration `loans/0002_reservation_notified_at` — §6.4 nouveau paragraphe « Flag notifié », §6.6 dashboard) ; itération 2 BUG-014 (bouton hidden submit peu fiable selon navigateur → remplacé par un bouton visible **« Valider »** à côté de chaque input, plus robuste — §6.3) ; FEAT-034 (liste d'attente PENDING au niveau notice ajoutée à la fiche `catalog:record_detail` — §6.4) ; BUG-014 (saisie clavier sur `/loans/lend/` + `/loans/return/` interceptée par le scan-handoff : bouton scan repassé en `type="button"` + ajout d'un submit caché par formulaire pour permettre l'implicit submission HTML — §6.3 workflow prêt) ; FEAT-034 (UI réservations : sur fiche notice, n° de carte + nom du membre qui retient l'exemplaire + date avant retrait ; sur page Retour, section « Réservations à relancer » pour les mises de côté ≤ J+2 ; paramètres `default_loan_days`/`reservation_expiry_days`/`pickup_hold_days` exposés dans `/settings/loans/` — §6.4 nouveau paragraphe « UI et paramètres ») ; FEAT-035 (durée prêt paramétrable globalement via `Setting.default_loan_days` défaut 21 — fallback final avant la constante Python ; nouvelle section « Relances à faire » en bas du dashboard, 10 prêts les plus en retard — §6.3 ordre de priorité durée prêt, §6.6 dashboard). — **Sprint 10** : FEAT-032 (gestion des emplacements UI librarian + endpoint `GET /api/locations` lecture seule — §6.1 nouveau paragraphe « Gestion des emplacements », §6.10 nouvelle sous-section « Catalogue des emplacements ») ; pas de migration (modèle `Location` inchangé depuis Sprint 1) ; comportement OfeliaScan inchangé côté catalogage (`location_code` inconnu → silencieux), bloquant côté récolement (`scope_location_code` inconnu → 400 `unknown_location`, existant depuis FEAT-021) ; FEAT-033 (réassignation automatique des exemplaires au récolement : si `scope_type=location`, chaque scan force `item.location = session.scope_location` — UI web ET API OfeliaScan — §6.5 nouveau paragraphe « Réassignation automatique au récolement », +champ `InventorySession.relocate_count` migration `inventory/0003`) ; comportement contrat API OfeliaScan inchangé (effet de bord serveur transparent). — **Sprint 9 (suite & finalisation)** : hotfixes FEAT-031 (placeholder OfeliaScan `ISBN:<isbn> - <dd.mm.aaaa hh.mn>` language-neutral à la place de `"Sans titre — session …"` — détecté + écrasé par l'enrichissement ; sources étendues : cover image (Google Books `imageLinks`, OpenLibrary `cover.large`), summary (OL `description`/`notes`/`excerpts`, GB, BNF, BNE `dc:description`), subjects → tags (OL `subjects[].name`, GB `categories` split, BNF/BNE `dc:subject`) — cap 10 tags max, longueur 40 max, dedup ; **fusion field-by-field** entre les réponses parallèles : pour chaque champ on prend la 1re source non vide dans l'ordre préféré → summary GB en fallback si OL vide ; vue détail enrichie : `field ← source` ; affichage cover sur fiche notice ; affichage subtitle dans la carte meta ; sources en parallèle via ThreadPoolExecutor (~×4 plus rapide) ; idempotence `run_enrichment_job` + `q_options={timeout:3600, retry:7200}` pour éviter le multi-run django-q2 — §6.11) ; BUG `Item.internal_id` collision quand séquence à trous (suppression / sessions échouées) : remplacement `count()+1` → `MAX(internal_id)+1` (§5.2 Item) ; recherche ISBN/EAN13 dans `/catalog/` via `classify_query` (FTS5 ne couvre pas les ISBN) — §6.1 ; nouveau filtre **tag (icontains)** dans la barre de filtre catalogue — §6.1 ; BUG i18n sélecteur de langue : `{{ request.path }}` → `{{ request.path_info }}` (sans `FORCE_SCRIPT_NAME`) pour que `translate_url` fonctionne en prod nginx (§6.9) ; **traductions complètes EN/ES/MG** (197 chaînes appliquées, 48 fuzzy nettoyés via `scripts/apply_translations.py`) couvrant dashboard, tile_strip, lend/return/reservations/advanced, settings, enrichment, suppressions Sprint 9 — §6.9. — **Sprint 9** : FEAT-026 (suppression en masse de notices : checkboxes sur `record_list`, page de confirmation, CASCADE manuel prêts→LOST + résa→CANCELLED, superadmin uniquement — §6.1) ; FEAT-027 (suppression définitive d'exemplaire à côté de Pilonner ; prêts actifs → LOST, résa actives → CANCELLED, CASCADE prêts passés ; cas du vol et de l'erreur de saisie — §6.1) ; FEAT-028 (toggle ACTIVE ↔ SUSPENDED sur fiche membre ; check `MemberStatus.ACTIVE` ajouté dans `loans.services.check_item_loanable` ; réactivation depuis EXPIRED recalcule `expiration_date` — §6.2) ; FEAT-029 (suppression d'un membre superadmin : annule réservations, force-retourne prêts actifs, CASCADE manuel des prêts/résa/consultations, détache dépendants ; pas de migration — §6.2) ; FEAT-030 (suppression d'un user superadmin avec garde-fous : self interdit, dernier SUPERADMIN actif interdit ; auditlog préservé via FK SET_NULL existantes — §9.2) ; FEAT-031 (enrichissement multi-sources async : modules `apps/catalog/sources/{openlibrary,google_books,bnf,bne}` ; modèle `EnrichmentJob` + tâche django-q2 `run_enrichment_job` ; UI Avancé → Enrichissement avec choix mode/sources/scope ; rapport par notice — nouvelle sous-section §6.11) — FEAT-025 (refonte design global Sprint 8 : 23 templates métiers harmonisés sur le design system OFELIA — pagehead inline, tilestrip de navigation contextuelle, `.table-wrap`/`.table` stylées, boutons `.btn` arrondis 44 px, `.card`/`.list-row` partout ; ajout helpers form `.advanced-section`/`.isbn-row`/`.form-control`/`.help-hint`/`.field-error`/`.req`/`.form-actions` à ofelia.css ; `_field.html` migré de `.form-row` vers `.field` — §10.1/§10.2) ; FEAT-024 (scanner caméra navigateur : mode alternatif au handoff OfeliaScan, lib `html5-qrcode` locale, toggle utilisateur device-scoped en localStorage, contrainte HTTPS — §6.10 nouvelle sous-section « Scanner caméra navigateur ») ; FEAT-023 (handoff single-scan OfeliaScan : nouveaux endpoints `/scan-handoff` + `/scan-handoff/{token}` ; modèle `ScanHandoff` ; deep-link `ofeliascan://scan-one` ; boutons « Scanner » des pages prêt/retour/dashboard câblés ; CSRF + polling 700 ms ; TTL 5 min — §6.10 nouvelle sous-section « Handoff single-scan ») ; Refonte UI design OFELIA (§3.2 Frontend, §10.2 Navigation/Écrans : tuiles, tile strip, page head, polices Bricolage Grotesque/DM Sans, ofelia.css, logo OFELIA) ; FEAT-021 (API scan-sessions + inventory-sessions : contrat aligné sur le client OfeliaScan — corps `{"items":[...]}`, champs `scanned_value`/`metadata_*`/`item_state`, idempotency `local_id`, finalize sync = create-or-add-copies, ownership contributor_api — §6.10) ; FEAT-020 (intégration keebee : déploiement sur la Ofelia Box via le wizard keebee, clone + build sur la Pi, routage nginx `/bibliofelia/`, réglage `SECURE_COOKIES`, statique servi par nginx — §4, §11) ; FEAT-018 (terminologie UI : l'EAN13 interne d'un exemplaire est nommé « code Ofelia » dans toute l'interface ; rapport d'inventaire enrichi du code Ofelia et de l'ISBN — §5.2/§6.5/§6.7) ; Sprint 4 : FEAT-011 (dashboard enrichi §6.6 + rapports + paramètres + gestion comptes), FEAT-012 (impression étiquettes + cartes §6.7), FEAT-013 (notifications offline §6.8), FEAT-014 (sauvegardes §8 + planification django-q2), FEAT-015 (wizard premier démarrage §11.3 + données démo §11.4), FEAT-017 (onglet « Avancé » + page Connexion OfeliaScan + « Mon compte » §6.6/§6.10/§10.2), BUG-006 (i18n : `accounts/` déplacé sous `i18n_patterns` + chaînes EN/ES/MG complétées) ; Sprint 3 : FEAT-016 — API OfeliaScan (§6.10 : auth JWT, /pairing/info, /isbn/{isbn}, /health) ; FEAT-019 — publication mDNS via service Avahi sur l'hôte (§6.10) ; SPEC-CORR-002 — /pairing/info renvoie `base_url` (URL absolue) ; Sprint 2 : FEAT-005 à FEAT-010 (§6.1 à §6.5, §10) ; i18n 4 langues (§6.9) ; BUG-002 à BUG-005 ; §6.10 réécrit comme contrat d'API (SPEC-CORR-001)

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

**Non-réutilisation des codes Ofelia (FEAT-043)** : un `internal_id` (et l'EAN13 dérivé) imprimé sur une étiquette physique ne doit jamais être réattribué à un nouvel exemplaire. À chaque suppression d'`Item` (unitaire, bulk-delete, CASCADE depuis `BibliographicRecord`, admin), une ligne est insérée dans `RetiredItemCode` (tombstone : `internal_id` PK, `ean13`, `record_title_snapshot`, `retired_at`, `retired_by`, `reason ∈ {item_delete, bulk_delete}`) via un signal `pre_delete`. `Item._assign_codes()` calcule le `MAX(internal_id)` du jour en **union `Item ∪ RetiredItemCode`** ; un code retiré n'est donc jamais réattribué, même si tous les items du jour sont supprimés. Migration `catalog/0007_retired_item_codes`.

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
- Bouton "Imprimer étiquette(s)" qui envoie au CUPS

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

#### Recherche
- Barre de recherche globale sur toutes les pages
- Full-text via FTS5 sur titre, sous-titre, résumé, auteurs
- Recherche exacte sur ISBN (13 ou 10) si la requête ressemble à un ISBN
- Recherche exacte sur EAN13 d'exemplaire ou n° de carte membre
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
- Pagination (25/page) : les liens Précédent/Suivant conservent **tous** les filtres actifs (FEAT-051). La vue expose `base_qs` = querystring courante privée de `page` (`request.GET.copy()` → `pop('page')` → `urlencode()`) ; le template construit `?{{ base_qs }}&page=N`. Avant FEAT-051, seuls `q` et `q_tag` étaient repris (les sélecteurs catégorie/type/langue/emplacement étaient perdus au changement de page).

#### Modification et suppression
- Édition libre de notice et exemplaire pour bibliothécaires
- **Pilonner un exemplaire** (`item_discard`) : passage du statut à `DISCARDED`, exemplaire conservé en base. Cas d'usage : livre abîmé sortant du fonds. Bloqué si statut `ON_LOAN` ou `RESERVED_FOR_PICKUP`.
- **Supprimer définitivement un exemplaire** (FEAT-027 — `item_delete`) : DELETE hard. Cas d'usage : doublon, EAN13 mal saisi, vol. Aucun blocage : si l'exemplaire est prêté, le prêt actif passe à `LoanStatus.LOST` (`return_date=now`) ; si réservé, la réservation correspondante passe à `CANCELLED` ; les prêts passés sont supprimés en cascade (CASCADE manuel car `Loan.item=PROTECT`). Bouton à côté de "Pilonner" sur la fiche notice. Rôle librarian + superadmin.
- **Supprimer une notice** (`record_delete`) : interdite si exemplaires actifs (AVAILABLE / ON_LOAN / RESERVED / IN_REPAIR), sinon DELETE en cascade.
- **Suppression en masse** (FEAT-026 — `record_bulk_delete`) : checkboxes sur `record_list.html` (visibles librarian + superadmin depuis FEAT-041) + barre d'action sticky. Bouton « Supprimer » réservé au superadmin → page de confirmation listant pour chaque notice le nombre d'exemplaires, de prêts actifs et de réservations actives impactés. Aucun blocage : prêts actifs → `LOST`, résa actives → `CANCELLED`, puis suppression en transaction unique (Item.record=CASCADE).
- **Actions en masse — catégorie / emplacement** (FEAT-041, Sprint 13) : la même barre d'action expose 2 boutons supplémentaires accessibles aux librarians :
  - « Affecter une catégorie » → page de confirmation avec sélecteur de `Category` (option vide = retirer la catégorie) → `BibliographicRecord.objects.filter(pk__in=ids).update(category_id=...)`.
  - « Affecter un emplacement » → page de confirmation avec sélecteur de `Location` (option vide = retirer l'emplacement) → `Item.objects.filter(record_id__in=ids).update(location_id=...)` : tous les exemplaires des notices sélectionnées sont déplacés en un seul UPDATE.
  Les exemplaires DISCARDED/LOST ne sont pas exclus (réorganisation libre).
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
> - CUPS : `pycups` (installé uniquement dans l'image Linux Docker, optionnel) ; `submit_to_cups(pdf)` retourne `sent=False` silencieusement en dev Windows, le PDF est servi en fallback.
> - Routes : `printing:labels`, `printing:labels_pdf`, `printing:labels_send`, `printing:cards`, `printing:cards_pdf` (rôle LIBRARIAN/SUPERADMIN).
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
- File d'impression : génération de tous les exemplaires sélectionnés en un job CUPS
- Fallback PDF si imprimante absente

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
| `google_books`   | `google_books.py`       | Clé API obligatoire (Google Cloud, gratuite). Couverture mondiale. |
| `bnf`            | `bnf.py` (SRU XML)      | Sans clé. Spécifique livres francophones.                       |
| `bne`            | `bne.py` (SRU Alma XML) | Sans clé. Spécifique livres hispanophones.                      |

Chaque module expose `lookup(isbn) -> dict | None` (clés normalisées :
`title`, `subtitle`, `authors_text`, `publisher`, `publication_year`,
`language`, `summary`, `subjects` (list), `cover_url` (str)). Les sources
SRU (BNF, BNE) ne renvoient pas de `cover_url`.

**Champs alimentés par l'enrichissement :**
- Texte/scalaires : `title` (écrase aussi le placeholder OfeliaScan `ISBN:<isbn> - <dd.mm.aaaa hh.mn>`), `subtitle`, `publisher`, `publication_year`, `language`, `summary`.
- Auteurs : split `;` côté source → `Author.get_or_create(full_name=…)` + `record.authors.add(…)`. En FILL_MISSING : seulement si pas d'auteur. En OVERWRITE : `record.authors.clear()` puis re-création.
- Tags (depuis subjects) : cap **10 max par notice**, longueur **≤ 40 caractères**, dedup insensible à la casse. En FILL_MISSING : seulement si la notice n'a aucun tag. En OVERWRITE : `record.tags.clear()` puis ajout.
- Cover : téléchargé via httpx (timeout 10s, **max 2 MB**, follow_redirects), stocké dans `record.cover_image` → `media/covers/<isbn>.jpg`. En FILL_MISSING : seulement si pas de cover. En OVERWRITE : remplace.

**Configuration** : `Paramètres → Sources de métadonnées` (`MetadataSourcesForm`,
section `sources` dans `core:settings_index`) — toggle on/off par source +
champ pour la clé Google Books (persistance dans `Setting["metadata.sources"]`
et `Setting["metadata.google_books_api_key"]`).

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
   `category` résolue par `name__iexact` (warning si inconnu). ISBN invalide →
   ignoré + `errors++` + entrée `report`. Les overrides FEAT-053 de la ligne
   sont mémorisés (indexés par `local_id`).
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
openpyxl (catalogage Excel FEAT-050)
rapidfuzz (matching titre+auteur FEAT-050)
pycups
httpx
gunicorn
nginx (partagé Edubox)
Docker + Docker Compose
ZeroTier (admin)
```
