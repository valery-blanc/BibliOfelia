# FEAT-086 — Bouclement de la journée

**Status:** DONE
**Date:** 2026-08-31

## Contexte

Demande Val (`temp.txt`, 2026-08-31) : « dans les menus principaux (catalogue,
membre etc.) ajouter le menu bouclement qui sert à gérer le travail des
employés et la caisse de la bibliothèque ».

Le bouclement est le **fil qui relie** FEAT-084 (caisse) et FEAT-085
(activités) : en fin de service, un employé passe par un écran unique qui lui
fait faire, dans l'ordre, tout ce qu'il ne faut pas oublier.

## Comportement

Nouvelle tuile **Bouclement** sur l'accueil, à côté de Catalogue et Membres.
L'écran présente la journée en **cinq étapes**, chacune avec son état (à faire
ou fait) :

1. **Saisir ses activités et ses animations** — renvoie vers les formulaires de
   FEAT-085, pré-datés du jour. L'étape affiche ce que l'employé connecté a
   déjà saisi aujourd'hui.
2. **Mouvements de caisse du jour** — entrées, sorties, solde, et la liste des
   encaissements de la journée (FEAT-084).
3. **Factures et relances à envoyer** — les factures jamais envoyées et les
   relances dues (échéance dépassée de plus d'un jour, jamais relancées).
   - **Instance hébergée** (BUG-043) : bouton « Envoyer maintenant », qui envoie
     tout de suite. Pas de notion de Box. Si le SMTP n'est pas configuré,
     l'écran le dit (Avancé → Paramètres → Email).
   - **Box en ligne** : bouton « Envoyer maintenant ».
   - **Box hors ligne** : la liste s'affiche pour prévenir **par téléphone** ;
     les emails restent en file et partent dès que la Box est de nouveau en
     ligne.
4. **Sauvegardes** — déclenche `apps.tasks.backup.run_backup(force_daily=True)`
   et affiche le résultat (chemin, taille, erreur éventuelle).
5. **Éteindre la Box** — voir ci-dessous.

Le bouclement n'est **pas** un verrou : un employé qui finit son service à midi
peut le faire, un autre le refera le soir. Un enregistrement `DayClosing` par
jour et par employé garde la trace de qui a bouclé quoi et quand ; les étapes 4
et 5 restent des actions de journée, pas des actions personnelles.

### Étape 5 — extinction (arbitrage Val)

Un conteneur Docker ne peut pas éteindre son hôte. Le bouton **n'apparaît que
sur la Box** (`Setting["is_box"]`, vrai quand l'instance tourne sur la Ofelia
Box) ; sur une instance hébergée — `sanjuan`, `grand-saconnex` — éteindre le
serveur n'a aucun sens et l'étape disparaît.

Sur la Box, BibliOfelia écrit un **fichier-drapeau** dans un volume partagé
(`BOX_SHUTDOWN_FLAG`, par défaut `/data/shutdown.request`). Une unité systemd
côté hôte surveille ce fichier et déclenche l'arrêt propre.

> ⚠️ **La moitié système est hors de ce dépôt.** L'unité `ofelia-shutdown.path`
> et son `ofelia-shutdown.service` sont à ajouter dans le dépôt `keebee` /
> `ofeliabox`. Tant qu'elles ne sont pas déployées, le bouton écrit son fichier
> et l'écran affiche « demande enregistrée » — mais la Box ne s'éteint pas. Le
> gabarit le dit explicitement plutôt que de laisser croire à un arrêt en cours.

## Spécification technique

```
DayClosing(closing_date, user, closed_at, activities_done, cash_reviewed,
           emails_sent, emails_queued, backup_status, backup_detail,
           shutdown_requested, note)
```

- `unique_together = (closing_date, user)`.
- `apps/closing/views.py::day_closing` : GET assemble les cinq étapes ; chaque
  action est un POST distinct (`step=emails|backup|shutdown`) — un bouclement
  n'est pas un formulaire monolithique qu'on rejoue par mégarde.
- `settings.BOX_SHUTDOWN_FLAG` + `Setting["is_box"]`.
- Détection en ligne : `apps.finance.services.is_online()`.

Rôles : `LIBRARIAN`/`SUPERADMIN`. L'extinction exige `SUPERADMIN`.

## Impact sur l'existant

- `templates/core/dashboard.html` : tuile « Bouclement ».
- `config/urls.py` : `closing/`.
- `config/settings/base.py` : `BOX_SHUTDOWN_FLAG`.
- Dépendance **externe** à créer dans keebee : unité systemd d'extinction.
