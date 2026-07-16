"""Fail-closed account/balance read model for PFI v0.2.5 Phase 4.1.

The current adapter consumes only the tracked, aggregate Stage 2 source
manifest. It does not read financial rows or infer balances from transactions.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from pfi_os.domain.accounts import CashReconciliationInput


PHASE_ID = "V025-S4-P4.1"
TASK_IDS = ("S4-P1-T1", "S4-P1-T2", "S4-P1-T3", "S4-P1-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S4-P41-ACCOUNT-SNAPSHOT"
FORMULA_ID = "FORM-PFI-008"
FORMULA_VERSION = "pfi-v0.2.5-cash-reconciliation-v1"
FORMULA_EXPRESSION = (
    "expected_closing_balance = opening_balance + confirmed_net_flows + adjustments; "
    "discrepancy = observed_closing_balance - expected_closing_balance"
)
PARAMETERS = {
    "cash_reconciliation_tolerance": "0",
    "confirmed_zero_complete_evidence_required": True,
    "non_ready_value_allowed": False,
}
REQUIRED_SOURCE_IDS = ("SRC-ACCOUNT-BALANCES", "SRC-LIABILITIES")
SOURCE_MANIFEST_PATH = Path("PFI/reports/pfi_v025/stage_2/phase_2_1/source_manifest.json")


def _canonical_json(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash(payload: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(payload)).hexdigest()


FORMULA_HASH = _hash({"formula_id": FORMULA_ID, "expression": FORMULA_EXPRESSION})
PARAMETER_HASH = _hash(PARAMETERS)


def build_phase41_contract() -> dict[str, object]:
    return {
        "version": "v0.2.5",
        "stage": 4,
        "phase": "4.1",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "current_phase_only": True,
        "read_only_real_sources": True,
        "financial_fixture_fallback_allowed": False,
        "transaction_balance_inference_allowed": False,
        "finder_used": False,
        "explicitly_not_done": [
            "Phase 4.2 holdings, prices and FX valuation",
            "Phase 4.3 all-surface integration and whole-stage acceptance",
            "production writes, GitHub push and canonical app install",
        ],
    }


def load_source_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / SOURCE_MANIFEST_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("Stage 2 source manifest is invalid")
    return payload


def _source_index(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ValueError("source manifest sources must be a list")
    index = {
        str(item.get("source_id")): item
        for item in sources
        if isinstance(item, Mapping) and item.get("source_id")
    }
    missing = [source_id for source_id in REQUIRED_SOURCE_IDS if source_id not in index]
    if missing:
        raise ValueError(f"source manifest missing required sources: {', '.join(missing)}")
    return index


def _metric_status(source: Mapping[str, Any]) -> str:
    status = str(source.get("status") or "not_loaded")
    mapping = {
        "not_loaded": "not_loaded",
        "source_missing": "source_missing",
        "permission_denied": "permission_denied",
        "path_error": "path_error",
        "parse_failed": "parse_failed",
        "outdated_snapshot": "outdated_snapshot",
        "partial": "partial_coverage",
        "partial_coverage": "partial_coverage",
    }
    # Phase 4.1 does not load private financial rows. A metadata-only "ready"
    # claim therefore cannot authorize a financial value.
    return mapping.get(status, "not_loaded")


def _metric(metric_id: str, source: Mapping[str, Any], *, formula_id: str) -> dict[str, Any]:
    coverage = source.get("coverage") if isinstance(source.get("coverage"), Mapping) else {}
    status = _metric_status(source)
    return {
        "metric_id": metric_id,
        "value": None,
        "currency": "CNY",
        "status": status,
        "source_ids": [str(source["source_id"])],
        "record_count": source.get("record_count") if isinstance(source.get("record_count"), int) else None,
        "coverage_start": coverage.get("start"),
        "coverage_end": coverage.get("end"),
        "data_as_of": source.get("as_of"),
        "valued_at": None,
        "fx_snapshot_id": None,
        "formula_id": formula_id,
        "formula_version": FORMULA_VERSION if formula_id == FORMULA_ID else None,
        "formula_hash": FORMULA_HASH if formula_id == FORMULA_ID else None,
        "parameter_hash": PARAMETER_HASH,
        "data_hash": source.get("content_hash"),
        "read_model_hash": "PENDING",
        "classification_confidence": None,
        "source_coverage": 0 if status == "not_loaded" else None,
        "reconciliation_coverage": 0 if formula_id == FORMULA_ID else None,
        "valuation_coverage": None,
        "model_validation": "blocked",
        "report_completeness": "blocked",
        "blocking_reason_zh": source.get("blocking_reason_zh")
        or "Phase 4.1 未加载完整账户快照证据，不执行财务计算。",
        "calculation_state": "not_run",
    }


def build_current_account_read_model(
    repo_root: Path,
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    manifest = load_source_manifest(repo_root)
    sources = _source_index(manifest)
    balance_source = sources["SRC-ACCOUNT-BALANCES"]
    liability_source = sources["SRC-LIABILITIES"]
    metrics = [
        _metric("account_assets_cny", balance_source, formula_id="SOURCE-SNAPSHOT-SUM"),
        _metric("cash_balance_cny", balance_source, formula_id=FORMULA_ID),
        _metric("liabilities_cny", liability_source, formula_id="SOURCE-SNAPSHOT-SUM"),
    ]
    semantic_payload = {
        "schema": "PFIV025AccountBalanceReadModelV1",
        "source_states": [
            {
                "source_id": source_id,
                "status": sources[source_id].get("status"),
                "record_count": sources[source_id].get("record_count"),
                "coverage": sources[source_id].get("coverage"),
                "as_of": sources[source_id].get("as_of"),
                "content_hash": sources[source_id].get("content_hash"),
            }
            for source_id in REQUIRED_SOURCE_IDS
        ],
        "metrics": [
            {key: value for key, value in metric.items() if key != "read_model_hash"}
            for metric in metrics
        ],
        "formula_hash": FORMULA_HASH,
        "parameter_hash": PARAMETER_HASH,
    }
    read_model_hash = _hash(semantic_payload)
    for metric in metrics:
        metric["read_model_hash"] = read_model_hash
    status = "not_loaded" if all(metric["status"] == "not_loaded" for metric in metrics) else "partial_coverage"
    return {
        "schema": "PFIV025AccountBalanceReadModelV1",
        "version": "v0.2.5",
        "stage": 4,
        "phase": "4.1",
        "acceptance_id": ACCEPTANCE_ID,
        "observed_at": observed_at or str(manifest.get("observed_at")),
        "status": status,
        "source_ids": list(REQUIRED_SOURCE_IDS),
        "metrics": metrics,
        "read_model_hash": read_model_hash,
        "formula_hash": FORMULA_HASH,
        "parameter_hash": PARAMETER_HASH,
        "transactions_available_is_not_balance_proof": True,
        "transaction_balance_inference_used": False,
        "financial_fixture_fallback_used": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def reconcile_cash(inputs: CashReconciliationInput) -> dict[str, Any]:
    expected = inputs.opening_balance + inputs.confirmed_net_flows + inputs.adjustments
    discrepancy = inputs.observed_closing_balance - expected
    passed = discrepancy == Decimal("0")
    return {
        "formula_id": FORMULA_ID,
        "formula_version": FORMULA_VERSION,
        "formula_hash": FORMULA_HASH,
        "parameter_hash": PARAMETER_HASH,
        "status": "ready" if passed else "reconciliation_failed",
        "value": str(inputs.observed_closing_balance) if passed else None,
        "currency": inputs.currency,
        "expected_closing_balance": str(expected),
        "observed_closing_balance": str(inputs.observed_closing_balance),
        "discrepancy": str(discrepancy),
        "source_ids": list(inputs.source_ids),
        "coverage_start": inputs.coverage_start.isoformat(),
        "coverage_end": inputs.coverage_end.isoformat(),
        "data_as_of": inputs.data_as_of.isoformat(),
        "source_content_hash": inputs.source_content_hash,
        "calculation_state": "calculated" if passed else "failed_closed",
        "cash_reconciliation_tolerance": PARAMETERS["cash_reconciliation_tolerance"],
    }


def build_account_home_api_contract(read_model: Mapping[str, Any]) -> dict[str, Any]:
    read_model_hash = str(read_model["read_model_hash"])
    metrics = deepcopy(read_model["metrics"])
    surfaces = {
        surface_id: {
            "read_model_hash": read_model_hash,
            "status": read_model["status"],
            "metrics": deepcopy(metrics),
        }
        for surface_id in ("homepage", "accounts")
    }
    return {
        "schema": "PFIV025AccountHomeAPIContractV1",
        "version": "v0.2.5",
        "stage": 4,
        "phase": "4.1",
        "status": read_model["status"],
        "surface_ids": ["homepage", "accounts"],
        "read_model_hash": read_model_hash,
        "surface_read_model_hashes": {
            surface_id: surface["read_model_hash"] for surface_id, surface in surfaces.items()
        },
        "surfaces": surfaces,
        "same_source_hash": len({surface["read_model_hash"] for surface in surfaces.values()}) == 1,
        "financial_values_emitted": read_model["financial_values_emitted"],
        "contains_private_values": False,
    }
