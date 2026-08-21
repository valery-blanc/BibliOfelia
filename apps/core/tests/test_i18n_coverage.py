"""BUG-028 (élargi) — les chaînes visibles passent toutes par gettext.

`scripts/i18n_check.py` vérifie que les chaînes **extraites** sont traduites, et
`test_form_labels.py` que les libellés de formulaire sont bien extraits. Restent
trois angles morts, couverts ici :

1. du texte français en dur dans un template, hors `{% trans %}` ;
2. un message / une `ValidationError` / un `help_text` Python sans `_()` ;
3. un libellé de `TextChoices` ou un `verbose_name` de `Meta` sans `_()`.

Aucun de ces cas n'apparaît dans les `.po` : sans ce test, la page sort en
français dans les trois autres langues sans que rien ne proteste.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

import pytest
from django.conf import settings

# Accents ou mots-outils français : suffisant pour repérer une phrase oubliée,
# sans se déclencher sur du balisage ou des identifiants techniques.
FRENCH = re.compile(
    r"[àâäéèêëîïôöùûüçÀÉÈÊÎÔÙÇ]"
    r"|\b(?:le|la|les|un|une|des|du|de|et|ou|pour|avec|dans|sur|par|est|sont|aux?)\b",
    re.I,
)

# `handler500` n'exécute ni les context processors ni le middleware de langue :
# la page ne peut pas être traduite et porte ses textes en 4 langues en dur.
# L'exception est documentée dans le template lui-même.
TEMPLATE_EXCEPTIONS = {"500.html"}


def _templates_root() -> Path:
    return Path(settings.BASE_DIR) / "templates"


def _apps_root() -> Path:
    return Path(settings.BASE_DIR) / "apps"


def _visible_text(html: str) -> str:
    """Ne garde que ce qu'un lecteur voit, hors balises et hors tags Django."""
    html = re.sub(r"\{%\s*blocktrans.*?\{%\s*endblocktrans\s*%\}", " ", html, flags=re.S)
    html = re.sub(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", " ", html, flags=re.S)
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    html = re.sub(r"\{%.*?%\}", " ", html, flags=re.S)
    html = re.sub(r"\{\{.*?\}\}", " ", html, flags=re.S)
    html = re.sub(r"\{#.*?#\}", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", "\n", html)


def test_templates_have_no_hardcoded_french():
    root = _templates_root()
    offenders = []
    for path in sorted(root.glob("**/*.html")):
        if path.name in TEMPLATE_EXCEPTIONS:
            continue
        for line in _visible_text(io.open(path, encoding="utf-8").read()).splitlines():
            text = line.strip()
            if len(text) >= 4 and FRENCH.search(text):
                offenders.append(f"{path.relative_to(root)} : {text[:60]}")

    assert not offenders, (
        "Texte français en dur dans un template — entourez-le de "
        "`{% trans %}` ou `{% blocktrans %}` :\n  " + "\n  ".join(offenders)
    )


def test_python_messages_go_through_gettext():
    root = _apps_root()
    pattern = re.compile(
        r"(messages\.\w+\(\s*request,\s*|ValidationError\(\s*|help_text\s*=\s*)"
        r"(\"[^\"]{4,}\"|'[^']{4,}')"
    )
    offenders = []
    for path in sorted(root.glob("**/*.py")):
        posix = path.as_posix()
        if "/tests/" in posix or "/migrations/" in posix:
            continue
        text = io.open(path, encoding="utf-8").read()
        for match in pattern.finditer(text):
            if FRENCH.search(match.group(2)):
                line = text[: match.start()].count("\n") + 1
                offenders.append(
                    f"{path.relative_to(root)}:{line} : {match.group(2)[:60]}"
                )

    assert not offenders, (
        "Chaîne française sans `_()` (message, erreur de validation ou aide de "
        "champ) :\n  " + "\n  ".join(offenders)
    )


def test_model_choices_and_meta_are_translatable():
    root = _apps_root()
    choice = re.compile(r"=\s*\"[a-z_0-9-]+\",\s*(\"[^\"]+\")")
    meta = re.compile(r"verbose_name(?:_plural)?\s*=\s*(\"[^\"]+\"|'[^']+')")
    offenders = []
    for path in sorted(root.glob("**/models.py")):
        text = io.open(path, encoding="utf-8").read()
        for pattern, kind in ((choice, "choix"), (meta, "verbose_name")):
            for match in pattern.finditer(text):
                if FRENCH.search(match.group(1)):
                    line = text[: match.start()].count("\n") + 1
                    offenders.append(
                        f"{path.relative_to(root)}:{line} : {kind} {match.group(1)[:50]}"
                    )

    assert not offenders, (
        "Libellé de modèle sans `_()` — il ne sera jamais traduit :\n  "
        + "\n  ".join(offenders)
    )


def test_the_audit_actually_reads_files():
    """Garde-fou : si les chemins cassent, les tests ci-dessus passeraient à vide."""
    assert len(list(_templates_root().glob("**/*.html"))) > 30
    assert len(list(_apps_root().glob("**/models.py"))) > 5
