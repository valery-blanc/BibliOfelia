"""Logique du wizard : application finale des choix accumulés en session.

Séparé des vues pour être testable. SPEC §11.3.
"""
from __future__ import annotations

import secrets
import string
from dataclasses import dataclass


@dataclass
class WizardCompletion:
    superadmin_username: str
    recovery_key: str
    demo_installed: bool
    avahi_written: bool


def generate_recovery_key(length: int = 32) -> str:
    """Clé hex affichée à imprimer (§9.3)."""
    alphabet = string.ascii_uppercase + string.digits
    return "-".join(
        "".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(length // 4)
    )


def apply_wizard(session_data: dict) -> WizardCompletion:
    """Applique les choix du wizard.

    `session_data` est attendu sous forme `{step_n: cleaned_data, ...}`.
    """
    from django.contrib.auth.hashers import make_password
    from django.core.management import call_command

    from apps.accounts.models import Role, User
    from apps.core.models import Setting

    s2 = session_data.get("step2", {})  # library
    s3 = session_data.get("step3", {})  # languages
    s4 = session_data.get("step4", {})  # superadmin
    s5 = session_data.get("step5", {})  # printer
    s6 = session_data.get("step6", {})  # backup
    s7 = session_data.get("step7", {})  # zerotier
    s8 = session_data.get("step8", {})  # demo

    # 1. Identité
    Setting.set("library_name", s2.get("name", "BibliOfelia"))
    Setting.set("box_name", s2.get("box_name", "BibliOfelia"))
    Setting.set("library_identity", {
        "name": s2.get("name", ""),
        "box_name": s2.get("box_name", ""),
        "address": s2.get("address", ""),
    })

    # 2. Langues
    if s3.get("enabled"):
        Setting.set("languages_config", {
            "enabled": s3["enabled"], "default": s3.get("default", "fr"),
        })

    # 3. Superadmin
    user, _ = User.objects.get_or_create(
        username=s4["username"],
        defaults={
            "first_name": s4.get("first_name", ""),
            "last_name": s4.get("last_name", ""),
            "email": s4.get("email", ""),
        },
    )
    user.role = Role.SUPERADMIN
    user.is_superuser = True
    user.is_staff = True
    user.password = make_password(s4["password"])
    user.save()

    # 4. Imprimante
    if s5:
        Setting.set("printer_config", {
            "enabled": bool(s5.get("enabled")),
            "cups_host": s5.get("cups_host", ""),
        })

    # 5. Backup
    if s6:
        Setting.set("backup_config", {
            "usb_path": s6.get("usb_path", "/backup"),
            "hourly_enabled": bool(s6.get("hourly_enabled", True)),
            "cloud_enabled": bool(s6.get("cloud_enabled")),
            "cloud_remote": s6.get("cloud_remote", ""),
        })

    # 6. ZeroTier
    if s7:
        Setting.set("zerotier", {
            "network_id": s7.get("network_id", ""),
            "status": "pending" if s7.get("enabled") else "disabled",
        })

    # 7. Recovery key
    rkey = generate_recovery_key()
    Setting.set("recovery_key_hash", make_password(rkey),
                "Hash de la clé de récupération (§9.3)")

    # 8. Démo
    demo_installed = False
    if s8.get("install_demo"):
        from .demo import install_demo

        install_demo()
        demo_installed = True

    # 9. Schedules django-q2 + service Avahi
    try:
        call_command("setup_schedules")
    except Exception:
        pass

    avahi_written = False
    try:
        call_command("generate_avahi_service")
        avahi_written = True
    except Exception:
        pass

    # 10. Marquer le wizard terminé
    Setting.set("setup_completed", True, "Wizard d'installation terminé")

    return WizardCompletion(
        superadmin_username=user.username,
        recovery_key=rkey,
        demo_installed=demo_installed,
        avahi_written=avahi_written,
    )
