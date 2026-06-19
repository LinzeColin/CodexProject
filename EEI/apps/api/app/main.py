from __future__ import annotations

from fastapi import FastAPI

from .domain import router as domain_router
from .health import router as health_router
from .settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.product_version,
        summary="商域图谱 API shell for MVP G1.",
    )
    app.include_router(health_router)
    app.include_router(domain_router)
    return app


app = create_app()
