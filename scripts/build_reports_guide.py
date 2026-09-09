#!/usr/bin/env python3
"""Génère la page « Tous les rapports » du guide utilisateur. FEAT-093.

La liste des rapports et de leurs sous-rapports **ne s'écrit pas à la main** :
chaque sous-rapport est atteint par une ancre dérivée de son titre
(`pages._key`), et ce titre est traduit. Une ancre recopiée à la main serait
fausse dans trois langues sur quatre, et se périmerait au premier
renommage. On interroge donc le registre, langue par langue.

À rejouer après tout ajout, retrait ou renommage de rapport :

    docker compose exec -T web python scripts/build_reports_guide.py

Écrit `docs/user-guide/docs/rapports/liste{,.en,.es,.mg}.md`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import django

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.utils import translation  # noqa: E402

from apps.reports import builders, periods  # noqa: E402
from apps.reports.pages import Table  # noqa: E402

GUIDE = Path(__file__).resolve().parent.parent / "docs/user-guide/docs/rapports"

# Le guide est servi à côté de l'application, sous le même préfixe.
APP_BASE = "/bibliofelia/{lang}/reports"

LANGS = ["fr", "en", "es", "mg"]

# Prose de la page. Traduite ici plutôt que par gettext : ce texte n'appartient
# pas à l'application, il appartient au guide.
TEXT = {
    "fr": {
        "title": "Tous les rapports",
        "intro": (
            "Cette page liste **tous les rapports** et, pour chacun, **tous ses "
            "tableaux et graphes**. Chaque titre est un lien : cliquez dessus pour "
            "aller directement à ce que vous cherchez.\n\n"
            "Servez-vous de la **recherche** du guide (en haut de la page) pour "
            "retrouver un chiffre par son nom — « factures », « dons », "
            "« présences » — puis suivez le lien."
        ),
        "work": "À faire aujourd'hui",
        "work_intro": (
            "Les listes de travail. Elles décrivent **aujourd'hui** : elles n'ont "
            "pas de période à choisir."
        ),
        "stats": "Les chiffres de la bibliothèque",
        "stats_intro": (
            "Ces écrans se lisent **sur une période**, que vous choisissez en haut "
            "de l'écran : les 12 derniers mois, un mois, une année, ou deux dates "
            "de votre choix."
        ),
        "open": "Ouvrir",
        "sub": "Ce qu'on y trouve",
        "exports": (
            "Chaque écran s'imprime en PDF et s'enregistre en Excel, en entier ou "
            "**tableau par tableau** : les deux petits liens sous un titre "
            "n'exportent que ce tableau-là."
        ),
        "generated": (
            "Page produite automatiquement par `scripts/build_reports_guide.py` à "
            "partir des écrans réels. Ne la modifiez pas à la main."
        ),
    },
    "en": {
        "title": "All reports",
        "intro": (
            "This page lists **every report** and, for each one, **all its tables "
            "and charts**. Every title is a link: click it to go straight to what "
            "you are looking for.\n\n"
            "Use the guide's **search** (top of the page) to find a figure by "
            "name — “invoices”, “gifts”, “attendance” — "
            "then follow the link."
        ),
        "work": "To do today",
        "work_intro": (
            "The working lists. They describe **today**: there is no period to "
            "choose."
        ),
        "stats": "The library's figures",
        "stats_intro": (
            "These screens cover **a period**, which you choose at the top of the "
            "screen: the last 12 months, a month, a year, or two dates of your own."
        ),
        "open": "Open",
        "sub": "What you will find there",
        "exports": (
            "Every screen prints to PDF and saves to Excel, whole or **table by "
            "table**: the two small links under a title export that table only."
        ),
        "generated": (
            "This page is produced automatically by "
            "`scripts/build_reports_guide.py` from the real screens. Do not edit "
            "it by hand."
        ),
    },
    "es": {
        "title": "Todos los informes",
        "intro": (
            "Esta página enumera **todos los informes** y, de cada uno, **todas sus "
            "tablas y gráficos**. Cada título es un enlace: haga clic para ir "
            "directamente a lo que busca.\n\n"
            "Use la **búsqueda** de la guía (arriba de la página) para encontrar "
            "una cifra por su nombre — «facturas», «donaciones», «asistencias» — "
            "y siga el enlace."
        ),
        "work": "Por hacer hoy",
        "work_intro": (
            "Las listas de trabajo. Describen **hoy**: no hay período que elegir."
        ),
        "stats": "Las cifras de la biblioteca",
        "stats_intro": (
            "Estas pantallas cubren **un período**, que usted elige arriba de la "
            "pantalla: los últimos 12 meses, un mes, un año, o dos fechas suyas."
        ),
        "open": "Abrir",
        "sub": "Lo que encontrará allí",
        "exports": (
            "Cada pantalla se imprime en PDF y se guarda en Excel, entera o **tabla "
            "por tabla**: los dos enlaces pequeños bajo un título exportan solo esa "
            "tabla."
        ),
        "generated": (
            "Página generada automáticamente por "
            "`scripts/build_reports_guide.py` a partir de las pantallas reales. No "
            "la modifique a mano."
        ),
    },
    "mg": {
        "title": "Ny tatitra rehetra",
        "intro": (
            "Ity pejy ity dia mitanisa ny **tatitra rehetra** ary, ho an'ny "
            "tsirairay, ny **tabilao sy sary rehetra** ao aminy. Rohy ny lohateny "
            "tsirairay : tsindrio mba handeha mivantana amin'izay tadiavinao.\n\n"
            "Ampiasao ny **fikarohana** eo amin'ny tampon'ny pejy mba hitadiavana "
            "isa amin'ny anarany — « faktiora », « fanomezana », « fanatrehana » — "
            "dia araho ny rohy."
        ),
        "work": "Atao androany",
        "work_intro": (
            "Ny lisitry ny asa. Mamaritra ny **androany** izy ireo : tsy misy "
            "vanim-potoana fidiana."
        ),
        "stats": "Ny isan'ny tranomboky",
        "stats_intro": (
            "Ireto efijery ireto dia mikasika **vanim-potoana** iray, izay fidianao "
            "eo ambony : ny volana 12 farany, volana iray, taona iray, na daty roa "
            "safidianao."
        ),
        "open": "Sokafy",
        "sub": "Izay hita ao",
        "exports": (
            "Ny efijery tsirairay dia atonta PDF ary tehirizina Excel, manontolo na "
            "**isaky ny tabilao** : ny rohy kely roa eo ambanin'ny lohateny dia tsy "
            "mamoaka afa-tsy io tabilao io."
        ),
        "generated": (
            "Pejy novokarin'ny `scripts/build_reports_guide.py` avy amin'ny efijery "
            "tena misy. Aza ovaina an-tanana."
        ),
    },
}


def collect(lang: str) -> list[dict]:
    """Les écrans et leurs sous-rapports, titrés dans `lang`.

    On construit chaque page pour de vrai : c'est la seule façon d'obtenir les
    titres et les clés exactement tels que l'écran les produira. Les données de
    la base n'importent pas ici — les blocs sont créés quoi qu'il arrive.
    """
    out = []
    with translation.override(lang):
        period = periods.default_period()
        for spec in builders.REPORTS:
            page = spec.builder(period if spec.needs_period else None, {})
            out.append({
                "slug": spec.slug,
                "group": spec.group,
                "title": str(spec.title),
                "description": str(spec.description),
                "blocks": [
                    {
                        "title": block.title,
                        "key": block.key,
                        "kind": "table" if isinstance(block, Table) else "chart",
                        "paired": isinstance(block, Table) and block.chart is not None,
                    }
                    for block in page.blocks
                ],
            })
    return out


def render(lang: str, screens: list[dict]) -> str:
    text = TEXT[lang]
    base = APP_BASE.format(lang=lang)
    lines = [f"# {text['title']}", "", text["intro"], "", f"!!! tip\n    {text['exports']}", ""]

    for group, heading, intro in (
        (builders.GROUP_WORK, text["work"], text["work_intro"]),
        (builders.GROUP_STATS, text["stats"], text["stats_intro"]),
    ):
        lines += [f"## {heading}", "", intro, ""]
        for screen in (s for s in screens if s["group"] == group):
            url = f"{base}/{screen['slug']}/"
            lines += [
                f"### [{screen['title']}]({url}){{ target=\"_blank\" }}",
                "",
                screen["description"],
                "",
                f"**{text['sub']} :**" if lang == "fr" else f"**{text['sub']}:**",
                "",
            ]
            for block in screen["blocks"]:
                anchor = f"{url}#{block['key']}"
                lines.append(f"- [{block['title']}]({anchor}){{ target=\"_blank\" }}")
            lines.append("")

    lines += ["---", "", f"*{text['generated']}*", ""]
    return "\n".join(lines)


def main() -> int:
    GUIDE.mkdir(parents=True, exist_ok=True)
    for lang in LANGS:
        screens = collect(lang)
        suffix = "" if lang == "fr" else f".{lang}"
        path = GUIDE / f"liste{suffix}.md"
        path.write_bytes(render(lang, screens).encode("utf-8"))
        blocks = sum(len(s["blocks"]) for s in screens)
        print(f"[{lang}] {path.name} — {len(screens)} écrans, {blocks} sous-rapports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
