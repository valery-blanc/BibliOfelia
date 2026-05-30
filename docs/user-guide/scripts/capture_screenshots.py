"""Capture des screenshots de BibliOfelia via Playwright (Sprint 15 Task 3).

Couvre les ~22 pages du sommaire v2 du guide utilisateur.

Prerequis :
    python -m venv .venv-doc
    .venv-doc\\Scripts\\activate
    pip install -r requirements-doc.txt
    playwright install chromium

    docker compose -f docker-compose.dev.yml up
    docker compose -f docker-compose.dev.yml exec web python manage.py seed_demo --reset

Lancement :
    python docs/user-guide/scripts/capture_screenshots.py
    python docs/user-guide/scripts/capture_screenshots.py --only dashboard,lend
    python docs/user-guide/scripts/capture_screenshots.py --lang en
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, sync_playwright

BASE_URL = "http://localhost:8001"
USERNAME = "demo_librarian"
PASSWORD = "OfeliaDemo2026!"
ROOT = Path(__file__).resolve().parent.parent
VIEWPORT = {"width": 1440, "height": 900}


def login(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/accounts/login/")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="username"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")


def switch_language(page: Page, base_url: str, lang: str) -> None:
    """Force la langue via le selecteur du header (cookie + redirection)."""
    page.goto(f"{base_url}/{lang}/")
    page.wait_for_load_state("networkidle")


def _first_pk_from_list(page: Page, base_url: str, lang: str, list_path: str) -> int | None:
    """Charge la liste et extrait le pk numerique du premier lien de detail."""
    import re
    page.goto(f"{base_url}/{lang}{list_path}")
    page.wait_for_load_state("networkidle")
    # Trouve tous les href finissant par /<int>/ qui contiennent list_path
    pattern = re.compile(rf"^/{lang}{re.escape(list_path)}(\d+)/$")
    hrefs = page.eval_on_selector_all(
        "a[href]", "els => els.map(e => e.getAttribute('href'))"
    )
    for href in hrefs:
        if href:
            m = pattern.match(href)
            if m:
                return int(m.group(1))
    return None


def open_first_record(page: Page, base_url: str, lang: str) -> int | None:
    pk = _first_pk_from_list(page, base_url, lang, "/catalog/")
    if pk:
        page.goto(f"{base_url}/{lang}/catalog/{pk}/")
        page.wait_for_load_state("networkidle")
    return pk


def open_first_member(page: Page, base_url: str, lang: str) -> int | None:
    pk = _first_pk_from_list(page, base_url, lang, "/members/")
    if pk:
        page.goto(f"{base_url}/{lang}/members/{pk}/")
        page.wait_for_load_state("networkidle")
    return pk


# Pages a capturer.
# Tuple : (group, name, url_path, full_page)
# Les URLs sont sans prefixe langue ; le LocaleMiddleware redirige.
PAGES: list[tuple[str, str, str, bool]] = [
    # Premiers pas
    ("premiers-pas", "login", "/accounts/login/", False),
    ("premiers-pas", "dashboard", "/", True),
    ("premiers-pas", "help", "/help/", True),
    ("premiers-pas", "advanced", "/advanced/", True),
    # Catalogue
    ("catalogue", "record-list", "/catalog/", True),
    ("catalogue", "record-create", "/catalog/new/", True),
    ("catalogue", "location-list", "/catalog/locations/", True),
    ("catalogue", "location-create", "/catalog/locations/new/", True),
    # Usagers
    ("usagers", "member-list", "/members/", True),
    ("usagers", "member-create", "/members/new/", True),
    # Prets et retours
    ("prets-retours", "lend", "/loans/lend/", True),
    ("prets-retours", "return", "/loans/return/", True),
    ("prets-retours", "consultation", "/loans/consultation/", True),
    # Reservations
    ("reservations", "reservation-list", "/loans/reservations/", True),
    # Impressions
    ("impressions", "cards-picker", "/printing/cards/", True),
    ("impressions", "labels-picker", "/printing/labels/", True),
    # Rapports
    ("rapports", "reports-index", "/reports/", True),
    ("rapports", "overdue-list", "/reports/overdue/", True),
    ("rapports", "reservations-pickup", "/reports/reservations-pickup/", True),
    ("rapports", "inactive", "/reports/inactive/", True),
]


def capture(page: Page, out_dir: Path, group: str, name: str, full_page: bool) -> None:
    out = out_dir / group / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=full_page)
    print(f"  -> {out.relative_to(out_dir.parent.parent)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture screenshots BibliOfelia")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--lang", default="fr", choices=["fr", "en", "es", "mg"])
    parser.add_argument("--only", default=None,
                        help="Liste de noms separes par , pour filtrer")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args(argv)

    only = set(args.only.split(",")) if args.only else None
    out_dir = ROOT / "docs" / "assets" / "screenshots" / args.lang
    print(f"Capture vers {out_dir}")
    print(f"  base URL : {args.base_url}    lang : {args.lang}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(
            viewport=VIEWPORT,
            locale=f"{args.lang}-{args.lang.upper()}",
        )
        page = ctx.new_page()

        # Pre-auth pages
        page.goto(f"{args.base_url}/{args.lang}/accounts/login/")
        page.wait_for_load_state("networkidle")
        if not only or "login" in only:
            capture(page, out_dir, "premiers-pas", "login", full_page=False)

        # Login + bascule de langue
        login(page, args.base_url)
        switch_language(page, args.base_url, args.lang)

        # Pages standard
        for group, name, path, full_page in PAGES:
            if name == "login":
                continue
            if only and name not in only:
                continue
            url = f"{args.base_url}/{args.lang}{path}"
            try:
                page.goto(url)
                page.wait_for_load_state("networkidle")
                capture(page, out_dir, group, name, full_page=full_page)
            except Exception as exc:  # noqa: BLE001
                print(f"  !! {name}: {exc}")

        # Captures dynamiques (record_detail, member_detail)
        if not only or "record-detail" in only:
            rec_pk = open_first_record(page, args.base_url, args.lang)
            if rec_pk:
                capture(page, out_dir, "catalogue", "record-detail", full_page=True)
                page.goto(f"{args.base_url}/{args.lang}/catalog/{rec_pk}/items/new/")
                page.wait_for_load_state("networkidle")
                capture(page, out_dir, "catalogue", "item-create", full_page=True)
            else:
                print("  !! record-detail: aucune notice trouvee")

        if not only or "member-detail" in only:
            mem_pk = open_first_member(page, args.base_url, args.lang)
            if mem_pk:
                capture(page, out_dir, "usagers", "member-detail", full_page=True)
                page.goto(f"{args.base_url}/{args.lang}/members/{mem_pk}/history/")
                page.wait_for_load_state("networkidle")
                capture(page, out_dir, "usagers", "member-history", full_page=True)
            else:
                print("  !! member-detail: aucun membre trouve")

        browser.close()

    print(f"\nOK — capture terminee : {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
