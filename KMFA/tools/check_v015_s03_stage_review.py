#!/usr/bin/env python3
"""Strict fail-closed validator for the KMFA v1.5 S03 Stage review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from KMFA.tools import build_v015_s03_stage_review as builder
from KMFA.tools import v015_s03_p3_public_repository_safety as repository_safety


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE
MANIFEST_PATH = ARTIFACT_ROOT / builder.MANIFEST_RELATIVE
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / builder.VALIDATION_RESULTS_RELATIVE

ALLOWED_REVIEW_PREFIXES = (
    "KMFA/stage_artifacts/V015_S03_STAGE_REVIEW/",
    "KMFA/tools/build_v015_s03_stage_review.py",
    "KMFA/tools/check_v015_s03_stage_review.py",
    "KMFA/tools/run_v015_s03_stage_review_validations.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_s03_stage_review.py",
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md", "KMFA/README.md", "KMFA/功能清单.md", "KMFA/开发记录.md",
    "KMFA/模型参数文件.md", "KMFA/docs/governance/", "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml", "KMFA/metadata/stage_status.jsonl",
)
_HASH_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HEAD_RE = re.compile(r"[0-9a-f]{40}\Z")


class CheckError(RuntimeError):
    """Raised when a Stage-review invariant fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CheckError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise CheckError(f"expected JSON object: {path}:{number}")
        rows.append(value)
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(args: Sequence[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise CheckError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _git_diff_paths(start: str, end: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", f"{start}..{end}", "--", "KMFA"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise CheckError(result.stderr.decode(errors="replace").strip() or "unable to enumerate changed paths")
    return {value.decode("utf-8") for value in result.stdout.split(b"\0") if value}


def _is_ancestor(commit: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=REPO_ROOT, check=False).returncode == 0


def _top_scalar(path: Path, key: str) -> Optional[str]:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                return value[1:-1]
            return value
    return None


def _validate_phase_evidence(manifest: Mapping[str, Any]) -> None:
    phases = manifest.get("phase_evidence")
    _require(isinstance(phases, list) and len(phases) == 3, "phase evidence count drift")
    expected_ids = list(builder.PHASES)
    _require([row.get("phase_id") for row in phases] == expected_ids, "phase evidence order/IDs drift")
    for row in phases:
        phase_id = str(row["phase_id"])
        spec = builder.PHASES[phase_id]
        path = REPO_ROOT / spec["manifest_ref"]
        _require(path.is_file(), f"missing predecessor manifest: {phase_id}")
        _require(row.get("manifest_ref") == spec["manifest_ref"], f"predecessor manifest ref drift: {phase_id}")
        _require(row.get("manifest_sha256") == _sha256(path), f"predecessor manifest digest drift: {phase_id}")
        _require(row.get("manifest_bytes") == path.stat().st_size, f"predecessor manifest byte count drift: {phase_id}")
        _require(row.get("content_hash_valid") is True, f"predecessor content hash drift: {phase_id}")
        _require(row.get("acceptance_status") == "PASSED", f"predecessor Phase not PASSED: {phase_id}")

        phase_manifest = _read_json(path)
        rows = _read_jsonl(REPO_ROOT / spec["validation_ref"])
        expected_count = 22 if phase_id == "S03-P3" else 15
        _require(len(rows) == expected_count, f"predecessor receipt count drift: {phase_id}")
        _require([item.get("execution_sequence") for item in rows] == list(range(1, expected_count + 1)), f"predecessor receipt sequence drift: {phase_id}")
        _require(all(item.get("result") == "PASS" and item.get("exit_code") == 0 for item in rows), f"predecessor receipt failure: {phase_id}")
        _require(len({item.get("run_id") for item in rows}) == 1, f"predecessor receipt run drift: {phase_id}")
        heads = {item.get("head_before") for item in rows} | {item.get("head_after") for item in rows}
        _require(len(heads) == 1, f"predecessor receipt HEAD drift: {phase_id}")
        head = str(next(iter(heads)))
        _require(_HEAD_RE.fullmatch(head) is not None and _is_ancestor(head), f"predecessor receipt HEAD unavailable: {phase_id}")
        subjects = {item.get("validation_subject_sha256") for item in rows}
        _require(len(subjects) == 1 and _HASH_RE.fullmatch(str(next(iter(subjects)))) is not None, f"predecessor receipt subject drift: {phase_id}")
        _require(all(item.get("phase_base_commit") == phase_manifest.get("phase_base_commit") for item in rows), f"predecessor phase base drift: {phase_id}")


def _validate_contracts_and_evidence(manifest: Mapping[str, Any]) -> None:
    contracts = _read_json(ARTIFACT_ROOT / builder.CONTRACTS_RELATIVE)
    rows = contracts.get("contracts")
    _require(isinstance(rows, list) and len(rows) == 14, "cross-Phase contract count drift")
    _require([row.get("contract_id") for row in rows] == [f"S03REV-C{i:02d}" for i in range(1, 15)], "cross-Phase contract IDs drift")
    _require(all(row.get("status") == "PASS" for row in rows), "cross-Phase contract failed")
    _require(contracts.get("accounting") == {"total": 14, "passed": 14, "failed": 0, "blocking_failed": 0}, "cross-Phase accounting drift")
    _require(manifest.get("cross_phase_accounting") == contracts["accounting"], "manifest cross-Phase accounting drift")

    findings = _read_csv(ARTIFACT_ROOT / builder.FINDINGS_RELATIVE)
    _require([row.get("finding_id") for row in findings] == ["S03REV-F001", "S03REV-F002"], "review finding IDs drift")
    _require(all(row.get("status") == "FIXED_VALIDATED" and row.get("blocks_stage_acceptance") == "false" for row in findings), "review finding closure drift")
    _require(manifest.get("review_findings") == {"total": 2, "fixed_validated": 2, "open": 0, "blocking_open": 0}, "manifest review finding accounting drift")

    risks = _read_csv(ARTIFACT_ROOT / builder.RISKS_RELATIVE)
    _require(len(risks) == 6 and [row.get("risk_id") for row in risks] == [f"RISK-KMFA-V015-S03-{i:03d}" for i in range(1, 7)], "risk register IDs/count drift")
    _require(all(row.get("status") == "ROUTED_RESIDUAL" and row.get("plan_complete") == "true" and row.get("blocks_s03_stage_acceptance") == "false" for row in risks), "risk route/plan drift")
    _require(manifest.get("open_risks") == {"total": 6, "routed": 6, "plan_gap_count": 0, "blocking": 0}, "manifest risk accounting drift")

    task_evidence = _read_json(ARTIFACT_ROOT / builder.TASK_EVIDENCE_RELATIVE)
    accounting = task_evidence.get("accounting")
    _require(accounting == {"task_count": 9, "slot_count": 90, "covered": 65, "n_a_with_rationale": 25, "invalid": 0}, "Task evidence accounting drift")
    _require(manifest.get("task_evidence_accounting") == accounting, "manifest Task evidence accounting drift")


def _validate_artifact_integrity(manifest: Mapping[str, Any]) -> None:
    rows = manifest.get("artifact_integrity")
    _require(isinstance(rows, list) and len(rows) == 10, "artifact integrity count drift")
    seen = set()
    for row in rows:
        ref = str(row.get("ref", ""))
        _require(ref in builder.ARTIFACT_REFS.values(), f"unknown artifact integrity ref: {ref}")
        path = REPO_ROOT / ref
        _require(path.is_file(), f"artifact missing: {ref}")
        _require(row.get("bytes") == path.stat().st_size and row.get("sha256") == _sha256(path), f"artifact integrity drift: {ref}")
        seen.add(ref)
    expected = set(builder.ARTIFACT_REFS.values()) - {builder.ARTIFACT_REFS["manifest"], builder.ARTIFACT_REFS["validation_results"]}
    _require(seen == expected, "artifact integrity coverage drift")


def _validate_static(*, final_expected: bool) -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    _require(manifest.get("schema_version") == "kmfa.v015.s03_stage_review.manifest.v1", "manifest schema drift")
    _require(manifest.get("project_id") == "KMFA" and manifest.get("target_release") == "v1.5", "manifest project/release drift")
    _require(manifest.get("stage_id") == "S03" and manifest.get("run_phase_id") == builder.RUN_PHASE_ID, "manifest Stage/Phase drift")
    _require(manifest.get("task_id") == builder.TASK_ID and manifest.get("acceptance_id") == builder.ACCEPTANCE_ID, "manifest task/acceptance drift")
    _require(manifest.get("review_base_commit") == builder.REVIEW_BASE_COMMIT, "review base drift")
    _require(manifest.get("counted_as_taskpack_phase") is False and manifest.get("counted_as_taskpack_task") is False, "review overlay was counted as Roadmap work")
    _require(manifest.get("content_hash") == builder._content_hash(manifest), "manifest content hash drift")
    _require(manifest.get("task_accounting") == {"total": 9, "accepted": 9}, "Task accounting drift")
    _validate_phase_evidence(manifest)
    _validate_contracts_and_evidence(manifest)
    _validate_artifact_integrity(manifest)

    runtime = builder.runtime_directory_summary()
    _require(runtime.get("invalid_directory_count") == 0 and runtime.get("all_directories_mode_0700") is True, "private runtime directory permission drift")
    _require(runtime.get("all_layers_gitignored") is True and runtime.get("gitignored_layer_count") == 9, "private runtime gitignore drift")
    _require(manifest.get("private_runtime") == runtime, "manifest private runtime summary drift")

    gate = manifest.get("stage_gate", {})
    expected_gate = {
        "review_execution_status": "COMPLETED" if final_expected else "EXECUTION_COMPLETE",
        "evidence_validation_status": "PASS" if final_expected else "PENDING",
        "stage_lifecycle_status": "COMPLETED" if final_expected else "IN_PROGRESS",
        "stage_acceptance_status": "PASSED" if final_expected else "PENDING",
        "decision": "GO_TO_S04_P1_ONLY" if final_expected else "REMAIN_IN_S03_STAGE_REVIEW",
    }
    _require(gate == expected_gate, "Stage gate drift")
    next_gate = manifest.get("next_entry_gate", {})
    _require(next_gate.get("s04_p1_entry_allowed") is final_expected, "S04-P1 entry gate drift")
    _require(next_gate.get("s04_p1_started") is False and next_gate.get("s04_plus_entry_allowed") is False, "downstream Stage started/allowed")
    _require(next_gate.get("github_upload_allowed") is False and next_gate.get("app_reinstall_allowed") is False, "upload/App gate widened")
    for key, value in manifest.get("downstream_actions", {}).items():
        _require(value is False, f"downstream action must remain false: {key}")

    rows = _read_jsonl(VALIDATION_RESULTS_PATH)
    final, accounting = builder.validation_status(rows)
    _require(final is final_expected, "validation receipt final state drift")
    _require(manifest.get("validation_receipts") == accounting, "manifest validation receipt accounting drift")
    if final_expected:
        head = str(rows[0].get("head_before"))
        subject = str(rows[0].get("validation_subject_sha256"))
        _require(manifest.get("validation_run_id") == rows[0].get("run_id"), "manifest validation run drift")
        _require(manifest.get("validation_head") == head and _HEAD_RE.fullmatch(head) is not None, "manifest validation HEAD drift")
        _require(manifest.get("validation_subject_sha256") == subject and _HASH_RE.fullmatch(subject) is not None, "manifest validation subject drift")
    else:
        _require(manifest.get("validation_run_id") is None and manifest.get("validation_head") is None and manifest.get("validation_subject_sha256") is None, "pending manifest has final receipt binding")
    return manifest


def _validate_governance(*, final_expected: bool) -> None:
    decision = "GO_TO_S04_P1_ONLY" if final_expected else "REMAIN_IN_S03_STAGE_REVIEW"
    lifecycle = "COMPLETED" if final_expected else "IN_PROGRESS"
    acceptance = "PASSED" if final_expected else "PENDING"
    for path in (PROJECT_ROOT / "docs/governance/project.yaml", PROJECT_ROOT / "docs/governance/roadmap.yaml"):
        _require(_top_scalar(path, "current_phase_id") == builder.RUN_PHASE_ID, f"current_phase_id drift: {path}")
        _require(_top_scalar(path, "current_task_id") == builder.TASK_ID, f"current_task_id drift: {path}")
        _require(_top_scalar(path, "current_acceptance_id") == builder.ACCEPTANCE_ID, f"current_acceptance_id drift: {path}")
        _require(_top_scalar(path, "stage_lifecycle_status") == lifecycle, f"stage lifecycle drift: {path}")
        _require(_top_scalar(path, "stage_acceptance_status") == acceptance, f"stage acceptance drift: {path}")
        _require(_top_scalar(path, "decision") == decision, f"Stage decision drift: {path}")
        _require(_top_scalar(path, "s04_p1_started") == "false", f"S04-P1 started drift: {path}")
        _require(_top_scalar(path, "github_upload_performed") == "false", f"GitHub upload drift: {path}")
        _require(_top_scalar(path, "app_reinstall_performed") == "false", f"App reinstall drift: {path}")
    for path in (PROJECT_ROOT / "README.md", PROJECT_ROOT / "HANDOFF.md"):
        text = path.read_text(encoding="utf-8")
        for token in (builder.RUN_PHASE_ID, builder.TASK_ID, builder.ACCEPTANCE_ID, decision):
            _require(token in text, f"governance token missing in {path.name}: {token}")

    for path in (PROJECT_ROOT / "docs/governance/events.jsonl", PROJECT_ROOT / "docs/governance/development_events.jsonl", PROJECT_ROOT / "metadata/stage_status.jsonl"):
        rows = _read_jsonl(path)
        matches = [row for row in rows if row.get("phase_id") == builder.RUN_PHASE_ID and row.get("acceptance_id") == builder.ACCEPTANCE_ID]
        _require(matches, f"Stage review governance event missing: {path}")
        latest = matches[-1]
        _require(latest.get("decision") == decision, f"Stage review event decision drift: {path}")
        _require(latest.get("stage_lifecycle_status") == lifecycle and latest.get("stage_acceptance_status") == acceptance, f"Stage review event state drift: {path}")
        _require(latest.get("s04_p1_started") is False and latest.get("github_upload_performed") is False and latest.get("app_reinstall_performed") is False, f"Stage review event boundary drift: {path}")


def _validate_added_line_safety() -> None:
    result = subprocess.run(["git", "diff", "--unified=0", f"{builder.REVIEW_BASE_COMMIT}..HEAD", "--", "KMFA"], cwd=REPO_ROOT, capture_output=True, check=False)
    if result.returncode:
        raise CheckError("unable to inspect review diff")
    added = b"\n".join(line[1:] for line in result.stdout.splitlines() if line.startswith(b"+") and not line.startswith(b"+++"))
    _require(builder._ABSOLUTE_PATH_RE.search(added) is None, "review diff added an absolute local path")
    _require(builder._SECRET_RE.search(added) is None, "review diff added a secret-like assignment")


def _validate_current_submission_safety() -> None:
    ignore = repository_safety.verify_gitignore_contract()
    _require(ignore.get("pass") is True, "current Git-ignore submission contract failed")
    for scope in ("head", "index", "worktree"):
        _, findings = repository_safety.scan_repository(scope=scope)
        _require(not findings, f"current {scope} repository scan found {len(findings)} blocking findings")


def _validate_clean_commit(manifest: Mapping[str, Any]) -> None:
    _require(not _git(["status", "--porcelain"]), "worktree must be clean")
    head = _git(["rev-parse", "HEAD"])
    parent = _git(["rev-parse", "HEAD^1"])
    receipt_head = str(manifest.get("validation_head"))
    _require(receipt_head == parent, "validation HEAD must be final evidence commit parent")
    _require(builder.validation_subject_sha256(receipt_head) == manifest.get("validation_subject_sha256"), "validation subject digest drift")
    changed = _git_diff_paths(receipt_head, head)
    _require(bool(changed), "final evidence commit is empty")
    _require(changed <= builder.FINAL_MUTABLE_REFS, "final evidence commit changed immutable refs: " + ", ".join(sorted(changed - builder.FINAL_MUTABLE_REFS)))
    all_changed = _git_diff_paths(builder.REVIEW_BASE_COMMIT, "HEAD")
    escaped = sorted(path for path in all_changed if path and not any(path == prefix or (prefix.endswith("/") and path.startswith(prefix)) for prefix in ALLOWED_REVIEW_PREFIXES))
    _require(not escaped, "S03 Stage review diff escaped scope: " + ", ".join(escaped))


def validate(*, pre_receipt: bool, skip_exact_rebuild: bool, require_clean_commit: bool) -> dict[str, Any]:
    manifest = _validate_static(final_expected=not pre_receipt)
    _validate_governance(final_expected=not pre_receipt)
    _validate_added_line_safety()
    if not skip_exact_rebuild:
        builder.run(write=False, check=True)
    if require_clean_commit:
        _require(not pre_receipt, "clean committed mode requires final receipts")
        _validate_clean_commit(manifest)
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pre-receipt", action="store_true")
    parser.add_argument("--skip-exact-rebuild", action="store_true")
    parser.add_argument("--require-clean-commit", action="store_true")
    parser.add_argument("--private-runtime-only", action="store_true")
    parser.add_argument("--current-submission-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.private_runtime_only and args.current_submission_only:
            raise CheckError("single-purpose live gates cannot be combined")
        if args.private_runtime_only:
            summary = builder.runtime_directory_summary()
            _require(summary["invalid_directory_count"] == 0 and summary["all_directories_mode_0700"] is True and summary["all_layers_gitignored"] is True, "private runtime contract failed")
            print(f"PASS: S03 private runtime directories={summary['directory_count_checked']} invalid=0 layers=9 ignored=9; no private file or raw inbox read")
            return 0
        if args.current_submission_only:
            _validate_current_submission_safety()
            print("PASS: S03 current HEAD/index/worktree repository submission safety; findings=0")
            return 0
        manifest = validate(pre_receipt=args.pre_receipt, skip_exact_rebuild=args.skip_exact_rebuild, require_clean_commit=args.require_clean_commit)
    except (builder.BuildError, CheckError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError, csv.Error) as error:
        print(f"FAIL: KMFA v1.5 S03 Stage review validation failed\n{error}", file=sys.stderr)
        return 1
    gate = manifest["stage_gate"]
    print(f"PASS: KMFA v1.5 S03 Stage review validated; stage={gate['stage_acceptance_status']} decision={gate['decision']} tasks=9/9 findings=2/0 risks=6 upload=false app=false s04_started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
