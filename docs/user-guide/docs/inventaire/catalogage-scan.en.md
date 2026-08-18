# Catalogue by scanning

When a crate of books arrives, **scan cataloguing** is the fastest way to
record everything: you scan the ISBNs one after another with the camera,
and BibliOfelia creates the records and their copies in one go.

It is, for creation, the equivalent of [inventory](recolement.md)
for checking: a **continuous scan**, with nothing to click between two
books.

## What a cataloguing session is for

A cataloguing **session** (also called a **batch**) is how you add **many books
at once** to the catalogue. It works in three steps:

1. **You open a batch and scan** every book in the crate, one after another.
   Nothing enters the catalogue yet: the batch is only a working list, which you
   can correct or empty.
2. **You check the list** — and above all, you apply **batch changes**: tick
   several rows (or all of them) and assign them, in a single click, the same
   **category**, the same **location** in the library or the same **condition**.
   That is the whole point of cataloguing together books that belong together.
3. **You send the batch to the catalogue**: records and copies are created for
   real, and you can print the labels **for that batch only** in one go.

A validated batch stays available: from the list of batches, **View batch**
shows which books it contained, with a link to each record.

## Start a cataloguing batch

From the [**Catalogue**](/bibliofelia/en/catalog/){ target="_blank" } (or
[**Advanced**](/bibliofelia/en/advanced/){ target="_blank" } → Inventory),
click
[**Catalogue by scanning**](/bibliofelia/en/catalog/scan/){ target="_blank" },
then [**New batch**](/bibliofelia/en/catalog/scan/new/){ target="_blank" }.

Before scanning, you can set **default values** for the whole batch:

- a default **category** (Adults, Youth…);
- a default **location** (the shelf these books will go to);
- a **label** to find the batch again later.

These values apply to every book in the batch, but you can **change them
line by line** afterwards.

## Scan the ISBNs in a row

1. Click **Start scanning**: the camera opens in continuous mode.
2. Scan the ISBN barcode on the **back** of each book (it starts with 978 or
   979).
3. On each read, a **beep** confirms and the line appears in the list:
   BibliOfelia automatically looks up the title, author and language
   (OpenLibrary, Google Books, BnF…).
4. While scanning, the screen shows the **title and author** found — or,
   failing that, the ISBN and language.

!!! tip "Several copies of the same book"
    Got two identical copies? Scan the same ISBN **twice**. On the second
    pass (after a few seconds), BibliOfelia shows "copy 2" in large type: it
    will add an extra copy to the same record, without creating a duplicate.
    A re-scan that is too quick (less than 3 seconds) is ignored, to avoid
    double reads.

!!! warning "Ofelia codes rejected"
    Cataloguing accepts book **ISBNs** (978/979) and magazine **ISSNs**
    (977, see below). If you mistakenly scan an Ofelia code label (290/291)
    already on a document, it is rejected: here you record new documents,
    not copies that are already catalogued.

## Cataloguing a magazine or journal

Magazines and journals have no ISBN, but an **ISSN**: a barcode that starts
with **977**. No separate tool needed — scan that 977 barcode **in the same
batch** as your books.

- BibliOfelia recognises the ISSN and looks up the **magazine's title**
  (BnF, BNE).
- All issues of the same magazine share the **same ISSN**: they therefore
  land on a **single "magazine" record**, to which each scanned issue adds a
  copy.

!!! info "One ISSN = a single magazine record"
    If you scan two different issues of the same magazine, BibliOfelia does
    not create two records: it adds a copy to the magazine's record. To tell
    the issues apart (date, number), note them in the copy's notes.

## Check and adjust the batch

When you press **Finish**, the batch list appears. For each line, you see
the book found (author, title, language) and you can:

- change the **category**, **location** or **condition** — per line, or for
  several lines at once using the checkboxes and the **Select all** button;
- adjust the **number of copies**;
- **delete** a line (trash icon) in case of a scan error.

!!! info "Record already exists"
    If an ISBN matches a book **already present** in the catalogue,
    BibliOfelia does not recreate the record: it simply adds your new copies
    to the existing record, without changing it.

## Save the batch

Click **Save the batch**. BibliOfelia creates all the missing records and
all the copies, with their Ofelia codes.

## Print only this batch's labels

Each copy created is attached to **its cataloguing batch**. So when printing
labels, you can filter on this exact batch: only what you have just recorded
is offered (and pre-checked), without pulling out the whole library. See
[Book labels](../impressions/etiquettes.md).

## See also

- [Scanning with the camera](../premiers-pas/scanner-camera.md) — how the
  camera works
- [Add a book](../catalogue/ajouter-livre.md) — creating a single record by hand
- [Book labels](../impressions/etiquettes.md) — print the batch's labels
