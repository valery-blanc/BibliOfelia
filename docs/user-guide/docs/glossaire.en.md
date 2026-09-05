# Glossary

Small lexicon of terms used in BibliOfelia.

## The different codes: what are they for?

BibliOfelia uses several kinds of codes to identify books and
members. It is important to distinguish them as they don't serve the
same purpose.

### Ofelia code (on labels and cards)

This is the **barcode** scanned with the scanner or OfeliaScan. It
starts with **290** for a book, or **291** for a member card. It has
13 digits total.

Examples:

- `2900000000017` → label on a book
- `2910000000444` → card of a member

It is the code BibliOfelia automatically generates when you create a
new copy or a new member. It is what is printed on physical labels
and cards. It is what is scanned for loans, returns, inventory.

Once printed, this code never changes. If a label or a card is lost,
**you don't print the same**: you create a new one with another code
(see [Lost book](faq.md#livre-perdu) and [Lost
card](faq.md#carte-perdue)).

### Internal code (on the book's record, not on the label)

Alongside the Ofelia code, each book also has a more readable
**internal code** for the librarian. It has the form
**OFL-YYYYMMDD-NNNN**:

- `OFL-20260525-0014` → 14th book entered on 25 May 2026

This code appears in BibliOfelia on the copy's record. It quickly
tells when a book was registered. It is not printed on the label, but
you **can type it** in search, lending or return — with or without
the hyphens.

### ISBN-13 (on the book cover, printed by the publisher)

This is the 13-digit code that the **publisher** prints on the back
of the book, usually next to a standard barcode. It identifies the
title universally.

Example: `9782070612758` → identifies *The Little Prince* by
Gallimard.

When you create a new record, BibliOfelia queries the OpenLibrary
database from the ISBN-13 to pre-fill the title, author and
publisher. ISBN-13 is therefore mainly used for **cataloging**, not
for daily lending.

For lending, it is the Ofelia code of the book that is scanned, **not
the ISBN** (a book can have 3 copies: they have the same ISBN, but
each has its own Ofelia code).

### ISBN-10 (old format)

Before 2007, books had a 10-digit publisher code: this is the
ISBN-10. You can find it on old books. BibliOfelia accepts both: if
you type an ISBN-10, it is automatically converted to ISBN-13.

### ISSN (magazines and journals)

The **ISSN** is the equivalent of the ISBN for **magazines and journals**.
On the barcode on the back of a magazine, it starts with **977**.

Unlike the ISBN, the ISSN identifies **the magazine's title**, not a
specific issue: every issue of the same magazine shares the same ISSN.
BibliOfelia therefore creates **a single record** per magazine, to which
each issue adds a copy. You catalog a magazine like a book, simply by
scanning its 977 barcode.

### Card number / member number

This is the Ofelia code of a member card (prefix 291). Also called
"card number" or "member number" — it's the same thing.

## Other terms

### BibliOfelia

The library management software, installed on the **Ofelia Box**.
Accessed from any computer or tablet in the library via a web
browser.

### In-library reading

A book read in the library without being borrowed (comic flipped
through, dictionary consulted for homework). Can be recorded for
statistics. See [In-library reading](prets-retours/consultation.md).

### Scanner

Barcode reader plugged via USB cable into the computer. Behaves like
a keyboard: you scan, the code appears in the input field. The
fastest tool.

### Copy

A physical instance of a book. A record can have multiple copies (for
example, 3 copies of *The Little Prince* on the shelves). Each copy
has its own Ofelia code. See [Manage
copies](catalogue/exemplaires.md).

### Location

The aisle or shelf where a book is stored. Identified by a short
code (`A1`, `YOUTH`, `BD`…). See
[Locations](catalogue/localisations.md).

### Member

A reader enrolled in the library. Has a card with a unique number.
Also called **user** or **reader**.

### Record

The descriptive entry of a book (title, author, ISBN…). Independent
of physical copies: a record can exist without a copy (book
referenced but not yet received) or with several copies (popular
book). See [Adding a book](catalogue/ajouter-livre.md).

### Ofelia Box

The small box (a Raspberry Pi mini-computer) that hosts BibliOfelia.
Plugged into the library network, it serves the app to all connected
workstations. No internet needed for it to work.

### OfeliaScan

The Android companion app for BibliOfelia. Turns a phone into a
scanner for barcodes. See [Activate
OfeliaScan](ofeliascan/activer.md).

### Fine

Amount billed **by hand** from a member profile (reason + amount).
BibliOfelia never auto-calculates an overdue fine. See
[Cash desk and invoices](caisse/caisse.md).

### Event

A session with an audience (story time, workshop). Members present
are counted (scan or last 4 digits of the card) and, separately,
non-members. See [Activities and events](caisse/activites.md).

### Closing

End of the day's service: activities, till, sends, backup, and on
the Box only shutdown. See
[End-of-day closing](caisse/bouclement.md).

### Cash desk

Register of cash in and out, distinct from bank transfers. Till
balance, invoices, email queue. See
[Cash desk and invoices](caisse/caisse.md).

### Membership fee

Annual amount carried by the **member category**, billed
automatically at enrollment and at each renewal. 0 = free. See
[Fees and member categories](caisse/tarifs.md).

### Loan

The borrowing of a book by a member, with a return date. See
[Lending a book](prets-retours/faire-pret.md).

### Inventory

Aisle check: walk the shelves and scan each book to verify it is in
the right place. See [Inventory](inventaire/recolement.md).

### Reservation

A loan request for a book currently unavailable. The member is
served first when the book returns. See
[Reservations](reservations/creer.md).
