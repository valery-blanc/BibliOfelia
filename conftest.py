"""Configuration pytest globale.

Le `SetupRequiredMiddleware` redirige toute requête vers /setup/ tant que le
Setting `setup_completed` est faux. Les tests de vues s'exécutent en aval du
wizard de premier démarrage : la fixture autouse ci-dessous pose le drapeau pour
toute la suite, quelle que soit la configuration de settings chargée.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _mark_setup_complete(db):
    from apps.core.models import Setting

    Setting.objects.update_or_create(
        pk="setup_completed",
        defaults={"value": True, "description": "Wizard d'installation terminé"},
    )
