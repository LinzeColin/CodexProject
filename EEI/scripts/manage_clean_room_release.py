#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]

EVIDENCE = Path("artifacts/tests/a200/t1215_clean_room_release.json")
PACKAGE = Path("artifacts/tests/a200/Enterprise_Ecosystem_Intelligence_clean_room_t1215.zip")
INTERNAL_MANIFEST = "PACKAGE_MANIFEST.json"
INTERNAL_CHECKSUMS = "PACKAGE_CHECKSUMS.sha256"
FIXED_ZIP_DATETIME = (2026, 6, 19, 0, 0, 0)

REQUIRED_MARKDOWN = {
    "README.md",
    "GOVERNANCE_INDEX.md",
    "DEVELOPMENT_STATUS.md",
    "RISK_AND_ACCEPTANCE.md",
    "MODEL_MANAGEMENT.md",
    "FUNCTION_CATALOG.md",
    "DOMAIN_DATA_CATALOG.md",
    "docs/phase/MVP_DEVELOPMENT_RECORD.md",
}

REQUIRED_CSV = {
    "data/acceptance_matrix.csv",
    "data/acceptance_traceability.csv",
    "data/development_status_ledger.csv",
    "data/github_document_registry.csv",
    "data/risk_control_traceability.csv",
    "data/task_backlog.csv",
    "artifacts/requirement_function_task_test_traceability_t1213.csv",
    "artifacts/risk_control_mapping_t1214.csv",
}

REQUIRED_JSON = {
    "artifacts/development_status_summary_t1213.json",
    "artifacts/risk_control_summary_t1214.json",
    "artifacts/tests/a200/t1212_clean_room_preflight.json",
}

REQUIRED_GITHUB = {
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/release_checklist.md",
    ".github/workflows/governance-validation.yml",
}

REQUIRED_PROTOTYPE = {
    "prototype/index.html",
    "prototype/standalone.html",
    "prototype/app.js",
    "prototype/styles.css",
}

REQUIRED_PDF = {"US_Corporate_Power_Map_Governance_Blueprint_v4.2.pdf"}

REQUIRED_SUPPORTING = {
    "scripts/manage_clean_room_release.py",
    "scripts/manage_release_artifacts.py",
    "scripts/validate_governance_consistency.py",
    "scripts/validate_github_governance.py",
    "scripts/validate_prototype_parity.py",
}

REQUIRED_PACKAGE_PATHS = (
    REQUIRED_MARKDOWN
    | REQUIRED_CSV
    | REQUIRED_JSON
    | REQUIRED_GITHUB
    | REQUIRED_PROTOTYPE
    | REQUIRED_PDF
    | REQUIRED_SUPPORTING
)

EXCLUDED_FROM_PACKAGE = {
    "CHECKSUMS.sha256",
    "DIRECTORY_TREE.txt",
    "manifest.txt",
    "artifacts/release_evidence_t1211.json",
    "artifacts/release_operation_log_t1211.jsonl",
    str(EVIDENCE),
    str(PACKAGE),
}


def run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return completed.stdout


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        raise AssertionError(f"missing required file: {path}")
    return target.read_text(encoding="utf-8")


def read_csv(path: str) -> list[dict[str, str]]:
    target = ROOT / path
    if not target.is_file():
        raise AssertionError(f"missing required CSV: {path}")
    with target.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise AssertionError(f"CSV has no rows: {path}")
    return rows


def read_json(path: str) -> Any:
    target = ROOT / path
    if not target.is_file():
        raise AssertionError(f"missing required JSON: {path}")
    return json.loads(target.read_text(encoding="utf-8"))


def tracked_paths() -> set[str]:
    return set(run_git("ls-files").splitlines())


def package_paths() -> list[str]:
    paths = tracked_paths() | REQUIRED_PACKAGE_PATHS
    paths -= EXCLUDED_FROM_PACKAGE
    missing = sorted(path for path in paths if not (ROOT / path).is_file())
    if missing:
        raise AssertionError(f"missing package files: {missing}")
    return sorted(paths)


def categorize(paths: list[str]) -> dict[str, list[str]]:
    return {
        "markdown": [path for path in paths if path.endswith(".md")],
        "csv": [path for path in paths if path.endswith(".csv")],
        "json": [path for path in paths if path.endswith(".json")],
        "github": [path for path in paths if path.startswith(".github/")],
        "prototype": [path for path in paths if path.startswith("prototype/")],
        "pdf": [path for path in paths if path.endswith(".pdf")],
    }


