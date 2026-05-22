"""Vues d'administration UI (§6.6 « Paramètres »).

Distinctes du `/admin/` Django : les bibliothécaires y accèdent (rôle
SUPERADMIN exclusivement pour modifier — LIBRARIAN en lecture le cas échéant).
"""
from __future__ import annotations

import secrets
import socket
import string

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Role
from apps.accounts.permissions import require_role

from .forms import (
    BackupConfigForm,
    LabelFormatForm,
    LanguagesForm,
    LibraryIdentityForm,
    ZeroTierForm,
)
from .models import Setting


from django.views.decorators.http import require_POST


FORMS = {
    "identity": ("Identité", LibraryIdentityForm),
    "languages": ("Langues", LanguagesForm),
    "backup": ("Sauvegardes", BackupConfigForm),
    "labels": ("Étiquettes", LabelFormatForm),
    "zerotier": ("ZeroTier", ZeroTierForm),
}


@require_role(Role.SUPERADMIN)
def settings_index(request):
    return render(request, "core/admin/settings_index.html", {
        "sections": FORMS,
    })


@require_role(Role.SUPERADMIN)
def settings_section(request, section: str):
    if section not in FORMS:
        return redirect("core:settings_index")
    label, form_cls = FORMS[section]
    if request.method == "POST":
        form = form_cls(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Paramètres %(label)s enregistrés.") % {"label": label})
            return redirect("core:settings_section", section=section)
    else:
        form = form_cls()
    return render(request, "core/admin/settings_section.html", {
        "form": form, "section": section, "label": label, "sections": FORMS,
    })


@require_POST
@require_role(Role.SUPERADMIN)
def backup_now(request):
    """Déclenche une sauvegarde manuelle. SPEC §8."""
    from apps.tasks.backup import run_backup

    result = run_backup(force_daily=True)
    if result.status == "ok":
        messages.success(request, _("Sauvegarde effectuée : %(p)s") % {"p": result.db_path})
    else:
        messages.error(request, _("Échec sauvegarde : %(e)s") % {"e": result.error})
    return redirect("core:settings_section", section="backup")


@require_role(Role.SUPERADMIN)
def backup_restore(request):
    """Upload d'un .sqlite3 / .sqlite3.gz à restaurer. SPEC §8.3."""
    from apps.tasks.backup import restore_from_file

    error = ""
    if request.method == "POST":
        upload = request.FILES.get("archive")
        if not upload:
            error = _("Aucun fichier fourni.")
        else:
            import tempfile, os
            suffix = ".sqlite3.gz" if upload.name.endswith(".gz") else ".sqlite3"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in upload.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            try:
                restore_from_file(tmp_path)
                messages.warning(
                    request,
                    _("Restauration terminée. Redémarrez l'application avant tout autre usage."),
                )
                return redirect("core:settings_section", section="backup")
            except Exception as exc:
                error = str(exc)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
    return render(request, "core/admin/backup_restore.html", {"error": error})


# ----------------------------------------------------------------------
# Connexion OfeliaScan : identifiants API + adresse de la box
# ----------------------------------------------------------------------
def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _box_addresses(request) -> dict:
    """Adresses par lesquelles OfeliaScan peut joindre la box."""
    info = {"request_host": request.get_host(), "hostname": "", "lan_ip": ""}
    try:
        info["hostname"] = socket.gethostname()
    except OSError:
        pass
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.2)
        sock.connect(("8.8.8.8", 80))  # ne transmet rien (UDP) : choisit l'interface
        info["lan_ip"] = sock.getsockname()[0]
        sock.close()
    except OSError:
        try:
            info["lan_ip"] = socket.gethostbyname(socket.gethostname())
        except OSError:
            pass
    return info


@require_role(Role.SUPERADMIN)
def ofeliascan_access(request):
    """Identifiants autorisés pour l'app mobile OfeliaScan + adresse de la box.

    OfeliaScan s'authentifie sur l'API via `POST /auth/login` (JWT). Les
    comptes utilisés sont de rôle `contributor_api`. Le mot de passe est
    stocké **en clair** dans `Setting.ofeliascan_credentials` pour que le
    bibliothécaire puisse le relire et le saisir sur le terminal mobile
    (cas d'usage proche d'un mot de passe Wi-Fi affiché : box hors-ligne,
    rôle à faible privilège — catalogage uniquement).
    """
    from apps.accounts.models import Role as R, User

    creds = Setting.get("ofeliascan_credentials", []) or []

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add":
            username = (request.POST.get("username") or "").strip()
            password = (request.POST.get("password") or "").strip()
            if not username:
                messages.error(request, _("Identifiant requis."))
            else:
                existing = User.objects.filter(username=username).first()
                if existing and existing.role != R.CONTRIBUTOR_API:
                    messages.error(
                        request,
                        _("Cet identifiant est déjà utilisé par un autre compte."),
                    )
                else:
                    if not password:
                        password = _generate_password()
                    user = existing or User(username=username)
                    user.role = R.CONTRIBUTOR_API
                    user.is_active = True
                    user.set_password(password)
                    user.save()
                    creds = [c for c in creds if c.get("username") != username]
                    creds.append({
                        "username": username,
                        "password": password,
                        "created_at": timezone.now().isoformat(),
                    })
                    Setting.set("ofeliascan_credentials", creds,
                                "Identifiants OfeliaScan (rôle contributor_api)")
                    messages.success(
                        request, _("Identifiant « %(u)s » autorisé.") % {"u": username})
            return redirect("core:ofeliascan")
        if action == "revoke":
            username = request.POST.get("username") or ""
            User.objects.filter(
                username=username, role=R.CONTRIBUTOR_API
            ).update(is_active=False)
            creds = [c for c in creds if c.get("username") != username]
            Setting.set("ofeliascan_credentials", creds,
                        "Identifiants OfeliaScan (rôle contributor_api)")
            messages.warning(
                request, _("Identifiant « %(u)s » révoqué.") % {"u": username})
            return redirect("core:ofeliascan")

    return render(request, "core/admin/ofeliascan.html", {
        "credentials": creds,
        "box": _box_addresses(request),
        "box_name": Setting.get("box_name", "BibliOfelia"),
        "api_path": settings.API_BASE_PATH,
        "suggested_password": _generate_password(),
    })


@require_role(Role.SUPERADMIN)
def diagnostics(request):
    """Bundle diag rapide : versions, état backup, ZeroTier, queue."""
    from django_q.models import Schedule, Task as QTask
    from apps.reports.services import system_status

    return render(request, "core/admin/diagnostics.html", {
        "status": system_status(),
        "last_settings": Setting.objects.order_by("-updated_at")[:20],
        "q_recent_tasks": QTask.objects.all()[:20],
        "q_schedules": Schedule.objects.all(),
    })
