"""L'icône du guide et le script qui la déplace restent d'accord."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from header_home import PUBLIC_HOME, app_href  # noqa: E402

JS = Path(__file__).resolve().parent / "docs" / "javascripts" / "header-links.js"

CASES = [
    ("/docs/", "/fr/"),
    ("/docs", "/fr/"),
    ("/docs/index.html", "/fr/"),
    ("/docs/reservations/creer/", "/fr/"),
    ("/docs/en/", "/en/"),
    ("/docs/en/premiers-pas/connexion/", "/en/"),
    ("/docs/es/", "/es/"),
    ("/docs/mg/faq/", "/mg/"),
    ("/bibliofelia/docs/", "/bibliofelia/fr/"),
    ("/bibliofelia/docs/en/faq/", "/bibliofelia/en/"),
    ("/bibliofelia/docs/reservations/creer/", "/bibliofelia/fr/"),
    ("/", PUBLIC_HOME),
    ("/en/", PUBLIC_HOME),
    ("/reservations/creer/", PUBLIC_HOME),
]


def test_app_href_keeps_the_language_and_the_prefix():
    for pathname, expected in CASES:
        assert app_href(pathname) == expected


def test_javascript_matches_the_python_cases():
    node = shutil.which("node")
    assert node, "node est requis pour vérifier header-links.js"
    runner = Path(tempfile.gettempdir()) / "bo-header-check.js"
    runner.write_text(
        "const h = require(" + json.dumps(JS.as_posix()) + ");\n"
        "const cases = " + json.dumps(CASES) + ";\n"
        "for (const [pathname, expected] of cases) {\n"
        "  const got = h.appHref(pathname);\n"
        "  if (got !== expected) {\n"
        "    console.error(pathname + ' -> ' + got + ' != ' + expected);\n"
        "    process.exit(1);\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    subprocess.check_call([node, str(runner)])
