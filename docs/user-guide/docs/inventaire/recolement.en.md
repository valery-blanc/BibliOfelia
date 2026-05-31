# Inventory (checking the stacks)

The **inventory** consists of walking through the stacks and checking that
each book is in its place. It is the most powerful operation of the system:
you walk the shelves while scanning with the **camera**, and BibliOfelia
updates itself automatically.

The inventory is now done **directly from the site**, with the camera of
your phone or tablet — no app to install. (OfeliaScan is still possible for
large-scale inventories, see the bottom of the page.)

## Prepare the inventory

Before starting:

1. Pick the **shelf** to inventory (one at a time so you don't get lost).
2. Bring a device with a camera (phone, tablet).
3. Open the **Advanced → Inventory** page on that device.

!!! warning "Secure connection required for the camera"
    The camera only works over a **secure (https://)** connection. See
    [Scanning with the camera](../premiers-pas/scanner-camera.md) if the
    camera refuses to open.

## Start an inventory session

1. Click **New inventory session**.
2. Choose the **scope**: a specific **location** (e.g. "Shelf A1") or **the
   whole collection**. If you choose a location, selecting it becomes
   mandatory.
3. Confirm: BibliOfelia opens the **report** page directly, which also
   serves as the scanning screen.

## Scan the books continuously

1. Click **Start inventory**: the camera opens in **continuous mode** and
   stays open.
2. Scan each book on the shelf, one after another. A **beep** (and a
   vibration) confirms each new book, and a **counter** climbs on screen.
3. For each scan:
   - book **on the right shelf**: it is marked "seen";
   - book **shelved elsewhere** (scope = a location): BibliOfelia
     automatically updates its shelf to the one you are inventorying;
   - **unknown code**: flagged, to investigate.

The same book scanned twice is counted only once. If a record has several
copies, the screen shows "copy 2", "copy 3"… to help you find them all.

!!! tip "Go fast, don't think"
    No need to check each scan: BibliOfelia sorts everything out at the end.
    Focus on speed and full coverage of the shelf. The list and counters
    update live.

When the shelf is covered, press **Finish**.

## Read the report

The report is shown **by record**, sorted by author and title. All Ofelia
codes appear as pills:

- **green**: copy found during the inventory;
- **red**: **missing** copy (present in the database, not seen on the shelf).

You also see the number of books scanned, automatically moved, and the
unknown codes encountered.

## What to do with missing books?

For each copy in red, two options:

- **It is elsewhere in the library**: inventory the other shelves, it will
  be repositioned automatically as you go.
- **It is lost**: mark the copy as **Lost** from its record (see [Lost
  book](../faq.md#livre-perdu)).

## Recommended frequency

- **Small library**: full inventory 1 to 2 times a year.
- **Large library**: 1 shelf per month in rotation.

Ideally do it when the library is quiet (morning, closing day).

## What about OfeliaScan?

For **large inventories**, the [OfeliaScan](../ofeliascan/activer.md) mobile app can also
send a whole session of scans to BibliOfelia. The logic is the same (books
seen, moved, missing). For the routine inventory of a single shelf, the
site's camera described above is the simplest way.
