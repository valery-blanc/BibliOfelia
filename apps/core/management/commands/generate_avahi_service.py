"""Génère le fichier de service Avahi pour la découverte mDNS d'OfeliaScan.

SPEC §6.10 (Découverte mDNS / DNS-SD) / SPEC-CORR-001 §7.

Publie un service DNS-SD `_bibliofelia._tcp.` qu'OfeliaScan recherche sur le
réseau local. Le fichier rendu est déposé dans `/etc/avahi/services/` (dossier
monté depuis l'hôte Raspberry Pi) ; `avahi-daemon`, géré par systemd sur
l'hôte, surveille ce dossier et recharge automatiquement.

Idempotent. Appelé par le wizard de premier démarrage (Task #15) après saisie
du nom de la bibliothèque, et exécutable à la main au déploiement.
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.models import Setting

TEMPLATE = """\
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>{name}</name>
  <service>
    <type>_bibliofelia._tcp</type>
    <port>{port}</port>
    <txt-record>library_name={library_name}</txt-record>
    <txt-record>version={version}</txt-record>
    <txt-record>api_base={api_base}</txt-record>
  </service>
</service-group>
"""


def render_avahi_service() -> str:
    """Rend le XML du service Avahi à partir des Setting et réglages courants.

    `box_name` et `library_name` proviennent du modèle Setting (renseignés par
    le wizard, §11.3) ; `version` et `api_base` des réglages Django. Toutes les
    valeurs interpolées sont échappées pour le XML.
    """
    box_name = Setting.get("box_name", "OfeliaBox")
    library_name = Setting.get("library_name", "BibliOfelia")
    return TEMPLATE.format(
        name=escape(str(box_name)),
        port=int(settings.MDNS_SERVICE_PORT),
        library_name=escape(str(library_name)),
        version=escape(str(settings.BIBLIOFELIA_VERSION)),
        api_base=escape(str(settings.API_BASE_PATH)),
    )


class Command(BaseCommand):
    help = "Génère le fichier de service Avahi pour la découverte mDNS (SPEC §6.10)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            help="Chemin du fichier à écrire (défaut : settings.AVAHI_SERVICE_PATH).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Affiche le XML sans écrire de fichier (vérification).",
        )

    def handle(self, *args, **options):
        xml = render_avahi_service()

        if options["dry_run"]:
            self.stdout.write(xml)
            return

        target = Path(options["output"] or settings.AVAHI_SERVICE_PATH)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(xml, encoding="utf-8")
        except OSError as exc:
            raise CommandError(
                f"Impossible d'écrire {target} : {exc}. Sur la Pi, "
                "/etc/avahi/services/ doit être monté en écriture dans le "
                "conteneur (cf. FEAT-019)."
            ) from exc

        self.stdout.write(self.style.SUCCESS(f"Service Avahi écrit : {target}"))
