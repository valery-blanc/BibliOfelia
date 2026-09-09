"""Le fonds. FEAT-093.

« Qu'est-ce qu'on a ? » d'abord, « qu'est-ce qui est entré et sorti ? » ensuite.
Les deux questions vivent sur le même écran mais dans deux blocs distincts :
elles ne se lisent pas au même moment de l'année.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils.translation import gettext as _

from .. import format as fmt
from ..pages import Chart, Column, Kpi, ReportPage, Series, Table

# Un exemplaire acquis il y a moins d'un an et jamais emprunté n'est pas du
# stock mort : c'est une nouveauté. Sans ce filtre, l'indicateur accuse la
# bibliothèque de dormir chaque fois qu'elle catalogue un carton de dons.
DORMANT_MIN_AGE_DAYS = 365

# Statuts qui sortent un exemplaire de la circulation : les compter au
# dénominateur d'un taux de rotation ferait baisser le taux d'un rayon parce
# qu'on y a pilonné des livres abîmés.
OUT_OF_CIRCULATION = ["lost", "discarded", "in_repair"]


def build(period, params) -> ReportPage:
    from apps.catalog.models import (
        AcquisitionSource,
        BibliographicRecord,
        DocumentType,
        Item,
        ItemState,
        ItemStatus,
    )
    from apps.loans.models import Loan

    items = Item.objects.all()
    total = items.count()
    by_status = dict(
        items.values_list("status").annotate(n=Count("id")).values_list("status", "n")
    )
    circulating = total - sum(by_status.get(s, 0) for s in OUT_OF_CIRCULATION)

    period_loans = Loan.objects.filter(
        loan_date__date__gte=period.start, loan_date__date__lte=period.end
    )
    loans_total = period_loans.count()

    kpis = [
        Kpi(_("Livres au total"), fmt.number(total), _("exemplaires du fonds"), "burgundy"),
        Kpi(_("Disponibles"), fmt.number(by_status.get(ItemStatus.AVAILABLE, 0)),
            _("sur les rayons maintenant"), "forest"),
        Kpi(_("Sortis"), fmt.number(by_status.get(ItemStatus.ON_LOAN, 0)),
            _("chez des usagers"), "orange"),
        Kpi(_("Titres différents"), fmt.number(BibliographicRecord.objects.count()),
            _("un titre peut avoir plusieurs exemplaires"), "sky"),
        Kpi(_("En réparation"), fmt.number(by_status.get(ItemStatus.IN_REPAIR, 0)),
            _("hors circulation"), "amber"),
        Kpi(_("Perdus"), fmt.number(by_status.get(ItemStatus.LOST, 0)),
            _("depuis le début"), "blush"),
        Kpi(_("Pilonnés"), fmt.number(by_status.get(ItemStatus.DISCARDED, 0)),
            _("retirés du fonds"), "olive"),
        Kpi(_("Rotation du fonds"), fmt.ratio(loans_total / circulating if circulating else None),
            _("prêts par livre sur la période"), "forest"),
    ]

    blocks = []

    # ── Par catégorie : le tableau que le comité regarde en premier ──
    category_rows, category_chart = _by_category(items, period, circulating)
    blocks.append(Table(
        title=_("Les rayons : ce qu'on a et ce qui sort"),
        columns=[
            Column(_("Rayon")),
            Column(_("Livres"), "right"),
            Column(_("Part du fonds"), "right"),
            Column(_("Prêts sur la période"), "right"),
            Column(_("Prêts par livre"), "right"),
        ],
        rows=category_rows,
        empty_text=_("Aucun livre catalogué."),
        note=_(
            "« Prêts par livre » compare les prêts de la période au nombre de livres "
            "en circulation du rayon : au-dessus de 1, chaque livre du rayon est sorti "
            "au moins une fois."
        ),
        chart=category_chart,
    ))

    # ── Type, état, langue ──
    blocks.append(_pie_from_choices(
        _("Par sorte de document"), items, "document_type_of_record", DocumentType
    ))
    blocks.append(_pie_from_choices(_("Dans quel état"), items, "state", ItemState))
    blocks.append(_language_table())

    # ── Où ils sont, d'où ils viennent ──
    blocks.append(_by_location(items))
    blocks.append(_by_provenance(items, period))
    blocks.append(_by_acquisition(items, AcquisitionSource))

    # ── Entrées et sorties de la période ──
    blocks.append(_new_items(period))
    blocks.append(_donors(period))
    blocks.append(_dormant())

    # ── Les données brutes, sous-rapport de cet écran (demande Val) ──
    blocks.append(_full_catalogue())

    return ReportPage(
        slug="collection",
        title=_("Le fonds"),
        subtitle=_("Ce que la bibliothèque possède, et ce qui est entré ou sorti."),
        kpis=kpis,
        blocks=[b for b in blocks if b is not None],
        period=period,
    )


def _by_category(items, period, circulating: int):
    from apps.loans.models import Loan

    rows_qs = (
        items.values("record__category__code", "record__category__name")
        .annotate(
            n=Count("id"),
            circulating=Count("id", filter=~Q(status__in=OUT_OF_CIRCULATION)),
        )
        .order_by("-n")
    )
    loans_by_category = dict(
        Loan.objects.filter(
            loan_date__date__gte=period.start, loan_date__date__lte=period.end
        )
        .values_list("item__record__category__code")
        .annotate(n=Count("id"))
        .values_list("item__record__category__code", "n")
    )

    total = items.count()
    rows, labels, books, loans = [], [], [], []
    for row in rows_qs:
        code = row["record__category__code"]
        label = row["record__category__name"] or _("Sans rayon")
        loans_count = loans_by_category.get(code, 0)
        turn = loans_count / row["circulating"] if row["circulating"] else None
        rows.append([
            label,
            fmt.number(row["n"]),
            fmt.percent(row["n"], total),
            fmt.number(loans_count),
            fmt.ratio(turn),
        ])
        labels.append(label)
        books.append(row["n"])
        loans.append(loans_count)

    # Deux barres par rayon plutôt qu'un camembert (demande Val) : le camembert
    # ne montrait que le fonds, et un rayon volumineux qui ne sort pas y avait
    # exactement l'air d'un rayon volumineux qui tourne. Côte à côte, l'écart
    # entre ce qu'on possède et ce qui sort se voit d'un coup d'œil.
    #
    # Groupées, jamais empilées : additionner des livres et des prêts ne veut
    # rien dire.
    chart = Chart(
        title=_("Les livres et les prêts par rayon"), kind="bar",
        labels=labels,
        series=[
            Series(_("Livres"), books),
            Series(_("Prêts sur la période"), loans),
        ],
    )
    return rows, chart


def _pie_from_choices(title: str, items, field: str, choices) -> Chart:
    """Un camembert sur un champ à choix, libellés traduits."""
    lookup = "record__document_type" if field == "document_type_of_record" else field
    counts = dict(
        items.values_list(lookup).annotate(n=Count("id")).values_list(lookup, "n")
    )
    labels, values = [], []
    for value, label in choices.choices:
        if counts.get(value):
            labels.append(str(label))
            values.append(counts[value])
    return Chart(title=title, kind="pie", labels=labels, values=values, unit=_("livres"))


def _language_table() -> Table:
    """Le fonds et le public côte à côte, langue par langue.

    Séparés, les deux chiffres ne disent rien ; ensemble ils répondent à « est-ce
    qu'on a des livres dans la langue des gens qui viennent ? », qui est la
    question de fond d'une bibliothèque Ofelia.
    """
    from apps.catalog.models import BibliographicRecord, Language
    from apps.members.models import Member

    names = {lang.code: lang.name for lang in Language.objects.all()}
    fonds = dict(
        BibliographicRecord.objects.exclude(language="")
        .values_list("language")
        .annotate(n=Count("id"))
        .values_list("language", "n")
    )
    # `spoken_languages` est un JSONField : on compte en Python, la base ne
    # sait pas agréger une liste. Une bibliothèque associative se compte en
    # milliers d'usagers, pas en millions.
    public: dict[str, int] = {}
    for spoken in Member.objects.values_list("spoken_languages", flat=True):
        for code in spoken or []:
            public[code] = public.get(code, 0) + 1

    total_records = sum(fonds.values())
    total_speakers = sum(public.values())
    codes = sorted(set(fonds) | set(public), key=lambda c: -(fonds.get(c, 0)))
    rows = [
        [
            names.get(code, code),
            fmt.number(fonds.get(code, 0)),
            fmt.percent(fonds.get(code, 0), total_records),
            fmt.number(public.get(code, 0)),
            fmt.percent(public.get(code, 0), total_speakers),
        ]
        for code in codes
    ]
    return Table(
        title=_("Les langues : le fonds et le public"),
        columns=[
            Column(_("Langue")),
            Column(_("Titres"), "right"),
            Column(_("Part du fonds"), "right"),
            Column(_("Usagers qui la parlent"), "right"),
            Column(_("Part du public"), "right"),
        ],
        rows=rows,
        empty_text=_("Aucune langue renseignée."),
    )


def _by_location(items) -> Table:
    rows_qs = (
        items.values("location__code").annotate(n=Count("id")).order_by("-n")
    )
    total = items.count()
    rows = [
        [
            row["location__code"] or _("Sans emplacement"),
            fmt.number(row["n"]),
            fmt.percent(row["n"], total),
        ]
        for row in rows_qs
    ]
    return Table(
        title=_("Où sont les livres"),
        columns=[Column(_("Emplacement")), Column(_("Livres"), "right"),
                 Column(_("Part"), "right")],
        rows=rows,
        empty_text=_("Aucun emplacement renseigné."),
    )


def _by_provenance(items, period) -> Table:
    """Par fonds d'origine, avec ses prêts : un fonds déposé par un tiers doit
    pouvoir être rendu, et son propriétaire veut savoir s'il a servi."""
    from apps.loans.models import Loan

    loans_by = dict(
        Loan.objects.filter(
            loan_date__date__gte=period.start, loan_date__date__lte=period.end
        )
        .values_list("item__provenance__code")
        .annotate(n=Count("id"))
        .values_list("item__provenance__code", "n")
    )
    rows_qs = (
        items.values("provenance__code", "provenance__label")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    rows = []
    for row in rows_qs:
        code = row["provenance__code"]
        rows.append([
            row["provenance__label"] or code or _("Fonds de la bibliothèque"),
            fmt.number(row["n"]),
            fmt.number(loans_by.get(code, 0)),
        ])
    return Table(
        title=_("D'où viennent les livres"),
        columns=[Column(_("Provenance")), Column(_("Livres"), "right"),
                 Column(_("Prêts sur la période"), "right")],
        rows=rows,
        empty_text=_("Aucune provenance renseignée."),
    )


def _by_acquisition(items, choices) -> Table:
    counts = dict(
        items.values_list("acquisition_source")
        .annotate(n=Count("id"))
        .values_list("acquisition_source", "n")
    )
    total = items.count()
    rows = [
        [str(label), fmt.number(counts.get(value, 0)), fmt.percent(counts.get(value, 0), total)]
        for value, label in choices.choices
        if counts.get(value)
    ]
    return Table(
        title=_("Comment ils sont arrivés"),
        columns=[Column(_("Origine")), Column(_("Livres"), "right"), Column(_("Part"), "right")],
        rows=rows,
        empty_text=_("Aucune origine renseignée."),
    )


def _new_items(period) -> Table:
    from apps.catalog.models import Item

    rows_qs = (
        Item.objects.filter(
            created_at__date__gte=period.start, created_at__date__lte=period.end
        )
        .values("record__category__name")
        .annotate(n=Count("id"), titles=Count("record_id", distinct=True))
        .order_by("-n")
    )
    rows_list = list(rows_qs)
    rows = [
        [row["record__category__name"] or _("Sans rayon"),
         fmt.number(row["titles"]), fmt.number(row["n"])]
        for row in rows_list
    ]
    total_items = sum(row["n"] for row in rows_list)
    return Table(
        title=_("Les livres entrés pendant la période"),
        columns=[Column(_("Rayon")), Column(_("Titres nouveaux"), "right"),
                 Column(_("Exemplaires"), "right")],
        rows=rows,
        total_row=[_("Total"), "", fmt.number(total_items)] if rows else None,
        empty_text=_("Aucun livre catalogué pendant cette période."),
    )


def _donors(period) -> Table:
    from apps.catalog.models import AcquisitionSource, Item

    rows_qs = (
        Item.objects.filter(
            acquisition_source=AcquisitionSource.DONATION,
            created_at__date__gte=period.start,
            created_at__date__lte=period.end,
        )
        .exclude(donor="")
        .values("donor")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    rows = [[row["donor"], fmt.number(row["n"])] for row in rows_qs]
    return Table(
        title=_("Les dons reçus pendant la période"),
        columns=[Column(_("Donateur")), Column(_("Livres donnés"), "right")],
        rows=rows,
        empty_text=_("Aucun don enregistré pendant cette période."),
    )


def _dormant() -> Table:
    """Les livres en rayon depuis plus d'un an et jamais sortis, par rayon.

    Le filtre d'ancienneté et l'exclusion des exemplaires hors circulation
    viennent de la revue Grok : sans eux, l'indicateur compte les nouveautés
    et les livres pilonnés, et accuse à tort les rayons qu'on vient d'enrichir.
    """
    from apps.catalog.models import Item

    cutoff = date.today() - timedelta(days=DORMANT_MIN_AGE_DAYS)
    rows_qs = (
        Item.objects.filter(created_at__date__lte=cutoff, loans__isnull=True)
        .exclude(status__in=OUT_OF_CIRCULATION)
        .values("record__category__name")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    rows = [
        [row["record__category__name"] or _("Sans rayon"), fmt.number(row["n"])]
        for row in rows_qs
    ]
    return Table(
        title=_("Les livres qui n'ont jamais servi"),
        columns=[Column(_("Rayon")), Column(_("Livres"), "right")],
        rows=rows,
        empty_text=_("Tous les livres en rayon depuis plus d'un an sont sortis au moins une fois."),
        note=_(
            "Comptés : les livres en rayon depuis plus d'un an et jamais empruntés. "
            "Les nouveautés, les livres perdus, pilonnés ou en réparation sont écartés."
        ),
    )


def _full_catalogue() -> Table:
    """Le catalogue complet, exemplaire par exemplaire. FEAT-093 (retour Val).

    C'est l'ancien « Catalogue complet (CSV) » du hub, devenu un sous-rapport de
    cet écran : il a donc désormais un écran, et ses exports PDF et Excel comme
    les autres. Le CSV reste offert à côté, avec ses vingt-trois colonnes, pour
    la reprise dans un tableur — ici on montre les colonnes qu'on lit.
    """
    from apps.catalog.models import Item

    rows = [
        [
            item.internal_id,
            item.record.title,
            "; ".join(a.full_name for a in item.record.authors.all()) or "—",
            item.record.category.name if item.record.category else "—",
            item.location.code if item.location else "—",
            item.get_state_display(),
            item.get_status_display(),
        ]
        for item in (
            Item.objects.select_related("record", "record__category", "location")
            .prefetch_related("record__authors")
            .order_by("record__title", "internal_id")
        )
    ]
    return Table(
        title=_("Le catalogue complet"),
        columns=[
            Column(_("N° du livre")), Column(_("Titre")), Column(_("Auteurs")),
            Column(_("Rayon")), Column(_("Emplacement")), Column(_("État")),
            Column(_("Situation")),
        ],
        rows=rows,
        empty_text=_("Aucun exemplaire au catalogue."),
        note=_(
            "Un exemplaire par ligne. Pour reprendre le catalogue dans un tableur avec "
            "toutes les colonnes (ISBN, éditeur, année, tags…), utilisez l'export CSV "
            "proposé sous ce tableau."
        ),
    )
