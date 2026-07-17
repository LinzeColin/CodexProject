#!/usr/bin/env python3
"""Build deterministic public-safe evidence for the KMFA v1.5 S03 Stage review.

The review is a governance overlay, not a fourth Roadmap Phase or a tenth Task.
It binds the accepted P1/P2/P3 manifests and validation receipts, evaluates the
cross-Phase raw/private/public contracts, records review remediations and routed
risks, and keeps S04, GitHub upload and App reinstall outside this run.

This builder never reads or lists the raw inbox.  Its only live private-state
observation is directory metadata below KMFA/local_runtime, which is required to
verify the S03-P2 0700 directory contract.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence
from zipfile import BadZipFile, ZipFile

from KMFA.tools import build_v015_s03_p1_read_only_root_governance as p1_builder
from KMFA.tools import build_v015_s03_p2_private_derived_runtime as p2_builder


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
SOURCE_PACKAGE_NAME = "KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip"
DEFAULT_SOURCE_PACKAGE = Path.home() / "Downloads" / SOURCE_PACKAGE_NAME
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
SOURCE_MANIFEST_SHA256 = "a4a5cb0e301a841a922e761ff503a2fce72982b1b088d9aeee9e11998939b2a5"
REVIEW_BASE_COMMIT = "8e4d09c446ee28f49b84b48a58ba417e52ccf161"
RUN_PHASE_ID = "V015_S03_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S03-STAGE-REVIEW-20260714"
ACCEPTANCE_ID = "ACC-KMFA-V015-S03-STAGE-REVIEW"

OUTPUT_ROOT_RELATIVE = Path("stage_artifacts/V015_S03_STAGE_REVIEW")
MANIFEST_RELATIVE = Path("machine/stage3_review_manifest.json")
MATRIX_RELATIVE = Path("machine/stage3_review_matrix_public_safe.json")
CONTRACTS_RELATIVE = Path("machine/cross_phase_contracts_public_safe.json")
FINDINGS_RELATIVE = Path("machine/stage3_review_findings_public_safe.csv")
RISKS_RELATIVE = Path("machine/open_risk_register_public_safe.csv")
TASK_EVIDENCE_RELATIVE = Path("machine/task_evidence_contract_public_safe.json")
SOURCE_CONTRACT_RELATIVE = Path("machine/source_contract_public_safe.json")
RECEIPT_TEMPLATE_RELATIVE = Path("machine/validation_receipts_template.jsonl")
VALIDATION_RESULTS_RELATIVE = Path("machine/validation_results.jsonl")
REPORT_RELATIVE = Path("human/stage3_review_report_zh.md")
TEST_RESULTS_RELATIVE = Path("human/test_results_zh.md")
ROLLBACK_RELATIVE = Path("human/rollback_plan_zh.md")


def _artifact_ref(relative: Path) -> str:
    return f"KMFA/{OUTPUT_ROOT_RELATIVE.as_posix()}/{relative.as_posix()}"


ARTIFACT_REFS = {
    "manifest": _artifact_ref(MANIFEST_RELATIVE),
    "review_matrix": _artifact_ref(MATRIX_RELATIVE),
    "cross_phase_contracts": _artifact_ref(CONTRACTS_RELATIVE),
    "review_findings": _artifact_ref(FINDINGS_RELATIVE),
    "open_risk_register": _artifact_ref(RISKS_RELATIVE),
    "task_evidence_contract": _artifact_ref(TASK_EVIDENCE_RELATIVE),
    "source_contract": _artifact_ref(SOURCE_CONTRACT_RELATIVE),
    "validation_receipts_template": _artifact_ref(RECEIPT_TEMPLATE_RELATIVE),
    "validation_results": _artifact_ref(VALIDATION_RESULTS_RELATIVE),
    "review_report": _artifact_ref(REPORT_RELATIVE),
    "test_results": _artifact_ref(TEST_RESULTS_RELATIVE),
    "rollback_plan": _artifact_ref(ROLLBACK_RELATIVE),
}

PHASES = {
    "S03-P1": {
        "manifest_ref": "KMFA/stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/machine/s03_p1_read_only_root_governance_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/machine/validation_results.jsonl",
        "evidence_ref": "KMFA/stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/machine/task_evidence_slot_matrix_public_safe.jsonl",
    },
    "S03-P2": {
        "manifest_ref": "KMFA/stage_artifacts/V015_S03_P2_PRIVATE_DERIVED_RUNTIME/machine/s03_p2_private_derived_runtime_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S03_P2_PRIVATE_DERIVED_RUNTIME/machine/validation_results.jsonl",
        "evidence_ref": "KMFA/stage_artifacts/V015_S03_P2_PRIVATE_DERIVED_RUNTIME/machine/task_evidence_slot_matrix_public_safe.jsonl",
    },
    "S03-P3": {
        "manifest_ref": "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/machine/s03_p3_public_repository_safety_manifest.json",
        "validation_ref": "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/machine/validation_results.jsonl",
        "evidence_ref": "KMFA/stage_artifacts/V015_S03_P3_PUBLIC_REPOSITORY_SAFETY/machine/task_evidence_slot_matrix_public_safe.jsonl",
    },
}

RUNTIME_LAYERS = (
    "content_mirror", "extracted", "staging", "facts", "cache",
    "reports", "logs", "backups", "quarantine",
)

FINDING_COLUMNS = (
    "finding_id", "severity", "finding_class", "status", "title",
    "source_ref", "reproduction", "impact", "fix_ref", "revalidation_ref",
    "blocks_stage_acceptance",
)
RISK_COLUMNS = (
    "risk_id", "severity", "status", "risk", "impact", "control",
    "follow_up_stage_task", "plan_complete", "blocks_s03_stage_acceptance",
    "evidence_refs",
)

EXPECTED_VALIDATIONS = {
    "python_compile": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -c \"import ast,pathlib; "
        "[ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in "
        "('KMFA/tools/build_v015_s03_stage_review.py',"
        "'KMFA/tools/check_v015_s03_stage_review.py',"
        "'KMFA/tools/run_v015_s03_stage_review_validations.py')]\""
    ),
    "source_package_integrity": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s03_stage_review.py --source-only"
    ),
    "stage_review_tests": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest "
        "KMFA.tests.test_v015_s03_stage_review -q"
    ),
    "p3_current_submission_dependency": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s03_stage_review.py --current-submission-only"
    ),
    "private_runtime_permissions": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s03_stage_review.py --private-runtime-only"
    ),
    "stage_review_pre_receipt": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/check_v015_s03_stage_review.py --pre-receipt --skip-exact-rebuild"
    ),
    "roadmap_governance_check": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/v015_roadmap_governance_sync.py --check"
    ),
    "project_governance": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/validate_project_governance.py --project KMFA --mode required"
    ),
    "lean_governance": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "scripts/lean_governance.py validate --project KMFA --mode required"
    ),
    "governance_sync": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        f"scripts/validate_governance_sync.py --changed-only --base-ref {REVIEW_BASE_COMMIT} --enforce-sync"
    ),
    "no_float_money": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/check_no_float_money.py",
    "no_omission": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B KMFA/tools/no_omission_check.py",
    "git_diff_check": f"git diff --check {REVIEW_BASE_COMMIT}..HEAD",
    "builder_exact_rebuild": (
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B "
        "KMFA/tools/build_v015_s03_stage_review.py --check"
    ),
}

FINAL_MUTABLE_REFS = frozenset({
    ARTIFACT_REFS["manifest"], ARTIFACT_REFS["review_matrix"],
    ARTIFACT_REFS["validation_results"], ARTIFACT_REFS["review_report"],
    ARTIFACT_REFS["test_results"],
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md", "KMFA/README.md", "KMFA/功能清单.md", "KMFA/开发记录.md",
    "KMFA/模型参数文件.md", "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md", "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md", "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv", "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml", "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/events.jsonl", "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml", "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/docs/governance/project.yaml", "KMFA/docs/governance/roadmap.yaml",
    "KMFA/metadata/model_registry.yaml", "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
})

_ABSOLUTE_PATH_RE = re.compile(rb"(?<![A-Za-z0-9_])/(?:Users|Volumes|private|tmp|home)/")
_SECRET_RE = re.compile(rb"(?i)(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}")


class BuildError(RuntimeError):
    """Raised when review evidence cannot be derived exactly and safely."""


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(dict(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for row in rows
    )


def _csv_bytes(headers: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(headers), extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, (list, dict, bool)) else value for key, value in row.items()})
    return buffer.getvalue().encode()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _content_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + _sha256(encoded)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"expected JSON object: {path}")
    return value


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


def _repo_path(ref: str) -> Path:
    path = Path(ref)
    if path.is_absolute() or not path.parts or path.parts[0] != "KMFA" or ".." in path.parts:
        raise BuildError(f"unsafe repository ref: {ref}")
    resolved = REPO_ROOT.joinpath(path).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError as error:
        raise BuildError(f"repository ref escaped root: {ref}") from error
    return resolved


def _git(args: Sequence[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise BuildError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _member(archive: ZipFile, basename: str) -> tuple[str, bytes]:
    matches = [item.filename for item in archive.infolist() if not item.is_dir() and item.filename.rsplit("/", 1)[-1] == basename]
    if len(matches) != 1:
        raise BuildError(f"source member resolution drift: {basename}")
    return matches[0], archive.read(matches[0])


def verify_source_package(path: Path = DEFAULT_SOURCE_PACKAGE) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    """Verify the ZIP manifest and derive the exact nine S03 task contracts."""

    payload = path.read_bytes()
    if _sha256(payload) != SOURCE_PACKAGE_SHA256:
        raise BuildError("source package SHA-256 drift")
    with ZipFile(path) as archive:
        names = [item.filename for item in archive.infolist() if not item.is_dir()]
        manifest_name, manifest_payload = _member(archive, "15_MANIFEST_SHA256_v2_0.csv")
        if _sha256(manifest_payload) != SOURCE_MANIFEST_SHA256:
            raise BuildError("source manifest SHA-256 drift")
        reader = csv.DictReader(io.StringIO(manifest_payload.decode("utf-8-sig"), newline=""))
        rows = list(reader)
        if reader.fieldnames != ["相对路径", "字节数", "SHA256"] or len(rows) != 21:
            raise BuildError("source manifest structure drift")
        declared: set[str] = set()
        for row in rows:
            relative = str(row["相对路径"])
            pure = PurePosixPath(relative)
            if not relative or pure.is_absolute() or ".." in pure.parts or relative in declared:
                raise BuildError("unsafe or duplicate source manifest path")
            declared.add(relative)
            matches = [name for name in names if name == relative or name.endswith("/" + relative)]
            if len(matches) != 1:
                raise BuildError(f"source member accounting drift: {relative}")
            member_payload = archive.read(matches[0])
            if len(member_payload) != int(row["字节数"]) or _sha256(member_payload) != row["SHA256"]:
                raise BuildError(f"source member integrity drift: {relative}")
        if len(names) != 22 or manifest_name in declared:
            raise BuildError("source archive member count drift")

        _, roadmap_payload = _member(archive, "02B_KMFA_Codex_Development_Roadmap_v2_0.json")
        roadmap = json.loads(roadmap_payload)
        if (roadmap.get("stage_count"), roadmap.get("phase_count"), roadmap.get("task_count")) != (24, 72, 216):
            raise BuildError("source Roadmap aggregate count drift")
        stages = [row for row in roadmap.get("stages", []) if row.get("id") == "S03"]
        if len(stages) != 1:
            raise BuildError("source S03 resolution drift")
        stage = stages[0]
        phases = stage.get("phases", [])
        if [row.get("id") for row in phases] != ["P1", "P2", "P3"]:
            raise BuildError("source S03 Phase structure drift")
        tasks: list[dict[str, str]] = []
        for phase in phases:
            if [row.get("id") for row in phase.get("tasks", [])] != ["T01", "T02", "T03"]:
                raise BuildError("source S03 Task structure drift")
            for task in phase["tasks"]:
                task_id = "S03" + phase["id"] + task["id"]
                contract = {key: str(task.get(key, "")) for key in ("name", "action", "output", "acceptance", "evidence", "stop")}
                tasks.append({
                    "task_id": task_id,
                    "phase_id": "S03-" + phase["id"],
                    "name": contract["name"],
                    "contract_sha256": "sha256:" + _sha256(json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()),
                })
        if len(tasks) != 9 or len({row["task_id"] for row in tasks}) != 9:
            raise BuildError("source S03 Task accounting drift")

        _, roadmap_md_payload = _member(archive, "02_KMFA_Codex_Development_Roadmap_24_Stages_v2_0.md")
        roadmap_md = roadmap_md_payload.decode("utf-8-sig")
        stage_gate = "本 Stage 所有 P0 Task 的验收、测试和证据通过；开放风险有明确后续任务；不得以时间到期替代质量证据。"
        if stage_gate not in roadmap_md or "下一 Stage 入口条件" not in roadmap_md:
            raise BuildError("source Stage gate text drift")

        _, quality_payload = _member(archive, "10_KMFA_质量门禁与测试证据规范_v2_0.md")
        quality = quality_payload.decode("utf-8-sig")
        after = quality.split("每个 Task 的证据目录至少包含：", 1)
        match = re.search(r"```text\s*(.*?)```", after[1] if len(after) == 2 else "", re.DOTALL)
        slots = [line.strip() for line in match.group(1).splitlines() if line.strip()] if match else []
        expected_slots = ["manifest.json", "commands.txt", "test_results.json", "human_summary.md", "changed_files.txt", "screenshots/", "logs/", "exports/", "rollback.md", "open_risks.md"]
        if slots != expected_slots:
            raise BuildError("quality evidence-slot contract drift")

    snapshot = {
        "name": SOURCE_PACKAGE_NAME,
        "bytes": len(payload),
        "sha256": SOURCE_PACKAGE_SHA256,
        "manifest_sha256": SOURCE_MANIFEST_SHA256,
        "verified_member_count": 21,
        "stage_count": 24,
        "phase_count": 72,
        "task_count": 216,
        "s03_phase_count": 3,
        "s03_task_count": 9,
        "formal_stage_review_task_present": False,
        "stage_gate_sha256": "sha256:" + _sha256(stage_gate.encode()),
    }
    return snapshot, tasks, slots


def _load_phase_contexts() -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for phase_id, spec in PHASES.items():
        manifest_path = _repo_path(spec["manifest_ref"])
        payload = manifest_path.read_bytes()
        manifest = _read_json(manifest_path)
        validations = _read_jsonl(_repo_path(spec["validation_ref"]))
        evidence_rows = _read_jsonl(_repo_path(spec["evidence_ref"]))
        if phase_id == "S03-P1":
            content_hash_valid = manifest.get("content_hash") == p1_builder._content_hash(manifest)
        elif phase_id == "S03-P2":
            content_hash_valid = manifest.get("content_hash") == p2_builder._content_hash(manifest)
        else:
            content_hash_valid = manifest.get("content_hash") is None
        contexts[phase_id] = {
            "manifest": manifest,
            "manifest_ref": spec["manifest_ref"],
            "manifest_sha256": _sha256(payload),
            "manifest_bytes": len(payload),
            "content_hash_valid": content_hash_valid,
            "validation_ref": spec["validation_ref"],
            "validations": validations,
            "evidence_ref": spec["evidence_ref"],
            "evidence_rows": evidence_rows,
        }
    return contexts


def runtime_directory_summary(
    runtime_root: Optional[Path] = None,
    *,
    check_gitignore: bool = True,
) -> dict[str, Any]:
    """Inspect only private runtime directory metadata; never read private files."""

    root = PROJECT_ROOT / "local_runtime" if runtime_root is None else Path(runtime_root)
    if not root.is_dir() or stat.S_IMODE(os.lstat(root).st_mode) != 0o700:
        raise BuildError("private runtime root must exist with mode 0700")
    checked = 1
    invalid: list[str] = []
    for layer in RUNTIME_LAYERS:
        layer_path = root / layer
        if not layer_path.is_dir():
            invalid.append(layer)
            continue
        for current, directories, _files in os.walk(layer_path, topdown=True, followlinks=False):
            current_path = Path(current)
            metadata = os.lstat(current_path)
            checked += 1
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700:
                invalid.append(current_path.relative_to(root).as_posix())
            directories.sort()
            for name in list(directories):
                child = current_path / name
                value = os.lstat(child)
                if stat.S_ISLNK(value.st_mode) or not stat.S_ISDIR(value.st_mode):
                    invalid.append(child.relative_to(root).as_posix())
    ignored = 0
    if check_gitignore:
        for layer in RUNTIME_LAYERS:
            result = subprocess.run(["git", "check-ignore", "-q", f"KMFA/local_runtime/{layer}"], cwd=REPO_ROOT, check=False)
            ignored += result.returncode == 0
    else:
        ignored = len(RUNTIME_LAYERS)
    return {
        "layer_count": len(RUNTIME_LAYERS),
        "directory_count_checked": checked,
        "invalid_directory_count": len(set(invalid)),
        "all_directories_mode_0700": not invalid,
        "gitignored_layer_count": ignored,
        "all_layers_gitignored": ignored == len(RUNTIME_LAYERS),
        "private_file_content_read": False,
        "raw_inbox_accessed": False,
    }


def _phase_receipt_summary(context: Mapping[str, Any]) -> dict[str, Any]:
    rows = context["validations"]
    run_ids = {row.get("run_id") for row in rows}
    heads = {row.get("head_before") for row in rows} | {row.get("head_after") for row in rows}
    subjects = {row.get("validation_subject_sha256") for row in rows}
    return {
        "recorded": len(rows),
        "passed": sum(row.get("result") == "PASS" and row.get("exit_code") == 0 for row in rows),
        "single_run": len(run_ids) == 1 and None not in run_ids,
        "single_head": len(heads) == 1 and None not in heads,
        "single_subject": len(subjects) == 1 and None not in subjects,
        "sequence_exact": [row.get("execution_sequence") for row in rows] == list(range(1, len(rows) + 1)),
    }


def _evidence_covered(row: Mapping[str, Any]) -> bool:
    return row.get("status") in {"COVERED", "PRESENT"}


def _evidence_na_valid(row: Mapping[str, Any]) -> bool:
    return row.get("status") == "N/A_WITH_RATIONALE" and bool(
        row.get("rationale") or row.get("not_applicable_reason")
    )


def _evidence_valid(row: Mapping[str, Any]) -> bool:
    return _evidence_covered(row) or _evidence_na_valid(row)


def _contract(contract_id: str, name: str, expected: Any, observed: Any, evidence_refs: Sequence[str], boundary: str) -> dict[str, Any]:
    return {
        "contract_id": contract_id,
        "name": name,
        "status": "PASS" if expected == observed else "FAIL",
        "expected": expected,
        "observed": observed,
        "evidence_refs": list(evidence_refs),
        "blocking": True,
        "boundary": boundary,
    }


def _cross_phase_contracts(source: Mapping[str, Any], phases: Mapping[str, Mapping[str, Any]], runtime: Mapping[str, Any]) -> dict[str, Any]:
    p1, p2, p3 = (phases[key]["manifest"] for key in ("S03-P1", "S03-P2", "S03-P3"))
    phase_refs = [phases[key]["manifest_ref"] for key in phases]
    receipts = {key: _phase_receipt_summary(value) for key, value in phases.items()}
    slot_rows = [row for value in phases.values() for row in value["evidence_rows"]]
    dual = _read_json(_repo_path(str(p3["artifact_refs"]["dual_plane"])))
    protection = _read_json(_repo_path(str(p3["artifact_refs"]["protection_verification"])))
    contracts = [
        _contract("S03REV-C01", "源包结构", {"stages": 24, "phases": 72, "tasks": 216, "s03_phases": 3, "s03_tasks": 9}, {"stages": source["stage_count"], "phases": source["phase_count"], "tasks": source["task_count"], "s03_phases": source["s03_phase_count"], "s03_tasks": source["s03_task_count"]}, [], "复审 overlay 不计入 72 Phase / 216 Task。"),
        _contract("S03REV-C02", "三 Phase 与九 Task 验收", {"phase_pass": 3, "tasks": 9}, {"phase_pass": sum((m.get("acceptance_status") or m.get("phase_acceptance_status")) == "PASSED" for m in (p1, p2, p3)), "tasks": int(p1["task_accounting"]["accepted"]) + int(p2["task_accounting"]["accepted"]) + int(p3["task_accepted_count"])}, phase_refs, "历史 Phase 以冻结 manifest 和 receipt 为准，不要求旧 checker 伪装当前权威状态。"),
        _contract("S03REV-C03", "冻结 validation receipt 重放", {"P1": [15, 15, True, True, True, True], "P2": [15, 15, True, True, True, True], "P3": [22, 22, True, True, True, True]}, {key.split("-")[-1]: [value["recorded"], value["passed"], value["single_run"], value["single_head"], value["single_subject"], value["sequence_exact"]] for key, value in receipts.items()}, [phases[key]["validation_ref"] for key in phases], "receipt 仅证明被接受提交时的可执行验证；当前门禁另行实时检查。"),
        _contract("S03REV-C04", "P1 只读 guard", {"guard": "PASS", "pre_post_equal": True, "mutation": False, "absolute_zero_claim": False}, {"guard": p1["guard_result"]["guard_status"], "pre_post_equal": p1["guard_result"]["pre_post_equal"], "mutation": p1["guard_result"]["prohibited_raw_mutation_detected"], "absolute_zero_claim": p1["guard_result"]["absolute_zero_metadata_mutation_claimed"]}, [phases["S03-P1"]["manifest_ref"]], "允许 list/stat/read-for-hash/hash；不将 atime 风险虚报为绝对零变更。"),
        _contract("S03REV-C05", "P2 对 P1 边界绑定", {"policy_receipt": True, "snapshot": True, "root_identity": True}, {"policy_receipt": p2["boundary_binding"]["fixed_p1_policy_and_receipt"], "snapshot": p2["boundary_binding"]["p1_final_snapshot_exact_match_both_runs"], "root_identity": p2["boundary_binding"]["raw_root_identity_match_both_runs"]}, [phases["S03-P2"]["manifest_ref"]], "复制运行必须继承并保持 P1 最终只读边界。"),
        _contract("S03REV-C06", "P2 九层私有运行空间", {"layers": 9, "present": True, "ignored": True, "tracked": 0, "permissions": True}, {"layers": p2["private_runtime"]["layer_count"], "present": p2["private_runtime"]["all_layers_present"], "ignored": p2["private_runtime"]["all_layers_gitignored"], "tracked": p2["private_runtime"]["tracked_entry_count"], "permissions": p2["private_runtime"]["minimum_permissions_pass"]}, [phases["S03-P2"]["manifest_ref"]], "私有层不得进入 Git。"),
        _contract("S03REV-C07", "P2 内容寻址复制与幂等", {"runs": 2, "source": 5, "unique": 5, "hash": True, "reuse": True, "new_bytes_second": 0}, {"runs": p2["copy_acceptance"]["run_count"], "source": p2["copy_acceptance"]["source_file_count"], "unique": p2["copy_acceptance"]["unique_blob_count"], "hash": p2["copy_acceptance"]["hash_match_both_runs"], "reuse": p2["copy_acceptance"]["idempotent_reuse_without_rewrite"], "new_bytes_second": p2["copy_acceptance"]["second_run_new_bytes"]}, [phases["S03-P2"]["manifest_ref"]], "只验证 hash/幂等聚合，不公开 raw 名称、路径或 hash。"),
        _contract("S03REV-C08", "P2 生命周期清理边界", {"dry_run": True, "synthetic": True, "irreversible": False, "confirmation": True}, {"dry_run": p2["cleanup_acceptance"]["canonical_dry_run"], "synthetic": p2["cleanup_acceptance"]["synthetic_rehearsal_pass"], "irreversible": p2["cleanup_acceptance"]["irreversible_real_cleanup_performed"], "confirmation": p2["cleanup_acceptance"]["second_confirmation_required"]}, [phases["S03-P2"]["manifest_ref"]], "Stage review 不执行真实不可逆清理。"),
        _contract("S03REV-C09", "当前 private runtime 权限", {"layers": 9, "invalid": 0, "mode_0700": True, "ignored": True}, {"layers": runtime["layer_count"], "invalid": runtime["invalid_directory_count"], "mode_0700": runtime["all_directories_mode_0700"], "ignored": runtime["all_layers_gitignored"]}, [], "仅 stat KMFA 私有 runtime 目录；不读取 private 文件或 raw inbox。"),
        _contract("S03REV-C10", "P3 当前提交安全", {"submission": True, "history_clean": False, "history_rewrite": False}, {"submission": protection["current_submission_gate_pass"], "history_clean": p3["history_boundary"]["reachable_history_clean"], "history_rewrite": p3["history_boundary"]["history_rewrite_performed"]}, [p3["artifact_refs"]["protection_verification"]], "当前树通过不等于 reachable history 已清洁；最终上传继续阻断。"),
        _contract("S03REV-C11", "P3 可提交 metadata", {"allow_classes": 6, "deny_classes": 4, "raw_access": 0}, {"allow_classes": p3["committable_metadata_class_count"], "deny_classes": p3["forbidden_public_detail_class_count"], "raw_access": p3["raw_root_access_count_by_phase"]}, [phases["S03-P3"]["manifest_ref"]], "公开面不含文件名明文、客户/金额明细或凭据。"),
        _contract("S03REV-C12", "P3 双平面绑定", {"same_run": True, "attack_model": True, "information_theoretic_claim": False, "plaintext_public": False}, {"same_run": dual.get("run_id") == dual.get("public_projection_summary", {}).get("run_id"), "attack_model": dual.get("verification", {}).get("declared_attack_model_pass"), "information_theoretic_claim": dual.get("verification", {}).get("information_theoretic_non_reconstruction_claimed"), "plaintext_public": dual.get("public_projection_summary", {}).get("plaintext_or_raw_private_values_public")}, [p3["artifact_refs"]["dual_plane"]], "不可反推结论仅限声明攻击模型。"),
        _contract("S03REV-C13", "九 Task 证据槽", {"rows": 90, "tasks": 9, "invalid": 0}, {"rows": len(slot_rows), "tasks": len({row.get("task_id") for row in slot_rows}), "invalid": sum(not _evidence_valid(row) for row in slot_rows)}, [phases[key]["evidence_ref"] for key in phases], "N/A 必须有理由；不伪造截图、日志或导出。"),
        _contract("S03REV-C14", "Stage 副作用停止条件", {"raw_mutation": False, "cleanup": False, "upload": False, "app": False, "s04_started": False}, {"raw_mutation": p1["guard_result"]["prohibited_raw_mutation_detected"], "cleanup": p2["cleanup_acceptance"]["irreversible_real_cleanup_performed"], "upload": p3["github_upload_performed"], "app": p3["app_reinstall_performed"], "s04_started": p3["s04_p1_entry_allowed"]}, phase_refs, "本 Run 只做 S03 Stage review/fix。"),
    ]
    return {
        "schema_version": "kmfa.v015.s03_stage_review.cross_phase_contracts.v1",
        "contracts": contracts,
        "accounting": {
            "total": len(contracts),
            "passed": sum(row["status"] == "PASS" for row in contracts),
            "failed": sum(row["status"] != "PASS" for row in contracts),
            "blocking_failed": sum(row["status"] != "PASS" and row["blocking"] for row in contracts),
        },
    }


def _finding_rows() -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "S03REV-F001", "severity": "P1", "finding_class": "PRIVATE_RUNTIME_PERMISSION_DRIFT", "status": "FIXED_VALIDATED",
            "title": "P3 后续验证曾在 P2 reports 层留下 0755 子目录",
            "source_ref": "LOCAL_PRIVATE_RUNTIME_DIRECTORY_METADATA",
            "reproduction": "S03 Stage review 首次调用 P2 private evidence validation 得到 CLEANUP_DIRECTORY_MODE_INVALID。",
            "impact": "生命周期清理计划 fail closed，P2 严格私有证据无法实时复跑。",
            "fix_ref": "KMFA/tools/check_v015_s03_stage_review.py",
            "revalidation_ref": ARTIFACT_REFS["validation_results"], "blocks_stage_acceptance": False,
        },
        {
            "finding_id": "S03REV-F002", "severity": "P1", "finding_class": "HISTORICAL_VALIDATOR_REPLAY_CONTRACT", "status": "FIXED_VALIDATED",
            "title": "P1/P2 current-state strict checker 不能在后续 Phase 治理状态下原样重放",
            "source_ref": "KMFA/tools/check_v015_s03_p1_read_only_root_governance.py;KMFA/tools/check_v015_s03_p2_private_derived_runtime.py",
            "reproduction": "后续 Phase 已更新 current_phase、HEAD 与允许 diff，旧 checker 正确报告当前状态漂移但不适合作为 Stage 历史依赖。",
            "impact": "若 Stage review 直接执行旧 current-state checker，会把合法后续治理演进误报为 Phase 失败。",
            "fix_ref": "KMFA/tools/check_v015_s03_stage_review.py",
            "revalidation_ref": ARTIFACT_REFS["cross_phase_contracts"], "blocks_stage_acceptance": False,
        },
    ]


def _risk_rows() -> list[dict[str, Any]]:
    values = [
        ("RISK-KMFA-V015-S03-001", "P0", "reachable Git history 尚未证明清洁。", "最终 GitHub main 上传必须继续阻断。", "最终闭环执行 history/remote gate；本 Stage 不改写历史。", "S24P2T03", PHASES["S03-P3"]["manifest_ref"]),
        ("RISK-KMFA-V015-S03-002", "P1", "本地 fail-closed gate 不等于 GitHub server-side enforcement。", "远端分支保护不能由本地证据替代。", "在最终上传 gate 复核远端保护与实际 main parity。", "S24P2T03", PHASES["S03-P3"]["manifest_ref"]),
        ("RISK-KMFA-V015-S03-003", "P1", "授权读取仍可能产生 OS-managed atime。", "不得宣称原始数据绝对零 metadata 变化。", "保留 atime 诚实声明且禁止 utime 伪恢复。", "S24P2T02", PHASES["S03-P1"]["manifest_ref"]),
        ("RISK-KMFA-V015-S03-004", "P2", "真实不可逆清理未执行且需要 exact plan 二次确认。", "自动清理不能由 synthetic rehearsal 代替授权。", "稳定运行阶段另行生成并确认 exact cleanup plan。", "S24P2T02", PHASES["S03-P2"]["manifest_ref"]),
        ("RISK-KMFA-V015-S03-005", "P2", "Stage evidence exact rebuild 依赖外部 hash-bound TaskPack ZIP。", "clone 单独存在时不能完成源包完整性复验。", "版本闭环归档 hash-bound 交付包，不回退到未锁定镜像。", "S24P2T03", ARTIFACT_REFS["source_contract"]),
        ("RISK-KMFA-V015-S03-006", "P2", "双平面不可反推只在声明攻击模型内成立。", "不得扩张为信息论不可逆声明。", "持续执行输入输出安全和攻击模型回归。", "S22P2T03", PHASES["S03-P3"]["manifest_ref"]),
    ]
    return [{
        "risk_id": risk_id, "severity": severity, "status": "ROUTED_RESIDUAL",
        "risk": risk, "impact": impact, "control": control,
        "follow_up_stage_task": task, "plan_complete": True,
        "blocks_s03_stage_acceptance": False, "evidence_refs": evidence,
    } for risk_id, severity, risk, impact, control, task, evidence in values]


def _task_evidence_contract(source_tasks: Sequence[Mapping[str, str]], phases: Mapping[str, Mapping[str, Any]], slots: Sequence[str]) -> dict[str, Any]:
    phase_rows = {}
    all_rows = []
    for phase_id, context in phases.items():
        rows = context["evidence_rows"]
        all_rows.extend(rows)
        phase_rows[phase_id] = {
            "task_count": len({row.get("task_id") for row in rows}),
            "slot_count": len(rows),
            "present": sum(_evidence_covered(row) for row in rows),
            "n_a_with_rationale": sum(_evidence_na_valid(row) for row in rows),
            "evidence_ref": context["evidence_ref"],
        }
    return {
        "schema_version": "kmfa.v015.s03_stage_review.task_evidence_contract.v1",
        "quality_slots": list(slots),
        "source_tasks": list(source_tasks),
        "phase_accounting": phase_rows,
        "accounting": {
            "task_count": len(source_tasks), "slot_count": len(all_rows),
            "covered": sum(_evidence_covered(row) for row in all_rows),
            "n_a_with_rationale": sum(_evidence_na_valid(row) for row in all_rows),
            "invalid": sum(not _evidence_valid(row) for row in all_rows),
        },
    }


def _validation_rows(output_root: Path) -> list[dict[str, Any]]:
    path = output_root / VALIDATION_RESULTS_RELATIVE
    if not path.exists():
        return []
    return _read_jsonl(path)


def validation_status(rows: Sequence[Mapping[str, Any]]) -> tuple[bool, dict[str, Any]]:
    exact_ids = list(EXPECTED_VALIDATIONS)
    passed = (
        len(rows) == len(exact_ids)
        and [row.get("validation_id") for row in rows] == exact_ids
        and [row.get("execution_sequence") for row in rows] == list(range(1, len(rows) + 1))
        and all(row.get("command") == EXPECTED_VALIDATIONS[row["validation_id"]] for row in rows)
        and all(row.get("result") == "PASS" and row.get("exit_code") == 0 for row in rows)
        and len({row.get("run_id") for row in rows}) == 1
        and len({row.get("head_before") for row in rows} | {row.get("head_after") for row in rows}) == 1
        and len({row.get("validation_subject_sha256") for row in rows}) == 1
    )
    return passed, {
        "expected": len(EXPECTED_VALIDATIONS), "recorded": len(rows),
        "passed": sum(row.get("result") == "PASS" and row.get("exit_code") == 0 for row in rows),
        "failed": sum(row.get("result") == "FAIL" for row in rows),
        "pending": sum(row.get("result") == "PENDING" for row in rows),
        "all_exact_pass": passed,
    }


def validation_subject_refs(git_ref: str = "HEAD") -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", f"{REVIEW_BASE_COMMIT}..{git_ref}", "--", "KMFA"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise BuildError(result.stderr.decode(errors="replace").strip() or "unable to enumerate validation subject refs")
    changed = {value.decode("utf-8") for value in result.stdout.split(b"\0") if value}
    return tuple(sorted(ref for ref in changed if ref and ref not in FINAL_MUTABLE_REFS))


def validation_subject_sha256(git_ref: str = "HEAD") -> str:
    digest = hashlib.sha256()
    for ref in validation_subject_refs(git_ref):
        result = subprocess.run(["git", "show", f"{git_ref}:{ref}"], cwd=REPO_ROOT, capture_output=True, check=False)
        if result.returncode:
            raise BuildError(f"validation subject ref missing at {git_ref}: {ref}")
        digest.update(ref.encode() + b"\0" + result.stdout + b"\0")
    return "sha256:" + digest.hexdigest()


def _public_safe(outputs: Mapping[Path, bytes]) -> None:
    for path, payload in outputs.items():
        if _ABSOLUTE_PATH_RE.search(payload):
            raise BuildError(f"public evidence contains absolute local path: {path}")
        if _SECRET_RE.search(payload):
            raise BuildError(f"public evidence contains secret-like assignment: {path}")


def _matrix(source: Mapping[str, Any], phases: Mapping[str, Mapping[str, Any]], contracts: Mapping[str, Any], runtime: Mapping[str, Any], task_evidence: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    final, receipt_accounting = validation_status(rows)
    findings = _finding_rows()
    risks = _risk_rows()
    gate_pass = (
        contracts["accounting"]["blocking_failed"] == 0
        and task_evidence["accounting"]["invalid"] == 0
        and task_evidence["accounting"]["slot_count"] == 90
        and runtime["invalid_directory_count"] == 0
        and final
    )
    return {
        "schema_version": "kmfa.v015.s03_stage_review.matrix.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S03",
        "run_phase_id": RUN_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID,
        "review_kind": "GOVERNANCE_OVERLAY_NOT_ROADMAP_PHASE_OR_TASK",
        "source_contract": dict(source),
        "phase_evidence": [{
            "phase_id": phase_id,
            "manifest_ref": context["manifest_ref"],
            "manifest_sha256": context["manifest_sha256"],
            "manifest_bytes": context["manifest_bytes"],
            "content_hash_valid": context["content_hash_valid"],
            "acceptance_status": context["manifest"].get("acceptance_status") or context["manifest"].get("phase_acceptance_status"),
            "validation_results_ref": context["validation_ref"],
        } for phase_id, context in phases.items()],
        "task_accounting": {"total": 9, "accepted": 9},
        "cross_phase_accounting": dict(contracts["accounting"]),
        "task_evidence_accounting": dict(task_evidence["accounting"]),
        "review_findings": {"total": len(findings), "fixed_validated": len(findings), "open": 0, "blocking_open": 0},
        "open_risks": {"total": len(risks), "routed": len(risks), "plan_gap_count": 0, "blocking": 0},
        "private_runtime": dict(runtime),
        "validation_receipts": receipt_accounting,
        "stage_gate": {
            "review_execution_status": "COMPLETED" if gate_pass else "EXECUTION_COMPLETE",
            "evidence_validation_status": "PASS" if gate_pass else "PENDING",
            "stage_lifecycle_status": "COMPLETED" if gate_pass else "IN_PROGRESS",
            "stage_acceptance_status": "PASSED" if gate_pass else "PENDING",
            "decision": "GO_TO_S04_P1_ONLY" if gate_pass else "REMAIN_IN_S03_STAGE_REVIEW",
        },
        "next_entry_gate": {
            "next_allowed_run": "S04-P1" if gate_pass else "S03 Stage review/fix",
            "s04_p1_entry_allowed": gate_pass,
            "s04_p1_started": False,
            "s04_plus_entry_allowed": False,
            "github_upload_allowed": False,
            "app_reinstall_allowed": False,
        },
        "downstream_actions": {
            "raw_inbox_accessed_by_review": False,
            "raw_inbox_mutated": False,
            "irreversible_real_cleanup_performed": False,
            "history_rewrite_performed": False,
            "s04_p1_started": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "formal_report_generated": False,
            "business_execution_performed": False,
        },
    }


def _report(matrix: Mapping[str, Any]) -> bytes:
    gate = matrix["stage_gate"]
    return (f"""# KMFA v1.5 S03 Stage 整体复审报告

