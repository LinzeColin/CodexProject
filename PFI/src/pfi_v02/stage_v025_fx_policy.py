from __future__ import annotations

import ast
import hashlib
import json
import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from pfi_v02.stage_v025_data_inventory import build_public_artifact_scan_report


VERSION = "v0.2.5"
STAGE = 2
PHASE_ID = "V025-S2-P2.2"
TASK_IDS = ("S2-P2-T1", "S2-P2-T2", "S2-P2-T3", "S2-P2-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S2-P22-TEMPORAL-FX"
CONTRACT_ID = "PFI-V025-STAGE2-PHASE22-TEMPORAL-FX"
TIMEZONE_NAME = "Australia/Sydney"
CUTOFF_LOCAL = "06:00:00"
FX_BASE_CURRENCY = "AUD"
FX_QUOTE_CURRENCY = "CNY"
FX_DIRECTION = "AUD_TO_CNY"
FX_SOURCE_ID = "SRC-FX-SNAPSHOT"
SNAPSHOT_HASH_SCHEME = "sha256-canonical-json-excluding-source-hash-v1"
TEMPORAL_FIELDS = (
    "transaction_time",
    "posted_at",
    "effective_at",
    "imported_at",
    "reconciled_at",
    "valued_at",
    "fx_effective_at",
    "report_as_of",
)

_CUTOFF_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$")
_PHASE22_PRIVACY_INPUTS = (
    "PFI/reports/pfi_v025/stage_2/phase_2_2/temporal_coverage.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_2/fx_snapshot_status.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_2/network_audit.json",
    "PFI/reports/pfi_v025/stage_2/phase_2_2/evidence.json",
    "PFI/docs/pfi_v025/stage_2/temporal_truth.md",
    "PFI/reports/pfi_v025/stage_2/phase_2_2/risk_and_rollback.md",
    "PFI/reports/pfi_v025/stage_2/phase_2_2/terminal.log",
    "PFI/reports/pfi_v025/stage_2/phase_2_2/changed_files.txt",
    "PFI/config/sources/v025_phase_2_2_fx_policy.json",
)
_NETWORK_IMPORT_ROOTS = {"aiohttp", "httpx", "requests", "socket", "urllib"}
_NETWORK_CALL_NAMES = {
    "create_connection",
    "open_connection",
    "urlopen",
}


def build_phase22_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage2Phase22ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase_id": PHASE_ID,
        "contract_id": CONTRACT_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "timezone": TIMEZONE_NAME,
        "current_phase_only": True,
        "ordinary_runtime_network_allowed": False,
        "finder_used": False,
        "risk_tier": "T3_FINANCIAL_TEMPORAL_POLICY",
        "explicitly_not_done": [
            "Phase 2.3",
            "Stage 2 whole-stage review",
            "生产 FX 抓取或 source promotion",
            "真实数据写入、迁移、复制、合并或删除",
            "GitHub push",
            "canonical App install",
        ],
    }


