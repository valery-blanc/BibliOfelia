"""Vérifie que toutes les chaînes traduisibles sont effectivement traduites.

Solution pérenne au problème récurrent : à chaque feature, des `{% trans %}` ou
`gettext(...)` apparaissent sans qu'on remette à jour les `.po` EN/ES/MG.

Usage local (avant commit) :

    docker compose -f docker-compose.dev.yml exec -T web \
        python manage.py makemessages -a --no-obsolete -l en -l es -l mg
    python scripts/i18n_check.py

Exit code :
- 0 si tous les `.po` de en/es/mg ont 0 `msgstr ""` et 0 `#, fuzzy`.
  Les formes plurielles (`msgstr[0]`, `msgstr[1]`) sont auditées depuis le
  Sprint 28 : elles échappaient au contrôle et sortaient en français.
- 1 sinon : affiche la liste des chaînes manquantes/fuzzy, locale par locale.

Le script est volontairement sans dépendance externe (stdlib uniquement) pour
pouvoir tourner en pre-commit, en CI, ou en local.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent / "locale"
LANGS = ["en", "es", "mg"]
MAX_PRINT_PER_LANG = 30


def _unquote(raw: str) -> str:
    """Concatène les morceaux d'une valeur msgid/msgstr multilignes.

    Les fichiers .po sont déjà en UTF-8 et n'ont qu'à voir leurs `\\"` / `\\n`
    déséchappés. Pas de `unicode_escape` (qui casserait les accents UTF-8).
    """
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith('"') and line.endswith('"'):
            chunk = line[1:-1]
            chunk = chunk.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
            out.append(chunk)
    return "".join(out)


def audit(po_path: Path) -> tuple[list[str], list[str]]:
    """Renvoie (empty_msgids, fuzzy_msgids)."""
    lines = po_path.read_text(encoding="utf-8").splitlines(keepends=True)
    empty: list[str] = []
    fuzzy: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("msgid "):
            i += 1
            continue
        # Détecter `#, fuzzy` au-dessus (commentaires consécutifs)
        j = i - 1
        is_fuzzy = False
        while j >= 0 and lines[j].startswith("#"):
            if "fuzzy" in lines[j]:
                is_fuzzy = True
            j -= 1
        start = i
        i += 1
        while i < len(lines) and lines[i].startswith('"'):
            i += 1
        msgid_block = lines[start][len("msgid "):] + "".join(lines[start + 1:i])
        msgid = _unquote(msgid_block)
        # Bloc pluriel : `msgid_plural` puis `msgstr[0]`, `msgstr[1]`… Ces blocs
        # étaient ignorés jusqu'au Sprint 28 — un `{% blocktrans count %}` non
        # traduit passait donc le gate sans bruit, et la page sortait en français
        # dans les 3 autres langues.
        if i < len(lines) and lines[i].startswith("msgid_plural "):
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                i += 1
            forms: list[str] = []
            while i < len(lines) and lines[i].startswith("msgstr["):
                start_form = i
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    i += 1
                head = lines[start_form]
                value = head[head.index(" ") + 1:] + "".join(lines[start_form + 1:i])
                forms.append(_unquote(value))
            if msgid:
                if not all(forms):
                    empty.append(msgid)
                elif is_fuzzy:
                    fuzzy.append(msgid)
            continue

        if i < len(lines) and lines[i].startswith("msgstr "):
            ms_start = i
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                i += 1
            msgstr_block = lines[ms_start][len("msgstr "):] + "".join(lines[ms_start + 1:i])
            msgstr = _unquote(msgstr_block)
            if msgid:  # ignore l'entrée d'en-tête (msgid vide)
                if not msgstr:
                    empty.append(msgid)
                elif is_fuzzy:
                    fuzzy.append(msgid)
    return empty, fuzzy


def main() -> int:
    failures = 0
    for lang in LANGS:
        po = ROOT / lang / "LC_MESSAGES" / "django.po"
        if not po.exists():
            print(f"[{lang}] django.po introuvable ({po})", file=sys.stderr)
            failures += 1
            continue
        empty, fuzzy = audit(po)
        if not empty and not fuzzy:
            print(f"[{lang}] OK — 0 chaîne manquante.")
            continue
        failures += 1
        print(
            f"[{lang}] {len(empty)} non traduites, {len(fuzzy)} fuzzy "
            f"({po.relative_to(ROOT.parent)})"
        )
        for tag, items in (("non traduit", empty), ("fuzzy", fuzzy)):
            for s in items[:MAX_PRINT_PER_LANG]:
                short = s if len(s) <= 90 else s[:87] + "..."
                print(f"  [{tag}] {short!r}")
            if len(items) > MAX_PRINT_PER_LANG:
                print(f"  ...et {len(items) - MAX_PRINT_PER_LANG} autres.")

    if failures:
        print(
            "\n[FAIL] Traductions manquantes. Workflow recommandé :\n"
            "  1) `docker compose -f docker-compose.dev.yml exec -T web "
            "python manage.py makemessages -a --no-obsolete`\n"
            "  2) compléter `locale/{en,es,mg}/LC_MESSAGES/django.po`\n"
            "     (ou enrichir `scripts/apply_translations.py` puis le rejouer)\n"
            "  3) relancer `python scripts/i18n_check.py`.\n"
            "\n"
            "Règle BibliOfelia : aucune chaîne FR ne doit rester en dur dans une "
            "page sans `{% trans %}` ou `_()`, et aucune chaîne traduisible ne "
            "doit rester sans traduction EN/ES/MG.",
            file=sys.stderr,
        )
        return 1
    print("\n[OK] Toutes les traductions EN/ES/MG sont complètes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
