from __future__ import annotations

import hashlib
import hmac
import re
import time
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .domain_repository import (
    CatalogRepository,
    ConflictError,
    DomainRepository,
    NotFoundError,
    RepositoryError,
)
from .settings import get_settings

router = APIRouter(prefix="/v1", tags=["domain"])
SAVED_VIEW_PRINCIPAL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,119}$")
SAVED_VIEW_GATEWAY_SIGNATURE_VERSION = "eei-saved-view-gateway-v1"

EntityType = Literal[
    "legal_entity",
    "brand",
    "security",
    "fund",
    "government_body",
    "person",
    "theme",
    "facility",
    "product",
    "business_segment",
    "industry",
    "contract",
    "standard",
    "asset",
]
PathType = Literal[
    "shortest",
    "upstream",
    "downstream",
    "control",
    "capital",
    "policy",
    "bottleneck",
]


class FocusRef(BaseModel):
    object_type: Literal["entity", "industry", "theme", "facility"]
    object_id: UUID


class GraphBudget(BaseModel):
    max_nodes: int = Field(default=42, ge=1, le=500)
    max_edges: int = Field(default=64, ge=1, le=2000)
    expand_nodes: int = Field(default=12, ge=1, le=100)


class ExploreRequest(BaseModel):
    session_id: UUID | None = None
    focus: FocusRef
    active_layers: list[str] = Field(default_factory=lambda: ["supply_chain_operations"])
    direction: Literal["both", "upstream", "downstream", "in", "out"] = "both"
    hops: int = Field(default=1, ge=1, le=2)
    as_of: datetime | None = None
    scoring_profile_version_id: UUID | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    budget: GraphBudget = Field(default_factory=GraphBudget)


class RerootRequest(BaseModel):
    session_id: UUID
    new_focus_entity_id: UUID
    inherit_state: bool = True
    open_in_new_workspace: bool = False


class ExpandRequest(BaseModel):
    session_id: UUID
    anchor_entity_id: UUID
    direction: Literal["both", "upstream", "downstream", "in", "out"]
    layers: list[str]
    budget: GraphBudget


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    default_scoring_profile_version_id: UUID | None = None


class WatchlistItem(BaseModel):
    object_type: Literal["entity", "industry", "theme", "facility"]
    object_id: UUID
    labels: list[str] = Field(default_factory=list)
    note: str | None = None
    saved_state: dict[str, Any] = Field(default_factory=dict)


class SavedViewCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    workspace_key: str = Field(default="default", min_length=1, max_length=120)
    state: dict[str, Any]
    schema_version: Literal["saved-view-v1"] = "saved-view-v1"
    change_note: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SavedViewUpdate(BaseModel):
    expected_version: int = Field(ge=1)
    state: dict[str, Any]
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    schema_version: Literal["saved-view-v1"] = "saved-view-v1"
    change_note: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SavedViewRestore(BaseModel):
    target_version: int = Field(ge=1)
    expected_version: int = Field(ge=1)
    change_note: str | None = Field(default=None, max_length=500)


class SavedViewPrincipal(BaseModel):
    namespace: str
    actor: str


class ScoringActivationRequest(BaseModel):
    expected_active_profile_version_id: UUID | None = None
    client_refresh_token: str | None = None
    reason: str = Field(
        default="Manual model activation request",
        min_length=1,
        max_length=500,
    )


class ScoringRollbackRequest(ScoringActivationRequest):
    reason: str = Field(
        default="Manual model rollback request",
        min_length=1,
        max_length=500,
    )


class ScoringProfileDraftCreate(BaseModel):
    base_profile_version_id: UUID | None = None
    profile_key: str = Field(
        default="balanced-v2-online-draft",
        min_length=3,
        max_length=80,
        pattern=r"^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$",
    )
    name: str = Field(default="Balanced v2 Online Draft", min_length=1, max_length=160)
    weights: dict[str, float]
    thresholds: dict[str, Any] = Field(default_factory=dict)
    half_lives_days: dict[str, int] = Field(default_factory=dict)
    missing_value_policy: Literal[
        "renormalize_available",
        "mark_unscored",
        "conservative_penalty",
    ] = "renormalize_available"
    reason: str = Field(
        default="Manual model-center online edit draft",
        min_length=1,
        max_length=500,
    )


