"""Command-line interface for arXiv Daily Push."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .arxiv_adapter import ArxivQuery, build_query_url, parse_atom_feed
from .doctor import doctor_report, render_report
from .evidence_gate import gate_publication
from .lesson import LessonGenerationError, generate_lesson
from .notifications import render_email
from .ranking import selection_payload
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

    arxiv_url = subparsers.add_parser("arxiv-url", help="Render an arXiv API query URL without fetching it.")
    arxiv_url.add_argument("--query", default="cat:cs.AI")
    arxiv_url.add_argument("--start", type=int, default=0)
    arxiv_url.add_argument("--max-results", type=int, default=10)
    arxiv_url.add_argument("--sort-by", default="submittedDate")
    arxiv_url.add_argument("--sort-order", default="descending")

    parse_arxiv = subparsers.add_parser("parse-arxiv-atom", help="Parse an arXiv Atom XML file into SourceItem JSON.")
    parse_arxiv.add_argument("--path", required=True, help="Atom XML fixture or downloaded response path.")
    parse_arxiv.add_argument("--retrieved-at", required=True, help="Retrieval timestamp to stamp on SourceItems.")
    parse_arxiv.add_argument("--json", action="store_true", help="Pretty-print JSON output.")

    rank = subparsers.add_parser("rank-candidates", help="Rank candidate SourceItems with evidence-gated audit output.")
    rank.add_argument("--path", required=True, help="JSON file containing a candidates array.")
    rank.add_argument("--recent-source-id", action="append", default=[], help="Source ID already selected recently.")
    rank.add_argument("--json", action="store_true", help="Print JSON selection payload.")

    gate = subparsers.add_parser("gate-publication", help="Build a Claim Ledger and gate publication from local JSON input.")
    gate.add_argument("--path", required=True, help="JSON file containing source_item, claims, run_id, publication_id, and created_at.")
    gate.add_argument("--json", action="store_true", help="Print JSON gate output.")

    lesson = subparsers.add_parser("generate-lesson", help="Generate evidence-linked Chinese Lesson JSON from local input.")
    lesson.add_argument("--path", required=True, help="JSON file containing source_item, claims, and generated_at or created_at.")
    lesson.add_argument("--language", default="zh-CN", help="Lesson language; default zh-CN.")
    lesson.add_argument("--json", action="store_true", help="Print JSON lesson output.")
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
    if args.command == "arxiv-url":
        query = ArxivQuery(
            search_query=args.query,
            start=args.start,
            max_results=args.max_results,
            sort_by=args.sort_by,
            sort_order=args.sort_order,
        )
        print(build_query_url(query))
        return 0
    if args.command == "parse-arxiv-atom":
        items = parse_atom_feed(Path(args.path).read_text(encoding="utf-8"), retrieved_at=args.retrieved_at)
        if args.json:
            print(json.dumps(items, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for item in items:
                print(f"{item['source_id']}\t{item['title']}")
        return 0
    if args.command == "rank-candidates":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        candidates = data.get("candidates") if isinstance(data, dict) else data
        payload = selection_payload(candidates, recent_source_ids=args.recent_source_id)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        elif payload["selected"]:
            selected = payload["selected"]
            print(f"{selected['source_id']}\t{selected['total_score']}")
        else:
            print("blocked")
            for audit in payload["audits"]:
                for reason in audit["blocking_reasons"]:
                    print(f"- {audit['source_id']}: {reason}")
        return 0 if payload["selected"] else 2
    if args.command == "gate-publication":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        payload = gate_publication(
            data["source_item"],
            data["claims"],
            run_id=data["run_id"],
            publication_id=data["publication_id"],
            publication_type=data.get("publication_type", "daily"),
            created_at=data["created_at"],
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        elif payload["publish_allowed"]:
            print("ready")
        else:
            print("blocked")
            for reason in payload["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if payload["publish_allowed"] else 2
    if args.command == "generate-lesson":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        generated_at = data.get("generated_at") or data.get("created_at")
        try:
            lesson = generate_lesson(data["source_item"], data["claims"], generated_at=generated_at, language=args.language)
        except LessonGenerationError as error:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": [str(error)]}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(lesson, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{lesson['lesson_id']}\t{lesson['title']}")
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")
