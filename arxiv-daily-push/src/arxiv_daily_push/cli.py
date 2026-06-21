"""Command-line interface for arXiv Daily Push."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .acceptance import AcceptanceError, build_acceptance_package, validate_acceptance_package
from .arxiv_adapter import ArxivQuery, build_query_url, parse_atom_feed
from .doctor import doctor_report, render_report
from .evidence_gate import gate_publication
from .handoff import HandoffError, build_handoff, validate_handoff
from .lesson import LessonGenerationError, generate_lesson
from .narration import NarrationError, generate_narration_plan
from .notifications import render_email
from .pipeline import PipelineError, run_daily_dry_run
from .production_preflight import build_production_preflight, validate_production_preflight
from .ranking import selection_payload
from .state_machine import validate_run_record
from .trial import evaluate_trial_evidence, validate_trial_evidence_report
from .trial_bootstrap import build_trial_bootstrap_plan, validate_trial_bootstrap_plan
from .video import VideoPlanError, generate_storyboard


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

    narration = subparsers.add_parser("generate-narration", help="Generate dry-run narration/TTS plan from Lesson JSON.")
    narration.add_argument("--path", required=True, help="JSON file containing lesson or a Lesson object.")
    narration.add_argument("--generated-at", required=True, help="Narration generation timestamp.")
    narration.add_argument("--tts-mode", default="dry_run", help="Only dry_run is allowed in Phase 7.")
    narration.add_argument("--check-path", default=".", help="Path used for resource gate disk checks.")
    narration.add_argument("--json", action="store_true", help="Print JSON narration output.")

    storyboard = subparsers.add_parser("generate-storyboard", help="Generate dry-run video storyboard from narration JSON.")
    storyboard.add_argument("--path", required=True, help="JSON file containing narration or a narration object.")
    storyboard.add_argument("--generated-at", required=True, help="Storyboard generation timestamp.")
    storyboard.add_argument("--check-path", default=".", help="Path used for media gate disk checks.")
    storyboard.add_argument("--json", action="store_true", help="Print JSON storyboard output.")

    pipeline = subparsers.add_parser("run-daily-dry-run", help="Run local daily dry-run pipeline from source/claims JSON.")
    pipeline.add_argument("--path", required=True, help="JSON file containing source_item, claims, run_id, publication_id, date, and generated_at.")
    pipeline.add_argument("--json", action="store_true", help="Print JSON dry-run pipeline output.")

    handoff = subparsers.add_parser("build-handoff", help="Build runner/release/email dry-run handoff from pipeline output.")
    handoff.add_argument("--path", required=True, help="JSON file containing a dry-run pipeline payload.")
    handoff.add_argument("--generated-at", required=True, help="Handoff generation timestamp.")
    handoff.add_argument("--json", action="store_true", help="Print JSON handoff output.")

    acceptance = subparsers.add_parser("build-acceptance", help="Build Phase 11 acceptance/handoff package from handoff JSON.")
    acceptance.add_argument("--path", required=True, help="JSON file containing a Phase 10 handoff payload.")
    acceptance.add_argument("--generated-at", required=True, help="Acceptance package generation timestamp.")
    acceptance.add_argument("--operational-evidence", help="Optional JSON file with live operational evidence refs.")
    acceptance.add_argument("--json", action="store_true", help="Print JSON acceptance package.")

    trial = subparsers.add_parser("evaluate-trial", help="Evaluate 30-day production trial evidence for Phase 11 acceptance.")
    trial.add_argument("--path", required=True, help="JSON file containing 30-day trial evidence.")
    trial.add_argument("--generated-at", required=True, help="Trial evidence report generation timestamp.")
    trial.add_argument("--json", action="store_true", help="Print JSON trial evidence report.")

    preflight = subparsers.add_parser("preflight-production", help="Run fail-closed production preflight before scheduled execution.")
    preflight.add_argument("--path", default=".", help="Repository path used for disk, Git, and cache checks.")
    preflight.add_argument("--generated-at", required=True, help="Preflight report generation timestamp.")
    preflight.add_argument("--json", action="store_true", help="Print JSON preflight report.")

    bootstrap = subparsers.add_parser("plan-trial-bootstrap", help="Validate the manual production trial bootstrap workflow.")
    bootstrap.add_argument("--path", default=".", help="Repository root path containing the workflow and runbook.")
    bootstrap.add_argument("--generated-at", required=True, help="Bootstrap plan generation timestamp.")
    bootstrap.add_argument("--json", action="store_true", help="Print JSON bootstrap plan.")
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
    if args.command == "generate-narration":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        lesson = data.get("lesson", data) if isinstance(data, dict) else data
        try:
            narration = generate_narration_plan(
                lesson,
                generated_at=args.generated_at,
                tts_mode=args.tts_mode,
                path=Path(args.check_path),
            )
        except NarrationError as error:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": [str(error)]}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(narration, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{narration['narration_id']}\t{len(narration['segments'])} segments")
        return 0
    if args.command == "generate-storyboard":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        narration = data.get("narration", data) if isinstance(data, dict) else data
        try:
            storyboard = generate_storyboard(narration, generated_at=args.generated_at, path=Path(args.check_path))
        except VideoPlanError as error:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": [str(error)]}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(storyboard, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{storyboard['storyboard_id']}\t{len(storyboard['scenes'])} scenes")
        return 0
    if args.command == "run-daily-dry-run":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        try:
            payload = run_daily_dry_run(
                data["source_item"],
                data["claims"],
                run_id=data["run_id"],
                publication_id=data["publication_id"],
                date=data["date"],
                generated_at=data["generated_at"],
                timezone=data.get("timezone", "Australia/Sydney"),
            )
        except PipelineError as error:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": [str(error)]}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{payload['run_record']['run_id']}\t{payload['status']}")
        return 0
    if args.command == "build-handoff":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        try:
            handoff = build_handoff(data, generated_at=args.generated_at)
        except HandoffError as error:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": [str(error)]}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                print(f"- {error}")
            return 2
        errors = validate_handoff(handoff)
        if errors:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": errors}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(handoff, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{handoff['handoff_id']}\tdry-run")
        return 0
    if args.command == "build-acceptance":
        handoff = json.loads(Path(args.path).read_text(encoding="utf-8"))
        evidence = (
            json.loads(Path(args.operational_evidence).read_text(encoding="utf-8"))
            if args.operational_evidence
            else None
        )
        try:
            package = build_acceptance_package(handoff, generated_at=args.generated_at, operational_evidence=evidence)
        except AcceptanceError as error:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": [str(error)]}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                print(f"- {error}")
            return 2
        errors = validate_acceptance_package(package)
        if errors:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": errors}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{package['acceptance_id']}\t{package['production_acceptance_status']}")
        return 0
    if args.command == "evaluate-trial":
        evidence = json.loads(Path(args.path).read_text(encoding="utf-8"))
        report = evaluate_trial_evidence(evidence, generated_at=args.generated_at)
        errors = validate_trial_evidence_report(report)
        if errors:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": errors}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{report['trial_evidence_id']}\t{report['production_evidence_status']}")
        return 0 if report["accepted_for_production"] else 2
    if args.command == "preflight-production":
        report = build_production_preflight(Path(args.path), generated_at=args.generated_at)
        errors = validate_production_preflight(report)
        if errors:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": errors}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{report['preflight_id']}\t{report['status']}")
        return 0 if report["production_run_allowed"] else 2
    if args.command == "plan-trial-bootstrap":
        plan = build_trial_bootstrap_plan(Path(args.path), generated_at=args.generated_at)
        errors = validate_trial_bootstrap_plan(plan)
        if errors:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": errors}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{plan['plan_id']}\t{plan['status']}")
        return 0 if plan["trial_bootstrap_ready"] else 2
    raise AssertionError(f"Unhandled command: {args.command}")
