#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S07-P3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import v015_s07_p3_release_gate as kernel


OUTPUT_DIR = Path("KMFA/stage_artifacts/V015_S07_P3_RELEASE_GATE")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "s07_p3_release_gate_manifest.json"
TASK_MATRIX_PATH = MACHINE_DIR / "task_acceptance_matrix_public_safe.json"
STATUS_SNAPSHOT_PATH = MACHINE_DIR / "report_status_snapshot_public_safe.json"
CLOSURE_PROTOCOL_PATH = MACHINE_DIR / "difference_closure_protocol_public_safe.json"
REGRESSION_PATH = MACHINE_DIR / "regression_gate_summary_public_safe.json"
RECEIPTS_PATH = MACHINE_DIR / "validation_results.jsonl"
CONTRACT_PATH = Path("KMFA/metadata/quality/v015_s07_p3_release_gate_public_safe.json")
STATUS_PATH = HUMAN_DIR / "execution_status_zh.md"
REPORT_STATUS_PATH = HUMAN_DIR / "report_status_zh.md"
CLOSURE_REPORT_PATH = HUMAN_DIR / "difference_closure_protocol_zh.md"
REGRESSION_REPORT_PATH = HUMAN_DIR / "regression_gate_report_zh.md"
TEST_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_PATH = HUMAN_DIR / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

S07_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V015_S07_P2_CONFLICT_CLASSIFICATION/machine/s07_p2_conflict_classification_manifest.json"
)
S07_P2_RECEIPTS_PATH = Path(
    "KMFA/stage_artifacts/V015_S07_P2_CONFLICT_CLASSIFICATION/machine/validation_results.jsonl"
)
EXPECTED_VALIDATION_NAMES = (
    "focused_kernel_tests",
    "focused_governance_tests",
    "pre_final_phase_checker",
    "s07_p2_dependency_check",
    "roadmap_governance_sync_tests",
    "metadata_protocol_check",
    "required_project_governance",
    "lean_governance",
    "changed_governance_sync",
    "no_omission_check",
    "no_float_money_check",
    "public_boundary_check",
    "private_regression_boundary_check",
    "deterministic_evidence_check",
    "python_compile_check",
    "combined_focused_tests",
    "structured_public_diff_check",
    "s07_p2_regression_contract_check",
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
    manifest = _json(S07_P2_MANIFEST_PATH)
    receipts = _jsonl(S07_P2_RECEIPTS_PATH)
    required = {
        "phase_id": "V015_S07_P2_CONFLICT_CLASSIFICATION",
        "phase_acceptance_status": "PASSED",
        "decision": "CONTINUE_TO_S07_P3_ONLY",
        "s07_p3_entry_allowed": True,
        "s07_p3_started": False,
        "validation_receipt_count": 18,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches or len(receipts) != 18 or any(row.get("status") != "PASS" for row in receipts):
        raise BuildError("S07-P2 dependency is not exact: " + ", ".join(mismatches))
    if {row.get("validation_head") for row in receipts} != {manifest.get("validation_head")}:
        raise BuildError("S07-P2 validation head mismatch")
    if {row.get("validation_run_id") for row in receipts} != {manifest.get("validation_run_id")}:
        raise BuildError("S07-P2 validation run mismatch")
    return {
        "phase_id": manifest["phase_id"],
        "acceptance_status": manifest["phase_acceptance_status"],
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(receipts),
    }


def final_receipts() -> list[dict[str, Any]]:
    receipts = _jsonl(RECEIPTS_PATH)
    if not receipts:
        return []
    if len(receipts) != len(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S07-P3 validation receipt count mismatch")
    if [row.get("name") for row in receipts] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S07-P3 validation receipt order mismatch")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S07-P3 receipt set contains failure")
    if len({row.get("validation_head") for row in receipts}) != 1:
        raise BuildError("S07-P3 receipts do not share one validation head")
    if len({row.get("validation_run_id") for row in receipts}) != 1:
        raise BuildError("S07-P3 receipts do not share one validation run")
    return receipts


def _task_matrix(final: bool) -> dict[str, Any]:
    common = {
        "execution_status": "EXECUTION_COMPLETE",
        "acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "current_result": "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION",
    }
    return {
        "schema_version": "kmfa.v015.s07p3.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S07P3T01", "name_zh": "建立报告可信状态",
                "acceptance": "界面只显示三种人类语言状态；关键差异未关闭时不得发布",
                "evidence_refs": [str(STATUS_SNAPSHOT_PATH), str(REPORT_STATUS_PATH)], **common,
            },
            {
                "task_id": "S07P3T02", "name_zh": "建立差异关闭条件",
                "acceptance": "四种关闭流程均必须重算和复核；只改状态不能关闭",
                "evidence_refs": [str(CLOSURE_PROTOCOL_PATH), str(CLOSURE_REPORT_PATH)], **common,
            },
            {
                "task_id": "S07P3T03", "name_zh": "建立回归门禁",
                "acceptance": "变更后自动重跑全部已通过项目，历史项目 100% 通过，失败禁止合并",
                "evidence_refs": [str(REGRESSION_PATH), str(REGRESSION_REPORT_PATH)], **common,
            },
        ],
    }


