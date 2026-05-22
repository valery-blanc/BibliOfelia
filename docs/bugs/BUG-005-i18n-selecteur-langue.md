# BUG-005 — Le sélecteur de langue ne traduit pas l'interface

**Statut** : FIXED
**Date** : 2026-05-22
**Sprint** : 2 (signalé par Val au test de fin de sprint)

## Symptôme

Changer de langue ne traduisait que les dates ; tout le texte de l'interface
restait en français.

## Causes (deux)

1. **Catalogues vides** : les fichiers `locale/{en,es,mg}/LC_MESSAGES/django.po`
   ne contenaient aucune traduction (chaînes du Sprint 2 jamais extraites, et
   en/es/mg jamais remplis). Sans `msgstr`, gettext affiche le `msgid` source
   (français).
2. **Routage** : `config/urls.py` utilisait `i18n_patterns(...,
   prefix_default_language=False)`. Avec ce réglage, Django **force** la langue
   par défaut sur toute URL sans préfixe de langue ; le cookie de préférence et
   l'en-tête `Accept-Language` sont ignorés. Seules les URLs `/en/…`, `/es/…`,
   `/mg/…` pouvaient afficher une autre langue.

## Fix

1. `makemessages` puis traduction complète de `en.po`, `es.po`, `mg.po`
   (303 chaînes chacune). Le malgache est une première passe à faire relire par
   un locuteur natif (mention en en-tête du fichier).
2. `prefix_default_language=True` : toutes les URLs portent un préfixe de langue
   (`/fr/…`, `/en/…`). Le cookie et le sélecteur sont alors respectés partout,
   y compris sur la page de login ; la racine `/` redirige vers `/<langue>/`.

## Section spec impactée

§6.9 (Multilingue) — réécrite : les 4 langues sont livrées traduites ; le
routage passe en `prefix_default_language=True`. Voir aussi FEAT-005.
