from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SNAPSHOT_PATH = PFI_ROOT / "config/reports/v025_phase93_decision_snapshot.json"
DATA_MODULE_PATH = PFI_ROOT / "web/app/pages/reports/stage9DecisionReviewData.js"


def _snapshot() -> dict[str, object]:
    payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _embedded() -> dict[str, object]:
    source = DATA_MODULE_PATH.read_text(encoding="utf-8")
    match = re.search(r"const data = (\{.*\});\n", source)
    assert match, "generated Phase 9.3 data module must expose one JSON payload"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def _assets() -> dict[str, bytes]:
    payload = _embedded()["assetsBase64"]
    return {key: base64.b64decode(value, validate=True) for key, value in payload.items()}


def test_embedded_export_assets_match_four_format_manifest_exactly() -> None:
    snapshot = _snapshot()
    embedded = _embedded()
    assets = _assets()
    files = {row["format"]: row for row in snapshot["export_manifest"]["files"]}

    assert embedded["schema"] == "PFIV025Stage9Phase93EmbeddedDataV1"
    assert embedded["packHash"] == snapshot["pack_hash"]
    assert embedded["uiContract"] == snapshot["ui_contract"]
    assert set(assets) == {"html", "pdf", "csv", "markdown"}
    assert set(files) == set(assets)
    for export_format, payload in assets.items():
        entry = files[export_format]
        assert len(payload) == entry["byte_size"]
        assert "sha256:" + hashlib.sha256(payload).hexdigest() == entry["sha256"]
        assert entry["source_snapshot_hash"] == snapshot["export_snapshot_hash"]


def test_html_markdown_csv_and_pdf_bind_the_same_snapshot() -> None:
    snapshot = _snapshot()
    assets = _assets()
    snapshot_hash = str(snapshot["export_snapshot_hash"])

    html = assets["html"].decode("utf-8")
    assert f'name="pfi-export-snapshot-hash" content="{snapshot_hash}"' in html
    assert 'id="pfi-export-snapshot"' in html
    assert "Human review is required" in html
    assert "Automatic trading and order execution are unavailable" in html

    markdown = assets["markdown"].decode("utf-8")
    assert f"- Snapshot: `{snapshot_hash}`" in markdown
    assert "Automatic trading: `forbidden`" in markdown
    assert "## Canonical snapshot JSON" in markdown

    rows = list(csv.DictReader(io.StringIO(assets["csv"].decode("utf-8"))))
    assert len(rows) == 11
    assert {row["record_type"] for row in rows} == {"report", "component", "decision"}
    components = [row for row in rows if row["record_type"] == "component"]
    assert len(components) == 4
    assert {row["record_id"] for row in components} == {
        "total_consumption_outflow_cny",
        "living_consumption_cny",
        "investment_funding_outflow_cny",
        "investment_allocation_amount_cny",
    }
    assert {row["snapshot_hash"] for row in rows} == {snapshot_hash}
    assert {row["source_analysis_pack_hash"] for row in rows} == {
        snapshot["source_analysis_pack_hash"]
    }

    assert assets["pdf"].startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(assets["pdf"]))
    assert len(reader.pages) >= 1
    assert reader.metadata.subject == snapshot_hash
    assert "human-review-required" in str(reader.metadata.get("/Keywords", ""))
    assert "no-automatic-trading" in str(reader.metadata.get("/Keywords", ""))


def test_public_exports_contain_no_financial_amount_or_private_path() -> None:
    assets = _assets()
    for export_format in ("html", "csv", "markdown"):
        text = assets[export_format].decode("utf-8")
        assert not re.search(r"\bCNY\s+-?[0-9]", text)
        assert "/Users/" not in text
        assert "/private/var/folders/" not in text
        assert "place_order" not in text
        assert "execute_trade" not in text
