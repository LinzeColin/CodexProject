from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import psycopg


class ConnectionFactory(Protocol):
    def __call__(self, conninfo: str, *, connect_timeout: int) -> object: ...


@dataclass(frozen=True)
class DatabaseHealth:
    status: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def check_database(
    database_url: str | None,
    connect: ConnectionFactory = psycopg.connect,
) -> DatabaseHealth:
    if not database_url:
        return DatabaseHealth(status="not_configured", detail="DATABASE_URL is not configured")

    try:
        with connect(database_url, connect_timeout=2) as connection:
            cursor = connection.cursor()
            cursor.execute("select 1")
            row = cursor.fetchone()
    except Exception as exc:  # noqa: BLE001
        return DatabaseHealth(status="unreachable", detail=exc.__class__.__name__)

    if row != (1,):
        return DatabaseHealth(status="invalid_response", detail="database did not return select 1")
    return DatabaseHealth(status="ok", detail="postgresql ready")
