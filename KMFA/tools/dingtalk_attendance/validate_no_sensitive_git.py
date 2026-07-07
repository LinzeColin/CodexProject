#!/usr/bin/env python3
"""Validate that KMFA S19 tracked files do not contain private runtime material."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DANGEROUS_SUFFIXES = (".sqlite", ".sqlite-wal", ".sqlite-shm", ".db")
DANGEROUS_PATH_PARTS = ("/private_runtime/",)


def _pattern(label: str, text: str) -> tuple[str, re.Pattern[str]]:
    return label, re.compile(re.escape(text), re.IGNORECASE)


SENSITIVE_TEXT_PATTERNS = (
    _pattern("access credential", "access" + "_token"),
    _pattern("app credential compact", "app" + "secret"),
    _pattern("app credential snake", "app" + "_secret"),
    _pattern("assignment style credential", "sec" + "ret="),
    _pattern("dingtalk robot endpoint", "dingtalk.com/robot/" + "send"),
)


@dataclass(frozen=True)
class Finding:
    path: str
    reason: str


def scan_payload_for_sensitive_text(payload: str) -> list[str]:
    return [label for label, pattern in SENSITIVE_TEXT_PATTERNS if pattern.search(payload)]


def _git_files(pathspec: str = "KMFA") -> list[str]:
    output = subprocess.check_output(["git", "ls-files", pathspec], cwd=ROOT, text=True)
    return [line for line in output.splitlines() if line]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def validate_paths(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for rel in paths:
        normalized = "/" + rel.replace("\\", "/")
        suffix = Path(rel).suffix
        if rel.endswith(DANGEROUS_SUFFIXES) or suffix in DANGEROUS_SUFFIXES:
            findings.append(Finding(rel, "tracked runtime database file"))
            continue
        if rel.endswith(".env.local"):
            findings.append(Finding(rel, "tracked local env file"))
            continue
        if any(part in normalized for part in DANGEROUS_PATH_PARTS) and not rel.endswith(
            ("private_runtime/README.md", "private_runtime/.gitkeep")
        ):
            findings.append(Finding(rel, "tracked private runtime content"))
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        text = _read_text(path)
        for label in scan_payload_for_sensitive_text(text):
            findings.append(Finding(rel, label))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan tracked Git files for KMFA S19 sensitive material.")
    parser.add_argument("--scope", choices=("tracked",), default="tracked")
    parser.add_argument("--pathspec", default="KMFA", help="Git pathspec to scan. Defaults to KMFA-only.")
    args = parser.parse_args(argv)

    paths = _git_files(args.pathspec) if args.scope == "tracked" else []
    findings = validate_paths(paths)
    if findings:
        for finding in findings:
            print(f"FAIL: {finding.path}: {finding.reason}")
        return 1
    print(f"PASS: no sensitive KMFA S19 material found in tracked files (pathspec={args.pathspec}, files={len(paths)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
