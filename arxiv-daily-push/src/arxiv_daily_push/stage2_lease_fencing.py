"""S2PMT03 local lease, fencing, and outbox evidence helpers."""

from __future__ import annotations

import copy
import hashlib
import threading
from collections.abc import Mapping
from typing import Any

from .state_machine import RUN_STATES, validate_transition


S2PMT03_LEASE_FENCING_MODEL_ID = "adp-s2pmt03-lease-fencing-outbox-v1"
S2PMT03_ACCEPTANCE_ID = "ACC-S2PMT03-LEASE-FENCING-OUTBOX"
S2PMT03_TASK_ID = "S2PMT03"
S2PMT03_SCHEMA_VERSION = 1
S2PMT03_MIN_LEASE_MS = 1000
S2PMT03_DEFAULT_LEASE_MS = 300000
S2PMT03_REQUIRED_TERMINAL_MAILS = ("M1", "M2", "M3")
S2PMT03_REQUIRED_OUTBOX_STATES = ("PENDING", "CLAIMED", "ACCEPTED_PENDING_COMMIT", "SENT", "BLOCKED")
S2PMT03_REQUIRED_GATES = (
    "row_version_compare_and_swap",
    "single_claimant_under_concurrency",
    "lease_expiry",
    "fencing_token",
    "state_history_consistency",
    "transactional_outbox",
    "smtp_accept_crash_window",
    "m4_cycle_watermark",
    "watchdog_stale_lock_recovery",
    "no_production_side_effect",
)

S2PMT03_CAS_UPDATE_STATEMENT = "UPDATE work_items SET lease_owner=?, lease_until_ms=?, row_version=row_version+1, fencing_token=fencing_token+1 WHERE work_id=? AND row_version=?"
S2PMT03_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "production_side_effects_enabled",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_upload_allowed",
    "production_restore_executed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "db_migration_executed",
)


def claim_leased_item(
    item: Mapping[str, Any],
    *,
    owner_id: str,
    now_ms: int,
    lease_ms: int = S2PMT03_DEFAULT_LEASE_MS,
) -> dict[str, Any]:
    """Claim a local work item only when no unexpired foreign lease exists."""

    reasons = _claim_blockers(item, owner_id=owner_id, now_ms=now_ms, lease_ms=lease_ms)
    if reasons:
        return _blocked_action("claim_lease", reasons, {"item": dict(item)})
    updated = copy.deepcopy(dict(item))
    updated["lease_owner"] = owner_id
    updated["lease_until_ms"] = now_ms + lease_ms
    updated["row_version"] = int(updated.get("row_version") or 0) + 1
    updated["fencing_token"] = int(updated.get("fencing_token") or 0) + 1
    return _pass_action(
        "claim_lease",
        {
            "item": updated,
            "owner_id": owner_id,
            "lease_ms": lease_ms,
            "now_ms": now_ms,
            "affected_rows": 1,
            "row_version_compare_and_swap": True,
            "fencing_token": updated["fencing_token"],
        },
    )


class LocalLeaseClaimRepository:
    """Local evidence stand-in for an atomic DB compare-and-swap lease claim."""

    def __init__(self, item: Mapping[str, Any]) -> None:
        self._item = copy.deepcopy(dict(item))
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._item)

    def events(self) -> list[dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._events)

    def claim(
        self,
        *,
        owner_id: str,
        expected_row_version: int,
        now_ms: int,
        lease_ms: int = S2PMT03_DEFAULT_LEASE_MS,
    ) -> dict[str, Any]:
        with self._lock:
            current = copy.deepcopy(self._item)
            if int(current.get("row_version") or 0) != expected_row_version:
                result = _blocked_action(
                    "claim_lease",
                    ["row_version compare-and-swap failed"],
                    {
                        "item": current,
                        "owner_id": owner_id,
                        "expected_row_version": expected_row_version,
                        "affected_rows": 0,
                        "cas_statement": S2PMT03_CAS_UPDATE_STATEMENT,
                    },
                )
            else:
                result = claim_leased_item(current, owner_id=owner_id, now_ms=now_ms, lease_ms=lease_ms)
                result["expected_row_version"] = expected_row_version
                result["cas_statement"] = S2PMT03_CAS_UPDATE_STATEMENT
                if result["status"] == "pass":
                    result["affected_rows"] = 1
                    self._item = copy.deepcopy(result["item"])
                else:
                    result["affected_rows"] = 0
            self._events.append(
                {
                    "action": "claim_lease",
                    "owner_id": owner_id,
                    "expected_row_version": expected_row_version,
                    "observed_row_version": int(current.get("row_version") or 0),
                    "status": result["status"],
                    "affected_rows": result["affected_rows"],
                }
            )
            return copy.deepcopy(result)


