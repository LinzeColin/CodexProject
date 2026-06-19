from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .settings import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(pattern="^(live|ready)$")
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


@router.get("/health/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    return _base_response(
        "ready",
        {
            "api": "ok",
            "database": "not_required_for_g1_shell",
            "contracts": "validate_with_make_validate_contracts",
        },
    )

