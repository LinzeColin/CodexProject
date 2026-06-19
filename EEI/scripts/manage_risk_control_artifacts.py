#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = Path("artifacts/risk_control_summary_t1214.json")
MAPPING_PATH = Path("artifacts/risk_control_mapping_t1214.csv")
A185_EVIDENCE_PATH = Path("artifacts/tests/a185/t1214_high_risk_traceability.json")

HIGH_SEVERITIES = {"high", "critical"}


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
    for item in [part.strip() for part in re.split(r"[,;/]", value or "") if part.strip()]:
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


def unique(rows: list[dict[str, str]], key: str, label: str) -> None:
    values = [row[key] for row in rows]
    if any(not value for value in values):
        raise AssertionError(f"{label} has blank {key}")
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if duplicates:
        raise AssertionError(f"{label} duplicate {key}: {duplicates}")


def render_csv(rows: list[dict[str, str]]) -> str:
    if not rows:
        raise AssertionError("cannot render empty CSV artifact")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def build_mapping() -> tuple[list[dict[str, str]], dict[str, Any]]:
    risks = read_csv("data/risk_register.csv")
    traces = read_csv("data/risk_control_traceability.csv")
    functions = {row["function_id"] for row in read_csv("data/function_catalog.csv")}
    tasks = {row["task_id"] for row in read_csv("data/task_backlog.csv")}
    acceptance = {row["acceptance_id"] for row in read_csv("data/acceptance_matrix.csv")}
    gates = {row["gate_id"] for row in read_csv("data/release_gate_catalog.csv")}

    unique(risks, "risk_id", "risk_register")
    unique(traces, "risk_id", "risk_control_traceability")
    risks_by_id = {row["risk_id"]: row for row in risks}
    traces_by_id = {row["risk_id"]: row for row in traces}
    if set(risks_by_id) != set(traces_by_id):
        raise AssertionError("risk register and traceability risk IDs differ")

    rows: list[dict[str, str]] = []
    high_or_critical_count = 0
    for risk_id in sorted(risks_by_id):
        risk = risks_by_id[risk_id]
        trace = traces_by_id[risk_id]
        severity = trace["severity"].lower()
        related_functions = split_ids(trace["related_function_ids"])
        task_ids = split_ids(trace["task_ids"])
        acceptance_ids = split_ids(trace["acceptance_ids"])
        release_gates = split_ids(trace["release_gate"])
        missing_functions = sorted(
            function_id
            for function_id in related_functions
            if function_id != "cross-cutting" and function_id not in functions
        )
        missing_tasks = sorted(task_id for task_id in task_ids if task_id not in tasks)
        missing_acceptance = sorted(
            acceptance_id for acceptance_id in acceptance_ids if acceptance_id not in acceptance
        )
        missing_gates = sorted(gate_id for gate_id in release_gates if gate_id not in gates)

        if severity in HIGH_SEVERITIES:
            high_or_critical_count += 1
            required_fields = [
                "related_function_ids",
                "control",
                "trigger",
                "owner",
                "task_ids",
                "acceptance_ids",
                "release_gate",
            ]
            missing_fields = [field for field in required_fields if not trace[field].strip()]
            if missing_fields:
                raise AssertionError(f"{risk_id} missing fields: {missing_fields}")
            if "cross-cutting" in related_functions:
                raise AssertionError(f"{risk_id} high/critical risk must cite concrete functions")
            if missing_functions or missing_tasks or missing_acceptance or missing_gates:
                raise AssertionError(
                    f"{risk_id} invalid references: "
                    f"functions={missing_functions} tasks={missing_tasks} "
                    f"acceptance={missing_acceptance} gates={missing_gates}"
                )

        rows.append(
            {
                "risk_id": risk_id,
                "severity": trace["severity"],
                "likelihood": trace["likelihood"],
                "risk": risk["risk"],
                "related_function_ids": ";".join(related_functions),
                "control": trace["control"],
                "trigger": trace["trigger"],
                "owner": trace["owner"],
                "task_ids": ";".join(task_ids),
                "acceptance_ids": ";".join(acceptance_ids),
                "release_gates": ";".join(release_gates),
                "status": trace["status"],
            }
        )

    return rows, {
        "risk_rows": len(risks),
        "traceability_rows": len(traces),
        "high_or_critical_risks": high_or_critical_count,
        "severity_counts": dict(sorted(Counter(row["severity"].lower() for row in traces).items())),
    }


def build_summary() -> dict[str, Any]:
    mapping, mapping_summary = build_mapping()
    return {
        "schema_version": 1,
        "task_id": "T1214",
        "acceptance_ids": ["A185"],
        "risk_control": mapping_summary,
        "artifacts": {
            "summary": str(SUMMARY_PATH),
            "mapping": str(MAPPING_PATH),
            "a185_evidence": str(A185_EVIDENCE_PATH),
        },
        "mapping_preview": mapping[:5],
    }


def build_a185_evidence(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_id": "T1214",
        "acceptance_id": "A185",
        "status": "DONE",
        "evidence_type": "high_risk_control_traceability",
        "high_or_critical_risks": summary["risk_control"]["high_or_critical_risks"],
        "artifact": str(MAPPING_PATH),
        "validated_by": [
            "scripts/manage_risk_control_artifacts.py validate",
            "make validate-risk-control-artifacts",
            "make verify",
        ],
    }


def expected_artifacts() -> dict[Path, str]:
    mapping, _ = build_mapping()
    summary = build_summary()
    return {
        SUMMARY_PATH: json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        MAPPING_PATH: render_csv(mapping),
        A185_EVIDENCE_PATH: json.dumps(build_a185_evidence(summary), ensure_ascii=False, indent=2)
        + "\n",
    }


def generate(_: argparse.Namespace) -> None:
    artifacts = expected_artifacts()
    for path, content in artifacts.items():
        write_text(path, content)
    validate(None)
    print(
        json.dumps(
            {"generated": True, "artifacts": sorted(str(path) for path in artifacts)},
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
        if target.read_text(encoding="utf-8") != expected:
            raise AssertionError(f"{path} is not synchronized with source catalogs")
    summary = json.loads((ROOT / SUMMARY_PATH).read_text(encoding="utf-8"))
    if summary["risk_control"]["risk_rows"] != 53:
        raise AssertionError("risk summary must cover 53 risks")
    if summary["risk_control"]["high_or_critical_risks"] <= 0:
        raise AssertionError("risk summary must include high/critical risks")
    print(
        json.dumps(
            {
                "valid": True,
                "risk_rows": summary["risk_control"]["risk_rows"],
                "high_or_critical_risks": summary["risk_control"][
                    "high_or_critical_risks"
                ],
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
        print(f"Risk-control artifact validation: FAIL - {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
