from __future__ import annotations

import hashlib
import json
import re
import secrets
from collections.abc import Mapping, Sequence
from typing import Final


PHASE_ID: Final = "V025-S10-P10.3"
TASK_IDS: Final = (
    "S10-P3-T1",
    "S10-P3-T2",
    "S10-P3-T3",
    "S10-P3-T4",
)
ACCEPTANCE_ID: Final = "ACC-PFI-V025-STAGE10-WHOLE-REVIEW"
JOB_TRACE_SCHEMA: Final = "PFIV025DurableJobTraceV1"
JOB_SPAN_SCHEMA: Final = "PFIV025DurableJobSpanV1"
JOB_LOG_SCHEMA: Final = "PFIV025DurableJobStructuredLogV1"
JOB_OBSERVABILITY_MIGRATION_ID: Final = "v025_stage10_job_observability_v1"

OBSERVABILITY_HASH_FIELDS: Final = (
    "source_hash",
    "data_hash",
    "formula_hash",
    "parameter_hash",
    "read_model_hash",
    "cache_key",
)
DEFAULT_OBSERVABILITY_CONTEXT: Final = {
    **{field: "not_loaded" for field in OBSERVABILITY_HASH_FIELDS},
    "impact_scope": [],
    "cache_fallback_used": False,
    "external_network_calls": 0,
}

_TRACE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_SPAN_ID_PATTERN = re.compile(r"^[0-9a-f]{16}$")
_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SCOPE_PATTERN = re.compile(r"^[a-z][a-z0-9_.:-]{0,79}$")
_HOME_PATH_PATTERN = re.compile(
    r"(?:/Users/|/private/var/folders/|/var/folders/|/tmp/)[^\s\"']*"
)
_EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Z0-9._~+/=-]{8,}")
_TOKEN_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?:token|secret|password|authorization|api[_-]?key)\s*[:=]\s*[^\s,;]+"
)
_LONG_ACCOUNT_PATTERN = re.compile(r"(?<![0-9a-f])\d{12,19}(?![0-9a-f])", re.IGNORECASE)
_MONEY_PATTERN = re.compile(
    r"(?i)(?:\b(?:CNY|RMB|AUD|USD|HKD)\b|[$¥])\s*[-+]?\d[\d,]*(?:\.\d+)?"
)
_SENSITIVE_FIELD_PATTERN = re.compile(
    r"(?i)(?:amount|balance|price|quantity|description|memo|raw|payload|secret|token|"
    r"password|authorization|api[_-]?key|account(?:_number)?|card|email|path|uri|"
    r"financial_value)"
)


def new_trace_id() -> str:
    return secrets.token_hex(16)


def new_span_id() -> str:
    return secrets.token_hex(8)


def deterministic_trace_id(job_id: str) -> str:
    return hashlib.sha256(f"pfi-trace\x1f{job_id}".encode("utf-8")).hexdigest()[:32]


def deterministic_span_id(trace_id: str, job_id: str, revision: int, event_type: str) -> str:
    validate_trace_id(trace_id)
    payload = f"{trace_id}\x1f{job_id}\x1f{revision}\x1f{event_type}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def validate_trace_id(value: object, *, allow_empty: bool = False) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized and allow_empty:
        return ""
    if not _TRACE_ID_PATTERN.fullmatch(normalized) or normalized == "0" * 32:
        raise ValueError("trace_id must be 32 non-zero lowercase hexadecimal characters")
    return normalized


def validate_span_id(value: object, *, allow_empty: bool = False) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized and allow_empty:
        return ""
    if not _SPAN_ID_PATTERN.fullmatch(normalized) or normalized == "0" * 16:
        raise ValueError("span_id must be 16 non-zero lowercase hexadecimal characters")
    return normalized