## Stage 结果

- Stage：`S03｜原始数据只读边界与私有运行空间`
- 状态：`{gate['stage_lifecycle_status']} / {gate['stage_acceptance_status']}`
- 决策：`{gate['decision']}`
- 完成 Task：`9/9`
- 未完成 Task：`0`
- review findings：`2 fixed / 0 open`
- routed residual risks：`6`，plan gap=`0`

## 复审结论

- P1 只读 guard、P2 九层私有运行空间/内容寻址/清理演练、P3 公开仓库安全/双平面均由冻结 manifest 与 receipt 绑定。
- 已修复 private runtime 子目录权限漂移，并新增当前目录 `0700` 实时门禁。
- 历史 Phase checker 的 current-state 语义与 Stage 历史重放分离，避免把合法后续治理状态误报为前序 Phase 失败。
- reachable Git history 仍未证明清洁，因此本 Stage 通过不授权 GitHub upload；App 重装也未执行。

## 下一 Stage 入口条件

仅当本目录 exact rebuild、validation receipts、治理同步和 clean committed checker 全部 PASS，才开放独立下一 Run `S04-P1`；不得在本 Run 启动。
""").encode()


def _test_results(matrix: Mapping[str, Any]) -> bytes:
    receipts = matrix["validation_receipts"]
    return (f"""# KMFA v1.5 S03 Stage Review 测试结果

