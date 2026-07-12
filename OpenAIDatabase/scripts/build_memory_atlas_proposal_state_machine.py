#!/usr/bin/env python3
"""Build the Memory Atlas v1.2 S13 P1 proposal state-machine report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "MA-V12-S13P1"
ACCEPTANCE_ID = "ACC-MA-V12-S13P1"
STATUS = "phase_s13_p1_proposal_state_machine_completed_pending_s13_p2"
CONTRACT_VERSION = "proposal_state_machine.v1_2_s13_p1"
SCHEMA_VERSION = "openai_database.proposal_state_machine.v1_2_s13_p1"

CONFIG_PATH = Path("机器治理/运行门禁/proposal_state_machine.v1_2_s13_p1.json")
SELF_ITERATION_PATH = Path("data/derived/behavior_intelligence/self_iteration_suggestions.json")
DECISION_DEBT_PATH = Path("data/derived/behavior_intelligence/decision_debt_ledger.json")
AUTHORIZATION_PATH = Path("data/derived/agent_collaboration/agent_authorization_boundary_report.json")
OUTPUT_PATH = Path("data/derived/proposals/proposal_state_machine_report.json")

FORBIDDEN_TARGET_FRAGMENTS = ("data/public_raw/", "data/raw/", "data/private_imports/", "credentials", "cookies", "tokens")


class ProposalStateBuildError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ProposalStateBuildError(f"missing required input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def isoformat_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_as_of(*payloads: dict[str, Any]) -> datetime:
    candidates = [parse_time(str(payload.get("generated_at"))) for payload in payloads if payload.get("generated_at")]
    valid = [candidate for candidate in candidates if candidate is not None]
    if not valid:
        return datetime(2026, 7, 8, tzinfo=timezone.utc)
    return max(valid)


def expiry_bucket(created_at: str | None, expires_at: str | None, as_of: datetime, expiry: dict[str, Any]) -> str:
    expires = parse_time(expires_at)
    created = parse_time(created_at)
    if expires and as_of >= expires:
        return "expired"
    if not created:
        return "active"
    age_days = max(0, (as_of - created).days)
    if age_days >= int(expiry.get("archive_after_days") or 90):
        return "archive_due"
    if age_days >= int(expiry.get("stale_after_days") or 30):
        return "stale"
    if age_days >= int(expiry.get("warn_after_days") or 7):
        return "warn"
    return "active"


def allowed_next_states(current_state: str, state_machine: dict[str, Any]) -> list[str]:
    transitions = state_machine.get("transitions") if isinstance(state_machine.get("transitions"), list) else []
    return [
        str(transition.get("to"))
        for transition in transitions
        if isinstance(transition, dict) and transition.get("from") == current_state and transition.get("to")
    ]


def validate_config(config: dict[str, Any]) -> None:
    required_states = {
        "draft",
        "pending_human_review",
        "approved_by_human",
        "applying",
        "applied",
        "validated",
        "committed",
        "failed_validation",
        "rollback_or_needs_revision",
    }
    state_machine = config.get("proposal_state_machine") if isinstance(config.get("proposal_state_machine"), dict) else {}
    states = {str(state) for state in state_machine.get("states") or []}
    missing = sorted(required_states - states)
    if config.get("schema_version") != CONTRACT_VERSION or config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise ProposalStateBuildError("S13 P1 config identity mismatch")
    if missing:
        raise ProposalStateBuildError(f"S13 P1 config missing states: {', '.join(missing)}")
    if state_machine.get("human_approval_required_before_applying") is not True:
        raise ProposalStateBuildError("human approval must be required before applying")
    if state_machine.get("current_phase_executes_apply") is not False:
        raise ProposalStateBuildError("S13 P1 must not execute apply")
    if state_machine.get("diff_narrator_deferred_to") != "S13 P2" or state_machine.get("apply_execution_deferred_to") != "S13 P3":
        raise ProposalStateBuildError("S13 P1 must defer diff narrator and apply execution")
    boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
    if boundary.get("raw_mutation") is not False or boundary.get("proposal_apply_execution") is not False:
        raise ProposalStateBuildError("S13 P1 boundary must keep raw mutation and proposal apply disabled")


def normalize_self_iteration_proposals(
    self_iteration: dict[str, Any],
    state_machine: dict[str, Any],
    expiry: dict[str, Any],
    as_of: datetime,
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for suggestion in self_iteration.get("self_iteration_suggestions") or []:
        if not isinstance(suggestion, dict):
            continue
        proposal = suggestion.get("proposal") if isinstance(suggestion.get("proposal"), dict) else {}
        if not proposal:
            continue
        target_files = [str(item) for item in proposal.get("target_files") or suggestion.get("target_files") or []]
        forbidden_hits = [file for file in target_files if any(fragment in file for fragment in FORBIDDEN_TARGET_FRAGMENTS)]
        current_state = str(proposal.get("state") or "pending_human_review")
        approval = proposal.get("approval") if isinstance(proposal.get("approval"), dict) else {}
        approval_status = str(approval.get("status") or "not_approved")
        apply_allowed = bool(proposal.get("apply_execution_allowed"))
        raw_allowed = bool(proposal.get("raw_apply_target_allowed"))
        proposals.append(
            {
                "proposal_id": str(proposal.get("proposal_id") or suggestion.get("suggestion_id")),
                "source": "self_iteration_suggestions",
                "source_suggestion_id": suggestion.get("suggestion_id"),
                "target_type": suggestion.get("target_type"),
                "target_files": target_files,
                "current_state": current_state,
                "allowed_next_states": allowed_next_states(current_state, state_machine),
                "approval_status": approval_status,
                "requires_human_approval_before_applying": True,
                "apply_execution_allowed": apply_allowed,
                "raw_apply_target_allowed": raw_allowed,
                "unauthorized_apply_blocked": current_state != "approved_by_human" and apply_allowed is False,
                "expires_at": proposal.get("expires_at"),
                "expiry_bucket": expiry_bucket(str(proposal.get("created_at") or ""), str(proposal.get("expires_at") or ""), as_of, expiry),
                "action_half_life_days": proposal.get("action_half_life_days") or suggestion.get("action_half_life_days"),
                "validation_commands": proposal.get("validation_commands") or [],
                "rollback_plan_zh": proposal.get("rollback_plan_zh") or "",
                "forbidden_target_hits": forbidden_hits,
            }
        )
    return proposals


def collect_decision_debt_links(decision_debt: dict[str, Any]) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for item in decision_debt.get("decision_debt_ledger") or []:
        if not isinstance(item, dict):
            continue
        for proposal_id in item.get("linked_proposal_ids") or []:
            links.append(
                {
                    "proposal_id": str(proposal_id),
                    "decision_debt_id": item.get("decision_debt_id"),
                    "decision_area_zh": item.get("decision_area_zh"),
                    "minimal_next_step": item.get("minimal_next_step"),
                }
            )
    return links


def build_payload(database_dir: Path, dry_run: bool) -> dict[str, Any]:
    config = read_json(database_dir / CONFIG_PATH)
    self_iteration = read_json(database_dir / SELF_ITERATION_PATH)
    decision_debt = read_json(database_dir / DECISION_DEBT_PATH)
    authorization = read_json(database_dir / AUTHORIZATION_PATH)
    validate_config(config)

    as_of = source_as_of(self_iteration, decision_debt, authorization)
    state_machine = config["proposal_state_machine"]
    expiry = config["proposal_expiry"]
    proposals = normalize_self_iteration_proposals(self_iteration, state_machine, expiry, as_of)
    decision_debt_links = collect_decision_debt_links(decision_debt)

    all_have_expiry = bool(proposals) and all(proposal.get("expires_at") for proposal in proposals)
    raw_allowed = any(proposal.get("raw_apply_target_allowed") is not False for proposal in proposals)
    proposal_apply_execution = any(proposal.get("apply_execution_allowed") is not False for proposal in proposals)
    unauthorized_apply_blocked = all(
        proposal.get("current_state") == "approved_by_human" or proposal.get("apply_execution_allowed") is False
        for proposal in proposals
    )
    forbidden_target_hits = [
        {"proposal_id": proposal["proposal_id"], "hits": proposal["forbidden_target_hits"]}
        for proposal in proposals
        if proposal.get("forbidden_target_hits")
    ]
    state_counts = {
        state: sum(1 for proposal in proposals if proposal.get("current_state") == state)
        for state in state_machine.get("states", [])
    }
    expiry_counts: dict[str, int] = {}
    for proposal in proposals:
        bucket = str(proposal.get("expiry_bucket"))
        expiry_counts[bucket] = expiry_counts.get(bucket, 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "contract_version": CONTRACT_VERSION,
        "state_machine_version": CONTRACT_VERSION,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "applies_proposals": False,
        "raw_mutation": False,
        "as_of": isoformat_z(as_of),
        "config_path": str(CONFIG_PATH),
        "output_path": str(OUTPUT_PATH),
        "source_reports": [
            str(SELF_ITERATION_PATH),
            str(DECISION_DEBT_PATH),
            str(AUTHORIZATION_PATH),
        ],
        "state_machine": {
            "states": state_machine["states"],
            "transitions": state_machine["transitions"],
            "failure_path": state_machine["failure_path"],
            "terminal_states": state_machine["terminal_states"],
            "human_approval_required_before_applying": True,
            "current_phase_executes_apply": False,
            "diff_narrator_deferred_to": "S13 P2",
            "apply_execution_deferred_to": "S13 P3",
        },
        "proposal_expiry": {
            "integrated": True,
            "warn_after_days": expiry["warn_after_days"],
            "stale_after_days": expiry["stale_after_days"],
            "archive_after_days": expiry["archive_after_days"],
            "expired_proposals_cannot_enter_applying": True,
        },
        "proposals": proposals,
        "decision_debt_links": decision_debt_links,
        "summary": {
            "proposal_count": len(proposals),
            "decision_debt_link_count": len(decision_debt_links),
            "state_counts": state_counts,
            "expiry_counts": expiry_counts,
            "all_proposals_have_expiry": all_have_expiry,
            "expiry_integrated": True,
            "unauthorized_apply_blocked": unauthorized_apply_blocked,
            "raw_apply_target_allowed": raw_allowed,
            "proposal_apply_execution": proposal_apply_execution,
            "current_phase_executes_apply": False,
            "forbidden_target_hit_count": len(forbidden_target_hits),
            "forbidden_target_hits": forbidden_target_hits,
        },
        "output_contract": {
            "report": str(OUTPUT_PATH),
            "machine_config": str(CONFIG_PATH),
            "next_phase": "S13 P2",
        },
        "phase_boundary": {
            "does_not_apply_proposals": True,
            "does_not_modify_raw": True,
            "does_not_upload_github_main": True,
            "does_not_push_remote": True,
            "does_not_generate_diff_narrator": True,
            "does_not_execute_rollback": True,
            "next_phase": "S13 P2",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Memory Atlas S13 P1 proposal state-machine report.")
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    database_dir = args.database_dir.resolve()
    payload = build_payload(database_dir, dry_run=args.dry_run)
    if not args.dry_run:
        output_file = database_dir / OUTPUT_PATH
        output_file.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if not output_file.exists() or output_file.read_text(encoding="utf-8") != serialized:
            output_file.write_text(serialized, encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
