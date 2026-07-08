#!/usr/bin/env python3
"""Build and inspect the Memory Atlas v1.2 S13 P3 proposal apply contract."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "MA-V12-S13P3"
ACCEPTANCE_ID = "ACC-MA-V12-S13P3"
STATUS = "phase_s13_p3_apply_rollback_completed_pending_s13_review"
CONTRACT_VERSION = "proposal_apply.v1_2_s13_p3"
SCHEMA_VERSION = "openai_database.proposal_apply.v1_2_s13_p3"
EVIDENCE_SCHEMA_VERSION = "openai_database.proposal_apply_evidence.v1_2_s13_p3"

CONFIG_PATH = Path("机器治理/运行门禁/proposal_apply.v1_2_s13_p3.json")
STATE_MACHINE_REPORT_PATH = Path("data/derived/proposals/proposal_state_machine_report.json")
DIFF_NARRATOR_REPORT_PATH = Path("data/derived/proposals/diff_narrator_report.json")
OUTPUT_PATH = Path("data/derived/proposals/proposal_apply_report.json")
EVIDENCE_PATH = Path("机器治理/证据与日志/proposal_apply/proposal_apply_evidence.v1_2_s13_p3.json")

FORBIDDEN_TARGET_FRAGMENTS = (
    "data/public_raw/",
    "data/raw/",
    "data/private_imports/",
    "credentials",
    "cookies",
    "tokens",
)


class ProposalApplyBuildError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ProposalApplyBuildError(f"missing required input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def isoformat_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def source_as_of(*payloads: dict[str, Any]) -> datetime:
    candidates = [parse_time(str(payload.get("as_of") or payload.get("generated_at"))) for payload in payloads]
    valid = [candidate for candidate in candidates if candidate is not None]
    if not valid:
        return datetime(2026, 7, 8, tzinfo=timezone.utc)
    return max(valid)


def git_head(database_dir: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=database_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != CONTRACT_VERSION or config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise ProposalApplyBuildError("S13 P3 config identity mismatch")
    if config.get("status") != STATUS:
        raise ProposalApplyBuildError("S13 P3 config status mismatch")
    contract = config.get("apply_contract") if isinstance(config.get("apply_contract"), dict) else {}
    if contract.get("human_approval_required_before_apply") is not True:
        raise ProposalApplyBuildError("S13 P3 must require human approval before apply")
    if contract.get("validation_after_apply_required") is not True:
        raise ProposalApplyBuildError("S13 P3 must require validation after apply")
    if contract.get("rollback_point_required") is not True:
        raise ProposalApplyBuildError("S13 P3 must require a rollback point")
    if contract.get("raw_archive_is_never_apply_target") is not True:
        raise ProposalApplyBuildError("S13 P3 must forbid raw archive apply targets")
    forbidden = set(str(item) for item in contract.get("forbidden_target_fragments") or [])
    if not set(FORBIDDEN_TARGET_FRAGMENTS).issubset(forbidden):
        raise ProposalApplyBuildError("S13 P3 config does not include all forbidden target fragments")
    boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
    if boundary.get("does_not_modify_raw") is not True or boundary.get("does_not_upload_github_main") is not True:
        raise ProposalApplyBuildError("S13 P3 boundary must forbid raw mutation and GitHub main upload")


def proposal_fixtures(config: dict[str, Any]) -> list[dict[str, Any]]:
    contract = config.get("apply_contract") if isinstance(config.get("apply_contract"), dict) else {}
    fixtures = contract.get("proposal_fixtures") if isinstance(contract.get("proposal_fixtures"), list) else []
    return [fixture for fixture in fixtures if isinstance(fixture, dict)]


def real_proposals(state_report: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for proposal in state_report.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        proposals.append(
            {
                "approval": {
                    "approved_at": None,
                    "approved_by": None,
                    "status": proposal.get("approval_status") or "not_approved",
                },
                "current_state": proposal.get("current_state"),
                "human_reason_zh": "真实 pending proposal 必须由人类授权后才允许 apply。",
                "proposal_id": proposal.get("proposal_id"),
                "rollback_plan_zh": proposal.get("rollback_plan_zh") or "使用 proposal rollback 或 git revert；raw 文件不回滚。",
                "source": "proposal_state_machine_report",
                "target_files": proposal.get("target_files") or [],
                "target_type": proposal.get("target_type"),
                "validation_commands": proposal.get("validation_commands") or [],
            }
        )
    return proposals


def all_known_proposals(config: dict[str, Any], state_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for proposal in proposal_fixtures(config) + real_proposals(state_report):
        proposal_id = proposal.get("proposal_id")
        if proposal_id:
            indexed[str(proposal_id)] = proposal
    return indexed


def forbidden_target_hits(target_files: list[str]) -> list[str]:
    return [target for target in target_files if any(fragment in target for fragment in FORBIDDEN_TARGET_FRAGMENTS)]


def has_human_approval(proposal: dict[str, Any]) -> bool:
    approval = proposal.get("approval") if isinstance(proposal.get("approval"), dict) else {}
    return (
        proposal.get("current_state") == "approved_by_human"
        and approval.get("status") == "approved_by_human"
        and bool(approval.get("approved_by"))
        and bool(approval.get("approved_at"))
    )


def base_attempt(
    database_dir: Path,
    proposal: dict[str, Any],
    dry_run: bool,
    as_of: datetime,
    simulate_validation_failure: bool,
) -> dict[str, Any]:
    target_files = [str(item) for item in proposal.get("target_files") or []]
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "PASS",
        "contract_version": CONTRACT_VERSION,
        "proposal_id": proposal.get("proposal_id"),
        "target_type": proposal.get("target_type"),
        "target_files": target_files,
        "dry_run": dry_run,
        "writes_files": False,
        "applies_proposal": False,
        "would_apply": False,
        "raw_mutation": False,
        "as_of": isoformat_z(as_of),
        "authorization": proposal.get("approval") or {},
        "human_approval_required_before_apply": True,
        "validation_after_apply": False,
        "validation_commands": [str(item) for item in proposal.get("validation_commands") or []],
        "rollback_plan_zh": proposal.get("rollback_plan_zh") or "使用 proposal rollback 或 git revert；raw 文件不回滚。",
        "rollback_point": {
            "type": "git_head",
            "value": git_head(database_dir),
            "required": True,
        },
        "rollback_point_created": False,
        "rollback_available": False,
        "rollback_or_needs_revision": False,
        "forbidden_target_hits": forbidden_target_hits(target_files),
        "failure_explanation_zh": "",
        "simulate_validation_failure": simulate_validation_failure,
    }


def fail_closed(attempt: dict[str, Any], explanation_zh: str, rollback_available: bool = False) -> dict[str, Any]:
    attempt["status"] = "FAIL_CLOSED"
    attempt["failure_explanation_zh"] = explanation_zh
    attempt["writes_files"] = False
    attempt["applies_proposal"] = False
    attempt["would_apply"] = False
    attempt["rollback_available"] = rollback_available
    attempt["rollback_or_needs_revision"] = rollback_available
    return attempt


def restore_targets(database_dir: Path, snapshots: dict[Path, str | None]) -> None:
    for path, previous in snapshots.items():
        absolute = database_dir / path
        if previous is None:
            if absolute.exists():
                absolute.unlink()
        else:
            absolute.parent.mkdir(parents=True, exist_ok=True)
            absolute.write_text(previous, encoding="utf-8")


def write_targets(database_dir: Path, proposal: dict[str, Any]) -> dict[Path, str | None]:
    payload = proposal.get("apply_payload") if isinstance(proposal.get("apply_payload"), dict) else {}
    snapshots: dict[Path, str | None] = {}
    for target in [Path(str(item)) for item in proposal.get("target_files") or []]:
        absolute = database_dir / target
        snapshots[target] = absolute.read_text(encoding="utf-8") if absolute.exists() else None
        absolute.parent.mkdir(parents=True, exist_ok=True)
        absolute.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return snapshots


def run_validation_commands(database_dir: Path, commands: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for command in commands:
        result = subprocess.run(
            shlex.split(command),
            cwd=database_dir,
            text=True,
            capture_output=True,
            check=False,
        )
        results.append(
            {
                "command": command,
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-1200:],
                "stderr_tail": result.stderr[-1200:],
            }
        )
    return results


def build_apply_attempt(
    database_dir: Path,
    proposal_id: str,
    dry_run: bool,
    simulate_validation_failure: bool = False,
) -> dict[str, Any]:
    config = read_json(database_dir / CONFIG_PATH)
    state_report = read_json(database_dir / STATE_MACHINE_REPORT_PATH)
    diff_report = read_json(database_dir / DIFF_NARRATOR_REPORT_PATH)
    validate_config(config)

    as_of = source_as_of(state_report, diff_report)
    proposals = all_known_proposals(config, state_report)
    proposal = proposals.get(proposal_id)
    if not proposal:
        return fail_closed(
            {
                "schema_version": SCHEMA_VERSION,
                "task_id": TASK_ID,
                "acceptance_id": ACCEPTANCE_ID,
                "status": "FAIL_CLOSED",
                "contract_version": CONTRACT_VERSION,
                "proposal_id": proposal_id,
                "dry_run": dry_run,
                "writes_files": False,
                "applies_proposal": False,
                "raw_mutation": False,
                "as_of": isoformat_z(as_of),
            },
            f"找不到 proposal：{proposal_id}。",
        )

    attempt = base_attempt(database_dir, proposal, dry_run, as_of, simulate_validation_failure)
    if attempt["forbidden_target_hits"]:
        return fail_closed(attempt, "proposal 命中 raw/private/credential 禁止 apply target。")
    if not has_human_approval(proposal):
        return fail_closed(attempt, "proposal 尚未获得人类授权，必须 fail-closed。")
    if simulate_validation_failure:
        return fail_closed(attempt, "模拟 validation 失败，已生成 rollback_or_needs_revision 路径。", rollback_available=True)

    attempt["would_apply"] = True
    attempt["validation_after_apply"] = True
    attempt["rollback_point_created"] = bool(attempt["rollback_point"]["value"] and attempt["rollback_point"]["value"] != "unknown")
    attempt["rollback_available"] = True

    if dry_run:
        return attempt

    snapshots = write_targets(database_dir, proposal)
    attempt["writes_files"] = True
    attempt["applies_proposal"] = True
    validation_results = run_validation_commands(database_dir, [str(item) for item in proposal.get("validation_commands") or []])
    attempt["validation_results"] = validation_results
    if any(result["returncode"] != 0 for result in validation_results):
        restore_targets(database_dir, snapshots)
        attempt["status"] = "FAIL_CLOSED"
        attempt["failure_explanation_zh"] = "apply 后 validation 失败，已按 rollback snapshot 还原目标文件。"
        attempt["writes_files"] = False
        attempt["applies_proposal"] = False
        attempt["rollback_or_needs_revision"] = True
    return attempt


def build_report_payloads(database_dir: Path, dry_run: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(database_dir / CONFIG_PATH)
    state_report = read_json(database_dir / STATE_MACHINE_REPORT_PATH)
    diff_report = read_json(database_dir / DIFF_NARRATOR_REPORT_PATH)
    validate_config(config)

    as_of = source_as_of(state_report, diff_report)
    unauthorized = build_apply_attempt(database_dir, "sample_unauthorized", dry_run=True)
    authorized = build_apply_attempt(database_dir, "sample", dry_run=True)
    failure = build_apply_attempt(database_dir, "sample", dry_run=True, simulate_validation_failure=True)
    real_pending = [proposal for proposal in real_proposals(state_report) if proposal.get("current_state") != "approved_by_human"]
    attempts = [unauthorized, authorized, failure]

    output = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "contract_version": CONTRACT_VERSION,
        "dry_run": dry_run,
        "writes_files": not dry_run,
        "applies_real_pending_proposals": False,
        "raw_mutation": False,
        "as_of": isoformat_z(as_of),
        "config_path": str(CONFIG_PATH),
        "source_reports": [str(STATE_MACHINE_REPORT_PATH), str(DIFF_NARRATOR_REPORT_PATH)],
        "output_path": str(OUTPUT_PATH),
        "evidence_path": str(EVIDENCE_PATH),
        "sample_outcomes": {
            "unauthorized_attempt": unauthorized,
            "authorized_apply_dry_run": authorized,
            "validation_failure_dry_run": failure,
        },
        "summary": {
            "unauthorized_apply_blocked": unauthorized.get("status") == "FAIL_CLOSED" and unauthorized.get("applies_proposal") is False,
            "authorized_apply_available": authorized.get("status") == "PASS" and authorized.get("would_apply") is True,
            "validation_after_apply": authorized.get("validation_after_apply") is True,
            "rollback_available": authorized.get("rollback_available") is True and failure.get("rollback_available") is True,
            "raw_mutation": False,
            "real_pending_proposal_count": len(real_pending),
            "real_pending_proposals_applied": 0,
            "machine_apply_attempt_count": len(attempts),
        },
        "output_contract": {
            "report": str(OUTPUT_PATH),
            "evidence": str(EVIDENCE_PATH),
            "machine_config": str(CONFIG_PATH),
            "next_phase": "S13 Review",
        },
        "phase_boundary": {
            "does_not_apply_unapproved_proposals": True,
            "does_not_apply_real_pending_proposals_without_human_approval": True,
            "does_not_modify_raw": True,
            "does_not_upload_github_main": True,
            "does_not_push_remote": True,
            "next_phase": "S13 Review",
        },
    }
    evidence = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "contract_version": CONTRACT_VERSION,
        "as_of": isoformat_z(as_of),
        "source_reports": [str(STATE_MACHINE_REPORT_PATH), str(DIFF_NARRATOR_REPORT_PATH)],
        "machine_apply_attempts": attempts,
        "summary": {
            "machine_apply_attempt_count": len(attempts),
            "unauthorized_apply_blocked": output["summary"]["unauthorized_apply_blocked"],
            "authorized_apply_available": output["summary"]["authorized_apply_available"],
            "validation_after_apply": output["summary"]["validation_after_apply"],
            "rollback_available": output["summary"]["rollback_available"],
            "raw_mutation": False,
        },
    }
    return output, evidence


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != serialized:
        path.write_text(serialized, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or inspect Memory Atlas S13 P3 proposal apply contract.")
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--proposal")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--simulate-validation-failure", action="store_true")
    args = parser.parse_args(argv)

    database_dir = args.database_dir.resolve()
    if args.proposal:
        attempt = build_apply_attempt(
            database_dir,
            args.proposal,
            dry_run=args.dry_run,
            simulate_validation_failure=args.simulate_validation_failure,
        )
        print(json.dumps(attempt, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if attempt.get("status") == "PASS" else 2

    output, evidence = build_report_payloads(database_dir, dry_run=args.dry_run)
    if not args.dry_run:
        write_json_if_changed(database_dir / OUTPUT_PATH, output)
        write_json_if_changed(database_dir / EVIDENCE_PATH, evidence)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
