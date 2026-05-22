# FEAT-015 — Wizard premier démarrage + données démo

Statut : DONE (validé Val 2026-05-22)
SPEC : §11.3-11.4

## Contexte

Au tout premier accès web (route `/setup/`), un wizard 8 étapes guide
le bibliothécaire : choix de la langue, identité, langues activées,
création du superadmin, imprimante, sauvegarde, ZeroTier, données démo
optionnelles. À la sortie, génération d'une `recovery_key` à imprimer
(SPEC §9.3) et passage à `Setting.setup_completed = True` (le middleware
`SetupRequiredMiddleware` ne redirige plus).

## Implémentation

### `apps/setup/forms.py`

8 formulaires `Step1..Step8` (chacun simple, validation Django standard +
`password_validation.validate_password`). `Step3LanguagesForm` valide que
la langue par défaut fait partie des langues activées.

### `apps/setup/views.py`

- `wizard_index` : redirige vers `step1` si pas encore setup, sinon page
  « déjà installé ».
- `wizard_step(step)` : multi-step session-based. Données accumulées dans
  `request.session["setup_wizard_data"]` (un dict `{stepN: cleaned_data}`).
  Step1 active immédiatement la langue choisie (`activate()` +
  `django_language` cookie).
- `wizard_finalize` : vérifie que les étapes obligatoires (2, 3, 4 :
  identité, langues, admin) sont présentes, applique via
  `services.apply_wizard`, vide la session, affiche
  `templates/setup/completed.html` avec la `recovery_key`.

### `apps/setup/services.py:apply_wizard(session_data)`

Applique en transaction :
1. `Setting.library_name` / `box_name` / `library_identity`.
2. `Setting.languages_config` (pris en compte au prochain redémarrage —
   `LANGUAGES` Django reste piloté par l'ENV pour l'instant).
3. Création / mise à jour du superadmin avec
   `is_superuser=True` et le mot de passe haché.
4. `Setting.printer_config`, `backup_config`, `zerotier`.
5. Génération de la `recovery_key` (32 chars groupés `XXXX-XXXX-...`),
   stockage du **hash** uniquement (`Setting.recovery_key_hash`).
6. Installation optionnelle des données démo (50 notices, 80 exemplaires,
   20 usagers, jusqu'à 15 prêts).
7. Appel idempotent à `setup_schedules` (django-q2 cf. FEAT-014) et à
   `generate_avahi_service` (lève le blocage du wizard sur Task #19).
8. `Setting.setup_completed = True`.

### `apps/setup/demo.py`

- `install_demo()` : crée des objets marqués `notes='[DEMO]'` /
  `summary='[DEMO]'` / `description='[DEMO]'` selon le modèle. Idempotent
  via `get_or_create` sur Author/Location, et 50/80/20/15 fixes pour les
  autres (un re-install ne crée pas de doublons silencieux car aucun
  identifiant naturel n'est forcé — c'est intentionnel pour tester le
  bouton « réinstaller »).
- `remove_demo()` : supprime les objets dont le marqueur correspond.
- Commande `python manage.py remove_demo`.

### Templates (`templates/setup/`)

- `step.html` : forme générique multi-étapes avec progress bar et boutons
  Précédent/Continuer. Pas de `{% extends "base.html" %}` pour rester
  fonctionnel même quand l'authentification n'est pas encore en place.
- `completed.html` : message de succès + bloc avec la `recovery_key`
  imprimable (`window.print()`) + lien vers `/accounts/login/`.
- `already_done.html` : protection si on revient sur `/setup/` après
  installation.

### Décisions

- **Multi-step session-based** (pas `django-formtools.WizardView`) :
  garde le code lisible, suffisant pour 8 étapes et ne tente pas de gérer
  un fichier `wizard.json` ou un cache externe (cohérent avec le
  contexte offline).
- **Recovery key** : générée en hex/uppercase, **uniquement le hash est
  stocké** (la clé en clair n'est affichée qu'à la fin du wizard). La
  procédure d'utilisation côté CLI sera implémentée à part (Task hors
  Sprint 4).
- **Wizard relancable** : `wizard_index` réinitialise la session, donc
  une session incomplète peut être abandonnée et reprise à zéro.
- **CUPS / USB / ZeroTier** : le wizard collecte les paramètres et les
  écrit dans `Setting`. La **détection automatique** des périphériques
  (mentionnée par la SPEC) est différée — l'utilisateur saisit les
  valeurs à la main pour l'instant. Pas bloquant pour la v1 : le wizard
  v1 sert surtout à créer le superadmin et la `recovery_key`.
- **Démo idempotente** : marqueur `[DEMO]` dans `notes` / `summary` pour
  cleanup propre. Pas de fixture YAML — code Python plus simple à faire
  évoluer.
