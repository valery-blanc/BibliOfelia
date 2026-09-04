"""Écrans activités / animations / bouclement. FEAT-085, FEAT-086."""
from __future__ import annotations

import csv
import re
from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.members.lookup import find_members_by_code

from . import services
from .forms import (
    ActivityEntryForm,
    ActivityTypeForm,
    AnimationSessionForm,
    AnimationTypeForm,
)
from .models import (
    ActivityEntry,
    ActivityType,
    AnimationAttendance,
    AnimationSession,
    AnimationType,
)

READ_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
WRITE_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN)


# ----------------------------------------------------------------------
# Activités
# ----------------------------------------------------------------------
@require_role(*WRITE_ROLES)
def activity_list(request):
    if request.method == "POST":
        form = ActivityEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            messages.success(request, _("Activité enregistrée."))
            return redirect("closing:activity_list")
    else:
        form = ActivityEntryForm()
    entries = (
        ActivityEntry.objects.filter(user=request.user)
        .select_related("activity_type")
        .order_by("-occurred_on", "-id")[:50]
    )
    return render(request, "closing/activity_list.html", {
        "form": form,
        "entries": entries,
        "today": date.today(),
        "has_types": ActivityType.objects.filter(is_active=True).exists(),
    })


@require_POST
@require_role(*WRITE_ROLES)
def activity_delete(request, pk: int):
    entry = get_object_or_404(ActivityEntry, pk=pk)
    if entry.user_id != request.user.pk and not request.user.is_superadmin:
        messages.error(request, _("Vous ne pouvez retirer que vos propres saisies."))
        return redirect("closing:activity_list")
    entry.delete()
    messages.success(request, _("Saisie retirée."))
    return redirect("closing:activity_list")


# ----------------------------------------------------------------------
# Animations
# ----------------------------------------------------------------------
@require_role(*WRITE_ROLES)
def animation_list(request):
    if request.method == "POST":
        form = AnimationSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False, user=request.user)
            session.presenter = request.user
            session.save()
            added, unresolved = _add_attendees_from_codes(
                session, form.cleaned_data.get("attendee_codes", "")
            )
            if added:
                messages.success(
                    request,
                    ngettext(
                        "Animation enregistrée avec %(n)s personne présente.",
                        "Animation enregistrée avec %(n)s personnes présentes.",
                        added,
                    ) % {"n": added},
                )
            else:
                messages.success(
                    request,
                    _("Animation enregistrée. Ajoutez maintenant les personnes présentes."),
                )
            if unresolved:
                # Ni deviné, ni perdu : on nomme les codes en échec et l'écran
                # de détail permet de les reprendre un par un.
                messages.warning(
                    request,
                    _("Codes non reconnus ou ambigus : %(codes)s. Ajoutez ces "
                      "personnes ci-dessous.") % {"codes": ", ".join(unresolved)},
                )
            return redirect("closing:animation_detail", pk=session.pk)
    else:
        form = AnimationSessionForm()
    sessions = (
        AnimationSession.objects.select_related("animation_type", "presenter")
        .prefetch_related("attendances")
        .order_by("-occurred_on", "-id")[:50]
    )
    return render(request, "closing/animation_list.html", {
        "form": form,
        "sessions": sessions,
        "today": date.today(),
    })


def _add_attendees_from_codes(session, raw: str) -> tuple[int, list[str]]:
    """Résout une saisie libre de cartes et note les présences.

    Renvoie (nombre ajouté, codes non résolus). Un code ambigu — quatre
    chiffres partagés par deux cartes — est **rendu à l'utilisateur** plutôt que
    tranché au hasard : une présence mal attribuée fausse les statistiques sans
    que personne ne s'en aperçoive.
    """
    codes = [c for c in re.split(r"[\s,;]+", raw or "") if c]
    added, unresolved = 0, []
    for code in codes:
        matches = find_members_by_code(code)
        if len(matches) != 1:
            unresolved.append(code)
            continue
        _obj, created = AnimationAttendance.objects.get_or_create(
            session=session, member=matches[0]
        )
        if created:
            added += 1
    return added, unresolved


@require_role(*READ_ROLES)
def animation_detail(request, pk: int):
    session = get_object_or_404(
        AnimationSession.objects.select_related("animation_type", "presenter"), pk=pk
    )
    return render(request, "closing/animation_detail.html", {
        "session": session,
        "attendances": session.attendances.select_related("member"),
        "candidates": [],
        "query": "",
    })


