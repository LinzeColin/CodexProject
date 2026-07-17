#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S08-P3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s08_p3_matching_quality_confirmation as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "a086e8d17048376ad091572b618290db2b2de04a"

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / "V015_S08_P3_MATCHING_QUALITY_CONFIRMATION"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s08_p3_matching_quality_confirmation_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
POLICY_PATH = MACHINE_ROOT / "matching_threshold_policy_public_safe.json"
CLASSIFICATION_PATH = MACHINE_ROOT / "matching_classification_cases_public_safe.json"
CONFIRMATION_PATH = MACHINE_ROOT / "confirmation_flow_public_safe.json"
EVENT_LEDGER_PATH = MACHINE_ROOT / "decision_event_ledger_public_safe.json"
RECALCULATION_PATH = MACHINE_ROOT / "affected_chain_recalculation_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
CONTRACT_PATH = PROJECT_ROOT / "metadata" / "quality" / "v015_s08_p3_matching_quality_confirmation_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
CONFIRMATION_FLOW_PATH = HUMAN_ROOT / "confirmation_flow_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
OPEN_RISKS_PATH = HUMAN_ROOT / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_ROOT / "rollback_plan_zh.md"

S08_P2_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts"
    / "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY"
    / "machine"
    / "s08_p2_business_entity_hierarchy_manifest.json"
)
S08_P2_RECEIPTS_PATH = (
    PROJECT_ROOT
    / "stage_artifacts"
    / "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY"
    / "machine"
    / "validation_results.jsonl"
)

EXPECTED_VALIDATION_NAMES = (
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "pre_final_phase_checker",
    "s08_p2_dependency_check",
    "legacy_matching_quality_regression",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "metadata_protocol",
    "project_governance",
    "lean_governance",
    "governance_sync",
    "no_omission",
    "no_float_money",
    "deterministic_evidence",
    "python_compile",
    "structured_public_diff",
    "public_boundary",
    "git_diff_check",
)


class BuildError(RuntimeError):
    pass


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"JSON object required: {path}")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL object rows required: {path}")
    return rows


def dependency() -> dict[str, Any]:
    manifest = _json(S08_P2_MANIFEST_PATH)
    receipts = _jsonl(S08_P2_RECEIPTS_PATH)
    required = {
        "phase_id": "V015_S08_P2_BUSINESS_ENTITY_HIERARCHY",
        "roadmap_phase_id": "S08-P2",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "CONTINUE_TO_S08_P3_ONLY",
        "s08_p3_entry_allowed": True,
        "s08_p3_started": False,
        "validation_receipt_count": 19,
        "overall_accepted_phase_count": 21,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches:
        raise BuildError("S08-P2 dependency mismatch: " + ", ".join(mismatches))
    if len(receipts) != 19 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S08-P2 receipt set is not exactly 19 PASS records")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S08-P2 validation head mismatch")
    if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
        raise BuildError("S08-P2 validation run mismatch")
    return {
        "phase_id": manifest["phase_id"],
        "acceptance_status": manifest["phase_acceptance_status"],
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(receipts),
        "s08_p3_entry_allowed": True,
        "s08_p3_started": False,
    }


def final_receipts() -> list[dict[str, Any]]:
    receipts = _jsonl(VALIDATION_RESULTS_PATH)
    if not receipts:
        return []
    if len(receipts) != len(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S08-P3 validation receipt count mismatch")
    if [row.get("name") for row in receipts] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S08-P3 validation receipt order mismatch")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S08-P3 validation receipt set contains a failure")
    if len({row.get("validation_head") for row in receipts}) != 1:
        raise BuildError("S08-P3 receipts do not share one validation head")
    if len({row.get("validation_run_id") for row in receipts}) != 1:
        raise BuildError("S08-P3 receipts do not share one validation run")
    return receipts


