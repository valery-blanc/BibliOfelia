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

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import Role
from apps.catalog.models import (
    BibliographicRecord,
    Location,
    ScanItem,
    ScanSession,
    ScanSessionState,
)
from apps.catalog.openlibrary import lookup_isbn, normalize_isbn
from apps.core.models import Setting
from apps.core.search import normalize_code
from apps.inventory.models import (
    InventoryScan,
    InventoryScope,
    InventorySession,
    InventoryStatus,
)
from apps.inventory.services import (
    maybe_relocate,
    close_session as close_inventory_session,
)

from .models import ScanHandoff, ScanHandoffState
from .permissions import get_session_for_user
from .serializers import (
    InventoryItemsBatchInputSerializer,
    InventorySessionCreateInputSerializer,
    LocationSerializer,
    OAuthTokenObtainSerializer,
    OAuthTokenRefreshSerializer,
    ScanHandoffCreateInputSerializer,
    ScanHandoffSubmitInputSerializer,
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
            raw = normalize_code(entry["scanned_value"])
            # Résolution de l'exemplaire : code interne Ofelia 290… en priorité,
            # puis ISBN-13 / ISBN-10 commercial.  Pour les ISBN multi-exemplaires,
            # on exclut les EAN déjà présents dans existing pour pointer le
            # prochain exemplaire non encore pointé (BUG-008).
            item = Item.objects.filter(ean13=raw).first()
            if item:
                storage_ean = raw
            else:
                item = (
                    Item.objects.filter(record__isbn_13=raw)
                    .exclude(ean13__in=existing)
                    .first()
                    or Item.objects.filter(record__isbn_10=raw)
                    .exclude(ean13__in=existing)
                    .first()
                )
                storage_ean = item.ean13 if item else raw

            if storage_ean in existing:
                duplicates += 1
                continue
            try:
                InventoryScan.objects.create(
                    session=session,
                    ean13=storage_ean,
                    item=item,
                    scanned_at=entry["scanned_at"],
                    device="ofeliascan",
                )
                existing.add(storage_ean)
                accepted += 1
                # FEAT-033 : relocate auto si session scopée sur une location
                maybe_relocate(item, session)
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


# ─── Scan handoff single-scan (FEAT-023) ───────────────────────────────────

DEEP_LINK_SCHEME = "ofeliascan://scan-one"
DEEP_LINK_INTENT_HOST = "scan-one"
DEEP_LINK_INTENT_SCHEME = "ofeliascan"


def _can_create_handoff(user) -> bool:
    return user.is_authenticated and user.role in (Role.SUPERADMIN, Role.LIBRARIAN)


def _can_view_handoff(handoff, user) -> bool:
    if not user.is_authenticated:
        return False
    if user.role == Role.SUPERADMIN:
        return True
    return handoff.created_by_id == user.id


def _serialize_handoff(handoff) -> dict:
    return {
        "token": str(handoff.token),
        "state": handoff.effective_state(),
        "target_kind": handoff.target_kind,
        "value": handoff.value,
        "value_kind": handoff.value_kind,
        "created_at": handoff.created_at.isoformat().replace("+00:00", "Z"),
        "expires_at": handoff.expires_at.isoformat().replace("+00:00", "Z"),
        "completed_at": (
            handoff.completed_at.isoformat().replace("+00:00", "Z")
            if handoff.completed_at
            else None
        ),
    }


def _build_deep_link(token: str, target_kind: str) -> str:
    """URL au scheme custom — Firefox/Safari/iOS, fallback hors Chrome Android."""
    return f"{DEEP_LINK_SCHEME}?token={token}&kind={target_kind}"


def _build_android_intent_url(token: str, target_kind: str) -> str:
    """URL `intent://` pour Chrome Android (plus fiable que le scheme custom).

    Chrome Android n'ouvre plus systématiquement `ofeliascan://…` via
    `window.location.href` (politique anti-deeplink-spam) ; l'URL `intent://`
    avec `package=` cible explicitement l'app installée et contourne la
    restriction.
    """
    package = settings.OFELIASCAN_ANDROID_PACKAGE
    return (
        f"intent://{DEEP_LINK_INTENT_HOST}?token={token}&kind={target_kind}"
        f"#Intent;scheme={DEEP_LINK_INTENT_SCHEME};package={package};end"
    )


def _handoff_error(code: str, message: str, http_status: int, **details):
    return Response(
        {"error": {"code": code, "message": message, "details": details}},
        status=http_status,
    )


class ScanHandoffCreateView(APIView):
    """`POST /scan-handoff` — crée un handoff pour la session web courante.

    Réservé aux librarian/superadmin (le contributor_api OfeliaScan ne crée
    pas de handoff, il les consomme). Retourne un token UUID + le deep-link
    `ofeliascan://scan-one?token=...&kind=...` que le navigateur ouvre pour
    déclencher OfeliaScan.
    """

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def post(self, request):
        if not _can_create_handoff(request.user):
            return _handoff_error(
                "forbidden",
                "Seul un bibliothécaire peut créer un handoff de scan.",
                status.HTTP_403_FORBIDDEN,
            )
        ser = ScanHandoffCreateInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target_kind = ser.validated_data.get("target_kind", "auto")
        handoff = ScanHandoff.objects.create(
            created_by=request.user, target_kind=target_kind
        )
        body = _serialize_handoff(handoff)
        body["deep_link"] = _build_deep_link(handoff.token, target_kind)
        body["android_intent_url"] = _build_android_intent_url(
            handoff.token, target_kind
        )
        return Response(body, status=status.HTTP_201_CREATED)


class ScanHandoffDetailView(APIView):
    """`GET/POST /scan-handoff/{token}`.

    `GET` (session-auth) : polling du résultat par le navigateur, réservé au
    créateur du handoff (sinon 404, pas de fuite d'existence).

    `POST` (JWT) : callback OfeliaScan — soumet la valeur scannée OU annule.
    Le token UUID est la capability ; tout JWT authentifié peut soumettre
    (la confidentialité du deep-link suffit en LAN).
    """

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def _get_handoff(self, token):
        return get_object_or_404(ScanHandoff, token=token)

    def get(self, request, token):
        handoff = self._get_handoff(token)
        if not _can_view_handoff(handoff, request.user):
            raise Http404()
        return Response(_serialize_handoff(handoff))

    def post(self, request, token):
        handoff = self._get_handoff(token)
        if handoff.state != ScanHandoffState.PENDING:
            return _handoff_error(
                "already_completed",
                "Handoff déjà complété ou annulé.",
                status.HTTP_409_CONFLICT,
                state=handoff.state,
            )
        if handoff.is_expired:
            return _handoff_error(
                "expired",
                "Le handoff a expiré.",
                status.HTTP_410_GONE,
                expires_at=handoff.expires_at.isoformat(),
            )

        ser = ScanHandoffSubmitInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        if data.get("cancelled"):
            handoff.state = ScanHandoffState.CANCELLED
            handoff.completed_at = timezone.now()
            handoff.completed_by = request.user
            handoff.save(update_fields=["state", "completed_at", "completed_by"])
        else:
            handoff.value = normalize_code(data["value"])
            handoff.value_kind = data.get("kind") or "manual"
            handoff.state = ScanHandoffState.COMPLETED
            handoff.completed_at = timezone.now()
            handoff.completed_by = request.user
            handoff.save(
                update_fields=[
                    "value",
                    "value_kind",
                    "state",
                    "completed_at",
                    "completed_by",
                ]
            )
        return Response(_serialize_handoff(handoff))


# ─── FEAT-032 — Catalogue des emplacements ────────────────────────────────


class LocationListView(APIView):
    """`GET /locations` — liste des emplacements pour le picker OfeliaScan.

    Lecture seule. La création/édition/suppression se fait depuis l'UI
    librarian (`/catalog/locations/`) — OfeliaScan n'a pas vocation à créer
    de Location lui-même.
    """

    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def get(self, request):
        qs = Location.objects.select_related("parent").order_by("code")
        return Response({"locations": LocationSerializer(qs, many=True).data})
