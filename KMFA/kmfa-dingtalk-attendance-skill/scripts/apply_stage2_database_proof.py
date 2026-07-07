#!/usr/bin/env python3
"""Apply a non-production PostgreSQL execution proof to a Stage-2 source."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from prepare_preconsensus_postgres_landing_bundle import stable_hash


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def proof_hash(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_proof(source: dict[str, Any], bundle_manifest: dict[str, Any], load_plan_manifest: dict[str, Any], proof: dict[str, Any]) -> tuple[str, str]:
    source_snapshot_hash = stable_hash(source)
    require(bundle_manifest.get("status") == "READY", "db landing bundle is not READY")
    require(bundle_manifest.get("mode") == "offline_preconsensus_db_landing_bundle", "db landing bundle is not pre-consensus")
    require(bundle_manifest.get("stage2_accepted") is False, "pre-consensus proof must not require accepted stage-2")
    require(bundle_manifest.get("source_snapshot_hash") == source_snapshot_hash, "db landing bundle source hash mismatch")
    require(load_plan_manifest.get("status") == "READY", "postgres load plan is not READY")
    require(load_plan_manifest.get("postgres_connection_used") is False, "load plan must be offline before execution")
    require(load_plan_manifest.get("database_mutation_performed") is False, "load plan manifest should not claim mutation")
    require(proof.get("status") == "pass", "execution proof status is not pass")
    require(proof.get("mode") == "postgres_load_plan_execution_guard", "execution proof mode mismatch")
    require(proof.get("execute_requested") is True, "execution proof did not request execution")
    require(proof.get("acknowledge_nonprod_mutation") is True, "non-production mutation acknowledgement missing")
    require(proof.get("psql_invoked") is True, "psql was not invoked")
    require(proof.get("postgres_connection_used") is True, "postgres connection was not used")
    require(proof.get("database_mutation_attempted") is True, "database mutation was not attempted")
    require(proof.get("database_mutation_performed") is True, "database mutation was not performed")
    require(proof.get("live_dws_performed") is False, "execution proof unexpectedly used live DWS")
    checks = proof.get("checks") if isinstance(proof.get("checks"), dict) else {}
    require(checks.get("static_validation_passed") is True, "static validation did not pass")
    require(checks.get("target_env_nonproduction") is True, "target environment was not non-production")
    require(checks.get("database_url_not_production_like") is True, "database URL looked production-like")
    require(checks.get("execution_guard_satisfied") is True, "execution guard was not satisfied")
    marker = "postgres-nonprod:" + proof_hash({
        "bundle_source_hash": bundle_manifest.get("source_snapshot_hash"),
        "load_plan_tables": load_plan_manifest.get("tables"),
        "payloads": load_plan_manifest.get("payloads"),
        "target_env": proof.get("target_env"),
        "psql_returncode": proof.get("psql_returncode"),
    }).removeprefix("sha256:")[:32]
    return marker, proof_hash(proof)


def materialize(source_json: Path, bundle_dir: Path, execution_proof_json: Path, out_json: Path) -> dict[str, Any]:
    source = load_json(source_json)
    bundle_manifest = load_json(bundle_dir / "db_landing_manifest.json")
    load_plan_manifest = load_json(bundle_dir / "postgres_load_plan_manifest.json")
    proof = load_json(execution_proof_json)
    require(isinstance(source, dict), "source snapshot must be an object")
    require(isinstance(bundle_manifest, dict), "bundle manifest must be an object")
    require(isinstance(load_plan_manifest, dict), "load plan manifest must be an object")
    require(isinstance(proof, dict), "execution proof must be an object")
    marker, execution_proof_hash = validate_proof(source, bundle_manifest, load_plan_manifest, proof)
    source = dict(source)
    gates = dict(source.get("quality_gates") if isinstance(source.get("quality_gates"), dict) else {})
    require(gates.get("raw_to_derived_reconciliation_passed") is True, "raw_to_derived gate must already be true")
    require(gates.get("location_evidence_thresholds_passed") is True, "location evidence gate must already be true")
    gates["database_transaction_committed"] = True
    gates["database_transaction_verified"] = True
    source["quality_gates"] = gates
    source["database_transaction_marker"] = marker
    source["database_execution_proof"] = {
        "proof_hash": execution_proof_hash,
        "bundle_source_hash": bundle_manifest.get("source_snapshot_hash"),
        "target_env": proof.get("target_env"),
        "psql_invoked": True,
        "postgres_connection_used": True,
        "database_mutation_performed": True,
        "live_dws_performed": False,
    }
    write_json(out_json, source)
    result = {
        "status": "READY",
        "mode": "stage2_database_proof_applied",
        "target_month": source.get("target_month"),
        "database_transaction_marker": marker,
        "execution_proof_hash": execution_proof_hash,
        "quality_gates": gates,
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply non-production DB execution proof to a Stage-2 source snapshot.")
    parser.add_argument("--source-json", required=True)
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--execution-proof-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    result = materialize(Path(args.source_json), Path(args.bundle_dir), Path(args.execution_proof_json), Path(args.out_json))
    if args.print_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
