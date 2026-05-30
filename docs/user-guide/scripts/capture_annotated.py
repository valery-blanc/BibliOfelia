"""Capture annotee : meme page que capture_screenshots.py, mais avec
des encadres rouges + pastilles numerotees rajoutees a partir de selectors
CSS (coords pixel-perfect via Playwright bounding_box).

Utilise pour les pages-cles du guide ou il faut guider l'oeil du lecteur
(boutons critiques, sequences d'actions numerotees).

    python docs/user-guide/scripts/capture_annotated.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from playwright.sync_api import Page, sync_playwright

# Permet d'importer annotate.py depuis le meme dossier
sys.path.insert(0, str(Path(__file__).resolve().parent))
from annotate import annotate  # noqa: E402

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


def boxes_from_selectors(
    page: Page,
    items: Iterable[tuple[str, str]],
    padding: int = 6,
) -> list[tuple[int, int, int, int, str]]:
    """Pour chaque (selector, label), renvoie le rect (x1,y1,x2,y2,label)
    enrichi d'un petit padding pour bien encadrer l'element."""
    boxes: list[tuple[int, int, int, int, str]] = []
    for sel, label in items:
        loc = page.locator(sel).first
        bbox = loc.bounding_box()
        if not bbox:
            print(f"  !! selector introuvable : {sel}")
            continue
        x1 = int(bbox["x"]) - padding
        y1 = int(bbox["y"]) - padding
        x2 = int(bbox["x"] + bbox["width"]) + padding
        y2 = int(bbox["y"] + bbox["height"]) + padding
        boxes.append((x1, y1, x2, y2, label))
    return boxes


def capture_annotated(
    page: Page,
    out_path: Path,
    url: str,
    selectors_labels: list[tuple[str, str]],
    full_page: bool = False,
) -> None:
    page.goto(url)
    page.wait_for_load_state("networkidle")
    raw = out_path.with_suffix(".raw.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(raw), full_page=full_page)
    boxes = boxes_from_selectors(page, selectors_labels)
    annotate(raw, out_path, boxes=boxes)
    raw.unlink()
    print(f"  -> {out_path.relative_to(ROOT)}  ({len(boxes)} annotations)")


def main() -> int:
    out_dir = ROOT / "docs" / "assets" / "screenshots" / "fr"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, locale="fr-FR")
        page = ctx.new_page()
        login(page, BASE_URL)

        # /loans/lend/ — 4 points cles numerotes
        capture_annotated(
            page,
            out_dir / "prets-retours" / "lend-annotated.png",
            url=f"{BASE_URL}/fr/loans/lend/",
            selectors_labels=[
                ('input[name="card"]', "1"),
                ('button.js-scan-handoff[data-scan-kind="card"]', "2"),
                ('input[name="ean"]', "3"),
                ('button.js-scan-handoff[data-scan-kind="book"]', "4"),
            ],
            full_page=True,
        )

        browser.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
