"""Wizard de premier démarrage. SPEC §11.3.

Multi-step session-based. Une fois `Setting.setup_completed=True`, le
middleware `SetupRequiredMiddleware` ne redirige plus vers `/setup/`.
"""
from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import activate, gettext as _

from apps.core.models import Setting

from .forms import (
    Step1LanguageForm,
    Step2LibraryForm,
    Step3LanguagesForm,
    Step4SuperadminForm,
    Step5PrinterForm,
    Step6BackupForm,
    Step7ZerotierForm,
    Step8DemoForm,
)
from .services import apply_wizard

WIZARD_STEPS = [
    ("step1", _("Langue"), Step1LanguageForm),
    ("step2", _("Bibliothèque"), Step2LibraryForm),
    ("step3", _("Langues activées"), Step3LanguagesForm),
    ("step4", _("Administrateur"), Step4SuperadminForm),
    ("step5", _("Imprimante"), Step5PrinterForm),
    ("step6", _("Sauvegarde"), Step6BackupForm),
    ("step7", _("ZeroTier"), Step7ZerotierForm),
    ("step8", _("Démo"), Step8DemoForm),
]
SESSION_KEY = "setup_wizard_data"


def wizard_index(request):
    """Si déjà setup, page de bienvenue/restart. Sinon, démarre à step1."""
    if Setting.get("setup_completed", False):
        return render(request, "setup/already_done.html")
    request.session[SESSION_KEY] = {}
    return redirect("setup:step", step="step1")


def wizard_step(request, step: str):
    if Setting.get("setup_completed", False):
        return redirect("core:dashboard")

    idx = _step_index(step)
    if idx is None:
        return HttpResponseNotFound()
    key, label, form_cls = WIZARD_STEPS[idx]

    data = request.session.get(SESSION_KEY, {})

    if request.method == "POST":
        form = form_cls(request.POST)
        if form.is_valid():
            data[key] = form.cleaned_data
            request.session[SESSION_KEY] = data
            # Sur step1, activer immédiatement la langue choisie
            if key == "step1":
                activate(form.cleaned_data["language"])
                request.session["django_language"] = form.cleaned_data["language"]
            if idx + 1 < len(WIZARD_STEPS):
                return redirect("setup:step", step=WIZARD_STEPS[idx + 1][0])
            return redirect("setup:finalize")
    else:
        form = form_cls(initial=data.get(key, {}))

    return render(request, "setup/step.html", {
        "form": form, "step_label": label, "step_index": idx + 1,
        "total_steps": len(WIZARD_STEPS),
        "step_key": key,
        "prev_url": reverse("setup:step", args=[WIZARD_STEPS[idx - 1][0]]) if idx > 0 else None,
    })


def wizard_finalize(request):
    if Setting.get("setup_completed", False):
        return redirect("core:dashboard")

    data = request.session.get(SESSION_KEY, {})
    required = {"step2", "step3", "step4"}
    missing = [k for k in required if k not in data]
    if missing:
        messages.error(request, _("Étapes manquantes : %(m)s") % {"m": ", ".join(missing)})
        return redirect("setup:step", step="step1")

    completion = apply_wizard(data)
    request.session.pop(SESSION_KEY, None)
    return render(request, "setup/completed.html", {
        "completion": completion,
    })


def _step_index(step: str) -> int | None:
    for idx, (key, _label, _form) in enumerate(WIZARD_STEPS):
        if key == step:
            return idx
    return None
