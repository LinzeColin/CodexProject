#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S07-P1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import v015_s07_p1_zero_delta_validator as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path("KMFA/stage_artifacts/V015_S07_P1_ZERO_DELTA_VALIDATOR")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "s07_p1_zero_delta_validator_manifest.json"
TASK_MATRIX_PATH = MACHINE_DIR / "task_acceptance_matrix_public_safe.json"
FIELD_SUMMARY_PATH = MACHINE_DIR / "field_comparison_summary_public_safe.json"
RECONCILIATION_SUMMARY_PATH = MACHINE_DIR / "reconciliation_summary_public_safe.json"
DIFFERENCE_SNAPSHOT_PATH = MACHINE_DIR / "difference_report_snapshot_public_safe.json"
RECEIPTS_PATH = MACHINE_DIR / "validation_results.jsonl"
CONTRACT_PATH = Path("KMFA/metadata/quality/v015_s07_p1_zero_delta_validator_public_safe.json")
STATUS_PATH = HUMAN_DIR / "execution_status_zh.md"
CROSS_REPORT_PATH = HUMAN_DIR / "cross_validation_report_zh.md"
DIFFERENCE_REPORT_PATH = HUMAN_DIR / "difference_report_snapshot_zh.md"
TEST_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_PATH = HUMAN_DIR / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

S06_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V015_S06_STAGE_REVIEW/machine/s06_stage_review_manifest.json"
)
S06_REVIEW_RECEIPTS_PATH = Path(
    "KMFA/stage_artifacts/V015_S06_STAGE_REVIEW/machine/validation_results.jsonl"
)
EXPECTED_VALIDATION_NAMES = (
    "focused_kernel_tests",
    "focused_governance_tests",
    "pre_final_phase_checker",
    "s06_dependency_check",
    "roadmap_governance_sync_tests",
    "metadata_protocol_check",
    "required_project_governance",
    "lean_governance",
    "changed_governance_sync",
    "no_omission_check",
    "no_float_money_check",
    "public_boundary_check",
    "private_golden_boundary_check",
    "deterministic_evidence_check",
    "python_compile_check",
    "combined_focused_tests",
    "structured_public_diff_check",
    "s06_regression_contract_check",
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
    values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(value, dict) for value in values):
        raise BuildError(f"JSONL object rows required: {path}")
    return values


def dependency() -> dict[str, Any]:
    manifest = _json(S06_REVIEW_MANIFEST_PATH)
    receipts = _jsonl(S06_REVIEW_RECEIPTS_PATH)
    required = {
        "run_phase_id": "V015_S06_STAGE_REVIEW",
        "stage_acceptance_status": "PASSED",
        "s06_stage_review_acceptance_status": "PASSED",
        "decision": "GO_TO_S07_P1_ONLY",
        "s07_p1_entry_allowed": True,
        "s07_p1_started": False,
        "validation_receipt_count": 21,
    }
    mismatches = [key for key, value in required.items() if manifest.get(key) != value]
    if mismatches or len(receipts) != 21 or any(row.get("status") != "PASS" for row in receipts):
        raise BuildError("S06 review dependency is not exact: " + ", ".join(mismatches))
    heads = {row.get("validation_head") for row in receipts}
    runs = {row.get("validation_run_id") for row in receipts}
    if heads != {manifest.get("validation_head")} or runs != {manifest.get("validation_run_id")}:
        raise BuildError("S06 review receipt binding mismatch")
    return {
        "phase_id": manifest["run_phase_id"],
        "acceptance_status": manifest["s06_stage_review_acceptance_status"],
        "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"],
        "validation_receipt_count": len(receipts),
    }


def final_receipts() -> list[dict[str, Any]]:
    receipts = _jsonl(RECEIPTS_PATH)
    if not receipts:
        return []
    if len(receipts) != len(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S07-P1 validation receipt count mismatch")
    if [row.get("name") for row in receipts] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S07-P1 validation receipt order mismatch")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S07-P1 receipt set contains failure")
    if len({row.get("validation_head") for row in receipts}) != 1:
        raise BuildError("S07-P1 receipts do not share one validation head")
    if len({row.get("validation_run_id") for row in receipts}) != 1:
        raise BuildError("S07-P1 receipts do not share one validation run")
    return receipts


