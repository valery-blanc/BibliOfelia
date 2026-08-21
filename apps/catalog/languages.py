"""FEAT-070 : helpers de langue, partagés catalogue et usagers.

La liste vit en base (`catalog.Language`) : elle est extensible par les
bibliothécaires. Ce module l'expose sous la forme attendue par les formulaires
et normalise les codes hérités des sources en ligne.
"""
from __future__ import annotations

from django.utils.translation import gettext_lazy as _

# ISO 639-2/B (ce que renvoient la BnF et les sources SRU) → ISO 639-1.
_ISO_639_2_TO_1 = {
    "fre": "fr", "fra": "fr", "eng": "en", "spa": "es", "por": "pt",
    "ita": "it", "ger": "de", "deu": "de", "ara": "ar", "alb": "sq",
    "sqi": "sq", "tur": "tr", "rus": "ru", "srp": "sh", "hrv": "sh",
    "tam": "ta", "chi": "zh", "zho": "zh", "pol": "pl", "per": "fa",
    "fas": "fa", "gre": "el", "ell": "el", "som": "so", "rum": "ro",
    "ron": "ro", "ukr": "uk", "jpn": "ja", "mlg": "mg",
}


def normalize_language_code(raw: str) -> str:
    """Ramène un code de langue à son abréviation internationale principale.

    Les notices importées portent des codes composites (`fre-fre`, `fre-eng`,
    `eng-fre`) : la BnF y met la langue du texte puis celle de l'original. On
    garde la première et on la convertit en code à 2 lettres.

    Un code inconnu est renvoyé tel quel, en minuscules : on ne perd jamais une
    donnée qu'on ne sait pas nommer.
    """
    code = (raw or "").strip().lower().replace("_", "-")
    if not code:
        return ""
    first = code.split("-", 1)[0]
    return _ISO_639_2_TO_1.get(first, first)


def language_choices(include_blank: bool = True) -> list[tuple[str, object]]:
    """Langues de la base, triées par libellé **dans la langue de l'interface**.

    Le tri se fait donc à l'affichage et change d'une langue à l'autre : c'est
    l'ordre alphabétique attendu par le lecteur, pas celui d'une locale figée.
    """
    from .models import Language

    rows = [(lang.code, str(lang)) for lang in Language.objects.all()]
    rows.sort(key=lambda row: row[1].lower())
    if include_blank:
        return [("", _("— non précisée —"))] + rows
    return rows


def label_for(code: str) -> str:
    """Libellé d'un code, ou le code brut s'il n'est pas dans la liste."""
    from .models import Language

    if not code:
        return ""
    lang = Language.objects.filter(code=code).first()
    return str(lang) if lang else code