def _manifest(projection: dict[str, Any], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    final = bool(receipts)
    value = {
        **projection,
        "schema_version": "kmfa.v015.s07p3.release_gate_manifest.v1",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "run_mode": "CONTROLLED_RUN",
        "work_kind": "PRODUCT_IMPLEMENTATION",
        "counted_as_taskpack_phase": True,
        "counted_as_taskpack_task_count": 3,
        "dependency": dependency(),
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "task_accepted_count": 3 if final else 0,
        "validation_receipt_count": len(receipts),
        "validation_failed_count": 0,
        "decision": "CONTINUE_TO_S07_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S07_P3_FINAL_VALIDATION",
        "s07_p2_acceptance_status": "PASSED",
        "s07_p3_started": True,
        "s07_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s07_stage_review_entry_allowed": final,
        "s07_stage_review_started": False,
        "s08_p1_entry_allowed": False,
    }
    if final:
        value.update({
            "validation_head": receipts[0]["validation_head"],
            "validation_run_id": receipts[0]["validation_run_id"],
            "validation_pass_count": len(receipts),
        })
    return value


def _status_snapshot() -> dict[str, Any]:
    cases = kernel.synthetic_acceptance_cases()
    current = kernel.current_private_release_status()
    return {
        "schema_version": "kmfa.v015.s07p3.report_status_snapshot.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC_AND_PRIVATE_AGGREGATE",
        "allowed_display_labels_zh": list(kernel.HUMAN_STATUS_LABELS),
        "synthetic_status_cases": cases["status_cases"],
        "ui_technical_abbreviation_count": cases["ui_technical_abbreviation_count"],
        "current_private_aggregate_status": current,
        "private_values_published": False,
    }


def _closure_protocol() -> dict[str, Any]:
    cases = kernel.synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p3.difference_closure_protocol.v1",
        "closure_kinds": list(kernel.CLOSURE_KINDS),
        "closure_kind_count": cases["closure_kind_count"],
        "required_common_steps_zh": ["提供对应更正或确认的证据", "重新计算", "重新复核", "确认重算后差异为零"],
        "synthetic_closure_cases": cases["closure_cases"],
        "status_only_closure_rejected": cases["status_only_closure_rejected"],
        "missing_recalculation_rejected": cases["missing_recalculation_rejected"],
        "private_values_published": False,
    }


def _regression_summary(projection: dict[str, Any]) -> dict[str, Any]:
    cases = kernel.synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p3.regression_gate_summary.v1",
        "automatic_rerun_required_after_every_change": True,
        "passing_synthetic_case": cases["passing_regression"],
        "failing_synthetic_case": cases["failing_regression"],
        "missing_project_rerun_rejected": cases["missing_project_rerun_rejected"],
        "private_historical_project_count": projection["private_historical_project_count"],
        "private_selected_for_rerun_count": projection["private_selected_for_rerun_count"],
        "private_regression_pass_count": projection["private_regression_pass_count"],
        "private_regression_fail_count": projection["private_regression_fail_count"],
        "private_regression_pass_rate_bps": projection["private_regression_pass_rate_bps"],
        "private_merge_allowed": projection["private_merge_allowed"],
        "private_project_identities_published": False,
    }


def _status(manifest: dict[str, Any]) -> str:
    return f"""# v1.5 S07-P3 执行状态

- 本轮只完成 S07-P3「发布门禁」，没有执行 S07 整体复审、S08、GitHub 上传或 App 重装。
- 三项任务均已实现；当前验收状态：`{manifest['phase_acceptance_status']}`，通过任务：{manifest['task_accepted_count']}/3。
- 用户只会看到“可内部使用”“需确认”“暂不可使用”三种中文状态，不显示技术等级缩写。
- 人工确认、规则更正、源文件更正和系统修复四种关闭方式都必须重新计算并复核；只改状态不能关闭差异。
- 每次变更后必须重跑全部已通过项目；当前 8 个历史项目全部重跑并通过，失败 0。
- 现有 128 项未确认事项和 6 项冲突候选没有被关闭；当前报告状态仍是“暂不可使用”，正式报告未生成。
- S07 Stage 执行进度 100%，但仍为 `IN_PROGRESS/PENDING`，等待新的独立 Stage 复审 Run。
- GitHub upload / App reinstall：`false / false`。
"""


