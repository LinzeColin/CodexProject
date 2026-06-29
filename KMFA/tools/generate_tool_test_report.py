#!/usr/bin/env python3
"""Generate the KMFA S04-P3 synthetic basic-tool test report."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.amount_tools import AmountNormalizationError, normalize_amount_to_cents
from KMFA.tools.field_standardization import FieldStandardizationError, MissingFieldError, standardize_date, standardize_period


CaseFunction = Callable[[Any], Any]


def _value_repr(value: Any) -> str:
    if isinstance(value, Decimal):
        return f"Decimal({str(value)!r})"
    return repr(value)


def _run_case(
    *,
    case_id: str,
    category: str,
    description: str,
    func: CaseFunction,
    value: Any,
    expected: Any = None,
    expected_error: type[BaseException] | tuple[type[BaseException], ...] | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "case_id": case_id,
        "category": category,
        "description": description,
        "input_repr": _value_repr(value),
    }
    try:
        actual = func(value)
    except Exception as exc:  # noqa: BLE001 - report expected and unexpected tool failures.
        record["actual_error"] = type(exc).__name__
        record["expected_error"] = (
            expected_error.__name__
            if isinstance(expected_error, type)
            else " or ".join(item.__name__ for item in expected_error or ())
        )
        record["outcome"] = "PASS" if expected_error is not None and isinstance(exc, expected_error) else "FAIL"
        return record

    record["actual"] = actual
    record["expected"] = expected
    record["outcome"] = "PASS" if expected_error is None and actual == expected else "FAIL"
    return record


def run_amount_boundary_cases() -> list[dict[str, Any]]:
    cases = [
        {
            "case_id": "S4PCT01-AMOUNT-DECIMAL-CENT",
            "category": "amount_decimal",
            "description": "Decimal string with one cent normalizes to integer cents.",
            "value": "0.01",
            "expected": 1,
        },
        {
            "case_id": "S4PCT01-AMOUNT-DECIMAL-LARGE",
            "category": "amount_decimal",
            "description": "Large decimal string preserves exact cents.",
            "value": "1234567890.12",
            "expected": 123456789012,
        },
        {
            "case_id": "S4PCT01-AMOUNT-DECIMAL-OBJECT",
            "category": "amount_decimal",
            "description": "Decimal object normalizes without float conversion.",
            "value": Decimal("0.01"),
            "expected": 1,
        },
        {
            "case_id": "S4PCT01-AMOUNT-FRACTIONAL-CENT",
            "category": "amount_decimal",
            "description": "Fractional cent input is rejected instead of rounded.",
            "value": "1.234",
            "expected_error": AmountNormalizationError,
        },
        {
            "case_id": "S4PCT01-AMOUNT-NEGATIVE-MINUS",
            "category": "amount_negative",
            "description": "Minus sign negative amount preserves sign.",
            "value": "-0.01",
            "expected": -1,
        },
        {
            "case_id": "S4PCT01-AMOUNT-NEGATIVE-PARENTHESES",
            "category": "amount_negative",
            "description": "Parentheses negative amount preserves sign.",
            "value": "(0.01)",
            "expected": -1,
        },
        {
            "case_id": "S4PCT01-AMOUNT-NEGATIVE-UNICODE",
            "category": "amount_negative",
            "description": "Unicode minus amount preserves sign.",
            "value": "\u22120.01",
            "expected": -1,
        },
        {
            "case_id": "S4PCT01-AMOUNT-WAN-MIN-CENT",
            "category": "amount_wan_yuan",
            "description": "Ten-thousand-yuan unit converts to exact cents.",
            "value": "0.0001\u4e07\u5143",
            "expected": 100,
        },
        {
            "case_id": "S4PCT01-AMOUNT-WAN-NEGATIVE",
            "category": "amount_wan_yuan",
            "description": "Negative ten-thousand-yuan unit converts to exact cents.",
            "value": "-1.2345\u4e07\u5143",
            "expected": -1234500,
        },
        {
            "case_id": "S4PCT01-AMOUNT-ABNORMAL-HASH",
            "category": "amount_abnormal_characters",
            "description": "Hash-containing amount is rejected.",
            "value": "1#2",
            "expected_error": AmountNormalizationError,
        },
        {
            "case_id": "S4PCT01-AMOUNT-ABNORMAL-PENDING",
            "category": "amount_abnormal_characters",
            "description": "Pending-confirmation text is rejected.",
            "value": "\u91d1\u989d\u5f85\u786e\u8ba4",
            "expected_error": AmountNormalizationError,
        },
    ]
    return [
        _run_case(
            case_id=str(case["case_id"]),
            category=str(case["category"]),
            description=str(case["description"]),
            func=normalize_amount_to_cents,
            value=case["value"],
            expected=case.get("expected"),
            expected_error=case.get("expected_error"),  # type: ignore[arg-type]
        )
        for case in cases
    ]


def run_date_period_boundary_cases() -> list[dict[str, Any]]:
    cases = [
        {
            "case_id": "S4PCT02-DATE-CHINESE",
            "category": "date_chinese",
            "description": "Chinese date normalizes to ISO date.",
            "func": standardize_date,
            "value": "2026\u5e746\u670829\u65e5",
            "expected": "2026-06-29",
        },
        {
            "case_id": "S4PCT02-DATE-COMPACT",
            "category": "date_compact",
            "description": "Compact numeric date normalizes to ISO date.",
            "func": standardize_date,
            "value": "20260629",
            "expected": "2026-06-29",
        },
        {
            "case_id": "S4PCT02-DATE-SLASH",
            "category": "date_separator",
            "description": "Slash-separated date normalizes to ISO date.",
            "func": standardize_date,
            "value": "2026/6/9",
            "expected": "2026-06-09",
        },
        {
            "case_id": "S4PCT02-PERIOD-CHINESE-YEARMONTH",
            "category": "period_chinese_year_month",
            "description": "Chinese year-month normalizes to YYYY-MM.",
            "func": standardize_period,
            "value": "2026\u5e746\u6708",
            "expected": "2026-06",
        },
        {
            "case_id": "S4PCT02-PERIOD-COMPACT",
            "category": "period_compact",
            "description": "Compact numeric period normalizes to YYYY-MM.",
            "func": standardize_period,
            "value": "202606",
            "expected": "2026-06",
        },
        {
            "case_id": "S4PCT02-PERIOD-FROM-CHINESE-DATE",
            "category": "period_from_date",
            "description": "Chinese date used as period normalizes to its month.",
            "func": standardize_period,
            "value": "2026\u5e746\u670829\u65e5",
            "expected": "2026-06",
        },
        {
            "case_id": "S4PCT02-DATE-NONE",
            "category": "date_nullish",
            "description": "None date is rejected as missing.",
            "func": standardize_date,
            "value": None,
            "expected_error": MissingFieldError,
        },
        {
            "case_id": "S4PCT02-PERIOD-BLANK",
            "category": "period_nullish",
            "description": "Blank period is rejected as missing.",
            "func": standardize_period,
            "value": " ",
            "expected_error": MissingFieldError,
        },
        {
            "case_id": "S4PCT02-DATE-HASH",
            "category": "date_nullish",
            "description": "Hash date is rejected as missing.",
            "func": standardize_date,
            "value": "#",
            "expected_error": MissingFieldError,
        },
        {
            "case_id": "S4PCT02-DATE-NA",
            "category": "date_nullish",
            "description": "N/A date is rejected as missing.",
            "func": standardize_date,
            "value": "N/A",
            "expected_error": MissingFieldError,
        },
        {
            "case_id": "S4PCT02-DATE-INVALID-MONTH",
            "category": "date_invalid",
            "description": "Invalid month is rejected.",
            "func": standardize_date,
            "value": "2026-13-01",
            "expected_error": FieldStandardizationError,
        },
    ]
    return [
        _run_case(
            case_id=str(case["case_id"]),
            category=str(case["category"]),
            description=str(case["description"]),
            func=case["func"],  # type: ignore[arg-type]
            value=case["value"],
            expected=case.get("expected"),
            expected_error=case.get("expected_error"),  # type: ignore[arg-type]
        )
        for case in cases
    ]


def build_report() -> dict[str, Any]:
    amount_cases = run_amount_boundary_cases()
    date_period_cases = run_date_period_boundary_cases()
    all_cases = amount_cases + date_period_cases
    passed = sum(1 for case in all_cases if case["outcome"] == "PASS")
    failed = len(all_cases) - passed
    return {
        "schema_version": "kmfa.tool_function_test_report.v1",
        "project_id": "KMFA",
        "stage": "S04",
        "phase": "S04-P3",
        "task_ids": ["S4PCT01", "S4PCT02", "S4PCT03"],
        "generated_at": "2026-06-29T23:05:00+10:00",
        "status": "PASS" if failed == 0 else "FAIL",
        "raw_business_data_used": False,
        "case_summary": {
            "total": len(all_cases),
            "passed": passed,
            "failed": failed,
        },
        "coverage": [
            "amount decimals",
            "amount negatives",
            "amount ten-thousand-yuan unit",
            "amount abnormal characters",
            "Chinese dates",
            "year-month periods",
            "nullish date and period values",
        ],
        "amount_boundary_cases": amount_cases,
        "date_period_boundary_cases": date_period_cases,
        "non_scope": [
            "raw business data import",
            "A0 golden baseline",
            "zero-delta validator",
            "fact layer",
            "report generation",
            "UI",
            "external connectors",
            "GitHub upload",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# S04-P3 Tool Function Test Report",
        "",
        f"- Project: `{report['project_id']}`",
        f"- Stage/Phase: `{report['stage']}/{report['phase']}`",
        f"- Status: `{report['status']}`",
        f"- Raw business data used: `{str(report['raw_business_data_used']).lower()}`",
        "",
        "## Case Summary",
        "",
        "| Total | Passed | Failed |",
        "|---:|---:|---:|",
        f"| {report['case_summary']['total']} | {report['case_summary']['passed']} | {report['case_summary']['failed']} |",
        "",
        "## Coverage",
        "",
    ]
    lines.extend(f"- {item}" for item in report["coverage"])
    lines.extend(["", "## Boundary Cases", "", "| Case | Category | Outcome |", "|---|---|---|"])
    for case in report["amount_boundary_cases"] + report["date_period_boundary_cases"]:
        lines.append(f"| `{case['case_id']}` | `{case['category']}` | `{case['outcome']}` |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S04-P3 synthetic basic-tool test report.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args(argv)
    report = build_report()
    if args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
