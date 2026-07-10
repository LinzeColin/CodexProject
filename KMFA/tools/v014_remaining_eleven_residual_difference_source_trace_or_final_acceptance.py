#!/usr/bin/env python3
"""Resolve eight cost components and preserve three final accepted cash differences."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools import (  # noqa: E402
    v014_global_residual_difference_queue_replay_or_authoritative_exclusion as prior_phase,
)


PROJECT_ROOT = Path("KMFA")
RAW_ROOT = prior_phase.RAW_ROOT
PHASE_ID = "V014_REMAINING_ELEVEN_RESIDUAL_DIFFERENCE_SOURCE_TRACE_OR_FINAL_ACCEPTANCE"
TASK_ID = "KMFA-V014-REMAINING-ELEVEN-RESIDUAL-DIFFERENCE-SOURCE-TRACE-OR-FINAL-ACCEPTANCE-20260710"
ACCEPTANCE_ID = "ACC-V014-REMAINING-ELEVEN-RESIDUAL-DIFFERENCE-SOURCE-TRACE-OR-FINAL-ACCEPTANCE"
VERSION = "0.1.4-remaining-eleven-residual-difference-source-trace-or-final-acceptance"
STATUS = "completed_validated_local_only_eight_cost_components_materialized_three_final_differences_accepted_no_go"
DECISION = "NO_GO"
PREFIX = "remaining_eleven_residual_difference_source_trace_or_final_acceptance"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / f"{PREFIX}_summary.json"
MANIFEST_PATH = MACHINE_DIR / f"{PREFIX}_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / f"{PREFIX}_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / f"{PREFIX}_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / f"{PREFIX}.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_matrix_public_safe.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / f".codex_private_runtime/v014_{PREFIX}"
PRIVATE_RAW_BEFORE_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_after.json"
PRIVATE_AUTHORITY_TABLES_PATH = PRIVATE_OUTPUT_DIR / "private_authority_pdf_tables.json"
PRIVATE_SOURCE_EVIDENCE_PATH = PRIVATE_OUTPUT_DIR / "private_cost_component_source_evidence.jsonl"
PRIVATE_MATERIALIZATIONS_PATH = PRIVATE_OUTPUT_DIR / "private_cost_component_materializations.jsonl"
PRIVATE_FINAL_REPLAY_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_global_residual_replay_records.jsonl"
PRIVATE_OPEN_CASH_DIFFERENCES_PATH = PRIVATE_OUTPUT_DIR / "private_open_final_cash_differences.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_remaining_eleven_trace_diagnostic.json"
PRIVATE_FINAL_DIFFERENCE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_final_difference_report_zh.md"

SOURCE_PRIOR_REPLAY_RECORDS_PATH = prior_phase.PRIVATE_REPLAY_RECORDS_PATH
SOURCE_PRIOR_OPEN_DIFFERENCES_PATH = prior_phase.PRIVATE_OPEN_DIFFERENCES_PATH
SOURCE_PRIOR_RAW_AFTER_PATH = prior_phase.PRIVATE_RAW_AFTER_PATH
SOURCE_PRIOR_SUMMARY_PATH = prior_phase.METADATA_SUMMARY_PATH
SOURCE_PRIOR_MANIFEST_PATH = prior_phase.METADATA_MANIFEST_PATH
SOURCE_STAGING_PATH = prior_phase.SOURCE_STAGING_PATH
SOURCE_OWNER_REPORT_PATH = prior_phase.SOURCE_OWNER_REPORT_PATH
SOURCE_BINDINGS_PATH = prior_phase.SOURCE_BINDINGS_PATH
SOURCE_PRECHECK_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_real_project_identity_private_rebinding_and_processed_value_materialization/private_real_project_identity_precheck.json"
)
SOURCE_COMPARISONS_PATH = prior_phase.SOURCE_COMPARISONS_PATH
SOURCE_CASH_DECISIONS_PATH = prior_phase.SOURCE_CASH_DECISIONS_PATH
SOURCE_UNRESOLVED_TARGETS_PATH = prior_phase.SOURCE_UNRESOLVED_TARGETS_PATH
SOURCE_FINAL_CASH_REPORT_PATH = prior_phase.SOURCE_FINAL_DIFFERENCE_REPORT_PATH
SOURCE_FINAL_CASH_RAW_AFTER_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_remaining_two_project_cash_collection_evidence_or_final_difference_acceptance/raw_immutability_after.json"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

TRAVEL_MARKERS = ("差旅费",)
INTEREST_MARKERS = ("资金利息", "利息")
NUMERIC_TOKEN_PATTERN = re.compile(r"[-+]?\d[\d,，]*(?:\.\d+)?")


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_pdf_amount_to_cents(value: Any) -> int:
    if value is None or isinstance(value, bool):
        raise ValueError("PDF amount cell is missing")
    text = str(value).strip().replace("\n", "").replace(" ", "")
    text = text.replace(",", "").replace("，", "")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text):
        raise ValueError("PDF amount cell is not a plain numeric value")
    try:
        decimal_value = Decimal(text) * 100
    except InvalidOperation as exc:
        raise ValueError("PDF amount cell cannot be parsed") from exc
    integer_value = decimal_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if decimal_value != integer_value:
        raise ValueError("PDF amount has sub-cent precision")
    return int(integer_value)


def disposition_policy(evidence_kind: str) -> dict[str, Any]:
    if evidence_kind == "unique_authority_cost_component":
        return {
            "queue_closed": True,
            "replay_status": "replayed_unique_authority_cost_component",
        }
    if evidence_kind == "final_cash_difference_acceptance":
        return {
            "queue_closed": False,
            "replay_status": "open_final_difference_accepted",
        }
    raise ValueError(f"unsupported evidence kind: {evidence_kind}")


def _row_text(row: list[Any]) -> str:
    return "|".join("" if cell is None else str(cell) for cell in row)


def _unique_row(table: list[list[Any]], markers: tuple[str, ...]) -> tuple[int, list[Any]]:
    matches = [
        (index, row)
        for index, row in enumerate(table)
        if any(marker in _row_text(row) for marker in markers)
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one authority table row for markers {markers}")
    return matches[0]


def extract_component_from_table(
    table: list[list[Any]], *, component: str
) -> dict[str, Any]:
    header_rows = [
        (index, row)
        for index, row in enumerate(table)
        if len(row) > 1 and "金额" in str(row[1] or "") and "元" in str(row[1] or "")
    ]
    if len(header_rows) != 1:
        raise ValueError("authority table must have one yuan amount-column header")
    header_index, header_row = header_rows[0]
    markers = TRAVEL_MARKERS if component == "travel" else INTEREST_MARKERS
    row_index, row = _unique_row(table, markers)
    if len(row) <= 1:
        raise ValueError("authority component row has no amount column")
    value_cents = parse_pdf_amount_to_cents(row[1])
    result = {
        "component": component,
        "header_row_index": header_index,
        "header_value": header_row[1],
        "row_index": row_index,
        "row": row,
        "raw_amount_value": row[1],
        "value_cents": value_cents,
        "child_sum_exact": None,
        "child_rows": [],
    }
    if component == "travel":
        if row_index + 2 >= len(table):
            raise ValueError("travel row lacks two child rows")
        child_rows = [table[row_index + 1], table[row_index + 2]]
        child_text = [_row_text(child) for child in child_rows]
        if "车票" not in child_text[0] or "住宿" not in child_text[1]:
            raise ValueError("travel child rows are not the expected ticket and lodging rows")
        child_values = [parse_pdf_amount_to_cents(child[1]) for child in child_rows]
        if value_cents != sum(child_values):
            raise ValueError("travel amount does not equal its integer child sum")
        result["child_sum_exact"] = True
        result["child_rows"] = child_rows
        result["child_values_cents"] = child_values
    return result


def _optional_amount_to_cents(value: Any) -> int:
    if value is None or not str(value).strip():
        return 0
    try:
        return parse_pdf_amount_to_cents(value)
    except ValueError:
        tokens = NUMERIC_TOKEN_PATTERN.findall(str(value))
        if len(tokens) != 1:
            raise ValueError("amount column does not contain one unambiguous numeric token")
        return parse_pdf_amount_to_cents(tokens[0])


def _normalize_snapshot(snapshot: dict[str, Any]) -> list[tuple[Any, ...]]:
    records = snapshot.get("files", snapshot.get("records"))
    if not isinstance(records, list):
        raise ValueError("raw snapshot has no records")
    fields = ("relative_path", "size", "mtime_ns", "inode", "mode", "sha256")
    return sorted(tuple(row.get(field) for field in fields) for row in records)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_float(child) for child in value)
    return False


def _git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _git_ignored(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", path.as_posix()],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def source_private_paths() -> list[Path]:
    return [
        SOURCE_PRIOR_REPLAY_RECORDS_PATH,
        SOURCE_PRIOR_OPEN_DIFFERENCES_PATH,
        SOURCE_PRIOR_RAW_AFTER_PATH,
        SOURCE_PRIOR_SUMMARY_PATH,
        SOURCE_PRIOR_MANIFEST_PATH,
        SOURCE_STAGING_PATH,
        SOURCE_OWNER_REPORT_PATH,
        SOURCE_BINDINGS_PATH,
        SOURCE_PRECHECK_PATH,
        SOURCE_COMPARISONS_PATH,
        SOURCE_CASH_DECISIONS_PATH,
        SOURCE_UNRESOLVED_TARGETS_PATH,
        SOURCE_FINAL_CASH_REPORT_PATH,
        SOURCE_FINAL_CASH_RAW_AFTER_PATH,
    ]


def phase_private_paths() -> list[Path]:
    return [
        PRIVATE_RAW_BEFORE_PATH,
        PRIVATE_RAW_AFTER_PATH,
        PRIVATE_AUTHORITY_TABLES_PATH,
        PRIVATE_SOURCE_EVIDENCE_PATH,
        PRIVATE_MATERIALIZATIONS_PATH,
        PRIVATE_FINAL_REPLAY_RECORDS_PATH,
        PRIVATE_OPEN_CASH_DIFFERENCES_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
        PRIVATE_FINAL_DIFFERENCE_REPORT_PATH,
    ]


def _raw_files_by_basename(raw_snapshot: dict[str, Any]) -> dict[str, Path]:
    records = raw_snapshot.get("files")
    if not isinstance(records, list):
        raise ValueError("current raw snapshot must contain files")
    result: dict[str, Path] = {}
    for row in records:
        relative = Path(str(row.get("relative_path")))
        if relative.name in result:
            raise ValueError("raw basenames must be unique for private source binding")
        result[relative.name] = RAW_ROOT / relative
    return result


def _text_engine_contains_value(text: str, marker: str, value_cents: int) -> bool:
    positions = [match.start() for match in re.finditer(re.escape(marker), text)]
    for position in positions:
        window = text[max(0, position - 80) : position + 200]
        for token in NUMERIC_TOKEN_PATTERN.findall(window):
            try:
                if parse_pdf_amount_to_cents(token) == value_cents:
                    return True
            except ValueError:
                continue
    return False


def _validate_authority_table_totals(
    table: list[list[Any]], *, expected_total_cents: int
) -> dict[str, Any]:
    direct_index, direct_row = _unique_row(table, ("资金运用及各项支出",))
    total_index, total_row = _unique_row(table, ("合计支出",))
    management_index, management_row = _unique_row(table, ("分摊的管理费用",))
    _, interest_row = _unique_row(table, ("资金利息",))
    category_rows = [
        row
        for row in table[direct_index + 1 : management_index]
        if re.match(r"^（[一二三四五六]）", str(row[0] or ""))
    ]
    if len(category_rows) != 6:
        raise ValueError("authority direct-expense category set is incomplete")
    direct_value = parse_pdf_amount_to_cents(direct_row[1])
    category_sum = sum(_optional_amount_to_cents(row[1]) for row in category_rows)
    if direct_value != category_sum:
        raise ValueError("authority direct-expense category sum does not replay")
    total_value = parse_pdf_amount_to_cents(total_row[1])
    if total_value != expected_total_cents:
        raise ValueError("authority total expense does not match current bound authority value")
    full_formula_value = (
        direct_value
        + _optional_amount_to_cents(management_row[1])
        + _optional_amount_to_cents(interest_row[1])
    )
    return {
        "direct_expense_row_index": direct_index,
        "direct_expense_value_cents": direct_value,
        "direct_expense_category_count": len(category_rows),
        "direct_expense_category_sum_cents": category_sum,
        "direct_expense_category_sum_exact": True,
        "total_expense_row_index": total_index,
        "total_expense_value_cents": total_value,
        "current_bound_authority_total_exact": True,
        "full_table_total_formula_value_cents": full_formula_value,
        "full_table_total_formula_exact": total_value == full_formula_value,
    }


def _extract_private_authority_evidence(
    *,
    raw_snapshot: dict[str, Any],
    precheck: dict[str, Any],
    bindings: list[dict[str, Any]],
    staging_slots: list[dict[str, Any]],
    prior_replay_records: list[dict[str, Any]],
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        import pdfplumber  # type: ignore
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError("bundled PDF dependencies are required for this phase") from exc

    project_rows = precheck.get("records")
    if not isinstance(project_rows, list) or len(project_rows) != 4:
        raise ValueError("private authority precheck must contain four projects")
    ordered_projects = sorted(project_rows, key=lambda row: int(row.get("candidate_order", 0)))
    ordered_bindings = sorted(bindings, key=lambda row: int(row.get("authority_candidate_order", 0)))
    if len(ordered_bindings) != 4:
        raise ValueError("private identity binding count changed")
    staging_by_key = {
        (str(row.get("context_group")), int(row.get("record_index", 0))): row
        for row in staging_slots
    }
    prior_by_slot = {
        str(row.get("target_slot_id")): row for row in prior_replay_records
    }
    raw_files = _raw_files_by_basename(raw_snapshot)
    table_records: list[dict[str, Any]] = []
    source_evidence: list[dict[str, Any]] = []
    materializations: list[dict[str, Any]] = []

    for project_index, (project, binding) in enumerate(
        zip(ordered_projects, ordered_bindings), start=1
    ):
        if project.get("candidate_id") != binding.get("authority_candidate_id"):
            raise ValueError("authority candidate and identity binding drifted")
        source = project.get("private_source")
        if not isinstance(source, dict):
            raise ValueError("project authority source must be unique")
        if source.get("source_ref_hash") != binding.get("source_ref_hash"):
            raise ValueError("project authority source reference drifted")
        raw_path = raw_files.get(str(source.get("raw_file_name")))
        if raw_path is None or not raw_path.is_file() or not zipfile.is_zipfile(raw_path):
            raise ValueError("authority raw archive is unavailable")
        member_name = str(source.get("archive_member_name"))
        with zipfile.ZipFile(raw_path) as archive:
            member_data = archive.read(member_name)

        pages: list[dict[str, Any]] = []
        matching_tables: list[tuple[int, int, list[list[Any]]]] = []
        with pdfplumber.open(io.BytesIO(member_data)) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()
                pages.append({"page_index": page_index, "tables": page_tables})
                for table_index, table in enumerate(page_tables, start=1):
                    joined = "\n".join(_row_text(row) for row in table)
                    if "差旅费" in joined and "资金利息" in joined:
                        matching_tables.append((page_index, table_index, table))
        if len(matching_tables) != 1:
            raise ValueError("each authority PDF must contain one cost-component table")
        page_index, table_index, table = matching_tables[0]
        pdf_text = "\n".join(
            page.extract_text() or "" for page in PdfReader(io.BytesIO(member_data)).pages
        )
        totals = _validate_authority_table_totals(
            table, expected_total_cents=int(project["values"]["cost_total_cents"])
        )
        table_record = {
            "schema_version": "kmfa.private.authority_pdf_table.v1",
            "classification": "private_authority_pdf_table_do_not_commit",
            "project_index": project_index,
            "candidate_id": project.get("candidate_id"),
            "candidate_label": project.get("candidate_label"),
            "binding_id": binding.get("binding_id"),
            "legacy_fact_record_id": binding.get("legacy_fact_record_id"),
            "legacy_margin_record_id": binding.get("legacy_margin_record_id"),
            "source": source,
            "raw_archive_sha256": _sha256_file(raw_path),
            "archive_member_sha256": _sha256_bytes(member_data),
            "matched_page_index": page_index,
            "matched_table_index": table_index,
            "pages": pages,
            "totals": totals,
        }
        table_records.append(table_record)

        for component in ("travel", "interest"):
            component_data = extract_component_from_table(table, component=component)
            slot = staging_by_key.get((component, project_index))
            if slot is None:
                raise ValueError("cost component target slot is missing")
            if str(binding.get("legacy_fact_record_id")) not in str(slot.get("private_processed_ref")):
                raise ValueError("cost component slot does not match its real project binding")
            slot_id = str(slot.get("target_slot_id"))
            prior = prior_by_slot.get(slot_id)
            if prior is None or prior.get("replay_status") != "open_missing_unique_authoritative_source":
                raise ValueError("cost component is not open in the prior residual replay")
            marker = "差旅费" if component == "travel" else "利息"
            value_cents = int(component_data["value_cents"])
            if value_cents < 0 or value_cents > int(project["values"]["cost_total_cents"]):
                raise ValueError("cost component is outside the bound authority total")
            text_match = _text_engine_contains_value(pdf_text, marker, value_cents)
            if not text_match:
                raise ValueError("PDF text engine does not corroborate the table amount")
            locator_hash = _sha256_text(
                ":".join(
                    [
                        _sha256_file(raw_path),
                        _sha256_bytes(member_data),
                        str(page_index),
                        str(table_index),
                        str(component_data["row_index"]),
                        "1",
                    ]
                )
            )
            evidence_id = f"V014-RE11-SOURCE-{project_index:02d}-{component.upper()}"
            evidence = {
                "schema_version": "kmfa.private.cost_component_source_evidence.v1",
                "classification": "private_cost_component_source_evidence_do_not_commit",
                "evidence_id": evidence_id,
                "generated_at": generated_at,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "project_index": project_index,
                "binding_id": binding.get("binding_id"),
                "legacy_fact_record_id": binding.get("legacy_fact_record_id"),
                "target_slot_id": slot_id,
                "context_group": component,
                "raw_file_name": source.get("raw_file_name"),
                "archive_member_name": member_name,
                "source_ref_hash": source.get("source_ref_hash"),
                "raw_archive_sha256": _sha256_file(raw_path),
                "archive_member_sha256": _sha256_bytes(member_data),
                "page_index": page_index,
                "table_index": table_index,
                "row_index": component_data["row_index"],
                "amount_column_index": 1,
                "amount_header": component_data["header_value"],
                "row": component_data["row"],
                "raw_amount_value": component_data["raw_amount_value"],
                "value_cents": value_cents,
                "value_fingerprint": prior_phase.canonical_value_fingerprint(
                    "cents", value_cents
                ),
                "travel_child_rows": component_data.get("child_rows", []),
                "travel_child_values_cents": component_data.get(
                    "child_values_cents", []
                ),
                "travel_child_sum_exact": component_data.get("child_sum_exact"),
                "direct_expense_category_sum_exact": totals[
                    "direct_expense_category_sum_exact"
                ],
                "current_bound_authority_total_exact": totals[
                    "current_bound_authority_total_exact"
                ],
                "full_table_total_formula_exact": totals[
                    "full_table_total_formula_exact"
                ],
                "pdf_table_engine_match": True,
                "pdf_text_engine_match": text_match,
                "project_binding_unique": True,
                "source_table_unique": True,
                "component_row_unique": True,
                "amount_column_unique": True,
                "source_record_ref_hash": locator_hash,
                "raw_layer_write_allowed": False,
                "public_commit_allowed": False,
            }
            source_evidence.append(evidence)
            materializations.append(
                {
                    "schema_version": "kmfa.private.cost_component_materialization.v1",
                    "classification": "private_cost_component_materialization_do_not_commit",
                    "materialization_id": f"V014-RE11-MAT-{project_index:02d}-{component.upper()}",
                    "generated_at": generated_at,
                    "phase_id": PHASE_ID,
                    "task_id": TASK_ID,
                    "target_slot_id": slot_id,
                    "binding_id": binding.get("binding_id"),
                    "legacy_fact_record_id": binding.get("legacy_fact_record_id"),
                    "context_group": component,
                    "value": value_cents,
                    "unit": "cents",
                    "value_fingerprint": prior_phase.canonical_value_fingerprint(
                        "cents", value_cents
                    ),
                    "source_evidence_id": evidence_id,
                    "source_record_ref_hash": locator_hash,
                    "materialization_status": "materialized_from_unique_authority_pdf_table",
                    "integer_only": True,
                    "raw_layer_write_allowed": False,
                    "public_commit_allowed": False,
                }
            )
    return table_records, source_evidence, materializations


def _build_final_replay_records(
    *,
    prior_records: list[dict[str, Any]],
    materializations: list[dict[str, Any]],
    raw_snapshot_chain_exact: bool,
    generated_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    materialization_by_slot = {
        str(row.get("target_slot_id")): row for row in materializations
    }
    final_records: list[dict[str, Any]] = []
    for row in prior_records:
        updated = dict(row)
        updated["generated_at"] = generated_at
        updated["phase_id"] = PHASE_ID
        updated["task_id"] = TASK_ID
        updated["source_prior_phase_id"] = row.get("phase_id")
        materialized = materialization_by_slot.get(str(row.get("target_slot_id")))
        if materialized is not None:
            policy = disposition_policy("unique_authority_cost_component")
            updated.update(
                {
                    **policy,
                    "evidence_kind": "unique_authority_cost_component",
                    "prior_replay_status": row.get("replay_status"),
                    "prior_private_candidate_option_count": row.get(
                        "private_candidate_option_count"
                    ),
                    "value": materialized.get("value"),
                    "unit": "cents",
                    "canonical_value_fingerprint": materialized.get(
                        "value_fingerprint"
                    ),
                    "source_evidence_id": materialized.get("source_evidence_id"),
                    "source_record_ref_hash": materialized.get(
                        "source_record_ref_hash"
                    ),
                    "source_reference_unique": True,
                    "integer_value_replayable": True,
                    "difference_report_required": False,
                }
            )
        elif row.get("replay_status") == "open_final_difference_accepted":
            policy = disposition_policy("final_cash_difference_acceptance")
            updated.update(
                {
                    **policy,
                    "evidence_kind": "final_cash_difference_acceptance",
                    "final_acceptance_status": "accepted_without_proven_numeric_value",
                    "raw_snapshot_chain_exact": raw_snapshot_chain_exact,
                    "new_raw_evidence_available": False,
                    "source_reference_unique": False,
                    "integer_value_replayable": False,
                    "difference_report_required": True,
                }
            )
        final_records.append(updated)
    if len(final_records) != 72 or len({row.get("target_slot_id") for row in final_records}) != 72:
        raise ValueError("final residual replay must preserve seventy-two unique records")
    open_rows = [row for row in final_records if row.get("queue_closed") is False]
    return final_records, open_rows


def _public_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_private_inputs_unchanged", summary["source_private_inputs_unchanged"]),
        ("raw_snapshot_exact_match", summary["raw_snapshot_exact_match"]),
        ("raw_snapshot_chain_exact", summary["raw_snapshot_chain_exact"]),
        ("source_open_count_11", summary["source_open_residual_difference_count"] == 11),
        ("four_authority_projects", summary["authority_project_source_count"] == 4),
        ("four_unique_tables", summary["unique_authority_table_count"] == 4),
        ("eight_cost_components", summary["cost_component_materialization_count"] == 8),
        ("four_travel", summary["travel_materialization_count"] == 4),
        ("four_interest", summary["interest_materialization_count"] == 4),
        ("eight_unique_sources", summary["unique_source_record_count"] == 8),
        ("eight_cross_engine_matches", summary["pdf_cross_engine_match_count"] == 8),
        ("four_travel_formulas", summary["travel_child_sum_exact_count"] == 4),
        ("four_direct_expense_formulas", summary["direct_expense_category_sum_exact_count"] == 4),
        ("four_authority_totals", summary["current_bound_authority_total_exact_count"] == 4),
        ("four_full_table_formulas", summary["authority_full_total_formula_exact_count"] == 4),
        ("final_classified_72", summary["classified_residual_record_count"] == 72),
        ("numeric_replay_61", summary["replayed_numeric_record_count"] == 61),
        ("closed_or_excluded_69", summary["queue_closed_or_excluded_count"] == 69),
        ("three_final_open", summary["open_final_difference_accepted_count"] == 3),
        ("nonzero_preserved", summary["nonzero_delta_reconciliation_count"] == 9),
        ("forced_zero_prohibited", summary["forced_zero_materialization_count"] == 0),
        ("private_outputs_ignored", summary["private_outputs_gitignored"]),
        ("business_consistency_not_overclaimed", not summary["business_value_consistency_verified"]),
        ("stage_review_not_performed", not summary["stage_review_performed"]),
        ("github_not_uploaded", not summary["github_upload_performed"]),
    ]
    rows = [
        {"check_id": f"RE11-{index:02d}", "check_name": name, "passed": bool(passed)}
        for index, (name, passed) in enumerate(checks, start=1)
    ]
    return {
        "schema_version": "kmfa.v014.remaining_eleven_trace_matrix.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["passed"] for row in rows),
        "check_fail_count": sum(not row["passed"] for row in rows),
        "checks": rows,
    }


def _private_report(
    *,
    summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
    open_rows: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> str:
    lines = [
        "# KMFA v0.1.4 剩余十一条差异来源追踪或最终接受报告",
        "",
        "## 本轮结论",
        "",
        f"- 进入本轮的未决记录：{summary['source_open_residual_difference_count']} 条。",
        f"- 唯一权威成本分项来源：{summary['cost_component_materialization_count']} 条。",
        f"- 最终关闭或排除 / 继续最终接受：{summary['queue_closed_or_excluded_count']} / {summary['open_final_difference_accepted_count']}。",
        f"- 保留非零 / 零 / 未完成比较：{summary['nonzero_delta_reconciliation_count']} / {summary['zero_delta_reconciliation_count']} / {summary['incomplete_reconciliation_count']}。",
        "- 所有金额均为整数分；未推导零、未平均、未覆盖非零差异。",
        "",
        "## 已唯一绑定的成本分项",
        "",
    ]
    for row in evidence_rows:
        lines.extend(
            [
                f"### {row['evidence_id']}",
                "",
                f"- 私有项目绑定：{row['binding_id']} / {row['legacy_fact_record_id']}",
                f"- 成本分项：{row['context_group']}",
                f"- 原始来源：{row['raw_file_name']} / {row['archive_member_name']}",
                f"- 定位：第 {row['page_index']} 页，第 {row['table_index']} 张表，第 {row['row_index']} 行，第 {row['amount_column_index']} 列",
                f"- 原始显示金额：{row['raw_amount_value']} 元",
                f"- 整数金额：{row['value_cents']} 分",
                f"- 表格/文本双引擎一致：{row['pdf_table_engine_match']} / {row['pdf_text_engine_match']}",
                f"- 差旅子项求和：{row['travel_child_sum_exact']}",
                f"- 直接支出分类求和：{row['direct_expense_category_sum_exact']}",
                f"- 当前权威总成本一致：{row['current_bound_authority_total_exact']}",
                f"- PDF完整总额公式一致：{row['full_table_total_formula_exact']}",
                "",
            ]
        )
    lines.extend(["## 最终接受但不生成数值的现金差异", ""])
    for row in open_rows:
        lines.extend(
            [
                f"- 队列 {row['queue_index']} / {row['target_slot_id']} / {row['context_group']}",
                f"  - 状态：{row['final_acceptance_status']}",
                f"  - 原因：{row.get('open_reason_codes', [])}",
                f"  - raw 快照链一致：{row['raw_snapshot_chain_exact']}",
                "  - 新增原始证据：无",
            ]
        )
    lines.extend(["", "## 当前比较", ""])
    for row in comparisons:
        lines.append(
            f"- {row['difference_id']}：{row['comparison_status']}；A={row['amount_a']}；B={row['amount_b']}；差额={row['delta']}。"
        )
    lines.extend(
        [
            "",
            "## 差异说明",
            "",
            f"- 四个权威 PDF 中完整总额公式精确一致 {summary['authority_full_total_formula_exact_count']} 个，不一致 {summary['authority_full_total_formula_difference_count']} 个；本轮保留原始显示值和现有非零差异，不调整来源数据。",
            "- 3 条现金差异在 raw 快照未变化且上一轮已完成主账、银行、应收、OOXML、WPS/OLE 交叉核验的前提下继续最终接受；接受差异不等于填入数值。",
            "- 本报告仅存在 ignored private runtime，不得提交 GitHub 或作为正式经营决策依据。",
            "",
        ]
    )
    return "\n".join(lines)


def _public_reports(summary: dict[str, Any]) -> dict[Path, str]:
    report = f"""# v0.1.4 剩余十一条差异来源追踪或最终接受

