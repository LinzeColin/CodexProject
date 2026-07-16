from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from pfi_v02.stage_v025_data_inventory import build_public_artifact_scan_report


VERSION = "v0.2.5"
STAGE = 3
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE3-WHOLE-REVIEW"
CONTRACT_ID = "PFI-V025-STAGE3-WHOLE-REVIEW"
REVIEW_BASE = "0f9672081463523bab35a2b310216078fd3ad9d3"
PHASE_COMMITS = {
    "3.1": "c0cf0a11291a7848206f72a13bce37bb2d41ff39",
    "3.2": "debdd04a9c5d12393d098dc65dd8937da3ce43f3",
    "3.3": REVIEW_BASE,
}
PHASE_EVIDENCE = {
    "3.1": "PFI/reports/pfi_v025/stage_3/phase_3_1/evidence.json",
    "3.2": "PFI/reports/pfi_v025/stage_3/phase_3_2/evidence.json",
    "3.3": "PFI/reports/pfi_v025/stage_3/phase_3_3/evidence.json",
}
PHASE_EVIDENCE_SHA256 = {
    "3.1": "e73fc62cfd58b0a6dc04372ab4a5420d3bb81e078fed4b0b83287d93205c84d7",
    "3.2": "884e73071d9afd7658e86ab79b58ac120c0a37deaafa6c8867c750315d839fcd",
    "3.3": "c9195e92f84123a528ef650cd8bfbaf999d5092a19501eec01b32e95d930cf6f",
}
TASK_IDS = tuple(f"S3-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5))
REVIEW_DIR = Path("PFI/reports/pfi_v025/stage_3/whole_stage_review")
_PRIVACY_INPUTS = (
    "PFI/reports/pfi_v025/stage_3/whole_stage_review/review_audit.json",
    "PFI/reports/pfi_v025/stage_3/whole_stage_review/final_evidence_index.json",
    "PFI/reports/pfi_v025/stage_3/whole_stage_review/source_disposition.json",
    "PFI/reports/pfi_v025/stage_3/whole_stage_review/human_acceptance.json",
    "PFI/reports/pfi_v025/stage_3/whole_stage_review/evidence.json",
    "PFI/docs/pfi_v025/stage_3/STAGE_3_WHOLE_STAGE_REVIEW.md",
    "PFI/reports/pfi_v025/stage_3/whole_stage_review/risk_and_rollback.md",
    "PFI/reports/pfi_v025/stage_3/whole_stage_review/terminal.log",
    "PFI/reports/pfi_v025/stage_3/whole_stage_review/changed_files.txt",
    "PFI/reports/pfi_v025/stage_3/phase_3_3/privacy_scan.txt",
)


def build_stage3_whole_review_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage3WholeReviewContractV1",
        "version": VERSION,
        "stage": STAGE,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_base": REVIEW_BASE,
        "task_ids": list(TASK_IDS),
        "acceptance_criteria_count": 6,
        "stop_condition_count": 4,
        "independent_review_tracks": [
            "requirements_evidence",
            "code_security_privacy",
            "governance_renderer",
        ],
        "user_confirmation_reference": "conversation_user_blanket_interim_authorization_before_final_acceptance",
        "stage_4_work_performed": False,
        "finder_used": False,
        "push_performed": False,
        "app_install_performed": False,
    }


def evaluate_stage3_phase_evidence(project_root: str | Path) -> dict[str, Any]:
    root = _repo_root(project_root)
    observed: dict[str, str] = {}
    phase_status: dict[str, str] = {}
    task_ids: set[str] = set()
    working_matches = True
    artifact_hashes_valid = True
    for phase, relative in PHASE_EVIDENCE.items():
        committed = _git_bytes(root, "show", f"{PHASE_COMMITS[phase]}:{relative}")
        current = (root / relative).read_bytes()
        observed[phase] = hashlib.sha256(committed).hexdigest()
        working_matches = working_matches and committed == current
        payload = json.loads(committed.decode("utf-8"))
        phase_status[phase] = str(payload.get("status"))
        task_ids.update(str(item) for item in payload.get("task_ids", []))
        for artifact, expected in payload.get("artifact_hashes", {}).items():
            target = root / str(artifact)
            artifact_hashes_valid = (
                artifact_hashes_valid
                and target.is_file()
                and _sha256(target) == str(expected)
            )
    passed = (
        observed == PHASE_EVIDENCE_SHA256
        and working_matches
        and artifact_hashes_valid
        and phase_status == {"3.1": "candidate_pass", "3.2": "candidate_pass", "3.3": "candidate_pass"}
        and task_ids == set(TASK_IDS)
    )
    return {
        "schema": "PFIV025Stage3PhaseEvidenceReviewV1",
        "status": "pass" if passed else "fail",
        "phase_count": 3,
        "task_count": len(task_ids),
        "phase_commits": dict(PHASE_COMMITS),
        "phase_status": phase_status,
        "phase_evidence_sha256": observed,
        "working_tree_matches_phase_commits": working_matches,
        "phase_artifact_hashes_valid": artifact_hashes_valid,
    }


