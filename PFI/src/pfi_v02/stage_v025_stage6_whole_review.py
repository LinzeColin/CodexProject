"""Independent Stage 6 whole-stage review and immutable phase binding."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


VERSION = "v0.2.5"
STAGE = 6
REVIEW_BASE = "8c18cbf56d3952f1d7e7d74fa424f3fb8889b431"
CONTRACT_ID = "PFI-V025-STAGE6-WHOLE-REVIEW"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE6-WHOLE-REVIEW"
PHASE_COMMITS = {
    "6.1": "6b96bcb655b1c11d91b23dd10cf25b33e37f0242",
    "6.2": "80396224f049658e9293f8da313a92a50431f903",
    "6.3": REVIEW_BASE,
}
PHASE_EVIDENCE = {
    phase: f"PFI/reports/pfi_v025/stage_6/phase_{phase.replace('.', '_')}/evidence.json"
    for phase in PHASE_COMMITS
}


def build_stage6_whole_review_contract() -> dict[str, Any]:
    """Return the bounded, fail-closed review contract for Stage 6."""

    return {
        "schema": "PFIV025Stage6WholeReviewContractV1",
        "version": VERSION,
        "stage": STAGE,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "review_base": REVIEW_BASE,
        "phase_commits": dict(PHASE_COMMITS),
        "task_ids": [f"S6-P{phase}-T{task}" for phase in range(1, 4) for task in range(1, 5)],
        "risk_tier": "T2_ROUTE_STATE_ACCESSIBILITY_RELEASE_PRIVACY",
        "independent_whole_stage_review": True,
        "initial_review_required": True,
        "remediation_required": True,
        "rereview_required": True,
        "explicit_acceptance_required": True,
        "primary_entry_count": 10,
        "secondary_page_count": 45,
        "canonical_route_count": 55,
        "legacy_alias_count": 7,
        "shared_responsive_primary_tree_required": True,
        "actual_current_head_browser_review_required": True,
        "taskpack_evidence_schema_required": True,
        "public_evidence_redacted": True,
        "real_financial_data_read": False,
        "real_financial_data_mutated": False,
        "database_changed": False,
        "finder_used": False,
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "stage_7_started": False,
    }


def evaluate_stage6_phase_evidence(repo_root: Path | str) -> dict[str, Any]:
    """Prove phase evidence existed in the exact linear phase commits."""

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
        evidence_rows.append(row)
    linear = (
        _git(root, "rev-parse", f"{PHASE_COMMITS['6.2']}^") == PHASE_COMMITS["6.1"]
        and _git(root, "rev-parse", f"{PHASE_COMMITS['6.3']}^") == PHASE_COMMITS["6.2"]
    )
    statuses_ok = all(row.get("status") == "candidate_pass" for row in evidence_rows)
    status = "pass" if all_present and all_ancestors and linear and statuses_ok else "fail"
    return {
        "schema": "PFIV025Stage6PhaseCommitBindingV1",
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
