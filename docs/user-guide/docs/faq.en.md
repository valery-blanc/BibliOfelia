# Frequently asked questions

## About sign-in and accounts

### I forgot my password, what should I do?

BibliOfelia works offline and does not send reset emails. Ask the
Box administrator to reset your password directly from the admin
console.

### My account is blocked after several attempts

This is protection against intrusion attempts. Wait a few minutes or
ask the administrator to unblock the account.

## About loans and returns

### Can a member borrow a book already on loan?

No. But they can **reserve** it: as soon as the book comes back, it
will be set aside for them. See [Create a
reservation](reservations/creer.md).

### How many books can a member borrow at the same time?

It depends on the member's category. By default: 5 for an adult, 3
for a child. The administrator can adjust.

### Can you lend to a member whose card is expired?

No. Renew the card first (see
[Renewal](usagers/renouvellement.md)), then register the loan.

## About the catalog

### How to add a book quickly?

If the book has an ISBN, type it in the new record form: BibliOfelia
queries OpenLibrary and pre-fills the record automatically. See [Add
a book](catalogue/ajouter-livre.md).

### What to do if the ISBN is not found?

Type the information manually. Rare but possible for very recent or
very old books.

### How to reorganize an aisle?

Run an inventory in the new location: all scanned books
will be automatically relocated. See [Inventory](inventaire/recolement.md).

## About reservations

### Can several members reserve the same book?

Yes. They are placed in a queue: the first to reserve is served
first when the book returns.

### How do I know when to notify a member?

The dashboard permanently displays a **Notifications to do** card.
See [Notifications and follow-ups](reservations/notifications.md).

## About OfeliaScan

### Do I need one phone per librarian?

Not required. You can share a phone, or use your personal Android
phone.

### Does OfeliaScan need internet?

No. It communicates with BibliOfelia via the local Wi-Fi of the
Ofelia Box. No internet connection is required for daily use.

## About languages

### Can I write a title in Malagasy?

Yes. BibliOfelia accepts all Unicode characters (accents, non-Latin
scripts). Type the title as is.

### Can the French-speaking member have a French card even though I work
in English?

Yes. When printing the card, choose the language in the selector.
You can generate PDFs in different languages without changing your
own interface language.

## About backups

### Is my data backed up?

The administrator sets up daily automatic backups on the Box. You
see **Last backup** in the **System status** panel of the dashboard.

If it's not from today or yesterday, warn the administrator.

## Difficult cases

### A book is lost or too damaged — how do I remove it? { #livre-perdu }

For a book lost during a loan: open the [member
profile](usagers/fiche.md), find the loan under **Active loans** and
click **Lost**. The loan and the copy move to status *Lost*; the
member keeps their history and can keep borrowing. For a book returned
too damaged: register the return, then on the [copy
page](catalogue/exemplaires.md) click **Discard**. To bill the
replacement, open the member profile and click **Fine** (free amount
and reason). See [Cash desk and invoices](caisse/caisse.md).

### How do I permanently delete a record from the catalog? { #supprimer-notice }

If a record no longer has any copy (all lost, given away, thrown out),
open its page and click **Delete record**, or use a [bulk
operation](catalogue/operations-lot.md). The Ofelia code of a deleted
copy stays reserved for good: a label still in circulation can never
designate another book by mistake.

### A member lost their card — what do I do? { #carte-perdue }

Open the [member profile](usagers/fiche.md) and click **Replace
card**: BibliOfelia assigns a new number, retires the old one for good
and keeps the whole history. The old card no longer works (any scan
returns an error) — destroy it if it reappears. While waiting for the
new card, the member can borrow by being looked up by name. Reprint
the card from [Print cards](impressions/cartes.md).

### How do I handle a long overdue? { #retard }

Track overdues with the **Overdue loans** counter on the dashboard and
**Reports → Overdue loans**. Depending on severity: (1) call the member
(phone shown on their profile); (2) to block their borrowing,
temporarily **deactivate** the member from their profile and reactivate
when the books come back; (3) for an overdue of several months, mark
the loan **Lost**. You can also add a **manual fine** from the
profile. BibliOfelia only emails a reminder for an overdue
**invoice** (once); for a late book without an invoice, phone or SMS
remain the most effective.

## Cash desk and email

### The membership fee is wrong after a category change

Changing category **realigns** still-open, unpaid membership
invoices. A fee already paid is not refunded. See
[Fees](caisse/tarifs.md).

### The screen talks about the Box but we are hosted (Grand-Saconnex…)

On a hosted instance, closing mentions the Box only by mistake. It
should instead say whether **SMTP** is configured. **Advanced →
Settings → Email**.

### Can I shut the server down from closing?

Only on the **Ofelia Box**, and only if the shutdown system service
is installed. On a hosted instance the step does not appear. See
[End-of-day closing](caisse/bouclement.md).

## A question not listed?

Contact your Box administrator.