class ScoringRecomputeRequest(BaseModel):
    expected_active_profile_version_id: UUID | None = None
    client_refresh_token: str | None = None
    scope: Literal["global", "active_workspace"] = "global"
    reason: str = Field(
        default="Manual score recompute request",
        min_length=1,
        max_length=500,
    )


class DataSnapshotRefreshRequest(BaseModel):
    expected_active_profile_version_id: UUID | None = None
    client_refresh_token: str | None = None
    scope: Literal["golden-vertical:nvidia", "global"] = "golden-vertical:nvidia"
    record_mode: Literal["fixture", "curated_official_fixture", "dry_run", "live"] = (
        "curated_official_fixture"
    )
    reason: str = Field(
        default="Manual data snapshot refresh request",
        min_length=1,
        max_length=500,
    )


def get_repository() -> DomainRepository:
    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is required for domain API endpoints",
        )
    return DomainRepository(settings.database_url)


RepositoryDependency = Annotated[DomainRepository, Depends(get_repository)]
CatalogRepositoryDependency = Annotated[CatalogRepository, Depends(CatalogRepository)]


def _normalize_saved_view_header(value: str | None, *, default: str) -> str:
    normalized = (value or default).strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "reason": "invalid_saved_view_principal",
                "message": "Saved-view namespace and actor headers cannot be blank.",
            },
        )
    if not SAVED_VIEW_PRINCIPAL_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "reason": "invalid_saved_view_principal",
                "message": (
                    "Saved-view namespace and actor headers must match "
                    "^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,119}$."
                ),
            },
        )
    return normalized


def _saved_view_gateway_signature_payload(
    *,
    method: str,
    path: str,
    namespace: str,
    actor: str,
    timestamp: str,
) -> str:
    return "\n".join(
        [
            SAVED_VIEW_GATEWAY_SIGNATURE_VERSION,
            method.upper(),
            path,
            namespace,
            actor,
            timestamp,
        ]
    )


def saved_view_gateway_signature(
    *,
    secret: str,
    method: str,
    path: str,
    namespace: str,
    actor: str,
    timestamp: str,
) -> str:
    payload = _saved_view_gateway_signature_payload(
        method=method,
        path=path,
        namespace=namespace,
        actor=actor,
        timestamp=timestamp,
    )
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _require_saved_view_gateway_principal(
    *,
    request: Request,
    namespace: str | None,
    actor: str | None,
    timestamp: str | None,
    signature: str | None,
) -> SavedViewPrincipal:
    settings = get_settings()
    if not settings.saved_view_gateway_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "reason": "saved_view_identity_gateway_not_configured",
                "message": (
                    "EEI_SAVED_VIEW_GATEWAY_SECRET is required when saved-view "
                    "identity mode is trusted_gateway."
                ),
            },
        )

    missing = [
        header
        for header, value in (
            ("X-EEI-User-Namespace", namespace),
            ("X-EEI-Actor", actor),
            ("X-EEI-Auth-Timestamp", timestamp),
            ("X-EEI-Auth-Signature", signature),
        )
        if value is None or not value.strip()
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "reason": "missing_saved_view_gateway_identity",
                "message": "Saved-view requests require trusted gateway identity headers.",
                "missing_headers": missing,
            },
        )

    resolved_namespace = _normalize_saved_view_header(namespace, default="")
    resolved_actor = _normalize_saved_view_header(actor, default="")
    assert timestamp is not None
    assert signature is not None
    try:
        issued_at = int(timestamp)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "reason": "invalid_saved_view_gateway_timestamp",
                "message": "Saved-view gateway timestamp must be Unix epoch seconds.",
            },
        ) from exc

    now = int(time.time())
    if abs(now - issued_at) > settings.saved_view_signature_ttl_seconds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "reason": "expired_saved_view_gateway_signature",
                "message": "Saved-view gateway signature timestamp is outside the allowed window.",
            },
        )

    expected = saved_view_gateway_signature(
        secret=settings.saved_view_gateway_secret,
        method=request.method,
        path=request.url.path,
        namespace=resolved_namespace,
        actor=resolved_actor,
        timestamp=timestamp,
    )
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "reason": "invalid_saved_view_gateway_signature",
                "message": "Saved-view gateway signature verification failed.",
            },
        )
    return SavedViewPrincipal(namespace=resolved_namespace, actor=resolved_actor)


