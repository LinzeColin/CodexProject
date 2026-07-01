#!/usr/bin/env python3
"""Validate KMFA S14-P1 fund/cash/loan public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.fund_cash_loan_plan import (
    DEFAULT_HTML_OUTPUT_DIR,
    DEFAULT_OUTPUT_ACCOUNT_SUMMARY,
    DEFAULT_OUTPUT_CASH_PRESSURE,
    DEFAULT_OUTPUT_LOAN_DUE_ALERTS,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_SOURCE_LANES,
    read_json,
    read_jsonl,
    validate_fund_cash_loan_plan_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S14-P1 fund/cash/loan planning artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--source-lanes", type=Path, default=DEFAULT_OUTPUT_SOURCE_LANES)
    parser.add_argument("--cash-pressure", type=Path, default=DEFAULT_OUTPUT_CASH_PRESSURE)
    parser.add_argument("--loan-due-alerts", type=Path, default=DEFAULT_OUTPUT_LOAN_DUE_ALERTS)
    parser.add_argument("--account-summaries", type=Path, default=DEFAULT_OUTPUT_ACCOUNT_SUMMARY)
    parser.add_argument("--html-output-dir", type=Path, default=DEFAULT_HTML_OUTPUT_DIR)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    source_lanes = read_jsonl(args.source_lanes)
    cash_pressure = read_jsonl(args.cash_pressure)
    loan_due_alerts = read_jsonl(args.loan_due_alerts)
    account_summaries = read_jsonl(args.account_summaries)
    html_outputs = {
        "fund_cash_loan_plan_overview": (
            args.html_output_dir / "fund_cash_loan_plan_overview.html"
        ).read_text(encoding="utf-8")
    }

    validate_fund_cash_loan_plan_artifacts(
        manifest,
        source_lanes,
        cash_pressure,
        loan_due_alerts,
        account_summaries,
        html_outputs,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S14-P1 fund cash loan plan check passed "
        f"(source_lanes={summary['source_lane_count']}, "
        f"cash_pressure={summary['cash_pressure_record_count']}, "
        f"loan_due_alerts={summary['loan_due_alert_count']}, "
        f"account_summaries={summary['account_balance_summary_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "payment_approval=false, bank_operation=false, loan_management=false, "
        "s14_p2_scope=false, s14_p3_scope=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
