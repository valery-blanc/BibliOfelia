"""Tests de la génération du service Avahi (mDNS). SPEC §6.10 / FEAT-019."""
from io import StringIO

import pytest
from django.core.management import call_command

from apps.core.management.commands.generate_avahi_service import render_avahi_service
from apps.core.models import Setting


@pytest.mark.django_db
class TestAvahiServiceRender:
    def test_render_contains_service_type_and_port(self):
        xml = render_avahi_service()
        assert "_bibliofelia._tcp" in xml
        assert "<port>80</port>" in xml

    def test_render_includes_txt_records(self):
        xml = render_avahi_service()
        assert "library_name=" in xml
        assert "version=" in xml
        assert "api_base=" in xml

    def test_render_uses_setting_values(self):
        Setting.set("box_name", "OfeliaBox-Tulear")
        Setting.set("library_name", "Bibliothèque de Tuléar")
        xml = render_avahi_service()
        assert "<name>OfeliaBox-Tulear</name>" in xml
        assert "library_name=Bibliothèque de Tuléar" in xml

    def test_render_escapes_xml_special_chars(self):
        Setting.set("library_name", "Livres & Cie")
        xml = render_avahi_service()
        assert "Livres &amp; Cie" in xml
        assert "Livres & Cie" not in xml


@pytest.mark.django_db
class TestGenerateAvahiCommand:
    def test_dry_run_prints_xml(self):
        out = StringIO()
        call_command("generate_avahi_service", "--dry-run", stdout=out)
        assert "_bibliofelia._tcp" in out.getvalue()

    def test_output_option_writes_file(self, tmp_path):
        target = tmp_path / "bibliofelia.service"
        call_command("generate_avahi_service", "--output", str(target))
        content = target.read_text(encoding="utf-8")
        assert "service-group" in content
        assert "_bibliofelia._tcp" in content
