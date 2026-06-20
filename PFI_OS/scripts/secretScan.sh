#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR"

PYTHON_BIN="${PFI_PYTHON:-$(command -v python3)}"
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(os.environ.get("PFI_SECRET_SCAN_ROOT", pathlib.Path.cwd())).expanduser().resolve()
PATTERNS = {
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github_pat": re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic_private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
}
ALLOWLIST = {
    "docs/archive/legacy-migration.md",
}
TEXT_SUFFIXES = {
    ".command",
    ".css",
    ".csv",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

result = subprocess.run(["git", "-C", str(ROOT), "ls-files"], check=True, capture_output=True, text=True)
violations: list[str] = []
for relative in result.stdout.splitlines():
    if relative in ALLOWLIST:
        continue
    path = ROOT / relative
    if not path.is_file():
        continue
    if path.suffix not in TEXT_SUFFIXES and path.name not in {".python-version", "requirements.lock"}:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for name, pattern in PATTERNS.items():
      if pattern.search(text):
          violations.append(f"{relative}:{name}")

if violations:
    print("Secret scan failed:")
    for item in violations:
        print(f"- {item}")
    sys.exit(1)

print("Secret scan passed.")
PY
