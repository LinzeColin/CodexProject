"""Validate the IDS STAGE-003 FinanceMetaDatabase rename boundary."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Iterable


STAGE = "STAGE-003"
ACCEPTANCE_ID = "ACC-STAGE-003"
CANONICAL_NAME = "FinanceMetaDatabase"
PRODUCT_NAME = "ProductMetaDatabase"
IGNORE_PARTS = {
    ".venv",
    "__pycache__",
    "data",
    "frontend/node_modules",
    "node_modules",
    "outputs",
    "reports",
}
RUNTIME_PARTS = {"backend", "frontend", "scripts", "app_bundle"}
STANDALONE_RE = re.compile(r"(?<!Product)\bMetaDatabase\b|\bFinanceMetaDatabase\b")


def _is_ignored(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & IGNORE_PARTS) or "frontend/node_modules" in str(path)


def _iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or _is_ignored(path):
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        yield path


def _git_changed_paths(root: Path) -> list[str]:
    repo_root = root.parent
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain"],
            cwd=repo_root,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line[3:] for line in output.splitlines() if line.strip()]


def build_report(root: Path | None = None) -> dict:
    root = (root or Path(__file__).resolve().parents[3]).resolve()
    issues: list[str] = []
    finance_meta_hits: list[str] = []
    standalone_old_hits: list[str] = []
    product_meta_hits: list[str] = []
    runtime_target_hits: list[str] = []

    for path in _iter_text_files(root):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root).as_posix()
        for lineno, line in enumerate(text.splitlines(), 1):
            if PRODUCT_NAME in line:
                product_meta_hits.append(f"{rel}:{lineno}")
            if CANONICAL_NAME in line:
                finance_meta_hits.append(f"{rel}:{lineno}")
            if re.search(r"(?<!Product)\bMetaDatabase\b", line):
                standalone_old_hits.append(f"{rel}:{lineno}")
            if STANDALONE_RE.search(line) and set(path.relative_to(root).parts) & RUNTIME_PARTS:
                runtime_target_hits.append(f"{rel}:{lineno}")

    changed_paths = _git_changed_paths(root)
    product_meta_path_touched = [
        path for path in changed_paths if path.startswith("KM_IDSystem/product_meta_database/")
    ]

    required = [
        root / "docs/pursuing_goal/ids_v0_1/STAGE003_PHASE2_REFERENCE_MIGRATION.md",
        root / "docs/pursuing_goal/ids_v0_1/validate_stage003_finance_meta_rename.py",
        root / "docs/pursuing_goal/ids_v0_1/tests/test_stage003_finance_meta_rename.py",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]

    if missing:
        issues.append("missing required migration artifacts: " + ", ".join(missing))
    if not finance_meta_hits:
        issues.append("FinanceMetaDatabase canonical references are missing")
    if not product_meta_hits:
        issues.append("ProductMetaDatabase exclusion guard found no preserved product references")
    if runtime_target_hits:
        issues.append("runtime paths contain standalone MetaDatabase/FinanceMetaDatabase hits")
    if product_meta_path_touched:
        issues.append("ProductMetaDatabase path was modified during STAGE-003 Phase 2")

    return {
        "acceptance_id": ACCEPTANCE_ID,
        "canonical_name": CANONICAL_NAME,
        "finance_meta_hits": len(finance_meta_hits),
        "finance_meta_hit_refs": finance_meta_hits,
        "issues": issues,
        "old_name": "MetaDatabase",
        "product_meta_hits": len(product_meta_hits),
        "product_meta_hit_sample": product_meta_hits[:20],
        "product_meta_path_touched": product_meta_path_touched,
        "runtime_target_hits": runtime_target_hits,
        "stage": STAGE,
        "standalone_old_hits": len(standalone_old_hits),
        "standalone_old_hit_sample": standalone_old_hits[:20],
        "valid": not issues,
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
