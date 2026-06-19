from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_case_generates_pdf_report():
    response = client.post(
        "/api/cases",
        json={
            "module": "gear",
            "title": "测试齿圈修复案例",
            "input_data": {"wear_depth": 1.6, "crack_length": 12, "temperature": 126},
            "uploaded_rows": [],
            "role": "engineer",
            "auto_generate_report": True,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["report_status"] == "ready"
    assert Path(payload["report_path"]).exists()
    assert payload["result"]["visualizations"]


def test_dashboard_and_model_settings_endpoints():
    dashboard = client.get("/api/dashboard/summary")
    assert dashboard.status_code == 200
    assert "risk_distribution" in dashboard.json()

    models = client.get("/api/settings/models")
    assert models.status_code == 200
    assert len(models.json()) >= 3

