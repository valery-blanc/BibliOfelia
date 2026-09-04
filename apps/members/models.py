"""Modèles usagers. SPEC §5.2.

MemberCategory, Member. card_number = EAN13 préfixe 291.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from apps.core.ean import build_ean13
from apps.catalog.models import DocumentType


MEMBER_EAN13_PREFIX = "291"


class MemberStatus(models.TextChoices):
    ACTIVE = "active", _("Actif")
    SUSPENDED = "suspended", _("Suspendu")
    EXPIRED = "expired", _("Expiré")
    CLOSED = "closed", _("Clôturé")


class MemberCategory(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name=_("code"))
    name = models.CharField(max_length=80, verbose_name=_("nom"))
    max_concurrent_loans = models.PositiveIntegerField(default=3)
    default_loan_duration_days = models.PositiveIntegerField(default=21)
    allowed_document_types = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Liste de codes DocumentType ; vide = tous autorisés."),
    )
    card_validity_months = models.PositiveIntegerField(default=12)
    # FEAT-084 : cotisation annuelle facturée à l'inscription puis à chaque
    # renouvellement de carte. Un montant nul n'émet aucune facture — une
    # bibliothèque gratuite ne doit pas crouler sous des factures à zéro.
    membership_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name=_("cotisation annuelle"),
        help_text=_("0 = pas de cotisation pour cette catégorie."),
    )

    class Meta:
        verbose_name = _("catégorie d'usager")
        verbose_name_plural = _("catégories d'usager")
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def allows_document_type(self, doc_type: str) -> bool:
        if not self.allowed_document_types:
            return True
        return doc_type in self.allowed_document_types


class Member(models.Model):
    card_number = models.CharField(
        max_length=13, unique=True, blank=True, verbose_name=_("n° de carte")
    )
    first_name = models.CharField(max_length=80, verbose_name=_("prénom"))
    last_name = models.CharField(max_length=80, verbose_name=_("nom"))
    birth_date = models.DateField(
        null=True, blank=True, verbose_name=_("date de naissance")
    )
    category = models.ForeignKey(
        MemberCategory,
        related_name="members",
        on_delete=models.PROTECT,
        verbose_name=_("catégorie"),
    )
    contact_phone = models.CharField(
        max_length=40, blank=True, verbose_name=_("téléphone")
    )
    # FEAT-083 : l'email n'est pas un confort — c'est lui qui reçoit les
    # factures et les relances (FEAT-084). Sans lui, le bouclement n'a rien
    # à envoyer.
    email = models.EmailField(blank=True, verbose_name=_("email"))
    # FEAT-083 : adresse découpée. L'ancien champ libre `address` ne permettait
    # pas de mettre en page une facture A4.
    address_street = models.CharField(
        max_length=200, blank=True, verbose_name=_("rue et n°")
    )
    address_extra = models.CharField(
        max_length=200, blank=True, verbose_name=_("complément d'adresse")
    )
    address_postal_code = models.CharField(
        max_length=20, blank=True, verbose_name=_("code postal")
    )
    address_city = models.CharField(
        max_length=100, blank=True, verbose_name=_("localité")
    )
    address_state = models.CharField(
        max_length=100, blank=True, verbose_name=_("état / province")
    )
    address_country = models.CharField(
        max_length=100, blank=True, verbose_name=_("pays")
    )
    registration_date = models.DateField(
        default=date.today, verbose_name=_("date d'inscription")
    )
    expiration_date = models.DateField(
        null=True, blank=True, verbose_name=_("date d'expiration")
    )
    status = models.CharField(
        max_length=15,
        choices=MemberStatus.choices,
        default=MemberStatus.ACTIVE,
        verbose_name=_("statut"),
    )
    # FEAT-083 : Val demandait « un champ commentaire libre optionnel (500
    # caractères) ». Ce champ existait déjà sous le nom `notes` ; il est
    # relibellé plutôt que doublé — deux zones de texte libre côte à côte sur
    # le même écran ne se remplissent jamais toutes les deux. La limite est
    # posée dans le formulaire, pas en base : les notes existantes plus
    # longues restent lisibles.
    notes = models.TextField(blank=True, verbose_name=_("commentaire"))
    preferred_language = models.CharField(
        max_length=10,
        blank=True,
        default="",
        verbose_name=_("langue de correspondance"),
    )
    # FEAT-065 : langues que l'usager parle — à ne pas confondre avec
    # `preferred_language`, qui dit seulement dans quelle langue lui écrire.
    # Codes figés (cf. apps/members/languages.py) ; le champ libre reçoit tout
    # ce qui n'est pas dans la liste, sans vérification.
    spoken_languages = models.JSONField(
        default=list, blank=True, verbose_name=_("langues parlées")
    )
    spoken_languages_other = models.CharField(
        max_length=200, blank=True, verbose_name=_("autres langues")
    )
    replaces_card_number = models.CharField(
        max_length=13, blank=True, verbose_name=_("ancienne carte")
    )
    photo = models.FileField(
        upload_to="member_photos/", blank=True, null=True, verbose_name=_("photo")
    )

    class Meta:
        verbose_name = _("usager")
        verbose_name_plural = _("usagers")
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"], name="member_name_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}".strip()

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating:
            if self.expiration_date is None and self.category_id:
                months = self.category.card_validity_months or 12
                self.expiration_date = self.registration_date + relativedelta(months=months)
            with transaction.atomic():
                super().save(*args, **kwargs)
                if not self.card_number:
                    self.card_number = build_ean13(MEMBER_EAN13_PREFIX, self.pk)
                    super().save(update_fields=["card_number"])
            return
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self) -> int | None:
        """FEAT-080 : âge en années révolues, None si la date de naissance manque.

        Contrairement à `MemberFamilyMember.age`, qui n'a qu'une année de
        naissance et approxime, on a ici la date complète : on décompte
        l'anniversaire pas encore passé, sinon un usager né en décembre
        paraîtrait un an plus vieux pendant onze mois.
        """
        if not self.birth_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @property
    def address_lines(self) -> list[str]:
        """FEAT-083 : adresse en lignes prêtes à afficher, vides écartées.

        Sert au gabarit de la fiche et au bloc destinataire de la facture PDF
        (FEAT-084) : les deux doivent écrire la même adresse.
        """
        city_line = " ".join(
            part for part in (self.address_postal_code, self.address_city) if part
        )
        return [
            line
            for line in (
                self.address_street,
                self.address_extra,
                city_line,
                self.address_state,
                self.address_country,
            )
            if line
        ]

    @property
    def postal_address(self) -> str:
        return ", ".join(self.address_lines)

    @property
    def is_active(self) -> bool:
        return self.status == MemberStatus.ACTIVE

    @property
    def family_first_names(self) -> list[str]:
        """FEAT-072 : prénoms des personnes rattachées, pour la carte imprimée."""
        return [
            person.first_name
            for person in self.family.all()
            if person.first_name
        ]

    @property
    def spoken_languages_display(self) -> str:
        """FEAT-065 : langues cochées puis champ libre, en une ligne."""
        from .languages import display

        return display(self.spoken_languages, self.spoken_languages_other)


class FamilyGender(models.TextChoices):
    GIRL = "f", _("Fille")
    BOY = "m", _("Garçon")
    OTHER = "x", _("Autre")


class MemberFamilyMember(models.Model):
    """FEAT-072 : personne rattachée à la carte d'un usager.

    Remplace `MemberChild` (FEAT-066), qui ne savait décrire que des enfants :
    en pratique une carte sert à toute une maisonnée — conjoint, grands-parents,
    enfants.

    On note une **année de naissance** pour les enfants plutôt qu'un âge : un âge
    saisi une fois devient faux l'année suivante, une année de naissance reste
    vraie. Pour un adulte, l'année n'apporte rien et n'est pas demandée.

    Ces personnes ne sont pas des usagers : pas de carte, pas d'emprunt à leur
    nom. D'où le CASCADE — leur fiche n'existe que rattachée au titulaire.
    """

    member = models.ForeignKey(
        Member, related_name="family", on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=80, verbose_name=_("prénom"))
    gender = models.CharField(
        max_length=1, choices=FamilyGender.choices, blank=True, verbose_name=_("sexe")
    )
    is_adult = models.BooleanField(default=False, verbose_name=_("adulte"))
    birth_year = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("année de naissance")
    )
    # Mêmes codes que Member.spoken_languages (cf. catalog.Language, FEAT-070).
    languages = models.JSONField(
        default=list, blank=True, verbose_name=_("langues parlées")
    )
    languages_other = models.CharField(
        max_length=200, blank=True, verbose_name=_("autres langues")
    )

    class Meta:
        verbose_name = _("membre de la famille")
        verbose_name_plural = _("membres de la famille")
        ordering = ["first_name"]

    def __str__(self) -> str:
        return self.first_name

    @property
    def age(self) -> int | None:
        """Âge approché en années, ou None pour un adulte ou une année absente.

        Approximation assumée : la bibliothèque a besoin de savoir « environ
        7 ans », pas de la date d'anniversaire.
        """
        if self.is_adult or not self.birth_year:
            return None
        return date.today().year - self.birth_year

    @property
    def languages_display(self) -> str:
        from .languages import display

        return display(self.languages, self.languages_other)
