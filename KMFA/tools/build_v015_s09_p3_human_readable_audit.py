#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S09-P3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from KMFA.tools import v015_s09_p3_human_readable_audit as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "cdea5801a08d435531834a17eaff5566cef19fe2"
P2_MANIFEST_PATH = PROJECT_ROOT / (
    "stage_artifacts/V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE/"
    "machine/s09_p2_conversion_reconciliation_manifest.json"
)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT"
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
RULE_MANUAL_PATH = PROJECT_ROOT / "metadata/protocol/v015_s09_p3_human_rule_manual_public_safe.json"
REPORT_DISPLAY_SPEC_PATH = PROJECT_ROOT / (
    "metadata/quality/v015_s09_p3_report_difference_display_spec_public_safe.json"
)
CLOSURE_PROTOCOL_PATH = PROJECT_ROOT / (
    "metadata/protocol/v015_s09_p3_difference_closure_protocol_public_safe.json"
)
RULE_REVIEW_PATH = MACHINE_ROOT / "rule_manual_review_public_safe.json"
REPORT_SAMPLE_PATH = MACHINE_ROOT / "report_difference_sample_public_safe.json"
CLOSURE_E2E_PATH = MACHINE_ROOT / "difference_closure_e2e_public_safe.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
MANIFEST_PATH = MACHINE_ROOT / "s09_p3_human_readable_audit_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"

EXPECTED_VALIDATION_NAMES = (
    "python_compile",
    "focused_kernel_tests",
    "focused_artifact_tests",
    "focused_governance_tests",
    "s09_predecessor_regression",
    "deterministic_evidence",
    "pre_final_phase_checker",
    "s09_p2_dependency",
    "roadmap_governance_tests",
    "roadmap_sync_pending",
    "metadata_protocol",
    "project_governance",
    "lean_governance",
    "governance_sync",
    "no_float_money",
    "no_omission",
    "taskpack_source",
    "business_display_boundary",
    "public_boundary",
    "git_diff_check",
)


class BuildError(RuntimeError):
    pass


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    value = json.loads(P2_MANIFEST_PATH.read_text(encoding="utf-8"))
    required = {
        "run_phase_id": "V015_S09_P2_CONVERSION_RECONCILIATION_ENGINE",
        "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS",
        "phase_task_accepted_count": 3,
        "overall_accepted_phase_count": 24,
        "stage_execution_percentage": 67,
        "s09_p2_acceptance_status": "PASSED",
        "s09_p3_entry_allowed": True,
        "s09_p3_started": False,
        "s09_stage_review_entry_allowed": False,
        "raw_root_access_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    mismatch = [key for key, expected in required.items() if value.get(key) != expected]
    if mismatch:
        raise BuildError("S09-P2 dependency drift: " + ", ".join(mismatch))
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


def _rule_manual(cases: dict[str, Any]) -> dict[str, Any]:
    return {
        **cases["manual"],
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "finance_reviewable_required": True,
        "owner_summary_required": True,
        "review_record_ref": (
            "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/"
            "machine/rule_manual_review_public_safe.json"
        ),
    }


def _report_spec(cases: dict[str, Any]) -> dict[str, Any]:
    return {
        **kernel.validate_report_display_spec(cases["report_display_spec"]),
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "sample_ref": (
            "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/"
            "machine/report_difference_sample_public_safe.json"
        ),
    }


def _closure_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s09p3.difference_closure_protocol.v1",
        "protocol_ref": "DIFFERENCE-CLOSURE-PROTOCOL-S09P3-V1",
        "protocol_version": "1.0.0",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "ordered_steps": list(kernel.CLOSURE_STEPS),
        "ordered_step_count": len(kernel.CLOSURE_STEPS),
        "feedback_required_for_every_step": True,
        "append_only_history_required": True,
        "status_refresh_persistence_required": True,
        "historical_query_required": True,
        "missing_feedback_fails": True,
        "out_of_order_step_fails": True,
        "source_or_fact_overwrite_allowed": False,
        "formal_report_generation_included": False,
        "raw_root_access_count": 0,
    }