def validate_required_paths(paths: list[str]) -> dict[str, int]:
    path_set = set(paths)
    missing = sorted(REQUIRED_PACKAGE_PATHS - path_set)
    if missing:
        raise AssertionError(f"clean-room package missing required paths: {missing}")
    unexpected = sorted(path for path in EXCLUDED_FROM_PACKAGE if path in path_set)
    if unexpected:
        raise AssertionError(f"clean-room package contains excluded paths: {unexpected}")

    categories = categorize(paths)
    required_categories = {
        "markdown": REQUIRED_MARKDOWN,
        "csv": REQUIRED_CSV,
        "json": REQUIRED_JSON,
        "github": REQUIRED_GITHUB,
        "prototype": REQUIRED_PROTOTYPE,
        "pdf": REQUIRED_PDF,
    }
    for category, required in required_categories.items():
        missing_in_category = sorted(required - set(categories[category]))
        if missing_in_category:
            raise AssertionError(f"{category} missing required paths: {missing_in_category}")
        if not categories[category]:
            raise AssertionError(f"{category} category is empty")
    return {category: len(values) for category, values in categories.items()}


def validate_source_files() -> dict[str, Any]:
    for path in REQUIRED_CSV:
        read_csv(path)
    for path in REQUIRED_JSON:
        read_json(path)
    workflow = yaml.safe_load(read_text(".github/workflows/governance-validation.yml"))
    if not isinstance(workflow, dict):
        raise AssertionError("governance workflow must parse as YAML object")
    workflow_text = read_text(".github/workflows/governance-validation.yml")
    if "python scripts/manage_clean_room_release.py validate" not in workflow_text:
        raise AssertionError("governance workflow does not validate clean-room release")

    index = (ROOT / "prototype/index.html").read_bytes()
    standalone = (ROOT / "prototype/standalone.html").read_bytes()
    if index != standalone:
        raise AssertionError("prototype/index.html and prototype/standalone.html differ")

    pdf_path = ROOT / "US_Corporate_Power_Map_Governance_Blueprint_v4.2.pdf"
    pdf_pages = len(PdfReader(str(pdf_path)).pages)
    if pdf_pages != 16:
        raise AssertionError(f"governance PDF expected 16 pages, got {pdf_pages}")

    return {
        "prototype_hash": sha256_bytes(index),
        "prototype_bytes": len(index),
        "pdf_pages": pdf_pages,
    }


def expect_status(path: str, key_column: str, key: str, status_column: str, expected: str) -> None:
    rows = read_csv(path)
    matches = [row for row in rows if row[key_column] == key]
    if len(matches) != 1:
        raise AssertionError(f"{path} expected one {key_column}={key}, got {len(matches)}")
    actual = matches[0][status_column]
    if actual != expected:
        raise AssertionError(f"{path} {key} {status_column} expected {expected}, got {actual}")


def validate_a200_status() -> None:
    expect_status("data/task_backlog.csv", "task_id", "T1215", "status", "DONE")
    expect_status("data/acceptance_matrix.csv", "acceptance_id", "A200", "status", "DONE")
    expect_status(
        "data/acceptance_traceability.csv",
        "trace_id",
        "TR-FUN-SYS-02-A200",
        "status",
        "DONE",
    )
    trace = [
        row
        for row in read_csv("data/acceptance_traceability.csv")
        if row["trace_id"] == "TR-FUN-SYS-02-A200"
    ][0]
    for required in [str(EVIDENCE), str(PACKAGE), "scripts/manage_clean_room_release.py"]:
        if required not in trace["evidence_path"]:
            raise AssertionError(f"A200 traceability missing evidence path: {required}")


def render_internal_checksums(checksums: dict[str, str]) -> str:
    return "\n".join(f"{digest}  {path}" for path, digest in sorted(checksums.items())) + "\n"


def zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path)
    info.date_time = FIXED_ZIP_DATETIME
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def write_zip(paths: list[str], manifest: dict[str, Any], checksums: dict[str, str]) -> None:
    target = ROOT / PACKAGE
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w") as archive:
        for path in paths:
            archive.writestr(zip_info(path), (ROOT / path).read_bytes())
        archive.writestr(
            zip_info(INTERNAL_MANIFEST),
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
            + b"\n",
        )
        archive.writestr(
            zip_info(INTERNAL_CHECKSUMS),
            render_internal_checksums(checksums).encode("utf-8"),
        )


def build_manifest(paths: list[str], category_counts: dict[str, int]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "package_id": "eei-clean-room-release-t1215",
        "task_id": "T1215",
        "acceptance_ids": ["A200"],
        "system": {
            "zh_name": "商域图谱",
            "en_name": "Enterprise Ecosystem Intelligence",
            "subtitle": "企业商业版图与供应链递归探索系统",
        },
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "included_path_count": len(paths),
        "category_counts": category_counts,
        "required_paths": sorted(REQUIRED_PACKAGE_PATHS),
        "excluded_paths": sorted(EXCLUDED_FROM_PACKAGE),
        "included_paths": paths,
    }


