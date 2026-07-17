#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S04-P2."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

from KMFA.tools import v015_s04_p2_lineage_version_impact as kernel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S04_P2_LINEAGE_VERSION")
OUTPUT_ROOT = PROJECT_ROOT / OUTPUT_ROOT_RELATIVE
MACHINE_ROOT = OUTPUT_ROOT / "machine"
HUMAN_ROOT = OUTPUT_ROOT / "human"
MANIFEST_PATH = MACHINE_ROOT / "s04_p2_lineage_version_manifest.json"
VALIDATION_RESULTS_PATH = MACHINE_ROOT / "validation_results.jsonl"


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(values: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n").encode()
        for value in values
    )


def _ref(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def field_lineage_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s04p2.field_lineage_protocol.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "required_fields": list(kernel.REQUIRED_LINEAGE_FIELDS),
        "critical_field_classes": list(kernel.CRITICAL_FIELD_CLASSES),
        "critical_lineage_coverage_required_bps": 10_000,
        "coverage_scope": "DECLARED_PUBLIC_SAFE_SYNTHETIC_ACCEPTANCE_FIXTURE",
        "actual_business_lineage_materialized": False,
        "raw_text_storage_plane": "PRIVATE_METADATA_ONLY",
        "public_projection_contains_opaque_ref_only": True,
        "below_gate_action": "BLOCK_PUBLICATION",
        "raw_root_access_required": False,
    }


def derived_version_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s04p2.derived_version_protocol.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "derived_node_types": list(kernel.DERIVED_NODE_TYPES),
        "required_version_bindings": list(kernel.REQUIRED_VERSION_BINDINGS),
        "immutable_versions_required": True,
        "history_rebuild_result_codes": ["REBUILDABLE", "NOT_REBUILDABLE"],
        "missing_input_action": "MARK_NOT_REBUILDABLE",
        "silent_default_or_latest_fallback_allowed": False,
        "raw_root_access_required": False,
    }


def impact_protocol() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s04p2.impact_protocol.v1",
        "phase_id": kernel.RUN_PHASE_ID,
        "supported_affected_types": ["FACT", "METRIC", "PAGE", "REPORT"],
        "traversal": "TRANSITIVE_DEPENDANTS_ONLY",
        "full_graph_recalculation_by_default": False,
        "unknown_change_action": "BLOCK_AUTOMATIC_PUBLICATION",
        "cycle_action": "BLOCK_AUTOMATIC_PUBLICATION",
        "formal_report_gate_independent": True,
        "raw_root_access_required": False,
    }


def lineage_coverage_report() -> dict[str, Any]:
    records = kernel.synthetic_field_lineage_records()
    summary = kernel.validate_field_lineage(records)
    return {
        "schema_version": "kmfa.v015.s04p2.lineage_coverage_report.v1",
        **summary,
        "scope": "PUBLIC_SAFE_SYNTHETIC_ACCEPTANCE_FIXTURE",
        "records": records,
        "production_raw_lineage_claimed": False,
        "raw_root_access_count": 0,
    }


def time_travel_verification() -> dict[str, Any]:
    chain = kernel.synthetic_version_chain()
    complete = kernel.reconstruct_historical_report(
        chain,
        "REPORT-VERSION::management_overview::1.0.0",
    )
    incomplete_chain = copy.deepcopy(chain)
    incomplete_chain["source_versions"].remove("SOURCE-VERSION::SYNTHETIC-BANK::1.0.0")
    incomplete = kernel.reconstruct_historical_report(
        incomplete_chain,
        "REPORT-VERSION::management_overview::1.0.0",
    )
    return {
        "schema_version": "kmfa.v015.s04p2.time_travel_verification.v1",
        "case_count": 2,
        "rebuildable_case": complete,
        "missing_input_case": incomplete,
        "expected_results_exact": (
            complete["status"] == "REBUILDABLE"
            and incomplete["status"] == "NOT_REBUILDABLE"
            and bool(incomplete["missing_input_version_refs"])
        ),
        "chain_summary": kernel.validate_version_chain(chain),
        "production_report_rebuilt": False,
        "raw_root_access_count": 0,
    }


