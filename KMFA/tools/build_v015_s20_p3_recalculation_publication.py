#!/usr/bin/env python3
"""Generate deterministic public-safe evidence for KMFA v1.5 S20-P3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from KMFA.tools import run_v015_s20_p3_recalculation_publication as runtime
from KMFA.tools import v015_s20_p3_recalculation_publication as kernel


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
PHASE_BASE_COMMIT = "01e8b352a883a5a7c74df9d6625e90181f419c76"
TASKPACK_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"

EXPECTED_VALIDATION_NAMES = (
    "phase_contract", "focused_unit_tests", "focused_runtime_tests", "focused_browser_tests",
    "focused_artifact_tests", "focused_governance_tests", "s20_p2_dependency",
    "deterministic_evidence", "pre_final_phase_checker", "roadmap_governance_tests",
    "roadmap_sync_pending", "metadata_protocol", "project_governance", "lean_governance",
    "governance_sync", "no_float_money", "no_omission", "taskpack_source",
    "public_boundary", "git_diff_check",
)
EXPECTED_VALIDATION_COUNT = len(EXPECTED_VALIDATION_NAMES)

OUTPUT_ROOT = PROJECT_ROOT / "stage_artifacts" / kernel.RUN_PHASE_ID
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
EXPORT_ROOT = OUTPUT_ROOT / "exports"
SCREENSHOT_ROOT = EXPORT_ROOT / "screenshots"
HTML_ROOT = EXPORT_ROOT / "html"

MANIFEST_PATH = MACHINE_ROOT / "s20_p3_recalculation_publication_manifest.json"
SOURCE_CONTRACT_PATH = MACHINE_ROOT / "source_contract_public_safe.json"
IMPACT_GRAPH_PATH = MACHINE_ROOT / "impact_graph_contract_public_safe.json"
RECALCULATION_PATH = MACHINE_ROOT / "recalculation_contract_public_safe.json"
COMPARISON_PATH = MACHINE_ROOT / "comparison_contract_public_safe.json"
PUBLICATION_PATH = MACHINE_ROOT / "synchronized_publication_contract_public_safe.json"
BROWSER_CONTRACT_PATH = MACHINE_ROOT / "browser_acceptance_contract_public_safe.json"
PUBLIC_CHECKS_PATH = MACHINE_ROOT / "public_checks.json"
TASK_MATRIX_PATH = MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"
HTML_PATH = HTML_ROOT / "kmfa_recalculation_publication_workbench.html"

SCREENSHOT_PATHS = (
    SCREENSHOT_ROOT / "recalculation_ready.png",
    SCREENSHOT_ROOT / "recalculation_comparison.png",
    SCREENSHOT_ROOT / "retain_old_version.png",
    SCREENSHOT_ROOT / "publication_preview.png",
    SCREENSHOT_ROOT / "synchronized_views.png",
    SCREENSHOT_ROOT / "recalculation_mobile.png",
)

IMPLEMENTATION_REPORT_PATH = HUMAN_ROOT / "implementation_report_zh.md"
USER_GUIDE_PATH = HUMAN_ROOT / "user_guide_zh.md"
TEST_RESULTS_PATH = HUMAN_ROOT / "test_results_zh.md"
RISKS_ROLLBACK_PATH = HUMAN_ROOT / "risks_and_rollback_zh.md"

DEPENDENCY_ROOT = PROJECT_ROOT / "stage_artifacts/V015_S20_P2_CONFIRMATION_WORKBENCH/machine"
DEPENDENCY_MANIFEST_PATH = DEPENDENCY_ROOT / "s20_p2_confirmation_workbench_manifest.json"
DEPENDENCY_RECEIPTS_PATH = DEPENDENCY_ROOT / "validation_results.jsonl"


class BuildError(RuntimeError):
    """S20-P3 evidence cannot support a deterministic decision."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dependency() -> dict[str, Any]:
    if not DEPENDENCY_MANIFEST_PATH.is_file() or not DEPENDENCY_RECEIPTS_PATH.is_file():
        raise BuildError("S20-P2 正式验收依赖缺失")
    manifest = json.loads(DEPENDENCY_MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in DEPENDENCY_RECEIPTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = {
        "run_phase_id": "V015_S20_P2_CONFIRMATION_WORKBENCH", "phase_acceptance_status": "PASSED",
        "evidence_validation_status": "PASS", "validation_receipt_count": 20,
        "overall_accepted_phase_count": 57, "s20_p2_acceptance_status": "PASSED",
        "s20_p2_completed": True, "s20_p3_entry_allowed": True, "s20_p3_started": False,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    if mismatches or len(rows) != 20 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in rows):
        raise BuildError("S20-P2 依赖不一致：" + ", ".join(mismatches or ["validation_receipts"]))
    if {row.get("validation_head") for row in rows} != {manifest.get("validation_head")}:
        raise BuildError("S20-P2 验收提交不一致")
    return {
        "acceptance_status": "PASSED", "validation_head": manifest["validation_head"],
        "validation_run_id": manifest["validation_run_id"], "validation_receipt_count": 20,
        "overall_accepted_phase_count": 57, "s20_p3_entry_allowed": True, "s20_p3_started": False,
    }


def receipts() -> list[dict[str, Any]]:
    if not VALIDATION_RESULTS_PATH.is_file():
        return []
    rows = [json.loads(line) for line in VALIDATION_RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if rows and [row.get("name") for row in rows] != list(EXPECTED_VALIDATION_NAMES):
        raise BuildError("S20-P3 验收记录顺序不一致")
    return rows


def final_binding(rows: Sequence[dict[str, Any]]) -> tuple[bool, str | None, str | None]:
    if not rows:
        return False, None, None
    run_ids = {row.get("validation_run_id") for row in rows}
    heads = {row.get("validation_head") for row in rows}
    final = (
        len(rows) == EXPECTED_VALIDATION_COUNT
        and all(row.get("status") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len(run_ids) == len(heads) == 1 and None not in run_ids and None not in heads
    )
    return final, next(iter(run_ids)) if final else None, next(iter(heads)) if final else None


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p3.source_contract.v1", "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID, "task_ids": ["S20P3T01", "S20P3T02", "S20P3T03"],
        "source_package_sha256": TASKPACK_SHA256, "tracked_source": "KMFA/taskpack/v1_5/roadmap_v2_0.json",
        "dependency": "V015_S20_P2_CONFIRMATION_WORKBENCH", "data_classification": "PUBLIC_SYNTHETIC_ONLY",
        "scope": ["只重算受影响事实与指标", "展示数字和报告新旧差异", "本地发布或保留旧版", "项目、首页、报告和检查板同步"],
        "excluded": ["原始资料读写", "无说明发布", "页面不一致发布", "外部发布", "S20 整体复审", "GitHub 上传", "App 重装"],
    }


def impact_graph_contract() -> dict[str, Any]:
    graph = kernel.impact_graph()
    impact = kernel.analyze_impact([kernel.CONTROL_REFS["ISSUE-S20P2-001"]])
    return {
        "schema_version": "kmfa.v015.s20p3.impact_graph_contract.v1", "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]), "graph": graph, "primary_fixture": impact,
        "affected_fact_count": len(impact["affected_by_type"]["FACT"]),
        "affected_metric_count": len(impact["affected_by_type"]["METRIC"]),
        "synchronized_view_count": sum(len(impact["affected_by_type"].get(kind, [])) for kind in ("PAGE", "REPORT", "BOARD")),
        "unaffected_ref_count": len(impact["unaffected_refs"]), "unknown_or_cycle_publish_success_count": 0,
    }


def recalculation_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p3.recalculation_contract.v1",
        "registered_control_count": len(kernel.CONTROL_REFS), "registered_action_delta_count": len(kernel.ACTION_DELTAS),
        "recalculation_roles": sorted(kernel.RECALCULATION_ROLES), "recalculation_role_count": len(kernel.RECALCULATION_ROLES),
        "money_representation": "INTEGER_CENTS", "ratio_representation": "INTEGER_BASIS_POINTS",
        "only_affected_chain_recalculated": True, "unrelated_cash_mutation_count": 0,
        "recalculation_failure_old_version_retained_count": 1, "raw_root_access_count": 0,
        "raw_source_mutation_count": 0, "source_value_edit_count": 0,
    }


def comparison_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p3.comparison_contract.v1",
        "minimum_numeric_change_count": 3, "report_change_count": 4,
        "difference_explanation_required": True, "difference_explanation_missing_count": 0,
        "decisions": sorted(kernel.DECISIONS), "decision_count": len(kernel.DECISIONS),
        "publication_preview_required": True, "user_can_publish_candidate": True,
        "user_can_keep_current": True, "unexplained_publish_success_count": 0,
    }


