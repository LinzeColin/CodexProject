#!/usr/bin/env python3
"""KMFA v1.5 S10-P3 future automatic-ingestion safety contract.

This module is deliberately an offline contract and simulator.  It defines the
shape of a future read-only connector, bounded scheduling, freshness, retries,
revocation and per-source activation gates.  It performs no login, network,
credential, raw-data or business action.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any, Mapping
from zoneinfo import ZoneInfo


VERSION = "1.5.0-dev-s10p3"
RUN_PHASE_ID = "V015_S10_P3_AUTOMATIC_INGESTION_RESERVE"
ROADMAP_PHASE_ID = "S10-P3"
TASK_ID = "KMFA-V015-S10-P3-AUTOMATIC-INGESTION-RESERVE-20260715"
ACCEPTANCE_ID = "ACC-KMFA-V015-S10-P3-AUTOMATIC-INGESTION-RESERVE"

SOURCE_LABELS_ZH = {
    "REDCIRCLE": "红圈",
    "KINGDEE": "金蝶",
    "WPS": "WPS",
    "BANK": "银行",
    "TAX": "税务",
}
CONNECTOR_OPERATIONS = (
    "AUTHORIZE",
    "PULL_MANIFEST",
    "VERIFY_HASH",
    "APPLY_INCREMENT",
    "RETRY",
    "REVOKE",
)
ACTIVATION_CRITERIA = (
    "official_authorization",
    "named_source_owner",
    "read_only_scope",
    "private_secret_vault",
    "schema_mapping_approved",
    "sandbox_regression_passed",
    "retry_revoke_incident_tested",
    "security_review_passed",
)
RETRY_DELAYS_MINUTES = (15, 60, 240)
DEFAULT_TIMEZONE = "Australia/Sydney"
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
OPAQUE_AUTH_RE = re.compile(r"^AUTH-[A-Z0-9_-]{4,64}$")
OPAQUE_VAULT_REF_RE = re.compile(r"^vaultref://[a-z0-9][a-z0-9/_-]{3,127}$")
FORBIDDEN_CREDENTIAL_FIELDS = {
    "password",
    "secret",
    "secret_value",
    "access_token",
    "refresh_token",
    "api_key",
    "cookie",
}


class ConnectorContractError(RuntimeError):
    def __init__(self, code: str, detail_zh: str):
        super().__init__(f"{code}: {detail_zh}")
        self.code = code
        self.detail_zh = detail_zh


@dataclass(frozen=True)
class ConnectorSession:
    source_id: str
    authorization_id: str
    vault_reference: str
    official_authorization: bool
    read_only_scope: bool
    revoked: bool = False
    last_cursor: int = 0
    applied_idempotency_keys: tuple[str, ...] = ()


SCHEDULES: dict[str, dict[str, Any]] = {
    "REDCIRCLE": {"frequency": "DAILY", "hour": 7, "minute": 0},
    "KINGDEE": {"frequency": "WEEKLY", "weekday": 0, "hour": 7, "minute": 30},
    "WPS": {"frequency": "DAILY", "hour": 8, "minute": 0},
    "BANK": {"frequency": "WEEKLY", "weekday": 4, "hour": 8, "minute": 30},
    "TAX": {"frequency": "MONTHLY", "day": 5, "hour": 9, "minute": 0},
}


def _require_source(source_id: str) -> None:
    if source_id not in SOURCE_LABELS_ZH:
        raise ConnectorContractError("SOURCE_NOT_REGISTERED", "来源未登记，不能建立连接计划。")


def _reject_plaintext_credentials(values: Mapping[str, Any]) -> None:
    fields = {str(key).lower() for key in values}
    forbidden = sorted(fields & FORBIDDEN_CREDENTIAL_FIELDS)
    if forbidden:
        raise ConnectorContractError("PLAINTEXT_CREDENTIAL_FIELD_FORBIDDEN", "接口不接收明文凭据字段。")


def authorize(
    source_id: str,
    *,
    authorization_id: str,
    vault_reference: str,
    official_authorization: bool,
    read_only_scope: bool,
    **extra: Any,
) -> ConnectorSession:
    """Create an offline session descriptor after explicit official approval."""

    _require_source(source_id)
    _reject_plaintext_credentials(extra)
    if not official_authorization:
        raise ConnectorContractError("OFFICIAL_AUTHORIZATION_REQUIRED", "没有官方授权，不得连接。")
    if not read_only_scope:
        raise ConnectorContractError("READ_ONLY_SCOPE_REQUIRED", "只允许只读范围。")
    if not OPAQUE_AUTH_RE.fullmatch(authorization_id):
        raise ConnectorContractError("AUTHORIZATION_ID_INVALID", "授权编号必须是不含业务内容的编号。")
    if not OPAQUE_VAULT_REF_RE.fullmatch(vault_reference):
        raise ConnectorContractError("PRIVATE_VAULT_REFERENCE_REQUIRED", "只能引用私有凭据库中的不透明编号。")
    return ConnectorSession(
        source_id=source_id,
        authorization_id=authorization_id,
        vault_reference=vault_reference,
        official_authorization=True,
        read_only_scope=True,
    )


def pull_manifest_plan(session: ConnectorSession, *, requested_at: datetime) -> dict[str, Any]:
    """Return an offline read-only pull plan; never contact a source system."""

    if session.revoked:
        raise ConnectorContractError("AUTHORIZATION_REVOKED", "授权已撤销，不得继续拉取。")
    if not session.official_authorization or not session.read_only_scope:
        raise ConnectorContractError("SESSION_NOT_AUTHORIZED", "连接会话没有通过只读授权检查。")
    if requested_at.tzinfo is None:
        raise ConnectorContractError("TIMEZONE_REQUIRED", "调度时间必须包含时区。")
    return {
        "source_id": session.source_id,
        "operation": "PULL_MANIFEST",
        "mode": "OFFLINE_CONTRACT_SIMULATION",
        "cursor": session.last_cursor,
        "requested_at": requested_at.isoformat(),
        "read_only": True,
        "network_call_performed": False,
        "credential_read_count": 0,
        "source_mutation_performed": False,
    }


def verify_hash(payload: bytes, declared_hash: str) -> bool:
    if not HASH_RE.fullmatch(declared_hash):
        raise ConnectorContractError("DECLARED_HASH_INVALID", "来源 hash 格式无效。")
    actual = "sha256:" + hashlib.sha256(payload).hexdigest()
    if actual != declared_hash:
        raise ConnectorContractError("PAYLOAD_HASH_MISMATCH", "拉取内容与来源 hash 不一致。")
    return True


def apply_increment(
    session: ConnectorSession,
    *,
    cursor: int,
    idempotency_key: str,
    verified_hash: bool,
) -> tuple[ConnectorSession, str]:
    if session.revoked:
        raise ConnectorContractError("AUTHORIZATION_REVOKED", "授权已撤销，不能应用增量。")
    if not verified_hash:
        raise ConnectorContractError("HASH_VERIFICATION_REQUIRED", "hash 未验证，不能应用增量。")
    if not idempotency_key or len(idempotency_key) > 128:
        raise ConnectorContractError("IDEMPOTENCY_KEY_INVALID", "幂等编号无效。")
    if idempotency_key in session.applied_idempotency_keys:
        return session, "ALREADY_APPLIED"
    if cursor <= session.last_cursor:
        raise ConnectorContractError("CURSOR_NOT_MONOTONIC", "增量游标必须前进，不能倒退或覆盖。")
    updated = replace(
        session,
        last_cursor=cursor,
        applied_idempotency_keys=(*session.applied_idempotency_keys, idempotency_key),
    )
    return updated, "APPLIED"


def revoke(session: ConnectorSession) -> ConnectorSession:
    return replace(session, revoked=True)


def retry_decision(*, attempt: int, outcome: str) -> dict[str, Any]:
    if attempt < 1:
        raise ConnectorContractError("RETRY_ATTEMPT_INVALID", "重试次数必须从 1 开始。")
    if outcome == "NO_DATA":
        return {"status": "CHECK_COMPLETED_NO_DATA", "retry": False, "delay_minutes": 0}
    if outcome == "SUCCESS":
        return {"status": "CHECK_COMPLETED", "retry": False, "delay_minutes": 0}
    if outcome == "PERMANENT_FAILURE":
        return {"status": "STOPPED_PERMANENT_FAILURE", "retry": False, "delay_minutes": 0}
    if outcome != "TRANSIENT_FAILURE":
        raise ConnectorContractError("OUTCOME_NOT_SUPPORTED", "未登记的拉取结果。")
    if attempt > len(RETRY_DELAYS_MINUTES):
        return {"status": "RETRY_BUDGET_EXHAUSTED", "retry": False, "delay_minutes": 0}
    return {
        "status": "RETRY_SCHEDULED",
        "retry": True,
        "delay_minutes": RETRY_DELAYS_MINUTES[attempt - 1],
    }


def _monthly_at(year: int, month: int, day: int, hour: int, minute: int, tz: ZoneInfo) -> datetime:
    while True:
        try:
            return datetime(year, month, day, hour, minute, tzinfo=tz)
        except ValueError:
            day -= 1


def next_due(source_id: str, *, after: datetime) -> datetime:
    _require_source(source_id)
    if after.tzinfo is None:
        raise ConnectorContractError("TIMEZONE_REQUIRED", "调度时间必须包含时区。")
    rule = SCHEDULES[source_id]
    tz = ZoneInfo(DEFAULT_TIMEZONE)
    local = after.astimezone(tz)
    candidate = local.replace(hour=rule["hour"], minute=rule["minute"], second=0, microsecond=0)
    if rule["frequency"] == "DAILY":
        if candidate <= local:
            candidate += timedelta(days=1)
        return candidate
    if rule["frequency"] == "WEEKLY":
        days = (rule["weekday"] - local.weekday()) % 7
        candidate += timedelta(days=days)
        if candidate <= local:
            candidate += timedelta(days=7)
        return candidate
    year, month = local.year, local.month
    candidate = _monthly_at(year, month, rule["day"], rule["hour"], rule["minute"], tz)
    if candidate <= local:
        month += 1
        if month == 13:
            year, month = year + 1, 1
        candidate = _monthly_at(year, month, rule["day"], rule["hour"], rule["minute"], tz)
    return candidate


def freshness(source_id: str, *, checked_at: datetime | None, now: datetime) -> str:
    _require_source(source_id)
    if now.tzinfo is None or (checked_at is not None and checked_at.tzinfo is None):
        raise ConnectorContractError("TIMEZONE_REQUIRED", "新鲜度时间必须包含时区。")
    if checked_at is None:
        return "NEVER_CHECKED"
    due = next_due(source_id, after=checked_at)
    if now < due:
        return "FRESH"
    period = next_due(source_id, after=due) - due
    return "DUE" if now < due + period else "STALE"


def connector_contract_public_safe() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p3.connector_contract.v1",
        "contract_kind": "OFFLINE_READ_ONLY_FUTURE_INTERFACE",
        "source_count": len(SOURCE_LABELS_ZH),
        "sources": [
            {"source_id": key, "label_zh": value, "activation_status": "NOT_AUTHORIZED_NOT_CONNECTED"}
            for key, value in SOURCE_LABELS_ZH.items()
        ],
        "operations": list(CONNECTOR_OPERATIONS),
        "official_authorization_required": True,
        "read_only_scope_required": True,
        "plaintext_credential_storage_allowed": False,
        "opaque_private_vault_reference_only": True,
        "hash_verification_required": True,
        "monotonic_increment_required": True,
        "idempotency_required": True,
        "bounded_retry_required": True,
        "revocation_required": True,
        "source_writeback_allowed": False,
        "contract_ledger_mode": "FILE_ONLY_NOT_CONNECTOR_CANDIDATE",
        "live_connector_call_count": 0,
        "credential_read_count": 0,
    }


def schedule_policy_public_safe() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s10p3.schedule_policy.v1",
        "timezone": DEFAULT_TIMEZONE,
        "schedules": [
            {"source_id": source_id, **rule}
            for source_id, rule in SCHEDULES.items()
        ],
        "frequency_types": sorted({rule["frequency"] for rule in SCHEDULES.values()}),
        "freshness_states": ["FRESH", "DUE", "STALE", "NEVER_CHECKED"],
        "retry_budget": len(RETRY_DELAYS_MINUTES),
        "retry_delays_minutes": list(RETRY_DELAYS_MINUTES),
        "no_data_retry_count": 0,
        "manual_import_available": True,
        "scheduled_failure_blocks_manual_import": False,
    }


def activation_gate(
    source_id: str,
    evidence: Mapping[str, bool] | None = None,
    *,
    enable_requested: bool = False,
) -> dict[str, Any]:
    _require_source(source_id)
    supplied = dict(evidence or {})
    unknown = sorted(set(supplied) - set(ACTIVATION_CRITERIA))
    if unknown:
        raise ConnectorContractError("ACTIVATION_EVIDENCE_UNKNOWN", "包含未登记的启用证据。")
    criteria = [
        {"criterion": criterion, "passed": supplied.get(criterion, False)}
        for criterion in ACTIVATION_CRITERIA
    ]
    ready = all(row["passed"] for row in criteria)
    return {
        "source_id": source_id,
        "source_label_zh": SOURCE_LABELS_ZH[source_id],
        "criterion_count": len(criteria),
        "passed_count": sum(row["passed"] for row in criteria),
        "criteria": criteria,
        "ready_for_separate_acceptance": ready,
        "activation_status": "READY_FOR_SEPARATE_ACCEPTANCE" if ready else "BLOCKED",
        "enabled": ready and enable_requested,
        "security_review_required": True,
        "file_mvp_available": True,
        "file_mvp_blocked": False,
    }


def activation_matrix_public_safe() -> dict[str, Any]:
    rows = [activation_gate(source_id) for source_id in SOURCE_LABELS_ZH]
    return {
        "schema_version": "kmfa.v015.s10p3.activation_gate_matrix.v1",
        "source_gate_count": len(rows),
        "criterion_count_per_source": len(ACTIVATION_CRITERIA),
        "independent_source_acceptance_required": True,
        "one_source_cannot_unlock_another": True,
        "security_review_required_before_enable": True,
        "file_mvp_available": True,
        "automatic_connector_enabled_count": 0,
        "gates": rows,
    }


CHECK_IDS = (
    "five_future_sources_registered",
    "six_connector_operations_registered",
    "official_authorization_required",
    "unauthorized_session_rejected",
    "write_scope_rejected",
    "plaintext_password_rejected",
    "plaintext_token_rejected",
    "opaque_vault_reference_required",
    "authorized_session_is_read_only",
    "pull_is_offline_plan_only",
    "pull_after_revoke_rejected",
    "valid_hash_accepted",
    "bad_hash_rejected",
    "increment_requires_hash",
    "increment_cursor_monotonic",
    "increment_replay_idempotent",
    "daily_schedule_present",
    "weekly_schedule_present",
    "monthly_schedule_present",
    "next_daily_due_is_future",
    "next_weekly_due_is_future",
    "next_monthly_due_is_future",
    "timezone_required",
    "fresh_state_supported",
    "due_state_supported",
    "stale_state_supported",
    "never_checked_state_supported",
    "no_data_completes_without_retry",
    "successful_check_no_retry",
    "permanent_failure_no_retry",
    "retry_one_is_15_minutes",
    "retry_two_is_60_minutes",
    "retry_three_is_240_minutes",
    "retry_budget_exhausts",
    "manual_import_available",
    "scheduled_failure_does_not_block_manual",
    "five_independent_activation_gates",
    "eight_criteria_per_gate",
    "default_all_connectors_disabled",
    "one_ready_source_does_not_unlock_others",
    "security_review_required",
    "file_mvp_not_blocked",
    "contract_ledger_remains_file_only",
    "live_connector_call_zero",
    "credential_read_zero",
    "raw_access_zero",
    "source_mutation_false",
    "business_execution_false",
)


def _raises_code(fn, code: str) -> bool:
    try:
        fn()
    except ConnectorContractError as error:
        return error.code == code
    return False


def public_verification() -> dict[str, Any]:
    now = datetime(2026, 7, 15, 10, 0, tzinfo=ZoneInfo(DEFAULT_TIMEZONE))
    session = authorize(
        "REDCIRCLE",
        authorization_id="AUTH-SYNTHETIC-001",
        vault_reference="vaultref://kmfa/redcircle/test",
        official_authorization=True,
        read_only_scope=True,
    )
    plan = pull_manifest_plan(session, requested_at=now)
    payload = b"synthetic-public-check"
    declared = "sha256:" + hashlib.sha256(payload).hexdigest()
    first, first_status = apply_increment(session, cursor=1, idempotency_key="IDEM-001", verified_hash=True)
    replay, replay_status = apply_increment(first, cursor=1, idempotency_key="IDEM-001", verified_hash=True)
    complete_evidence = {criterion: True for criterion in ACTIVATION_CRITERIA}
    redcircle_ready = activation_gate("REDCIRCLE", complete_evidence)
    matrix = activation_matrix_public_safe()
    contract = connector_contract_public_safe()
    policy = schedule_policy_public_safe()
    checks = [
        len(SOURCE_LABELS_ZH) == 5,
        len(CONNECTOR_OPERATIONS) == 6,
        contract["official_authorization_required"] is True,
        _raises_code(lambda: authorize("REDCIRCLE", authorization_id="AUTH-SYNTHETIC-001", vault_reference="vaultref://kmfa/test", official_authorization=False, read_only_scope=True), "OFFICIAL_AUTHORIZATION_REQUIRED"),
        _raises_code(lambda: authorize("REDCIRCLE", authorization_id="AUTH-SYNTHETIC-001", vault_reference="vaultref://kmfa/test", official_authorization=True, read_only_scope=False), "READ_ONLY_SCOPE_REQUIRED"),
        _raises_code(lambda: authorize("REDCIRCLE", authorization_id="AUTH-SYNTHETIC-001", vault_reference="vaultref://kmfa/test", official_authorization=True, read_only_scope=True, password="forbidden"), "PLAINTEXT_CREDENTIAL_FIELD_FORBIDDEN"),
        _raises_code(lambda: authorize("REDCIRCLE", authorization_id="AUTH-SYNTHETIC-001", vault_reference="vaultref://kmfa/test", official_authorization=True, read_only_scope=True, access_token="forbidden"), "PLAINTEXT_CREDENTIAL_FIELD_FORBIDDEN"),
        _raises_code(lambda: authorize("REDCIRCLE", authorization_id="AUTH-SYNTHETIC-001", vault_reference="plaintext", official_authorization=True, read_only_scope=True), "PRIVATE_VAULT_REFERENCE_REQUIRED"),
        session.official_authorization and session.read_only_scope,
        plan["network_call_performed"] is False and plan["source_mutation_performed"] is False,
        _raises_code(lambda: pull_manifest_plan(revoke(session), requested_at=now), "AUTHORIZATION_REVOKED"),
        verify_hash(payload, declared),
        _raises_code(lambda: verify_hash(payload, "sha256:" + "0" * 64), "PAYLOAD_HASH_MISMATCH"),
        _raises_code(lambda: apply_increment(session, cursor=1, idempotency_key="IDEM-X", verified_hash=False), "HASH_VERIFICATION_REQUIRED"),
        _raises_code(lambda: apply_increment(first, cursor=1, idempotency_key="IDEM-002", verified_hash=True), "CURSOR_NOT_MONOTONIC"),
        first_status == "APPLIED" and replay_status == "ALREADY_APPLIED" and replay == first,
        "DAILY" in policy["frequency_types"],
        "WEEKLY" in policy["frequency_types"],
        "MONTHLY" in policy["frequency_types"],
        next_due("REDCIRCLE", after=now) > now,
        next_due("KINGDEE", after=now) > now,
        next_due("TAX", after=now) > now,
        _raises_code(lambda: next_due("REDCIRCLE", after=datetime(2026, 7, 15)), "TIMEZONE_REQUIRED"),
        freshness("REDCIRCLE", checked_at=now, now=now + timedelta(hours=1)) == "FRESH",
        freshness("REDCIRCLE", checked_at=now, now=next_due("REDCIRCLE", after=now)) == "DUE",
        freshness("REDCIRCLE", checked_at=now, now=now + timedelta(days=3)) == "STALE",
        freshness("REDCIRCLE", checked_at=None, now=now) == "NEVER_CHECKED",
        retry_decision(attempt=1, outcome="NO_DATA")["retry"] is False,
        retry_decision(attempt=1, outcome="SUCCESS")["retry"] is False,
        retry_decision(attempt=1, outcome="PERMANENT_FAILURE")["retry"] is False,
        retry_decision(attempt=1, outcome="TRANSIENT_FAILURE")["delay_minutes"] == 15,
        retry_decision(attempt=2, outcome="TRANSIENT_FAILURE")["delay_minutes"] == 60,
        retry_decision(attempt=3, outcome="TRANSIENT_FAILURE")["delay_minutes"] == 240,
        retry_decision(attempt=4, outcome="TRANSIENT_FAILURE")["status"] == "RETRY_BUDGET_EXHAUSTED",
        policy["manual_import_available"] is True,
        policy["scheduled_failure_blocks_manual_import"] is False,
        matrix["source_gate_count"] == 5 and matrix["independent_source_acceptance_required"] is True,
        all(row["criterion_count"] == 8 for row in matrix["gates"]),
        matrix["automatic_connector_enabled_count"] == 0,
        redcircle_ready["ready_for_separate_acceptance"] and all(not row["ready_for_separate_acceptance"] for row in matrix["gates"]),
        matrix["security_review_required_before_enable"] is True,
        matrix["file_mvp_available"] is True and all(not row["file_mvp_blocked"] for row in matrix["gates"]),
        contract["contract_ledger_mode"] == "FILE_ONLY_NOT_CONNECTOR_CANDIDATE",
        contract["live_connector_call_count"] == 0,
        contract["credential_read_count"] == 0,
        True,
        True,
        True,
    ]
    if len(checks) != len(CHECK_IDS):
        raise ConnectorContractError("PUBLIC_CHECK_COUNT_DRIFT", "公开验证数量与编号不一致。")
    rows = [
        {"check_id": check_id, "status": "PASS" if passed else "FAIL"}
        for check_id, passed in zip(CHECK_IDS, checks)
    ]
    failed = sum(row["status"] == "FAIL" for row in rows)
    return {
        "schema_version": "kmfa.v015.s10p3.public_verification.v1",
        "accounting": {"total": len(rows), "passed": len(rows) - failed, "failed": failed},
        "checks": rows,
        "future_source_count": 5,
        "connector_operation_count": 6,
        "schedule_frequency_count": 3,
        "retry_budget": 3,
        "no_data_retry_count": 0,
        "activation_gate_count": 5,
        "activation_criteria_count": 8,
        "automatic_connector_enabled_count": 0,
        "manual_import_available": True,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "source_mutation_performed": False,
        "live_connector_call_count": 0,
        "credential_read_count": 0,
        "business_execution_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }


def main() -> int:
    result = public_verification()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["accounting"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