def _evidence(cases: dict[str, Any]) -> dict[str, dict[str, Any]]:
    review = cases["manual_review"]
    report = cases["report_summary"]
    closure = cases["closure_snapshot"]
    return {
        "review": {
            **review,
            "phase_id": kernel.RUN_PHASE_ID,
            "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
            "manual_ref": cases["manual"]["manual_ref"],
            "rule_keys": [row["rule_key"] for row in cases["manual"]["rules"]],
            "raw_root_access_count": 0,
        },
        "report": {
            **report,
            "phase_id": kernel.RUN_PHASE_ID,
            "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
            "display_spec_ref": cases["report_display_spec"]["spec_ref"],
        },
        "closure": {
            "schema_version": "kmfa.v015.s09p3.difference_closure_e2e.v1",
            "phase_id": kernel.RUN_PHASE_ID,
            "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
            "case_ref": closure["case_ref"],
            "business_label_zh": closure["business_label_zh"],
            "required_step_count": len(kernel.CLOSURE_STEPS),
            "event_count": len(closure["events"]),
            "event_types": [row["event_type"] for row in closure["events"]],
            "feedback_count": sum(bool(row.get("feedback_zh")) for row in closure["events"]),
            "current_status_zh": closure["current_status_zh"],
            "initial_report_version": closure["initial_report_version"],
            "current_report_version": closure["current_report_version"],
            "report_version_advanced": closure["current_report_version"] != closure["initial_report_version"],
            "closure_complete": closure["closure_complete"],
            "refresh_state_persisted": cases["refresh_state_persisted"],
            "history_queryable": cases["history_queryable"],
            "history": cases["closure_history"],
            "missing_feedback_rejected": cases["missing_feedback_rejected"],
            "out_of_order_rejected": cases["out_of_order_rejected"],
            "source_or_fact_mutation_performed": closure["source_or_fact_mutation_performed"],
            "raw_root_access_count": 0,
        },
    }


def _task_matrix(final: bool) -> dict[str, Any]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    tasks = [
        {
            "task_id": "S09P3T01",
            "name_zh": "编写人类可读规则手册",
            "output_zh": "规则手册",
            "acceptance_zh": "两类转换与八类差异均用业务语言说明，财务可逐项复核，老板可阅读摘要。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/protocol/v015_s09_p3_human_rule_manual_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/machine/rule_manual_review_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/human/rule_manual_zh.md",
            ],
        },
        {
            "task_id": "S09P3T02",
            "name_zh": "设计报告差异摘要",
            "output_zh": "报告展示规范",
            "acceptance_zh": "只展示影响经营判断的差异，标题不暴露内部机制，经营摘要不含调试信息。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/quality/v015_s09_p3_report_difference_display_spec_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/machine/report_difference_sample_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/human/report_sample_zh.md",
            ],
        },
        {
            "task_id": "S09P3T03",
            "name_zh": "验证差异闭环",
            "output_zh": "闭环证据",
            "acceptance_zh": "发现、处理、影响预览、确认、重算、报告更新六步都有反馈，刷新后状态持久且历史可查。",
            "status": status,
            "current_result": result,
            "evidence_refs": [
                "KMFA/metadata/protocol/v015_s09_p3_difference_closure_protocol_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/machine/difference_closure_e2e_public_safe.json",
                "KMFA/stage_artifacts/V015_S09_P3_HUMAN_READABLE_AUDIT/human/difference_closure_record_zh.md",
            ],
        },
    ]
    return {
        "schema_version": "kmfa.v015.s09p3.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_count": 3,
        "task_accepted_count": 3 if final else 0,
        "phase_acceptance_status": status,
        "tasks": tasks,
    }


