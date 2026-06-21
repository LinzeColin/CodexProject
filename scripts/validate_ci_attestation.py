#!/usr/bin/env python3
"""Create and validate post-commit governance CI attestations."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
VALID_CONCLUSIONS = {"success", "failure", "cancelled", "skipped", "timed_out", "action_required"}


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def commit_exists(sha: str) -> bool:
    return bool(git_output("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"))


def payload_hash(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("evidence_hash", None)
    blob = json.dumps(clone, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_attestation(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "attestation_id": args.run_id,
        "binds_run_manifest": args.binds_run_manifest or "NOT_APPLICABLE",
        "workflow": args.workflow,
        "workflow_run_id": str(args.run_id_number),
        "workflow_run_attempt": str(args.run_attempt),
        "job_id": args.job_id or "UNKNOWN",
        "commit_sha": args.commit_sha,
        "base_ref": args.base_ref or "UNKNOWN",
        "tree_hash": git_output("rev-parse", f"{args.commit_sha}^{{tree}}") or "UNKNOWN",
        "conclusion": args.conclusion,
        "finished_at": args.finished_at or datetime.now(UTC).replace(microsecond=0).isoformat(),
        "artifact_ref": args.artifact_ref or "NOT_APPLICABLE",
        "fact_level": "EXTRACTED",
    }
    payload["evidence_hash"] = payload_hash(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "attestation_id",
        "workflow",
        "workflow_run_id",
        "workflow_run_attempt",
        "commit_sha",
        "conclusion",
        "finished_at",
        "evidence_hash",
    }
    missing = sorted(field for field in required if not payload.get(field))
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    if payload.get("conclusion") not in VALID_CONCLUSIONS:
        errors.append(f"invalid conclusion: {payload.get('conclusion')}")
    commit_sha = str(payload.get("commit_sha") or "")
    if commit_sha and not commit_exists(commit_sha):
        errors.append(f"commit_sha does not resolve locally: {commit_sha}")
    if payload.get("evidence_hash") != payload_hash(payload):
        errors.append("evidence_hash does not match attestation payload")
    return errors


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def command_write(args: argparse.Namespace) -> int:
    payload = build_attestation(args)
    errors = validate_payload(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output), "attestation_id": payload["attestation_id"]}, indent=2))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    payload = load_json(Path(args.file))
    errors = validate_payload(payload)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(json.dumps({"status": "PASS", "file": args.file, "attestation_id": payload["attestation_id"]}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    write_parser = subparsers.add_parser("write")
    write_parser.add_argument("--run-id", required=True)
    write_parser.add_argument("--binds-run-manifest", default="")
    write_parser.add_argument("--workflow", required=True)
    write_parser.add_argument("--run-id-number", required=True)
    write_parser.add_argument("--run-attempt", required=True)
    write_parser.add_argument("--job-id", default="")
    write_parser.add_argument("--commit-sha", required=True)
    write_parser.add_argument("--base-ref", default="")
    write_parser.add_argument("--conclusion", required=True, choices=sorted(VALID_CONCLUSIONS))
    write_parser.add_argument("--finished-at", default="")
    write_parser.add_argument("--artifact-ref", default="")
    write_parser.add_argument("--output", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--file", required=True)
    args = parser.parse_args(argv)
    if args.command == "write":
        return command_write(args)
    return command_validate(args)


if __name__ == "__main__":
    raise SystemExit(main())
