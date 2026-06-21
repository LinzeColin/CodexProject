from __future__ import annotations

import sys

import httpx
import pytest

from scripts import fetch_official_source_full_text as official_source
from scripts import load_live_official_captures as live_loader


def sample_anchor_row() -> dict[str, str]:
    return {
        "anchor_id": "unit-live-anchor-001",
        "source_date": "2025-06-01",
        "official_publisher": "NVIDIA",
        "title": "NVIDIA official source unit fixture",
        "url": "https://example.test/nvidia-official-source",
        "evidence_scope": "unit test live connector contract",
        "expected_entities_or_stages": "TSMC;CoWoS;AI factories",
        "validation_status": "machine_verified",
        "notes": "unit fixture",
    }


def test_live_contract_artifact_is_no_network_and_not_release_clearance() -> None:
    payload = official_source.build_live_contract_artifact()

    assert payload["system_name"] == "EEI"
    assert payload["task_id"] == "T1301"
    assert payload["acceptance_ids"] == ["A202", "A206"]
    assert payload["status"] == "NETWORK_EVIDENCE_MISSING"
    assert payload["capture_policy"]["live_retrieval"] is False
    assert payload["capture_policy"]["relationship_publication"] is False
    assert payload["capture_policy"]["release_clearance"] is False
    assert payload["capture_policy"]["committed_full_text"] is False


def test_extract_text_from_html_ignores_scripts_and_tags() -> None:
    body = b"""
    <html>
      <head><style>.hidden { display: none; }</style></head>
      <body>
        <script>NVIDIA Corporation TSMC CoWoS AI factories hidden</script>
        <h1>NVIDIA Corporation</h1>
        <p>TSMC supports CoWoS packaging for AI factories.</p>
      </body>
    </html>
    """

    text = official_source.extract_text_from_response(
        url="https://example.test/source",
        content_type="text/html; charset=utf-8",
        body=body,
    )

    assert "hidden" not in text
    assert "NVIDIA Corporation" in text
    assert "TSMC supports CoWoS packaging for AI factories" in text


def test_token_present_accepts_governed_aliases_without_lowering_threshold() -> None:
    source_text = (
        "NVIDIA announced that Foxconn and partner facilities support "
        "advanced packaging and testing for AI factories."
    )

    assert official_source.token_present(source_text, "NVIDIA Corporation")
    assert official_source.token_present(source_text, "Hon Hai/Foxconn")
    assert official_source.token_present(source_text, "packaging/test")
    assert not official_source.token_present(
        "NVIDIA announced advanced packaging for AI factories.",
        "packaging/test",
    )


def test_select_anchor_rows_preserves_registry_order_and_rejects_unknown() -> None:
    rows = [
        {"anchor_id": "NVDA-ANCHOR-001"},
        {"anchor_id": "NVDA-ANCHOR-002"},
        {"anchor_id": "NVDA-ANCHOR-003"},
    ]

    selected = official_source.select_anchor_rows(
        rows,
        ["NVDA-ANCHOR-003", "NVDA-ANCHOR-001"],
    )

    assert [row["anchor_id"] for row in selected] == [
        "NVDA-ANCHOR-001",
        "NVDA-ANCHOR-003",
    ]
    with pytest.raises(ValueError, match="Unknown live capture anchor_id"):
        official_source.select_anchor_rows(rows, ["NVDA-ANCHOR-404"])


def test_capture_live_official_sources_records_hash_not_full_text() -> None:
    row = sample_anchor_row()
    paragraph = (
        "NVIDIA Corporation describes how TSMC, CoWoS and AI factories appear in "
        "its official ecosystem source. "
    )
    body = f"<html><body><h1>{row['title']}</h1><p>{paragraph * 8}</p></body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == row["url"]
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=body.encode("utf-8"),
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    payload = official_source.capture_live_official_sources(
        rows=[row],
        client=client,
        options=official_source.LiveCaptureOptions(sleep_between_retries=False),
    )

    anchor = payload["anchors"][0]
    assert payload["status"] == "LIVE_CAPTURE_READY_FOR_OPERATOR_REVIEW"
    assert payload["capture_policy"]["relationship_publication"] is False
    assert payload["capture_policy"]["release_clearance"] is False
    assert payload["counts"] == {
        "anchors_total": 1,
        "anchors_healthy": 1,
        "anchors_failed": 0,
    }
    assert anchor["capture_status"] == "success"
    assert anchor["source_text_sha256"]
    assert "source_text" not in anchor
    assert "source_text_excerpt" in anchor
    assert anchor["source_health"]["status"] == "healthy"
    assert anchor["source_health"]["token_coverage"]["ratio"] == 1.0
    assert anchor["source_health"]["attempts"][0]["transport"] == "httpx"


def test_capture_live_cli_requires_explicit_network_permission(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["fetch_official_source_full_text.py", "--capture-live"])

    exit_code = official_source.main()

    assert exit_code == 2
    assert "LIVE_NETWORK_NOT_ALLOWED" in capsys.readouterr().out


def test_live_capture_postgres_contract_requires_missing_operator_payload() -> None:
    payload = live_loader.build_contract_artifact()

    assert payload["system"]["en_name"] == "Enterprise Ecosystem Intelligence"
    assert payload["task_id"] == "T1301"
    assert payload["acceptance_ids"] == ["A202", "A206"]
    assert payload["status"] == "MISSING_OPERATOR_LIVE_PAYLOAD"
    assert payload["database_contract"]["relationship_fact_candidates"].startswith(
        "must remain zero"
    )


def test_live_capture_loader_rejects_committed_full_text() -> None:
    row = sample_anchor_row()
    source_health = official_source.live_capture_source_health(
        row,
        source_text=(
            "NVIDIA Corporation official text references TSMC, CoWoS and "
            "AI factories. "
            * 10
        ),
        http_status=200,
        content_type="text/html",
        content_length_bytes=512,
        attempts=[
            {
                "attempt": 1,
                "transport": "httpx",
                "status": "response",
                "http_status": 200,
            }
        ],
    )
    anchor = {
        "anchor_id": row["anchor_id"],
        "source_url": row["url"],
        "source_url_sha256": official_source.sha256_text(row["url"]),
        "capture_status": "success",
        "source_text": "forbidden committed full text",
        "source_text_sha256": "a" * 64,
        "source_text_excerpt": "NVIDIA Corporation official text references TSMC.",
        "source_health": source_health,
        "relationship_publication": False,
        "release_clearance": False,
    }

    with pytest.raises(ValueError, match="must not include committed source_text"):
        live_loader.validate_live_anchor(row, anchor)


def test_live_capture_fixture_requires_explicit_fixture_flag() -> None:
    fixture = live_loader.load_artifact(
        live_loader.ROOT
        / "tests/fixtures/live_official_captures/nvidia_live_official_capture_fixture.json"
    )

    with pytest.raises(ValueError, match="fixture_artifact requires"):
        live_loader.validate_live_capture_artifact(fixture)

    result = live_loader.validate_live_capture_artifact(
        fixture,
        allow_fixture_capture=True,
    )

    assert len(result["anchors"]) == 2
