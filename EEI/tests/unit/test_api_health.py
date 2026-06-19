from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.db_health import check_database
from apps.api.app.main import app


def test_live_health_contains_product_identity() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "live"
    assert payload["product_name_zh"] == "商域图谱"
    assert payload["product_version"] == "v0.1"
    assert payload["task_pack_version"] == "v4.2.0"


def test_ready_health_requires_database_configuration(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = TestClient(app).get("/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["checks"]["database"] == "not_configured"


def test_database_health_can_pass_with_select_one() -> None:
    class Cursor:
        def execute(self, query: str) -> None:
            assert query == "select 1"

        def fetchone(self) -> tuple[int]:
            return (1,)

    class Connection:
        def __enter__(self) -> Connection:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def cursor(self) -> Cursor:
            return Cursor()

    def connect(conninfo: str, *, connect_timeout: int) -> Connection:
        assert conninfo == "postgresql://eei:test@localhost:5432/eei"
        assert connect_timeout == 2
        return Connection()

    result = check_database("postgresql://eei:test@localhost:5432/eei", connect=connect)

    assert result.ok
    assert result.status == "ok"
