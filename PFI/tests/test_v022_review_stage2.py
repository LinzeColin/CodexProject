from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from pfi_v02.stage_v022_fx import (
    amount_display_label,
    effective_fx_date,
    ledger_amount_fields,
    missing_fx_snapshot_status,
    validate_snapshot_hash,
)


ROOT = Path(__file__).resolve().parents[1]
REVIEW_REPORT = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE2_REVIEW_20260628.md"

STAGE2_TASK_IDS = (
    "S2-P1-T1",
    "S2-P1-T2",
    "S2-P1-T3",
    "S2-P2-T1",
    "S2-P2-T2",
    "S2-P2-T3",
)

STOP_CONDITIONS = (
    "任一核心板块仍以 AUD 为主显示时停止",
    "原币丢失或汇率不显示时停止",
    "金额无法追溯汇率时停止",
    "03:00 错用当天汇率时停止",
    "每次运行触发网络抓取时停止",
    "汇率无快照或无法追溯时停止",
)


def test_stage2_review_report_covers_acceptance_fixes_and_stop_conditions() -> None:
    text = REVIEW_REPORT.read_text(encoding="utf-8")

    assert "v0.2.2 Stage 2 复审并解决" in text
    assert "本轮只复审解决 Stage 2" in text
    assert "不复审 Stage 3-13" in text
    assert "复审结论：通过" in text
    assert "上线阻塞项：0" in text
    assert "修复 1：补齐 `currency.base_currency` 的现金流影响面" in text
    assert "修复 2：账本金额字段增加中文标签映射" in text

    for task_id in STAGE2_TASK_IDS:
        assert task_id in text
    for stop_condition in STOP_CONDITIONS:
        assert stop_condition in text

    required_evidence_terms = (
        "PFI/config/pfi_parameters.yaml",
        "PFI/src/pfi_v02/stage_v022_fx.py",
        "PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json",
        "PFI/tests/test_v022_fx_effective_date.py",
        "PFI/tests/test_v022_review_stage2.py",
        "验证命令",
        "证据来源",
        "停止条件复核",
        "剩余风险",
    )
    for term in required_evidence_terms:
        assert term in text


def test_stage2_cny_base_currency_covers_cashflow_surface() -> None:
    catalog = json.loads((ROOT / "config" / "pfi_parameters.yaml").read_text(encoding="utf-8"))
    base_currency = catalog["parameters"]["currency"]["base_currency"]

    assert base_currency["value"] == "CNY"
    assert "首页总览" in base_currency["impact_surfaces"]
    assert "投资管理" in base_currency["impact_surfaces"]
    assert "消费管理" in base_currency["impact_surfaces"]
    assert "现金流" in base_currency["impact_surfaces"]
    assert "报告与洞察" in base_currency["impact_surfaces"]


def test_stage2_ledger_amount_fields_keep_machine_keys_and_chinese_labels() -> None:
    snapshot = {
        "snapshot_id": "fx_AUD_CNY_20260628",
        "display_pair": "AUD/CNY",
        "pair_base": "AUD",
        "rate": "4.8100",
    }
    fields = ledger_amount_fields(original_amount=500, original_currency="AUD", snapshot=snapshot)

    assert fields["original_amount"] == "500.00"
    assert fields["original_currency"] == "AUD"
    assert fields["amount_cny"] == "2405.00"
    assert fields["fx_snapshot_id"] == "fx_AUD_CNY_20260628"
    assert fields["field_labels_zh"] == {
        "original_amount": "原始金额",
        "original_currency": "原始币种",
        "amount_cny": "CNY金额",
        "fx_snapshot_id": "汇率快照ID",
    }
    assert amount_display_label(Decimal("500"), "AUD", snapshot) == "¥2,405.00 / 约 500.00 AUD / AUD/CNY=4.81"


def test_stage2_effective_date_snapshot_and_missing_status_are_traceable() -> None:
    sydney = ZoneInfo("Australia/Sydney")
    assert effective_fx_date(datetime(2026, 6, 28, 3, 0, tzinfo=sydney)) == date(2026, 6, 27)
    assert effective_fx_date(datetime(2026, 6, 28, 6, 0, tzinfo=sydney)) == date(2026, 6, 28)

    snapshot = json.loads((ROOT / "data" / "fx_snapshots" / "AUD_CNY" / "2026-06-28.json").read_text(encoding="utf-8"))
    assert snapshot["display_pair"] == "AUD/CNY"
    assert snapshot["base_currency"] == "CNY"
    assert snapshot["effective_time_local"] == "06:00"
    assert snapshot["ordinary_runtime_network_refresh"] is False
    assert "Frankfurter" in snapshot["source_provider"]
    assert validate_snapshot_hash(snapshot)

    status = missing_fx_snapshot_status(now=datetime(2026, 6, 29, 8, 0, tzinfo=sydney))
    assert status["status"] == "汇率数据待更新"
    assert status["ordinary_runtime_network_refresh"] is False
