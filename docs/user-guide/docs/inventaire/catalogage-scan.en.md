# Catalogue by scanning

When a crate of books arrives, **scan cataloguing** is the fastest way to
record everything: you scan the ISBNs one after another, and BiblOFELIA
creates the records and their copies in one go.

Two tools do the same job. The **camera** of a phone or tablet, and the
**USB scanner** plugged into a fixed workstation. Only the way the barcode
is read changes. The batch, the default values, the review and the send to
the catalogue are the same.

It is, for creation, the equivalent of [inventory](recolement.md)
for checking: a **continuous scan**, with nothing to click between two
books.

!!! info "Camera or USB scanner?"
    The **USB scanner** is ideal at a desk, on a fixed station, and works even
    without a secure connection (`https://`). The **camera** is ideal on the
    move, tablet in hand. Both fill the same catalogue.

## What a cataloguing session is for

A cataloguing **session** (also called a **batch**) is how you add **many books
at once** to the catalogue. It works in three steps:

1. **You open a batch and scan** every book in the crate, one after another.
   Nothing enters the catalogue yet: the batch is only a working list, which you
   can correct or empty.
2. **You check the list** — and above all, you apply **batch changes**: tick
   several rows (or all of them) and assign them, in a single click, the same
   **classification**, the same **location** in the library or the same **condition**.
   That is the whole point of cataloguing together books that belong together.
3. **You send the batch to the catalogue**: records and copies are created for
   real, with the **source** chosen at the start, and you can print the labels
   **for that batch only** in one go.

A validated batch stays available: from the list of batches, **View batch**
shows which books it contained, with a link to each record.

## Start a batch

Both entries open **the same form**. Set the
[default values](#defauts), then click **Start cataloging**.

### With the camera { #camera }

From the [**Catalogue**](/bibliofelia/en/catalog/){ target="_blank" },
click
[**Catalog by scanning**](/bibliofelia/en/catalog/scan/){ target="_blank" },
then [**New batch**](/bibliofelia/en/catalog/scan/new/){ target="_blank" }.

The same screen is also under
[**Advanced**](/bibliofelia/en/advanced/){ target="_blank" } → Inventory →
**Cataloging by scan**.

### With the USB scanner { #douchette }

From [**Advanced**](/bibliofelia/en/advanced/){ target="_blank" } →
Inventory, click
[**Cataloguing with a barcode scanner**](/bibliofelia/en/catalog/scan/new-douchette/){ target="_blank" }.

## Default values for the batch { #defauts }

Before scanning, you can set **default values** for the whole batch.
**This is optional**: a batch with no classification, no location and no
source catalogues perfectly well.

To use one of these values, you must **create it first**. The batch form
only offers what already exists, and it cannot add a new one. These lists
are under
[**Advanced**](/bibliofelia/en/advanced/){ target="_blank" } → Metadata:

- a default [**classification**](/bibliofelia/en/catalog/categories/){ target="_blank" }
  (Youth Non-fiction, Adult Fiction…). The Ofelia classifications are
  already provided; open the list only to add one;
- a default [**location**](/bibliofelia/en/catalog/locations/){ target="_blank" }
  (the shelf these books will go to);
- a default [**source**](/bibliofelia/en/catalog/provenances/){ target="_blank" }
  — where these books come from: bought by the library, a gift, a loan from
  another library. **Every copy in the batch** receives it. That is the
  right choice for a box of borrowed books: on the day they go back, a
  filter on this source finds them all;
- a **batch name**, to find the batch again later. You type it directly:
  there is no list to prepare.

The classification and the location apply to every book, and you can
**change them afterwards**, one line or several at once. The source belongs
to the **whole batch**: you choose it here, before scanning. To change it
once the copies exist, use
[Sources](/bibliofelia/en/catalog/provenances/){ target="_blank" }.

## Scan the ISBNs in a row

The ISBN barcode is on the **back** of the book. It starts with 978 or 979.
On each read, BiblOFELIA automatically looks up the title, author and
language (OpenLibrary, Google Books, BnF…).

### With the camera

1. Click **Scan books**: the camera opens in continuous mode.
2. Scan each book.
3. A **beep** confirms the read. The screen shows the **title and author**
   found — or, failing that, the ISBN and language.
4. Press **Finish**: the camera closes and the batch list appears, ready
   to review.

### With the USB scanner

1. The page opens with the input field **already active**: you have
   **nothing to click**.
2. Scan each book with the scanner. The line appears in the list as you go.
3. When you are done, click **Finish and review the batch** to move on to
   the review.

In both cases, the field **Enter an ISBN manually** lets you type a damaged
code, then **Add**.

!!! tip "Several copies of the same book"
    Got two identical copies? Scan the same ISBN **twice**. On the second
    pass (after a few seconds), BiblOFELIA shows "copy 2" — in large type
    in the camera viewfinder, in the list with the scanner. It will add an
    extra copy to the same record, without creating a duplicate. A re-scan
    that is too quick (less than 3 seconds) is ignored, to avoid double
    reads.

!!! warning "Ofelia codes rejected"
    Cataloguing accepts book **ISBNs** (978/979) and magazine **ISSNs**
    (977, see below). If you mistakenly scan an Ofelia code label (290/291)
    already on a document, it is rejected: here you record new documents,
    not copies that are already catalogued.

## Cataloguing a magazine or journal

Magazines and journals have no ISBN, but an **ISSN**: a barcode that starts
with **977**. No separate tool needed — scan that 977 barcode **in the same
batch** as your books, with the camera or the USB scanner.

- BiblOFELIA recognises the ISSN and looks up the **magazine's title**
  (BnF, BNE).
- All issues of the same magazine share the **same ISSN**: they therefore
  land on a **single "magazine" record**, to which each scanned issue adds a
  copy.

!!! info "One ISSN = a single magazine record"
    If you scan two different issues of the same magazine, BiblOFELIA does
    not create two records: it adds a copy to the magazine's record. To tell
    the issues apart (date, number), note them in the copy's notes.

## Check and adjust the batch

The list is the same whether the batch was scanned with the camera or the
USB scanner. For each line, you see the book found (author, title, language)
and you can:

- change the **classification**, **location** or **condition**: tick one or
  more lines (the checkbox at the top of the table ticks them all), choose
  the values in **Edit checked rows**, then **Apply to checked rows**;
- adjust the **number of copies** on the line;
- **delete** a line (trash icon) in case of a scan error.

**Save** keeps these adjustments without creating anything in the catalogue.
You can resume the batch later.

!!! info "Record already exists"
    If an ISBN matches a book **already present** in the catalogue,
    BiblOFELIA does not recreate the record: it simply adds your new copies
    to the existing record, without changing it.

## Send the batch to the catalogue

Click **Send to catalog**. BiblOFELIA creates all the missing records and
all the copies, with their Ofelia codes and the **source** chosen when the
batch was started.

## Print only this batch's labels

Each copy created is attached to **its cataloguing batch**. So when printing
labels, you can filter on this exact batch: only what you have just recorded
is offered (and pre-checked), without pulling out the whole library. See
[Book labels](../impressions/etiquettes.md).

## See also

- [Sources](../catalogue/provenances.md) — where a copy comes from, and how
  to find a borrowed collection again
- [Scanning with the camera](../premiers-pas/scanner-camera.md) — how the
  camera works
- [Input methods](../premiers-pas/saisie.md) — scanner, camera, keyboard
- [Add a book](../catalogue/ajouter-livre.md) — creating a single record by
  hand
- [Book labels](../impressions/etiquettes.md) — print the batch's labels
