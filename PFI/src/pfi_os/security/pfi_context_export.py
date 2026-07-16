from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any


PFI_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_PATH = PFI_ROOT / "config/data_domains/stage11_distribution_boundaries.json"
DEFAULT_SCHEMA_PATH = PFI_ROOT / "shared/context/pfi_context_v1.schema.json"
PUBLIC_DISTRIBUTION_ROOTS = (
    PFI_ROOT / "web/cloudflare-public/public",
    PFI_ROOT / "web/cloudflare-public/dist",
)
PFI_CONTEXT_SCHEMA_VERSION = "pfi_context.v1"
CONTEXT_METADATA_FIELDS = (
    "schema_version",
    "as_of",
    "source_or_read_model_hash",
    "privacy_classification",
    "consumer",
    "read_only",
    "writeback_allowed",
)
CONTEXT_PAYLOAD_FIELDS = (
    "net_worth_state",
    "investable_cash_state",
    "cashflow_pressure",
    "asset_allocation",
    "risk_budget",
    "investment_behavior_tags",
    "consumption_pressure_summary",
    "data_freshness",
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ContextExportError(ValueError):
    """Raised when a PFI Context export violates its minimized boundary."""


def load_distribution_boundary_policy(
    policy_path: Path | str | None = None,
) -> dict[str, Any]:
    path = Path(policy_path) if policy_path is not None else DEFAULT_POLICY_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextExportError("distribution boundary policy is unavailable") from exc
    if not isinstance(payload, dict):
        raise ContextExportError("distribution boundary policy must be an object")
    context = payload.get("pfi_context")
    public = payload.get("public_cloudflare")
    if not isinstance(context, dict) or not isinstance(public, dict):
        raise ContextExportError("distribution boundary policy sections are incomplete")
    if context.get("schema_version") != PFI_CONTEXT_SCHEMA_VERSION:
        raise ContextExportError("unexpected PFI Context schema version")
    if tuple(context.get("payload_fields", ())) != CONTEXT_PAYLOAD_FIELDS:
        raise ContextExportError("PFI Context payload field order does not match the contract")
    if tuple(context.get("metadata_fields", ())) != CONTEXT_METADATA_FIELDS:
        raise ContextExportError("PFI Context metadata fields do not match the contract")
    if context.get("consumer") != "Alpha":
        raise ContextExportError("PFI Context consumer must be Alpha")
    if context.get("read_only") is not True or context.get("writeback_allowed") is not False:
        raise ContextExportError("PFI Context must be read-only with writeback disabled")
    if public.get("active_ui") is not False:
        raise ContextExportError("public Cloudflare surface must not be an active UI")
    return payload


def build_pfi_context_export(
    *,
    as_of: str,
    source_or_read_model_hash: str,
    net_worth_state: str,
    investable_cash_state: str,
    cashflow_pressure: str,
    asset_allocation: str,
    risk_budget: str,
    investment_behavior_tags: Sequence[str] = (),
    consumption_pressure_summary: str,
    data_freshness: str,
    policy_path: Path | str | None = None,
) -> dict[str, Any]:
    policy = load_distribution_boundary_policy(policy_path)
    context = policy["pfi_context"]
    payload: dict[str, Any] = {
        "schema_version": PFI_CONTEXT_SCHEMA_VERSION,
        "as_of": str(as_of),
        "source_or_read_model_hash": str(source_or_read_model_hash).lower(),
        "privacy_classification": context["privacy_classification"],
        "consumer": context["consumer"],
        "read_only": True,
        "writeback_allowed": False,
        "net_worth_state": str(net_worth_state),
        "investable_cash_state": str(investable_cash_state),
        "cashflow_pressure": str(cashflow_pressure),
        "asset_allocation": str(asset_allocation),
        "risk_budget": str(risk_budget),
        "investment_behavior_tags": sorted({str(item) for item in investment_behavior_tags}),
        "consumption_pressure_summary": str(consumption_pressure_summary),
        "data_freshness": str(data_freshness),
    }
    validate_pfi_context_export(payload, policy=policy)
    return payload


def build_blocked_pfi_context_export(
    *,
    as_of: str,
    source_payload: object,
    read_model_payload: object,
    policy_path: Path | str | None = None,
) -> dict[str, Any]:
    provenance_hash = _canonical_sha256(
        {
            "source_payload": source_payload,
            "read_model_payload": read_model_payload,
        }
    )
    return build_pfi_context_export(
        as_of=as_of,
        source_or_read_model_hash=provenance_hash,
        net_worth_state="blocked",
        investable_cash_state="blocked",
        cashflow_pressure="blocked",
        asset_allocation="blocked",
        risk_budget="blocked",
        investment_behavior_tags=("review_required",),
        consumption_pressure_summary="blocked",
        data_freshness="not_loaded",
        policy_path=policy_path,
    )


def validate_pfi_context_export(
    payload: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
    policy_path: Path | str | None = None,
) -> None:
    active_policy = dict(policy) if policy is not None else load_distribution_boundary_policy(
        policy_path
    )
    context = active_policy["pfi_context"]
    expected_fields = set(CONTEXT_METADATA_FIELDS + CONTEXT_PAYLOAD_FIELDS)
    actual_fields = set(payload)
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        extra = sorted(actual_fields - expected_fields)
        raise ContextExportError(
            f"PFI Context fields do not match the minimized contract: missing={missing}, extra={extra}"
        )
    _require_exact(payload, "schema_version", PFI_CONTEXT_SCHEMA_VERSION)
    _require_exact(payload, "privacy_classification", context["privacy_classification"])
    _require_exact(payload, "consumer", "Alpha")
    _require_exact(payload, "read_only", True)
    _require_exact(payload, "writeback_allowed", False)
    _require_aware_datetime(str(payload["as_of"]))
    if not _HEX64.fullmatch(str(payload["source_or_read_model_hash"])):
        raise ContextExportError("source_or_read_model_hash must be a lowercase SHA-256")

    metric_states = set(context["metric_state_values"])
    pressure_values = set(context["pressure_values"])
    freshness_values = set(context["freshness_values"])
    behavior_values = set(context["behavior_tag_values"])
    for field in ("net_worth_state", "investable_cash_state", "asset_allocation", "risk_budget"):
        _require_member(payload, field, metric_states)
    for field in ("cashflow_pressure", "consumption_pressure_summary"):
        _require_member(payload, field, pressure_values)
    _require_member(payload, "data_freshness", freshness_values)

    tags = payload["investment_behavior_tags"]
    if not isinstance(tags, list) or len(tags) > len(behavior_values):
        raise ContextExportError("investment_behavior_tags must be a minimized list")
    if any(not isinstance(item, str) or item not in behavior_values for item in tags):
        raise ContextExportError("investment_behavior_tags contains an unapproved value")
    if tags != sorted(set(tags)):
        raise ContextExportError("investment_behavior_tags must be sorted and unique")

    for field in CONTEXT_PAYLOAD_FIELDS:
        value = payload[field]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            raise ContextExportError(f"numeric financial values are forbidden in {field}")


def canonical_context_bytes(payload: Mapping[str, Any]) -> bytes:
    validate_pfi_context_export(payload)
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def write_new_context_export(
    payload: Mapping[str, Any],
    output_path: Path | str,
) -> dict[str, Any]:
    raw = canonical_context_bytes(payload)
    output = _absolute_path(output_path)
    _reject_public_distribution_path(output)
    if output.is_symlink() or output.exists():
        raise ContextExportError("context export output already exists; overwrite is forbidden")
    _prepare_private_directory(output.parent)
    descriptor: int | None = None
    created = False
    try:
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        if created:
            output.unlink(missing_ok=True)
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    _fsync_directory(output.parent)
    return {
        "schema": "PFIV025ContextExportReceiptV1",
        "status": "written",
        "schema_version": PFI_CONTEXT_SCHEMA_VERSION,
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "byte_size": len(raw),
        "file_mode": "0600",
        "overwrote_existing_file": False,
        "contains_path": False,
        "contains_financial_values": False,
    }


def _canonical_sha256(payload: object) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _require_exact(payload: Mapping[str, Any], field: str, expected: object) -> None:
    if payload[field] != expected or type(payload[field]) is not type(expected):
        raise ContextExportError(f"{field} must equal the boundary contract value")


def _require_member(payload: Mapping[str, Any], field: str, allowed: set[str]) -> None:
    value = payload[field]
    if not isinstance(value, str) or value not in allowed:
        raise ContextExportError(f"{field} is outside the allowed state vocabulary")


def _require_aware_datetime(value: str) -> None:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ContextExportError("as_of must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContextExportError("as_of must include a timezone offset")


def _absolute_path(path_value: Path | str) -> Path:
    path = Path(path_value).expanduser()
    return path if path.is_absolute() else Path.cwd() / path


def _reject_public_distribution_path(path: Path) -> None:
    resolved = path.resolve(strict=False)
    for root in PUBLIC_DISTRIBUTION_ROOTS:
        resolved_root = root.resolve(strict=False)
        if resolved == resolved_root or resolved_root in resolved.parents:
            raise ContextExportError("context export cannot be written to a public distribution")


def _prepare_private_directory(path: Path) -> None:
    if path.is_symlink():
        raise ContextExportError("context export directory must not be a symbolic link")
    existed = path.exists()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir():
        raise ContextExportError("context export parent must be a directory")
    permissions = stat.S_IMODE(path.stat().st_mode)
    if existed and permissions & 0o077:
        raise ContextExportError(
            "existing context export directory must not grant group or other access"
        )
    if not existed:
        os.chmod(path, 0o700)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = [
    "CONTEXT_METADATA_FIELDS",
    "CONTEXT_PAYLOAD_FIELDS",
    "DEFAULT_POLICY_PATH",
    "DEFAULT_SCHEMA_PATH",
    "PFI_CONTEXT_SCHEMA_VERSION",
    "PUBLIC_DISTRIBUTION_ROOTS",
    "ContextExportError",
    "build_blocked_pfi_context_export",
    "build_pfi_context_export",
    "canonical_context_bytes",
    "load_distribution_boundary_policy",
    "validate_pfi_context_export",
    "write_new_context_export",
]