def _task_matrix(final: bool) -> dict[str, Any]:
    acceptance = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    result = "TASK_ACCEPTED" if final else "AWAITING_FINAL_VALIDATION"
    common = {
        "execution_status": "EXECUTION_COMPLETE",
        "acceptance_status": acceptance,
        "current_result": result,
    }
    return {
        "schema_version": "kmfa.v015.s07p1.task_acceptance_matrix.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                "task_id": "S07P1T01",
                "name_zh": "实现字段级精确比较",
                "acceptance": "金额容差固定为 0 分，任何 1 分差异失败",
                "evidence_refs": [str(FIELD_SUMMARY_PATH), "KMFA/tests/test_v015_s07_p1_zero_delta_validator.py"],
                **common,
            },
            {
                "task_id": "S07P1T02",
                "name_zh": "实现汇总与交叉勾稽",
                "acceptance": "每条公式都有输入证据和差额记录，不可解释差异阻塞",
                "evidence_refs": [str(RECONCILIATION_SUMMARY_PATH), str(CROSS_REPORT_PATH)],
                **common,
            },
            {
                "task_id": "S07P1T03",
                "name_zh": "生成差异报告",
                "acceptance": "报告可定位字段、公式、影响和处理步骤",
                "evidence_refs": [str(DIFFERENCE_SNAPSHOT_PATH), str(DIFFERENCE_REPORT_PATH)],
                **common,
            },
        ],
    }


