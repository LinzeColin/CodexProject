from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re

from pfi_os.application.analysis.report_analysis import (
    FORMULA_IDS,
    PHASE_ID,
    build_phase92_analysis_pack,
    build_phase92_contract,
    validate_phase92_analysis_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_phase92_contract_is_t3_and_stops_before_phase93() -> None:
    contract = build_phase92_contract()

    assert contract["phase_id"] == PHASE_ID
    assert contract["risk_tier"] == "T3_FINANCIAL_MODEL_VALIDATION_UI"
    assert contract["current_phase_only"] is True
    assert contract["phase_9_1_required"] is True
    assert contract["phase_9_2_analysis_implementation"] is True
    assert contract["phase_9_3_started"] is False
    assert contract["stage_9_whole_stage_review_done"] is False
    assert contract["automatic_trading_allowed"] is False
    assert contract["financial_fixture_acceptance_allowed"] is False
    assert contract["finder_used"] is False
    assert contract["external_network_performed"] is False
    assert contract["push_performed"] is False
    assert contract["app_install_performed"] is False


def test_formula_drilldowns_bind_registry_validation_and_report_routes() -> None:
    pack = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )
    registry = _json(PFI_ROOT / "config/formulas/v025_formula_registry.json")
    registry_by_id = {row["formula_id"]: row for row in registry["formulas"]}
    drilldowns = {row["formula_id"]: row for row in pack["formula_drilldowns"]}

    assert set(drilldowns) == set(FORMULA_IDS)
    assert {key: value["validation_status"] for key, value in drilldowns.items()} == {
        "FORM-PFI-015": "validated_real_snapshot",
        "FORM-PFI-016": "blocked_missing_required_sources",
        "FORM-PFI-017": "blocked_missing_required_sources",
        "FORM-PFI-018": "blocked_insufficient_chain",
        "FORM-PFI-019": "validated_real_snapshot",
        "FORM-PFI-020": "validated_structure_only",
    }
    for formula_id, row in drilldowns.items():
        source = registry_by_id[formula_id]
        assert row["formula_hash"] == source["formula_hash"]
        assert row["formula_version"] == source["version"]
        assert row["label_zh"] == source["label_zh"]
        assert row["parameters"] == source["parameters"]
        assert row["report_types"]
        assert row["review_route"].startswith("/reports/metric-drilldown")
        assert row["limitation"]


def test_sensitivity_preview_shows_real_count_impact_and_blocks_unprovable_results() -> None:
    pack = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )
    previews = {row["sensitivity_id"]: row for row in pack["sensitivity_previews"]}

    assert set(previews) == {
        "SENS-CASHFLOW-WINDOW",
        "SENS-CLASSIFICATION-THRESHOLD",
        "SENS-XIRR-POLICY",
        "SENS-MONEY-QUANTUM",
    }
    cashflow = previews["SENS-CASHFLOW-WINDOW"]
    assert cashflow["status"] == "partial_ready_nonfinancial_impact"
    assert cashflow["parameter_ids"] == ["PARAM-PFI-086"]
    assert len(cashflow["observations"]) == 7
    assert cashflow["impact_visible"] is True
    assert "金额影响不在公开证据中输出" in cashflow["limitation_zh"]
    assert previews["SENS-CLASSIFICATION-THRESHOLD"]["status"] == "blocked_missing_scores"
    assert previews["SENS-XIRR-POLICY"]["status"] == "blocked_insufficient_chain"
    assert previews["SENS-MONEY-QUANTUM"]["status"] == "blocked_missing_required_sources"
    assert all(row["financial_values_emitted"] == 0 for row in previews.values())


def test_model_card_preserves_limitations_counter_evidence_and_oos_block() -> None:
    pack = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )
    card = pack["model_validation_cards"][0]

    assert card["model_id"] == "MOD-PFI-010"
    assert card["status"] == "partial_validated_with_blocked_components"
    assert card["invariant_status"] == "partial_pass_with_blocked_components"
    assert card["metamorphic_status"] == "pass"
    assert card["historical_out_of_sample_validation"] == {
        "status": "blocked_insufficient_ground_truth",
        "reason": "No complete target, labels and pre-specified split are available for a defensible historical or out-of-sample claim.",
    }
    assert len(card["formula_validation"]) == 6
    assert card["limitations"]
    assert card["counter_evidence"]
    assert card["formal_ui_contract_embedded"] is True
    assert card["automatic_trading_allowed"] is False
    assert card["financial_values_emitted"] == 0
    assert card["contains_private_values"] is False


def test_ui_contract_exposes_reports_formula_sensitivity_models_and_review_actions() -> None:
    pack = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )
    ui = pack["ui_contract"]
    serialized = json.dumps(ui, ensure_ascii=False, sort_keys=True)

    assert ui["schema"] == "PFIV025Stage9Phase92UIContractV1"
    assert ui["report_count"] == 5
    assert len(ui["report_cards"]) == 5
    assert len(ui["formula_cards"]) == 6
    assert len(ui["sensitivity_cards"]) == 4
    assert len(ui["model_cards"]) == 1
    assert len(ui["review_cards"]) == 7
    assert ui["phase_9_3_started"] is False
    assert ui["automatic_trading_allowed"] is False
    assert "模型验证" in serialized
    assert "敏感性" in serialized
    assert "FORM-PFI-015" in serialized
    assert "FORM-PFI-016" in serialized
    assert not re.search(r"\bCNY\s+-?[0-9]", serialized)


def test_validator_rejects_forged_sensitivity_and_formula_validation_status() -> None:
    original = build_phase92_analysis_pack(
        PFI_ROOT, observed_at="2026-07-15T16:00:00+10:00"
    )

    forged_sensitivity = deepcopy(original)
    forged_sensitivity["sensitivity_previews"][1]["status"] = "pass"
    assert validate_phase92_analysis_pack(
        forged_sensitivity, pfi_root=PFI_ROOT
    )["status"] == "fail"

    forged_formula = deepcopy(original)
    forged_formula["formula_drilldowns"][1]["validation_status"] = (
        "validated_real_snapshot"
    )
    assert validate_phase92_analysis_pack(
        forged_formula, pfi_root=PFI_ROOT
    )["status"] == "fail"
