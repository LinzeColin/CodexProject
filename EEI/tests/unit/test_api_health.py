from __future__ import annotations

import time

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from apps.api.app.db_health import check_database
from apps.api.app.domain import get_saved_view_principal, saved_view_gateway_signature
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


def test_settings_defaults_saved_view_identity_to_trusted_gateway_in_production(
    monkeypatch,
) -> None:
    monkeypatch.setenv("EEI_ENV", "production")
    monkeypatch.delenv("EEI_SAVED_VIEW_IDENTITY_MODE", raising=False)

    assert get_settings().saved_view_identity_mode == "trusted_gateway"


def test_settings_allows_local_saved_view_identity_override_in_production(monkeypatch) -> None:
    monkeypatch.setenv("EEI_ENV", "production")
    monkeypatch.setenv("EEI_SAVED_VIEW_IDENTITY_MODE", "local")

    assert get_settings().saved_view_identity_mode == "local"


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
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "x-eei-user-namespace" in allowed_headers
    assert "x-eei-auth-signature" in allowed_headers


def request_for_saved_views(method: str = "GET", path: str = "/v1/saved-views") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
        }
    )


def test_saved_view_principal_local_mode_keeps_local_default(monkeypatch) -> None:
    monkeypatch.setenv("EEI_ENV", "local")
    monkeypatch.delenv("EEI_SAVED_VIEW_IDENTITY_MODE", raising=False)

    principal = get_saved_view_principal(request_for_saved_views())

    assert principal.namespace == "local_user"
    assert principal.actor == "local_user"


def test_saved_view_principal_production_requires_gateway_secret(monkeypatch) -> None:
    monkeypatch.setenv("EEI_ENV", "production")
    monkeypatch.delenv("EEI_SAVED_VIEW_IDENTITY_MODE", raising=False)
    monkeypatch.delenv("EEI_SAVED_VIEW_GATEWAY_SECRET", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        get_saved_view_principal(
            request_for_saved_views(),
            namespace="tenant-prod",
            actor="tenant-prod-analyst",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["reason"] == "saved_view_identity_gateway_not_configured"


def test_saved_view_principal_trusted_gateway_rejects_unsigned_headers(monkeypatch) -> None:
    monkeypatch.setenv("EEI_ENV", "production")
    monkeypatch.setenv("EEI_SAVED_VIEW_GATEWAY_SECRET", "test-hmac-fixture-key")

    with pytest.raises(HTTPException) as exc_info:
        get_saved_view_principal(
            request_for_saved_views(),
            namespace="tenant-prod",
            actor="tenant-prod-analyst",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["reason"] == "missing_saved_view_gateway_identity"


def test_saved_view_principal_trusted_gateway_rejects_invalid_signature(monkeypatch) -> None:
    monkeypatch.setenv("EEI_ENV", "production")
    monkeypatch.setenv("EEI_SAVED_VIEW_GATEWAY_SECRET", "test-hmac-fixture-key")

    with pytest.raises(HTTPException) as exc_info:
        get_saved_view_principal(
            request_for_saved_views(method="POST"),
            namespace="tenant-prod",
            actor="tenant-prod-analyst",
            auth_timestamp=str(int(time.time())),
            auth_signature="not-a-valid-signature",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["reason"] == "invalid_saved_view_gateway_signature"


def test_saved_view_principal_trusted_gateway_accepts_valid_signature(monkeypatch) -> None:
    gateway_hmac_fixture_key = "test-hmac-fixture-key"
    namespace = "tenant-prod"
    actor = "tenant-prod-analyst"
    timestamp = str(int(time.time()))
    request = request_for_saved_views(method="POST")
    monkeypatch.setenv("EEI_ENV", "production")
    monkeypatch.setenv("EEI_SAVED_VIEW_GATEWAY_SECRET", gateway_hmac_fixture_key)
    signature = saved_view_gateway_signature(
        secret=gateway_hmac_fixture_key,
        method=request.method,
        path=request.url.path,
        namespace=namespace,
        actor=actor,
        timestamp=timestamp,
    )

    principal = get_saved_view_principal(
        request,
        namespace=namespace,
        actor=actor,
        auth_timestamp=timestamp,
        auth_signature=signature,
    )

    assert principal.namespace == namespace
    assert principal.actor == actor


def test_saved_view_principal_trusted_gateway_rejects_expired_signature(monkeypatch) -> None:
    gateway_hmac_fixture_key = "test-hmac-fixture-key"
    namespace = "tenant-prod"
    actor = "tenant-prod-analyst"
    timestamp = str(int(time.time()) - 999)
    request = request_for_saved_views(method="POST")
    monkeypatch.setenv("EEI_ENV", "production")
    monkeypatch.setenv("EEI_SAVED_VIEW_GATEWAY_SECRET", gateway_hmac_fixture_key)
    monkeypatch.setenv("EEI_SAVED_VIEW_SIGNATURE_TTL_SECONDS", "300")
    signature = saved_view_gateway_signature(
        secret=gateway_hmac_fixture_key,
        method=request.method,
        path=request.url.path,
        namespace=namespace,
        actor=actor,
        timestamp=timestamp,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_saved_view_principal(
            request,
            namespace=namespace,
            actor=actor,
            auth_timestamp=timestamp,
            auth_signature=signature,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["reason"] == "expired_saved_view_gateway_signature"


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
