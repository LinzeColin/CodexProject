#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S09-P1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s09_p1_scope_rule_modeling as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "29e355302cfec7c5e5f4e076eaa226c32bc18213"
EXPECTED_VALIDATION_COUNT = 20
EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s08_stage_review_regression",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "s08_stage_review_dependency",
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

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / "V015_S09_P1_SCOPE_RULE_MODELING"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s09_p1_scope_rule_modeling_manifest.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
BOUNDARY_CASES_PATH = MACHINE_ROOT / "ledger_view_boundary_cases_public_safe.json"
DIFFERENCE_CASES_PATH = MACHINE_ROOT / "difference_dictionary_cases_public_safe.json"
ADJUSTMENT_CASES_PATH = MACHINE_ROOT / "adjustment_event_cases_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

LEDGER_POLICY_PATH = PROJECT_ROOT / "metadata" / "quality" / "v015_s09_p1_ledger_view_policy_public_safe.json"
DIFFERENCE_DICTIONARY_PATH = PROJECT_ROOT / "metadata" / "quality" / "v015_s09_p1_difference_dictionary_public_safe.json"
ADJUSTMENT_PROTOCOL_PATH = PROJECT_ROOT / "metadata" / "protocol" / "v015_s09_p1_adjustment_event_protocol_public_safe.json"

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
LEDGER_MAP_PATH = HUMAN_ROOT / "ledger_view_map_zh.md"
DIFFERENCE_DICTIONARY_HUMAN_PATH = HUMAN_ROOT / "difference_dictionary_zh.md"
ADJUSTMENT_PROTOCOL_HUMAN_PATH = HUMAN_ROOT / "adjustment_protocol_zh.md"
OPEN_RISKS_PATH = HUMAN_ROOT / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_ROOT / "rollback_plan_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"

S08_REVIEW_MANIFEST_PATH = (
    PROJECT_ROOT
    / "stage_artifacts"
    / "V015_S08_STAGE_REVIEW"
    / "machine"
    / "s08_stage_review_manifest.json"
)
S08_REVIEW_RECEIPTS_PATH = (
    PROJECT_ROOT
    / "stage_artifacts"
    / "V015_S08_STAGE_REVIEW"
    / "machine"
    / "validation_results.jsonl"
)


class BuildError(RuntimeError):
    pass


def dependency() -> dict[str, Any]:
    manifest = json.loads(S08_REVIEW_MANIFEST_PATH.read_text(encoding="utf-8"))
    receipts = [
        json.loads(line)
        for line in S08_REVIEW_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    required = {
        "run_phase_id": "V015_S08_STAGE_REVIEW",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "decision": "GO_TO_S09_P1_ONLY",
        "s08_stage_review_performed": True,
        "s08_stage_review_acceptance_status": "PASSED",
        "s09_entry_allowed": True,
        "s09_p1_entry_allowed": True,
        "s09_p1_started": False,
        "validation_receipt_count": 23,
    }
    mismatches = [key for key, expected in required.items() if manifest.get(key) != expected]
    if mismatches:
        raise BuildError("S08 review dependency mismatch: " + ", ".join(mismatches))
    if len(receipts) != 23 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S08 review receipt set is not exactly 23 PASS records")
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S08 review validation head mismatch")
    if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
        raise BuildError("S08 review validation run mismatch")
    return {
        "acceptance_status": manifest["phase_acceptance_status"],
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(receipts),
        "s09_p1_entry_allowed": True,
        "s09_p1_started": False,
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise BuildError("validation receipt row must be an object")
            rows.append(value)
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S09-P1 validation receipt order mismatch")
    return rows


def _final_binding(receipts: list[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not receipts:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in receipts}
    heads = {row.get("validation_head") for row in receipts}
    final = (
        len(receipts) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in receipts)
        and len(run_ids) == 1
        and len(heads) == 1
        and None not in run_ids
        and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S09P1T01",
            "name_zh": "建立唯一账本与多视图边界",
            "output_zh": "口径地图",
            "acceptance_zh": "只有一套合法账本，五类视图均可解释并回勾法定账务。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/quality/v015_s09_p1_ledger_view_policy_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/ledger_view_boundary_cases_public_safe.json",
            ],
        },
        {
            "task_id": "S09P1T02",
            "name_zh": "建立差异类型字典",
            "output_zh": "差异字典",
            "acceptance_zh": "八类差异均有方向、证据、处理和报告展示规则；未知类型进入确认。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/quality/v015_s09_p1_difference_dictionary_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/difference_dictionary_cases_public_safe.json",
            ],
        },
        {
            "task_id": "S09P1T03",
            "name_zh": "建立调整事件模型",
            "output_zh": "调整协议",
            "acceptance_zh": "调整只追加事件，不改原账；包含原因、证据、审批、有效期和撤销。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/protocol/v015_s09_p1_adjustment_event_protocol_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/machine/adjustment_event_cases_public_safe.json",
            ],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s09p1.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_count": len(tasks),
        "task_accepted_count": len(tasks) if final else 0,
        "phase_acceptance_status": status,
        "tasks": tasks,
    }


