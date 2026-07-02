"""Validate the IDS STAGE-004 legacy-name scan boundary."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Iterable


STAGE = "STAGE-004"
ACCEPTANCE_ID = "ACC-STAGE-004"
ACCEPTED_NAMES = ("IDS / Industrial Data System", "ProductMetaDatabase", "FinanceMetaDatabase")
IGNORE_PARTS = {
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "data",
    "frontend/node_modules",
    "node_modules",
    "outputs",
    "reports",
}
FORBIDDEN_CHANGED_PREFIXES = (
    "KM_IDSystem/data/",
    "KM_IDSystem/reports/",
    "KM_IDSystem/outputs/",
    "KM_IDSystem/frontend/node_modules/",
    "KM_IDSystem/.venv/",
    "KM_IDSystem/product_meta_database/",
)


LEGACY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("legacy_product_full_en", re.compile(r"Wuhan Kaiming OpMe")),
    ("legacy_product_full_cn", re.compile(r"武汉开明智能工业运维助手")),
    ("legacy_slug", re.compile(r"wuhan-kaiming-assistant")),
    ("legacy_path_camel", re.compile(r"OpMe_System")),
    ("legacy_path_kebab", re.compile(r"opme-system")),
    ("legacy_opme_word", re.compile(r"(?<![A-Za-z0-9_])(?:OpMe|OPME|opme)(?![A-Za-z0-9_])")),
    ("legacy_wuhan_snake", re.compile(r"wuhan_kaiming")),
    ("legacy_wuhan_en", re.compile(r"Wuhan Kaiming")),
    ("legacy_wuhan_cn", re.compile(r"武汉开明")),
    ("legacy_asset_opmeicon", re.compile(r"OpMeIcon")),
    ("legacy_report_path", re.compile(r"OpMe_structure_report")),
    ("legacy_standalone_metadatabase", re.compile(r"(?<!Product)\bMetaDatabase\b")),
)


def _is_ignored(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & IGNORE_PARTS) or "frontend/node_modules" in path.as_posix()


def _git_ls_files(root: Path) -> list[Path]:
    repo_root = root.parent
    try:
        output = subprocess.check_output(["git", "ls-files", root.name], cwd=repo_root, text=True)
    except (OSError, subprocess.CalledProcessError):
        return [path.relative_to(root.parent) for path in root.rglob("*") if path.is_file()]
    return [Path(line) for line in output.splitlines() if line.strip()]


def _iter_text_files(root: Path) -> Iterable[tuple[str, Path]]:
    repo_root = root.parent
    for rel_path in _git_ls_files(root):
        path = repo_root / rel_path
        if not path.is_file() or _is_ignored(path):
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        yield rel_path.as_posix(), path


def _git_changed_paths(root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotePath=false", "status", "--porcelain"],
            cwd=root.parent,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line[3:] for line in output.splitlines() if line.strip()]


def find_legacy_hits(line: str) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for pattern_name, pattern in LEGACY_PATTERNS:
        for match in pattern.finditer(line):
            value = match.group(0)
            if value in {"ProductMetaDatabase", "FinanceMetaDatabase"}:
                continue
            hits.append({"pattern": pattern_name, "value": value})
    return hits


def _contains_any(line: str, needles: tuple[str, ...]) -> bool:
    lowered = line.lower()
    return any(needle.lower() in lowered for needle in needles)


def classify_hit(rel_path: str, line: str, pattern_name: str) -> str:
    if rel_path.startswith("KM_IDSystem/docs/pursuing_goal/ids_v0_1/"):
        return "allowed_legacy_context"
    if rel_path.startswith("KM_IDSystem/docs/governance/"):
        return "allowed_legacy_context"
    if rel_path.startswith("KM_IDSystem/backend/tests/"):
        return "allowed_legacy_context"
    if rel_path in {"KM_IDSystem/docs/HANDOFF.md", "KM_IDSystem/CHANGELOG.md"}:
        return "allowed_legacy_context"
    if rel_path.startswith("KM_IDSystem/docs/CLEANUP"):
        return "allowed_legacy_context"
    if rel_path == "KM_IDSystem/docs/OpMe_structure_report.md":
        return "allowed_legacy_context"
    if rel_path == "KM_IDSystem/README.md" and _contains_any(
        line,
        (
            "legacy",
            "OpMe_structure_report",
            "OpMeIcon",
            "wuhan_kaiming.sqlite",
            "历史",
            "兼容",
            "回滚",
        ),
    ):
        return "allowed_legacy_context"
    if rel_path == "KM_IDSystem/backend/app/core/config.py" and pattern_name == "legacy_wuhan_snake":
        return "allowed_legacy_context"
    if rel_path == "KM_IDSystem/backend/app/services/model_router.py" and pattern_name == "legacy_wuhan_cn":
        return "allowed_legacy_context"
    if rel_path in {
        "KM_IDSystem/scripts/build_app_bundle.sh",
        "KM_IDSystem/scripts/generate_app_icon.py",
    } and pattern_name == "legacy_asset_opmeicon":
        return "allowed_legacy_context"
    return "active_display_debt"


def build_report(root: Path | None = None) -> dict:
    root = (root or Path(__file__).resolve().parents[3]).resolve()
    issues: list[str] = []
    legacy_refs: list[dict[str, str | int]] = []
    pattern_counts = {name: 0 for name, _pattern in LEGACY_PATTERNS}
    classification_counts = {
        "allowed_legacy_context": 0,
        "active_display_debt": 0,
    }
    active_display_debt_refs: list[str] = []
    accepted_name_hits = {name: 0 for name in ACCEPTED_NAMES}
    files_scanned = 0

    for rel_path, path in _iter_text_files(root):
        text = path.read_text(encoding="utf-8")
        files_scanned += 1
        for lineno, line in enumerate(text.splitlines(), 1):
            for accepted_name in ACCEPTED_NAMES:
                if accepted_name in line:
                    accepted_name_hits[accepted_name] += line.count(accepted_name)
            for hit in find_legacy_hits(line):
                pattern_name = hit["pattern"]
                classification = classify_hit(rel_path, line, pattern_name)
                pattern_counts[pattern_name] += 1
                classification_counts[classification] += 1
                ref = f"{rel_path}:{lineno}:{pattern_name}"
                legacy_refs.append(
                    {
                        "classification": classification,
                        "line": lineno,
                        "path": rel_path,
                        "pattern": pattern_name,
                        "value": hit["value"],
                    }
                )
                if classification == "active_display_debt":
                    active_display_debt_refs.append(ref)

    changed_paths = _git_changed_paths(root)
    forbidden_changed_paths = [
        path for path in changed_paths if path.startswith(FORBIDDEN_CHANGED_PREFIXES)
    ]

    required = [
        root / "docs/pursuing_goal/ids_v0_1/STAGE004_ENTRY_CONTRACT.md",
        root / "docs/pursuing_goal/ids_v0_1/STAGE004_PHASE1_SCOPE_BOUNDARY.md",
        root / "docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py",
        root / "docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]

    if missing:
        issues.append("missing required STAGE-004 artifacts: " + ", ".join(missing))
    if not legacy_refs:
        issues.append("legacy-name scan found no references to classify")
    if active_display_debt_refs:
        issues.append("active display-name debt refs require Phase 3 review or Phase 2 narrowing")
    if forbidden_changed_paths:
        issues.append("forbidden path changed during STAGE-004")
    if accepted_name_hits["ProductMetaDatabase"] == 0:
        issues.append("ProductMetaDatabase false-positive guard found no preserved accepted references")
    if accepted_name_hits["FinanceMetaDatabase"] == 0:
        issues.append("FinanceMetaDatabase false-positive guard found no preserved accepted references")

    unique_paths = sorted({str(ref["path"]) for ref in legacy_refs})
    return {
        "accepted_name_hits": accepted_name_hits,
        "acceptance_id": ACCEPTANCE_ID,
        "active_display_debt_refs": active_display_debt_refs,
        "classification_counts": classification_counts,
        "files_scanned": files_scanned,
        "forbidden_changed_paths": forbidden_changed_paths,
        "issues": issues,
        "legacy_name_hit_sample": legacy_refs[:30],
        "legacy_name_hits": len(legacy_refs),
        "pattern_counts": pattern_counts,
        "stage": STAGE,
        "unique_paths_with_legacy_hits": len(unique_paths),
        "unique_path_sample": unique_paths[:30],
        "valid": not issues,
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
