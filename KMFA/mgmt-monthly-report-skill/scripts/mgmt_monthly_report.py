#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
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
    public_source_ref: str
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
        "SRC-MMR-V2-001",
        "WPS 武汉开明 2026年回款表",
        ("*2026*回款表*.xlsx", "*2026*回款*.xlsx"),
        prefer_patterns=("*销售会计*.xlsx",),
    ),
    InputSlot(
        "invoice_tax_cash",
        "SRC-MMR-V2-002",
        "开票纳税资金汇总表",
        ("*开票*纳税*资金汇总*.xlsx",),
        required_sheet_aliases=(
            ("开票纳税汇总", ("开票纳税汇总", "*开票*纳税*汇总*", "*各个主体*开票*纳税*")),
            ("2026年销售回款", ("2026年销售回款", "*销售回款*", "*回2026年合同款*", "*回款*合同款*")),
            ("2026年资金汇总", ("2026年资金汇总", "*资金汇总*", "*资金流汇总*")),
        ),
    ),
    InputSlot("receivable_contract", "SRC-MMR-V2-003", "应收账款合同登记", ("*应收账款*合同登记*.xlsx", "*合同登记*.xlsx")),
    InputSlot("aging", "SRC-MMR-V2-004", "应收账龄表", ("*应收账龄*.xlsx",)),
    InputSlot("deposit", "SRC-MMR-V2-005", "2026年保证金", ("*保证金2026*.xlsx", "*保证金*.xlsx")),
    InputSlot("three_major_projects", "SRC-MMR-V2-006", "三大项目", ("*三大项目*.xlsx",)),
    InputSlot(
        "project_status_contracts",
        "SRC-MMR-V2-007",
        "生产项目状态表与红圈主合同",
        ("*生产项目状态表*.xlsx", "*红圈主合同*.xlsx"),
        min_physical_files=1,
        recommended_physical_files=2,
        allow_multiple=True,
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def inspect_xlsx_sheets(path: Path) -> tuple[list[str], str | None]:
    try:
        with zipfile.ZipFile(path) as zf:
            data = zf.read("xl/workbook.xml")
    except Exception:  # noqa: BLE001 - fail closed without exposing source details
        return [], "workbook_structure_unreadable"

    try:
        root = ET.fromstring(data)
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheets = [elem.attrib.get("name", "") for elem in root.findall(".//main:sheets/main:sheet", ns)]
        return [s for s in sheets if s], None
    except Exception:  # noqa: BLE001
        return [], "workbook_structure_invalid"


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
        status = slot_status(slot, selected, alternates)
        if status.startswith("failed"):
            errors.append(f"{slot.public_source_ref}:{status}")
        elif status.startswith("warning"):
            warnings.append(f"{slot.public_source_ref}:{status}")

        sheet_group_passed_count = 0
        sheet_group_failed_count = 0
        if slot.required_sheet_aliases and selected:
            sheets, sheet_error = inspect_xlsx_sheets(selected[0])
            for _, aliases in slot.required_sheet_aliases:
                matched = match_aliases(sheets, aliases)
                ok = bool(matched)
                if not ok:
                    errors.append(f"{slot.public_source_ref}:required_sheet_group_missing")
                    sheet_group_failed_count += 1
                else:
                    sheet_group_passed_count += 1
            if sheet_error:
                errors.append(f"{slot.public_source_ref}:sheet_structure_unreadable")

        input_slots.append(
            {
                "source_group_ref": slot.public_source_ref,
                "status": status,
                "selection_status": selection_reason,
                "candidate_count": len(candidates),
                "selected_count": len(selected),
                "alternate_candidate_count": len(alternates),
                "minimum_required_count": slot.min_physical_files,
                "recommended_count": slot.recommended_physical_files,
                "required_sheet_group_count": len(slot.required_sheet_aliases),
                "passed_sheet_group_count": sheet_group_passed_count,
                "failed_sheet_group_count": sheet_group_failed_count,
            }
        )

    excel = output_dir / OFFICIAL_EXCEL.format(period=period)
    pdf = output_dir / OFFICIAL_PDF.format(period=period)
    outputs = [
        output_record("OUT-MMR-V2-001", excel),
        output_record("OUT-MMR-V2-002", pdf),
    ]

    status = "failed" if errors else ("warning" if warnings else "passed")
    return {
        "schema_version": "mgmt-monthly-report-public-safe-v2",
        "record_type": "deidentified_run_manifest",
        "period": period,
        "run_id": run_id,
        "created_at_utc": utc_now(),
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "input_slot_count": len(INPUT_SLOTS),
        "input_slots": input_slots,
        "outputs": outputs,
        "metadata_root_ref": "META-MMR-PUBLIC-V2",
        "metadata_policy": {
            "public_safe_only": True,
            "opaque_refs_non_derived": True,
            "private_or_source_digests_committed_to_git": False,
            "raw_sensitive_plaintext_committed_to_git": False,
            "report_plaintext_committed_to_git": False,
            "runtime_sqlite_committed_to_git": False,
        },
    }


def output_record(output_ref: str, path: Path) -> dict:
    exists = path.exists()
    return {
        "output_ref": output_ref,
        "status": "present" if exists else "missing",
        "retained_locally": exists,
        "committed_plaintext_to_git": False,
    }


def ensure_metadata_dirs(root: Path) -> None:
    for name in [
        "backup_registry",
        "cleanup",
        "database",
        "run_status",
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
        "-- Public-safe aggregate SQL export generated by mgmt_monthly_report.py v2.",
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
        lines.append(
            "INSERT OR REPLACE INTO monthly_report_input_slot_aggregate "
            "(run_id, source_group_ref, status, selection_status, candidate_count, selected_count, "
            "alternate_candidate_count, minimum_required_count, recommended_count, "
            "required_sheet_group_count, passed_sheet_group_count, failed_sheet_group_count) VALUES "
            f"({sql_literal(manifest['run_id'])}, {sql_literal(slot['source_group_ref'])}, "
            f"{sql_literal(slot['status'])}, {sql_literal(slot['selection_status'])}, "
            f"{sql_literal(slot['candidate_count'])}, {sql_literal(slot['selected_count'])}, "
            f"{sql_literal(slot['alternate_candidate_count'])}, {sql_literal(slot['minimum_required_count'])}, "
            f"{sql_literal(slot['recommended_count'])}, {sql_literal(slot['required_sheet_group_count'])}, "
            f"{sql_literal(slot['passed_sheet_group_count'])}, {sql_literal(slot['failed_sheet_group_count'])});"
        )
    for out in manifest["outputs"]:
        lines.append(
            "INSERT OR REPLACE INTO monthly_report_output_status "
            "(run_id, output_ref, status, retained_locally, committed_plaintext_to_git) "
            "VALUES "
            f"({sql_literal(manifest['run_id'])}, {sql_literal(out['output_ref'])}, "
            f"{sql_literal(out['status'])}, "
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
        "schema_version": "mgmt-monthly-report-public-safe-v2",
        "record_type": "deidentified_source_aggregate_index",
        "period": period,
        "run_id": manifest["run_id"],
        "metadata_mode": "strict_public_safe_metadata_only",
        "owner_plaintext_exception_effective": False,
        "input_slots": manifest["input_slots"],
    }
    report_index = {
        "schema_version": "mgmt-monthly-report-public-safe-v2",
        "record_type": "deidentified_output_status_index",
        "period": period,
        "run_id": manifest["run_id"],
        "outputs": manifest["outputs"],
        "plaintext_reports_committed_to_git": False,
    }
    cleanup_audit = cleanup_audit_for_outputs(period, manifest["outputs"])
    backup_entry = {
        "schema_version": "mgmt-monthly-report-public-safe-v2",
        "record_type": "public_artifact_backup_status",
        "period": period,
        "run_id": manifest["run_id"],
        "created_at_utc": manifest["created_at_utc"],
        "public_artifact_refs": [
            f"KMFA/metadata/mgmt-monthly-report-skill/raw_index/{period}_public_safe_source_index.json",
            f"KMFA/metadata/mgmt-monthly-report-skill/run_manifests/{period}_public_safe_run_manifest.json",
            f"KMFA/metadata/mgmt-monthly-report-skill/public_reports/{period}_output_report_index.json",
            f"KMFA/metadata/mgmt-monthly-report-skill/database/{period}_registry_export.sql",
        ],
        "raw_sensitive_plaintext_uploaded": False,
        "reason": (
            "KMFA v1.5 public-repository policy denies plaintext sensitive uploads for every role; "
            "this register command records strict public-safe metadata only and does not copy raw files."
        ),
        "status": manifest["status"],
    }
    log_entry = {
        "schema_version": "mgmt-monthly-report-public-safe-v2",
        "record_type": "aggregate_run_status",
        "event": "monthly_report_register",
        "period": period,
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "error_count": len(manifest["errors"]),
        "warning_count": len(manifest["warnings"]),
        "created_at_utc": manifest["created_at_utc"],
    }

    write_json(metadata_root / "raw_index" / f"{period}_public_safe_source_index.json", raw_index)
    write_json(metadata_root / "run_manifests" / f"{period}_public_safe_run_manifest.json", manifest)
    write_json(metadata_root / "public_reports" / f"{period}_output_report_index.json", report_index)
    write_json(metadata_root / "cleanup" / f"{period}_cleanup_audit.json", cleanup_audit)
    jsonl_append(metadata_root / "backup_registry" / "backup_upload_register.jsonl", backup_entry)
    jsonl_append(metadata_root / "run_status" / f"{period}_public_safe_run_status.jsonl", log_entry)

    export_sql = render_sql_export(manifest)
    schema_path = metadata_root / "database" / "schema.sql"
    if schema_path.exists():
        smoke_test_sql(schema_path, export_sql)
    (metadata_root / "database" / f"{period}_registry_export.sql").write_text(export_sql, encoding="utf-8")


def cleanup_audit_for_outputs(period: str, outputs: list[dict]) -> dict:
    return {
        "schema_version": "mgmt-monthly-report-public-safe-v2",
        "record_type": "aggregate_cleanup_status",
        "period": period,
        "target_state": "local_output_retention_policy_applied",
        "output_statuses": outputs,
        "auto_deleted_item_count": 0,
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

    register = sub.add_parser(
        "register",
        help="Create governed run metadata; this command does not copy raw data.",
    )
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
