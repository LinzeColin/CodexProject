"""Command-line interface for arXiv Daily Push."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from pathlib import Path
import subprocess

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
from .local_runner import (
    build_launchd_package,
    build_local_preflight,
    run_local_daily,
    validate_local_runner_report,
)
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
from .preprint_adapter import fetch_preprint_details_with_curl, ingest_latest_preprints, validate_preprint_source_batch
from .top_journal_adapter import fetch_top_journal_rss_with_curl, ingest_latest_top_journal, validate_top_journal_source_batch
from .source_ingest import ingest_latest_arxiv, validate_source_batch
from .source_registry import (
    build_source_registry_report,
    load_source_registry_controls,
    validate_source_registry_report,
)
from .smtp_delivery import deliver_notification, validate_smtp_delivery_report
from .stage1_b1_report import build_b1_report_email_package, validate_b1_report_email_package
from .stage1_bootstrap import (
    STAGE1_BOOTSTRAP_NETWORK_MAX_ATTEMPTS,
    STAGE1_BOOTSTRAP_NETWORK_TIMEOUT_SECONDS,
    build_stage1_bootstrap_report,
    validate_stage1_bootstrap_report,
)
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
from .stage2_replay_gate import (
    build_s2plt01_independent_replay_review_report,
    build_s2plt01_replay_payload_execution_report,
    build_s2plt01_terminal_acceptance_artifact_validation_state,
    build_s2plt01_terminal_acceptance_audit_state,
    validate_s2plt01_independent_replay_review_report,
    validate_s2plt01_replay_payload_execution_report,
)
from .stage2_final_gate import (
    S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
    S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
    build_final_acceptance_bundle_readiness_state,
    build_final_acceptance_bundle_manifest_validation_state,
    build_final_bundle_prerequisite_plan_state,
    build_final_command_execution_validation_state,
    build_independent_final_closure_decision_owner_packet_state,
    build_independent_final_reviewer_assignment_artifact_draft_state,
    build_independent_final_reviewer_assignment_owner_packet_state,
    build_independent_final_reviewer_assignment_validation_state,
    build_next_agent_handoff_validation_state,
    build_no_production_side_effect_attestation_validation_state,
    build_p0_p1_zero_proof_artifact_validation_state,
    build_s2plt02_dry_run_second_day_audit_state,
    build_s2plt02_real_proof_capture_authorization_artifact_draft_state,
    build_s2plt02_real_proof_capture_authorization_owner_packet_state,
    build_s2plt02_real_proof_capture_authorization_validation_state,
    build_s2plt02_real_proof_capture_readiness_state,
    build_s2plt02_real_delivery_manifest_validation_state,
    build_s2plt02_normalized_delivery_manifest_state,
    build_s2plt02_real_scheduler_proof_validation_state,
    build_s2plt02_terminal_delivery_input_inventory_state,
    build_s2plt02_terminal_delivery_proof_capture_plan_state,
    build_s2plt02_terminal_delivery_proof_artifact_draft_state,
    build_s2plt02_terminal_delivery_proof_artifact_validation_state,
    build_s2plt02_terminal_readiness_audit_state,
    build_s2plt03_terminal_resilience_proof_artifact_validation_state,
    build_s2plt03_resilience_precheck_report,
    build_s2plt04_completion_evidence_audit_state,
    build_s2plt04_completion_report_validation_state,
    validate_final_acceptance_bundle_readiness_state,
    validate_final_bundle_prerequisite_plan_state,
    validate_independent_final_closure_decision_owner_packet_state,
    validate_independent_final_reviewer_assignment_owner_packet_state,
    validate_s2plt02_real_proof_capture_authorization_owner_packet_state,
    validate_s2plt02_dry_run_second_day_audit_state,
    validate_s2plt02_real_proof_capture_readiness_state,
    validate_s2plt02_real_delivery_manifest_validation_state,
    validate_s2plt02_normalized_delivery_manifest_state,
    validate_s2plt02_real_scheduler_proof_validation_state,
    validate_s2plt02_terminal_delivery_input_inventory_state,
    validate_s2plt02_terminal_delivery_proof_capture_plan_state,
    validate_s2plt02_terminal_delivery_proof_artifact,
    validate_s2plt03_terminal_resilience_proof_artifact_validation_state,
    validate_s2plt04_completion_evidence_audit_state,
)
from .stage2_sources import (
    run_s2pgt05_cross_board_calibration,
    run_s2pgt04_delta_resonance,
    run_s2pgt03_source_board_routing,
    run_s2pgt02_knowledge_graph_spine,
    run_s2pgt01_evidence_packet_v2_compatibility,
    build_s2p1_preprint_replay_shadow_evidence,
    build_s2p1_preprint_promotion_report,
    run_s2pft05_d3_full_governance_qualification,
    run_s2pft04_special_zone_discovery,
    run_s2pft03_key_city_coverage,
    run_s2pft02_hk_mo_independent_profile,
    run_s2pft01_china_provincial_template_coverage,
    run_s2pdt04_china_d3_readiness_review,
    run_s2pdt03_china_legal_metadata_relation_shadow,
    run_s2pdt02_china_c1_department_source_map,
    run_s2pdt01_china_c0_source_foundation,
    run_s2pet01_us_ta_source_foundation,
    run_s2pet02_us_lg_legal_backbone,
    run_s2pet03_us_fm_source_backbone,
    run_s2pet04_us_tp_d4_qualification,
    run_s2pit01_user_center,
    run_s2pit02_runtime_dashboard,
    run_s2pit03_source_model_view,
    run_s2pit04_content_ledger,
    run_s2pkt01_mail_contract,
    run_s2pkt02_m1_mail,
    run_s2pkt03_m2_mail,
    run_s2pkt04_m3_mail,
    run_s2pkt05_m4_mail,
    run_s2pjt01_lifecycle_state,
    run_s2pjt02_review_schedule,
    run_s2pjt03_action_asset_roi,
    run_s2pjt04_weekly_report,
    run_s2pjt05_monthly_report,
    run_s2pht05_content_quality_gate,
    run_s2pct07_d2_source_domain_qualification,
    run_s2pct06_authoritative_report_shadow,
    run_s2pct05_engineering_signal_shadow,
    run_s2pct04_top_journal_profile_shadow,
    run_s2pct03_lancet_shadow_daily,
    run_s2pct02_science_shadow_daily,
    run_s2p2_top_journal_shadow_daily,
    run_s2p1_preprint_shadow_daily,
    validate_s2pdt04_china_d3_readiness_review_report,
    validate_s2pdt03_china_legal_metadata_relation_shadow_report,
    validate_s2pdt02_china_c1_department_source_map_report,
    validate_s2pdt01_china_c0_source_foundation_report,
    validate_s2pet01_us_ta_source_foundation_report,
    validate_s2pet02_us_lg_legal_backbone_report,
    validate_s2pet03_us_fm_source_backbone_report,
    validate_s2pet04_us_tp_d4_qualification_report,
    validate_s2pit01_user_center_report,
    validate_s2pit02_runtime_dashboard_report,
    validate_s2pit03_source_model_view_report,
    validate_s2pit04_content_ledger_report,
    validate_s2pkt01_mail_contract_report,
    validate_s2pkt02_m1_mail_report,
    validate_s2pkt03_m2_mail_report,
    validate_s2pkt04_m3_mail_report,
    validate_s2pkt05_m4_mail_report,
    validate_s2pjt01_lifecycle_state_report,
    validate_s2pjt02_review_schedule_report,
    validate_s2pjt03_action_asset_roi_report,
    validate_s2pjt04_weekly_report,
    validate_s2pjt05_monthly_report,
    validate_s2pht05_content_quality_gate_report,
    validate_s2pct07_d2_source_domain_qualification_report,
    validate_s2pct06_authoritative_report_source_report,
    validate_s2pct05_engineering_signal_report,
    validate_s2pct04_top_journal_profile_report,
    validate_s2pct03_lancet_shadow_report,
    validate_s2pct02_science_shadow_report,
    validate_s2p1_preprint_replay_shadow_report,
    validate_s2p1_shadow_report,
    validate_s2p2_top_journal_shadow_report,
    validate_s2pft05_d3_full_governance_qualification_report,
    validate_s2pgt05_cross_board_calibration_report,
    validate_s2pgt04_delta_resonance_report,
    validate_s2pgt03_source_board_routing_report,
    validate_s2pgt02_knowledge_graph_spine_report,
    validate_s2pgt01_evidence_packet_v2_compatibility_report,
    validate_s2pft04_special_zone_discovery_report,
    validate_s2pft03_key_city_coverage_report,
    validate_s2pft02_hk_mo_independent_profile_report,
    validate_s2pft01_china_provincial_template_coverage_report,
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


def load_json_records(path: str | Path, key: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get(key, [])
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list or an object with {key}")
    return [item for item in data if isinstance(item, dict)]


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

    local_runner = subparsers.add_parser("local-runner", help="Run or package the Stage 1 local Codex runner.")
    local_subparsers = local_runner.add_subparsers(dest="local_runner_command", required=True)
    local_preflight = local_subparsers.add_parser("preflight", help="Check local runner readiness without secret values.")
    local_preflight.add_argument("--project-root", default=".", help="Repository root used for local execution.")
    local_preflight.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    local_preflight.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    local_preflight.add_argument("--require-smtp", action="store_true", help="Require SMTP env names for a real local send.")
    local_preflight.add_argument("--json", action="store_true", help="Print JSON local preflight report.")
    local_daily = local_subparsers.add_parser("daily", help="Run one local Stage 1 daily path and persist evidence.")
    local_daily.add_argument("--project-root", default=".", help="Repository root used for local execution.")
    local_daily.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    local_daily.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    local_daily.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    local_daily.add_argument("--max-results-per-category", type=int, default=ALL_ARXIV_MAX_RESULTS_PER_CATEGORY)
    local_daily.add_argument("--polite-delay-seconds", type=float, default=0.0)
    local_daily.add_argument(
        "--daily-input-report",
        help="Reuse an existing adp-daily-input-report.json for resend/catch-up instead of fetching live arXiv input.",
    )
    local_daily.add_argument("--allow-smtp-send", action="store_true", help="Attempt real SMTP only when env keys are present.")
    local_daily.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    local_daily.add_argument("--json", action="store_true", help="Print JSON local runner report.")
    local_launchd = local_subparsers.add_parser("launchd-package", help="Generate macOS launchd templates without installing.")
    local_launchd.add_argument("--project-root", default=".", help="Repository root used by the launchd command.")
    local_launchd.add_argument("--state-dir", required=True, help="Local ADP state directory used by launchd.")
    local_launchd.add_argument("--artifact-dir", required=True, help="Directory that receives launchd package files.")
    local_launchd.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    local_launchd.add_argument("--no-write", action="store_true", help="Preview package without writing files.")
    local_launchd.add_argument("--json", action="store_true", help="Print JSON launchd package report.")

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
    post_migration_bootstrap.add_argument(
        "--network-timeout-seconds",
        type=int,
        default=STAGE1_BOOTSTRAP_NETWORK_TIMEOUT_SECONDS,
        help="Per-attempt arXiv network probe timeout.",
    )
    post_migration_bootstrap.add_argument(
        "--network-max-attempts",
        type=int,
        default=STAGE1_BOOTSTRAP_NETWORK_MAX_ATTEMPTS,
        help="Maximum arXiv network probe attempts before failing closed.",
    )
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

    fetch_preprint = subparsers.add_parser("fetch-preprint-latest", help="Fetch latest bioRxiv/medRxiv metadata SourceItems.")
    fetch_preprint.add_argument("--server", choices=("biorxiv", "medrxiv"), required=True, help="Preprint server to query.")
    fetch_preprint.add_argument("--interval", default="1d", help="API interval: Nd, N, DOI, or YYYY-MM-DD/YYYY-MM-DD.")
    fetch_preprint.add_argument("--cursor", type=int, default=0, help="bioRxiv/medRxiv API cursor.")
    fetch_preprint.add_argument("--max-records", type=int, default=3, help="Small metadata result window to keep.")
    fetch_preprint.add_argument("--generated-at", required=True, help="Fetch timestamp used for SourceItems and batch evidence.")
    fetch_preprint.add_argument("--seen-source-id", action="append", default=[], help="Previously processed source_id to exclude.")
    fetch_preprint.add_argument("--fetcher", choices=("urllib", "curl"), default="urllib", help="Real metadata fetch implementation.")
    fetch_preprint.add_argument("--json", action="store_true", help="Print JSON source batch.")

    fetch_top_journal = subparsers.add_parser("fetch-top-journal-latest", help="Fetch latest top-journal public RSS metadata SourceItems.")
    fetch_top_journal.add_argument("--journal", choices=("nature", "science", "lancet"), default="nature", help="Top journal to query.")
    fetch_top_journal.add_argument("--max-records", type=int, default=3, help="Small metadata result window to keep.")
    fetch_top_journal.add_argument("--generated-at", required=True, help="Fetch timestamp used for SourceItems and batch evidence.")
    fetch_top_journal.add_argument("--seen-source-id", action="append", default=[], help="Previously processed source_id to exclude.")
    fetch_top_journal.add_argument("--fetcher", choices=("urllib", "curl"), default="urllib", help="Real metadata fetch implementation.")
    fetch_top_journal.add_argument("--json", action="store_true", help="Print JSON source batch.")

    s2p1_gate = subparsers.add_parser("stage2-preprint-gate", help="Evaluate S2P1T01 bioRxiv/medRxiv source promotion gates.")
    s2p1_gate.add_argument("--biorxiv-batch", required=True, help="bioRxiv preprint source batch JSON.")
    s2p1_gate.add_argument("--medrxiv-batch", required=True, help="medRxiv preprint source batch JSON.")
    s2p1_gate.add_argument("--replay-report", help="Optional 30-day terminal replay report JSON.")
    s2p1_gate.add_argument("--shadow-report", help="Optional 48h shadow report JSON.")
    s2p1_gate.add_argument("--generated-at", required=True, help="Gate report timestamp.")
    s2p1_gate.add_argument("--json", action="store_true", help="Print JSON gate report.")

    s2p1_shadow = subparsers.add_parser("stage2-preprint-shadow-daily", help="Run one no-send S2P1 bioRxiv/medRxiv shadow daily preview.")
    s2p1_shadow.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2p1_shadow.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2p1_shadow.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2p1_shadow.add_argument("--biorxiv-batch", required=True, help="bioRxiv preprint source batch JSON.")
    s2p1_shadow.add_argument("--medrxiv-batch", required=True, help="medRxiv preprint source batch JSON.")
    s2p1_shadow.add_argument("--queue-path", help="Optional existing S2P1 preprint queue JSON.")
    s2p1_shadow.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2p1_shadow.add_argument("--json", action="store_true", help="Print JSON shadow report.")

    s2p1_replay = subparsers.add_parser(
        "stage2-preprint-replay-shadow",
        help="Run S2P1T01 30-date bioRxiv/medRxiv replay plus 48h no-production shadow evidence.",
    )
    s2p1_replay.add_argument("--state-dir", required=True, help="Local ADP state directory for replay queue, ledger, and reports.")
    s2p1_replay.add_argument("--generated-at", required=True, help="Replay evidence timestamp.")
    s2p1_replay.add_argument("--start-date", help="First historical as-of date. Defaults from --end-date/--count.")
    s2p1_replay.add_argument("--end-date", help="Last historical as-of date. Defaults to generated-at date.")
    s2p1_replay.add_argument("--count", type=int, default=30, help="Number of historical as-of dates to replay.")
    s2p1_replay.add_argument("--lookback-days", type=int, default=7, help="Trailing preprint date window per as-of date.")
    s2p1_replay.add_argument("--max-records", type=int, default=3, help="Small metadata result window per server/date.")
    s2p1_replay.add_argument("--fetcher", choices=("urllib", "curl"), default="curl", help="Real metadata fetch implementation.")
    s2p1_replay.add_argument("--polite-delay-seconds", type=float, default=1.0, help="Delay between historical API windows.")
    s2p1_replay.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2p1_replay.add_argument("--json", action="store_true", help="Print JSON replay/shadow report.")

    s2p2_shadow = subparsers.add_parser("stage2-top-journal-shadow-daily", help="Run one no-send S2P2 Nature shadow daily preview.")
    s2p2_shadow.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2p2_shadow.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2p2_shadow.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2p2_shadow.add_argument("--nature-batch", required=True, help="Nature RSS source batch JSON.")
    s2p2_shadow.add_argument("--queue-path", help="Optional existing S2P2 top-journal queue JSON.")
    s2p2_shadow.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2p2_shadow.add_argument("--json", action="store_true", help="Print JSON shadow report.")

    s2pct02_shadow = subparsers.add_parser("stage2-science-shadow-daily", help="Run one no-send S2PCT02 Science shadow daily preview.")
    s2pct02_shadow.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pct02_shadow.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pct02_shadow.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pct02_shadow.add_argument("--science-batch", required=True, help="Science RSS source batch JSON.")
    s2pct02_shadow.add_argument("--queue-path", help="Optional existing S2PCT02 Science queue JSON.")
    s2pct02_shadow.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pct02_shadow.add_argument("--json", action="store_true", help="Print JSON shadow report.")

    s2pct03_shadow = subparsers.add_parser("stage2-lancet-shadow-daily", help="Run one no-send S2PCT03 The Lancet shadow daily preview.")
    s2pct03_shadow.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pct03_shadow.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pct03_shadow.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pct03_shadow.add_argument("--lancet-batch", required=True, help="The Lancet RSS source batch JSON.")
    s2pct03_shadow.add_argument("--queue-path", help="Optional existing S2PCT03 Lancet queue JSON.")
    s2pct03_shadow.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pct03_shadow.add_argument("--json", action="store_true", help="Print JSON shadow report.")

    s2pct04_profile = subparsers.add_parser(
        "stage2-top-journal-profile-shadow",
        help="Run S2PCT04 top-journal profile, relation, correction, and retraction shadow evidence.",
    )
    s2pct04_profile.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pct04_profile.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pct04_profile.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pct04_profile.add_argument("--nature-batch", required=True, help="Nature RSS source batch JSON.")
    s2pct04_profile.add_argument("--science-batch", required=True, help="Science RSS source batch JSON.")
    s2pct04_profile.add_argument("--lancet-batch", required=True, help="The Lancet RSS source batch JSON.")
    s2pct04_profile.add_argument("--publication-events", required=True, help="Publication relation/correction/retraction event JSON.")
    s2pct04_profile.add_argument("--prior-profile-state", help="Optional prior profile state JSON for forced updates.")
    s2pct04_profile.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pct04_profile.add_argument("--json", action="store_true", help="Print JSON profile report.")

    s2pct05_engineering = subparsers.add_parser(
        "stage2-engineering-signals-shadow",
        help="Run S2PCT05 engineering open-source/code/benchmark/standards shadow evidence.",
    )
    s2pct05_engineering.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pct05_engineering.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pct05_engineering.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pct05_engineering.add_argument("--profile-report", required=True, help="Passing S2PCT04 top-journal profile report JSON.")
    s2pct05_engineering.add_argument("--engineering-signals", required=True, help="Engineering signal metadata JSON list or object with signals.")
    s2pct05_engineering.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pct05_engineering.add_argument("--json", action="store_true", help="Print JSON engineering signal report.")

    s2pct06_reports = subparsers.add_parser(
        "stage2-authoritative-reports-shadow",
        help="Run S2PCT06 authoritative research institution and industry technical report shadow evidence.",
    )
    s2pct06_reports.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pct06_reports.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pct06_reports.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pct06_reports.add_argument("--engineering-signal-report", required=True, help="Passing S2PCT05 engineering signal report JSON.")
    s2pct06_reports.add_argument("--technical-reports", required=True, help="Technical report metadata JSON list or object with reports.")
    s2pct06_reports.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pct06_reports.add_argument("--json", action="store_true", help="Print JSON authoritative report source report.")

    s2pct07_qualification = subparsers.add_parser(
        "stage2-d2-source-domain-qualification",
        help="Run S2PCT07 D2 source-domain qualification and cross-type calibration evidence.",
    )
    s2pct07_qualification.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pct07_qualification.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pct07_qualification.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pct07_qualification.add_argument("--profile-report", required=True, help="Passing S2PCT04 profile report JSON.")
    s2pct07_qualification.add_argument("--engineering-signal-report", required=True, help="Passing S2PCT05 engineering signal report JSON.")
    s2pct07_qualification.add_argument("--authoritative-report", required=True, help="Passing S2PCT06 authoritative report JSON.")
    s2pct07_qualification.add_argument("--replay-records", required=True, help="D2 replay records JSON list or object with replay_records.")
    s2pct07_qualification.add_argument("--shadow-records", required=True, help="D2 shadow records JSON list or object with shadow_records.")
    s2pct07_qualification.add_argument("--forced-event-records", required=True, help="Forced-event records JSON list or object with forced_event_records.")
    s2pct07_qualification.add_argument("--queue-explanation-records", required=True, help="Queue explanation records JSON list or object with queue_explanation_records.")
    s2pct07_qualification.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pct07_qualification.add_argument("--json", action="store_true", help="Print JSON qualification report.")

    s2pdt01_china_c0 = subparsers.add_parser(
        "stage2-china-c0-source-foundation",
        help="Run S2PDT01/S2P3T01 China C0 national authority metadata-only source foundation evidence.",
    )
    s2pdt01_china_c0.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pdt01_china_c0.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pdt01_china_c0.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pdt01_china_c0.add_argument("--d2-qualification-report", required=True, help="Passing S2PCT07 D2 qualification report JSON.")
    s2pdt01_china_c0.add_argument("--authority-records", required=True, help="China C0 authority metadata JSON list or object with authority_records.")
    s2pdt01_china_c0.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pdt01_china_c0.add_argument("--json", action="store_true", help="Print JSON C0 source foundation report.")

    s2pdt02_china_c1 = subparsers.add_parser(
        "stage2-china-c1-department-source-map",
        help="Run S2PDT02/S2P3T02 China C1 central department metadata-only source-map evidence.",
    )
    s2pdt02_china_c1.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pdt02_china_c1.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pdt02_china_c1.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pdt02_china_c1.add_argument("--c0-source-foundation-report", required=True, help="Passing S2PDT01 C0 source foundation report JSON.")
    s2pdt02_china_c1.add_argument("--department-records", required=True, help="China C1 department metadata JSON list or object with department_records.")
    s2pdt02_china_c1.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pdt02_china_c1.add_argument("--json", action="store_true", help="Print JSON C1 department source-map report.")

    s2pdt03_china_legal = subparsers.add_parser(
        "stage2-china-legal-metadata-relation-shadow",
        help="Run S2PDT03/S2P3T03 China legal metadata, version/effectivity, and reprint relation shadow evidence.",
    )
    s2pdt03_china_legal.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pdt03_china_legal.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pdt03_china_legal.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pdt03_china_legal.add_argument("--c1-department-source-map-report", required=True, help="Passing S2PDT02 C1 department source-map report JSON.")
    s2pdt03_china_legal.add_argument("--legal-records", required=True, help="China legal metadata JSON list or object with legal_records.")
    s2pdt03_china_legal.add_argument("--relation-records", required=True, help="China legal relation JSON list or object with relation_records.")
    s2pdt03_china_legal.add_argument("--prior-conclusion-records", required=True, help="Prior conclusion update JSON list or object with prior_conclusion_records.")
    s2pdt03_china_legal.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pdt03_china_legal.add_argument("--json", action="store_true", help="Print JSON legal metadata relation shadow report.")

    s2pdt04_china_readiness = subparsers.add_parser(
        "stage2-china-d3-readiness-review",
        help="Run S2PDT04/S2P3T04 China D3 replay, shadow, authority, and board-routing readiness evidence.",
    )
    s2pdt04_china_readiness.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pdt04_china_readiness.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pdt04_china_readiness.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pdt04_china_readiness.add_argument("--c0-source-foundation-report", required=True, help="Passing S2PDT01 C0 source foundation report JSON.")
    s2pdt04_china_readiness.add_argument("--c1-department-source-map-report", required=True, help="Passing S2PDT02 C1 source-map report JSON.")
    s2pdt04_china_readiness.add_argument("--legal-metadata-relation-report", required=True, help="Passing S2PDT03 legal metadata relation report JSON.")
    s2pdt04_china_readiness.add_argument("--replay-records", required=True, help="D3 replay records JSON list or object with replay_records.")
    s2pdt04_china_readiness.add_argument("--shadow-records", required=True, help="D3 shadow records JSON list or object with shadow_records.")
    s2pdt04_china_readiness.add_argument("--board-route-records", required=True, help="D3 board route records JSON list or object with board_route_records.")
    s2pdt04_china_readiness.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pdt04_china_readiness.add_argument("--json", action="store_true", help="Print JSON D3 readiness review report.")

    s2pet01_us_ta = subparsers.add_parser(
        "stage2-us-ta-source-foundation",
        help="Run S2PET01/S2P4T01 US official technology-agency metadata-only source foundation evidence.",
    )
    s2pet01_us_ta.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pet01_us_ta.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pet01_us_ta.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pet01_us_ta.add_argument("--agency-records", required=True, help="US-TA official agency metadata JSON list or object with agency_records.")
    s2pet01_us_ta.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pet01_us_ta.add_argument("--json", action="store_true", help="Print JSON US-TA source foundation report.")

    s2pet02_us_lg = subparsers.add_parser(
        "stage2-us-lg-legal-backbone",
        help="Run S2PET02/S2P4T02 US legal metadata-only backbone and cross-document relation evidence.",
    )
    s2pet02_us_lg.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pet02_us_lg.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pet02_us_lg.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pet02_us_lg.add_argument("--us-ta-source-foundation-report", required=True, help="Passing S2PET01 US-TA source foundation report JSON.")
    s2pet02_us_lg.add_argument("--legal-records", required=True, help="US-LG legal metadata JSON list or object with legal_records.")
    s2pet02_us_lg.add_argument("--relation-records", required=True, help="US-LG legal relation JSON list or object with relation_records.")
    s2pet02_us_lg.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pet02_us_lg.add_argument("--json", action="store_true", help="Print JSON US-LG legal backbone report.")

    s2pet03_us_fm = subparsers.add_parser(
        "stage2-us-fm-source-backbone",
        help="Run S2PET03/S2P4T03 US finance, market, and macro metadata-only source backbone evidence.",
    )
    s2pet03_us_fm.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pet03_us_fm.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pet03_us_fm.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pet03_us_fm.add_argument("--us-lg-legal-backbone-report", required=True, help="Passing S2PET02 US-LG legal backbone report JSON.")
    s2pet03_us_fm.add_argument("--finance-records", required=True, help="US-FM finance metadata JSON list or object with finance_records.")
    s2pet03_us_fm.add_argument("--relation-records", required=True, help="US-FM finance relation JSON list or object with relation_records.")
    s2pet03_us_fm.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pet03_us_fm.add_argument("--json", action="store_true", help="Print JSON US-FM source backbone report.")

    s2pet04_us_tp = subparsers.add_parser(
        "stage2-us-tp-d4-qualification",
        help="Run S2PET04/S2P4T04 US technology policy and D4 qualification metadata-only evidence.",
    )
    s2pet04_us_tp.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pet04_us_tp.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pet04_us_tp.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pet04_us_tp.add_argument("--us-ta-source-foundation-report", required=True, help="Passing S2PET01 US-TA source foundation report JSON.")
    s2pet04_us_tp.add_argument("--us-lg-legal-backbone-report", required=True, help="Passing S2PET02 US-LG legal backbone report JSON.")
    s2pet04_us_tp.add_argument("--us-fm-source-backbone-report", required=True, help="Passing S2PET03 US-FM source backbone report JSON.")
    s2pet04_us_tp.add_argument("--policy-records", required=True, help="US-TP policy metadata JSON list or object with policy_records.")
    s2pet04_us_tp.add_argument("--replay-records", required=True, help="D4 replay JSON list or object with replay_records.")
    s2pet04_us_tp.add_argument("--shadow-records", required=True, help="D4 shadow JSON list or object with shadow_records.")
    s2pet04_us_tp.add_argument("--board-route-records", required=True, help="D4 board route JSON list or object with board_route_records.")
    s2pet04_us_tp.add_argument("--budget-records", required=True, help="D4 budget JSON list or object with budget_records.")
    s2pet04_us_tp.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pet04_us_tp.add_argument("--json", action="store_true", help="Print JSON US-TP D4 qualification report.")

    s2pft01_china_provinces = subparsers.add_parser(
        "stage2-china-provincial-template-coverage",
        help="Run S2PFT01/S2P5T01 mainland provincial template coverage and health-tier evidence.",
    )
    s2pft01_china_provinces.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pft01_china_provinces.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pft01_china_provinces.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pft01_china_provinces.add_argument("--d3-readiness-review-report", required=True, help="Passing S2PDT04 D3 readiness review report JSON.")
    s2pft01_china_provinces.add_argument("--provincial-records", required=True, help="Mainland provincial records JSON list or object with provincial_records.")
    s2pft01_china_provinces.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pft01_china_provinces.add_argument("--json", action="store_true", help="Print JSON provincial template coverage report.")

    s2pft02_hk_mo = subparsers.add_parser(
        "stage2-hk-mo-independent-profile",
        help="Run S2PFT02/S2P5T02 Hong Kong and Macau independent legal/government profile evidence.",
    )
    s2pft02_hk_mo.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pft02_hk_mo.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pft02_hk_mo.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pft02_hk_mo.add_argument("--provincial-template-coverage-report", required=True, help="Passing S2PFT01 provincial template coverage report JSON.")
    s2pft02_hk_mo.add_argument("--jurisdiction-profiles", required=True, help="HK/MO profile JSON list or object with jurisdiction_profiles.")
    s2pft02_hk_mo.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pft02_hk_mo.add_argument("--json", action="store_true", help="Print JSON HK/MO profile report.")

    s2pft03_cities = subparsers.add_parser(
        "stage2-key-city-coverage",
        help="Run S2PFT03/S2P5T03 first key-city metadata-only coverage evidence.",
    )
    s2pft03_cities.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pft03_cities.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pft03_cities.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pft03_cities.add_argument("--hk-mo-profile-report", required=True, help="Passing S2PFT02 HK/MO profile report JSON.")
    s2pft03_cities.add_argument("--city-records", required=True, help="Key city metadata JSON list or object with city_records.")
    s2pft03_cities.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pft03_cities.add_argument("--json", action="store_true", help="Print JSON key-city coverage report.")

    s2pft04_zones = subparsers.add_parser(
        "stage2-special-zone-discovery",
        help="Run S2PFT04/S2P5T04 special-zone metadata-only discovery evidence.",
    )
    s2pft04_zones.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pft04_zones.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pft04_zones.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pft04_zones.add_argument("--key-city-coverage-report", required=True, help="Passing S2PFT03 key-city coverage report JSON.")
    s2pft04_zones.add_argument("--zone-records", required=True, help="Special-zone metadata JSON list or object with zone_records.")
    s2pft04_zones.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pft04_zones.add_argument("--json", action="store_true", help="Print JSON special-zone discovery report.")

    s2pft05_d3_full = subparsers.add_parser(
        "stage2-d3-full-governance-qualification",
        help="Run S2PFT05/S2P5T05 D3 full governance qualification evidence without production inclusion.",
    )
    s2pft05_d3_full.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pft05_d3_full.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pft05_d3_full.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pft05_d3_full.add_argument("--d3-readiness-review-report", required=True, help="Passing S2PDT04 D3 readiness review report JSON.")
    s2pft05_d3_full.add_argument("--provincial-template-coverage-report", required=True, help="Passing S2PFT01 provincial coverage report JSON.")
    s2pft05_d3_full.add_argument("--hk-mo-profile-report", required=True, help="Passing S2PFT02 HK/MO profile report JSON.")
    s2pft05_d3_full.add_argument("--key-city-coverage-report", required=True, help="Passing S2PFT03 key-city coverage report JSON.")
    s2pft05_d3_full.add_argument("--special-zone-discovery-report", required=True, help="Passing S2PFT04 special-zone discovery report JSON.")
    s2pft05_d3_full.add_argument("--governance-records", required=True, help="D3 governance records JSON list or object with governance_records.")
    s2pft05_d3_full.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pft05_d3_full.add_argument("--json", action="store_true", help="Print JSON D3 full governance qualification report.")

    s2pgt01_packets = subparsers.add_parser(
        "stage2-evidence-packet-v2-compatibility",
        help="Run S2PGT01 EvidencePacket V2 compatibility evidence without public schema or production side effects.",
    )
    s2pgt01_packets.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pgt01_packets.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pgt01_packets.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pgt01_packets.add_argument("--source-domain-reports", required=True, help="Source-domain reports JSON list or object with source_domain_reports.")
    s2pgt01_packets.add_argument("--packet-records", required=True, help="EvidencePacket input records JSON list or object with packet_records.")
    s2pgt01_packets.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pgt01_packets.add_argument("--json", action="store_true", help="Print JSON EvidencePacket V2 compatibility report.")

    s2pgt02_graph = subparsers.add_parser(
        "stage2-knowledge-graph-spine",
        help="Run S2PGT02 private identity and knowledge-graph spine evidence without schema or production side effects.",
    )
    s2pgt02_graph.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pgt02_graph.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pgt02_graph.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pgt02_graph.add_argument("--evidence-packet-report", required=True, help="Passing S2PGT01 EvidencePacket report JSON.")
    s2pgt02_graph.add_argument("--identity-records", required=True, help="Identity records JSON list or object with identity_records.")
    s2pgt02_graph.add_argument("--relation-records", required=True, help="Relation records JSON list or object with relation_records.")
    s2pgt02_graph.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pgt02_graph.add_argument("--json", action="store_true", help="Print JSON knowledge-graph spine report.")

    s2pgt03_routing = subparsers.add_parser(
        "stage2-source-board-routing",
        help="Run S2PGT03 private D1-D4 to B1-B6 routing evidence without schema or production side effects.",
    )
    s2pgt03_routing.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pgt03_routing.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pgt03_routing.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pgt03_routing.add_argument("--evidence-packet-report", required=True, help="Passing S2PGT01 EvidencePacket report JSON.")
    s2pgt03_routing.add_argument("--route-records", required=True, help="Route records JSON list or object with route_records.")
    s2pgt03_routing.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pgt03_routing.add_argument("--json", action="store_true", help="Print JSON source-board routing report.")

    s2pgt04_delta = subparsers.add_parser(
        "stage2-delta-resonance",
        help="Run S2PGT04 private frontier delta and signal resonance evidence without schema or production side effects.",
    )
    s2pgt04_delta.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pgt04_delta.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pgt04_delta.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pgt04_delta.add_argument("--routing-report", required=True, help="Passing S2PGT03 source-board routing report JSON.")
    s2pgt04_delta.add_argument("--delta-records", required=True, help="Delta records JSON list or object with delta_records.")
    s2pgt04_delta.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pgt04_delta.add_argument("--json", action="store_true", help="Print JSON delta/resonance report.")

    s2pgt05_calibration = subparsers.add_parser(
        "stage2-cross-board-calibration",
        help="Run S2PGT05 private cross-board calibration and explainable queue evidence without mutating production queues.",
    )
    s2pgt05_calibration.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pgt05_calibration.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pgt05_calibration.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pgt05_calibration.add_argument("--delta-resonance-report", required=True, help="Passing S2PGT04 delta/resonance report JSON.")
    s2pgt05_calibration.add_argument("--queue-candidates", required=True, help="Queue candidate records JSON list or object with queue_candidate_records.")
    s2pgt05_calibration.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pgt05_calibration.add_argument("--json", action="store_true", help="Print JSON calibration report.")

    s2pit01_user_center = subparsers.add_parser(
        "stage2-user-center",
        help="Build S2PIT01 Chinese user-center and one-edit-entry evidence without production side effects.",
    )
    s2pit01_user_center.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pit01_user_center.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pit01_user_center.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pit01_user_center.add_argument("--controls", help="Path to owner_controls.yaml.")
    s2pit01_user_center.add_argument("--storage-inspect-report", required=True, help="Passing read-only storage inspect report JSON.")
    s2pit01_user_center.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pit01_user_center.add_argument("--json", action="store_true", help="Print JSON user-center report.")

    s2pit02_dashboard = subparsers.add_parser(
        "stage2-runtime-dashboard",
        help="Build S2PIT02 local-only runtime dashboard evidence from existing reports.",
    )
    s2pit02_dashboard.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pit02_dashboard.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pit02_dashboard.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pit02_dashboard.add_argument("--user-center-report", required=True, help="Passing S2PIT01 user-center report JSON.")
    s2pit02_dashboard.add_argument("--runtime-audit-report", required=True, help="Passing runtime-audit report JSON.")
    s2pit02_dashboard.add_argument("--watchdog-report", required=True, help="Passing watchdog report JSON.")
    s2pit02_dashboard.add_argument("--storage-inspect-report", required=True, help="Passing read-only storage inspect report JSON.")
    s2pit02_dashboard.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pit02_dashboard.add_argument(
        "--owner-status-summary",
        required=True,
        help="Required shallow GitHub user-center mail/queue status summary JSON.",
    )
    s2pit02_dashboard.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pit02_dashboard.add_argument("--json", action="store_true", help="Print JSON runtime dashboard report.")

    s2pit03_source_model = subparsers.add_parser(
        "stage2-source-model-view",
        help="Build S2PIT03 local source, board, parameter, and queue view evidence.",
    )
    s2pit03_source_model.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pit03_source_model.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pit03_source_model.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pit03_source_model.add_argument("--user-center-report", required=True, help="Passing S2PIT01 user-center report JSON.")
    s2pit03_source_model.add_argument("--source-domains", required=True, help="D1-D4 source-domain view records JSON.")
    s2pit03_source_model.add_argument("--reading-boards", required=True, help="B1-B6 reading-board view records JSON.")
    s2pit03_source_model.add_argument("--parameters", required=True, help="Parameter disclosure records JSON.")
    s2pit03_source_model.add_argument("--queue-view", required=True, help="Queue view records JSON.")
    s2pit03_source_model.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pit03_source_model.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pit03_source_model.add_argument("--json", action="store_true", help="Print JSON source/model view report.")

    s2pit04_content_ledger = subparsers.add_parser(
        "stage2-content-ledger-view",
        help="Build S2PIT04 local content, mail, review, action, asset, and ROI ledger evidence.",
    )
    s2pit04_content_ledger.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pit04_content_ledger.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pit04_content_ledger.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pit04_content_ledger.add_argument("--runtime-dashboard-report", required=True, help="Passing S2PIT02 runtime dashboard report JSON.")
    s2pit04_content_ledger.add_argument("--source-model-view-report", required=True, help="Passing S2PIT03 source/model view report JSON.")
    s2pit04_content_ledger.add_argument("--lifecycle-state-report", required=True, help="Passing S2PJT01 lifecycle state report JSON.")
    s2pit04_content_ledger.add_argument("--review-schedule-report", required=True, help="Passing S2PJT02 review schedule report JSON.")
    s2pit04_content_ledger.add_argument("--action-roi-report", required=True, help="Passing S2PJT03 action/asset/ROI report JSON.")
    s2pit04_content_ledger.add_argument("--ledger-records", required=True, help="Ledger records JSON list or object with ledger_records.")
    s2pit04_content_ledger.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pit04_content_ledger.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pit04_content_ledger.add_argument("--json", action="store_true", help="Print JSON content ledger report.")

    s2pkt01_mail_contract = subparsers.add_parser(
        "stage2-mail-contract",
        help="Build S2PKT01 local M1-M4 shared mail contract readiness evidence without sending mail.",
    )
    s2pkt01_mail_contract.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pkt01_mail_contract.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pkt01_mail_contract.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pkt01_mail_contract.add_argument("--content-quality-report", required=True, help="Passing S2PHT05 content quality gate report JSON.")
    s2pkt01_mail_contract.add_argument("--content-ledger-report", required=True, help="Passing S2PIT04 content ledger report JSON.")
    s2pkt01_mail_contract.add_argument("--action-roi-report", required=True, help="Passing S2PJT03 action/asset/ROI report JSON.")
    s2pkt01_mail_contract.add_argument("--mail-contracts", required=True, help="Mail contract records JSON list or object with mail_contracts.")
    s2pkt01_mail_contract.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pkt01_mail_contract.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pkt01_mail_contract.add_argument("--json", action="store_true", help="Print JSON mail contract report.")

    s2pkt02_m1_mail = subparsers.add_parser(
        "stage2-m1-mail",
        help="Build S2PKT02 local M1 science/theory frontier mail evidence without sending mail.",
    )
    s2pkt02_m1_mail.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pkt02_m1_mail.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pkt02_m1_mail.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pkt02_m1_mail.add_argument("--mail-contract-report", required=True, help="Passing S2PKT01 mail contract report JSON.")
    s2pkt02_m1_mail.add_argument("--content-quality-report", required=True, help="Passing S2PHT05 content quality gate report JSON.")
    s2pkt02_m1_mail.add_argument("--content-ledger-report", required=True, help="Passing S2PIT04 content ledger report JSON.")
    s2pkt02_m1_mail.add_argument("--action-roi-report", required=True, help="Passing S2PJT03 action/asset/ROI report JSON.")
    s2pkt02_m1_mail.add_argument("--m1-mail-record", required=True, help="M1 mail evidence record JSON object.")
    s2pkt02_m1_mail.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pkt02_m1_mail.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pkt02_m1_mail.add_argument("--json", action="store_true", help="Print JSON M1 mail report.")

    s2pkt03_m2_mail = subparsers.add_parser(
        "stage2-m2-mail",
        help="Build S2PKT03 local M2 engineering/product/industry frontier mail evidence without sending mail.",
    )
    s2pkt03_m2_mail.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pkt03_m2_mail.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pkt03_m2_mail.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pkt03_m2_mail.add_argument("--mail-contract-report", required=True, help="Passing S2PKT01 mail contract report JSON.")
    s2pkt03_m2_mail.add_argument("--content-quality-report", required=True, help="Passing S2PHT05 content quality gate report JSON.")
    s2pkt03_m2_mail.add_argument("--content-ledger-report", required=True, help="Passing S2PIT04 content ledger report JSON.")
    s2pkt03_m2_mail.add_argument("--action-roi-report", required=True, help="Passing S2PJT03 action/asset/ROI report JSON.")
    s2pkt03_m2_mail.add_argument("--m2-mail-record", required=True, help="M2 mail evidence record JSON object.")
    s2pkt03_m2_mail.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pkt03_m2_mail.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pkt03_m2_mail.add_argument("--json", action="store_true", help="Print JSON M2 mail report.")

    s2pkt04_m3_mail = subparsers.add_parser(
        "stage2-m3-mail",
        help="Build S2PKT04 local M3 policy/capital/geopolitical frontier mail evidence without sending mail.",
    )
    s2pkt04_m3_mail.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pkt04_m3_mail.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pkt04_m3_mail.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pkt04_m3_mail.add_argument("--mail-contract-report", required=True, help="Passing S2PKT01 mail contract report JSON.")
    s2pkt04_m3_mail.add_argument("--content-quality-report", required=True, help="Passing S2PHT05 content quality gate report JSON.")
    s2pkt04_m3_mail.add_argument("--content-ledger-report", required=True, help="Passing S2PIT04 content ledger report JSON.")
    s2pkt04_m3_mail.add_argument("--action-roi-report", required=True, help="Passing S2PJT03 action/asset/ROI report JSON.")
    s2pkt04_m3_mail.add_argument("--m3-mail-record", required=True, help="M3 mail evidence record JSON object.")
    s2pkt04_m3_mail.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pkt04_m3_mail.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pkt04_m3_mail.add_argument("--json", action="store_true", help="Print JSON M3 mail report.")

    s2pkt05_m4_mail = subparsers.add_parser(
        "stage2-m4-mail",
        help="Build S2PKT05 local M4 3+1 orchestration and watermark evidence without sending mail.",
    )
    s2pkt05_m4_mail.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pkt05_m4_mail.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pkt05_m4_mail.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pkt05_m4_mail.add_argument("--mail-contract-report", required=True, help="Passing S2PKT01 mail contract report JSON.")
    s2pkt05_m4_mail.add_argument("--m1-mail-report", required=True, help="Passing S2PKT02 M1 mail report JSON.")
    s2pkt05_m4_mail.add_argument("--m2-mail-report", required=True, help="Passing S2PKT03 M2 mail report JSON.")
    s2pkt05_m4_mail.add_argument("--m3-mail-report", required=True, help="Passing S2PKT04 M3 mail report JSON.")
    s2pkt05_m4_mail.add_argument("--content-ledger-report", required=True, help="Passing S2PIT04 content ledger report JSON.")
    s2pkt05_m4_mail.add_argument("--action-roi-report", required=True, help="Passing S2PJT03 action/asset/ROI report JSON.")
    s2pkt05_m4_mail.add_argument("--review-schedule-report", required=True, help="Passing S2PJT02 review schedule report JSON.")
    s2pkt05_m4_mail.add_argument("--m4-orchestration-record", required=True, help="M4 orchestration evidence record JSON object.")
    s2pkt05_m4_mail.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pkt05_m4_mail.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pkt05_m4_mail.add_argument("--json", action="store_true", help="Print JSON M4 orchestration report.")

    s2pjt01_lifecycle = subparsers.add_parser(
        "stage2-lifecycle-state",
        help="Build S2PJT01 review/action/asset/conversion/mastery lifecycle state evidence without DB migration.",
    )
    s2pjt01_lifecycle.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pjt01_lifecycle.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pjt01_lifecycle.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pjt01_lifecycle.add_argument("--runtime-dashboard-report", required=True, help="Passing S2PIT02 runtime dashboard report JSON.")
    s2pjt01_lifecycle.add_argument("--lifecycle-records", required=True, help="Lifecycle records JSON list or object with lifecycle_records.")
    s2pjt01_lifecycle.add_argument("--migration-plan", required=True, help="Dry-run migration plan JSON with rollback/count conservation proof.")
    s2pjt01_lifecycle.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pjt01_lifecycle.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pjt01_lifecycle.add_argument("--json", action="store_true", help="Print JSON lifecycle state report.")

    s2pjt02_review_schedule = subparsers.add_parser(
        "stage2-review-schedule",
        help="Build S2PJT02 local review schedule and due queue evidence without installing a scheduler.",
    )
    s2pjt02_review_schedule.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pjt02_review_schedule.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pjt02_review_schedule.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pjt02_review_schedule.add_argument("--lifecycle-state-report", required=True, help="Passing S2PJT01 lifecycle state report JSON.")
    s2pjt02_review_schedule.add_argument("--review-records", required=True, help="Review records JSON list or object with review_records.")
    s2pjt02_review_schedule.add_argument("--schedule-policy", help="Optional schedule policy JSON; defaults to 1/3/7/14/30/90 dry-run.")
    s2pjt02_review_schedule.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pjt02_review_schedule.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pjt02_review_schedule.add_argument("--json", action="store_true", help="Print JSON review schedule report.")

    s2pjt03_action_roi = subparsers.add_parser(
        "stage2-action-roi-ledger",
        help="Build S2PJT03 local action, capability asset, and ROI ledger evidence without production side effects.",
    )
    s2pjt03_action_roi.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pjt03_action_roi.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pjt03_action_roi.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pjt03_action_roi.add_argument("--review-schedule-report", required=True, help="Passing S2PJT02 review schedule report JSON.")
    s2pjt03_action_roi.add_argument("--action-records", required=True, help="Action records JSON list or object with action_records.")
    s2pjt03_action_roi.add_argument("--capability-assets", required=True, help="Capability assets JSON list or object with capability_assets.")
    s2pjt03_action_roi.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pjt03_action_roi.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pjt03_action_roi.add_argument("--json", action="store_true", help="Print JSON action/asset/ROI ledger report.")

    s2pjt04_weekly = subparsers.add_parser(
        "stage2-weekly-report",
        help="Build S2PJT04 local weekly synthesis and attention reallocation evidence without production side effects.",
    )
    s2pjt04_weekly.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pjt04_weekly.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pjt04_weekly.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pjt04_weekly.add_argument("--week-start", required=True, help="Weekly report start date YYYY-MM-DD.")
    s2pjt04_weekly.add_argument("--week-end", required=True, help="Weekly report end date YYYY-MM-DD.")
    s2pjt04_weekly.add_argument("--action-roi-report", required=True, help="Passing S2PJT03 action/asset/ROI report JSON.")
    s2pjt04_weekly.add_argument("--weekly-items", required=True, help="Weekly item records JSON list or object with weekly_items.")
    s2pjt04_weekly.add_argument("--weekly-sections", required=True, help="Weekly sections JSON mapping.")
    s2pjt04_weekly.add_argument("--next-week-focus", required=True, help="Next week focus JSON list or object with next_week_focus.")
    s2pjt04_weekly.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pjt04_weekly.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pjt04_weekly.add_argument("--json", action="store_true", help="Print JSON weekly report.")

    s2pjt05_monthly = subparsers.add_parser(
        "stage2-monthly-report",
        help="Build S2PJT05 local monthly cognitive delta, capability, ROI, and forecast evidence without production side effects.",
    )
    s2pjt05_monthly.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pjt05_monthly.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pjt05_monthly.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pjt05_monthly.add_argument("--month-start", required=True, help="Monthly report start date YYYY-MM-DD.")
    s2pjt05_monthly.add_argument("--month-end", required=True, help="Monthly report end date YYYY-MM-DD.")
    s2pjt05_monthly.add_argument("--weekly-reports", required=True, help="Passing S2PJT04 reports JSON list or object with weekly_reports.")
    s2pjt05_monthly.add_argument("--cognitive-snapshots", required=True, help="Monthly start/end cognitive snapshots JSON mapping.")
    s2pjt05_monthly.add_argument("--monthly-sections", required=True, help="Monthly sections JSON mapping.")
    s2pjt05_monthly.add_argument("--capability-growth", required=True, help="Capability growth JSON list or object with capability_growth.")
    s2pjt05_monthly.add_argument("--economic-conversions", required=True, help="Economic conversions JSON list or object with economic_conversions.")
    s2pjt05_monthly.add_argument("--forecast-reviews", required=True, help="Forecast reviews JSON list or object with forecast_reviews.")
    s2pjt05_monthly.add_argument("--next-month-focus", required=True, help="Next month focus JSON list or object with next_month_focus.")
    s2pjt05_monthly.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pjt05_monthly.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pjt05_monthly.add_argument("--json", action="store_true", help="Print JSON monthly report.")

    s2pht05_quality = subparsers.add_parser(
        "stage2-content-quality-gate",
        help="Build S2PHT05 local semantic content quality gate evidence without production side effects.",
    )
    s2pht05_quality.add_argument("--state-dir", required=True, help="Local ADP state directory.")
    s2pht05_quality.add_argument("--date", required=True, help="Sydney service date YYYY-MM-DD.")
    s2pht05_quality.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2pht05_quality.add_argument("--dependency-receipts", required=True, help="S2PHT01-S2PHT04 dependency receipts JSON list or object with dependency_receipts.")
    s2pht05_quality.add_argument("--gold-items", required=True, help="Ten-item semantic gold set JSON list or object with gold_items.")
    s2pht05_quality.add_argument("--stage1-regression-checks", required=True, help="Stage 1 arXiv/evidence/email regression checks JSON list or object with stage1_regression_checks.")
    s2pht05_quality.add_argument("--manual-review-samples", required=True, help="Manual review samples JSON list or object with manual_review_samples.")
    s2pht05_quality.add_argument("--production-gate-state", help="Optional production gate state JSON; all production side-effect flags must be false.")
    s2pht05_quality.add_argument("--no-write", action="store_true", help="Run without writing local state/artifacts.")
    s2pht05_quality.add_argument("--json", action="store_true", help="Print JSON content quality gate report.")

    s2plt01_replay_execution = subparsers.add_parser(
        "stage2-replay-payload-execution",
        help="Build S2PLT01 no-production replay payload execution evidence from explicit records.",
    )
    s2plt01_replay_execution.add_argument("--input", required=True, help="JSON object with replay, mail preview, and source terminal evidence records.")
    s2plt01_replay_execution.add_argument("--execution-id", required=True, help="Stable local execution package ID.")
    s2plt01_replay_execution.add_argument("--generated-at", required=True, help="Evidence timestamp.")
    s2plt01_replay_execution.add_argument("--generated-by", default="codex-stage2-local", help="Evidence producer ID.")
    s2plt01_replay_execution.add_argument(
        "--evidence-mode",
        choices=("actual_replay_evidence", "fixture_replay_contract"),
        default="actual_replay_evidence",
        help="Evidence mode label. Neither mode enables production side effects.",
    )
    s2plt01_replay_execution.add_argument("--evidence-ref", action="append", default=[], help="Durable evidence ref. May be repeated.")
    s2plt01_replay_execution.add_argument("--json", action="store_true", help="Print JSON replay payload execution report.")

    s2plt01_independent_review = subparsers.add_parser(
        "stage2-independent-replay-review",
        help="Build S2PLT01 no-production independent replay review evidence from a replay execution report.",
    )
    s2plt01_independent_review.add_argument("--execution-report", required=True, help="S2PLT01 replay payload execution report JSON.")
    s2plt01_independent_review.add_argument("--review-id", required=True, help="Stable independent review package ID.")
    s2plt01_independent_review.add_argument("--generated-at", required=True, help="Review timestamp.")
    s2plt01_independent_review.add_argument("--reviewer-id", required=True, help="Reviewer identity label.")
    s2plt01_independent_review.add_argument("--reviewer-role", required=True, help="Reviewer role label.")
    s2plt01_independent_review.add_argument(
        "--reviewer-involved-in-implementation",
        action="store_true",
        help="Set only when the reviewer was involved in S2PLT01 implementation; this blocks the review package.",
    )
    s2plt01_independent_review.add_argument("--ci-evidence-ref", action="append", default=[], help="CI/workflow evidence ref. May be repeated.")
    s2plt01_independent_review.add_argument("--evidence-ref", action="append", default=[], help="Durable review evidence ref. May be repeated.")
    s2plt01_independent_review.add_argument("--json", action="store_true", help="Print JSON independent replay review report.")

    s2plt01_terminal_audit = subparsers.add_parser(
        "audit-s2plt01-terminal-acceptance",
        help="Audit current S2PLT01 terminal acceptance evidence without accepting S2PLT01.",
    )
    s2plt01_terminal_audit.add_argument("--repo-root", default=".", help="Repository root containing governance manifests.")
    s2plt01_terminal_audit.add_argument("--json", action="store_true", help="Print JSON terminal acceptance audit state.")

    s2plt01_terminal_acceptance = subparsers.add_parser(
        "validate-s2plt01-terminal-acceptance",
        help="Validate future S2PLT01 terminal acceptance artifact without accepting production.",
    )
    s2plt01_terminal_acceptance.add_argument("--repo-root", default=".", help="Repository root containing final-bundle artifacts.")
    s2plt01_terminal_acceptance.add_argument("--json", action="store_true", help="Print JSON artifact validation state.")

    s2plt02_terminal_audit = subparsers.add_parser(
        "audit-s2plt02-terminal-readiness",
        help="Audit current S2PLT02 terminal readiness without accepting S2PLT02.",
    )
    s2plt02_terminal_audit.add_argument(
        "--generated-at",
        default="2026-06-29T10:35:11+10:00",
        help="Evidence timestamp for the deterministic audit payload.",
    )
    s2plt02_terminal_audit.add_argument("--json", action="store_true", help="Print JSON S2PLT02 terminal-readiness audit state.")

    s2plt02_dry_run_second_day_audit = subparsers.add_parser(
        "audit-s2plt02-dry-run-second-day",
        help="Audit a second-day local dry-run trace without granting S2PLT02 terminal delivery credit.",
    )
    s2plt02_dry_run_second_day_audit.add_argument(
        "--state-dir",
        default=None,
        help="ADP state directory containing runs/YYYYMMDD reports; defaults to ~/.adp/arxiv-daily-push.",
    )
    s2plt02_dry_run_second_day_audit.add_argument(
        "--service-date",
        default="2026-06-29",
        help="Service date to audit as a dry-run-only trace.",
    )
    s2plt02_dry_run_second_day_audit.add_argument("--json", action="store_true", help="Print JSON dry-run second-day audit state.")

    s2plt02_real_proof_capture_readiness = subparsers.add_parser(
        "audit-s2plt02-real-proof-capture-readiness",
        help="Audit whether real S2PLT02 SMTP/scheduler proof capture can proceed without enabling production.",
    )
    s2plt02_real_proof_capture_readiness.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing final-bundle artifacts.",
    )
    s2plt02_real_proof_capture_readiness.add_argument(
        "--state-dir",
        default=None,
        help="ADP state directory containing runs/YYYYMMDD reports; defaults to ~/.adp/arxiv-daily-push.",
    )
    s2plt02_real_proof_capture_readiness.add_argument(
        "--service-date",
        default="2026-06-29",
        help="Service date whose dry-run trace should be audited as nonterminal.",
    )
    s2plt02_real_proof_capture_readiness.add_argument(
        "--launchctl-disabled-file",
        default=None,
        help="Optional sanitized launchctl print-disabled text file for deterministic validation.",
    )
    s2plt02_real_proof_capture_readiness.add_argument("--json", action="store_true", help="Print JSON real-proof capture readiness state.")

    s2plt02_real_proof_capture_authorization = subparsers.add_parser(
        "validate-s2plt02-real-proof-capture-authorization",
        help="Validate the future S2PLT02 owner authorization artifact without enabling SMTP or scheduler.",
    )
    s2plt02_real_proof_capture_authorization.add_argument(
        "--path",
        default="FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json",
        help="Path to FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json.",
    )
    s2plt02_real_proof_capture_authorization.add_argument(
        "--expected-readiness-state-hash",
        default=None,
        help="Optional readiness state hash that the authorization artifact must bind.",
    )
    s2plt02_real_proof_capture_authorization.add_argument(
        "--json",
        action="store_true",
        help="Print JSON authorization validation state.",
    )

    s2plt02_real_proof_capture_authorization_owner_packet = subparsers.add_parser(
        "build-s2plt02-real-proof-capture-authorization-owner-packet",
        help="Print the owner action packet for explicit S2PLT02 real SMTP/scheduler proof capture authorization.",
    )
    s2plt02_real_proof_capture_authorization_owner_packet.add_argument(
        "--readiness-state-hash",
        default="",
        help="Optional current S2PLT02 real-proof capture readiness state hash to bind in the packet.",
    )
    s2plt02_real_proof_capture_authorization_owner_packet.add_argument(
        "--json",
        action="store_true",
        help="Print JSON owner action packet.",
    )

    s2plt02_real_proof_capture_authorization_draft = subparsers.add_parser(
        "build-s2plt02-real-proof-capture-authorization-artifact-draft",
        help=(
            "Build a stdout-only S2PLT02 real-proof capture authorization artifact draft "
            "from explicit owner inputs."
        ),
    )
    s2plt02_real_proof_capture_authorization_draft.add_argument(
        "--owner-id",
        required=True,
        help="Owner identity label to embed in the future authorization artifact.",
    )
    s2plt02_real_proof_capture_authorization_draft.add_argument(
        "--owner-role",
        required=True,
        choices=("owner", "content_owner + engineering_owner"),
        help="Owner role to embed in the future authorization artifact.",
    )
    s2plt02_real_proof_capture_authorization_draft.add_argument(
        "--generated-at",
        required=True,
        help="Authorization artifact timestamp to embed in the draft.",
    )
    s2plt02_real_proof_capture_authorization_draft.add_argument(
        "--readiness-state-hash",
        required=True,
        help="Current S2PLT02 real-proof capture readiness state hash to bind in the draft.",
    )
    s2plt02_real_proof_capture_authorization_draft.add_argument(
        "--json",
        action="store_true",
        help="Print JSON draft wrapper. The command never writes the live authorization artifact.",
    )

    s2plt02_real_scheduler_proof = subparsers.add_parser(
        "validate-s2plt02-real-scheduler-proof",
        help="Validate a real scheduler proof input without enabling scheduler or accepting production.",
    )
    s2plt02_real_scheduler_proof.add_argument(
        "--scheduler-proof",
        required=True,
        help="Real launchd scheduler proof manifest JSON to validate as S2PLT02 input.",
    )
    s2plt02_real_scheduler_proof.add_argument(
        "--json",
        action="store_true",
        help="Print JSON scheduler proof validation state.",
    )
    s2plt02_real_delivery_manifest = subparsers.add_parser(
        "validate-s2plt02-real-delivery-manifest",
        help="Validate one real M1-M4 delivery manifest input without sending mail or writing artifacts.",
    )
    s2plt02_real_delivery_manifest.add_argument(
        "--delivery-manifest",
        required=True,
        help="Real M1-M4 delivery manifest JSON to validate as S2PLT02 input.",
    )
    s2plt02_real_delivery_manifest.add_argument(
        "--json",
        action="store_true",
        help="Print JSON delivery manifest validation state.",
    )
    s2plt02_normalized_delivery_manifest = subparsers.add_parser(
        "build-s2plt02-normalized-delivery-manifest",
        help="Build a stdout-only normalized M1-M4 delivery manifest input without sending mail or writing artifacts.",
    )
    s2plt02_normalized_delivery_manifest.add_argument(
        "--raw-manifest",
        required=True,
        help="Historical or raw real-delivery manifest JSON to normalize.",
    )
    s2plt02_normalized_delivery_manifest.add_argument(
        "--raw-manifest-ref",
        required=True,
        help="Repository evidence ref for the raw manifest.",
    )
    s2plt02_normalized_delivery_manifest.add_argument(
        "--normalized-manifest-ref",
        required=True,
        help="Target evidence ref to embed in the normalized manifest.",
    )
    s2plt02_normalized_delivery_manifest.add_argument(
        "--normalized-at",
        required=True,
        help="Normalization timestamp.",
    )
    s2plt02_normalized_delivery_manifest.add_argument(
        "--json",
        action="store_true",
        help="Print JSON normalization wrapper.",
    )
    s2plt02_terminal_delivery_inputs = subparsers.add_parser(
        "audit-s2plt02-terminal-delivery-inputs",
        help="Audit current S2PLT02 terminal proof inputs without writing the proof artifact.",
    )
    s2plt02_terminal_delivery_inputs.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing final-bundle artifacts.",
    )
    s2plt02_terminal_delivery_inputs.add_argument(
        "--generated-at",
        required=True,
        help="Inventory timestamp.",
    )
    s2plt02_terminal_delivery_inputs.add_argument(
        "--json",
        action="store_true",
        help="Print JSON S2PLT02 terminal delivery input inventory.",
    )

    s2plt02_terminal_delivery_capture_plan = subparsers.add_parser(
        "plan-s2plt02-terminal-delivery-proof-capture",
        help="Print the safe S2PLT02 terminal proof capture plan without sending mail or enabling scheduler.",
    )
    s2plt02_terminal_delivery_capture_plan.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing final-bundle artifacts.",
    )
    s2plt02_terminal_delivery_capture_plan.add_argument(
        "--generated-at",
        required=True,
        help="Capture-plan timestamp.",
    )
    s2plt02_terminal_delivery_capture_plan.add_argument(
        "--json",
        action="store_true",
        help="Print JSON S2PLT02 terminal delivery proof capture plan.",
    )

    s2plt02_terminal_delivery_proof = subparsers.add_parser(
        "validate-s2plt02-terminal-delivery-proof",
        help="Validate future S2PLT02 terminal delivery proof artifact without accepting production.",
    )
    s2plt02_terminal_delivery_proof.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing final-bundle artifacts.",
    )
    s2plt02_terminal_delivery_proof.add_argument(
        "--json",
        action="store_true",
        help="Print JSON S2PLT02 terminal delivery proof validation state.",
    )
    s2plt02_terminal_delivery_proof_draft = subparsers.add_parser(
        "build-s2plt02-terminal-delivery-proof-artifact-draft",
        help=(
            "Build a stdout-only S2PLT02 terminal delivery proof artifact candidate "
            "from explicit delivery and scheduler evidence inputs."
        ),
    )
    s2plt02_terminal_delivery_proof_draft.add_argument(
        "--generated-at",
        required=True,
        help="Terminal proof candidate timestamp.",
    )
    s2plt02_terminal_delivery_proof_draft.add_argument(
        "--delivery-manifest",
        action="append",
        required=True,
        help="Real M1-M4 delivery manifest JSON. Pass exactly two consecutive service-date manifests.",
    )
    s2plt02_terminal_delivery_proof_draft.add_argument(
        "--scheduler-proof",
        required=True,
        help="Real launchd scheduler proof manifest JSON.",
    )
    s2plt02_terminal_delivery_proof_draft.add_argument("--json", action="store_true", help="Print JSON draft wrapper.")

    s2plt03_resilience_audit = subparsers.add_parser(
        "audit-s2plt03-resilience-readiness",
        help="Audit current S2PLT03 resilience readiness without accepting S2PLT03.",
    )
    s2plt03_resilience_audit.add_argument(
        "--generated-at",
        default="2026-06-29T12:12:00+10:00",
        help="Evidence timestamp for the deterministic audit payload.",
    )
    s2plt03_resilience_audit.add_argument("--json", action="store_true", help="Print JSON S2PLT03 resilience-readiness audit state.")

    s2plt03_terminal_resilience_proof = subparsers.add_parser(
        "validate-s2plt03-terminal-resilience-proof",
        help="Validate future S2PLT03 terminal resilience proof artifact without accepting production.",
    )
    s2plt03_terminal_resilience_proof.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing final-bundle artifacts.",
    )
    s2plt03_terminal_resilience_proof.add_argument(
        "--json",
        action="store_true",
        help="Print JSON S2PLT03 terminal resilience proof validation state.",
    )

    final_reviewer_assignment = subparsers.add_parser(
        "validate-final-reviewer-assignment",
        help="Validate the S2PMT07 independent final reviewer assignment artifact without production side effects.",
    )
    final_reviewer_assignment.add_argument(
        "--path",
        default=S2PMT07_INDEPENDENT_FINAL_REVIEWER_ASSIGNMENT_ARTIFACT_PATH,
        help="Path to FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json.",
    )
    final_reviewer_assignment.add_argument("--json", action="store_true", help="Print JSON validation state.")

    p0_p1_zero_proof = subparsers.add_parser(
        "validate-p0-p1-zero-proof",
        help="Validate the S2PMT07 P0/P1 zero-proof artifact without production side effects.",
    )
    p0_p1_zero_proof.add_argument(
        "--path",
        default=S2PMT07_P0_P1_ZERO_PROOF_ARTIFACT_PATH,
        help="Path to FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json.",
    )
    p0_p1_zero_proof.add_argument("--json", action="store_true", help="Print JSON validation state.")

    final_command_execution = subparsers.add_parser(
        "validate-final-command-execution",
        help="Validate the S2PMT07 final-command execution artifact without production side effects.",
    )
    final_command_execution.add_argument(
        "--path",
        default="FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json",
        help="Path to FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json.",
    )
    final_command_execution.add_argument("--json", action="store_true", help="Print JSON validation state.")

    final_bundle_manifest = subparsers.add_parser(
        "validate-final-bundle-manifest",
        help="Validate the S2PMT07 final acceptance bundle manifest artifact without production side effects.",
    )
    final_bundle_manifest.add_argument(
        "--path",
        default="FINAL_ACCEPTANCE_BUNDLE/manifest.json",
        help="Path to FINAL_ACCEPTANCE_BUNDLE/manifest.json.",
    )
    final_bundle_manifest.add_argument("--json", action="store_true", help="Print JSON validation state.")

    s2plt04_completion_report = subparsers.add_parser(
        "validate-s2plt04-completion-report",
        help="Validate the S2PMT07 S2PLT04 completion report artifact without production side effects.",
    )
    s2plt04_completion_report.add_argument(
        "--path",
        default="FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json",
        help="Path to FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json.",
    )
    s2plt04_completion_report.add_argument("--json", action="store_true", help="Print JSON validation state.")

    s2plt04_completion_evidence_audit = subparsers.add_parser(
        "audit-s2plt04-completion-evidence",
        help="Audit S2PLT04 completion-report source evidence without writing the report.",
    )
    s2plt04_completion_evidence_audit.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing committed S2PLT04 prerequisite artifacts.",
    )
    s2plt04_completion_evidence_audit.add_argument("--json", action="store_true", help="Print JSON audit state.")

    no_production_attestation = subparsers.add_parser(
        "validate-no-production-attestation",
        help="Validate the S2PMT07 no-production side-effect attestation artifact.",
    )
    no_production_attestation.add_argument(
        "--path",
        default="FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json",
        help="Path to FINAL_ACCEPTANCE_BUNDLE/no_production_side_effects.json.",
    )
    no_production_attestation.add_argument("--json", action="store_true", help="Print JSON validation state.")

    next_agent_handoff = subparsers.add_parser(
        "validate-next-agent-handoff",
        help="Validate the S2PMT07 next-agent handoff artifact without production side effects.",
    )
    next_agent_handoff.add_argument(
        "--path",
        default="HANDOFF/00_下一Agent先读.md",
        help="Path to HANDOFF/00_下一Agent先读.md JSON artifact.",
    )
    next_agent_handoff.add_argument("--json", action="store_true", help="Print JSON validation state.")

    final_reviewer_assignment_owner_packet = subparsers.add_parser(
        "build-final-reviewer-assignment-owner-packet",
        help="Print the S2PMT07 owner/coordinator action packet for assigning an independent final reviewer.",
    )
    final_reviewer_assignment_owner_packet.add_argument(
        "--json",
        action="store_true",
        help="Print JSON owner action packet.",
    )

    final_reviewer_assignment_draft = subparsers.add_parser(
        "build-final-reviewer-assignment-artifact-draft",
        help=(
            "Build a stdout-only S2PMT07 independent final reviewer assignment artifact draft "
            "from explicit owner/coordinator inputs."
        ),
    )
    final_reviewer_assignment_draft.add_argument(
        "--reviewer-id",
        required=True,
        help="Independent final reviewer identity label. Must not be codex-current-agent.",
    )
    final_reviewer_assignment_draft.add_argument(
        "--assigned-by",
        required=True,
        choices=("owner_or_coordinator", "owner"),
        help="Assignment authority recorded in the future artifact.",
    )
    final_reviewer_assignment_draft.add_argument(
        "--generated-at",
        required=True,
        help="Assignment artifact timestamp to embed in the draft.",
    )
    final_reviewer_assignment_draft.add_argument(
        "--assignment-scope",
        default="S2PMT07_P0_P1_FINAL_CLOSURE_REVIEW",
        help="Assignment scope. Defaults to the S2PMT07 final closure review scope.",
    )
    final_reviewer_assignment_draft.add_argument(
        "--json",
        action="store_true",
        help="Print JSON draft wrapper. The command never writes the live assignment artifact.",
    )

    final_closure_decision_owner_packet = subparsers.add_parser(
        "build-final-closure-decision-owner-packet",
        help="Print the S2PMT07 owner/reviewer action packet for a future independent final closure decision.",
    )
    final_closure_decision_owner_packet.add_argument(
        "--json",
        action="store_true",
        help="Print JSON owner/reviewer closure decision packet.",
    )

    final_bundle_prerequisites = subparsers.add_parser(
        "plan-final-bundle-prerequisites",
        help="Print the S2PMT07 final-bundle prerequisite execution plan without production side effects.",
    )
    final_bundle_prerequisites.add_argument(
        "--json",
        action="store_true",
        help="Print JSON prerequisite plan.",
    )

    final_acceptance_bundle = subparsers.add_parser(
        "validate-final-acceptance-bundle",
        help="Validate S2PMT07 final acceptance bundle readiness without production side effects.",
    )
    final_acceptance_bundle.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing FINAL_ACCEPTANCE_BUNDLE and HANDOFF artifacts.",
    )
    final_acceptance_bundle.add_argument("--json", action="store_true", help="Print JSON readiness state.")

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
    live_all_arxiv.add_argument("--fetcher", choices=("curl", "urllib"), default="urllib", help="Live arXiv fetch implementation.")
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
    if args.command == "local-runner":
        if args.local_runner_command == "preflight":
            report = build_local_preflight(
                project_root=args.project_root,
                state_dir=args.state_dir,
                generated_at=args.generated_at,
                require_smtp=args.require_smtp,
            )
            errors = validate_production_preflight(report)
            if errors:
                report = {**report, "status": "blocked", "production_run_allowed": False, "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        elif args.local_runner_command == "daily":
            report = run_local_daily(
                project_root=args.project_root,
                state_dir=args.state_dir,
                date=args.date,
                generated_at=args.generated_at,
                max_results_per_category=args.max_results_per_category,
                daily_input_report_path=args.daily_input_report,
                polite_delay_seconds=args.polite_delay_seconds,
                allow_smtp_send=args.allow_smtp_send,
                write=not args.no_write,
            )
        else:
            report = build_launchd_package(
                project_root=args.project_root,
                state_dir=args.state_dir,
                artifact_dir=args.artifact_dir,
                generated_at=args.generated_at,
                write=not args.no_write,
            )
        errors = validate_local_runner_report(report) if report.get("model_id") else []
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            if report.get("run_dir"):
                print(f"- run_dir: {report.get('run_dir')}")
            if report.get("artifact_dir"):
                print(f"- artifact_dir: {report.get('artifact_dir')}")
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
            network_timeout_seconds=args.network_timeout_seconds,
            network_max_attempts=args.network_max_attempts,
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
    if args.command == "fetch-preprint-latest":
        preprint_fetcher = fetch_preprint_details_with_curl if args.fetcher == "curl" else None
        batch = ingest_latest_preprints(
            server=args.server,
            interval=args.interval,
            cursor=args.cursor,
            max_records=args.max_records,
            generated_at=args.generated_at,
            seen_source_ids=args.seen_source_id,
            fetcher=preprint_fetcher,
        )
        errors = validate_preprint_source_batch(batch)
        if args.json:
            print(json.dumps(batch, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(batch["status"])
            print(f"- server: {batch.get('server')}")
            print(f"- new_item_count: {batch.get('new_item_count')}")
            for reason in batch.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if batch["status"] == "pass" and not errors else 2
    if args.command == "fetch-top-journal-latest":
        top_journal_fetcher = fetch_top_journal_rss_with_curl if args.fetcher == "curl" else None
        batch = ingest_latest_top_journal(
            journal=args.journal,
            max_records=args.max_records,
            generated_at=args.generated_at,
            seen_source_ids=args.seen_source_id,
            fetcher=top_journal_fetcher,
        )
        errors = validate_top_journal_source_batch(batch)
        if args.json:
            print(json.dumps(batch, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(batch["status"])
            print(f"- journal: {batch.get('journal')}")
            print(f"- new_item_count: {batch.get('new_item_count')}")
            for reason in batch.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if batch["status"] == "pass" and not errors else 2
    if args.command == "stage2-preprint-gate":
        source_batches = {
            "biorxiv": load_json_mapping(args.biorxiv_batch),
            "medrxiv": load_json_mapping(args.medrxiv_batch),
        }
        replay_report = load_json_mapping(args.replay_report) if args.replay_report else None
        shadow_report = load_json_mapping(args.shadow_report) if args.shadow_report else None
        report = build_s2p1_preprint_promotion_report(
            generated_at=args.generated_at,
            source_batches=source_batches,
            replay_report=replay_report,
            shadow_report=shadow_report,
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "stage2-preprint-shadow-daily":
        source_batches = {
            "biorxiv": load_json_mapping(args.biorxiv_batch),
            "medrxiv": load_json_mapping(args.medrxiv_batch),
        }
        queue = load_json_mapping(args.queue_path) if args.queue_path else None
        report = run_s2p1_preprint_shadow_daily(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            source_batches=source_batches,
            queue=queue,
            write=not args.no_write,
        )
        errors = validate_s2p1_shadow_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-preprint-replay-shadow":
        preprint_fetcher = fetch_preprint_details_with_curl if args.fetcher == "curl" else None
        report = build_s2p1_preprint_replay_shadow_evidence(
            state_dir=args.state_dir,
            generated_at=args.generated_at,
            start_date=args.start_date,
            end_date=args.end_date,
            count=args.count,
            lookback_days=args.lookback_days,
            max_records=args.max_records,
            fetcher=preprint_fetcher,
            write=not args.no_write,
            polite_delay_seconds=args.polite_delay_seconds,
        )
        errors = validate_s2p1_preprint_replay_shadow_report(report) if report.get("status") == "pass" else []
        if errors:
            report = {**report, "status": "blocked", "blocking_reasons": sorted(set([*report.get("blocking_reasons", []), *errors]))}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            replay_report = report.get("replay_report") if isinstance(report.get("replay_report"), dict) else {}
            shadow_report = report.get("shadow_report") if isinstance(report.get("shadow_report"), dict) else {}
            print(report["status"])
            print(f"- success_count: {replay_report.get('success_count')}/{replay_report.get('required_replay_count')}")
            print(f"- unique_date_count: {replay_report.get('unique_date_count')}")
            print(f"- duplicate_selected_count: {replay_report.get('duplicate_selected_count')}")
            print(f"- future_leakage_count: {replay_report.get('future_leakage_count')}")
            print(f"- p0_p1_blocker_count: {replay_report.get('p0_p1_blocker_count')}")
            print(f"- shadow_hours: {shadow_report.get('shadow_hours')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-top-journal-shadow-daily":
        source_batches = {"nature": load_json_mapping(args.nature_batch)}
        queue = load_json_mapping(args.queue_path) if args.queue_path else None
        report = run_s2p2_top_journal_shadow_daily(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            source_batches=source_batches,
            queue=queue,
            write=not args.no_write,
        )
        errors = validate_s2p2_top_journal_shadow_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-science-shadow-daily":
        source_batches = {"science": load_json_mapping(args.science_batch)}
        queue = load_json_mapping(args.queue_path) if args.queue_path else None
        report = run_s2pct02_science_shadow_daily(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            source_batches=source_batches,
            queue=queue,
            write=not args.no_write,
        )
        errors = validate_s2pct02_science_shadow_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-lancet-shadow-daily":
        source_batches = {"lancet": load_json_mapping(args.lancet_batch)}
        queue = load_json_mapping(args.queue_path) if args.queue_path else None
        report = run_s2pct03_lancet_shadow_daily(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            source_batches=source_batches,
            queue=queue,
            write=not args.no_write,
        )
        errors = validate_s2pct03_lancet_shadow_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-top-journal-profile-shadow":
        source_batches = {
            "nature": load_json_mapping(args.nature_batch),
            "science": load_json_mapping(args.science_batch),
            "lancet": load_json_mapping(args.lancet_batch),
        }
        publication_payload = json.loads(Path(args.publication_events).read_text(encoding="utf-8"))
        if isinstance(publication_payload, dict) and isinstance(publication_payload.get("events"), list):
            publication_events = publication_payload["events"]
        elif isinstance(publication_payload, list):
            publication_events = publication_payload
        else:
            publication_events = []
        prior_profile_state = load_json_mapping(args.prior_profile_state) if args.prior_profile_state else None
        report = run_s2pct04_top_journal_profile_shadow(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            source_batches=source_batches,
            publication_events=publication_events,
            prior_profile_state=prior_profile_state,
            write=not args.no_write,
        )
        errors = validate_s2pct04_top_journal_profile_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- profile_kinds_observed: {', '.join(report.get('profile_kinds_observed', []))}")
            print(f"- forced_event_update_count: {report.get('forced_event_update_count')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-engineering-signals-shadow":
        profile_report = load_json_mapping(args.profile_report)
        signal_payload = json.loads(Path(args.engineering_signals).read_text(encoding="utf-8"))
        if isinstance(signal_payload, dict) and isinstance(signal_payload.get("signals"), list):
            engineering_signals = signal_payload["signals"]
        elif isinstance(signal_payload, list):
            engineering_signals = signal_payload
        else:
            engineering_signals = []
        report = run_s2pct05_engineering_signal_shadow(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            profile_report=profile_report,
            engineering_signals=engineering_signals,
            write=not args.no_write,
        )
        errors = validate_s2pct05_engineering_signal_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- signal_types_observed: {', '.join(report.get('signal_types_observed', []))}")
            print(f"- engineering_signal_count: {report.get('engineering_signal_count')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-authoritative-reports-shadow":
        engineering_signal_report = load_json_mapping(args.engineering_signal_report)
        report_payload = json.loads(Path(args.technical_reports).read_text(encoding="utf-8"))
        if isinstance(report_payload, dict) and isinstance(report_payload.get("reports"), list):
            technical_reports = report_payload["reports"]
        elif isinstance(report_payload, list):
            technical_reports = report_payload
        else:
            technical_reports = []
        report = run_s2pct06_authoritative_report_shadow(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            engineering_signal_report=engineering_signal_report,
            technical_reports=technical_reports,
            write=not args.no_write,
        )
        errors = validate_s2pct06_authoritative_report_source_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- report_types_observed: {', '.join(report.get('report_types_observed', []))}")
            print(f"- authoritative_report_count: {report.get('authoritative_report_count')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-d2-source-domain-qualification":
        report = run_s2pct07_d2_source_domain_qualification(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            profile_report=load_json_mapping(args.profile_report),
            engineering_signal_report=load_json_mapping(args.engineering_signal_report),
            authoritative_report=load_json_mapping(args.authoritative_report),
            replay_records=load_json_records(args.replay_records, "replay_records"),
            shadow_records=load_json_records(args.shadow_records, "shadow_records"),
            forced_event_records=load_json_records(args.forced_event_records, "forced_event_records"),
            queue_explanation_records=load_json_records(args.queue_explanation_records, "queue_explanation_records"),
            write=not args.no_write,
        )
        errors = validate_s2pct07_d2_source_domain_qualification_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- replay_gate: {report.get('replay_gate')}")
            print(f"- shadow_gate: {report.get('shadow_gate')}")
            print(f"- type_calibration_gate: {report.get('type_calibration_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-china-c0-source-foundation":
        report = run_s2pdt01_china_c0_source_foundation(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            d2_qualification_report=load_json_mapping(args.d2_qualification_report),
            authority_records=load_json_records(args.authority_records, "authority_records"),
            write=not args.no_write,
        )
        errors = validate_s2pdt01_china_c0_source_foundation_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- authority_taxonomy_gate: {report.get('authority_taxonomy_gate')}")
            print(f"- official_identity_gate: {report.get('official_identity_gate')}")
            print(f"- document_traceability_gate: {report.get('document_traceability_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-china-c1-department-source-map":
        report = run_s2pdt02_china_c1_department_source_map(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            c0_source_foundation_report=load_json_mapping(args.c0_source_foundation_report),
            department_records=load_json_records(args.department_records, "department_records"),
            write=not args.no_write,
        )
        errors = validate_s2pdt02_china_c1_department_source_map_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- sector_coverage_gate: {report.get('sector_coverage_gate')}")
            print(f"- official_identity_gate: {report.get('official_identity_gate')}")
            print(f"- alias_gate: {report.get('alias_gate')}")
            print(f"- industry_route_gate: {report.get('industry_route_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-china-legal-metadata-relation-shadow":
        report = run_s2pdt03_china_legal_metadata_relation_shadow(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            c1_department_source_map_report=load_json_mapping(args.c1_department_source_map_report),
            legal_records=load_json_records(args.legal_records, "legal_records"),
            relation_records=load_json_records(args.relation_records, "relation_records"),
            prior_conclusion_records=load_json_records(args.prior_conclusion_records, "prior_conclusion_records"),
            write=not args.no_write,
        )
        errors = validate_s2pdt03_china_legal_metadata_relation_shadow_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- legal_status_taxonomy_gate: {report.get('legal_status_taxonomy_gate')}")
            print(f"- version_effectivity_gate: {report.get('version_effectivity_gate')}")
            print(f"- reprint_relation_gate: {report.get('reprint_relation_gate')}")
            print(f"- forced_update_gate: {report.get('forced_update_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-china-d3-readiness-review":
        report = run_s2pdt04_china_d3_readiness_review(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            c0_source_foundation_report=load_json_mapping(args.c0_source_foundation_report),
            c1_department_source_map_report=load_json_mapping(args.c1_department_source_map_report),
            legal_metadata_relation_report=load_json_mapping(args.legal_metadata_relation_report),
            replay_records=load_json_records(args.replay_records, "replay_records"),
            shadow_records=load_json_records(args.shadow_records, "shadow_records"),
            board_route_records=load_json_records(args.board_route_records, "board_route_records"),
            write=not args.no_write,
        )
        errors = validate_s2pdt04_china_d3_readiness_review_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- d3_replay_gate: {report.get('d3_replay_gate')}")
            print(f"- d3_shadow_gate: {report.get('d3_shadow_gate')}")
            print(f"- board_routing_gate: {report.get('board_routing_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-us-ta-source-foundation":
        report = run_s2pet01_us_ta_source_foundation(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            agency_records=load_json_records(args.agency_records, "agency_records"),
            write=not args.no_write,
        )
        errors = validate_s2pet01_us_ta_source_foundation_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- agency_coverage_gate: {report.get('agency_coverage_gate')}")
            print(f"- signal_type_gate: {report.get('signal_type_gate')}")
            print(f"- official_identity_gate: {report.get('official_identity_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-us-lg-legal-backbone":
        report = run_s2pet02_us_lg_legal_backbone(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            us_ta_source_foundation_report=load_json_mapping(args.us_ta_source_foundation_report),
            legal_records=load_json_records(args.legal_records, "legal_records"),
            relation_records=load_json_records(args.relation_records, "relation_records"),
            write=not args.no_write,
        )
        errors = validate_s2pet02_us_lg_legal_backbone_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- upstream_us_ta_source_foundation_gate: {report.get('upstream_us_ta_source_foundation_gate')}")
            print(f"- source_system_coverage_gate: {report.get('source_system_coverage_gate')}")
            print(f"- document_type_gate: {report.get('document_type_gate')}")
            print(f"- legal_relation_gate: {report.get('legal_relation_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-us-fm-source-backbone":
        report = run_s2pet03_us_fm_source_backbone(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            us_lg_legal_backbone_report=load_json_mapping(args.us_lg_legal_backbone_report),
            finance_records=load_json_records(args.finance_records, "finance_records"),
            relation_records=load_json_records(args.relation_records, "relation_records"),
            write=not args.no_write,
        )
        errors = validate_s2pet03_us_fm_source_backbone_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- upstream_us_lg_legal_backbone_gate: {report.get('upstream_us_lg_legal_backbone_gate')}")
            print(f"- source_system_coverage_gate: {report.get('source_system_coverage_gate')}")
            print(f"- sec_form_coverage_gate: {report.get('sec_form_coverage_gate')}")
            print(f"- identifier_gate: {report.get('identifier_gate')}")
            print(f"- finance_relation_gate: {report.get('finance_relation_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-us-tp-d4-qualification":
        report = run_s2pet04_us_tp_d4_qualification(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            us_ta_source_foundation_report=load_json_mapping(args.us_ta_source_foundation_report),
            us_lg_legal_backbone_report=load_json_mapping(args.us_lg_legal_backbone_report),
            us_fm_source_backbone_report=load_json_mapping(args.us_fm_source_backbone_report),
            policy_records=load_json_records(args.policy_records, "policy_records"),
            replay_records=load_json_records(args.replay_records, "replay_records"),
            shadow_records=load_json_records(args.shadow_records, "shadow_records"),
            board_route_records=load_json_records(args.board_route_records, "board_route_records"),
            budget_records=load_json_records(args.budget_records, "budget_records"),
            write=not args.no_write,
        )
        errors = validate_s2pet04_us_tp_d4_qualification_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- upstream_s2pet01_s2pet03_gate: {report.get('upstream_s2pet01_s2pet03_gate')}")
            print(f"- us_tp_source_system_gate: {report.get('us_tp_source_system_gate')}")
            print(f"- d4_replay_gate: {report.get('d4_replay_gate')}")
            print(f"- d4_shadow_gate: {report.get('d4_shadow_gate')}")
            print(f"- board_routing_gate: {report.get('board_routing_gate')}")
            print(f"- budget_explanation_gate: {report.get('budget_explanation_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-china-provincial-template-coverage":
        report = run_s2pft01_china_provincial_template_coverage(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            d3_readiness_review_report=load_json_mapping(args.d3_readiness_review_report),
            provincial_records=load_json_records(args.provincial_records, "provincial_records"),
            write=not args.no_write,
        )
        errors = validate_s2pft01_china_provincial_template_coverage_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- provincial_coverage_gate: {report.get('provincial_coverage_gate')}")
            print(f"- core_department_template_gate: {report.get('core_department_template_gate')}")
            print(f"- health_tier_gate: {report.get('health_tier_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-hk-mo-independent-profile":
        report = run_s2pft02_hk_mo_independent_profile(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            provincial_template_coverage_report=load_json_mapping(args.provincial_template_coverage_report),
            jurisdiction_profiles=load_json_records(args.jurisdiction_profiles, "jurisdiction_profiles"),
            write=not args.no_write,
        )
        errors = validate_s2pft02_hk_mo_independent_profile_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- jurisdiction_coverage_gate: {report.get('jurisdiction_coverage_gate')}")
            print(f"- language_profile_gate: {report.get('language_profile_gate')}")
            print(f"- legal_status_gate: {report.get('legal_status_gate')}")
            print(f"- template_independence_gate: {report.get('template_independence_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-key-city-coverage":
        report = run_s2pft03_key_city_coverage(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            hk_mo_profile_report=load_json_mapping(args.hk_mo_profile_report),
            city_records=load_json_records(args.city_records, "city_records"),
            write=not args.no_write,
        )
        errors = validate_s2pft03_key_city_coverage_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- city_coverage_gate: {report.get('city_coverage_gate')}")
            print(f"- city_alias_gate: {report.get('city_alias_gate')}")
            print(f"- city_department_template_gate: {report.get('city_department_template_gate')}")
            print(f"- region_weight_gate: {report.get('region_weight_gate')}")
            print(f"- health_tier_gate: {report.get('health_tier_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-special-zone-discovery":
        report = run_s2pft04_special_zone_discovery(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            key_city_coverage_report=load_json_mapping(args.key_city_coverage_report),
            zone_records=load_json_records(args.zone_records, "zone_records"),
            write=not args.no_write,
        )
        errors = validate_s2pft04_special_zone_discovery_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- zone_coverage_gate: {report.get('zone_coverage_gate')}")
            print(f"- zone_authority_role_gate: {report.get('zone_authority_role_gate')}")
            print(f"- zone_type_policy_gate: {report.get('zone_type_policy_gate')}")
            print(f"- parent_city_mapping_gate: {report.get('parent_city_mapping_gate')}")
            print(f"- health_tier_gate: {report.get('health_tier_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-d3-full-governance-qualification":
        report = run_s2pft05_d3_full_governance_qualification(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            d3_readiness_review_report=load_json_mapping(args.d3_readiness_review_report),
            provincial_template_coverage_report=load_json_mapping(args.provincial_template_coverage_report),
            hk_mo_profile_report=load_json_mapping(args.hk_mo_profile_report),
            key_city_coverage_report=load_json_mapping(args.key_city_coverage_report),
            special_zone_discovery_report=load_json_mapping(args.special_zone_discovery_report),
            governance_records=load_json_records(args.governance_records, "governance_records"),
            write=not args.no_write,
        )
        errors = validate_s2pft05_d3_full_governance_qualification_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- component_coverage_gate: {report.get('component_coverage_gate')}")
            print(f"- quota_balance_gate: {report.get('quota_balance_gate')}")
            print(f"- health_balance_gate: {report.get('health_balance_gate')}")
            print(f"- elimination_explanation_gate: {report.get('elimination_explanation_gate')}")
            print(f"- fallback_route_gate: {report.get('fallback_route_gate')}")
            print(f"- d3_full_replay_gate: {report.get('d3_full_replay_gate')}")
            print(f"- metadata_only_gate: {report.get('metadata_only_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-evidence-packet-v2-compatibility":
        report = run_s2pgt01_evidence_packet_v2_compatibility(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            source_domain_reports=load_json_records(args.source_domain_reports, "source_domain_reports"),
            packet_records=load_json_records(args.packet_records, "packet_records"),
            write=not args.no_write,
        )
        errors = validate_s2pgt01_evidence_packet_v2_compatibility_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- source_domain_gate: {report.get('source_domain_gate')}")
            print(f"- packet_shape_gate: {report.get('packet_shape_gate')}")
            print(f"- evidence_level_gate: {report.get('evidence_level_gate')}")
            print(f"- old_arxiv_compatibility_gate: {report.get('old_arxiv_compatibility_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-knowledge-graph-spine":
        report = run_s2pgt02_knowledge_graph_spine(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            evidence_packet_report=load_json_mapping(args.evidence_packet_report),
            identity_records=load_json_records(args.identity_records, "identity_records"),
            relation_records=load_json_records(args.relation_records, "relation_records"),
            write=not args.no_write,
        )
        errors = validate_s2pgt02_knowledge_graph_spine_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- identifier_coverage_gate: {report.get('identifier_coverage_gate')}")
            print(f"- canonical_dedupe_gate: {report.get('canonical_dedupe_gate')}")
            print(f"- relation_evidence_gate: {report.get('relation_evidence_gate')}")
            print(f"- idempotent_update_gate: {report.get('idempotent_update_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-source-board-routing":
        report = run_s2pgt03_source_board_routing(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            evidence_packet_report=load_json_mapping(args.evidence_packet_report),
            route_records=load_json_records(args.route_records, "route_records"),
            write=not args.no_write,
        )
        errors = validate_s2pgt03_source_board_routing_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- source_domain_coverage_gate: {report.get('source_domain_coverage_gate')}")
            print(f"- primary_board_coverage_gate: {report.get('primary_board_coverage_gate')}")
            print(f"- cross_cutting_board_coverage_gate: {report.get('cross_cutting_board_coverage_gate')}")
            print(f"- route_reason_gate: {report.get('route_reason_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-delta-resonance":
        report = run_s2pgt04_delta_resonance(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            routing_report=load_json_mapping(args.routing_report),
            delta_records=load_json_records(args.delta_records, "delta_records"),
            write=not args.no_write,
        )
        errors = validate_s2pgt04_delta_resonance_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- upstream_routing_gate: {report.get('upstream_routing_gate')}")
            print(f"- delta_type_coverage_gate: {report.get('delta_type_coverage_gate')}")
            print(f"- support_refute_gate: {report.get('support_refute_gate')}")
            print(f"- resonance_group_gate: {report.get('resonance_group_gate')}")
            print(f"- delta_reason_gate: {report.get('delta_reason_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-cross-board-calibration":
        report = run_s2pgt05_cross_board_calibration(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            delta_resonance_report=load_json_mapping(args.delta_resonance_report),
            queue_candidate_records=load_json_records(args.queue_candidates, "queue_candidate_records"),
            write=not args.no_write,
        )
        errors = validate_s2pgt05_cross_board_calibration_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- upstream_delta_resonance_gate: {report.get('upstream_delta_resonance_gate')}")
            print(f"- percentile_calibration_gate: {report.get('percentile_calibration_gate')}")
            print(f"- source_balance_gate: {report.get('source_balance_gate')}")
            print(f"- waiting_credit_gate: {report.get('waiting_credit_gate')}")
            print(f"- queue_reason_gate: {report.get('queue_reason_gate')}")
            print(f"- deterministic_order_gate: {report.get('deterministic_order_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-user-center":
        controls = load_owner_controls(args.controls)
        owner_validation = validate_owner_controls(controls)
        owner_preview = build_owner_impact_preview(controls)
        report = run_s2pit01_user_center(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            owner_controls=controls,
            owner_validation_report=owner_validation,
            owner_impact_preview=owner_preview,
            storage_inspect_report=load_json_mapping(args.storage_inspect_report),
            write=not args.no_write,
        )
        errors = validate_s2pit01_user_center_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- owner_controls_gate: {report.get('owner_controls_gate')}")
            print(f"- storage_readability_gate: {report.get('storage_readability_gate')}")
            print(f"- one_edit_directory_gate: {report.get('one_edit_directory_gate')}")
            print(f"- control_domain_gate: {report.get('control_domain_gate')}")
            print(f"- click_depth_gate: {report.get('click_depth_gate')}")
            print(f"- compatible_config_gate: {report.get('compatible_config_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-runtime-dashboard":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        owner_status_summary = load_json_mapping(args.owner_status_summary)
        report = run_s2pit02_runtime_dashboard(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            user_center_report=load_json_mapping(args.user_center_report),
            runtime_audit_report=load_json_mapping(args.runtime_audit_report),
            watchdog_report=load_json_mapping(args.watchdog_report),
            storage_inspect_report=load_json_mapping(args.storage_inspect_report),
            production_gate_state=production_gate_state,
            owner_status_summary=owner_status_summary,
            write=not args.no_write,
        )
        errors = validate_s2pit02_runtime_dashboard_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- owner_center_gate: {report.get('owner_center_gate')}")
            print(f"- owner_status_count_gate: {report.get('owner_status_count_gate')}")
            print(f"- runtime_state_gate: {report.get('runtime_state_gate')}")
            print(f"- storage_state_gate: {report.get('storage_state_gate')}")
            print(f"- production_boundary_gate: {report.get('production_boundary_gate')}")
            print(f"- dashboard_section_gate: {report.get('dashboard_section_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-source-model-view":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pit03_source_model_view(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            user_center_report=load_json_mapping(args.user_center_report),
            source_domain_records=load_json_records(args.source_domains, "source_domain_records"),
            reading_board_records=load_json_records(args.reading_boards, "reading_board_records"),
            parameter_records=load_json_records(args.parameters, "parameter_records"),
            queue_view_records=load_json_records(args.queue_view, "queue_view_records"),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pit03_source_model_view_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- user_center_gate: {report.get('user_center_gate')}")
            print(f"- source_domain_gate: {report.get('source_domain_gate')}")
            print(f"- reading_board_gate: {report.get('reading_board_gate')}")
            print(f"- parameter_disclosure_gate: {report.get('parameter_disclosure_gate')}")
            print(f"- queue_view_gate: {report.get('queue_view_gate')}")
            print(f"- traceability_gate: {report.get('traceability_gate')}")
            print(f"- deterministic_view_gate: {report.get('deterministic_view_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-content-ledger-view":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pit04_content_ledger(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            runtime_dashboard_report=load_json_mapping(args.runtime_dashboard_report),
            source_model_view_report=load_json_mapping(args.source_model_view_report),
            lifecycle_state_report=load_json_mapping(args.lifecycle_state_report),
            review_schedule_report=load_json_mapping(args.review_schedule_report),
            action_roi_report=load_json_mapping(args.action_roi_report),
            ledger_records=load_json_records(args.ledger_records, "ledger_records"),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pit04_content_ledger_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- runtime_dashboard_gate: {report.get('runtime_dashboard_gate')}")
            print(f"- source_model_view_gate: {report.get('source_model_view_gate')}")
            print(f"- lifecycle_state_gate: {report.get('lifecycle_state_gate')}")
            print(f"- review_schedule_gate: {report.get('review_schedule_gate')}")
            print(f"- action_roi_gate: {report.get('action_roi_gate')}")
            print(f"- ledger_record_gate: {report.get('ledger_record_gate')}")
            print(f"- traceability_gate: {report.get('traceability_gate')}")
            print(f"- count_conservation_gate: {report.get('count_conservation_gate')}")
            print(f"- deterministic_ledger_gate: {report.get('deterministic_ledger_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-mail-contract":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pkt01_mail_contract(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            content_quality_report=load_json_mapping(args.content_quality_report),
            content_ledger_report=load_json_mapping(args.content_ledger_report),
            action_roi_report=load_json_mapping(args.action_roi_report),
            mail_contracts=load_json_records(args.mail_contracts, "mail_contracts"),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pkt01_mail_contract_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- content_quality_gate: {report.get('content_quality_gate')}")
            print(f"- content_ledger_gate: {report.get('content_ledger_gate')}")
            print(f"- action_roi_gate: {report.get('action_roi_gate')}")
            print(f"- shared_contract_gate: {report.get('shared_contract_gate')}")
            print(f"- board_differentiation_gate: {report.get('board_differentiation_gate')}")
            print(f"- reading_layer_gate: {report.get('reading_layer_gate')}")
            print(f"- evidence_label_gate: {report.get('evidence_label_gate')}")
            print(f"- feedback_component_gate: {report.get('feedback_component_gate')}")
            print(f"- hash_status_gate: {report.get('hash_status_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-m1-mail":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pkt02_m1_mail(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            mail_contract_report=load_json_mapping(args.mail_contract_report),
            content_quality_report=load_json_mapping(args.content_quality_report),
            content_ledger_report=load_json_mapping(args.content_ledger_report),
            action_roi_report=load_json_mapping(args.action_roi_report),
            m1_mail_record=load_json_mapping(args.m1_mail_record),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pkt02_m1_mail_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- mail_contract_gate: {report.get('mail_contract_gate')}")
            print(f"- content_quality_gate: {report.get('content_quality_gate')}")
            print(f"- content_ledger_gate: {report.get('content_ledger_gate')}")
            print(f"- action_roi_gate: {report.get('action_roi_gate')}")
            print(f"- m1_scope_gate: {report.get('m1_scope_gate')}")
            print(f"- section_coverage_gate: {report.get('section_coverage_gate')}")
            print(f"- evidence_counterevidence_gate: {report.get('evidence_counterevidence_gate')}")
            print(f"- personal_action_gate: {report.get('personal_action_gate')}")
            print(f"- hash_status_gate: {report.get('hash_status_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-m2-mail":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pkt03_m2_mail(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            mail_contract_report=load_json_mapping(args.mail_contract_report),
            content_quality_report=load_json_mapping(args.content_quality_report),
            content_ledger_report=load_json_mapping(args.content_ledger_report),
            action_roi_report=load_json_mapping(args.action_roi_report),
            m2_mail_record=load_json_mapping(args.m2_mail_record),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pkt03_m2_mail_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- mail_contract_gate: {report.get('mail_contract_gate')}")
            print(f"- content_quality_gate: {report.get('content_quality_gate')}")
            print(f"- content_ledger_gate: {report.get('content_ledger_gate')}")
            print(f"- action_roi_gate: {report.get('action_roi_gate')}")
            print(f"- m2_scope_gate: {report.get('m2_scope_gate')}")
            print(f"- section_coverage_gate: {report.get('section_coverage_gate')}")
            print(f"- engineering_reproducibility_gate: {report.get('engineering_reproducibility_gate')}")
            print(f"- product_limit_action_gate: {report.get('product_limit_action_gate')}")
            print(f"- hash_status_gate: {report.get('hash_status_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-m3-mail":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pkt04_m3_mail(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            mail_contract_report=load_json_mapping(args.mail_contract_report),
            content_quality_report=load_json_mapping(args.content_quality_report),
            content_ledger_report=load_json_mapping(args.content_ledger_report),
            action_roi_report=load_json_mapping(args.action_roi_report),
            m3_mail_record=load_json_mapping(args.m3_mail_record),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pkt04_m3_mail_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- mail_contract_gate: {report.get('mail_contract_gate')}")
            print(f"- content_quality_gate: {report.get('content_quality_gate')}")
            print(f"- content_ledger_gate: {report.get('content_ledger_gate')}")
            print(f"- action_roi_gate: {report.get('action_roi_gate')}")
            print(f"- m3_scope_gate: {report.get('m3_scope_gate')}")
            print(f"- section_coverage_gate: {report.get('section_coverage_gate')}")
            print(f"- legal_capital_geo_gate: {report.get('legal_capital_geo_gate')}")
            print(f"- personal_impact_action_gate: {report.get('personal_impact_action_gate')}")
            print(f"- hash_status_gate: {report.get('hash_status_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-m4-mail":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pkt05_m4_mail(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            mail_contract_report=load_json_mapping(args.mail_contract_report),
            m1_mail_report=load_json_mapping(args.m1_mail_report),
            m2_mail_report=load_json_mapping(args.m2_mail_report),
            m3_mail_report=load_json_mapping(args.m3_mail_report),
            content_ledger_report=load_json_mapping(args.content_ledger_report),
            action_roi_report=load_json_mapping(args.action_roi_report),
            review_schedule_report=load_json_mapping(args.review_schedule_report),
            m4_orchestration_record=load_json_mapping(args.m4_orchestration_record),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pkt05_m4_mail_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- mail_contract_gate: {report.get('mail_contract_gate')}")
            print(f"- m1_terminal_gate: {report.get('m1_terminal_gate')}")
            print(f"- m2_terminal_gate: {report.get('m2_terminal_gate')}")
            print(f"- m3_terminal_gate: {report.get('m3_terminal_gate')}")
            print(f"- m4_scope_gate: {report.get('m4_scope_gate')}")
            print(f"- staggered_schedule_gate: {report.get('staggered_schedule_gate')}")
            print(f"- watermark_gate: {report.get('watermark_gate')}")
            print(f"- duplicate_suppression_gate: {report.get('duplicate_suppression_gate')}")
            print(f"- section_coverage_gate: {report.get('section_coverage_gate')}")
            print(f"- cross_board_synthesis_gate: {report.get('cross_board_synthesis_gate')}")
            print(f"- action_review_gate: {report.get('action_review_gate')}")
            print(f"- hash_status_gate: {report.get('hash_status_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-lifecycle-state":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pjt01_lifecycle_state(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            runtime_dashboard_report=load_json_mapping(args.runtime_dashboard_report),
            lifecycle_records=load_json_records(args.lifecycle_records, "lifecycle_records"),
            migration_plan=load_json_mapping(args.migration_plan),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pjt01_lifecycle_state_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- runtime_dashboard_gate: {report.get('runtime_dashboard_gate')}")
            print(f"- state_coverage_gate: {report.get('state_coverage_gate')}")
            print(f"- append_only_history_gate: {report.get('append_only_history_gate')}")
            print(f"- count_conservation_gate: {report.get('count_conservation_gate')}")
            print(f"- ledger_mapping_gate: {report.get('ledger_mapping_gate')}")
            print(f"- migration_plan_gate: {report.get('migration_plan_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-review-schedule":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        schedule_policy = load_json_mapping(args.schedule_policy) if args.schedule_policy else None
        report = run_s2pjt02_review_schedule(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            lifecycle_state_report=load_json_mapping(args.lifecycle_state_report),
            review_records=load_json_records(args.review_records, "review_records"),
            schedule_policy=schedule_policy,
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pjt02_review_schedule_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- lifecycle_state_gate: {report.get('lifecycle_state_gate')}")
            print(f"- schedule_policy_gate: {report.get('schedule_policy_gate')}")
            print(f"- review_record_gate: {report.get('review_record_gate')}")
            print(f"- due_count_gate: {report.get('due_count_gate')}")
            print(f"- deterministic_queue_gate: {report.get('deterministic_queue_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-action-roi-ledger":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pjt03_action_asset_roi(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            review_schedule_report=load_json_mapping(args.review_schedule_report),
            action_records=load_json_records(args.action_records, "action_records"),
            capability_assets=load_json_records(args.capability_assets, "capability_assets"),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pjt03_action_asset_roi_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- review_schedule_gate: {report.get('review_schedule_gate')}")
            print(f"- action_window_gate: {report.get('action_window_gate')}")
            print(f"- expected_roi_gate: {report.get('expected_roi_gate')}")
            print(f"- actual_roi_gate: {report.get('actual_roi_gate')}")
            print(f"- asset_trace_gate: {report.get('asset_trace_gate')}")
            print(f"- deterministic_ledger_gate: {report.get('deterministic_ledger_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-weekly-report":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pjt04_weekly_report(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            week_start=args.week_start,
            week_end=args.week_end,
            action_roi_report=load_json_mapping(args.action_roi_report),
            weekly_items=load_json_records(args.weekly_items, "weekly_items"),
            weekly_sections=load_json_mapping(args.weekly_sections),
            next_week_focus=load_json_records(args.next_week_focus, "next_week_focus"),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pjt04_weekly_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- action_roi_gate: {report.get('action_roi_gate')}")
            print(f"- week_window_gate: {report.get('week_window_gate')}")
            print(f"- section_trace_gate: {report.get('section_trace_gate')}")
            print(f"- state_trace_gate: {report.get('state_trace_gate')}")
            print(f"- no_duplication_gate: {report.get('no_duplication_gate')}")
            print(f"- next_focus_gate: {report.get('next_focus_gate')}")
            print(f"- deterministic_report_gate: {report.get('deterministic_report_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-monthly-report":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pjt05_monthly_report(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            month_start=args.month_start,
            month_end=args.month_end,
            weekly_reports=load_json_records(args.weekly_reports, "weekly_reports"),
            cognitive_snapshots=load_json_mapping(args.cognitive_snapshots),
            monthly_sections=load_json_mapping(args.monthly_sections),
            capability_growth=load_json_records(args.capability_growth, "capability_growth"),
            economic_conversions=load_json_records(args.economic_conversions, "economic_conversions"),
            forecast_reviews=load_json_records(args.forecast_reviews, "forecast_reviews"),
            next_month_focus=load_json_records(args.next_month_focus, "next_month_focus"),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pjt05_monthly_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- weekly_report_gate: {report.get('weekly_report_gate')}")
            print(f"- month_window_gate: {report.get('month_window_gate')}")
            print(f"- cognitive_delta_gate: {report.get('cognitive_delta_gate')}")
            print(f"- capability_growth_gate: {report.get('capability_growth_gate')}")
            print(f"- conversion_trace_gate: {report.get('conversion_trace_gate')}")
            print(f"- forecast_review_gate: {report.get('forecast_review_gate')}")
            print(f"- section_trace_gate: {report.get('section_trace_gate')}")
            print(f"- deterministic_report_gate: {report.get('deterministic_report_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-content-quality-gate":
        production_gate_state = load_json_mapping(args.production_gate_state) if args.production_gate_state else {}
        report = run_s2pht05_content_quality_gate(
            state_dir=args.state_dir,
            date=args.date,
            generated_at=args.generated_at,
            dependency_receipts=load_json_records(args.dependency_receipts, "dependency_receipts"),
            gold_items=load_json_records(args.gold_items, "gold_items"),
            stage1_regression_checks=load_json_records(args.stage1_regression_checks, "stage1_regression_checks"),
            manual_review_samples=load_json_records(args.manual_review_samples, "manual_review_samples"),
            production_gate_state=production_gate_state,
            write=not args.no_write,
        )
        errors = validate_s2pht05_content_quality_gate_report(report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- dependency_receipt_gate: {report.get('dependency_receipt_gate')}")
            print(f"- gold_dimension_gate: {report.get('gold_dimension_gate')}")
            print(f"- entailment_gate: {report.get('entailment_gate')}")
            print(f"- quote_location_gate: {report.get('quote_location_gate')}")
            print(f"- template_rate_gate: {report.get('template_rate_gate')}")
            print(f"- counterevidence_gate: {report.get('counterevidence_gate')}")
            print(f"- personal_action_gate: {report.get('personal_action_gate')}")
            print(f"- stage1_regression_gate: {report.get('stage1_regression_gate')}")
            print(f"- manual_review_gate: {report.get('manual_review_gate')}")
            print(f"- deterministic_gate: {report.get('deterministic_gate')}")
            print(f"- no_side_effect_gate: {report.get('no_side_effect_gate')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "stage2-replay-payload-execution":
        evidence_input = load_json_mapping(args.input)
        evidence_refs = args.evidence_ref or list(evidence_input.get("evidence_refs") or [args.input])
        report = build_s2plt01_replay_payload_execution_report(
            execution_id=args.execution_id,
            generated_at=args.generated_at,
            generated_by=args.generated_by,
            evidence_mode=args.evidence_mode,
            replay_records=list(evidence_input.get("replay_records") or []),
            mail_preview_records=list(evidence_input.get("mail_preview_records") or []),
            source_terminal_states=list(evidence_input.get("source_terminal_states") or []),
            evidence_refs=evidence_refs,
        )
        errors = validate_s2plt01_replay_payload_execution_report(report)
        output = {**report, "report_validation_errors": errors} if errors else report
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- payload_execution_package_passed: {report.get('payload_execution_package_passed')}")
            print(f"- entry_precheck_passed: {report.get('entry_precheck_passed')}")
            print(f"- execution_hash: {report.get('execution_hash')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["payload_execution_package_passed"] and not errors else 2
    if args.command == "stage2-independent-replay-review":
        execution_report = load_json_mapping(args.execution_report)
        report = build_s2plt01_independent_replay_review_report(
            review_id=args.review_id,
            generated_at=args.generated_at,
            reviewer_id=args.reviewer_id,
            reviewer_role=args.reviewer_role,
            reviewer_involved_in_s2plt01_implementation=args.reviewer_involved_in_implementation,
            replay_execution_report=execution_report,
            ci_evidence_refs=list(args.ci_evidence_ref or []),
            evidence_refs=list(args.evidence_ref or []),
        )
        errors = validate_s2plt01_independent_replay_review_report(report)
        output = {**report, "report_validation_errors": errors} if errors else report
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- review_package_passed: {report.get('review_package_passed')}")
            print(f"- review_hash: {report.get('review_hash')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["review_package_passed"] and not errors else 2
    if args.command == "audit-s2plt01-terminal-acceptance":
        report = build_s2plt01_terminal_acceptance_audit_state(repo_root=args.repo_root)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- terminal_acceptance_ready: {report.get('terminal_acceptance_ready')}")
            print(f"- review_receipt_present: {report.get('review_receipt_present')}")
            print(f"- review_package_passed: {report.get('review_package_passed')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-s2plt01-terminal-acceptance":
        report = build_s2plt01_terminal_acceptance_artifact_validation_state(repo_root=args.repo_root)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_present: {report.get('artifact_present')}")
            print(f"- s2plt01_accepted_by_artifact: {report.get('s2plt01_accepted_by_artifact')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "audit-s2plt02-terminal-readiness":
        report = build_s2plt02_terminal_readiness_audit_state(generated_at=args.generated_at)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- observed_natural_days: {report.get('observed_natural_days')}")
            print(f"- observed_email_count: {report.get('observed_email_count')}")
            print(f"- m4_watermark_correct: {report.get('m4_watermark_correct')}")
            print(f"- s2plt02_accepted: {report.get('s2plt02_accepted')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "audit-s2plt02-dry-run-second-day":
        report = build_s2plt02_dry_run_second_day_audit_state(
            state_dir=args.state_dir,
            service_date=args.service_date,
        )
        validation_errors = validate_s2plt02_dry_run_second_day_audit_state(report)
        if validation_errors:
            report = dict(report)
            report["validator_errors"] = validation_errors
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- service_date: {report.get('service_date')}")
            print(f"- dry_run_mail_count: {report.get('dry_run_mail_count')}")
            print(f"- real_sent_mail_count: {report.get('real_sent_mail_count')}")
            print(f"- counts_toward_s2plt02_terminal_proof: {report.get('counts_toward_s2plt02_terminal_proof')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in report.get("validation_errors", []):
                print(f"- evidence_error: {error}")
            for error in validation_errors:
                print(f"- validator_error: {error}")
        return 0 if report["status"] == "pass" and not validation_errors else 2
    if args.command == "audit-s2plt02-real-proof-capture-readiness":
        if args.launchctl_disabled_file:
            launchctl_disabled_text = Path(args.launchctl_disabled_file).read_text(encoding="utf-8")
        else:
            completed = subprocess.run(
                ["launchctl", "print-disabled", f"gui/{os.getuid()}"],
                check=False,
                capture_output=True,
                text=True,
            )
            launchctl_disabled_text = completed.stdout
        launchctl_print_outputs: dict[str, str] = {}
        for label in (
            "com.linze.adp.local.daily",
            "com.linze.adp.local.health",
            "com.linze.adp.local.watchdog",
        ):
            completed = subprocess.run(
                ["launchctl", "print", f"gui/{os.getuid()}/{label}"],
                check=False,
                capture_output=True,
                text=True,
            )
            launchctl_print_outputs[label] = completed.stdout
        report = build_s2plt02_real_proof_capture_readiness_state(
            repo_root=args.repo_root,
            state_dir=args.state_dir,
            service_date=args.service_date,
            launchctl_disabled_text=launchctl_disabled_text,
            launchctl_print_outputs=launchctl_print_outputs,
        )
        validation_errors = validate_s2plt02_real_proof_capture_readiness_state(report)
        if validation_errors:
            report = dict(report)
            report["validator_errors"] = validation_errors
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- safe_to_collect_terminal_proof: {report.get('safe_to_collect_terminal_proof')}")
            print(f"- all_required_launchagents_disabled: {report.get('all_required_launchagents_disabled')}")
            print(f"- second_real_delivery_day_present: {report.get('second_real_delivery_day_present')}")
            print(
                "- terminal_delivery_proof_artifact_present: "
                f"{report.get('terminal_delivery_proof_artifact_present')}"
            )
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in report.get("validation_errors", []):
                print(f"- evidence_error: {error}")
            for error in validation_errors:
                print(f"- validator_error: {error}")
        return 0 if report["status"] == "pass" and not validation_errors else 2
    if args.command == "validate-s2plt02-real-proof-capture-authorization":
        artifact_path = Path(args.path)
        payload = load_json_mapping(artifact_path) if artifact_path.exists() else None
        report = build_s2plt02_real_proof_capture_authorization_validation_state(
            payload,
            expected_readiness_state_hash=args.expected_readiness_state_hash,
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_path: {report.get('artifact_path')}")
            print(f"- authorization_present: {report.get('authorization_present')}")
            print(
                "- real_proof_capture_authorized_by_payload: "
                f"{report.get('real_proof_capture_authorized_by_payload')}"
            )
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "build-s2plt02-real-proof-capture-authorization-owner-packet":
        readiness_state = {}
        if args.readiness_state_hash:
            readiness_state = {"state_hash": args.readiness_state_hash, "status": "blocked"}
        report = build_s2plt02_real_proof_capture_authorization_owner_packet_state(readiness_state)
        errors = validate_s2plt02_real_proof_capture_authorization_owner_packet_state(report)
        output = {**report, "owner_packet_validation_errors": errors}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- task_id: {report.get('task_id')}")
            print(f"- artifact_path: {report.get('artifact_path')}")
            print(f"- next_required_action: {report.get('next_required_action')}")
            for action in report.get("required_owner_actions", []):
                print(f"- required_owner_action: {action}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if not errors else 2
    if args.command == "build-s2plt02-real-proof-capture-authorization-artifact-draft":
        report = build_s2plt02_real_proof_capture_authorization_artifact_draft_state(
            owner_id=args.owner_id,
            owner_role=args.owner_role,
            generated_at=args.generated_at,
            readiness_state_hash=args.readiness_state_hash,
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(report["status"])
            print(f"- task_id: {report.get('task_id')}")
            print(f"- artifact_path: {report.get('artifact_path')}")
            print(f"- authorization_artifact_written: {report.get('authorization_artifact_written')}")
            print(
                "- authorization_gate_satisfied_by_this_command: "
                f"{report.get('authorization_gate_satisfied_by_this_command')}"
            )
            print(f"- next_required_action: {report.get('next_required_action')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "draft" and not report.get("validation_errors") else 2
    if args.command == "validate-s2plt02-terminal-delivery-proof":
        report = build_s2plt02_terminal_delivery_proof_artifact_validation_state(repo_root=args.repo_root)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_present: {report.get('artifact_present')}")
            print(f"- terminal_delivery_proof_ready: {report.get('terminal_delivery_proof_ready')}")
            print(f"- s2plt02_accepted_by_artifact: {report.get('s2plt02_accepted_by_artifact')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-s2plt02-real-scheduler-proof":
        report = build_s2plt02_real_scheduler_proof_validation_state(
            scheduler_proof=load_json_mapping(args.scheduler_proof)
        )
        state_errors = validate_s2plt02_real_scheduler_proof_validation_state(report)
        if state_errors:
            report = {**report, "state_validation_errors": state_errors}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- scheduler_proof_ready: {report.get('scheduler_proof_ready')}")
            print(f"- proof_ref: {report.get('proof_ref')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
            for error in state_errors:
                print(f"- state_error: {error}")
        return 0 if report["status"] == "pass" and not state_errors else 2
    if args.command == "validate-s2plt02-real-delivery-manifest":
        report = build_s2plt02_real_delivery_manifest_validation_state(
            delivery_manifest=load_json_mapping(args.delivery_manifest)
        )
        state_errors = validate_s2plt02_real_delivery_manifest_validation_state(report)
        if state_errors:
            report = {**report, "state_validation_errors": state_errors}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- delivery_manifest_ready: {report.get('delivery_manifest_ready')}")
            print(f"- manifest_ref: {report.get('manifest_ref')}")
            print(f"- service_date: {report.get('service_date')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
            for error in state_errors:
                print(f"- state_error: {error}")
        return 0 if report["status"] == "pass" and not state_errors else 2
    if args.command == "build-s2plt02-normalized-delivery-manifest":
        report = build_s2plt02_normalized_delivery_manifest_state(
            raw_manifest=load_json_mapping(args.raw_manifest),
            raw_manifest_ref=args.raw_manifest_ref,
            normalized_manifest_ref=args.normalized_manifest_ref,
            normalized_at=args.normalized_at,
        )
        state_errors = validate_s2plt02_normalized_delivery_manifest_state(report)
        if state_errors:
            report = {**report, "state_validation_errors": state_errors}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- normalized_manifest_ready: {report.get('normalized_manifest_ready')}")
            print(f"- raw_manifest_ref: {report.get('raw_manifest_ref')}")
            print(f"- normalized_manifest_ref: {report.get('normalized_manifest_ref')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in report.get("manifest_validation_errors", []):
                print(f"- error: {error}")
            for error in state_errors:
                print(f"- state_error: {error}")
        return 0 if report["status"] == "pass" and not state_errors else 2
    if args.command == "audit-s2plt02-terminal-delivery-inputs":
        report = build_s2plt02_terminal_delivery_input_inventory_state(
            generated_at=args.generated_at,
            repo_root=args.repo_root,
        )
        state_errors = validate_s2plt02_terminal_delivery_input_inventory_state(report)
        if state_errors:
            report = {**report, "state_validation_errors": state_errors}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- terminal_delivery_proof_ready: {report.get('terminal_delivery_proof_ready')}")
            print(f"- observed_real_delivery_days: {report.get('observed_real_delivery_days')}")
            print(f"- observed_real_email_count: {report.get('observed_real_email_count')}")
            for item in report.get("missing_inputs", []):
                print(f"- missing_input: {item}")
            for error in state_errors:
                print(f"- state_error: {error}")
        return 0 if report["status"] == "pass" and not state_errors else 2
    if args.command == "plan-s2plt02-terminal-delivery-proof-capture":
        report = build_s2plt02_terminal_delivery_proof_capture_plan_state(
            generated_at=args.generated_at,
            repo_root=args.repo_root,
        )
        state_errors = validate_s2plt02_terminal_delivery_proof_capture_plan_state(report)
        if state_errors:
            report = {**report, "state_validation_errors": state_errors}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- terminal_delivery_proof_ready: {report.get('terminal_delivery_proof_ready')}")
            print(f"- next_executable_step: {report.get('next_executable_step')}")
            for item in report.get("blocked_by_missing_inputs", []):
                print(f"- missing_input: {item}")
            for step in report.get("capture_steps", []):
                print(f"- capture_step: {step.get('step_id')}")
            for error in state_errors:
                print(f"- state_error: {error}")
        return 0 if report["status"] == "pass" and not state_errors else 2
    if args.command == "build-s2plt02-terminal-delivery-proof-artifact-draft":
        report = build_s2plt02_terminal_delivery_proof_artifact_draft_state(
            generated_at=args.generated_at,
            delivery_manifests=[load_json_mapping(path) for path in args.delivery_manifest],
            scheduler_proof=load_json_mapping(args.scheduler_proof),
        )
        artifact = report.get("artifact_draft")
        artifact_validation_errors = (
            validate_s2plt02_terminal_delivery_proof_artifact(artifact) if isinstance(artifact, Mapping) else []
        )
        report = {**report, "artifact_validation_errors": artifact_validation_errors}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
            for error in artifact_validation_errors:
                print(f"- artifact_error: {error}")
        return 0 if report["status"] == "pass" and not artifact_validation_errors else 2
    if args.command == "audit-s2plt03-resilience-readiness":
        report = build_s2plt03_resilience_precheck_report(generated_at=args.generated_at)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- s2plt03_accepted: {report.get('s2plt03_accepted')}")
            print(f"- s2plt03_resilience_drill_completed: {report.get('s2plt03_resilience_drill_completed')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-s2plt03-terminal-resilience-proof":
        report = build_s2plt03_terminal_resilience_proof_artifact_validation_state(repo_root=args.repo_root)
        errors = validate_s2plt03_terminal_resilience_proof_artifact_validation_state(report)
        if errors:
            report = dict(report)
            report["validation_errors"] = list(report.get("validation_errors", [])) + errors
            report["status"] = "blocked"
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_present: {report.get('artifact_present')}")
            print(f"- terminal_resilience_proof_ready: {report.get('terminal_resilience_proof_ready')}")
            print(f"- s2plt03_accepted_by_artifact: {report.get('s2plt03_accepted_by_artifact')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-final-reviewer-assignment":
        artifact_path = Path(args.path)
        payload = load_json_mapping(artifact_path) if artifact_path.exists() else None
        report = build_independent_final_reviewer_assignment_validation_state(payload)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_path: {report.get('artifact_path')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-p0-p1-zero-proof":
        artifact_path = Path(args.path)
        payload = load_json_mapping(artifact_path) if artifact_path.exists() else None
        report = build_p0_p1_zero_proof_artifact_validation_state(payload)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_path: {report.get('artifact_path')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-final-command-execution":
        artifact_path = Path(args.path)
        payload = load_json_mapping(artifact_path) if artifact_path.exists() else None
        report = build_final_command_execution_validation_state(payload)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_path: {report.get('artifact_path')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-final-bundle-manifest":
        artifact_path = Path(args.path)
        payload = load_json_mapping(artifact_path) if artifact_path.exists() else None
        report = build_final_acceptance_bundle_manifest_validation_state(payload)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_path: {report.get('manifest_path')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-s2plt04-completion-report":
        artifact_path = Path(args.path)
        payload = load_json_mapping(artifact_path) if artifact_path.exists() else None
        report = build_s2plt04_completion_report_validation_state(payload)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_path: {report.get('report_path')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "audit-s2plt04-completion-evidence":
        report = build_s2plt04_completion_evidence_audit_state(repo_root=Path(args.repo_root))
        errors = validate_s2plt04_completion_evidence_audit_state(report)
        output = {**report, "audit_validation_errors": errors}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- next_required_artifact: {report.get('next_required_artifact')}")
            print(f"- completion_report_ready: {report.get('completion_report_ready')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "validate-no-production-attestation":
        artifact_path = Path(args.path)
        payload = load_json_mapping(artifact_path) if artifact_path.exists() else None
        report = build_no_production_side_effect_attestation_validation_state(payload)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_path: {report.get('artifact_path')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "validate-next-agent-handoff":
        artifact_path = Path(args.path)
        payload = load_json_mapping(artifact_path) if artifact_path.exists() else None
        report = build_next_agent_handoff_validation_state(payload)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- artifact_path: {report.get('artifact_path')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" else 2
    if args.command == "build-final-reviewer-assignment-owner-packet":
        report = build_independent_final_reviewer_assignment_owner_packet_state()
        errors = validate_independent_final_reviewer_assignment_owner_packet_state(report)
        output = {**report, "owner_packet_validation_errors": errors}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- task_id: {report.get('task_id')}")
            print(f"- next_required_action: {report.get('next_required_action')}")
            print(f"- assignment_artifact_path: {report.get('assignment_artifact_path')}")
            print(f"- assignment_artifact_present: {report.get('assignment_artifact_present')}")
            print(f"- observed_open_p0_findings: {report.get('observed_open_p0_findings')}")
            print(f"- observed_open_p1_findings: {report.get('observed_open_p1_findings')}")
            for action in report.get("required_owner_actions", []):
                print(f"- required_owner_action: {action}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if not errors else 2
    if args.command == "build-final-reviewer-assignment-artifact-draft":
        report = build_independent_final_reviewer_assignment_artifact_draft_state(
            reviewer_id=args.reviewer_id,
            assigned_by=args.assigned_by,
            generated_at=args.generated_at,
            assignment_scope=args.assignment_scope,
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(report["status"])
            print(f"- task_id: {report.get('task_id')}")
            print(f"- artifact_path: {report.get('artifact_path')}")
            print(f"- assignment_artifact_written: {report.get('assignment_artifact_written')}")
            print(
                "- assignment_gate_satisfied_by_this_command: "
                f"{report.get('assignment_gate_satisfied_by_this_command')}"
            )
            print(f"- next_required_action: {report.get('next_required_action')}")
            for error in report.get("validation_errors", []):
                print(f"- error: {error}")
        return 0 if report["status"] == "draft" and not report.get("validation_errors") else 2
    if args.command == "build-final-closure-decision-owner-packet":
        report = build_independent_final_closure_decision_owner_packet_state()
        errors = validate_independent_final_closure_decision_owner_packet_state(report)
        output = {**report, "owner_packet_validation_errors": errors}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- task_id: {report.get('task_id')}")
            print(f"- next_required_action: {report.get('next_required_action')}")
            print(f"- decision_artifact_ref: {report.get('decision_artifact_ref')}")
            print(f"- assignment_artifact_path: {report.get('assignment_artifact_path')}")
            print(f"- assignment_artifact_present: {report.get('assignment_artifact_present')}")
            print(f"- independent_final_closure_decision_present: {report.get('independent_final_closure_decision_present')}")
            print(f"- observed_open_p0_findings: {report.get('observed_open_p0_findings')}")
            print(f"- observed_open_p1_findings: {report.get('observed_open_p1_findings')}")
            for action in report.get("required_owner_actions", []):
                print(f"- required_owner_action: {action}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if not errors else 2
    if args.command == "plan-final-bundle-prerequisites":
        report = build_final_bundle_prerequisite_plan_state()
        errors = validate_final_bundle_prerequisite_plan_state(report)
        output = {**report, "plan_validation_errors": errors}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- task_id: {report.get('task_id')}")
            print(f"- next_required_step: {report.get('next_required_step')}")
            print(f"- ready_for_final_bundle_manifest: {report.get('ready_for_final_bundle_manifest')}")
            for step in report.get("ordered_steps", []):
                print(f"- step: {step.get('step_id')} status={step.get('status')} artifact={step.get('artifact_ref')}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
    if args.command == "validate-final-acceptance-bundle":
        report = build_final_acceptance_bundle_readiness_state(repo_root=Path(args.repo_root))
        errors = validate_final_acceptance_bundle_readiness_state(report)
        output = {**report, "readiness_validation_errors": errors}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(report["status"])
            print(f"- scope: {report.get('scope')}")
            print(f"- bundle_present: {report.get('bundle_present')}")
            for item in report.get("missing_items", []):
                print(f"- missing: {item}")
            for reason in report.get("blocking_reasons", []):
                print(f"- blocked: {reason}")
            for error in errors:
                print(f"- error: {error}")
        return 0 if report["status"] == "pass" and not errors else 2
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
        fetcher = fetch_atom_with_curl if args.fetcher == "curl" else None
        report = build_live_all_arxiv_dry_run(
            generated_at=args.generated_at,
            date=args.date or None,
            max_results_per_category=args.max_results_per_category,
            fetcher=fetcher,
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


if __name__ == "__main__":
    raise SystemExit(main())
