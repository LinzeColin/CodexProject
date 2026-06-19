from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_live_health_contains_product_identity() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "live"
    assert payload["product_name_zh"] == "商域图谱"
    assert payload["product_version"] == "v0.1"
    assert payload["task_pack_version"] == "v4.2.0"


def test_ready_health_is_available_without_database_for_g1_shell() -> None:
    response = TestClient(app).get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["checks"]["database"] == "not_required_for_g1_shell"

