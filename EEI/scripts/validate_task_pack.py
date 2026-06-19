#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".next", ".venv", "__pycache__", "node_modules", "playwright-report", "test-results"}


def run(command: list[str], label: str) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode:
        raise AssertionError(f"{label} failed: {result.stderr.strip()}")


def generated_or_external(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts)


def main() -> int:
    run([sys.executable, str(ROOT / "scripts/validate_governance.py")], "governance validation")
    run([sys.executable, str(ROOT / "scripts/validate_catalog_integrity.py")], "catalog integrity")
    run(
        [
            sys.executable,
            str(ROOT / "scripts/validate_model_config.py"),
            str(ROOT / "config/model_profiles/balanced-v2.json"),
            str(ROOT / "config/thresholds/default-v2.json"),
        ],
        "model config validation",
    )

    required = [
        "README.md",
        "REPORT.md",
        "AGENTS.md",
        "CODEX_MASTER_TASK.md",
        "FUNCTION_CATALOG.md",
        "MODEL_MANAGEMENT.md",
        "DOMAIN_DATA_CATALOG.md",
        "DEVELOPMENT_STATUS.md",
        "RISK_AND_ACCEPTANCE.md",
        "GITHUB_REPOSITORY_BACKUP_INDEX.md",
        "US_Corporate_Power_Map_UIUX_Redesign_v4.2.md",
        "US_Corporate_Power_Map_Governance_Blueprint_v4.2.pdf",
        "prototype/index.html",
        "prototype/standalone.html",
        "prototype/app.js",
        "prototype/styles.css",
        "prototype/screenshots/default_1440x900.png",
        "prototype/screenshots/models_1440x900.png",
        "prototype/screenshots/data_1440x900.png",
        "prototype/screenshots/governance_1440x900.png",
        "specs/domain_schema.sql",
        "specs/api_contract.yaml",
        "prompts/01_PLAN_ONLY.md",
        "prompts/02_BUILD_MVP.md",
        "prompts/03_QA_RELEASE.md",
        "scripts/preflight.sh",
        "scripts/run_codex_autonomous.sh",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    if missing:
        raise AssertionError(f"missing pack files: {missing}")

    pdf_path = ROOT / "US_Corporate_Power_Map_Governance_Blueprint_v4.2.pdf"
    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted or len(reader.pages) != 16:
        raise AssertionError(f"governance PDF expected 16 unencrypted pages, got {len(reader.pages)}")

    for shell in ["scripts/preflight.sh", "scripts/run_codex_autonomous.sh"]:
        result = subprocess.run(["bash", "-n", str(ROOT / shell)], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(f"shell syntax {shell}: {result.stderr.strip()}")

    for path in ROOT.rglob("*.json"):
        if generated_or_external(path):
            continue
        json.loads(path.read_text(encoding="utf-8"))
    for path in list(ROOT.rglob("*.yaml")) + list(ROOT.rglob("*.yml")):
        if generated_or_external(path):
            continue
        yaml.safe_load(path.read_text(encoding="utf-8"))

    if (ROOT / "prototype/index.html").read_bytes() != (ROOT / "prototype/standalone.html").read_bytes():
        raise AssertionError("prototype/index.html and standalone.html diverged")

    node = shutil.which("node")
    if node:
        run([node, "--check", str(ROOT / "prototype/app.js")], "prototype JavaScript syntax")
    else:
        print("WARN node not installed; JavaScript syntax check skipped")

    print("Task Pack validation: PASS")
    print(f"  governance PDF pages: {len(reader.pages)}")
    print("  prototype standalone/index: identical")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Task Pack validation: FAIL - {exc}", file=sys.stderr)
        raise SystemExit(1)