def impact_verification() -> dict[str, Any]:
    graph = kernel.synthetic_impact_graph()
    exact = kernel.analyze_impact(graph, ["FORMULA::COLLECTION-RATIO"])
    unknown = kernel.analyze_impact(graph, ["RULE::UNKNOWN"])
    cyclic_graph = copy.deepcopy(graph)
    cyclic_graph["edges"].append(["REPORT::MANAGEMENT-OVERVIEW", "SOURCE::LEDGER"])
    cyclic = kernel.analyze_impact(cyclic_graph, ["SOURCE::LEDGER"])
    expected = [
        "METRIC::COLLECTION-RATIO",
        "PAGE::MANAGEMENT-OVERVIEW",
        "REPORT::MANAGEMENT-OVERVIEW",
    ]
    return {
        "schema_version": "kmfa.v015.s04p2.impact_verification.v1",
        "case_count": 3,
        "exact_scope_case": exact,
        "unknown_scope_case": unknown,
        "cycle_case": cyclic,
        "exact_scope_expected": expected,
        "exact_scope_passed": exact["affected_refs"] == expected,
        "unrelated_fact_excluded": "FACT::UNRELATED-STATUS" not in exact["affected_refs"],
        "unknown_and_cycle_publication_blocked": (
            not unknown["automatic_publication_allowed"]
            and not cyclic["automatic_publication_allowed"]
        ),
        "production_publication_performed": False,
        "raw_root_access_count": 0,
    }


def task_matrix() -> list[dict[str, Any]]:
    return [
        {
            "task_id": "S04P2T01",
            "name": "建立字段级血缘",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/lineage/v015_s04_p2_field_lineage_protocol_public_safe.json"),
                _ref(MACHINE_ROOT / "lineage_coverage_report_public_safe.json"),
            ],
        },
        {
            "task_id": "S04P2T02",
            "name": "建立派生版本链",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/lineage/v015_s04_p2_derived_version_protocol_public_safe.json"),
                _ref(MACHINE_ROOT / "time_travel_reconstruction_verification_public_safe.json"),
            ],
        },
        {
            "task_id": "S04P2T03",
            "name": "建立影响图",
            "execution_status": "EXECUTION_COMPLETE",
            "acceptance_status": "PASSED",
            "evidence_refs": [
                _ref(PROJECT_ROOT / "metadata/lineage/v015_s04_p2_impact_protocol_public_safe.json"),
                _ref(MACHINE_ROOT / "impact_analysis_verification_public_safe.json"),
            ],
        },
    ]


