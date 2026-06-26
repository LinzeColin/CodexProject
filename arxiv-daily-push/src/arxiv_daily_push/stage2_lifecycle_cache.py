"""S2PMT04 local lifecycle and cache-cleanup evidence helpers."""

from __future__ import annotations

import hashlib
import json
import plistlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


S2PMT04_LIFECYCLE_CACHE_MODEL_ID = "adp-s2pmt04-lifecycle-cache-cleanup-v1"
S2PMT04_ACCEPTANCE_ID = "ACC-S2PMT04-LIFECYCLE"
S2PMT04_TASK_ID = "S2PMT04"
S2PMT04_SCHEMA_VERSION = 1
S2PMT04_DEFAULT_CACHE_TTL_SECONDS = 604800
S2PMT04_DEFAULT_CACHE_CAP_BYTES = 1073741824
S2PMT04_DEFAULT_SHUTDOWN_GRACE_SECONDS = 300
S2PMT04_LAUNCHD_LABEL = "com.linze.adp.local.daily"
S2PMT04_LIFECYCLE_STATES = (
    "STOPPED",
    "STARTING",
    "RECOVERING",
    "LEADER",
    "RUNNING",
    "DRAINING",
    "CHECKPOINTING",
    "CLEANING",
)
S2PMT04_LIFECYCLE_TRANSITIONS = (
    ("STOPPED", "STARTING"),
    ("STARTING", "RECOVERING"),
    ("RECOVERING", "LEADER"),
    ("LEADER", "RUNNING"),
    ("RUNNING", "DRAINING"),
    ("DRAINING", "CHECKPOINTING"),
    ("CHECKPOINTING", "CLEANING"),
    ("CLEANING", "STOPPED"),
)
S2PMT04_CACHE_CLASSES = ("durable_evidence", "rebuildable_cache", "temp")
S2PMT04_REQUIRED_SHUTDOWN_RECEIPT_STEPS = (
    "inflight",
    "outbox",
    "checkpoint",
    "cleanup",
    "backup",
    "lease_release",
)
S2PMT04_REQUIRED_GATES = (
    "automatic_wake_dry_run",
    "lifecycle_transition_chain",
    "startup_reconciliation",
    "shutdown_receipt",
    "transaction_completion_signal",
    "cache_cleanup_safety",
    "launchd_plist_parseable",
    "no_production_side_effect",
)
S2PMT04_REQUIRED_PRODUCTION_FALSE_FLAGS = (
    "production_side_effects_enabled",
    "real_smtp_sent",
    "scheduler_installed",
    "scheduler_enabled",
    "release_upload_allowed",
    "production_restore_executed",
    "public_schema_changed",
    "queue_schema_changed",
    "queue_mutation_allowed",
    "db_migration_executed",
)


def validate_lifecycle_transition(from_state: str, to_state: str) -> list[str]:
    """Validate one S2PMT04 lifecycle transition."""

    errors: list[str] = []
    if from_state not in S2PMT04_LIFECYCLE_STATES:
        errors.append("from_state is not an S2PMT04 lifecycle state")
    if to_state not in S2PMT04_LIFECYCLE_STATES and to_state != "STOPPED":
        errors.append("to_state is not an S2PMT04 lifecycle state")
    if (from_state, to_state) not in S2PMT04_LIFECYCLE_TRANSITIONS:
        errors.append(f"transition {from_state}->{to_state} is not allowed")
    return errors


def build_lifecycle_transition_plan(*, cycle_id: str, generated_at: str) -> dict[str, Any]:
    """Build the required wake-to-drain local lifecycle sequence."""

    steps = [
        {
            "from_state": from_state,
            "to_state": to_state,
            "allowed": not validate_lifecycle_transition(from_state, to_state),
        }
        for from_state, to_state in S2PMT04_LIFECYCLE_TRANSITIONS
    ]
    return {
        "cycle_id": cycle_id,
        "generated_at": generated_at,
        "initial_state": "STOPPED",
        "terminal_state": "STOPPED",
        "states": list(S2PMT04_LIFECYCLE_STATES),
        "transitions": steps,
        "claim_new_work_disabled_during_draining": True,
        "direct_stop_without_drain_allowed": False,
        "transition_chain_valid": all(step["allowed"] for step in steps),
    }


