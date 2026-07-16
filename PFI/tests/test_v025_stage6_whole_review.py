from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from jsonschema import Draft202012Validator, FormatChecker

from pfi_v02.stage_v025_stage6_whole_review import (
    ACCEPTANCE_ID,
    PHASE_COMMITS,
    REVIEW_BASE,
    build_stage6_whole_review_contract,
    evaluate_stage6_phase_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_6/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"


def _json(name: str) -> dict[str, object]:
    payload = json.loads((REVIEW_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _taskpack_schema(name: str) -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        return json.loads(archive.read(f"PFI_v0.2.5_TaskPack/schemas/{name}"))


def _routes() -> dict[str, object]:
    result = subprocess.run(
        ["node", "-e", "console.log(JSON.stringify(require(process.argv[1])))", str(PFI_ROOT / "web/app/routes.js")],
        cwd=REPO_ROOT, check=True, text=True, capture_output=True,
    )
    return json.loads(result.stdout)


def test_contract_is_exactly_stage6_whole_review() -> None:
    contract = build_stage6_whole_review_contract()
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-STAGE6-WHOLE-REVIEW"
    assert contract["review_base"] == REVIEW_BASE
    assert contract["phase_commits"] == PHASE_COMMITS
    assert contract["task_ids"] == [f"S6-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)]
    assert contract["primary_entry_count"] == 10
    assert contract["secondary_page_count"] == 45
    assert contract["canonical_route_count"] == 55
    assert contract["stage_7_started"] is False
    assert contract["finder_used"] is False


def test_phase_evidence_is_immutably_commit_bound() -> None:
    result = evaluate_stage6_phase_evidence(REPO_ROOT)
    assert result["status"] == "pass"
    assert result["phase_commits"] == PHASE_COMMITS
    assert result["task_count"] == 12
    assert result["linear_commit_chain"] is True
    assert result["all_phase_evidence_present_in_bound_commits"] is True
    assert result["all_phase_evidence_candidate_pass"] is True


def test_current_route_registry_is_exact_and_has_one_strategy_lab() -> None:
    routes = _routes()
    assert len(routes["officialPrimaryEntries"]) == 10
    assert len(routes["phase62RouteRegistry"]["canonicalSecondaryRoutes"]) == 45
    assert len(routes["phase73RouteRegistry"]["canonicalSecondaryRoutes"]) == 3
    assert len(routes["canonicalSecondaryRoutes"]) == 48
    assert len(routes["aliasMatrix"]) == 7
    assert routes["primaryEntryCount"] == 10
    assert routes["legacyAliasPrimaryEntryAllowed"] is False
    assert routes["canonicalStrategyLabRoute"] == "/market-research/strategy-lab"
    assert [page["routeAlias"] for page in routes["pageContracts"]["pages"] if page["pageLabel"] == "策略实验室"] == [
        "/market-research/strategy-lab"
    ]


def test_all_phase_evidence_packs_now_validate_taskpack_schema() -> None:
    validator = Draft202012Validator(_taskpack_schema("evidence_pack.schema.json"))
    for phase in ("6_1", "6_2", "6_3"):
        payload = json.loads((PFI_ROOT / f"reports/pfi_v025/stage_6/phase_{phase}/evidence.json").read_text(encoding="utf-8"))
        validator.validate(payload)


def test_initial_findings_fixed_and_rereview_clean() -> None:
    audit = _json("review_audit.json")
    assert audit["initial_review"]["counts"] == {"critical": 0, "important": 4, "minor": 1}
    assert all(item["status"] == "fixed" for item in audit["initial_review"]["findings"])
    assert audit["post_remediation_review"]["counts"] == {"critical": 0, "important": 0, "minor": 0}


def test_current_head_browser_review_covers_all_stage6_gates() -> None:
    browser = _json("browser_validation.json")
    a11y = _json("accessibility_tree.json")
    assert browser["status"] == "pass"
    assert browser["current_head_combined_review"] is True
    assert browser["primary_routes_checked"] == 10
    assert browser["representative_secondary_routes_checked"] == 10
    assert browser["alias_routes_checked"] == 7
    assert browser["nojs_primary_route_count"] == 10
    assert browser["nojs_secondary_route_count"] == 45
    assert all(browser["checks"].values())
    assert browser["external_network_performed"] is False
    assert browser["finder_used"] is False
    assert a11y["status"] == "pass"
    assert a11y["primary_navigation_count"] == 10
    assert a11y["primary_navigation_unique_count"] == 10
    for name in ("desktop_navigation.png", "mobile_navigation.png", "nojs_navigation.png", "invalid_route.png", "browser_trace.zip"):
        assert (REVIEW_DIR / name).stat().st_size > 0


def test_legacy_diagnostic_failures_are_explicitly_disposed() -> None:
    disposition = _json("legacy_test_disposition.json")
    assert disposition["status"] == "pass"
    assert disposition["passed"] == 17
    assert disposition["expected_superseded_failures"] == 4
    assert disposition["unclassified_failures"] == 0
    assert len(disposition["failures"]) == 4


def test_final_index_accepts_stage6_and_stops_before_stage7() -> None:
    index = _json("final_evidence_index.json")
    assert index["status"] == "accepted_for_transition"
    assert index["task_disposition"] == {f"S6-P{phase}-T{task}": "pass" for phase in range(1, 4) for task in range(1, 5)}
    assert len(index["acceptance_criteria"]) == 6
    assert all(item["status"] == "pass" for item in index["acceptance_criteria"])
    assert len(index["stop_conditions"]) == 4
    assert all(item["status"] == "safety_stop_active" for item in index["stop_conditions"])
    assert index["pass_gate_result"] == "pass"
    assert index["stage_7_entry_authorized"] is True
    assert index["stage_7_status"] == "not_started"


def test_human_acceptance_schema_and_final_index_binding() -> None:
    acceptance = _json("human_acceptance.json")
    Draft202012Validator(
        _taskpack_schema("human_acceptance.schema.json"), format_checker=FormatChecker()
    ).validate(acceptance)
    assert acceptance["git_commit"] == REVIEW_BASE
    assert acceptance["evidence_index_hash"] == "sha256:" + _sha256(REVIEW_DIR / "final_evidence_index.json")
    assert acceptance["user_confirmation_reference"] == "thread_pre_final_acceptance_blanket_authorization_and_active_goal_continuation"


def test_review_evidence_pack_is_schema_valid_and_safe() -> None:
    evidence = _json("evidence.json")
    Draft202012Validator(_taskpack_schema("evidence_pack.schema.json")).validate(evidence)
    assert evidence["contains_private_values"] is False
    assert evidence["real_financial_data_read"] is False
    assert evidence["real_financial_data_mutated"] is False
    assert evidence["database_changed"] is False
    assert evidence["finder_used"] is False
    assert evidence["stage_6_status"] == "accepted_for_transition"
    assert evidence["stage_7_work_performed"] is False
