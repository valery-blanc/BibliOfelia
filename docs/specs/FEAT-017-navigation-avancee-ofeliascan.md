# FEAT-017 — Navigation « Avancé » + page Connexion OfeliaScan

Statut : DONE (validé Val 2026-05-22)
SPEC : §6.6, §6.10, §10.2

## Contexte

Après le test fonctionnel de Sprint 4 par Val, deux constats :
1. Les nouvelles routes (rapports, impression, paramètres, comptes) n'avaient
   aucun point d'accès dans le menu.
2. Il manquait une page pour gérer les identifiants par lesquels
   l'application mobile OfeliaScan se connecte à la box.

## Implémentation

### Onglet « Avancé »

- `core:advanced` (`apps/core/views.py:advanced_index`) + template
  `templates/core/advanced.html` : page index regroupant tous les outils
  hors-workflow, chaque lien accompagné d'une phrase d'explication.
- Sections, dans l'ordre : **Impression**, **Rapports**, **Inventaire**,
  **Administration**. Impression et Inventaire sont réservés aux
  bibliothécaires (`user.is_librarian`), Administration aux superadmins.
- Entrée « Avancé » ajoutée à la barre de navigation principale.

### Réorganisation de la navigation

- **Barre principale** : suppression de « Tableau de bord » (doublon avec le
  logo qui pointe déjà vers `core:dashboard`) et de « Récolement »
  (désormais accessible via Avancé → Inventaire). Icône du logo :
  `book-open` → `house` (nouveau SVG `static/icons/house.svg`).
- **Menu utilisateur (haut-droite)** : suppression de « Mode avancé/simple »
  et de « Administration ». Ajout de « Mon compte » → page d'édition du
  compte courant. Nouveau SVG `static/icons/user.svg`.
- La vue/route `core:toggle_advanced` (bascule simple/avancé, SPEC §10.3)
  existe toujours mais n'est plus surfacée dans l'UI.

### « Mon compte » — auto-édition

`accounts:user_edit` accepte désormais, en plus des superadmins, tout
utilisateur éditant **son propre** compte (lien « Mon compte »). En
auto-édition non-superadmin, `UserAdminForm(self_edit=True)` masque les
champs `role` et `is_active` : **aucune escalade de privilège possible**.
`clean()` ne touche à `is_superuser` que si le champ `role` est présent.
Après sauvegarde, un non-superadmin est redirigé vers le dashboard (la
liste des comptes lui est interdite).

### Renommage « Récolement » → « Inventaire »

Libellé visible uniquement (templates `inventory/`). Le code, l'app
`inventory` et les modèles `InventorySession`/`InventoryScan` conservent
leur nom. « Rapport de récolement » → « Rapport d'inventaire », etc.

### Page Connexion OfeliaScan

- `core:ofeliascan` (`apps/core/admin_views.py:ofeliascan_access`) +
  template `templates/core/admin/ofeliascan.html`. Accès SUPERADMIN.
- **Adresse de la box** : nom d'hôte, IP locale (détectée via socket
  UDP — ne transmet rien), hôte courant, chemin de l'API. Sert de
  secours quand la découverte mDNS échoue.
- **Identifiants autorisés** : liste des comptes de rôle
  `contributor_api` que l'API accepte (`POST /auth/login`). Création
  (login + mot de passe, généré par défaut) et révocation
  (`is_active=False` → SimpleJWT refuse l'authentification au prochain
  appel).
- Stockage : `Setting["ofeliascan_credentials"]` = liste
  `[{username, password, created_at}]`. **Le mot de passe est conservé
  en clair** (cf. décision ci-dessous).

## Décisions

- **Mot de passe OfeliaScan en clair** : demande explicite de Val. Le
  bibliothécaire doit pouvoir relire le couple login/mot de passe pour le
  saisir sur le terminal mobile (modèle « mot de passe Wi-Fi affiché sur
  le routeur »). Contexte : box hors-ligne, et le rôle `contributor_api`
  n'a que les droits de catalogage (add/view) — faible privilège. Le
  compte Django garde malgré tout un mot de passe **haché** (Argon2) :
  c'est lui que `POST /auth/login` vérifie. Le clair n'est qu'une copie
  de commodité dans `Setting`.
- **Réutilisation d'un username existant** : refusée si le compte
  existant n'est pas déjà `contributor_api` (évite de convertir par
  erreur un compte bibliothécaire en compte API).
- **« Mon compte » pointe vers `user_edit`** (et non une vue dédiée) :
  une vue, un template, avec un formulaire restreint en auto-édition.
  Évite de dupliquer le formulaire de compte.
- **`toggle_advanced` conservé** : la bascule mode simple/avancé
  (SPEC §10.3) reste fonctionnelle côté modèle (`User.always_show_advanced`)
  mais sans entrée de menu — Val a jugé l'entrée redondante avec le
  nouvel onglet « Avancé ». Réintroduire un contrôle ailleurs reste
  possible sans changement de modèle.

## i18n

`makemessages -a` + traduction des 33 nouvelles chaînes. État :
**545 chaînes / 0 fuzzy / 0 untranslated** par locale (`en/es/mg`).

## Vérification

- `manage.py check` : 0 issue.
- pytest : 139 passed (aucune régression).
- Test fonctionnel Val : OK (2026-05-22).
