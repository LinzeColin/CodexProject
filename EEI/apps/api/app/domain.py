from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from .domain_repository import DomainRepository, NotFoundError, RepositoryError
from .settings import get_settings

router = APIRouter(prefix="/v1", tags=["domain"])


class FocusRef(BaseModel):
    object_type: Literal["entity", "industry", "theme", "facility"]
    object_id: UUID


class GraphBudget(BaseModel):
    max_nodes: int = Field(default=80, ge=1, le=500)
    max_edges: int = Field(default=300, ge=1, le=2000)
    expand_nodes: int = Field(default=40, ge=1, le=100)


class ExploreRequest(BaseModel):
    session_id: UUID | None = None
    focus: FocusRef
    active_layers: list[str]
    direction: Literal["both", "upstream", "downstream", "in", "out"]
    hops: int = Field(ge=1, le=2)
    as_of: datetime | None = None
    scoring_profile_version_id: UUID | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    budget: GraphBudget


class RerootRequest(BaseModel):
    session_id: UUID
    new_focus_entity_id: UUID
    inherit_state: bool = True
    open_in_new_workspace: bool = False


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


def get_repository() -> DomainRepository:
    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is required for domain API endpoints",
        )
    return DomainRepository(settings.database_url)


RepositoryDependency = Annotated[DomainRepository, Depends(get_repository)]


def translate_repository_error(error: RepositoryError) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


@router.get("/home")
def get_home(repository: RepositoryDependency) -> dict[str, Any]:
    try:
        return repository.list_home()
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
    response: Response,
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
    return response


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


@router.get("/calibrations")
def list_calibrations(repository: RepositoryDependency) -> list[dict[str, Any]]:
    return repository.list_calibrations()


@router.post("/calibrations/run", status_code=status.HTTP_202_ACCEPTED)
def run_calibration(repository: RepositoryDependency) -> dict[str, Any]:
    return repository.queue_calibration()