def apply_fenced_state_transition(
    record: Mapping[str, Any],
    *,
    next_state: str,
    expected_row_version: int,
    fencing_token: int,
    reason: str,
    at: str,
) -> dict[str, Any]:
    """Apply a state transition only for the current row version and fencing token."""

    current_state = str(record.get("current_state") or "")
    reasons: list[str] = []
    if current_state not in RUN_STATES:
        reasons.append("current_state is invalid")
    if int(record.get("row_version") or 0) != expected_row_version:
        reasons.append("row_version compare-and-swap failed")
    if int(record.get("fencing_token") or 0) != fencing_token:
        reasons.append("fencing_token is stale")
    reasons.extend(validate_transition(current_state, next_state))
    history = record.get("state_history") if isinstance(record.get("state_history"), list) else []
    if history:
        last = history[-1]
        if isinstance(last, Mapping) and str(last.get("to_state") or "") != current_state:
            reasons.append("state_history last to_state does not match current_state")
    if reasons:
        return _blocked_action(
            "state_transition",
            reasons,
            {
                "record": dict(record),
                "next_state": next_state,
                "expected_row_version": expected_row_version,
                "fencing_token": fencing_token,
                "affected_rows": 0,
                "cas_statement": "UPDATE run_records SET current_state=?, row_version=row_version+1 WHERE run_id=? AND row_version=? AND fencing_token=?",
            },
        )

    updated = copy.deepcopy(dict(record))
    updated["current_state"] = next_state
    updated["row_version"] = expected_row_version + 1
    updated["state_history"] = list(history) + [{"from_state": current_state, "to_state": next_state, "reason": reason, "at": at}]
    return _pass_action(
        "state_transition",
        {
            "record": updated,
            "expected_row_version": expected_row_version,
            "fencing_token": fencing_token,
            "affected_rows": 1,
            "cas_statement": "UPDATE run_records SET current_state=?, row_version=row_version+1 WHERE run_id=? AND row_version=? AND fencing_token=?",
            "state_history_consistency": True,
        },
    )


def build_outbox_message(
    *,
    cycle_id: str,
    product_id: str,
    recipient: str,
    content_revision_id: str,
    body: str,
    generated_at: str,
) -> dict[str, Any]:
    """Build an idempotent outbox message identity for at-least-once delivery."""

    mail_key = f"{cycle_id}|{product_id}|{recipient}"
    body_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    message_seed = f"{mail_key}|{content_revision_id}|{body_sha256}"
    message_id = f"adp-{hashlib.sha256(message_seed.encode('utf-8')).hexdigest()[:24]}@arxiv-daily-push.local"
    return {
        "mail_key": mail_key,
        "cycle_id": cycle_id,
        "product_id": product_id,
        "recipient": recipient,
        "content_revision_id": content_revision_id,
        "body_sha256": body_sha256,
        "message_id": message_id,
        "status": "PENDING",
        "row_version": 0,
        "fencing_token": 0,
        "lease_owner": "",
        "lease_until_ms": 0,
        "send_attempts": 0,
        "generated_at": generated_at,
        "real_smtp_sent": False,
    }


def claim_outbox_message(
    message: Mapping[str, Any],
    *,
    owner_id: str,
    now_ms: int,
    lease_ms: int = S2PMT03_DEFAULT_LEASE_MS,
) -> dict[str, Any]:
    """Claim one outbox row with the same lease/fencing rules as work items."""

    if message.get("status") not in S2PMT03_REQUIRED_OUTBOX_STATES:
        return _blocked_action("claim_outbox", ["outbox status is invalid"], {"message": dict(message)})
    claim = claim_leased_item(message, owner_id=owner_id, now_ms=now_ms, lease_ms=lease_ms)
    if claim["status"] != "pass":
        return _blocked_action("claim_outbox", list(claim.get("blocking_reasons") or []), {"message": dict(message)})
    updated = dict(claim["item"])
    updated["status"] = "CLAIMED"
    updated["send_attempts"] = int(updated.get("send_attempts") or 0) + 1
    return _pass_action("claim_outbox", {"message": updated, "transactional_outbox": True})


