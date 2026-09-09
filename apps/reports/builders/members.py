"""Les usagers. FEAT-093.

Trois définitions valent d'être écrites une bonne fois :

- **famille** — un titulaire qui a au moins une personne rattachée à sa carte ;
  « personnes couvertes » = titulaires + rattachés, c'est le chiffre d'impact
  qu'attend un bailleur ;
- **réinscription** — un renouvellement de carte enregistré (`CardRenewal`) ;
  `Member.expiration_date` étant écrasée à chaque renouvellement, aucune
  soustraction ne pouvait le retrouver ;
- **membre perdu** — une carte dont l'expiration tombe dans la période et qui
  est toujours périmée aujourd'hui. Une carte renouvelée a par construction une
  expiration dans le futur : ici, la soustraction suffit.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count
from django.utils.translation import gettext as _

from .. import format as fmt
from ..pages import Chart, Column, Kpi, ReportPage, Series, Table
from ..periods import months_between

TOP_SIZE = 20
EXPIRY_WARNING_DAYS = 30


def build(period, params) -> ReportPage:
    from apps.members.models import Member, MemberFamilyMember, MemberStatus

    today = date.today()
    members = Member.objects.all()
    total = members.count()
    valid_cards = members.filter(
        status=MemberStatus.ACTIVE, expiration_date__gte=today
    ).count()

    families = members.filter(family__isnull=False).distinct().count()
    attached = MemberFamilyMember.objects.count()

    new_members = members.filter(
        registration_date__gte=period.start, registration_date__lte=period.end
    ).count()
    renewals, renewals_since = _renewals(period)
    lost = members.filter(
        expiration_date__gte=period.start,
        expiration_date__lte=min(period.end, today),
        expiration_date__lt=today,
    ).count()

    active, coverage_note = _really_active(period)

    kpis = [
        Kpi(_("Usagers inscrits"), fmt.number(total), _("depuis l'ouverture"), "burgundy"),
        Kpi(_("Cartes valides"), fmt.number(valid_cards), _("aujourd'hui"), "forest"),
        Kpi(_("Familles"), fmt.number(families),
            _("cartes avec plusieurs personnes"), "orange"),
        Kpi(_("Personnes touchées"), fmt.number(total + attached),
            _("titulaires et personnes de leur foyer"), "sky"),
        Kpi(_("Usagers venus"), fmt.number(active),
            _("ont emprunté ou participé sur la période"), "olive"),
        Kpi(_("Nouveaux"), fmt.number(new_members), _("inscrits sur la période"), "forest"),
        Kpi(_("Réinscriptions"), fmt.number(renewals),
            renewals_since, "amber"),
        Kpi(_("Usagers perdus"), fmt.number(lost),
            _("carte périmée sur la période et non renouvelée"), "blush"),
    ]

    blocks = [
        _age_chart(members, today),
        _by_category(members),
        _movement_table(period),
        _expiring_soon(today),
        _by_city(members),
        _languages(members),
        _top_borrowers(period),
    ]

    return ReportPage(
        slug="members",
        title=_("Les usagers"),
        subtitle=_("Combien de personnes la bibliothèque touche, et qui elles sont."),
        kpis=kpis,
        blocks=[b for b in blocks if b is not None],
        period=period,
        note=coverage_note,
    )


def _renewals(period) -> tuple[int, str]:
    """Réinscriptions de la période, et depuis quand elles sont comptées.

    L'historique antérieur à la mise en service de `CardRenewal` est perdu par
    construction. On le dit plutôt que d'afficher un zéro qui ferait croire que
    personne ne se réinscrit.
    """
    from apps.members.models import CardRenewal

    count = CardRenewal.objects.filter(
        renewed_on__gte=period.start, renewed_on__lte=period.end
    ).count()
    first = CardRenewal.objects.order_by("renewed_on").values_list(
        "renewed_on", flat=True
    ).first()
    if first is None or first > period.start:
        since = first or date.today()
        return count, _("comptées depuis le %(d)s") % {"d": fmt.day(since)}
    return count, _("cartes renouvelées sur la période")


def _really_active(period) -> tuple[int, str]:
    """Usagers ayant emprunté **ou** participé à une animation sur la période.

    « Personnes touchées » compte des inscrits, pas des présents : présenté
    seul, il flatte. Ce compteur-ci dit combien sont réellement venus.
    """
    from apps.closing.models import AnimationAttendance
    from apps.loans.models import Loan

    borrowers = set(
        Loan.objects.filter(
            loan_date__date__gte=period.start, loan_date__date__lte=period.end
        ).values_list("member_id", flat=True)
    )
    attendees = set(
        AnimationAttendance.objects.filter(
            session__occurred_on__gte=period.start, session__occurred_on__lte=period.end
        ).values_list("member_id", flat=True)
    )
    return len(borrowers | attendees), _(
        "« Usagers venus » réunit les emprunteurs et les participants aux animations : "
        "quelqu'un qui a fait les deux n'est compté qu'une fois."
    )


def _age_chart(members, today: date) -> Chart:
    """Pyramide des âges, « âge inconnu » affiché plutôt qu'écarté.

    Écarter les dates de naissance manquantes donnerait un graphe faux dont
    rien ne signalerait l'incomplétude."""
    buckets: dict[str, int] = {label: 0 for label in fmt.bracket_labels()}
    for birth_date in members.values_list("birth_date", flat=True):
        buckets[fmt.age_bracket(fmt.age_on(birth_date, today))] += 1
    labels = [label for label in fmt.bracket_labels() if buckets[label]]
    return Chart(
        title=_("L'âge des usagers"), kind="bar",
        labels=labels, values=[buckets[label] for label in labels], unit=_("usagers"),
    )


