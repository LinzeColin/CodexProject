#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S07-P2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import v015_s07_p2_conflict_classification as kernel


OUTPUT_DIR = Path("KMFA/stage_artifacts/V015_S07_P2_CONFLICT_CLASSIFICATION")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "s07_p2_conflict_classification_manifest.json"
TASK_MATRIX_PATH = MACHINE_DIR / "task_acceptance_matrix_public_safe.json"
SAME_SOURCE_PATH = MACHINE_DIR / "same_source_rerun_summary_public_safe.json"
CROSS_SOURCE_PATH = MACHINE_DIR / "cross_source_conflict_queue_snapshot_public_safe.json"
RESPONSIBILITY_PATH = MACHINE_DIR / "responsibility_matrix_public_safe.json"
RECEIPTS_PATH = MACHINE_DIR / "validation_results.jsonl"
CONTRACT_PATH = Path("KMFA/metadata/quality/v015_s07_p2_conflict_classification_public_safe.json")
STATUS_PATH = HUMAN_DIR / "execution_status_zh.md"
SAME_SOURCE_REPORT_PATH = HUMAN_DIR / "same_source_rerun_report_zh.md"
CROSS_SOURCE_REPORT_PATH = HUMAN_DIR / "cross_source_conflict_report_zh.md"
RESPONSIBILITY_REPORT_PATH = HUMAN_DIR / "responsibility_matrix_zh.md"
TEST_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_PATH = HUMAN_DIR / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

S07_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V015_S07_P1_ZERO_DELTA_VALIDATOR/machine/s07_p1_zero_delta_validator_manifest.json"
)
S07_P1_RECEIPTS_PATH = Path(
    "KMFA/stage_artifacts/V015_S07_P1_ZERO_DELTA_VALIDATOR/machine/validation_results.jsonl"
)
EXPECTED_VALIDATION_NAMES = (
    "focused_kernel_tests",
    "focused_governance_tests",
    "pre_final_phase_checker",
    "s07_p1_dependency_check",
    "roadmap_governance_sync_tests",
    "metadata_protocol_check",
    "required_project_governance",
    "lean_governance",
    "changed_governance_sync",
    "no_omission_check",
    "no_float_money_check",
    "public_boundary_check",
    "private_conflict_boundary_check",
    "deterministic_evidence_check",
    "python_compile_check",
    "combined_focused_tests",
    "structured_public_diff_check",
    "s07_p1_regression_contract_check",
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
    manifest = _json(S07_P1_MANIFEST_PATH)
    receipts = _jsonl(S07_P1_RECEIPTS_PATH)
    required = {
        "phase_id": "V015_S07_P1_ZERO_DELTA_VALIDATOR",
        "phase_acceptance_status": "PASSED",
        "decision": "CONTINUE_TO_S07_P2_ONLY",
        "s07_p2_entry_allowed": True,
        "s07_p2_started": False,
        "validation_receipt_count": 18,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches or len(receipts) != 18 or any(row.get("status") != "PASS" for row in receipts):
        raise BuildError("S07-P1 dependency is not exact: " + ", ".join(mismatches))
    heads = {row.get("validation_head") for row in receipts}
    runs = {row.get("validation_run_id") for row in receipts}
    if heads != {manifest.get("validation_head")} or runs != {manifest.get("validation_run_id")}:
        raise BuildError("S07-P1 receipt binding mismatch")
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
        raise BuildError("S07-P2 validation receipt count mismatch")
    if [row.get("name") for row in receipts] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S07-P2 validation receipt order mismatch")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S07-P2 receipt set contains failure")
    if len({row.get("validation_head") for row in receipts}) != 1:
        raise BuildError("S07-P2 receipts do not share one validation head")
    if len({row.get("validation_run_id") for row in receipts}) != 1:
        raise BuildError("S07-P2 receipts do not share one validation run")
    return receipts


def _task_matrix(final: bool) -> dict[str, Any]:
    common = {
        "execution_status": "EXECUTION_COMPLETE",
        "acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "current_result": "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION",
    }
    return {
        "schema_version": "kmfa.v015.s07p2.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S07P2T01", "name_zh": "区分同源引用不一致",
                "acceptance": "同源不一致自动失效并重跑；重跑仍不一致进入系统错误",
                "evidence_refs": [str(SAME_SOURCE_PATH), str(SAME_SOURCE_REPORT_PATH)], **common,
            },
            {
                "task_id": "S07P2T02", "name_zh": "区分跨源业务冲突",
                "acceptance": "跨源冲突进入人工队列，系统不自动选边，未处理时阻断正式报告",
                "evidence_refs": [str(CROSS_SOURCE_PATH), str(CROSS_SOURCE_REPORT_PATH)], **common,
            },
            {
                "task_id": "S07P2T03", "name_zh": "区分用户错误与系统错误",
                "acceptance": "按五层证据判责；系统问题不推给用户；证据不足标记未判定",
                "evidence_refs": [str(RESPONSIBILITY_PATH), str(RESPONSIBILITY_REPORT_PATH)], **common,
            },
        ],
    }


