"""Liste tous les msgid avec msgstr vide dans le .po EN."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
# Import sans déclencher l'application des traductions
import importlib.util
spec = importlib.util.spec_from_file_location(
    "apply_translations",
    Path(__file__).parent / "apply_translations.py",
)
# On lit juste les fonctions et le dict sans exécuter le for au bas du fichier
mod_source = (Path(__file__).parent / "apply_translations.py").read_text(encoding="utf-8")
# Strip le for principal (qui appelle process_file)
trimmed = mod_source.split("\nfor lang in")[0]
exec_globals = {
    "__name__": "__main__",
    "__file__": str(Path(__file__).parent / "apply_translations.py"),
}
exec(compile(trimmed, "apply_translations.py", "exec"), exec_globals)
unquote_po = exec_globals["unquote_po"]

po = Path(__file__).parent.parent / "locale" / "en" / "LC_MESSAGES" / "django.po"
lines = po.read_text(encoding="utf-8").splitlines(keepends=True)

i = 0
problems = []  # (msgid, "empty" | "fuzzy")
while i < len(lines):
    line = lines[i]
    if line.startswith("msgid "):
        # Remonter pour voir s'il y a un marqueur fuzzy dans les commentaires
        j = i - 1
        is_fuzzy = False
        while j >= 0 and lines[j].startswith("#"):
            if lines[j].startswith("#, fuzzy") or "fuzzy" in lines[j]:
                is_fuzzy = True
            j -= 1
        start = i
        i += 1
        while i < len(lines) and lines[i].startswith('"'):
            i += 1
        msgid_raw = lines[start][len("msgid "):] + "".join(lines[start + 1:i])
        msgid_text = unquote_po(msgid_raw)
        if i < len(lines) and lines[i].startswith("msgstr "):
            ms_start = i
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                i += 1
            msgstr_raw = lines[ms_start][len("msgstr "):] + "".join(lines[ms_start + 1:i])
            msgstr_text = unquote_po(msgstr_raw)
            if msgid_text:
                if not msgstr_text:
                    problems.append((msgid_text, "empty"))
                elif is_fuzzy:
                    problems.append((msgid_text, "fuzzy"))
        continue
    i += 1

print(f"=== {len(problems)} msgid à traduire (empty + fuzzy) ===")
for s, status in problems:
    if len(s) > 100:
        s = s[:97] + "..."
    marker = "[F]" if status == "fuzzy" else "[ ]"
    print(f"  {marker} {s!r}")
