from __future__ import annotations

import json
from pathlib import Path

from app.core.platform_trade_checker import FetchResult, run_platform_trade_check
from app.db import connect
from tests.helpers import copy_sample_data, temp_settings


def _fake_fetch(text: str):
    def fetcher(url: str, timeout_seconds: float) -> FetchResult:
        return FetchResult(
            fetch_status="fetched",
            http_status=200,
            content_type="text/html; charset=utf-8",
            text=text,
            content_sha256=f"sha-{Path(url).name or 'root'}",
            message="页面已抓取",
        )

    return fetcher


def test_platform_trade_check_archives_advisory_only_open_status(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    before_rules = (settings.manual_dir / "fund_rules.csv").read_text(encoding="utf-8")

    result = run_platform_trade_check(
        settings,
        asset_codes=["008887"],
        fetcher=_fake_fetch("基金交易状态：开放申购，开放赎回。支付宝页面仅作确认参考。"),
    )

    assert result["status"] == "pass"
    assert result["row_count"] == 1
    assert result["manual_review_count"] == 0
    assert result["advisory_only"] is True
    assert result["ranking_impact"] == "none"
    assert (settings.manual_dir / "fund_rules.csv").read_text(encoding="utf-8") == before_rules

    payload = json.loads(Path(result["files"]["json"]).read_text(encoding="utf-8"))
    row = payload["rows"][0]
    assert row["subscription_advisory"] == "open"
    assert row["redemption_advisory"] == "open"
    assert row["advisory_only"] is True

    with connect(settings.db_path) as conn:
        db_row = conn.execute(
            """
            SELECT asset_code, subscription_advisory, redemption_advisory, advisory_only
            FROM platform_trade_check_snapshot
            WHERE check_run_id=?
            """,
            (result["check_run_id"],),
        ).fetchone()
    assert db_row["asset_code"] == "008887"
    assert db_row["subscription_advisory"] == "open"
    assert db_row["redemption_advisory"] == "open"
    assert db_row["advisory_only"] == 1


def test_platform_trade_check_marks_limited_buy_without_blocking_candidate(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    result = run_platform_trade_check(
        settings,
        asset_codes=["270042"],
        fetcher=_fake_fetch("QDII额度提示：暂停大额申购，单日累计限额；赎回状态：开放赎回。"),
    )

    assert result["status"] == "pass"
    assert result["manual_review_count"] == 0
    payload = json.loads(Path(result["files"]["json"]).read_text(encoding="utf-8"))
    row = payload["rows"][0]
    assert row["subscription_advisory"] == "limited"
    assert row["redemption_advisory"] == "open"
    assert "advisory-only" in row["message"]


def test_platform_trade_check_skips_excluded_rows_by_default(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    result = run_platform_trade_check(settings, fetcher=_fake_fetch("开放申购 开放赎回"))
    payload = json.loads(Path(result["files"]["json"]).read_text(encoding="utf-8"))

    assert "BOND001" not in {row["asset_code"] for row in payload["rows"]}
