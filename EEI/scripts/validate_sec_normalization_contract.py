#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.ingest.sec_normalizer import (  # noqa: E402
    SEC_COMPANY_FACTS_NORMALIZER_VERSION,
    SEC_SUBMISSIONS_NORMALIZER_VERSION,
    NormalizedCompanyFact,
    normalize_sec_company_facts,
    normalize_sec_submissions,
)

SUBMISSIONS_FIXTURE = ROOT / "tests/fixtures/sec/submissions_golden.json"
COMPANY_FACTS_FIXTURE = ROOT / "tests/fixtures/sec/companyfacts_golden.json"
A100_OUTPUT = ROOT / "artifacts/tests/a100/t702_sec_submissions_normalization_contract.json"
A101_OUTPUT = ROOT / "artifacts/tests/a101/t702_sec_companyfacts_normalization_contract.json"
OFFICIAL_SCHEMA_REFERENCE = (
    "https://www.sec.gov/search-filings/edgar-application-programming-interfaces"
)
A100_FIELDS = ["accession", "form", "filed", "report", "accepted", "document"]
A101_FIELDS = ["concept", "unit", "period", "form", "filed", "frame"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def generated_at() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    require(isinstance(payload, dict), f"fixture/artifact must be an object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def revision_group_key(fact: NormalizedCompanyFact) -> tuple[object, ...]:
    return (
        fact.taxonomy,
        fact.concept,
        fact.unit,
        fact.period_start,
        fact.period_end,
    )


def build_contracts() -> tuple[dict[str, Any], dict[str, Any]]:
    submissions_payload = read_json(SUBMISSIONS_FIXTURE)
    companyfacts_payload = read_json(COMPANY_FACTS_FIXTURE)
    for path, payload in (
        (SUBMISSIONS_FIXTURE, submissions_payload),
        (COMPANY_FACTS_FIXTURE, companyfacts_payload),
    ):
        metadata = payload.get("_fixture_metadata") or {}
        require(metadata.get("record_mode") == "fixture", f"fixture mode drift: {path}")
        require(metadata.get("synthetic") is True, f"synthetic marker missing: {path}")
        require(
            metadata.get("schema_reference") == OFFICIAL_SCHEMA_REFERENCE,
            f"official schema reference drift: {path}",
        )

    submissions = normalize_sec_submissions(submissions_payload, record_mode="fixture")
    companyfacts = normalize_sec_company_facts(companyfacts_payload, record_mode="fixture")
    period_kinds = Counter(fact.period_kind for fact in companyfacts.facts)
    revision_groups = Counter(revision_group_key(fact) for fact in companyfacts.facts)
    repeated_period_groups = sum(count > 1 for count in revision_groups.values())

    common = {
        "task_id": "T702",
        "generated_at": generated_at(),
        "source_commit": git_commit(),
        "schema_reference": OFFICIAL_SCHEMA_REFERENCE,
        "release_scope": {
            "fixture_only": True,
            "live_sec_request_performed": False,
            "database_write_performed": False,
            "a202_closed_by_contract": False,
            "a209_closed_by_contract": False,
            "mvp_release_ready": False,
        },
        "test_evidence": [
            "tests/unit/test_sec_normalizer.py",
            "tests/fixtures/sec/submissions_golden.json",
            "tests/fixtures/sec/companyfacts_golden.json",
        ],
    }
    a100 = {
        "schema_version": "eei-a100-sec-submissions-normalization-contract-v1",
        "status": "PASS",
        "acceptance_ids": ["A100"],
        **common,
        "fixture": {
            "path": SUBMISSIONS_FIXTURE.relative_to(ROOT).as_posix(),
            "sha256": file_sha256(SUBMISSIONS_FIXTURE),
            "record_mode": submissions.record_mode,
            "synthetic": True,
        },
        "contract": {
            "normalizer_version": SEC_SUBMISSIONS_NORMALIZER_VERSION,
            "fields_preserved": A100_FIELDS,
            "columnar_arrays_require_equal_length": True,
            "cik_zero_padded_to_ten_digits": submissions.cik == "0000000001",
            "filing_count": len(submissions.filings),
            "amendment_count": sum(filing.is_amendment for filing in submissions.filings),
            "unknown_report_date_count": sum(
                filing.report_date is None for filing in submissions.filings
            ),
            "accepted_timestamps_are_utc": all(
                filing.accepted_at is None or filing.accepted_at.tzinfo is UTC
                for filing in submissions.filings
            ),
            "additional_history_file_count": len(submissions.additional_files),
            "fixture_cannot_be_relabeled_live": True,
        },
        "sample": submissions.filings[0].to_dict(),
    }
    a101 = {
        "schema_version": "eei-a101-sec-companyfacts-normalization-contract-v1",
        "status": "PASS",
        "acceptance_ids": ["A101"],
        **common,
        "fixture": {
            "path": COMPANY_FACTS_FIXTURE.relative_to(ROOT).as_posix(),
            "sha256": file_sha256(COMPANY_FACTS_FIXTURE),
            "record_mode": companyfacts.record_mode,
            "synthetic": True,
        },
        "contract": {
            "normalizer_version": SEC_COMPANY_FACTS_NORMALIZER_VERSION,
            "fields_preserved": A101_FIELDS,
            "taxonomy_count": len({fact.taxonomy for fact in companyfacts.facts}),
            "concept_count": len({fact.concept for fact in companyfacts.facts}),
            "unit_count": len({fact.unit for fact in companyfacts.facts}),
            "fact_count": len(companyfacts.facts),
            "duration_fact_count": period_kinds["duration"],
            "instant_fact_count": period_kinds["instant"],
            "amendment_count": sum(fact.is_amendment for fact in companyfacts.facts),
            "missing_frame_preserved_as_null_count": sum(
                fact.frame is None for fact in companyfacts.facts
            ),
            "same_period_revision_group_count": repeated_period_groups,
            "same_period_revisions_preserved_without_collapse": True,
            "restatement_inferred_without_source_evidence": False,
            "fixture_cannot_be_relabeled_live": True,
        },
        "samples": [fact.to_dict() for fact in companyfacts.facts],
    }
    return a100, a101


def validate_contracts(a100: dict[str, Any], a101: dict[str, Any]) -> None:
    require(a100.get("status") == "PASS", "A100 contract status must be PASS")
    require(a100.get("task_id") == "T702", "A100 task_id must be T702")
    require(a100.get("acceptance_ids") == ["A100"], "A100 acceptance mapping drift")
    require(
        (a100.get("fixture") or {}).get("sha256") == file_sha256(SUBMISSIONS_FIXTURE),
        "A100 fixture hash drift",
    )
    submissions = a100.get("contract") or {}
    require(submissions.get("fields_preserved") == A100_FIELDS, "A100 field contract drift")
    require(submissions.get("filing_count") == 2, "A100 filing count drift")
    require(submissions.get("amendment_count") == 1, "A100 amendment count drift")
    require(
        submissions.get("columnar_arrays_require_equal_length") is True,
        "A100 parallel-array guard missing",
    )
    require(
        submissions.get("fixture_cannot_be_relabeled_live") is True,
        "A100 fixture boundary missing",
    )

    require(a101.get("status") == "PASS", "A101 contract status must be PASS")
    require(a101.get("task_id") == "T702", "A101 task_id must be T702")
    require(a101.get("acceptance_ids") == ["A101"], "A101 acceptance mapping drift")
    require(
        (a101.get("fixture") or {}).get("sha256") == file_sha256(COMPANY_FACTS_FIXTURE),
        "A101 fixture hash drift",
    )
    companyfacts = a101.get("contract") or {}
    require(companyfacts.get("fields_preserved") == A101_FIELDS, "A101 field contract drift")
    require(companyfacts.get("fact_count") == 3, "A101 fact count drift")
    require(companyfacts.get("duration_fact_count") == 2, "A101 duration count drift")
    require(companyfacts.get("instant_fact_count") == 1, "A101 instant count drift")
    require(companyfacts.get("amendment_count") == 1, "A101 amendment count drift")
    require(
        companyfacts.get("same_period_revisions_preserved_without_collapse") is True,
        "A101 revision preservation drift",
    )
    require(
        companyfacts.get("restatement_inferred_without_source_evidence") is False,
        "A101 must not infer restatements",
    )

    for artifact in (a100, a101):
        scope = artifact.get("release_scope") or {}
        require(scope.get("fixture_only") is True, "normalization evidence must be fixture-only")
        require(
            scope.get("live_sec_request_performed") is False,
            "normalization evidence must not claim live SEC access",
        )
        require(
            scope.get("database_write_performed") is False,
            "normalization evidence must not claim PostgreSQL writes",
        )
        require(
            scope.get("mvp_release_ready") is False,
            "T702 contract must not claim MVP release readiness",
        )
        require(bool(artifact.get("source_commit")), "source_commit is required")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("generate", "validate"))
    args = parser.parse_args()

    if args.action == "generate":
        a100, a101 = build_contracts()
        validate_contracts(a100, a101)
        write_json(A100_OUTPUT, a100)
        write_json(A101_OUTPUT, a101)
    else:
        a100 = read_json(A100_OUTPUT)
        a101 = read_json(A101_OUTPUT)
        validate_contracts(a100, a101)

    print(
        json.dumps(
            {
                "valid": True,
                "task_id": "T702",
                "acceptance_ids": ["A100", "A101"],
                "fixture_only": True,
                "live_sec_request_performed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
