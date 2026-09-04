"""Écrans de caisse. FEAT-084, SPEC §6.13."""
from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.members.forms import MemberCategoryForm
from apps.members.models import Member, MemberCategory

from . import services
from .forms import (
    CashMovementForm,
    FineForm,
    InvoiceForm,
    InvoiceLineFormSet,
    PaymentForm,
    TariffForm,
)
from .models import (
    EmailStatus,
    FeeKind,
    Invoice,
    InvoiceStatus,
    OutboundEmail,
    Tariff,
)
from .money import config, format_amount

READ_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
WRITE_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN)


def _period(request) -> tuple[date, date]:
    """Période de l'écran de caisse — la journée par défaut."""
    today = date.today()
    start = _parse_date(request.GET.get("start")) or today
    end = _parse_date(request.GET.get("end")) or today
    if end < start:
        start, end = end, start
    return start, end


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


# ----------------------------------------------------------------------
# État de la caisse
# ----------------------------------------------------------------------
@require_role(*READ_ROLES)
def cash_index(request):
    start, end = _period(request)
    summary = services.cash_summary(start, end)
    overdue = (
        Invoice.objects.filter(status=InvoiceStatus.OPEN, due_date__lt=date.today())
        .select_related("member")
        .order_by("due_date")[:20]
    )
    return render(request, "finance/cash_index.html", {
        "summary": summary,
        "start": start,
        "end": end,
        "movement_form": CashMovementForm(),
        "total_outstanding": services.total_outstanding(),
        "cash_balance": services.cash_balance_all_time(),
        "overdue_invoices": overdue,
        "pending_emails": services.pending_emails().count(),
        "currency": config()["currency"],
        **services.email_ui_context(),
    })


@require_POST
@require_role(*WRITE_ROLES)
def cash_movement_create(request):
    form = CashMovementForm(request.POST)
    if form.is_valid():
        movement = form.save(commit=False)
        movement.created_by = request.user
        movement.save()
        messages.success(request, _("Mouvement de caisse enregistré."))
    else:
        messages.error(request, _("Mouvement refusé : %(e)s") % {"e": form.errors.as_text()})
    return redirect("finance:cash_index")


@require_POST
@require_role(Role.SUPERADMIN)
def outbox_flush(request):
    """Vide la file d'emails à la demande."""
    result = services.flush_outbox()
    _emit_flush_messages(request, result)
    nxt = request.POST.get("next")
    if nxt == "closing":
        return redirect("closing:day_closing")
    if nxt == "cash":
        return redirect("finance:cash_index")
    return redirect("finance:outbox_list")


def _emit_flush_messages(request, result: dict) -> None:
    emitters = {
        "success": messages.success,
        "error": messages.error,
        "warning": messages.warning,
        "info": messages.info,
    }
    for level, text in services.flush_user_messages(result):
        emitters[level](request, text)


@require_role(Role.SUPERADMIN)
def currency_search(request):
    """FEAT-088 : recherche de devise par trigramme ou nom de pays.

    Sert le champ de réglage de la caisse (SUPERADMIN uniquement, comme l'écran
    qui l'héberge). Les libellés sont rendus dans la langue de la requête.
    """
    from django.http import JsonResponse

    from . import currencies

    query = (request.GET.get("q") or "").strip()
    results = [c.as_dict() for c in currencies.search(query)]
    return JsonResponse({
        "results": results,
        "query": query,
        "min_length": currencies.MIN_QUERY_LENGTH,
    })


@require_role(*READ_ROLES)
def outbox_list(request):
    return render(request, "finance/outbox_list.html", {
        "emails": OutboundEmail.objects.select_related("invoice__member")[:200],
        "pending": services.pending_emails().count(),
        "statuses": EmailStatus.choices,
        **services.email_ui_context(),
    })


# ----------------------------------------------------------------------
# Factures
# ----------------------------------------------------------------------
@require_role(*READ_ROLES)
def invoice_list(request):
    invoices = Invoice.objects.select_related("member")
    status = request.GET.get("status") or ""
    if status == "overdue":
        invoices = invoices.filter(status=InvoiceStatus.OPEN, due_date__lt=date.today())
    elif status:
        invoices = invoices.filter(status=status)
    q = (request.GET.get("q") or "").strip()
    if q:
        invoices = invoices.filter(
            Q(number__icontains=q)
            | Q(member__last_name__icontains=q)
            | Q(member__first_name__icontains=q)
            | Q(member__card_number__icontains=q)
        )
    paginator = Paginator(invoices, 25)
    return render(request, "finance/invoice_list.html", {
        "page_obj": paginator.get_page(request.GET.get("page")),
        "status": status,
        "q": q,
        "statuses": InvoiceStatus.choices,
        "total_outstanding": services.total_outstanding(),
    })