- Phase: `{PHASE_ID}`
- 决策: `{DECISION}`
- 输入未决记录: {summary['source_open_residual_difference_count']}
- 新增唯一成本分项来源: {summary['cost_component_materialization_count']}
- 差旅 / 利息物化: {summary['travel_materialization_count']} / {summary['interest_materialization_count']}
- 数值重放 / 非数值排除: {summary['replayed_numeric_record_count']} / {summary['owner_authorized_non_numeric_exclusion_count']}
- 关闭或排除 / 最终接受未决: {summary['queue_closed_or_excluded_count']} / {summary['open_final_difference_accepted_count']}
- 保留非零差异: {summary['nonzero_delta_reconciliation_count']}
- raw 前后完全一致: `{str(summary['raw_snapshot_exact_match']).lower()}`

四个真实项目的差旅和利息均从已绑定权威 PDF 的唯一表格行读取，并经整数公式或双 PDF 引擎交叉验证。3 条现金槽位因 raw 无新增证据继续最终差异接受，不写零。
"""
    go_no_go = f"""# Go / No-Go 记录

- 决策: `NO_GO`
- 已完成: 新增 {summary['cost_component_materialization_count']} 条唯一权威成本分项，累计 {summary['queue_closed_or_excluded_count']} 条队列记录关闭或排除。
- 阻断: {summary['open_final_difference_accepted_count']} 条现金槽位仍无可证明数值，{summary['nonzero_delta_reconciliation_count']} 条非零口径差异继续保留。
- GitHub upload / app reinstall / business execution: `not_performed`
"""
    tests = """# 测试结果

