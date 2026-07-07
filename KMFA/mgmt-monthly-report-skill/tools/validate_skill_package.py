#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "KMFA" / "mgmt-monthly-report-skill"
METADATA = ROOT / "KMFA" / "metadata" / "mgmt-monthly-report-skill"


REQUIRED_FILES = [
    SKILL / "SKILL.md",
    SKILL / "README.md",
    SKILL / "功能清单.md",
    SKILL / "规则清单.md",
    SKILL / "agents" / "openai.yaml",
    SKILL / "config" / "input_manifest.7slots.template.yml",
    SKILL / "config" / "v6_spec.json",
    SKILL / "references" / "runbook.md",
    SKILL / "references" / "data_contract.md",
    SKILL / "references" / "excel_pdf_contract.md",
    SKILL / "references" / "data_governance.md",
    SKILL / "scripts" / "mgmt_monthly_report.py",
    SKILL / "scripts" / "validate_deliverables.py",
    METADATA / "README.md",
    METADATA / "database" / "schema.sql",
    METADATA / "cleanup" / "local_retention_policy.json",
]

REQUIRED_METADATA_DIRS = [
    "backup_registry",
    "cleanup",
    "config",
    "database",
    "logs",
    "public_reports",
    "raw_index",
    "run_manifests",
    "validation",
]

FORBIDDEN_GIT_SUFFIXES = {".xlsx", ".xls", ".pdf", ".sqlite", ".sqlite3", ".db", ".gz"}


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def main() -> int:
    errors: list[str] = []

    check(SKILL.exists(), f"missing skill dir: {SKILL}", errors)
    check(METADATA.exists(), f"missing metadata dir: {METADATA}", errors)
    for path in REQUIRED_FILES:
        check(path.exists(), f"missing required file: {path.relative_to(ROOT)}", errors)
    for name in REQUIRED_METADATA_DIRS:
        check((METADATA / name).is_dir(), f"missing metadata dir: KMFA/metadata/mgmt-monthly-report-skill/{name}", errors)

    if (SKILL / "SKILL.md").exists():
        fm = parse_frontmatter(SKILL / "SKILL.md")
        check(fm.get("name") == "mgmt-monthly-report-skill", "SKILL.md name must match directory", errors)
        check(bool(fm.get("description")), "SKILL.md description is required", errors)

    if (SKILL / "config" / "v6_spec.json").exists():
        spec = json.loads((SKILL / "config" / "v6_spec.json").read_text(encoding="utf-8"))
        check(len(spec.get("visible_sheet_order", [])) == 11, "v6_spec visible_sheet_order must contain 11 sheets", errors)
        check("output_files" in spec, "v6_spec output_files missing", errors)
        check("forbidden_visible_terms" in spec, "v6_spec forbidden_visible_terms missing", errors)

    for rel in [
        "scripts/mgmt_monthly_report.py",
        "scripts/validate_deliverables.py",
        "tools/validate_skill_package.py",
    ]:
        path = SKILL / rel
        if path.exists():
            py_compile.compile(str(path), doraise=True)

    forbidden = [
        p.relative_to(ROOT)
        for p in list(SKILL.rglob("*")) + list(METADATA.rglob("*"))
        if p.is_file() and p.suffix.lower() in FORBIDDEN_GIT_SUFFIXES
    ]
    check(not forbidden, f"forbidden committed data-like files: {forbidden}", errors)

    if errors:
        print(json.dumps({"status": "failed", "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": "passed", "skill": "mgmt-monthly-report-skill"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

