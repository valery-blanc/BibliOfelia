# Pickup and expiration of a reservation

Once the book has arrived and the member has been notified, you must
set it aside until they come to collect it. If no one comes, the
reservation expires and the book is released.

## Set the book aside

When the book is returned, if it triggers a reservation, BibliOfelia
indicates this with a message:

> **Set aside for [Member name]**

Physically store the book in the reservation area (a dedicated shelf
behind the welcome desk, for example), not on the open stacks.

## When the member comes to collect

The member arrives with their card. Do a normal loan:

1. Open the [**Lend**](/bibliofelia/en/loans/lend/){ target="_blank" } page
2. Scan the card
3. Scan the book

The reservation automatically becomes a loan. Its expiration date
clears, its status moves to **Fulfilled** in the history.

## Expiration: the member doesn't come

If the notified member doesn't come to collect the book within a set
time (7 days by default), the reservation automatically expires.

Concretely:

- The reservation moves to status **Expired**
- The book becomes available again (or moves to the next member in
  the queue)
- The **Set aside** button disappears: put the book back on the
  shelf

!!! info "The delay is configurable"
    The administrator can adjust the default duration in the settings
    (`pickup_hold_days`). Default is 7 days.

## See reservations at risk of expiring

From **Reports → Reservations to pick up**, you see the list of ready
reservations with their expiration date. The closest appear at the
top — that's your priority follow-up list.

## Edge cases

### The member wants to extend the wait

If the member tells you they will come next week, you can open the
reservation and manually change the expiration date to avoid it
expiring too soon.

### The member gives up

If they no longer want the book, open the reservation and click
**Cancel**. The book moves to the next member or becomes available
again.
