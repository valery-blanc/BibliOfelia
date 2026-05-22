"""Endpoints de l'API OfeliaScan. SPEC §6.10 / SPEC-CORR-001.

Authentification JWT, appairage, lookup ISBN, diagnostic. Le contrat JSON est
figé : voir `docs/specs/SPEC-CORR-001-contrat-api-box.md`. Les chemins n'ont
pas de slash final (cf. `apps/api/urls.py`).
"""
from __future__ import annotations

import shutil

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.catalog.models import BibliographicRecord
from apps.catalog.openlibrary import lookup_isbn, normalize_isbn
from apps.core.models import Setting

from .serializers import OAuthTokenObtainSerializer, OAuthTokenRefreshSerializer


class LoginView(TokenObtainPairView):
    """`POST /auth/login` — auth non requise."""

    serializer_class = OAuthTokenObtainSerializer
    throttle_scope = "auth"


class RefreshView(TokenRefreshView):
    """`POST /auth/refresh` — auth non requise (le refresh token fait foi)."""

    serializer_class = OAuthTokenRefreshSerializer
    throttle_scope = "auth"


class LogoutView(APIView):
    """`POST /auth/logout` — met les refresh tokens de l'utilisateur sur liste noire."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth"

    def post(self, request):
        for token in OutstandingToken.objects.filter(user=request.user):
            BlacklistedToken.objects.get_or_create(token=token)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PairingInfoView(APIView):
    """`GET /pairing/info` — endpoint de découverte, auth non requise."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {
                "box_name": Setting.get("box_name", "OfeliaBox"),
                "library_name": Setting.get("library_name", "BibliOfelia"),
                "version": settings.BIBLIOFELIA_VERSION,
                "base_url": self._base_url(request),
            }
        )

    @staticmethod
    def _base_url(request) -> str:
        """URL absolue de la base de l'API, slash final inclus.

        OfeliaScan l'utilise telle quelle (`BibliOfeliaApiFactory.forBaseUrl`).
        Override explicite via le réglage API_BASE_URL ; sinon reconstruite
        depuis la requête — la box publie l'adresse réellement utilisée par le
        client, donc aucun chemin n'est codé en dur (SPEC-CORR-002).
        """
        configured = settings.API_BASE_URL
        if configured:
            return configured if configured.endswith("/") else configured + "/"
        full = request.build_absolute_uri(request.path)
        suffix = "pairing/info"
        return full[: -len(suffix)] if full.endswith(suffix) else full


class HealthView(APIView):
    """`GET /health` — diagnostic, auth requise."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            free_mb = shutil.disk_usage(settings.DATABASE_PATH).free // (1024 * 1024)
        except OSError:
            free_mb = None
        return Response(
            {
                "status": "ok",
                "version": settings.BIBLIOFELIA_VERSION,
                "disk_free_mb": free_mb,
                "last_backup_at": Setting.get("last_backup_at"),
            }
        )


class IsbnLookupView(APIView):
    """`GET /isbn/{isbn}` — cache local de la box, puis fallback OpenLibrary."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "isbn"

    def get(self, request, isbn):
        normalized = normalize_isbn(isbn)
        if len(normalized) not in (10, 13):
            return self._not_found(isbn)

        record = (
            BibliographicRecord.objects.filter(isbn_13=normalized).first()
            or BibliographicRecord.objects.filter(isbn_10=normalized).first()
        )
        if record:
            return Response(self._from_record(request, record, normalized))

        data = lookup_isbn(normalized)
        if data:
            return Response(self._from_openlibrary(data, normalized))

        return self._not_found(normalized)

    @staticmethod
    def _not_found(isbn):
        return Response(
            {
                "error": {
                    "code": "isbn_not_found",
                    "message": "ISBN introuvable dans le catalogue et sur OpenLibrary.",
                    "details": {"isbn": isbn},
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def _from_record(request, record, isbn):
        cover_url = None
        if record.cover_image:
            cover_url = request.build_absolute_uri(record.cover_image.url)
        return {
            "isbn": isbn,
            "title": record.title or None,
            "authors": [a.full_name for a in record.authors.all()],
            "publisher": record.publisher or None,
            "publication_year": record.publication_year,
            "language": record.language or None,
            "cover_url": cover_url,
            "source": "cache",
            "cached": True,
        }

    @staticmethod
    def _from_openlibrary(data, isbn):
        year = str(data.get("publication_year") or "")
        authors = data.get("authors_text", "")
        return {
            "isbn": isbn,
            "title": data.get("title") or None,
            "authors": [a.strip() for a in authors.split(";") if a.strip()],
            "publisher": data.get("publisher") or None,
            "publication_year": int(year) if year.isdigit() else None,
            "language": None,
            "cover_url": None,
            "source": "openlibrary",
            "cached": False,
        }
