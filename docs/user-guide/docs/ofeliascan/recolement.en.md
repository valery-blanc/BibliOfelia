# Inventory (checking the stacks)

The **inventory** consists of walking through the stacks and checking
that each book is in its place. With OfeliaScan, this is the most
powerful operation of the system — you walk the shelves while
scanning, and BibliOfelia updates itself automatically.

## Prepare the inventory

Before starting:

1. Pick the **location** to inventory (one aisle at a time so you
   don't get lost)
2. Bring your phone with OfeliaScan
3. Open the **Advanced → Inventory** page on the computer

## Start an inventory session

On the computer:

1. Click **New inventory session**
2. Choose the **scope**: a precise location (e.g. "Aisle A1") or the
   entire catalog
3. Validate

On the phone, OfeliaScan receives the session. You see the chosen
scope and a counter at 0.

## Scan the books

In the aisle, scan each book one after another. For each scan:

- If the book is **in the right location**: it is marked "seen",
  nothing changes
- If the book is **in a different location**: BibliOfelia automatically
  updates its location to the current aisle
- If the code does not exist: OfeliaScan warns you (unknown label,
  to investigate)

!!! tip "Go fast, don't think"
    No need to check each scan manually: BibliOfelia sorts everything
    at the end. Focus on speed and full coverage of the aisle.

## Close the session

Once the aisle is covered:

1. On the phone, tap **End session**
2. On the computer, open the inventory report

You see:

- Number of books scanned
- Number of **missing** books (present in the database, not seen in
  the aisle)
- Number of **automatically relocated** books
- Number of **unknown codes** encountered

## What to do with missing books?

For each book reported missing, two possibilities:

- **It's elsewhere in the library**: do an inventory of the other
  aisles, it will be automatically repositioned
- **It's lost**: mark the copy as **Lost** from its page (see [Lost
  book](../cas-courants/livre-perdu.md))

## Recommended frequency

- **Small library**: full inventory 1 to 2 times a year
- **Large library**: 1 aisle per month in rotation

Do it ideally when the library is quiet (morning, closed day).