@require_role(*WRITE_ROLES)
def invoice_create(request, member_pk: int):
    member = get_object_or_404(Member, pk=member_pk)
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            lines = [
                {
                    "kind": f.cleaned_data.get("kind") or FeeKind.OTHER,
                    "label": f.cleaned_data["label"],
                    "amount": f.cleaned_data["amount"],
                    "quantity": f.cleaned_data.get("quantity") or 1,
                }
                for f in formset.forms
                if getattr(f, "cleaned_data", None)
                and not f.cleaned_data.get("DELETE")
            ]
            invoice = services.create_invoice(
                member,
                lines,
                issue_date=form.cleaned_data["issue_date"],
                due_date=form.cleaned_data["due_date"],
                user=request.user,
                note=form.cleaned_data.get("note", ""),
            )
            messages.success(
                request,
                _("Facture %(num)s créée (%(amount)s).")
                % {"num": invoice.number, "amount": format_amount(invoice.total_amount)},
            )
            return redirect("finance:invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm()
        formset = InvoiceLineFormSet()
    return render(request, "finance/invoice_form.html", {
        "member": member,
        "form": form,
        "formset": formset,
        "tariffs": Tariff.objects.filter(is_active=True),
    })


@require_role(*READ_ROLES)
def invoice_detail(request, pk: int):
    invoice = get_object_or_404(
        Invoice.objects.select_related("member").prefetch_related("lines", "payments"),
        pk=pk,
    )
    return render(request, "finance/invoice_detail.html", {
        "invoice": invoice,
        "payment_form": PaymentForm(invoice=invoice),
        "account": services.member_account(invoice.member),
        "emails": invoice.emails.all(),
        **services.email_ui_context(),
    })


@require_POST
@require_role(*WRITE_ROLES)
def invoice_pay(request, pk: int):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status == InvoiceStatus.CANCELLED:
        messages.error(request, _("Cette facture est annulée."))
        return redirect("finance:invoice_detail", pk=pk)
    form = PaymentForm(request.POST, invoice=invoice)
    if form.is_valid():
        services.register_payment(
            invoice,
            form.cleaned_data["amount"],
            method=form.cleaned_data["method"],
            paid_on=form.cleaned_data["paid_on"],
            note=form.cleaned_data.get("note", ""),
            user=request.user,
        )
        invoice.refresh_from_db()
        if invoice.status == InvoiceStatus.PAID:
            messages.success(
                request,
                _("Facture %(num)s réglée intégralement.") % {"num": invoice.number},
            )
        else:
            messages.success(
                request,
                _("Encaissement enregistré. Reste %(b)s.")
                % {"b": format_amount(invoice.balance)},
            )
    else:
        messages.error(request, form.errors.as_text())
    return redirect("finance:invoice_detail", pk=pk)


@require_POST
@require_role(*WRITE_ROLES)
def invoice_cancel(request, pk: int):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.payments.exists():
        messages.error(
            request,
            _("Facture déjà encaissée : elle ne peut plus être annulée."),
        )
        return redirect("finance:invoice_detail", pk=pk)
    services.cancel_invoice(invoice, reason=request.POST.get("reason", ""))
    messages.warning(
        request, _("Facture %(num)s annulée.") % {"num": invoice.number}
    )
    return redirect("finance:invoice_detail", pk=pk)


@require_role(*READ_ROLES)
def invoice_pdf(request, pk: int):
    from .pdf import render_invoice_pdf

    invoice = get_object_or_404(
        Invoice.objects.select_related("member").prefetch_related("lines"), pk=pk
    )
    response = HttpResponse(render_invoice_pdf(invoice), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.number}.pdf"'
    return response


@require_POST
@require_role(*WRITE_ROLES)
def invoice_email(request, pk: int):
    from django.utils import timezone

    from .models import EmailKind

    invoice = get_object_or_404(Invoice.objects.select_related("member"), pk=pk)
    if not invoice.member.email:
        messages.error(
            request,
            _("%(name)s n'a pas d'adresse email sur sa fiche.")
            % {"name": invoice.member.full_name},
        )
        return redirect("finance:invoice_detail", pk=pk)
    services.queue_invoice_email(invoice, kind=EmailKind.INVOICE)
    Invoice.objects.filter(pk=invoice.pk).update(emailed_at=timezone.now())
    result = services.flush_outbox()
    if result["sent"]:
        messages.success(request, _("Facture envoyée par email."))
    else:
        _emit_flush_messages(request, result)
    return redirect("finance:invoice_detail", pk=pk)


# ----------------------------------------------------------------------
# Amende / frais rapides depuis la fiche usager
# ----------------------------------------------------------------------
@require_role(*WRITE_ROLES)
def fee_create(request, member_pk: int, kind: str):
    """Amende ou frais d'animation en un formulaire court.

    Décision Val : les amendes sont **manuelles**. Le motif vient du
    référentiel des tarifs, le montant reste libre.
    """
    if kind not in (FeeKind.FINE, FeeKind.ACTIVITY, FeeKind.OTHER):
        return redirect("members:detail", pk=member_pk)
    member = get_object_or_404(Member, pk=member_pk)
    if request.method == "POST":
        form = FineForm(request.POST, kind=kind)
        if form.is_valid():
            invoice = services.create_invoice(
                member,
                [{
                    "kind": kind,
                    "label": form.cleaned_data["label"],
                    "amount": form.cleaned_data["amount"],
                    "quantity": 1,
                }],
                user=request.user,
            )
            messages.success(
                request,
                _("Facture %(num)s créée (%(amount)s).")
                % {"num": invoice.number, "amount": format_amount(invoice.total_amount)},
            )
            return redirect("finance:invoice_detail", pk=invoice.pk)
    else:
        form = FineForm(kind=kind)
    labels = {
        FeeKind.FINE: _("Nouvelle amende"),
        FeeKind.ACTIVITY: _("Frais d'animation"),
        FeeKind.OTHER: _("Autre montant à facturer"),
    }
    return render(request, "finance/fee_form.html", {
        "member": member,
        "form": form,
        "kind": kind,
        "title": labels[kind],
    })


# ----------------------------------------------------------------------
# Référentiel des tarifs
# ----------------------------------------------------------------------
@require_role(Role.SUPERADMIN)
def tariff_list(request):
    if request.method == "POST":
        form = TariffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Tarif ajouté."))
            return redirect("finance:tariff_list")
    else:
        form = TariffForm()
    return render(request, "finance/tariff_list.html", {
        "tariffs": Tariff.objects.all(),
        "form": form,
        "categories": (
            MemberCategory.objects.annotate(member_count=Count("members"))
            .order_by("code")
        ),
    })


@require_role(Role.SUPERADMIN)
def member_category_create(request):
    if request.method == "POST":
        form = MemberCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie d'usager créée."))
            return redirect("finance:tariff_list")
    else:
        form = MemberCategoryForm()
    return render(request, "finance/member_category_form.html", {
        "form": form,
        "form_title": _("Nouvelle catégorie d'usager"),
    })


@require_role(Role.SUPERADMIN)
def member_category_edit(request, pk: int):
    category = get_object_or_404(MemberCategory, pk=pk)
    if request.method == "POST":
        form = MemberCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie d'usager mise à jour."))
            return redirect("finance:tariff_list")
    else:
        form = MemberCategoryForm(instance=category)
    return render(request, "finance/member_category_form.html", {
        "form": form,
        "form_title": _("Modifier la catégorie d'usager"),
        "category": category,
    })


@require_role(Role.SUPERADMIN)
def member_category_delete(request, pk: int):
    category = get_object_or_404(
        MemberCategory.objects.annotate(member_count=Count("members")), pk=pk
    )
    if request.method == "POST":
        if category.member_count:
            messages.error(
                request,
                ngettext(
                    "Impossible de supprimer : %(n)s usager est encore dans cette catégorie.",
                    "Impossible de supprimer : %(n)s usagers sont encore dans cette catégorie.",
                    category.member_count,
                )
                % {"n": category.member_count},
            )
            return redirect("finance:member_category_delete", pk=pk)
        category.delete()
        messages.success(request, _("Catégorie d'usager supprimée."))
        return redirect("finance:tariff_list")
    return render(request, "finance/member_category_confirm_delete.html", {
        "category": category,
    })


@require_role(Role.SUPERADMIN)
def tariff_edit(request, pk: int):
    tariff = get_object_or_404(Tariff, pk=pk)
    if request.method == "POST":
        form = TariffForm(request.POST, instance=tariff)
        if form.is_valid():
            form.save()
            messages.success(request, _("Tarif modifié."))
            return redirect("finance:tariff_list")
    else:
        form = TariffForm(instance=tariff)
    return render(request, "finance/tariff_form.html", {"form": form, "tariff": tariff})


@require_POST
@require_role(Role.SUPERADMIN)
def tariff_delete(request, pk: int):
    tariff = get_object_or_404(Tariff, pk=pk)
    tariff.delete()
    messages.success(request, _("Tarif supprimé."))
    return redirect("finance:tariff_list")


# ----------------------------------------------------------------------
# Divers
# ----------------------------------------------------------------------
@require_role(*READ_ROLES)
def member_account_view(request, member_pk: int):
    """Compte complet d'un usager : factures, paiements, solde."""
    member = get_object_or_404(Member, pk=member_pk)
    invoices = (
        Invoice.objects.filter(member=member)
        .prefetch_related("lines", "payments")
        .order_by("-issue_date", "-id")
    )
    return render(request, "finance/member_account.html", {
        "member": member,
        "account": services.member_account(member),
        "invoices": invoices,
    })
