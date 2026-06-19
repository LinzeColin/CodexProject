from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from .db_health import check_database
from .settings import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(pattern="^(live|ready|not_ready)$")
    service: str
    product_name_zh: str
    product_version: str
    task_pack_version: str
    environment: str
    generated_at: datetime
    checks: dict[str, str]


def _base_response(status: str, checks: dict[str, str]) -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status=status,
        service=settings.app_name,
        product_name_zh=settings.product_name_zh,
        product_version=settings.product_version,
        task_pack_version=settings.task_pack_version,
        environment=settings.environment,
        generated_at=datetime.now(tz=UTC),
        checks=checks,
    )


@router.get("/health/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return _base_response("live", {"api": "ok"})


def readiness_response() -> HealthResponse:
    settings = get_settings()
    database = check_database(settings.database_url)
    readiness = "ready" if database.ok else "not_ready"
    return _base_response(
        readiness,
        {
            "api": "ok",
            "database": database.status,
            "database_detail": database.detail,
            "contracts": "validate_with_make_validate_contracts",
        },
    )


@router.get("/health/ready", response_model=HealthResponse)
def ready(response: Response) -> HealthResponse:
    payload = readiness_response()
    if payload.status == "not_ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
