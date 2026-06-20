from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.db_health import check_database
from apps.api.app.main import app
from apps.api.app.settings import get_settings


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


def test_settings_reads_database_url_at_call_time(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://eei:test@localhost:5432/eei")

    assert get_settings().database_url == "postgresql://eei:test@localhost:5432/eei"


def test_settings_reads_cors_origins_at_call_time(monkeypatch) -> None:
    monkeypatch.setenv(
        "EEI_CORS_ALLOW_ORIGINS",
        "http://127.0.0.1:3000, http://localhost:3000",
    )

    assert get_settings().cors_allow_origins == (
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    )


def test_api_allows_configured_browser_origin_for_saved_view_requests() -> None:
    response = TestClient(app).options(
        "/v1/saved-views",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_domain_api_fails_closed_without_database(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = TestClient(app).get("/v1/home")

    assert response.status_code == 503
    assert response.json()["detail"] == "DATABASE_URL is required for domain API endpoints"


def test_catalog_api_exposes_machine_readable_object_scope_without_database(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(app)

    response = client.get("/v1/system/object-scope")

    assert response.status_code == 200
    payload = response.json()
    assert payload["navigation_module"]["name_zh"] == "对象与范围"
    assert payload["navigation_module"]["visible"] is True
    assert payload["coverage"] == {
        "required_catalogs_present": True,
        "object_scope_catalog_count": 10,
        "total_declared_rows": 363,
        "relationship_families": 10,
        "relationship_types": 52,
        "upstream_downstream_roles": 24,
        "supply_chain_stages": 16,
        "industries": 26,
        "sectors": 13,
        "business_segments": 20,
        "capital_objects": 30,
        "domain_objects": 32,
        "companies": 140,
    }
    assert all(catalog["source_of_truth"] is True for catalog in payload["catalogs"])
    assert payload["catalogs"][0]["export_links"]["json"].startswith("/v1/catalogs/")
    assert payload["catalogs"][0]["export_links"]["csv"].endswith("?format=csv")


def test_catalog_detail_exposes_definitions_and_csv_export(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(app)

    detail = client.get("/v1/catalogs/relationship")
    csv_export = client.get("/v1/catalogs/relationship?format=csv")
    missing = client.get("/v1/catalogs/not-a-catalog")

    assert detail.status_code == 200
    payload = detail.json()
    assert payload["catalog_key"] == "relationship"
    assert payload["row_count"] == 52
    assert payload["actual_row_count"] == 52
    assert {"relationship_type", "family", "direction", "definition"} <= set(payload["fields"])
    assert payload["records"][0]["definition"]
    assert csv_export.status_code == 200
    assert csv_export.text.startswith("relationship_type,family,direction")
    assert missing.status_code == 404


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
