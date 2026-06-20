from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_allow_origins),
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=[
                "content-type",
                "x-eei-actor",
                "x-eei-auth-signature",
                "x-eei-auth-timestamp",
                "x-eei-user-namespace",
            ],
        )
    app.include_router(health_router)
    app.include_router(domain_router)
    return app


app = create_app()
