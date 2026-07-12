from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Literal, cast

from .sec_client import normalize_cik

RecordMode = Literal["fixture", "curated_official_fixture", "dry_run", "live"]

SEC_SUBMISSIONS_NORMALIZER_VERSION = "sec-submissions-normalizer-v1"
SEC_COMPANY_FACTS_NORMALIZER_VERSION = "sec-companyfacts-normalizer-v1"
SUPPORTED_RECORD_MODES = frozenset({"fixture", "curated_official_fixture", "dry_run", "live"})
ACCESSION_NUMBER_PATTERN = re.compile(r"^\d{10}-\d{2}-\d{6}$")


class SecNormalizationError(ValueError):
    """Raised when an SEC payload cannot be normalized without losing semantics."""


def validate_record_mode(value: str) -> RecordMode:
    if value not in SUPPORTED_RECORD_MODES:
        raise SecNormalizationError(
            f"record_mode must be one of {sorted(SUPPORTED_RECORD_MODES)}"
        )
    return cast(RecordMode, value)


def validate_payload_mode(
    payload: Mapping[str, Any],
    *,
    record_mode: RecordMode,
    path: str,
) -> None:
    metadata_raw = payload.get("_fixture_metadata")
    if metadata_raw is None:
        return
    metadata = require_mapping(metadata_raw, f"{path}._fixture_metadata")
    declared_mode = metadata.get("record_mode")
    if declared_mode is not None and declared_mode != record_mode:
        raise SecNormalizationError(
            f"{path} fixture record_mode {declared_mode!r} cannot be relabeled as {record_mode!r}"
        )
    if metadata.get("synthetic") is True and record_mode != "fixture":
        raise SecNormalizationError(f"{path} synthetic fixture cannot be normalized as live data")


def require_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SecNormalizationError(f"{path} must be an object")
    return value


def require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise SecNormalizationError(f"{path} must be an array")
    return value


def require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SecNormalizationError(f"{path} must be a non-empty string")
    return value.strip()


def optional_string(value: Any, path: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise SecNormalizationError(f"{path} must be a string or null")
    return value.strip() or None


def parse_date(value: Any, path: str, *, required: bool) -> date | None:
    normalized = optional_string(value, path)
    if normalized is None:
        if required:
            raise SecNormalizationError(f"{path} is required")
        return None
    try:
        return date.fromisoformat(normalized)
    except ValueError as exc:
        raise SecNormalizationError(f"{path} must use YYYY-MM-DD") from exc


def parse_datetime(value: Any, path: str, *, required: bool) -> datetime | None:
    normalized = optional_string(value, path)
    if normalized is None:
        if required:
            raise SecNormalizationError(f"{path} is required")
        return None
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SecNormalizationError(f"{path} must use ISO-8601") from exc
    if parsed.tzinfo is None:
        raise SecNormalizationError(f"{path} must include a timezone")
    return parsed.astimezone(UTC)


def validate_accession_number(value: Any, path: str) -> str:
    accession_number = require_string(value, path)
    if not ACCESSION_NUMBER_PATTERN.fullmatch(accession_number):
        raise SecNormalizationError(f"{path} must use ##########-##-###### format")
    return accession_number


def form_semantics(form: str) -> tuple[str, bool]:
    normalized = form.upper()
    is_amendment = normalized.endswith("/A")
    base_form = form[:-2] if is_amendment else form
    return base_form, is_amendment


@dataclass(frozen=True)
class NormalizedSubmissionFileReference:
    name: str
    filing_from: date
    filing_to: date

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "filing_from": self.filing_from.isoformat(),
            "filing_to": self.filing_to.isoformat(),
        }


@dataclass(frozen=True)
class NormalizedSecFiling:
    record_mode: RecordMode
    cik: str
    entity_name: str
    accession_number: str
    form: str
    base_form: str
    is_amendment: bool
    filed_date: date
    report_date: date | None
    accepted_at: datetime | None
    primary_document: str | None
    primary_document_description: str | None
    source_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_mode": self.record_mode,
            "cik": self.cik,
            "entity_name": self.entity_name,
            "accession_number": self.accession_number,
            "form": self.form,
            "base_form": self.base_form,
            "is_amendment": self.is_amendment,
            "filed_date": self.filed_date.isoformat(),
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "accepted_at": (
                self.accepted_at.isoformat().replace("+00:00", "Z")
                if self.accepted_at
                else None
            ),
            "primary_document": self.primary_document,
            "primary_document_description": self.primary_document_description,
            "source_index": self.source_index,
        }


@dataclass(frozen=True)
class NormalizedSecSubmissions:
    schema_version: str
    record_mode: RecordMode
    cik: str
    entity_name: str
    filings: tuple[NormalizedSecFiling, ...]
    additional_files: tuple[NormalizedSubmissionFileReference, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_mode": self.record_mode,
            "cik": self.cik,
            "entity_name": self.entity_name,
            "filings": [filing.to_dict() for filing in self.filings],
            "additional_files": [item.to_dict() for item in self.additional_files],
        }


