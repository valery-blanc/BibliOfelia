"""Description d'un écran de rapport. FEAT-093.

La règle posée par Val — « pas d'écran sans export PDF et Excel, pas d'export
sans écran » — ne tient pas si l'écran et ses exports sont écrits séparément :
au troisième écran, l'un des trois diverge, et le PDF qu'on tend à un donateur
ne dit plus la même chose que la page qu'on lui a montrée.

Un écran produit donc **un objet** `ReportPage`, et trois moteurs le rendent :
le gabarit HTML, `pdf.render_report_pdf`, `excel.render_report_xlsx`. Ajouter un
écran = écrire une fonction `build_…(period, params) -> ReportPage` et
l'inscrire au registre ; les trois sorties suivent sans une ligne de plus.

Chaque bloc est un **sous-rapport** : il porte une clé stable, se cite dans le
sommaire de l'écran et s'exporte seul.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date


def _key(title: str) -> str:
    """Clé stable d'un bloc, dérivée de son titre.

    Un index de position changerait de sens dès qu'on réordonne un écran, et un
    lien d'export partagé par courriel pointerait alors sur un autre tableau.
    """
    return "b" + hashlib.md5(title.encode("utf-8")).hexdigest()[:8]


@dataclass
class Period:
    """Fenêtre de temps d'un rapport, avec son libellé prêt à afficher."""

    start: date
    end: date
    label: str
    key: str = "custom"

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


@dataclass
class Kpi:
    """Un compteur. `hint` porte la comparaison ou l'unité, jamais l'essentiel."""

    label: str
    value: str
    hint: str = ""
    color: str = "burgundy"


@dataclass
class Column:
    label: str
    align: str = "left"  # left | right


@dataclass
class Series:
    """Une courbe d'un graphe en lignes."""

    label: str
    values: list[float] = field(default_factory=list)


@dataclass
class Chart:
    """Un graphe. `kind` vaut `bar`, `pie` ou `line` — pas d'autre forme.

    Les libellés et les valeurs sont déjà prêts : le tracé ne calcule rien, il
    dessine. C'est ce qui permet au SVG, au PDF et au fichier Excel de montrer
    exactement les mêmes barres.
    """

    title: str
    kind: str
    labels: list[str] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    series: list[Series] = field(default_factory=list)
    unit: str = ""
    note: str = ""

    @property
    def key(self) -> str:
        return _key(self.title)

    @property
    def is_empty(self) -> bool:
        # Un graphe à séries (courbes, histogramme groupé) n'a rien dans
        # `values` : c'est `series` qui le remplit.
        if self.series:
            return not self.labels or not any(any(s.values) for s in self.series)
        return not self.values or not any(self.values)

    @property
    def total(self) -> float:
        return sum(self.values)

    def pairs(self) -> list[tuple[str, float]]:
        return list(zip(self.labels, self.values))


@dataclass
class Table:
    """Un tableau, éventuellement accompagné du graphe des **mêmes** données.

    `chart` n'est pas un graphe voisin mais la même information sous une autre
    forme : l'écran et le PDF les posent côte à côte, moitié-moitié, et le
    fichier Excel les met sur la même feuille. Un chiffre ne doit exister qu'une
    fois dans la page.
    """

    title: str
    columns: list[Column]
    rows: list[list] = field(default_factory=list)
    total_row: list | None = None
    empty_text: str = ""
    note: str = ""
    chart: Chart | None = None

    @property
    def key(self) -> str:
        return _key(self.title)

    @property
    def is_empty(self) -> bool:
        return not self.rows


@dataclass
class ReportPage:
    slug: str
    title: str
    subtitle: str = ""
    kpis: list[Kpi] = field(default_factory=list)
    blocks: list = field(default_factory=list)  # Chart | Table, dans l'ordre affiché
    period: Period | None = None
    note: str = ""
    query: str = ""  # paramètres à recopier dans les liens d'export
    filters: dict = field(default_factory=dict)  # réglages propres à l'écran

    @property
    def tables(self) -> list[Table]:
        return [b for b in self.blocks if isinstance(b, Table)]

    @property
    def charts(self) -> list[Chart]:
        """Les graphes de la page, ceux appariés à un tableau compris."""
        out = [b for b in self.blocks if isinstance(b, Chart)]
        out += [b.chart for b in self.tables if b.chart is not None]
        return out

    def block(self, key: str):
        """Le sous-rapport de clé `key`, ou None."""
        for item in self.blocks:
            if item.key == key:
                return item
        return None

    def filename(self, extension: str, block=None) -> str:
        """`fonds_2026-01-01_2026-09-09.pdf` — le nom dit la période exportée."""
        stem = self.slug
        if block is not None:
            stem = f"{self.slug}_{block.key}"
        if self.period:
            stem = f"{stem}_{self.period.start.isoformat()}_{self.period.end.isoformat()}"
        else:
            stem = f"{stem}_{date.today().isoformat()}"
        return f"{stem}.{extension}"
