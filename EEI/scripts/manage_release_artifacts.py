#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MANIFEST = Path("manifest.txt")
DIRECTORY_TREE = Path("DIRECTORY_TREE.txt")
CHECKSUMS = Path("CHECKSUMS.sha256")
RELEASE_EVIDENCE = Path("artifacts/release_evidence_t1211.json")
OPERATION_LOG = Path("artifacts/release_operation_log_t1211.jsonl")

REQUIRED_RELEASE_PATHS = {
    str(MANIFEST),
    str(DIRECTORY_TREE),
    str(CHECKSUMS),
    str(RELEASE_EVIDENCE),
    str(OPERATION_LOG),
    "scripts/manage_release_artifacts.py",
}

TRACKED_PATH_EXCLUDES = {
    "apps/web/next-env.d.ts",
}

CHECKSUM_EXCLUDES = {str(CHECKSUMS)}


def run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return completed.stdout


def tracked_paths() -> list[str]:
    paths = run_git("ls-files").splitlines()
    combined = set(paths) | REQUIRED_RELEASE_PATHS
    combined -= TRACKED_PATH_EXCLUDES
    return sorted(path for path in combined if path and not path.endswith("/"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def render_manifest(paths: list[str]) -> str:
    return "\n".join(paths) + "\n"


def render_tree(paths: list[str]) -> str:
    tree: dict[str, Any] = {}
    for path in paths:
        cursor = tree
        parts = path.split("/")
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor.setdefault("__files__", []).append(parts[-1])

    lines = ["Enterprise_Ecosystem_Intelligence_release"]

    def walk(node: dict[str, Any], prefix: str = "") -> None:
        dirs = sorted(key for key in node if key != "__files__")
        files = sorted(node.get("__files__", []))
        entries = [(name, True) for name in dirs] + [(name, False) for name in files]
        for index, (name, is_dir) in enumerate(entries):
            connector = "└── " if index == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{name}")
            if is_dir:
                extension = "    " if index == len(entries) - 1 else "│   "
                walk(node[name], prefix + extension)

    walk(tree)
    return "\n".join(lines) + "\n"


def render_checksums(paths: list[str]) -> str:
    lines = []
    for path in paths:
        if path in CHECKSUM_EXCLUDES:
            continue
        target = ROOT / path
        if not target.is_file():
            raise AssertionError(f"missing file for checksum: {path}")
        lines.append(f"{sha256_file(target)}  {path}")
    return "\n".join(lines) + "\n"


def release_evidence(remote_status: str, remote_run_id: str, remote_job_id: str) -> dict[str, Any]:
    commit = run_git("rev-parse", "--short", "HEAD").strip()
    return {
        "schema_version": 1,
        "artifact_id": "release-t1211-manifest-checksum-evidence",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_commit": commit,
        "system": {
            "zh_name": "商域图谱",
            "en_name": "Enterprise Ecosystem Intelligence",
            "subtitle": "企业商业版图与供应链递归探索系统",
        },
        "task_id": "T1211",
        "acceptance_ids": ["A175", "A177"],
        "artifact_paths": sorted(REQUIRED_RELEASE_PATHS),
        "required_commands": [
            "make verify",
            "make verify-g2-db",
            "sha256sum -c CHECKSUMS.sha256",
        ],
        "release_checks": [
            "manifest.txt is generated from git ls-files plus required release evidence files",
            "DIRECTORY_TREE.txt is generated from manifest.txt",
            "CHECKSUMS.sha256 covers every manifest file except CHECKSUMS.sha256",
            (
                "artifacts/release_operation_log_t1211.jsonl records the release "
                "artifact publish operation"
            ),
        ],
        "rollback": {
            "procedure": [
                "Revert the release evidence commit.",
                "Regenerate manifest.txt, DIRECTORY_TREE.txt and CHECKSUMS.sha256.",
                "Run make verify and sha256sum -c CHECKSUMS.sha256.",
                "Push a restoring commit and cite the CI run in the development record.",
            ],
            "owner": "repository owner",
        },
        "remote_verification": {
            "status": remote_status,
            "run_id": remote_run_id,
            "job_id": remote_job_id,
        },
    }


def operation_log_entry() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "operation_id": "release-t1211-publish-reproducible-artifacts",
        "operation_type": "release_artifact_publish",
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "task_id": "T1211",
        "acceptance_ids": ["A175", "A177"],
        "actor": "Codex",
        "artifact_paths": sorted(REQUIRED_RELEASE_PATHS),
        "rollback": "Revert the release evidence commit and regenerate release artifacts.",
    }


def operation_log_entries() -> list[dict[str, Any]]:
    target = ROOT / OPERATION_LOG
    if not target.exists():
        return []
    entries = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def ensure_operation_log_entry() -> None:
    entries = operation_log_entries()
    if any(
        entry.get("operation_id") == "release-t1211-publish-reproducible-artifacts"
        for entry in entries
    ):
        return
    entries.append(operation_log_entry())
    payload = "\n".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) for entry in entries)
    write_text(OPERATION_LOG, payload + "\n")