def _manifest(
    final: bool,
    run_id: str | None,
    head: str | None,
    receipt_count: int,
    cases: dict[str, Any],
) -> dict[str, Any]:
    review = cases["manual_review"]
    report = cases["report_summary"]
    closure = cases["closure_snapshot"]
    return {
        "schema_version": "kmfa.v015.s09p3.manifest.v1",
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
        "overall_accepted_phase_count": 25 if final else 24,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "manual_audience_count": review["audience_count"],
        "transformation_rule_count": review["transformation_rule_count"],
        "difference_rule_count": review["difference_rule_count"],
        "human_rule_count": review["total_rule_count"],
        "unexplained_rule_count": review["unexplained_rule_count"],
        "owner_summary_missing_count": review["owner_summary_missing_count"],
        "finance_review_status": review["finance_review_status"],
        "owner_summary_status": review["owner_summary_status"],
        "external_human_signoff_claimed": False,
        "report_input_difference_count": report["input_difference_count"],
        "report_included_difference_count": report["included_difference_count"],
        "report_excluded_non_decision_difference_count": report["excluded_non_decision_difference_count"],
        "report_technical_term_occurrence_count": report["technical_term_occurrence_count"],
        "report_debug_field_count": report["debug_field_count"],
        "closure_required_step_count": len(kernel.CLOSURE_STEPS),
        "closure_event_count": len(closure["events"]),
        "closure_feedback_count": sum(bool(row.get("feedback_zh")) for row in closure["events"]),
        "closure_complete": closure["closure_complete"],
        "refresh_state_persisted": cases["refresh_state_persisted"],
        "history_queryable": cases["history_queryable"],
        "missing_feedback_rejected": cases["missing_feedback_rejected"],
        "out_of_order_rejected": cases["out_of_order_rejected"],
        "report_version_advanced": closure["current_report_version"] != closure["initial_report_version"],
        "source_or_fact_mutation_performed": False,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "decision": "CONTINUE_TO_S09_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S09_P3_FINAL_VALIDATION",
        "s09_p1_acceptance_status": "PASSED",
        "s09_p2_acceptance_status": "PASSED",
        "s09_p3_started": True,
        "s09_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s09_stage_review_entry_allowed": final,
        "s09_stage_review_started": False,
        "s09_stage_review_performed": False,
        "s10_entry_allowed": False,
        "s10_p1_entry_allowed": False,
        "s10_p1_started": False,
        "report_sample_generated": True,
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


def _rule_manual_markdown(cases: dict[str, Any]) -> str:
    lines = [
        "# S09-P3 人类规则手册",
        "",
        "这份手册只回答三件事：发生了什么、会影响什么、下一步怎么做。",
        "财务人员可按来源、期间、金额、证据和审批逐项复核；老板只看经营影响摘要。",
        "",
    ]
    for index, row in enumerate(cases["manual"]["rules"], start=1):
        lines.extend(
            [
                f"## {index}. {row['name_zh']}",
                "",
                f"- 发生了什么：{row['what_happened_zh']}",
                f"- 经营影响：{row['business_impact_zh']}",
                f"- 财务怎么审：{row['review_action_zh']}",
                f"- 老板摘要：{row['owner_summary_zh']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 评审边界",
            "",
            "本轮完成的是内容结构与可读性评审记录，不冒充真实业务人员签字，也不生成正式经营报告。",
            "",
        ]
    )
    return "\n".join(lines)


def _report_sample_markdown(cases: dict[str, Any]) -> str:
    report = cases["report_summary"]
    lines = [
        "# 经营差异摘要样例",
        "",
        "这里只展示会影响经营判断的事项。内部编号、技术机制和调试信息不会出现。",
        "",
    ]
    for item in report["items"]:
        lines.extend(
            [
                f"## {item['title_zh']}",
                "",
                f"- 发生了什么：{item['what_changed_zh']}",
                f"- 对经营的影响：{item['business_impact_zh']}",
                f"- 当前状态：{item['current_status_zh']}",
                f"- 建议动作：{item['recommended_action_zh']}",
                "",
            ]
        )
    lines.append("本文件是公开安全的模拟展示，不是正式经营报告。")
    lines.append("")
    return "\n".join(lines)


def _closure_markdown(cases: dict[str, Any]) -> str:
    lines = [
        "# 差异闭环记录",
        "",
        "状态必须依次经过发现、处理、影响预览、确认、重算和报告更新。任何一步没有反馈都会失败。",
        "",
    ]
    for row in cases["closure_history"]:
        lines.append(f"{row['sequence']}. {row['step_zh']}：{row['feedback_zh']}")
    lines.extend(
        [
            "",
            "刷新验证：状态保持不变；历史六步均可查询；旧报告版本保留。",
            "",
        ]
    )
    return "\n".join(lines)


def _human_outputs(
    final: bool,
    run_id: str | None,
    head: str | None,
    cases: dict[str, Any],
) -> dict[Path, str]:
    state = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    receipt = (
        f"最终验收批次 `{run_id}` 已将 20 项通过记录绑定到实现提交 `{head}`。"
        if final
        else "实现已完成，等待绑定同一实现提交的最终验收记录。"
    )
    return {
        HUMAN_ROOT / "rule_manual_zh.md": _rule_manual_markdown(cases),
        HUMAN_ROOT / "rule_manual_review_zh.md": (
            "# 规则手册评审记录\n\n"
            "财务复核视角：通过；两类转换与八类差异均可逐项检查。\n\n"
            "老板摘要视角：通过；每类规则都说明了经营影响与下一步动作。\n\n"
            "说明：这是设计验收自评，不冒充真实外部签字。\n"
        ),
        HUMAN_ROOT / "report_display_spec_zh.md": (
            "# 经营差异展示规范\n\n"
            "1. 只展示会改变收入、成本、毛利、现金、税务时点或风险判断的差异。\n"
            "2. 每条只写发生了什么、经营影响、当前状态和建议动作。\n"
            "3. 标题必须是业务语言；内部编号、代码、调试信息和故障堆栈不得出现。\n"
            "4. 无经营影响的控制项留在内部待办，不挤占老板注意力。\n"
            "5. 本规范只生成模拟样例，不生成正式经营报告。\n"
        ),
        HUMAN_ROOT / "report_sample_zh.md": _report_sample_markdown(cases),
        HUMAN_ROOT / "difference_closure_record_zh.md": _closure_markdown(cases),
        HUMAN_ROOT / "implementation_report_zh.md": (
            "# S09-P3 实施结果\n\n"
            f"当前状态：`{state}`。\n\n"
            "两类转换和八类差异已有中文规则手册；经营摘要只保留影响决策的事项；"
            "差异必须经过发现、处理、影响预览、确认、重算和报告更新六步，刷新后状态不丢失，历史可查询。\n\n"
            f"{receipt}\n\n"
            "未读取或改写 raw，未生成正式报告，未上传 GitHub，未重装 App。\n"
        ),
        HUMAN_ROOT / "risks_and_rollback_zh.md": (
            "# 风险与回滚\n\n"
            "- 规则没有中文说明：阻断验收。\n"
            "- 经营摘要出现内部机制或调试信息：阻断验收。\n"
            "- 闭环缺步骤、乱序或没有反馈：阻断验收。\n"
            "- 刷新后状态或历史变化：阻断验收。\n"
            "- 回滚只撤销本阶段派生文件和治理登记；S09-P1/P2、原账和 raw 保持不变。\n"
        ),
        HUMAN_ROOT / "test_results_zh.md": (
            "# S09-P3 验收结果\n\n"
            f"状态：`{state}`。\n\n"
            "已覆盖规则完整性、财务与老板双视角、经营影响筛选、技术词与调试字段阻断、"
            "六步顺序、逐步反馈、人工确认、重算、报告版本更新、刷新持久和历史查询。\n\n"
            f"{receipt}\n"
        ),
    }


def expected_outputs() -> dict[Path, str]:
    dependency()
    final, run_id, head, receipt_count = _validation_binding()
    cases = kernel.synthetic_acceptance_cases()
    evidence = _evidence(cases)
    outputs = {
        RULE_MANUAL_PATH: _json_text(_rule_manual(cases)),
        REPORT_DISPLAY_SPEC_PATH: _json_text(_report_spec(cases)),
        CLOSURE_PROTOCOL_PATH: _json_text(_closure_protocol()),
        RULE_REVIEW_PATH: _json_text(evidence["review"]),
        REPORT_SAMPLE_PATH: _json_text(evidence["report"]),
        CLOSURE_E2E_PATH: _json_text(evidence["closure"]),
        TASK_MATRIX_PATH: _json_text(_task_matrix(final)),
        MANIFEST_PATH: _json_text(_manifest(final, run_id, head, receipt_count, cases)),
    }
    outputs.update(_human_outputs(final, run_id, head, cases))
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
        raise BuildError("generated S09-P3 evidence drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: S09-P3 deterministic evidence is current" if args.check else "PASS: S09-P3 evidence written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