def normalize_temporal_record(record: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    for field in TEMPORAL_FIELDS:
        if field not in normalized or normalized[field] is None:
            continue
        raw = normalized[field]
        if not isinstance(raw, str):
            raise TypeError(f"{field} must be a string or null")
        parsed = _parse_aware_rfc3339(raw, field=field)
        normalized[field] = _format_rfc3339(parsed)
    return normalized


def build_temporal_coverage(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_records = [normalize_temporal_record(record) for record in records]
    fields: dict[str, dict[str, Any]] = {}
    for field in TEMPORAL_FIELDS:
        values = [
            str(record[field])
            for record in normalized_records
            if record.get(field) is not None
        ]
        ordered = sorted(
            values,
            key=lambda value: _parse_aware_rfc3339(value, field=field).astimezone(timezone.utc),
        )
        fields[field] = {
            "non_null_count": len(values),
            "null_count": len(normalized_records) - len(values),
            "coverage_start": ordered[0] if ordered else None,
            "coverage_end": ordered[-1] if ordered else None,
        }
    return {
        "schema": "PFIV025TemporalCoverageV1",
        "version": VERSION,
        "phase": "2.2",
        "timezone_contract": TIMEZONE_NAME,
        "record_count": len(normalized_records),
        "fields": fields,
    }


def effective_fx_business_date(
    instant: datetime,
    *,
    cutoff_local: str = CUTOFF_LOCAL,
    timezone_name: str = TIMEZONE_NAME,
    explicit_closed_dates: Iterable[date] = (),
) -> date:
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("FX evaluation instant must be timezone-aware")
    cutoff = _parse_cutoff(cutoff_local)
    closed = _validate_closed_dates(explicit_closed_dates)
    local = instant.astimezone(ZoneInfo(timezone_name))
    candidate = local.date()
    if local.timetz().replace(tzinfo=None) < cutoff:
        candidate -= timedelta(days=1)
    return _previous_open_business_date(candidate, closed)


def canonical_snapshot_hash(snapshot: Mapping[str, Any]) -> str:
    canonical = {key: value for key, value in snapshot.items() if key != "source_hash"}
    raw = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def build_fx_snapshot_status(
    registry_source: Mapping[str, Any],
    *,
    snapshot: Mapping[str, Any] | None,
    evaluated_at: datetime,
    explicit_closed_dates: Iterable[date] = (),
) -> dict[str, Any]:
    if str(registry_source.get("source_id", "")) != FX_SOURCE_ID:
        raise ValueError("unexpected FX source_id")
    closed = _validate_closed_dates(explicit_closed_dates)
    expected = effective_fx_business_date(
        evaluated_at,
        explicit_closed_dates=closed,
    )
    registry_status = str(registry_source.get("status", "not_loaded"))
    common = {
        "schema": "PFIV025FxSnapshotStatusV1",
        "version": VERSION,
        "phase": "2.2",
        "source_id": FX_SOURCE_ID,
        "base_currency": FX_BASE_CURRENCY,
        "quote_currency": FX_QUOTE_CURRENCY,
        "direction": FX_DIRECTION,
        "meaning": "1 AUD = rate CNY",
        "timezone": TIMEZONE_NAME,
        "cutoff_local": CUTOFF_LOCAL,
        "evaluated_at": _format_rfc3339(evaluated_at.astimezone(ZoneInfo(TIMEZONE_NAME))),
        "expected_effective_business_date": expected.isoformat(),
        "closed_date_source": "explicit_source_closed_dates",
        "closed_date_count": len(closed),
        "ordinary_runtime_network_allowed": False,
        "hash_scheme": SNAPSHOT_HASH_SCHEME,
        "private_values_included": False,
        "financial_fixture_fallback_used": False,
    }
    if snapshot is None:
        return {
            **common,
            "status": registry_status if registry_status != "ready" else "source_missing",
            "snapshot_id": None,
            "source_provider": None,
            "effective_business_date": None,
            "fx_effective_at": None,
            "rate": None,
            "source_hash": None,
            "stale_status": "unavailable",
            "stale_business_days": None,
            "blocking_reason_zh": "生产 FX snapshot 尚未绑定 canonical source；汇率与依赖指标保持 blocked/null。",
        }
    if registry_status != "ready":
        raise ValueError("snapshot cannot override a non-ready source registry state")

    _validate_snapshot_identity(snapshot)
    if str(snapshot.get("source_hash")) != canonical_snapshot_hash(snapshot):
        raise ValueError("FX snapshot hash mismatch")
    effective = date.fromisoformat(str(snapshot["effective_business_date"]))
    if effective > expected:
        raise ValueError("FX snapshot effective date is in the future")
    age = _business_day_age(effective, expected, closed)
    stale = effective < expected
    return {
        **common,
        "status": "outdated" if stale else "ready",
        "snapshot_id": str(snapshot["snapshot_id"]),
        "source_provider": str(snapshot["source_provider"]),
        "effective_business_date": effective.isoformat(),
        "fx_effective_at": _format_rfc3339(
            _parse_aware_rfc3339(str(snapshot["fx_effective_at"]), field="fx_effective_at")
        ),
        "rate": str(snapshot["rate"]),
        "source_hash": str(snapshot["source_hash"]),
        "stale_status": "stale" if stale else "current",
        "stale_business_days": age,
        "blocking_reason_zh": (
            "FX snapshot 早于当前预期有效业务日；依赖指标保持 blocked。" if stale else None
        ),
    }


def build_network_audit(module_path: str | Path, policy_path: str | Path) -> dict[str, Any]:
    module = Path(module_path)
    policy_file = Path(policy_path)
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imported = sorted(
        {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        | {
            str(node.module).split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
    )
    forbidden_imports = sorted(set(imported) & _NETWORK_IMPORT_ROOTS)
    called_names = sorted(
        {
            _call_path(node.func)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
        }
        - {""}
    )
    forbidden_calls = sorted(
        name
        for name in called_names
        if name.rsplit(".", 1)[-1] in _NETWORK_CALL_NAMES
        or name.split(".", 1)[0] in _NETWORK_IMPORT_ROOTS
    )
    policy = json.loads(policy_file.read_text(encoding="utf-8"))
    ordinary_allowed = policy.get("ordinary_runtime_network_allowed") is True
    passed = not forbidden_imports and not forbidden_calls and not ordinary_allowed
    return {
        "schema": "PFIV025Phase22NetworkAuditV1",
        "version": VERSION,
        "phase": "2.2",
        "status": "pass" if passed else "fail",
        "audited_module": "PFI/src/pfi_v02/stage_v025_fx_policy.py",
        "policy_file": "PFI/config/sources/v025_phase_2_2_fx_policy.json",
        "network_import_count": len(forbidden_imports),
        "network_import_roots": forbidden_imports,
        "network_call_count": len(forbidden_calls),
        "network_call_symbols": forbidden_calls,
        "ordinary_runtime_network_allowed": ordinary_allowed,
        "v025_explicit_refresh_implemented": False,
        "legacy_refresh_requires_explicit_allow_network": True,
        "source_mutation_performed": False,
        "finder_used": False,
    }


def build_phase22_privacy_scan_report(project_root: str | Path, observed_at: str) -> str:
    return build_public_artifact_scan_report(
        project_root,
        observed_at,
        inputs=_PHASE22_PRIVACY_INPUTS,
        scanner_name="pfi-v025-phase22-public-artifact-scan-v1",
        scan_command=(
            "PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B -m pytest "
            "-p no:cacheprovider PFI/tests/test_v025_stage2_fx_policy.py "
            "-q -k phase22_privacy_scan_is_deterministic"
        ),
    )


def _parse_cutoff(value: str) -> time:
    if not isinstance(value, str) or not _CUTOFF_RE.fullmatch(value):
        raise ValueError("cutoff_local must use HH:MM:SS")
    return time.fromisoformat(value)


def _validate_closed_dates(values: Iterable[date]) -> frozenset[date]:
    closed = tuple(values)
    if any(type(value) is not date for value in closed):
        raise TypeError("explicit_closed_dates must contain date objects")
    return frozenset(closed)


def _previous_open_business_date(candidate: date, closed: frozenset[date]) -> date:
    current = candidate
    while current.weekday() >= 5 or current in closed:
        current -= timedelta(days=1)
    return current


def _business_day_age(start: date, end: date, closed: frozenset[date]) -> int:
    if start > end:
        raise ValueError("FX snapshot effective date is in the future")
    count = 0
    current = start
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in closed:
            count += 1
    return count


def _validate_snapshot_identity(snapshot: Mapping[str, Any]) -> None:
    expected = {
        "source_id": FX_SOURCE_ID,
        "base_currency": FX_BASE_CURRENCY,
        "quote_currency": FX_QUOTE_CURRENCY,
        "direction": FX_DIRECTION,
    }
    for field, expected_value in expected.items():
        if str(snapshot.get(field, "")) != expected_value:
            raise ValueError(f"FX snapshot {field} or direction mismatch")
    try:
        rate = Decimal(str(snapshot["rate"]))
    except (InvalidOperation, KeyError) as exc:
        raise ValueError("FX snapshot rate must be a positive decimal") from exc
    if not rate.is_finite() or rate <= 0:
        raise ValueError("FX snapshot rate must be a positive decimal")
    effective = date.fromisoformat(str(snapshot["effective_business_date"]))
    effective_at = _parse_aware_rfc3339(str(snapshot["fx_effective_at"]), field="fx_effective_at")
    local = effective_at.astimezone(ZoneInfo(TIMEZONE_NAME))
    if local.date() != effective or local.timetz().replace(tzinfo=None) != _parse_cutoff(CUTOFF_LOCAL):
        raise ValueError("FX snapshot effective timestamp mismatch")


def _parse_aware_rfc3339(value: str, *, field: str) -> datetime:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field} must use RFC3339 date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def _format_rfc3339(value: datetime) -> str:
    rendered = value.isoformat(timespec="seconds")
    return rendered[:-6] + "Z" if rendered.endswith("+00:00") else rendered


def _call_path(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_path(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""
