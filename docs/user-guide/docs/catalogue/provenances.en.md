# Sources

A **source** says where a copy comes from: bought by the library, given by
someone, lent by a partner library.

It belongs to the **copy**, not to the book. That matters: you may well have
two copies of the same title, one bought by Ofelia, the other lent by the
library next door.

## Creating a source

From [**Advanced**](/bibliofelia/en/advanced/){ target="_blank" }, open
**Sources**, then click **New source**.

- **Code** — short, no spaces: `OFELIA`, `BM-GE`, `DON-DUPONT`
- **Full name** — what librarians will see in lists: "On loan from Geneva
  Library"
- **Notes** — the contact, the expected return date, the terms of the
  deposit

## Assigning a source

Three ways, from the fastest to the most piecemeal:

1. **While cataloguing** — when you start a scanning batch, pick a **default
   source**: every copy in the batch will get it. That is the right method
   for a box of borrowed books.
2. **From the catalog** — tick **Search copies**, select the lines you want,
   then **Assign a source**.
3. **One copy at a time** — the **Source** field on the copy form.

The [Excel import](../inventaire/catalogage-excel.md) also accepts a
`PROVENANCE` column.

## Returning a borrowed collection

This is the case that justifies all the rest:

1. Open the [**Catalog**](/bibliofelia/en/catalog/){ target="_blank" }
2. Tick **Search copies**
3. Filter on the source concerned
4. **Select all**, then **Delete the selected copies**

You see the exact list before confirming. The copies disappear, the records
stay in the catalog.

!!! warning "Check current loans"
    The confirmation screen tells you how many of these books are out with a
    reader. Their loan will be closed as "lost" — better to get them back
    first, or wait for them to be returned.

## Deleting a source

As long as one copy still uses it, BibliOfelia **refuses** to delete it:
that would lose the only trace of where those books came from. The screen
then offers to show you the copies concerned so you can deal with them
first.

## See also

- [Manage copies](exemplaires.md)
- [Search](recherche.md)
- [Catalogue from Excel](../inventaire/catalogage-excel.md)