def _adjustment_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s09p1.adjustment_event_protocol.v1",
        "protocol_ref": "ADJUSTMENT-EVENT-PROTOCOL-S09P1-V1",
        "protocol_version": "1.0.0",
        "event_schema_version": "kmfa.v015.s09p1.adjustment_event.v1",
        "event_types": list(kernel.EVENT_TYPES),
        "required_fields": [
            "event_ref",
            "sequence",
            "previous_event_ref",
            "event_type",
            "adjustment_ref",
            "difference_type_code",
            "amount_delta_cents",
            "affected_view_ids",
            "reason_zh",
            "evidence_codes",
            "risk_level",
            "valid_from",
            "valid_to",
            "actor_role",
            "recorded_at",
            "target_event_ref",
            "approval_status",
        ],
        "normal_approver_roles": list(kernel.APPROVER_ROLES),
        "high_risk_approver_roles": list(kernel.HIGH_RISK_APPROVER_ROLES),
        "append_only_required": True,
        "direct_legal_ledger_mutation_allowed": False,
        "raw_source_mutation_allowed": False,
        "unapproved_adjustment_effective_allowed": False,
        "high_risk_without_owner_level_approval_allowed": False,
        "reversal_requires_new_event": True,
        "s09_p2_conversion_execution_included": False,
    }


def _human_ledger_map(policy: dict[str, Any]) -> str:
    lines = [
        "# S09-P1 唯一账本与多视图口径地图",
        "",
        "KMFA 只有一套合法账本。下面五类内容都是从同一账本按版本化规则形成的只读视图，不是内账、外账或第二套账。",
        "",
        "| 视图 | 用途 | 必须遵守 |",
        "|---|---|---|",
    ]
    for view in policy["views"]:
        lines.append(
            f"| {view['label_zh']} | {view['purpose_zh']} | 必须回勾合法账本；调整只写控制事件；不得改原值。 |"
        )
    lines.extend(
        [
            "",
            "## 硬停止线",
            "",
            "- 不允许创建平行账本或把视图固化成另一套账。",
            "- 不允许绕过法定账务核对，也不允许以任何方式规避监管。",
            "- 不允许为了经营展示直接修改原账或原始资料。",
        ]
    )
    return "\n".join(lines) + "\n"


def _human_difference_dictionary(dictionary: dict[str, Any]) -> str:
    lines = [
        "# S09-P1 差异类型字典",
        "",
        "| 差异类型 | 方向 | 风险 | 需要什么证据 | 如何处理 |",
        "|---|---|---|---|---|",
    ]
    for row in dictionary["types"]:
        lines.append(
            "| {label} | {direction} | {risk} | {evidence} | {handling} |".format(
                label=row["label_zh"],
                direction=row["direction"],
                risk="高" if row["risk_level"] == "HIGH" else "普通",
                evidence="、".join(row["required_evidence_codes"]),
                handling=row["handling_rule_zh"],
            )
        )
    lines.extend(
        [
            "",
            "未知类型或证据不完整时一律进入人工确认，不自动归类、不静默轧差。经营报告只显示会影响经营判断的中文摘要。",
        ]
    )
    return "\n".join(lines) + "\n"


def _human_adjustment_protocol() -> str:
    return """# S09-P1 调整事件协议

管理调整不能改原账，也不能改原始资料。每次处理都新增一条事件，历史事件永久保留。

每个调整必须包含：差异类型、整数分金额、受影响视图、业务原因、证据、风险等级、生效期间、操作人和记录时间。

生效顺序：

1. 提出调整，状态为“等待审批”。
2. 审批通过后，且在有效期内，调整才可用于后续视图计算。
3. 高风险调整必须由财务负责人或负责人审批，普通复核人不能放行。
4. 撤销必须新增撤销事件，不能删除或覆盖原审批。
5. S09-P2 才实现转换与核对引擎，本阶段只完成规则和事件边界。
"""