def get_saved_view_principal(
    request: Request,
    namespace: Annotated[str | None, Header(alias="X-EEI-User-Namespace")] = None,
    actor: Annotated[str | None, Header(alias="X-EEI-Actor")] = None,
    auth_timestamp: Annotated[str | None, Header(alias="X-EEI-Auth-Timestamp")] = None,
    auth_signature: Annotated[str | None, Header(alias="X-EEI-Auth-Signature")] = None,
) -> SavedViewPrincipal:
    if get_settings().saved_view_identity_mode == "trusted_gateway":
        return _require_saved_view_gateway_principal(
            request=request,
            namespace=namespace,
            actor=actor,
            timestamp=auth_timestamp,
            signature=auth_signature,
        )
    resolved_namespace = _normalize_saved_view_header(namespace, default="local_user")
    resolved_actor = _normalize_saved_view_header(actor, default=resolved_namespace)
    return SavedViewPrincipal(namespace=resolved_namespace, actor=resolved_actor)


SavedViewPrincipalDependency = Annotated[SavedViewPrincipal, Depends(get_saved_view_principal)]


def translate_repository_error(error: RepositoryError) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error.detail)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


@router.get("/home")
def get_home(repository: RepositoryDependency) -> dict[str, Any]:
    try:
        return repository.list_home()
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/catalogs")
def list_catalogs(repository: CatalogRepositoryDependency) -> dict[str, Any]:
    return repository.list_catalogs()


@router.get("/catalogs/{catalogKey}", response_model=None)
def get_catalog(
    catalogKey: str,
    repository: CatalogRepositoryDependency,
    format: Literal["json", "csv"] = Query(default="json"),
) -> dict[str, Any] | FileResponse:
    try:
        if format == "csv":
            csv_path = repository.csv_path_for_key(catalogKey)
            return FileResponse(
                csv_path,
                media_type="text/csv",
                filename=csv_path.name,
            )
        return repository.get_catalog(catalogKey)
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/system/object-scope")
def get_object_scope(repository: CatalogRepositoryDependency) -> dict[str, Any]:
    return repository.object_scope()