- validation receipts：`{receipts['passed']}/{receipts['expected']} PASS`
- cross-Phase contracts：`{matrix['cross_phase_accounting']['passed']}/{matrix['cross_phase_accounting']['total']} PASS`
- Task evidence slots：`{matrix['task_evidence_accounting']['slot_count']}/90`，invalid=`{matrix['task_evidence_accounting']['invalid']}`
- private runtime invalid directory count：`{matrix['private_runtime']['invalid_directory_count']}`
- evidence validation：`{matrix['stage_gate']['evidence_validation_status']}`

命令与 exit code 以 machine/validation_results.jsonl 为准；本报告不替代 receipt。
""").encode()


def _rollback() -> bytes:
    return """# KMFA v1.5 S03 Stage Review 回滚计划

仅回滚本 Stage review/fix 的 tracked 变更与本 Run 修复的 KMFA private runtime 目录 mode；不得修改、移动、删除或恢复 raw inbox，不得改写 Git 历史。若任一门禁失败，保持 S03 Stage=`IN_PROGRESS/PENDING`、S04 entry=false、GitHub upload=false、App reinstall=false。
""".encode()


def _pending_receipts() -> list[dict[str, Any]]:
    return [{
        "schema_version": "kmfa.v015.s03_stage_review.validation_receipt.v1",
        "run_id": None, "validation_id": validation_id, "command": command,
        "result": "PENDING", "exit_code": None, "execution_sequence": sequence,
        "review_base_commit": REVIEW_BASE_COMMIT,
    } for sequence, (validation_id, command) in enumerate(EXPECTED_VALIDATIONS.items(), 1)]


def expected_outputs(*, generated_at: str, source_package: Path = DEFAULT_SOURCE_PACKAGE) -> dict[Path, bytes]:
    source, source_tasks, slots = verify_source_package(source_package)
    phases = _load_phase_contexts()
    runtime = runtime_directory_summary()
    contracts = _cross_phase_contracts(source, phases, runtime)
    findings = _finding_rows()
    risks = _risk_rows()
    task_evidence = _task_evidence_contract(source_tasks, phases, slots)
    output_root = PROJECT_ROOT / OUTPUT_ROOT_RELATIVE
    rows = _validation_rows(output_root)
    matrix = _matrix(source, phases, contracts, runtime, task_evidence, rows)

    outputs: dict[Path, bytes] = {
        output_root / MATRIX_RELATIVE: _json_bytes(matrix),
        output_root / CONTRACTS_RELATIVE: _json_bytes(contracts),
        output_root / FINDINGS_RELATIVE: _csv_bytes(FINDING_COLUMNS, findings),
        output_root / RISKS_RELATIVE: _csv_bytes(RISK_COLUMNS, risks),
        output_root / TASK_EVIDENCE_RELATIVE: _json_bytes(task_evidence),
        output_root / SOURCE_CONTRACT_RELATIVE: _json_bytes(source),
        output_root / RECEIPT_TEMPLATE_RELATIVE: _jsonl_bytes(_pending_receipts()),
        output_root / REPORT_RELATIVE: _report(matrix),
        output_root / TEST_RESULTS_RELATIVE: _test_results(matrix),
        output_root / ROLLBACK_RELATIVE: _rollback(),
    }
    integrity = []
    for key, ref in ARTIFACT_REFS.items():
        if key in {"manifest", "validation_results"}:
            continue
        path = _repo_path(ref)
        payload = outputs.get(path, path.read_bytes() if path.exists() else b"")
        integrity.append({"ref": ref, "bytes": len(payload), "sha256": _sha256(payload)})
    final, receipt_accounting = validation_status(rows)
    manifest: dict[str, Any] = {
        "schema_version": "kmfa.v015.s03_stage_review.manifest.v1",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S03",
        "run_phase_id": RUN_PHASE_ID, "task_id": TASK_ID, "acceptance_id": ACCEPTANCE_ID,
        "run_mode": "IMPLEMENT", "work_kind": "STAGE_REVIEW_REMEDIATION",
        "review_base_commit": REVIEW_BASE_COMMIT, "generated_at": generated_at,
        "counted_as_taskpack_phase": False, "counted_as_taskpack_task": False,
        "source_package": source,
        "phase_evidence": matrix["phase_evidence"],
        "task_accounting": matrix["task_accounting"],
        "review_findings": matrix["review_findings"],
        "open_risks": matrix["open_risks"],
        "cross_phase_accounting": matrix["cross_phase_accounting"],
        "task_evidence_accounting": matrix["task_evidence_accounting"],
        "private_runtime": matrix["private_runtime"],
        "validation_receipts": receipt_accounting,
        "stage_gate": matrix["stage_gate"],
        "next_entry_gate": matrix["next_entry_gate"],
        "downstream_actions": matrix["downstream_actions"],
        "artifact_refs": ARTIFACT_REFS,
        "artifact_integrity": integrity,
        "validation_run_id": rows[0].get("run_id") if final else None,
        "validation_head": rows[0].get("head_before") if final else None,
        "validation_subject_sha256": rows[0].get("validation_subject_sha256") if final else None,
    }
    manifest["content_hash"] = _content_hash(manifest)
    outputs[output_root / MANIFEST_RELATIVE] = _json_bytes(manifest)
    _public_safe(outputs)
    return outputs


def _manifest_generated_at(path: Path) -> str:
    if not path.exists():
        return datetime.now().astimezone().isoformat(timespec="seconds")
    value = str(_read_json(path).get("generated_at", ""))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise BuildError("manifest generated_at is invalid") from error
    if parsed.tzinfo is None:
        raise BuildError("manifest generated_at must include timezone")
    return value


def run(*, write: bool, check: bool, generated_at: str = "", source_package: Path = DEFAULT_SOURCE_PACKAGE) -> None:
    manifest_path = PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / MANIFEST_RELATIVE
    timestamp = generated_at or _manifest_generated_at(manifest_path)
    outputs = expected_outputs(generated_at=timestamp, source_package=source_package)
    if check:
        drift = []
        for path, expected in outputs.items():
            if not path.is_file() or path.read_bytes() != expected:
                drift.append(path.relative_to(REPO_ROOT).as_posix())
        if drift:
            raise BuildError("S03 Stage-review evidence drift: " + ", ".join(drift))
        print(f"PASS: exact S03 Stage-review outputs match ({len(outputs)} files)")
        return
    if not write:
        raise BuildError("one of --write/--check is required")
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        print(f"WROTE {path}")
    results = PROJECT_ROOT / OUTPUT_ROOT_RELATIVE / VALIDATION_RESULTS_RELATIVE
    if not results.exists():
        results.write_bytes(_jsonl_bytes(_pending_receipts()))
        print(f"WROTE {results} (PENDING)")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--source-only", action="store_true")
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--source-package", type=Path, default=DEFAULT_SOURCE_PACKAGE)
    args = parser.parse_args(argv)
    try:
        if args.source_only:
            source, tasks, slots = verify_source_package(args.source_package)
            print(f"PASS: source package 21/21; stages/phases/tasks={source['stage_count']}/{source['phase_count']}/{source['task_count']}; S03 phases/tasks=3/{len(tasks)}; slots={len(slots)}")
        else:
            run(write=args.write, check=args.check, generated_at=args.generated_at, source_package=args.source_package)
    except (BadZipFile, BuildError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError, csv.Error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
