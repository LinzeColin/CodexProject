#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from verify_browser_acceptance import DEFAULT_EXPECTED_COUNT, load_payload, validate_payload


DEFAULT_OUTPUT_DIR = "outputs/finance_ledger_20220605_20260603"
DEFAULT_LEDGER_DB = "data/finance_ledger/finance_ledger.sqlite"


def _iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root]
    ignored_parts = {"__pycache__", ".pytest_cache"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def _add_path(archive: ZipFile, path: Path, arc_root: str, manifest_files: list[dict[str, object]]) -> None:
    for file_path in _iter_files(path):
        rel = file_path.relative_to(ROOT) if file_path.is_relative_to(ROOT) else file_path.name
        arcname = str(Path(arc_root) / rel)
        archive.write(file_path, arcname)
        manifest_files.append({"path": arcname, "size_bytes": file_path.stat().st_size})


def _required_paths(output_path: Path, ledger_path: Path) -> list[Path]:
    return [
        ROOT / "README.md",
        ROOT / "pyproject.toml",
        ROOT / "configs",
        ROOT / "scripts",
        ROOT / "src",
        ROOT / "docs",
        ROOT / "tests",
        ROOT / output_path,
        ROOT / ledger_path,
    ]


def _write_zip(zip_path: Path, required_paths: list[Path], output_path: Path, ledger_path: Path) -> tuple[list[dict[str, object]], list[str]]:
    manifest_files: list[dict[str, object]] = []
    missing: list[str] = []
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in required_paths:
            if path.exists():
                _add_path(archive, path, "economic_bleed_delivery", manifest_files)
            else:
                missing.append(str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path))
        package_manifest = {
            "package_type": "economic_bleed_delivery",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "output_dir": str(output_path),
            "ledger_db": str(ledger_path),
            "file_count": len(manifest_files),
            "missing": missing,
            "files": manifest_files,
            "entry_points": {
                "report_portal": str(output_path / "reports" / "index.html"),
                "operations_center": str(output_path / "reports" / "operations_center.html"),
                "acceptance_workbench": str(output_path / "reports" / "acceptance_workbench.html"),
                "reference_model_lab": str(output_path / "reports" / "reference_model_lab.html"),
                "dashboard": str(output_path / "reports" / "dashboard.html"),
                "review_workbench": str(output_path / "reports" / "review_workbench.html"),
                "user_manual_pdf": str(output_path / "reports" / "user_manual_report.pdf"),
                "user_acceptance_matrix_pdf": str(output_path / "reports" / "user_acceptance_matrix_report.pdf"),
                "ledger_db": str(ledger_path),
            },
        }
        archive.writestr(
            "economic_bleed_delivery/PACKAGE_MANIFEST.json",
            json.dumps(package_manifest, ensure_ascii=False, indent=2),
        )
    return manifest_files, missing


def _refresh_goal_completion_audit(output_path: Path, ledger_path: Path, zip_path: Path) -> dict[str, object]:
    from audit_goal_completion import run_audit

    return run_audit(
        argparse.Namespace(
            output_dir=str(output_path),
            ledger_db=str(ledger_path),
            delivery_zip=str(zip_path),
            json=False,
        )
    )


def build_delivery_package(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ledger_db: str | Path = DEFAULT_LEDGER_DB,
    package_dir: str | Path = "outputs/delivery",
    package_name: str = "",
    require_browser_acceptance: bool = True,
) -> dict[str, object]:
    generated_at = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_root = Path(package_dir)
    package_root.mkdir(parents=True, exist_ok=True)
    zip_path = package_root / (package_name or f"economic_bleed_delivery_{generated_at}.zip")
    output_path = Path(output_dir)
    ledger_path = Path(ledger_db)
    browser_errors: list[str] = []
    if require_browser_acceptance:
        browser_audit = ROOT / output_path / "audit" / "browser_visual_acceptance.json"
        if not browser_audit.exists():
            browser_errors.append(f"missing browser acceptance audit: {browser_audit.relative_to(ROOT)}")
        else:
            try:
                browser_payload = load_payload(browser_audit)
            except Exception as exc:
                browser_errors.append(f"invalid browser acceptance audit: {exc}")
            else:
                browser_errors.extend(
                    validate_payload(browser_payload, expected_count=DEFAULT_EXPECTED_COUNT, audit_path=browser_audit, html_root=ROOT / output_path)
                )
    if browser_errors:
        return {
            "zip_path": "",
            "size_bytes": 0,
            "file_count": 0,
            "missing": [],
            "browser_acceptance_errors": browser_errors,
        }
    required_paths = _required_paths(output_path, ledger_path)
    manifest_files, missing = _write_zip(zip_path, required_paths, output_path, ledger_path)
    goal_audit_refresh = _refresh_goal_completion_audit(output_path, ledger_path, zip_path)
    manifest_files, missing = _write_zip(zip_path, required_paths, output_path, ledger_path)
    return {
        "zip_path": str(zip_path),
        "size_bytes": zip_path.stat().st_size,
        "file_count": len(manifest_files),
        "missing": missing,
        "browser_acceptance_errors": [],
        "goal_audit_refreshed": bool(goal_audit_refresh.get("ok")),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Package the economic bleed analyzer project, reports, SQLite, and audit artifacts into a ZIP deliverable.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Generated report output directory to include.")
    parser.add_argument("--ledger-db", default=DEFAULT_LEDGER_DB, help="Shared ledger SQLite path to include.")
    parser.add_argument("--package-dir", default="outputs/delivery", help="Directory where the ZIP package is written.")
    parser.add_argument("--package-name", default="", help="Optional ZIP filename.")
    parser.add_argument("--skip-browser-acceptance", action="store_true", help="Package even when browser acceptance audit is missing, stale, or failed. Use only for interim debugging bundles.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_delivery_package(
        output_dir=args.output_dir,
        ledger_db=args.ledger_db,
        package_dir=args.package_dir,
        package_name=args.package_name,
        require_browser_acceptance=not args.skip_browser_acceptance,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"delivery_zip: {result['zip_path']}")
        print(f"size_bytes: {result['size_bytes']}")
        print(f"file_count: {result['file_count']}")
        if result["missing"]:
            print("missing: " + ", ".join(str(item) for item in result["missing"]))
        if result.get("browser_acceptance_errors"):
            print("browser_acceptance_errors:")
            for error in result["browser_acceptance_errors"]:
                print(f"- {error}")
    return 1 if result["missing"] or result.get("browser_acceptance_errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