@dataclass(frozen=True)
class NormalizedCompanyFact:
    record_mode: RecordMode
    cik: str
    entity_name: str
    taxonomy: str
    concept: str
    label: str
    description: str
    unit: str
    value: str | int | float | bool | None
    period_start: date | None
    period_end: date
    period_kind: Literal["duration", "instant"]
    accession_number: str
    fiscal_year: int | None
    fiscal_period: str | None
    form: str
    base_form: str
    is_amendment: bool
    filed_date: date
    frame: str | None
    source_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_mode": self.record_mode,
            "cik": self.cik,
            "entity_name": self.entity_name,
            "taxonomy": self.taxonomy,
            "concept": self.concept,
            "label": self.label,
            "description": self.description,
            "unit": self.unit,
            "value": self.value,
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat(),
                "kind": self.period_kind,
            },
            "accession_number": self.accession_number,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "form": self.form,
            "base_form": self.base_form,
            "is_amendment": self.is_amendment,
            "filed_date": self.filed_date.isoformat(),
            "frame": self.frame,
            "source_index": self.source_index,
        }


@dataclass(frozen=True)
class NormalizedSecCompanyFacts:
    schema_version: str
    record_mode: RecordMode
    cik: str
    entity_name: str
    facts: tuple[NormalizedCompanyFact, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_mode": self.record_mode,
            "cik": self.cik,
            "entity_name": self.entity_name,
            "facts": [fact.to_dict() for fact in self.facts],
        }


def normalize_sec_submissions(
    payload: Mapping[str, Any],
    *,
    record_mode: str,
) -> NormalizedSecSubmissions:
    mode = validate_record_mode(record_mode)
    root = require_mapping(payload, "submissions")
    validate_payload_mode(root, record_mode=mode, path="submissions")
    cik = normalize_cik(require_string(root.get("cik"), "submissions.cik"))
    entity_name = require_string(root.get("name"), "submissions.name")
    filings = require_mapping(root.get("filings"), "submissions.filings")
    recent = require_mapping(filings.get("recent"), "submissions.filings.recent")

    required_columns = {
        name: require_list(recent.get(name), f"submissions.filings.recent.{name}")
        for name in (
            "accessionNumber",
            "form",
            "filingDate",
            "reportDate",
            "acceptanceDateTime",
            "primaryDocument",
        )
    }
    row_count = len(required_columns["accessionNumber"])
    for name, values in required_columns.items():
        if len(values) != row_count:
            raise SecNormalizationError(
                f"submissions.filings.recent.{name} length must equal accessionNumber length"
            )

    descriptions_raw = recent.get("primaryDocDescription")
    if descriptions_raw is None:
        descriptions: list[Any] = [None] * row_count
    else:
        descriptions = require_list(
            descriptions_raw,
            "submissions.filings.recent.primaryDocDescription",
        )
        if len(descriptions) != row_count:
            raise SecNormalizationError(
                "submissions.filings.recent.primaryDocDescription length must equal "
                "accessionNumber length"
            )

    normalized_filings: list[NormalizedSecFiling] = []
    for index in range(row_count):
        path = f"submissions.filings.recent[{index}]"
        form = require_string(required_columns["form"][index], f"{path}.form")
        base_form, is_amendment = form_semantics(form)
        filed_date = parse_date(
            required_columns["filingDate"][index],
            f"{path}.filingDate",
            required=True,
        )
        assert filed_date is not None
        normalized_filings.append(
            NormalizedSecFiling(
                record_mode=mode,
                cik=cik,
                entity_name=entity_name,
                accession_number=validate_accession_number(
                    required_columns["accessionNumber"][index],
                    f"{path}.accessionNumber",
                ),
                form=form,
                base_form=base_form,
                is_amendment=is_amendment,
                filed_date=filed_date,
                report_date=parse_date(
                    required_columns["reportDate"][index],
                    f"{path}.reportDate",
                    required=False,
                ),
                accepted_at=parse_datetime(
                    required_columns["acceptanceDateTime"][index],
                    f"{path}.acceptanceDateTime",
                    required=False,
                ),
                primary_document=optional_string(
                    required_columns["primaryDocument"][index],
                    f"{path}.primaryDocument",
                ),
                primary_document_description=optional_string(
                    descriptions[index],
                    f"{path}.primaryDocDescription",
                ),
                source_index=index,
            )
        )

    additional_files_raw = filings.get("files", [])
    additional_files: list[NormalizedSubmissionFileReference] = []
    for index, item in enumerate(require_list(additional_files_raw, "submissions.filings.files")):
        path = f"submissions.filings.files[{index}]"
        file_row = require_mapping(item, path)
        filing_from = parse_date(file_row.get("filingFrom"), f"{path}.filingFrom", required=True)
        filing_to = parse_date(file_row.get("filingTo"), f"{path}.filingTo", required=True)
        assert filing_from is not None and filing_to is not None
        if filing_from > filing_to:
            raise SecNormalizationError(f"{path}.filingFrom must be <= filingTo")
        additional_files.append(
            NormalizedSubmissionFileReference(
                name=require_string(file_row.get("name"), f"{path}.name"),
                filing_from=filing_from,
                filing_to=filing_to,
            )
        )

    return NormalizedSecSubmissions(
        schema_version=SEC_SUBMISSIONS_NORMALIZER_VERSION,
        record_mode=mode,
        cik=cik,
        entity_name=entity_name,
        filings=tuple(normalized_filings),
        additional_files=tuple(additional_files),
    )