@require_POST
@require_role(*WRITE_ROLES)
def animation_add_attendee(request, pk: int):
    """Ajoute un présent : carte scannée **ou** 4 derniers chiffres.

    Quand plusieurs cartes finissent par les mêmes chiffres, on affiche le
    choix au lieu d'en prendre une : une présence mal attribuée fausse les
    statistiques sans que personne ne s'en aperçoive.
    """
    session = get_object_or_404(AnimationSession, pk=pk)
    query = (request.POST.get("code") or "").strip()
    member_pk = request.POST.get("member_pk")
    candidates = []
    if member_pk:
        from apps.members.models import Member

        matches = [get_object_or_404(Member, pk=member_pk)]
    else:
        matches = find_members_by_code(query)

    if len(matches) == 1:
        _created = AnimationAttendance.objects.get_or_create(
            session=session, member=matches[0]
        )[1]
        if _created:
            messages.success(
                request,
                _("%(name)s ajouté(e) à l'animation.")
                % {"name": matches[0].full_name},
            )
        else:
            messages.info(
                request,
                _("%(name)s était déjà noté(e) présent(e).")
                % {"name": matches[0].full_name},
            )
        return redirect("closing:animation_detail", pk=pk)
    if not matches:
        messages.error(
            request,
            _("Aucun usager ne correspond à « %(q)s ».") % {"q": query},
        )
        return redirect("closing:animation_detail", pk=pk)

    candidates = matches
    return render(request, "closing/animation_detail.html", {
        "session": session,
        "attendances": session.attendances.select_related("member"),
        "candidates": candidates,
        "query": query,
    })


@require_POST
@require_role(*WRITE_ROLES)
def animation_remove_attendee(request, pk: int, attendance_pk: int):
    attendance = get_object_or_404(AnimationAttendance, pk=attendance_pk, session_id=pk)
    name = attendance.member.full_name
    attendance.delete()
    messages.success(request, _("%(name)s retiré(e).") % {"name": name})
    return redirect("closing:animation_detail", pk=pk)


@require_POST
@require_role(*WRITE_ROLES)
def animation_delete(request, pk: int):
    session = get_object_or_404(AnimationSession, pk=pk)
    if session.presenter_id != request.user.pk and not request.user.is_superadmin:
        messages.error(request, _("Vous ne pouvez retirer que vos propres animations."))
        return redirect("closing:animation_detail", pk=pk)
    session.delete()
    messages.success(request, _("Animation supprimée."))
    return redirect("closing:animation_list")


# ----------------------------------------------------------------------
# Référentiels
# ----------------------------------------------------------------------
@require_role(Role.SUPERADMIN)
def type_list(request):
    activity_form = ActivityTypeForm()
    animation_form = AnimationTypeForm()
    if request.method == "POST":
        which = request.POST.get("which")
        if which == "activity":
            activity_form = ActivityTypeForm(request.POST)
            if activity_form.is_valid():
                activity_form.save()
                messages.success(request, _("Nature d'activité ajoutée."))
                return redirect("closing:type_list")
        else:
            animation_form = AnimationTypeForm(request.POST)
            if animation_form.is_valid():
                animation_form.save()
                messages.success(request, _("Type d'animation ajouté."))
                return redirect("closing:type_list")
    return render(request, "closing/type_list.html", {
        "activity_types": ActivityType.objects.all(),
        "animation_types": AnimationType.objects.all(),
        "activity_form": activity_form,
        "animation_form": animation_form,
    })


@require_POST
@require_role(Role.SUPERADMIN)
def type_toggle(request, kind: str, pk: int):
    model = ActivityType if kind == "activity" else AnimationType
    obj = get_object_or_404(model, pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=["is_active"])
    messages.success(
        request,
        _("« %(label)s » activé.") % {"label": obj.label}
        if obj.is_active
        else _("« %(label)s » désactivé — les saisies passées restent comptées.")
        % {"label": obj.label},
    )
    return redirect("closing:type_list")


# ----------------------------------------------------------------------
# Statistiques
# ----------------------------------------------------------------------
def _year(request) -> int:
    try:
        return int(request.GET.get("year") or date.today().year)
    except ValueError:
        return date.today().year


@require_role(*READ_ROLES)
def stats(request):
    year = _year(request)
    start, end = date(year, 1, 1), date(year, 12, 31)
    return render(request, "closing/stats.html", {
        "year": year,
        "years": range(date.today().year, date.today().year - 6, -1),
        "animation": services.animation_stats(start, end),
        "activities": services.activity_stats(start, end),
        "months": services.monthly_rows(year),
    })


