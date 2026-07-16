from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import zipfile

from jsonschema import Draft202012Validator, FormatChecker

from pfi_os.application.metrics.model_validation import build_stage5_private_surface_payload
from pfi_os.application.metrics.stage5_whole_review import (
    ACCEPTANCE_ID,
    PHASE_COMMITS,
    REVIEW_BASE,
    build_stage5_whole_review_contract,
    evaluate_stage5_phase_evidence,
)
from pfi_os.application.read_model_status import build_v024_read_model_status


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_5/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
COMPONENT_IDS = (
    "total_consumption_outflow_cny",
    "living_consumption_cny",
    "investment_funding_outflow_cny",
    "investment_allocation_amount_cny",
)


def _json(name: str) -> dict[str, object]:
    value = json.loads((REVIEW_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_contract_is_exactly_stage5_whole_review() -> None:
    contract = build_stage5_whole_review_contract()
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-STAGE5-WHOLE-REVIEW"
    assert contract["review_base"] == REVIEW_BASE
    assert contract["phase_commits"] == PHASE_COMMITS
    assert contract["task_ids"] == [f"S5-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)]
    assert contract["stage_6_started"] is False
    assert contract["finder_used"] is False
    assert contract["scope_exception"]["status"] == "accepted_for_required_acceptance_remediation"


def test_phase_evidence_is_commit_bound() -> None:
    result = evaluate_stage5_phase_evidence(REPO_ROOT)
    assert result["status"] == "pass"
    assert result["phase_commits"] == PHASE_COMMITS
    assert result["task_count"] == 12
    assert result["linear_commit_chain"] is True
    assert result["all_phase_evidence_present_in_bound_commits"] is True


def test_private_real_snapshot_payload_reconciles_without_fixture() -> None:
    payload = build_stage5_private_surface_payload(
        REPO_ROOT,
        observed_at="2026-07-15T02:00:00+10:00",
        git_ref=REVIEW_BASE,
    )
    components = {item["metric_id"]: item for item in payload["components"]}
    assert tuple(components) == COMPONENT_IDS
    assert all(item["status"] == "ready" for item in components.values())
    assert all(item["currency"] == "CNY" for item in components.values())
    values = {key: Decimal(str(item["value"])) for key, item in components.items()}
    assert values["total_consumption_outflow_cny"] == (
        values["living_consumption_cny"]
        + values["investment_funding_outflow_cny"]
        + values["investment_allocation_amount_cny"]
    )
    assert components["investment_funding_outflow_cny"]["observed_zero_in_published_scope"] is True
    assert payload["source"]["input_record_count"] == 8815
    assert payload["source"]["published_record_count"] == 6879
    assert payload["source"]["review_queue_record_count"] == 1936
    assert payload["source"]["silent_drop_count"] == 0
    assert payload["actual_ui_render_binding_completed"] is True
    assert payload["actual_report_render_binding_completed"] is True
    assert payload["financial_fixture_fallback_used"] is False
    assert len(set(payload["surface_payload_hashes"].values())) == 1


def test_runtime_read_model_exposes_stage5_payload_to_formal_shell() -> None:
    status = build_v024_read_model_status(PFI_ROOT)
    payload = status["stage5_financial_model"]
    assert payload["schema"] == "PFIV025Stage5PrivateFinancialSurfaceV1"
    assert payload["surface_ids"] == ["homepage", "consumption_page", "report"]
    assert payload["actual_ui_render_binding_completed"] is True
    assert payload["actual_report_render_binding_completed"] is True
    labels = [item["label_zh"] for item in payload["components"]]
    assert labels == ["消费总流出金额（用户定义活动口径）", "生活消费金额", "投资资金流出金额", "投资域内配置金额"]
    shell = (PFI_ROOT / "web/app/shell.js").read_text(encoding="utf-8")
    for metric_id in COMPONENT_IDS:
        assert metric_id in shell
    assert "applyV025Stage5FinancialModelToSurfaces" in shell


def test_initial_findings_are_fixed_and_rereview_is_clean() -> None:
    audit = _json("review_audit.json")
    assert audit["initial_review"]["counts"] == {"critical": 1, "important": 4, "minor": 1}
    assert all(item["status"] == "fixed" for item in audit["initial_review"]["findings"])
    assert audit["post_remediation_review"]["counts"] == {"critical": 0, "important": 0, "minor": 0}


def test_final_index_accepts_stage5_with_explicit_blocked_models() -> None:
    index = _json("final_evidence_index.json")
    assert index["status"] == "accepted_for_transition"
    assert index["task_disposition"] == {f"S5-P{phase}-T{task}": "pass" for phase in range(1, 4) for task in range(1, 5)}
    assert len(index["acceptance_criteria"]) == 7
    assert all(item["status"] == "pass" for item in index["acceptance_criteria"])
    assert len(index["stop_conditions"]) == 4
    assert all(item["status"] == "safety_stop_active" for item in index["stop_conditions"])
    assert index["pass_gate_result"] == "pass_with_explicit_blocked_models"
    assert index["actual_ui_render_binding_completed"] is True
    assert index["actual_report_render_binding_completed"] is True
    assert index["stage_6_entry_authorized"] is True
    assert index["stage_6_status"] == "not_started"


def test_human_acceptance_schema_and_index_binding() -> None:
    acceptance = _json("human_acceptance.json")
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(acceptance)
    assert acceptance["git_commit"] == REVIEW_BASE
    assert acceptance["evidence_index_hash"] == "sha256:" + _sha256(REVIEW_DIR / "final_evidence_index.json")
    assert acceptance["user_confirmation_reference"]
    assert any("FORM-PFI-016" in item for item in acceptance["known_defects"])


def test_browser_evidence_proves_actual_three_surface_binding_without_leak() -> None:
    browser = _json("browser_validation.json")
    a11y = _json("accessibility_tree.json")
    assert browser["status"] == "pass"
    assert browser["actual_formal_shell"] is True
    assert browser["finder_used"] is False
    assert browser["network_performed"] is True
    assert browser["network_scope"] == "ephemeral_local_loopback_only"
    assert browser["external_network_performed"] is False
    assert browser["private_numeric_value_count_verified_before_redaction"] == 4
    assert browser["redacted_visible_financial_value_count"] == 4
    assert browser["surface_ids"] == ["homepage", "consumption_page", "report"]
    assert all(count == 4 for count in browser["visible_component_label_counts"].values())
    assert all(
        state == {"release_identity_state": "ready", "conflict_hidden": True, "app_shell_hidden": False}
        for state in browser["release_identity_ready_surfaces"].values()
    )
    assert browser["actual_ui_render_binding_completed"] is True
    assert browser["actual_report_render_binding_completed"] is True
    assert a11y["status"] == "pass"
    assert a11y["private_financial_values_present"] is False
    for screenshot_name in (
        "homepage_redacted.png",
        "consumption_page_redacted.png",
        "report_redacted.png",
    ):
        assert (REVIEW_DIR / screenshot_name).stat().st_size > 0
    trace = REVIEW_DIR / "browser_trace.zip"
    assert trace.stat().st_size > 0
    with zipfile.ZipFile(trace) as archive:
        assert "sanitized_dom.html" in archive.namelist()
        sanitized = archive.read("sanitized_dom.html").decode("utf-8")
    assert not re.search(r"CNY\s+[0-9]", sanitized)


def test_evidence_pack_is_schema_valid_and_safe() -> None:
    evidence = _json("evidence.json")
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
    Draft202012Validator(schema).validate(evidence)
    assert evidence["contains_private_values"] is False
    assert evidence["real_financial_data_read"] is True
    assert evidence["real_financial_data_mutated"] is False
    assert evidence["database_changed"] is False
    assert evidence["finder_used"] is False
    assert evidence["stage_5_status"] == "accepted_for_transition"
    assert evidence["stage_6_work_performed"] is False
