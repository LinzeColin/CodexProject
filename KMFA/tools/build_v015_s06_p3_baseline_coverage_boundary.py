#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S06-P3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import v015_s06_p3_baseline_coverage_boundary as kernel


OUTPUT_DIR = Path("KMFA/stage_artifacts/V015_S06_P3_BASELINE_COVERAGE_BOUNDARY")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "s06_p3_baseline_coverage_boundary_manifest.json"
TASK_MATRIX_PATH = MACHINE_DIR / "task_acceptance_matrix_public_safe.json"
RECEIPTS_PATH = MACHINE_DIR / "validation_results.jsonl"
CONTRACT_PATH = Path("KMFA/metadata/quality/v015_s06_p3_baseline_coverage_boundary_public_safe.json")
STATUS_PATH = HUMAN_DIR / "execution_status_zh.md"
QUEUE_PATH = HUMAN_DIR / "open_item_queue_summary_zh.md"
COVERAGE_PATH = HUMAN_DIR / "sample_coverage_report_zh.md"
TEST_PATH = HUMAN_DIR / "test_results_zh.md"
RISK_PATH = HUMAN_DIR / "open_risks_zh.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan_zh.md"

P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/machine/"
    "s06_p2_golden_baseline_lock_manifest.json"
)
P2_RECEIPTS_PATH = Path(
    "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/machine/validation_results.jsonl"
)

EXPECTED_VALIDATION_NAMES = (
    "S06-P3 kernel tests",
    "S06-P3 governance tests",
    "S06-P3 strict pre-final checker",
    "S06-P2 dependency checker",
    "roadmap governance sync tests",
    "governance consistency tests",
    "model registry tests",
    "formula registry tests",
    "parameter registry tests",
    "traceability tests",
    "no float money check",
    "public-safe boundary tests",
    "private mode and ignore check",
    "deterministic builder check",
    "python compile check",
    "targeted unittest discovery",
    "structured public diff check",
    "raw invariant check",
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
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise BuildError(f"JSONL objects required: {path}")
    return rows


def _dependency() -> dict[str, Any]:
    manifest = _json(P2_MANIFEST_PATH)
    receipts = _jsonl(P2_RECEIPTS_PATH)
    valid = (
        manifest.get("phase_id") == "V015_S06_P2_GOLDEN_BASELINE_LOCK"
        and manifest.get("phase_acceptance_status") == "PASSED"
        and manifest.get("decision") == "CONTINUE_TO_S06_P3_ONLY"
        and manifest.get("validation_receipt_count") == 20
        and len(receipts) == 20
        and all(row.get("status") == "PASS" for row in receipts)
        and len({row.get("validation_run_id") for row in receipts}) == 1
        and len({row.get("validation_head") for row in receipts}) == 1
    )
    if not valid:
        raise BuildError("S06-P2 dependency is not receipt-bound PASSED")
    return {
        "phase_id": manifest["phase_id"],
        "acceptance_status": manifest["phase_acceptance_status"],
        "receipt_count": len(receipts),
        "validation_run_id": receipts[0]["validation_run_id"],
        "validation_head": receipts[0]["validation_head"],
        "evidence_ref": "KMFA/stage_artifacts/V015_S06_P2_GOLDEN_BASELINE_LOCK/",
    }


def _final_receipts() -> list[dict[str, Any]]:
    receipts = _jsonl(RECEIPTS_PATH)
    if not receipts:
        return []
    if len(receipts) != len(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S06-P3 validation receipt count mismatch")
    if [row.get("name") for row in receipts] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S06-P3 validation receipt names/order mismatch")
    if any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in receipts):
        raise BuildError("S06-P3 validation receipt set contains failure")
    if len({row.get("validation_run_id") for row in receipts}) != 1:
        raise BuildError("S06-P3 receipts must share one run")
    if len({row.get("validation_head") for row in receipts}) != 1:
        raise BuildError("S06-P3 receipts must share one implementation HEAD")
    return receipts


def _task_matrix(projection: dict[str, Any], final: bool) -> dict[str, Any]:
    accepted = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    common = {
        "execution_status": "EXECUTION_COMPLETE",
        "acceptance_status": accepted,
        "private_evidence_only": True,
        "evidence_refs": [str(CONTRACT_PATH), str(MANIFEST_PATH)],
    }
    return {
        "schema_version": "kmfa.v015.s06p3.task_acceptance_matrix_public_safe.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID,
        "task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "tasks": [
            {
                **common, "task_id": "S06P3T01", "name": "标注无法确认项",
                "open_item_count": projection["open_item_count"],
                "impact_coverage_bps": projection["open_item_impact_coverage_bps"],
                "resolution_path_coverage_bps": projection["open_item_resolution_path_coverage_bps"],
                "guessing_used": False,
            },
            {
                **common, "task_id": "S06P3T02", "name": "建立回归夹具",
                "fixture_version_count": projection["fixture_version_count"],
                "fixture_project_count": projection["fixture_project_count"],
                "fixture_hash_recorded_private": True,
                "fixture_consistent_with_golden": True,
                "public_private_fixture_hash_count": 0,
            },
            {
                **common, "task_id": "S06P3T03", "name": "评估扩展样本需求",
                "required_scenario_count": projection["required_scenario_count"],
                "covered_scenario_count": projection["covered_scenario_count"],
                "missing_scenario_count": projection["missing_scenario_count"],
                "coverage_disposition_count": projection["coverage_disposition_count"],
                "future_sample_count": projection["future_sample_count"],
                "sample_expansion_required": projection["sample_expansion_required"],
                "empirical_coverage_complete": projection["empirical_coverage_complete"],
                "registered_gap_satisfies_stop_condition": projection["registered_gap_satisfies_stop_condition"],
                "downstream_cross_period_claim_allowed": projection["downstream_cross_period_claim_allowed"],
            },
        ],
    }


