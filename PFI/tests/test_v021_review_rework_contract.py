from __future__ import annotations

import tempfile
from pathlib import Path

from pfi_v02.stage_v021_holdings_persistence import V021HoldingsPersistenceService


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "web" / "app" / "shell.js").read_text(encoding="utf-8")
WEB_SOURCE = HTML + "\n" + JS


def test_formal_ui_removes_boundary_limit_visible_text() -> None:
    forbidden_visible_terms = (
        "运行边界",
        "使用限制",
        "隐私边界",
        "数据边界",
        "只读边界",
        "只读",
        "实盘",
        "无实盘执行",
        "不下单",
        "不支付",
        "不登录",
        "不连接真实账户",
        "不做实盘自动下单",
        "禁止实盘自动下单",
        "只做研究",
        "不连接券商",
        "不提交订单",
        "交易密码",
        "Boundary",
    )

    for term in forbidden_visible_terms:
        assert term not in WEB_SOURCE, term
    assert "data-function-boundary" not in WEB_SOURCE


def test_holdings_frontend_uses_backend_api_not_browser_cache_for_committed_save() -> None:
    forbidden_committed_storage = (
        "const HOLDINGS_STORAGE_KEY",
        "localStorage.getItem(HOLDINGS_STORAGE_KEY",
        "localStorage.setItem(HOLDINGS_STORAGE_KEY",
        "localStorage.removeItem(HOLDINGS_STORAGE_KEY",
        "刷新或重开页面仍保留本机持仓草稿",
        "已保存到本机",
    )

    for term in forbidden_committed_storage:
        assert term not in WEB_SOURCE, term

    assert "HOLDINGS_DRAFT_STORAGE_KEY" in JS
    assert "未提交草稿" in WEB_SOURCE
    assert "/api/holdings" in JS
    assert "saveHoldingsToBackend" in JS
    assert "SQLite" in WEB_SOURCE


def test_runtime_api_persists_ui_holdings_to_sqlite_across_service_reopen() -> None:
    from pfi_v02.stage_v021_runtime_api import load_v021_holdings_payload, save_v021_holdings_payload

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "operational.sqlite"
        payload = {
            "rows": [
                {
                    "snapshotId": "v021-review-spy",
                    "portfolioId": "core",
                    "instrumentId": "SPY",
                    "displayName": "SPY ETF",
                    "quantity": 13.5,
                    "averageCost": 520.0,
                    "marketPrice": 552.25,
                    "currency": "USD",
                    "sourceId": "review_e2e",
                    "asOf": "2026-06-28",
                }
            ]
        }

        saved = save_v021_holdings_payload(payload, db_path=db_path)
        assert saved["summary"]["snapshot_count"] == 1

        reopened = V021HoldingsPersistenceService(db_path)
        persisted = reopened.get_snapshot("v021-review-spy")
        assert persisted is not None
        assert persisted.quantity == 13.5
        assert persisted.market_price == 552.25
        assert reopened.list_adjustments()

        loaded = load_v021_holdings_payload(db_path=db_path)
        assert loaded["rows"][0]["snapshotId"] == "v021-review-spy"
        assert loaded["summary"]["market_value_total"] == round(persisted.market_value, 2)


def test_trends_are_derived_from_operational_store_not_demo_arrays() -> None:
    from pfi_v02.stage_v021_runtime_api import build_v021_operational_trends, save_v021_holdings_payload

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "operational.sqlite"
        save_v021_holdings_payload(
            {
                "rows": [
                    {
                        "snapshotId": "v021-review-510300",
                        "portfolioId": "core",
                        "instrumentId": "510300",
                        "displayName": "沪深300ETF",
                        "quantity": 1000,
                        "averageCost": 3.5,
                        "marketPrice": 4.0,
                        "currency": "CNY",
                        "sourceId": "review_e2e",
                        "asOf": "2026-06-28",
                    }
                ]
            },
            db_path=db_path,
        )

        trends = build_v021_operational_trends(db_path=db_path)
        investment = trends["investment"]
        market_value = next(item for item in investment["series"] if item["id"] == "market_value_cny")
        total_return = next(item for item in investment["series"] if item["id"] == "total_return_cny")

        assert market_value["values"][-1] == 4000.0
        assert total_return["values"][-1] == 500.0
        assert investment["source"] == "SQLite 运行读模型"
        assert "hardcoded" not in JS.lower()
        assert "[86200, 88900, 91500" not in JS


def test_strategy_lab_has_one_canonical_route_and_shared_component() -> None:
    assert 'data-route-alias="/investment/strategy-lab"' in HTML
    assert 'data-command-route="/investment/strategy-lab"' in HTML
    assert '策略实验室: { workspace: "investment", routeAlias: "/investment/strategy-lab"' in JS
    assert '策略实验室: { view: "single"' not in JS
    assert 'feature("策略实验室", "可用", "PFI 策略实验室"' in JS
    assert '{ workspace: "investment", routeAlias: "/investment/strategy-lab", label: "打开策略" }' in JS
