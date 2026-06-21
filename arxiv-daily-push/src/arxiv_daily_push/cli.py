"""Command-line interface for arXiv Daily Push."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .acceptance import AcceptanceError, build_acceptance_package, validate_acceptance_package
from .arxiv_adapter import ArxivQuery, build_query_url, parse_atom_feed
from .daily_input import build_daily_input_package, validate_daily_input_report
from .doctor import doctor_report, render_report
from .evidence_gate import gate_publication
from .handoff import HandoffError, build_handoff, validate_handoff
from .lesson import LessonGenerationError, generate_lesson
from .narration import NarrationError, generate_narration_plan
from .notifications import render_email
from .pipeline import PipelineError, run_daily_dry_run
from .production_launch import build_production_launch_readiness, validate_production_launch_readiness
from .production_preflight import build_production_preflight, validate_production_preflight
from .production_refs import build_production_refs_report, validate_production_refs_report
from .production_scheduler import build_production_scheduler_plan, validate_production_scheduler_plan
from .ranking import selection_payload
from .release_delivery import DEFAULT_RELEASE_REPO, deliver_release, validate_release_delivery_report
from .scheduled_execution import (
    SCHEDULED_EXECUTION_MODES,
    load_json_mapping,
    run_scheduled_execution,
    validate_scheduled_execution_report,
)
from .source_ingest import ingest_latest_arxiv, validate_source_batch
from .smtp_delivery import deliver_notification, validate_smtp_delivery_report
from .state_machine import validate_run_record
from .trial import evaluate_trial_evidence, validate_trial_evidence_report
from .trial_bootstrap import build_trial_bootstrap_plan, validate_trial_bootstrap_plan
from .trial_ledger import update_trial_evidence_ledger, validate_trial_ledger_update_report
from .trial_ops import annotate_trial_operational_evidence, validate_trial_ops_report
from .trial_recovery import build_trial_recovery_evidence, validate_trial_recovery_report
from .trial_resource import build_trial_resource_evidence, validate_trial_resource_report
from .trial_replay import build_trial_replay_evidence, validate_trial_replay_report
from .trial_start import build_trial_start_gate, validate_trial_start_report
from .trial_start_workflow import build_trial_start_workflow_plan, validate_trial_start_workflow_plan
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

    send_notification = subparsers.add_parser("send-notification", help="Render and optionally send a fail-closed SMTP notification.")
    send_notification.add_argument("--status", default="success")
    send_notification.add_argument("--run-id", required=True)
    send_notification.add_argument("--summary", required=True)
    send_notification.add_argument("--date", required=True)
    send_notification.add_argument("--generated-at", required=True)
    send_notification.add_argument("--phase", default="11")
    send_notification.add_argument("--stage", default="production-trial")
    send_notification.add_argument("--claim-gate", default="not_applicable_notification")
    send_notification.add_argument("--next-action", default="inspect_smtp_delivery_report")
    send_notification.add_argument("--allow-send", action="store_true", help="Actually send SMTP mail when required env keys are present.")
    send_notification.add_argument("--json", action="store_true", help="Print JSON delivery evidence.")

    release = subparsers.add_parser("publish-release", help="Create a fail-closed GitHub Release delivery evidence report.")
    release.add_argument("--tag", required=True, help="GitHub Release tag.")
    release.add_argument("--title", required=True, help="GitHub Release title.")
    release.add_argument("--notes", default="", help="Release notes text. The evidence report stores only a SHA256.")
    release.add_argument("--notes-file", help="Path to Release notes text. Overrides --notes.")
    release.add_argument("--asset", action="append", default=[], help="Release asset path. May be repeated.")
    release.add_argument("--generated-at", required=True, help="Release evidence timestamp.")
    release.add_argument("--target", help="Release target commit-ish. Defaults to ADP_RELEASE_TARGET.")
    release.add_argument("--repo", default=DEFAULT_RELEASE_REPO, help="GitHub repo owner/name.")
    release.add_argument("--allow-upload", action="store_true", help="Actually create the Release with gh.")
    release.add_argument("--publish", action="store_true", help="Create a published Release instead of the default draft.")
    release.add_argument("--json", action="store_true", help="Print JSON delivery evidence.")

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

    fetch_arxiv = subparsers.add_parser("fetch-arxiv-latest", help="Fetch latest arXiv SourceItems with incremental duplicate filtering.")
    fetch_arxiv.add_argument("--query", default="cat:cs.AI", help="arXiv search_query.")
    fetch_arxiv.add_argument("--max-results", type=int, default=10, help="Small arXiv result window to fetch.")
    fetch_arxiv.add_argument("--start", type=int, default=0, help="arXiv result start offset.")
    fetch_arxiv.add_argument("--generated-at", required=True, help="Fetch timestamp used for SourceItems and batch evidence.")
    fetch_arxiv.add_argument("--seen-source-id", action="append", default=[], help="Previously published source_id to exclude.")
    fetch_arxiv.add_argument("--json", action="store_true", help="Print JSON source batch.")

    build_daily_input = subparsers.add_parser(
        "build-daily-input",
        help="Build a ranked daily pipeline input from an arXiv source batch.",
    )
    build_daily_input.add_argument("--source-batch", required=True, help="JSON source batch from fetch-arxiv-latest.")
    build_daily_input.add_argument("--date", required=True, help="Daily publication date in YYYY-MM-DD form.")
    build_daily_input.add_argument("--generated-at", required=True, help="Builder timestamp used for evidence claims.")
    build_daily_input.add_argument("--timezone", default="Australia/Sydney", help="Daily run timezone.")
    build_daily_input.add_argument("--recent-source-id", action="append", default=[], help="Source ID already selected recently.")
    build_daily_input.add_argument("--json", action="store_true", help="Print JSON daily input builder report.")

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

    trial_ledger = subparsers.add_parser(
        "update-trial-ledger",
        help="Append one production-ready scheduled daily-run report to a trial evidence ledger.",
    )
    trial_ledger.add_argument("--path", help="Existing trial evidence JSON. Empty starts a new ledger.")
    trial_ledger.add_argument("--scheduled-execution", required=True, help="Scheduled execution report JSON.")
    trial_ledger.add_argument("--generated-at", required=True, help="Ledger update timestamp.")
    trial_ledger.add_argument("--trial-id", default="adp-trial-current")
    trial_ledger.add_argument("--trial-ref", default="")
    trial_ledger.add_argument("--expected-days", type=int, default=30)
    trial_ledger.add_argument("--text-degradation-verified", action="store_true")
    trial_ledger.add_argument("--video-degradation-verified", action="store_true")
    trial_ledger.add_argument("--scheduler-enabled", action="store_true")
    trial_ledger.add_argument("--manual-rerun-verified", action="store_true")
    trial_ledger.add_argument("--scheduler-ref", default="")
    trial_ledger.add_argument("--private-release-verified", action="store_true")
    trial_ledger.add_argument("--release-ref", default="")
    trial_ledger.add_argument("--real-smtp-verified", action="store_true")
    trial_ledger.add_argument("--email-ref", default="")
    trial_ledger.add_argument("--resource-pressure-ok", action="store_true")
    trial_ledger.add_argument("--resource-ref", default="")
    trial_ledger.add_argument("--weekly-replay-verified", action="store_true")
    trial_ledger.add_argument("--monthly-replay-verified", action="store_true")
    trial_ledger.add_argument("--weekly-monthly-ref", default="")
    trial_ledger.add_argument("--recovery-drill-verified", action="store_true")
    trial_ledger.add_argument("--recovery-ref", default="")
    trial_ledger.add_argument("--json", action="store_true", help="Print JSON trial ledger update report.")

    trial_state = subparsers.add_parser(
        "export-trial-ledger-state",
        help="Export the trial_evidence object from a passing trial ledger update report.",
    )
    trial_state.add_argument("--ledger-update", required=True, help="Trial ledger update report JSON.")
    trial_state.add_argument("--json", action="store_true", help="Print JSON trial evidence state.")

    trial_ops = subparsers.add_parser(
        "annotate-trial-ops-evidence",
        help="Merge explicit weekly/monthly/recovery and operational evidence refs into a trial evidence ledger.",
    )
    trial_ops.add_argument("--path", required=True, help="Existing trial evidence JSON.")
    trial_ops.add_argument("--generated-at", required=True, help="Operational evidence annotation timestamp.")
    trial_ops.add_argument("--trial-id", default="adp-trial-current")
    trial_ops.add_argument("--trial-ref", default="")
    trial_ops.add_argument("--expected-days", type=int, default=30)
    trial_ops.add_argument("--scheduler-enabled", action="store_true")
    trial_ops.add_argument("--manual-rerun-verified", action="store_true")
    trial_ops.add_argument("--scheduler-ref", default="")
    trial_ops.add_argument("--private-release-verified", action="store_true")
    trial_ops.add_argument("--release-ref", default="")
    trial_ops.add_argument("--real-smtp-verified", action="store_true")
    trial_ops.add_argument("--email-ref", default="")
    trial_ops.add_argument("--resource-pressure-ok", action="store_true")
    trial_ops.add_argument("--resource-ref", default="")
    trial_ops.add_argument("--weekly-replay-verified", action="store_true")
    trial_ops.add_argument("--monthly-replay-verified", action="store_true")
    trial_ops.add_argument("--weekly-monthly-ref", default="")
    trial_ops.add_argument("--recovery-drill-verified", action="store_true")
    trial_ops.add_argument("--recovery-ref", default="")
    trial_ops.add_argument("--json", action="store_true", help="Print JSON operational evidence annotation report.")

    trial_ops_state = subparsers.add_parser(
        "export-trial-ops-state",
        help="Export the trial_evidence object from a passing trial ops annotation report.",
    )
    trial_ops_state.add_argument("--ops-update", required=True, help="Trial ops annotation report JSON.")
    trial_ops_state.add_argument("--json", action="store_true", help="Print JSON trial evidence state.")

    trial_replay = subparsers.add_parser(
        "build-trial-replay-evidence",
        help="Build fail-closed weekly/monthly replay evidence from a trial evidence ledger.",
    )
    trial_replay.add_argument("--path", required=True, help="Existing trial evidence JSON.")
    trial_replay.add_argument("--generated-at", required=True, help="Replay evidence timestamp.")
    trial_replay.add_argument("--weekly-replay", action="store_true", help="Verify weekly replay coverage.")
    trial_replay.add_argument("--monthly-replay", action="store_true", help="Verify monthly replay coverage.")
    trial_replay.add_argument("--replay-ref", default="", help="Durable artifact, workflow, or Release ref for the replay evidence.")
    trial_replay.add_argument("--json", action="store_true", help="Print JSON replay evidence report.")

    trial_recovery = subparsers.add_parser(
        "build-trial-recovery-evidence",
        help="Build fail-closed recovery drill evidence from failed and recovered scheduled daily runs.",
    )
    trial_recovery.add_argument("--failure-execution", required=True, help="Failed, blocked, or degraded scheduled execution report JSON.")
    trial_recovery.add_argument("--recovery-execution", required=True, help="Recovered production-ready scheduled execution report JSON.")
    trial_recovery.add_argument("--generated-at", required=True, help="Recovery evidence timestamp.")
    trial_recovery.add_argument("--failure-ref", default="", help="Durable artifact, workflow, or Release ref for the failed execution.")
    trial_recovery.add_argument("--recovery-ref", default="", help="Durable artifact, workflow, or Release ref for the recovered execution.")
    trial_recovery.add_argument("--json", action="store_true", help="Print JSON recovery evidence report.")

    trial_resource = subparsers.add_parser(
        "build-trial-resource-evidence",
        help="Build fail-closed resource telemetry evidence from trial daily refs and production preflight reports.",
    )
    trial_resource.add_argument("--path", required=True, help="Existing trial evidence JSON.")
    trial_resource.add_argument("--preflight-report", action="append", default=[], help="Production preflight report JSON. Repeat for each daily resource ref.")
    trial_resource.add_argument("--generated-at", required=True, help="Resource evidence timestamp.")
    trial_resource.add_argument("--resource-ref", default="", help="Durable artifact, workflow, or Release ref for the resource evidence report.")
    trial_resource.add_argument("--json", action="store_true", help="Print JSON resource evidence report.")

    trial_start = subparsers.add_parser(
        "plan-trial-start",
        help="Build a fail-closed start-readiness gate for the real 30-day production trial.",
    )
    trial_start.add_argument("--preflight-report", required=True, help="Passing production preflight report JSON.")
    trial_start.add_argument("--bootstrap-plan", required=True, help="Passing trial bootstrap plan JSON.")
    trial_start.add_argument("--scheduler-plan", required=True, help="Passing production scheduler plan JSON.")
    trial_start.add_argument("--source-batch", required=True, help="Passing live arXiv source batch JSON.")
    trial_start.add_argument("--smtp-delivery", required=True, help="Real sent SMTP delivery report JSON.")
    trial_start.add_argument("--release-delivery", required=True, help="Real created Release delivery report JSON.")
    trial_start.add_argument("--generated-at", required=True, help="Trial start readiness timestamp.")
    trial_start.add_argument("--default-branch-ref", default="", help="Durable default-branch commit/workflow ref.")
    trial_start.add_argument("--runner-ref", default="", help="Durable private self-hosted runner ref.")
    trial_start.add_argument("--preflight-ref", default="", help="Durable archived production preflight ref.")
    trial_start.add_argument("--source-ingest-ref", default="", help="Durable archived live source ingest ref.")
    trial_start.add_argument("--smtp-ref", default="", help="Durable SMTP delivery ref matching the SMTP report.")
    trial_start.add_argument("--release-ref", default="", help="Durable Release ref matching the Release report.")
    trial_start.add_argument("--scheduler-ref", default="", help="Durable scheduled workflow/default-branch ref.")
    trial_start.add_argument("--trial-state-ref", default="", help="Durable initial trial ledger state ref.")
    trial_start.add_argument("--trial-start-ref", default="", help="Durable archived trial start gate ref.")
    trial_start.add_argument("--confirm-start", action="store_true", help="Explicitly confirm start-readiness evaluation.")
    trial_start.add_argument("--json", action="store_true", help="Print JSON trial start report.")

    trial_start_workflow = subparsers.add_parser(
        "plan-trial-start-workflow",
        help="Validate the manual GitHub workflow that collects trial start evidence.",
    )
    trial_start_workflow.add_argument("--path", default=".", help="Repository root path containing the workflow and runbook.")
    trial_start_workflow.add_argument("--generated-at", required=True, help="Workflow plan generation timestamp.")
    trial_start_workflow.add_argument("--json", action="store_true", help="Print JSON workflow plan.")

    production_refs = subparsers.add_parser(
        "plan-production-refs",
        help="Build a no-secret readiness report for external runner, SMTP secret, Release target, and workflow variable refs.",
    )
    production_refs.add_argument("--readiness-input", required=True, help="JSON file containing no-secret readiness metadata.")
    production_refs.add_argument("--generated-at", required=True, help="Production refs report timestamp.")
    production_refs.add_argument("--json", action="store_true", help="Print JSON production refs report.")

    production_launch = subparsers.add_parser(
        "plan-production-launch",
        help="Build a fail-closed launch readiness report before running the default-branch trial start workflow.",
    )
    production_launch.add_argument("--path", default=".", help="Repository root path containing the trial start workflow.")
    production_launch.add_argument("--pr-info", required=True, help="JSON metadata for the GitHub PR.")
    production_launch.add_argument("--generated-at", required=True, help="Launch readiness timestamp.")
    production_launch.add_argument("--expected-head-sha", required=True, help="Expected PR head SHA to bind the launch audit.")
    production_launch.add_argument("--default-branch-ref", default="", help="Durable merged default-branch commit ref.")
    production_launch.add_argument("--runner-ref", default="", help="Durable private self-hosted runner readiness ref.")
    production_launch.add_argument("--smtp-secret-ref", default="", help="Durable GitHub SMTP secrets readiness ref without secret values.")
    production_launch.add_argument("--release-target-ref", default="", help="Durable GitHub Release target readiness ref.")
    production_launch.add_argument("--workflow-vars-ref", default="", help="Durable GitHub variables readiness ref.")
    production_launch.add_argument("--trial-start-workflow-ref", default="", help="Durable default-branch trial start workflow ref.")
    production_launch.add_argument("--production-refs-report", default="", help="Optional passing plan-production-refs report used to fill external refs.")
    production_launch.add_argument("--confirm-launch", action="store_true", help="Explicitly confirm launch readiness evaluation.")
    production_launch.add_argument("--json", action="store_true", help="Print JSON launch readiness report.")

    preflight = subparsers.add_parser("preflight-production", help="Run fail-closed production preflight before scheduled execution.")
    preflight.add_argument("--path", default=".", help="Repository path used for disk, Git, and cache checks.")
    preflight.add_argument("--generated-at", required=True, help="Preflight report generation timestamp.")
    preflight.add_argument("--json", action="store_true", help="Print JSON preflight report.")

    bootstrap = subparsers.add_parser("plan-trial-bootstrap", help="Validate the manual production trial bootstrap workflow.")
    bootstrap.add_argument("--path", default=".", help="Repository root path containing the workflow and runbook.")
    bootstrap.add_argument("--generated-at", required=True, help="Bootstrap plan generation timestamp.")
    bootstrap.add_argument("--json", action="store_true", help="Print JSON bootstrap plan.")

    scheduler = subparsers.add_parser("plan-production-scheduler", help="Validate the scheduled production workflow gate.")
    scheduler.add_argument("--path", default=".", help="Repository root path containing the scheduled workflow and runbook.")
    scheduler.add_argument("--generated-at", required=True, help="Scheduler plan generation timestamp.")
    scheduler.add_argument("--json", action="store_true", help="Print JSON scheduler plan.")

    scheduled = subparsers.add_parser("run-scheduled-production", help="Run one fail-closed scheduled production mode.")
    scheduled.add_argument("--mode", required=True, choices=SCHEDULED_EXECUTION_MODES, help="Scheduled mode to run.")
    scheduled.add_argument("--generated-at", required=True, help="Scheduled execution timestamp.")
    scheduled.add_argument("--preflight-report", required=True, help="JSON report from preflight-production.")
    scheduled.add_argument("--daily-input", help="Daily input package for daily-run mode.")
    scheduled.add_argument("--release-asset", action="append", default=[], help="Release asset path for daily-run mode.")
    scheduled.add_argument("--previous-execution-report", help="Previous daily execution report for watchdog mode.")
    scheduled.add_argument("--json", action="store_true", help="Print JSON scheduled execution report.")
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
    if args.command == "send-notification":
        email = render_email(
            args.status,
            args.run_id,
            args.summary,
            date=args.date,
            phase=args.phase,
            stage=args.stage,
            claim_gate=args.claim_gate,
            next_action=args.next_action,
        )
        report = deliver_notification(email, generated_at=args.generated_at, allow_send=args.allow_send)
        errors = validate_smtp_delivery_report(report)
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
            print(f"{report['delivery_id']}\t{report['status']}")
        return 0 if report["status"] in {"dry_run", "sent"} else 2
    if args.command == "publish-release":
        notes = Path(args.notes_file).read_text(encoding="utf-8") if args.notes_file else args.notes
        report = deliver_release(
            tag=args.tag,
            title=args.title,
            notes=notes,
            asset_paths=args.asset,
            generated_at=args.generated_at,
            target=args.target,
            repo=args.repo,
            draft=not args.publish,
            allow_upload=args.allow_upload,
        )
        errors = validate_release_delivery_report(report)
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
            print(f"{report['delivery_id']}\t{report['status']}")
        return 0 if report["status"] in {"dry_run", "created"} else 2
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
    if args.command == "fetch-arxiv-latest":
        batch = ingest_latest_arxiv(
            search_query=args.query,
            generated_at=args.generated_at,
            max_results=args.max_results,
            start=args.start,
            seen_source_ids=args.seen_source_id,
        )
        errors = validate_source_batch(batch)
        if errors:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": errors}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(batch, ensure_ascii=False, indent=2, sort_keys=True))
        elif batch["new_items"]:
            for item in batch["new_items"]:
                print(f"{item['source_id']}\t{item['title']}")
        else:
            print(batch["status"])
            for reason in batch["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if batch["status"] == "pass" else 2
    if args.command == "build-daily-input":
        source_batch = load_json_mapping(args.source_batch)
        report = build_daily_input_package(
            source_batch,
            date=args.date,
            generated_at=args.generated_at,
            timezone=args.timezone,
            recent_source_ids=args.recent_source_id,
        )
        errors = validate_daily_input_report(report)
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
        elif report["daily_input_ready"]:
            daily_input = report["daily_input"]
            print(f"{daily_input['run_id']}\t{daily_input['source_item']['source_id']}")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["daily_input_ready"] else 2
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
    if args.command == "update-trial-ledger":
        existing = load_json_mapping(args.path) if args.path else None
        scheduled_report = load_json_mapping(args.scheduled_execution)
        report = update_trial_evidence_ledger(
            existing,
            scheduled_report,
            generated_at=args.generated_at,
            trial_id=args.trial_id,
            trial_ref=args.trial_ref,
            expected_days=args.expected_days,
            text_degradation_path_verified=args.text_degradation_verified,
            video_degradation_path_verified=args.video_degradation_verified,
            scheduler_enabled=args.scheduler_enabled,
            manual_rerun_verified=args.manual_rerun_verified,
            scheduler_ref=args.scheduler_ref,
            private_release_verified=args.private_release_verified,
            release_ref=args.release_ref,
            real_smtp_verified=args.real_smtp_verified,
            email_ref=args.email_ref,
            resource_pressure_ok=args.resource_pressure_ok,
            resource_ref=args.resource_ref,
            weekly_replay_verified=args.weekly_replay_verified,
            monthly_replay_verified=args.monthly_replay_verified,
            weekly_monthly_ref=args.weekly_monthly_ref,
            recovery_drill_verified=args.recovery_drill_verified,
            recovery_ref=args.recovery_ref,
        )
        errors = validate_trial_ledger_update_report(report)
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
        elif report["ledger_updated"]:
            print(f"{report['ledger_update_id']}\t{report['observed_day_count']} days")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["ledger_updated"] else 2
    if args.command == "export-trial-ledger-state":
        report = load_json_mapping(args.ledger_update)
        errors = validate_trial_ledger_update_report(report)
        if report.get("ledger_updated") is not True:
            errors.extend(str(reason) for reason in report.get("blocking_reasons") or ["trial ledger update did not append evidence"])
        evidence = report.get("trial_evidence")
        if not isinstance(evidence, dict):
            errors.append("trial ledger update report requires trial_evidence object")
        if errors:
            payload = {"status": "blocked", "errors": errors}
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{evidence.get('trial_id', 'trial:unknown')}\t{len(evidence.get('daily_runs') or [])} days")
        return 0
    if args.command == "annotate-trial-ops-evidence":
        evidence = load_json_mapping(args.path)
        report = annotate_trial_operational_evidence(
            evidence,
            generated_at=args.generated_at,
            trial_id=args.trial_id,
            trial_ref=args.trial_ref,
            expected_days=args.expected_days,
            scheduler_enabled=args.scheduler_enabled,
            manual_rerun_verified=args.manual_rerun_verified,
            scheduler_ref=args.scheduler_ref,
            private_release_verified=args.private_release_verified,
            release_ref=args.release_ref,
            real_smtp_verified=args.real_smtp_verified,
            email_ref=args.email_ref,
            resource_pressure_ok=args.resource_pressure_ok,
            resource_ref=args.resource_ref,
            weekly_replay_verified=args.weekly_replay_verified,
            monthly_replay_verified=args.monthly_replay_verified,
            weekly_monthly_ref=args.weekly_monthly_ref,
            recovery_drill_verified=args.recovery_drill_verified,
            recovery_ref=args.recovery_ref,
        )
        errors = validate_trial_ops_report(report)
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
        elif report["trial_evidence_updated"]:
            print(f"{report['ops_update_id']}\t{report['observed_day_count']} days")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["trial_evidence_updated"] else 2
    if args.command == "export-trial-ops-state":
        report = load_json_mapping(args.ops_update)
        errors = validate_trial_ops_report(report)
        if report.get("trial_evidence_updated") is not True:
            errors.extend(str(reason) for reason in report.get("blocking_reasons") or ["trial ops annotation did not update evidence"])
        evidence = report.get("trial_evidence")
        if not isinstance(evidence, dict):
            errors.append("trial ops annotation report requires trial_evidence object")
        if errors:
            payload = {"status": "blocked", "errors": errors}
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"{evidence.get('trial_id', 'trial:unknown')}\t{len(evidence.get('daily_runs') or [])} days")
        return 0
    if args.command == "build-trial-replay-evidence":
        evidence = load_json_mapping(args.path)
        report = build_trial_replay_evidence(
            evidence,
            generated_at=args.generated_at,
            weekly_replay=args.weekly_replay,
            monthly_replay=args.monthly_replay,
            replay_ref=args.replay_ref,
        )
        errors = validate_trial_replay_report(report)
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
        elif report["replay_evidence_verified"]:
            modes = ",".join(mode for mode, enabled in report["requested_replay_modes"].items() if enabled)
            print(f"{report['replay_report_id']}\t{modes}")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["replay_evidence_verified"] else 2
    if args.command == "build-trial-recovery-evidence":
        failure_report = load_json_mapping(args.failure_execution)
        recovery_report = load_json_mapping(args.recovery_execution)
        report = build_trial_recovery_evidence(
            failure_report,
            recovery_report,
            generated_at=args.generated_at,
            failure_ref=args.failure_ref,
            recovery_ref=args.recovery_ref,
        )
        errors = validate_trial_recovery_report(report)
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
        elif report["recovery_drill_verified"]:
            print(f"{report['recovery_report_id']}\t{report['recovery_ref']}")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["recovery_drill_verified"] else 2
    if args.command == "build-trial-resource-evidence":
        evidence = load_json_mapping(args.path)
        preflight_reports = [load_json_mapping(path) for path in args.preflight_report]
        report = build_trial_resource_evidence(
            evidence,
            preflight_reports,
            generated_at=args.generated_at,
            resource_ref=args.resource_ref,
        )
        errors = validate_trial_resource_report(report)
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
        elif report["resource_pressure_verified"]:
            print(f"{report['resource_report_id']}\t{report['resource_evidence_ref']}")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["resource_pressure_verified"] else 2
    if args.command == "plan-trial-start":
        report = build_trial_start_gate(
            generated_at=args.generated_at,
            preflight_report=load_json_mapping(args.preflight_report),
            bootstrap_plan=load_json_mapping(args.bootstrap_plan),
            scheduler_plan=load_json_mapping(args.scheduler_plan),
            source_batch=load_json_mapping(args.source_batch),
            smtp_delivery_report=load_json_mapping(args.smtp_delivery),
            release_delivery_report=load_json_mapping(args.release_delivery),
            default_branch_ref=args.default_branch_ref,
            runner_ref=args.runner_ref,
            preflight_ref=args.preflight_ref,
            source_ingest_ref=args.source_ingest_ref,
            smtp_ref=args.smtp_ref,
            release_ref=args.release_ref,
            scheduler_ref=args.scheduler_ref,
            trial_state_ref=args.trial_state_ref,
            trial_start_ref=args.trial_start_ref,
            confirm_start=args.confirm_start,
        )
        errors = validate_trial_start_report(report)
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
        elif report["trial_start_ready"]:
            print(f"{report['trial_start_report_id']}\tready")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["trial_start_ready"] else 2
    if args.command == "plan-trial-start-workflow":
        plan = build_trial_start_workflow_plan(Path(args.path), generated_at=args.generated_at)
        errors = validate_trial_start_workflow_plan(plan)
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
        return 0 if plan["trial_start_workflow_ready"] else 2
    if args.command == "plan-production-refs":
        report = build_production_refs_report(
            load_json_mapping(args.readiness_input),
            generated_at=args.generated_at,
        )
        errors = validate_production_refs_report(report)
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
        elif report["production_refs_ready"]:
            print(f"{report['refs_report_id']}\tready")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["production_refs_ready"] else 2
    if args.command == "plan-production-launch":
        launch_refs = {
            "runner_ref": args.runner_ref,
            "smtp_secret_ref": args.smtp_secret_ref,
            "release_target_ref": args.release_target_ref,
            "workflow_vars_ref": args.workflow_vars_ref,
        }
        if args.production_refs_report:
            refs_report = load_json_mapping(args.production_refs_report)
            refs_errors = validate_production_refs_report(refs_report)
            if refs_errors or refs_report.get("production_refs_ready") is not True:
                errors = refs_errors or ["production refs report is not ready"]
                if args.json:
                    print(json.dumps({"status": "blocked", "errors": errors}, ensure_ascii=False, indent=2, sort_keys=True))
                else:
                    print("blocked")
                    for error in errors:
                        print(f"- {error}")
                return 2
            report_refs = refs_report.get("readiness_refs")
            if isinstance(report_refs, dict):
                for key in launch_refs:
                    if not launch_refs[key]:
                        launch_refs[key] = str(report_refs.get(key) or "")
        report = build_production_launch_readiness(
            Path(args.path),
            generated_at=args.generated_at,
            pr_info=load_json_mapping(args.pr_info),
            expected_head_sha=args.expected_head_sha,
            default_branch_ref=args.default_branch_ref,
            runner_ref=launch_refs["runner_ref"],
            smtp_secret_ref=launch_refs["smtp_secret_ref"],
            release_target_ref=launch_refs["release_target_ref"],
            workflow_vars_ref=launch_refs["workflow_vars_ref"],
            trial_start_workflow_ref=args.trial_start_workflow_ref,
            confirm_launch=args.confirm_launch,
        )
        errors = validate_production_launch_readiness(report)
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
        elif report["production_launch_ready"]:
            print(f"{report['launch_readiness_id']}\tready")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["production_launch_ready"] else 2
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
    if args.command == "plan-production-scheduler":
        plan = build_production_scheduler_plan(Path(args.path), generated_at=args.generated_at)
        errors = validate_production_scheduler_plan(plan)
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
        return 0 if plan["scheduler_contract_ready"] else 2
    if args.command == "run-scheduled-production":
        preflight_report = load_json_mapping(args.preflight_report)
        daily_input = load_json_mapping(args.daily_input) if args.daily_input else None
        previous = load_json_mapping(args.previous_execution_report) if args.previous_execution_report else None
        report = run_scheduled_execution(
            mode=args.mode,
            generated_at=args.generated_at,
            preflight_report=preflight_report,
            daily_input=daily_input,
            daily_input_path=args.daily_input,
            release_asset_paths=args.release_asset,
            previous_execution_report=previous,
        )
        errors = validate_scheduled_execution_report(report)
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
            print(f"{report['execution_id']}\t{report['status']}")
        return int(report["exit_code"])
    raise AssertionError(f"Unhandled command: {args.command}")
