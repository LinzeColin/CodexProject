from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.integrations.system_orchestrator import (
    orchestrate_child_system,
    orchestration_runs_frame,
    register_default_systems,
    sync_default_system_artifacts,
    system_artifacts_frame,
    system_registry_frame,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="PFIOS local mother-child system orchestrator.")
    parser.add_argument("--db", default="", help="Optional ResearchBus SQLite path.")
    sub = parser.add_subparsers(required=True)

    register = sub.add_parser("register")
    register.add_argument("--json", action="store_true")

    artifacts = sub.add_parser("sync-artifacts")
    artifacts.add_argument("--limit-per-system", type=int, default=200)
    artifacts.add_argument("--json", action="store_true")

    status = sub.add_parser("status")
    status.add_argument("--limit", type=int, default=200)
    status.add_argument("--json", action="store_true")

    run = sub.add_parser("run")
    run.add_argument("--system", required=True)
    run.add_argument("--action", choices=["health", "sync", "standalone"], default="health")
    run.add_argument("--execute", action="store_true", help="Actually execute the registered command. Default is dry-run registration only.")
    run.add_argument("--timeout-seconds", type=int, default=120)
    run.add_argument("--json", action="store_true")

    args = parser.parse_args()
    db_path = Path(args.db).expanduser() if args.db else None

    if hasattr(args, "limit_per_system"):
        payload = sync_default_system_artifacts(db_path=db_path, limit_per_system=args.limit_per_system)
        _print(payload, as_json=args.json)
        return

    if hasattr(args, "system"):
        result = orchestrate_child_system(
            args.system,
            action=args.action,
            execute=args.execute,
            db_path=db_path,
            timeout_seconds=args.timeout_seconds,
        )
        _print(result.to_dict(), as_json=args.json)
        return

    if args.__dict__.get("limit", None) is not None:
        payload = {
            "systems": system_registry_frame(db_path).to_dict("records"),
            "artifacts": system_artifacts_frame(db_path, limit=args.limit).to_dict("records"),
            "runs": orchestration_runs_frame(db_path, limit=args.limit).to_dict("records"),
        }
        _print(payload, as_json=args.json)
        return

    payload = register_default_systems(db_path)
    _print(payload, as_json=args.json)


def _print(payload, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        print(payload)


if __name__ == "__main__":
    main()
