# FEAT-035 — Durée de prêt paramétrable + relances en bas du dashboard

**Status:** DONE
**Date:** 2026-05-25

## Context

Demande Val (temp.txt) : « Expirations des prêts 3 semaines paramétrable. Affichage de la liste des relances à faire en bas de la home page. »

Aujourd'hui :
- `apps/loans/services.py` calcule la `due_date` via `compute_due_date` qui regarde la `Category.default_loan_duration_days` puis `MemberCategory.default_loan_duration_days`, et tombe sur la constante Python `DEFAULT_LOAN_DAYS = 21` si rien n'est défini. Aucun `Setting` global ne pilote la valeur par défaut.
- Le dashboard affiche déjà un KPI « Prêts en retard » mais aucune liste actionnable.

## Behavior

### Setting global `default_loan_days`

- Nouveau réglage `default_loan_days` (entier, défaut 21).
- `compute_due_date` l'utilise comme **dernier fallback**, avant la constante Python (qui reste comme ultime garde-fou).
- Exposé dans le formulaire des paramètres `reservations` (cf. FEAT-034) ou dans une section dédiée — voir choix d'implémentation.

### Relances à faire (dashboard)

Nouvelle section en bas de `templates/core/dashboard.html`, sous « Top 10 + État système », visible des `librarian` / `superadmin` uniquement.

- Titre : « Relances à faire ».
- Liste des prêts `ACTIVE` ou `OVERDUE` dont `due_date < today`, triée par ancienneté de retard décroissante.
- Colonnes : titre, membre (lien fiche), date d'échéance, nombre de jours de retard.
- Cap visuel : 10 lignes max + lien « Voir tout » vers la page existante `/loans/return/` (qui liste déjà les prêts en retard).

## Technical spec

1. **Setting** : `default_loan_days` ajouté à `seed_defaults` (rétrocompatible : `Setting.get("default_loan_days", 21)` en lecture).
2. **Helper** : `apps/loans/services.py:_setting_int("default_loan_days", DEFAULT_LOAN_DAYS)` utilisé en fallback dans `compute_due_date`.
3. **Formulaire** : champ ajouté au `ReservationDefaultsForm` de FEAT-034 (un seul écran « Durées prêts & réservations »).
4. **Dashboard** : `apps/core/views.py:dashboard` injecte `reminders = Loan.objects.filter(status__in=open, due_date__lt=today).select_related("item__record", "member").order_by("due_date")[:10]`. Template ajoute la section.

## Impact on existing code

- `apps/loans/services.py` : `compute_due_date` lit le Setting
- `apps/core/forms.py` : champ ajouté au formulaire réservations (renommé `LoanReservationDefaultsForm`)
- `apps/core/views.py` : `dashboard` injecte `reminders`
- `templates/core/dashboard.html` : nouvelle section
- `apps/core/management/commands/seed_defaults.py` : nouvelle clé
- `SPEC_BIBLIOFELIA.md` §6.3 + §6.6 : durée paramétrable, dashboard enrichi
