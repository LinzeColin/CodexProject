"""Command-line interface for Phase 1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .doctor import doctor_report, render_report
from .notifications import render_email
from .state_machine import validate_run_record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adp", description="arXiv Daily Push CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Print package version.")

    doctor = subparsers.add_parser("doctor", help="Run local Phase 1 readiness checks.")
    doctor.add_argument("--json", action="store_true", help="Print JSON report.")
    doctor.add_argument("--path", default=".", help="Path used for disk readiness checks.")

    email = subparsers.add_parser("render-email", help="Render a dry-run notification email.")
    email.add_argument("--status", default="success")
    email.add_argument("--run-id", default="phase1-foundation")
    email.add_argument("--summary", default="Phase 1 foundation status")
    email.add_argument("--date", default="not-scheduled")

    validate_record = subparsers.add_parser("validate-record", help="Validate a RunRecord JSON file.")
    validate_record.add_argument("--path", required=True, help="RunRecord JSON path.")
    validate_record.add_argument("--json", action="store_true", help="Print JSON validation output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "doctor":
        report = doctor_report(Path(args.path))
        print(render_report(report, as_json=args.json))
        return 0 if report["status"] in {"pass", "warn"} else 2
    if args.command == "render-email":
        email = render_email(args.status, args.run_id, args.summary, date=args.date)
        print(f"To: {email.recipient}")
        print(f"Subject: {email.subject}")
        print("")
        print(email.body)
        return 0
    if args.command == "validate-record":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        errors = validate_run_record(data)
        payload = {"status": "pass" if not errors else "fail", "errors": errors}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(payload["status"])
            for error in errors:
                print(f"- {error}")
        return 0 if not errors else 2
    raise AssertionError(f"Unhandled command: {args.command}")
