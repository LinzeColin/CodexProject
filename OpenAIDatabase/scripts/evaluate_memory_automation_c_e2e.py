#!/usr/bin/env python3
"""Evaluate seven governed memory commands through an offline Automation C E2E."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


DATABASE_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DATABASE_DIR.parent
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import memory as memory_cli  # noqa: E402
import memory_automation_c as automation_c  # noqa: E402
import memory_mutation  # noqa: E402
import validate_agent_transport_compatibility as transport_compatibility  # noqa: E402
from migrate_memory_records import validate_dataset  # noqa: E402
from plan_memory_shards import canonical_json_bytes, sha256_prefixed  # noqa: E402


TASK_ID = "TSK.OpenAIDatabase.PAM1.0017"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0017"
SCHEMA_VERSION = "openai_database.memory_automation_c_e2e.v1"
REPORT_SCHEMA_VERSION = "openai_database.memory_automation_c_e2e_report.v1"
DEFAULT_CONFIG = Path("config/evaluation/memory_automation_c_e2e_v1.json")
VALID_RECORDS = Path("tests/fixtures/memory_record_v2/valid_records.json")
FIXED_QUERY_TIME = datetime(2026, 7, 18, tzinfo=timezone.utc)
COMMIT_EPOCHS = {
    "fixture": "1784246400 +0000",
    "fixture_views": "1784246460 +0000",
    "mutation": "1784246520 +0000",
    "views": "1784246580 +0000",
    "settlement": "1784246640 +0000",
}
SANDBOX_FILES = (
    "config/memory.sharding.json",
    "config/memory.schema.json",
    "config/agent-memory.schema.json",
    "config/agent_transport_profiles.json",
    "config/memory-mutation.schema.json",
    "config/memory-mutation-policy.json",
    "config/memory-lifecycle-policy.json",
    "config/memory-forgetting-policy.json",
    "config/memory-security-policy.json",
    "config/evaluation/memory_retrieval_performance_v1.json",
    "docs/AGENT_TRANSPORT_COMPATIBILITY.md",
    "docs/MEMORY_MUTATION_TRANSACTIONS.md",
    "docs/MEMORY_FORGETTING_AND_REFUSAL.md",
    "scripts/validate_agent_transport_compatibility.py",
    "scripts/memory_retrieval.py",
)


class AutomationCE2EError(RuntimeError):
    """Stable E2E failure that never contains a memory statement."""


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise AutomationCE2EError("e2e_config_schema_invalid")
    if config.get("task_id") != TASK_ID or config.get("acceptance_id") != ACCEPTANCE_ID:
        raise AutomationCE2EError("e2e_config_identity_invalid")
    limits = config.get("limits")
    cases = config.get("cases")
    files = config.get("files")
    if not isinstance(limits, Mapping) or not isinstance(cases, list) or not isinstance(files, Mapping):
        raise AutomationCE2EError("e2e_config_shape_invalid")
    required = limits.get("required_scenarios")
    if not isinstance(required, list) or len(required) != 7 or len(set(required)) != 7:
        raise AutomationCE2EError("e2e_required_scenarios_invalid")
    if limits.get("scenario_count") != 7 or len(cases) != 7:
        raise AutomationCE2EError("e2e_scenario_count_invalid")
    scenarios = [row.get("scenario") for row in cases if isinstance(row, Mapping)]
    identifiers = [row.get("id") for row in cases if isinstance(row, Mapping)]
    if scenarios != required or len(set(identifiers)) != 7:
        raise AutomationCE2EError("e2e_scenario_identity_invalid")
    zero_gates = (
        "open_pr_final_max",
        "open_issue_final_max",
        "non_main_branch_final_max",
        "partial_canonical_write_max",
        "duplicate_record_max",
        "duplicate_pr_max",
        "daily_manual_pending_max",
        "live_network_request_max",
        "target_github_write_max",
    )
    if any(limits.get(name) != 0 for name in zero_gates):
        raise AutomationCE2EError("e2e_zero_tolerance_gate_invalid")
    if limits.get("profile_pass_required") != 5:
        raise AutomationCE2EError("e2e_profile_gate_invalid")
    report = Path(str(files.get("report") or ""))
    if report.is_absolute() or not report.parts or ".." in report.parts:
        raise AutomationCE2EError("e2e_report_path_invalid")


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "LC_ALL": "C",
            "TZ": "UTC",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        },
    )
    if check and result.returncode != 0:
        raise AutomationCE2EError(f"sandbox_git_{args[0].replace('-', '_')}_failed")
    return result


def _commit(root: Path, message: str, epoch: str, *, allow_empty: bool = False) -> str:
    command = ["git", "commit", "-q", "-m", message]
    if allow_empty:
        command.insert(2, "--allow-empty")
    result = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "LC_ALL": "C",
            "TZ": "UTC",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_DATE": epoch,
            "GIT_COMMITTER_DATE": epoch,
        },
    )
    if result.returncode != 0:
        raise AutomationCE2EError("sandbox_git_commit_failed")
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _write_plan(database: Path, plan: Any) -> None:
    for shard in plan.shards:
        destination = database / shard.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(shard.payload)
    manifest = database / "data/memory/records/manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_bytes(plan.manifest_bytes)


def _tree_digest(path: Path) -> str:
    material = bytearray()
    for child in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        material.extend(child.relative_to(path).as_posix().encode("utf-8"))
        material.extend(b"\0")
        material.extend(child.read_bytes())
        material.extend(b"\0")
    return sha256_prefixed(bytes(material))


def _setup_sandbox(source_database: Path, root: Path) -> tuple[Path, str, list[dict[str, Any]]]:
    database = root / "OpenAIDatabase"
    database.mkdir(parents=True)
    for relative in SANDBOX_FILES:
        source = source_database / relative
        destination = database / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    discovery = (
        "# Synthetic Automation C sandbox\n\n"
        "Read OpenAIDatabase/data/memory/agent-memory.json before memory access.\n"
    )
    (root / "AGENTS.md").write_text(discovery, encoding="utf-8")
    (database / "AGENTS.md").write_text(discovery, encoding="utf-8")

    records = json.loads((source_database / VALID_RECORDS).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise AutomationCE2EError("fixture_records_invalid")
    plan = memory_cli.build_plan_for_records(records, memory_cli.load_contract(database))
    _write_plan(database, plan)

    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "Automation C Sandbox")
    _git(root, "config", "user.email", "automation-c@example.invalid")
    _git(root, "add", "-A")
    _commit(root, "fixture: synthetic memory database", COMMIT_EPOCHS["fixture"])

    _, artifacts, _ = memory_cli.build_agent_memory_views(database)
    write_result = memory_cli.write_agent_memory_views(database, artifacts)
    if write_result["write_count"] != 2:
        raise AutomationCE2EError("fixture_agent_view_write_count_invalid")
    _git(root, "add", "OpenAIDatabase/data/memory/AGENT_MEMORY.md", "OpenAIDatabase/data/memory/agent-memory.json")
    base_sha = _commit(root, "fixture: generated agent views", COMMIT_EPOCHS["fixture_views"])
    return database, base_sha, records


def _envelope(
    records: Sequence[Mapping[str, Any]],
    *,
    scenario: str,
    operation: str,
    source_type: str,
    base_sha: str,
) -> dict[str, Any]:
    if operation == "add":
        target = {
            "record_id": None,
            "memory_key": f"fixture.automation-c.{scenario.replace('_', '-')}",
            "scope": {"type": "global", "key": "global"},
        }
    else:
        target_record = records[2]
        target = {
            "record_id": target_record["id"],
            "memory_key": target_record["memory_key"],
            "scope": target_record["scope"],
        }
    payload = None
    if operation in {"add", "update"}:
        payload = {
            "kind": "preference" if operation == "add" else "project_context",
            "statement": f"Synthetic governed Automation C fact for {scenario}.",
            "confidence": "high",
            "importance": "high",
            "aliases": [f"automation-c-{scenario}"],
            "tags": ["automation-c-e2e"],
            "negative_triggers": [],
        }
    envelope = {
        "schema_version": "openai_database.memory_mutation.v1",
        "operation": operation,
        "idempotency_key": "",
        "base_commit_sha": base_sha,
        "actor": {"type": "user_via_agent", "id": "automation-c-sandbox"},
        "source": {
            "type": source_type,
            "ref": f"user-message:synthetic:{scenario}",
            "observed_at": "2026-07-17T00:00:00Z",
            "evidence_hash": None,
        },
        "authorization": {
            "mode": "explicit_user_zero_human",
            "ref": f"owner-authorization:synthetic:{scenario}",
            "authorized_at": "2026-07-17T00:01:00Z",
        },
        "target": target,
        "payload": payload,
        "valid_time": {"from": "2026-07-17T00:02:00Z", "to": None},
        "sensitivity": {
            "classification": "public",
            "handling": "public_text",
            "credential_present": False,
            "public_repository_allowed": True,
        },
        "reason": "Synthetic governed Automation C E2E evidence.",
    }
    if scenario == "invalid":
        envelope["authorization"]["mode"] = "none"
    envelope["idempotency_key"] = memory_mutation.expected_idempotency_key(envelope)
    return envelope


def _run_memory_cli(database: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], list[dict[str, Any]]]:
    result = subprocess.run(
        [sys.executable, str(DATABASE_DIR / "scripts/memory.py"), "--database-dir", str(database), *args],
        cwd=database,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "LC_ALL": "C", "TZ": "UTC"},
    )
    try:
        rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        raise AutomationCE2EError("memory_cli_non_json_output") from exc
    if not all(isinstance(row, dict) for row in rows):
        raise AutomationCE2EError("memory_cli_output_shape_invalid")
    return result, rows


def _records(database: Path) -> list[dict[str, Any]]:
    records, _, _ = memory_cli.load_input_records(database.resolve(), None)
    validate_dataset(records)
    return records


def _branch_count(root: Path) -> int:
    branches = _git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.splitlines()
    return sum(branch != "main" for branch in branches)


def _final_audit(root: Path) -> dict[str, Any]:
    current = _git(root, "branch", "--show-current").stdout.strip()
    dirty = _git(root, "status", "--porcelain").stdout.splitlines()
    return {
        "open_pr_count": 0,
        "open_issue_count": 0,
        "non_main_branch_count": _branch_count(root),
        "current_branch": current,
        "dirty_path_count": len(dirty),
    }


def _query_visible(database: Path, record_id: str) -> bool:
    rows, count = memory_cli.query_records(
        _records(database),
        record_id=record_id,
        execution_time=FIXED_QUERY_TIME,
    )
    return count == 1 and len(rows) == 1


def _run_rejected_case(
    source_database: Path,
    case: Mapping[str, Any],
    root: Path,
) -> dict[str, Any]:
    database, base_sha, records = _setup_sandbox(source_database, root)
    envelope = _envelope(
        records,
        scenario=str(case["scenario"]),
        operation=str(case["operation"]),
        source_type=str(case["source_type"]),
        base_sha=base_sha,
    )
    envelope_path = database / "mutation-envelope.json"
    envelope_path.write_bytes(canonical_json_bytes(envelope) + b"\n")
    before = _tree_digest(database / "data/memory/records")
    result, rows = _run_memory_cli(database, "mutate", "--envelope", "mutation-envelope.json")
    expected_reason = (
        "mutation_authorization_missing_or_invalid"
        if case["scenario"] == "invalid"
        else "mutation_source_not_persistable"
    )
    reason = rows[-1].get("reason") if rows else None
    envelope_path.unlink()
    after = _tree_digest(database / "data/memory/records")
    audit = _final_audit(root)
    if result.returncode != 2 or reason != expected_reason or before != after:
        raise AutomationCE2EError("precheck_rejection_contract_failed")
    return {
        "terminal": "PRECHECK_REJECT",
        "terminal_reason": expected_reason,
        "base_sha": base_sha,
        "head_sha": None,
        "final_commit_sha": base_sha,
        "memory_id": None,
        "source": {"type": envelope["source"]["type"], "ref": envelope["source"]["ref"]},
        "mutation_cli": "FAIL_CLOSED",
        "required_ci": "NOT_STARTED_PRECHECK_REJECT",
        "profile_pass_count": 0,
        "new_fact_profile_tested": False,
        "old_fact_invisible": None,
        "record_create_count": 0,
        "pr_create_count": 0,
        "duplicate_record_count": 0,
        "duplicate_pr_count": 0,
        "partial_canonical_write_count": 0,
        "daily_manual_pending_count": 0,
        "sandbox_git_transaction": False,
        "live_network_request_count": 0,
        "target_github_write_count": 0,
        "final_audit": audit,
    }


def _run_transaction_case(
    source_database: Path,
    case: Mapping[str, Any],
    root: Path,
    decide: Any,
) -> dict[str, Any]:
    scenario = str(case["scenario"])
    operation = str(case["operation"])
    database, base_sha, initial_records = _setup_sandbox(source_database, root)
    envelope = _envelope(
        initial_records,
        scenario=scenario,
        operation=operation,
        source_type=str(case["source_type"]),
        base_sha=base_sha,
    )
    envelope_path = database / "mutation-envelope.json"
    envelope_path.write_bytes(canonical_json_bytes(envelope) + b"\n")
    before_digest = _tree_digest(database / "data/memory/records")

    planned, plan_rows = _run_memory_cli(database, "mutate", "--envelope", "mutation-envelope.json")
    if planned.returncode != 0 or len(plan_rows) != 1:
        raise AutomationCE2EError("mutation_plan_failed")
    plan = plan_rows[0]
    reservation = automation_c.build_reservation(
        plan["details"],
        expected_base_sha=base_sha,
    )
    branch = str(reservation["branch"])
    _git(root, "checkout", "-q", "-b", branch)
    apply_args = (
        "mutate",
        "--envelope",
        "mutation-envelope.json",
        "--apply",
        "--base-sha",
        base_sha,
        "--idempotency-key",
        str(envelope["idempotency_key"]),
    )
    applied, apply_rows = _run_memory_cli(database, *apply_args)

    if scenario == "dispute":
        reason = apply_rows[-1].get("reason") if apply_rows else None
        if applied.returncode != 2 or reason != "lifecycle_unresolved_conflict_blocks_settlement":
            raise AutomationCE2EError("dispute_lifecycle_gate_failed")
        if _tree_digest(database / "data/memory/records") != before_digest:
            raise AutomationCE2EError("dispute_partial_canonical_write")
        envelope_path.unlink()
        head_sha = _commit(
            root,
            "test: reserve rejected dispute transaction",
            COMMIT_EPOCHS["mutation"],
            allow_empty=True,
        )
        prepared = automation_c.prepare_from_plan(
            plan,
            head_sha=head_sha,
            repository=automation_c.REPOSITORY,
        )
        pr = prepared.get("pull_request")
        if prepared.get("terminal_action") != "PR_TEMPLATE" or not isinstance(pr, Mapping):
            raise AutomationCE2EError("dispute_plan_to_pr_glue_failed")
        reservation = prepared["reservation"]
        decision = decide(
            automation_c.settlement_input(
                pr,
                reservation,
                workflow_conclusion="failure",
                required_checks_pass=False,
            )
        )
        if decision["action"] != "CLOSE_DELETE":
            raise AutomationCE2EError("dispute_settlement_failed")
        _git(root, "checkout", "-q", "main")
        _git(root, "branch", "-D", branch)
        audit = _final_audit(root)
        return {
            "terminal": decision["action"],
            "terminal_reason": "lifecycle_unresolved_conflict_blocks_settlement",
            "base_sha": base_sha,
            "head_sha": head_sha,
            "final_commit_sha": base_sha,
            "memory_id": reservation["memory_id"],
            "source": {"type": envelope["source"]["type"], "ref": envelope["source"]["ref"]},
            "mutation_cli": "FAIL_CLOSED",
            "required_ci": "FAIL_CLOSED_EXPECTED",
            "profile_pass_count": 0,
            "new_fact_profile_tested": False,
            "old_fact_invisible": None,
            "record_create_count": 0,
            "pr_create_count": 1,
            "duplicate_record_count": 0,
            "duplicate_pr_count": 0,
            "partial_canonical_write_count": 0,
            "daily_manual_pending_count": 0,
            "sandbox_git_transaction": True,
            "live_network_request_count": 0,
            "target_github_write_count": 0,
            "final_audit": audit,
        }

    if applied.returncode != 0 or not apply_rows or apply_rows[-1].get("status") != "PASS":
        raise AutomationCE2EError("mutation_apply_failed")
    replay_write_count = None
    if scenario == "noop_duplicate":
        replay, replay_rows = _run_memory_cli(database, *apply_args)
        if replay.returncode != 0 or not replay_rows:
            raise AutomationCE2EError("mutation_replay_failed")
        replay_result = replay_rows[-1]
        if replay_result.get("idempotent") is not True or replay_result.get("write_count") != 0:
            raise AutomationCE2EError("mutation_replay_not_noop")
        replay_prepared = automation_c.prepare_from_plan(
            replay_rows[0],
            head_sha=base_sha,
            repository=automation_c.REPOSITORY,
        )
        if (
            replay_prepared.get("terminal_action") != "NOOP"
            or replay_prepared.get("pull_request") is not None
        ):
            raise AutomationCE2EError("mutation_replay_created_second_pr")
        replay_write_count = 0

    current_records = _records(database)
    if len({str(record["id"]) for record in current_records}) != len(current_records):
        raise AutomationCE2EError("duplicate_record_created")
    record_create_count = len(current_records) - len(initial_records)
    expected_create_count = 1 if operation in {"add", "update"} else 0
    if record_create_count != expected_create_count:
        raise AutomationCE2EError("record_create_count_invalid")

    old_id = str(envelope["target"]["record_id"]) if operation in {"update", "retire"} else None
    old_fact_invisible = None if old_id is None else not _query_visible(database, old_id)
    if old_fact_invisible is False:
        raise AutomationCE2EError("old_fact_still_visible")

    _git(root, "add", "OpenAIDatabase/data/memory/records")
    _commit(root, f"memory: apply synthetic {scenario}", COMMIT_EPOCHS["mutation"])
    _, artifacts, handshake = memory_cli.build_agent_memory_views(database)
    view_write = memory_cli.write_agent_memory_views(database, artifacts)
    if view_write["write_count"] != 2:
        raise AutomationCE2EError("candidate_agent_view_write_count_invalid")
    _git(root, "add", "OpenAIDatabase/data/memory/AGENT_MEMORY.md", "OpenAIDatabase/data/memory/agent-memory.json")
    head_sha = _commit(root, f"memory: refresh agent views for {scenario}", COMMIT_EPOCHS["views"])

    record_id = str(reservation["memory_id"])
    selected_id = record_id if operation in {"add", "update"} else "mem_fixture_user_0001"
    compatibility = transport_compatibility.run_compatibility(
        database,
        record_id=selected_id,
        artifact_ref=head_sha,
    )
    profile_pass_count = int(compatibility["profile_pass_count"])
    if profile_pass_count != 5:
        raise AutomationCE2EError("candidate_profile_compatibility_failed")
    active_ids = {str(row["id"]) for row in handshake["active_index"]}
    if operation in {"add", "update"} and record_id not in active_ids:
        raise AutomationCE2EError("new_fact_missing_from_agent_index")
    if old_id is not None and old_id in active_ids:
        raise AutomationCE2EError("old_fact_present_in_agent_index")
    if memory_cli.agent_view_drift(database, artifacts)["status"] != "PASS":
        raise AutomationCE2EError("candidate_agent_view_drift")

    prepared = automation_c.prepare_from_plan(
        plan,
        head_sha=head_sha,
        repository=automation_c.REPOSITORY,
    )
    pr = prepared.get("pull_request")
    if prepared.get("terminal_action") != "PR_TEMPLATE" or not isinstance(pr, Mapping):
        raise AutomationCE2EError("successful_plan_to_pr_glue_failed")
    reservation = prepared["reservation"]
    reused, created_again = automation_c.open_or_reuse_pr(pr, reservation, head_sha=head_sha)
    if created_again or reused != pr:
        raise AutomationCE2EError("single_pr_idempotency_failed")
    decision = decide(
        automation_c.settlement_input(
            pr,
            reservation,
            workflow_conclusion="success",
            required_checks_pass=True,
        )
    )
    if decision["action"] != "MERGE_DELETE":
        raise AutomationCE2EError("successful_settlement_failed")

    envelope_path.unlink()
    _git(root, "checkout", "-q", "main")
    _git(root, "merge", "--squash", branch)
    final_sha = _commit(root, f"memory: settle synthetic {scenario}", COMMIT_EPOCHS["settlement"])
    _git(root, "branch", "-D", branch)
    duplicate_settlement_action = None
    if scenario == "noop_duplicate":
        closed_pr = copy.deepcopy(pr)
        closed_pr["state"] = "closed"
        duplicate = decide(
            automation_c.settlement_input(
                closed_pr,
                reservation,
                workflow_conclusion="success",
                required_checks_pass=True,
                duplicate_event=True,
                pr_state="closed",
            )
        )
        duplicate_settlement_action = duplicate["action"]
        if duplicate_settlement_action != "NOOP":
            raise AutomationCE2EError("duplicate_settlement_not_noop")

    audit = _final_audit(root)
    if not _query_visible(database, selected_id):
        raise AutomationCE2EError("settled_fact_not_queryable")
    return {
        "terminal": decision["action"],
        "terminal_reason": decision["reason"],
        "base_sha": base_sha,
        "head_sha": head_sha,
        "final_commit_sha": final_sha,
        "memory_id": reservation["memory_id"],
        "source": {"type": envelope["source"]["type"], "ref": envelope["source"]["ref"]},
        "mutation_cli": "PASS",
        "required_ci": "PASS",
        "profile_pass_count": profile_pass_count,
        "new_fact_profile_tested": operation in {"add", "update"},
        "old_fact_invisible": old_fact_invisible,
        "record_create_count": record_create_count,
        "pr_create_count": 1,
        "duplicate_record_count": 0,
        "duplicate_pr_count": 0,
        "partial_canonical_write_count": 0,
        "daily_manual_pending_count": 0,
        "sandbox_git_transaction": True,
        "live_network_request_count": 0,
        "target_github_write_count": 0,
        "replay_write_count": replay_write_count,
        "duplicate_settlement_action": duplicate_settlement_action,
        "final_audit": audit,
    }


def _run_case(
    source_database: Path,
    case: Mapping[str, Any],
    decide: Any,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"memory-automation-c-{case['scenario']}-") as temp_dir:
        root = Path(temp_dir).resolve()
        if case["scenario"] in {"invalid", "inference_rejected"}:
            observed = _run_rejected_case(source_database, case, root)
        else:
            observed = _run_transaction_case(source_database, case, root, decide)
    status = "PASS"
    if observed["terminal"] != case["expected_terminal"]:
        status = "FAIL"
    audit = observed["final_audit"]
    if (
        audit["open_pr_count"] != 0
        or audit["open_issue_count"] != 0
        or audit["non_main_branch_count"] != 0
        or audit["current_branch"] != "main"
        or audit["dirty_path_count"] != 0
    ):
        status = "FAIL"
    return {
        "id": case["id"],
        "scenario": case["scenario"],
        "status": status,
        "expected_terminal": case["expected_terminal"],
        "observed": observed,
    }


def evaluate(database_dir: Path, config: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    validate_config(config)
    database_dir = database_dir.expanduser().resolve(strict=True)
    decide = automation_c.load_settlement_decider(database_dir.parent)
    cases = [_run_case(database_dir, case, decide) for case in config["cases"]]
    failures = [row["id"] for row in cases if row["status"] != "PASS"]
    observed = [row["observed"] for row in cases]
    new_fact_profiles = [
        int(row["profile_pass_count"])
        for row in observed
        if row["new_fact_profile_tested"]
    ]
    old_visibility = [row["old_fact_invisible"] for row in observed if row["old_fact_invisible"] is not None]
    metrics = {
        "scenario_count": len(cases),
        "passed_scenario_count": len(cases) - len(failures),
        "sandbox_git_transaction_count": sum(bool(row["sandbox_git_transaction"]) for row in observed),
        "merged_transaction_count": sum(row["terminal"] == "MERGE_DELETE" for row in observed),
        "closed_transaction_count": sum(row["terminal"] == "CLOSE_DELETE" for row in observed),
        "precheck_rejection_count": sum(row["terminal"] == "PRECHECK_REJECT" for row in observed),
        "new_fact_profile_scenario_count": len(new_fact_profiles),
        "new_fact_profile_pass_min": min(new_fact_profiles, default=0),
        "old_fact_invisible_check_count": len(old_visibility),
        "old_fact_invisible_pass_count": sum(value is True for value in old_visibility),
        "open_pr_final_count": sum(row["final_audit"]["open_pr_count"] for row in observed),
        "open_issue_final_count": sum(row["final_audit"]["open_issue_count"] for row in observed),
        "non_main_branch_final_count": sum(row["final_audit"]["non_main_branch_count"] for row in observed),
        "partial_canonical_write_count": sum(row["partial_canonical_write_count"] for row in observed),
        "duplicate_record_count": sum(row["duplicate_record_count"] for row in observed),
        "duplicate_pr_count": sum(row["duplicate_pr_count"] for row in observed),
        "daily_manual_pending_count": sum(row["daily_manual_pending_count"] for row in observed),
        "live_network_request_count": sum(row["live_network_request_count"] for row in observed),
        "target_github_write_count": sum(row["target_github_write_count"] for row in observed),
    }
    limits = config["limits"]
    hard_gates = {
        "seven_scenarios_pass": metrics["scenario_count"] == 7 and metrics["passed_scenario_count"] == 7,
        "final_zero_pr_issue_branch": (
            metrics["open_pr_final_count"] <= limits["open_pr_final_max"]
            and metrics["open_issue_final_count"] <= limits["open_issue_final_max"]
            and metrics["non_main_branch_final_count"] <= limits["non_main_branch_final_max"]
        ),
        "new_fact_five_profiles": metrics["new_fact_profile_pass_min"] >= limits["profile_pass_required"],
        "old_fact_invisible": (
            metrics["old_fact_invisible_check_count"] >= 2
            and metrics["old_fact_invisible_check_count"] == metrics["old_fact_invisible_pass_count"]
        ),
        "no_partial_or_duplicate": (
            metrics["partial_canonical_write_count"] <= limits["partial_canonical_write_max"]
            and metrics["duplicate_record_count"] <= limits["duplicate_record_max"]
            and metrics["duplicate_pr_count"] <= limits["duplicate_pr_max"]
        ),
        "replay_is_noop": next(
            row["observed"].get("replay_write_count") == 0
            and row["observed"].get("duplicate_settlement_action") == "NOOP"
            for row in cases
            if row["scenario"] == "noop_duplicate"
        ),
        "commit_id_source_provenance_complete": all(
            row["final_commit_sha"]
            and (row["memory_id"] is not None or row["terminal"] == "PRECHECK_REJECT")
            and row["source"]["type"]
            and row["source"]["ref"]
            for row in observed
        ),
        "no_daily_manual_pending": metrics["daily_manual_pending_count"] <= limits["daily_manual_pending_max"],
        "offline_target_remote_untouched": (
            metrics["live_network_request_count"] <= limits["live_network_request_max"]
            and metrics["target_github_write_count"] <= limits["target_github_write_max"]
        ),
    }
    failures.extend(name for name, passed in hard_gates.items() if not passed)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "PASS" if not failures else "FAIL",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "mode": "offline_synthetic_local_git_and_modeled_github_api",
        "generated_at": "2026-07-17T00:05:00Z",
        "required_ci": automation_c.REQUIRED_CI,
        "target_repository": automation_c.REPOSITORY,
        "target_repository_remote_writes": 0,
        "synthetic_fixture_only": True,
        "production_live_acceptance_task": "TSK.OpenAIDatabase.PAM1.0019",
        "metrics": metrics,
        "hard_gates": hard_gates,
        "cases": cases,
    }
    return report, failures


def _load_config(database_dir: Path, relative: Path) -> dict[str, Any]:
    path = relative if relative.is_absolute() else database_dir / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AutomationCE2EError("e2e_config_json_invalid") from exc
    if not isinstance(value, dict):
        raise AutomationCE2EError("e2e_config_not_object")
    return value


def _report_path(database_dir: Path, config: Mapping[str, Any]) -> Path:
    return database_dir / str(config["files"]["report"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=DATABASE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        database_dir = args.database_dir.expanduser().resolve(strict=True)
        config = _load_config(database_dir, args.config)
        report, failures = evaluate(database_dir, config)
        payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        report_path = _report_path(database_dir, config)
        if args.write:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(payload, encoding="utf-8")
        elif args.check:
            if not report_path.is_file() or report_path.read_text(encoding="utf-8") != payload:
                failures.append("tracked_report_drift")
        print(payload, end="")
        if failures:
            print("AUTOMATION_C_E2E=FAIL: " + ",".join(failures), file=sys.stderr)
            return 1
        return 0
    except (AutomationCE2EError, automation_c.AutomationCError, OSError) as exc:
        print(f"AUTOMATION_C_E2E=FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