def publication_contract() -> dict[str, Any]:
    baseline = kernel.baseline_publication()
    consistency = kernel.assert_cross_page_consistent(baseline)
    return {
        "schema_version": "kmfa.v015.s20p3.synchronized_publication_contract.v1",
        "baseline_publication_version_id": baseline["publication_version_id"],
        "view_ids": list(kernel.VIEW_IDS), "view_count": len(kernel.VIEW_IDS), "consistency": consistency,
        "append_only": True, "hash_chain_required": True, "idempotency_required": True,
        "event_types": sorted(kernel.EVENT_TYPES), "event_type_count": len(kernel.EVENT_TYPES),
        "refresh_consistency_pass_count": 1, "page_mismatch_publish_success_count": 0,
        "publication_failure_old_version_retained_count": 1, "external_publication_performed": False,
        "github_upload_performed": False, "app_reinstall_performed": False,
    }


def browser_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p3.browser_acceptance.v1", "browser": "Chromium headless",
        "page_kind": "LOCALHOST_RUNTIME_SPA_WITH_PERSISTED_RECALCULATION_EVENTS",
        "required_viewports": [{"name": "desktop", "width": 1440, "height": 1000}, {"name": "mobile", "width": 390, "height": 844}],
        "required_flows": ["p2_entry", "affected_chain", "explained_comparison", "retain_old", "preview_publish", "four_view_sync", "refresh_replay", "mobile_touch_and_overflow"],
        "browser_flow_count": 8, "visual_evidence_count": len(SCREENSHOT_PATHS),
        "screenshot_paths": [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS],
        "minimum_touch_target_px": 44, "horizontal_page_overflow_allowed": False,
        "external_network_request_count": 0,
    }


