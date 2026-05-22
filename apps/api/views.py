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

from apps.catalog.models import BibliographicRecord, ScanItem, ScanSession, ScanSessionState
from apps.catalog.openlibrary import lookup_isbn, normalize_isbn
from apps.core.models import Setting
from apps.core.search import normalize_code
from apps.inventory.models import (
    InventoryScan,
    InventoryScope,
    InventorySession,
    InventoryStatus,
)
from apps.inventory.services import close_session as close_inventory_session

from .permissions import get_session_for_user
from .serializers import (
    InventoryItemsBatchInputSerializer,
    InventorySessionCreateInputSerializer,
    OAuthTokenObtainSerializer,
    OAuthTokenRefreshSerializer,
    ScanItemsBatchInputSerializer,
    ScanSessionCreateInputSerializer,
)
from .services import finalize_scan_session


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


# ─── Sessions de scan OfeliaScan (FEAT-021) ────────────────────────────────


def _session_closed_response(session_id):
    return Response(
        {
            "error": {
                "code": "session_closed",
                "message": "Cette session n'accepte plus de modifications.",
                "details": {"session_id": str(session_id)},
            }
        },
        status=status.HTTP_409_CONFLICT,
    )


class ScanSessionCreateView(APIView):
    """`POST /scan-sessions` — crée une session de catalogage OfeliaScan."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def post(self, request):
        ser = ScanSessionCreateInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        label = ser.validated_data.get("label") or (
            f"OfeliaScan — {request.user.username}"
        )
        session = ScanSession.objects.create(label=label, created_by=request.user)
        return Response(
            {
                "session_id": str(session.session_id),
                "state": session.state,
                "created_at": session.started_at.isoformat().replace("+00:00", "Z"),
            },
            status=status.HTTP_201_CREATED,
        )


class ScanSessionItemsView(APIView):
    """`POST /scan-sessions/{id}/items` — batch d'items, idempotent par local_id."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def post(self, request, session_id):
        session = get_session_for_user(
            ScanSession, session_id=session_id, user=request.user
        )
        if not session.is_open:
            return _session_closed_response(session.session_id)

        ser = ScanItemsBatchInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        items_data = ser.validated_data["items"]

        existing_local_ids = set(
            session.items.values_list("local_id", flat=True)
        )
        accepted = 0
        duplicates = 0
        rejected = []
        for data in items_data:
            local_id = data["local_id"]
            if local_id in existing_local_ids:
                duplicates += 1
                continue
            try:
                ScanItem.objects.create(
                    session=session,
                    local_id=local_id,
                    scan_kind=data["scan_kind"],
                    scanned_value=data.get("scanned_value", ""),
                    metadata_title=data.get("metadata_title", ""),
                    metadata_authors=data.get("metadata_authors", []),
                    metadata_language=data.get("metadata_language", ""),
                    metadata_publisher=data.get("metadata_publisher", ""),
                    metadata_year=data.get("metadata_year"),
                    location_code=data.get("location_code", ""),
                    item_state=data.get("item_state", ""),
                    copy_count=data.get("copy_count", 1),
                    scanned_at=data["scanned_at"],
                    notes=data.get("notes", ""),
                )
                existing_local_ids.add(local_id)
                accepted += 1
            except Exception as exc:  # pragma: no cover
                rejected.append({"local_id": local_id, "reason": str(exc)})

        return Response(
            {
                "session_id": str(session.session_id),
                "accepted": accepted,
                "duplicates": duplicates,
                "rejected": rejected,
            }
        )


