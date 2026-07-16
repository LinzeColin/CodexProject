#!/usr/bin/env python3
"""Pure Automation C settlement policy; performs no GitHub operation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


TERMINAL_FAILURES = {
    "action_required",
    "cancelled",
    "failure",
    "neutral",
    "skipped",
    "timed_out",
}


class SettlementPolicyError(ValueError):
    pass


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise SettlementPolicyError(f"{key} must be boolean")
    return value


def decide(payload: Mapping[str, Any]) -> dict[str, Any]:
    conclusion = payload.get("workflow_conclusion")
    pr_state = payload.get("pr_state")
    if not isinstance(conclusion, str) or not conclusion:
        raise SettlementPolicyError("workflow_conclusion must be a non-empty string")
    if pr_state not in {"open", "closed", "missing"}:
        raise SettlementPolicyError("pr_state must be open, closed, or missing")

    close_issue = _required_bool(payload, "issue_open")
    if _required_bool(payload, "duplicate_event"):
        return _result("NOOP", "duplicate_event", close_issue=close_issue)

    if _required_bool(payload, "orphan"):
        if _required_bool(payload, "trusted_marker") and _required_bool(payload, "head_exact"):
            return _result(
                "DELETE_ORPHAN",
                "trusted_orphan",
                delete_branch=True,
                close_issue=close_issue,
            )
        return _result("BLOCK", "untrusted_orphan", close_issue=close_issue)

    if pr_state != "open":
        return _result("NOOP", "pr_already_settled", close_issue=close_issue)

    if not _required_bool(payload, "trusted_marker"):
        return _result("BLOCK", "untrusted_marker", close_issue=close_issue)
    if not _required_bool(payload, "same_repo"):
        return _close_only("fork", close_issue)
    if not _required_bool(payload, "authorized_actor"):
        return _close_only("unauthorized_actor", close_issue)
    if not _required_bool(payload, "head_exact"):
        return _close_only("stale_head", close_issue)
    if _required_bool(payload, "superseded"):
        return _close("superseded", close_issue)
    if conclusion in TERMINAL_FAILURES:
        return _close(conclusion, close_issue)
    if not _required_bool(payload, "non_draft"):
        return _close("draft", close_issue)
    if not _required_bool(payload, "base_main"):
        return _close("wrong_base", close_issue)
    if not _required_bool(payload, "tested_base_exact"):
        return _close("stale_tested_base", close_issue)
    if not _required_bool(payload, "mergeable"):
        return _close("conflict", close_issue)
    if not _required_bool(payload, "required_checks_pass"):
        return _close("required_check_failure", close_issue)
    if conclusion != "success":
        return _result("WAIT", "workflow_not_terminal", close_issue=close_issue)
    return _result(
        "MERGE_DELETE",
        "all_gates_pass",
        merge_pr=True,
        delete_branch=True,
        close_issue=close_issue,
    )


def _close(reason: str, close_issue: bool) -> dict[str, Any]:
    return _result(
        "CLOSE_DELETE",
        reason,
        close_pr=True,
        delete_branch=True,
        close_issue=close_issue,
    )


def _close_only(reason: str, close_issue: bool) -> dict[str, Any]:
    return _result(
        "CLOSE_ONLY",
        reason,
        close_pr=True,
        close_issue=close_issue,
    )


def _result(
    action: str,
    reason: str,
    *,
    close_pr: bool = False,
    merge_pr: bool = False,
    delete_branch: bool = False,
    close_issue: bool = False,
) -> dict[str, Any]:
    return {
        "action": action,
        "close_issue": close_issue,
        "close_pr": close_pr,
        "delete_branch": delete_branch,
        "merge_pr": merge_pr,
        "reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate one Automation C terminal state.")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise SettlementPolicyError("input must be a JSON object")
        print(json.dumps(decide(payload), sort_keys=True))
    except (OSError, json.JSONDecodeError, SettlementPolicyError) as exc:
        print(f"SETTLEMENT_POLICY=FAIL: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
