"""Vues du squelette : dashboard placeholder + health."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render


@login_required
def dashboard(request):
    return render(request, "core/dashboard.html", {})


def health(request):
    """Endpoint de santé minimal, étendu plus tard (espace disque, backup, version)."""
    return JsonResponse({"status": "ok", "version": "0.1.0-dev"})