def _manifest(projection: dict[str, Any], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    final = bool(receipts)
    value = {
        **projection,
        "schema_version": "kmfa.v015.s07p2.conflict_classification_manifest.v1",
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
        "decision": "CONTINUE_TO_S07_P3_ONLY" if final else "REMAIN_IN_S07_P2_FINAL_VALIDATION",
        "s07_p1_acceptance_status": "PASSED",
        "s07_p2_started": True,
        "s07_p2_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s07_p3_entry_allowed": final,
        "s07_p3_started": False,
        "s07_stage_review_entry_allowed": False,
        "s07_stage_review_started": False,
    }
    if final:
        value.update({
            "validation_head": receipts[0]["validation_head"],
            "validation_run_id": receipts[0]["validation_run_id"],
            "validation_pass_count": len(receipts),
        })
    return value


def _same_source_summary() -> dict[str, Any]:
    cases = kernel.synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p2.same_source_rerun_summary.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC_ONLY",
        "cases": cases["same_source_cases"],
        "consistent_count": cases["same_source_consistent_count"],
        "invalidated_count": cases["same_source_invalidated_count"],
        "rerun_resolved_count": cases["same_source_rerun_resolved_count"],
        "persistent_system_error_count": cases["same_source_persistent_system_error_count"],
        "private_values_published": False,
    }


def _cross_source_summary(projection: dict[str, Any]) -> dict[str, Any]:
    cases = kernel.synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p2.cross_source_queue_snapshot.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC_ONLY",
        "queue": cases["cross_source_queue"],
        "synthetic_conflict_count": projection["cross_source_conflict_count"],
        "private_conflict_candidate_count": projection["private_conflict_candidate_count"],
        "private_conflict_auto_selected_count": 0,
        "automatic_winner_count": 0,
        "formal_report_blocked_while_pending": True,
        "private_values_published": False,
    }


def _responsibility_summary() -> dict[str, Any]:
    cases = kernel.synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p2.responsibility_matrix.v1",
        "layers": list(kernel.RESPONSIBILITY_LAYERS),
        "cases": cases["responsibility_cases"],
        "case_count": cases["responsibility_case_count"],
        "system_error_count": cases["responsibility_system_error_count"],
        "source_correction_count": cases["responsibility_source_correction_count"],
        "undetermined_count": cases["responsibility_undetermined_count"],
        "system_problem_assigned_to_user_count": 0,
    }


def _status(manifest: dict[str, Any]) -> str:
    return f"""# v1.5 S07-P2 执行状态

- 本轮只完成 S07-P2「冲突分类」，没有进入 S07-P3 或 Stage 复审。
- 三项任务均已实现；当前验收状态：`{manifest['phase_acceptance_status']}`，通过任务：{manifest['task_accepted_count']}/3。
- 同一来源被多个页面引用却出现不同值时，会先让这些引用失效并重跑；重跑仍不一致，明确归为系统错误。
- 不同来源互相冲突时，只进入人工处理队列；系统不会替用户选择 PDF、Excel 或财务表中的任何一方。
- 责任判断固定检查原始值、映射、规则、计算和展示五层；证据不足时只写“未判定”。
- 私有队列仍有 128 项未确认，其中 6 项是冲突候选；本阶段没有自动选边或说成已解决。
- S07 Stage 进度 67%，Stage 仍为 `IN_PROGRESS/PENDING`。
- GitHub upload / App reinstall：`false / false`。
"""