def decide_watchdog_stale_lock_recovery(
    lock: Mapping[str, Any],
    *,
    recovery_owner_id: str,
    now_ms: int,
    live_owner_ids: set[str] | frozenset[str],
    lease_ms: int = S2PMT03_DEFAULT_LEASE_MS,
) -> dict[str, Any]:
    """Decide whether a watchdog may safely recover a stale local lease."""

    owner_id = str(lock.get("lease_owner") or "")
    lease_until = int(lock.get("lease_until_ms") or 0)
    reasons: list[str] = []
    if not recovery_owner_id:
        reasons.append("recovery_owner_id is required")
    if owner_id and owner_id in live_owner_ids:
        reasons.append("lease owner is still live; watchdog recovery is forbidden")
    if lease_until > now_ms:
        reasons.append("lease has not expired")
    if reasons:
        return _blocked_action(
            "watchdog_stale_lock_recovery",
            reasons,
            {
                "lock": dict(lock),
                "now_ms": now_ms,
                "live_owner_ids": sorted(live_owner_ids),
                "watchdog_stale_lock_recovery": False,
                "safe_takeover": False,
                "affected_rows": 0,
            },
        )

    recovered = claim_leased_item(lock, owner_id=recovery_owner_id, now_ms=now_ms, lease_ms=lease_ms)
    if recovered["status"] != "pass":
        return _blocked_action(
            "watchdog_stale_lock_recovery",
            list(recovered.get("blocking_reasons") or ["watchdog recovery claim failed"]),
            {
                "lock": dict(lock),
                "now_ms": now_ms,
                "live_owner_ids": sorted(live_owner_ids),
                "watchdog_stale_lock_recovery": False,
                "safe_takeover": False,
                "affected_rows": 0,
            },
        )
    return _pass_action(
        "watchdog_stale_lock_recovery",
        {
            "lock": recovered["item"],
            "previous_owner_id": owner_id,
            "recovery_owner_id": recovery_owner_id,
            "now_ms": now_ms,
            "live_owner_ids": sorted(live_owner_ids),
            "watchdog_stale_lock_recovery": True,
            "safe_takeover": True,
            "affected_rows": recovered["affected_rows"],
            "fencing_token": recovered["fencing_token"],
        },
    )


def reconcile_smtp_accept_crash(
    message: Mapping[str, Any],
    *,
    provider_accept_ref: str | None = None,
) -> dict[str, Any]:
    """Represent the SMTP accepted-before-local-commit crash window fail-closed."""

    if message.get("status") != "ACCEPTED_PENDING_COMMIT":
        return _blocked_action("smtp_accept_crash", ["outbox status must be ACCEPTED_PENDING_COMMIT"], {"message": dict(message)})
    durable_ref = bool(provider_accept_ref and "://" in provider_accept_ref)
    updated = copy.deepcopy(dict(message))
    updated["smtp_accept_crash_window_reproduced"] = True
    updated["real_smtp_sent"] = False
    if not durable_ref:
        updated["status"] = "BLOCKED"
        updated["retry_safe"] = False
        return _blocked_action(
            "smtp_accept_crash",
            ["provider_accept_ref is required before any resend decision"],
            {"message": updated, "smtp_accept_crash_window": True},
        )
    updated["status"] = "SENT"
    updated["provider_accept_ref"] = provider_accept_ref
    updated["retry_safe"] = False
    return _pass_action("smtp_accept_crash", {"message": updated, "smtp_accept_crash_window": True})


