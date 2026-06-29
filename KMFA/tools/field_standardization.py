#!/usr/bin/env python3
"""KMFA S04-P2 field standardization utilities.

The module standardizes field names and values only. It does not persist raw
business rows, mutate raw sources, or resolve missing-field quality issues.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.file_import_register import parse_received_at, sha256_bytes


class FieldStandardizationError(ValueError):
    """Raised when a field alias or value cannot be safely standardized."""


class MissingFieldError(FieldStandardizationError):
    """Raised when a required field is blank, null-ish, or absent."""


CANONICAL_FIELDS = (
    "document_date",
    "period_month",
    "company_entity",
    "project_name",
    "counterparty",
    "contract_number",
)

CANONICAL_FIELD_LABELS_ZH = {
    "document_date": "日期",
    "period_month": "期间",
    "company_entity": "公司主体",
    "project_name": "项目名称",
    "counterparty": "客户/对手方",
    "contract_number": "合同编号",
}

FIELD_ALIASES = {
    "document_date": (
        "日期",
        "业务日期",
        "发生日期",
        "单据日期",
        "开票日期",
        "付款日期",
        "收款日期",
        "document_date",
        "date",
    ),
    "period_month": (
        "期间",
        "所属期间",
        "会计期间",
        "年月",
        "月份",
        "period_month",
        "period",
        "month",
    ),
    "company_entity": (
        "公司主体",
        "主体",
        "法人主体",
        "公司",
        "单位",
        "company_entity",
        "entity",
        "company",
    ),
    "project_name": (
        "项目名称",
        "项目",
        "工程名称",
        "项目简称",
        "project_name",
        "project",
    ),
    "counterparty": (
        "客户/对手方",
        "客户",
        "客户名称",
        "对手方",
        "供应商",
        "对方单位",
        "往来单位",
        "counterparty",
        "customer",
        "supplier",
    ),
    "contract_number": (
        "合同编号",
        "合同号",
        "合同编码",
        "合同",
        "contract_number",
        "contract_no",
        "contract_id",
    ),
}

BLANK_MARKERS = {
    "",
    "-",
    "--",
    "---",
    "#",
    "##",
    "###",
    "n/a",
    "na",
    "null",
    "none",
    "无",
    "暂无",
    "不适用",
}

QUALITY_STATUS_MISSING = "field_missing_requires_review"
QUALITY_STATUS_INVALID = "field_invalid_requires_review"
QUALITY_GRADE_FOR_FIELD_ISSUE = "Q1"


def require_text(value: Any, field_name: str) -> str:
    if value is None:
        raise MissingFieldError(f"{field_name} is required")
    if isinstance(value, bool):
        raise FieldStandardizationError(f"{field_name} must not be boolean")
    text = unicodedata.normalize("NFKC", str(value)).strip()
    marker = re.sub(r"\s+", "", text).lower()
    if marker in BLANK_MARKERS:
        raise MissingFieldError(f"{field_name} is required")
    return text


def normalize_header_key(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    return re.sub(r"[\s_\-—–/／\\:：,，.。()（）\[\]【】]+", "", text)


def _build_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for canonical_field, aliases in FIELD_ALIASES.items():
        index[normalize_header_key(canonical_field)] = canonical_field
        for alias in aliases:
            index[normalize_header_key(alias)] = canonical_field
    return index


ALIAS_INDEX = _build_alias_index()


def resolve_field_alias(header: str) -> str:
    key = normalize_header_key(header)
    if not key:
        raise MissingFieldError("field header is required")
    canonical = ALIAS_INDEX.get(key)
    if canonical is None:
        raise FieldStandardizationError(f"unknown field alias: {header!r}")
    return canonical


def standardize_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = require_text(value, "document_date")
    if re.fullmatch(r"\d{8}", text):
        text = f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    else:
        text = (
            text.replace("年", "-")
            .replace("月", "-")
            .replace("日", "")
            .replace("号", "")
            .replace("/", "-")
            .replace(".", "-")
        )
    text = re.sub(r"-+", "-", text).strip("-")
    match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if not match:
        raise FieldStandardizationError(f"invalid document_date: {value!r}")
    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError as exc:
        raise FieldStandardizationError(f"invalid document_date: {value!r}") from exc


def standardize_period(value: Any) -> str:
    if isinstance(value, datetime):
        return f"{value.year:04d}-{value.month:02d}"
    if isinstance(value, date):
        return f"{value.year:04d}-{value.month:02d}"

    text = require_text(value, "period_month")
    if re.fullmatch(r"\d{6}", text):
        text = f"{text[0:4]}-{text[4:6]}"
    else:
        text = (
            text.replace("年", "-")
            .replace("月", "-")
            .replace("日", "")
            .replace("号", "")
            .replace("/", "-")
            .replace(".", "-")
        )
    text = re.sub(r"-+", "-", text).strip("-")
    date_match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if date_match:
        return standardize_date(text)[:7]

    match = re.fullmatch(r"(\d{4})-(\d{1,2})", text)
    if not match:
        raise FieldStandardizationError(f"invalid period_month: {value!r}")
    year, month = (int(part) for part in match.groups())
    if month < 1 or month > 12:
        raise FieldStandardizationError(f"invalid period_month: {value!r}")
    return f"{year:04d}-{month:02d}"


def standardize_identity_text(value: Any, field_name: str) -> str:
    text = require_text(value, field_name)
    return re.sub(r"\s+", " ", text).strip()


def standardize_contract_number(value: Any) -> str:
    text = require_text(value, "contract_number")
    text = text.replace("—", "-").replace("–", "-").replace("－", "-")
    return re.sub(r"\s+", "", text).upper()


def standardize_field_value(canonical_field: str, value: Any) -> str:
    if canonical_field == "document_date":
        return standardize_date(value)
    if canonical_field == "period_month":
        return standardize_period(value)
    if canonical_field in {"company_entity", "project_name", "counterparty"}:
        return standardize_identity_text(value, canonical_field)
    if canonical_field == "contract_number":
        return standardize_contract_number(value)
    raise FieldStandardizationError(f"unsupported canonical field: {canonical_field!r}")


def build_mapping_record(
    *,
    source_id: str,
    mapping_version: str,
    source_field_alias: str,
    evidence_ref: str,
) -> dict[str, Any]:
    canonical_field = resolve_field_alias(source_field_alias)
    alias_key = normalize_header_key(source_field_alias)
    return {
        "record_type": "field_mapping_rule",
        "schema_version": "kmfa.field_mapping_rule.v1",
        "stage_phase": "S04-P2",
        "source_id": require_text(source_id, "source_id"),
        "mapping_version": require_text(mapping_version, "mapping_version"),
        "canonical_field": canonical_field,
        "canonical_field_label_zh": CANONICAL_FIELD_LABELS_ZH[canonical_field],
        "source_field_alias_key": alias_key,
        "source_field_alias_hash": "sha256:" + sha256_bytes(alias_key.encode("utf-8")),
        "status": "active",
        "target_layer": "metadata",
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "evidence_ref": require_text(evidence_ref, "evidence_ref"),
    }


def build_field_quality_status(
    *,
    source_id: str,
    import_run_id: str,
    mapping_version: str,
    canonical_field: str,
    issue_type: str,
    event_time: str | None,
    evidence_ref: str,
) -> dict[str, Any]:
    if canonical_field not in CANONICAL_FIELDS:
        raise FieldStandardizationError(f"unsupported canonical field: {canonical_field!r}")
    if issue_type not in {"missing_required_field", "invalid_field_value"}:
        raise FieldStandardizationError(f"unsupported field quality issue: {issue_type!r}")
    timestamp = parse_received_at(event_time)
    source_id_value = require_text(source_id, "source_id")
    import_run_id_value = require_text(import_run_id, "import_run_id")
    mapping_version_value = require_text(mapping_version, "mapping_version")
    suffix = sha256_bytes(
        f"{source_id_value}|{import_run_id_value}|{mapping_version_value}|{canonical_field}|{issue_type}".encode(
            "utf-8"
        )
    )[:12]
    status = QUALITY_STATUS_MISSING if issue_type == "missing_required_field" else QUALITY_STATUS_INVALID
    return {
        "record_type": "field_quality_status",
        "schema_version": "kmfa.field_quality_status.v1",
        "stage_phase": "S04-P2",
        "event_id": f"FQS-{timestamp.strftime('%Y%m%d-%H%M%S')}-{suffix}",
        "source_id": source_id_value,
        "import_run_id": import_run_id_value,
        "mapping_version": mapping_version_value,
        "canonical_field": canonical_field,
        "canonical_field_label_zh": CANONICAL_FIELD_LABELS_ZH[canonical_field],
        "issue_type": issue_type,
        "status": status,
        "quality_grade": QUALITY_GRADE_FOR_FIELD_ISSUE,
        "target_layer": "metadata",
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "field_skipped_silently": False,
        "evidence_ref": require_text(evidence_ref, "evidence_ref"),
        "event_time": timestamp.isoformat(),
    }


def standardize_record(
    row: dict[str, Any],
    *,
    source_id: str,
    import_run_id: str,
    mapping_version: str,
    evidence_ref: str,
    event_time: str | None = None,
    required_fields: tuple[str, ...] = CANONICAL_FIELDS,
) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise FieldStandardizationError("row must be a JSON object")
    standardized: dict[str, str] = {}
    quality_statuses: list[dict[str, Any]] = []

    for source_field, value in row.items():
        try:
            canonical_field = resolve_field_alias(str(source_field))
        except FieldStandardizationError:
            continue
        try:
            standardized[canonical_field] = standardize_field_value(canonical_field, value)
        except MissingFieldError:
            quality_statuses.append(
                build_field_quality_status(
                    source_id=source_id,
                    import_run_id=import_run_id,
                    mapping_version=mapping_version,
                    canonical_field=canonical_field,
                    issue_type="missing_required_field",
                    event_time=event_time,
                    evidence_ref=evidence_ref,
                )
            )
        except FieldStandardizationError:
            quality_statuses.append(
                build_field_quality_status(
                    source_id=source_id,
                    import_run_id=import_run_id,
                    mapping_version=mapping_version,
                    canonical_field=canonical_field,
                    issue_type="invalid_field_value",
                    event_time=event_time,
                    evidence_ref=evidence_ref,
                )
            )

    for canonical_field in required_fields:
        if canonical_field not in standardized and not any(
            status.get("canonical_field") == canonical_field for status in quality_statuses
        ):
            quality_statuses.append(
                build_field_quality_status(
                    source_id=source_id,
                    import_run_id=import_run_id,
                    mapping_version=mapping_version,
                    canonical_field=canonical_field,
                    issue_type="missing_required_field",
                    event_time=event_time,
                    evidence_ref=evidence_ref,
                )
            )

    return {
        "record_type": "field_standardization_result",
        "schema_version": "kmfa.field_standardization.v1",
        "stage_phase": "S04-P2",
        "source_id": require_text(source_id, "source_id"),
        "import_run_id": require_text(import_run_id, "import_run_id"),
        "mapping_version": require_text(mapping_version, "mapping_version"),
        "standardized_fields": standardized,
        "quality_statuses": quality_statuses,
        "quality_passed": not quality_statuses,
        "target_layer": "metadata",
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "evidence_ref": require_text(evidence_ref, "evidence_ref"),
    }


def append_quality_statuses(path: str | Path, statuses: list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        for status in statuses:
            if status.get("record_type") != "field_quality_status":
                raise FieldStandardizationError("only field_quality_status records can be appended")
            if status.get("raw_layer_write_allowed") is not False:
                raise FieldStandardizationError("field quality status must not write raw layer")
            if status.get("field_skipped_silently") is not False:
                raise FieldStandardizationError("field quality status must prove field_skipped_silently=false")
            handle.write(json.dumps(status, ensure_ascii=False, sort_keys=True) + "\n")


def load_json_object(value: str) -> dict[str, Any]:
    data = json.loads(value)
    if not isinstance(data, dict):
        raise FieldStandardizationError("JSON input must be an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Standardize KMFA S04-P2 field aliases and values.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    alias_parser = subparsers.add_parser("map-alias")
    alias_parser.add_argument("--source-id", required=True)
    alias_parser.add_argument("--mapping-version", required=True)
    alias_parser.add_argument("--source-field-alias", required=True)
    alias_parser.add_argument("--evidence-ref", required=True)

    record_parser = subparsers.add_parser("standardize-row")
    record_parser.add_argument("--row-json", required=True)
    record_parser.add_argument("--source-id", required=True)
    record_parser.add_argument("--import-run-id", required=True)
    record_parser.add_argument("--mapping-version", required=True)
    record_parser.add_argument("--evidence-ref", required=True)
    record_parser.add_argument("--event-time", default=None)

    args = parser.parse_args(argv)
    if args.command == "map-alias":
        output = build_mapping_record(
            source_id=args.source_id,
            mapping_version=args.mapping_version,
            source_field_alias=args.source_field_alias,
            evidence_ref=args.evidence_ref,
        )
    else:
        output = standardize_record(
            load_json_object(args.row_json),
            source_id=args.source_id,
            import_run_id=args.import_run_id,
            mapping_version=args.mapping_version,
            evidence_ref=args.evidence_ref,
            event_time=args.event_time,
        )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