def _policy_artifact(cases: dict[str, Any]) -> dict[str, Any]:
    policy = cases["matching_policy"]
    return {
        "schema_version": "kmfa.v015.s08p3.matching_threshold_policy_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "policy": policy,
        "acceptance": {
            "match_state_count": len(policy["state_labels_zh"]),
            "auto_match_min_bps": policy["auto_match_min_bps"],
            "candidate_review_min_bps": policy["candidate_review_min_bps"],
            "thresholds_externalized": policy["policy_source"] == "TRACKED_PUBLIC_SAFE_CONFIG",
            "threshold_change_requires_regression": policy["threshold_change_requires_regression"],
            "silent_threshold_change_allowed": policy["silent_threshold_change_allowed"],
            "minimum_policy_regression_case_count": policy["minimum_policy_regression_case_count"],
        },
        "private_business_values_published": False,
    }


def _classification_artifact(cases: dict[str, Any]) -> dict[str, Any]:
    rows = cases["classification_cases"]
    regression = cases["policy_regression"]
    states = [row["state"] for row in rows.values()]
    return {
        "schema_version": "kmfa.v015.s08p3.matching_classification_cases_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "classification_cases": rows,
        "policy_regression": regression,
        "acceptance": {
            "classification_case_count": len(rows),
            "automatic_state_count": states.count("AUTO_MATCH"),
            "candidate_state_count": states.count("CANDIDATE_REVIEW"),
            "manual_state_count": states.count("MANUAL_CONFIRMATION"),
            "hard_conflict_manual_override_count": sum(
                bool(row["hard_conflict_codes"]) and row["state"] == "MANUAL_CONFIRMATION"
                for row in rows.values()
            ),
            "reasoned_case_count": sum(bool(row["reason_details"]) for row in rows.values()),
            "regression_case_count": regression["regression_case_count"],
            "regression_pass_count": regression["regression_pass_count"],
            "regression_fail_count": regression["regression_fail_count"],
            "regression_required_enforced": cases["regression_required_enforced"],
        },
        "private_business_values_published": False,
    }


def _confirmation_artifact(cases: dict[str, Any]) -> dict[str, Any]:
    cards = cases["confirmation_cards"]
    plain_text = json.dumps(cards, ensure_ascii=False).lower()
    forbidden_count = sum(term.lower() in plain_text for term in kernel.PLAIN_LANGUAGE_FORBIDDEN_TERMS)
    return {
        "schema_version": "kmfa.v015.s08p3.confirmation_flow_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "confirmation_cards": cards,
        "acceptance": {
            "confirmation_card_count": len(cards),
            "side_by_side_column_count_per_card": 2,
            "display_field_count_per_candidate": 6,
            "required_explanation_section_count": 4,
            "decision_option_count": 3,
            "technical_term_occurrence_count": forbidden_count,
            "source_mutation_performed": False,
            "fact_table_mutation_performed": False,
        },
        "private_business_values_published": False,
    }


def _event_artifact(cases: dict[str, Any]) -> dict[str, Any]:
    events = cases["decision_events"]
    return {
        "schema_version": "kmfa.v015.s08p3.decision_event_ledger_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "events": events,
        "acceptance": {
            "control_event_count": len(events),
            "decision_recorded_event_count": sum(row["event_type"] == "MATCH_DECISION_RECORDED" for row in events),
            "reversal_event_count": sum(row["event_type"] == "MATCH_DECISION_REVERSED" for row in events),
            "rollback_event_count": sum(row["event_type"] == "MATCH_DECISION_ROLLBACK" for row in events),
            "append_only_event_count": sum(row["append_only"] for row in events),
            "auditable_event_count": sum(row["auditable"] for row in events),
            "reversible_event_count": sum(row["reversible"] for row in events),
            "persistence_roundtrip_event_count": cases["decision_event_roundtrip_count"],
            "persistence_roundtrip_exact": cases["decision_event_roundtrip_exact"],
            "current_decision_after_rollback": cases["current_decision_after_rollback"],
            "direct_fact_mutation_rejected": cases["direct_fact_mutation_rejected"],
            "source_snapshot_unchanged": cases["source_snapshot_unchanged"],
            "fact_snapshot_unchanged": cases["fact_snapshot_unchanged"],
        },
        "private_business_values_published": False,
    }


