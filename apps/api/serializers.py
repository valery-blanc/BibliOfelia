"""Serializers de l'API OfeliaScan. SPEC §6.10 / SPEC-CORR-001.

Ils émettent les noms de champs OAuth 2.0 attendus par OfeliaScan
(`access_token`, `refresh_token`, `token_type`, `expires_in`), là où SimpleJWT
renvoie `{access, refresh}` par défaut.
"""
from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

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