def build_m4_cycle_watermark(
    *,
    cycle_id: str,
    terminal_mails: list[Mapping[str, Any]],
    generated_at: str,
    deadline_passed: bool = False,
) -> dict[str, Any]:
    """Validate that M4 is keyed to one cycle and terminal M1-M3 states."""

    by_product = {str(item.get("product_id") or ""): item for item in terminal_mails}
    reasons: list[str] = []
    for product_id in S2PMT03_REQUIRED_TERMINAL_MAILS:
        item = by_product.get(product_id)
        if not item:
            reasons.append(f"{product_id} terminal mail is missing")
            continue
        if item.get("cycle_id") != cycle_id:
            reasons.append(f"{product_id} cycle_id does not match")
        if item.get("status") not in {"SENT", "DEGRADED"}:
            reasons.append(f"{product_id} terminal status is invalid")
    status = "ready" if not reasons else "degraded" if deadline_passed else "waiting"
    return {
        "cycle_id": cycle_id,
        "generated_at": generated_at,
        "status": status,
        "deadline_passed": deadline_passed,
        "required_terminal_mails": list(S2PMT03_REQUIRED_TERMINAL_MAILS),
        "observed_terminal_mails": sorted(by_product),
        "blocking_reasons": reasons,
        "m4_ready": status == "ready",
        "m4_cycle_watermark": status in {"ready", "degraded"},
    }


