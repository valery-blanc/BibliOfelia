"""Modèle User étendu (rôle + langue par défaut). SPEC §5.2 et §9.2."""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    SUPERADMIN = "superadmin", _("Superadmin")
    LIBRARIAN = "librarian", _("Bibliothécaire")
    CONTRIBUTOR_API = "contributor_api", _("Contributeur OfeliaScan")
    READONLY = "readonly", _("Support / lecture seule")


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.LIBRARIAN,
        verbose_name=_("rôle"),
    )
    default_language = models.CharField(
        max_length=10, blank=True, default="", verbose_name=_("langue par défaut")
    )
    always_show_advanced = models.BooleanField(
        default=False, verbose_name=_("toujours afficher les options avancées")
    )

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"

    @property
    def is_librarian(self) -> bool:
        return self.role in {Role.LIBRARIAN, Role.SUPERADMIN}

    @property
    def is_superadmin(self) -> bool:
        return self.role == Role.SUPERADMIN or self.is_superuser
