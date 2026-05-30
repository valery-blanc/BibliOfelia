# Lost or damaged book

When a book doesn't come back, is damaged or must leave the catalog,
you need to remove it cleanly from BibliOfelia.

## Book lost during a loan

When a member reports they have lost a book:

1. Open the [member profile](../usagers/fiche.md)
2. Find the affected loan in **Active loans**
3. Click the **Lost** button on the right of the row
4. Confirm

Consequences:

- The loan moves to status **Lost**
- The copy moves to status **Lost**
- The copy no longer appears as available
- The member no longer has this loan in their active books

The member keeps their history and can continue to borrow other
books. It is up to you to handle replacement or fees according to
your internal rules (BibliOfelia does not handle billing).

## Book damaged but recovered

If the book is returned too damaged to lend again:

1. Register the **return** normally
2. Open the [copy page](../catalogue/exemplaires.md)
3. Click **Discard**

The book stays in the catalog (for memory) but is no longer lendable.

## Permanently remove a book from the catalog

If the record no longer has any copy (all lost, given, thrown out),
you can delete the record itself:

1. Open the record page
2. Click **Delete record**
3. Confirm

Or use the [bulk operation](../catalogue/operations-lot.md) to delete
several at once.

!!! danger "The Ofelia code is never reused"
    When you delete a copy, its Ofelia code stays reserved: no other
    book will ever carry the same code in the future. This prevents a
    label still circulating somewhere (trash, donated book) from
    accidentally designating another book when scanned.

    Concretely: if the label of a deleted book is scanned later,
    BibliOfelia answers "unknown code" — and not "here is book X"
    which would be a serious confusion.

## See also

- [Manage copies](../catalogue/exemplaires.md)
- [Bulk operations](../catalogue/operations-lot.md)
