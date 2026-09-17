# Classifications

**Classifications** file books: Youth Non-fiction, Adult Fiction, Children's
Picture books… Every record gets one, and it is what sets the default loan
period.

From [**Advanced**](/bibliofelia/en/advanced/){ target="_blank" }, open
**Classifications** to create, edit or delete them.

## The fields

- **Code** — unique identifier. For Ofelia classifications, it matches the
  classification code (`JE DOC`)
- **Name** — what librarians and readers see (e.g. "Youth Non-fiction")
- **Classification code** — what is **printed on the book's spine** (see
  below)
- **Parent classification** — to file one classification under another
- **Loan period** — in days; leave empty for the library's default

## The classifications provided

BibliOfelia ships with the **20 official Ofelia classifications**: five age
groups crossed with four document types.

| | Fiction | Non-fiction | Picture books | Comics |
|---|---|---|---|---|
| Adults | `AD FIC` | `AD DOC` | `AD ALB` | `AD BD` |
| Youth | `JE FIC` | `JE DOC` | `JE ALB` | `JE BD` |
| Teens | `ADO FIC` | `ADO DOC` | `ADO ALB` | `ADO BD` |
| Children | `EN FIC` | `EN DOC` | `EN ALB` | `EN BD` |
| Early childhood | `PE FIC` | `PE DOC` | `PE ALB` | `PE BD` |

The **code doubles as the classification code**: what is written on the book's
spine is what you see in the menu.

!!! info "The language is not part of the classification"
    An English book shelved as adult fiction goes into `AD FIC`, not into an
    "English Adults Fiction" classification. The language is set on the book's
    record and found again with the catalog's **Language** filter. One
    classification per language would multiply the rows for nothing.

## The classification code

It is the short version of the name, the one that fits on a spine label. For
"Youth Non-fiction", you write `JE DOC`.

It applies to **every** record in the classification: one entry only, and two
books of the same classification can never show two different codes.

On installation, the classifications provided get a starting code (`JE DOC`,
`AD FIC`…). You can replace them with your own: BibliOfelia will never
overwrite a code you typed in.

Once the codes are in place, print the
[spine labels](../impressions/etiquettes.md).

## Deleting a classification

**No book is deleted.** The records concerned simply end up with no
classification, and the confirmation screen tells you how many there are. You
can give them a new one with [bulk operations](operations-lot.md).

## See also

- [Bulk operations](operations-lot.md)
- [Print the labels](../impressions/etiquettes.md)