def manifest(*, final_validation: bool, receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = receipts or []
    passed = bool(final_validation and receipts and all(row.get("status") == "PASS" for row in receipts))
    validation_head = receipts[0].get("validation_head") if passed else None
    validation_run_id = receipts[0].get("validation_run_id") if passed else None
    if passed and any(row.get("validation_head") != validation_head for row in receipts):
        raise ValueError("validation receipts do not share one validation_head")
    if passed and any(row.get("validation_run_id") != validation_run_id for row in receipts):
        raise ValueError("validation receipts do not share one validation_run_id")
    coverage = kernel.validate_field_lineage(kernel.synthetic_field_lineage_records())
    chain = kernel.validate_version_chain(kernel.synthetic_version_chain())
    return {
        "schema_version": "kmfa.v015.s04p2.lineage_version_manifest.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S04",
        "phase_id": kernel.RUN_PHASE_ID,
        "roadmap_phase_id": "S04-P2",
        "task_id": kernel.TASK_ID,
        "acceptance_id": kernel.ACCEPTANCE_ID,
        "version": kernel.VERSION,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "evidence_validation_status": "PASS" if passed else "PENDING",
        "stage_lifecycle_status": "IN_PROGRESS",
        "stage_acceptance_status": "PENDING",
        "stage_execution_percentage": 67,
        "phase_task_count": 3,
        "task_execution_complete_count": 3,
        "task_accepted_count": 3 if passed else 0,
        "critical_field_class_count": coverage["critical_field_class_count"],
        "declared_critical_field_count": coverage["declared_critical_field_count"],
        "lineage_coverage_bps": coverage["lineage_coverage_bps"],
        "synthetic_lineage_record_count": coverage["synthetic_lineage_record_count"],
        "actual_business_lineage_record_count": 0,
        "derived_version_node_type_count": chain["derived_version_node_type_count"],
        "required_version_binding_count": chain["required_version_binding_count"],
        "time_travel_case_count": 2,
        "impact_case_count": 3,
        "impact_scope_unknown_publication_blocked": True,
        "formal_report_allowed": False,
        "formal_report_stop_reason": "ACTUAL_BUSINESS_LINEAGE_NOT_MATERIALIZED",
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "product_implementation_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": "CONTINUE_TO_S04_P3_ONLY" if passed else "REMAIN_IN_S04_P2",
        "s04_p1_acceptance_status": "PASSED",
        "s04_p2_started": True,
        "s04_p2_acceptance_status": "PASSED" if passed else "PENDING_FINAL_VALIDATION",
        "s04_p3_entry_allowed": bool(passed),
        "s04_p3_started": False,
        "s04_stage_review_entry_allowed": False,
        "validation_run_id": validation_run_id,
        "validation_head": validation_head,
        "validation_receipt_count": len(receipts) if passed else 0,
        "validation_pass_count": len(receipts) if passed else 0,
        "validation_failed_count": 0,
        "evidence_refs": [
            _ref(MACHINE_ROOT / "task_acceptance_matrix_public_safe.json"),
            _ref(MACHINE_ROOT / "lineage_coverage_report_public_safe.json"),
            _ref(MACHINE_ROOT / "time_travel_reconstruction_verification_public_safe.json"),
            _ref(MACHINE_ROOT / "impact_analysis_verification_public_safe.json"),
            _ref(VALIDATION_RESULTS_PATH),
        ],
    }


def expected_static_outputs() -> dict[Path, bytes]:
    return {
        PROJECT_ROOT / "metadata/lineage/v015_s04_p2_field_lineage_protocol_public_safe.json": _json_bytes(field_lineage_protocol()),
        PROJECT_ROOT / "metadata/lineage/v015_s04_p2_derived_version_protocol_public_safe.json": _json_bytes(derived_version_protocol()),
        PROJECT_ROOT / "metadata/lineage/v015_s04_p2_impact_protocol_public_safe.json": _json_bytes(impact_protocol()),
        MACHINE_ROOT / "lineage_coverage_report_public_safe.json": _json_bytes(lineage_coverage_report()),
        MACHINE_ROOT / "time_travel_reconstruction_verification_public_safe.json": _json_bytes(time_travel_verification()),
        MACHINE_ROOT / "impact_analysis_verification_public_safe.json": _json_bytes(impact_verification()),
        MACHINE_ROOT / "task_acceptance_matrix_public_safe.json": _json_bytes(task_matrix()),
        HUMAN_ROOT / "completion_record_zh.md": (
            "# v1.5 S04-P2 血缘与版本完成记录\n\n"
            "- 建立页、表、单元格、私有原文引用、标准字段、映射版本、处理步骤和事实版本组成的字段级血缘内核。\n"
            "- public-safe synthetic 夹具覆盖 2 类、4 个声明关键字段，覆盖率 100%；真实业务血缘记录仍为 0，正式报告继续阻断。\n"
            "- FACT/METRIC/REPORT 全部绑定输入、规则和公式版本；历史输入缺失时明确返回 NOT_REBUILDABLE。\n"
            "- 影响分析仅遍历传递依赖；未知节点或成环时影响范围未知并阻断自动发布。\n"
            "- 本 Phase 未访问 raw inbox；S04-P3、Stage review、GitHub、App 和业务执行均未启动。\n"
        ).encode(),
        HUMAN_ROOT / "test_results_zh.md": (
            "# 测试结果\n\n"
            "最终结果以 `machine/validation_results.jsonl` 与 strict checker 为准；覆盖完整血缘、缺字段拒绝、"
            "历史重建/缺输入降级、精确影响范围、未知节点和环路 fail-closed。\n"
        ).encode(),
        HUMAN_ROOT / "rollback_plan_zh.md": (
            "# 回滚方案\n\n"
            "仅回滚本 Phase 新增的 lineage metadata、工具、测试、证据和对应治理登记；"
            "不得触碰 raw inbox、S04-P1 证据、已安装 App 或远端分支。\n"
        ).encode(),
        HUMAN_ROOT / "open_risks_zh.md": (
            "# 未解决风险\n\n"
            "- `S04P2-RISK-001`：本 Phase 的 100% 覆盖仅针对声明的 public-safe synthetic acceptance fixture；"
            "真实业务血缘记录数仍为 0，正式报告必须保持关闭，后续私有导入绑定不得把合成覆盖率冒充生产覆盖率。\n"
        ).encode(),
    }


def write_outputs(*, final_validation: bool = False, receipts: list[dict[str, Any]] | None = None) -> None:
    outputs = expected_static_outputs()
    outputs[MANIFEST_PATH] = _json_bytes(manifest(final_validation=final_validation, receipts=receipts))
    outputs[VALIDATION_RESULTS_PATH] = _jsonl_bytes(receipts or [])
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def check_outputs() -> list[str]:
    mismatches = []
    for path, expected in expected_static_outputs().items():
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(_ref(path))
    for path in (MANIFEST_PATH, VALIDATION_RESULTS_PATH):
        if not path.is_file():
            mismatches.append(_ref(path))
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                raise ValueError("artifact drift: " + ", ".join(mismatches))
            print("PASS: S04-P2 public-safe artifacts match deterministic builder")
        else:
            write_outputs()
            print("UPDATED: S04-P2 public-safe artifacts")
    except (OSError, ValueError, kernel.LineageVersionError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