@require_role(*READ_ROLES)
def stats_csv(request):
    year = _year(request)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="activites-{year}.csv"'
    response.write("﻿")
    writer = csv.writer(response, delimiter=";")
    writer.writerow([
        _("Mois"), _("Animations"), _("Membres présents"), _("Non-membres"),
        _("Minutes d'activité"),
    ])
    for row in services.monthly_rows(year):
        writer.writerow([
            row.month, row.sessions, row.member_attendance, row.non_members,
            row.activity_minutes,
        ])
    return response


# ----------------------------------------------------------------------
# Bouclement
# ----------------------------------------------------------------------
@require_role(*WRITE_ROLES)
def day_closing(request):
    from apps.finance import services as finance_services

    today = date.today()
    closing = services.get_or_create_closing(request.user, today)

    if request.method == "POST":
        step = request.POST.get("step")
        if step == "emails":
            _run_emails_step(request, closing)
        elif step == "backup":
            _run_backup_step(request, closing)
        elif step == "shutdown":
            _run_shutdown_step(request, closing)
        return redirect("closing:day_closing")

    my_activities = ActivityEntry.objects.filter(
        user=request.user, occurred_on=today
    ).select_related("activity_type")
    my_animations = AnimationSession.objects.filter(
        presenter=request.user, occurred_on=today
    ).select_related("animation_type")
    if my_activities.exists() or my_animations.exists():
        if not closing.activities_done:
            closing.activities_done = True
            closing.save(update_fields=["activities_done"])

    cash = finance_services.cash_summary(today, today)
    return render(request, "closing/day_closing.html", {
        "closing": closing,
        "today": today,
        "my_activities": my_activities,
        "my_animations": my_animations,
        "cash": cash,
        "invoices_to_send": finance_services.invoices_to_send()[:50],
        "reminders_to_send": finance_services.reminders_to_send()[:50],
        "pending_emails": finance_services.pending_emails().count(),
        **finance_services.email_ui_context(),
        "is_box": services.is_box(),
        "shutdown_flag": getattr(
            __import__("django.conf", fromlist=["settings"]).settings,
            "BOX_SHUTDOWN_FLAG",
            "",
        ),
    })


def _run_emails_step(request, closing) -> None:
    from apps.finance import services as finance_services

    queued = finance_services.queue_pending_invoice_emails()
    total_queued = queued["invoices"] + queued["reminders"]
    result = finance_services.flush_outbox()
    closing.emails_sent += result["sent"]
    closing.emails_queued = finance_services.pending_emails().count()
    closing.save(update_fields=["emails_sent", "emails_queued"])
    notes = finance_services.flush_user_messages(result)
    # `flush_user_messages` dit « aucun email en attente » quand la file
    # était déjà vide — ici on vient peut-être de n'avoir rien à mettre
    # en file non plus.
    if not total_queued and not result["sent"] and not result["skipped"] and not result["failed"]:
        messages.info(request, _("Rien à envoyer aujourd'hui."))
        return
    emitters = {
        "success": messages.success,
        "error": messages.error,
        "warning": messages.warning,
        "info": messages.info,
    }
    for level, text in notes:
        if level == "info" and text == _("Aucun email en attente."):
            continue
        emitters[level](request, text)


def _run_backup_step(request, closing) -> None:
    from apps.tasks.backup import run_backup

    result = run_backup(force_daily=True)
    closing.backup_status = result.status
    closing.backup_detail = (result.db_path or result.error)[:250]
    closing.save(update_fields=["backup_status", "backup_detail"])
    if result.status == "ok":
        messages.success(
            request, _("Sauvegarde effectuée : %(p)s") % {"p": result.db_path}
        )
    else:
        messages.error(request, _("Échec sauvegarde : %(e)s") % {"e": result.error})


def _run_shutdown_step(request, closing) -> None:
    if not request.user.is_superadmin:
        messages.error(request, _("Seul un administrateur peut éteindre la Box."))
        return
    if not services.is_box():
        messages.error(
            request, _("Cette instance n'est pas la Box : rien à éteindre.")
        )
        return
    result = services.request_shutdown()
    if result.requested:
        closing.shutdown_requested = True
        closing.save(update_fields=["shutdown_requested"])
        messages.warning(
            request,
            _(
                "Demande d'extinction enregistrée (%(p)s). La Box s'éteindra si "
                "le service système d'extinction est installé."
            ) % {"p": result.flag_path},
        )
    else:
        messages.error(
            request, _("Demande impossible : %(e)s") % {"e": result.error}
        )