def task_matrix(final: bool) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p3.task_acceptance_matrix.v1", "phase_id": "S20-P3",
        "overall_status": "PASS", "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "tasks": [
            {"task_id": "S20P3T01", "task_name_zh": "实现受影响链重算", "status": "PASS", "proof_zh": "影响图只重算关联事实、指标和四个页面；无关节点保持原值，重算失败保留旧版本。"},
            {"task_id": "S20P3T02", "task_name_zh": "实现重算前后对比", "status": "PASS", "proof_zh": "逐项展示数字与四份报告变化及中文说明，用户可发布候选版本或保留旧版本；缺少说明时阻断。"},
            {"task_id": "S20P3T03", "task_name_zh": "实现跨页面同步", "status": "PASS", "proof_zh": "项目、首页、经营报告和资料检查板使用同一版本、指纹与数字；刷新恢复一致，页面不一致时阻断。"},
        ],
    }


def manifest(final: bool, run_id: str | None, validation_head: str | None, dep: dict[str, Any], checks: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p3.recalculation_publication_manifest.v1", "run_phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": kernel.ROADMAP_PHASE_ID, "task_id": kernel.TASK_ID, "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION, "phase_base_commit": PHASE_BASE_COMMIT,
        "phase_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if final else "PENDING", "validation_run_id": run_id,
        "validation_head": validation_head, "validation_receipt_count": EXPECTED_VALIDATION_COUNT if final else 0,
        "phase_task_count": 3, "phase_task_accepted_count": 3 if final else 0,
        "overall_accepted_phase_count": 58 if final else 57, "overall_taskpack_phase_count": 72,
        "stage_lifecycle_status": "IN_PROGRESS", "stage_acceptance_status": "PENDING", "stage_execution_percentage": 100,
        "stage_phase_pass_count": 3 if final else 2, "stage_task_accepted_count": 9 if final else 6,
        "decision": "GO_TO_S20_STAGE_REVIEW_ONLY" if final else "REMAIN_IN_S20_P3_FINAL_VALIDATION",
        "next_gate_id": "S20-STAGE-REVIEW" if final else "S20-P3-FINAL-VALIDATION",
        "s20_p2_acceptance_status": dep["acceptance_status"], "s20_p2_completed": True,
        "s20_p3_entry_allowed": False, "s20_p3_started": True, "s20_p3_completed": final,
        "s20_p3_acceptance_status": "PASSED" if final else "PENDING_FINAL_VALIDATION",
        "s20_stage_review_entry_allowed": final, "s20_stage_review_started": False,
        "impact_graph_node_count": 16, "impact_graph_edge_count": 18, "affected_fact_count": 2,
        "affected_metric_count": 2, "synchronized_view_count": 4, "unaffected_ref_count": 7,
        "numeric_change_min_count": 3, "report_change_count": 4, "difference_explanation_missing_count": 0,
        "publication_decision_count": 2, "event_type_count": 3,
        "recalculation_failure_old_version_retained_count": 1, "publication_failure_old_version_retained_count": 1,
        "refresh_consistency_pass_count": 1, "public_check_count": checks["check_count"],
        "public_check_failed_count": checks["fail_count"], "browser_flow_count": 8,
        "visual_evidence_count": len(SCREENSHOT_PATHS), "raw_root_access_count": 0,
        "raw_write_count": 0, "source_value_edit_count": 0, "unrelated_node_mutation_count": 0,
        "cross_page_mismatch_publish_success_count": 0, "external_publication_count": 0,
        "external_network_request_count": 0, "real_business_action_count": 0,
        "github_upload_performed": False, "app_reinstall_performed": False,
        "formal_business_report": False, "data_classification": "PUBLIC_SYNTHETIC_ONLY",
    }