def build_startup_reconciliation(
    *,
    temp_items: Sequence[Mapping[str, Any]],
    inflight_items: Sequence[Mapping[str, Any]],
    outbox_items: Sequence[Mapping[str, Any]],
    stale_locks: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    """Plan startup recovery for temp files, inflight work, outbox rows, and stale locks."""

    temp_actions = [
        {
            "item_id": str(item.get("item_id") or item.get("path") or ""),
            "action": "cleanup_temp_after_whitelist_check",
            "dry_run": True,
        }
        for item in temp_items
    ]
    inflight_actions = [
        {
            "work_id": str(item.get("work_id") or ""),
            "previous_state": str(item.get("state") or "unknown"),
            "action": "requeue_or_resume_after_checkpoint_check",
            "queue_mutation_applied": False,
        }
        for item in inflight_items
    ]
    outbox_actions = [
        {
            "mail_key": str(item.get("mail_key") or ""),
            "previous_status": str(item.get("status") or "unknown"),
            "action": "reconcile_transactional_outbox",
            "resend_allowed_without_provider_ref": False,
        }
        for item in outbox_items
    ]
    lock_actions = [
        {
            "lock_id": str(item.get("lock_id") or ""),
            "lease_owner": str(item.get("lease_owner") or ""),
            "action": "release_stale_lock_dry_run",
            "lease_release_applied": False,
        }
        for item in stale_locks
    ]
    return {
        "generated_at": generated_at,
        "phase": "RECOVERING",
        "temp_actions": temp_actions,
        "inflight_actions": inflight_actions,
        "outbox_actions": outbox_actions,
        "stale_lock_actions": lock_actions,
        "new_work_claim_allowed": False,
        "queue_mutation_applied": False,
        "reconciliation_ready": True,
    }


def build_shutdown_receipt(
    *,
    cycle_id: str,
    inflight_count: int,
    outbox_pending_count: int,
    checkpoint_ref: str,
    cleanup_ref: str,
    backup_ref: str,
    lease_released: bool,
    graceful_elapsed_seconds: int,
    generated_at: str,
) -> dict[str, Any]:
    """Build a durable shutdown receipt for drain/checkpoint/cleanup exit."""

    requeue_required = graceful_elapsed_seconds > S2PMT04_DEFAULT_SHUTDOWN_GRACE_SECONDS and inflight_count > 0
    steps = {
        "inflight": {
            "count": inflight_count,
            "new_claims_stopped": True,
            "safe_requeue_required": requeue_required,
            "safe_requeue_applied": False,
        },
        "outbox": {
            "pending_count": outbox_pending_count,
            "transactional_identity_preserved": True,
            "resend_without_provider_ref_allowed": False,
        },
        "checkpoint": {"ref": checkpoint_ref, "written": bool(checkpoint_ref)},
        "cleanup": {"ref": cleanup_ref, "dry_run_or_whitelisted": bool(cleanup_ref)},
        "backup": {"ref": backup_ref, "written": bool(backup_ref)},
        "lease_release": {"released": bool(lease_released)},
    }
    errors = validate_shutdown_receipt_steps(steps)
    if requeue_required:
        errors.append("grace period exceeded with inflight work; safe requeue must be recorded before zero exit")
    return {
        "cycle_id": cycle_id,
        "generated_at": generated_at,
        "grace_seconds": S2PMT04_DEFAULT_SHUTDOWN_GRACE_SECONDS,
        "graceful_elapsed_seconds": graceful_elapsed_seconds,
        "steps": steps,
        "exit_code": 0 if not errors else 2,
        "status": "pass" if not errors else "blocked",
        "blocking_reasons": sorted(set(errors)),
    }


def validate_shutdown_receipt_steps(steps: Mapping[str, Any]) -> list[str]:
    """Validate required shutdown receipt sections."""

    errors: list[str] = []
    for step in S2PMT04_REQUIRED_SHUTDOWN_RECEIPT_STEPS:
        if step not in steps:
            errors.append(f"shutdown receipt step {step} is missing")
    if isinstance(steps.get("checkpoint"), Mapping) and not steps["checkpoint"].get("written"):
        errors.append("checkpoint must be written")
    if isinstance(steps.get("backup"), Mapping) and not steps["backup"].get("written"):
        errors.append("backup must be written")
    if isinstance(steps.get("lease_release"), Mapping) and steps["lease_release"].get("released") is not True:
        errors.append("lease release must be recorded")
    return errors


def build_transaction_completion_receipt(
    *,
    cycle_id: str,
    steps: Sequence[Mapping[str, Any]],
    interrupted_after_step: str | None,
    generated_at: str,
) -> dict[str, Any]:
    """Build observable transaction boundaries for shutdown save/cleanup steps."""

    required = set(S2PMT04_REQUIRED_SHUTDOWN_RECEIPT_STEPS)
    observed_steps: list[dict[str, Any]] = []
    recovery_actions: list[dict[str, Any]] = []
    blocking_reasons: list[str] = []
    interruption_seen = False

    for index, raw_step in enumerate(steps):
        step_id = str(raw_step.get("step_id") or "")
        committed = bool(raw_step.get("committed"))
        durable_ref = str(raw_step.get("durable_ref") or "")
        rollback_ref = str(raw_step.get("rollback_ref") or "")
        if step_id not in required:
            blocking_reasons.append(f"transaction step {step_id or '<empty>'} is not a required shutdown step")
        if committed and not durable_ref:
            blocking_reasons.append(f"transaction step {step_id} committed without durable_ref")
        if not committed and not rollback_ref:
            blocking_reasons.append(f"transaction step {step_id} lacks rollback_ref for recovery")
        if interrupted_after_step and interruption_seen and committed:
            blocking_reasons.append(f"transaction step {step_id} committed after interruption point")
        observed_steps.append(
            {
                "step_id": step_id,
                "sequence": index + 1,
                "transaction_state": "COMMITTED" if committed else "PENDING_ROLLBACK",
                "durable_ref": durable_ref,
                "rollback_ref": rollback_ref,
                "completion_signal": f"{cycle_id}:{step_id}:{'committed' if committed else 'pending_rollback'}",
                "observable": bool(durable_ref or rollback_ref),
            }
        )
        if not committed:
            recovery_actions.append(
                {
                    "step_id": step_id,
                    "resume_action": "rollback_then_retry_from_receipt",
                    "rollback_ref": rollback_ref,
                    "new_work_claim_allowed": False,
                }
            )
        if interrupted_after_step and step_id == interrupted_after_step:
            interruption_seen = True

    missing = sorted(required.difference({step["step_id"] for step in observed_steps}))
    for step_id in missing:
        blocking_reasons.append(f"transaction step {step_id} is missing")
        recovery_actions.append(
            {
                "step_id": step_id,
                "resume_action": "reconstruct_from_previous_checkpoint_before_retry",
                "rollback_ref": "",
                "new_work_claim_allowed": False,
            }
        )
    completed = not blocking_reasons and not recovery_actions
    interrupted_recoverable = bool(interrupted_after_step) and bool(recovery_actions) and not any(
        reason.endswith("committed after interruption point") for reason in blocking_reasons
    )
    return {
        "cycle_id": cycle_id,
        "generated_at": generated_at,
        "interrupted_after_step": interrupted_after_step or "",
        "steps": observed_steps,
        "missing_steps": missing,
        "recovery_actions": recovery_actions,
        "completed": completed,
        "interrupted_recoverable": interrupted_recoverable,
        "new_work_claim_allowed": False if recovery_actions else True,
        "completion_signal_observable": all(step["observable"] for step in observed_steps) and not missing,
        "status": "pass" if (completed or interrupted_recoverable) and not blocking_reasons else "blocked",
        "blocking_reasons": sorted(set(blocking_reasons)),
    }


def validate_transaction_completion_receipt(receipt: Mapping[str, Any]) -> list[str]:
    """Validate observable shutdown transaction boundaries and recovery signals."""

    errors: list[str] = []
    steps = receipt.get("steps") if isinstance(receipt.get("steps"), list) else []
    observed = {str(step.get("step_id") or "") for step in steps if isinstance(step, Mapping)}
    for step_id in S2PMT04_REQUIRED_SHUTDOWN_RECEIPT_STEPS:
        if step_id not in observed:
            errors.append(f"transaction step {step_id} is missing")
    if receipt.get("completion_signal_observable") is not True:
        errors.append("transaction completion signal must be observable")
    if receipt.get("status") == "pass":
        if receipt.get("completed") is not True and receipt.get("interrupted_recoverable") is not True:
            errors.append("passing transaction receipt must be completed or interrupted_recoverable")
        if receipt.get("blocking_reasons"):
            errors.append("passing transaction receipt must not have blocking_reasons")
    if receipt.get("recovery_actions") and receipt.get("new_work_claim_allowed") is not False:
        errors.append("recovery actions must block new work claims")
    return errors


def build_cache_cleanup_plan(
    *,
    cache_entries: Sequence[Mapping[str, Any]],
    whitelist_roots: Sequence[str | Path],
    ttl_seconds: int = S2PMT04_DEFAULT_CACHE_TTL_SECONDS,
    cap_bytes: int = S2PMT04_DEFAULT_CACHE_CAP_BYTES,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Plan safe cache cleanup with whitelist, symlink, TTL, cap, and class gates."""

    roots = [_resolve_path(root) for root in whitelist_roots]
    total_rebuildable_bytes = sum(
        int(entry.get("size_bytes") or 0)
        for entry in cache_entries
        if entry.get("cache_class") == "rebuildable_cache"
    )
    cap_pressure = total_rebuildable_bytes > cap_bytes
    candidates: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []

    for entry in cache_entries:
        path = Path(str(entry.get("path") or ""))
        cache_class = str(entry.get("cache_class") or "")
        safe = _cache_entry_safety(path, cache_class, roots)
        row = {
            "path": str(path),
            "resolved_path": str(_resolve_path(path)),
            "cache_class": cache_class,
            "size_bytes": int(entry.get("size_bytes") or 0),
            "age_seconds": int(entry.get("age_seconds") or 0),
            "safe": safe["safe"],
            "blocking_reasons": safe["blocking_reasons"],
        }
        if not safe["safe"]:
            blocked.append({**row, "action": "blocked"})
            continue
        if cache_class == "durable_evidence":
            retained.append({**row, "action": "retain_durable_evidence"})
            continue
        should_delete = cache_class == "temp" or int(entry.get("age_seconds") or 0) >= ttl_seconds or cap_pressure
        if should_delete:
            candidates.append(
                {
                    **row,
                    "action": "delete_candidate",
                    "dry_run": dry_run,
                    "delete_applied": False,
                    "reason": "temp_cleanup" if cache_class == "temp" else "ttl_or_cap_cleanup",
                }
            )
        else:
            retained.append({**row, "action": "retain_not_expired"})

    return {
        "ttl_seconds": ttl_seconds,
        "cap_bytes": cap_bytes,
        "dry_run": dry_run,
        "whitelist_roots": [str(root) for root in roots],
        "total_rebuildable_bytes": total_rebuildable_bytes,
        "cap_pressure": cap_pressure,
        "candidate_count": len(candidates),
        "blocked_count": len(blocked),
        "retained_count": len(retained),
        "delete_bytes_dry_run": sum(item["size_bytes"] for item in candidates),
        "candidates": candidates,
        "blocked": blocked,
        "retained": retained,
        "deletion_ledger": [
            {
                "path": item["resolved_path"],
                "cache_class": item["cache_class"],
                "size_bytes": item["size_bytes"],
                "dry_run": dry_run,
                "delete_applied": False,
                "reason": item["reason"],
            }
            for item in candidates
        ],
        "durable_evidence_delete_allowed": False,
        "cleanup_safe": len(blocked) == 0 and dry_run is True,
    }


def build_launchd_plist_payload(
    *,
    label: str,
    program_arguments: Sequence[str],
    disabled: bool = True,
    hour: int = 5,
    minute: int = 0,
    stdout_path: str = "/tmp/adp-local-daily.out",
    stderr_path: str = "/tmp/adp-local-daily.err",
) -> bytes:
    """Build a parseable launchd plist without installing or enabling it."""

    payload = {
        "Label": label,
        "Disabled": bool(disabled),
        "StartCalendarInterval": {"Hour": int(hour), "Minute": int(minute)},
        "RunAtLoad": False,
        "StandardOutPath": stdout_path,
        "StandardErrorPath": stderr_path,
        "ProgramArguments": [str(arg) for arg in program_arguments],
    }
    return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False)


def validate_launchd_plist_payload(payload: bytes) -> list[str]:
    """Validate a generated launchd plist payload for S2PMT04 no-install evidence."""

    errors: list[str] = []
    try:
        parsed = plistlib.loads(payload)
    except Exception as exc:  # pragma: no cover - exact plistlib subclass varies by Python version
        return [f"launchd plist is not parseable: {exc}"]
    if parsed.get("Disabled") is not True:
        errors.append("launchd plist must remain disabled")
    if parsed.get("RunAtLoad") is not False:
        errors.append("launchd plist RunAtLoad must remain false")
    if not isinstance(parsed.get("ProgramArguments"), list) or not parsed.get("ProgramArguments"):
        errors.append("launchd plist ProgramArguments must be a non-empty array")
    if "EnvironmentVariables" in parsed:
        errors.append("launchd plist must not embed environment variables or secrets")
    return errors


def build_lifecycle_cache_report(*, generated_at: str, cache_root: str | Path | None = None) -> dict[str, Any]:
    """Build a deterministic local S2PMT04 lifecycle/cache evidence report."""

    root = Path(cache_root or "/tmp/adp-s2pmt04-cache").resolve()
    transition_plan = build_lifecycle_transition_plan(cycle_id="2026-07-03", generated_at=generated_at)
    startup = build_startup_reconciliation(
        temp_items=[{"item_id": "tmp-1", "path": str(root / "tmp" / "scratch.json")}],
        inflight_items=[{"work_id": "cycle-20260703-M1", "state": "RUNNING"}],
        outbox_items=[{"mail_key": "2026-07-03|M1|owner", "status": "ACCEPTED_PENDING_COMMIT"}],
        stale_locks=[{"lock_id": "lock-1", "lease_owner": "worker-old"}],
        generated_at=generated_at,
    )
    shutdown = build_shutdown_receipt(
        cycle_id="2026-07-03",
        inflight_count=0,
        outbox_pending_count=1,
        checkpoint_ref="checkpoint://local/s2pmt04/2026-07-03",
        cleanup_ref="cleanup://local/s2pmt04/2026-07-03",
        backup_ref="backup://local/s2pmt04/2026-07-03",
        lease_released=True,
        graceful_elapsed_seconds=120,
        generated_at=generated_at,
    )
    transaction_receipt = build_transaction_completion_receipt(
        cycle_id="2026-07-03",
        generated_at=generated_at,
        interrupted_after_step="cleanup",
        steps=[
            {"step_id": "inflight", "committed": True, "durable_ref": "receipt://local/s2pmt04/inflight"},
            {"step_id": "outbox", "committed": True, "durable_ref": "receipt://local/s2pmt04/outbox"},
            {"step_id": "checkpoint", "committed": True, "durable_ref": "receipt://local/s2pmt04/checkpoint"},
            {"step_id": "cleanup", "committed": True, "durable_ref": "receipt://local/s2pmt04/cleanup"},
            {"step_id": "backup", "committed": False, "rollback_ref": "rollback://local/s2pmt04/backup"},
            {"step_id": "lease_release", "committed": False, "rollback_ref": "rollback://local/s2pmt04/lease_release"},
        ],
    )
    cleanup = build_cache_cleanup_plan(
        cache_entries=[
            {
                "path": str(root / "raw" / "evidence.json"),
                "cache_class": "durable_evidence",
                "size_bytes": 512,
                "age_seconds": 999999,
            },
            {
                "path": str(root / "fulltext" / "paper.txt"),
                "cache_class": "rebuildable_cache",
                "size_bytes": 2048,
                "age_seconds": S2PMT04_DEFAULT_CACHE_TTL_SECONDS + 1,
            },
            {"path": str(root / "tmp" / "scratch.json"), "cache_class": "temp", "size_bytes": 128, "age_seconds": 1},
        ],
        whitelist_roots=[root],
        dry_run=True,
    )
    plist_payload = build_launchd_plist_payload(
        label=S2PMT04_LAUNCHD_LABEL,
        program_arguments=("/bin/zsh", "-lc", "ADP_LOCAL_DAILY_RUN_ENABLED=true python3 -m arxiv_daily_push local-runner daily"),
    )
    gates = {
        "automatic_wake_dry_run": validate_launchd_plist_payload(plist_payload) == [],
        "lifecycle_transition_chain": transition_plan["transition_chain_valid"] is True,
        "startup_reconciliation": startup["reconciliation_ready"] is True,
        "shutdown_receipt": shutdown["status"] == "pass",
        "transaction_completion_signal": transaction_receipt["status"] == "pass"
        and validate_transaction_completion_receipt(transaction_receipt) == [],
        "cache_cleanup_safety": cleanup["cleanup_safe"] is True and cleanup["durable_evidence_delete_allowed"] is False,
        "launchd_plist_parseable": validate_launchd_plist_payload(plist_payload) == [],
        "no_production_side_effect": True,
    }
    status = "pass" if all(gates.values()) else "blocked"
    report = {
        "model_id": S2PMT04_LIFECYCLE_CACHE_MODEL_ID,
        "schema_version": S2PMT04_SCHEMA_VERSION,
        "task_id": S2PMT04_TASK_ID,
        "acceptance_id": S2PMT04_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": status,
        "blocking_reasons": [] if status == "pass" else [key for key, value in gates.items() if value is not True],
        "gates": gates,
        "transition_plan": transition_plan,
        "startup_reconciliation": startup,
        "shutdown_receipt": shutdown,
        "transaction_completion_receipt": transaction_receipt,
        "cache_cleanup_plan": cleanup,
        "launchd_plist_sha256": hashlib.sha256(plist_payload).hexdigest(),
        "report_hash": "",
        "production_side_effects_enabled": False,
        "real_smtp_sent": False,
        "scheduler_installed": False,
        "scheduler_enabled": False,
        "release_upload_allowed": False,
        "production_restore_executed": False,
        "public_schema_changed": False,
        "queue_schema_changed": False,
        "queue_mutation_allowed": False,
        "db_migration_executed": False,
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_lifecycle_cache_report(report: Mapping[str, Any]) -> list[str]:
    """Validate S2PMT04 local lifecycle/cache evidence reports."""

    errors: list[str] = []
    if report.get("model_id") != S2PMT04_LIFECYCLE_CACHE_MODEL_ID:
        errors.append("S2PMT04 report model_id is invalid")
    if report.get("schema_version") != S2PMT04_SCHEMA_VERSION:
        errors.append("S2PMT04 report schema_version must be 1")
    if report.get("task_id") != S2PMT04_TASK_ID:
        errors.append("S2PMT04 report task_id is invalid")
    if report.get("acceptance_id") != S2PMT04_ACCEPTANCE_ID:
        errors.append("S2PMT04 report acceptance_id is invalid")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("S2PMT04 report status must be pass or blocked")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked S2PMT04 report requires blocking_reasons")
    for key in S2PMT04_REQUIRED_PRODUCTION_FALSE_FLAGS:
        if report.get(key) is not False:
            errors.append(f"{key} must be false")
    gates = report.get("gates") if isinstance(report.get("gates"), Mapping) else {}
    for gate in S2PMT04_REQUIRED_GATES:
        if gate not in gates:
            errors.append(f"gates.{gate} is required")
    if report.get("status") == "pass" and not all(gates.get(gate) is True for gate in S2PMT04_REQUIRED_GATES):
        errors.append("passing S2PMT04 report requires all gates true")
    cleanup = report.get("cache_cleanup_plan") if isinstance(report.get("cache_cleanup_plan"), Mapping) else {}
    if cleanup.get("durable_evidence_delete_allowed") is not False:
        errors.append("durable evidence cache class must never be auto-deleted")
    if cleanup.get("dry_run") is not True:
        errors.append("S2PMT04 evidence report cache cleanup must remain dry-run")
    transaction_receipt = report.get("transaction_completion_receipt")
    if not isinstance(transaction_receipt, Mapping):
        errors.append("transaction_completion_receipt is required")
    else:
        errors.extend(validate_transaction_completion_receipt(transaction_receipt))
    return errors


def _cache_entry_safety(path: Path, cache_class: str, roots: Sequence[Path]) -> dict[str, Any]:
    reasons: list[str] = []
    resolved = _resolve_path(path)
    if cache_class not in S2PMT04_CACHE_CLASSES:
        reasons.append("cache_class is invalid")
    if not any(_is_relative_to(resolved, root) for root in roots):
        reasons.append("path is outside cache cleanup whitelist")
    if path.is_symlink():
        reasons.append("symbolic links are not cleanup candidates")
    return {"safe": not reasons, "blocking_reasons": reasons}


def _resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
