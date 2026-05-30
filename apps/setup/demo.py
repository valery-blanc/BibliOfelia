"""Données de démo (§11.4) : 50 notices, 80 exemplaires, 20 usagers, 15 prêts.

Idempotent : marque les objets avec `notes='[DEMO]'` pour pouvoir les retirer
proprement via `remove_demo()`.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from django.db import transaction

DEMO_MARKER = "[DEMO]"

_TITLES_FR = [
    "Le Petit Prince", "Les Misérables", "Notre-Dame de Paris", "Madame Bovary",
    "Le Comte de Monte-Cristo", "Germinal", "L'Étranger", "Les Fleurs du mal",
    "Le Rouge et le Noir", "À la recherche du temps perdu", "Bel-Ami",
    "Le Père Goriot", "Voyage au bout de la nuit", "L'Assommoir",
    "Vingt mille lieues sous les mers", "Les Trois Mousquetaires",
    "Le Tour du monde en 80 jours", "Cyrano de Bergerac", "Boule de suif",
    "Candide", "Zadig", "Tartuffe", "Le Misanthrope", "L'Avare",
    "Phèdre", "Le Cid", "Andromaque", "Le Mariage de Figaro",
    "Les Fables", "Les Confessions", "Du contrat social",
    "Lettres persanes", "Manon Lescaut", "La Princesse de Clèves",
    "Gargantua", "Pantagruel", "Les Caractères", "Les Pensées",
    "Le Discours de la méthode", "Les Essais", "Le Chevalier au bouclier vert",
    "Le Roman de Renart", "La Chanson de Roland", "Tristan et Iseut",
    "Yvain ou le Chevalier au lion", "Perceval", "Les Lais", "Roman de la rose",
    "Aucassin et Nicolette", "Le Jeu de Robin et Marion",
]

_AUTHORS = [
    "Antoine de Saint-Exupéry", "Victor Hugo", "Gustave Flaubert",
    "Alexandre Dumas", "Émile Zola", "Albert Camus", "Charles Baudelaire",
    "Stendhal", "Marcel Proust", "Guy de Maupassant", "Honoré de Balzac",
    "Louis-Ferdinand Céline", "Jules Verne", "Edmond Rostand", "Voltaire",
    "Molière", "Jean Racine", "Pierre Corneille", "Beaumarchais",
    "Jean de La Fontaine", "Jean-Jacques Rousseau", "Montesquieu",
    "Antoine François Prévost", "Madame de La Fayette", "François Rabelais",
    "Jean de La Bruyère", "Blaise Pascal", "René Descartes", "Michel de Montaigne",
    "Chrétien de Troyes",
]

_FIRST_NAMES = ["Aïna", "Bao", "Camille", "Dao", "Emma", "Faraah", "Gaël",
                "Hari", "Iris", "Jules", "Koto", "Léa", "Manou", "Naina",
                "Olive", "Pierre", "Rina", "Sami", "Tia", "Volana"]
_LAST_NAMES = ["Rasoa", "Andria", "Rakoto", "Razafy", "Dubois", "Martin",
               "Bernard", "Petit", "Robert", "Richard", "Durand", "Moreau",
               "Laurent", "Simon", "Michel", "Lefebvre", "Garcia", "Lopez",
               "Roy", "Vidal"]


def install_demo(librarian=None) -> dict:
    """Crée les données de démo. Idempotent : si la démo est déjà installée
    (au moins une notice marquée DEMO_MARKER), retourne les compteurs courants
    sans rien créer.

    `librarian` (optionnel) : User attribué aux prêts créés. Sans librarian,
    les prêts sont créés sans bibliothécaire (champ SET_NULL).
    """
    from apps.catalog.models import BibliographicRecord
    from apps.loans.models import Loan
    from apps.members.models import Member

    # Garde d'idempotence : si la démo est déjà installée, ne rien refaire.
    existing = BibliographicRecord.objects.filter(summary=DEMO_MARKER).count()
    if existing:
        return {
            "records": existing,
            "items": _count_items(),
            "members": Member.objects.filter(notes=DEMO_MARKER).count(),
            "loans": Loan.objects.filter(item__notes=DEMO_MARKER).count(),
            "skipped": True,
        }
    return _install_demo_inner(librarian)


def _count_items() -> int:
    from apps.catalog.models import Item
    return Item.objects.filter(notes=DEMO_MARKER).count()


@transaction.atomic
def _install_demo_inner(librarian=None) -> dict:
    from apps.catalog.models import (
        Author, BibliographicRecord, Category, Item, ItemStatus, Location,
    )
    from apps.loans.models import Loan, LoanStatus
    from apps.loans.services import compute_due_date, create_loan
    from apps.members.models import Member, MemberCategory

    rng = random.Random(42)
    authors = [
        Author.objects.get_or_create(full_name=name, defaults={"notes": DEMO_MARKER})[0]
        for name in _AUTHORS
    ]
    locations = []
    for code in ("A1", "A2", "B1", "JEUN"):
        loc, _ = Location.objects.get_or_create(code=code, defaults={"description": DEMO_MARKER})
        locations.append(loc)

    categories = list(Category.objects.all()[:5])
    if not categories:
        categories = [Category.objects.create(code="DEMO", name=DEMO_MARKER)]

    # 50 notices + 80 exemplaires
    records = []
    for i in range(50):
        title = rng.choice(_TITLES_FR) + (f" — vol. {i // 25 + 1}" if i >= 25 else "")
        rec = BibliographicRecord.objects.create(
            title=title,
            publisher=rng.choice(["Gallimard", "Hachette", "Flammarion", "Stock", "Le Seuil"]),
            publication_year=rng.randint(1900, 2025),
            language="fr",
            # None et pas "" : la contrainte UNIQUE partielle sur isbn_13 est
            # WHERE isbn_13 IS NOT NULL ; SQLite traite "" comme une valeur
            # ordinaire et fait collisionner les notices sans ISBN (BUG-007).
            isbn_13=None if rng.random() < 0.3 else f"978{rng.randint(10**9, 10**10 - 1)}",
            category=rng.choice(categories),
            summary=DEMO_MARKER,
        )
        rec.authors.add(*rng.sample(authors, k=rng.randint(1, 2)))
        records.append(rec)

    items = []
    for i in range(80):
        rec = rng.choice(records)
        it = Item.objects.create(
            record=rec,
            location=rng.choice(locations),
            notes=DEMO_MARKER,
        )
        items.append(it)

    # 20 usagers
    mcat = MemberCategory.objects.first()
    if not mcat:
        mcat = MemberCategory.objects.create(
            code="DEMO", name=DEMO_MARKER, max_concurrent_loans=5,
            default_loan_duration_days=21, card_validity_months=12,
        )
    members = []
    for i in range(20):
        members.append(Member.objects.create(
            first_name=rng.choice(_FIRST_NAMES),
            last_name=rng.choice(_LAST_NAMES),
            category=mcat,
            notes=DEMO_MARKER,
        ))

    # 15 prêts en cours
    loans = 0
    pool_items = [it for it in items if it.status == ItemStatus.AVAILABLE]
    rng.shuffle(pool_items)
    for it in pool_items[:15]:
        member = rng.choice(members)
        try:
            create_loan(item=it, member=member, librarian=librarian)
            loans += 1
        except Exception:
            continue

    return {
        "records": len(records), "items": len(items),
        "members": len(members), "loans": loans,
    }


def install_doc_extras(librarian=None) -> dict:
    """Ajoute au-dessus de install_demo() les états utiles aux captures du guide :
    - 2 réservations PENDING (avec membre + notice existants)
    - 3 prêts en retard (due_date forcée dans le passé)
    - 1 carte de membre expirée

    Idempotent : si au moins une réservation marquée DEMO existe, skip.
    """
    from apps.loans.models import Reservation
    from apps.members.models import Member

    if Reservation.objects.filter(
        record__summary=DEMO_MARKER,
        member__notes=DEMO_MARKER,
    ).exists():
        return {"skipped": True}

    return _install_doc_extras_inner(librarian)


@transaction.atomic
def _install_doc_extras_inner(librarian=None) -> dict:
    from apps.catalog.models import BibliographicRecord
    from apps.loans.models import Loan, LoanStatus, Reservation, ReservationStatus
    from apps.loans.services import create_reservation
    from apps.members.models import Member

    rng = random.Random(43)
    records = list(
        BibliographicRecord.objects.filter(summary=DEMO_MARKER).order_by("pk")
    )
    members = list(Member.objects.filter(notes=DEMO_MARKER).order_by("pk"))
    if not records or not members:
        return {"error": "install_demo doit etre execute avant install_doc_extras"}

    # 2 réservations PENDING
    reservations = 0
    for rec in rng.sample(records, k=min(2, len(records))):
        m = rng.choice(members)
        create_reservation(record=rec, member=m)
        reservations += 1

    # 3 prêts en retard : on prend 3 prêts actifs et on force due_date dans le passé
    overdue = 0
    active_loans = list(
        Loan.objects.filter(
            status=LoanStatus.ACTIVE,
            item__notes=DEMO_MARKER,
        ).order_by("pk")[:3]
    )
    for ln in active_loans:
        ln.due_date = date.today() - timedelta(days=rng.randint(7, 30))
        ln.save(update_fields=["due_date"])
        overdue += 1

    # 1 carte de membre expirée
    expired = 0
    candidate = (
        Member.objects.filter(notes=DEMO_MARKER, expiration_date__gt=date.today())
        .order_by("pk").first()
    )
    if candidate:
        candidate.expiration_date = date.today() - timedelta(days=15)
        candidate.save(update_fields=["expiration_date"])
        expired = 1

    return {
        "reservations": reservations,
        "overdue_loans": overdue,
        "expired_cards": expired,
    }


@transaction.atomic
def remove_demo() -> dict:
    """Supprime les objets marqués DEMO. Retourne un compteur."""
    from apps.catalog.models import Author, BibliographicRecord, Item, Location
    from apps.loans.models import Loan, Reservation
    from apps.members.models import Member, MemberCategory

    counters = {}
    # Ordre : Reservation → Loan → Item → Record → Author/Location/MemberCategory → Member
    counters["reservations"] = Reservation.objects.filter(
        record__summary=DEMO_MARKER
    ).delete()[0]
    counters["loans"] = Loan.objects.filter(
        item__notes=DEMO_MARKER
    ).delete()[0]
    counters["items"] = Item.objects.filter(notes=DEMO_MARKER).delete()[0]
    counters["records"] = BibliographicRecord.objects.filter(summary=DEMO_MARKER).delete()[0]
    counters["members"] = Member.objects.filter(notes=DEMO_MARKER).delete()[0]
    # Auteurs/locations/mcat avec marqueur uniquement (sécuritaire)
    counters["authors"] = Author.objects.filter(notes=DEMO_MARKER).delete()[0]
    counters["locations"] = Location.objects.filter(description=DEMO_MARKER).delete()[0]
    return counters