def _manifest(projection: dict[str, Any], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    final = bool(receipts)
    value = {
        **projection,
        "schema_version": "kmfa.v015.s07p1.zero_delta_manifest.v1",
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
        "decision": "CONTINUE_TO_S07_P2_ONLY" if final else "REMAIN_IN_S07_P1_FINAL_VALIDATION",
        "s07_p1_started": True,
        "s07_p1_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s07_p2_entry_allowed": final,
        "s07_p2_started": False,
        "s07_p3_entry_allowed": False,
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


def _field_summary(projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s07p1.field_comparison_summary.v1",
        "field_types": projection["field_types"],
        "field_type_count": projection["field_type_count"],
        "money_tolerance_cents": projection["money_tolerance_cents"],
        "minimum_fail_difference_cents": projection["minimum_fail_difference_cents"],
        "one_cent_difference_detected": projection["one_cent_difference_detected"],
        "synthetic_exact_pass_count": projection["synthetic_field_exact_pass_count"],
        "synthetic_deliberate_fail_count": projection["synthetic_field_deliberate_fail_count"],
        "private_values_published": False,
    }


def _reconciliation_summary(projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s07p1.reconciliation_summary.v1",
        "formula_families": ["DETAIL_TO_CATEGORY", "CATEGORY_TO_PROJECT", "GROSS_PROFIT", "GROSS_MARGIN"],
        "margin_rounding_policy": projection["rounding_policy"],
        "every_formula_has_evidence_and_difference_record": projection["every_formula_has_evidence_and_difference_record"],
        "synthetic_formula_count": projection["synthetic_reconciliation_formula_count"],
        "synthetic_exact_pass_count": projection["synthetic_reconciliation_exact_pass_count"],
        "synthetic_deliberate_fail_count": projection["synthetic_reconciliation_deliberate_fail_count"],
        "private_project_count": projection["private_project_count"],
        "private_accepted_field_count": projection["private_accepted_field_count"],
        "private_formula_check_count": projection["private_formula_check_count"],
        "private_formula_fail_count": projection["private_formula_fail_count"],
        "private_zero_difference": projection["private_zero_difference"],
        "blocking_unexplained_difference_count": projection["blocking_unexplained_difference_count"],
        "open_unconfirmed_item_count": projection["open_unconfirmed_item_count"],
        "open_items_may_be_treated_as_resolved": False,
        "private_values_published": False,
    }


def _difference_snapshot() -> dict[str, Any]:
    synthetic = kernel.synthetic_acceptance_cases()
    return {
        "schema_version": "kmfa.v015.s07p1.difference_report_snapshot.v1",
        "fixture_scope": "PUBLIC_SAFE_SYNTHETIC_ONLY",
        "required_fields": list(kernel.DIFFERENCE_FIELDS),
        "difference_count": synthetic["difference_report_count"],
        "complete_difference_count": synthetic["difference_report_complete_count"],
        "differences": synthetic["difference_snapshot"],
        "private_difference_detail_published": False,
    }


def _status(manifest: dict[str, Any]) -> str:
    return f"""# v1.5 S07-P1 执行状态

- 本轮只完成 S07-P1「零差异校验器」，没有进入 S07-P2、S07-P3 或 Stage 复审。
- 三项任务均已实现；当前验收状态：`{manifest['phase_acceptance_status']}`，通过任务：{manifest['task_accepted_count']}/3。
- 金额按整数分精确比较，允许误差固定为 0 分；任何 1 分差异都会失败。
- 文本、枚举、日期和单位均按已登记规则精确比较，不会自动猜测或吞掉差异。
- 已确认的 8 个项目、92 个字段在私有运行区复算，公开文件不包含项目名、金额、来源定位或私有哈希。
- 仍有 128 项等待证据；本阶段没有把它们说成已解决，也没有擅自统一税口径或推广跨期结论。
- S07 Stage 进度 33%，Stage 仍为 `IN_PROGRESS/PENDING`。
- GitHub upload / App reinstall：`false / false`。
"""


def _cross_report(manifest: dict[str, Any]) -> str:
    return f"""# S07-P1 交叉勾稽报告

本校验器按四层顺序检查：

1. 同一分类下的明细金额之和，必须等于该分类合计。
2. 全部分类合计之和，必须等于项目总成本。
3. 合同金额减项目总成本，必须等于毛利。
4. 毛利除以合同金额，按 `ROUND_HALF_UP` 取整数基点后，必须等于毛利率。

每条公式都保存输入证据、预期值、实际值和差额。私有黄金范围共复算 {manifest['private_project_count']} 个项目、{manifest['private_formula_check_count']} 条公式，失败 {manifest['private_formula_fail_count']} 条，金额误差为 0 分。

边界：这只证明 92 个已确认字段及其项目汇总；128 个待证据事项继续保持未解决，不能据此生成正式报告或业务结论。
"""


def _difference_report(snapshot: dict[str, Any]) -> str:
    lines = [
        "# S07-P1 差异报告快照", "",
        "以下均为公开安全的模拟差异，用来证明报告不是只写“校验失败”。", "",
        "| 字段 | 预期值 | 实际值 | 差额 | 影响 | 建议处理 |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in snapshot["differences"]:
        lines.append(
            f"| {row['field_id']} | {row['expected_value']} | {row['actual_value']} | "
            f"{row['difference_value']} | {row['impact']} | {row['recommended_action']} |"
        )
    lines.extend([
        "", "每条记录还包含来源、公式、稳定记录标识和阻塞标志，可直接定位到处理步骤。",
        "私有业务项目的差异明细不会写入 tracked 文件。", "",
    ])
    return "\n".join(lines)


def _tests(manifest: dict[str, Any]) -> str:
    return f"""# S07-P1 测试结果

- 最终验证状态：`{manifest['evidence_validation_status']}`。
- 同一验证 Run receipts：{manifest['validation_receipt_count']}/{len(EXPECTED_VALIDATION_NAMES)}。
- 已覆盖 5 类字段、1 分失败、浮点金额拒绝、日期格式拒绝、四层勾稽、毛利率舍入和私有黄金范围回归。
- 已检查公开证据不含私有项目名、金额、来源定位或私有哈希。
"""


def _risks() -> str:
    return """# S07-P1 开放风险

- 128 项仍等待补充证据；不得把它们视为已解决，不得自动统一税口径。
- 当前黄金集合没有证明跨期样本；不得从本校验结果推广跨期结论。
- 当前私有黄金是项目汇总级权威数据。明细到分类的能力已由公开安全模拟案例验证；真实明细进入后仍须按相同门禁重新运行。
- 任何不可解释差异都会阻断后续阶段；本阶段不生成正式报告、不上传 GitHub、不重装 App。
"""


def _rollback() -> str:
    return """# S07-P1 回滚方案

- tracked 实现和证据可用本 Phase 的提交反向提交回滚。
- S06 已锁定的私有黄金版本和回归夹具不属于本阶段修改范围，不得覆盖或删除。
- 若公式或比较规则有误，只回滚 S07-P1，并在修正后重新生成完整验证记录；不得跳过 1 分差异门禁。
- Downloads 原始数据不属于本阶段写入或回滚范围。
"""


def expected_outputs() -> dict[Path, str]:
    projection = kernel.public_projection()
    receipts = final_receipts()
    manifest = _manifest(projection, receipts)
    snapshot = _difference_snapshot()
    return {
        CONTRACT_PATH: _dump(projection),
        MANIFEST_PATH: _dump(manifest),
        TASK_MATRIX_PATH: _dump(_task_matrix(bool(receipts))),
        FIELD_SUMMARY_PATH: _dump(_field_summary(projection)),
        RECONCILIATION_SUMMARY_PATH: _dump(_reconciliation_summary(projection)),
        DIFFERENCE_SNAPSHOT_PATH: _dump(snapshot),
        STATUS_PATH: _status(manifest),
        CROSS_REPORT_PATH: _cross_report(manifest),
        DIFFERENCE_REPORT_PATH: _difference_report(snapshot),
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
    parser = argparse.ArgumentParser(description="Build S07-P1 public-safe evidence")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.write:
        write_outputs()
        print("WROTE: S07-P1 public-safe evidence")
    else:
        check_outputs()
        print("PASS: S07-P1 public-safe evidence matches deterministic builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
