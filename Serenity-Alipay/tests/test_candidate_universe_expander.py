from pathlib import Path

from app.core.candidate_universe_expander import (
    expand_candidate_universe,
    parse_eastmoney_fund_list,
    select_growth_funds,
)
from tests.helpers import copy_sample_data, temp_settings


def test_parse_eastmoney_fund_list_payload():
    payload = 'var r = [["000001","HXCZHH","华夏成长混合","混合型-灵活","HUAXIACHENGZHANGHUNHE"],["000009","YFDTTLCHBA","易方达天天理财货币A","货币型-普通货币","YIFANGDA"]];'

    rows = parse_eastmoney_fund_list(payload)

    assert rows[0]["code"] == "000001"
    assert rows[0]["name"] == "华夏成长混合"
    assert rows[0]["fund_type"] == "混合型-灵活"


def test_select_growth_funds_excludes_conservative_assets():
    rows = [
        {"code": "000001", "name": "华夏半导体芯片混合A", "fund_type": "混合型-偏股", "pinyin": "HXBDT"},
        {"code": "000002", "name": "稳健短债债券A", "fund_type": "债券型-短债", "pinyin": "WJDZ"},
        {"code": "000003", "name": "纳斯达克人工智能QDIIA", "fund_type": "QDII", "pinyin": "NSDKRGZN"},
    ]

    selected = select_growth_funds(rows, min_theme_score=3, limit=10)

    assert [item.code for item in selected] == ["000003", "000001"]


def test_short_ascii_keyword_does_not_match_pinyin_noise():
    rows = [
        {"code": "018523", "name": "华泰紫金恒生互联网科技业指数型发起基金(QDII)A", "fund_type": "指数型-海外股票", "pinyin": "HUATAIZIJINHENGSHENGHULIANWANGKEJIYEZHISHUXINGFAQIJIJINQDIIA"},
    ]

    selected = select_growth_funds(rows, min_theme_score=3, limit=10)

    assert selected[0].matched_keywords == ("科技", "互联网", "QDII")


def test_expand_candidate_universe_stages_all_market_growth_candidates(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    def fake_fetch(timeout_seconds):
        return [
            {"code": "999001", "name": "测试半导体芯片混合A", "fund_type": "混合型-偏股", "pinyin": "CSBDT"},
            {"code": "999002", "name": "测试天天货币A", "fund_type": "货币型-普通货币", "pinyin": "CSHB"},
            {"code": "999003", "name": "测试纳斯达克人工智能QDIIA", "fund_type": "QDII", "pinyin": "CSNSDK"},
        ]

    monkeypatch.setattr("app.core.candidate_universe_expander.fetch_eastmoney_fund_list", fake_fetch)

    result = expand_candidate_universe(settings, live_fetch=True, max_additions=5)

    assert result["status"] == "pass"
    assert result["scanned_count"] == 3
    assert result["added_count"] == 2
    expanded = Path(str(result["expanded_candidates_path"])).read_text(encoding="utf-8")
    assert "999001" in expanded
    assert "999003" in expanded
    assert "999002" not in expanded
    assert (settings.manual_dir / "candidates.csv").read_text(encoding="utf-8").count("999001") == 0


def test_expand_candidate_universe_backfills_runtime_nav_without_overwriting_manual(monkeypatch, tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    original_price_history = (settings.manual_dir / "price_history.csv").read_text(encoding="utf-8")

    def fake_fetch(timeout_seconds):
        return [
            {"code": "999001", "name": "测试半导体芯片混合A", "fund_type": "混合型-偏股", "pinyin": "CSBDT"},
        ]

    def fake_nav(settings_arg, item, *, generated_at):
        return (
            [
                {
                    "asset_code": item.code,
                    "date": "2024-01-01",
                    "close": "1.0",
                    "source_name": "fake",
                    "source_type": "public_aggregation",
                    "source_priority": "5",
                    "url_or_path": "fake",
                    "evidence_level": "Medium",
                    "as_of": generated_at[:10],
                },
                {
                    "asset_code": item.code,
                    "date": "2026-02-01",
                    "close": "1.8",
                    "source_name": "fake",
                    "source_type": "public_aggregation",
                    "source_priority": "5",
                    "url_or_path": "fake",
                    "evidence_level": "Medium",
                    "as_of": generated_at[:10],
                },
            ],
            "fake",
        )

    monkeypatch.setattr("app.core.candidate_universe_expander.fetch_eastmoney_fund_list", fake_fetch)
    monkeypatch.setattr("app.core.candidate_universe_expander._fetch_nav_history_rows", fake_nav)

    result = expand_candidate_universe(settings, live_fetch=True, max_additions=1, backfill_nav=True)

    price_path = Path(str(result["expanded_price_history_path"]))
    assert price_path.exists()
    assert "999001,2024-01-01,1.0" in price_path.read_text(encoding="utf-8")
    assert result["price_history_expansion"]["nav_backfilled_codes"] == ["999001"]
    assert (settings.manual_dir / "price_history.csv").read_text(encoding="utf-8") == original_price_history
