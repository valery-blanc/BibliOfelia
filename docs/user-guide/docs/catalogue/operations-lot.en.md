# Bulk operations

To save time when you have several records to modify the same way,
BibliOfelia offers **bulk operations** (or "mass actions") from the
catalog list.

## Selecting several records

Two checkboxes above the list tick everything at once:

- **Select the N visible results** — the lines of the page shown.
- **Select the N search results** — **all pages**. This one only appears when
  there is more than one page.

The number shown is the real one, so you always know how many books you are
about to change or delete.

!!! warning "Do not mix the two up"
    Ticking "visible results" only takes the current page — 25 lines. On a
    collection of several hundred books, the second checkbox is the one you
    want. Ticking one unticks the other, and ticking a single line by hand
    cancels the extended selection.

Before a deletion, the confirmation page reminds you of the total. Past 100
lines it shows only the first 100 and says how many others follow — but **all**
of them will indeed be deleted.

From the [**Catalog**](/bibliofelia/en/catalog/){ target="_blank" } page,
each record row has a checkbox on the left. Tick the records you want to process.

An action bar appears at the top, with a counter ("3 records
selected") and the available operations.

## Available operations

### Bulk assignment from the catalog

As soon as you tick a line, a bar appears above the list with drop-down menus
and an **Apply** button.

**In record mode** (the default view), two menus:

- **Category** — applied to the ticked records
- **Location** — applied to **every copy** of those records

**In copy mode** (with "Search copies" ticked), one menu:

- **Source** — applied to the ticked copies

Each piece of information is set where it belongs: the category belongs to the
book, the source to the copy.

!!! tip "“Leave unchanged” is the starting value"
    A menu left on **Leave unchanged** touches nothing. So you can change the
    category without accidentally clearing the location. To remove an
    assignment, choose **— (clear)**.

After applying, you land back on the catalog **with your filters still on**:
handy for working through several batches in a row.

### Delete selected records

For cleanup (books no longer in the library, duplicates), tick the
records and click **Delete selected records**.

!!! danger "Permanent deletion"
    Records AND all their copies are deleted. Active loans are marked
    **Lost**, active reservations are cancelled. **These deletions
    are permanent.**

    Read the confirmation message carefully before validating. Codes
    of deleted copies cannot be reused (see [Common cases: lost
    book](../faq.md#livre-perdu)).

## Tip: select all on the page

The checkbox at the top of the column selects (or deselects) all
records visible on the page. If you applied a filter (for example
"category = Obsolete"), you only select the filtered records.

!!! tip "Filter well before selecting all"
    For a bulk operation, the safest is to **filter first** to see
    only the records to process, then **select all**. You avoid
    inattention errors.
