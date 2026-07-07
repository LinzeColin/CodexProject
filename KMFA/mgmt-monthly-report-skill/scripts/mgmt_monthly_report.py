#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sqlite3
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


PERIOD_RE = re.compile(r"^[0-9]{6}$")
OFFICIAL_EXCEL = "经营管理分析报表 {period}.xlsx"
OFFICIAL_PDF = "董事会经营分析摘要 {period}.pdf"


@dataclass(frozen=True)
class InputSlot:
    slot_id: str
    display_name: str
    patterns: tuple[str, ...]
    required: bool = True
    prefer_patterns: tuple[str, ...] = ()
    min_physical_files: int = 1
    recommended_physical_files: int = 1
    required_sheet_aliases: tuple[tuple[str, tuple[str, ...]], ...] = ()
    allow_multiple: bool = False


INPUT_SLOTS: tuple[InputSlot, ...] = (
    InputSlot(
        "collection_2026",
        "WPS 武汉开明 2026年回款表",
        ("*2026*回款表*.xlsx", "*2026*回款*.xlsx"),
        prefer_patterns=("*销售会计*.xlsx",),
    ),
    InputSlot(
        "invoice_tax_cash",
        "开票纳税资金汇总表",
        ("*开票*纳税*资金汇总*.xlsx",),
        required_sheet_aliases=(
            ("开票纳税汇总", ("开票纳税汇总", "*开票*纳税*汇总*", "*各个主体*开票*纳税*")),
            ("2026年销售回款", ("2026年销售回款", "*销售回款*", "*回2026年合同款*", "*回款*合同款*")),
            ("2026年资金汇总", ("2026年资金汇总", "*资金汇总*", "*资金流汇总*")),
        ),
    ),
    InputSlot("receivable_contract", "应收账款合同登记", ("*应收账款*合同登记*.xlsx", "*合同登记*.xlsx")),
    InputSlot("aging", "应收账龄表", ("*应收账龄*.xlsx",)),
    InputSlot("deposit", "2026年保证金", ("*保证金2026*.xlsx", "*保证金*.xlsx")),
    InputSlot("three_major_projects", "三大项目", ("*三大项目*.xlsx",)),
    InputSlot(
        "project_status_contracts",
        "生产项目状态表与红圈主合同",
        ("*生产项目状态表*.xlsx", "*红圈主合同*.xlsx"),
        min_physical_files=1,
        recommended_physical_files=2,
        allow_multiple=True,
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def inspect_xlsx_sheets(path: Path) -> tuple[list[str], str | None]:
    try:
        with zipfile.ZipFile(path) as zf:
            data = zf.read("xl/workbook.xml")
    except Exception as exc:  # noqa: BLE001 - public-safe diagnostic only
        return [], f"{type(exc).__name__}: {exc}"

    try:
        root = ET.fromstring(data)
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheets = [elem.attrib.get("name", "") for elem in root.findall(".//main:sheets/main:sheet", ns)]
        return [s for s in sheets if s], None
    except Exception as exc:  # noqa: BLE001
        return [], f"{type(exc).__name__}: {exc}"


def match_aliases(sheet_names: Iterable[str], aliases: Iterable[str]) -> list[str]:
    out: list[str] = []
    names = list(sheet_names)
    for alias in aliases:
        for name in names:
            if name == alias or fnmatch.fnmatch(name, alias):
                out.append(name)
    return sorted(set(out))


def list_xlsx(input_dir: Path) -> list[Path]:
    return sorted([p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in {".xlsx", ".xls"}])


def candidates_for_slot(input_dir: Path, slot: InputSlot) -> list[Path]:
    matches: list[Path] = []
    for path in list_xlsx(input_dir):
        for pattern in slot.patterns:
            if fnmatch.fnmatch(path.name, pattern):
                matches.append(path)
                break
    return sorted(set(matches))


def select_candidates(slot: InputSlot, candidates: list[Path]) -> tuple[list[Path], list[Path], str]:
    if slot.allow_multiple:
        return candidates, [], "all_matching_files_selected"
    if not candidates:
        return [], [], "missing"
    for prefer in slot.prefer_patterns:
        preferred = [p for p in candidates if fnmatch.fnmatch(p.name, prefer)]
        if len(preferred) == 1:
            return preferred, [p for p in candidates if p != preferred[0]], "preferred_file_selected"
    if len(candidates) == 1:
        return candidates, [], "single_file_selected"
    return [candidates[0]], candidates[1:], "multiple_candidates_first_selected_requires_review"


def public_file_record(path: Path, slot: InputSlot, matched_pattern: str | None = None) -> dict:
    sheets, sheet_error = inspect_xlsx_sheets(path) if path.suffix.lower() == ".xlsx" else ([], "xls_not_supported")
    return {
        "slot_id": slot.slot_id,
        "display_name": slot.display_name,
        "file_name_sha256": sha256_text(path.name),
        "file_sha256": sha256_file(path),
        "file_size_bytes": path.stat().st_size,
        "extension": path.suffix.lower(),
        "is_symlink": path.is_symlink(),
        "sheet_count": len(sheets),
        "sheet_names_sha256": sha256_text("\n".join(sheets)) if sheets else None,
        "sheet_read_error": sheet_error,
        "matched_pattern": matched_pattern,
        "committed_plaintext_to_git": False,
    }


def slot_status(slot: InputSlot, selected: list[Path], alternates: list[Path]) -> str:
    if slot.required and len(selected) < slot.min_physical_files:
        return "failed_missing"
    if any(p.suffix.lower() == ".xls" for p in selected):
        return "failed_xls_requires_conversion"
    if slot.recommended_physical_files and len(selected) < slot.recommended_physical_files:
        return "warning_below_recommended_physical_files"
    if alternates:
        return "warning_alternate_candidates_present"
    return "passed"


def build_manifest(period: str, input_dir: Path, output_dir: Path, metadata_root: Path) -> dict:
    if not PERIOD_RE.match(period):
        raise SystemExit(f"period must be YYYYMM, got {period!r}")
    if not input_dir.exists():
        raise SystemExit(f"input_dir not found: {input_dir}")

    run_id = f"mgmt-monthly-report-{period}-{utc_now().replace(':', '').replace('-', '')}"
    input_slots: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []

    for slot in INPUT_SLOTS:
        candidates = candidates_for_slot(input_dir, slot)
        selected, alternates, selection_reason = select_candidates(slot, candidates)
        records = [public_file_record(path, slot) for path in selected]
        status = slot_status(slot, selected, alternates)
        if status.startswith("failed"):
            errors.append(f"{slot.slot_id}:{status}")
        elif status.startswith("warning"):
            warnings.append(f"{slot.slot_id}:{status}")

        sheet_group_checks = []
        if slot.required_sheet_aliases and selected:
            sheets, sheet_error = inspect_xlsx_sheets(selected[0])
            for canonical, aliases in slot.required_sheet_aliases:
                matched = match_aliases(sheets, aliases)
                ok = bool(matched)
                if not ok:
                    errors.append(f"{slot.slot_id}:missing_sheet_group:{canonical}")
                sheet_group_checks.append(
                    {
                        "canonical": canonical,
                        "matched_sheet_names_sha256": sha256_text("\n".join(matched)) if matched else None,
                        "matched_count": len(matched),
                        "status": "passed" if ok else "failed",
                    }
                )
            if sheet_error:
                errors.append(f"{slot.slot_id}:sheet_read_error")

        input_slots.append(
            {
                "slot_id": slot.slot_id,
                "display_name": slot.display_name,
                "status": status,
                "selection_reason": selection_reason,
                "candidate_count": len(candidates),
                "selected_count": len(selected),
                "alternate_candidate_count": len(alternates),
                "min_physical_files": slot.min_physical_files,
                "recommended_physical_files": slot.recommended_physical_files,
                "files": records,
                "sheet_group_checks": sheet_group_checks,
            }
        )

    excel = output_dir / OFFICIAL_EXCEL.format(period=period)
    pdf = output_dir / OFFICIAL_PDF.format(period=period)
    outputs = {
        "excel": output_record("excel", excel),
        "pdf": output_record("pdf", pdf),
    }

    status = "failed" if errors else ("warning" if warnings else "passed")
    return {
        "period": period,
        "run_id": run_id,
        "created_at_utc": utc_now(),
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "input_slot_count": len(INPUT_SLOTS),
        "input_slots": input_slots,
        "outputs": outputs,
        "metadata_root": str(metadata_root),
        "metadata_policy": {
            "public_safe_only": True,
            "raw_sensitive_plaintext_committed_to_git": False,
            "report_plaintext_committed_to_git": False,
            "runtime_sqlite_committed_to_git": False,
        },
    }


def output_record(output_type: str, path: Path) -> dict:
    exists = path.exists()
    return {
        "output_type": output_type,
        "expected_file_name": path.name,
        "output_dir_sha256": sha256_text(str(path.parent)),
        "exists": exists,
        "file_sha256": sha256_file(path) if exists else None,
        "file_size_bytes": path.stat().st_size if exists else None,
        "retained_locally": exists,
        "committed_plaintext_to_git": False,
    }


def ensure_metadata_dirs(root: Path) -> None:
    for name in [
        "backup_registry",
        "cleanup",
        "database",
        "logs",
        "public_reports",
        "raw_index",
        "run_manifests",
        "validation",
    ]:
        (root / name).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jsonl_append(path: Path, entry: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def render_sql_export(manifest: dict) -> str:
    lines = [
        "-- Public-safe SQL export generated by mgmt_monthly_report.py",
        "BEGIN;",
        (
            "INSERT OR REPLACE INTO monthly_report_run "
            "(run_id, period, status, created_at, metadata_policy) VALUES "
            f"({sql_literal(manifest['run_id'])}, {sql_literal(manifest['period'])}, "
            f"{sql_literal(manifest['status'])}, {sql_literal(manifest['created_at_utc'])}, "
            f"{sql_literal(json.dumps(manifest['metadata_policy'], ensure_ascii=False, sort_keys=True))});"
        ),
    ]
    for slot in manifest["input_slots"]:
        for file_rec in slot["files"]:
            lines.append(
                "INSERT OR REPLACE INTO monthly_report_input_file "
                "(run_id, slot_id, file_sha256, file_size_bytes, extension, sheet_count, "
                "sheet_names_sha256, matched_pattern, is_symlink) VALUES "
                f"({sql_literal(manifest['run_id'])}, {sql_literal(slot['slot_id'])}, "
                f"{sql_literal(file_rec['file_sha256'])}, {sql_literal(file_rec['file_size_bytes'])}, "
                f"{sql_literal(file_rec['extension'])}, {sql_literal(file_rec['sheet_count'])}, "
                f"{sql_literal(file_rec['sheet_names_sha256'])}, {sql_literal(file_rec['matched_pattern'])}, "
                f"{sql_literal(file_rec['is_symlink'])});"
            )
    for output_type, out in manifest["outputs"].items():
        lines.append(
            "INSERT OR REPLACE INTO monthly_report_output_index "
            "(run_id, output_type, file_sha256, file_size_bytes, retained_locally, committed_plaintext_to_git) "
            "VALUES "
            f"({sql_literal(manifest['run_id'])}, {sql_literal(output_type)}, "
            f"{sql_literal(out['file_sha256'])}, {sql_literal(out['file_size_bytes'])}, "
            f"{sql_literal(out['retained_locally'])}, {sql_literal(out['committed_plaintext_to_git'])});"
        )
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def smoke_test_sql(schema_path: Path, export_sql: str) -> None:
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.executescript(export_sql)
    finally:
        conn.close()


def write_artifacts(manifest: dict, metadata_root: Path) -> None:
    ensure_metadata_dirs(metadata_root)
    period = manifest["period"]
    raw_index = {
        "period": period,
        "run_id": manifest["run_id"],
        "public_safe_only": True,
        "input_slots": manifest["input_slots"],
    }
    report_index = {
        "period": period,
        "run_id": manifest["run_id"],
        "outputs": manifest["outputs"],
        "plaintext_reports_committed_to_git": False,
    }
    cleanup_audit = cleanup_audit_for_outputs(period, manifest["outputs"])
    backup_entry = {
        "period": period,
        "run_id": manifest["run_id"],
        "created_at_utc": manifest["created_at_utc"],
        "metadata_paths": [
            f"KMFA/metadata/mgmt-monthly-report-skill/raw_index/{period}_public_safe_source_index.json",
            f"KMFA/metadata/mgmt-monthly-report-skill/run_manifests/{period}_public_safe_run_manifest.json",
            f"KMFA/metadata/mgmt-monthly-report-skill/public_reports/{period}_output_report_index.json",
            f"KMFA/metadata/mgmt-monthly-report-skill/database/{period}_registry_export.sql",
        ],
        "raw_sensitive_plaintext_uploaded": False,
        "reason": "KMFA AGENTS.md permits public-safe hashes/manifests only for sensitive经营数据.",
        "status": manifest["status"],
    }
    log_entry = {
        "event": "monthly_report_register",
        "period": period,
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "errors": manifest["errors"],
        "warnings": manifest["warnings"],
        "created_at_utc": manifest["created_at_utc"],
    }

    write_json(metadata_root / "raw_index" / f"{period}_public_safe_source_index.json", raw_index)
    write_json(metadata_root / "run_manifests" / f"{period}_public_safe_run_manifest.json", manifest)
    write_json(metadata_root / "public_reports" / f"{period}_output_report_index.json", report_index)
    write_json(metadata_root / "cleanup" / f"{period}_cleanup_audit.json", cleanup_audit)
    jsonl_append(metadata_root / "backup_registry" / "backup_upload_register.jsonl", backup_entry)
    jsonl_append(metadata_root / "logs" / f"{period}_public_safe_run_log.jsonl", log_entry)

    export_sql = render_sql_export(manifest)
    schema_path = metadata_root / "database" / "schema.sql"
    if schema_path.exists():
        smoke_test_sql(schema_path, export_sql)
    (metadata_root / "database" / f"{period}_registry_export.sql").write_text(export_sql, encoding="utf-8")


def cleanup_audit_for_outputs(period: str, outputs: dict) -> dict:
    return {
        "period": period,
        "target_state": "local_report_output_dir_keeps_official_xlsx_and_pdf_only",
        "official_outputs": outputs,
        "auto_deleted_files": [],
        "destructive_deletion_performed": False,
        "notes": [
            "This audit does not delete user original input files.",
            "Run-specific temp/cache cleanup must be limited to skill-created artifacts.",
        ],
    }


def validate_manifest(manifest: dict) -> int:
    if manifest["status"] == "failed":
        return 2
    if manifest["status"] == "warning":
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register and govern KMFA management monthly report runs.")
    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register", help="Create public-safe run metadata without copying raw data.")
    register.add_argument("--period", required=True)
    register.add_argument("--input-dir", required=True, type=Path)
    register.add_argument("--output-dir", required=True, type=Path)
    register.add_argument("--metadata-root", default=Path("KMFA/metadata/mgmt-monthly-report-skill"), type=Path)
    register.add_argument("--write", action="store_true", help="Write metadata artifacts. Without this flag, print manifest only.")
    register.add_argument("--strict", action="store_true", help="Return non-zero for warnings as well as failures.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "register":
        manifest = build_manifest(args.period, args.input_dir, args.output_dir, args.metadata_root)
        if args.write:
            write_artifacts(manifest, args.metadata_root)
        else:
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
        code = validate_manifest(manifest)
        return code if args.strict else (2 if code == 2 else 0)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
