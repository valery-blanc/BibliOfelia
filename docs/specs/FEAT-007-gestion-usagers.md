# FEAT-007 — Gestion des usagers

Statut : **DONE — tests écrits, non exécutés** (2026-05-21)
Sprint : 2
Task : #7 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.2

## Périmètre

### Vues (`apps/members/`)

- `member_list` — liste paginée, recherche nom / n° de carte, filtres
  catégorie / statut.
- `member_detail` — fiche : carte, expiration (alerte si < 30 jours), prêts en
  cours, membres rattachés, actions.
- `member_history` — prêts en cours, historique complet, consultations sur
  place, statistiques par catégorie de document.
- `member_create` / `member_edit` — `MemberForm`. `card_number` et
  `expiration_date` calculés par `Member.save()` ; expiration ajustable.
- `member_replace_card` / `member_renew` — actions 1 clic.

### Logique métier (`apps/members/services.py`)

- `replace_card` — nouveau `card_number`, ancien archivé dans
  `replaces_card_number`. Les cartes de remplacement puisent dans une plage de
  séquence haute (≥ 900 000 000, compteur `Setting`) pour ne jamais entrer en
  collision avec les cartes initiales (séquence = `pk`).
- `renew_card` — repousse `expiration_date` d'une période de validité (ancrée
  sur `max(aujourd'hui, expiration)` pour gérer le renouvellement anticipé) ;
  réactive une carte `expired`.
- `is_expiring_soon` / `days_until_expiration` — alerte 30 jours.
- `mark_expired_members` — passe les cartes échues en `expired`.

### Tâche planifiée

`python manage.py expire_members` — à planifier quotidiennement (django-q2).
Le `Schedule` sera créé au paramétrage (Task #15).

## Écarts / décisions

- **Compte parent** : `MemberForm.parent_account` accepte tout autre usager (pas
  de filtre sur une catégorie « collectif » — `MemberCategory` ne porte pas de
  drapeau de ce type). Suffisant pour la v1.
- **Carte PDF** (§6.2 aperçu/impression) : hors périmètre — impression Task #12.
- Le `Schedule` django-q2 d'`expire_members` n'est pas créé automatiquement —
  Task #15.

## Tests (`apps/members/tests/`)

- `test_services.py` : remplacement de carte (archivage, unicité, EAN13 valide),
  renouvellement, `mark_expired_members`, `is_expiring_soon`.
- `test_views.py` : inscription (génère la carte), création interdite en lecture
  seule, fiche, historique, recherche, renouvellement, remplacement de carte.
