#!/usr/bin/env python3
"""Fail closed when a public Cloudflare distribution contains private material."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_FILE = REPO_ROOT / "governance/cloudflare/projects.yaml"
FORBIDDEN_SUFFIXES = {
    ".db",
    ".duckdb",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
}
FORBIDDEN_NAMES = {".env", ".env.local", "id_ed25519", "id_rsa"}
TEXT_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "local_absolute_path": re.compile(r"(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\\\Users\\\\)"),
    "openai_api_key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "cloudflare_token_value": re.compile(
        r"CLOUDFLARE_API_TOKEN\s*[:=]\s*['\"]?[A-Za-z0-9_-]{20,}",
        re.IGNORECASE,
    ),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}


def scan_path(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.is_dir():
        return [f"missing_distribution: {root}"]
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        return [f"empty_distribution: {root}"]
    if not (root / "index.html").is_file():
        findings.append(f"missing_index_html: {root}")
    for path in files:
        relative = path.relative_to(root)
        lowered_name = path.name.lower()
        if lowered_name in FORBIDDEN_NAMES:
            findings.append(f"forbidden_filename: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(f"forbidden_file_type: {relative}")
        try:
            payload = path.read_bytes()
        except OSError as exc:
            findings.append(f"unreadable_file: {relative}: {exc}")
            continue
        if b"\x00" in payload[:4096]:
            continue
        text = payload.decode("utf-8", errors="ignore")
        for label, pattern in TEXT_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label}: {relative}")
    return findings


def required_output_paths(projects_file: Path) -> list[Path]:
    document = json.loads(projects_file.read_text(encoding="utf-8"))
    roots: list[Path] = []
    for item in document.get("projects", []):
        if item.get("required_for_this_task") is True:
            output_dir = item.get("output_dir")
            source_repo = item.get("source_repo")
            if source_repo != "LinzeColin/CodexProject":
                continue
            if isinstance(output_dir, str) and output_dir:
                roots.append(REPO_ROOT / output_dir)
    return roots


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", type=Path, default=[])
    parser.add_argument("--all-required-deployments", action="store_true")
    parser.add_argument("--projects", type=Path, default=PROJECTS_FILE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    paths = [path.resolve() for path in args.path]
    if args.all_required_deployments:
        try:
            paths.extend(required_output_paths(args.projects))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"FAIL: cannot load projects registry: {exc}")
            return 1
    unique_paths = list(dict.fromkeys(paths))
    if not unique_paths:
        print("FAIL: provide --path or --all-required-deployments")
        return 1
    findings: list[str] = []
    for path in unique_paths:
        for finding in scan_path(path):
            findings.append(f"{path}: {finding}")
    if findings:
        print("FAIL: public distribution scan")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"PASS: public distribution scan ({len(unique_paths)} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

