#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S02-P2.

This phase materializes planning traceability only.  It never reads the raw
business inbox, enables product formulas, performs a full lineage check, or
authorizes product/report/business execution.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence
from zipfile import ZipFile

from KMFA.tools.v015_s02_p2_formula_trace import (
    build_formula_trace,
    build_parameter_trace,
    validate_formula_parameter_trace,
)
from KMFA.tools.v015_s02_p2_lineage_contract import (
    build_lineage_contract_payload,
    count_actual_lineage_records,
    parse_source_domain_csv,
    validate_lineage_contract_payload,
)
from KMFA.tools.v015_s02_p2_requirement_trace import (
    TRACE_COLUMNS,
    build_requirement_task_trace,
    validate_requirement_task_trace,
)


SOURCE_PACKAGE_NAME = (
    "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
)
SOURCE_PACKAGE_SHA256 = (
    "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
)
SOURCE_DOMAIN_MEMBER_SHA256 = (
    "40704635a8725b55de0ebf164eb94cdb9686d88e3e0111b28b7087d73089c53a"
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME
OUTPUT_ROOT_RELATIVE = Path(
    "stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY"
)
P1_MACHINE_RELATIVE = Path(
    "stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine"
)

REQUIREMENT_RELATIVE = Path("machine/requirement_task_traceability_public_safe.csv")
LINEAGE_RELATIVE = Path("machine/data_report_lineage_field_contract_public_safe.json")
EDGE_RELATIVE = Path("machine/lineage_layer_edge_contract_public_safe.csv")
SOURCE_DOMAIN_RELATIVE = Path("machine/source_domain_lineage_coverage_public_safe.csv")
FORMULA_RELATIVE = Path("machine/formula_test_traceability_public_safe.csv")
PARAMETER_RELATIVE = Path("machine/formula_parameter_traceability_public_safe.csv")
SUMMARY_RELATIVE = Path("human/end_to_end_traceability_zh.md")
MANIFEST_RELATIVE = Path("machine/s02_p2_end_to_end_traceability_manifest.json")

FINAL_ARTIFACT_REFS = {
    "manifest": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/s02_p2_end_to_end_traceability_manifest.json",
    "requirement_trace": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/requirement_task_traceability_public_safe.csv",
    "lineage_contract": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/data_report_lineage_field_contract_public_safe.json",
    "lineage_edges": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/lineage_layer_edge_contract_public_safe.csv",
    "source_domain_coverage": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/source_domain_lineage_coverage_public_safe.csv",
    "formula_trace": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/formula_test_traceability_public_safe.csv",
    "parameter_trace": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/formula_parameter_traceability_public_safe.csv",
    "traceability_summary": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/human/end_to_end_traceability_zh.md",
    "completion_record": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/human/completion_record_zh.md",
    "rollback_plan": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/human/rollback_plan_zh.md",
    "test_results": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/human/test_results_zh.md",
    "validation_results": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/validation_results.jsonl",
}


class BuildError(RuntimeError):
    """Raised when S02-P2 public-safe core evidence cannot be built."""


_EMAIL_RE = re.compile(
    rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def _normalize_project_root(project_root: Optional[Path]) -> Path:
    root = PROJECT_ROOT if project_root is None else Path(project_root).resolve()
    if (root / "stage_artifacts").is_dir() and (root / "tools").is_dir():
        return root
    nested = root / "KMFA"
    if (nested / "stage_artifacts").is_dir() and (nested / "tools").is_dir():
        return nested
    raise BuildError(f"KMFA project root not found: {root}")


def _csv_bytes(headers: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(headers),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        serialized = {
            key: (
                json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                if isinstance(value, (list, dict, bool))
                else value
            )
            for key, value in row.items()
        }
        writer.writerow(serialized)
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _content_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + _sha256_bytes(encoded)


def _summary_markdown(
    requirement_rows: Sequence[Mapping[str, Any]],
    lineage: Mapping[str, Any],
    formula_rows: Sequence[Mapping[str, Any]],
    parameter_rows: Sequence[Mapping[str, Any]],
) -> bytes:
    mapping_origins: dict[str, int] = {}
    for row in requirement_rows:
        key = str(row["mapping_origin"])
        mapping_origins[key] = mapping_origins.get(key, 0) + 1
    raw_statuses: dict[str, int] = {}
    for row in formula_rows:
        key = str(row["raw_status"])
        raw_statuses[key] = raw_statuses.get(key, 0) + 1
    actual_count = int(lineage["actual_lineage_record_count"])
    lines = [
        "# KMFA v1.5 S02-P2 全链路追溯规划",
        "",
        "## 结论",
        "",
        f"- 需求：55 项，规范化 requirement→Task 绑定 {len(requirement_rows)} 行；"
        f"source explicit={mapping_origins.get('SOURCE_EXPLICIT', 0)}，"
        f"受控 Stage 闭包={mapping_origins.get('S02_P2_STAGE_CLOSURE_DECISION', 0)}。",
        "- `R017→S11P2T01`、`R023→S21P1T02` 只作为受控补充边；"
        "原始需求矩阵保持不变。P0/P1 requirement 与 primary Stage 闭包均为 100%。",
        f"- lineage：仅建立合同；actual lineage rows={actual_count}，"
        "`lineage_full_check_complete=false`，不得发布正式报告或作为业务决策依据。",
        f"- 公式/模型：{len(formula_rows)} 项，source status={raw_statuses}；"
        f"参数/阈值规划：{len(parameter_rows)} 项。所有 runtime enablement=false。",
        "- 本 Phase 没有读取 raw、选择技术栈、实现 runtime/API/DB/UI、执行业务动作、"
        "上传 GitHub 或重装 App。",
        "",
        "## 三条追溯链",
        "",
        "1. 需求→Stage/Phase/Task：每个绑定沿用 Roadmap Task 的 action、output、evidence、"
        "acceptance、stop 合同；概念维度映射均标记 `CONTROLLED_S02_P2_DERIVATION`。",
        "2. 数据→报告：合同固定 L0→L6 主链与 L7 控制边，但当前 tracked lineage 只有"
        " protocol headers，不得声称实例血缘完成。",
        "3. 公式/参数→测试/报告：fixture/report refs 是规划绑定，不是可执行夹具或产品证据；"
        "source-less、test-less、unknown-default 或 legacy-active 继承均不得启用。",
        "",
        "## 下一门禁",
        "",
        "S02-P2 验收通过后仅开放下一独立 Run 的 S02-P3；S02 Stage 仍为"
        " `IN_PROGRESS / PENDING`。",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def _assert_public_safe(outputs: Mapping[Path, bytes]) -> None:
    forbidden = (
        b"/Users/",
        b"/Volumes/",
        b"/private/",
        b"/tmp/",
        b"KMFA_MetaData",
        b"OWNER_NOTIFICATION_EMAIL_TOKEN@",
    )
    for path, payload in outputs.items():
        for token in forbidden:
            if token in payload:
                raise BuildError(
                    f"public-safe token violation in {path}: {token!r}"
                )
        if _EMAIL_RE.search(payload):
            raise BuildError(f"email leaked into public-safe output: {path}")


def _source_domain_rows_from_package(package: Path) -> list[dict[str, Any]]:
    with ZipFile(package) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.rsplit("/", 1)[-1].startswith("09_") and name.endswith(".csv")
        ]
        if len(names) != 1:
            raise BuildError(f"source-domain member count mismatch: {len(names)}")
        payload = archive.read(names[0])
    if _sha256_bytes(payload) != SOURCE_DOMAIN_MEMBER_SHA256:
        raise BuildError("source-domain member hash drift")
    return parse_source_domain_csv(payload)


def _tracked_actual_lineage_count(root: Path) -> int:
    total = 0
    for name in ("field_lineage.jsonl", "metric_lineage.jsonl", "report_lineage.jsonl"):
        path = root / "metadata/lineage" / name
        if not path.is_file():
            raise BuildError(f"tracked lineage register missing: {path}")
        rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise BuildError(f"tracked lineage row must be an object: {path}:{line_number}")
            rows.append(value)
        total += count_actual_lineage_records(rows)
    return total


def expected_core_outputs(
    project_root: Optional[Path] = None,
    source_package: Optional[Path] = None,
    output_root: Optional[Path] = None,
) -> dict[Path, bytes]:
    """Return deterministic absolute output paths and their exact bytes."""

    root = _normalize_project_root(project_root)
    package = DEFAULT_SOURCE_PACKAGE if source_package is None else Path(source_package)
    destination = (
        root / OUTPUT_ROOT_RELATIVE
        if output_root is None
        else Path(output_root).resolve()
    )
    p1_machine = root / P1_MACHINE_RELATIVE

    requirement_rows = build_requirement_task_trace(
        package,
        p1_machine / "requirements_ledger_public_safe.csv",
        p1_machine / "business_line_matrix_public_safe.csv",
    )
    requirement_errors = validate_requirement_task_trace(requirement_rows)
    if requirement_errors:
        raise BuildError("requirement trace invalid: " + "; ".join(requirement_errors))

    actual_lineage_count = _tracked_actual_lineage_count(root)
    if actual_lineage_count != 0:
        raise BuildError(
            "S02-P2 planning contract requires the tracked actual lineage count "
            f"to remain 0; observed {actual_lineage_count}"
        )
    lineage = build_lineage_contract_payload(
        source_domain_rows=_source_domain_rows_from_package(package)
    )
    validate_lineage_contract_payload(lineage)

    formula_rows = build_formula_trace(package)
    parameter_rows = build_parameter_trace(package)
    formula_errors = validate_formula_parameter_trace(
        formula_rows, parameter_rows, source_package=package
    )
    if formula_errors:
        raise BuildError("formula trace invalid: " + "; ".join(formula_errors))

    edge_rows = lineage["layer_edge_contract"]
    source_domain_rows = lineage["source_domain_coverage"]
    if not edge_rows or not source_domain_rows or not formula_rows or not parameter_rows:
        raise BuildError("one or more S02-P2 core tables are empty")

    outputs = {
        destination / REQUIREMENT_RELATIVE: _csv_bytes(
            TRACE_COLUMNS, requirement_rows
        ),
        destination / LINEAGE_RELATIVE: _json_bytes(lineage),
        destination / EDGE_RELATIVE: _csv_bytes(
            list(edge_rows[0]), edge_rows
        ),
        destination / SOURCE_DOMAIN_RELATIVE: _csv_bytes(
            list(source_domain_rows[0]), source_domain_rows
        ),
        destination / FORMULA_RELATIVE: _csv_bytes(
            list(formula_rows[0]), formula_rows
        ),
        destination / PARAMETER_RELATIVE: _csv_bytes(
            list(parameter_rows[0]), parameter_rows
        ),
        destination / SUMMARY_RELATIVE: _summary_markdown(
            requirement_rows, lineage, formula_rows, parameter_rows
        ),
    }
    _assert_public_safe(outputs)
    return outputs


def build_final_manifest(
    *,
    generated_at: str,
    project_root: Optional[Path] = None,
    source_package: Optional[Path] = None,
) -> dict[str, Any]:
    """Build the final manifest after all non-self artifacts exist."""

    if not generated_at or "+" not in generated_at:
        raise BuildError("generated_at must be an offset-aware ISO-8601 value")
    root = _normalize_project_root(project_root)
    package = DEFAULT_SOURCE_PACKAGE if source_package is None else Path(source_package)
    package_payload = package.read_bytes()
    if _sha256_bytes(package_payload) != SOURCE_PACKAGE_SHA256:
        raise BuildError("source package hash drift")

    p1_path = (
        root
        / "stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/s02_p1_requirements_scope_lock_manifest.json"
    )
    p1_payload = p1_path.read_bytes()
    p1 = json.loads(p1_payload)
    artifact_integrity: list[dict[str, Any]] = []
    for key, ref in FINAL_ARTIFACT_REFS.items():
        if key == "manifest":
            continue
        path = root.parent / ref
        if not path.is_file():
            raise BuildError(f"final artifact missing: {ref}")
        payload = path.read_bytes()
        artifact_integrity.append(
            {"ref": ref, "bytes": len(payload), "sha256": _sha256_bytes(payload)}
        )

    manifest: dict[str, Any] = {
        "schema_version": "kmfa.v015.s02_p2_end_to_end_traceability.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S02",
        "roadmap_phase_id": "S02-P2",
        "run_phase_id": "V015_S02_P2_END_TO_END_TRACEABILITY",
        "task_id": "KMFA-V015-S02-P2-END-TO-END-TRACEABILITY-20260713",
        "acceptance_id": "ACC-KMFA-V015-S02-P2-END-TO-END-TRACEABILITY",
        "generated_at": generated_at,
        "run_mode": "IMPLEMENT",
        "work_kind": "END_TO_END_TRACEABILITY_PLANNING",
        "phase_base_commit": "1de399f35d1c0d2b7ee1ea6451c2be8d1c49a861",
        "source_package": {
            "name": SOURCE_PACKAGE_NAME,
            "bytes": len(package_payload),
            "sha256": SOURCE_PACKAGE_SHA256,
            "stage_count": 24,
            "phase_count": 72,
            "task_count": 216,
            "requirement_count": 55,
        },
        "dependency_evidence": {
            "count": 1,
            "dependencies": [
                {
                    "dependency_id": "s02_p1_requirements_scope_lock",
                    "ref": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/s02_p1_requirements_scope_lock_manifest.json",
                    "bytes": len(p1_payload),
                    "sha256": _sha256_bytes(p1_payload),
                    "content_hash": p1["content_hash"],
                    "result_commit": "1de399f35d1c0d2b7ee1ea6451c2be8d1c49a861",
                }
            ],
        },
        "phase_scope": {
            "planning_traceability_only": True,
            "requirement_task_trace_built": True,
            "lineage_contract_built": True,
            "formula_parameter_trace_built": True,
            "actual_lineage_generated": False,
            "lineage_full_check_complete": False,
            "formula_runtime_enablement_performed": False,
            "product_implementation_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
        },
        "task_accounting": {
            "total": 3,
            "execution_complete": 3,
            "accepted": 3,
            "not_accepted": 0,
        },
        "tasks": [
            {
                "task_id": "S02P2T01",
                "name": "需求映射到 Stage/Phase/Task",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": "PASSED",
                "evidence_refs": [FINAL_ARTIFACT_REFS["requirement_trace"]],
            },
            {
                "task_id": "S02P2T02",
                "name": "建立数据到报告追溯链",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": "PASSED",
                "evidence_refs": [
                    FINAL_ARTIFACT_REFS["lineage_contract"],
                    FINAL_ARTIFACT_REFS["lineage_edges"],
                    FINAL_ARTIFACT_REFS["source_domain_coverage"],
                ],
            },
            {
                "task_id": "S02P2T03",
                "name": "建立公式到测试追溯链",
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": "PASSED",
                "evidence_refs": [
                    FINAL_ARTIFACT_REFS["formula_trace"],
                    FINAL_ARTIFACT_REFS["parameter_trace"],
                ],
            },
        ],
        "trace_accounting": {
            "requirement_count": 55,
            "normalized_binding_count": 134,
            "source_explicit_binding_count": 132,
            "controlled_stage_closure_binding_count": 2,
            "p0_p1_requirement_coverage_numerator": 54,
            "p0_p1_requirement_coverage_denominator": 54,
            "p0_p1_requirement_stage_coverage_numerator": 96,
            "p0_p1_requirement_stage_coverage_denominator": 96,
            "all_requirement_stage_coverage_numerator": 97,
            "all_requirement_stage_coverage_denominator": 97,
        },
        "lineage_accounting": {
            "actual_lineage_record_count": 0,
            "lineage_full_check_complete": False,
            "layer_count": 8,
            "allowed_edge_count": 10,
            "source_domain_row_count": 21,
            "source_system_count": 7,
            "formal_report_allowed": False,
        },
        "formula_accounting": {
            "formula_model_count": 22,
            "formula_count": 14,
            "model_count": 8,
            "parameter_control_count": 38,
            "source_proposed_count": 17,
            "source_verified_required_count": 5,
            "runtime_enabled_count": 0,
            "product_implementation_claim_count": 0,
            "unknown_parameter_default_count": 0,
        },
        "phase_result": {
            "execution_status": "EXECUTION_COMPLETE",
            "evidence_validation_status": "PASS",
            "final_validation_status": "PASS",
            "acceptance_status": "PASSED",
            "decision": "CONTINUE_TO_S02_P3_ONLY",
        },
        "stage_state": {
            "stage_id": "S02",
            "stage_lifecycle_status": "IN_PROGRESS",
            "stage_acceptance_status": "PENDING",
            "stage_passed": False,
            "completed_phase_count": 2,
            "total_phase_count": 3,
        },
        "next_entry_gate": {
            "next_allowed_taskpack_phase": "S02-P3",
            "s02_p3_entry_allowed": True,
            "s02_p3_started_in_current_run": False,
            "s03_plus_entry_allowed": False,
            "product_implementation_allowed": False,
        },
        "downstream_actions": {
            "s02_p3_started": False,
            "s03_plus_started": False,
            "technology_stack_selected": False,
            "product_runtime_implementation_performed": False,
            "api_implementation_performed": False,
            "database_implementation_performed": False,
            "ui_implementation_performed": False,
            "raw_business_content_read": False,
            "raw_root_listed_or_inventoried": False,
            "raw_inbox_mutated": False,
            "business_execution_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
        },
        "artifact_refs": dict(FINAL_ARTIFACT_REFS),
        "artifact_integrity": artifact_integrity,
    }
    manifest["content_hash"] = _content_hash(manifest)
    return manifest


def _write_outputs(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        print(f"WROTE {path}")


def _check_outputs(outputs: Mapping[Path, bytes]) -> None:
    failures = [
        str(path)
        for path, expected in outputs.items()
        if not path.is_file() or path.read_bytes() != expected
    ]
    if failures:
        raise BuildError("core artifact drift: " + ", ".join(failures))
    print(f"PASS: exact S02-P2 core outputs match ({len(outputs)} files)")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", type=Path, default=DEFAULT_SOURCE_PACKAGE)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--finalize-manifest", action="store_true")
    parser.add_argument("--generated-at", default="")
    args = parser.parse_args(argv)
    try:
        if args.finalize_manifest:
            if args.output_root is not None:
                raise BuildError("--output-root is not supported with --finalize-manifest")
            manifest = build_final_manifest(
                generated_at=args.generated_at,
                project_root=args.project_root,
                source_package=args.source_package,
            )
            path = _normalize_project_root(args.project_root) / OUTPUT_ROOT_RELATIVE / MANIFEST_RELATIVE
            payload = _json_bytes(manifest)
            if args.check:
                if not path.is_file() or path.read_bytes() != payload:
                    raise BuildError(f"final manifest drift: {path}")
                print("PASS: exact S02-P2 final manifest matches")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                print(f"WROTE {path}")
        else:
            outputs = expected_core_outputs(
                project_root=args.project_root,
                source_package=args.source_package,
                output_root=args.output_root,
            )
            if args.check:
                _check_outputs(outputs)
            else:
                _write_outputs(outputs)
    except (BuildError, OSError, ValueError, KeyError, csv.Error) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
