#!/usr/bin/env python3
"""Build and validate fail-closed Automation C transactions for memory mutations.

This module performs no GitHub write. It binds a validated mutation plan to the
exact transaction marker consumed by the trusted default-branch Settlement
workflow, and delegates terminal decisions to the repository's pure settlement
policy.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from plan_memory_shards import canonical_json_bytes, sha256_prefixed


TASK_ID = "TSK.OpenAIDatabase.PAM1.0017"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0017"
MUTATION_TASK_ID = "TSK.OpenAIDatabase.PAM1.0009"
MUTATION_ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0009"
SCHEMA_VERSION = "openai_database.memory_automation_c.v1"
PLAN_SCHEMA_VERSION = "openai_database.memory_cli_plan.v1"
REPOSITORY = "LinzeColin/CodexProject"
REQUIRED_CI = "Project Governance / governance"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TRANSACTION_ID_RE = re.compile(r"^mut_[0-9a-f]{20}$")
MEMORY_ID_RE = re.compile(r"^mem_[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
IDEMPOTENCY_KEY_RE = re.compile(r"^memory-mutation:[0-9a-f]{64}$")
TRANSACTION_RE = re.compile(
    r"<!-- AUTOMATION_C_TRANSACTION_V1\s+"
    r"task_id=(?P<task>\S+)\s+acceptance_id=(?P<acceptance>\S+)\s+"
    r"head_sha=(?P<head>[0-9a-f]{40})\s+base_sha=(?P<base>[0-9a-f]{40})\s+"
    r"END_AUTOMATION_C_TRANSACTION_V1 -->"
)
V2_TASK_RE = re.compile(
    r"^TSK\.(?P<project>[A-Z][A-Za-z0-9]*)\."
    r"(?P<program>[A-Z][A-Za-z0-9]*)\.(?P<sequence>[0-9]{4})$"
)
V2_ACCEPTANCE_RE = re.compile(
    r"^ACC\.(?P<project>[A-Z][A-Za-z0-9]*)\."
    r"(?P<program>[A-Z][A-Za-z0-9]*)\.(?P<sequence>[0-9]{4})$"
)
LEGACY_ID_RE = re.compile(r"^(?!(?:TSK|ACC|AC|PG)\.)[A-Za-z0-9][A-Za-z0-9_.-]{1,127}$")


class AutomationCError(ValueError):
    """Stable transaction error that contains no memory statement content."""


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise AutomationCError(f"{label}_invalid")
    return value


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AutomationCError(f"{label}_invalid")
    return value


def build_reservation(
    mutation_details: Mapping[str, Any],
    *,
    expected_base_sha: str,
    repository: str = REPOSITORY,
) -> dict[str, Any]:
    """Bind an admitted mutation plan to one same-repository transaction."""

    base_sha = _sha(expected_base_sha, "expected_base_sha")
    if mutation_details.get("task_id") != MUTATION_TASK_ID:
        raise AutomationCError("mutation_task_identity_mismatch")
    if mutation_details.get("acceptance_id") != MUTATION_ACCEPTANCE_ID:
        raise AutomationCError("mutation_acceptance_identity_mismatch")
    if mutation_details.get("base_commit_sha") != base_sha:
        raise AutomationCError("mutation_base_sha_mismatch")
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise AutomationCError("repository_invalid")

    automation = _mapping(mutation_details.get("automation_c"), "automation_c")
    transaction_id = mutation_details.get("transaction_id")
    branch = automation.get("branch")
    if not isinstance(transaction_id, str) or TRANSACTION_ID_RE.fullmatch(transaction_id) is None:
        raise AutomationCError("transaction_id_invalid")
    if branch != f"automation-c/memory-{transaction_id}":
        raise AutomationCError("transaction_branch_mismatch")
    operation = mutation_details.get("operation")
    memory_id = mutation_details.get("record_id")
    if operation not in {"add", "update", "retire", "dispute"}:
        raise AutomationCError("mutation_operation_invalid")
    if not isinstance(memory_id, str) or MEMORY_ID_RE.fullmatch(memory_id) is None:
        raise AutomationCError("memory_id_invalid")
    idempotency_key = mutation_details.get("idempotency_key")
    if not isinstance(idempotency_key, str) or IDEMPOTENCY_KEY_RE.fullmatch(idempotency_key) is None:
        raise AutomationCError("mutation_idempotency_key_invalid")
    idempotent_replay = mutation_details.get("idempotent_replay")
    transaction_required = automation.get("transaction_required")
    if not isinstance(idempotent_replay, bool) or not isinstance(transaction_required, bool):
        raise AutomationCError("mutation_replay_contract_invalid")
    if transaction_required is idempotent_replay:
        raise AutomationCError("mutation_replay_contract_invalid")
    if (
        automation.get("base_branch") != "main"
        or automation.get("same_repository_only") is not True
        or automation.get("non_draft_pr_count") != 1
        or automation.get("issue_mutations") != 0
        or automation.get("direct_main_write") is not False
        or automation.get("required_ci") != REQUIRED_CI
        or automation.get("settlement") != "trusted_default_branch_api_only"
        or automation.get("terminal_state") != "PR=0/Issue=0/non-main=0"
        or automation.get("live_transaction_glue_task") != TASK_ID
        or mutation_details.get("generated_views_refresh_owner") != "scripts/memory_automation_c.py"
        or mutation_details.get("production_live_acceptance_task") != "TSK.OpenAIDatabase.PAM1.0019"
        or mutation_details.get("manual_approval_required") is not False
        or mutation_details.get("model_inference_persisted") != 0
    ):
        raise AutomationCError("automation_c_contract_drift")
    source = _mapping(mutation_details.get("source"), "mutation_source")
    source_type = source.get("type")
    if source_type not in {"explicit_user", "repository_evidence"}:
        raise AutomationCError("mutation_source_not_transaction_eligible")
    statement_sha256 = mutation_details.get("statement_sha256")
    if statement_sha256 is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", str(statement_sha256)):
        raise AutomationCError("statement_sha256_invalid")

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "mutation_task_id": MUTATION_TASK_ID,
        "mutation_acceptance_id": MUTATION_ACCEPTANCE_ID,
        "repository": repository,
        "transaction_id": transaction_id,
        "marker_task_id": f"memory-mutation-{transaction_id}",
        "marker_acceptance_id": f"memory-acceptance-{transaction_id}",
        "operation": operation,
        "memory_id": memory_id,
        "idempotent_replay": idempotent_replay,
        "transaction_required": transaction_required,
        "branch": branch,
        "base_branch": "main",
        "base_sha": base_sha,
        "source_type": source_type,
        "source_ref_sha256": _portable_ref_sha256(source.get("ref")),
        "statement_sha256": statement_sha256,
        "required_ci": REQUIRED_CI,
        "non_draft_pr_limit": 1,
        "issue_mutation_limit": 0,
        "direct_main_write": False,
        "settlement": "trusted_default_branch_api_only",
        "terminal_state": "PR=0/Issue=0/non-main=0",
    }


def _portable_ref_sha256(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise AutomationCError("source_ref_invalid")
    import hashlib

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def transaction_marker(reservation: Mapping[str, Any], head_sha: str) -> str:
    head = _sha(head_sha, "head_sha")
    base = _sha(reservation.get("base_sha"), "base_sha")
    if reservation.get("task_id") != TASK_ID or reservation.get("acceptance_id") != ACCEPTANCE_ID:
        raise AutomationCError("reservation_identity_mismatch")
    marker_task = reservation.get("marker_task_id")
    marker_acceptance = reservation.get("marker_acceptance_id")
    _validate_marker_identity(marker_task, marker_acceptance)
    return (
        "<!-- AUTOMATION_C_TRANSACTION_V1 "
        f"task_id={marker_task} acceptance_id={marker_acceptance} "
        f"head_sha={head} base_sha={base} "
        "END_AUTOMATION_C_TRANSACTION_V1 -->"
    )


def parse_transaction_marker(body: Any) -> dict[str, str]:
    if not isinstance(body, str):
        raise AutomationCError("transaction_marker_missing")
    matches = list(TRANSACTION_RE.finditer(body))
    if len(matches) != 1:
        raise AutomationCError("transaction_marker_cardinality_invalid")
    values = matches[0].groupdict()
    _validate_marker_identity(values["task"], values["acceptance"])
    return values


def _validate_marker_identity(task_id: Any, acceptance_id: Any) -> None:
    if not isinstance(task_id, str) or not isinstance(acceptance_id, str):
        raise AutomationCError("transaction_marker_identity_mismatch")
    task_v2 = V2_TASK_RE.fullmatch(task_id)
    acceptance_v2 = V2_ACCEPTANCE_RE.fullmatch(acceptance_id)
    if task_v2 or acceptance_v2:
        if not task_v2 or not acceptance_v2:
            raise AutomationCError("transaction_marker_identity_mismatch")
        task_suffix = tuple(task_v2.group(name) for name in ("project", "program", "sequence"))
        acceptance_suffix = tuple(
            acceptance_v2.group(name) for name in ("project", "program", "sequence")
        )
        if task_suffix != acceptance_suffix:
            raise AutomationCError("transaction_marker_identity_mismatch")
        return
    if LEGACY_ID_RE.fullmatch(task_id) is None or LEGACY_ID_RE.fullmatch(acceptance_id) is None:
        raise AutomationCError("transaction_marker_identity_mismatch")


def build_pr_body(reservation: Mapping[str, Any], head_sha: str) -> str:
    """Render a redacted PR body; raw statement and source ref never appear."""

    marker = transaction_marker(reservation, head_sha)
    return "\n".join(
        [
            marker,
            "",
            "## Governed memory mutation",
            "",
            f"- transaction: `{reservation['transaction_id']}`",
            f"- mutation task: `{reservation['mutation_task_id']}`",
            f"- operation: `{reservation['operation']}`",
            f"- memory id: `{reservation['memory_id']}`",
            f"- source type: `{reservation['source_type']}`",
            f"- source ref SHA-256: `{reservation['source_ref_sha256']}`",
            f"- statement SHA-256: `{reservation['statement_sha256'] or 'not_applicable'}`",
            f"- required CI: `{reservation['required_ci']}`",
            "",
            "Settlement must verify this exact head/base pair, then squash-merge or close and delete.",
            "",
        ]
    )


def open_or_reuse_pr(
    existing: Mapping[str, Any] | None,
    reservation: Mapping[str, Any],
    *,
    head_sha: str,
    actor: str = "automation-c-sandbox",
) -> tuple[dict[str, Any], bool]:
    """Create one modeled non-draft PR or idempotently reuse the exact one."""

    if reservation.get("transaction_required") is not True:
        raise AutomationCError("idempotent_transaction_pr_forbidden")
    head = _sha(head_sha, "head_sha")
    body = build_pr_body(reservation, head)
    expected = {
        "number": 1,
        "state": "open",
        "draft": False,
        "body": body,
        "head": {
            "ref": reservation["branch"],
            "sha": head,
            "repo": {"full_name": reservation["repository"]},
        },
        "base": {"ref": "main", "sha": reservation["base_sha"]},
        "user": {"login": actor},
        "issue_open": False,
    }
    if existing is None:
        return expected, True
    if dict(existing) != expected:
        raise AutomationCError("duplicate_pr_conflicts_with_reserved_transaction")
    return expected, False


def settlement_input(
    pr: Mapping[str, Any],
    reservation: Mapping[str, Any],
    *,
    workflow_conclusion: str,
    required_checks_pass: bool,
    mergeable: bool = True,
    duplicate_event: bool = False,
    pr_state: str | None = None,
    authorized_actors: Sequence[str] = ("automation-c-sandbox",),
) -> dict[str, Any]:
    """Validate untrusted PR fields, then build the pure Settlement input."""

    marker = parse_transaction_marker(pr.get("body"))
    head = _mapping(pr.get("head"), "pr_head")
    base = _mapping(pr.get("base"), "pr_base")
    head_repo = _mapping(head.get("repo"), "pr_head_repo")
    expected_head = _sha(head.get("sha"), "pr_head_sha")
    trusted_marker = (
        marker["head"] == expected_head
        and marker["base"] == reservation.get("base_sha")
        and marker["task"] == reservation.get("marker_task_id")
        and marker["acceptance"] == reservation.get("marker_acceptance_id")
    )
    return {
        "workflow_conclusion": workflow_conclusion,
        "pr_state": pr_state or str(pr.get("state")),
        "issue_open": pr.get("issue_open") is True,
        "duplicate_event": duplicate_event,
        "orphan": False,
        "trusted_marker": trusted_marker,
        "same_repo": head_repo.get("full_name") == reservation.get("repository"),
        "authorized_actor": str(_mapping(pr.get("user"), "pr_user").get("login")).casefold()
        in {actor.casefold() for actor in authorized_actors},
        "head_exact": head.get("ref") == reservation.get("branch") and trusted_marker,
        "superseded": False,
        "non_draft": pr.get("draft") is False,
        "base_main": base.get("ref") == "main",
        "tested_base_exact": base.get("sha") == reservation.get("base_sha"),
        "mergeable": mergeable,
        "required_checks_pass": required_checks_pass,
    }


def load_settlement_decider(
    repository_root: Path | None = None,
) -> Callable[[Mapping[str, Any]], dict[str, Any]]:
    root = repository_root or Path(__file__).resolve().parents[2]
    path = root / "scripts/agent_loop/settlement_policy.py"
    spec = importlib.util.spec_from_file_location("memory_automation_c_settlement_policy", path)
    if spec is None or spec.loader is None:
        raise AutomationCError("settlement_policy_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.decide


def prepare_from_plan(plan: Mapping[str, Any], *, head_sha: str, repository: str) -> dict[str, Any]:
    if (
        plan.get("schema_version") != PLAN_SCHEMA_VERSION
        or plan.get("event") != "PLAN"
        or plan.get("status") != "PASS"
        or plan.get("operation") != "mutate"
        or plan.get("task_id") != MUTATION_TASK_ID
        or plan.get("acceptance_id") != MUTATION_ACCEPTANCE_ID
        or plan.get("writes_files") is not False
    ):
        raise AutomationCError("mutation_plan_contract_invalid")
    details = _mapping(plan.get("details"), "mutation_plan_details")
    plan_material = {
        "schema_version": plan["schema_version"],
        "operation": plan["operation"],
        "details": dict(details),
    }
    if plan.get("plan_sha256") != sha256_prefixed(canonical_json_bytes(plan_material)):
        raise AutomationCError("mutation_plan_hash_mismatch")
    if plan.get("required_idempotency_key") != details.get("idempotency_key"):
        raise AutomationCError("mutation_plan_idempotency_guard_mismatch")
    if plan.get("required_write_guards") != [
        "--apply",
        "--base-sha",
        "--idempotency-key",
        "exact_automation_c_branch",
    ]:
        raise AutomationCError("mutation_plan_write_guards_invalid")
    reservation = build_reservation(
        details,
        expected_base_sha=str(details.get("base_commit_sha")),
        repository=repository,
    )
    if reservation["transaction_required"] is False:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "writes_files": False,
            "idempotent": True,
            "terminal_action": "NOOP",
            "reservation": reservation,
            "pull_request": None,
        }
    pr, _ = open_or_reuse_pr(None, reservation, head_sha=head_sha)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "writes_files": False,
        "idempotent": False,
        "terminal_action": "PR_TEMPLATE",
        "reservation": reservation,
        "pull_request": pr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path, help="Mutation PLAN JSON object")
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--repository", default=REPOSITORY)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        if not isinstance(plan, dict):
            raise AutomationCError("mutation_plan_invalid")
        print(
            json.dumps(
                prepare_from_plan(plan, head_sha=args.head_sha, repository=args.repository),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except (AutomationCError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "status": "FAIL_CLOSED",
                    "writes_files": False,
                    "reason": str(exc) if isinstance(exc, AutomationCError) else "input_error",
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