def build_evidence(
    paths: list[str],
    category_counts: dict[str, int],
    source_checks: dict[str, Any],
) -> dict[str, Any]:
    package_path = ROOT / PACKAGE
    return {
        "schema_version": 1,
        "artifact_id": "a200-clean-room-release-validation",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_commit": run_git("rev-parse", "--short", "HEAD").strip(),
        "task_id": "T1215",
        "acceptance_ids": ["A200"],
        "status": "LOCAL_PASS",
        "package": {
            "path": str(PACKAGE),
            "sha256": sha256_file(package_path),
            "bytes": package_path.stat().st_size,
            "entry_count": len(paths) + 2,
            "internal_manifest": INTERNAL_MANIFEST,
            "internal_checksums": INTERNAL_CHECKSUMS,
        },
        "category_counts": category_counts,
        "source_checks": source_checks,
        "commands": [
            "python scripts/manage_clean_room_release.py generate",
            "python scripts/manage_clean_room_release.py validate",
            "make verify",
            "sha256sum -c CHECKSUMS.sha256",
        ],
        "rollback": [
            "Revert the T1215 clean-room release evidence commit.",
            "Regenerate clean-room package and release artifacts.",
            "Run make verify and sha256sum -c CHECKSUMS.sha256.",
        ],
    }


def generate(_: argparse.Namespace) -> None:
    validate_a200_status()
    paths = package_paths()
    category_counts = validate_required_paths(paths)
    source_checks = validate_source_files()
    checksums = {path: sha256_file(ROOT / path) for path in paths}
    manifest = build_manifest(paths, category_counts)
    write_zip(paths, manifest, checksums)
    evidence = build_evidence(paths, category_counts, source_checks)
    (ROOT / EVIDENCE).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / EVIDENCE).write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    validate(None)
    print(
        json.dumps(
            {
                "generated": True,
                "package": str(PACKAGE),
                "evidence": str(EVIDENCE),
                "package_paths": len(paths),
                "package_sha256": evidence["package"]["sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def read_package_checksums(archive: zipfile.ZipFile) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in archive.read(INTERNAL_CHECKSUMS).decode("utf-8").splitlines():
        if not line.strip():
            continue
        digest, path = line.split("  ", 1)
        checksums[path] = digest
    return checksums


def validate(_: argparse.Namespace | None = None) -> None:
    validate_a200_status()
    paths = package_paths()
    category_counts = validate_required_paths(paths)
    source_checks = validate_source_files()

    if not (ROOT / PACKAGE).is_file():
        raise AssertionError(f"missing clean-room release ZIP: {PACKAGE}")
    if not (ROOT / EVIDENCE).is_file():
        raise AssertionError(f"missing clean-room release evidence: {EVIDENCE}")

    evidence = json.loads((ROOT / EVIDENCE).read_text(encoding="utf-8"))
    if evidence.get("task_id") != "T1215":
        raise AssertionError("clean-room evidence must cite T1215")
    if set(evidence.get("acceptance_ids", [])) != {"A200"}:
        raise AssertionError("clean-room evidence must cite A200")
    if evidence.get("status") != "LOCAL_PASS":
        raise AssertionError("clean-room evidence status must be LOCAL_PASS")
    if evidence.get("category_counts") != category_counts:
        raise AssertionError("clean-room evidence category counts are stale")
    if evidence.get("source_checks") != source_checks:
        raise AssertionError("clean-room evidence source checks are stale")
    if evidence.get("package", {}).get("sha256") != sha256_file(ROOT / PACKAGE):
        raise AssertionError("clean-room package digest mismatch")

    expected_entries = set(paths) | {INTERNAL_MANIFEST, INTERNAL_CHECKSUMS}
    with zipfile.ZipFile(ROOT / PACKAGE) as archive:
        actual_entries = set(archive.namelist())
        if actual_entries != expected_entries:
            missing = sorted(expected_entries - actual_entries)
            extra = sorted(actual_entries - expected_entries)
            raise AssertionError(f"clean-room ZIP entries mismatch missing={missing} extra={extra}")
        manifest = json.loads(archive.read(INTERNAL_MANIFEST).decode("utf-8"))
        if manifest.get("included_paths") != paths:
            raise AssertionError("clean-room ZIP internal manifest paths are stale")
        if manifest.get("category_counts") != category_counts:
            raise AssertionError("clean-room ZIP internal manifest counts are stale")
        checksums = read_package_checksums(archive)
        if sorted(checksums) != paths:
            raise AssertionError("clean-room ZIP internal checksums path set mismatch")
        for path, digest in checksums.items():
            actual = sha256_bytes(archive.read(path))
            if actual != digest:
                raise AssertionError(f"clean-room ZIP checksum mismatch for {path}")
            workspace_actual = sha256_file(ROOT / path)
            if workspace_actual != digest:
                raise AssertionError(f"clean-room ZIP is stale for {path}")

    print(
        json.dumps(
            {
                "valid": True,
                "package": str(PACKAGE),
                "evidence": str(EVIDENCE),
                "package_paths": len(paths),
                "category_counts": category_counts,
                "package_sha256": evidence["package"]["sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("generate")
    subparsers.add_parser("validate")
    args = parser.parse_args()

    try:
        if args.command == "generate":
            generate(args)
        else:
            validate(args)
    except (
        AssertionError,
        csv.Error,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
        yaml.YAMLError,
    ) as exc:
        print(f"Clean-room release validation: FAIL - {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