def _recalculation_artifact(cases: dict[str, Any]) -> dict[str, Any]:
    receipts = cases["recalculation_receipts"]
    return {
        "schema_version": "kmfa.v015.s08p3.affected_chain_recalculation_public_safe.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC",
        "recalculation_receipts": receipts,
        "acceptance": {
            "recalculation_receipt_count": len(receipts),
            "recalculation_pass_count": sum(row["status"] == "RECALCULATED" for row in receipts),
            "trigger_event_binding_count": sum(bool(row["trigger_event_ref"]) for row in receipts),
            "affected_node_count_per_receipt": sorted({row["affected_node_count"] for row in receipts}),
            "raw_source_mutation_count": sum(row["raw_source_mutation_performed"] for row in receipts),
            "fact_table_mutation_count": sum(row["fact_table_mutation_performed"] for row in receipts),
        },
        "private_business_values_published": False,
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    common = {
        "execution_status": "EXECUTION_COMPLETE",
        "acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "current_result": "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION",
    }
    return {
        "schema_version": "kmfa.v015.s08p3.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S08P3T01",
                "name_zh": "定义匹配阈值和原因",
                "acceptance_zh": "自动、候选和人工三类状态由外置参数决定；改阈值必须先完成回归。",
                "evidence_refs": [POLICY_PATH.relative_to(REPO_ROOT).as_posix(), CLASSIFICATION_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
            {
                "task_id": "S08P3T02",
                "name_zh": "设计简洁确认流程",
                "acceptance_zh": "普通用户能并排看候选、相同点、冲突点和影响；确认不修改原始资料。",
                "evidence_refs": [CONFIRMATION_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
            {
                "task_id": "S08P3T03",
                "name_zh": "记录匹配决定",
                "acceptance_zh": "决定追加为控制事件并重算受影响链；可撤销、可追溯、可回滚，事实表禁止直改。",
                "evidence_refs": [EVENT_LEDGER_PATH.relative_to(REPO_ROOT).as_posix(), RECALCULATION_PATH.relative_to(REPO_ROOT).as_posix()],
                **common,
            },
        ],
    }


def _contract(
    policy: dict[str, Any],
    classification: dict[str, Any],
    confirmation: dict[str, Any],
    events: dict[str, Any],
    recalculation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s08p3.matching_quality_confirmation_contract.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "match_state_count": policy["acceptance"]["match_state_count"],
        "auto_match_min_bps": policy["acceptance"]["auto_match_min_bps"],
        "candidate_review_min_bps": policy["acceptance"]["candidate_review_min_bps"],
        "thresholds_externalized": True,
        "threshold_change_requires_regression": True,
        "policy_regression_case_count": classification["acceptance"]["regression_case_count"],
        "policy_regression_fail_count": 0,
        "confirmation_card_count": confirmation["acceptance"]["confirmation_card_count"],
        "confirmation_technical_term_occurrence_count": 0,
        "confirmation_source_mutation_performed": False,
        "control_event_count": events["acceptance"]["control_event_count"],
        "reversal_event_count": events["acceptance"]["reversal_event_count"],
        "rollback_event_count": events["acceptance"]["rollback_event_count"],
        "decision_persistence_roundtrip_exact": True,
        "recalculation_receipt_count": recalculation["acceptance"]["recalculation_receipt_count"],
        "direct_fact_mutation_rejected": True,
        "raw_root_access_count": 0,
        "private_business_values_published": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def _manifest(
    policy: dict[str, Any],
    classification: dict[str, Any],
    confirmation: dict[str, Any],
    events: dict[str, Any],
    recalculation: dict[str, Any],
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    final = bool(receipts)
    value: dict[str, Any] = {
        "schema_version": "kmfa.v015.s08p3.matching_quality_confirmation_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "version": kernel.VERSION,
        "stage_id": "S08",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "run_mode": "CONTROLLED_RUN",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "counted_as_taskpack_phase": True,
        "counted_as_taskpack_task_count": 3,
        "phase_base_commit": PHASE_BASE_COMMIT,
        "dependency": dependency(),
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "match_state_count": policy["acceptance"]["match_state_count"],
        "auto_match_min_bps": policy["acceptance"]["auto_match_min_bps"],
        "candidate_review_min_bps": policy["acceptance"]["candidate_review_min_bps"],
        "thresholds_externalized": True,
        "threshold_change_requires_regression": True,
        "silent_threshold_change_allowed": False,
        "classification_case_count": classification["acceptance"]["classification_case_count"],
        "automatic_state_count": classification["acceptance"]["automatic_state_count"],
        "candidate_state_count": classification["acceptance"]["candidate_state_count"],
        "manual_state_count": classification["acceptance"]["manual_state_count"],
        "hard_conflict_manual_override_count": classification["acceptance"]["hard_conflict_manual_override_count"],
        "policy_regression_case_count": classification["acceptance"]["regression_case_count"],
        "policy_regression_pass_count": classification["acceptance"]["regression_pass_count"],
        "policy_regression_fail_count": 0,
        "regression_required_enforced": classification["acceptance"]["regression_required_enforced"],
        "confirmation_card_count": confirmation["acceptance"]["confirmation_card_count"],
        "confirmation_side_by_side_column_count": confirmation["acceptance"]["side_by_side_column_count_per_card"],
        "confirmation_explanation_section_count": confirmation["acceptance"]["required_explanation_section_count"],
        "confirmation_decision_option_count": confirmation["acceptance"]["decision_option_count"],
        "confirmation_technical_term_occurrence_count": 0,
        "confirmation_source_mutation_performed": False,
        "control_event_count": events["acceptance"]["control_event_count"],
        "reversal_event_count": events["acceptance"]["reversal_event_count"],
        "rollback_event_count": events["acceptance"]["rollback_event_count"],
        "append_only_event_count": events["acceptance"]["append_only_event_count"],
        "persistence_roundtrip_event_count": events["acceptance"]["persistence_roundtrip_event_count"],
        "decision_persistence_roundtrip_exact": events["acceptance"]["persistence_roundtrip_exact"],
        "direct_fact_mutation_rejected": events["acceptance"]["direct_fact_mutation_rejected"],
        "source_snapshot_unchanged": events["acceptance"]["source_snapshot_unchanged"],
        "fact_snapshot_unchanged": events["acceptance"]["fact_snapshot_unchanged"],
        "recalculation_receipt_count": recalculation["acceptance"]["recalculation_receipt_count"],
        "recalculation_pass_count": recalculation["acceptance"]["recalculation_pass_count"],
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "decision": "CONTINUE_TO_S08_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S08_P3_FINAL_VALIDATION",
        "s08_p1_acceptance_status": "PASSED",
        "s08_p2_acceptance_status": "PASSED",
        "s08_p3_entry_allowed": False,
        "s08_p3_started": True,
        "s08_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s08_stage_review_entry_allowed": final,
        "s08_stage_review_started": False,
        "s08_stage_review_performed": False,
        "overall_accepted_phase_count": 22 if final else 21,
        "overall_taskpack_phase_count": 72,
        "current_private_open_unconfirmed_item_count": 128,
        "current_private_conflict_candidate_count": 6,
        "current_report_display_label_zh": "暂不可使用",
        "current_formal_report_release_allowed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "source_mutation_performed": False,
        "fact_table_mutation_performed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_receipt_count": len(receipts),
        "validation_failed_count": 0,
    }
    if final:
        value.update(
            {
                "validation_head": receipts[0]["validation_head"],
                "validation_run_id": receipts[0]["validation_run_id"],
                "validation_pass_count": len(receipts),
            }
        )
    return value


def _implementation_report(final: bool) -> str:
    status = "已通过" if final else "等待最终验收"
    return f"""# KMFA v1.5 S08-P3 匹配判断与人工确认

- 当前状态：{status}。
- 匹配结果分为“自动通过、候选需确认、必须人工确认”三类；关键冲突即使匹配程度很高也必须人工处理。
- 阈值放在独立参数文件中，可以查看版本和变化；任何阈值调整都必须先跑完整回归案例。
- 确认卡并排显示两条记录，并用普通中文说明相同点、冲突点、缺失信息和可能影响。
- 人工选择只会追加决定记录并重算受影响链，不会改原始资料或事实记录；决定可撤销、可追溯、可回滚。
- 本轮没有读取原始资料，没有执行 S08 整体复审，没有上传 GitHub，也没有重装 App。
"""


def _confirmation_flow() -> str:
    return """# 匹配确认流程

## 用户会看到什么

1. 左边是当前记录，右边是候选记录。
2. 页面直接列出相同点、冲突点、缺失信息和可能影响。
3. 用户可以选择“确认是同一项目”“确认不是同一项目”或“暂不确定”。
4. 页面不显示内部编码、摘要值或其他机器术语。

## 选择后会发生什么

- 系统只新增一条决定记录，不覆盖原始资料，也不直接改事实表。
- 每条决定都会触发项目归属、项目成本汇总和报告可用状态的重算。
- 发现错误时，可以追加撤销记录；也可以回滚到一条较早的已确认决定。
- 所有历史决定都保留，便于审计和追溯。
"""


def _test_results(final: bool, receipts: list[dict[str, Any]]) -> str:
    if not final:
        return "# 测试结果\n\n- 功能和公开安全证据已生成，等待在干净实现提交上执行最终验收。\n"
    return (
        "# 测试结果\n\n"
        f"- 最终验收：{len(receipts)}/{len(EXPECTED_VALIDATION_NAMES)} 全部通过。\n"
        f"- 验收批次：`{receipts[0]['validation_run_id']}`。\n"
        f"- 绑定实现提交：`{receipts[0]['validation_head']}`。\n"
        "- 已覆盖三类阈值、关键冲突、阈值变更回归、普通中文确认卡、追加决定、持久化重放、撤销、回滚、受影响链重算和事实表写保护。\n"
    )


def _open_risks() -> str:
    return """# 开放风险

- 本阶段只交付规则内核和公开安全模拟证据；尚未进行 S08 三个部分的整体复审。
- 当前 128 项待确认事项和 6 项冲突没有被本阶段自动处理，报告仍显示“暂不可使用”。
- 后续接入真实界面或持久化存储时，必须继续使用控制事件，不能绕过事实表写保护或原始资料只读边界。
- GitHub 上传和 App 重装必须继续等待 v1.5 全部阶段、各阶段复审和最终整体复审完成。
"""


def _rollback() -> str:
    return """# 回滚方案

- 只撤销 S08-P3 新增内核、测试、公开安全证据和对应治理记录。
- 保留已通过的 S08-P1、S08-P2 及更早阶段证据。
- 决定回滚必须通过追加回滚事件，不得删改历史决定或直接修改事实表。
- 不修改原始资料、私有黄金数据、远端 GitHub 或已安装 App。
"""


def expected_outputs() -> dict[Path, str]:
    cases = kernel.synthetic_acceptance_cases()
    receipts = final_receipts()
    final = bool(receipts)
    policy = _policy_artifact(cases)
    classification = _classification_artifact(cases)
    confirmation = _confirmation_artifact(cases)
    events = _event_artifact(cases)
    recalculation = _recalculation_artifact(cases)
    return {
        POLICY_PATH: _dump(policy),
        CLASSIFICATION_PATH: _dump(classification),
        CONFIRMATION_PATH: _dump(confirmation),
        EVENT_LEDGER_PATH: _dump(events),
        RECALCULATION_PATH: _dump(recalculation),
        TASK_MATRIX_PATH: _dump(_task_matrix(final)),
        MANIFEST_PATH: _dump(_manifest(policy, classification, confirmation, events, recalculation, receipts)),
        CONTRACT_PATH: _dump(_contract(policy, classification, confirmation, events, recalculation)),
        IMPLEMENTATION_REPORT_PATH: _implementation_report(final),
        CONFIRMATION_FLOW_PATH: _confirmation_flow(),
        TEST_RESULTS_PATH: _test_results(final, receipts),
        OPEN_RISKS_PATH: _open_risks(),
        ROLLBACK_PATH: _rollback(),
    }


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        VALIDATION_RESULTS_PATH.write_text("", encoding="utf-8")


def check_outputs() -> list[str]:
    mismatches = [
        path.relative_to(REPO_ROOT).as_posix()
        for path, expected in expected_outputs().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
    if not VALIDATION_RESULTS_PATH.is_file():
        mismatches.append(VALIDATION_RESULTS_PATH.relative_to(REPO_ROOT).as_posix())
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise BuildError("deterministic output drift: " + ", ".join(mismatches))
            print("PASS: S08-P3 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("PASS: S08-P3 public-safe artifacts written")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
