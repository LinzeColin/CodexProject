"""Unified, page-independent PFI v0.2.5 Stage 4 read model."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any, Mapping

from .account_balance import build_current_account_read_model
from .investment import build_current_investment_read_model
from .metric_state import (
    METRIC_CONTRACT_VERSION,
    canonical_hash,
    dependency_set_hash,
    metric_fingerprint,
    validate_metric_state,
)


PHASE_ID = "V025-S4-P4.3"
TASK_IDS = ("S4-P3-T1", "S4-P3-T2", "S4-P3-T3", "S4-P3-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S4-P43-METRIC-CONSISTENCY"
SURFACE_IDS = ("homepage", "accounts", "investment", "consumption", "report")
SOURCE_SNAPSHOT_FORMULA_ID = "FORM-PFI-011"
NET_WORTH_FORMULA_ID = "FORM-PFI-012"
READ_MODEL_HASH_FORMULA_ID = "FORM-PFI-013"
SOURCE_SNAPSHOT_FORMULA_VERSION = "pfi-v0.2.5-source-snapshot-sum-v1"
NET_WORTH_FORMULA_VERSION = "pfi-v0.2.5-net-worth-composition-v1"
READ_MODEL_HASH_FORMULA_VERSION = "pfi-v0.2.5-unified-read-model-hash-v1"
SOURCE_SNAPSHOT_FORMULA_EXPRESSION = (
    "source_snapshot_sum_cny = sum(explicit source-reported CNY snapshot values); "
    "transaction events never infer missing balances"
)
NET_WORTH_FORMULA_EXPRESSION = (
    "net_worth_cny = account_assets_cny + investment_market_value_cny - liabilities_cny"
)
READ_MODEL_HASH_FORMULA_EXPRESSION = (
    "dependency_set_hash = SHA256(canonical_json(sorted dependency hashes)); "
    "read_model_hash = SHA256(canonical_json(metric states without page identity or observation time, "
    "dependency hashes and formula/parameter contract)); every surface binds the same snapshot hash"
)
PARAMETERS = {
    "financial_zero_display_policy": "confirmed_zero_with_complete_evidence_only",
    "read_model_hash_algorithm": "sha256",
    "read_model_hash_serialization": "canonical_json_sort_keys_utf8_no_whitespace",
    "read_model_hash_scope": "snapshot_not_page",
    "surface_ids": list(SURFACE_IDS),
}
SOURCE_SNAPSHOT_FORMULA_HASH = canonical_hash(
    {"formula_id": SOURCE_SNAPSHOT_FORMULA_ID, "expression": SOURCE_SNAPSHOT_FORMULA_EXPRESSION}
)
NET_WORTH_FORMULA_HASH = canonical_hash(
    {"formula_id": NET_WORTH_FORMULA_ID, "expression": NET_WORTH_FORMULA_EXPRESSION}
)
READ_MODEL_HASH_FORMULA_HASH = canonical_hash(
    {"formula_id": READ_MODEL_HASH_FORMULA_ID, "expression": READ_MODEL_HASH_FORMULA_EXPRESSION}
)
PARAMETER_HASH = canonical_hash(PARAMETERS)
STAGE3_READ_MODEL_PATH = Path(
    "PFI/reports/pfi_v025/stage_3/phase_3_3/read_model_contract.json"
)
SOURCE_MANIFEST_PATH = Path("PFI/reports/pfi_v025/stage_2/phase_2_1/source_manifest.json")


def build_phase43_contract() -> dict[str, object]:
    return {
        "version": "v0.2.5",
        "stage": 4,
        "phase": "4.3",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "surface_ids": list(SURFACE_IDS),
        "current_phase_only": True,
        "read_only_real_sources": True,
        "financial_fixture_fallback_allowed": False,
        "finder_used": False,
        "stage_4_whole_stage_review_done": False,
        "explicitly_not_done": [
            "Stage 4 whole-stage independent review, remediation, re-review and transition acceptance",
            "Stage 5 formula/model implementation",
            "private financial row loading, production writes, GitHub push and canonical app install",
        ],
    }


def _load_json(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid JSON object: {path}")
    return payload


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _metric_status(metrics: list[Mapping[str, Any]]) -> str:
    statuses = {str(metric.get("status") or "not_loaded") for metric in metrics}
    precedence = (
        "permission_denied",
        "path_error",
        "parse_failed",
        "calculation_failed",
        "reconciliation_failed",
        "source_missing",
        "outdated_snapshot",
        "valuation_missing",
        "partial_coverage",
        "not_loaded",
        "filtered_empty",
        "confirmed_zero",
        "ready",
    )
    return next(status for status in precedence if status in statuses)


def _enrich_component_metric(
    metric: Mapping[str, Any],
    *,
    component_name: str,
    component_hash: str,
) -> dict[str, Any]:
    result = deepcopy(dict(metric))
    result["metric_contract_version"] = METRIC_CONTRACT_VERSION
    result["component_read_model_hash"] = component_hash
    dependencies = {component_name: component_hash}
    result["dependency_hashes"] = dependencies
    result["dependency_set_hash"] = dependency_set_hash(dependencies)
    result["read_model_hash"] = "PENDING"
    if result.get("formula_id") == "SOURCE-SNAPSHOT-SUM":
        result["component_formula_id"] = "SOURCE-SNAPSHOT-SUM"
        result["formula_id"] = SOURCE_SNAPSHOT_FORMULA_ID
        result["formula_version"] = SOURCE_SNAPSHOT_FORMULA_VERSION
        result["formula_hash"] = SOURCE_SNAPSHOT_FORMULA_HASH
        result["parameter_hash"] = PARAMETER_HASH
    return result


def _build_net_worth_metric(
    component_metrics: Mapping[str, Mapping[str, Any]],
    dependency_hashes: Mapping[str, str],
) -> dict[str, Any]:
    inputs = [
        component_metrics["account_assets_cny"],
        component_metrics["investment_market_value_cny"],
        component_metrics["liabilities_cny"],
    ]
    status = _metric_status(inputs)
    reasons = [
        str(metric["blocking_reason_zh"])
        for metric in inputs
        if metric.get("blocking_reason_zh")
    ]
    sources: list[str] = []
    for metric in inputs:
        for source_id in metric.get("source_ids", []):
            if source_id not in sources:
                sources.append(str(source_id))
    dependencies = {
        "account_balance_read_model": dependency_hashes["account_balance_read_model"],
        "investment_read_model": dependency_hashes["investment_read_model"],
    }
    return {
        "metric_contract_version": METRIC_CONTRACT_VERSION,
        "metric_id": "net_worth_cny",
        "value": None,
        "currency": "CNY",
        "status": status,
        "source_ids": sources,
        "record_count": None,
        "coverage_start": None,
        "coverage_end": None,
        "data_as_of": None,
        "valued_at": None,
        "fx_snapshot_id": None,
        "formula_id": NET_WORTH_FORMULA_ID,
        "formula_version": NET_WORTH_FORMULA_VERSION,
        "formula_hash": NET_WORTH_FORMULA_HASH,
        "component_formula_ids": [
            str(component_metrics["account_assets_cny"]["formula_id"]),
            str(component_metrics["investment_market_value_cny"]["formula_id"]),
            str(component_metrics["liabilities_cny"]["formula_id"]),
        ],
        "parameter_hash": PARAMETER_HASH,
        "data_hash": None,
        "read_model_hash": "PENDING",
        "dependency_hashes": dependencies,
        "dependency_set_hash": dependency_set_hash(dependencies),
        "classification_confidence": None,
        "source_coverage": 0,
        "reconciliation_coverage": 0,
        "valuation_coverage": 0,
        "model_validation": "blocked",
        "report_completeness": "blocked",
        "blocking_reason_zh": "；".join(dict.fromkeys(reasons))
        or "净资产组成依赖未完整加载，不执行计算。",
        "calculation_state": "not_run",
    }


def _semantic_hash_payload(read_model: Mapping[str, Any]) -> dict[str, Any]:
    metrics = read_model.get("metrics")
    if not isinstance(metrics, list):
        raise ValueError("read model metrics must be a list")
    return {
        "schema": "PFIV025UnifiedReadModelV1",
        "contract_version": READ_MODEL_HASH_FORMULA_VERSION,
        "dependency_hashes": read_model["dependency_hashes"],
        "dependency_set_hash": read_model["dependency_set_hash"],
        "metrics": [
            {key: value for key, value in metric.items() if key != "read_model_hash"}
            for metric in metrics
            if isinstance(metric, Mapping)
        ],
        "source_snapshot_formula_hash": SOURCE_SNAPSHOT_FORMULA_HASH,
        "net_worth_formula_hash": NET_WORTH_FORMULA_HASH,
        "read_model_hash_formula_hash": READ_MODEL_HASH_FORMULA_HASH,
        "parameter_hash": PARAMETER_HASH,
    }


def rebuild_read_model_hash(read_model: Mapping[str, Any]) -> str:
    return canonical_hash(_semantic_hash_payload(read_model))


def build_current_unified_read_model(
    repo_root: Path,
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    account = build_current_account_read_model(repo_root, observed_at=observed_at)
    investment = build_current_investment_read_model(repo_root, observed_at=observed_at)
    stage3_path = repo_root / STAGE3_READ_MODEL_PATH
    stage3 = _load_json(stage3_path)
    stage3_hash = str(stage3.get("read_model_hash") or "")
    if not stage3_hash.startswith("sha256:"):
        raise ValueError("Stage 3 read model hash is unavailable")
    dependency_hashes = {
        "account_balance_read_model": str(account["read_model_hash"]),
        "investment_read_model": str(investment["read_model_hash"]),
        "stage2_source_manifest": _file_hash(repo_root / SOURCE_MANIFEST_PATH),
        "stage3_event_read_model": stage3_hash,
    }

    component_metrics: list[dict[str, Any]] = []
    for metric in account["metrics"]:
        component_metrics.append(
            _enrich_component_metric(
                metric,
                component_name="account_balance_read_model",
                component_hash=str(account["read_model_hash"]),
            )
        )
    for metric in investment["metrics"]:
        component_metrics.append(
            _enrich_component_metric(
                metric,
                component_name="investment_read_model",
                component_hash=str(investment["read_model_hash"]),
            )
        )
    by_id = {str(metric["metric_id"]): metric for metric in component_metrics}
    metrics = [_build_net_worth_metric(by_id, dependency_hashes), *component_metrics]
    read_model: dict[str, Any] = {
        "schema": "PFIV025UnifiedReadModelV1",
        "version": "v0.2.5",
        "stage": 4,
        "phase": "4.3",
        "phase_id": PHASE_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "observed_at": observed_at or str(account.get("observed_at")),
        "as_of": None,
        "status": _metric_status(metrics),
        "surface_ids": list(SURFACE_IDS),
        "dependency_hashes": dependency_hashes,
        "dependency_set_hash": dependency_set_hash(dependency_hashes),
        "metrics": metrics,
        "source_snapshot_formula_hash": SOURCE_SNAPSHOT_FORMULA_HASH,
        "net_worth_formula_hash": NET_WORTH_FORMULA_HASH,
        "read_model_hash_formula_hash": READ_MODEL_HASH_FORMULA_HASH,
        "parameter_hash": PARAMETER_HASH,
    }
    read_model_hash = rebuild_read_model_hash(read_model)
    for metric in metrics:
        metric["read_model_hash"] = read_model_hash
        validate_metric_state(metric)
    fingerprints = [metric_fingerprint(metric) for metric in metrics]
    metric_ids = [str(metric["metric_id"]) for metric in metrics]
    surfaces = {
        surface_id: {
            "read_model_hash": read_model_hash,
            "dependency_set_hash": read_model["dependency_set_hash"],
            "metric_ids": list(metric_ids),
            "metric_fingerprints": list(fingerprints),
        }
        for surface_id in SURFACE_IDS
    }
    read_model.update(
        {
            "read_model_hash": read_model_hash,
            "core_metric_states": deepcopy(metrics),
            "metric_ids": metric_ids,
            "metric_fingerprints": fingerprints,
            "surfaces": surfaces,
            "cross_page_difference_count": 0,
            "blocked_metric_ids": [
                str(metric["metric_id"])
                for metric in metrics
                if metric["status"] not in {"ready", "confirmed_zero"}
            ],
            "confirmed_zero_count": sum(
                metric["status"] == "confirmed_zero" for metric in metrics
            ),
            "non_ready_value_count": sum(
                metric["status"] not in {"ready", "confirmed_zero"}
                and metric["value"] is not None
                for metric in metrics
            ),
            "financial_values_emitted": sum(metric["value"] is not None for metric in metrics),
            "transactions_available_is_not_balance_or_holding_proof": True,
            "transaction_balance_inference_used": False,
            "transaction_holding_inference_used": False,
            "financial_fixture_fallback_used": False,
            "contains_private_values": False,
            "stage_4_whole_stage_review_done": False,
            "stage_5_started": False,
        }
    )
    return read_model
