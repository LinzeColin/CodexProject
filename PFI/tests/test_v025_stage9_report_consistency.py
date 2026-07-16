from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re

from pfi_os.application.analysis.report_analysis import (
    ACCEPTANCE_ID,
    FINANCIAL_REPORT_TYPES,
    PHASE_ID,
    TASK_IDS,
    build_phase92_analysis_pack,
    validate_phase92_analysis_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE91_MANIFEST = (
    PFI_ROOT / "reports/pfi_v025/stage_9/phase_9_1/report_manifest.json"
)


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _contains_financial_value(payload: object) -> bool:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return bool(
        re.search(r"\bCNY\s+-?[0-9]", serialized)
        or re.search(r'"(?:value|amount|financial_value)"\s*:', serialized)
        or re.search(r'"[a-z0-9_]+_cny"\s*:', serialized)
    )


def test_phase92_report_set_implements_only_current_calculable_scope() -> None:
    pack = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )
    gate = validate_phase92_analysis_pack(pack, pfi_root=PFI_ROOT)
    reports = {report["report_type"]: report for report in pack["report_set"]}
    phase91 = _json(PHASE91_MANIFEST)

    assert gate == {
        "schema": "PFIV025Stage9Phase92AnalysisValidationV1",
        "phase_id": PHASE_ID,
        "status": "pass",
        "errors": [],
        "report_count": 5,
        "formula_drilldown_count": 6,
        "sensitivity_preview_count": 4,
        "model_validation_card_count": 1,
        "source_review_count": 7,
        "cross_report_hashes_consistent": True,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }
    assert pack["phase_id"] == PHASE_ID
    assert pack["task_ids"] == list(TASK_IDS)
    assert pack["acceptance_id"] == ACCEPTANCE_ID
    assert pack["analysis_implementation_status"] == "ready"
    assert pack["base_report_manifest_hash"] == phase91["manifest_hash"]
    assert set(reports) == set(FINANCIAL_REPORT_TYPES)
    assert {key: value["status"] for key, value in reports.items()} == {
        "net_worth": "blocked",
        "cash": "blocked",
        "investment": "blocked",
        "consumption": "partial",
        "cashflow": "partial",
    }
    assert reports["net_worth"]["conclusions"] == []
    assert reports["cash"]["conclusions"] == []
    assert reports["investment"]["conclusions"] == []
    assert reports["net_worth"]["calculable_components"] == []
    assert reports["cash"]["calculable_components"] == []
    assert reports["investment"]["calculable_components"] == []
    assert reports["consumption"]["calculable_components"]
    assert reports["cashflow"]["calculable_components"]
    assert all(report["hashes"] == pack["hashes"] for report in reports.values())
    assert all(report["financial_values_emitted"] == 0 for report in reports.values())
    assert all(report["contains_private_values"] is False for report in reports.values())
    assert not _contains_financial_value(pack)


def test_dual_consumption_and_cashflow_reports_are_truthful_and_explain_scope() -> None:
    pack = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )
    reports = {report["report_type"]: report for report in pack["report_set"]}
    consumption = reports["consumption"]
    cashflow = reports["cashflow"]

    assert consumption["formula_ids"] == ["FORM-PFI-015", "FORM-PFI-020"]
    assert consumption["component_metric_ids"] == [
        "total_consumption_outflow_cny",
        "living_consumption_cny",
        "investment_funding_outflow_cny",
        "investment_allocation_amount_cny",
    ]
    assert "不等于净资产损失" in consumption["scope_explanation_zh"]
    assert consumption["calculable_components"][0] == {
        "component_id": "real_source_partition",
        "status": "partial",
        "input_record_count": 8815,
        "published_record_count": 6879,
        "review_queue_record_count": 1936,
        "silent_drop_count": 0,
        "coverage_start": "2022-06-06",
        "coverage_end": "2026-06-03",
    }
    windows = cashflow["calculable_components"][0]["windows"]
    assert [row["window_days"] for row in windows] == [7, 21, 30, 60, 90, 180, 360]
    assert [row["record_count"] for row in windows] == sorted(
        row["record_count"] for row in windows
    )
    assert all(re.fullmatch(r"sha256:[0-9a-f]{64}", row["financial_fingerprint"]) for row in windows)
    assert consumption["conclusions"][0]["scope"] == "source_coverage_only"
    assert cashflow["conclusions"][0]["scope"] == "source_coverage_only"


def test_every_gap_and_anomaly_has_an_actionable_source_review_route() -> None:
    pack = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )
    reviews = {row["review_id"]: row for row in pack["source_review_index"]}

    assert len(reviews) == 7
    assert set(reviews) == {
        "REVIEW-SRC-ACCOUNT-BALANCES",
        "REVIEW-SRC-LIABILITIES",
        "REVIEW-SRC-HOLDINGS",
        "REVIEW-SRC-MARKET-PRICES",
        "REVIEW-SRC-FX-SNAPSHOT",
        "REVIEW-SRC-TRANSACTIONS-ALIPAY",
        "REVIEW-ECONOMIC-EVENT-ADAPTER",
    }
    assert all(str(row["review_route"]).startswith("/") for row in reviews.values())
    assert all(row["action_label_zh"] for row in reviews.values())
    assert all("path_alias" not in row for row in reviews.values())
    for report in pack["report_set"]:
        assert report["review_entry_ids"]
        assert set(report["review_entry_ids"]) <= set(reviews)
        assert report["anomaly_ids"] == report["review_entry_ids"]


def test_phase92_validator_rejects_whole_pack_hash_false_conclusion_and_value_tamper() -> None:
    original = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )

    hash_drift = deepcopy(original)
    forged = "sha256:" + "0" * 64
    hash_drift["hashes"]["parameter_hash"] = forged
    for report in hash_drift["report_set"]:
        report["hashes"]["parameter_hash"] = forged
    assert validate_phase92_analysis_pack(hash_drift, pfi_root=PFI_ROOT)[
        "status"
    ] == "fail"

    false_conclusion = deepcopy(original)
    false_conclusion["report_set"][0]["conclusions"].append(
        {
            "scope": "financial",
            "statement_zh": "缺少依赖时仍输出确定性结论。",
            "evidence_refs": ["invalid"],
        }
    )
    assert validate_phase92_analysis_pack(false_conclusion, pfi_root=PFI_ROOT)[
        "status"
    ] == "fail"

    financial_value = deepcopy(original)
    financial_value["report_set"][3]["calculable_components"][0][
        "amount"
    ] = "1.00"
    assert validate_phase92_analysis_pack(financial_value, pfi_root=PFI_ROOT)[
        "status"
    ] == "fail"

    unsafe_route = deepcopy(original)
    unsafe_route["source_review_index"][0]["review_route"] = ""
    assert validate_phase92_analysis_pack(unsafe_route, pfi_root=PFI_ROOT)[
        "status"
    ] == "fail"