def normalize_sec_company_facts(
    payload: Mapping[str, Any],
    *,
    record_mode: str,
) -> NormalizedSecCompanyFacts:
    mode = validate_record_mode(record_mode)
    root = require_mapping(payload, "companyfacts")
    validate_payload_mode(root, record_mode=mode, path="companyfacts")
    cik = normalize_cik(require_string(str(root.get("cik", "")), "companyfacts.cik"))
    entity_name = require_string(root.get("entityName"), "companyfacts.entityName")
    taxonomies = require_mapping(root.get("facts"), "companyfacts.facts")
    normalized_facts: list[NormalizedCompanyFact] = []

    for taxonomy in sorted(taxonomies):
        concepts = require_mapping(taxonomies[taxonomy], f"companyfacts.facts.{taxonomy}")
        for concept in sorted(concepts):
            path = f"companyfacts.facts.{taxonomy}.{concept}"
            concept_payload = require_mapping(concepts[concept], path)
            label = require_string(concept_payload.get("label"), f"{path}.label")
            description = require_string(
                concept_payload.get("description"),
                f"{path}.description",
            )
            units = require_mapping(concept_payload.get("units"), f"{path}.units")
            for unit in sorted(units):
                entries = require_list(units[unit], f"{path}.units.{unit}")
                for source_index, item in enumerate(entries):
                    fact_path = f"{path}.units.{unit}[{source_index}]"
                    fact = require_mapping(item, fact_path)
                    if "val" not in fact:
                        raise SecNormalizationError(f"{fact_path}.val is required")
                    value = fact["val"]
                    if isinstance(value, list | Mapping):
                        raise SecNormalizationError(f"{fact_path}.val must be a JSON scalar")
                    form = require_string(fact.get("form"), f"{fact_path}.form")
                    base_form, is_amendment = form_semantics(form)
                    period_start = parse_date(
                        fact.get("start"),
                        f"{fact_path}.start",
                        required=False,
                    )
                    period_end = parse_date(
                        fact.get("end"),
                        f"{fact_path}.end",
                        required=True,
                    )
                    filed_date = parse_date(
                        fact.get("filed"),
                        f"{fact_path}.filed",
                        required=True,
                    )
                    assert period_end is not None and filed_date is not None
                    if period_start is not None and period_start > period_end:
                        raise SecNormalizationError(f"{fact_path}.start must be <= end")

                    fiscal_year_raw = fact.get("fy")
                    if fiscal_year_raw is not None and (
                        not isinstance(fiscal_year_raw, int)
                        or isinstance(fiscal_year_raw, bool)
                    ):
                        raise SecNormalizationError(f"{fact_path}.fy must be an integer or null")
                    normalized_facts.append(
                        NormalizedCompanyFact(
                            record_mode=mode,
                            cik=cik,
                            entity_name=entity_name,
                            taxonomy=require_string(taxonomy, f"{path}.taxonomy"),
                            concept=require_string(concept, f"{path}.concept"),
                            label=label,
                            description=description,
                            unit=require_string(unit, f"{fact_path}.unit"),
                            value=value,
                            period_start=period_start,
                            period_end=period_end,
                            period_kind="duration" if period_start else "instant",
                            accession_number=validate_accession_number(
                                fact.get("accn"),
                                f"{fact_path}.accn",
                            ),
                            fiscal_year=fiscal_year_raw,
                            fiscal_period=optional_string(
                                fact.get("fp"),
                                f"{fact_path}.fp",
                            ),
                            form=form,
                            base_form=base_form,
                            is_amendment=is_amendment,
                            filed_date=filed_date,
                            frame=optional_string(
                                fact.get("frame"),
                                f"{fact_path}.frame",
                            ),
                            source_index=source_index,
                        )
                    )

    return NormalizedSecCompanyFacts(
        schema_version=SEC_COMPANY_FACTS_NORMALIZER_VERSION,
        record_mode=mode,
        cik=cik,
        entity_name=entity_name,
        facts=tuple(normalized_facts),
    )
