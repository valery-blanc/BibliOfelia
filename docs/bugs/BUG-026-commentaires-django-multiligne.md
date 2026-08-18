# BUG-026 — Commentaires `{# … #}` multi-lignes affichés à l'écran

**Status:** FIXED
**Date:** 2026-08-03

## Symptôme

Sur `/fr/catalog/scan/5/`, le texte suivant s'affichait en clair dans la page :

> `{# BUG-024 : la liste ci-dessous est rendue par le serveur, les scans arrivent en AJAX. Ce bouton ne sert donc qu'à recharger une liste périmée : masqué quand la liste est déjà à jour, ré-affiché par le JS au premier scan. #}`

## Cause racine

Le lexer de templates Django compile
`({%.*?%}|{{.*?}}|{#.*?#})` **sans `re.DOTALL`**. Un `{# … #}` étalé sur
plusieurs lignes n'est donc pas reconnu comme un token : il traverse le moteur
et atterrit dans le HTML rendu.

Le piège s'était déjà refermé au Sprint 9 (commentaire visible sur le dashboard).
La règle — `{# … #}` **mono-ligne uniquement**, `{% comment %}…{% endcomment %}`
pour le reste — n'était appliquée nulle part automatiquement, donc elle a été
re-violée.

## Fix appliqué

1. Les **5** commentaires multi-lignes du dépôt convertis en
   `{% comment %}…{% endcomment %}` :
   `catalog/scan_session.html` (celui vu par Val),
   `inventory/session_report.html`, `catalog/record_bulk_delete.html`,
   `errors/_error_page.html`, `500.html`. Les quatre derniers étaient des
   régressions latentes, jamais signalées.
2. **Garde-fou automatique** : `apps/core/tests/test_template_comments.py` scanne
   tous les `templates/**/*.html` et échoue si un `{#` n'a pas son `#}` sur la
   même ligne. La règle ne repose donc plus sur la mémoire.

## Section spec impactée

Aucune (défaut de présentation). Convention notée dans le test lui-même.
