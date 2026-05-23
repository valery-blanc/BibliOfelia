"""Serializers de l'API OfeliaScan. SPEC §6.10 / SPEC-CORR-001 / FEAT-021.

Ils émettent les noms de champs OAuth 2.0 attendus par OfeliaScan
(`access_token`, `refresh_token`, `token_type`, `expires_in`), là où SimpleJWT
renvoie `{access, refresh}` par défaut.
"""
from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import ScanKind

TOKEN_TYPE = "Bearer"


def _expires_in() -> int:
    """Durée de vie de l'access token, en secondes."""
    return int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())


class OAuthTokenObtainSerializer(TokenObtainPairSerializer):
    """`POST /auth/login` : valide username/password, émet les 4 champs OAuth."""

    def validate(self, attrs):
        data = super().validate(attrs)
        return {
            "access_token": data["access"],
            "refresh_token": data["refresh"],
            "token_type": TOKEN_TYPE,
            "expires_in": _expires_in(),
        }


class OAuthTokenRefreshSerializer(serializers.Serializer):
    """`POST /auth/refresh` : rotation du refresh token, mêmes 4 champs.

    `RefreshToken(...)` lève `TokenError` si le jeton est invalide, expiré ou
    sur liste noire — la vue le convertit en réponse `401`.
    """

    refresh_token = serializers.CharField()

    def validate(self, attrs):
        refresh = RefreshToken(attrs["refresh_token"])
        data = {
            "access_token": str(refresh.access_token),
            "token_type": TOKEN_TYPE,
            "expires_in": _expires_in(),
        }
        # Rotation activée dans les settings : l'ancien refresh token est mis
        # sur liste noire et un nouveau est émis, pour aligner la réponse sur
        # /auth/login (cf. SPEC-CORR-001 §3.2).
        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                refresh.blacklist()
            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()
        data["refresh_token"] = str(refresh)
        return data


# ─── Sessions de scan OfeliaScan (FEAT-021) ────────────────────────────────


class ScanSessionCreateInputSerializer(serializers.Serializer):
    """`POST /scan-sessions` — `label` optionnel."""

    label = serializers.CharField(required=False, allow_blank=True, max_length=120)


class ScanItemInputSerializer(serializers.Serializer):
    """Un item dans le batch `POST /scan-sessions/{id}/items`.

    Le client (OfeliaScan) fournit `local_id`, `scan_kind`, `scanned_at` au
    minimum. Tous les `metadata_*`, `location_code`, `item_state`, `notes`
    sont optionnels — on accepte `null`/`""` indifféremment et on normalise.
    """

    local_id = serializers.CharField(max_length=120)
    scan_kind = serializers.ChoiceField(choices=ScanKind.choices)
    scanned_value = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=32, default=""
    )
    metadata_title = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=300, default=""
    )
    metadata_authors = serializers.ListField(
        child=serializers.CharField(allow_blank=True, max_length=200),
        required=False,
        default=list,
    )
    metadata_language = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=10, default=""
    )
    metadata_publisher = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=200, default=""
    )
    metadata_year = serializers.IntegerField(required=False, allow_null=True, default=None)
    location_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=20, default=""
    )
    item_state = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=10, default=""
    )
    copy_count = serializers.IntegerField(required=False, min_value=1, max_value=999, default=1)
    scanned_at = serializers.DateTimeField()
    notes = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        # Normalise les `null` JSON en chaînes vides (`CharField` les rejette
        # par défaut quand `allow_null=True` mais on veut juste les "absent").
        for k in (
            "scanned_value",
            "metadata_title",
            "metadata_language",
            "metadata_publisher",
            "location_code",
            "item_state",
            "notes",
        ):
            if value.get(k) is None:
                value[k] = ""
        if value.get("metadata_authors") is None:
            value["metadata_authors"] = []
        return value


class ScanItemsBatchInputSerializer(serializers.Serializer):
    """`POST /scan-sessions/{id}/items` — corps `{"items": [...]}`."""

    items = ScanItemInputSerializer(many=True)


class InventorySessionCreateInputSerializer(serializers.Serializer):
    """`POST /inventory-sessions` — label + scope optionnels."""

    label = serializers.CharField(required=False, allow_blank=True, max_length=120)
    scope_type = serializers.ChoiceField(
        choices=["all", "location", "category"], required=False, default="all"
    )
    scope_location_code = serializers.CharField(
        required=False, allow_blank=True, max_length=20
    )
    scope_category_code = serializers.CharField(
        required=False, allow_blank=True, max_length=20
    )


class InventoryItemInputSerializer(serializers.Serializer):
    """Un item dans `POST /inventory-sessions/{id}/items`."""

    scanned_value = serializers.CharField(max_length=32)
    scanned_at = serializers.DateTimeField()


class InventoryItemsBatchInputSerializer(serializers.Serializer):
    items = InventoryItemInputSerializer(many=True)


# ─── Scan handoff single-scan (FEAT-023) ──────────────────────────────────


class ScanHandoffCreateInputSerializer(serializers.Serializer):
    """`POST /scan-handoff` — target_kind optionnel (auto par défaut)."""

    target_kind = serializers.ChoiceField(
        choices=["auto", "book", "card"], required=False, default="auto"
    )


class ScanHandoffSubmitInputSerializer(serializers.Serializer):
    """`POST /scan-handoff/{token}` — corps envoyé par OfeliaScan.

    `cancelled=true` autorise OfeliaScan à signaler une annulation utilisateur
    sans renvoyer de valeur ; sinon `value` + `kind` requis.
    """

    value = serializers.CharField(
        required=False, allow_blank=True, max_length=64, default=""
    )
    kind = serializers.ChoiceField(
        choices=["ean13", "isbn", "card", "item", "manual"],
        required=False,
        allow_blank=True,
        default="manual",
    )
    cancelled = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if not attrs.get("cancelled") and not (attrs.get("value") or "").strip():
            raise serializers.ValidationError(
                {"value": "Champ `value` requis sauf si `cancelled=true`."}
            )
        return attrs
