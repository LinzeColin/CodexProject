from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def read_qbvs_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    root = Path(bundle_dir)
    manifest = _read_json(root / "quantlab_bundle_manifest.json")
    payload = _read_json(root / "quantlab_ingestion_payload.json")
    candidates = _read_csv(root / "quantlab_candidate_strategies.csv")
    _require_external_only(manifest, payload)
    return {
        "kind": "qbvs_bundle",
        "bundle_dir": str(root),
        "manifest": manifest,
        "payload": payload,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "approval_state": "review_only",
        "requires_exact_rerun": any(_truthy(row.get("requires_exact_validation")) for row in candidates),
        "requires_fund_rule_review": any(_truthy(row.get("requires_fund_rule_review")) for row in candidates),
    }


def read_qbvs_campaign(campaign_dir: str | Path) -> dict[str, Any]:
    root = Path(campaign_dir)
    plan = _read_json(root / "campaign_plan.json")
    status = _read_csv(root / "campaign_status.csv")
    if plan.get("starts_background_processes") is not False:
        raise ValueError("QBVS campaign must not start background processes.")
    return {
        "kind": "qbvs_campaign",
        "campaign_dir": str(root),
        "plan": plan,
        "status_rows": len(status),
        "status": status,
        "approval_state": "review_only",
    }


def read_qbvs_promotion_candidates(path: str | Path) -> dict[str, Any]:
    rows = _read_csv(Path(path))
    return {
        "kind": "qbvs_promotion_candidates",
        "path": str(path),
        "candidate_count": len(rows),
        "external_candidate_count": sum(1 for row in rows if row.get("promotion_state") == "external_candidate"),
        "requires_exact_rerun": all(_truthy(row.get("requires_quantlab_exact_rerun")) for row in rows) if rows else True,
        "requires_user_approval": all(_truthy(row.get("requires_user_approval_before_strategy_library_write")) for row in rows) if rows else True,
        "candidates": rows,
    }


def build_independent_validation_record(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_system": "QBVS",
        "status": "ReviewOnly",
        "mode": evidence.get("kind", ""),
        "manifest_path": evidence.get("bundle_dir") or evidence.get("campaign_dir") or evidence.get("path", ""),
        "total_rows": int(evidence.get("candidate_count") or evidence.get("status_rows") or 0),
        "shard_count": 0,
        "payload_json": evidence,
        "approval_boundary": "Do not write approved strategies without exact rerun and user approval.",
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _require_external_only(manifest: dict[str, Any], payload: dict[str, Any]) -> None:
    if manifest.get("writes_quantlab_database") is not False:
        raise ValueError("QBVS bundle must not write QuantLab database.")
    if manifest.get("writes_quantlab_source") is not False:
        raise ValueError("QBVS bundle must not write QuantLab source.")
    if payload.get("ingestion_mode") != "external_evidence_only":
        raise ValueError("QBVS payload must be external_evidence_only.")


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
