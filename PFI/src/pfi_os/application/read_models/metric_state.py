"""Strict PFI v0.2.5 metric-state and dependency-hash invariants."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any, Mapping


METRIC_CONTRACT_VERSION = "PFIV025MetricStateStrictV1"
METRIC_STATUSES = (
    "ready",
    "confirmed_zero",
    "partial_coverage",
    "not_loaded",
    "source_missing",
    "path_error",
    "parse_failed",
    "outdated_snapshot",
    "permission_denied",
    "calculation_failed",
    "reconciliation_failed",
    "valuation_missing",
    "filtered_empty",
)
NON_READY_STATUSES = tuple(
    status for status in METRIC_STATUSES if status not in {"ready", "confirmed_zero"}
)
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_BASE_REQUIRED_FIELDS = (
    "metric_contract_version",
    "metric_id",
    "value",
    "currency",
    "status",
    "source_ids",
    "record_count",
    "coverage_start",
    "coverage_end",
    "data_as_of",
    "formula_id",
    "formula_version",
    "formula_hash",
    "parameter_hash",
    "data_hash",
    "read_model_hash",
    "dependency_hashes",
    "dependency_set_hash",
    "classification_confidence",
    "source_coverage",
    "reconciliation_coverage",
    "valuation_coverage",
    "model_validation",
    "report_completeness",
    "blocking_reason_zh",
    "calculation_state",
)
_CONFIRMED_EVIDENCE_FIELDS = (
    "record_count",
    "coverage_start",
    "coverage_end",
    "data_as_of",
    "formula_version",
    "formula_hash",
    "parameter_hash",
    "data_hash",
    "classification_confidence",
    "source_coverage",
    "reconciliation_coverage",
    "valuation_coverage",
)


def canonical_hash(payload: object) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require_sha256(name: str, value: object) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{name} must be sha256:<64 lowercase hex>")
    return value


def dependency_set_hash(dependency_hashes: Mapping[str, str]) -> str:
    if not isinstance(dependency_hashes, Mapping) or not dependency_hashes:
        raise ValueError("dependency_hashes must be a non-empty mapping")
    normalized: dict[str, str] = {}
    for name, value in dependency_hashes.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("dependency hash name must be a non-empty string")
        normalized[name] = require_sha256(f"dependency_hashes[{name}]", value)
    return canonical_hash(normalized)


def metric_fingerprint(metric: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in metric.items() if key != "read_model_hash"}
    return canonical_hash(payload)


def _numeric(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError("metric value must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("metric value must be finite numeric") from exc
    if not result.is_finite():
        raise ValueError("metric value must be finite numeric")
    return result


def _require_ratio(name: str, value: object, *, maximum: Decimal) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{name} must be numeric")
    numeric = Decimal(str(value))
    if not numeric.is_finite() or numeric < 0 or numeric > maximum:
        raise ValueError(f"{name} must be between 0 and {maximum}")


def validate_metric_state(metric: Mapping[str, Any]) -> None:
    """Fail closed on incomplete ready/zero states and any non-ready value."""

    if not isinstance(metric, Mapping):
        raise ValueError("metric state must be an object")
    missing = [field for field in _BASE_REQUIRED_FIELDS if field not in metric]
    if missing:
        raise ValueError(f"metric state missing fields: {', '.join(missing)}")
    if metric["metric_contract_version"] != METRIC_CONTRACT_VERSION:
        raise ValueError("metric_contract_version is unsupported")
    if not isinstance(metric["metric_id"], str) or not metric["metric_id"].strip():
        raise ValueError("metric_id must be a non-empty string")
    status = metric["status"]
    if status not in METRIC_STATUSES:
        raise ValueError("metric status is unsupported")
    source_ids = metric["source_ids"]
    if status in {"ready", "confirmed_zero"}:
        if not isinstance(source_ids, list) or not source_ids:
            raise ValueError(f"{status} requires complete evidence: source_ids")
        for field in _CONFIRMED_EVIDENCE_FIELDS:
            value_for_field = metric[field]
            if value_for_field is None or value_for_field == "":
                raise ValueError(f"{status} requires complete evidence: {field}")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not isinstance(item, str) or not item.strip() for item in source_ids)
        or len(set(source_ids)) != len(source_ids)
    ):
        raise ValueError("source_ids must be a non-empty unique string list")
    record_count = metric["record_count"]
    if record_count is not None and (
        isinstance(record_count, bool) or not isinstance(record_count, int) or record_count < 0
    ):
        raise ValueError("record_count must be a non-negative integer or null")
    if not isinstance(metric["formula_id"], str) or not metric["formula_id"].strip():
        raise ValueError("formula_id must be a non-empty string")
    if not isinstance(metric["formula_version"], str) or not metric["formula_version"].strip():
        raise ValueError("formula_version must be a non-empty string")
    require_sha256("formula_hash", metric["formula_hash"])
    require_sha256("parameter_hash", metric["parameter_hash"])
    require_sha256("read_model_hash", metric["read_model_hash"])
    dependencies = metric["dependency_hashes"]
    expected_dependency_hash = dependency_set_hash(dependencies)
    if metric["dependency_set_hash"] != expected_dependency_hash:
        raise ValueError("dependency_set_hash does not match dependency_hashes")

    if status in NON_READY_STATUSES:
        if metric["value"] is not None:
            raise ValueError("non-ready metric value must be null")
        if not isinstance(metric["blocking_reason_zh"], str) or not metric[
            "blocking_reason_zh"
        ].strip():
            raise ValueError("non-ready metric requires blocking_reason_zh")
        return

    value = _numeric(metric["value"])
    if status == "ready" and value == 0:
        raise ValueError("financial zero must use confirmed_zero")
    if status == "confirmed_zero" and value != 0:
        raise ValueError("confirmed_zero value must be numeric zero")

    if not source_ids:
        raise ValueError(f"{status} requires source_ids")
    if status == "confirmed_zero" and metric["record_count"] is None:
        raise ValueError("confirmed_zero requires complete evidence: record_count")
    require_sha256("data_hash", metric["data_hash"])
    _require_ratio("classification_confidence", metric["classification_confidence"], maximum=Decimal("100"))
    for field in ("source_coverage", "reconciliation_coverage", "valuation_coverage"):
        _require_ratio(field, metric[field], maximum=Decimal("1"))
    if metric["model_validation"] != "validated":
        raise ValueError(f"{status} requires model_validation=validated")
    if metric["report_completeness"] != "complete":
        raise ValueError(f"{status} requires report_completeness=complete")