@router.get("/entities")
def search_entities(
    repository: RepositoryDependency,
    q: Annotated[str | None, Query()] = None,
    type: Annotated[EntityType | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict[str, Any]]:
    try:
        return repository.search_entities(query=q, entity_type=type, limit=limit)
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/entities/{entityId}")
def get_entity(entityId: UUID, repository: RepositoryDependency) -> dict[str, Any]:
    try:
        return repository.get_entity(entityId)
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/entities/{entityId}/empire")
def get_entity_empire(
    entityId: UUID,
    repository: RepositoryDependency,
    as_of: Annotated[datetime | None, Query()] = None,
    profile: Annotated[UUID | None, Query()] = None,
) -> dict[str, Any]:
    try:
        return repository.get_entity_empire(
            entity_id=entityId,
            as_of=as_of,
            profile_id=profile,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/industries")
def list_industries(
    repository: RepositoryDependency,
    parent: Annotated[UUID | None, Query()] = None,
) -> list[dict[str, Any]]:
    return repository.list_industries(parent=parent)


@router.get("/industries/{industryId}/landscape")
def get_industry_landscape(
    industryId: UUID,
    repository: RepositoryDependency,
    as_of: Annotated[datetime | None, Query()] = None,
    profile: Annotated[UUID | None, Query()] = None,
) -> dict[str, Any]:
    try:
        return repository.get_industry_landscape(
            industry_id=industryId,
            as_of=as_of,
            profile_id=profile,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/explore")
def start_or_restore_exploration(
    payload: ExploreRequest,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.start_exploration(payload.model_dump(mode="json"))
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/explore/reroot")
def reroot_exploration(
    payload: RerootRequest,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.reroot_exploration(payload.model_dump(mode="json"))
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/explore/expand")
def expand_exploration(
    payload: ExpandRequest,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.expand_exploration(payload.model_dump(mode="json"))
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/paths")
def find_relationship_paths(
    repository: RepositoryDependency,
    from_entity_id: Annotated[UUID, Query(alias="from")],
    to_entity_id: Annotated[UUID, Query(alias="to")],
    path_type: Annotated[PathType, Query()] = "shortest",
    max_length: Annotated[int, Query(ge=1, le=8)] = 4,
    as_of: Annotated[datetime | None, Query()] = None,
) -> dict[str, Any]:
    try:
        return repository.find_relationship_paths(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            path_type=path_type,
            max_length=max_length,
            as_of=as_of,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/watchlists")
def list_watchlists(repository: RepositoryDependency) -> list[dict[str, Any]]:
    return repository.list_watchlists()


@router.post("/watchlists", status_code=status.HTTP_201_CREATED)
def create_watchlist(
    payload: WatchlistCreate,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.create_watchlist(
            name=payload.name,
            description=payload.description,
            default_scoring_profile_version_id=payload.default_scoring_profile_version_id,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/watchlists/{watchlistId}")
def get_watchlist(watchlistId: UUID, repository: RepositoryDependency) -> dict[str, Any]:
    try:
        return repository.get_watchlist(watchlistId)
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/watchlists/{watchlistId}/items", status_code=status.HTTP_201_CREATED)
def add_watchlist_item(
    watchlistId: UUID,
    payload: WatchlistItem,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.add_watchlist_item(
            watchlistId,
            object_type=payload.object_type,
            object_id=payload.object_id,
            labels=payload.labels,
            note=payload.note,
            saved_state=payload.saved_state,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.delete("/watchlists/{watchlistId}/items", status_code=status.HTTP_204_NO_CONTENT)
def remove_watchlist_item(
    watchlistId: UUID,
    object_type: Literal["entity", "industry", "theme", "facility"],
    object_id: UUID,
    repository: RepositoryDependency,
) -> Response:
    try:
        repository.remove_watchlist_item(
            watchlistId,
            object_type=object_type,
            object_id=object_id,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/saved-views")
def list_saved_views(
    repository: RepositoryDependency,
    principal: SavedViewPrincipalDependency,
    workspace_key: Annotated[str, Query(min_length=1, max_length=120)] = "default",
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    try:
        return repository.list_saved_views(
            namespace=principal.namespace,
            workspace_key=workspace_key,
            include_inactive=include_inactive,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/saved-views", status_code=status.HTTP_201_CREATED)
def create_saved_view(
    payload: SavedViewCreate,
    repository: RepositoryDependency,
    principal: SavedViewPrincipalDependency,
) -> dict[str, Any]:
    try:
        return repository.create_saved_view(
            name=payload.name,
            description=payload.description,
            namespace=principal.namespace,
            workspace_key=payload.workspace_key,
            state=payload.state,
            schema_version=payload.schema_version,
            change_note=payload.change_note,
            metadata=payload.metadata,
            actor=principal.actor,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/saved-views/{savedViewId}")
def get_saved_view(
    savedViewId: UUID,
    repository: RepositoryDependency,
    principal: SavedViewPrincipalDependency,
) -> dict[str, Any]:
    try:
        return repository.get_saved_view(savedViewId, namespace=principal.namespace)
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.put("/saved-views/{savedViewId}")
def update_saved_view(
    savedViewId: UUID,
    payload: SavedViewUpdate,
    repository: RepositoryDependency,
    principal: SavedViewPrincipalDependency,
) -> dict[str, Any]:
    try:
        return repository.update_saved_view(
            savedViewId,
            expected_version=payload.expected_version,
            namespace=principal.namespace,
            name=payload.name,
            description=payload.description,
            state=payload.state,
            schema_version=payload.schema_version,
            change_note=payload.change_note,
            metadata=payload.metadata,
            actor=principal.actor,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/saved-views/{savedViewId}/versions")
def list_saved_view_versions(
    savedViewId: UUID,
    repository: RepositoryDependency,
    principal: SavedViewPrincipalDependency,
) -> list[dict[str, Any]]:
    try:
        return repository.list_saved_view_versions(
            savedViewId,
            namespace=principal.namespace,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/saved-views/{savedViewId}/restore")
def restore_saved_view(
    savedViewId: UUID,
    payload: SavedViewRestore,
    repository: RepositoryDependency,
    principal: SavedViewPrincipalDependency,
) -> dict[str, Any]:
    try:
        return repository.restore_saved_view(
            savedViewId,
            target_version=payload.target_version,
            expected_version=payload.expected_version,
            change_note=payload.change_note,
            namespace=principal.namespace,
            actor=principal.actor,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/changes")
def list_changes(
    repository: RepositoryDependency,
    since: datetime | None = None,
    change_type: str | None = None,
) -> list[dict[str, Any]]:
    return repository.list_changes(since=since, change_type=change_type)


@router.get("/audit-logs")
def list_audit_logs(
    repository: RepositoryDependency,
    object_type: str | None = None,
    object_id: UUID | None = None,
    since: datetime | None = None,
) -> list[dict[str, Any]]:
    return repository.list_audit_logs(object_type=object_type, object_id=object_id, since=since)


@router.get("/scoring/profiles")
def list_scoring_profiles(repository: RepositoryDependency) -> list[dict[str, Any]]:
    return repository.list_scoring_profiles()


@router.post("/scoring/profiles", status_code=status.HTTP_201_CREATED)
def create_scoring_profile_version(
    payload: ScoringProfileDraftCreate,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.create_scoring_profile_version(
            base_profile_version_id=payload.base_profile_version_id,
            profile_key=payload.profile_key,
            name=payload.name,
            weights=payload.weights,
            thresholds=payload.thresholds or None,
            half_lives_days=payload.half_lives_days or None,
            missing_value_policy=payload.missing_value_policy,
            reason=payload.reason,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/scoring/active-context")
def get_active_scoring_context(
    repository: RepositoryDependency,
    client_refresh_token: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    try:
        return repository.get_active_analysis_context(
            client_refresh_token=client_refresh_token,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/scoring/profiles/{profileVersionId}/activate")
def activate_scoring_profile(
    profileVersionId: UUID,
    payload: ScoringActivationRequest,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.activate_scoring_profile_version(
            profile_version_id=profileVersionId,
            expected_active_profile_version_id=payload.expected_active_profile_version_id,
            client_refresh_token=payload.client_refresh_token,
            reason=payload.reason,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/scoring/profiles/{profileVersionId}/rollback")
def rollback_scoring_profile(
    profileVersionId: UUID,
    payload: ScoringRollbackRequest,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.rollback_scoring_profile_version(
            profile_version_id=profileVersionId,
            expected_active_profile_version_id=payload.expected_active_profile_version_id,
            client_refresh_token=payload.client_refresh_token,
            reason=payload.reason,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/scoring/recompute")
def enqueue_score_recompute(
    payload: ScoringRecomputeRequest,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.enqueue_score_recompute(
            expected_active_profile_version_id=payload.expected_active_profile_version_id,
            client_refresh_token=payload.client_refresh_token,
            scope=payload.scope,
            reason=payload.reason,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.post("/data/snapshots/refresh")
def enqueue_data_snapshot_refresh(
    payload: DataSnapshotRefreshRequest,
    repository: RepositoryDependency,
) -> dict[str, Any]:
    try:
        return repository.enqueue_data_snapshot_refresh(
            expected_active_profile_version_id=payload.expected_active_profile_version_id,
            client_refresh_token=payload.client_refresh_token,
            scope=payload.scope,
            record_mode=payload.record_mode,
            reason=payload.reason,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/scoring/explain/{objectType}/{objectId}")
def explain_score(
    objectType: str,
    objectId: UUID,
    repository: RepositoryDependency,
    profile: Annotated[UUID | None, Query()] = None,
) -> dict[str, Any]:
    try:
        return repository.explain_score(
            object_type=objectType,
            object_id=objectId,
            profile_id=profile,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/evidence/{objectType}/{objectId}")
def get_evidence_detail(
    objectType: str,
    objectId: UUID,
    repository: RepositoryDependency,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> dict[str, Any]:
    try:
        return repository.evidence_detail(
            object_type=objectType,
            object_id=objectId,
            limit=limit,
        )
    except RepositoryError as exc:
        raise translate_repository_error(exc) from exc


@router.get("/calibrations")
def list_calibrations(repository: RepositoryDependency) -> list[dict[str, Any]]:
    return repository.list_calibrations()


@router.post("/calibrations/run", status_code=status.HTTP_202_ACCEPTED)
def run_calibration(repository: RepositoryDependency) -> dict[str, Any]:
    return repository.queue_calibration()
