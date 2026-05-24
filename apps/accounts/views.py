"""Vues de gestion des comptes (§6.6).

Réservées au rôle SUPERADMIN. La connexion / déconnexion utilise les vues
natives `django.contrib.auth` (cf. urls.py).
"""
from __future__ import annotations

import secrets
import string

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from .forms import PasswordResetForm, UserAdminForm
from .models import Role, User
from .permissions import require_role


@require_role(Role.SUPERADMIN)
def user_list(request):
    users = User.objects.all().order_by("username")
    return render(request, "accounts/user_list.html", {"users": users})


@require_role(Role.SUPERADMIN)
def user_create(request):
    if request.method == "POST":
        form = UserAdminForm(request.POST, creating=True)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Compte %(u)s créé.") % {"u": user.username})
            return redirect("accounts:user_list")
    else:
        form = UserAdminForm(creating=True)
    return render(request, "accounts/user_form.html", {"form": form, "creating": True})


@login_required
def user_edit(request, pk: int):
    """Édition d'un compte.

    Accessible aux superadmins (n'importe quel compte) et à tout utilisateur
    pour son propre compte — entrée « Mon compte » du menu. En auto-édition
    non-superadmin, le formulaire masque `role` et `is_active` (pas
    d'escalade de privilèges possible).
    """
    user = get_object_or_404(User, pk=pk)
    is_self = request.user.pk == user.pk
    if not (request.user.is_superadmin or is_self):
        raise PermissionDenied(_("Accès réservé."))
    self_edit = is_self and not request.user.is_superadmin

    if request.method == "POST":
        form = UserAdminForm(request.POST, instance=user, self_edit=self_edit)
        if form.is_valid():
            form.save()
            messages.success(request, _("Compte %(u)s mis à jour.") % {"u": user.username})
            if request.user.is_superadmin:
                return redirect("accounts:user_list")
            return redirect("core:dashboard")
    else:
        form = UserAdminForm(instance=user, self_edit=self_edit)
    return render(request, "accounts/user_form.html",
                  {"form": form, "creating": False, "target": user,
                   "self_edit": self_edit})


@require_role(Role.SUPERADMIN)
def user_password_reset(request, pk: int):
    """Réinitialisation par admin (sans envoi mail : on est offline §6.8)."""
    user = get_object_or_404(User, pk=pk)
    generated_password = None
    form = PasswordResetForm(user=user)

    if request.method == "POST":
        if request.POST.get("auto") == "1":
            generated_password = _generate_password()
            user.set_password(generated_password)
            user.save(update_fields=["password"])
            messages.warning(
                request,
                _("Communiquez ce mot de passe à l'utilisateur puis fermez la page."),
            )
        else:
            form = PasswordResetForm(request.POST, user=user)
            if form.is_valid():
                form.save()
                messages.success(
                    request, _("Mot de passe réinitialisé pour %(u)s.") % {"u": user.username},
                )
                return redirect("accounts:user_list")

    return render(request, "accounts/password_reset.html", {
        "form": form,
        "target": user,
        "generated_password": generated_password,
    })


def _generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@require_role(Role.SUPERADMIN)
def user_delete(request, pk: int):
    """FEAT-030 : suppression d'un compte.

    Garde-fous : interdit pour self + interdit si dernier SUPERADMIN actif.
    Les FK auditables (`loans.librarian`, `records.created_by`,
    `scan_sessions.created_by`) sont déjà SET_NULL côté modèle.
    """
    user = get_object_or_404(User, pk=pk)

    if request.user.pk == user.pk:
        messages.error(request, _("Vous ne pouvez pas supprimer votre propre compte."))
        return redirect("accounts:user_list")

    if user.role == Role.SUPERADMIN or user.is_superuser:
        other_active_supers = (
            User.objects.filter(is_active=True)
            .filter(Q(role=Role.SUPERADMIN) | Q(is_superuser=True))
            .exclude(pk=user.pk)
            .count()
        )
        if other_active_supers == 0:
            messages.error(
                request,
                _("Impossible : il doit rester au moins un superadmin actif."),
            )
            return redirect("accounts:user_list")

    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, _("Compte %(u)s supprimé.") % {"u": username})
        return redirect("accounts:user_list")

    impacts = {
        "loans_handled": user.loans_handled.count(),
        "records_created": user.records_created.count(),
        "scan_sessions": user.scan_sessions.count(),
    }
    return render(
        request,
        "accounts/user_confirm_delete.html",
        {"target": user, "impacts": impacts},
    )
