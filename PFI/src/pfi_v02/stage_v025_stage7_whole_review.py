"""PFI v0.2.5 Stage 7 independent whole-stage review contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


VERSION = "v0.2.5"
STAGE = 7
REVIEW_BASE = "fc2c7db7e5906f4d1a0902a2907eb3155bfa89bf"
CONTRACT_ID = "PFI-V025-STAGE7-WHOLE-REVIEW"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE7-WHOLE-REVIEW"
PHASE_COMMITS = {
    "7.1": "a81175771a5186605b506a77ea4e9e852c739e2d",
    "7.2": "45d362c7ff95320aa2bbe0fcc841102abc48c146",
    "7.3": REVIEW_BASE,
}
PHASE_EVIDENCE = {
    phase: f"PFI/reports/pfi_v025/stage_7/phase_{phase.replace('.', '_')}/evidence.json"
    for phase in PHASE_COMMITS
}


def build_stage7_whole_review_contract() -> dict[str, Any]:
    """Return the bounded, fail-closed Stage 7 acceptance contract."""

    return {
        "schema": "PFIV025Stage7WholeReviewContractV1",
        "version": VERSION,
        "stage": STAGE,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "review_base": REVIEW_BASE,
        "phase_commits": dict(PHASE_COMMITS),
        "task_ids": [f"S7-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)],
        "risk_tier": "T3_FINANCIAL_WORKFLOW_PERSISTENCE_PRIVACY_RELEASE",
        "independent_whole_stage_review": True,
        "initial_review_required": True,
        "remediation_required": True,
        "rereview_required": True,
        "explicit_acceptance_required": True,
        "actual_current_head_browser_review_required": True,
        "sqlite_transaction_and_restart_evidence_required": True,
        "taskpack_evidence_schema_required": True,
        "public_evidence_redacted": True,
        "workflow_ids": [
            "real_upload_preview_review_ledger",
            "holding_settings_sqlite_restart",
            "parameter_interconnection_metric_drilldown",
        ],
        "allowed_file_exception_policy": (
            "minimum formal-shell/runtime/release/governance integration is accepted only when "
            "the phase records an explicit exception and does not create a sidecar product surface"
        ),
        "finder_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "stage_8_started": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    }


def evaluate_stage7_phase_evidence(repo_root: Path | str) -> dict[str, Any]:
    """Prove each Phase evidence existed in the exact linear Phase commit."""

    root = Path(repo_root).expanduser().resolve()
    current_head = _git(root, "rev-parse", "HEAD")
    rows: list[dict[str, Any]] = []
    all_present = True
    all_ancestors = True
    for phase, commit in PHASE_COMMITS.items():
        path = PHASE_EVIDENCE[phase]
        present = _git_ok(root, "cat-file", "-e", f"{commit}:{path}")
        ancestor = _git_ok(root, "merge-base", "--is-ancestor", commit, current_head)
        all_present = all_present and present
        all_ancestors = all_ancestors and ancestor
        row: dict[str, Any] = {
            "phase": phase,
            "commit": commit,
            "path": path,
            "present": present,
            "ancestor_of_current_head": ancestor,
        }
        if present:
            raw = _git_bytes(root, "show", f"{commit}:{path}")
            payload = json.loads(raw)
            row.update(
                {
                    "status": payload.get("status") or payload.get("result"),
                    "contract_id": payload.get("contract_id"),
                    "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                }
            )
        rows.append(row)

    linear = (
        _git(root, "rev-parse", f"{PHASE_COMMITS['7.2']}^") == PHASE_COMMITS["7.1"]
        and _git(root, "rev-parse", f"{PHASE_COMMITS['7.3']}^") == PHASE_COMMITS["7.2"]
    )
    statuses_ok = all(row.get("status") == "candidate_pass" for row in rows)
    status = "pass" if all_present and all_ancestors and linear and statuses_ok else "fail"
    return {
        "schema": "PFIV025Stage7PhaseCommitBindingV1",
        "version": VERSION,
        "stage": STAGE,
        "status": status,
        "review_base": REVIEW_BASE,
        "current_head": current_head,
        "phase_commits": dict(PHASE_COMMITS),
        "phase_evidence": rows,
        "task_count": 12,
        "linear_commit_chain": linear,
        "all_phase_commits_are_ancestors": all_ancestors,
        "all_phase_evidence_present_in_bound_commits": all_present,
        "all_phase_evidence_candidate_pass": statuses_ok,
    }


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    )
    return completed.stdout.strip()


def _git_bytes(root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return completed.stdout


def _git_ok(root: Path, *args: str) -> bool:
    return subprocess.run(
        ["git", *args], cwd=root, check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
