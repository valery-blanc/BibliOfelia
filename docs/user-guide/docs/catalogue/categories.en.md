# Categories

**Categories** classify books: Novels, Picture books, Non-fiction… Every
record gets one, and it is what sets the default loan period.

From [**Advanced**](/bibliofelia/en/advanced/){ target="_blank" }, open
**Categories** to create, edit or delete them.

## The fields

- **Code** — short, no spaces: `ENF-ALB`, `ADU-ROM`
- **Name** — what librarians and readers see
- **Abbreviation** — the **shelf mark** printed on the book's spine (see
  below)
- **Parent category** — to file "Picture books" under "Childhood"
- **Loan period** — in days; leave empty for the library's default

## The categories provided

BibliOfelia ships with the **20 official Ofelia categories**: five age groups
crossed with four document types.

| | Fiction | Non-fiction | Picture books | Comics |
|---|---|---|---|---|
| Adults | `AD FIC` | `AD DOC` | `AD ALB` | `AD BD` |
| Youth | `JE FIC` | `JE DOC` | `JE ALB` | `JE BD` |
| Teens | `ADO FIC` | `ADO DOC` | `ADO ALB` | `ADO BD` |
| Children | `EN FIC` | `EN DOC` | `EN ALB` | `EN BD` |
| Early childhood | `PE FIC` | `PE DOC` | `PE ALB` | `PE BD` |

The **code doubles as the shelf mark**: what is written on the book's spine is
what you see in the category menu.

!!! info "The language is not part of the category"
    An English book shelved as adult fiction goes into `AD FIC`, not into an
    "English Adults Fiction" category. The language is set on the book's record
    and found again with the catalog's **Language** filter. One category per
    language would multiply the rows for nothing.

## The abbreviation, or shelf mark

It is the short version of the name, the one that fits on a spine label. For
"Teen fiction novels", you write `RO FI ADO`.

It applies to **every** record in the category: one entry only, and two
books of the same category can never show two different shelf marks.

On installation, the 16 categories provided get a starting abbreviation
(`ENF ALB`, `ADU ROM`…). You can replace them with your own: BibliOfelia
will never overwrite a shelf mark you typed in.

Once the abbreviations are in place, print the
[spine labels](../impressions/etiquettes.md).

## Deleting a category

**No book is deleted.** The records concerned simply end up with no
category, and the confirmation screen tells you how many there are. You can
give them a new one with [bulk operations](operations-lot.md).

## See also

- [Bulk operations](operations-lot.md)
- [Print the labels](../impressions/etiquettes.md)
