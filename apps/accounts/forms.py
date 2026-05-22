"""Formulaires de gestion des comptes (§6.6)."""
from __future__ import annotations

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from .models import Role, User


class UserAdminForm(forms.ModelForm):
    """Création/édition d'un compte par un superadmin."""

    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput,
        required=False,
        help_text=_("Laisser vide pour ne pas changer."),
    )
    password_confirm = forms.CharField(
        label=_("Confirmer"), widget=forms.PasswordInput, required=False,
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role",
                  "default_language", "is_active")

    def __init__(self, *args, creating=False, self_edit=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.creating = creating
        if creating:
            self.fields["password"].required = True
            self.fields["password_confirm"].required = True
        if self_edit:
            # Auto-édition (« Mon compte ») : l'utilisateur ne peut ni changer
            # son rôle ni se désactiver.
            self.fields.pop("role", None)
            self.fields.pop("is_active", None)

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        confirm = cleaned.get("password_confirm")
        if pwd or confirm:
            if pwd != confirm:
                raise forms.ValidationError(_("Les mots de passe ne correspondent pas."))
            validate_password(pwd, self.instance)
        # `role` absent en auto-édition : on ne touche alors pas aux privilèges.
        if "role" in self.fields:
            if cleaned.get("role") == Role.SUPERADMIN:
                # SUPERADMIN ⇒ is_superuser=True (signal force aussi is_staff)
                self.instance.is_superuser = True
            else:
                self.instance.is_superuser = False
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user


class PasswordResetForm(forms.Form):
    password = forms.CharField(label=_("Nouveau mot de passe"), widget=forms.PasswordInput)
    password_confirm = forms.CharField(label=_("Confirmer"), widget=forms.PasswordInput)

    def __init__(self, *args, user: User | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password_confirm"):
            raise forms.ValidationError(_("Les mots de passe ne correspondent pas."))
        validate_password(cleaned.get("password"), self.user)
        return cleaned

    def save(self) -> User:
        self.user.set_password(self.cleaned_data["password"])
        self.user.save(update_fields=["password"])
        return self.user