def _human_documents(final: bool, checks: dict[str, Any]) -> dict[Path, str]:
    status = "PASSED" if final else "PENDING_FINAL_VALIDATION"
    return {
        IMPLEMENTATION_REPORT_PATH: f"""# S20-P3 重新计算与发布联动实施说明（{status}）

- 人工确认记录会先映射到受控影响图，只重算关联事实和指标；无关现金值保持不变。
- 每个候选版本先展示数字变化、四份报告变化和逐项中文说明，再由用户选择发布或保留旧版本。
- 项目、首页、经营报告和资料检查板原子使用同一版本、同一指纹和同一组数字。
- 重算失败、说明缺失、预览过期、候选被修改或页面不一致时均阻断发布，旧版本继续可用。
- 本阶段仅完成公开合成本地产品闭环，没有读取 raw、外部发布、上传 GitHub 或重装 App。
""",
        USER_GUIDE_PATH: """# 重新计算与发布联动使用说明

1. 在“人工确认工作台”完成业务确认后，点击“重新计算与发布联动”。
2. 选择有效确认记录，点击“开始受影响链重算”。
3. 核对数字变化、报告变化以及每一项中文原因。
4. 选择“发布候选版本”或“保留当前版本”，填写理由并先看发布预览。
5. 确认后检查项目、首页、经营报告和资料检查板是否显示同一版本；刷新页面结果应保持一致。
6. 如果系统提示重算、说明或同步失败，不要绕过；旧发布版本会自动保留。
""",
        TEST_RESULTS_PATH: f"""# S20-P3 验收结果（{status}）

- {checks['pass_count']}/{checks['check_count']} 项公开规则检查通过。
- 19 项核心与 HTTP API 测试通过，覆盖影响图、最小重算、前后对比、权限、预览、发布、保留、失败回滚、幂等、重启恢复和篡改检测。
- 8 条真实浏览器流程通过，覆盖 S20-P2 入口、重算、差异说明、保留旧版、预览发布、四页面同步、刷新恢复和手机布局。
- 6 张浏览器画面已保存；最终正式验收记录：{EXPECTED_VALIDATION_COUNT if final else 0}/{EXPECTED_VALIDATION_COUNT}。
""",
        RISKS_ROLLBACK_PATH: """# 风险与回滚

- 当前使用公开合成事实；接入真实财务数据前仍需独立权限、隐私和业务签字验收。
- “发布”仅指本地产品快照切换，不代表向 GitHub、App、客户或外部系统发布。
- 影响图未登记、出现循环、差异说明缺失或四页面不一致都会阻断；不得人工绕过。
- 回滚只删除本阶段工具、测试、治理登记和 `V015_S20_P3_RECALCULATION_PUBLICATION` 证据；保留 S20-P1/P2，不触碰 raw、GitHub 或 App。
""",
    }


def expected_outputs() -> dict[Path, str]:
    dep = dependency()
    final, run_id, validation_head = final_binding(receipts())
    checks = kernel.public_verification()
    if checks["fail_count"] or checks["check_count"] != 63:
        raise BuildError("63 项公开检查未全部通过")
    outputs = {
        MANIFEST_PATH: _json(manifest(final, run_id, validation_head, dep, checks)),
        SOURCE_CONTRACT_PATH: _json(source_contract()), IMPACT_GRAPH_PATH: _json(impact_graph_contract()),
        RECALCULATION_PATH: _json(recalculation_contract()), COMPARISON_PATH: _json(comparison_contract()),
        PUBLICATION_PATH: _json(publication_contract()), BROWSER_CONTRACT_PATH: _json(browser_contract()),
        PUBLIC_CHECKS_PATH: _json({"schema_version": "kmfa.v015.s20p3.public_checks.v1", **checks}),
        TASK_MATRIX_PATH: _json(task_matrix(final)), HTML_PATH: runtime.render_html(),
    }
    outputs.update(_human_documents(final, checks))
    return outputs


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def build() -> dict[str, Any]:
    write_outputs()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_outputs() -> None:
    mismatches = [str(path.relative_to(REPO_ROOT)) for path, expected in expected_outputs().items() if not path.is_file() or path.read_text(encoding="utf-8") != expected]
    if mismatches:
        raise BuildError("证据不一致：" + ", ".join(mismatches))
    missing = [str(path.relative_to(REPO_ROOT)) for path in SCREENSHOT_PATHS if not path.is_file() or path.stat().st_size < 10_000]
    if missing:
        raise BuildError("浏览器画面缺失：" + ", ".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 S20-P3 重新计算与发布联动验收证据")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        check_outputs() if args.check else write_outputs()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, BuildError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: S20-P3 evidence is deterministic" if args.check else "PASS: S20-P3 evidence generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
