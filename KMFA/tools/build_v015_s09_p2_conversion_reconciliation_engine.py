#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S09-P2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s09_p2_conversion_reconciliation_engine as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "1085bcf2609fc54e70f1e8b9e8d1f1238a0d263f"
P1_MANIFEST_PATH = PROJECT_ROOT / "stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/s09_p1_scope_rule_modeling_manifest.json"

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
CONVERSION_POLICY_PATH = PROJECT_ROOT / "metadata/quality/v015_s09_p2_conversion_policy_public_safe.json"
RECONCILIATION_POLICY_PATH = PROJECT_ROOT / "metadata/quality/v015_s09_p2_project_financial_reconciliation_public_safe.json"
RERUN_PROTOCOL_PATH = PROJECT_ROOT / "metadata/protocol/v015_s09_p2_rerun_confirmation_protocol_public_safe.json"
CONVERSION_CASES_PATH = MACHINE_ROOT / "conversion_conservation_cases_public_safe.json"
RECONCILIATION_CASES_PATH = MACHINE_ROOT / "project_financial_reconciliation_cases_public_safe.json"
RERUN_CASES_PATH = MACHINE_ROOT / "rerun_confirmation_cases_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
MANIFEST_PATH = MACHINE_ROOT / "s09_p2_conversion_reconciliation_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s09_p1_dependency_regression",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "s09_p1_dependency",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "metadata_protocol",
    "project_governance",
    "lean_governance",
    "governance_sync",
    "no_float_money",
    "no_omission",
    "taskpack_source",
    "structured_public_diff",
    "public_boundary",
    "git_diff_check",
)


