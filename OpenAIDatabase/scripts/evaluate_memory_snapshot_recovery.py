#!/usr/bin/env python3
"""Run the deterministic memory-only snapshot clean-room recovery drill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


DATABASE_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DATABASE_DIR.parent
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import memory_snapshot  # noqa: E402


TASK_ID = "TSK.OpenAIDatabase.PAM1.0018"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PAM1.0018"
CONFIG_SCHEMA = "openai_database.memory_snapshot_recovery_evaluation.v1"
REPORT_SCHEMA = "openai_database.memory_snapshot_recovery_report.v1"
DEFAULT_CONFIG = Path("config/evaluation/memory_snapshot_recovery_v1.json")


class RecoveryEvaluationError(RuntimeError):
    """Stable drill failure that never contains memory statement text."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def sha256_prefixed(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryEvaluationError(f"{label}_json_invalid") from exc
    if not isinstance(value, dict):
        raise RecoveryEvaluationError(f"{label}_shape_invalid")
    return value


def _safe_database_path(database_dir: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise RecoveryEvaluationError(f"{label}_path_invalid")
    relative = Path(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise RecoveryEvaluationError(f"{label}_path_invalid")
    path = (database_dir / relative).resolve()
    database = database_dir.resolve()
    if database not in path.parents:
        raise RecoveryEvaluationError(f"{label}_path_invalid")
    return path


def validate_config(config: Mapping[str, Any]) -> None:
    if (
        config.get("schema_version") != CONFIG_SCHEMA
        or config.get("task_id") != TASK_ID
        or config.get("acceptance_id") != ACCEPTANCE_ID
    ):
        raise RecoveryEvaluationError("recovery_config_identity_invalid")
    source_commit = config.get("source_commit")
    if not isinstance(source_commit, str) or memory_snapshot.SHA_RE.fullmatch(source_commit) is None:
        raise RecoveryEvaluationError("recovery_source_commit_invalid")
    if config.get("smoke_query_iterations_per_surface") != 5:
        raise RecoveryEvaluationError("recovery_smoke_query_count_invalid")
    if config.get("required_negative_cases") != [
        "tampered_member",
        "missing_member",
        "wrong_expected_commit",
    ]:
        raise RecoveryEvaluationError("recovery_negative_cases_invalid")
    if config.get("rto_target_seconds") != 1800 or config.get("local_drill_bound_seconds") != 30:
        raise RecoveryEvaluationError("recovery_rto_gate_invalid")
    generated_at = config.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at.endswith("Z"):
        raise RecoveryEvaluationError("recovery_generated_at_invalid")
    for key in ("policy", "report"):
        value = config.get(key)
        if not isinstance(value, str) or not value:
            raise RecoveryEvaluationError(f"recovery_{key}_path_invalid")
        path = Path(value)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise RecoveryEvaluationError(f"recovery_{key}_path_invalid")


def _git_bytes(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "LC_ALL": "C",
            "TZ": "UTC",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        },
    )
    if result.returncode != 0:
        raise RecoveryEvaluationError("recovery_git_read_failed")
    return result.stdout


def _repository_state(root: Path) -> dict[str, str]:
    refs = _git_bytes(root, "for-each-ref", "--format=%(refname)%00%(objectname)")
    objects = _git_bytes(root, "count-objects", "-v")
    status = _git_bytes(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    return {
        "refs_sha256": sha256_prefixed(refs),
        "objects_sha256": sha256_prefixed(objects),
        "worktree_status_sha256": sha256_prefixed(status),
    }


def _expect_snapshot_error(action: Callable[[], Any], expected: str) -> dict[str, Any]:
    try:
        action()
    except memory_snapshot.SnapshotError as exc:
        observed = str(exc)
        if observed != expected:
            raise RecoveryEvaluationError("recovery_negative_case_error_mismatch") from exc
        return {"status": "PASS", "fail_closed": True, "reason": observed}
    raise RecoveryEvaluationError("recovery_negative_case_did_not_fail_closed")


def _rewrite_snapshot(
    source: Path,
    destination: Path,
    transform: Callable[[dict[str, bytes]], None],
) -> None:
    with zipfile.ZipFile(source, "r") as archive:
        members = {info.filename: archive.read(info) for info in archive.infolist()}
    transform(members)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(members):
            archive.writestr(memory_snapshot._zip_info(name), members[name])


def _tamper_one_member(members: dict[str, bytes]) -> None:
    candidates = sorted(name for name in members if name.endswith("records-0001.jsonl"))
    if len(candidates) != 1 or not members[candidates[0]]:
        raise RecoveryEvaluationError("recovery_tamper_target_invalid")
    payload = bytearray(members[candidates[0]])
    payload[0] ^= 1
    members[candidates[0]] = bytes(payload)


def _remove_required_member(members: dict[str, bytes]) -> None:
    target = "OpenAIDatabase/data/memory/AGENT_MEMORY.md"
    if members.pop(target, None) is None:
        raise RecoveryEvaluationError("recovery_missing_target_invalid")


def _embedded_query(
    restored_root: Path,
    record_id: str,
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    tool = restored_root / "tools/memory_snapshot.py"
    database = restored_root / "OpenAIDatabase"
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(tool),
                "query",
                "--database-dir",
                str(database),
                "--record-id",
                record_id,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
            env={
                "LC_ALL": "C",
                "TZ": "UTC",
                "PYTHONHASHSEED": "0",
                "PYTHONNOUSERSITE": "1",
                "PATH": os.environ.get("PATH", ""),
            },
        )
    except subprocess.TimeoutExpired as exc:
        raise RecoveryEvaluationError("recovery_embedded_query_timeout") from exc
    if result.returncode != 0:
        raise RecoveryEvaluationError("recovery_embedded_query_failed")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RecoveryEvaluationError("recovery_embedded_query_output_invalid") from exc
    if not isinstance(value, dict) or value.get("status") != "PASS":
        raise RecoveryEvaluationError("recovery_embedded_query_output_invalid")
    return value


def _commit_payload_match(
    repository_root: Path,
    restored_root: Path,
    source_commit: str,
    validation: memory_snapshot.SnapshotValidation,
) -> dict[str, Any]:
    checked = 0
    matched = 0
    for descriptor in validation.manifest["files"]:
        if descriptor["origin"] != "git_commit":
            continue
        checked += 1
        snapshot_path = str(descriptor["path"])
        relative = snapshot_path.removeprefix("OpenAIDatabase/")
        source = memory_snapshot._git_file(repository_root, source_commit, relative)
        snapshot = validation.payloads[snapshot_path]
        restored = (restored_root / snapshot_path).read_bytes()
        if source == snapshot == restored:
            matched += 1
    if not checked or matched != checked:
        raise RecoveryEvaluationError("recovery_commit_payload_mismatch")
    return {
        "checked_file_count": checked,
        "matched_file_count": matched,
        "hash_identical_percent": 100,
        "status": "PASS",
    }


def evaluate(database_dir: Path, config: Mapping[str, Any]) -> tuple[dict[str, Any], float]:
    validate_config(config)
    database = database_dir.expanduser().resolve(strict=True)
    root = database.parent
    source_commit = str(config["source_commit"])
    policy_path = _safe_database_path(database, config["policy"], "policy")
    policy = memory_snapshot.load_policy(policy_path)
    state_before = _repository_state(root)
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="memory-snapshot-recovery-") as temp_dir:
        sandbox = Path(temp_dir).resolve()
        export_a, asset_a = memory_snapshot.export_snapshot(
            database, policy, source_commit, sandbox / "export-a"
        )
        export_idempotent, repeated_asset = memory_snapshot.export_snapshot(
            database, policy, source_commit, sandbox / "export-a"
        )
        export_b, asset_b = memory_snapshot.export_snapshot(
            database, policy, source_commit, sandbox / "export-b"
        )
        if (
            repeated_asset != asset_a
            or export_idempotent.get("idempotent") is not True
            or asset_a.read_bytes() != asset_b.read_bytes()
            or export_a["asset_sha256"] != export_b["asset_sha256"]
        ):
            raise RecoveryEvaluationError("recovery_snapshot_not_deterministic")

        validation = memory_snapshot.validate_snapshot(asset_a, source_commit)
        record_id = str(validation.manifest["smoke_query_record_id"])
        iterations = int(config["smoke_query_iterations_per_surface"])
        snapshot_queries = [
            memory_snapshot.query_snapshot(asset_a, source_commit, record_id)
            for _ in range(iterations)
        ]
        if len({canonical_json_bytes(row) for row in snapshot_queries}) != 1:
            raise RecoveryEvaluationError("recovery_snapshot_query_not_deterministic")

        restored_root = sandbox / "restored"
        restore = memory_snapshot.restore_snapshot(asset_a, source_commit, restored_root)
        restored_queries = [
            _embedded_query(
                restored_root,
                record_id,
                timeout_seconds=int(config["local_drill_bound_seconds"]),
            )
            for _ in range(iterations)
        ]
        if (
            len({canonical_json_bytes(row) for row in restored_queries}) != 1
            or restored_queries[0] != snapshot_queries[0]
        ):
            raise RecoveryEvaluationError("recovery_clean_room_query_mismatch")

        payload_match = _commit_payload_match(
            root, restored_root, source_commit, validation
        )
        recovery_elapsed = time.monotonic() - started
        if recovery_elapsed > int(config["local_drill_bound_seconds"]):
            raise RecoveryEvaluationError("recovery_local_rto_exceeded")

        tampered = sandbox / "tampered" / asset_a.name
        _rewrite_snapshot(asset_a, tampered, _tamper_one_member)
        missing = sandbox / "missing" / asset_a.name
        _rewrite_snapshot(asset_a, missing, _remove_required_member)
        negative_cases = {
            "tampered_member": _expect_snapshot_error(
                lambda: memory_snapshot.validate_snapshot(tampered, source_commit),
                "snapshot_file_hash_mismatch",
            ),
            "missing_member": _expect_snapshot_error(
                lambda: memory_snapshot.validate_snapshot(missing, source_commit),
                "snapshot_file_manifest_invalid",
            ),
            "wrong_expected_commit": _expect_snapshot_error(
                lambda: memory_snapshot.validate_snapshot(asset_a, "0" * 40),
                "snapshot_manifest_identity_invalid",
            ),
        }

        report = {
            "schema_version": REPORT_SCHEMA,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "generated_at": config["generated_at"],
            "status": "PASS",
            "source": {
                "repository": policy["source_repository"],
                "commit": source_commit,
                "policy_sha256": sha256_prefixed(policy_path.read_bytes()),
                "config_sha256": sha256_prefixed(canonical_json_bytes(config) + b"\n"),
            },
            "snapshot": {
                "asset_name": asset_a.name,
                "asset_bytes": export_a["asset_bytes"],
                "asset_sha256": export_a["asset_sha256"],
                "payload_tree_sha256": validation.manifest["payload_tree_sha256"],
                "file_count": validation.result["file_count"],
                "commit_file_count": validation.result["commit_file_count"],
                "runtime_file_count": validation.result["runtime_file_count"],
                "raw_file_count": validation.result["raw_file_count"],
                "release_candidate": validation.result["release_candidate"],
                "all_members_from_source_commit": validation.result[
                    "all_members_from_source_commit"
                ],
                "deterministic_export_count": 2,
                "idempotent_reexport_pass": True,
                "integrity_verified": True,
                "authenticity_claim": False,
            },
            "canonical": validation.result["canonical"],
            "roundtrip": {
                **payload_match,
                "atomic_restore": restore["atomic_publish"],
                "partial_restore_count": restore["partial_restore_count"],
            },
            "offline_query_smoke": {
                "record_id": record_id,
                "snapshot_query_pass_count": len(snapshot_queries),
                "clean_room_query_pass_count": len(restored_queries),
                "total_pass_count": len(snapshot_queries) + len(restored_queries),
                "network_request_count": 0,
                "target_github_write_count": 0,
                "status": "PASS",
            },
            "negative_cases": negative_cases,
            "rto": {
                "target_seconds": config["rto_target_seconds"],
                "local_drill_bound_seconds": config["local_drill_bound_seconds"],
                "observed_less_than_seconds": config["local_drill_bound_seconds"],
                "status": "PASS",
            },
            "release": {
                "repository": policy["release"]["repository"],
                "visibility": policy["release"]["visibility"],
                "publish_task_id": policy["release"]["publish_task_id"],
                "asset_published": False,
                "repository_archive_or_bundle_created": False,
                "archive_branch_created": False,
                "public_release_safe_record_count": validation.result[
                    "public_release"
                ]["public_release_safe_record_count"],
            },
        }

    state_after = _repository_state(root)
    if state_before != state_after:
        raise RecoveryEvaluationError("recovery_repository_state_changed")
    report["repository_immutability"] = {
        "refs_unchanged": True,
        "objects_unchanged": True,
        "worktree_status_unchanged": True,
        "status": "PASS",
    }
    return report, recovery_elapsed


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=DATABASE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source-commit", help="Override the drill commit for ephemeral acceptance.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--ephemeral", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        database = args.database_dir.expanduser().resolve(strict=True)
        config_path = _safe_database_path(database, args.config.as_posix(), "config")
        config = _load_json(config_path, "recovery_config")
        if args.source_commit is not None:
            if not args.ephemeral:
                raise RecoveryEvaluationError("recovery_source_override_requires_ephemeral")
            config = {**config, "source_commit": args.source_commit}
        report_path = _safe_database_path(database, config.get("report"), "report")
        report, elapsed = evaluate(database, config)
        rendered = canonical_json_bytes(report) + b"\n"
        if args.ephemeral:
            print(rendered.decode("utf-8"), end="")
            return 0
        if args.write:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_bytes(rendered)
        else:
            if not report_path.is_file() or report_path.read_bytes() != rendered:
                raise RecoveryEvaluationError("recovery_report_stale_or_missing")
        print(
            json.dumps(
                {
                    "schema_version": REPORT_SCHEMA,
                    "status": "PASS",
                    "mode": "write" if args.write else "check",
                    "report": report_path.relative_to(database).as_posix(),
                    "source_commit": config["source_commit"],
                    "canonical_hash_identical_percent": report["roundtrip"][
                        "hash_identical_percent"
                    ],
                    "offline_query_pass_count": report["offline_query_smoke"][
                        "total_pass_count"
                    ],
                    "negative_case_pass_count": len(report["negative_cases"]),
                    "recovery_elapsed_seconds": round(elapsed, 3),
                    "local_drill_bound_seconds": config["local_drill_bound_seconds"],
                },
                sort_keys=True,
            )
        )
        return 0
    except (OSError, RecoveryEvaluationError, memory_snapshot.SnapshotError) as exc:
        reason = str(exc) if isinstance(exc, (RecoveryEvaluationError, memory_snapshot.SnapshotError)) else "recovery_io_error"
        print(
            json.dumps(
                {
                    "schema_version": REPORT_SCHEMA,
                    "status": "FAIL_CLOSED",
                    "reason": reason,
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
