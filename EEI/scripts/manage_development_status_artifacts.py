#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = Path("artifacts/development_status_summary_t1213.json")
TRACEABILITY_MATRIX_PATH = Path(
    "artifacts/requirement_function_task_test_traceability_t1213.csv"
)
A183_EVIDENCE_PATH = Path(
    "artifacts/tests/a183/t1213_requirement_function_task_test_traceability.json"
)
A184_EVIDENCE_PATH = Path("artifacts/tests/a184/t1213_development_status_ledger.json")

SPEC_STATUSES = {"DONE", "PARTIAL", "NOT_STARTED", "N/A"}
PROTOTYPE_STATUSES = {"DONE", "PARTIAL", "NOT_STARTED", "N/A"}
IMPLEMENTATION_STATUSES = {"DONE", "PARTIAL", "NOT_STARTED", "N/A"}
VALIDATION_STATUSES = {
    "SPEC_VALIDATED",
    "CATALOG_VALIDATED",
    "VALIDATED",
    "LOCAL_VALIDATED",
    "LOCAL_E2E_VALIDATED",
    "CI_VALIDATED",
    "NOT_VALIDATED",
}


def read_csv(path: str) -> list[dict[str, str]]:
    target = ROOT / path
    if not target.is_file():
        raise AssertionError(f"missing required CSV: {path}")
    with target.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_text(path: Path, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def split_ids(value: str) -> list[str]:
    ids: list[str] = []
    for item in [part.strip() for part in re.split(r"[;,]", value or "") if part.strip()]:
        match = re.fullmatch(r"([A-Z]+)(\d+)-([A-Z]+)(\d+)", item)
        if not match:
            ids.append(item)
            continue
        start_prefix, start_number, end_prefix, end_number = match.groups()
        if start_prefix != end_prefix:
            ids.append(item)
            continue
        width = max(len(start_number), len(end_number))
        start = int(start_number)
        end = int(end_number)
        step = 1 if end >= start else -1
        ids.extend(
            f"{start_prefix}{number:0{width}d}" for number in range(start, end + step, step)
        )
    return ids


def status_counter(rows: list[dict[str, str]], column: str) -> dict[str, int]:
    return dict(sorted(Counter(row[column] for row in rows).items()))


def validate_ledger_rows(ledger: list[dict[str, str]]) -> None:
    seen: set[str] = set()
    for row in ledger:
        item_id = row["item_id"]
        if item_id in seen:
            raise AssertionError(f"duplicate development status item_id: {item_id}")
        seen.add(item_id)
        for column, allowed in [
            ("spec_status", SPEC_STATUSES),
            ("prototype_status", PROTOTYPE_STATUSES),
            ("implementation_status", IMPLEMENTATION_STATUSES),
            ("validation_status", VALIDATION_STATUSES),
        ]:
            if row[column] not in allowed:
                raise AssertionError(f"{item_id} has invalid {column}: {row[column]}")
        for column in ["resolved", "unresolved", "next_action", "source_file"]:
            if not row[column].strip():
                raise AssertionError(f"{item_id} has blank {column}")


def build_traceability_matrix() -> tuple[list[dict[str, str]], dict[str, Any]]:
    functions = read_csv("data/function_catalog.csv")
    tasks = {row["task_id"]: row for row in read_csv("data/task_backlog.csv")}
    acceptance = {row["acceptance_id"]: row for row in read_csv("data/acceptance_matrix.csv")}
    traces = read_csv("data/acceptance_traceability.csv")

    traces_by_function: dict[str, list[dict[str, str]]] = defaultdict(list)
    for trace in traces:
        traces_by_function[trace["requirement_or_function_id"]].append(trace)

    matrix: list[dict[str, str]] = []
    p0_functions_checked = 0
    p0_functions_with_trace = 0
    for function in functions:
        function_id = function["function_id"]
        task_ids = split_ids(function["task_ids"])
        acceptance_ids = split_ids(function["acceptance_ids"])
        trace_rows = traces_by_function.get(function_id, [])
        done_traces = [trace for trace in trace_rows if trace["status"] == "DONE"]
        evidence_paths = sorted(
            {
                evidence.strip()
                for trace in trace_rows
                for evidence in trace["evidence_path"].split(";")
                if evidence.strip()
            }
        )
        test_types = sorted({trace["test_type"] for trace in trace_rows if trace["test_type"]})
        missing_tasks = sorted(task_id for task_id in task_ids if task_id not in tasks)
        missing_acceptance = sorted(
            acceptance_id for acceptance_id in acceptance_ids if acceptance_id not in acceptance
        )
        if function["priority"] == "P0":
            p0_functions_checked += 1
            if trace_rows and evidence_paths and not missing_tasks and not missing_acceptance:
                p0_functions_with_trace += 1
        matrix.append(
            {
                "function_id": function_id,
                "name_zh": function["name_zh"],
                "priority": function["priority"],
                "task_ids": ";".join(task_ids),
                "acceptance_ids": ";".join(acceptance_ids),
                "traceability_rows": str(len(trace_rows)),
                "done_traceability_rows": str(len(done_traces)),
                "test_types": ";".join(test_types),
                "evidence_paths": ";".join(evidence_paths),
                "missing_task_ids": ";".join(missing_tasks),
                "missing_acceptance_ids": ";".join(missing_acceptance),
                "source_doc": function["source_doc"],
            }
        )

    if p0_functions_checked == 0:
        raise AssertionError("no P0 functions found for traceability generation")
    if p0_functions_checked != p0_functions_with_trace:
        raise AssertionError("not every P0 function has task/acceptance/test evidence")
    return matrix, {
        "function_rows": len(functions),
        "traceability_rows": len(traces),
        "p0_functions_checked": p0_functions_checked,
        "p0_functions_with_trace": p0_functions_with_trace,
    }


def render_csv(rows: list[dict[str, str]]) -> str:
    if not rows:
        raise AssertionError("cannot render empty CSV artifact")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def build_summary() -> dict[str, Any]:
    ledger = read_csv("data/development_status_ledger.csv")
    tasks = read_csv("data/task_backlog.csv")
    acceptance = read_csv("data/acceptance_matrix.csv")
    resolved_register = read_csv("data/resolved_unresolved_register.csv")
    validate_ledger_rows(ledger)
    matrix, matrix_summary = build_traceability_matrix()
    lane_counts = {
        "resolved": sum(
            row["validation_status"]
            in {"CI_VALIDATED", "LOCAL_E2E_VALIDATED", "LOCAL_VALIDATED", "VALIDATED"}
            for row in ledger
        ),
        "prototyped": sum(
            row["prototype_status"] == "DONE" and row["implementation_status"] != "DONE"
            for row in ledger
        ),
        "specified": sum(
            row["spec_status"] == "DONE" and row["implementation_status"] == "NOT_STARTED"
            for row in ledger
        ),
        "not_started_tasks": sum(row["status"] == "NOT STARTED" for row in tasks),
        "blocked_tasks": sum(row["status"] == "BLOCKED" for row in tasks),
        "out_of_scope_tasks": sum(
            row["gate"] == "Phase2" or row["priority"] == "P1" for row in tasks
        ),
    }
    return {
        "schema_version": 1,
        "task_id": "T1213",
        "acceptance_ids": ["A183", "A184"],
        "ledger": {
            "rows": len(ledger),
            "spec_status": status_counter(ledger, "spec_status"),
            "prototype_status": status_counter(ledger, "prototype_status"),
            "implementation_status": status_counter(ledger, "implementation_status"),
            "validation_status": status_counter(ledger, "validation_status"),
            "lane_counts": lane_counts,
            "resolved_fields_present": all(row["resolved"].strip() for row in ledger),
            "unresolved_fields_present": all(row["unresolved"].strip() for row in ledger),
        },
        "catalogs": {
            "task_rows": len(tasks),
            "acceptance_rows": len(acceptance),
            "resolved_unresolved_rows": len(resolved_register),
        },
        "traceability": matrix_summary,
        "artifacts": {
            "summary": str(SUMMARY_PATH),
            "traceability_matrix": str(TRACEABILITY_MATRIX_PATH),
            "a183_evidence": str(A183_EVIDENCE_PATH),
            "a184_evidence": str(A184_EVIDENCE_PATH),
        },
        "matrix_preview": matrix[:5],
    }


def build_a183_evidence(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_id": "T1213",
        "acceptance_id": "A183",
        "status": "DONE",
        "evidence_type": "requirement_function_task_test_traceability",
        "p0_functions_checked": summary["traceability"]["p0_functions_checked"],
        "p0_functions_with_trace": summary["traceability"]["p0_functions_with_trace"],
        "artifact": str(TRACEABILITY_MATRIX_PATH),
        "validated_by": [
            "scripts/manage_development_status_artifacts.py validate",
            "make validate-development-status-artifacts",
            "make verify",
        ],
    }


def build_a184_evidence(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_id": "T1213",
        "acceptance_id": "A184",
        "status": "DONE",
        "evidence_type": "development_status_ledger_review",
        "status_columns": [
            "spec_status",
            "prototype_status",
            "implementation_status",
            "validation_status",
        ],
        "ledger": summary["ledger"],
        "validated_by": [
            "scripts/manage_development_status_artifacts.py validate",
            "make validate-development-status-artifacts",
            "make verify",
        ],
    }


def expected_artifacts() -> dict[Path, str]:
    matrix, _ = build_traceability_matrix()
    summary = build_summary()
    return {
        SUMMARY_PATH: json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        TRACEABILITY_MATRIX_PATH: render_csv(matrix),
        A183_EVIDENCE_PATH: json.dumps(build_a183_evidence(summary), ensure_ascii=False, indent=2)
        + "\n",
        A184_EVIDENCE_PATH: json.dumps(build_a184_evidence(summary), ensure_ascii=False, indent=2)
        + "\n",
    }


def generate(_: argparse.Namespace) -> None:
    artifacts = expected_artifacts()
    for path, content in artifacts.items():
        write_text(path, content)
    validate(None)
    print(
        json.dumps(
            {
                "generated": True,
                "artifacts": sorted(str(path) for path in artifacts),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def validate(_: argparse.Namespace | None = None) -> None:
    artifacts = expected_artifacts()
    for path, expected in artifacts.items():
        target = ROOT / path
        if not target.is_file():
            raise AssertionError(f"missing generated artifact: {path}")
        actual = target.read_text(encoding="utf-8")
        if actual != expected:
            raise AssertionError(f"{path} is not synchronized with source catalogs")
    summary = json.loads((ROOT / SUMMARY_PATH).read_text(encoding="utf-8"))
    if summary["ledger"]["rows"] < 30:
        raise AssertionError("development status ledger artifact has too few rows")
    if not summary["ledger"]["resolved_fields_present"]:
        raise AssertionError("development status ledger has missing resolved fields")
    if not summary["ledger"]["unresolved_fields_present"]:
        raise AssertionError("development status ledger has missing unresolved fields")
    if summary["traceability"]["p0_functions_checked"] != summary["traceability"][
        "p0_functions_with_trace"
    ]:
        raise AssertionError("P0 traceability matrix is incomplete")
    print(
        json.dumps(
            {
                "valid": True,
                "ledger_rows": summary["ledger"]["rows"],
                "p0_functions_checked": summary["traceability"]["p0_functions_checked"],
                "artifacts": sorted(str(path) for path in artifacts),
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
    except (AssertionError, csv.Error, json.JSONDecodeError) as exc:
        print(f"Development status artifact validation: FAIL - {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
