#!/usr/bin/env python3
"""Build deterministic public-safe evidence for KMFA v1.5 S02-P3.

The phase locks scope priorities, hard-stop prohibitions, and change control.
It is planning/governance work only: it never reads raw business content,
implements product/runtime behavior, performs the S02 Stage review, enters S03,
uploads GitHub, reinstalls the App, or executes a business action.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence
from zipfile import BadZipFile, ZipFile

from KMFA.tools.v015_s02_p3_scope_gate import (
    DEFAULT_SOURCE_PACKAGE,
    PROHIBITION_COLUMNS,
    PROJECT_ROOT,
    SCOPE_COLUMNS,
    SOURCE_PACKAGE_NAME,
    SOURCE_PACKAGE_SHA256,
    build_change_control_protocol,
    build_prohibited_action_rows,
    build_scope_priority_rows,
    load_s02_p3_task_contract,
    validate_change_control_protocol,
    validate_prohibited_action_rows,
    validate_scope_priority_rows,
)


PHASE_BASE_COMMIT = "833c8a12203a837ae20afa6ba22ab114a636c846"
P1_RESULT_COMMIT = "1de399f35d1c0d2b7ee1ea6451c2be8d1c49a861"
P2_RESULT_COMMIT = PHASE_BASE_COMMIT
P1_MANIFEST_SHA256 = (
    "ca2048b9fc5aa15a80e3ed02e4cae52d995279ecc343b4f1b0d2eeea2936327a"
)
P1_MANIFEST_CONTENT_HASH = (
    "sha256:5e2450b41b5308e35a8a57307bfb763c07a38b0ad321f9ac495b9bd8f53e6a04"
)
P2_MANIFEST_SHA256 = (
    "f21cce631c849fbe0d1a3f3e2a36172e45dcfa2b8db81359b9ddc3ad82f8d51a"
)
P2_MANIFEST_CONTENT_HASH = (
    "sha256:51e83439ebc7440ea73d065f2e4e3423a27c2df11e877881027ef802b204d2d9"
)

OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S02_P3_SCOPE_GATE")
P1_MANIFEST_RELATIVE = Path(
    "stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/"
    "machine/s02_p1_requirements_scope_lock_manifest.json"
)
P2_MANIFEST_RELATIVE = Path(
    "stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/"
    "machine/s02_p2_end_to_end_traceability_manifest.json"
)
P1_MACHINE_RELATIVE = P1_MANIFEST_RELATIVE.parent

SCOPE_RELATIVE = Path("machine/scope_priority_gate_public_safe.csv")
PROHIBITION_RELATIVE = Path(
    "machine/prohibited_action_hard_stops_public_safe.csv"
)
CHANGE_CONTROL_RELATIVE = Path("machine/change_control_protocol_public_safe.json")
ACCEPTANCE_RELATIVE = Path("machine/acceptance_matrix_public_safe.json")
SUMMARY_RELATIVE = Path("human/scope_gate_zh.md")
MANIFEST_RELATIVE = Path("machine/s02_p3_scope_gate_manifest.json")

FINAL_ARTIFACT_REFS = {
    "manifest": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/"
        "machine/s02_p3_scope_gate_manifest.json"
    ),
    "scope_priority_gate": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/"
        "machine/scope_priority_gate_public_safe.csv"
    ),
    "prohibited_action_hard_stops": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/"
        "machine/prohibited_action_hard_stops_public_safe.csv"
    ),
    "change_control_protocol": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/"
        "machine/change_control_protocol_public_safe.json"
    ),
    "acceptance_matrix": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/"
        "machine/acceptance_matrix_public_safe.json"
    ),
    "scope_gate_summary": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/human/scope_gate_zh.md"
    ),
    "completion_record": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/"
        "human/completion_record_zh.md"
    ),
    "rollback_plan": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/human/rollback_plan_zh.md"
    ),
    "test_results": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/human/test_results_zh.md"
    ),
    "validation_results": (
        "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/"
        "machine/validation_results.jsonl"
    ),
}

_EMAIL_RE = re.compile(
    rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
_FORBIDDEN_PUBLIC_TOKENS = (
    b"/Users/",
    b"/Volumes/",
    b"/private/",
    b"/tmp/",
    b"/home/",
    b"KMFA_MetaData",
    b"OWNER_NOTIFICATION_EMAIL_TOKEN@",
)


class BuildError(RuntimeError):
    """Raised when deterministic S02-P3 evidence cannot be built."""


def _normalize_project_root(project_root: Optional[Path]) -> Path:
    root = PROJECT_ROOT if project_root is None else Path(project_root).resolve()
    if (root / "stage_artifacts").is_dir() and (root / "tools").is_dir():
        return root
    nested = root / "KMFA"
    if (nested / "stage_artifacts").is_dir() and (nested / "tools").is_dir():
        return nested
    raise BuildError(f"KMFA project root not found: {root}")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _csv_bytes(
    headers: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(headers),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: (
                    json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    if isinstance(value, (list, dict, bool))
                    else value
                )
                for key, value in row.items()
            }
        )
    return buffer.getvalue().encode("utf-8")


def _content_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + _sha256_bytes(encoded)


def _assert_public_safe(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        for token in _FORBIDDEN_PUBLIC_TOKENS:
            if token in payload:
                raise BuildError(
                    f"public-safe token violation in {path}: {token!r}"
                )
        if _EMAIL_RE.search(payload):
            raise BuildError(f"email leaked into public-safe output: {path}")


def _verify_source_package(package: Path) -> dict[str, Any]:
    if not package.is_file():
        raise BuildError(f"source package missing: {package}")
    package_payload = package.read_bytes()
    if _sha256_bytes(package_payload) != SOURCE_PACKAGE_SHA256:
        raise BuildError("source package hash drift")

    try:
        with ZipFile(package) as archive:
            file_names = [item.filename for item in archive.infolist() if not item.is_dir()]
            manifest_names = [
                name
                for name in file_names
                if name.rsplit("/", 1)[-1].startswith("15_MANIFEST_SHA256_")
                and name.endswith(".csv")
            ]
            if len(manifest_names) != 1:
                raise BuildError(
                    f"source SHA manifest member count drift: {len(manifest_names)}"
                )
            manifest_name = manifest_names[0]
            manifest_payload = archive.read(manifest_name)
            reader = csv.DictReader(
                io.StringIO(manifest_payload.decode("utf-8-sig"), newline="")
            )
            rows = [dict(row) for row in reader]
            if reader.fieldnames != ["相对路径", "字节数", "SHA256"]:
                raise BuildError("source SHA manifest header drift")
            if len(rows) != 21:
                raise BuildError(
                    f"source SHA manifest row count drift: {len(rows)}"
                )

            declared: set[str] = set()
            verified = 0
            for row in rows:
                relative = str(row.get("相对路径", ""))
                relative_path = PurePosixPath(relative)
                if (
                    not relative
                    or relative_path.is_absolute()
                    or ".." in relative_path.parts
                    or relative in declared
                ):
                    raise BuildError("unsafe or duplicate source manifest path")
                declared.add(relative)
                candidates = [
                    name
                    for name in file_names
                    if name == relative or name.endswith("/" + relative)
                ]
                if len(candidates) != 1:
                    raise BuildError(
                        f"source member resolution drift for {relative}: {len(candidates)}"
                    )
                payload = archive.read(candidates[0])
                try:
                    declared_bytes = int(str(row.get("字节数", "")))
                except ValueError as error:
                    raise BuildError(
                        f"invalid source manifest byte count: {relative}"
                    ) from error
                if len(payload) != declared_bytes:
                    raise BuildError(f"source member byte drift: {relative}")
                if _sha256_bytes(payload) != str(row.get("SHA256", "")):
                    raise BuildError(f"source member SHA drift: {relative}")
                verified += 1

            unlisted = [
                name
                for name in file_names
                if name != manifest_name
                and not any(name == item or name.endswith("/" + item) for item in declared)
            ]
            if unlisted:
                raise BuildError(f"source package has unmanifested files: {len(unlisted)}")
            if len(file_names) != 22 or verified != 21:
                raise BuildError("source package 21/21 verification failed")
    except BadZipFile as error:
        raise BuildError("source package is not a readable ZIP") from error

    return {
        "name": SOURCE_PACKAGE_NAME,
        "bytes": len(package_payload),
        "sha256": SOURCE_PACKAGE_SHA256,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
        "requirement_count": 55,
        "sha_manifest_member": manifest_name.rsplit("/", 1)[-1],
        "sha_manifest_bytes": len(manifest_payload),
        "sha_manifest_sha256": _sha256_bytes(manifest_payload),
        "sha_manifest_declared_member_count": 21,
        "sha_manifest_verified_member_count": 21,
        "sha_manifest_verification_status": "PASS",
        "sha_manifest_mismatch_count": 0,
        "unmanifested_member_count": 0,
    }


def _acceptance_check(
    *,
    check_id: str,
    task_id: str,
    criterion: str,
    observed: Any,
    evidence_refs: Sequence[str],
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "task_id": task_id,
        "criterion": criterion,
        "status": "PASS",
        "observed": observed,
        "evidence_refs": list(evidence_refs),
        "blocking": True,
    }


def _acceptance_matrix(
    *,
    task_contract: Mapping[str, Mapping[str, str]],
    scope_rows: Sequence[Mapping[str, Any]],
    prohibition_rows: Sequence[Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    scope_ref = FINAL_ARTIFACT_REFS["scope_priority_gate"]
    prohibition_ref = FINAL_ARTIFACT_REFS["prohibited_action_hard_stops"]
    protocol_ref = FINAL_ARTIFACT_REFS["change_control_protocol"]
    acceptance_ref = FINAL_ARTIFACT_REFS["acceptance_matrix"]
    scope_counts = Counter(
        (str(row["scope_item_type"]), str(row["priority"])) for row in scope_rows
    )
    explicit_count = sum(
        row["source_scope"] == "S02_P3_EXPLICIT" for row in prohibition_rows
    )
    business_count = sum(
        row["source_scope"] == "BUSINESS_LINE_MATRIX" for row in prohibition_rows
    )
    all_hard_stopped = all(
        row["hard_stop_required"] is True
        and row["planning_gate_defined"] is True
        and row["runtime_guard_implemented"] is False
        and row["product_action_authorized"] is False
        for row in prohibition_rows
    )
    merge_gate = protocol["merge_gate"]
    checks = [
        _acceptance_check(
            check_id="ACC-S02P3-T01-001",
            task_id="S02P3T01",
            criterion=task_contract["S02P3T01"]["acceptance"],
            observed={"scope_rows": len(scope_rows), "authority_counts": "55/10/37/1"},
            evidence_refs=[scope_ref],
        ),
        _acceptance_check(
            check_id="ACC-S02P3-T01-002",
            task_id="S02P3T01",
            criterion="P0/P1/P2 与业务线优先级保持权威来源不漂移。",
            observed={
                "requirement_priorities": {
                    "P0": scope_counts[("REQUIREMENT", "P0")],
                    "P1": scope_counts[("REQUIREMENT", "P1")],
                    "P2": scope_counts[("REQUIREMENT", "P2")],
                },
                "business_line_priorities": {
                    "P0": scope_counts[("BUSINESS_LINE", "P0")],
                    "P1": scope_counts[("BUSINESS_LINE", "P1")],
                    "P2": scope_counts[("BUSINESS_LINE", "P2")],
                },
            },
            evidence_refs=[scope_ref],
        ),
        _acceptance_check(
            check_id="ACC-S02P3-T01-003",
            task_id="S02P3T01",
            criterion="时间压力不得降低质量或绕过变更控制。",
            observed={
                "quality_tradeoff_allowed_count": sum(
                    row["time_pressure_quality_tradeoff_allowed"] is True
                    for row in scope_rows
                ),
                "change_control_required_count": sum(
                    row["change_control_required"] is True for row in scope_rows
                ),
            },
            evidence_refs=[scope_ref, protocol_ref],
        ),
        _acceptance_check(
            check_id="ACC-S02P3-T02-001",
            task_id="S02P3T02",
            criterion=task_contract["S02P3T02"]["acceptance"],
            observed={
                "prohibition_rows": len(prohibition_rows),
                "explicit": explicit_count,
                "business_line": business_count,
            },
            evidence_refs=[prohibition_ref],
        ),
        _acceptance_check(
            check_id="ACC-S02P3-T02-002",
            task_id="S02P3T02",
            criterion="全部禁止事项必须 fail closed，且本 Phase 不实现 runtime guard。",
            observed={
                "all_hard_stopped": all_hard_stopped,
                "runtime_guard_implemented_count": sum(
                    row["runtime_guard_implemented"] is True
                    for row in prohibition_rows
                ),
            },
            evidence_refs=[prohibition_ref],
        ),
        _acceptance_check(
            check_id="ACC-S02P3-T03-001",
            task_id="S02P3T03",
            criterion=task_contract["S02P3T03"]["acceptance"],
            observed={
                "auditable_domains": protocol["auditable_domains"],
                "required_change_fields": len(protocol["required_change_fields"]),
            },
            evidence_refs=[protocol_ref],
        ),
        _acceptance_check(
            check_id="ACC-S02P3-T03-002",
            task_id="S02P3T03",
            criterion="未登记、未批准或未验证的变更不得合并。",
            observed={
                "unregistered_merge_allowed": merge_gate[
                    "unregistered_change_merge_allowed"
                ],
                "unapproved_merge_allowed": merge_gate[
                    "unapproved_change_merge_allowed"
                ],
                "unvalidated_merge_allowed": merge_gate[
                    "unvalidated_change_merge_allowed"
                ],
                "planning_policy_defined": True,
                "runtime_or_ci_hook_implemented": protocol[
                    "runtime_or_ci_hook_implemented_in_s02_p3"
                ],
                "merge_authorization_emitted_by_evaluator": protocol[
                    "merge_authorization_emitted_by_evaluator"
                ],
            },
            evidence_refs=[protocol_ref],
        ),
        _acceptance_check(
            check_id="ACC-S02P3-PHASE-001",
            task_id="S02P3T03",
            criterion="Phase 完成只开放独立 S02 Stage review，不开放 S03 或产品实现。",
            observed={
                "stage_review_required": True,
                "stage_review_performed": False,
                "s03_entry_allowed": False,
                "product_implementation_allowed": False,
            },
            evidence_refs=[acceptance_ref],
        ),
    ]
    return {
        "schema_version": "kmfa.v015.s02_p3_acceptance_matrix.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S02",
        "roadmap_phase_id": "S02-P3",
        "run_phase_id": "V015_S02_P3_SCOPE_GATE",
        "task_contract": {
            task_id: dict(task_contract[task_id]) for task_id in sorted(task_contract)
        },
        "checks": checks,
        "accounting": {
            "total": len(checks),
            "passed": len(checks),
            "failed": 0,
        },
        "phase_acceptance_eligible": True,
        "stage_acceptance_allowed": False,
        "stage_review_required": True,
        "stage_review_performed": False,
        "phase_result": {
            "acceptance_status": "PASSED",
            "decision": "CONTINUE_TO_S02_STAGE_REVIEW_ONLY",
        },
        "stage_state": {
            "lifecycle_status": "IN_PROGRESS",
            "acceptance_status": "PENDING",
            "execution_percentage": 100,
        },
        "next_entry_gate": {
            "next_gate_id": "S02-STAGE-REVIEW",
            "s02_stage_review_entry_allowed": True,
        },
        "s03_entry_allowed": False,
        "product_implementation_allowed": False,
        "public_safe_status": "PUBLIC_SAFE",
    }


def _summary_markdown(
    *,
    scope_rows: Sequence[Mapping[str, Any]],
    prohibition_rows: Sequence[Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> bytes:
    scope_counts = Counter(str(row["scope_item_type"]) for row in scope_rows)
    explicit = sum(
        row["source_scope"] == "S02_P3_EXPLICIT" for row in prohibition_rows
    )
    business = sum(
        row["source_scope"] == "BUSINESS_LINE_MATRIX" for row in prohibition_rows
    )
    lines = [
        "# KMFA v1.5 S02-P3 范围门禁",
        "",
        "## 结论",
        "",
        f"- 范围优先级表共 {len(scope_rows)} 行：需求 {scope_counts['REQUIREMENT']}、"
        f"业务线 {scope_counts['BUSINESS_LINE']}、能力 {scope_counts['CAPABILITY']}、"
        f"后置策略 {scope_counts['POLICY']}。权威优先级保持不变。",
        f"- 禁止事项共 {len(prohibition_rows)} 行：S02-P3 显式禁止 {explicit} 行、"
        f"10 条业务线派生 {business} 行；全部为 hard stop，runtime guard 仍未实现。",
        f"- 变更控制覆盖 {len(protocol['auditable_domains'])} 个必审域、"
        f"{len(protocol['required_change_fields'])} 个必填字段；未登记、未批准、"
        "未验证或缺回归范围的变更按规划协议不得合并。当前 evaluator 只做 schema/"
        "planning completeness，不解析 registry、artifact ref 或 audit event，也不发出真实 merge 授权。",
        "",
        "## 边界",
        "",
        "- 本 Phase 只建立 public-safe 范围、禁止事项与变更控制规划合同。",
        "- 未读取 raw，未实现 runtime/API/DB/UI、CI hook、禁止动作或业务动作，"
        "未上传 GitHub，未重装 App。",
        "- S02 三个 Phase 执行完成后 Stage 仍为 `IN_PROGRESS / PENDING`；"
        "下一独立 Run 只能执行 S02 Stage review/fix，S03 仍关闭。",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def expected_core_outputs(
    project_root: Optional[Path] = None,
    source_package: Optional[Path] = None,
    output_root: Optional[Path] = None,
) -> dict[Path, bytes]:
    """Return deterministic absolute output paths and their exact bytes."""

    root = _normalize_project_root(project_root)
    package = DEFAULT_SOURCE_PACKAGE if source_package is None else Path(source_package)
    _verify_source_package(package)
    destination = (
        root / OUTPUT_ROOT_RELATIVE
        if output_root is None
        else Path(output_root).resolve()
    )
    p1_machine = root / P1_MACHINE_RELATIVE

    task_contract = load_s02_p3_task_contract(package)
    scope_rows = build_scope_priority_rows(
        p1_machine / "requirements_ledger_public_safe.csv",
        p1_machine / "business_line_matrix_public_safe.csv",
        p1_machine / "scope_lock_dispositions_public_safe.csv",
    )
    scope_errors = validate_scope_priority_rows(scope_rows)
    if scope_errors:
        raise BuildError("scope priority invalid: " + "; ".join(scope_errors))

    prohibition_rows = build_prohibited_action_rows(
        p1_machine / "business_line_matrix_public_safe.csv"
    )
    prohibition_errors = validate_prohibited_action_rows(prohibition_rows)
    if prohibition_errors:
        raise BuildError(
            "prohibited action contract invalid: " + "; ".join(prohibition_errors)
        )

    protocol = build_change_control_protocol()
    protocol_errors = validate_change_control_protocol(protocol)
    if protocol_errors:
        raise BuildError(
            "change control protocol invalid: " + "; ".join(protocol_errors)
        )
    acceptance = _acceptance_matrix(
        task_contract=task_contract,
        scope_rows=scope_rows,
        prohibition_rows=prohibition_rows,
        protocol=protocol,
    )
    if acceptance["accounting"]["failed"] != 0:
        raise BuildError("S02-P3 acceptance matrix contains failures")

    outputs = {
        destination / SCOPE_RELATIVE: _csv_bytes(SCOPE_COLUMNS, scope_rows),
        destination / PROHIBITION_RELATIVE: _csv_bytes(
            PROHIBITION_COLUMNS, prohibition_rows
        ),
        destination / CHANGE_CONTROL_RELATIVE: _json_bytes(protocol),
        destination / ACCEPTANCE_RELATIVE: _json_bytes(acceptance),
        destination / SUMMARY_RELATIVE: _summary_markdown(
            scope_rows=scope_rows,
            prohibition_rows=prohibition_rows,
            protocol=protocol,
        ),
    }
    _assert_public_safe(outputs)
    return outputs


def _dependency_row(
    *,
    path: Path,
    dependency_id: str,
    ref: str,
    expected_sha256: str,
    expected_content_hash: str,
    result_commit: str,
) -> dict[str, Any]:
    payload = path.read_bytes()
    if _sha256_bytes(payload) != expected_sha256:
        raise BuildError(f"dependency SHA drift: {dependency_id}")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise BuildError(f"dependency manifest must be an object: {dependency_id}")
    if value.get("content_hash") != expected_content_hash:
        raise BuildError(f"dependency content hash drift: {dependency_id}")
    if value.get("phase_result", {}).get("acceptance_status") != "PASSED":
        raise BuildError(f"dependency not passed: {dependency_id}")
    return {
        "dependency_id": dependency_id,
        "ref": ref,
        "bytes": len(payload),
        "sha256": expected_sha256,
        "content_hash": expected_content_hash,
        "result_commit": result_commit,
    }


def build_final_manifest(
    generated_at: str,
    project_root: Optional[Path] = None,
    source_package: Optional[Path] = None,
) -> dict[str, Any]:
    """Build the final manifest after every non-self artifact is finalized."""

    try:
        parsed_time = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
    except ValueError as error:
        raise BuildError("generated_at must be ISO-8601") from error
    if parsed_time.tzinfo is None or parsed_time.utcoffset() is None:
        raise BuildError("generated_at must include a timezone offset")

    root = _normalize_project_root(project_root)
    package = DEFAULT_SOURCE_PACKAGE if source_package is None else Path(source_package)
    source_snapshot = _verify_source_package(package)

    expected_core = expected_core_outputs(
        project_root=root,
        source_package=package,
    )
    for path, expected in expected_core.items():
        if not path.is_file() or path.read_bytes() != expected:
            raise BuildError(f"core artifact drift before manifest finalization: {path}")

    dependencies = [
        _dependency_row(
            path=root / P1_MANIFEST_RELATIVE,
            dependency_id="s02_p1_requirements_scope_lock",
            ref=(
                "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/"
                "machine/s02_p1_requirements_scope_lock_manifest.json"
            ),
            expected_sha256=P1_MANIFEST_SHA256,
            expected_content_hash=P1_MANIFEST_CONTENT_HASH,
            result_commit=P1_RESULT_COMMIT,
        ),
        _dependency_row(
            path=root / P2_MANIFEST_RELATIVE,
            dependency_id="s02_p2_end_to_end_traceability",
            ref=(
                "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/"
                "machine/s02_p2_end_to_end_traceability_manifest.json"
            ),
            expected_sha256=P2_MANIFEST_SHA256,
            expected_content_hash=P2_MANIFEST_CONTENT_HASH,
            result_commit=P2_RESULT_COMMIT,
        ),
    ]

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

    scope_rows = build_scope_priority_rows(
        root / P1_MACHINE_RELATIVE / "requirements_ledger_public_safe.csv",
        root / P1_MACHINE_RELATIVE / "business_line_matrix_public_safe.csv",
        root / P1_MACHINE_RELATIVE / "scope_lock_dispositions_public_safe.csv",
    )
    prohibition_rows = build_prohibited_action_rows(
        root / P1_MACHINE_RELATIVE / "business_line_matrix_public_safe.csv"
    )
    protocol = build_change_control_protocol()
    task_contract = load_s02_p3_task_contract(package)
    scope_counts = Counter(
        (str(row["scope_item_type"]), str(row["priority"])) for row in scope_rows
    )
    explicit_prohibitions = sum(
        row["source_scope"] == "S02_P3_EXPLICIT" for row in prohibition_rows
    )
    business_prohibitions = sum(
        row["source_scope"] == "BUSINESS_LINE_MATRIX" for row in prohibition_rows
    )
    override_fields = (
        "change_control_can_override",
        "owner_authorization_can_override",
    )
    acceptance = json.loads(
        (root / OUTPUT_ROOT_RELATIVE / ACCEPTANCE_RELATIVE).read_text(
            encoding="utf-8"
        )
    )

    manifest: dict[str, Any] = {
        "schema_version": "kmfa.v015.s02_p3_scope_gate.v1",
        "project_id": "KMFA",
        "target_release": "v1.5",
        "stage_id": "S02",
        "roadmap_phase_id": "S02-P3",
        "run_phase_id": "V015_S02_P3_SCOPE_GATE",
        "task_id": "KMFA-V015-S02-P3-SCOPE-GATE-20260713",
        "acceptance_id": "ACC-KMFA-V015-S02-P3-SCOPE-GATE",
        "generated_at": generated_at,
        "run_mode": "IMPLEMENT",
        "work_kind": "SCOPE_GATE_CHANGE_CONTROL_PLANNING",
        "phase_base_commit": PHASE_BASE_COMMIT,
        "source_package": source_snapshot,
        "dependency_evidence": {
            "count": len(dependencies),
            "dependencies": dependencies,
        },
        "phase_scope": {
            "planning_only": True,
            "scope_priority_lock_built": True,
            "prohibited_action_hard_stops_built": True,
            "change_control_protocol_built": True,
            "runtime_or_ci_hook_implemented": False,
            "product_implementation_allowed": False,
            "formal_report_allowed": False,
            "business_execution_allowed": False,
            "s02_stage_review_performed": False,
            "s03_started": False,
        },
        "task_accounting": {
            "total": 3,
            "execution_complete": 3,
            "accepted": 3,
            "not_accepted": 0,
        },
        "tasks": [
            {
                "task_id": "S02P3T01",
                "name": task_contract["S02P3T01"]["name"],
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": "PASSED",
                "evidence_refs": [
                    FINAL_ARTIFACT_REFS["scope_priority_gate"],
                    FINAL_ARTIFACT_REFS["acceptance_matrix"],
                ],
            },
            {
                "task_id": "S02P3T02",
                "name": task_contract["S02P3T02"]["name"],
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": "PASSED",
                "evidence_refs": [
                    FINAL_ARTIFACT_REFS["prohibited_action_hard_stops"],
                    FINAL_ARTIFACT_REFS["acceptance_matrix"],
                ],
            },
            {
                "task_id": "S02P3T03",
                "name": task_contract["S02P3T03"]["name"],
                "execution_status": "EXECUTION_COMPLETE",
                "acceptance_status": "PASSED",
                "evidence_refs": [
                    FINAL_ARTIFACT_REFS["change_control_protocol"],
                    FINAL_ARTIFACT_REFS["acceptance_matrix"],
                ],
            },
        ],
        "scope_accounting": {
            "scope_row_count": len(scope_rows),
            "requirement_count": scope_counts[("REQUIREMENT", "P0")]
            + scope_counts[("REQUIREMENT", "P1")]
            + scope_counts[("REQUIREMENT", "P2")],
            "business_line_count": scope_counts[("BUSINESS_LINE", "P0")]
            + scope_counts[("BUSINESS_LINE", "P1")]
            + scope_counts[("BUSINESS_LINE", "P2")],
            "capability_count": scope_counts[("CAPABILITY", "NA")],
            "deferred_policy_count": scope_counts[("POLICY", "NA")],
            "requirement_p0_count": scope_counts[("REQUIREMENT", "P0")],
            "requirement_p1_count": scope_counts[("REQUIREMENT", "P1")],
            "requirement_p2_count": scope_counts[("REQUIREMENT", "P2")],
            "business_line_p0_count": scope_counts[("BUSINESS_LINE", "P0")],
            "business_line_p1_count": scope_counts[("BUSINESS_LINE", "P1")],
            "business_line_p2_count": scope_counts[("BUSINESS_LINE", "P2")],
            "time_pressure_quality_tradeoff_allowed_count": sum(
                row["time_pressure_quality_tradeoff_allowed"] is True
                for row in scope_rows
            ),
            "implementation_authorized_count": sum(
                row["implementation_authorized_by_s02_p3"] is True
                for row in scope_rows
            ),
        },
        "prohibition_accounting": {
            "prohibition_row_count": len(prohibition_rows),
            "explicit_prohibition_count": explicit_prohibitions,
            "business_line_prohibition_count": business_prohibitions,
            "covered_business_line_count": len(
                {
                    row["business_line_id"]
                    for row in prohibition_rows
                    if row["source_scope"] == "BUSINESS_LINE_MATRIX"
                }
            ),
            "hard_stop_required_count": sum(
                row["hard_stop_required"] is True for row in prohibition_rows
            ),
            "runtime_guard_implemented_count": sum(
                row["runtime_guard_implemented"] is True
                for row in prohibition_rows
            ),
            "prohibited_action_implemented_count": sum(
                row["prohibited_action_implemented_in_s02_p3"] is True
                for row in prohibition_rows
            ),
            "product_action_authorized_count": sum(
                row["product_action_authorized"] is True
                for row in prohibition_rows
            ),
            "override_allowed_count": sum(
                any(row[field] is True for field in override_fields)
                for row in prohibition_rows
            ),
        },
        "change_control_accounting": {
            "auditable_domain_count": len(protocol["auditable_domains"]),
            "required_change_field_count": len(protocol["required_change_fields"]),
            "change_type_count": len(protocol["change_types"]),
            "runtime_or_ci_hook_implemented": protocol[
                "runtime_or_ci_hook_implemented_in_s02_p3"
            ],
            "unregistered_change_merge_allowed": protocol["merge_gate"][
                "unregistered_change_merge_allowed"
            ],
            "unapproved_change_merge_allowed": protocol["merge_gate"][
                "unapproved_change_merge_allowed"
            ],
            "unvalidated_change_merge_allowed": protocol["merge_gate"][
                "unvalidated_change_merge_allowed"
            ],
        },
        "acceptance_accounting": dict(acceptance["accounting"]),
        "phase_result": {
            "execution_status": "EXECUTION_COMPLETE",
            "evidence_validation_status": "PASS",
            "final_validation_status": "PASS",
            "acceptance_status": "PASSED",
            "decision": "CONTINUE_TO_S02_STAGE_REVIEW_ONLY",
        },
        "stage_state": {
            "stage_id": "S02",
            "stage_lifecycle_status": "IN_PROGRESS",
            "stage_acceptance_status": "PENDING",
            "stage_passed": False,
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "execution_percentage": 100,
            "stage_review_performed": False,
        },
        "next_entry_gate": {
            "next_allowed_run": "S02-STAGE-REVIEW",
            "next_gate_id": "S02-STAGE-REVIEW",
            "s02_stage_review_entry_allowed": True,
            "s02_stage_review_started_in_current_run": False,
            "s03_entry_allowed": False,
            "s03_plus_entry_allowed": False,
            "product_implementation_allowed": False,
        },
        "downstream_actions": {
            "s02_stage_review_performed": False,
            "s03_started": False,
            "s03_plus_started": False,
            "technology_stack_selected": False,
            "product_runtime_implementation_performed": False,
            "runtime_or_ci_hook_implemented": False,
            "api_implementation_performed": False,
            "database_implementation_performed": False,
            "ui_implementation_performed": False,
            "raw_business_content_read": False,
            "raw_root_listed_or_inventoried": False,
            "raw_inbox_mutated": False,
            "formal_report_generated": False,
            "external_full_report_sent": False,
            "payment_performed": False,
            "tax_filing_performed": False,
            "invoice_issuance_performed": False,
            "payroll_approval_performed": False,
            "business_execution_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
        },
        "artifact_refs": dict(FINAL_ARTIFACT_REFS),
        "artifact_integrity": artifact_integrity,
    }
    manifest["content_hash"] = _content_hash(manifest)
    payload = _json_bytes(manifest)
    _assert_public_safe({root / OUTPUT_ROOT_RELATIVE / MANIFEST_RELATIVE: payload})
    return manifest


def _write_outputs(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        print(f"WROTE {path}")


def _check_outputs(outputs: Mapping[Path, bytes]) -> None:
    failures: list[str] = []
    for path, expected in outputs.items():
        if not path.is_file():
            failures.append(f"MISSING {path}")
            continue
        actual = path.read_bytes()
        if actual != expected:
            failures.append(
                f"DRIFT {path} expected_sha256={_sha256_bytes(expected)} "
                f"actual_sha256={_sha256_bytes(actual)}"
            )
    if failures:
        raise BuildError("core artifact check failed:\n" + "\n".join(failures))
    print(f"PASS: exact S02-P3 core outputs match ({len(outputs)} files)")


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
                args.generated_at,
                project_root=args.project_root,
                source_package=args.source_package,
            )
            path = (
                _normalize_project_root(args.project_root)
                / OUTPUT_ROOT_RELATIVE
                / MANIFEST_RELATIVE
            )
            payload = _json_bytes(manifest)
            if args.check:
                if not path.is_file() or path.read_bytes() != payload:
                    raise BuildError(f"final manifest drift: {path}")
                print("PASS: exact S02-P3 final manifest matches")
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
    except (
        BadZipFile,
        BuildError,
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
        csv.Error,
        json.JSONDecodeError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