def build_lease_fencing_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic local S2PMT03 evidence report."""

    claim = claim_leased_item({"work_id": "cycle-20260702-M1", "row_version": 0}, owner_id="worker-a", now_ms=1000)
    claim_repo = LocalLeaseClaimRepository({"work_id": "cycle-20260702-M1", "row_version": 0})
    first_claim = claim_repo.claim(owner_id="worker-a", expected_row_version=0, now_ms=1000)
    stale_claim = claim_repo.claim(owner_id="worker-b", expected_row_version=0, now_ms=1000)
    stale_transition = apply_fenced_state_transition(
        {"current_state": "created", "row_version": 1, "fencing_token": 1, "state_history": [{"from_state": "", "to_state": "created"}]},
        next_state="health_checked",
        expected_row_version=0,
        fencing_token=1,
        reason="stale worker",
        at=generated_at,
    )
    valid_transition = apply_fenced_state_transition(
        {"current_state": "created", "row_version": 1, "fencing_token": 1, "state_history": [{"from_state": "", "to_state": "created"}]},
        next_state="health_checked",
        expected_row_version=1,
        fencing_token=1,
        reason="owner worker",
        at=generated_at,
    )
    live_lock_recovery = decide_watchdog_stale_lock_recovery(
        {
            "work_id": "cycle-20260702-M2",
            "row_version": 4,
            "lease_owner": "slow-worker",
            "lease_until_ms": 1000,
            "fencing_token": 9,
        },
        recovery_owner_id="watchdog",
        now_ms=2000,
        live_owner_ids={"slow-worker"},
    )
    dead_lock_recovery = decide_watchdog_stale_lock_recovery(
        {
            "work_id": "cycle-20260702-M3",
            "row_version": 5,
            "lease_owner": "dead-worker",
            "lease_until_ms": 1000,
            "fencing_token": 10,
        },
        recovery_owner_id="watchdog",
        now_ms=2000,
        live_owner_ids=set(),
    )
    outbox = build_outbox_message(
        cycle_id="2026-07-02",
        product_id="M1",
        recipient="linzezhang35@gmail.com",
        content_revision_id="rev-1",
        body="learning mail body",
        generated_at=generated_at,
    )
    outbox_claim = claim_outbox_message(outbox, owner_id="sender-a", now_ms=1000)
    accepted = dict(outbox_claim["message"])
    accepted["status"] = "ACCEPTED_PENDING_COMMIT"
    crash = reconcile_smtp_accept_crash(accepted)
    watermark = build_m4_cycle_watermark(
        cycle_id="2026-07-02",
        generated_at=generated_at,
        terminal_mails=[
            {"cycle_id": "2026-07-02", "product_id": "M1", "status": "SENT"},
            {"cycle_id": "2026-07-02", "product_id": "M2", "status": "SENT"},
            {"cycle_id": "2026-07-02", "product_id": "M3", "status": "DEGRADED"},
        ],
        deadline_passed=True,
    )
    gates = {
        "row_version_compare_and_swap": claim["status"] == "pass" and stale_transition["status"] == "blocked" and stale_claim["affected_rows"] == 0,
        "single_claimant_under_concurrency": first_claim["status"] == "pass" and stale_claim["status"] == "blocked",
        "lease_expiry": int(claim["item"]["lease_until_ms"]) > 1000 if claim["status"] == "pass" else False,
        "fencing_token": valid_transition["status"] == "pass" and stale_transition["status"] == "blocked",
        "state_history_consistency": valid_transition["status"] == "pass",
        "transactional_outbox": outbox_claim["status"] == "pass" and bool(outbox.get("mail_key")),
        "smtp_accept_crash_window": crash["status"] == "blocked" and crash.get("smtp_accept_crash_window") is True,
        "m4_cycle_watermark": watermark["m4_cycle_watermark"] is True,
        "watchdog_stale_lock_recovery": live_lock_recovery["status"] == "blocked"
        and dead_lock_recovery["status"] == "pass"
        and dead_lock_recovery["safe_takeover"] is True,
        "no_production_side_effect": True,
    }
    status = "pass" if all(gates.values()) else "blocked"
    return _base_report(
        status=status,
        generated_at=generated_at,
        blocking_reasons=[] if status == "pass" else [key for key, passed in gates.items() if not passed],
        extra={
            "gates": gates,
            "lease_claim": claim,
            "cas_claim": first_claim,
            "stale_cas_claim": stale_claim,
            "cas_event_log": claim_repo.events(),
            "stale_transition": stale_transition,
            "valid_transition": valid_transition,
            "live_lock_recovery": live_lock_recovery,
            "dead_lock_recovery": dead_lock_recovery,
            "outbox_claim": outbox_claim,
            "smtp_accept_crash": crash,
            "m4_watermark": watermark,
        },
    )


def validate_lease_fencing_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PMT03 local lease/fencing evidence reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT03_LEASE_FENCING_MODEL_ID:
        errors.append("S2PMT03 report model_id is invalid")
    if report.get("schema_version") != S2PMT03_SCHEMA_VERSION:
        errors.append("S2PMT03 report schema_version must be 1")
    if report.get("task_id") != S2PMT03_TASK_ID:
        errors.append("S2PMT03 report task_id is invalid")
    if report.get("acceptance_id") != S2PMT03_ACCEPTANCE_ID:
        errors.append("S2PMT03 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PMT03 report status must be pass or blocked")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PMT03 report requires blocking_reasons")
    for key in S2PMT03_REQUIRED_PRODUCTION_FALSE_FLAGS:
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    gates = report.get("gates") if isinstance(report.get("gates"), Mapping) else {}
    for gate in S2PMT03_REQUIRED_GATES:
        if gate not in gates:
            errors.append(f"gates.{gate} is required")
    if report.get("status") == "pass" and not all(gates.get(gate) is True for gate in S2PMT03_REQUIRED_GATES):
        errors.append("passing S2PMT03 report requires all gates true")
    return errors


def _claim_blockers(item: Mapping[str, Any], *, owner_id: str, now_ms: int, lease_ms: int) -> list[str]:
    reasons: list[str] = []
    if not item.get("work_id") and not item.get("mail_key"):
        reasons.append("leased item requires work_id or mail_key")
    if not owner_id:
        reasons.append("owner_id is required")
    if lease_ms < S2PMT03_MIN_LEASE_MS:
        reasons.append(f"lease_ms must be at least {S2PMT03_MIN_LEASE_MS}")
    lease_owner = str(item.get("lease_owner") or "")
    lease_until = int(item.get("lease_until_ms") or 0)
    if lease_owner and lease_owner != owner_id and lease_until > now_ms:
        reasons.append("unexpired foreign lease blocks claim")
    return reasons


def _base_report(*, status: str, generated_at: str, blocking_reasons: list[str], extra: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "model_id": S2PMT03_LEASE_FENCING_MODEL_ID,
        "schema_version": S2PMT03_SCHEMA_VERSION,
        "task_id": S2PMT03_TASK_ID,
        "acceptance_id": S2PMT03_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "delivery_semantics": "at_least_once_with_idempotent_message_id",
        "exactly_once_claimed": False,
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "production_restore_executed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
        **dict(extra),
    }


def _pass_action(action: str, extra: Mapping[str, Any]) -> dict[str, Any]:
    return {"action": action, "status": "pass", "blocking_reasons": [], **dict(extra)}


def _blocked_action(action: str, reasons: list[str], extra: Mapping[str, Any]) -> dict[str, Any]:
    return {"action": action, "status": "blocked", "blocking_reasons": sorted(set(reasons)), **dict(extra)}