def generate(args: argparse.Namespace) -> None:
    evidence = release_evidence(args.remote_status, args.remote_run_id, args.remote_job_id)
    write_text(RELEASE_EVIDENCE, json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    ensure_operation_log_entry()
    paths = tracked_paths()
    write_text(MANIFEST, render_manifest(paths))
    write_text(DIRECTORY_TREE, render_tree(paths))
    write_text(CHECKSUMS, render_checksums(paths))
    validate(None)
    print(
        json.dumps(
            {
                "generated": True,
                "manifest_paths": len(paths),
                "checksum_paths": len(paths) - len(CHECKSUM_EXCLUDES),
                "release_evidence": str(RELEASE_EVIDENCE),
                "operation_log": str(OPERATION_LOG),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_checksums() -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in (ROOT / CHECKSUMS).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, path = line.split("  ", 1)
        checksums[path] = digest
    return checksums


def validate(_: argparse.Namespace | None = None) -> None:
    paths = tracked_paths()
    expected_manifest = render_manifest(paths)
    actual_manifest = (ROOT / MANIFEST).read_text(encoding="utf-8")
    if actual_manifest != expected_manifest:
        raise AssertionError("manifest.txt is not synchronized with tracked release paths")

    expected_tree = render_tree(paths)
    actual_tree = (ROOT / DIRECTORY_TREE).read_text(encoding="utf-8")
    if actual_tree != expected_tree:
        raise AssertionError("DIRECTORY_TREE.txt is not synchronized with manifest.txt")

    expected_checksum_paths = [path for path in paths if path not in CHECKSUM_EXCLUDES]
    checksums = parse_checksums()
    if sorted(checksums) != expected_checksum_paths:
        raise AssertionError("CHECKSUMS.sha256 path set does not match manifest.txt")
    for path, digest in checksums.items():
        actual = sha256_file(ROOT / path)
        if actual != digest:
            raise AssertionError(f"checksum mismatch for {path}")

    evidence = json.loads((ROOT / RELEASE_EVIDENCE).read_text(encoding="utf-8"))
    if evidence.get("task_id") != "T1211":
        raise AssertionError("release evidence must cite T1211")
    if set(evidence.get("acceptance_ids", [])) != {"A175", "A177"}:
        raise AssertionError("release evidence must cite A175 and A177")
    if set(evidence.get("artifact_paths", [])) != REQUIRED_RELEASE_PATHS:
        raise AssertionError("release evidence artifact_paths mismatch")
    if evidence.get("remote_verification", {}).get("status") not in {"PENDING", "PASS"}:
        raise AssertionError("remote verification status must be PENDING or PASS")

    entries = operation_log_entries()
    by_operation = defaultdict(list)
    for entry in entries:
        by_operation[entry.get("operation_id")].append(entry)
    publish_entries = by_operation["release-t1211-publish-reproducible-artifacts"]
    if len(publish_entries) != 1:
        raise AssertionError("operation log must contain one T1211 publish entry")
    publish = publish_entries[0]
    if publish.get("operation_type") != "release_artifact_publish":
        raise AssertionError("operation log publish entry type mismatch")
    if set(publish.get("acceptance_ids", [])) != {"A175", "A177"}:
        raise AssertionError("operation log must cite A175 and A177")
    if set(publish.get("artifact_paths", [])) != REQUIRED_RELEASE_PATHS:
        raise AssertionError("operation log artifact_paths mismatch")

    print(
        json.dumps(
            {
                "valid": True,
                "manifest_paths": len(paths),
                "checksum_paths": len(checksums),
                "remote_status": evidence["remote_verification"]["status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--remote-status", choices=["PENDING", "PASS"], default="PENDING")
    generate_parser.add_argument("--remote-run-id", default="")
    generate_parser.add_argument("--remote-job-id", default="")
    subparsers.add_parser("validate")
    args = parser.parse_args()

    try:
        if args.command == "generate":
            generate(args)
        else:
            validate(args)
    except (AssertionError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"Release artifact validation: FAIL - {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
