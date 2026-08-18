"""BUG-026 — aucun commentaire `{# … #}` multi-ligne dans les templates.

Le lexer Django compile `({%.*?%}|{{.*?}}|{#.*?#})` **sans** `re.DOTALL` : un
commentaire `{# … #}` étalé sur plusieurs lignes n'est pas reconnu comme un
token et se retrouve **affiché tel quel** dans la page. Le piège s'est déjà
refermé au Sprint 9 puis à BUG-024 (message visible sur `/catalog/scan/<pk>/`).
Pour les commentaires multi-lignes : `{% comment %}…{% endcomment %}`.
"""
from __future__ import annotations

import re
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
# Un `{#` dont le `#}` n'est pas sur la même ligne.
UNCLOSED_INLINE_COMMENT = re.compile(r"\{#(?![^\n]*#\})")


def test_no_multiline_django_comment_in_templates():
    offenders = []
    for path in TEMPLATES_DIR.rglob("*.html"):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if UNCLOSED_INLINE_COMMENT.search(line):
                rel = path.relative_to(TEMPLATES_DIR)
                offenders.append(f"{rel}:{lineno}")
    assert not offenders, (
        "Commentaires `{# … #}` multi-lignes (affichés à l'écran par Django) — "
        "utiliser {% comment %} : " + ", ".join(offenders)
    )
