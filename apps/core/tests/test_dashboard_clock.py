"""FEAT-077 — horloge de la Box sur l'accueil.

La Box perd son horloge quand on la coupe. Afficher *sa* date et *son* heure
sur l'accueil permet au bibliothécaire de s'en apercevoir sans rien chercher —
à condition que ce soit bien l'heure du serveur qui s'affiche, pas celle du
poste, sinon un poste à l'heure masquerait une Box déréglée.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role
from apps.core.models import Setting

pytestmark = pytest.mark.django_db

_CLOCK_RE = re.compile(r'data-clock="([^"]+)"')


@pytest.fixture
def librarian(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )
    client.force_login(user)
    return user


def _clock(client) -> datetime:
    body = client.get(reverse("core:dashboard")).content.decode()
    match = _CLOCK_RE.search(body)
    assert match, "attribut data-clock absent de l'accueil"
    return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")


def test_dashboard_publishes_the_server_clock(client, librarian):
    """L'horodatage rendu doit être celui du serveur, à la seconde près."""
    served = _clock(client)
    now = timezone.localtime(timezone.now()).replace(tzinfo=None)
    assert abs(served - now) < timedelta(seconds=30)


def test_clock_is_not_read_from_the_browser(client, librarian):
    """Le gabarit ne doit jamais fabriquer l'heure côté client : `new Date()`
    sans argument réintroduirait l'horloge du poste."""
    source = (
        Path(settings.BASE_DIR) / "templates" / "core" / "dashboard.html"
    ).read_text(encoding="utf-8")
    script = source[source.index("hero-clock"):]
    assert "new Date(box.dataset.clock" in script
    assert "new Date()" not in script


def test_dashboard_shows_date_and_time(client, librarian):
    body = client.get(reverse("core:dashboard")).content.decode()
    assert "hero-clock-time" in body
    assert "hero-clock-date" in body
    assert timezone.localtime(timezone.now()).strftime("%H:%M") in body


def test_dashboard_shows_the_timezone_abbreviation(client, librarian):
    """Une heure sans fuseau ne se vérifie pas : on affiche CEST, Caracas…"""
    Setting.set("timezone", "Europe/Zurich")
    body = client.get(reverse("core:dashboard")).content.decode()
    assert "hero-clock-tz" in body
    assert timezone.localtime(timezone.now()).strftime("%Z") in body


def test_city_is_shown_when_the_zone_has_no_literal_abbreviation(client, librarian):
    """« -04 » n'apprend rien à un bibliothécaire : on affiche « Caracas »
    (Val, 2026-08-22)."""
    Setting.set("timezone", "America/Caracas")
    body = client.get(reverse("core:dashboard")).content.decode()
    assert ">Caracas<" in body
    assert ">-04<" not in body


def test_multiword_city_is_readable(client, librarian):
    Setting.set("timezone", "America/Argentina/San_Juan")
    body = client.get(reverse("core:dashboard")).content.decode()
    assert ">San Juan<" in body


def test_refresh_script_never_overwrites_the_timezone(client, librarian):
    """Le sigle disparaissait au bout de 15 s : le script écrasait tout le bloc
    heure, fuseau compris. L'heure a désormais son propre span."""
    source = (
        Path(settings.BASE_DIR) / "templates" / "core" / "dashboard.html"
    ).read_text(encoding="utf-8")
    script = source[source.index("var box = document.querySelector"):]
    assert "hero-clock-hm" in script
    assert "querySelector('.hero-clock-time')" not in script


def test_setting_overrides_the_system_timezone(client, librarian):
    """Le réglage des Paramètres l'emporte sur le `TZ` de la machine."""
    Setting.set("timezone", "America/Argentina/San_Juan")
    buenos_aires = _clock(client)
    Setting.set("timezone", "Europe/Zurich")
    zurich = _clock(client)
    # Zurich est en avance sur San Juan (UTC+1/+2 contre UTC-3).
    assert timedelta(hours=3) <= (zurich - buenos_aires) <= timedelta(hours=7)


def test_blank_setting_falls_back_to_the_system_timezone(client, librarian):
    """Réglage vide = fuseau du système : c'est le cas de la Box."""
    Setting.set("timezone", "")
    served = _clock(client)
    now = timezone.localtime(timezone.now()).replace(tzinfo=None)
    assert abs(served - now) < timedelta(seconds=30)


def test_unknown_timezone_is_ignored_not_fatal(client, librarian):
    """Une valeur aberrante en base ne doit pas mettre l'application à terre."""
    Setting.set("timezone", "Mars/Olympus_Mons")
    resp = client.get(reverse("core:dashboard"))
    assert resp.status_code == 200


def test_timezone_form_rejects_an_unknown_zone():
    from apps.core.forms import TimezoneForm

    form = TimezoneForm(data={"name": "Mars/Olympus_Mons"})
    assert not form.is_valid()


def test_timezone_choices_show_abbreviation_and_offset():
    """Le nom IANA seul ne se choisit pas : on ne devine pas qu'une bibliothèque
    de Canaima veut `America/Caracas` (Val, 2026-08-22)."""
    from apps.core.forms import TimezoneForm

    labels = dict(TimezoneForm._choices())
    assert labels["Europe/Zurich"].startswith("Europe/Zurich — ")
    assert "(UTC+" in labels["Europe/Zurich"]
    assert labels["America/Caracas"] == "America/Caracas (UTC-4)"
    assert "-04" not in labels["America/Caracas"]
    assert labels["Asia/Kolkata"] == "Asia/Kolkata — IST (UTC+5:30)"


def test_numeric_abbreviations_are_not_repeated():
    """La base IANA a retiré les sigles littéraux d'Amérique du Sud :
    `America/Caracas` renvoie `-04`. Inutile d'écrire « -04 (UTC-4) »."""
    from apps.core.forms import TimezoneForm

    label = TimezoneForm._label("America/Argentina/San_Juan")
    assert label == "America/Argentina/San_Juan (UTC-3)"
    assert "-03" not in label


def test_every_timezone_is_selectable():
    """La liste reste exhaustive : une bibliothèque peut être n'importe où."""
    import zoneinfo

    from apps.core.forms import TimezoneForm

    values = {value for value, _label in TimezoneForm._choices()}
    assert values >= zoneinfo.available_timezones()
    assert "" in values  # « Fuseau du système »


def test_timezone_form_saves_and_is_offered_in_settings(client, django_user_model):
    from apps.core.admin_views import FORMS
    from apps.core.forms import TimezoneForm

    assert FORMS["timezone"][1] is TimezoneForm

    admin = django_user_model.objects.create_user(
        username="chef", password="motdepasse123", role=Role.SUPERADMIN
    )
    client.force_login(admin)
    resp = client.post(
        reverse("core:settings_section", kwargs={"section": "timezone"}),
        {"name": "Europe/Zurich"},
    )
    assert resp.status_code == 302
    assert Setting.get("timezone") == "Europe/Zurich"


def test_timezone_is_configurable_per_instance():
    """Sans fuseau réglable, chaque bibliothèque hors UTC croirait sa Box
    déréglée en permanence (FEAT-077). Le défaut reste UTC."""
    source = (
        Path(settings.BASE_DIR) / "config" / "settings" / "base.py"
    ).read_text(encoding="utf-8")
    assert 'TIME_ZONE = env("TZ")' in source
    assert 'TZ=(str, "UTC")' in source