def _manifest(projection: dict[str, Any], dependency: dict[str, Any], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    final = bool(receipts)
    return {
        **projection,
        "schema_version": "kmfa.v015.s06p3.baseline_coverage_boundary_manifest.v1",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "dependency": dependency,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING",
        "validation_receipt_count": len(receipts),
        "validation_run_id": receipts[0]["validation_run_id"] if final else None,
        "validation_head": receipts[0]["validation_head"] if final else None,
        "task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if final else 0,
        "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2,
        "stage_task_accepted_count": 9 if final else 6,
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "decision": "CONTINUE_TO_S06_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S06_P3_PENDING_FINAL_VALIDATION",
        "s06_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s06_stage_review_entry_allowed": final,
        "s06_stage_review_started": False,
        "formal_report_generated": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }


def _status(manifest: dict[str, Any]) -> str:
    final = manifest["phase_acceptance_status"] == "PASSED"
    return f"""# v1.5 S06-P3 执行状态

- 本 Run 只完成 `S06-P3 基准覆盖与边界`，没有启动 S06 Stage 复审。
- 状态：`{manifest['phase_acceptance_status']}`；3 项任务已执行，验收通过 {manifest['task_accepted_count']}/3。
- 已把锁定黄金数据转成私有不可变回归夹具；夹具与黄金基准一致，金额误差 0 分。
- 已建立 {manifest['open_item_count']} 项私有队列，每项都有影响与解决路径，全程没有猜测补齐。
- 五类样本场景覆盖 4 类；跨期场景未被当前基准证明，已登记 1 个后续补样本项。
- 本 Phase 的通过依据是“4 类已有证据 + 1 类按停止条件登记后续样本”，不是 5/5 类经验覆盖；禁止据此作跨期结论。
- 128 项待证据事项不得视为已解决；税口径不得被擅自标准化。
- S06 Stage 执行进度 100%，Stage 仍为 `IN_PROGRESS/PENDING`，等待下一轮独立复审。
- Stage review 入口/已启动：`{str(final).lower()}/false`。
- GitHub upload / App reinstall：`false / false`。
"""


def _queue(manifest: dict[str, Any]) -> str:
    counts = manifest["open_item_category_counts"]
    status = manifest["open_item_status_counts"]
    return f"""# 无法确认项队列摘要

公开文件只提供汇总，不含项目名、金额、原文、定位或私有哈希。

| 分类 | 数量 | 处理原则 |
|---|---:|---|
| 缺失 | {counts['MISSING']} | 税口径未说明；后续取得授权依据时追加黄金版本 |
| 模糊 | {counts['AMBIGUOUS']} | 无法精确绑定项目；禁止猜测，等待授权绑定或明确排除 |
| 冲突 | {counts['CONFLICT']} | 已按确认合同额与总成本精确派生，不采用冲突展示值 |
| 不适用 | {counts['NOT_APPLICABLE']} | 保持排除，除非新黄金版本改变权威字段 |

- 待后续证据：{status['OPEN']} 项。
- 已路由为精确派生：{status['ROUTED_DERIVATION']} 项。
- 已路由为明确排除：{status['ROUTED_EXCLUSION']} 项。
- 影响说明覆盖率：100%；解决路径覆盖率：100%；猜测补齐：否。
"""


def _coverage(manifest: dict[str, Any]) -> str:
    labels = {
        "PROFITABLE": "盈利项目", "LOSS": "亏损项目",
        "ZERO_OR_NEGATIVE_COST": "零或负成本结构", "CROSS_PERIOD": "跨期项目",
        "CONFLICT_TEMPLATE": "冲突模板",
    }
    lines = [
        "# 样本覆盖报告", "",
        "| 场景 | 状态 | 证据数量 |", "|---|---|---:|",
    ]
    for row in manifest["coverage_matrix"]:
        lines.append(f"| {labels[row['scenario']]} | {row['status']} | {row['evidence_count']} |")
    lines.extend([
        "", "结论：当前黄金集合能证明盈利、亏损、零成本和冲突模板场景。",
        "跨期场景没有可验证字段，因此没有被擅自判定为已覆盖；已登记后续补样本。",
        "Task Pack 的停止条件允许把缺口登记为后续样本，因此本 Phase 可验收；这不代表 5/5 类已有经验覆盖。",
        "跨期结论继续保持禁止，直至取得可验证的授权样本并追加新黄金版本。", "",
    ])
    return "\n".join(lines)


def _tests(manifest: dict[str, Any]) -> str:
    return f"""# S06-P3 测试结果

- 最终验证状态：`{manifest['evidence_validation_status']}`。
- 同一验证 Run receipts：{manifest['validation_receipt_count']}/{len(EXPECTED_VALIDATION_NAMES)}。
- 私有夹具哈希已记录并复验，但未进入公开文件。
- 黄金一致性、队列完整性、样本矩阵、私有权限、公开泄漏和 raw 不变式均纳入验证。
"""


def _risks(manifest: dict[str, Any]) -> str:
    return """# S06-P3 开放风险

- `S06P3-RISK-001`：当前黄金集合缺少可验证的跨期项目字段。状态=`REGISTERED_FOLLOW_UP`；下一步是在授权来源扩展时追加新黄金版本与新夹具版本。
- 128 项仍等待补充证据，其中 82 项为税口径未说明，46 项为跨来源项目绑定模糊。它们均有解决路径，且没有被猜测写入黄金基准。
- 硬边界：不得把待证据事项标为已解决，不得擅自统一税口径，不得从当前样本推广跨期结论。
- S06 Stage 尚未复审；本 Run 不生成正式报告、不上传 GitHub、不重装 App。
"""


def _rollback() -> str:
    return """# S06-P3 回滚方案

- tracked 产物可用本 Phase commit 反向提交回滚。
- private regression fixture 是一次写入且与 S06-P2 黄金记录绑定；发现不一致时停止，不覆盖原夹具。
- 基准业务修正必须在 S06-P2 规则下追加黄金版本，再创建新的夹具版本；不得修改既有黄金记录或夹具。
- raw inbox 不属于本 Phase 的写入或回滚范围。
"""


def expected_outputs() -> dict[Path, str]:
    projection = kernel.current_public_projection()
    receipts = _final_receipts()
    manifest = _manifest(projection, _dependency(), receipts)
    return {
        CONTRACT_PATH: _dump(projection),
        MANIFEST_PATH: _dump(manifest),
        TASK_MATRIX_PATH: _dump(_task_matrix(projection, bool(receipts))),
        STATUS_PATH: _status(manifest),
        QUEUE_PATH: _queue(manifest),
        COVERAGE_PATH: _coverage(manifest),
        TEST_PATH: _tests(manifest),
        RISK_PATH: _risks(manifest),
        ROLLBACK_PATH: _rollback(),
    }


def write_outputs() -> None:
    for path, content in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs() -> None:
    errors = [str(path) for path, content in expected_outputs().items()
              if not path.is_file() or path.read_text(encoding="utf-8") != content]
    if errors:
        raise BuildError("deterministic output mismatch: " + ", ".join(errors))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build S06-P3 public-safe evidence")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.write:
        write_outputs()
        print("WROTE: S06-P3 public-safe evidence")
    else:
        check_outputs()
        print("PASS: S06-P3 public-safe evidence matches deterministic builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
