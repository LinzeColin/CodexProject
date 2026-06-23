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
from .global_scan import (
    ALL_ARXIV_MAX_RESULTS_PER_CATEGORY,
    LIVE_ARXIV_TRANSIENT_RETRY_COUNT,
    LIVE_ARXIV_TRANSIENT_RETRY_DELAY_SECONDS,
    build_all_arxiv_daily_input,
    build_live_all_arxiv_dry_run,
    build_all_arxiv_scan_plan,
    validate_all_arxiv_daily_input_report,
    validate_live_all_arxiv_dry_run_report,
    validate_all_arxiv_scan_plan,
)
from .handoff import HandoffError, build_handoff, validate_handoff
from .lesson import LessonGenerationError, generate_lesson
from .narration import NarrationError, generate_narration_plan
from .notifications import render_email
from .owner_controls import (
    build_owner_impact_preview,
    load_owner_controls,
    render_owner_documents,
    validate_owner_controls,
)
from .pipeline import PipelineError, run_daily_dry_run
from .production_launch import build_production_launch_readiness, validate_production_launch_readiness
from .production_preflight import build_production_preflight, validate_production_preflight
from .production_refs import (
    DEFAULT_GITHUB_REPO,
    ProductionRefsDiscoveryError,
    build_production_refs_input_template,
    build_production_refs_report,
    build_provisioning_audit_review,
    discover_production_refs_input_with_gh,
    validate_production_refs_report,
    validate_provisioning_audit_review,
)
from .production_scheduler import build_production_scheduler_plan, validate_production_scheduler_plan
from .ranking import selection_payload
from .release_delivery import DEFAULT_RELEASE_REPO, deliver_release, validate_release_delivery_report
from .scheduled_execution import (
    SCHEDULED_EXECUTION_MODES,
    load_json_mapping,
    run_scheduled_execution,
    validate_scheduled_execution_report,
)
from .simulation import run_two_day_simulation, validate_two_day_simulation_report
from .source_ingest import ingest_latest_arxiv, validate_source_batch
from .source_registry import (
    build_source_registry_report,
    load_source_registry_controls,
    validate_source_registry_report,
)
from .smtp_delivery import deliver_notification, validate_smtp_delivery_report
from .stage1_b1_report import build_b1_report_email_package, validate_b1_report_email_package
from .stage1_bootstrap import build_stage1_bootstrap_report, validate_stage1_bootstrap_report
from .stage1_historical_previews import (
    build_historical_b1_previews,
    build_historical_b1_previews_report,
    load_historical_daily_inputs,
    validate_historical_b1_previews,
)
from .stage1_real_replay import (
    build_real_historical_arxiv_replay,
    fetch_atom_with_curl,
    fetch_atom_with_urllib,
    validate_real_historical_arxiv_replay_report,
)
from .stage1_accelerated_acceptance import (
    build_stage1_accelerated_acceptance_report,
    validate_stage1_accelerated_acceptance_report,
)
from .stage1_migration import build_migration_package, validate_stage1_migration_report, verify_migration_package
from .stage1_queue import build_stage1_queue_report, validate_stage1_queue_report
from .stage1_runtime import (
    STAGE1_RUNTIME_SUPPORTED_SCHEDULER_PLATFORMS,
    build_runtime_audit,
    build_scheduler_plan,
    create_runtime_backup,
    restore_runtime_backup,
    run_tick,
    run_watchdog,
    validate_stage1_runtime_report,
)
from .storage import (
    inspect_database,
    migrate_database,
    rollback_database,
    validate_storage_report,
)
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
from .video import render_lightweight_mp4, validate_mp4_render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adp", description="arXiv Daily Push CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Print package version.")

    owner = subparsers.add_parser("owner", help="Validate owner controls and generate owner-readable views.")
    owner_subparsers = owner.add_subparsers(dest="owner_command", required=True)
    owner_validate = owner_subparsers.add_parser("validate", help="Validate config/owner_controls.yaml.")
    owner_validate.add_argument("--controls", help="Path to owner_controls.yaml.")
    owner_validate.add_argument("--json", action="store_true", help="Print JSON validation output.")

    owner_preview = owner_subparsers.add_parser("preview-impact", help="Preview owner_controls impact without side effects.")
    owner_preview.add_argument("--controls", help="Path to owner_controls.yaml.")
    owner_preview.add_argument("--days", type=int, default=30, help="Replay window to describe.")
    owner_preview.add_argument("--json", action="store_true", help="Print JSON impact output.")

    owner_render = owner_subparsers.add_parser("render-docs", help="Render generated docs/owner files from owner_controls.yaml.")
    owner_render.add_argument("--controls", help="Path to owner_controls.yaml.")
    owner_render.add_argument("--project-path", default="", help="Project root that receives docs/owner files.")
    owner_render.add_argument("--generated-at", default="2026-06-22T00:00:00+10:00", help="Timestamp written to generated docs.")
    owner_render.add_argument("--write", action="store_true", help="Write generated owner docs to disk.")
    owner_render.add_argument("--json", action="store_true", help="Print JSON render output.")

    storage = subparsers.add_parser("storage", help="Manage the local SQLite/WAL/FTS5 document store.")
    storage_subparsers = storage.add_subparsers(dest="storage_command", required=True)
    storage_migrate = storage_subparsers.add_parser("migrate", help="Create or migrate the local SQLite store.")
    storage_migrate.add_argument("--db", required=True, help="SQLite database path.")
    storage_migrate.add_argument("--json", action="store_true", help="Print JSON storage report.")
    storage_inspect = storage_subparsers.add_parser("inspect", help="Inspect the local SQLite store.")
    storage_inspect.add_argument("--db", required=True, help="SQLite database path.")
    storage_inspect.add_argument("--json", action="store_true", help="Print JSON storage report.")
    storage_rollback = storage_subparsers.add_parser("rollback", help="Rollback the S1-04 local SQLite schema.")
    storage_rollback.add_argument("--db", required=True, help="SQLite database path.")
    storage_rollback.add_argument("--target-version", type=int, default=0, help="Rollback target schema version.")
    storage_rollback.add_argument("--json", action="store_true", help="Print JSON storage report.")

    source_registry = subparsers.add_parser(
        "source-registry",
        help="Validate the Stage 1 source registry and connector contract.",
    )
    source_registry.add_argument("--controls", help="Path to owner_controls.yaml.")
    source_registry.add_argument("--fixture-atom", help="Optional offline arXiv Atom fixture to validate.")
    source_registry.add_argument("--generated-at", required=True, help="Registry report timestamp.")
    source_registry.add_argument("--json", action="store_true", help="Print JSON registry report.")

    stage1_queue = subparsers.add_parser(
        "stage1-queue",
        help="Build and validate the Review8 Stage 1 scoring, 10,000 queue, and content ledger report.",
    )
    stage1_queue.add_argument("--input", required=True, help="JSON file containing items or an object with an items array.")
    stage1_queue.add_argument("--controls", help="Path to owner_controls.yaml.")
    stage1_queue.add_argument("--as-of-date", required=True, help="Queue date in YYYY-MM-DD form.")
    stage1_queue.add_argument("--generated-at", required=True, help="Queue report timestamp.")
    stage1_queue.add_argument("--run-id", default="stage1-queue-fixture", help="Run ID written to content ledger rows.")
    stage1_queue.add_argument("--json", action="store_true", help="Print JSON queue report.")

    b1_report = subparsers.add_parser(
        "build-b1-report-email",
        help="Build the V5 Stage 1 B1/arXiv Chinese report and email preview artifacts.",
    )
    b1_report.add_argument("--daily-input", required=True, help="Daily input builder report or daily_input JSON.")
    b1_report.add_argument("--generated-at", required=True, help="Report/email artifact timestamp.")
    b1_report.add_argument("--recipient", default="linzezhang35@gmail.com", help="Dry-run email recipient.")
    b1_report.add_argument("--artifact-dir", help="Directory for Markdown, HTML, and JSON artifacts.")
    b1_report.add_argument("--write", action="store_true", help="Write report/email/audit artifacts to --artifact-dir.")
    b1_report.add_argument("--json", action="store_true", help="Print JSON report/email package.")

    historical_previews = subparsers.add_parser(
        "historical-b1-previews",
        help="Build the S1-11 30-sample historical B1/arXiv report and email preview evidence package.",
    )
    historical_previews.add_argument("--input", help="Optional JSON array, JSONL, or object with daily_inputs.")
    historical_previews.add_argument("--generated-at", required=True, help="Preview report timestamp.")
    historical_previews.add_argument("--start-date", default="2026-05-01", help="First historical local date.")
    historical_previews.add_argument("--count", type=int, default=30, help="Number of historical previews to build.")
    historical_previews.add_argument("--recipient", default="linzezhang35@gmail.com", help="Dry-run email recipient.")
    historical_previews.add_argument("--artifact-dir", help="Directory for preview artifacts and manifest.")
    historical_previews.add_argument("--write", action="store_true", help="Write preview artifacts to --artifact-dir.")
    historical_previews.add_argument("--json", action="store_true", help="Print JSON S1-11 preview report.")

    real_replay = subparsers.add_parser(
        "real-historical-arxiv-replay",
        help="Backfill 30 historical as-of dates with real arXiv Atom data and Stage 1 text artifacts.",
    )
    real_replay.add_argument("--generated-at", required=True, help="Replay evidence generation timestamp.")
    real_replay.add_argument("--start-date", help="First historical as-of date. Defaults from --end-date/--count.")
    real_replay.add_argument("--end-date", help="Last historical as-of date. Defaults to generated-at date.")
    real_replay.add_argument("--count", type=int, default=30, help="Number of as-of dates to replay.")
    real_replay.add_argument("--lookback-days", type=int, default=7, help="Trailing submittedDate window per as-of date.")
    real_replay.add_argument("--max-results", type=int, default=10, help="Max real arXiv Atom results per as-of date.")
    real_replay.add_argument("--recipient", default="linzezhang35@gmail.com", help="Dry-run email recipient.")
    real_replay.add_argument("--artifact-dir", help="Directory for compact replay artifacts.")
    real_replay.add_argument("--write", action="store_true", help="Write compact replay artifacts to --artifact-dir.")
    real_replay.add_argument("--fetcher", choices=("curl", "urllib"), default="curl", help="Real arXiv fetch implementation.")
    real_replay.add_argument("--polite-delay-seconds", type=float, default=3.0, help="Delay between arXiv API calls.")
    real_replay.add_argument("--json", action="store_true", help="Print JSON real replay report.")

    runtime_audit = subparsers.add_parser("runtime-audit", help="Audit Stage 1 local runtime readiness without side effects.")
    runtime_audit.add_argument("--state-dir", required=True, help="Explicit local runtime state directory.")
    runtime_audit.add_argument("--db", help="Optional Stage 1 SQLite database path to inspect.")
    runtime_audit.add_argument("--generated-at", required=True, help="Audit timestamp.")
    runtime_audit.add_argument("--json", action="store_true", help="Print JSON runtime audit report.")

    tick = subparsers.add_parser("tick", help="Run the Stage 1 local tick control and write heartbeat/checkpoint state.")
    tick.add_argument("--state-dir", required=True, help="Explicit local runtime state directory.")
    tick.add_argument("--generated-at", required=True, help="Tick timestamp.")
    tick.add_argument("--no-write", action="store_true", help="Dry-run the tick without writing heartbeat/checkpoint files.")
    tick.add_argument("--json", action="store_true", help="Print JSON tick report.")

    watchdog = subparsers.add_parser("watchdog", help="Check Stage 1 local heartbeat and lock freshness.")
    watchdog.add_argument("--state-dir", required=True, help="Explicit local runtime state directory.")
    watchdog.add_argument("--generated-at", required=True, help="Watchdog timestamp.")
    watchdog.add_argument("--json", action="store_true", help="Print JSON watchdog report.")

    backup = subparsers.add_parser("backup", help="Create a small Stage 1 SQLite/config backup with a SHA256 manifest.")
    backup.add_argument("--db", required=True, help="Stage 1 SQLite database path.")
    backup.add_argument("--backup-dir", required=True, help="Directory that receives the backup folder.")
    backup.add_argument("--generated-at", required=True, help="Backup timestamp.")
    backup.add_argument("--include-path", action="append", default=[], help="Small supporting file to include. May be repeated.")
    backup.add_argument("--json", action="store_true", help="Print JSON backup report.")

    restore = subparsers.add_parser("restore", help="Restore a Stage 1 SQLite backup to an explicit target path.")
    restore.add_argument("--manifest", required=True, help="backup_manifest.json path.")
    restore.add_argument("--target-db", required=True, help="Explicit restore target database path.")
    restore.add_argument("--generated-at", required=True, help="Restore timestamp.")
    restore.add_argument("--confirm-restore", action="store_true", help="Required confirmation for restore writes.")
    restore.add_argument("--allow-overwrite", action="store_true", help="Allow replacing an existing target database.")
    restore.add_argument("--json", action="store_true", help="Print JSON restore report.")

    scheduler = subparsers.add_parser("scheduler", help="Build Stage 1 OS-native scheduler dry-run templates.")
    scheduler_subparsers = scheduler.add_subparsers(dest="scheduler_command", required=True)
    for scheduler_action in ("install", "uninstall"):
        scheduler_parser = scheduler_subparsers.add_parser(scheduler_action, help=f"Build scheduler {scheduler_action} dry-run templates.")
        scheduler_parser.add_argument("--platform", choices=STAGE1_RUNTIME_SUPPORTED_SCHEDULER_PLATFORMS, required=True)
        scheduler_parser.add_argument("--project-root", default=".", help="Repository root used in generated templates.")
        scheduler_parser.add_argument("--state-dir", required=True, help="Explicit local runtime state directory.")
        scheduler_parser.add_argument("--generated-at", required=True, help="Template generation timestamp.")
        scheduler_parser.add_argument("--artifact-dir", help="Directory for template files when --write is used.")
        scheduler_parser.add_argument("--write", action="store_true", help="Write template files only; never install them.")
        scheduler_parser.add_argument("--json", action="store_true", help="Print JSON scheduler report.")

    migration = subparsers.add_parser("migration", help="Build or verify the Stage 1 low-resource migration package.")
    migration_subparsers = migration.add_subparsers(dest="migration_command", required=True)
    migration_export = migration_subparsers.add_parser("export", help="Export the Stage 1 migration package.")
    migration_export.add_argument("--project-root", default=".", help="Repository root used for source-file inventory.")
    migration_export.add_argument("--db", required=True, help="Migrated Stage 1 SQLite database path.")
    migration_export.add_argument("--output-dir", required=True, help="Directory that receives the migration package.")
    migration_export.add_argument("--generated-at", required=True, help="Migration package timestamp.")
    migration_export.add_argument("--include-path", action="append", default=[], help="Small supporting file to include in the backup. May be repeated.")
    migration_export.add_argument("--required-path", action="append", default=[], help="Required source path relative to project root. May be repeated.")
    migration_export.add_argument("--no-write", action="store_true", help="Validate the export without writing package files.")
    migration_export.add_argument("--json", action="store_true", help="Print JSON migration export report.")
    migration_verify = migration_subparsers.add_parser("verify", help="Verify a Stage 1 migration package manifest.")
    migration_verify.add_argument("--manifest", required=True, help="migration_manifest.json path.")
    migration_verify.add_argument("--generated-at", required=True, help="Verification timestamp.")
    migration_verify.add_argument("--json", action="store_true", help="Print JSON migration verification report.")

    post_migration_bootstrap = subparsers.add_parser(
        "post-migration-bootstrap",
        help="Verify the Stage 1 target machine or GitHub-hosted cloud runner bootstrap boundary.",
    )
    post_migration_bootstrap.add_argument("--project-root", default=".", help="Repository root to validate as a Git checkout.")
    post_migration_bootstrap.add_argument("--migration-manifest", required=True, help="S1-09 migration_manifest.json to verify before bootstrap.")
    post_migration_bootstrap.add_argument("--state-dir", required=True, help="Explicit runtime state directory for low-resource smoke.")
    post_migration_bootstrap.add_argument("--db", required=True, help="SQLite database path to create or inspect.")
    post_migration_bootstrap.add_argument("--generated-at", required=True, help="Bootstrap report timestamp.")
    post_migration_bootstrap.add_argument(
        "--target-environment",
        choices=("github_actions_cloud_runner", "new_machine"),
        default="github_actions_cloud_runner",
    )
    post_migration_bootstrap.add_argument("--workflow-path", help="Optional GitHub Actions workflow path to verify.")
    post_migration_bootstrap.add_argument("--require-github-actions", action="store_true", help="Require GitHub-hosted cloud runner evidence.")
    post_migration_bootstrap.add_argument("--require-network-probe", action="store_true", help="Run one lightweight HTTPS arXiv API probe.")
    post_migration_bootstrap.add_argument("--require-secret-presence", action="store_true", help="Require SMTP secret env names to be present without printing values.")
    post_migration_bootstrap.add_argument("--json", action="store_true", help="Print JSON bootstrap report.")

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

    all_arxiv_plan = subparsers.add_parser("plan-all-arxiv-scan", help="Print the Phase 12 all-arXiv scan plan.")
    all_arxiv_plan.add_argument("--max-results-per-category", type=int, default=ALL_ARXIV_MAX_RESULTS_PER_CATEGORY)
    all_arxiv_plan.add_argument("--json", action="store_true", help="Print JSON scan plan.")

    all_arxiv_daily = subparsers.add_parser(
        "build-all-arxiv-daily-input",
        help="Build Phase 12 all-arXiv daily input with ROI ranking and candidate queue.",
    )
    all_arxiv_daily.add_argument("--date", required=True, help="Daily publication date in YYYY-MM-DD form.")
    all_arxiv_daily.add_argument("--generated-at", required=True, help="Builder timestamp used for evidence claims.")
    all_arxiv_daily.add_argument("--timezone", default="Australia/Sydney", help="Daily run timezone.")
    all_arxiv_daily.add_argument("--queue-path", help="Existing candidate queue JSON. Missing path starts an empty queue.")
    all_arxiv_daily.add_argument("--queue-output", help="Path to write updated candidate queue JSON.")
    all_arxiv_daily.add_argument("--artifact-dir", help="Directory for daily input, queue, video artifact, and email brief JSON.")
    all_arxiv_daily.add_argument("--recent-source-id", action="append", default=[], help="Source ID already selected recently.")
    all_arxiv_daily.add_argument("--max-results-per-category", type=int, default=ALL_ARXIV_MAX_RESULTS_PER_CATEGORY)
    all_arxiv_daily.add_argument("--polite-delay-seconds", type=float, default=0.0, help="Optional delay between live archive fetches.")
    all_arxiv_daily.add_argument("--transient-retry-count", type=int, default=LIVE_ARXIV_TRANSIENT_RETRY_COUNT)
    all_arxiv_daily.add_argument("--transient-retry-delay-seconds", type=float, default=LIVE_ARXIV_TRANSIENT_RETRY_DELAY_SECONDS)
    all_arxiv_daily.add_argument("--json", action="store_true", help="Print JSON Phase 12 daily input report.")

    live_all_arxiv = subparsers.add_parser(
        "run-live-all-arxiv-dry-run",
        help="Fetch every arXiv primary archive once and fail closed unless all 20 archive buckets are reachable.",
    )
    live_all_arxiv.add_argument("--generated-at", required=True, help="Dry-run timestamp.")
    live_all_arxiv.add_argument("--date", default="", help="Daily input date for the live-selected sample paper.")
    live_all_arxiv.add_argument("--max-results-per-category", type=int, default=1)
    live_all_arxiv.add_argument("--artifact-dir", help="Directory for the live all-arXiv dry-run report.")
    live_all_arxiv.add_argument("--polite-delay-seconds", type=float, default=0.0, help="Optional delay between archive fetches.")
    live_all_arxiv.add_argument("--json", action="store_true", help="Print JSON dry-run report.")

    accelerated_acceptance = subparsers.add_parser(
        "build-stage1-accelerated-acceptance",
        help="Build Stage 1 accelerated real-arXiv acceptance evidence without production side effects.",
    )
    accelerated_acceptance.add_argument("--live-dry-run", required=True, help="Passing live all-arXiv dry-run report JSON.")
    accelerated_acceptance.add_argument("--controlled-smtp-manifest", required=True, help="Controlled SMTP evidence manifest JSON.")
    accelerated_acceptance.add_argument("--generated-at", required=True, help="Evidence generation timestamp.")
    accelerated_acceptance.add_argument("--expected-samples", type=int, default=30)
    accelerated_acceptance.add_argument("--live-dry-run-ref", default="")
    accelerated_acceptance.add_argument("--controlled-smtp-ref", default="")
    accelerated_acceptance.add_argument("--scheduler-ref", default=".github/workflows/arxiv-daily-push-scheduled.yml")
    accelerated_acceptance.add_argument("--resource-ref", default="")
    accelerated_acceptance.add_argument("--recovery-ref", default="governance/run_manifests/ADP-S1-08-LOCAL-RUNTIME-RECOVERY-20260622.json")
    accelerated_acceptance.add_argument("--artifact-dir", help="Directory for accelerated acceptance artifacts.")
    accelerated_acceptance.add_argument("--json", action="store_true", help="Print JSON accelerated acceptance report.")

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

    mp4 = subparsers.add_parser("render-lightweight-mp4", help="Render a lightweight real MP4 video artifact from a daily input JSON.")
    mp4.add_argument("--daily-input", required=True, help="Daily input JSON or Phase 12 daily input report JSON.")
    mp4.add_argument("--output", required=True, help="Output .mp4 path.")
    mp4.add_argument("--generated-at", required=True, help="MP4 render timestamp.")
    mp4.add_argument("--duration-seconds", type=int, default=12)
    mp4.add_argument("--json", action="store_true", help="Print JSON MP4 render evidence.")

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

    trial = subparsers.add_parser("evaluate-trial", help="Evaluate 30 unique-date operational evidence coverage for Phase 11 acceptance.")
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
    trial_ledger.add_argument("--text-artifacts-verified", action="store_true")
    trial_ledger.add_argument("--text-artifact-ref", default="")
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
    trial_ops.add_argument("--text-artifacts-verified", action="store_true")
    trial_ops.add_argument("--text-artifact-ref", default="")
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
    trial_start.add_argument("--source-batch", required=True, help="Passing live SourceBatch or Phase 12 all-arXiv daily input JSON.")
    trial_start.add_argument("--smtp-delivery", required=True, help="Real sent SMTP delivery report JSON.")
    trial_start.add_argument("--release-delivery", help="Legacy optional Release delivery report JSON.")
    trial_start.add_argument("--generated-at", required=True, help="Trial start readiness timestamp.")
    trial_start.add_argument("--default-branch-ref", default="", help="Durable default-branch commit/workflow ref.")
    trial_start.add_argument("--runner-ref", default="", help="Durable GitHub-hosted runner ref.")
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

    production_refs_template = subparsers.add_parser(
        "print-production-refs-template",
        help="Print a no-secret JSON input template for plan-production-refs.",
    )
    production_refs_template.add_argument("--runner-label", default="ubuntu-latest", help="GitHub-hosted runner label placeholder.")

    production_refs_discovery = subparsers.add_parser(
        "discover-production-refs",
        help="Use gh to discover no-secret GitHub Actions metadata and build a production refs report.",
    )
    production_refs_discovery.add_argument("--repo", default=DEFAULT_GITHUB_REPO, help="GitHub repo owner/name.")
    production_refs_discovery.add_argument("--runner-label", default="arxiv-daily-push", help="Legacy self-hosted runner label for metadata discovery.")
    production_refs_discovery.add_argument("--generated-at", required=True, help="Production refs report timestamp.")
    production_refs_discovery.add_argument("--gh-command", default="gh", help="gh executable name or path.")
    production_refs_discovery.add_argument("--json", action="store_true", help="Print JSON production refs report.")

    provisioning_audit_review = subparsers.add_parser(
        "review-provisioning-audit",
        help="Review a no-secret provisioning audit artifact before trial-start dispatch.",
    )
    provisioning_audit_review.add_argument("--production-refs-report", required=True, help="Downloaded adp-production-provisioning-audit JSON report.")
    provisioning_audit_review.add_argument("--workflow-run-ref", default="", help="Durable GitHub Actions workflow run ref for the audit.")
    provisioning_audit_review.add_argument("--artifact-ref", default="", help="Durable artifact ref for adp-production-provisioning-audit.")
    provisioning_audit_review.add_argument("--generated-at", required=True, help="Provisioning audit review timestamp.")
    provisioning_audit_review.add_argument("--json", action="store_true", help="Print JSON provisioning audit review.")

    production_launch = subparsers.add_parser(
        "plan-production-launch",
        help="Build a fail-closed launch readiness report before running the default-branch trial start workflow.",
    )
    production_launch.add_argument("--path", default=".", help="Repository root path containing the trial start workflow.")
    production_launch.add_argument("--pr-info", required=True, help="JSON metadata for the GitHub PR.")
    production_launch.add_argument("--generated-at", required=True, help="Launch readiness timestamp.")
    production_launch.add_argument("--expected-head-sha", required=True, help="Expected PR head SHA to bind the launch audit.")
    production_launch.add_argument("--default-branch-ref", default="", help="Durable merged default-branch commit ref.")
    production_launch.add_argument("--runner-ref", default="", help="Durable GitHub-hosted runner readiness ref.")
    production_launch.add_argument("--smtp-secret-ref", default="", help="Durable GitHub SMTP secrets readiness ref without secret values.")
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

    simulation = subparsers.add_parser("run-two-day-simulation", help="Run the no-real-side-effect two-day Phase 11 simulation.")
    simulation.add_argument("--path", default=".", help="Repository root path for simulated preflight context.")
    simulation.add_argument("--generated-at", required=True, help="Simulation report generation timestamp.")
    simulation.add_argument("--start-date", required=True, help="First simulated local date in YYYY-MM-DD format.")
    simulation.add_argument("--json", action="store_true", help="Print JSON two-day simulation report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "owner":
        controls = load_owner_controls(args.controls)
        if args.owner_command == "validate":
            report = validate_owner_controls(controls)
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(report["status"])
                for group in report["weight_groups"]:
                    print(f"- {group['group_id']}: {group['total']}/{group['target']} {group['status']}")
                for warning in report["warnings"]:
                    print(f"- warning: {warning}")
                for error in report["errors"]:
                    print(f"- error: {error}")
            return 0 if report["status"] == "pass" else 2
        if args.owner_command == "preview-impact":
            report = build_owner_impact_preview(controls, days=args.days)
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(report["status"])
                print(f"- days: {report['days']}")
                print(f"- ranking_change_preview: {report['ranking_change_preview']}")
                print(f"- rollback_config_version: {report['rollback_config_version']}")
                for error in report["errors"]:
                    print(f"- error: {error}")
            return 0 if report["status"] == "pass" else 2
        if args.owner_command == "render-docs":
            report = render_owner_documents(
                controls,
                project_path=Path(args.project_path) if args.project_path else None,
                generated_at=args.generated_at,
                write=args.write,
            )
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(report["status"])
                for item in report["owner_view_files"]:
                    print(f"- {item}")
                for error in report["errors"]:
                    print(f"- error: {error}")
            return 0 if report["status"] == "rendered" else 2
        raise AssertionError(f"Unhandled owner command: {args.owner_command}")
    if args.command == "storage":
        if args.storage_command == "migrate":
            report = migrate_database(args.db)
        elif args.storage_command == "inspect":
            report = inspect_database(args.db)
        elif args.storage_command == "rollback":
            report = rollback_database(args.db, target_version=args.target_version)
        else:
            raise AssertionError(f"Unhandled storage command: {args.storage_command}")
        errors = validate_storage_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": [*report.get("blocking_reasons", []), *errors]}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "source-registry":
        controls = load_source_registry_controls(args.controls)
        fixture_atom = Path(args.fixture_atom).read_text(encoding="utf-8") if args.fixture_atom else None
        report = build_source_registry_report(controls, generated_at=args.generated_at, fixture_atom=fixture_atom)
        errors = validate_source_registry_report(report, controls=controls)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "stage1-queue":
        controls = load_owner_controls(args.controls)
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        items = payload.get("items", payload) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            report = {"status": "blocked", "blocking_reasons": ["input must be a JSON array or object with an items array"]}
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for reason in report["blocking_reasons"]:
                    print(f"- {reason}")
            return 2
        report = build_stage1_queue_report(
            items,
            controls,
            as_of_date=args.as_of_date,
            generated_at=args.generated_at,
            run_id=args.run_id,
        )
        errors = validate_stage1_queue_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": errors}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- active_count: {report.get('active_count')}")
            print(f"- evicted_count: {report.get('evicted_count')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "build-b1-report-email":
        payload = load_json_mapping(args.daily_input)
        report = build_b1_report_email_package(
            payload,
            generated_at=args.generated_at,
            recipient=args.recipient,
            artifact_dir=args.artifact_dir,
            write=args.write,
        )
        errors = validate_b1_report_email_package(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            if report["status"] == "pass":
                print(f"- report_id: {report['report_id']}")
                print(f"- email_subject: {report['email_subject']}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "historical-b1-previews":
        if args.input:
            report = build_historical_b1_previews_report(
                load_historical_daily_inputs(args.input),
                generated_at=args.generated_at,
                recipient=args.recipient,
                artifact_dir=args.artifact_dir,
                write=args.write,
                required_count=args.count,
            )
        else:
            report = build_historical_b1_previews(
                generated_at=args.generated_at,
                start_date=args.start_date,
                preview_count=args.count,
                recipient=args.recipient,
                artifact_dir=args.artifact_dir,
                write=args.write,
            )
        errors = validate_historical_b1_previews(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- preview_count: {report.get('preview_count')}")
            print(f"- unique_source_id_count: {report.get('unique_source_id_count')}")
            manifest_path = (
                (report.get("artifact_summary") or {}).get("manifest_path")
                if isinstance(report.get("artifact_summary"), dict)
                else ""
            )
            if manifest_path:
                print(f"- manifest_path: {manifest_path}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "real-historical-arxiv-replay":
        fetcher = fetch_atom_with_curl if args.fetcher == "curl" else fetch_atom_with_urllib
        report = build_real_historical_arxiv_replay(
            generated_at=args.generated_at,
            start_date=args.start_date,
            end_date=args.end_date,
            count=args.count,
            lookback_days=args.lookback_days,
            max_results=args.max_results,
            recipient=args.recipient,
            artifact_dir=args.artifact_dir,
            write=args.write,
            fetcher=fetcher,
            polite_delay_seconds=args.polite_delay_seconds,
        )
        errors = validate_real_historical_arxiv_replay_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- success_count: {report.get('success_count')}/{report.get('required_replay_count')}")
            print(f"- unique_as_of_date_count: {report.get('unique_as_of_date_count')}")
            print(f"- unique_selected_source_count: {report.get('unique_selected_source_count')}")
            artifact_dir = (
                (report.get("artifact_summary") or {}).get("artifact_dir")
                if isinstance(report.get("artifact_summary"), dict)
                else ""
            )
            if artifact_dir:
                print(f"- artifact_dir: {artifact_dir}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "runtime-audit":
        report = build_runtime_audit(
            state_dir=args.state_dir,
            db_path=args.db,
            generated_at=args.generated_at,
        )
        errors = validate_stage1_runtime_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "tick":
        report = run_tick(state_dir=args.state_dir, generated_at=args.generated_at, write=not args.no_write)
        errors = validate_stage1_runtime_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- heartbeat_path: {report.get('heartbeat_path')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "watchdog":
        report = run_watchdog(state_dir=args.state_dir, generated_at=args.generated_at)
        errors = validate_stage1_runtime_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "backup":
        report = create_runtime_backup(
            db_path=args.db,
            backup_dir=args.backup_dir,
            generated_at=args.generated_at,
            include_paths=args.include_path,
        )
        errors = validate_stage1_runtime_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            if report["status"] == "pass":
                print(f"- backup_manifest_path: {report.get('backup_manifest_path')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "restore":
        report = restore_runtime_backup(
            manifest_path=args.manifest,
            target_db_path=args.target_db,
            generated_at=args.generated_at,
            confirm_restore=args.confirm_restore,
            allow_overwrite=args.allow_overwrite,
        )
        errors = validate_stage1_runtime_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "scheduler":
        action = f"scheduler_{args.scheduler_command}"
        report = build_scheduler_plan(
            action=action,
            platform=args.platform,
            project_root=args.project_root,
            state_dir=args.state_dir,
            generated_at=args.generated_at,
            artifact_dir=args.artifact_dir,
            write=args.write,
        )
        errors = validate_stage1_runtime_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print("- dry_run_only: true")
            for path in report.get("written_paths", []):
                print(f"- template: {path}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "migration":
        if args.migration_command == "export":
            report = build_migration_package(
                project_root=args.project_root,
                output_dir=args.output_dir,
                db_path=args.db,
                generated_at=args.generated_at,
                include_paths=args.include_path,
                required_paths=args.required_path or None,
                write=not args.no_write,
            )
        else:
            report = verify_migration_package(manifest_path=args.manifest, generated_at=args.generated_at)
        errors = validate_stage1_migration_report(report)
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            if report.get("package_manifest_path"):
                print(f"- package_manifest_path: {report.get('package_manifest_path')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "post-migration-bootstrap":
        report = build_stage1_bootstrap_report(
            project_root=args.project_root,
            migration_manifest=args.migration_manifest,
            state_dir=args.state_dir,
            db_path=args.db,
            generated_at=args.generated_at,
            target_environment=args.target_environment,
            workflow_path=args.workflow_path,
            require_github_actions=args.require_github_actions,
            require_network_probe=args.require_network_probe,
            require_secret_presence=args.require_secret_presence,
        )
        errors = validate_stage1_bootstrap_report(report)
        if errors:
            report = {**report, "status": "blocked", "bootstrap_ready": False, "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- target_environment: {report.get('target_environment')}")
            print(f"- cloud_runner_verified: {str(report.get('cloud_runner_verified')).lower()}")
            for reason in report.get("blocking_reasons", []):
                print(f"- error: {reason}")
        return 0 if report["status"] == "pass" else 2
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
    if args.command == "plan-all-arxiv-scan":
        plan = build_all_arxiv_scan_plan(max_results_per_category=args.max_results_per_category)
        errors = validate_all_arxiv_scan_plan(plan)
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
            for archive in plan["archives"]:
                print(f"{archive['archive_id']}\t{archive['query']}\t{archive['group']}")
        return 0
    if args.command == "build-all-arxiv-daily-input":
        queue = None
        if args.queue_path and Path(args.queue_path).is_file():
            queue = load_json_mapping(args.queue_path)
        report = build_all_arxiv_daily_input(
            date=args.date,
            generated_at=args.generated_at,
            timezone=args.timezone,
            queue=queue,
            recent_source_ids=args.recent_source_id,
            max_results_per_category=args.max_results_per_category,
            artifact_dir=args.artifact_dir,
            queue_output_path=args.queue_output,
            polite_delay_seconds=args.polite_delay_seconds,
            transient_retry_count=args.transient_retry_count,
            transient_retry_delay_seconds=args.transient_retry_delay_seconds,
        )
        errors = validate_all_arxiv_daily_input_report(report)
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
    if args.command == "run-live-all-arxiv-dry-run":
        report = build_live_all_arxiv_dry_run(
            generated_at=args.generated_at,
            date=args.date or None,
            max_results_per_category=args.max_results_per_category,
            artifact_dir=args.artifact_dir,
            polite_delay_seconds=args.polite_delay_seconds,
        )
        errors = validate_live_all_arxiv_dry_run_report(report)
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
        elif report["live_dry_run_ready"]:
            print(f"{report['dry_run_id']}\t{report['verified_archive_count']} archives")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["live_dry_run_ready"] else 2
    if args.command == "build-stage1-accelerated-acceptance":
        report = build_stage1_accelerated_acceptance_report(
            load_json_mapping(args.live_dry_run),
            load_json_mapping(args.controlled_smtp_manifest),
            generated_at=args.generated_at,
            expected_samples=args.expected_samples,
            live_dry_run_ref=args.live_dry_run_ref,
            controlled_smtp_ref=args.controlled_smtp_ref,
            scheduler_ref=args.scheduler_ref,
            resource_ref=args.resource_ref,
            recovery_ref=args.recovery_ref,
            artifact_dir=args.artifact_dir,
        )
        errors = validate_stage1_accelerated_acceptance_report(report)
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
        elif report["accelerated_acceptance_ready"]:
            print(f"{report['acceptance_id']}\tARXIV_PRODUCTION_ACCEPTED")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["accelerated_acceptance_ready"] else 2
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
    if args.command == "render-lightweight-mp4":
        data = load_json_mapping(args.daily_input)
        daily_input = data.get("daily_input", data) if isinstance(data, dict) else data
        report = render_lightweight_mp4(
            daily_input,
            output_path=args.output,
            generated_at=args.generated_at,
            duration_seconds=args.duration_seconds,
        )
        errors = validate_mp4_render_report(report)
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
        elif report["mp4_rendered"]:
            print(f"{report['render_id']}\t{report['video_path']}")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["mp4_rendered"] else 2
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
            text_artifacts_verified=args.text_artifacts_verified,
            text_artifact_ref=args.text_artifact_ref,
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
            text_artifacts_verified=args.text_artifacts_verified,
            text_artifact_ref=args.text_artifact_ref,
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
            release_delivery_report=load_json_mapping(args.release_delivery) if args.release_delivery else None,
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
    if args.command == "print-production-refs-template":
        template = build_production_refs_input_template(
            runner_label=args.runner_label,
        )
        print(json.dumps(template, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "discover-production-refs":
        try:
            refs_input = discover_production_refs_input_with_gh(
                repo=args.repo,
                runner_label=args.runner_label,
                gh_command=args.gh_command,
            )
        except ProductionRefsDiscoveryError as error:
            payload = {
                "status": "blocked",
                "production_refs_ready": False,
                "side_effects_performed": False,
                "secret_values_logged": False,
                "codex_auth_read": False,
                "workflow_dispatched": False,
                "production_acceptance_claimed": False,
                "errors": [str(error)],
            }
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                print(f"- {error}")
            return 2
        report = build_production_refs_report(refs_input, generated_at=args.generated_at)
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
    if args.command == "review-provisioning-audit":
        review = build_provisioning_audit_review(
            load_json_mapping(args.production_refs_report),
            generated_at=args.generated_at,
            workflow_run_ref=args.workflow_run_ref,
            artifact_ref=args.artifact_ref,
        )
        errors = validate_provisioning_audit_review(review)
        if errors:
            if args.json:
                print(json.dumps({"status": "blocked", "errors": errors}, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("blocked")
                for error in errors:
                    print(f"- {error}")
            return 2
        if args.json:
            print(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True))
        elif review["provisioning_audit_ready"]:
            print(f"{review['audit_review_id']}\tready")
        else:
            print("blocked")
            for reason in review["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if review["provisioning_audit_ready"] else 2
    if args.command == "plan-production-launch":
        launch_refs = {
            "runner_ref": args.runner_ref,
            "smtp_secret_ref": args.smtp_secret_ref,
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
    if args.command == "run-two-day-simulation":
        report = run_two_day_simulation(
            path=Path(args.path),
            generated_at=args.generated_at,
            start_date=args.start_date,
        )
        errors = validate_two_day_simulation_report(report)
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
        elif report["two_day_simulation_ready"]:
            print(f"{report['simulation_id']}\t{report['observed_day_count']} days")
        else:
            print("blocked")
            for reason in report["blocking_reasons"]:
                print(f"- {reason}")
        return 0 if report["two_day_simulation_ready"] else 2
    raise AssertionError(f"Unhandled command: {args.command}")
