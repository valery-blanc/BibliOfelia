# Scanning with the camera

BibliOfelia can scan barcodes **directly with the camera** of your
device — phone, tablet, or laptop with a webcam. No app to install:
everything happens in the browser.

This is the mode used by every **Scan** button on the site (the dashboard
banner, the Loan and Return pages, search, and the ISBN field of a record).

## How it works

1. Click a **Scan** button (or the round camera icon next to a search
   field).
2. The camera opens in a window, with an **aiming band** in the centre of
   the screen.
3. Place the book or card barcode **inside the central band**. No need to
   aim the whole image: only what passes through the band is read.
4. As soon as the code is recognised, you hear a **beep** (and the phone
   vibrates). The code is filled in automatically.

!!! tip "Aim at the band, not the whole screen"
    Reading is deliberately limited to a horizontal band in the middle of
    the image. This avoids mistakenly reading a neighbouring barcode when
    several books sit side by side. Move the book closer until its barcode
    fills the width of the band.

## Two ways to scan

Depending on the page, the camera works differently:

- **Single scan** (Loan, Return, search, ISBN): the camera reads **one**
  code, then closes and fills the field. You restart the scan for the next
  one.
- **Continuous scan** (Inventory, Scan cataloguing): the camera **stays
  open** and reads one after another. A counter appears, a beep confirms
  each new book. You sweep a whole shelf or crate without clicking again.
  Press **Finish** when you are done.

## What the camera reads

The camera only recognises **book and card barcodes** (EAN-13 format, 13
digits). This is intentional: it makes reading far more reliable and avoids
false reads. Recognised codes:

- **ISBNs** on the back of books (starting with 978 or 979);
- **Ofelia codes** on labels and member cards (starting with 290 or 291).

## The camera won't open?

A few things to check:

!!! warning "Secure connection (HTTPS) required"
    For security reasons, browsers only allow the camera over a **secure
    (https://)** connection. If you reach BibliOfelia through a local
    `http://` address (for example `http://ofelia.local`), the camera
    cannot open. In that case, use a **barcode scanner** or **keyboard
    entry**, or ask the Box administrator for the secure address.

- **Permission denied**: the first time, the browser asks for permission to
  use the camera. Answer **Allow**. If you declined, re-enable the camera in
  the site settings (the padlock icon left of the address).
- **No camera detected**: on a desktop without a webcam, the camera is not
  available — use a barcode scanner or the keyboard.
- **Clear error message**: if something goes wrong, BibliOfelia shows the
  exact reason and invites you to **type the code by hand**. You are never
  stuck.

## What if I have no camera?

Every workflow remains usable **without a camera**:

- a USB **barcode scanner** behaves like an ultra-fast keyboard;
- **keyboard entry** is always possible (type the code, then **Enter** or
  **Validate**).

See [Input modes](saisie.md) to choose the right tool.

## See also

- [Make a loan](../prets-retours/faire-pret.md)
- [Catalogue by scanning](../inventaire/catalogage-scan.md)
- [Inventory](../inventaire/recolement.md)
