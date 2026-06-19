from __future__ import annotations

import json
from pathlib import Path

from src.monitoring.data_trust import build_data_trust_audit, write_data_trust_audit


def test_data_trust_classifies_valid_source_log_as_reconciled(tmp_path: Path) -> None:
    root = tmp_path / "project"
    reports_home = tmp_path / "reports"
    report_name = "1. 05062026_盘前报告"
    source_dir = root / "data" / "report_artifacts" / "6月第1周 0106-0706" / "_source_logs"
    markdown_dir = source_dir.parent / "_markdown"
    pdf_dir = reports_home / "6月第1周 0106-0706"
    source_dir.mkdir(parents=True)
    markdown_dir.mkdir(parents=True)
    pdf_dir.mkdir(parents=True)
    (source_dir / f"{report_name}_sources.json").write_text(
        json.dumps(
            {
                "report_name": report_name,
                "sources": [
                    {
                        "source_name": "Moomoo Watchlist Snapshot",
                        "source_url": "file:///tmp/watchlist_snapshot.csv",
                        "fetch_time": "2026-06-05T08:00:00+10:00",
                        "data_version": "v1",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (markdown_dir / f"{report_name}.md").write_text("# report", encoding="utf-8")
    (pdf_dir / f"{report_name}.pdf").write_bytes(b"%PDF-1.4\n")

    audit = build_data_trust_audit("2026-06-06", root=root, reports_home=reports_home)

    assert audit["status_counts"]["RECONCILED"] == 1
    assert audit["records"][0]["data_trust_status"] == "RECONCILED"
    assert audit["records"][0]["decision_grade"] == "Actionable"


def test_data_trust_classifies_alipay_candidates_as_review(tmp_path: Path) -> None:
    root = tmp_path / "project"
    alipay_dir = root / "data" / "private" / "alipay"
    alipay_dir.mkdir(parents=True)
    (alipay_dir / "current_positions.csv").write_text(
        "\n".join(
            [
                "date,source,symbol,name,asset_type,amount,status",
                "2026-06-05,alipay_video,,示例基金,fund,100.00,video_visible",
            ]
        ),
        encoding="utf-8",
    )

    audit = build_data_trust_audit("2026-06-06", root=root, reports_home=tmp_path / "reports")

    assert audit["audit_status"] == "Review"
    assert audit["status_counts"]["NEEDS_REVIEW"] == 1
    assert audit["records"][0]["next_action"].startswith("当前持仓含视频")


def test_data_trust_write_outputs(tmp_path: Path) -> None:
    root = tmp_path / "project"
    sample_dir = root / "data" / "sample"
    sample_dir.mkdir(parents=True)
    (sample_dir / "watchlist_moomoo.csv").write_text(
        "\n".join(
            [
                "symbol,name,exchange,asset_class",
                "512620,农业ETF天弘,SSE,ETF",
            ]
        ),
        encoding="utf-8",
    )

    audit = write_data_trust_audit("2026-06-06", root=root, reports_home=tmp_path / "reports")

    assert audit["record_count"] == 1
    assert Path(audit["outputs"]["json"]).exists()
    assert Path(audit["outputs"]["csv"]).exists()
    assert Path(audit["outputs"]["markdown"]).exists()
    assert Path(audit["outputs"]["pdf"]).exists()
