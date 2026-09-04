"""Moteur de recherche de devise. FEAT-088."""
from __future__ import annotations

import json

import pytest

from apps.core.forms import FinanceConfigForm
from apps.core.models import Setting
from apps.finance import currencies

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------
# Catalogue
# ----------------------------------------------------------------------
def test_only_currencies_in_circulation_are_listed():
    """Babel connaît 306 codes ISO 4217, dont des monnaies mortes (franc
    français, mark…) qu'il serait absurde de proposer."""
    codes = {c.code for c in currencies.catalogue("fr")}
    assert "CHF" in codes and "VES" in codes and "MGA" in codes
    assert "FRF" not in codes
    assert "DEM" not in codes
    assert 100 < len(codes) < 250


def test_the_three_instance_currencies_are_available():
    codes = {c.code for c in currencies.catalogue("fr")}
    for code in ("CHF", "VES", "ARS", "EUR", "USD", "MGA"):
        assert code in codes


def test_countries_are_attached_to_the_currency():
    chf = currencies.describe("CHF", language="fr")
    assert chf is not None
    assert "Suisse" in chf.countries_display


# ----------------------------------------------------------------------
# Recherche : trigramme, nom, pays
# ----------------------------------------------------------------------
def test_search_by_full_code():
    assert currencies.search("CHF", language="fr")[0].code == "CHF"


def test_search_by_partial_code():
    codes = [c.code for c in currencies.search("VE", language="fr")]
    assert "VES" in codes


def test_search_by_country_name():
    """Demande Val : « une partie ou tout le nom du pays »."""
    codes = [c.code for c in currencies.search("Suisse", language="fr")]
    assert "CHF" in codes
    codes = [c.code for c in currencies.search("Venez", language="fr")]
    assert "VES" in codes


def test_search_by_currency_name():
    codes = [c.code for c in currencies.search("bolivar", language="fr")]
    assert "VES" in codes


def test_search_ignores_accents():
    """« pérou » doit se trouver en tapant « perou »."""
    with_accent = [c.code for c in currencies.search("pérou", language="fr")]
    without = [c.code for c in currencies.search("perou", language="fr")]
    assert with_accent == without
    assert "PEN" in without


def test_search_is_case_insensitive():
    assert currencies.search("chf", language="fr")[0].code == "CHF"


def test_exact_code_comes_first():
    """`ARS` ne doit pas être noyé sous les devises dont un pays contient
    « ars » (Marshall, Marseille…)."""
    assert currencies.search("ARS", language="fr")[0].code == "ARS"


def test_one_letter_returns_the_suggestions_not_the_whole_list():
    """« Le moteur attend la 2ᵉ lettre » (Val). Une lettre remonterait la
    moitié de la liste ; on rend les devises des instances existantes."""
    results = currencies.search("c", language="fr")
    assert [c.code for c in results] == list(currencies.SUGGESTED)


def test_empty_query_returns_the_suggestions():
    results = currencies.search("", language="fr")
    assert [c.code for c in results] == list(currencies.SUGGESTED)


def test_nonsense_query_returns_nothing():
    assert currencies.search("zzzzzz", language="fr") == []


# ----------------------------------------------------------------------
# Langues
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "language,needle,code",
    [
        ("fr", "Suisse", "CHF"),
        ("en", "Switzerland", "CHF"),
        ("es", "Suiza", "CHF"),
        ("mg", "Soisa", "CHF"),
    ],
)
def test_country_search_works_in_every_language(language, needle, code):
    """Les libellés viennent du CLDR de Babel, pas de nos .po — mais ils
    doivent bien être servis dans la langue demandée."""
    assert code in [c.code for c in currencies.search(needle, language=language)]


def test_currency_name_is_localised():
    assert currencies.describe("CHF", language="fr").name != currencies.describe(
        "CHF", language="es"
    ).name


def test_missing_cldr_name_falls_back_to_the_code():
    """Le CLDR malgache ne nomme pas toutes les devises : on garde le code
    plutôt qu'une chaîne vide."""
    ves = currencies.describe("VES", language="mg")
    assert ves is not None
    assert ves.name


def test_unknown_language_falls_back_to_english():
    assert currencies.catalogue("xx-XX") == currencies.catalogue("en")


# ----------------------------------------------------------------------
# Précision
# ----------------------------------------------------------------------
def test_precision_follows_the_currency():
    assert currencies.precision("MGA") == 0
    assert currencies.precision("CHF") == 2


def test_precision_of_an_unknown_code_defaults_to_two():
    assert currencies.precision("ZZZ") == 2


# ----------------------------------------------------------------------
# Endpoint
# ----------------------------------------------------------------------
def test_search_endpoint_returns_json(client, superadmin):
    client.force_login(superadmin)
    resp = client.get("/fr/finance/currencies/?q=suisse")
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert any(row["code"] == "CHF" for row in data["results"])
    assert data["min_length"] == currencies.MIN_QUERY_LENGTH


def test_search_endpoint_is_superadmin_only(client, librarian):
    client.force_login(librarian)
    assert client.get("/fr/finance/currencies/?q=chf").status_code == 403


# ----------------------------------------------------------------------
# Formulaire de réglage
# ----------------------------------------------------------------------
def test_form_accepts_a_code():
    form = FinanceConfigForm(
        {"currency": "ves", "decimals": "", "payment_terms_days": "30"}
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["currency"] == "VES"


def test_form_accepts_an_unambiguous_free_text():
    """Une recherche tapée puis validée au clavier, sans passer par la liste,
    ne doit pas être rejetée quand elle est sans ambiguïté."""
    form = FinanceConfigForm(
        {"currency": "Suisse", "decimals": "", "payment_terms_days": "30"}
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["currency"] == "CHF"


def test_form_refuses_a_dead_currency():
    form = FinanceConfigForm(
        {"currency": "FRF", "decimals": "", "payment_terms_days": "30"}
    )
    assert not form.is_valid()
    assert "currency" in form.errors


def test_form_refuses_nonsense():
    form = FinanceConfigForm(
        {"currency": "zzzzzz", "decimals": "", "payment_terms_days": "30"}
    )
    assert not form.is_valid()


def test_form_refuses_an_ambiguous_free_text():
    form = FinanceConfigForm(
        {"currency": "franc", "decimals": "", "payment_terms_days": "30"}
    )
    assert not form.is_valid()
    assert "plusieurs" in str(form.errors["currency"])


def test_decimals_default_to_the_currency_precision():
    form = FinanceConfigForm(
        {"currency": "MGA", "decimals": "", "payment_terms_days": "30"}
    )
    assert form.is_valid(), form.errors
    form.save()
    assert Setting.get("finance_config")["decimals"] == 0


def test_explicit_decimals_win_over_the_default():
    form = FinanceConfigForm(
        {"currency": "MGA", "decimals": "2", "payment_terms_days": "30"}
    )
    assert form.is_valid(), form.errors
    form.save()
    assert Setting.get("finance_config")["decimals"] == 2


def test_settings_page_renders_the_search_field(client, superadmin):
    client.force_login(superadmin)
    resp = client.get("/fr/admin/settings/finance/")
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "data-currency-search" in html
    # Plus de liste déroulante : c'est tout l'objet de FEAT-088.
    assert "<select" not in html.split('name="currency"')[0][-400:]
