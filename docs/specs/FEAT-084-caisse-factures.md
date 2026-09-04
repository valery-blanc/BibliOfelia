# FEAT-084 — Caisse, cotisations, amendes et factures

**Status:** DONE
**Date:** 2026-08-31

## Contexte

Demande Val (`temp.txt`, 2026-08-31) : « il faut pouvoir gérer la caisse de la
bibliothèque ». Les usagers paient une **cotisation annuelle**, des **frais
d'animation** et des **amendes** quand ils abîment ou ne rendent pas un livre.
Aujourd'hui BibliOfelia ne connaît aucun montant : rien dans les modèles, rien
à l'écran.

### Arbitrages Val (2026-08-31)

| Question | Décision |
|---|---|
| Naissance des amendes | **Manuelles uniquement.** Motif choisi dans une liste administrable, montant libre. Aucun calcul automatique, aucune amende de retard générée dans le dos d'un employé |
| Cotisation | **Montant par catégorie d'usager**, facture générée **automatiquement** à l'inscription puis à chaque renouvellement de carte |

| Devise | **Réglage par instance**, au même endroit que le fuseau horaire (`/admin/settings/`). `canaima` → **bolívar (VES)**, `grand-saconnex` → **CHF**, `sanjuan` → à choisir |

Décisions prises par défaut, faute d'indication : **nombre de décimales** déduit
de la devise (0 pour VES et MGA, 2 pour CHF, EUR, USD), **échéance des factures
à 30 jours** (réglable), **SMTP réglable avec file d'attente** pour la Box hors
ligne.

## Comportement

### État du compte, sur la fiche usager

Un encadré donne l'un de trois états :

- **À jour sur ses paiements** — aucune facture ouverte.
- **N à régler** — factures ouvertes, aucune échue. L'échéance la plus proche
  est indiquée.
- **En retard : N depuis le JJ/MM/AAAA** — au moins une facture dépassée. La
  date est celle de la **plus ancienne** échéance impayée. Le détail suit,
  ventilé par nature : cotisation, animation, amende, autre.

### Facturer

- **Cotisation** : facture émise toute seule à l'inscription et à chaque
  renouvellement, du montant porté par la catégorie de l'usager. Un montant
  nul n'émet rien — une bibliothèque gratuite ne croule pas sous des factures
  à zéro.
- **Animation, amende, autre** : le bibliothécaire crée la facture depuis la
  fiche de l'usager ou depuis la liste des factures. Chaque ligne se choisit
  dans le référentiel des tarifs (libellé + montant pré-rempli, tous deux
  modifiables) ou se saisit librement.

### Encaisser

Formulaire d'encaissement sur la facture : montant (pré-rempli au solde),
**mode** — espèces par défaut —, date, note. Un encaissement **en espèces**
crée automatiquement une **entrée de caisse**. Les paiements partiels sont
acceptés ; la facture passe à « réglée » quand le solde atteint zéro.

### Facture A4

Bouton « Facture PDF » : A4 à la charte OFELIA (logo, bordeaux `#6B2138`),
en-tête de la bibliothèque (nom + adresse des réglages), bloc destinataire
(nom + adresse de l'usager, FEAT-083), tableau des lignes, total, solde,
échéance, et la mention « Réglée le … » quand elle l'est. Rendu dans la langue
de correspondance de l'usager si elle est renseignée, sinon dans celle de
l'écran.

### Envoi par email

Bouton « Envoyer par email » sur la facture, et envoi groupé depuis le
bouclement (FEAT-086). L'email est **toujours mis en file** (`OutboundEmail`) ;
un émetteur tente ensuite de la vider. Si la Box est hors ligne, la file reste
en attente et l'écran l'affiche — rien n'est perdu, rien n'échoue en silence.
Un admin peut vider la file à la demande depuis l'écran de la caisse.

**Relances** : une facture non réglée **plus d'un jour après son échéance**
entre dans la liste des relances. Une seule relance est envoyée par facture
(`reminder_sent_at`) : le but est de prévenir, pas de harceler.

### État de la caisse

Écran accessible hors bouclement (`/finance/`) : solde, entrées et sorties sur
une période (jour par défaut), total dû par les usagers, factures en retard,
file d'emails en attente. Saisie manuelle d'un mouvement (entrée ou **sortie**,
pour une dépense) directement sur l'écran.

## Spécification technique

Nouvelle application `apps/finance`.

```
Tariff(kind, label, amount, is_active, order)      # référentiel administrable
MemberCategory.membership_fee                       # champ ajouté (FEAT-084)
Invoice(number, member, issue_date, due_date, status,
        total_amount, amount_paid, note, created_by,
        emailed_at, reminder_sent_at)
InvoiceLine(invoice, kind, label, amount, quantity)
Payment(invoice, amount, method, paid_on, note, received_by)
CashMovement(occurred_on, direction, amount, label, payment, created_by)
OutboundEmail(kind, to_address, subject, body, invoice, status,
              created_at, sent_at, error)
```

- `kind` ∈ {`membership`, `activity`, `fine`, `other`} — partagé par `Tariff` et
  `InvoiceLine`, c'est lui qui produit le détail « cotisation / amendes ».
- `Invoice.number` : `F-<année>-<séquence sur 4>`, alloué dans la transaction de
  création à partir de `Setting["invoice_seq_<année>"]`. Une facture numérotée
  ne se supprime pas — elle s'**annule** (`status="cancelled"`), sans quoi la
  numérotation devient trouée et le registre de caisse illisible.
- `total_amount` et `amount_paid` sont **stockés** et recalculés par
  `Invoice.recompute()` : le total dû de tous les usagers doit s'agréger en une
  requête, pas en parcourant les lignes de chaque facture.
- Montants en `DecimalField(max_digits=10, decimal_places=2)`. L'affichage
  applique `Setting["finance"]["decimals"]` — le stockage garde deux décimales
  quelle que soit la devise, pour ne pas perdre une donnée si le réglage change.
- `apps/finance/services.py` : `member_account()`, `create_membership_invoice()`,
  `register_payment()`, `cash_summary()`, `queue_invoice_email()`,
  `flush_outbox()`, `is_online()`.
- `apps/finance/pdf.py` : `render_invoice_pdf()` (reportlab, A4).
- Réglages : section `finance` (devise, décimales, délai d'échéance) et section
  `email` (SMTP) dans `apps/core/admin_views.py::FORMS`.

Rôles : lecture `LIBRARIAN`/`SUPERADMIN`/`READONLY`, écriture
`LIBRARIAN`/`SUPERADMIN`, référentiel des tarifs et vidage de la file
`SUPERADMIN`.

**FEAT-089** : la cotisation ne se règle plus dans `/admin/` — catégories
d'usagers et tarifs partagent l'écran `/finance/tariffs/`.

## Impact sur l'existant

- `MemberCategory` gagne un champ → migration `members`.
- `apps/members/services.py::renew_card()` émet une facture de cotisation.
- `Member.save()` (création) émet une facture de cotisation.
- Fiche usager : encadré « Compte ».
- Accueil : nouvelle tuile « Caisse » et compteur « en retard de paiement ».
