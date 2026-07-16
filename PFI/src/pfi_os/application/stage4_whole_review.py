from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


VERSION = "v0.2.5"
STAGE = 4
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE4-WHOLE-REVIEW"
CONTRACT_ID = "PFI-V025-STAGE4-WHOLE-REVIEW"
REVIEW_BASE = "8478bbc65ed739ef5f22b1cfc4a932f15837be1d"
PHASE_COMMITS = {
    "4.1": "c12acf6de23111eea71ccd077bd94bcefa05fdb4",
    "4.2": "1ab51eb518c30b10bab6a7d9b4442e7c462c6452",
    "4.3": REVIEW_BASE,
}
PHASE_EVIDENCE = {
    phase: f"PFI/reports/pfi_v025/stage_4/phase_{phase.replace('.', '_')}/evidence.json"
    for phase in PHASE_COMMITS
}
PHASE_EVIDENCE_SHA256 = {
    "4.1": "c43892376f33294cc137579fb3ac0015ba27a7d1e1ee08874306fbde0a50dcd5",
    "4.2": "b848f363bc983d7c6399963dffec36cd40b33efecd2169844c464de13e9e22c4",
    "4.3": "12218a5aa0eb9f389856a042c1f4e0d4a97e86c1f55d940eaafd4b4233a17bb2",
}
TASK_IDS = tuple(f"S4-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5))
REVIEW_DIR = Path("PFI/reports/pfi_v025/stage_4/whole_stage_review")


def build_stage4_whole_review_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage4WholeReviewContractV1",
        "version": VERSION,
        "stage": STAGE,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_base": REVIEW_BASE,
        "task_ids": list(TASK_IDS),
        "acceptance_criteria_count": 6,
        "stop_condition_count": 4,
        "review_tracks": ["requirements_evidence", "code_security_privacy", "governance_renderer"],
        "user_confirmation_reference": "conversation_user_blanket_interim_authorization_before_final_acceptance",
        "stage_5_work_performed": False,
        "finder_used": False,
        "network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
    }


def evaluate_stage4_phase_evidence(project_root: str | Path) -> dict[str, Any]:
    root = _repo_root(project_root)
    observed: dict[str, str] = {}
    statuses: dict[str, str] = {}
    tasks: set[str] = set()
    current_matches = True
    for phase, relative in PHASE_EVIDENCE.items():
        committed = _git_bytes(root, "show", f"{PHASE_COMMITS[phase]}:{relative}")
        current = (root / relative).read_bytes()
        observed[phase] = hashlib.sha256(committed).hexdigest()
        current_matches = current_matches and committed == current
        payload = json.loads(committed)
        statuses[phase] = str(payload.get("status"))
        tasks.update(str(item) for item in payload.get("task_ids", []))
    passed = (
        observed == PHASE_EVIDENCE_SHA256
        and current_matches
        and statuses == {phase: "candidate_pass" for phase in PHASE_COMMITS}
        and tasks == set(TASK_IDS)
    )
    return {
        "schema": "PFIV025Stage4PhaseEvidenceReviewV1",
        "status": "pass" if passed else "fail",
        "phase_count": 3,
        "task_count": len(tasks),
        "phase_commits": dict(PHASE_COMMITS),
        "phase_status": statuses,
        "phase_evidence_sha256": observed,
        "working_tree_matches_phase_commits": current_matches,
    }


