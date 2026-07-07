#!/usr/bin/env python3
"""Verify a PostgreSQL landing bundle is visible in a non-production DB."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from execute_postgres_load_plan import (
    ALLOW_ENV,
    DSN_ENV,
    NONPRODUCTION_ENVS,
    TARGET_ENV_ENV,
    database_url_looks_production,
    fingerprint,
    redact_database_url,
    scrub_tail,
)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def quote_sql(value: Any) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def expected_counts(bundle_dir: Path, tables: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in tables:
        if table in {"policy_version", "canonical_month_snapshot", "stage2_consensus_certificate"}:
            counts[table] = 1
        else:
            counts[table] = count_jsonl(bundle_dir / f"{table}.jsonl")
    return counts


def build_query(bundle_dir: Path, tables: list[str]) -> str:
    manifest = load_json(bundle_dir / "db_landing_manifest.json")
    policy = load_json(bundle_dir / "policy_version.json")
    snapshot = load_json(bundle_dir / "canonical_month_snapshot.json")
    target_month = manifest.get("target_month")
    policy_version_id = policy.get("policy_version_id")
    snapshot_id = snapshot.get("snapshot_id")
    canonical_hash = snapshot.get("canonical_hash")
    parts: list[str] = []
    if "policy_version" in tables:
        parts.extend([
            quote_sql("policy_version"),
            f"(SELECT count(*) FROM policy_version WHERE policy_version_id = {quote_sql(policy_version_id)}::uuid)",
        ])
    if "canonical_month_snapshot" in tables:
        parts.extend([
            quote_sql("canonical_month_snapshot"),
            f"(SELECT count(*) FROM canonical_month_snapshot WHERE snapshot_id = {quote_sql(snapshot_id)}::uuid AND canonical_hash = {quote_sql(canonical_hash)})",
        ])
    if "stage2_shadow_run" in tables:
        parts.extend([
            quote_sql("stage2_shadow_run"),
            f"(SELECT count(*) FROM stage2_shadow_run WHERE target_month = {quote_sql(target_month)} AND canonical_hash = {quote_sql(canonical_hash)})",
        ])
    if "stage2_consensus_certificate" in tables:
        certificate = load_json(bundle_dir / "stage2_consensus_certificate.json")
        parts.extend([
            quote_sql("stage2_consensus_certificate"),
            f"(SELECT count(*) FROM stage2_consensus_certificate WHERE stage2_certificate_id = {quote_sql(certificate.get('stage2_certificate_id'))}::uuid AND accepted = true)",
        ])
    if "attendance_day_fact" in tables:
        parts.extend([
            quote_sql("attendance_day_fact"),
            f"(SELECT count(*) FROM attendance_day_fact WHERE target_month = {quote_sql(target_month)} AND policy_version_id = {quote_sql(policy_version_id)}::uuid)",
        ])
    if "payroll_baseline_attendance" in tables:
        parts.extend([
            quote_sql("payroll_baseline_attendance"),
            f"(SELECT count(*) FROM payroll_baseline_attendance WHERE target_month = {quote_sql(target_month)} AND canonical_hash = {quote_sql(canonical_hash)})",
        ])
    return "SET search_path TO kmfa_attendance, public; SELECT jsonb_build_object(" + ", ".join(parts) + ")::text;"


def run_psql(args: argparse.Namespace, database_url: str, query: str) -> subprocess.CompletedProcess[str]:
    command = [
        args.psql_bin,
        database_url,
        "--set",
        "ON_ERROR_STOP=on",
        "--tuples-only",
        "--no-align",
        "--command",
        query,
    ]
    env = os.environ.copy()
    env.setdefault("PGAPPNAME", "kmfa_attendance_nonprod_state_verifier")
    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)


def verify(args: argparse.Namespace) -> dict[str, Any]:
    bundle_dir = Path(args.bundle_dir)
    manifest = load_json(bundle_dir / "db_landing_manifest.json")
    load_order = load_json(bundle_dir / "load_order.json")
    tables = load_order.get("tables") if isinstance(load_order.get("tables"), list) else []
    database_url = args.database_url or os.environ.get(DSN_ENV, "")
    target_env = (args.target_env or os.environ.get(TARGET_ENV_ENV, "")).strip()
    target_env_normalized = target_env.lower()
    allow_flag = os.environ.get(ALLOW_ENV) == "1"
    expected = expected_counts(bundle_dir, tables)
    failures: list[str] = []
    if not tables:
        failures.append("load_order_missing")
    if not args.acknowledge_nonprod_read:
        failures.append("nonprod_read_ack_missing")
    if not allow_flag:
        failures.append("nonprod_execution_not_allowed")
    if not database_url:
        failures.append(f"database_url_missing:{DSN_ENV}")
    if not target_env:
        failures.append(f"target_env_missing:{TARGET_ENV_ENV}")
    elif target_env_normalized not in NONPRODUCTION_ENVS:
        failures.append(f"target_env_not_nonproduction:{target_env}")
    if database_url and database_url_looks_production(database_url):
        failures.append("database_url_looks_production")

    result: dict[str, Any] = {
        "status": "fail" if failures else "pass",
        "mode": "postgres_landing_state_verification",
        "target_month": manifest.get("target_month"),
        "bundle_mode": manifest.get("mode"),
        "bundle_source_hash": manifest.get("source_snapshot_hash") or manifest.get("canonical_snapshot_hash"),
        "bundle_dir_fingerprint": fingerprint(str(bundle_dir.expanduser().resolve())),
        "tables_checked": tables,
        "expected_counts": expected,
        "observed_counts": {},
        "target_env": target_env,
        "database_url_redacted": redact_database_url(database_url),
        "database_url_fingerprint": fingerprint(database_url) if database_url else "",
        "allow_env": ALLOW_ENV,
        "allow_env_enabled": allow_flag,
        "acknowledge_nonprod_read": bool(args.acknowledge_nonprod_read),
        "checks": {
            "target_env_nonproduction": target_env_normalized in NONPRODUCTION_ENVS,
            "database_url_not_production_like": bool(database_url) and not database_url_looks_production(database_url),
            "counts_match": False,
        },
        "failures": failures,
        "psql_invoked": False,
        "postgres_connection_used": False,
        "database_mutation_attempted": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }
    if failures:
        return result

    query = build_query(bundle_dir, tables)
    proc = run_psql(args, database_url, query)
    result.update({
        "psql_invoked": True,
        "postgres_connection_used": True,
        "psql_bin": Path(args.psql_bin).name,
        "psql_returncode": proc.returncode,
        "psql_stdout_tail": scrub_tail(proc.stdout, database_url=database_url, paths=[Path(args.psql_bin)]),
        "psql_stderr_tail": scrub_tail(proc.stderr, database_url=database_url, paths=[Path(args.psql_bin)]),
    })
    if proc.returncode != 0:
        result["status"] = "fail"
        result["failures"] = failures + [f"psql_exit_code:{proc.returncode}"]
        return result
    try:
        observed = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        result["status"] = "fail"
        result["failures"] = failures + [f"psql_json_parse_failed:{type(exc).__name__}"]
        return result
    result["observed_counts"] = {table: int(observed.get(table) or 0) for table in tables}
    count_failures = [
        f"count_mismatch:{table}:expected={expected[table]}:observed={result['observed_counts'][table]}"
        for table in tables
        if result["observed_counts"][table] != expected[table]
    ]
    if count_failures:
        result["status"] = "fail"
        result["failures"] = failures + count_failures
    result["checks"]["counts_match"] = not count_failures
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify PostgreSQL landing rows against a private KMFA DB landing bundle.")
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--database-url", default="")
    parser.add_argument("--target-env", default="")
    parser.add_argument("--psql-bin", default="psql")
    parser.add_argument("--acknowledge-nonprod-read", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    result = verify(args)
    if args.print_json or result["status"] == "fail":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