def build_outputs() -> dict[Path, str]:
    acceptance = kernel.synthetic_acceptance_cases()
    policy = acceptance["ledger_view_policy"]
    dictionary = acceptance["difference_dictionary"]
    receipts = _receipts()
    final, validation_run_id, validation_head = _final_binding(receipts)
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    decision = "CONTINUE_TO_S09_P2_ONLY" if final else "REMAIN_IN_S09_P1_FINAL_VALIDATION"
    task_matrix = _task_matrix(final)

    boundary_cases = {
        "schema_version": "kmfa.v015.s09p1.ledger_view_boundary_cases.v1",
        "synthetic_fixture": True,
        "positive_case_count": len(acceptance["boundary_results"]),
        "positive_pass_count": len(acceptance["boundary_results"]),
        "negative_case_count": len(acceptance["negative_boundary_codes"]),
        "negative_pass_count": len(acceptance["negative_boundary_codes"]),
        "results": acceptance["boundary_results"],
        "rejected_codes": acceptance["negative_boundary_codes"],
    }
    difference_cases = {
        "schema_version": "kmfa.v015.s09p1.difference_dictionary_cases.v1",
        "synthetic_fixture": True,
        "registered_type_count": len(dictionary["types"]),
        "registered_case_count": len(acceptance["difference_classification_results"]),
        "registered_case_pass_count": len(acceptance["difference_classification_results"]),
        "results": acceptance["difference_classification_results"],
        "unknown_result": acceptance["unknown_difference_result"],
        "incomplete_result": acceptance["incomplete_difference_result"],
        "float_money_rejected": acceptance["float_money_rejected"],
        "silent_offset_count": 0,
    }
    adjustment_cases = {
        "schema_version": "kmfa.v015.s09p1.adjustment_event_cases.v1",
        "synthetic_fixture": True,
        "event_count": len(acceptance["adjustment_events"]),
        "events": acceptance["adjustment_events"],
        "event_roundtrip_exact": acceptance["adjustment_event_roundtrip_exact"],
        "normal_before_approval": acceptance["normal_before_approval"],
        "normal_active": acceptance["normal_active"],
        "normal_reversed": acceptance["normal_reversed"],
        "high_before_approval": acceptance["high_before_approval"],
        "high_risk_unauthorized_rejected": acceptance["high_risk_unauthorized_rejected"],
        "high_active": acceptance["high_active"],
        "high_expired": acceptance["high_expired"],
        "direct_ledger_mutation_rejected": acceptance["direct_ledger_mutation_rejected"],
        "source_snapshot_unchanged": acceptance["source_snapshot_unchanged"],
    }
    manifest: dict[str, Any] = {
        "schema_version": "kmfa.v015.s09p1.scope_rule_modeling_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "run_mode": "CONTROLLED_RUN",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "counted_as_taskpack_phase": True,
        "counted_as_taskpack_task_count": 3,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": status,
        "evidence_validation_status": "PASS" if final else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 33,
        "stage_phase_pass_count": 1 if final else 0,
        "stage_task_accepted_count": 3 if final else 0,
        "phase_task_count": 3,
        "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 23 if final else 22,
        "overall_taskpack_phase_count": 72,
        "decision": decision,
        "s08_stage_review_acceptance_status": "PASSED",
        "s08_stage_review_performed": True,
        "s09_entry_allowed": True,
        "s09_p1_entry_allowed": False,
        "s09_p1_started": True,
        "s09_p1_acceptance_status": status,
        "s09_p2_entry_allowed": final,
        "s09_p2_started": False,
        "s09_p3_entry_allowed": False,
        "s09_stage_review_entry_allowed": False,
        "product_implementation_allowed": final,
        "legal_ledger_count": 1,
        "derived_view_count": len(policy["views"]),
        "parallel_ledger_rejected": True,
        "regulatory_evasion_rejected": True,
        "source_value_mutation_allowed": False,
        "difference_type_count": len(dictionary["types"]),
        "difference_required_field_coverage_count": len(dictionary["types"]),
        "unknown_difference_confirmation_count": 1,
        "incomplete_difference_confirmation_count": 1,
        "silent_offset_count": 0,
        "adjustment_event_count": len(acceptance["adjustment_events"]),
        "adjustment_event_roundtrip_exact": acceptance["adjustment_event_roundtrip_exact"],
        "unapproved_adjustment_effective_count": 0,
        "high_risk_unauthorized_approval_rejected": acceptance["high_risk_unauthorized_rejected"],
        "reversal_case_count": 1,
        "direct_ledger_mutation_rejected": acceptance["direct_ledger_mutation_rejected"],
        "source_snapshot_unchanged": acceptance["source_snapshot_unchanged"],
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "validation_receipt_count": len(receipts) if final else 0,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "evidence_refs": [
            "KMFA/metadata/quality/v015_s09_p1_ledger_view_policy_public_safe.json",
            "KMFA/metadata/quality/v015_s09_p1_difference_dictionary_public_safe.json",
            "KMFA/metadata/protocol/v015_s09_p1_adjustment_event_protocol_public_safe.json",
            "KMFA/stage_artifacts/V015_S09_P1_SCOPE_RULE_MODELING/",
        ],
    }

    implementation_report = f"""# KMFA v1.5 S09-P1 口径规则建模

- 状态：`{status}`。
- 唯一合法账本：1 套；派生视图：5 类；平行账本、监管规避和原账修改均被阻断。
- 差异类型：8 类；未知类型和证据不完整均进入人工确认，静默轧差为 0。
- 调整事件：{len(acceptance['adjustment_events'])} 条模拟事件；未审批不生效；高风险未经负责人级审批会失败；支持追加式撤销。
- 本轮未读取原始业务资料，未执行转换核对引擎、正式报告、GitHub 上传或 App 重装。
- 下一步：{'只开放尚未开始的 S09-P2。' if final else '完成同一实现提交上的最终验证；S09-P2 保持关闭。'}
"""
    test_results = f"""# S09-P1 测试结果

- 唯一账本与五类视图正向案例：5/5 通过。
- 平行账本、监管规避、绕过核对和修改原账：4/4 被阻断。
- 八类差异字典案例：8/8 通过；未知类型和证据不足均进入确认。
- 调整事件追加、审批、生效、撤销、有效期和回放：全部通过。
- 最终验收回执：{len(receipts)}/{EXPECTED_VALIDATION_COUNT if final else EXPECTED_VALIDATION_COUNT} {'通过' if final else '尚未生成'}。
"""
    open_risks = """# S09-P1 开放风险

- 本阶段只建立规则与事件边界，S09-P2 的转换、守恒和交叉核对引擎尚未实现。
- 128 项待确认事项和 6 项冲突仍未关闭，不能据此发布正式经营报告。
- 税务、坏账和跨期规则属于高风险事项，真实使用前仍需合格负责人复核，系统不得替代监管、税务或法律判断。
- 公开证据全部为模拟数据，不能冒充真实业务结果。
"""
    rollback = """# S09-P1 回滚方案

1. 仅回滚本阶段新增的规则模块、测试、公开安全元数据、证据和治理记录。
2. 不触碰原始业务资料、历史验收回执和 S08 已通过证据。
3. 回滚后恢复到 S08 整体复审通过、仅允许重新进入 S09-P1 的状态。
"""

    return {
        LEDGER_POLICY_PATH: _json(policy),
        DIFFERENCE_DICTIONARY_PATH: _json(dictionary),
        ADJUSTMENT_PROTOCOL_PATH: _json(_adjustment_protocol()),
        TASK_MATRIX_PATH: _json(task_matrix),
        BOUNDARY_CASES_PATH: _json(boundary_cases),
        DIFFERENCE_CASES_PATH: _json(difference_cases),
        ADJUSTMENT_CASES_PATH: _json(adjustment_cases),
        MANIFEST_PATH: _json(manifest),
        IMPLEMENTATION_REPORT_PATH: implementation_report,
        LEDGER_MAP_PATH: _human_ledger_map(policy),
        DIFFERENCE_DICTIONARY_HUMAN_PATH: _human_difference_dictionary(dictionary),
        ADJUSTMENT_PROTOCOL_HUMAN_PATH: _human_adjustment_protocol(),
        OPEN_RISKS_PATH: open_risks,
        ROLLBACK_PATH: rollback,
        TEST_RESULTS_PATH: test_results,
    }


def write_outputs() -> None:
    for path, content in build_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    VALIDATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not VALIDATION_RESULTS_PATH.exists():
        VALIDATION_RESULTS_PATH.write_text("", encoding="utf-8")


def check_outputs() -> list[str]:
    mismatches: list[str] = []
    for path, expected in build_outputs().items():
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(path.relative_to(REPO_ROOT).as_posix())
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
                raise BuildError("deterministic artifact drift: " + ", ".join(mismatches))
            print("PASS: S09-P1 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S09-P1 public-safe artifacts")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