def verify_stage4_whole_review(
    project_root: str | Path,
    *,
    candidate: str | None = None,
    task_pack: str | Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(project_root)
    review_dir = root / REVIEW_DIR
    evidence = _json(review_dir / "evidence.json")
    audit = _json(review_dir / "review_audit.json")
    index = _json(review_dir / "final_evidence_index.json")
    metrics = _json(review_dir / "metric_disposition.json")
    acceptance = _json(review_dir / "human_acceptance.json")
    browser = _json(review_dir / "browser_validation.json")
    a11y = _json(review_dir / "accessibility_tree.json")
    errors: list[str] = []

    pack = Path(task_pack).expanduser() if task_pack else Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    with zipfile.ZipFile(pack) as archive:
        evidence_schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"))
        acceptance_schema = json.loads(archive.read("PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"))
    try:
        Draft202012Validator(evidence_schema).validate(evidence)
        Draft202012Validator(acceptance_schema, format_checker=FormatChecker()).validate(acceptance)
    except Exception as exc:  # pragma: no cover
        errors.append(f"schema:{type(exc).__name__}")

    phase_review = evaluate_stage4_phase_evidence(root)
    if phase_review["status"] != "pass":
        errors.append("phase_evidence")
    if index.get("task_disposition") != {task: "pass" for task in TASK_IDS}:
        errors.append("task_disposition")
    if len(index.get("acceptance_criteria", [])) != 6 or not all(item.get("status") == "pass" for item in index.get("acceptance_criteria", [])):
        errors.append("acceptance_criteria")
    if len(index.get("stop_conditions", [])) != 4 or not all(item.get("status") == "safety_stop_active" for item in index.get("stop_conditions", [])):
        errors.append("stop_conditions")
    if index.get("pass_gate_result") != "pass_with_not_loaded_sources":
        errors.append("pass_gate")
    if audit.get("post_remediation_review", {}).get("counts") != {"critical": 0, "important": 0, "minor": 0}:
        errors.append("review_findings")

    expected_metrics = {
        "metric_count": 7,
        "statuses": {"not_loaded": 7},
        "non_null_value_count": 0,
        "confirmed_zero_count": 0,
        "false_zero_count": 0,
        "surface_count": 5,
        "surface_hash_count": 1,
        "read_model_hash": "sha256:56527147cd3bb48cd3262696a6289e0396208e4de751022368497dcce94d779e",
    }
    for key, value in expected_metrics.items():
        if metrics.get(key) != value:
            errors.append(f"metric:{key}")
    if browser.get("status") != "pass" or browser.get("false_zero_render_count") != 0 or browser.get("finder_used") is not False:
        errors.append("browser")
    if a11y.get("status") != "pass" or int(a11y.get("missing_state_explanation_count", 0)) < 1:
        errors.append("a11y")
    if acceptance.get("evidence_index_hash") != "sha256:" + _sha256(review_dir / "final_evidence_index.json"):
        errors.append("acceptance_index_binding")
    for relative, expected in evidence.get("artifact_hashes", {}).items():
        target = root / str(relative)
        if not target.is_file() or _sha256(target) != str(expected):
            errors.append(f"artifact_hash:{relative}")

    project = (root / "PFI/docs/governance/project.yaml").read_text(encoding="utf-8")
    roadmap = (root / "PFI/docs/governance/roadmap.yaml").read_text(encoding="utf-8")
    for token in (
        'stage_4_status: "accepted_for_transition"',
        "stage_5_entry_authorized: true",
        'stage_5_status: "not_started"',
    ):
        if token not in project or token not in roadmap:
            errors.append(f"governance:{token}")
    if 'next_gate_id: "ACC-PFI-V025-STAGE5-WHOLE-REVIEW"' not in roadmap:
        errors.append("governance:next_gate")
    if "v0.2.5 Stage 4 当前真值" not in (root / "PFI/README.md").read_text(encoding="utf-8"):
        errors.append("readme_current_truth")
    if "v0.2.5 Stage 4 当前交接" not in (root / "PFI/HANDOFF.md").read_text(encoding="utf-8"):
        errors.append("handoff_current_truth")

    actual = _changed_paths(root)
    if candidate:
        if _git_text(root, "rev-parse", f"{candidate}^") != REVIEW_BASE:
            errors.append("candidate_parent")
        actual = sorted(_git_text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", candidate).splitlines())
    expected_changed = sorted((review_dir / "changed_files.txt").read_text(encoding="utf-8").splitlines())
    if actual != expected_changed or evidence.get("changed_files") != expected_changed:
        errors.append("changed_scope")
    prohibited = ("finder_used", "network_performed", "push_performed", "app_install_performed", "production_accepted", "final_human_acceptance", "stage_5_work_performed", "database_changed")
    if any(bool(evidence.get(key)) for key in prohibited):
        errors.append("prohibited_action_or_claim")
    return {
        "schema": "PFIV025Stage4WholeReviewVerificationResultV1",
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "phase_evidence": phase_review,
        "task_count": 12,
        "acceptance_criteria_count": 6,
        "stop_condition_count": 4,
        "stage_4_status": index.get("status"),
        "stage_5_entry_authorized": index.get("stage_5_entry_authorized"),
        "stage_5_work_performed": False,
        "finder_used": False,
    }


def _repo_root(path: str | Path) -> Path:
    return Path(_git_text(Path(path).expanduser().absolute(), "rev-parse", "--show-toplevel"))


def _git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, check=True, capture_output=True).stdout


def _git_text(root: Path, *args: str) -> str:
    return _git_bytes(root, *args).decode("utf-8").strip()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _changed_paths(root: Path) -> list[str]:
    tracked = _git_text(root, "diff", "HEAD", "--name-only").splitlines()
    untracked = _git_text(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked + untracked))


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only PFI v0.2.5 Stage 4 whole-stage verifier")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--candidate")
    parser.add_argument("--task-pack")
    args = parser.parse_args()
    result = verify_stage4_whole_review(args.repo_root, candidate=args.candidate, task_pack=args.task_pack)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
