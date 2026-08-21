# Catalogue from Excel

Many libraries join the Ofelia project with a collection already typed into
an **Excel spreadsheet** (an in-house id, a title, an author, sometimes an
ISBN). **Excel cataloging** offers two tools to make use of that file:

1. **Check a file** — BibliOfelia annotates your spreadsheet with what the
   online databases know about each book, without changing anything in the
   catalog. Ideal **before** a migration, to measure the quality of the
   file and fix it by hand.
2. **Import into the catalog** — BibliOfelia turns a list of ISBNs into
   records and copies, all at once.

!!! info "Librarians only"
    Excel cataloging lives in the **Advanced** menu, available to
    librarians and administrators.

## Open Excel cataloging

From the [**Advanced**](/bibliofelia/en/advanced/){ target="_blank" } menu,
**Inventory** section, click
[**Excel cataloging**](/bibliofelia/en/catalog/excel-catalog/){ target="_blank" }.

The page shows two boxes side by side: **Check a file** (left) and
**Import into BibliOfelia** (right).

## Check a file

Use this to **review** a spreadsheet without touching the catalog.

Your file must be an **`.xlsx`** whose first row contains at least these
four columns (case and accents are tolerated):

| Column | Content |
|---|---|
| `ID` | your in-house id (kept as is) |
| `TITLE` | the book title |
| `AUTHOR` | the author(s) |
| `ISBN` | the full ISBN (10 or 13 digits) |

!!! warning "Incomplete or wrong ISBN"
    The ISBN search only accepts a **valid** ISBN (10 or 13 digits). An
    incomplete or wrong ISBN is flagged `ISBN_INVALID` and can**not** be
    used to find the book by ISBN — that is precisely the worst case. The
    `TITLE` and `AUTHOR` then save the day, through the title + author
    search: take care with those two columns.

In the
[**Check a file**](/bibliofelia/en/catalog/excel-catalog/){ target="_blank" }
box, choose your file then click **Start verification**.

BibliOfelia queries **OpenLibrary, Google Books, the BNF and the BNE**,
first by ISBN, then by title + author. Processing runs in the background:
expect about **10 minutes per 300 rows**.

When the job is finished, click **Download the annotated file**. You get
your original spreadsheet back, enriched with extra columns:

- `TITLE_FOUND_BY_ISBN`, `AUTHOR_FOUND_BY_ISBN`, `SOURCE_BY_ISBN` — what the
  ISBN made it possible to find;
- `ISBN_FOUND_BY_TA`, `TITLE_FOUND_BY_TA`, `AUTHOR_FOUND_BY_TA` — what the
  title + author search found;
- `CONFIDENCE` — a 0-to-100 score for how reliable the match is.

!!! tip "Read the colours"
    Cells with a low confidence score appear in **orange**: those are the
    rows to review by hand. An `ISBN_FOUND_BY_TA` that differs from your
    ISBN often signals a **typo** in the original file.

The check **writes nothing** to the catalog: you can run it as many times
as you need.

## Import into the catalog

Use this to actually **create** the records and copies from a list of
ISBNs.

Your `.xlsx` file must contain at least one **`ISBN`** column. Every other
column is **optional**: add only the ones you have, in any order.

| Column | Content |
|---|---|
| `ISBN` | **required** |
| `LOCATION` | the location code (otherwise the copy is created without a location) |
| `CATEGORY` | the name of an existing category |
| `TITLE` | the record title |
| `AUTHOR` | the author(s), separated by **semicolons** |
| `TYPE` | the document type (Book, Comic / manga, Magazine, Newspaper, Audio CD, Other) |
| `EDITOR` | the publisher |
| `YEAR` | the publication year |
| `LANGUAGE` | the language code (fr, en, es…) |
| `TAGS` | keywords separated by **commas** |
| `EXTERNAL_CODE` | another library's code already on the book |
| `PROVENANCE` | the code or the name of an existing source |
| `CATEGORY_ABBR` | the category abbreviation (shelf mark) |
| `CONDITION` | the copy condition (New, Good, Worn, Damaged) |

In the
[**Import into BibliOfelia**](/bibliofelia/en/catalog/excel-catalog/){ target="_blank" }
box, choose your file then click **Import into the catalog**.

Each ISBN becomes a record and a copy. If an ISBN is **already present** in
the catalog, BibliOfelia does not recreate the record: it simply adds a
copy to the existing one.

!!! info "A filled-in column replaces the record's information"
    If you add one of the columns above (title, author, publisher…) and the
    **cell is filled in**, its value **overwrites** the matching field of
    the record — **even if the record already exists**. An **empty cell
    changes nothing**: the information already in place is kept. For author
    and tags, the file's list **replaces** the existing one (it is not added
    to it). A value that is not recognised for `TYPE` or `CONDITION`, or a
    year that is not a number, is **ignored** and reported in the batch
    warnings.

The import creates a **cataloging batch**: once the job is finished, click
**View the imported batch** to open it, or find it again under
[**Cataloging by scan**](/bibliofelia/en/catalog/scan/){ target="_blank" },
exactly like a batch scanned with the camera.

!!! tip "Filling in what's missing online"
    Do you only have ISBNs, with no title or author? Then run an
    **enrichment** on the batch to fetch the metadata online (OpenLibrary,
    Google Books, BnF…). The file's columns stay authoritative: enrichment
    only fills in what is still empty.

## Track your jobs

At the bottom of the
[**Excel cataloging**](/bibliofelia/en/catalog/excel-catalog/){ target="_blank" }
page, the **Recent jobs** section lists your latest checks and imports.
Click **Details** to track progress, download an annotated file or review
the warnings row by row.

## Good to know

!!! warning "Format and limits"
    - Only **`.xlsx`** files are accepted (no `.xls`, `.csv` or `.ods`).
    - Maximum size: **5 MB**, **10,000 rows**.
    - For better ISBN coverage, a **Google Books key** can be configured by
      the administrator; without it, a quota may leave a few rows
      incomplete (column `SOURCE_BY_ISBN` = `RATE_LIMITED`). Re-run the next
      day: the quota resets every day.

## See also

- [Catalogue by scanning](catalogage-scan.md) — the same import, but with
  the camera book by book
- [Add a book](../catalogue/ajouter-livre.md) — create a single record by
  hand
