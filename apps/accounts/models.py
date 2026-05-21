"""Modèle User étendu (rôle + langue par défaut). SPEC §5.2 et §9.2."""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    SUPERADMIN = "superadmin", "Superadmin"
    LIBRARIAN = "librarian", "Bibliothécaire"
    CONTRIBUTOR_API = "contributor_api", "Contributeur OfeliaScan"
    READONLY = "readonly", "Support / lecture seule"


class User(AbstractUser):
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.LIBRARIAN
    )
    default_language = models.CharField(max_length=10, blank=True, default="")
    always_show_advanced = models.BooleanField(default=False)

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"

    @property
    def is_librarian(self) -> bool:
        return self.role in {Role.LIBRARIAN, Role.SUPERADMIN}

    @property
    def is_superadmin(self) -> bool:
        return self.role == Role.SUPERADMIN or self.is_superuser