def normalize_observability_context(
    context: Mapping[str, object] | None,
) -> dict[str, object]:
    if context is None:
        return {
            **{field: "not_loaded" for field in OBSERVABILITY_HASH_FIELDS},
            "impact_scope": [],
            "cache_fallback_used": False,
            "external_network_calls": 0,
        }
    if not isinstance(context, Mapping):
        raise TypeError("observability_context must be an object")
    unknown = set(context) - set(DEFAULT_OBSERVABILITY_CONTEXT)
    if unknown:
        raise ValueError(f"unsupported observability context fields: {sorted(unknown)}")

    normalized: dict[str, object] = {}
    for field in OBSERVABILITY_HASH_FIELDS:
        value = str(context.get(field) or "not_loaded").strip().lower()
        if value != "not_loaded" and not _HASH_PATTERN.fullmatch(value):
            raise ValueError(f"{field} must be a SHA-256 hash or not_loaded")
        normalized[field] = value

    impact_scope = context.get("impact_scope", [])
    if not isinstance(impact_scope, Sequence) or isinstance(impact_scope, (str, bytes)):
        raise TypeError("impact_scope must be a list")
    scopes = sorted({str(item or "").strip().lower() for item in impact_scope})
    if len(scopes) > 32 or any(not _SCOPE_PATTERN.fullmatch(item) for item in scopes):
        raise ValueError("impact_scope contains an invalid or excessive scope id")
    normalized["impact_scope"] = scopes

    cache_fallback_used = context.get("cache_fallback_used", False)
    if not isinstance(cache_fallback_used, bool):
        raise TypeError("cache_fallback_used must be a boolean")
    normalized["cache_fallback_used"] = cache_fallback_used

    external_network_calls = context.get("external_network_calls", 0)
    if isinstance(external_network_calls, bool) or not isinstance(external_network_calls, int):
        raise TypeError("external_network_calls must be an integer")
    if external_network_calls != 0:
        raise ValueError("ordinary PFI runtime jobs must record zero external network calls")
    normalized["external_network_calls"] = 0
    return normalized


def redact_log_text(value: object, *, limit: int = 1000) -> str:
    text = str(value or "").replace("\x00", "").strip()
    text = _HOME_PATH_PATTERN.sub("<redacted-private-path>", text)
    text = _EMAIL_PATTERN.sub("<redacted-email>", text)
    text = _BEARER_PATTERN.sub("Bearer <redacted-token>", text)
    text = _TOKEN_ASSIGNMENT_PATTERN.sub("<redacted-secret>", text)
    text = _LONG_ACCOUNT_PATTERN.sub("<redacted-account>", text)
    text = _MONEY_PATTERN.sub("<redacted-financial-value>", text)
    return text[:limit]


def redact_log_fields(
    fields: Mapping[str, object] | None,
    *,
    maximum_depth: int = 4,
) -> dict[str, object]:
    if fields is None:
        return {}
    if not isinstance(fields, Mapping):
        raise TypeError("structured log fields must be an object")

    def redact(value: object, key: str, depth: int) -> object:
        if _SENSITIVE_FIELD_PATTERN.search(key):
            return "<redacted-field>"
        if depth >= maximum_depth:
            return "<redacted-depth>"
        if isinstance(value, Mapping):
            return {
                str(child_key)[:80]: redact(child_value, str(child_key), depth + 1)
                for child_key, child_value in sorted(value.items(), key=lambda item: str(item[0]))
            }
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [redact(item, key, depth + 1) for item in list(value)[:50]]
        if isinstance(value, str):
            return redact_log_text(value, limit=500)
        if value is None or isinstance(value, (bool, int)):
            return value
        if isinstance(value, float):
            return "<redacted-numeric>"
        return redact_log_text(value, limit=500)

    redacted = {
        str(key)[:80]: redact(value, str(key), 0)
        for key, value in sorted(fields.items(), key=lambda item: str(item[0]))
    }
    json.dumps(redacted, ensure_ascii=False, allow_nan=False, sort_keys=True)
    return redacted


def build_phase_10_3_contract() -> dict[str, object]:
    return {
        "schema": "PFIV025Stage10Phase103RunContractV1",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "status": "implementation_contract",
        "current_phase_only": True,
        "trace": {
            "trace_schema": JOB_TRACE_SCHEMA,
            "span_schema": JOB_SPAN_SCHEMA,
            "cross_stage_propagation": True,
            "job_and_event_projection": True,
            "stage_timing": True,
        },
        "structured_logs": {
            "schema": JOB_LOG_SCHEMA,
            "persistent": True,
            "append_only": True,
            "redacted_before_persist": True,
            "payload_or_financial_values_allowed": False,
            "hash_dimensions": list(OBSERVABILITY_HASH_FIELDS),
        },
        "failure_matrix": ["kill", "restart", "offline", "timeout"],
        "ui": {
            "source": "durable_job_api",
            "timer_based_progress": False,
            "completed_units_over_total_units_only": True,
            "error_retry_and_result_entry_visible": True,
        },
        "safety_boundary": {
            "external_network_allowed": False,
            "canonical_private_database_used_by_phase_tests": False,
            "financial_values_in_logs_or_evidence": False,
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
        },
        "stage_10_whole_review_status": "not_started",
        "stage_11_started": False,
    }