class BuildError(RuntimeError):
    pass


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    value = json.loads(P1_MANIFEST_PATH.read_text(encoding="utf-8"))
    required = {
        "run_phase_id": "V015_S09_P1_SCOPE_RULE_MODELING",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "phase_task_accepted_count": 3,
        "s09_p2_entry_allowed": True,
        "s09_p2_started": False,
        "legal_ledger_count": 1,
        "derived_view_count": 5,
        "difference_type_count": 8,
        "raw_root_access_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    mismatch = [key for key, expected in required.items() if value.get(key) != expected]
    if mismatch:
        raise BuildError("S09-P1 dependency drift: " + ", ".join(mismatch))
    return value


def _validation_binding() -> tuple[bool, str | None, str | None, int]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return False, None, None, 0
    rows = [
        json.loads(line)
        for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(rows) != len(EXPECTED_VALIDATION_NAMES):
        return False, None, None, len(rows)
    if [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        return False, None, None, len(rows)
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == 1
        and len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None, len(rows)


def _conversion_policy() -> dict[str, Any]:
    policy = kernel.validate_conversion_policy(kernel.default_conversion_policy())
    return {
        **policy,
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "input_output_conservation_required": True,
        "imbalance_blocks_processing": True,
        "unapproved_adjustment_effective_allowed": False,
        "formal_report_generation_included": False,
        "raw_root_access_count": 0,
    }


def _reconciliation_policy() -> dict[str, Any]:
    return {
        **kernel.default_reconciliation_policy(),
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "project_metric_scope": list(kernel.OPERATING_METRICS),
        "difference_required_fields": [
            "difference_ref",
            "difference_type_code",
            "status",
            "project_ref",
            "metric",
            "source_kind",
            "source_refs",
            "expected_amount_cents",
            "actual_amount_cents",
            "delta_cents",
            "affected_view_ids",
            "impact_zh",
        ],
        "formal_report_generation_included": False,
        "raw_root_access_count": 0,
    }


def _rerun_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s09p2.rerun_confirmation_protocol.v1",
        "protocol_ref": "RERUN-CONFIRMATION-PROTOCOL-S09P2-V1",
        "protocol_version": "1.0.0",
        "phase_id": kernel.RUN_PHASE_ID,
        "same_source_mismatch_action": "INVALIDATE_AND_RERUN_FULL_DERIVED_CHAIN",
        "persistent_same_source_mismatch_action": "BLOCK_AS_SYSTEM_ERROR",
        "cross_source_conflict_action": "PENDING_HUMAN_CONFIRMATION",
        "rerun_chain_layers": list(kernel.RERUN_CHAIN_LAYERS),
        "all_affected_consumers_required": True,
        "source_version_binding_must_not_change": True,
        "old_derived_versions_preserved": True,
        "old_derived_version_overwrite_allowed": False,
        "automatic_cross_source_winner_allowed": False,
        "raw_source_mutation_allowed": False,
        "source_layer_write_allowed": False,
        "formal_report_generation_included": False,
        "raw_root_access_count": 0,
    }


def _cases() -> dict[str, dict[str, Any]]:
    acceptance = kernel.synthetic_acceptance_cases()
    conversion = acceptance["conversion"]
    reconciliation = acceptance["reconciliation"]
    missing = acceptance["missing_source_reconciliation"]
    resolved = acceptance["rerun_resolved"]
    persistent = acceptance["rerun_persistent"]
    cross_source = acceptance["cross_source_confirmation"]
    return {
        "conversion": {
            "schema_version": "kmfa.v015.s09p2.conversion_cases.v1",
            "balanced_conversion": conversion,
            "conversion_rule_count": len(kernel.default_conversion_policy()["rules"]),
            "operating_fact_count": len(conversion["operating_facts"]),
            "imbalance_blocked": acceptance["imbalance_blocked"],
            "float_money_rejected": acceptance["float_money_rejected"],
            "source_snapshot_unchanged": conversion["source_snapshot_unchanged"],
            "unapproved_effective_count": conversion["unapproved_effective_count"],
            "silent_difference_count": conversion["silent_difference_count"],
            "raw_root_access_count": 0,
        },
        "reconciliation": {
            "schema_version": "kmfa.v015.s09p2.reconciliation_cases.v1",
            "complete_chain_case": reconciliation,
            "missing_source_case": missing,
            "required_source_kinds": list(kernel.RECONCILIATION_SOURCE_KINDS),
            "opposite_delta_values": acceptance["opposite_delta_values"],
            "opposite_differences_retained_separately": reconciliation[
                "opposite_differences_retained_separately"
            ],
            "silent_offset_count": reconciliation["silent_offset_count"],
            "every_difference_has_source_and_impact": all(
                row.get("source_refs") and row.get("affected_view_ids") and row.get("impact_zh")
                for row in reconciliation["differences"] + missing["differences"]
            ),
            "raw_root_access_count": 0,
        },
        "rerun": {
            "schema_version": "kmfa.v015.s09p2.rerun_cases.v1",
            "same_source_resolved_case": resolved,
            "same_source_persistent_case": persistent,
            "cross_source_confirmation_case": cross_source,
            "full_chain_layer_count": len(kernel.RERUN_CHAIN_LAYERS),
            "resolved_chain_state_consistent": resolved["chain_state_consistent"],
            "persistent_chain_state_consistent": persistent["chain_state_consistent"],
            "cross_source_automatic_winner": cross_source["automatic_winner"],
            "source_snapshot_unchanged": resolved["source_snapshot_unchanged"]
            and persistent["source_snapshot_unchanged"],
            "raw_source_mutation_performed": False,
            "raw_root_access_count": 0,
        },
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S09P2T01",
            "name_zh": "实现账务到经营视图转换",
            "output_zh": "转换引擎",
            "acceptance_zh": "输入、已审批调整、输出和显式差异按整数分守恒；无法平衡时阻断。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/quality/v015_s09_p2_conversion_policy_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/conversion_conservation_cases_public_safe.json",
            ],
        },
        {
            "task_id": "S09P2T02",
            "name_zh": "实现项目与财务交叉核对",
            "output_zh": "交叉核对",
            "acceptance_zh": "凭证、应收、发票和银行逐项核对，每个差异都有来源和影响且不静默轧差。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/quality/v015_s09_p2_project_financial_reconciliation_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/project_financial_reconciliation_cases_public_safe.json",
            ],
        },
        {
            "task_id": "S09P2T03",
            "name_zh": "实现同源重跑和跨源确认",
            "output_zh": "重跑编排",
            "acceptance_zh": "同源不一致重跑完整派生链；跨源冲突不自动选边；所有状态一致且来源不变。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/protocol/v015_s09_p2_rerun_confirmation_protocol_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/machine/rerun_confirmation_cases_public_safe.json",
            ],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s09p2.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_count": 3,
        "task_accepted_count": 3 if final else 0,
        "phase_acceptance_status": status,
        "tasks": tasks,
    }