def build_stage3_whole_review_privacy_scan(project_root: str | Path, observed_at: str) -> str:
    return build_public_artifact_scan_report(
        project_root,
        observed_at,
        inputs=_PRIVACY_INPUTS,
        scanner_name="pfi-v025-stage3-whole-review-public-artifact-scan-v1",
        scan_command=(
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B "
            "-m pytest -p no:cacheprovider PFI/tests/test_v025_stage3_whole_review.py -q"
        ),
    )


def verify_stage3_whole_review(
    project_root: str | Path,
    *,
    candidate: str | None = None,
    task_pack: str | Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(project_root)
    review_dir = root / REVIEW_DIR
    evidence = _read_json(review_dir / "evidence.json")
    audit = _read_json(review_dir / "review_audit.json")
    index = _read_json(review_dir / "final_evidence_index.json")
    disposition = _read_json(review_dir / "source_disposition.json")
    acceptance = _read_json(review_dir / "human_acceptance.json")
    phase_review = evaluate_stage3_phase_evidence(root)
    errors: list[str] = []

    pack = (
        Path(task_pack).expanduser()
        if task_pack is not None
        else Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    )
    with zipfile.ZipFile(pack) as archive:
        evidence_schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
        acceptance_schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"))
    try:
        Draft202012Validator(evidence_schema).validate(evidence)
        Draft202012Validator(acceptance_schema, format_checker=FormatChecker()).validate(acceptance)
    except Exception as exc:  # pragma: no cover - validator wording is environment-specific
        errors.append(f"schema:{type(exc).__name__}")

    if phase_review["status"] != "pass":
        errors.append("phase_evidence")
    expected_tasks = {task: "pass" for task in TASK_IDS}
    if index.get("task_disposition") != expected_tasks:
        errors.append("task_disposition")
    criteria = index.get("acceptance_criteria", [])
    if len(criteria) != 6 or not all(item.get("status") == "pass" for item in criteria):
        errors.append("acceptance_criteria")
    stop_conditions = index.get("stop_conditions", [])
    if len(stop_conditions) != 4 or not all(item.get("status") == "clear" for item in stop_conditions):
        errors.append("stop_conditions")
    if index.get("pass_gate_status") != "pass" or index.get("pass_gate_result") != "pass_with_review_queue":
        errors.append("pass_gate")
    if audit.get("post_remediation_review", {}).get("counts") != {
        "critical": 0,
        "important": 0,
        "minor": 0,
    }:
        errors.append("review_findings")

    expected_snapshot = {
        "source_id": "SRC-TRANSACTIONS-ALIPAY",
        "isolation_mode": "immutable_git_object_snapshot",
        "input_record_count": 8815,
        "published_record_count": 6879,
        "review_queue_record_count": 1936,
        "silent_drop_count": 0,
    }
    if disposition.get("real_snapshot") != expected_snapshot:
        errors.append("source_partition")
    if disposition.get("review_reason_counts") != {
        "refund_offset_missing": 249,
        "transfer_role_or_link_missing": 1250,
        "upstream_review_required": 406,
        "zero_amount": 31,
    }:
        errors.append("review_queue")
    if disposition.get("transfer_chain", {}).get("confirmed") is not False:
        errors.append("transfer_overclaim")
    if disposition.get("refund_chain", {}).get("confirmed") is not False:
        errors.append("refund_overclaim")
    if disposition.get("investment_chain", {}).get("published_count") != 3166:
        errors.append("investment_chain")
    if disposition.get("financial_zero_claims") != 0:
        errors.append("false_zero")

    if acceptance.get("evidence_index_hash") != "sha256:" + _sha256(review_dir / "final_evidence_index.json"):
        errors.append("acceptance_index_binding")
    for relative, expected in evidence.get("artifact_hashes", {}).items():
        target = root / str(relative)
        if not target.is_file() or _sha256(target) != str(expected):
            errors.append(f"artifact_hash:{relative}")

    privacy_path = review_dir / "privacy_scan.txt"
    observed_at = next(
        (
            line.removeprefix("observed_at=")
            for line in privacy_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("observed_at=")
        ),
        "",
    )
    try:
        if privacy_path.read_text(encoding="utf-8") != build_stage3_whole_review_privacy_scan(root, observed_at):
            errors.append("privacy_scan_drift")
    except (OSError, ValueError, json.JSONDecodeError):
        errors.append("privacy_scan")

    project_text = (root / "PFI/docs/governance/project.yaml").read_text(encoding="utf-8")
    roadmap_text = (root / "PFI/docs/governance/roadmap.yaml").read_text(encoding="utf-8")
    for token in (
        'stage_3_status: "accepted_for_transition"',
        "stage_4_entry_authorized: true",
        'stage_4_status: "not_started"',
    ):
        if token not in project_text or token not in roadmap_text:
            errors.append(f"governance:{token}")
    if 'next_gate_id: "ACC-PFI-V025-S4-P41-ACCOUNT-SNAPSHOT"' not in roadmap_text:
        errors.append("governance:next_gate")

    if candidate:
        resolved = _git_text(root, "rev-parse", candidate)
        if resolved != _git_text(root, "rev-parse", "HEAD"):
            errors.append("candidate_not_head")
        if _git_text(root, "rev-parse", f"{candidate}^") != REVIEW_BASE:
            errors.append("candidate_parent")
        if _git_bytes(root, "status", "--porcelain"):
            errors.append("worktree_not_clean")
        actual = sorted(
            _git_text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", candidate).splitlines()
        )
    else:
        actual = _changed_paths(root)
    expected_changed = sorted((review_dir / "changed_files.txt").read_text(encoding="utf-8").splitlines())
    if actual != expected_changed or evidence.get("changed_files") != expected_changed:
        errors.append("changed_scope")

    prohibited_true = (
        "finder_used",
        "network_performed",
        "push_performed",
        "app_install_performed",
        "production_accepted",
        "final_human_acceptance",
        "stage_4_work_performed",
        "source_mutation_performed",
        "database_changed",
    )
    if any(bool(evidence.get(key)) for key in prohibited_true):
        errors.append("prohibited_action_or_claim")
    return {
        "schema": "PFIV025Stage3WholeReviewVerificationResultV1",
        "version": VERSION,
        "stage": STAGE,
        "acceptance_id": ACCEPTANCE_ID,
        "candidate": candidate,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "review_findings": audit.get("post_remediation_review", {}).get("counts"),
        "phase_evidence": phase_review,
        "task_count": len(expected_tasks),
        "acceptance_criteria_count": len(criteria),
        "stop_condition_count": len(stop_conditions),
        "stage_3_status": index.get("status"),
        "stage_4_entry_authorized": index.get("stage_4_entry_authorized"),
        "stage_4_work_performed": False,
        "finder_used": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    }


def _repo_root(project_root: str | Path) -> Path:
    return Path(_git_text(Path(project_root).expanduser().absolute(), "rev-parse", "--show-toplevel"))


def _git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout


def _git_text(root: Path, *args: str) -> str:
    return _git_bytes(root, *args).decode("utf-8").strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _changed_paths(root: Path) -> list[str]:
    tracked = _git_text(root, "diff", "HEAD", "--name-only").splitlines()
    untracked = _git_text(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked + untracked))


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only PFI v0.2.5 Stage 3 whole-stage verifier")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--candidate")
    parser.add_argument("--task-pack")
    args = parser.parse_args()
    result = verify_stage3_whole_review(
        Path(args.repo_root),
        candidate=args.candidate,
        task_pack=args.task_pack,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