def _by_category(members) -> Chart:
    rows = members.values("category__name").annotate(n=Count("id")).order_by("-n")
    return Chart(
        title=_("Les catégories d'usager"), kind="pie",
        labels=[row["category__name"] or _("Sans catégorie") for row in rows],
        values=[row["n"] for row in rows], unit=_("usagers"),
    )


def _movement_table(period) -> Table:
    """Arrivées, réinscriptions et départs — en tableau **et** en courbes.

    Trois colonnes de chiffres ne montrent pas qu'une courbe passe au-dessus de
    l'autre ; c'est pourtant le seul moment où l'on voit qu'on perd plus de
    monde qu'on n'en gagne.
    """
    from apps.members.models import CardRenewal, Member

    rows = []
    labels: list[str] = []
    new_values: list[float] = []
    renewed_values: list[float] = []
    lost_values: list[float] = []
    today = date.today()
    for start, end, label in months_between(period):
        new = Member.objects.filter(
            registration_date__gte=start, registration_date__lte=end
        ).count()
        renewed = CardRenewal.objects.filter(
            renewed_on__gte=start, renewed_on__lte=end
        ).count()
        lost = Member.objects.filter(
            expiration_date__gte=start, expiration_date__lte=end, expiration_date__lt=today
        ).count()
        rows.append([label, fmt.number(new), fmt.number(renewed), fmt.number(lost)])
        labels.append(label)
        new_values.append(new)
        renewed_values.append(renewed)
        lost_values.append(lost)

    chart = Chart(
        title=_("Qui arrive, qui reste, qui part"), kind="line",
        labels=labels,
        series=[
            Series(_("Nouveaux"), new_values),
            Series(_("Réinscriptions"), renewed_values),
            Series(_("Usagers perdus"), lost_values),
        ],
        unit=_("usagers"),
    )
    return Table(
        title=_("Qui arrive, qui reste, qui part"),
        columns=[
            Column(_("Mois")),
            Column(_("Nouveaux"), "right"),
            Column(_("Réinscriptions"), "right"),
            Column(_("Usagers perdus"), "right"),
        ],
        rows=rows,
        empty_text=_("Aucun mouvement sur cette période."),
        chart=chart,
    )


