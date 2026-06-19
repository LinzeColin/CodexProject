import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from quantlab.integrations.holding_symbol_map import (
    build_entity_registry,
    entity_registry_frame,
    holdings_symbol_proxy_frame,
    resolve_holding_symbol_proxy,
    write_entity_registry,
)


def test_holding_symbol_proxy_maps_common_fund_names_to_research_proxies():
    gold = resolve_holding_symbol_proxy("国泰黄金ETF联接A", market="CN")
    nasdaq = resolve_holding_symbol_proxy("南方纳斯达克100指数(QDII)A", market="CN")

    assert gold is not None
    assert gold.symbol == "518880"
    assert gold.role == "持仓代理"
    assert nasdaq is not None
    assert nasdaq.symbol == "QQQ"
    assert nasdaq.market == "US"


def test_holding_symbol_proxy_uses_custom_mapping_before_defaults():
    with TemporaryDirectory() as tmp:
        mapping_path = Path(tmp) / "HoldingSymbolMap.json"
        mapping_path.write_text(
            '{"mappings":[{"keywords":["黄金"],"symbol":"GLD","name":"自定义黄金代理","market":"US","confidence":"Custom","reason":"test override"}]}',
            encoding="utf-8",
        )

        proxy = resolve_holding_symbol_proxy("国泰黄金ETF联接A", market="CN", path=mapping_path)

        assert proxy is not None
        assert proxy.symbol == "GLD"
        assert proxy.confidence == "Custom"


def test_holdings_symbol_proxy_frame_marks_missing_and_proxy_rows():
    holdings = pd.DataFrame(
        [
            {"symbol": "", "name": "国泰黄金ETF联接A", "market": "CN"},
            {"symbol": "", "name": "未知主动基金", "market": "CN"},
            {"symbol": "510300", "name": "沪深300ETF", "market": "CN"},
        ]
    )

    frame = holdings_symbol_proxy_frame(holdings, market="CN")

    assert list(frame["status"]) == ["ProxyMapped", "MissingSymbol", "ConfirmedSymbol"]
    assert frame.iloc[0]["proxy_symbol"] == "518880"
    assert frame.iloc[2]["proxy_symbol"] == "510300"


def test_entity_registry_classifies_confirmed_proxy_and_missing_symbols():
    holdings = pd.DataFrame(
        [
            {"symbol": "510300", "name": "沪深300ETF", "market": "CN", "source_system": "手动录入", "updated_at": "2026-06-06"},
            {"symbol": "", "name": "国泰黄金ETF联接A", "market": "CN", "source_system": "支付宝持仓账本"},
            {"symbol": "", "name": "未知主动基金", "market": "CN", "source_system": "支付宝持仓账本"},
        ]
    )

    registry = build_entity_registry(holdings, as_of="2026-06-06T00:00:00")
    frame = entity_registry_frame(registry)

    assert registry["schema"] == "QuantLabEntityRegistryV1"
    assert registry["status_counts"] == {"MissingSymbol": 1, "ProxyMapped": 1, "TradableSymbol": 1}
    by_name = {row["name"]: row for row in frame.to_dict("records")}
    assert by_name["沪深300ETF"]["provider_symbol_tushare"] == "510300.SH"
    assert by_name["国泰黄金ETF联接A"]["canonical_symbol"] == "518880"
    assert by_name["国泰黄金ETF联接A"]["status"] == "ProxyMapped"
    assert by_name["未知主动基金"]["status"] == "MissingSymbol"


def test_write_entity_registry_exports_json_csv_markdown_without_mutating_holdings(tmp_path):
    holdings = pd.DataFrame(
        [
            {"symbol": "510300", "name": "沪深300ETF", "market": "CN", "source_system": "手动录入", "updated_at": "2026-06-06"},
            {"symbol": "", "name": "国泰黄金ETF联接A", "market": "CN", "source_system": "支付宝持仓账本"},
            {"symbol": "", "name": "未知主动基金", "market": "CN", "source_system": "支付宝持仓账本"},
        ]
    )
    original = holdings.copy(deep=True)

    registry = write_entity_registry(holdings, output_dir=tmp_path, as_of="2026-06-06T00:00:00")

    pd.testing.assert_frame_equal(holdings, original)
    json_path = tmp_path / "EntityRegistry.json"
    csv_path = tmp_path / "EntityRegistry.csv"
    markdown_path = tmp_path / "EntityRegistry.md"
    assert registry["outputs"] == {"json": str(json_path), "csv": str(csv_path), "markdown": str(markdown_path)}
    assert json_path.exists()
    assert csv_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    csv_frame = pd.read_csv(csv_path)
    markdown = markdown_path.read_text(encoding="utf-8")
    assert payload["status_counts"] == {"MissingSymbol": 1, "ProxyMapped": 1, "TradableSymbol": 1}
    assert set(csv_frame["status"]) == {"MissingSymbol", "ProxyMapped", "TradableSymbol"}
    assert "`MissingSymbol`" in markdown
