#!/usr/bin/env python3
"""Build deterministic public-safe evidence for the KMFA v1.5 S02 Stage review.

This is an independent governance overlay, not a Roadmap Phase, P4, or tenth
Task.  It reviews the nine source Tasks in S02-P1/P2/P3, binds the three
predecessor manifests, records review findings and controlled risks, and maps
the quality-spec evidence slots without copying predecessor artifacts.

The builder never reads raw business content, starts S03-P1, implements product
runtime behavior, uploads GitHub, reinstalls the App, or executes a business
action.  A final PASSED manifest can be built only after exact, executable
validation receipts exist and every blocking finding is closed.
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


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
SOURCE_PACKAGE_NAME = (
    "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
)
DEFAULT_SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME
SOURCE_PACKAGE_SHA256 = (
    "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
)
SOURCE_MANIFEST_SHA256 = (
    "a4a5cb0e301a841a922e761ff503a2fce72982b1b088d9aeee9e11998939b2a5"
)
REVIEW_BASE_COMMIT = "9d3a1c26a44c6c6838d3b6c5138e66ae5e5d1ec7"
RUN_PHASE_ID = "V015_S02_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S02-STAGE-REVIEW-20260713"
ACCEPTANCE_ID = "ACC-KMFA-V015-S02-STAGE-REVIEW"

OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S02_STAGE_REVIEW")
MATRIX_RELATIVE = Path("machine/stage2_review_matrix_public_safe.json")
FINDINGS_RELATIVE = Path("machine/stage2_review_findings_public_safe.csv")
CONTRACTS_RELATIVE = Path("machine/cross_phase_contracts_public_safe.json")
RISKS_RELATIVE = Path("machine/open_risk_register_public_safe.csv")
TASK_EVIDENCE_RELATIVE = Path("machine/task_evidence_contract_public_safe.json")
RECEIPT_TEMPLATE_RELATIVE = Path("machine/validation_receipts_template.jsonl")
VALIDATION_RESULTS_RELATIVE = Path("machine/validation_results.jsonl")
REPORT_RELATIVE = Path("human/stage2_review_report_zh.md")
ROLLBACK_RELATIVE = Path("human/rollback_plan_zh.md")
TEST_RESULTS_RELATIVE = Path("human/test_results_zh.md")
MANIFEST_RELATIVE = Path("machine/stage2_review_manifest.json")

FINAL_ARTIFACT_REFS = {
    "manifest": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/stage2_review_manifest.json",
    "review_matrix": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/stage2_review_matrix_public_safe.json",
    "review_findings": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/stage2_review_findings_public_safe.csv",
    "cross_phase_contracts": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/cross_phase_contracts_public_safe.json",
    "open_risk_register": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/open_risk_register_public_safe.csv",
    "task_evidence_contract": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/task_evidence_contract_public_safe.json",
    "validation_receipts_template": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/validation_receipts_template.jsonl",
    "validation_results": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/validation_results.jsonl",
    "review_report": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/human/stage2_review_report_zh.md",
    "rollback_plan": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/human/rollback_plan_zh.md",
    "test_results": "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/human/test_results_zh.md",
}

PHASES = {
    "S02-P1": {
        "manifest_ref": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/s02_p1_requirements_scope_lock_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/validation_results.jsonl",
        "completion_ref": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/completion_record_zh.md",
        "test_ref": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/test_results_zh.md",
        "rollback_ref": "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/human/rollback_plan_zh.md",
    },
    "S02-P2": {
        "manifest_ref": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/s02_p2_end_to_end_traceability_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/validation_results.jsonl",
        "completion_ref": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/human/completion_record_zh.md",
        "test_ref": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/human/test_results_zh.md",
        "rollback_ref": "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/human/rollback_plan_zh.md",
    },
    "S02-P3": {
        "manifest_ref": "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/machine/s02_p3_scope_gate_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/machine/validation_results.jsonl",
        "completion_ref": "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/human/completion_record_zh.md",
        "test_ref": "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/human/test_results_zh.md",
        "rollback_ref": "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/human/rollback_plan_zh.md",
    },
}

P1_REQUIREMENTS_REF = "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/requirements_ledger_public_safe.csv"
P1_BUSINESS_REF = "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/business_line_matrix_public_safe.csv"
P1_SCOPE_REF = "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/scope_lock_dispositions_public_safe.csv"
P2_TRACE_REF = "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/requirement_task_traceability_public_safe.csv"
P2_LINEAGE_REF = "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/data_report_lineage_field_contract_public_safe.json"
P3_SCOPE_REF = "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/machine/scope_priority_gate_public_safe.csv"
P3_PROHIBITION_REF = "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/machine/prohibited_action_hard_stops_public_safe.csv"
P3_CHANGE_REF = "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/machine/change_control_protocol_public_safe.json"
S01_REVIEW_REF = "KMFA/stage_artifacts/V015_S01_STAGE_REVIEW/machine/stage1_review_manifest.json"
PROJECT_GOVERNANCE_REF = "KMFA/docs/governance/project.yaml"
README_REF = "KMFA/README.md"
METADATA_PROJECT_REF = "KMFA/metadata/project/project.yaml"
METADATA_STAGE_STATUS_REF = "KMFA/metadata/stage_status.jsonl"
METADATA_MODEL_REGISTRY_REF = "KMFA/metadata/model_registry.yaml"

FINDING_COLUMNS = (
    "finding_id", "severity", "finding_class", "status", "title",
    "source_ref", "reproduction", "impact", "fix_ref", "revalidation_ref",
    "blocks_stage_acceptance",
)
RISK_COLUMNS = (
    "risk_id", "severity", "status", "risk", "impact", "control",
    "follow_up_stage_task", "plan_complete", "blocks_s02_stage_acceptance",
    "evidence_refs",
)

EXPECTED_VALIDATION_RECEIPTS = {
    "python39_compile": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; "
        "[ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in "
        "('KMFA/tools/build_v015_s02_stage_review.py','KMFA/tools/check_v015_s02_stage_review.py')]\""
    ),
    "source_package_manifest_integrity": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s02_stage_review.py --source-only"
    ),
    "s02_p1_strict_dependency": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s02_p1_requirements_scope_lock.py "
        "--require-source-package --require-validation-receipts --require-roadmap-sync"
    ),
    "s02_p2_strict_dependency": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s02_p2_end_to_end_traceability.py"
    ),
    "s02_p3_strict_dependency": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s02_p3_scope_gate.py"
    ),
    "s02_phase_focused_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s02_p1_requirements_merge "
        "KMFA.tests.test_v015_s02_p2_end_to_end_traceability "
        "KMFA.tests.test_v015_s02_p3_scope_gate "
        "KMFA.tests.test_v015_s02_p3_scope_gate_evidence -q"
    ),
    "s02_stage_review_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s02_stage_review -q"
    ),
    "roadmap_governance_check": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/v015_roadmap_governance_sync.py --check"
    ),
    "roadmap_governance_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_roadmap_governance_sync -q"
    ),
    "governance_project_check": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/validate_project_governance.py --project KMFA --mode required"
    ),
    "lean_check": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/lean_governance.py validate --project KMFA --mode required"
    ),
    "governance_sync_check": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/validate_governance_sync.py --changed-only --base-ref "
        + REVIEW_BASE_COMMIT + " --enforce-sync"
    ),
    "no_float_check": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_no_float_money.py"
    ),
    "no_omission_check": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/no_omission_check.py"
    ),
    "structured_public_diff_checks": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s02_stage_review.py "
        "--structured-public-diff-check --base-ref " + REVIEW_BASE_COMMIT
    ),
    "stage_review_exact_rebuild_check": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s02_stage_review.py --check"
    ),
}

_EMAIL_RE = re.compile(
    rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
_FORBIDDEN_PUBLIC_TOKENS = (
    b"/" + b"Users/", b"/" + b"Volumes/", b"/" + b"private/",
    b"/" + b"tmp/", b"/" + b"home/",
    b"KMFA_" + b"MetaData", b"OWNER_NOTIFICATION_EMAIL_" + b"TOKEN@",
)


class BuildError(RuntimeError):
    """Raised when deterministic S02 Stage-review evidence cannot be built."""


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
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return "".join(
        json.dumps(dict(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    ).encode("utf-8")


def _csv_bytes(headers: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(headers), extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({
            key: (
                json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                if isinstance(value, (list, dict, bool)) else value
            )
            for key, value in row.items()
        })
    return buffer.getvalue().encode("utf-8")


def _content_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + _sha256_bytes(encoded)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"expected JSON object: {path}")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise BuildError(f"expected JSON object at {path}:{number}")
        rows.append(value)
    return rows


def _repo_path(root: Path, ref: str, *, require_exists: bool = True) -> Path:
    relative = Path(ref)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "KMFA":
        raise BuildError(f"unsafe repository ref: {ref}")
    path = (root.parent / relative).resolve()
    try:
        path.relative_to(root.parent.resolve())
    except ValueError as error:
        raise BuildError(f"repository ref escaped root: {ref}") from error
    if require_exists and not path.exists():
        raise BuildError(f"repository ref missing: {ref}")
    return path


def _assert_public_safe(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        for token in _FORBIDDEN_PUBLIC_TOKENS:
            if token in payload:
                raise BuildError(f"public-safe token violation in {path}: {token!r}")
        if _EMAIL_RE.search(payload):
            raise BuildError(f"email leaked into public-safe output: {path}")


def _member_by_basename(archive: ZipFile, basename: str) -> tuple[str, bytes]:
    names = [
        item.filename for item in archive.infolist()
        if not item.is_dir() and item.filename.rsplit("/", 1)[-1] == basename
    ]
    if len(names) != 1:
        raise BuildError(f"source member resolution drift for {basename}: {len(names)}")
    return names[0], archive.read(names[0])


def _verify_source_package(package: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    """Verify all 21 declared members and derive the exact S02 source contract."""

    if not package.is_file():
        raise BuildError(f"source package missing: {package}")
    package_payload = package.read_bytes()
    if _sha256_bytes(package_payload) != SOURCE_PACKAGE_SHA256:
        raise BuildError("source package hash drift")

    try:
        with ZipFile(package) as archive:
            file_names = [item.filename for item in archive.infolist() if not item.is_dir()]
            manifest_names = [
                name for name in file_names
                if name.rsplit("/", 1)[-1] == "15_MANIFEST_SHA256_v2_0.csv"
            ]
            if len(manifest_names) != 1:
                raise BuildError("source SHA manifest member count drift")
            manifest_name = manifest_names[0]
            manifest_payload = archive.read(manifest_name)
            if _sha256_bytes(manifest_payload) != SOURCE_MANIFEST_SHA256:
                raise BuildError("source SHA manifest hash drift")
            reader = csv.DictReader(io.StringIO(manifest_payload.decode("utf-8-sig"), newline=""))
            rows = [dict(row) for row in reader]
            if reader.fieldnames != ["相对路径", "字节数", "SHA256"] or len(rows) != 21:
                raise BuildError("source SHA manifest structure drift")
            declared: set[str] = set()
            relevant_members: dict[str, dict[str, Any]] = {}
            for row in rows:
                relative = str(row.get("相对路径", ""))
                relative_path = PurePosixPath(relative)
                if (
                    not relative or relative_path.is_absolute()
                    or ".." in relative_path.parts or relative in declared
                ):
                    raise BuildError("unsafe or duplicate source manifest path")
                declared.add(relative)
                candidates = [
                    name for name in file_names
                    if name == relative or name.endswith("/" + relative)
                ]
                if len(candidates) != 1:
                    raise BuildError(f"source member resolution drift for {relative}")
                payload = archive.read(candidates[0])
                try:
                    expected_bytes = int(str(row.get("字节数", "")))
                except ValueError as error:
                    raise BuildError(f"invalid source byte count: {relative}") from error
                if len(payload) != expected_bytes or _sha256_bytes(payload) != str(row.get("SHA256", "")):
                    raise BuildError(f"source member integrity drift: {relative}")
                basename = relative.rsplit("/", 1)[-1]
                if basename in {
                    "01_KMFA_Codex_TaskPack_v2_0_界面交互全量重构_完整防遗漏.md",
                    "02_KMFA_Codex_Development_Roadmap_24_Stages_v2_0.md",
                    "02B_KMFA_Codex_Development_Roadmap_v2_0.json",
                    "10_KMFA_质量门禁与测试证据规范_v2_0.md",
                }:
                    relevant_members[basename] = {
                        "member": candidates[0], "bytes": len(payload),
                        "sha256": _sha256_bytes(payload),
                    }
            unlisted = [
                name for name in file_names if name != manifest_name
                and not any(name == item or name.endswith("/" + item) for item in declared)
            ]
            if len(file_names) != 22 or unlisted:
                raise BuildError("source package member accounting drift")

            _, roadmap_payload = _member_by_basename(
                archive, "02B_KMFA_Codex_Development_Roadmap_v2_0.json"
            )
            roadmap = json.loads(roadmap_payload.decode("utf-8"))
            if not isinstance(roadmap, dict):
                raise BuildError("source roadmap must be an object")
            expected_counts = (24, 72, 216)
            observed_counts = (
                roadmap.get("stage_count"), roadmap.get("phase_count"), roadmap.get("task_count")
            )
            if observed_counts != expected_counts:
                raise BuildError(f"source roadmap count drift: {observed_counts}")
            stages = roadmap.get("stages", [])
            stage_rows = [row for row in stages if isinstance(row, dict) and row.get("id") == "S02"]
            if len(stage_rows) != 1:
                raise BuildError("source S02 Stage resolution drift")
            stage = stage_rows[0]
            phases = stage.get("phases", [])
            if [row.get("id") for row in phases if isinstance(row, dict)] != ["P1", "P2", "P3"]:
                raise BuildError("S02 must contain exactly P1/P2/P3")
            task_contracts: list[dict[str, Any]] = []
            for phase in phases:
                phase_id = str(phase.get("id", ""))
                tasks = phase.get("tasks", [])
                if [row.get("id") for row in tasks if isinstance(row, dict)] != ["T01", "T02", "T03"]:
                    raise BuildError(f"{phase_id}: source task structure drift")
                for task in tasks:
                    composite_id = "S02" + phase_id + str(task.get("id", ""))
                    task_contracts.append({
                        "task_id": composite_id,
                        "phase_id": "S02-" + phase_id,
                        "phase_name": str(phase.get("name", "")),
                        "name": str(task.get("name", "")),
                        "action": str(task.get("action", "")),
                        "output": str(task.get("output", "")),
                        "acceptance": str(task.get("acceptance", "")),
                        "evidence": str(task.get("evidence", "")),
                        "stop": str(task.get("stop", "")),
                    })
            if len(task_contracts) != 9 or len({row["task_id"] for row in task_contracts}) != 9:
                raise BuildError("S02 source task accounting drift")

            _, taskpack_payload = _member_by_basename(
                archive, "01_KMFA_Codex_TaskPack_v2_0_界面交互全量重构_完整防遗漏.md"
            )
            taskpack_text = taskpack_payload.decode("utf-8-sig")
            required_no_review_text = "内部多视角复核不写进 Codex 正式任务包，避免误解。"
            if required_no_review_text not in taskpack_text:
                raise BuildError("R050 no-review-role source contract drift")

            _, roadmap_md_payload = _member_by_basename(
                archive, "02_KMFA_Codex_Development_Roadmap_24_Stages_v2_0.md"
            )
            roadmap_md = roadmap_md_payload.decode("utf-8-sig")
            stage_gate = (
                "本 Stage 所有 P0 Task 的验收、测试和证据通过；开放风险有明确后续任务；"
                "不得以时间到期替代质量证据。"
            )
            phase_gate = (
                "本 Phase 所有 Task 均有可复验输出；任何金额、原始数据、安全或权限停止条件未触发；"
                "相关中文文档同步。"
            )
            for required in (stage_gate, phase_gate, "下一 Stage 入口条件"):
                if required not in roadmap_md:
                    raise BuildError(f"source Roadmap gate text missing: {required}")

            _, quality_payload = _member_by_basename(
                archive, "10_KMFA_质量门禁与测试证据规范_v2_0.md"
            )
            quality_text = quality_payload.decode("utf-8-sig")
            marker = "每个 Task 的证据目录至少包含："
            after = quality_text.split(marker, 1)
            if len(after) != 2:
                raise BuildError("quality-spec evidence marker missing")
            match = re.search(r"```text\s*(.*?)```", after[1], re.DOTALL)
            if match is None:
                raise BuildError("quality-spec evidence slot block missing")
            evidence_slots = [line.strip() for line in match.group(1).splitlines() if line.strip()]
            expected_slots = [
                "manifest.json", "commands.txt", "test_results.json", "human_summary.md",
                "changed_files.txt", "screenshots/", "logs/", "exports/", "rollback.md",
                "open_risks.md",
            ]
            if evidence_slots != expected_slots:
                raise BuildError(f"quality-spec evidence slot drift: {evidence_slots}")
    except BadZipFile as error:
        raise BuildError("source package is not a readable ZIP") from error

    snapshot = {
        "name": SOURCE_PACKAGE_NAME,
        "bytes": len(package_payload),
        "sha256": SOURCE_PACKAGE_SHA256,
        "schema_version": str(roadmap.get("schema_version", "")),
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
        "manifest_member_count": 21,
        "verified_member_count": 21,
        "unmanifested_member_count": 0,
        "manifest_sha256": SOURCE_MANIFEST_SHA256,
        "s02_phase_count": 3,
        "s02_task_count": 9,
        "s02_formal_stage_review_task_present": False,
        "r050_no_review_role_task_verified": True,
        "members": relevant_members,
        "stage_contract": {
            "stage_id": "S02",
            "name": str(stage.get("name", "")),
            "goal": str(stage.get("goal", "")),
            "estimate": str(stage.get("estimate", "")),
            "stage_gate": stage_gate,
            "phase_gate": phase_gate,
        },
    }
    return snapshot, task_contracts, evidence_slots


def _validation_by_id(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        validation_id = str(row.get("validation_id", ""))
        if not validation_id or validation_id in result:
            raise BuildError("validation receipt IDs must be unique and non-empty")
        result[validation_id] = row
    return result


def _receipt_pass(row: Optional[Mapping[str, Any]], command: Optional[str] = None) -> bool:
    if row is None:
        return False
    if command is not None and row.get("command") != command:
        return False
    return row.get("result") == "PASS" and row.get("exit_code") == 0


def _load_phase_context(root: Path) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for phase_id, spec in PHASES.items():
        manifest_path = _repo_path(root, str(spec["manifest_ref"]))
        manifest_payload = manifest_path.read_bytes()
        manifest = json.loads(manifest_payload)
        if not isinstance(manifest, dict):
            raise BuildError(f"{phase_id}: manifest must be an object")
        content_hash_valid = manifest.get("content_hash") == _content_hash(manifest)
        validation_path = _repo_path(root, str(spec["validation_ref"]))
        validations = _read_jsonl(validation_path)
        tasks = manifest.get("tasks", [])
        task_rows = {
            str(row.get("task_id", "")): row for row in tasks if isinstance(row, dict)
        } if isinstance(tasks, list) else {}
        contexts[phase_id] = {
            "manifest": manifest,
            "manifest_ref": spec["manifest_ref"],
            "manifest_bytes": len(manifest_payload),
            "manifest_sha256": _sha256_bytes(manifest_payload),
            "manifest_content_hash": manifest.get("content_hash"),
            "manifest_content_hash_valid": content_hash_valid,
            "validation_ref": spec["validation_ref"],
            "validations": validations,
            "validations_by_id": _validation_by_id(validations),
            "completion_ref": spec["completion_ref"],
            "test_ref": spec["test_ref"],
            "rollback_ref": spec["rollback_ref"],
            "task_rows": task_rows,
        }
    return contexts


def _contract_row(
    contract_id: str,
    name: str,
    expected: Any,
    observed: Any,
    evidence_refs: Sequence[str],
    boundary: str,
    *,
    blocking: bool = True,
) -> dict[str, Any]:
    return {
        "contract_id": contract_id,
        "name": name,
        "status": "PASS" if observed == expected else "FAIL",
        "expected": expected,
        "observed": observed,
        "evidence_refs": list(evidence_refs),
        "blocking": blocking,
        "boundary": boundary,
    }


def _cross_phase_contracts(
    root: Path,
    source_snapshot: Mapping[str, Any],
    source_tasks: Sequence[Mapping[str, Any]],
    phases: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    p1_requirements = _read_csv(_repo_path(root, P1_REQUIREMENTS_REF))
    p1_business = _read_csv(_repo_path(root, P1_BUSINESS_REF))
    p1_scope = _read_csv(_repo_path(root, P1_SCOPE_REF))
    p2_trace = _read_csv(_repo_path(root, P2_TRACE_REF))
    p2_lineage = _read_json(_repo_path(root, P2_LINEAGE_REF))
    p3_scope = _read_csv(_repo_path(root, P3_SCOPE_REF))
    p3_prohibitions = _read_csv(_repo_path(root, P3_PROHIBITION_REF))
    p3_change = _read_json(_repo_path(root, P3_CHANGE_REF))
    s01_review = _read_json(_repo_path(root, S01_REVIEW_REF))
    project_governance = _repo_path(root, PROJECT_GOVERNANCE_REF).read_text(encoding="utf-8")

    p1_manifest = phases["S02-P1"]["manifest"]
    p2_manifest = phases["S02-P2"]["manifest"]
    p3_manifest = phases["S02-P3"]["manifest"]
    p1_req_ids = {row.get("requirement_id", "") for row in p1_requirements}
    p2_req_ids = {row.get("requirement_id", "") for row in p2_trace}
    p3_req_ids = {
        row.get("scope_item_id", "") for row in p3_scope
        if row.get("scope_item_type") == "REQUIREMENT"
    }
    p1_business_ids = {row.get("business_line_id", "") for row in p1_business}
    p3_business_ids = {
        row.get("scope_item_id", "") for row in p3_scope
        if row.get("scope_item_type") == "BUSINESS_LINE"
    }
    scope_types = Counter(row.get("scope_item_type", "") for row in p3_scope)
    phase_task_ids = {
        task_id for context in phases.values() for task_id in context["task_rows"]
    }
    source_task_ids = {str(row.get("task_id", "")) for row in source_tasks}
    s01_gate = s01_review.get("stage_gate", {})
    s01_expected = {
        "lifecycle": "BLOCKED", "acceptance": "NOT_PASSED", "decision": "NO_GO",
        "s02_entry_allowed": False,
    }
    s01_observed = {
        "lifecycle": s01_gate.get("stage_lifecycle_status"),
        "acceptance": s01_gate.get("stage_acceptance_status"),
        "decision": s01_gate.get("decision"),
        "s02_entry_allowed": s01_gate.get("s02_entry_allowed"),
    }
    governance_s01_observed = {
        "lifecycle": 's01_stage_review_lifecycle_status: "BLOCKED"' in project_governance,
        "acceptance": 's01_stage_review_acceptance_status: "NOT_PASSED"' in project_governance,
        "decision": 's01_stage_review_decision: "NO_GO"' in project_governance,
        "planning_bridge_only": 's01_controlled_transition_product_implementation_allowed: false' in project_governance,
    }

    contracts = [
        _contract_row(
            "S02REV-C01", "锁定源包结构",
            {"stages": 24, "phases": 72, "tasks": 216, "s02_phases": 3, "s02_tasks": 9},
            {
                "stages": source_snapshot.get("stage_count"),
                "phases": source_snapshot.get("phase_count"),
                "tasks": source_snapshot.get("task_count"),
                "s02_phases": source_snapshot.get("s02_phase_count"),
                "s02_tasks": source_snapshot.get("s02_task_count"),
            },
            [], "锁定 ZIP 21/21 member integrity；review overlay 不计入 216 Task。",
        ),
        _contract_row(
            "S02REV-C02", "Roadmap Task 边界",
            {"source_task_ids": sorted(source_task_ids), "formal_review_task": False, "p4_present": False},
            {
                "source_task_ids": sorted(phase_task_ids),
                "formal_review_task": source_snapshot.get("s02_formal_stage_review_task_present"),
                "p4_present": any(str(row).startswith("S02P4") for row in phase_task_ids),
            },
            [README_REF], "V015_S02_STAGE_REVIEW 是治理 overlay，不是 P4 或第十个 Task。",
        ),
        _contract_row(
            "S02REV-C03", "P1 需求与范围计数",
            {"requirements": 55, "p0": 46, "p1": 8, "p2": 1, "business_lines": 10, "capabilities": 37},
            {
                "requirements": len(p1_requirements),
                "p0": sum(row.get("priority") == "P0" for row in p1_requirements),
                "p1": sum(row.get("priority") == "P1" for row in p1_requirements),
                "p2": sum(row.get("priority") == "P2" for row in p1_requirements),
                "business_lines": len(p1_business), "capabilities": len(p1_scope),
            },
            [P1_REQUIREMENTS_REF, P1_BUSINESS_REF, P1_SCOPE_REF],
            "这些是规划总账，不继承产品验收。",
        ),
        _contract_row(
            "S02REV-C04", "P2 需求追溯计数",
            {"requirements": 55, "normalized_bindings": 134, "p0_p1_covered": 54},
            {
                "requirements": len(p2_req_ids),
                "normalized_bindings": len(p2_trace),
                "p0_p1_covered": len({row.get("requirement_id") for row in p2_trace if row.get("priority") in {"P0", "P1"}}),
            },
            [P2_TRACE_REF], "追溯映射是规划合同，不是 runtime 实现。",
        ),
        _contract_row(
            "S02REV-C05", "P2 lineage 真实性",
            {"actual_lineage_record_count": 0, "lineage_full_check_complete": False, "formal_report_allowed": False},
            {
                "actual_lineage_record_count": p2_lineage.get("actual_lineage_record_count"),
                "lineage_full_check_complete": p2_lineage.get("lineage_full_check_complete"),
                "formal_report_allowed": p2_lineage.get("formal_report_allowed"),
            },
            [P2_LINEAGE_REF], "不得把字段合同误称实际 lineage 或正式报告证据。",
        ),
        _contract_row(
            "S02REV-C06", "P2 公式/参数规划边界",
            {"definitions": 22, "controls": 38, "runtime_enabled": 0, "product_claims": 0},
            {
                "definitions": p2_manifest.get("formula_accounting", {}).get("formula_model_count"),
                "controls": p2_manifest.get("formula_accounting", {}).get("parameter_control_count"),
                "runtime_enabled": p2_manifest.get("formula_accounting", {}).get("runtime_enabled_count"),
                "product_claims": p2_manifest.get("formula_accounting", {}).get("product_implementation_claim_count"),
            },
            [str(PHASES["S02-P2"]["manifest_ref"])], "无 executable fixture/runtime/report artifact，不得启用。",
        ),
        _contract_row(
            "S02REV-C07", "P3 scope 计数",
            {"rows": 103, "requirements": 55, "business_lines": 10, "capabilities": 37, "policies": 1},
            {
                "rows": len(p3_scope), "requirements": scope_types["REQUIREMENT"],
                "business_lines": scope_types["BUSINESS_LINE"],
                "capabilities": scope_types["CAPABILITY"], "policies": scope_types["POLICY"],
            },
            [P3_SCOPE_REF], "P3 锁定优先级，不授权实现。",
        ),
        _contract_row(
            "S02REV-C08", "P3 禁止事项硬停止",
            {"rows": 51, "runtime_guards": 0, "implemented": 0, "override_allowed": 0},
            {
                "rows": len(p3_prohibitions),
                "runtime_guards": sum(row.get("runtime_guard_implemented") == "true" for row in p3_prohibitions),
                "implemented": sum(row.get("prohibited_action_implemented_in_s02_p3") == "true" for row in p3_prohibitions),
                "override_allowed": sum(
                    row.get("change_control_can_override") == "true" or row.get("owner_authorization_can_override") == "true"
                    for row in p3_prohibitions
                ),
            },
            [P3_PROHIBITION_REF], "禁止付款/报税/开票/工资审批/外发完整报告/修改 raw。",
        ),
        _contract_row(
            "S02REV-C09", "P3 change-control 仅为 schema/planning",
            {"auditable_domains": 4, "change_types": 5, "required_fields": 36, "runtime_or_ci_hook": False},
            {
                "auditable_domains": len(p3_change.get("auditable_domains", [])),
                "change_types": len(p3_change.get("change_types", [])),
                "required_fields": len(p3_change.get("required_change_fields", [])),
                "runtime_or_ci_hook": p3_change.get("runtime_or_ci_hook_implemented_in_s02_p3"),
            },
            [P3_CHANGE_REF], "evaluator 只做 schema/planning completeness，不发出真实 merge 授权。",
        ),
        _contract_row(
            "S02REV-C10", "跨 Phase ID 一致",
            {"p1_p2_requirements": True, "p1_p3_requirements": True, "p1_p3_business_lines": True},
            {
                "p1_p2_requirements": p1_req_ids == p2_req_ids,
                "p1_p3_requirements": p1_req_ids == p3_req_ids,
                "p1_p3_business_lines": p1_business_ids == p3_business_ids,
            },
            [P1_REQUIREMENTS_REF, P2_TRACE_REF, P3_SCOPE_REF], "无孤儿 ID 或优先级旁路。",
        ),
        _contract_row(
            "S02REV-C11", "三个 Phase manifest 完整性",
            {phase_id: True for phase_id in PHASES},
            {phase_id: bool(context["manifest_content_hash_valid"]) for phase_id, context in phases.items()},
            [str(PHASES[phase_id]["manifest_ref"]) for phase_id in PHASES],
            "每个 predecessor manifest 必须通过 canonical content_hash 复算。",
        ),
        _contract_row(
            "S02REV-C12", "S01 历史状态不可改写",
            {"review_manifest": s01_expected, "governance_flags": {"lifecycle": True, "acceptance": True, "decision": True, "planning_bridge_only": True}},
            {"review_manifest": s01_observed, "governance_flags": governance_s01_observed},
            [S01_REVIEW_REF, PROJECT_GOVERNANCE_REF],
            "controlled transition amendment 只开放规划桥，不把 S01 改成 PASSED/GO。",
        ),
        _contract_row(
            "S02REV-C13", "S02 Stage 通过语义",
            {"planning_governance_only": True, "product_release_business_pass": False},
            {
                "planning_governance_only": True,
                "product_release_business_pass": any(
                    p3_manifest.get("downstream_actions", {}).get(key) is True
                    for key in (
                        "product_runtime_implementation_performed", "formal_report_generated",
                        "business_execution_performed", "github_upload_performed", "app_reinstall_performed",
                    )
                ),
            },
            [str(PHASES["S02-P3"]["manifest_ref"])],
            "Stage PASS 只代表 S02 规划治理合同通过。",
        ),
    ]
    failed = [row for row in contracts if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s02_cross_phase_contracts.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S02",
        "run_phase_id": RUN_PHASE_ID,
        "contracts": contracts,
        "accounting": {
            "total": len(contracts), "passed": len(contracts) - len(failed),
            "failed": len(failed), "blocking_failed": sum(row["blocking"] for row in failed),
        },
        "actual_lineage_record_count": p2_lineage.get("actual_lineage_record_count"),
        "lineage_full_check_complete": p2_lineage.get("lineage_full_check_complete"),
        "formal_report_allowed": p2_lineage.get("formal_report_allowed"),
        "public_safe_status": "PUBLIC_SAFE",
    }


def _risk_rows() -> list[dict[str, Any]]:
    return [
        {
            "risk_id": "RISK-KMFA-V015-S02-001", "severity": "P0", "status": "ROUTED_RESIDUAL",
            "risk": "actual_lineage_record_count 仍为 0，尚无真实字段级 lineage record。",
            "impact": "不得生成正式报告或声称 lineage full check 已完成。",
            "control": "维持 formal_report_allowed=false 与 lineage_full_check_complete=false。",
            "follow_up_stage_task": "S04P2T01", "plan_complete": True,
            "blocks_s02_stage_acceptance": False, "evidence_refs": P2_LINEAGE_REF,
        },
        {
            "risk_id": "RISK-KMFA-V015-S02-002", "severity": "P2", "status": "ROUTED_RESIDUAL",
            "risk": "Stage evidence 构建依赖外部 hash-bound TaskPack ZIP，clone 不是自包含复建。",
            "impact": "缺少锁定 ZIP 时 source-integrity exact rebuild 会 fail closed。",
            "control": "绑定 ZIP SHA-256 与 21/21 manifest；不得回退到未锁定镜像。",
            "follow_up_stage_task": "S24P2T03", "plan_complete": True,
            "blocks_s02_stage_acceptance": False, "evidence_refs": FINAL_ARTIFACT_REFS["cross_phase_contracts"],
        },
        {
            "risk_id": "RISK-KMFA-V015-S02-003", "severity": "P1", "status": "ROUTED_RESIDUAL",
            "risk": "change-control evaluator 仍仅做 schema/planning completeness；runtime/CI enforcement=false。",
            "impact": "不得将规划 evaluator 称为真实 merge eligibility 或 CI gate。",
            "control": "保持 runtime_or_ci_hook=false；后续实现与 mutation/e2e 另行验收。",
            "follow_up_stage_task": "S07P3T03", "plan_complete": True,
            "blocks_s02_stage_acceptance": False, "evidence_refs": P3_CHANGE_REF,
        },
    ]


def _task_evidence_contract(
    source_slots: Sequence[str],
    source_tasks: Sequence[Mapping[str, Any]],
    phases: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    accounted_slots = 0
    for source_task in source_tasks:
        task_id = str(source_task["task_id"])
        phase_id = str(source_task["phase_id"])
        phase = phases[phase_id]
        observed = phase["task_rows"].get(task_id, {})
        task_refs = list(observed.get("evidence_refs", [])) if isinstance(observed, dict) else []
        slot_rows = [
            {
                "slot": "manifest.json", "status": "INDEXED_EXISTING_EVIDENCE",
                "evidence_refs": [str(phase["manifest_ref"])], "not_applicable_reason": "",
            },
            {
                "slot": "commands.txt", "status": "INDEXED_EXISTING_EVIDENCE",
                "evidence_refs": [str(phase["validation_ref"])],
                "not_applicable_reason": "命令保留在 phase validation_results.jsonl；不复制。",
            },
            {
                "slot": "test_results.json", "status": "INDEXED_EXISTING_EVIDENCE",
                "evidence_refs": [str(phase["validation_ref"]), str(phase["test_ref"])],
                "not_applicable_reason": "结构化 receipt 与中文测试结果共同索引；不改写格式。",
            },
            {
                "slot": "human_summary.md", "status": "INDEXED_EXISTING_EVIDENCE",
                "evidence_refs": [str(phase["completion_ref"])] + task_refs,
                "not_applicable_reason": "Phase completion record 与 Task evidence refs 共同定位。",
            },
            {
                "slot": "changed_files.txt", "status": "INDEXED_BY_PHASE_MANIFEST",
                "evidence_refs": [str(phase["manifest_ref"])],
                "not_applicable_reason": "Phase manifest artifact_refs/integrity 为权威变更证据索引；不复制。",
            },
            {
                "slot": "screenshots/", "status": "NOT_APPLICABLE_WITH_REASON",
                "evidence_refs": [],
                "not_applicable_reason": "S02 是规划/治理 Stage，未执行 UI/runtime，不制造截图。",
            },
            {
                "slot": "logs/", "status": "INDEXED_EXISTING_EVIDENCE",
                "evidence_refs": [str(phase["validation_ref"])],
                "not_applicable_reason": "公开安全 validation receipt 是本 Stage 的命令日志索引。",
            },
            {
                "slot": "exports/", "status": "NOT_APPLICABLE_WITH_REASON",
                "evidence_refs": [],
                "not_applicable_reason": "S02 不生成业务导出或正式报告；不得制造 export。",
            },
            {
                "slot": "rollback.md", "status": "INDEXED_EXISTING_EVIDENCE",
                "evidence_refs": [str(phase["rollback_ref"])], "not_applicable_reason": "",
            },
            {
                "slot": "open_risks.md", "status": "INDEXED_BY_STAGE_REVIEW",
                "evidence_refs": [FINAL_ARTIFACT_REFS["review_findings"], FINAL_ARTIFACT_REFS["open_risk_register"]],
                "not_applicable_reason": "逐 Task 风险统一由 Stage review findings/risk register 去重登记。",
            },
        ]
        if [row["slot"] for row in slot_rows] != list(source_slots):
            raise BuildError(f"{task_id}: evidence slot mapping drift")
        accounted_slots += len(slot_rows)
        tasks.append({
            "task_id": task_id, "phase_id": phase_id,
            "task_name": str(source_task["name"]),
            "physical_task_directory_materialized": False,
            "evidence_pack_strategy": "REFERENCE_ONLY_NO_DUPLICATION",
            "slots": slot_rows,
        })
    return {
        "schema_version": "kmfa.v015.s02_task_evidence_contract.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S02",
        "run_phase_id": RUN_PHASE_ID,
        "source_required_slots": list(source_slots),
        "strategy": {
            "kind": "REFERENCE_ONLY_NO_DUPLICATION",
            "physical_task_directories_materialized": False,
            "auditable_slot_mapping_required": True,
            "not_applicable_requires_reason": True,
            "predecessor_artifacts_copied": False,
        },
        "task_count": len(tasks),
        "tasks": tasks,
        "accounting": {
            "task_count": len(tasks), "required_slot_count_per_task": len(source_slots),
            "expected_slot_mapping_count": len(tasks) * len(source_slots),
            "accounted_slot_mapping_count": accounted_slots,
            "missing_slot_mapping_count": len(tasks) * len(source_slots) - accounted_slots,
        },
        "public_safe_status": "PUBLIC_SAFE",
    }


def _fixed_status(condition: bool) -> str:
    return "FIXED_VALIDATED" if condition else "OPEN"


def _finding_rows(
    root: Path,
    phases: Mapping[str, Mapping[str, Any]],
    task_evidence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    p1_receipts = phases["S02-P1"]["validations_by_id"]
    p2_receipts = phases["S02-P2"]["validations_by_id"]
    p3_receipts = phases["S02-P3"]["validations_by_id"]
    p1_diff = p1_receipts.get("phase_diff_whitespace_check")
    p2_gov = p2_receipts.get("governance_sync_check")
    p2_rebuild = p2_receipts.get("exact_core_rebuild_check")
    p3_diff = p3_receipts.get("phase_diff_whitespace_check")
    p1_fixed = _receipt_pass(p1_diff) and str(p1_diff.get("command", "")).startswith("git diff --check ")
    p2_fixed = (
        _receipt_pass(p2_gov) and "--base-ref HEAD" not in str(p2_gov.get("command", ""))
        and _receipt_pass(p2_rebuild)
        and "build_v015_s02_p2_end_to_end_traceability.py --check" in str(p2_rebuild.get("command", ""))
    )
    p3_fixed = _receipt_pass(p3_diff) and str(p3_diff.get("command", "")).startswith("git diff --check ")

    scope_summary = _repo_path(
        root, "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/human/scope_gate_zh.md"
    ).read_text(encoding="utf-8")
    p3_protocol = _read_json(_repo_path(root, P3_CHANGE_REF))
    evaluator_fixed = (
        p3_protocol.get("runtime_or_ci_hook_implemented_in_s02_p3") is False
        and "schema/planning completeness" in scope_summary
        and "不发出真实 merge 授权" in scope_summary
    )

    readme = _repo_path(root, README_REF).read_text(encoding="utf-8")
    metadata_project = _repo_path(root, METADATA_PROJECT_REF).read_text(encoding="utf-8")
    stage_status = _repo_path(root, METADATA_STAGE_STATUS_REF).read_text(encoding="utf-8")
    cross_plane_fixed = all(
        token in readme for token in (RUN_PHASE_ID, TASK_ID, ACCEPTANCE_ID)
    ) and all(
        token in metadata_project for token in (RUN_PHASE_ID, TASK_ID, ACCEPTANCE_ID)
    ) and all(
        token in stage_status for token in (
            "V015_S02_P2_END_TO_END_TRACEABILITY", "V015_S02_P3_SCOPE_GATE", RUN_PHASE_ID,
        )
    )
    model_registry = _repo_path(root, METADATA_MODEL_REGISTRY_REF).read_text(encoding="utf-8")
    model_mirror_fixed = (
        "V015" in model_registry
        and ("S02-STAGE-REVIEW" in model_registry or RUN_PHASE_ID in model_registry)
    )
    evidence_fixed = (
        task_evidence.get("task_count") == 9
        and task_evidence.get("accounting", {}).get("accounted_slot_mapping_count") == 90
        and task_evidence.get("accounting", {}).get("missing_slot_mapping_count") == 0
    )

    rows = [
        {
            "finding_id": "S02REV-F001", "severity": "P1", "finding_class": "VALIDATION_EVIDENCE",
            "status": _fixed_status(p3_fixed), "title": "P3 structured receipt 曾用 exact-builder check 代替真实 diff/public scan",
            "source_ref": str(PHASES["S02-P3"]["validation_ref"]),
            "reproduction": "旧 structured_public_diff_checks 仅执行 builder --check；且 predecessor diff 曾检出 3 个 Markdown trailing blank EOF。",
            "impact": "旧 receipt 不能证明 whitespace/public-diff 门禁。",
            "fix_ref": str(PHASES["S02-P3"]["validation_ref"]),
            "revalidation_ref": str(PHASES["S02-P3"]["test_ref"]),
            "blocks_stage_acceptance": not p3_fixed,
        },
        {
            "finding_id": "S02REV-F002", "severity": "P1", "finding_class": "VALIDATION_EVIDENCE",
            "status": _fixed_status(p1_fixed), "title": "P1 receipt 曾为不可执行 procedure label",
            "source_ref": str(PHASES["S02-P1"]["validation_ref"]),
            "reproduction": "旧 command='structured parse plus ...' 直接重放 exit 127。",
            "impact": "历史 receipt 不可独立复放。",
            "fix_ref": str(PHASES["S02-P1"]["validation_ref"]),
            "revalidation_ref": str(PHASES["S02-P1"]["test_ref"]),
            "blocks_stage_acceptance": not p1_fixed,
        },
        {
            "finding_id": "S02REV-F003", "severity": "P1", "finding_class": "VALIDATION_EVIDENCE",
            "status": _fixed_status(p2_fixed), "title": "P2 governance HEAD no-op 与误名 receipt",
            "source_ref": str(PHASES["S02-P2"]["validation_ref"]),
            "reproduction": "旧 governance sync 使用 --base-ref HEAD；旧 structured_public_diff_checks 实际仅 builder --check。",
            "impact": "clean tree 下无法覆盖 Phase 变更，且 receipt 名义与命令不一致。",
            "fix_ref": str(PHASES["S02-P2"]["validation_ref"]),
            "revalidation_ref": str(PHASES["S02-P2"]["test_ref"]),
            "blocks_stage_acceptance": not p2_fixed,
        },
        {
            "finding_id": "S02REV-F004", "severity": "P1", "finding_class": "SEMANTIC_OVERCLAIM",
            "status": _fixed_status(evaluator_fixed), "title": "P3 schema completeness 曾被误称真实 merge eligibility",
            "source_ref": P3_CHANGE_REF,
            "reproduction": "构造不存在 registry/artifact/audit refs 的完整 record，旧 evaluator 仍可能返回 merge_eligible。",
            "impact": "可能把规划 schema checker 误解成 runtime/CI merge enforcement。",
            "fix_ref": "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/human/scope_gate_zh.md",
            "revalidation_ref": str(PHASES["S02-P3"]["test_ref"]),
            "blocks_stage_acceptance": not evaluator_fixed,
        },
        {
            "finding_id": "S02REV-F005", "severity": "P1", "finding_class": "CROSS_PLANE_DRIFT",
            "status": _fixed_status(cross_plane_fixed), "title": "README 与 metadata status plane 曾停留在旧 S02 状态",
            "source_ref": README_REF + ";" + METADATA_PROJECT_REF + ";" + METADATA_STAGE_STATUS_REF,
            "reproduction": "对照 canonical governance 与 README/metadata，旧镜像缺 P2/P3/review。",
            "impact": "用户入口与机器镜像会误报当前开发 gate。",
            "fix_ref": README_REF + ";" + METADATA_PROJECT_REF + ";" + METADATA_STAGE_STATUS_REF,
            "revalidation_ref": FINAL_ARTIFACT_REFS["validation_results"],
            "blocks_stage_acceptance": not cross_plane_fixed,
        },
        {
            "finding_id": "S02REV-F006", "severity": "P2", "finding_class": "CROSS_PLANE_DRIFT",
            "status": _fixed_status(model_mirror_fixed), "title": "metadata model registry 缺 v1.5 mirror 或权威性声明",
            "source_ref": METADATA_MODEL_REGISTRY_REF,
            "reproduction": "旧 registry 全文件无 V015 Stage-review binding。",
            "impact": "模型/公式镜像可能被误读为当前权威状态。",
            "fix_ref": METADATA_MODEL_REGISTRY_REF,
            "revalidation_ref": FINAL_ARTIFACT_REFS["validation_results"],
            "blocks_stage_acceptance": not model_mirror_fixed,
        },
        {
            "finding_id": "S02REV-F007", "severity": "P2", "finding_class": "EVIDENCE_PACKAGING",
            "status": _fixed_status(evidence_fixed), "title": "九个 Task 缺质量规范 §5 evidence-slot 映射",
            "source_ref": "SOURCE_PACKAGE_TOKEN::10_KMFA_质量门禁与测试证据规范_v2_0.md",
            "reproduction": "Phase-level evidence 存在，但旧状态无 9 Task × 10 slot 审计索引。",
            "impact": "Stage review 无法逐 Task 证明必备证据槽已登记或明确 N/A。",
            "fix_ref": FINAL_ARTIFACT_REFS["task_evidence_contract"],
            "revalidation_ref": FINAL_ARTIFACT_REFS["validation_results"],
            "blocks_stage_acceptance": not evidence_fixed,
        },
    ]
    return rows


def _validation_template_rows() -> list[dict[str, Any]]:
    return [
        {
            "validation_id": validation_id, "command": command,
            "expected_result": "PASS", "expected_exit_code": 0,
            "blocking": True,
        }
        for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items()
    ]


def _pending_validation_rows() -> list[dict[str, Any]]:
    return [
        {
            "validation_id": validation_id, "command": command,
            "result": "PENDING", "exit_code": None,
        }
        for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items()
    ]


def _validation_accounting(output_root: Path) -> dict[str, Any]:
    path = output_root / VALIDATION_RESULTS_RELATIVE
    if not path.is_file():
        return {
            "expected": len(EXPECTED_VALIDATION_RECEIPTS), "recorded": 0,
            "passed": 0, "pending": 0, "failed_or_drifted": 0,
            "missing_ids": list(EXPECTED_VALIDATION_RECEIPTS), "unexpected_ids": [],
            "all_exact_pass": False,
        }
    rows = _read_jsonl(path)
    by_id = _validation_by_id(rows)
    passed = 0
    pending = 0
    failed_or_drifted = 0
    for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items():
        if _receipt_pass(by_id.get(validation_id), command):
            passed += 1
        elif (
            validation_id in by_id
            and by_id[validation_id].get("command") == command
            and by_id[validation_id].get("result") == "PENDING"
            and by_id[validation_id].get("exit_code") is None
        ):
            pending += 1
        elif validation_id in by_id:
            failed_or_drifted += 1
    missing = [item for item in EXPECTED_VALIDATION_RECEIPTS if item not in by_id]
    unexpected = [item for item in by_id if item not in EXPECTED_VALIDATION_RECEIPTS]
    all_exact = not missing and not unexpected and not failed_or_drifted and passed == len(EXPECTED_VALIDATION_RECEIPTS)
    return {
        "expected": len(EXPECTED_VALIDATION_RECEIPTS), "recorded": len(rows),
        "passed": passed, "pending": pending, "failed_or_drifted": failed_or_drifted,
        "missing_ids": missing, "unexpected_ids": unexpected,
        "all_exact_pass": all_exact,
    }


def _normalize_output_root(root: Path, output_root: Optional[Path]) -> Path:
    if output_root is None:
        return root / OUTPUT_ROOT_RELATIVE
    candidate = Path(output_root).resolve()
    if candidate.name == "machine":
        return candidate.parent
    if candidate.name == "stage_artifacts":
        return candidate / OUTPUT_ROOT_RELATIVE.name
    return candidate


def _phase_evidence_rows(phases: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for phase_id in ("S02-P1", "S02-P2", "S02-P3"):
        context = phases[phase_id]
        manifest = context["manifest"]
        result = manifest.get("phase_result", {})
        accounting = manifest.get("task_accounting", {})
        rows.append({
            "phase_id": phase_id,
            "manifest_ref": context["manifest_ref"],
            "manifest_bytes": context["manifest_bytes"],
            "manifest_sha256": context["manifest_sha256"],
            "manifest_content_hash": context["manifest_content_hash"],
            "manifest_content_hash_valid": context["manifest_content_hash_valid"],
            "validation_results_ref": context["validation_ref"],
            "execution_status": result.get("execution_status"),
            "acceptance_status": result.get("acceptance_status"),
            "accepted_tasks": accounting.get("accepted"),
            "total_tasks": accounting.get("total"),
        })
    return rows


def _review_matrix(
    source_snapshot: Mapping[str, Any],
    source_tasks: Sequence[Mapping[str, Any]],
    phases: Mapping[str, Mapping[str, Any]],
    contracts: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    risks: Sequence[Mapping[str, Any]],
    task_evidence: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    task_rows: list[dict[str, Any]] = []
    for source_task in source_tasks:
        phase_id = str(source_task["phase_id"])
        task_id = str(source_task["task_id"])
        observed = phases[phase_id]["task_rows"].get(task_id, {})
        task_rows.append({
            "task_id": task_id,
            "phase_id": phase_id,
            "phase_name": source_task["phase_name"],
            "name": source_task["name"],
            "source_contract": {
                "action": source_task["action"], "output": source_task["output"],
                "acceptance": source_task["acceptance"], "evidence": source_task["evidence"],
                "stop": source_task["stop"],
            },
            "observed": {
                "execution_status": observed.get("execution_status", "MISSING"),
                "acceptance_status": observed.get("acceptance_status", "MISSING"),
                "evidence_refs": list(observed.get("evidence_refs", [])),
                "phase_manifest_ref": phases[phase_id]["manifest_ref"],
                "stop_condition_status": "NOT_TRIGGERED_BY_ACCEPTED_PHASE_EVIDENCE",
            },
            "evidence_pack_ref": FINAL_ARTIFACT_REFS["task_evidence_contract"],
        })

    accepted = sum(row["observed"]["acceptance_status"] == "PASSED" for row in task_rows)
    executed = sum(row["observed"]["execution_status"] == "EXECUTION_COMPLETE" for row in task_rows)
    open_findings = [row for row in findings if row.get("status") != "FIXED_VALIDATED"]
    blocking_findings = [row for row in open_findings if row.get("blocks_stage_acceptance") is True]
    risk_plan_gaps = [row for row in risks if row.get("plan_complete") is not True]
    blocking_risks = [row for row in risks if row.get("blocks_s02_stage_acceptance") is True]
    cross_failed = int(contracts.get("accounting", {}).get("blocking_failed", 0))
    evidence_complete = (
        task_evidence.get("accounting", {}).get("missing_slot_mapping_count") == 0
        and task_evidence.get("task_count") == 9
    )
    stage_pass = (
        accepted == executed == len(task_rows) == 9
        and not blocking_findings and not risk_plan_gaps and not blocking_risks
        and cross_failed == 0 and evidence_complete
        and validation.get("all_exact_pass") is True
    )
    stage_gate = {
        "review_execution_status": "COMPLETED" if stage_pass else "IN_PROGRESS",
        "evidence_validation_status": "PASS" if not blocking_findings and cross_failed == 0 and evidence_complete else "FAIL",
        "final_validation_status": "PASS" if stage_pass else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if stage_pass else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if stage_pass else "PENDING",
        "decision": "GO_TO_S03_P1_ONLY" if stage_pass else "REMAIN_IN_S02_STAGE_REVIEW",
        "planning_governance_stage_passed": stage_pass,
        "product_release_business_passed": False,
        "s03_p1_entry_allowed": stage_pass,
    }
    next_entry = {
        "next_gate_id": "S03-P1" if stage_pass else "S02-STAGE-REVIEW",
        "next_allowed_run": "S03-P1" if stage_pass else "S02-STAGE-REVIEW-FIX",
        "s03_p1_entry_allowed": stage_pass,
        "s03_p1_started": False,
        "s03_plus_entry_allowed": False,
        "product_implementation_allowed": False,
    }
    downstream = {
        "s03_p1_started": False, "s03_plus_started": False,
        "product_runtime_implementation_performed": False,
        "runtime_or_ci_change_control_enforcement_implemented": False,
        "api_implementation_performed": False, "database_implementation_performed": False,
        "ui_implementation_performed": False, "actual_lineage_materialized": False,
        "lineage_full_check_complete": False, "formal_report_generated": False,
        "raw_business_content_read": False, "raw_root_listed_or_inventoried": False,
        "raw_inbox_mutated": False, "business_execution_performed": False,
        "github_upload_performed": False, "app_reinstall_performed": False,
    }
    return {
        "schema_version": "kmfa.v015.s02_stage_review_matrix.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S02",
        "run_phase_id": RUN_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID,
        "review_base_commit": REVIEW_BASE_COMMIT,
        "counted_as_taskpack_task": False,
        "current_phase_kind": "GOVERNANCE_OVERLAY",
        "current_phase_is_taskpack_roadmap_phase": False,
        "current_task_is_taskpack_roadmap_task": False,
        "source_package": dict(source_snapshot),
        "task_accounting": {
            "total": len(task_rows), "execution_complete": executed,
            "accepted": accepted, "not_accepted": len(task_rows) - accepted,
            "all_source_tasks_explicitly_indexed": len(task_rows) == 9,
            "triggered_stop_condition_count": 0,
        },
        "tasks": task_rows,
        "phase_summaries": _phase_evidence_rows(phases),
        "review_finding_accounting": {
            "total": len(findings), "fixed_validated": len(findings) - len(open_findings),
            "open": len(open_findings), "blocking_open": len(blocking_findings),
            "p0_p1_open": sum(row.get("severity") in {"P0", "P1"} for row in open_findings),
        },
        "cross_phase_accounting": dict(contracts.get("accounting", {})),
        "open_risk_accounting": {
            "total": len(risks), "p0": sum(row.get("severity") == "P0" for row in risks),
            "p1": sum(row.get("severity") == "P1" for row in risks),
            "p2": sum(row.get("severity") == "P2" for row in risks),
            "blocking": len(blocking_risks), "plan_gap_count": len(risk_plan_gaps),
            "p0_p1_plan_gap_count": sum(
                row.get("severity") in {"P0", "P1"} and row.get("plan_complete") is not True
                for row in risks
            ),
        },
        "validation_receipt_accounting": dict(validation),
        "stage_gate": stage_gate,
        "next_entry_gate": next_entry,
        "downstream_actions": downstream,
        "public_safe_status": "PUBLIC_SAFE",
    }


def _report_markdown(
    matrix: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    risks: Sequence[Mapping[str, Any]],
) -> bytes:
    gate = matrix["stage_gate"]
    tasks = matrix["task_accounting"]
    finding_counts = matrix["review_finding_accounting"]
    lines = [
        "# KMFA v1.5 S02 Stage Review/Fix 报告",
        "",
        "## Stage 结果",
        "",
        f"- 生命周期/验收/决策：`{gate['stage_lifecycle_status']} / {gate['stage_acceptance_status']} / {gate['decision']}`。",
        "- 本 gate 是独立治理 overlay，不是 Roadmap P4 或第 10 个 Task。",
        "- 通过语义仅限 S02 需求总账、追溯、范围与变更控制规划治理；不代表产品、发布、业务或 raw gate 通过。",
        "",
        "## 完成 Task",
        "",
        f"- S02 source Tasks：{tasks['accepted']}/{tasks['total']} accepted，{tasks['execution_complete']}/{tasks['total']} execution complete。",
    ]
    for row in matrix["tasks"]:
        lines.append(f"- `{row['task_id']}` {row['name']}：`{row['observed']['acceptance_status']}`。")
    lines.extend([
        "",
        "## 未完成 Task",
        "",
        "- 无额外 Roadmap Task；Stage review 本身不计入 source Task。" if tasks["accepted"] == 9 else "- 存在未通过 source Task，Stage 保持 PENDING。",
        "",
        "## Findings",
        "",
        f"- 总计 {finding_counts['total']}；FIXED_VALIDATED {finding_counts['fixed_validated']}；open {finding_counts['open']}；blocking open {finding_counts['blocking_open']}。",
    ])
    for row in findings:
        lines.append(f"- `{row['finding_id']}` `{row['severity']}` `{row['status']}`：{row['title']}。")
    lines.extend([
        "",
        "## 测试命令与结果",
        "",
        f"- exact validation receipts：{matrix['validation_receipt_accounting']['passed']}/{matrix['validation_receipt_accounting']['expected']} PASS。",
        f"- final validation：`{gate['final_validation_status']}`。",
        "",
        "## 证据文件",
        "",
        f"- 9-Task matrix：`{FINAL_ARTIFACT_REFS['review_matrix']}`。",
        f"- cross-phase contracts：`{FINAL_ARTIFACT_REFS['cross_phase_contracts']}`。",
        f"- 9×10 evidence-slot mapping：`{FINAL_ARTIFACT_REFS['task_evidence_contract']}`。",
        "",
        "## 修改文件摘要",
        "",
        "- 本复审只修复证据可重放性、语义过度声称、治理镜像与 Task evidence-slot 索引；不实现产品能力。",
        "",
        "## 回滚方式",
        "",
        f"- 以 review base `{REVIEW_BASE_COMMIT}` 为核验基线；仅回滚本复审提交，不改 predecessor 历史事实或 raw。",
        "",
        "## 开放风险",
        "",
    ])
    for row in risks:
        lines.append(f"- `{row['risk_id']}` `{row['severity']}` -> `{row['follow_up_stage_task']}`：{row['risk']}。")
    lines.extend([
        "",
        "## 下一 Stage 入口条件",
        "",
        "- 仅当本报告为 `COMPLETED / PASSED / GO_TO_S03_P1_ONLY` 时，下一独立 Run 可进入 S03-P1。",
        "- 本 Run 未启动 S03-P1；未读取/列举/修改 raw，未上传 GitHub，未重装 App，未执行业务动作。",
        "",
    ])
    return "\n".join(lines).encode("utf-8")


def _rollback_markdown(matrix: Mapping[str, Any]) -> bytes:
    return (
        "# KMFA v1.5 S02 Stage Review/Fix 回滚计划\n\n"
        "- 回滚单元：仅本 Stage review/fix 的代码、治理镜像和 public-safe evidence。\n"
        f"- 核验基线：`{REVIEW_BASE_COMMIT}`。\n"
        "- 回滚后状态：S02 恢复 `IN_PROGRESS / PENDING`，下一 gate 恢复 `S02-STAGE-REVIEW-FIX`。\n"
        "- 不回滚或改写 S02-P1/P2/P3 已提交历史事实；若 predecessor receipt 修复需撤销，应以追加更正记录说明。\n"
        "- 不访问、删除、移动、覆盖或修改 raw；不执行 GitHub upload 或 App reinstall。\n"
        f"- 当前生成态：`{matrix['stage_gate']['stage_lifecycle_status']} / {matrix['stage_gate']['stage_acceptance_status']}`。\n"
    ).encode("utf-8")


def _test_results_markdown(matrix: Mapping[str, Any]) -> bytes:
    validation = matrix["validation_receipt_accounting"]
    lines = [
        "# KMFA v1.5 S02 Stage Review/Fix 测试结果",
        "",
        f"- expected receipts：{validation['expected']}。",
        f"- exact PASS：{validation['passed']}。",
        f"- pending：{validation.get('pending', 0)}；missing：{len(validation['missing_ids'])}；unexpected：{len(validation['unexpected_ids'])}；failed/drifted：{validation['failed_or_drifted']}。",
        f"- final validation：`{matrix['stage_gate']['final_validation_status']}`。",
        "",
    ]
    for validation_id, command in EXPECTED_VALIDATION_RECEIPTS.items():
        status = "PASS" if validation["all_exact_pass"] else "PENDING_OR_RECHECK_REQUIRED"
        lines.append(f"- `{validation_id}` `{status}`：`{command}`")
    lines.extend([
        "",
        "边界：测试只验证 S02 规划治理 Stage review；actual lineage 仍为 0，runtime/CI change-control enforcement 仍为 false。",
        "",
    ])
    return "\n".join(lines).encode("utf-8")


def _build_review_state(
    root: Path,
    package: Path,
    output_root: Path,
) -> dict[str, Any]:
    source_snapshot, source_tasks, source_slots = _verify_source_package(package)
    phases = _load_phase_context(root)
    contracts = _cross_phase_contracts(root, source_snapshot, source_tasks, phases)
    risks = _risk_rows()
    task_evidence = _task_evidence_contract(source_slots, source_tasks, phases)
    findings = _finding_rows(root, phases, task_evidence)
    validation = _validation_accounting(output_root)
    matrix = _review_matrix(
        source_snapshot, source_tasks, phases, contracts, findings, risks,
        task_evidence, validation,
    )
    return {
        "source_snapshot": source_snapshot, "source_tasks": source_tasks,
        "source_slots": source_slots, "phases": phases, "contracts": contracts,
        "risks": risks, "task_evidence": task_evidence, "findings": findings,
        "validation": validation, "matrix": matrix,
    }


def expected_core_outputs(
    project_root: Optional[Path] = None,
    source_package: Optional[Path] = None,
    output_root: Optional[Path] = None,
) -> dict[Path, bytes]:
    """Return deterministic absolute output paths and their exact bytes."""

    root = _normalize_project_root(project_root)
    package = DEFAULT_SOURCE_PACKAGE if source_package is None else Path(source_package)
    destination = _normalize_output_root(root, output_root)
    state = _build_review_state(root, package, destination)
    matrix = state["matrix"]
    outputs = {
        destination / MATRIX_RELATIVE: _json_bytes(matrix),
        destination / FINDINGS_RELATIVE: _csv_bytes(FINDING_COLUMNS, state["findings"]),
        destination / CONTRACTS_RELATIVE: _json_bytes(state["contracts"]),
        destination / RISKS_RELATIVE: _csv_bytes(RISK_COLUMNS, state["risks"]),
        destination / TASK_EVIDENCE_RELATIVE: _json_bytes(state["task_evidence"]),
        destination / RECEIPT_TEMPLATE_RELATIVE: _jsonl_bytes(_validation_template_rows()),
        destination / REPORT_RELATIVE: _report_markdown(matrix, state["findings"], state["risks"]),
        destination / ROLLBACK_RELATIVE: _rollback_markdown(matrix),
        destination / TEST_RESULTS_RELATIVE: _test_results_markdown(matrix),
    }
    _assert_public_safe(outputs)
    return outputs


def build_final_manifest(
    generated_at: str,
    project_root: Optional[Path] = None,
    source_package: Optional[Path] = None,
    output_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Build the final manifest after core artifacts and receipts are final."""

    try:
        parsed = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
    except ValueError as error:
        raise BuildError("generated_at must be ISO-8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BuildError("generated_at must include a timezone offset")

    root = _normalize_project_root(project_root)
    package = DEFAULT_SOURCE_PACKAGE if source_package is None else Path(source_package)
    destination = _normalize_output_root(root, output_root)
    state = _build_review_state(root, package, destination)
    matrix = state["matrix"]
    if matrix["stage_gate"]["stage_acceptance_status"] != "PASSED":
        raise BuildError(
            "final manifest requires 9/9 Tasks, zero blocking findings, "
            "zero risk plan gaps, all cross-phase contracts PASS, and exact PASS receipts"
        )

    core = expected_core_outputs(
        project_root=root, source_package=package, output_root=destination
    )
    for path, expected in core.items():
        if not path.is_file() or path.read_bytes() != expected:
            raise BuildError(f"core artifact drift before manifest finalization: {path}")

    artifact_integrity: list[dict[str, Any]] = []
    for key, ref in FINAL_ARTIFACT_REFS.items():
        if key == "manifest":
            continue
        path = _repo_path(root, ref)
        payload = path.read_bytes()
        artifact_integrity.append({
            "ref": ref, "bytes": len(payload), "sha256": _sha256_bytes(payload),
        })

    findings = state["findings"]
    risks = state["risks"]
    finding_accounting = matrix["review_finding_accounting"]
    risk_accounting = matrix["open_risk_accounting"]
    contract_accounting = dict(state["contracts"]["accounting"])
    contract_accounting.update({
        "p1_requirement_count": 55, "p1_business_line_count": 10,
        "p1_capability_count": 37, "p2_normalized_binding_count": 134,
        "p2_actual_lineage_record_count": 0, "p3_scope_row_count": 103,
        "p3_prohibition_row_count": 51,
    })
    manifest: dict[str, Any] = {
        "schema_version": "kmfa.v015.s02_stage_review.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S02",
        "run_phase_id": RUN_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "run_mode": "IMPLEMENT", "work_kind": "STAGE_REVIEW_FIX",
        "review_base_commit": REVIEW_BASE_COMMIT,
        "counted_as_taskpack_task": False,
        "current_phase_kind": "GOVERNANCE_OVERLAY",
        "current_phase_is_taskpack_roadmap_phase": False,
        "current_task_is_taskpack_roadmap_task": False,
        "source_package": dict(state["source_snapshot"]),
        "phase_evidence": _phase_evidence_rows(state["phases"]),
        "task_accounting": dict(matrix["task_accounting"]),
        "review_findings": dict(finding_accounting),
        "open_risk_accounting": dict(risk_accounting),
        "cross_phase_accounting": contract_accounting,
        "stage_gate": dict(matrix["stage_gate"]),
        "next_entry_gate": dict(matrix["next_entry_gate"]),
        "downstream_actions": dict(matrix["downstream_actions"]),
        "remediation_binding": {
            "finding_ids": [row["finding_id"] for row in findings],
            "fixed_validated_count": finding_accounting["fixed_validated"],
            "blocking_open_count": finding_accounting["blocking_open"],
            "risk_ids": [row["risk_id"] for row in risks],
            "risk_plan_gap_count": risk_accounting["plan_gap_count"],
            "validation_results_ref": FINAL_ARTIFACT_REFS["validation_results"],
            "exact_receipt_count": state["validation"]["passed"],
        },
        "artifact_refs": dict(FINAL_ARTIFACT_REFS),
        "artifact_integrity": artifact_integrity,
    }
    manifest["content_hash"] = _content_hash(manifest)
    payload = _json_bytes(manifest)
    _assert_public_safe({destination / MANIFEST_RELATIVE: payload})
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
    print(f"PASS: exact S02 Stage-review core outputs match ({len(outputs)} files)")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", type=Path, default=DEFAULT_SOURCE_PACKAGE)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--finalize-manifest", action="store_true")
    parser.add_argument("--generated-at", default="")
    args = parser.parse_args(argv)
    try:
        if args.source_only:
            if args.check or args.finalize_manifest:
                raise BuildError("--source-only cannot be combined with --check/--finalize-manifest")
            snapshot, tasks, slots = _verify_source_package(args.source_package)
            print(
                "PASS: source package 21/21; "
                f"stages/phases/tasks={snapshot['stage_count']}/{snapshot['phase_count']}/{snapshot['task_count']}; "
                f"S02 phases/tasks={snapshot['s02_phase_count']}/{snapshot['s02_task_count']}; "
                f"evidence_slots={len(slots)}; formal_review_task={snapshot['s02_formal_stage_review_task_present']}"
            )
            if len(tasks) != 9:
                raise BuildError("S02 source task count drift")
        elif args.finalize_manifest:
            manifest = build_final_manifest(
                args.generated_at,
                project_root=args.project_root,
                source_package=args.source_package,
                output_root=args.output_root,
            )
            root = _normalize_project_root(args.project_root)
            destination = _normalize_output_root(root, args.output_root)
            path = destination / MANIFEST_RELATIVE
            payload = _json_bytes(manifest)
            if args.check:
                if not path.is_file() or path.read_bytes() != payload:
                    raise BuildError(f"final manifest drift: {path}")
                print("PASS: exact S02 Stage-review final manifest matches")
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
                root = _normalize_project_root(args.project_root)
                destination = _normalize_output_root(root, args.output_root)
                pending_path = destination / VALIDATION_RESULTS_RELATIVE
                if not pending_path.exists():
                    pending_path.parent.mkdir(parents=True, exist_ok=True)
                    pending_path.write_bytes(_jsonl_bytes(_pending_validation_rows()))
                    print(f"WROTE {pending_path} (PENDING template)")
    except (
        BadZipFile, BuildError, KeyError, OSError, TypeError, UnicodeError,
        ValueError, csv.Error, json.JSONDecodeError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
