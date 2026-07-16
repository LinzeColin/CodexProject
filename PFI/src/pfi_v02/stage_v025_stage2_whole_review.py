from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from pfi_v02.stage_v025_data_inventory import build_public_artifact_scan_report


VERSION = "v0.2.5"
STAGE = 2
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE2-WHOLE-REVIEW"
CONTRACT_ID = "PFI-V025-STAGE2-WHOLE-REVIEW"
REVIEW_BASE = "431ddb30c483f6451c29dfb6890c4bee5690c57c"
PHASE_COMMITS = {
    "2.1": "bce1b21826a829094481a3ef63c46aa5aa95c99e",
    "2.2": "7875e006aa913a6afbc59e146ab28fc5dae94bc6",
    "2.3": REVIEW_BASE,
}
PHASE_EVIDENCE = {
    "2.1": "PFI/reports/pfi_v025/stage_2/phase_2_1/evidence.json",
    "2.2": "PFI/reports/pfi_v025/stage_2/phase_2_2/evidence.json",
    "2.3": "PFI/reports/pfi_v025/stage_2/phase_2_3/evidence.json",
}
PHASE_EVIDENCE_SHA256 = {
    "2.1": "81fb9fb6b1f4fef1974474622c08b1b08510f1692014bc896f689d3de14723db",
    "2.2": "dcefd989c4c82dadbcee03037318bff978cadf1158b1d160c9ed703316dc15f7",
    "2.3": "b1cd5ed64fd0af3433547c5c142f0f26263e5b0d94df0c294f41bb5f32f2ecfc",
}
TASK_IDS = tuple(f"S2-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5))
REVIEW_DIR = Path("PFI/reports/pfi_v025/stage_2/whole_stage_review")
_PRIVACY_INPUTS = (
    "PFI/reports/pfi_v025/stage_2/whole_stage_review/review_audit.json",
    "PFI/reports/pfi_v025/stage_2/whole_stage_review/final_evidence_index.json",
    "PFI/reports/pfi_v025/stage_2/whole_stage_review/source_disposition.json",
    "PFI/reports/pfi_v025/stage_2/whole_stage_review/human_acceptance.json",
    "PFI/reports/pfi_v025/stage_2/whole_stage_review/evidence.json",
    "PFI/docs/pfi_v025/stage_2/STAGE_2_WHOLE_STAGE_REVIEW.md",
    "PFI/reports/pfi_v025/stage_2/whole_stage_review/risk_and_rollback.md",
    "PFI/reports/pfi_v025/stage_2/whole_stage_review/terminal.log",
    "PFI/reports/pfi_v025/stage_2/whole_stage_review/changed_files.txt",
    "PFI/reports/pfi_v025/stage_2/phase_2_3/privacy_scan.txt",
)


def build_stage2_whole_review_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage2WholeReviewContractV1",
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
        "stage_3_work_performed": False,
        "finder_used": False,
        "push_performed": False,
        "app_install_performed": False,
    }


def evaluate_stage2_phase_evidence(project_root: str | Path) -> dict[str, Any]:
    root = _repo_root(project_root)
    observed: dict[str, str] = {}
    working_matches = True
    phase_status: dict[str, str] = {}
    task_ids: set[str] = set()
    for phase, relative in PHASE_EVIDENCE.items():
        commit = PHASE_COMMITS[phase]
        committed = _git_bytes(root, "show", f"{commit}:{relative}")
        current = (root / relative).read_bytes()
        digest = hashlib.sha256(committed).hexdigest()
        observed[phase] = digest
        working_matches = working_matches and committed == current
        payload = json.loads(committed.decode("utf-8"))
        phase_status[phase] = str(payload.get("status"))
        task_ids.update(str(item) for item in payload.get("task_ids", []))
    passed = (
        observed == PHASE_EVIDENCE_SHA256
        and working_matches
        and phase_status == {"2.1": "candidate_pass", "2.2": "candidate_pass", "2.3": "candidate_pass"}
        and task_ids == set(TASK_IDS)
    )
    return {
        "schema": "PFIV025Stage2PhaseEvidenceReviewV1",
        "status": "pass" if passed else "fail",
        "phase_count": 3,
        "task_count": len(task_ids),
        "phase_commits": dict(PHASE_COMMITS),
        "phase_status": phase_status,
        "phase_evidence_sha256": observed,
        "working_tree_matches_phase_commits": working_matches,
    }


def build_stage2_whole_review_privacy_scan(project_root: str | Path, observed_at: str) -> str:
    return build_public_artifact_scan_report(
        project_root,
        observed_at,
        inputs=_PRIVACY_INPUTS,
        scanner_name="pfi-v025-stage2-whole-review-public-artifact-scan-v1",
        scan_command=(
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B "
            "-m pytest -p no:cacheprovider PFI/tests/test_v025_stage2_whole_review.py -q"
        ),
    )


