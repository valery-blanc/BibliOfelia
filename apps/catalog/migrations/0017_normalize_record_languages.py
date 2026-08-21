"""FEAT-070 — normalisation des codes langue hérités des sources en ligne.

Les notices importées de la BnF portent des codes composites (`fre-fre`,
`fre-eng`, `eng-fre`) : la source y met la langue du texte puis celle de
l'original. Ces valeurs n'apparaissaient dans aucun filtre. On garde la première
langue et on la convertit en abréviation internationale à 2 lettres.

Un code déjà normalisé est laissé tel quel ; un code inconnu est conservé (on ne
perd jamais une donnée qu'on ne sait pas nommer). Migration réversible dans le
sens où elle ne détruit rien : la marche arrière est un no-op assumé, les codes
d'origine ne sont pas restaurables et n'ont pas d'intérêt.
"""
from django.db import migrations

_ISO_639_2_TO_1 = {
    "fre": "fr", "fra": "fr", "eng": "en", "spa": "es", "por": "pt",
    "ita": "it", "ger": "de", "deu": "de", "ara": "ar", "alb": "sq",
    "sqi": "sq", "tur": "tr", "rus": "ru", "srp": "sh", "hrv": "sh",
    "tam": "ta", "chi": "zh", "zho": "zh", "pol": "pl", "per": "fa",
    "fas": "fa", "gre": "el", "ell": "el", "som": "so", "rum": "ro",
    "ron": "ro", "ukr": "uk", "jpn": "ja", "mlg": "mg",
}


def _normalize(raw: str) -> str:
    code = (raw or "").strip().lower().replace("_", "-")
    if not code:
        return ""
    first = code.split("-", 1)[0]
    return _ISO_639_2_TO_1.get(first, first)


def normalize_languages(apps, schema_editor):
    Record = apps.get_model("catalog", "BibliographicRecord")
    updates = []
    for pk, language in Record.objects.values_list("pk", "language"):
        normalized = _normalize(language)
        if normalized != (language or ""):
            updates.append((pk, normalized))
    for pk, normalized in updates:
        Record.objects.filter(pk=pk).update(language=normalized)


def noop(apps, schema_editor):
    """Marche arrière : rien à faire, aucun code d'origine n'a été détruit."""


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0016_language"),
    ]

    operations = [
        migrations.RunPython(normalize_languages, noop),
    ]
