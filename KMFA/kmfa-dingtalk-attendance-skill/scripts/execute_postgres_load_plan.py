#!/usr/bin/env python3
"""Fail-closed executor for KMFA PostgreSQL landing load plans."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from validate_postgres_load_plan import validate as validate_load_plan


ALLOW_ENV = "KMFA_ALLOW_NONPROD_POSTGRES_EXECUTION"
DSN_ENV = "KMFA_ATTENDANCE_POSTGRES_DSN"
TARGET_ENV_ENV = "KMFA_POSTGRES_TARGET_ENV"
NONPRODUCTION_ENVS = {"local", "dev", "development", "test", "testing", "stage", "staging", "nonprod", "sandbox"}
PRODUCTION_TOKEN_RE = re.compile(r"(^|[-_.])(?:prod|production|live)([-_.]|$)")


def tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text


def redact_database_url(database_url: str) -> str:
    if not database_url:
        return ""
    try:
        parts = urlsplit(database_url)
    except ValueError:
        return "<invalid-url>"
    if not parts.netloc:
        return database_url
    netloc = parts.netloc
    if "@" in netloc:
        userinfo, hostinfo = netloc.rsplit("@", 1)
        username = userinfo.split(":", 1)[0]
        netloc = f"{username}:***@{hostinfo}" if username else f"***@{hostinfo}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def database_url_looks_production(database_url: str) -> bool:
    if not database_url:
        return False
    try:
        parts = urlsplit(database_url)
    except ValueError:
        return True
    host = (parts.hostname or "").lower()
    db_name = parts.path.strip("/").lower()
    return any(PRODUCTION_TOKEN_RE.search(value) for value in [host, db_name] if value)


def build_psql_command(psql_bin: str, database_url: str, schema: Path, views: Path, sql: Path) -> list[str]:
    return [
        psql_bin,
        database_url,
        "--set",
        "ON_ERROR_STOP=on",
        "--file",
        str(schema),
        "--file",
        str(views),
        "--file",
        str(sql),
    ]


def preflight(args: argparse.Namespace) -> dict[str, object]:
    schema = Path(args.schema)
    views = Path(args.views)
    bundle_dir = Path(args.bundle_dir)
    sql = Path(args.sql) if args.sql else bundle_dir / "postgres_load_plan.sql"
    database_url = args.database_url or os.environ.get(DSN_ENV, "")
    target_env = (args.target_env or os.environ.get(TARGET_ENV_ENV, "")).strip()
    target_env_normalized = target_env.lower()
    allow_flag = os.environ.get(ALLOW_ENV) == "1"
    failures: list[str] = []

    static_result = validate_load_plan(schema, bundle_dir, sql)
    if static_result.get("status") != "pass":
        failures.append("static_validation_failed")
        failures.extend(str(item) for item in static_result.get("failures", []))
    if not views.is_file():
        failures.append(f"views_sql_missing:{views}")

    if args.execute:
        if not allow_flag:
            failures.append("nonprod_execution_not_allowed")
        if not args.acknowledge_nonprod_mutation:
            failures.append("nonprod_mutation_ack_missing")
        if not database_url:
            failures.append(f"database_url_missing:{DSN_ENV}")
        if not target_env:
            failures.append(f"target_env_missing:{TARGET_ENV_ENV}")
        elif target_env_normalized not in NONPRODUCTION_ENVS:
            failures.append(f"target_env_not_nonproduction:{target_env}")
        if database_url and database_url_looks_production(database_url):
            failures.append("database_url_looks_production")

    return {
        "status": "fail" if failures else "pass",
        "mode": "postgres_load_plan_execution_guard",
        "schema": str(schema),
        "views": str(views),
        "bundle_dir": str(bundle_dir),
        "sql": str(sql),
        "target_env": target_env,
        "target_env_source": "arg" if args.target_env else ("env" if os.environ.get(TARGET_ENV_ENV) else ""),
        "database_url_redacted": redact_database_url(database_url),
        "execute_requested": bool(args.execute),
        "acknowledge_nonprod_mutation": bool(args.acknowledge_nonprod_mutation),
        "allow_env": ALLOW_ENV,
        "allow_env_enabled": allow_flag,
        "checks": {
            "static_validation_passed": static_result.get("status") == "pass",
            "views_sql_present": views.is_file(),
            "target_env_nonproduction": target_env_normalized in NONPRODUCTION_ENVS,
            "database_url_not_production_like": bool(database_url) and not database_url_looks_production(database_url),
            "execution_guard_satisfied": args.execute and not failures,
        },
        "failures": failures,
        "psql_invoked": False,
        "postgres_connection_used": False,
        "database_mutation_attempted": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }


def execute(result: dict[str, object], args: argparse.Namespace) -> dict[str, object]:
    database_url = args.database_url or os.environ.get(DSN_ENV, "")
    schema = Path(str(result["schema"]))
    views = Path(str(result["views"]))
    sql = Path(str(result["sql"]))
    command = build_psql_command(args.psql_bin, database_url, schema, views, sql)
    redacted_command = build_psql_command(args.psql_bin, redact_database_url(database_url), schema, views, sql)
    env = os.environ.copy()
    env.setdefault("PGAPPNAME", "kmfa_attendance_nonprod_loader")
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    result.update({
        "psql_invoked": True,
        "postgres_connection_used": True,
        "database_mutation_attempted": True,
        "database_mutation_performed": proc.returncode == 0,
        "psql_command_redacted": redacted_command,
        "psql_returncode": proc.returncode,
        "psql_stdout_tail": tail(proc.stdout),
        "psql_stderr_tail": tail(proc.stderr),
    })
    if proc.returncode != 0:
        result["status"] = "fail"
        failures = list(result.get("failures", []))
        failures.append(f"psql_exit_code:{proc.returncode}")
        result["failures"] = failures
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute a KMFA PostgreSQL load plan only after explicit non-production approval.")
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--views", required=True)
    parser.add_argument("--sql", default="")
    parser.add_argument("--database-url", default="")
    parser.add_argument("--target-env", default="")
    parser.add_argument("--psql-bin", default="psql")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--acknowledge-nonprod-mutation", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    result = preflight(args)
    if args.execute and result["status"] == "pass":
        result = execute(result, args)
    if args.print_json or result["status"] == "fail":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
