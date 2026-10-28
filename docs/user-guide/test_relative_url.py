"""Le sélecteur de langue du guide ne doit jamais émettre un lien en `/…`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relative_url import relative_href  # noqa: E402


def test_homepage_languages_stay_relative():
    assert relative_href("/en/", "") == "en/"
    assert relative_href("/es/", ".") == "es/"
    assert relative_href("/mg/", "index.html") == "mg/"
    assert relative_href("/", "") == "./"


def test_language_home_points_at_the_other_language_home():
    assert relative_href("/", "en/") == "../"
    assert relative_href("/es/", "en/") == "../es/"
    assert relative_href("/en/", "en/") == "./"


def test_nested_page_keeps_the_same_chapter():
    page = "premiers-pas/connexion/"
    assert (
        relative_href("/en/premiers-pas/connexion/", page)
        == "../../en/premiers-pas/connexion/"
    )
    assert relative_href("./", page) == "./"


def test_translated_page_climbs_back_to_french():
    page = "en/premiers-pas/connexion/"
    assert (
        relative_href("/premiers-pas/connexion/", page)
        == "../../../premiers-pas/connexion/"
    )
    assert relative_href("/en/premiers-pas/connexion/", page) == "./"