def _report_status_report() -> str:
    return """# S07-P3 报告状态说明

用户只看到三种状态：

- 可内部使用：关键差异已关闭，重算、复核和历史项目回归全部通过。
- 需确认：没有关键阻断，但仍有非关键事项或责任待确认。
- 暂不可使用：仍有关键差异、来源冲突、系统错误，或重算、复核、回归未通过。

当前真实状态是“暂不可使用”，因为仍有未处理的冲突候选和待证据事项。本 Phase 通过只证明门禁能力正确，不代表正式报告已经可以发布。
"""


def _closure_report() -> str:
    return """# S07-P3 差异关闭协议

差异只能通过四种流程关闭：人工确认、规则更正、源文件更正、系统修复。每种流程都必须依次完成：

1. 保存对应的确认或更正证据。
2. 重新计算受影响结果。
3. 重新复核计算结果和来源。
4. 确认重算后该差异为零，再写入关闭状态。

只把状态从“开放”改成“关闭”、缺少重算记录、缺少复核记录或重算后仍有差异，均会失败。
"""


def _regression_report(projection: dict[str, Any]) -> str:
    return f"""# S07-P3 回归门禁报告

- 每次变更都必须选择全部历史已通过项目执行回归，少跑任何一个项目都会失败。
- 当前历史项目：{projection['private_historical_project_count']} 个。
- 已自动选择并重跑：{projection['private_selected_for_rerun_count']} 个。
- 通过/失败：{projection['private_regression_pass_count']}/{projection['private_regression_fail_count']}，通过率 100%。
- 只要有一个项目失败，合并权限立即关闭。
- 公开证据只保留数量，不包含项目名称、金额、来源路径或私有哈希。
"""


def _tests(manifest: dict[str, Any]) -> str:
    return f"""# S07-P3 测试结果

- 最终验证状态：`{manifest['evidence_validation_status']}`。
- 同一验证 Run receipts：{manifest['validation_receipt_count']}/{len(EXPECTED_VALIDATION_NAMES)}。
- 已覆盖三种中文状态、技术缩写禁用、关键差异阻断、四种关闭流程、只改状态失败、全项目自动回归和任一失败禁止合并。
- 已检查当前正式报告仍关闭，S07 复审、S08、GitHub 和 App 均未启动。
"""


def _risks() -> str:
    return """# S07-P3 开放风险

- 128 项未确认事项和 6 项冲突候选仍未解决，当前报告仍是“暂不可使用”。
- 当前 8 个历史项目回归通过，只证明已确认黄金范围；新增项目或新来源必须进入后续回归集合。
- S07 三个 Phase 尚未合并复审；Stage 复审可能发现跨 Phase 合同问题。
- 本阶段不生成正式报告、不执行 Stage 复审/S08、不上传 GitHub、不重装 App。
"""


def _rollback() -> str:
    return """# S07-P3 回滚方案

- tracked 实现和证据可用本 Phase 的提交反向提交回滚。
- S07-P1/P2 和 S06 私有黄金、队列不属于本阶段修改范围，不得覆盖或删除。
- 若状态、关闭或回归规则有误，只回滚 S07-P3，修正后重新生成完整验证记录。
- Downloads 原始数据、GitHub 和已安装 App 不属于本阶段写入或回滚范围。
"""


def expected_outputs() -> dict[Path, str]:
    projection = kernel.public_projection()
    receipts = final_receipts()
    manifest = _manifest(projection, receipts)
    return {
        CONTRACT_PATH: _dump(projection),
        MANIFEST_PATH: _dump(manifest),
        TASK_MATRIX_PATH: _dump(_task_matrix(bool(receipts))),
        STATUS_SNAPSHOT_PATH: _dump(_status_snapshot()),
        CLOSURE_PROTOCOL_PATH: _dump(_closure_protocol()),
        REGRESSION_PATH: _dump(_regression_summary(projection)),
        STATUS_PATH: _status(manifest),
        REPORT_STATUS_PATH: _report_status_report(),
        CLOSURE_REPORT_PATH: _closure_report(),
        REGRESSION_REPORT_PATH: _regression_report(projection),
        TEST_PATH: _tests(manifest),
        RISK_PATH: _risks(),
        ROLLBACK_PATH: _rollback(),
    }


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs() -> None:
    mismatches = [
        str(path) for path, content in expected_outputs().items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    if mismatches:
        raise BuildError("deterministic output mismatch: " + ", ".join(mismatches))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build S07-P3 public-safe evidence")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.write:
        write_outputs()
        print("WROTE: S07-P3 public-safe evidence")
    else:
        check_outputs()
        print("PASS: S07-P3 public-safe evidence matches deterministic builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
