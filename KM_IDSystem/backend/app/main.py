from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import APP_NAME, APP_VERSION, ensure_runtime_dirs
from app.services.db import init_db


def create_app() -> FastAPI:
    ensure_runtime_dirs()
    init_db()
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()