def _expiring_soon(today: date) -> Table:
    """Les cartes à renouveler dans le mois — la seule liste d'action de cet
    écran, et celle qui évite de perdre un usager par oubli."""
    from apps.members.models import Member, MemberStatus

    limit = today + timedelta(days=EXPIRY_WARNING_DAYS)
    rows_qs = (
        Member.objects.filter(
            status=MemberStatus.ACTIVE,
            expiration_date__gte=today,
            expiration_date__lte=limit,
        )
        .select_related("category")
        .order_by("expiration_date")
    )
    rows = [
        [
            f"{m.last_name} {m.first_name}".strip(),
            m.card_number,
            fmt.blank(m.contact_phone),
            m.category.name if m.category else "—",
            fmt.day(m.expiration_date),
        ]
        for m in rows_qs
    ]
    return Table(
        title=_("Cartes à renouveler dans les %(n)s jours") % {"n": EXPIRY_WARNING_DAYS},
        columns=[
            Column(_("Usager")), Column(_("N° de carte")), Column(_("Téléphone")),
            Column(_("Catégorie")), Column(_("Expire le")),
        ],
        rows=rows,
        empty_text=_("Aucune carte n'arrive à échéance ce mois-ci."),
    )


def _by_city(members) -> Table:
    rows_qs = (
        members.exclude(address_city="")
        .values("address_postal_code", "address_city")
        .annotate(n=Count("id"))
        .order_by("-n", "address_city")
    )
    total = members.count()
    rows_list = list(rows_qs)
    rows = [
        [
            fmt.blank(row["address_postal_code"]),
            row["address_city"],
            fmt.number(row["n"]),
            fmt.percent(row["n"], total),
        ]
        for row in rows_list
    ]
    missing = members.filter(address_city="").count()
    chart = Chart(
        title=_("D'où viennent les usagers"), kind="pie",
        labels=[row["address_city"] for row in rows_list],
        values=[row["n"] for row in rows_list],
        unit=_("usagers"),
    )
    return Table(
        title=_("D'où viennent les usagers"),
        columns=[
            Column(_("Code postal")), Column(_("Localité")),
            Column(_("Usagers"), "right"), Column(_("Part"), "right"),
        ],
        rows=rows,
        empty_text=_("Aucune localité renseignée."),
        note=_("%(n)s usagers n'ont pas de localité renseignée.") % {"n": missing}
        if missing else "",
        chart=chart,
    )


def _languages(members) -> Table:
    from apps.catalog.models import Language

    names = {lang.code: lang.name for lang in Language.objects.all()}
    counts: dict[str, int] = {}
    missing = 0
    for spoken in members.values_list("spoken_languages", flat=True):
        if not spoken:
            missing += 1
            continue
        for code in spoken:
            counts[code] = counts.get(code, 0) + 1
    total = members.count()
    rows = [
        [names.get(code, code), fmt.number(n), fmt.percent(n, total)]
        for code, n in sorted(counts.items(), key=lambda item: -item[1])
    ]
    return Table(
        title=_("Les langues parlées par les usagers"),
        columns=[Column(_("Langue")), Column(_("Usagers"), "right"), Column(_("Part"), "right")],
        rows=rows,
        empty_text=_("Aucune langue renseignée."),
        note=_("%(n)s usagers n'ont aucune langue renseignée.") % {"n": missing}
        if missing else "",
    )


def _top_borrowers(period) -> Table:
    from apps.loans.models import Loan

    rows_qs = (
        Loan.objects.filter(
            loan_date__date__gte=period.start, loan_date__date__lte=period.end
        )
        .values("member__last_name", "member__first_name", "member__card_number")
        .annotate(n=Count("id"))
        .order_by("-n")[:TOP_SIZE]
    )
    rows = [
        [
            f"{row['member__last_name']} {row['member__first_name']}".strip(),
            row["member__card_number"],
            fmt.number(row["n"]),
        ]
        for row in rows_qs
    ]
    return Table(
        title=_("Les usagers qui ont le plus emprunté"),
        columns=[Column(_("Usager")), Column(_("N° de carte")), Column(_("Prêts"), "right")],
        rows=rows,
        empty_text=_("Aucun prêt sur cette période."),
    )