class ScanSessionFinalizeView(APIView):
    """`POST /scan-sessions/{id}/finalize` — matérialise + clôt la session."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def post(self, request, session_id):
        session = get_session_for_user(
            ScanSession, session_id=session_id, user=request.user
        )
        if not session.is_open:
            return _session_closed_response(session.session_id)
        summary = finalize_scan_session(session)
        return Response(
            {
                "session_id": str(session.session_id),
                "state": session.state,
                "finalized_at": session.finalized_at.isoformat().replace("+00:00", "Z"),
                "summary": summary,
            }
        )


# ─── Sessions de récolement OfeliaScan (FEAT-021) ──────────────────────────


def _resolve_inventory_scope(data):
    """Convertit le scope reçu (codes texte) en objets Location/Category.

    Retourne (scope_type, scope_location, scope_category, error_dict_or_None).
    """
    from apps.catalog.models import Category, Location

    scope_type = data.get("scope_type", "all")
    if scope_type == "location":
        code = data.get("scope_location_code", "")
        loc = Location.objects.filter(code=code).first()
        if not loc:
            return None, None, None, {
                "code": "unknown_location",
                "message": "Emplacement inconnu.",
                "details": {"scope_location_code": code},
            }
        return InventoryScope.LOCATION, loc, None, None
    if scope_type == "category":
        code = data.get("scope_category_code", "")
        cat = Category.objects.filter(code=code).first()
        if not cat:
            return None, None, None, {
                "code": "unknown_category",
                "message": "Catégorie inconnue.",
                "details": {"scope_category_code": code},
            }
        return InventoryScope.CATEGORY, None, cat, None
    return InventoryScope.ALL, None, None, None


class InventorySessionCreateView(APIView):
    """`POST /inventory-sessions` — crée une session de récolement."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def post(self, request):
        ser = InventorySessionCreateInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        scope_type, scope_loc, scope_cat, error = _resolve_inventory_scope(data)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        session = InventorySession.objects.create(
            label=data.get("label") or f"OfeliaScan — {request.user.username}",
            scope_type=scope_type,
            scope_location=scope_loc,
            scope_category=scope_cat,
            created_by=request.user,
            mobile_created=True,
        )
        return Response(
            {
                "session_id": str(session.session_id),
                "state": "open",
                "started_at": session.started_at.isoformat().replace("+00:00", "Z"),
            },
            status=status.HTTP_201_CREATED,
        )


class InventorySessionItemsView(APIView):
    """`POST /inventory-sessions/{id}/items` — batch de pointages."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def post(self, request, session_id):
        session = get_session_for_user(
            InventorySession, session_id=session_id, user=request.user
        )
        if session.status != InventoryStatus.OPEN:
            return _session_closed_response(session.session_id)

        ser = InventoryItemsBatchInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        items = ser.validated_data["items"]

        existing = set(session.scans.values_list("ean13", flat=True))
        accepted = 0
        duplicates = 0
        rejected = []
        from apps.catalog.models import Item

        for entry in items:
            ean = normalize_code(entry["scanned_value"])
            if ean in existing:
                duplicates += 1
                continue
            try:
                item = Item.objects.filter(ean13=ean).first()
                InventoryScan.objects.create(
                    session=session,
                    ean13=ean,
                    item=item,
                    scanned_at=entry["scanned_at"],
                    device="ofeliascan",
                )
                existing.add(ean)
                accepted += 1
            except Exception as exc:  # pragma: no cover
                rejected.append({"scanned_value": entry["scanned_value"], "reason": str(exc)})

        return Response(
            {
                "session_id": str(session.session_id),
                "accepted": accepted,
                "duplicates": duplicates,
                "rejected": rejected,
            }
        )


class InventorySessionCloseView(APIView):
    """`POST /inventory-sessions/{id}/close` — clôt la session."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def post(self, request, session_id):
        session = get_session_for_user(
            InventorySession, session_id=session_id, user=request.user
        )
        if session.status != InventoryStatus.OPEN:
            return _session_closed_response(session.session_id)
        close_inventory_session(session)
        return Response(
            {
                "session_id": str(session.session_id),
                "state": "closed",
                "closed_at": session.closed_at.isoformat().replace("+00:00", "Z"),
                "scans_count": session.scans.count(),
            }
        )
