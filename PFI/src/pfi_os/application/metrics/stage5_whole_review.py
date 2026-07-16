"""Independent Stage 5 whole-stage review contract and commit binding."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


VERSION = "v0.2.5"
STAGE = 5
REVIEW_BASE = "ec3e3af020cc37f5bddd39dba2e445895e015f9e"
CONTRACT_ID = "PFI-V025-STAGE5-WHOLE-REVIEW"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE5-WHOLE-REVIEW"
PHASE_COMMITS = {
    "5.1": "73a3186d0e64b65d77555aeb6f882c8e237790ae",
    "5.2": "61a14d9366c68a8c849c0c056a107116d5b377d1",
    "5.3": "ec3e3af020cc37f5bddd39dba2e445895e015f9e",
}
PHASE_EVIDENCE = {
    "5.1": "PFI/reports/pfi_v025/stage_5/phase_5_1/evidence.json",
    "5.2": "PFI/reports/pfi_v025/stage_5/phase_5_2/evidence.json",
    "5.3": "PFI/reports/pfi_v025/stage_5/phase_5_3/evidence.json",
}


def build_stage5_whole_review_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage5WholeReviewContractV1",
        "version": VERSION,
        "stage": STAGE,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "review_base": REVIEW_BASE,
        "phase_commits": dict(PHASE_COMMITS),
        "task_ids": [f"S5-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)],
        "risk_tier": "T3_FINANCIAL_MODEL_UI_REPORT_PRIVACY",
        "independent_whole_stage_review": True,
        "initial_review_required": True,
        "remediation_required": True,
        "rereview_required": True,
        "explicit_acceptance_required": True,
        "scope_exception": {
            "status": "accepted_for_required_acceptance_remediation",
            "reason": (
                "Stage 5 Allowed Files omit the formal Web/read-model consumers while the same Roadmap requires the main UI, "
                "consumption page and report to display the real four-component metric. The whole-stage remediation therefore "
                "touches only the minimum formal runtime binding files needed to satisfy that acceptance criterion."
            ),
            "exception_files": [
                "PFI/src/pfi_os/application/read_model_status.py",
                "PFI/web/app/shell.js",
                "PFI/scripts/v025/browser_validate_stage5_whole_review.py",
            ],
        },
        "real_data_read_only": True,
        "public_evidence_redacted": True,
        "financial_fixture_fallback_allowed": False,
        "database_changed": False,
        "finder_used": False,
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "stage_6_started": False,
    }


def evaluate_stage5_phase_evidence(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).expanduser().resolve()
    current_head = _git(root, "rev-parse", "HEAD")
    evidence_rows: list[dict[str, Any]] = []
    all_present = True
    all_ancestors = True
    for phase, commit in PHASE_COMMITS.items():
        path = PHASE_EVIDENCE[phase]
        present = _git_ok(root, "cat-file", "-e", f"{commit}:{path}")
        ancestor = _git_ok(root, "merge-base", "--is-ancestor", commit, current_head)
        all_present = all_present and present
        all_ancestors = all_ancestors and ancestor
        if not present:
            evidence_rows.append({"phase": phase, "commit": commit, "path": path, "present": False})
            continue
        payload = json.loads(_git(root, "show", f"{commit}:{path}"))
        evidence_rows.append(
            {
                "phase": phase,
                "commit": commit,
                "path": path,
                "present": True,
                "status": payload.get("status") or payload.get("result"),
                "contract_id": payload.get("contract_id"),
                "sha256": "sha256:" + hashlib.sha256(
                    _git_bytes(root, "show", f"{commit}:{path}")
                ).hexdigest(),
            }
        )
    linear = (
        _git(root, "rev-parse", f"{PHASE_COMMITS['5.2']}^") == PHASE_COMMITS["5.1"]
        and _git(root, "rev-parse", f"{PHASE_COMMITS['5.3']}^") == PHASE_COMMITS["5.2"]
    )
    statuses_ok = all(row.get("status") == "candidate_pass" for row in evidence_rows)
    status = "pass" if all_present and all_ancestors and linear and statuses_ok else "fail"
    return {
        "schema": "PFIV025Stage5PhaseCommitBindingV1",
        "version": VERSION,
        "stage": STAGE,
        "status": status,
        "review_base": REVIEW_BASE,
        "current_head": current_head,
        "phase_commits": dict(PHASE_COMMITS),
        "phase_evidence": evidence_rows,
        "task_count": 12,
        "linear_commit_chain": linear,
        "all_phase_commits_are_ancestors": all_ancestors,
        "all_phase_evidence_present_in_bound_commits": all_present,
        "all_phase_evidence_candidate_pass": statuses_ok,
    }


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _git_bytes(root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _git_ok(root: Path, *args: str) -> bool:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