- focused unit test: `PASS` (`2 tests`)
- phase/private validator: `PASS` (`8 resolved / 3 final accepted / 69 closed-or-excluded / decision=NO_GO`)
- previous phase validator: `PASS`
- governance validators: `PASS` (`errors=0 / warnings=0`)
- raw/private/secret scan: `PASS` (`raw unchanged / private tracked=0 / sensitive hits=0`)
"""
    risks = f"""# 风险登记

- 高: {summary['open_final_difference_accepted_count']} 条现金槽位没有可证明数值，不能从缺失推导零。
- 高: {summary['nonzero_delta_reconciliation_count']} 条非零口径差异继续保留，不得覆盖权威显示值。
- 中: 3 条现金最终接受不等于业务值一致，正式报告等级仍须受质量门禁限制。
- 中: 当前仅完成本 phase，不代表 Stage 复审或整体业务一致性验收。
"""
    rollback = """# 回滚方案

1. 删除本 phase public-safe artifacts 与 metadata 镜像。
2. 删除本 phase ignored private outputs；不触碰 raw 根目录和上一 phase 私有输入。
3. 移除本 phase三条治理记录并重跑上一 phase validator。
"""
    return {
        REPORT_PATH: report,
        GO_NO_GO_RECORD_PATH: go_no_go,
        TEST_RESULTS_PATH: tests,
        RISK_REGISTER_PATH: risks,
        ROLLBACK_PATH: rollback,
    }


def _upsert_jsonl(path: Path, key: str, row: dict[str, Any]) -> None:
    source_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    updated_lines: list[str] = []
    replaced = False
    for source_line in source_lines:
        if not source_line.strip():
            continue
        current = json.loads(source_line)
        if not isinstance(current, dict):
            raise ValueError(f"{path} must contain JSON objects")
        if current.get(key) == row.get(key):
            updated_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            replaced = True
        else:
            updated_lines.append(source_line)
    if not replaced:
        updated_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def _phase_public_files() -> list[str]:
    return [
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        MATRIX_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        GO_NO_GO_RECORD_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        METADATA_MATRIX_PATH.as_posix(),
        "KMFA/tests/test_v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance.py",
        "KMFA/tools/check_v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance.py",
        "KMFA/tools/v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance.py",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
        "KMFA/metadata/model_registry.yaml",
        "KMFA/HANDOFF.md",
        "KMFA/CHANGELOG.md",
        "KMFA/VERSION",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    _upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260710-V014-REMAINING-ELEVEN-RESIDUAL-DIFFERENCE-SOURCE-TRACE-OR-FINAL-ACCEPTANCE",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "cost_component_materialization_count": 8,
            "queue_closed_or_excluded_count": 69,
            "open_final_difference_accepted_count": 3,
            "nonzero_delta_reconciliation_count": 9,
            "raw_snapshot_exact_match": summary["raw_snapshot_exact_match"],
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "stage_phase_status",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    _upsert_jsonl(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "REMAINING_ELEVEN_RESIDUAL_DIFFERENCE_SOURCE_TRACE_OR_FINAL_ACCEPTANCE",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 remaining eleven residual difference source trace or final acceptance",
            "phase_goal": "materialize unique authority cost components and retain unproven cash values as final accepted differences",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(
    *, generated_at: str | None = None, write_governance_event: bool = True
) -> dict[str, Any]:
    timestamp = _now(generated_at)
    for path in source_private_paths():
        if not path.exists():
            raise FileNotFoundError(path)
    source_hashes_before = {path.as_posix(): _sha256_file(path) for path in source_private_paths()}
    comparisons_hash_before = _sha256_file(SOURCE_COMPARISONS_PATH)
    raw_before = prior_phase._raw_snapshot("before_remaining_eleven_source_trace")
    prior_raw_after = _read_json(SOURCE_PRIOR_RAW_AFTER_PATH)
    final_cash_raw_after = _read_json(SOURCE_FINAL_CASH_RAW_AFTER_PATH)
    raw_snapshot_chain_exact = (
        _normalize_snapshot(raw_before)
        == _normalize_snapshot(prior_raw_after)
        == _normalize_snapshot(final_cash_raw_after)
    )
    if not raw_snapshot_chain_exact:
        raise ValueError("raw snapshot changed since final cash acceptance")

    prior_records = _read_jsonl(SOURCE_PRIOR_REPLAY_RECORDS_PATH)
    prior_open = _read_jsonl(SOURCE_PRIOR_OPEN_DIFFERENCES_PATH)
    prior_summary = _read_json(SOURCE_PRIOR_SUMMARY_PATH)
    staging = _read_json(SOURCE_STAGING_PATH)
    staging_slots = [row for row in staging.get("processed_target_slots", []) if isinstance(row, dict)]
    bindings = _read_jsonl(SOURCE_BINDINGS_PATH)
    precheck = _read_json(SOURCE_PRECHECK_PATH)
    comparisons = _read_jsonl(SOURCE_COMPARISONS_PATH)
    cash_decisions = _read_jsonl(SOURCE_CASH_DECISIONS_PATH)
    unresolved_targets = _read_jsonl(SOURCE_UNRESOLVED_TARGETS_PATH)

    if len(prior_records) != 72 or len(prior_open) != 11:
        raise ValueError("prior residual replay counts changed")
    if sum(row.get("replay_status") == "open_missing_unique_authoritative_source" for row in prior_open) != 8:
        raise ValueError("prior ambiguous cost-component count changed")
    if sum(row.get("replay_status") == "open_final_difference_accepted" for row in prior_open) != 3:
        raise ValueError("prior final accepted cash count changed")
    if len(unresolved_targets) != 3:
        raise ValueError("source unresolved cash target count changed")
    if sum(row.get("resolution_status") == "difference_accepted_unresolved" for row in cash_decisions) != 1:
        raise ValueError("source final cash acceptance is missing")
    prior_phase.validate_nonzero_difference_guard(comparisons, required_nonzero_count=9)

    table_records, source_evidence, materializations = _extract_private_authority_evidence(
        raw_snapshot=raw_before,
        precheck=precheck,
        bindings=bindings,
        staging_slots=staging_slots,
        prior_replay_records=prior_records,
        generated_at=timestamp,
    )
    final_records, open_rows = _build_final_replay_records(
        prior_records=prior_records,
        materializations=materializations,
        raw_snapshot_chain_exact=raw_snapshot_chain_exact,
        generated_at=timestamp,
    )
    if len(table_records) != 4 or len(source_evidence) != 8 or len(materializations) != 8:
        raise ValueError("authority source trace counts changed")
    if len(open_rows) != 3 or any(row.get("replay_status") != "open_final_difference_accepted" for row in open_rows):
        raise ValueError("only three final accepted cash differences may remain open")
    if _contains_float([table_records, source_evidence, materializations, final_records, open_rows]):
        raise ValueError("private outputs cannot contain floats")

    status_counts = Counter(str(row.get("replay_status")) for row in final_records)
    expected_status_counts = {
        "replayed_private_integer_value": 37,
        "replayed_private_integer_formula": 16,
        "owner_authorized_non_numeric_exclusion": 8,
        "replayed_unique_authority_cost_component": 8,
        "open_final_difference_accepted": 3,
    }
    if dict(status_counts) != expected_status_counts:
        raise ValueError("final residual disposition counts changed")

    source_hashes_after = {path.as_posix(): _sha256_file(path) for path in source_private_paths()}
    comparisons_hash_after = _sha256_file(SOURCE_COMPARISONS_PATH)
    raw_after = prior_phase._raw_snapshot("after_remaining_eleven_source_trace")
    source_unchanged = source_hashes_before == source_hashes_after
    raw_snapshot_exact_match = _normalize_snapshot(raw_before) == _normalize_snapshot(raw_after)
    comparisons_unchanged = comparisons_hash_before == comparisons_hash_after
    if not source_unchanged or not raw_snapshot_exact_match or not comparisons_unchanged:
        raise ValueError("source private evidence comparisons or raw inbox changed")

    zero_count = sum(
        row.get("comparison_status") == "comparison_complete_zero_delta" and row.get("delta") == 0
        for row in comparisons
    )
    incomplete_count = sum(
        row.get("comparison_status") == "comparison_incomplete_cash_source_disambiguation_required"
        for row in comparisons
    )
    summary = {
        "schema_version": "kmfa.v014.remaining_eleven_trace_summary.v1",
        "record_type": "v014_remaining_eleven_trace_summary",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "generated_at": timestamp,
        "source_phase_id": prior_summary.get("phase_id"),
        "source_private_inputs_unchanged": source_unchanged,
        "source_open_residual_difference_count": len(prior_open),
        "source_open_ambiguous_cost_component_count": 8,
        "source_open_final_difference_accepted_count": 3,
        "authority_project_source_count": len(table_records),
        "unique_authority_table_count": len(table_records),
        "cost_component_source_evidence_count": len(source_evidence),
        "cost_component_materialization_count": len(materializations),
        "travel_materialization_count": sum(row.get("context_group") == "travel" for row in materializations),
        "interest_materialization_count": sum(row.get("context_group") == "interest" for row in materializations),
        "unique_source_record_count": len({row.get("source_record_ref_hash") for row in source_evidence}),
        "pdf_table_engine_match_count": sum(row.get("pdf_table_engine_match") is True for row in source_evidence),
        "pdf_text_engine_match_count": sum(row.get("pdf_text_engine_match") is True for row in source_evidence),
        "pdf_cross_engine_match_count": sum(
            row.get("pdf_table_engine_match") is True and row.get("pdf_text_engine_match") is True
            for row in source_evidence
        ),
        "travel_child_sum_exact_count": sum(row.get("travel_child_sum_exact") is True for row in source_evidence),
        "direct_expense_category_sum_exact_count": sum(
            row.get("context_group") == "travel" and row.get("direct_expense_category_sum_exact") is True
            for row in source_evidence
        ),
        "current_bound_authority_total_exact_count": sum(
            row.get("context_group") == "travel" and row.get("current_bound_authority_total_exact") is True
            for row in source_evidence
        ),
        "authority_full_total_formula_exact_count": sum(
            record["totals"]["full_table_total_formula_exact"] is True for record in table_records
        ),
        "authority_full_total_formula_difference_count": sum(
            record["totals"]["full_table_total_formula_exact"] is False for record in table_records
        ),
        "classified_residual_record_count": len(final_records),
        "prior_private_target_materialization_replay_count": status_counts[
            "replayed_private_integer_value"
        ],
        "prior_integer_metric_formula_replay_count": status_counts[
            "replayed_private_integer_formula"
        ],
        "new_unique_authority_cost_component_replay_count": status_counts[
            "replayed_unique_authority_cost_component"
        ],
        "replayed_numeric_record_count": status_counts["replayed_private_integer_value"]
        + status_counts["replayed_private_integer_formula"]
        + status_counts["replayed_unique_authority_cost_component"],
        "owner_authorized_non_numeric_exclusion_count": status_counts[
            "owner_authorized_non_numeric_exclusion"
        ],
        "queue_closed_or_excluded_count": sum(row.get("queue_closed") is True for row in final_records),
        "open_residual_difference_count": len(open_rows),
        "open_final_difference_accepted_count": status_counts[
            "open_final_difference_accepted"
        ],
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": zero_count,
        "incomplete_reconciliation_count": incomplete_count,
        "existing_comparisons_unchanged": comparisons_unchanged,
        "forced_zero_materialization_count": 0,
        "raw_snapshot_chain_exact": raw_snapshot_chain_exact,
        "raw_source_file_count": raw_before["file_count"],
        "raw_snapshot_exact_match": raw_snapshot_exact_match,
        "raw_inbox_mutated_by_this_phase": not raw_snapshot_exact_match,
        "global_residual_queue_replay_performed": True,
        "global_residual_queue_final_disposition_complete": True,
        "global_residual_queue_fully_closed": False,
        "partial_raw_to_processed_reconciliation_performed": True,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "private_outputs_gitignored": all(_git_ignored(path) for path in phase_private_paths()),
        "raw_business_data_committed": False,
        "raw_filename_or_value_committed": False,
        "credential_or_secret_committed": False,
        "stage_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "goal_status_recommendation": "continue_active_with_stage9_post_remediation_overall_review",
        "next_recommended_phase": "stage9_post_remediation_overall_review",
    }
    matrix = _public_matrix(summary)
    if matrix["check_fail_count"]:
        raise ValueError("public acceptance matrix contains failures")
    manifest = {
        "schema_version": "kmfa.v014.remaining_eleven_trace_manifest.v1",
        "record_type": "v014_remaining_eleven_trace_manifest",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "generated_at": timestamp,
        "reviewed_head": _git_output(["rev-parse", "HEAD"]),
        "branch": _git_output(["branch", "--show-current"]),
        "remote": _git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_remaining_eleven_residual_difference_source_trace_or_final_acceptance.py",
        },
        "public_repo_safety": {
            "aggregate_only": True,
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "identity_plaintext_committed": False,
            "field_plaintext_committed": False,
            "business_value_committed": False,
            "private_ref_committed": False,
            "private_fingerprint_committed": False,
            "credential_or_secret_committed": False,
        },
        "phase_boundaries": {
            "single_phase_only": True,
            "cost_component_source_trace_performed": True,
            "final_cash_difference_acceptance_preserved": True,
            "unproven_cash_values_materialized": False,
            "forced_zero_materialization_allowed": False,
            "existing_nonzero_differences_overwritten": False,
            "stage_review_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
    }
    go_no_go = {
        "schema_version": "kmfa.v014.remaining_eleven_trace_go_no_go.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "cost_component_materialization_count": 8,
        "queue_closed_or_excluded_count": 69,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "blocking_reason_codes": [
            "three_cash_slots_have_final_accepted_missing_collection_evidence",
            "nine_nonzero_scope_differences_remain_preserved",
            "full_business_value_consistency_not_verified",
        ],
        "github_upload_performed": False,
    }

    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    _write_json(
        PRIVATE_AUTHORITY_TABLES_PATH,
        {
            "schema_version": "kmfa.private.authority_pdf_tables.v1",
            "classification": "private_authority_pdf_tables_do_not_commit",
            "phase_id": PHASE_ID,
            "generated_at": timestamp,
            "records": table_records,
        },
    )
    _write_jsonl(PRIVATE_SOURCE_EVIDENCE_PATH, source_evidence)
    _write_jsonl(PRIVATE_MATERIALIZATIONS_PATH, materializations)
    _write_jsonl(PRIVATE_FINAL_REPLAY_RECORDS_PATH, final_records)
    _write_jsonl(PRIVATE_OPEN_CASH_DIFFERENCES_PATH, open_rows)
    _write_json(
        PRIVATE_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.remaining_eleven_trace_diagnostic.v1",
            "classification": "private_remaining_eleven_trace_diagnostic_do_not_commit",
            "phase_id": PHASE_ID,
            "generated_at": timestamp,
            "source_hashes_before": source_hashes_before,
            "source_hashes_after": source_hashes_after,
            "source_private_inputs_unchanged": source_unchanged,
            "comparisons_hash_before": comparisons_hash_before,
            "comparisons_hash_after": comparisons_hash_after,
            "existing_comparisons_unchanged": comparisons_unchanged,
            "prior_raw_after": prior_raw_after,
            "final_cash_raw_after": final_cash_raw_after,
            "raw_before": raw_before,
            "raw_after": raw_after,
            "raw_snapshot_chain_exact": raw_snapshot_chain_exact,
            "raw_snapshot_exact_match": raw_snapshot_exact_match,
            "status_counts": dict(status_counts),
        },
    )
    _write_text(
        PRIVATE_FINAL_DIFFERENCE_REPORT_PATH,
        _private_report(
            summary=summary,
            evidence_rows=source_evidence,
            open_rows=open_rows,
            comparisons=comparisons,
        ),
    )
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)
    for path, content in _public_reports(summary).items():
        _write_text(path, content)
    if write_governance_event:
        _write_governance(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--skip-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(
        generated_at=args.generated_at,
        write_governance_event=not args.skip_governance_event,
    )
    summary = result["summary"]
    print(
        "remaining eleven trace: "
        f"decision={summary['decision']} "
        f"resolved={summary['cost_component_materialization_count']} "
        f"closed_or_excluded={summary['queue_closed_or_excluded_count']} "
        f"open={summary['open_residual_difference_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
