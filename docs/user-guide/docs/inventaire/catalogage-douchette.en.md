# Cataloguing with the USB scanner

If your workstation has a **USB barcode scanner** (a wired scanner that plugs
in like a keyboard), you can catalogue a box of books **without a camera**: you
scan the ISBNs one after another, directly on the BibliOfelia screen.

It is the scanner counterpart of [cataloguing by
camera](catalogage-scan.md): same result (BibliOfelia creates the records and
copies), but driven by the fixed workstation's scanner.

!!! info "Scanner or camera?"
    The **USB scanner** is ideal at a desk, on a fixed station, and works even
    without a secure connection (`https://`). The **camera** is ideal on the
    move, tablet in hand. Both fill the same catalogue.

## Start a batch with the scanner

From [**Advanced**](/bibliofelia/en/advanced/){ target="_blank" } → Inventory,
click
[**Cataloguing with the scanner**](/bibliofelia/en/catalog/scan/new-douchette/){ target="_blank" }.

As with camera cataloguing, you can set **default values** for the whole batch
(category, location, label). You can **change them line by line** afterwards.

## Scan the ISBNs one after another

1. The page opens with the input field **already active**: you have **nothing
   to click**.
2. Scan the ISBN barcode on the **back** of each book (it starts with 978 or
   979) with the scanner.
3. On each read, the line appears in the list: BibliOfelia automatically looks
   up the title, author and language (OpenLibrary, Google Books, BnF…).

!!! tip "Several copies of the same book"
    Do you have two identical copies? Scan the same ISBN **twice**. On the
    second pass (after a few seconds), BibliOfelia adds an extra copy to the
    same record, without creating a duplicate. A too-fast re-scan is ignored,
    to avoid double reads.

!!! warning "Ofelia codes rejected"
    Cataloguing accepts book **ISBNs** (978/979) and magazine **ISSNs** (977).
    If you scan an Ofelia code label (290/291) already stuck on a document by
    mistake, it is rejected: here you register new documents, not copies that
    are already catalogued.

## Finish and check the batch

When you are done scanning, click **Finish and view the batch**. The batch list
appears. For each line you see the book found (author, title, language) and you
can:

- change the **category**, **location** or **condition** — per line, or for
  several lines at once using the checkboxes;
- adjust the **number of copies**;
- **delete** a line (trash icon) in case of a scanning error.

## Save the batch

Click **Send to catalogue**. BibliOfelia creates all missing records and all
copies, with their Ofelia codes. You can then [print only this batch's
labels](../impressions/etiquettes.md).

## See also

- [Cataloguing by scanning (camera)](catalogage-scan.md) — the same thing with
  the camera
- [Input methods](../premiers-pas/saisie.md) — scanner, camera, keyboard
- [Book labels](../impressions/etiquettes.md) — print the batch's labels