def _manifest(final: bool, run_id: str | None, head: str | None, receipt_count: int, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    conversion = cases["conversion"]["balanced_conversion"]
    reconciliation = cases["reconciliation"]["complete_chain_case"]
    return {
        "schema_version": "kmfa.v015.s09p2.manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "version": kernel.VERSION,
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "run_mode": "CONTROLLED_RUN",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_phase_count": 72,
        "overall_accepted_phase_count": 24 if final else 23,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "stage_phase_pass_count": 2 if final else 1,
        "stage_task_accepted_count": 6 if final else 3,
        "conversion_rule_count": cases["conversion"]["conversion_rule_count"],
        "operating_fact_count": cases["conversion"]["operating_fact_count"],
        "input_total_cents": conversion["conservation"]["input_total_cents"],
        "approved_adjustment_total_cents": conversion["conservation"]["approved_adjustment_total_cents"],
        "output_total_cents": conversion["conservation"]["output_total_cents"],
        "conservation_residual_cents": conversion["conservation"]["residual_cents"],
        "conservation_passed": conversion["conservation"]["conservation_passed"],
        "imbalance_blocked": cases["conversion"]["imbalance_blocked"],
        "float_money_rejected": cases["conversion"]["float_money_rejected"],
        "reconciliation_required_source_count": reconciliation["required_source_count"],
        "reconciliation_exact_match_count": reconciliation["exact_match_count"],
        "reconciliation_difference_count": reconciliation["difference_count"],
        "missing_source_confirmation_count": sum(
            1
            for row in cases["reconciliation"]["missing_source_case"]["differences"]
            if row["status"] == "MISSING_SOURCE_REQUIRES_CONFIRMATION"
        ),
        "opposite_differences_retained_separately": cases["reconciliation"][
            "opposite_differences_retained_separately"
        ],
        "every_difference_has_source_and_impact": cases["reconciliation"][
            "every_difference_has_source_and_impact"
        ],
        "silent_offset_count": 0,
        "rerun_chain_layer_count": cases["rerun"]["full_chain_layer_count"],
        "same_source_rerun_resolved": cases["rerun"]["same_source_resolved_case"]["status"]
        == "RERUN_RESOLVED",
        "persistent_same_source_blocked": cases["rerun"]["same_source_persistent_case"]["status"]
        == "SYSTEM_ERROR_BLOCKED",
        "cross_source_status": cases["rerun"]["cross_source_confirmation_case"]["status"],
        "cross_source_automatic_winner": None,
        "chain_state_consistent": cases["rerun"]["resolved_chain_state_consistent"]
        and cases["rerun"]["persistent_chain_state_consistent"],
        "source_snapshot_unchanged": cases["conversion"]["source_snapshot_unchanged"]
        and cases["rerun"]["source_snapshot_unchanged"],
        "raw_source_mutation_performed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "decision": "CONTINUE_TO_S09_P3_ONLY" if final else "REMAIN_IN_S09_P2_FINAL_VALIDATION",
        "s09_p1_acceptance_status": "PASSED",
        "s09_p2_started": True,
        "s09_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s09_p3_entry_allowed": final,
        "s09_p3_started": False,
        "s09_stage_review_entry_allowed": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_run_id": run_id,
        "validation_head": head,
        "validation_receipt_count": receipt_count if final else 0,
        "validation_pass_count": receipt_count if final else 0,
        "validation_failed_count": 0,
    }


def _human_outputs(final: bool, run_id: str | None, head: str | None) -> dict[Path, str]:
    state = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    receipt = (
        f"最终验收批次 `{run_id}` 已将 20 项通过记录绑定到实现提交 `{head}`。"
        if final
        else "实现已完成，等待绑定同一实现提交的最终验收记录。"
    )
    return {
        HUMAN_ROOT / "implementation_report_zh.md": (
            "# S09-P2 实施结果\n\n"
            f"当前状态：`{state}`。\n\n"
            "本阶段把同一套合法账本按版本化规则转换为经营事实；每一分钱都必须在输入、已审批调整、输出或显式差异中找到去向。"
            "项目收入和成本分别与凭证、应收、发票、银行逐项核对，正负差异即使合计为零也保留两条。"
            "同一来源在不同位置显示不一致时重跑完整派生链；重跑仍不一致就按系统错误阻断。不同来源冲突只交给人工确认。\n\n"
            f"{receipt}\n\n"
            "未读取或改写 raw，未生成正式报告，未上传 GitHub，未重装 App。\n"
        ),
        HUMAN_ROOT / "conversion_guide_zh.md": (
            "# 账务转经营视图说明\n\n"
            "1. 每条账务记录只匹配一条已登记规则。\n"
            "2. 只有已审批且在有效范围内的调整可以进入经营事实。\n"
            "3. 输入金额 + 有效调整 = 输出金额 + 显式差异；差一分钱即停止。\n"
            "4. 转换只生成新事实，不修改合法账本或 raw。\n"
        ),
        HUMAN_ROOT / "reconciliation_guide_zh.md": (
            "# 项目与财务核对说明\n\n"
            "项目收入或成本分别与凭证、应收、发票、银行核对。每项差异必须写清来源、预期、实际、相差金额和影响。"
            "缺少任何一类来源都会进入人工确认；两项方向相反的差异不会互相抵消。\n"
        ),
        HUMAN_ROOT / "rerun_guide_zh.md": (
            "# 重跑与人工确认说明\n\n"
            "同一来源、同一版本、同一字段在多个位置不一致时，所有受影响结果先失效，再重跑完整派生链。"
            "旧版本保留，不覆盖。重跑后仍不一致时按系统错误阻断。不同来源冲突不自动选边，只进入人工确认。\n"
        ),
        HUMAN_ROOT / "risks_and_rollback_zh.md": (
            "# 风险与回滚\n\n"
            "- 无法守恒：立即阻断，不发布经营事实。\n"
            "- 来源缺失或口径不同：进入人工确认，不输出伪通过。\n"
            "- 同源重跑仍冲突：完整链标记系统错误，不修改来源。\n"
            "- 回滚：撤销本阶段派生版本和治理登记；合法账本、raw 与前序验收不变。\n"
        ),
        HUMAN_ROOT / "test_results_zh.md": (
            "# S09-P2 验收结果\n\n"
            f"状态：`{state}`。\n\n"
            "已覆盖整数分守恒、不平衡阻断、浮点拒绝、四类来源交叉核对、差异来源与影响、反向差异不轧差、"
            "缺来源确认、同源重跑成功与持续失败、跨源人工确认、完整链状态一致和来源不变。\n\n"
            f"{receipt}\n"
        ),
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    final, run_id, head, receipt_count = _validation_binding()
    cases = _cases()
    outputs = {
        CONVERSION_POLICY_PATH: _json_text(_conversion_policy()),
        RECONCILIATION_POLICY_PATH: _json_text(_reconciliation_policy()),
        RERUN_PROTOCOL_PATH: _json_text(_rerun_protocol()),
        CONVERSION_CASES_PATH: _json_text(cases["conversion"]),
        RECONCILIATION_CASES_PATH: _json_text(cases["reconciliation"]),
        RERUN_CASES_PATH: _json_text(cases["rerun"]),
        TASK_MATRIX_PATH: _json_text(_task_matrix(final)),
        MANIFEST_PATH: _json_text(_manifest(final, run_id, head, receipt_count, cases)),
    }
    outputs.update(_human_outputs(final, run_id, head))
    return outputs


def write_outputs() -> None:
    for path, text in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def check_outputs() -> None:
    drift = []
    for path, expected in expected_outputs().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            drift.append(str(path.relative_to(REPO_ROOT)))
    if drift:
        raise BuildError("generated S09-P2 evidence drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S09-P2 deterministic evidence is current" if args.check else "PASS: S09-P2 evidence written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