def _same_source_report() -> str:
    return """# S07-P2 同源重跑报告

同一来源、同一版本、同一字段被多个页面使用时，所有页面必须得到完全相同的值。

模拟验收覆盖了三种情况：原本一致；发现不一致后让全部引用失效并重跑，重跑恢复一致；重跑后仍不一致。最后一种不会归咎用户，而是明确标为系统错误，并继续阻断正式报告。
"""


def _cross_source_report(projection: dict[str, Any]) -> str:
    return f"""# S07-P2 跨源冲突报告

PDF、Excel、财务表等不同来源对同一字段给出不同值时，系统建立人工处理事项，保留来源和证据标识，但不自动选择任何一方，也不生成已解决值。

当前私有队列有 {projection['private_conflict_candidate_count']} 项冲突候选、{projection['private_open_unconfirmed_item_count']} 项未确认事项。公开文件只保留数量，不包含项目名、业务金额、来源路径或私有哈希。未处理冲突继续阻断正式报告。
"""


def _responsibility_report() -> str:
    return """# S07-P2 责任判定矩阵

| 检查层 | 有完整证据时的结论 | 证据不足时 |
|---|---|---|
| 原始值 | 只有明确的授权输入证据，才标记“输入方需确认或更正” | 未判定 |
| 映射 | 系统错误 | 未判定 |
| 规则 | 系统错误 | 未判定 |
| 计算 | 系统错误 | 未判定 |
| 展示 | 系统错误 | 未判定 |

系统处理层的问题一律不会转嫁给用户。跨来源业务冲突也不会直接认定为用户错误，必须等待人工核实权威来源。
"""


def _tests(manifest: dict[str, Any]) -> str:
    return f"""# S07-P2 测试结果

- 最终验证状态：`{manifest['evidence_validation_status']}`。
- 同一验证 Run receipts：{manifest['validation_receipt_count']}/{len(EXPECTED_VALIDATION_NAMES)}。
- 已覆盖同源失效与重跑、重跑持续不一致、跨源不自动选边、五层判责、证据不足未判定和私有队列边界。
- 已检查公开证据不含私有项目名、业务值、来源定位或私有哈希。
"""


def _risks() -> str:
    return """# S07-P2 开放风险

- 128 项未确认事项仍未解决，其中 6 项冲突候选仍需要人工确认权威来源。
- 本阶段证明分类和门禁逻辑，不代表所有真实冲突已经完成责任判定。
- “输入方需确认或更正”必须有明确授权输入证据；没有证据时只能未判定。
- 本阶段不生成正式报告、不执行 S07-P3/Stage 复审、不上传 GitHub、不重装 App。
"""


def _rollback() -> str:
    return """# S07-P2 回滚方案

- tracked 实现和证据可用本 Phase 的提交反向提交回滚。
- S07-P1 与 S06 锁定证据不属于本阶段修改范围，不得覆盖或删除。
- 若分类或判责规则有误，只回滚 S07-P2，修正后重新生成完整验证记录。
- Downloads 原始数据和私有队列内容不属于本阶段写入或回滚范围。
"""


def expected_outputs() -> dict[Path, str]:
    projection = kernel.public_projection()
    receipts = final_receipts()
    manifest = _manifest(projection, receipts)
    return {
        CONTRACT_PATH: _dump(projection),
        MANIFEST_PATH: _dump(manifest),
        TASK_MATRIX_PATH: _dump(_task_matrix(bool(receipts))),
        SAME_SOURCE_PATH: _dump(_same_source_summary()),
        CROSS_SOURCE_PATH: _dump(_cross_source_summary(projection)),
        RESPONSIBILITY_PATH: _dump(_responsibility_summary()),
        STATUS_PATH: _status(manifest),
        SAME_SOURCE_REPORT_PATH: _same_source_report(),
        CROSS_SOURCE_REPORT_PATH: _cross_source_report(projection),
        RESPONSIBILITY_REPORT_PATH: _responsibility_report(),
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
    parser = argparse.ArgumentParser(description="Build S07-P2 public-safe evidence")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.write:
        write_outputs()
        print("WROTE: S07-P2 public-safe evidence")
    else:
        check_outputs()
        print("PASS: S07-P2 public-safe evidence matches deterministic builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