def verify_stage2_whole_review(
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
    phase_review = evaluate_stage2_phase_evidence(root)
    errors: list[str] = []

    pack = Path(task_pack).expanduser() if task_pack is not None else Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    with zipfile.ZipFile(pack) as archive:
        evidence_schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
        acceptance_schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"))
    try:
        Draft202012Validator(evidence_schema).validate(evidence)
        Draft202012Validator(acceptance_schema, format_checker=FormatChecker()).validate(acceptance)
    except Exception as exc:  # pragma: no cover - exact validator message is environment-specific
        errors.append(f"schema:{type(exc).__name__}")

    if phase_review["status"] != "pass":
        errors.append("phase_evidence")
    expected_tasks = {task: "pass" for task in TASK_IDS}
    if index.get("task_disposition") != expected_tasks:
        errors.append("task_disposition")
    if len(index.get("acceptance_criteria", [])) != 6 or not all(
        item.get("status") == "pass" for item in index.get("acceptance_criteria", [])
    ):
        errors.append("acceptance_criteria")
    if len(index.get("stop_conditions", [])) != 4 or not all(
        item.get("status") == "clear" for item in index.get("stop_conditions", [])
    ):
        errors.append("stop_conditions")
    if index.get("pass_gate_status") != "pass":
        errors.append("pass_gate")
    if audit.get("post_remediation_review", {}).get("counts") != {
        "critical": 0,
        "important": 0,
        "minor": 0,
    }:
        errors.append("review_findings")
    if disposition.get("financial_zero_claims") != 0:
        errors.append("false_zero")
    if disposition.get("production_fx", {}).get("status") != "not_loaded":
        errors.append("fx_truth")
    if acceptance.get("evidence_index_hash") != "sha256:" + _sha256(review_dir / "final_evidence_index.json"):
        errors.append("acceptance_index_binding")

    for relative, expected in evidence.get("artifact_hashes", {}).items():
        if _sha256(root / str(relative)) != str(expected):
            errors.append(f"artifact_hash:{relative}")
    privacy_path = review_dir / "privacy_scan.txt"
    observed_at = next(
        (line.removeprefix("observed_at=") for line in privacy_path.read_text(encoding="utf-8").splitlines() if line.startswith("observed_at=")),
        "",
    )
    try:
        expected_privacy = build_stage2_whole_review_privacy_scan(root, observed_at)
        if privacy_path.read_text(encoding="utf-8") != expected_privacy:
            errors.append("privacy_scan_drift")
    except (OSError, ValueError, json.JSONDecodeError):
        errors.append("privacy_scan")

    project_text = (root / "PFI/docs/governance/project.yaml").read_text(encoding="utf-8")
    roadmap_text = (root / "PFI/docs/governance/roadmap.yaml").read_text(encoding="utf-8")
    for token in (
        'stage_2_status: "accepted_for_transition"',
        "stage_3_entry_authorized: true",
        'stage_3_status: "not_started"',
    ):
        if token not in project_text or token not in roadmap_text:
            errors.append(f"governance:{token}")

    if candidate:
        resolved = _git_text(root, "rev-parse", candidate)
        if resolved != _git_text(root, "rev-parse", "HEAD"):
            errors.append("candidate_not_head")
        if _git_text(root, "rev-parse", f"{candidate}^") != REVIEW_BASE:
            errors.append("candidate_parent")
        if _git_bytes(root, "status", "--porcelain"):
            errors.append("worktree_not_clean")
        actual = sorted(_git_text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", candidate).splitlines())
    else:
        actual = _changed_paths(root)
    expected_changed = sorted((review_dir / "changed_files.txt").read_text(encoding="utf-8").splitlines())
    if actual != expected_changed or evidence.get("changed_files") != expected_changed:
        errors.append("changed_scope")

    prohibited_true = (
        "finder_used",
        "push_performed",
        "app_install_performed",
        "production_accepted",
        "final_human_acceptance",
        "stage_3_work_performed",
    )
    if any(bool(evidence.get(key)) for key in prohibited_true):
        errors.append("prohibited_action_or_claim")
    return {
        "schema": "PFIV025Stage2WholeReviewVerificationResultV1",
        "version": VERSION,
        "stage": STAGE,
        "acceptance_id": ACCEPTANCE_ID,
        "candidate": candidate,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "review_findings": audit.get("post_remediation_review", {}).get("counts"),
        "phase_evidence": phase_review,
        "task_count": len(expected_tasks),
        "acceptance_criteria_count": len(index.get("acceptance_criteria", [])),
        "stop_condition_count": len(index.get("stop_conditions", [])),
        "stage_2_status": index.get("status"),
        "stage_3_entry_authorized": index.get("stage_3_entry_authorized"),
        "stage_3_work_performed": False,
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
