from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .db import (
    connect,
    get_current_authority,
    init_database,
    list_sources,
    review_source,
    score_all,
    score_one,
    source_snapshot,
)
from .formatting import authority_badge
from .analyzer import CODEX_ANALYSIS_MODE, TEMPLATE_ANALYSIS_MODE
from .automation_status import (
    load_latest_automation_run,
    record_automation_step,
    write_automation_dashboard,
)
from .automation_readiness import (
    build_automation_readiness,
    cleanup_stale_pipeline_lock,
    inspect_pipeline_lock,
    write_automation_readiness_dashboard,
)
from .automation_scheduler import write_automation_scheduler_plan
from .ai_research_request import write_ai_research_priority_file
from .access_readiness import build_access_readiness, write_access_readiness_dashboard
from .attachment_parser_registry import (
    build_attachment_parser_status,
    write_attachment_parser_dashboard,
)
from .content_db import connect_content, init_content_database
from .content_db import (
    bulk_update_external_reference_gap_status,
    list_external_reference_gaps,
    reconcile_orphaned_pipeline_runs,
    update_external_reference_gap_status,
)
from .config_setup import write_config_setup
from .crawl_policy import build_crawl_policy_status, write_crawl_policy_dashboard
from .data_trust import write_data_trust_audit
from .benchmark import build_benchmark_status, write_benchmark_dashboard
from .chrome_bilibili_discovery import (
    build_chrome_bilibili_discovery,
    write_chrome_bilibili_discovery_dashboard,
)
from .credential_doctor import build_credential_doctor, write_credential_doctor_dashboard
from .gap_dashboard import write_gap_dashboard
from .monitor import write_monitor_status
from .ops_dashboard import ops_dashboard_summary, write_ops_dashboard
from .platform_auth_validation import (
    build_platform_auth_validation,
    write_platform_auth_validation_dashboard,
)
from .platform_auth_intake import (
    build_platform_auth_intake,
    write_platform_auth_intake_dashboard,
)
from .platform_auth_import import (
    import_platform_auth_cookie,
    import_platform_auth_cookie_bundle,
    import_platform_auth_cookie_directory,
    import_platform_auth_session_reference,
)
from .platform_coverage import build_platform_coverage, write_platform_coverage_dashboard
from .platform_parser_registry import (
    build_platform_parser_status,
    write_platform_parser_dashboard,
)
from .platform_parser_validation import (
    build_platform_parser_validation,
    write_platform_parser_validation_dashboard,
)
from .platform_parser_samples import (
    build_platform_parser_sample_acceptance,
    write_platform_parser_sample_dashboard,
)
from .pipeline import PipelineConfig, run_pipeline
from .quality_gates import (
    build_quality_gate_status,
    quality_rule_thresholds,
    write_quality_gates_dashboard,
)
from .report_artifacts import inspect_report_artifacts, write_report_artifact_dashboard
from .reference_gaps import gap_action_label, gap_type_label
from .readiness import build_readiness_status
from .search_validation import build_search_validation, write_search_validation_dashboard
from .search_secret_import import import_search_secret, import_search_secret_bundle
from .search_secret_intake import build_search_secret_intake, write_search_secret_intake_dashboard
from .setup_wizard import build_setup_wizard, write_setup_wizard_dashboard
from .seeds import import_official_csv, seed_from_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source-registry",
        description="Manage the independent source authority registry database.",
    )
    parser.add_argument(
        "--db",
        default="data/source_registry.sqlite",
        help="Path to source_registry.sqlite.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize or migrate the database schema.")

    seed = sub.add_parser("seed", help="Import JSON seed sources and score them.")
    seed.add_argument(
        "--seed-file",
        default="config/seed_sources.json",
        help="JSON seed file path.",
    )

    import_csv = sub.add_parser(
        "import-csv",
        help="Import official government website catalog CSV or ZIP files.",
    )
    import_csv.add_argument("path", help="CSV or ZIP path.")

    score = sub.add_parser("score", help="Recompute authority score.")
    score.add_argument("--source-id", help="Source id. If omitted, score all sources.")

    listing = sub.add_parser("list", help="List current source authority records.")
    listing.add_argument("--crawl-enabled", action="store_true")
    listing.add_argument("--min-score", type=int)
    listing.add_argument("--json", action="store_true")

    show = sub.add_parser("show", help="Show one source authority record.")
    show.add_argument("source_id")
    show.add_argument("--json", action="store_true")

    review = sub.add_parser("review", help="Record a manual review/final score.")
    review.add_argument("source_id")
    review.add_argument("--final-score", type=int)
    review.add_argument(
        "--status",
        default="user_confirmed",
        choices=[
            "unreviewed",
            "system_scored",
            "user_confirmed",
            "rejected",
            "needs_review",
        ],
    )
    review.add_argument("--reviewer")
    review.add_argument("--note")

    snapshot = sub.add_parser(
        "snapshot",
        help="Emit the source authority snapshot fields for a document record.",
    )
    snapshot.add_argument("source_id")

    status = sub.add_parser(
        "status",
        help="Write and print the latest automation health status.",
    )
    status.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    status.add_argument(
        "--data-dir",
        default="data",
        help="Directory for monitor output and run logs.",
    )
    status.add_argument(
        "--analysis-mode",
        choices=["template", "codex"],
        default="template",
        help="Queue analysis mode to inspect.",
    )
    status.add_argument("--min-external-references", type=int)
    status.add_argument("--min-external-platforms", type=int)
    status.add_argument(
        "--quality-rules-file",
        default="rules/quality_gates.json",
        help="Declarative quality gate rules file.",
    )
    status.add_argument("--json", action="store_true")

    automation_step = sub.add_parser(
        "automation-step",
        help="Record one automation step status into data/automation/latest_run.json.",
    )
    automation_step.add_argument("--data-dir", default="data")
    automation_step.add_argument("--run-id", required=True)
    automation_step.add_argument("--step-key", required=True)
    automation_step.add_argument("--step-label", required=True)
    automation_step.add_argument(
        "--status",
        required=True,
        choices=["running", "completed", "failed", "skipped"],
    )
    automation_step.add_argument("--exit-code", type=int)
    automation_step.add_argument("--error-summary")
    automation_step.add_argument("--json", action="store_true")

    automation_dashboard = sub.add_parser(
        "automation-dashboard",
        help="Render the latest automation step status dashboard.",
    )
    automation_dashboard.add_argument("--data-dir", default="data")
    automation_dashboard.add_argument(
        "--output",
        default="reports/automation_run_dashboard.html",
        help="Output HTML automation step dashboard path.",
    )
    automation_dashboard.add_argument("--json", action="store_true")

    automation_lock = sub.add_parser(
        "automation-lock-clean",
        help="Inspect and safely remove a stale data/pipeline.lock whose PID is no longer running.",
    )
    automation_lock.add_argument("--data-dir", default="data")
    automation_lock.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Optional content database used to mark orphaned running pipeline_runs as failed when no lock is active.",
    )
    automation_lock.add_argument("--json", action="store_true")

    automation_readiness = sub.add_parser(
        "automation-readiness",
        help="Check unattended twice-daily automation readiness: schedule, lock, queue, monitor and P0 credentials.",
    )
    automation_readiness.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    automation_readiness.add_argument("--data-dir", default="data")
    automation_readiness.add_argument(
        "--analysis-mode",
        choices=["template", "codex"],
        default="template",
        help="Queue analysis mode to inspect.",
    )
    automation_readiness.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Values are never printed.",
    )
    automation_readiness.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Values and full paths are not printed.",
    )
    automation_readiness.add_argument(
        "--quality-rules-file",
        default="rules/quality_gates.json",
        help="Declarative quality gate rules file.",
    )
    automation_readiness.add_argument(
        "--schedule-time",
        action="append",
        help="Expected daily run time. Can be repeated, for example --schedule-time 09:00 --schedule-time 21:00.",
    )
    automation_readiness.add_argument(
        "--scheduler-file",
        help="Optional scheduler evidence file, for example data/automation/scheduler.json. Secret values are never printed.",
    )
    automation_readiness.add_argument(
        "--max-running-minutes",
        type=int,
        default=180,
        help="Maximum allowed duration for a running automation record before it is treated as failed.",
    )
    automation_readiness.add_argument(
        "--output",
        default="reports/automation_readiness_dashboard.html",
        help="Output HTML automation readiness dashboard path.",
    )
    automation_readiness.add_argument("--json", action="store_true")

    automation_scheduler = sub.add_parser(
        "automation-scheduler-plan",
        help="Generate a reviewable launchd scheduler plan without installing or enabling it.",
    )
    automation_scheduler.add_argument(
        "--workspace",
        default=".",
        help="Workspace directory that launchd should run from.",
    )
    automation_scheduler.add_argument("--data-dir", default="data")
    automation_scheduler.add_argument(
        "--output-dir",
        default="reports",
        help="Directory for the launchd plist draft, manifest example and dashboard.",
    )
    automation_scheduler.add_argument(
        "--label",
        default="com.source-registry.policy-report",
        help="launchd label.",
    )
    automation_scheduler.add_argument(
        "--schedule-time",
        action="append",
        help="Expected daily run time. Can be repeated, for example --schedule-time 09:00 --schedule-time 21:00.",
    )
    automation_scheduler.add_argument(
        "--timezone",
        default="Australia/Sydney",
        help="Human-facing timezone recorded in the manifest example.",
    )
    automation_scheduler.add_argument(
        "--entrypoint",
        default="bash scripts/run_policy_report.sh",
        help="Command run by launchd after cd into the workspace.",
    )
    automation_scheduler.add_argument("--json", action="store_true")

    gaps = sub.add_parser(
        "gaps",
        help="List external reference gaps that block report quality gates.",
    )
    gaps.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    gaps.add_argument(
        "--status",
        choices=["pending", "resolved", "ignored", "all"],
        default="pending",
        help="Gap status to list.",
    )
    gaps.add_argument("--required-action", help="Filter by required action.")
    gaps.add_argument("--gap-type", help="Filter by gap type.")
    gaps.add_argument("--limit", type=int, default=30)
    gaps.add_argument("--json", action="store_true")

    gap_review = sub.add_parser(
        "gap-review",
        help="Mark one external reference gap as resolved, ignored, or pending.",
    )
    gap_review.add_argument("gap_id")
    gap_review.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    gap_review.add_argument(
        "--status",
        required=True,
        choices=["pending", "resolved", "ignored"],
    )
    gap_review.add_argument("--reviewer")
    gap_review.add_argument("--note")
    gap_review.add_argument("--json", action="store_true")

    gap_bulk = sub.add_parser(
        "gap-bulk-review",
        help="Bulk mark external reference gaps by action, type, or platform.",
    )
    gap_bulk.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    gap_bulk.add_argument(
        "--status",
        required=True,
        choices=["pending", "resolved", "ignored"],
        help="New status to apply.",
    )
    gap_bulk.add_argument(
        "--from-status",
        default="pending",
        choices=["pending", "resolved", "ignored", "all"],
        help="Current status to select from.",
    )
    gap_bulk.add_argument("--required-action", help="Filter by required action.")
    gap_bulk.add_argument("--gap-type", help="Filter by gap type.")
    gap_bulk.add_argument("--platform", help="Filter by platform.")
    gap_bulk.add_argument("--limit", type=int, default=100)
    gap_bulk.add_argument("--reviewer")
    gap_bulk.add_argument("--note")
    gap_bulk.add_argument("--dry-run", action="store_true")
    gap_bulk.add_argument("--json", action="store_true")

    gap_dashboard = sub.add_parser(
        "gap-dashboard",
        help="Generate a visual HTML dashboard for external reference gaps.",
    )
    gap_dashboard.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    gap_dashboard.add_argument(
        "--status",
        choices=["pending", "resolved", "ignored", "all"],
        default="pending",
        help="Gap status to visualize.",
    )
    gap_dashboard.add_argument("--limit", type=int, default=300)
    gap_dashboard.add_argument(
        "--output",
        default="reports/external_reference_gap_dashboard.html",
        help="Output HTML dashboard path.",
    )
    gap_dashboard.add_argument("--json", action="store_true")

    ops_dashboard = sub.add_parser(
        "ops-dashboard",
        help="Generate a cross-run operations dashboard for reports, gaps, queue, and quality gates.",
    )
    ops_dashboard.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    ops_dashboard.add_argument(
        "--data-dir",
        default="data",
        help="Directory for monitor output and run logs.",
    )
    ops_dashboard.add_argument(
        "--analysis-mode",
        choices=["template", "codex"],
        default="template",
        help="Queue analysis mode to visualize.",
    )
    ops_dashboard.add_argument("--min-external-references", type=int)
    ops_dashboard.add_argument("--min-external-platforms", type=int)
    ops_dashboard.add_argument(
        "--quality-rules-file",
        default="rules/quality_gates.json",
        help="Declarative quality gate rules file.",
    )
    ops_dashboard.add_argument(
        "--output",
        default="reports/policy_ops_dashboard.html",
        help="Output HTML operations dashboard path.",
    )
    ops_dashboard.add_argument("--json", action="store_true")

    platform_coverage = sub.add_parser(
        "platform-coverage",
        help="Generate a platform coverage matrix for full-web readiness.",
    )
    platform_coverage.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    platform_coverage.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Values are never printed.",
    )
    platform_coverage.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Paths are not printed.",
    )
    platform_coverage.add_argument(
        "--interpretation-source-file",
        default="config/interpretation_sources.json",
        help="JSON config for interpretation/search sources.",
    )
    platform_coverage.add_argument(
        "--output",
        default="reports/platform_coverage_dashboard.html",
        help="Output HTML platform coverage dashboard path.",
    )
    platform_coverage.add_argument("--json", action="store_true")

    platform_parsers = sub.add_parser(
        "platform-parsers",
        help="Generate a platform parser capability registry dashboard.",
    )
    platform_parsers.add_argument(
        "--parser-file",
        default="config/platform_parsers.json",
        help="JSON platform parser capability registry.",
    )
    platform_parsers.add_argument(
        "--output",
        default="reports/platform_parser_dashboard.html",
        help="Output HTML platform parser dashboard path.",
    )
    platform_parsers.add_argument("--json", action="store_true")

    platform_parser_validate = sub.add_parser(
        "platform-parser-validate",
        help="Validate platform parser acceptance prerequisites against local search keys and platform auth state.",
    )
    platform_parser_validate.add_argument(
        "--parser-file",
        default="config/platform_parsers.json",
        help="JSON platform parser capability registry.",
    )
    platform_parser_validate.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Values are never printed.",
    )
    platform_parser_validate.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Paths are summarized only.",
    )
    platform_parser_validate.add_argument(
        "--output",
        default="reports/platform_parser_validation_dashboard.html",
        help="Output HTML platform parser validation dashboard path.",
    )
    platform_parser_validate.add_argument("--json", action="store_true")

    platform_parser_samples = sub.add_parser(
        "platform-parser-samples",
        help="Validate platform parser output against local collected interpretation samples.",
    )
    platform_parser_samples.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    platform_parser_samples.add_argument(
        "--parser-file",
        default="config/platform_parsers.json",
        help="JSON platform parser capability registry.",
    )
    platform_parser_samples.add_argument("--limit", type=int, default=200)
    platform_parser_samples.add_argument(
        "--output",
        default="reports/platform_parser_sample_dashboard.html",
        help="Output HTML platform parser sample acceptance dashboard path.",
    )
    platform_parser_samples.add_argument("--json", action="store_true")

    crawl_policy = sub.add_parser(
        "crawl-policy",
        help="Generate a crawl policy and compliance boundary dashboard for source registry entries.",
    )
    crawl_policy.add_argument(
        "--policy-file",
        default="config/crawl_policies.json",
        help="JSON crawl policy registry.",
    )
    crawl_policy.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include sources whose crawl_enabled flag is false.",
    )
    crawl_policy.add_argument(
        "--check-robots",
        action="store_true",
        help="Fetch robots.txt and check whether the configured User-Agent can fetch each source homepage.",
    )
    crawl_policy.add_argument("--robots-timeout", type=int, default=8)
    crawl_policy.add_argument(
        "--allow-insecure-tls",
        action="store_true",
        help="Allow robots.txt checks with relaxed TLS verification when local trust store fails. Off by default.",
    )
    crawl_policy.add_argument("--limit", type=int, default=300)
    crawl_policy.add_argument(
        "--output",
        default="reports/crawl_policy_dashboard.html",
        help="Output HTML crawl policy dashboard path.",
    )
    crawl_policy.add_argument("--json", action="store_true")

    attachment_parsers = sub.add_parser(
        "attachment-parsers",
        help="Generate an attachment parser capability registry dashboard.",
    )
    attachment_parsers.add_argument(
        "--parser-file",
        default="config/attachment_parsers.json",
        help="JSON parser capability registry.",
    )
    attachment_parsers.add_argument(
        "--output",
        default="reports/attachment_parser_dashboard.html",
        help="Output HTML attachment parser dashboard path.",
    )
    attachment_parsers.add_argument("--json", action="store_true")

    setup_wizard = sub.add_parser(
        "setup-wizard",
        help="Generate a local onboarding wizard for search keys, platform auth, readiness, and dashboards.",
    )
    setup_wizard.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    setup_wizard.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Directory used by setup-config templates.",
    )
    setup_wizard.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Values are never printed.",
    )
    setup_wizard.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Paths are summarized only.",
    )
    setup_wizard.add_argument(
        "--interpretation-source-file",
        default="config/interpretation_sources.json",
        help="JSON config for interpretation/search sources.",
    )
    setup_wizard.add_argument(
        "--output",
        default="reports/setup_wizard_dashboard.html",
        help="Output HTML setup wizard dashboard path.",
    )
    setup_wizard.add_argument("--json", action="store_true")

    access_readiness = sub.add_parser(
        "access-readiness",
        help="Generate one consolidated full-web access readiness dashboard for search, platform auth, and parser prerequisites.",
    )
    access_readiness.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    access_readiness.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Values are never printed.",
    )
    access_readiness.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Paths are summarized only.",
    )
    access_readiness.add_argument(
        "--parser-file",
        default="config/platform_parsers.json",
        help="JSON platform parser capability registry.",
    )
    access_readiness.add_argument(
        "--interpretation-source-file",
        default="config/interpretation_sources.json",
        help="JSON config for interpretation/search sources.",
    )
    access_readiness.add_argument(
        "--output",
        default="reports/access_readiness_dashboard.html",
        help="Output HTML access readiness dashboard path.",
    )
    access_readiness.add_argument("--json", action="store_true")

    data_trust = sub.add_parser(
        "data-trust-audit",
        help="Generate a local read-only Data Trust audit bundle for policy sources, content, reports, and control files.",
    )
    data_trust.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    data_trust.add_argument(
        "--report-dir",
        default="reports",
        help="Directory containing generated policy reports and dashboards.",
    )
    data_trust.add_argument(
        "--output-dir",
        default="reports/system_audit",
        help="Directory for Data Trust JSON/CSV/Markdown/PDF audit outputs.",
    )
    data_trust.add_argument(
        "--as-of",
        help="Optional audit date label in YYYY-MM-DD format.",
    )
    data_trust.add_argument("--json", action="store_true")

    credential_doctor = sub.add_parser(
        "credential-doctor",
        help="Check local search key and platform auth files without exposing secret values.",
    )
    credential_doctor.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Directory used by setup-config templates.",
    )
    credential_doctor.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Values are never printed.",
    )
    credential_doctor.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Values and full cookie paths are not printed.",
    )
    credential_doctor.add_argument(
        "--output",
        default="reports/credential_doctor_dashboard.html",
        help="Output HTML credential doctor dashboard path.",
    )
    credential_doctor.add_argument("--json", action="store_true")

    search_validate = sub.add_parser(
        "search-validate",
        help="Validate SerpAPI/Bing/Google CSE connectivity without exposing API keys.",
    )
    search_validate.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Values are never printed.",
    )
    search_validate.add_argument("--query", default="中国 政策 解读")
    search_validate.add_argument("--timeout", type=int, default=10)
    search_validate.add_argument("--retries", type=int, default=0)
    search_validate.add_argument("--allow-insecure-tls", action="store_true")
    search_validate.add_argument(
        "--offline",
        action="store_true",
        help="Only check configuration, do not call external search APIs.",
    )
    search_validate.add_argument(
        "--output",
        default="reports/search_validation_dashboard.html",
        help="Output HTML search validation dashboard path.",
    )
    search_validate.add_argument("--json", action="store_true")

    search_secret_import = sub.add_parser(
        "search-secret-import",
        help="Safely import a search API key into the private local search secret file.",
    )
    search_secret_import.add_argument(
        "--provider",
        required=True,
        choices=["serpapi", "bing", "google"],
        help="Search provider to update.",
    )
    search_secret_import.add_argument(
        "--value-file",
        help="Local file containing the API key. The value is never printed.",
    )
    search_secret_import.add_argument(
        "--value-env",
        help="Environment variable name containing the API key. The value is never printed.",
    )
    search_secret_import.add_argument(
        "--engine-id-file",
        help="Google CSE only: local file containing GOOGLE_CSE_ID.",
    )
    search_secret_import.add_argument(
        "--engine-id-env",
        help="Google CSE only: environment variable name containing GOOGLE_CSE_ID.",
    )
    search_secret_import.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Private directory used by setup-config templates.",
    )
    search_secret_import.add_argument(
        "--search-secrets-file",
        help="JSON search secrets file to update.",
    )
    search_secret_import.add_argument("--force", action="store_true", help="Overwrite existing provider values.")
    search_secret_import.add_argument("--dry-run", action="store_true", help="Validate inputs and show sanitized planned result without writing.")
    search_secret_import.add_argument("--json", action="store_true")

    search_secret_bulk_import = sub.add_parser(
        "search-secret-bulk-import",
        help="Safely import multiple search API fields from one local JSON bundle.",
    )
    search_secret_bulk_import.add_argument(
        "--source-file",
        required=True,
        help="Local JSON file containing search API fields. Values are never printed.",
    )
    search_secret_bulk_import.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Private directory used by setup-config templates.",
    )
    search_secret_bulk_import.add_argument(
        "--search-secrets-file",
        help="JSON search secrets file to update.",
    )
    search_secret_bulk_import.add_argument("--force", action="store_true", help="Overwrite existing provider values.")
    search_secret_bulk_import.add_argument("--dry-run", action="store_true", help="Validate inputs and show sanitized planned result without writing.")
    search_secret_bulk_import.add_argument("--json", action="store_true")

    search_secret_intake = sub.add_parser(
        "search-secret-intake",
        help="Generate a search API key intake checklist with import and validation commands.",
    )
    search_secret_intake.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Private directory used by setup-config templates.",
    )
    search_secret_intake.add_argument(
        "--search-secrets-file",
        help="JSON search secrets file to inspect. Values are never printed.",
    )
    search_secret_intake.add_argument(
        "--output",
        default="reports/search_secret_intake_dashboard.html",
        help="Output HTML search secret intake dashboard path.",
    )
    search_secret_intake.add_argument("--json", action="store_true")

    platform_auth_validate = sub.add_parser(
        "platform-auth-validate",
        help="Validate local platform authorization files without exposing cookies or session values.",
    )
    platform_auth_validate.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Values and full paths are not printed.",
    )
    platform_auth_validate.add_argument(
        "--platform",
        action="append",
        help="Optional platform filter. Can be repeated, for example --platform bilibili --platform zhihu.",
    )
    platform_auth_validate.add_argument(
        "--online",
        action="store_true",
        help="Run explicit online validation. Bilibili uses a dedicated login-state check; other platforms use configured validation_url markers.",
    )
    platform_auth_validate.add_argument("--timeout", type=int, default=10)
    platform_auth_validate.add_argument("--retries", type=int, default=0)
    platform_auth_validate.add_argument("--allow-insecure-tls", action="store_true")
    platform_auth_validate.add_argument(
        "--output",
        default="reports/platform_auth_validation_dashboard.html",
        help="Output HTML platform auth validation dashboard path.",
    )
    platform_auth_validate.add_argument("--json", action="store_true")

    platform_auth_intake = sub.add_parser(
        "platform-auth-intake",
        help="Generate a platform authorization intake checklist with target files and validation commands.",
    )
    platform_auth_intake.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Directory used by setup-config templates.",
    )
    platform_auth_intake.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Values and full paths are not printed.",
    )
    platform_auth_intake.add_argument(
        "--output",
        default="reports/platform_auth_intake_dashboard.html",
        help="Output HTML platform auth intake dashboard path.",
    )
    platform_auth_intake.add_argument("--json", action="store_true")

    platform_auth_import = sub.add_parser(
        "platform-auth-import",
        help="Safely import a locally exported platform cookie into the private auth store.",
    )
    platform_auth_import.add_argument(
        "--platform",
        required=True,
        help="Platform key, for example bilibili, zhihu, weibo, douyin, wechat.",
    )
    platform_auth_import.add_argument(
        "--source-file",
        help="Local file containing the exported cookie string. The cookie value is never printed.",
    )
    platform_auth_import.add_argument(
        "--cookie-env",
        help="Environment variable name that contains the cookie string. The value is never printed.",
    )
    platform_auth_import.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Private directory used by setup-config templates.",
    )
    platform_auth_import.add_argument(
        "--platform-auth-file",
        help="JSON file to update with the imported cookie path.",
    )
    platform_auth_import.add_argument(
        "--target-file",
        help="Optional target cookie file. Defaults to <secure-dir>/cookies/<platform>_cookie.txt.",
    )
    platform_auth_import.add_argument("--force", action="store_true", help="Overwrite the target cookie file if it exists.")
    platform_auth_import.add_argument("--dry-run", action="store_true", help="Validate inputs and show the planned target without writing.")
    platform_auth_import.add_argument("--json", action="store_true")

    platform_auth_session_import = sub.add_parser(
        "platform-auth-session-import",
        help="Register a local Chrome/Playwright session file or Chrome profile directory without copying secrets.",
    )
    platform_auth_session_import.add_argument(
        "--platform",
        required=True,
        help="Platform key, for example bilibili, zhihu, weibo, douyin, wechat.",
    )
    platform_auth_session_import.add_argument(
        "--session-file",
        required=True,
        help="Local Chrome/Playwright session file or Chrome profile directory. Full path is never printed.",
    )
    platform_auth_session_import.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Private directory used by setup-config templates.",
    )
    platform_auth_session_import.add_argument(
        "--platform-auth-file",
        help="JSON file to update with the session reference.",
    )
    platform_auth_session_import.add_argument(
        "--auth-method",
        choices=["chrome_session", "chrome_profile_reference"],
        help="Optional auth method label. Defaults from file-vs-directory type.",
    )
    platform_auth_session_import.add_argument("--dry-run", action="store_true", help="Validate inputs without writing.")
    platform_auth_session_import.add_argument("--json", action="store_true")

    platform_auth_bulk_import = sub.add_parser(
        "platform-auth-bulk-import",
        help="Safely import multiple platform cookie files from a local directory.",
    )
    platform_auth_bulk_import.add_argument(
        "--source-dir",
        required=True,
        help="Directory containing files such as bilibili_cookie.txt, zhihu_cookie.txt, weibo_cookie.txt.",
    )
    platform_auth_bulk_import.add_argument(
        "--platform",
        action="append",
        help="Optional platform filter. Can be repeated. Defaults to all supported platforms.",
    )
    platform_auth_bulk_import.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Private directory used by setup-config templates.",
    )
    platform_auth_bulk_import.add_argument(
        "--platform-auth-file",
        help="JSON file to update with imported cookie paths.",
    )
    platform_auth_bulk_import.add_argument("--force", action="store_true", help="Overwrite target cookie files if they exist.")
    platform_auth_bulk_import.add_argument("--dry-run", action="store_true", help="Validate inputs and show planned targets without writing.")
    platform_auth_bulk_import.add_argument("--json", action="store_true")

    platform_auth_bundle_import = sub.add_parser(
        "platform-auth-bundle-import",
        help="Safely import platform cookie files from one local JSON bundle of file paths.",
    )
    platform_auth_bundle_import.add_argument(
        "--source-file",
        required=True,
        help="Local JSON file mapping platforms to exported cookie file paths. Values are never printed.",
    )
    platform_auth_bundle_import.add_argument(
        "--platform",
        action="append",
        help="Optional platform filter. Can be repeated. Defaults to all supported platforms.",
    )
    platform_auth_bundle_import.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Private directory used by setup-config templates.",
    )
    platform_auth_bundle_import.add_argument(
        "--platform-auth-file",
        help="JSON file to update with imported cookie paths.",
    )
    platform_auth_bundle_import.add_argument("--force", action="store_true", help="Overwrite target cookie files if they exist.")
    platform_auth_bundle_import.add_argument("--dry-run", action="store_true", help="Validate inputs and show planned targets without writing.")
    platform_auth_bundle_import.add_argument("--json", action="store_true")

    chrome_bilibili_discovery = sub.add_parser(
        "chrome-bilibili-discovery",
        help="Read authorized local Chrome History/Cookies status for Bilibili without exposing cookie values.",
    )
    chrome_bilibili_discovery.add_argument(
        "--chrome-profile-dir",
        help="Chrome profile directory. Defaults to ~/Library/Application Support/Google/Chrome/Default.",
    )
    chrome_bilibili_discovery.add_argument("--history-file", help="Optional explicit Chrome History SQLite file.")
    chrome_bilibili_discovery.add_argument("--cookies-file", help="Optional explicit Chrome Cookies SQLite file.")
    chrome_bilibili_discovery.add_argument("--keyword", default="", help="Optional keyword filter for Bilibili history candidates.")
    chrome_bilibili_discovery.add_argument("--limit", type=int, default=30)
    chrome_bilibili_discovery.add_argument(
        "--output",
        default="reports/chrome_bilibili_discovery_dashboard.html",
        help="Output HTML local discovery dashboard path.",
    )
    chrome_bilibili_discovery.add_argument("--json", action="store_true")

    benchmark_dashboard = sub.add_parser(
        "benchmark-dashboard",
        help="Generate the open-source/commercial reference-model benchmark dashboard.",
    )
    benchmark_dashboard.add_argument(
        "--benchmark-file",
        default="config/benchmark_models.json",
        help="JSON benchmark registry with source evidence and capability targets.",
    )
    benchmark_dashboard.add_argument(
        "--output",
        default="reports/benchmark_dashboard.html",
        help="Output HTML benchmark dashboard path.",
    )
    benchmark_dashboard.add_argument("--json", action="store_true")

    quality_gates = sub.add_parser(
        "quality-gates",
        help="Generate the declarative report quality-gate dashboard.",
    )
    quality_gates.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    quality_gates.add_argument(
        "--data-dir",
        default="data",
        help="Directory for monitor output and run logs.",
    )
    quality_gates.add_argument(
        "--analysis-mode",
        choices=["template", "codex"],
        default="template",
        help="Queue analysis mode to inspect.",
    )
    quality_gates.add_argument(
        "--quality-rules-file",
        default="rules/quality_gates.json",
        help="Declarative quality gate rules file.",
    )
    quality_gates.add_argument(
        "--output",
        default="reports/quality_gates_dashboard.html",
        help="Output HTML quality-gates dashboard path.",
    )
    quality_gates.add_argument("--json", action="store_true")

    report_check = sub.add_parser(
        "report-check",
        help="Inspect generated PDF/HTML/Markdown/dashboard report artifacts.",
    )
    report_check.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database. Used when --report-path is omitted.",
    )
    report_check.add_argument(
        "--report-path",
        help="PDF report path to inspect. Defaults to the latest pipeline run report.",
    )
    report_check.add_argument(
        "--output",
        default="reports/report_artifact_check_dashboard.html",
        help="Output HTML report artifact check dashboard path.",
    )
    report_check.add_argument("--json", action="store_true")

    readiness = sub.add_parser(
        "readiness",
        help="Check safe local readiness for search API keys and platform authorization files.",
    )
    readiness.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    readiness.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Values are never printed.",
    )
    readiness.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files. Paths are not printed.",
    )
    readiness.add_argument(
        "--interpretation-source-file",
        default="config/interpretation_sources.json",
        help="JSON config for interpretation/search sources.",
    )
    readiness.add_argument("--json", action="store_true")

    setup_config = sub.add_parser(
        "setup-config",
        help="Create local secret/auth template files outside the project.",
    )
    setup_config.add_argument(
        "--secure-dir",
        default="~/.policy-intelligence",
        help="Directory for generated local templates. Defaults to ~/.policy-intelligence.",
    )
    setup_config.add_argument(
        "--search-secrets-path",
        help="Optional explicit path for the search API key template.",
    )
    setup_config.add_argument(
        "--platform-auth-path",
        help="Optional explicit path for the platform auth template.",
    )
    setup_config.add_argument("--force", action="store_true", help="Overwrite existing template files.")
    setup_config.add_argument("--dry-run", action="store_true", help="Print planned files without writing.")
    setup_config.add_argument("--json", action="store_true")

    ai_research_priority = sub.add_parser(
        "ai-research-priority",
        help="Build a temporary industry priority file from an AI-Research-System policy request.",
    )
    ai_research_priority.add_argument("--request-file", required=True)
    ai_research_priority.add_argument(
        "--base-file",
        default="config/industry_priorities.json",
        help="Base industry priority config to preserve after request-focused industries.",
    )
    ai_research_priority.add_argument(
        "--output",
        default="data/ai_research_policy_request_industries.json",
        help="Output temporary industry priority JSON.",
    )
    ai_research_priority.add_argument("--json", action="store_true")

    run = sub.add_parser(
        "run",
        help="Run the automation-ready collection, analysis, and report pipeline.",
    )
    run.add_argument(
        "--content-db",
        default="data/policy_documents.sqlite",
        help="Path to the document/content SQLite database.",
    )
    run.add_argument(
        "--data-dir",
        default="data",
        help="Directory for locks, snapshots, and run logs.",
    )
    run.add_argument(
        "--report-dir",
        default="reports",
        help="Directory for generated PDF reports and HTML/Markdown sidecar files.",
    )
    run.add_argument("--max-sources", type=int, default=5)
    run.add_argument("--max-pages-per-source", type=int, default=2)
    run.add_argument("--max-links-per-page", type=int, default=20)
    run.add_argument("--max-analyze", type=int, default=20)
    run.add_argument("--max-interpretation-documents", type=int, default=10)
    run.add_argument(
        "--min-external-references",
        type=int,
        help="Minimum count of usable public external research/interpretation references expected in each report.",
    )
    run.add_argument(
        "--min-external-platforms",
        type=int,
        help="Minimum count of distinct external platforms expected in each report.",
    )
    run.add_argument(
        "--quality-rules-file",
        default="rules/quality_gates.json",
        help="Declarative quality gate rules file. CLI min values override this file when provided.",
    )
    run.add_argument(
        "--fetch-interpretation-results",
        action="store_true",
        help="Fetch public interpretation results, including Bilibili public video search metadata when available.",
    )
    run.add_argument(
        "--bilibili-cookie-file",
        help="Optional path to a Bilibili cookie text file. Do not store passwords in this project.",
    )
    run.add_argument(
        "--search-secrets-file",
        help="Optional JSON or dotenv file for search API keys. Do not commit this file.",
    )
    run.add_argument(
        "--platform-auth-file",
        help="Optional JSON file that points to local cookie/session files for external platforms. Do not commit this file.",
    )
    run.add_argument(
        "--fetch-search-result-pages",
        action="store_true",
        help="Fetch public webpages returned by search APIs and extract readable article/body excerpts when possible.",
    )
    run.add_argument(
        "--interpretation-request-timeout",
        type=int,
        default=20,
        help="Timeout in seconds for public interpretation source requests.",
    )
    run.add_argument(
        "--interpretation-request-retries",
        type=int,
        default=1,
        help="Retry count for public interpretation and search API requests.",
    )
    run.add_argument(
        "--interpretation-request-delay-seconds",
        type=float,
        default=0.0,
        help="Optional delay between external interpretation source requests.",
    )
    run.add_argument("--min-authority-score", type=int, default=60)
    run.add_argument(
        "--interpretation-source-file",
        default="config/interpretation_sources.json",
        help="JSON config for non-original interpretation sources such as Bilibili video searches.",
    )
    run.add_argument(
        "--industry-priority-file",
        default="config/industry_priorities.json",
        help="JSON config for industry priority order and keyword classification.",
    )
    run.add_argument(
        "--document-since",
        default="2025-01-01",
        help="Only queue documents whose published_date or discovered_at is on or after this date.",
    )
    run.add_argument(
        "--analysis-mode",
        choices=["template", "codex"],
        default="template",
        help="Use template for deterministic triage or codex for codex exec analysis.",
    )
    run.add_argument(
        "--mode",
        default="manual",
        choices=["manual", "automation"],
        help="Stored run mode.",
    )
    run.add_argument(
        "--allow-insecure-tls",
        action="store_true",
        help="Allow fetching HTTPS pages when the local Python trust store cannot verify a certificate chain.",
    )
    run.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db_path = Path(args.db)
    if args.command == "data-trust-audit":
        audit = write_data_trust_audit(
            source_db=args.db,
            content_db=args.content_db,
            root=".",
            report_dir=args.report_dir,
            output_dir=args.output_dir,
            as_of=args.as_of,
        )
        if args.json:
            print(json.dumps(audit, ensure_ascii=False, indent=2))
        else:
            outputs = audit.get("outputs") or {}
            print(f"data_trust_audit: {outputs.get('pdf')}")
            print(
                f"status: {audit.get('audit_status')} records: {audit.get('record_count')} "
                f"review: {audit.get('review_count')} rejected: {audit.get('rejected_count')}"
            )
        return 0
    conn = connect(db_path)
    init_database(conn)

    try:
        if args.command == "init":
            print(f"initialized {db_path}")
            return 0
        if args.command == "seed":
            source_ids = seed_from_file(conn, args.seed_file)
            print(f"seeded {len(source_ids)} sources")
            return 0
        if args.command == "import-csv":
            source_ids = import_official_csv(conn, args.path)
            print(f"imported {len(source_ids)} sources")
            return 0
        if args.command == "score":
            if args.source_id:
                record = score_one(conn, args.source_id)
                print(authority_badge(record))
            else:
                records = score_all(conn)
                print(f"scored {len(records)} sources")
            return 0
        if args.command == "list":
            records = list_sources(
                conn,
                crawl_enabled=True if args.crawl_enabled else None,
                min_score=args.min_score,
            )
            if args.json:
                print(json.dumps(records, ensure_ascii=False, indent=2))
            else:
                for record in records:
                    print(f"{record['source_id']} | {authority_badge(record)} | {record['official_url']}")
            return 0
        if args.command == "show":
            record = get_current_authority(conn, args.source_id)
            if args.json:
                print(json.dumps(record, ensure_ascii=False, indent=2))
            else:
                print(authority_badge(record))
                print(record["official_url"])
            return 0
        if args.command == "review":
            record = review_source(
                conn,
                args.source_id,
                args.final_score,
                args.status,
                reviewer=args.reviewer,
                note=args.note,
            )
            print(authority_badge(record))
            return 0
        if args.command == "snapshot":
            print(
                json.dumps(
                    source_snapshot(conn, args.source_id),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "status":
            thresholds = _quality_thresholds(args)
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            target_analysis_mode = (
                CODEX_ANALYSIS_MODE if args.analysis_mode == "codex" else TEMPLATE_ANALYSIS_MODE
            )
            status_result = write_monitor_status(
                content_conn,
                args.data_dir,
                target_analysis_mode,
                min_external_references=thresholds["min_external_references"],
                min_external_platforms=thresholds["min_external_platforms"],
                quality_rules_file=args.quality_rules_file,
            )
            content_conn.close()
            if args.json:
                print(json.dumps(status_result, ensure_ascii=False, indent=2))
            else:
                print(f"overall: {status_result['overall_status']}")
                latest = status_result.get("latest_run") or {}
                if latest:
                    print(f"latest_run: {latest.get('run_id')} {latest.get('status')} {latest.get('report_path')}")
                quality = status_result.get("quality_gate") or {}
                print(
                    "quality: "
                    f"refs {quality.get('external_reference_count')}/{quality.get('min_external_references')}, "
                    f"platforms {quality.get('external_platform_count')}/{quality.get('min_external_platforms')}"
                )
                queue = status_result.get("queue") or {}
                print(
                    f"queue: pending {queue.get('pending_count')}, "
                    f"active {queue.get('active_industry_rank')} {queue.get('active_industry_name')}"
                )
                gaps = status_result.get("external_reference_gaps") or {}
                actions = gaps.get("by_action") or {}
                action_text = ", ".join(
                    f"{gap_action_label(str(action))}:{count}"
                    for action, count in sorted(actions.items(), key=lambda item: str(item[0]))
                )
                print(f"reference_gaps: pending {gaps.get('pending_count', 0)} {action_text}")
                print(f"status_path: {status_result.get('status_path')}")
            return 0
        if args.command == "automation-step":
            result = record_automation_step(
                data_dir=args.data_dir,
                run_id=args.run_id,
                step_key=args.step_key,
                step_label=args.step_label,
                status=args.status,
                exit_code=args.exit_code,
                error_summary=args.error_summary,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(
                    f"automation_step: {args.run_id} {args.step_key} {args.status} "
                    f"latest={result.get('latest_path')}"
                )
            return 0
        if args.command == "automation-dashboard":
            output_path = write_automation_dashboard(args.output, data_dir=args.data_dir)
            result = {
                "dashboard_path": output_path,
                "latest_run": load_latest_automation_run(args.data_dir),
            }
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"automation_dashboard: {output_path}")
            return 0
        if args.command == "automation-lock-clean":
            lock_path = Path(args.data_dir) / "pipeline.lock"
            before = inspect_pipeline_lock(lock_path)
            result = cleanup_stale_pipeline_lock(lock_path)
            reconciled_runs: list[dict[str, object]] = []
            if result.get("final_status") == "absent" and args.content_db:
                content_conn = connect_content(args.content_db)
                init_content_database(content_conn)
                try:
                    reconciled_runs = reconcile_orphaned_pipeline_runs(content_conn)
                finally:
                    content_conn.close()
            result = {"before": before, **result, "reconciled_pipeline_runs": reconciled_runs}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(
                    "automation_lock_clean: "
                    f"status={result.get('status')} removed={result.get('removed')} "
                    f"final={result.get('final_status')} reconciled={len(reconciled_runs)}"
                )
            return 0
        if args.command == "automation-readiness":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            report = build_automation_readiness(
                content_conn=content_conn,
                data_dir=args.data_dir,
                analysis_mode=CODEX_ANALYSIS_MODE if args.analysis_mode == "codex" else TEMPLATE_ANALYSIS_MODE,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
                quality_rules_file=args.quality_rules_file,
                schedule_times=args.schedule_time,
                scheduler_file=args.scheduler_file,
                max_running_minutes=args.max_running_minutes,
            )
            output_path = write_automation_readiness_dashboard(
                args.output,
                content_conn=content_conn,
                data_dir=args.data_dir,
                analysis_mode=CODEX_ANALYSIS_MODE if args.analysis_mode == "codex" else TEMPLATE_ANALYSIS_MODE,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
                quality_rules_file=args.quality_rules_file,
                schedule_times=args.schedule_time,
                scheduler_file=args.scheduler_file,
                max_running_minutes=args.max_running_minutes,
            )
            content_conn.close()
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"automation_readiness: {output_path}")
                print(
                    f"status: {report.get('overall_status')} "
                    f"pass: {summary.get('passed_count', 0)} warn: {summary.get('warning_count', 0)} fail: {summary.get('failed_count', 0)}"
                )
            return 0
        if args.command == "automation-scheduler-plan":
            result = write_automation_scheduler_plan(
                args.output_dir,
                workspace=args.workspace,
                data_dir=args.data_dir,
                label=args.label,
                schedule_times=args.schedule_time,
                timezone_name=args.timezone,
                entrypoint=args.entrypoint,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                artifacts = result.get("artifacts") or {}
                print(f"automation_scheduler_plan: {artifacts.get('dashboard')}")
                print(f"status: {result.get('status')} label: {result.get('label')}")
            return 0
        if args.command == "gaps":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            rows = list_external_reference_gaps(
                content_conn,
                status=args.status,
                required_action=args.required_action,
                gap_type=args.gap_type,
                limit=args.limit,
            )
            content_conn.close()
            if args.json:
                print(json.dumps(rows, ensure_ascii=False, indent=2))
            else:
                if not rows:
                    print("no external reference gaps")
                for row in rows:
                    print(_gap_line(row))
            return 0
        if args.command == "gap-review":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            row = update_external_reference_gap_status(
                content_conn,
                args.gap_id,
                args.status,
                reviewer=args.reviewer,
                note=args.note,
            )
            content_conn.close()
            if args.json:
                print(json.dumps(row, ensure_ascii=False, indent=2))
            else:
                print(_gap_line(row))
            return 0
        if args.command == "gap-bulk-review":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            rows = bulk_update_external_reference_gap_status(
                content_conn,
                status=args.status,
                from_status=args.from_status,
                required_action=args.required_action,
                gap_type=args.gap_type,
                platform=args.platform,
                reviewer=args.reviewer,
                note=args.note,
                limit=args.limit,
                dry_run=args.dry_run,
            )
            content_conn.close()
            if args.json:
                print(json.dumps({"count": len(rows), "dry_run": args.dry_run, "items": rows}, ensure_ascii=False, indent=2))
            else:
                prefix = "would update" if args.dry_run else "updated"
                print(f"{prefix}: {len(rows)} gaps")
                for row in rows[:20]:
                    print(_gap_line(row))
            return 0
        if args.command == "gap-dashboard":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            rows = list_external_reference_gaps(
                content_conn,
                status=args.status,
                limit=args.limit,
            )
            content_conn.close()
            output_path = write_gap_dashboard(args.output, rows)
            result = {"dashboard_path": output_path, "gap_count": len(rows), "status": args.status}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"gap_dashboard: {output_path}")
                print(f"gaps: {len(rows)} status={args.status}")
            return 0
        if args.command == "ops-dashboard":
            thresholds = _quality_thresholds(args)
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            target_analysis_mode = (
                CODEX_ANALYSIS_MODE if args.analysis_mode == "codex" else TEMPLATE_ANALYSIS_MODE
            )
            output_path = write_ops_dashboard(
                args.output,
                content_conn,
                data_dir=args.data_dir,
                analysis_mode=target_analysis_mode,
                min_external_references=thresholds["min_external_references"],
                min_external_platforms=thresholds["min_external_platforms"],
                quality_rules_file=args.quality_rules_file,
            )
            summary = ops_dashboard_summary(content_conn, target_analysis_mode)
            content_conn.close()
            result = {"dashboard_path": output_path, **summary}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"ops_dashboard: {output_path}")
                print(
                    f"runs: {summary['run_total']} generated_reports: {summary['generated_reports']} "
                    f"pending_queue: {summary['pending_queue']} pending_gaps: {summary['pending_gaps']}"
                )
            return 0
        if args.command == "platform-coverage":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            coverage = build_platform_coverage(
                content_conn=content_conn,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
                interpretation_source_file=args.interpretation_source_file,
            )
            output_path = write_platform_coverage_dashboard(
                args.output,
                content_conn=content_conn,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
                interpretation_source_file=args.interpretation_source_file,
            )
            content_conn.close()
            result = {"dashboard_path": output_path, **coverage}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = coverage.get("summary") or {}
                print(f"platform_coverage: {output_path}")
                print(
                    f"total: {summary.get('total', 0)} ready: {summary.get('ready', 0)} "
                    f"partial: {summary.get('partial', 0)} blocked: {summary.get('blocked', 0)}"
                )
            return 0
        if args.command == "platform-parsers":
            status_result = build_platform_parser_status(args.parser_file)
            output_path = write_platform_parser_dashboard(
                args.output,
                parser_file=args.parser_file,
            )
            result = {"dashboard_path": output_path, **status_result}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = status_result.get("summary") or {}
                print(f"platform_parsers: {output_path}")
                print(
                    f"parsers: {summary.get('parser_count', 0)} "
                    f"platforms: {summary.get('platform_count', 0)} "
                    f"ready: {summary.get('ready_count', 0)} "
                    f"partial: {summary.get('partial_count', 0)} planned: {summary.get('planned_count', 0)}"
                )
            return 0
        if args.command == "platform-parser-validate":
            validation = build_platform_parser_validation(
                parser_file=args.parser_file,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
            )
            output_path = write_platform_parser_validation_dashboard(
                args.output,
                parser_file=args.parser_file,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
            )
            result = {"dashboard_path": output_path, **validation}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = validation.get("summary") or {}
                print(f"platform_parser_validation: {output_path}")
                print(
                    f"ready: {summary.get('current_ready_count', 0)} "
                    f"partial: {summary.get('current_partial_count', 0)} "
                    f"missing_search_key: {summary.get('missing_search_key_count', 0)} "
                    f"missing_platform_auth: {summary.get('missing_platform_auth_count', 0)}"
                )
            return 0
        if args.command == "platform-parser-samples":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            try:
                sample_report = build_platform_parser_sample_acceptance(
                    content_conn,
                    parser_file=args.parser_file,
                    limit=args.limit,
                )
                output_path = write_platform_parser_sample_dashboard(
                    args.output,
                    content_conn,
                    parser_file=args.parser_file,
                    limit=args.limit,
                )
            finally:
                content_conn.close()
            result = {"dashboard_path": output_path, **sample_report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = sample_report.get("summary") or {}
                print(f"platform_parser_samples: {output_path}")
                print(
                    f"passed: {summary.get('sample_passed_count', 0)} "
                    f"partial: {summary.get('partial_sample_count', 0)} "
                    f"no_samples: {summary.get('no_sample_count', 0)} "
                    f"references: {summary.get('reference_item_count', 0)}"
                )
            return 0
        if args.command == "crawl-policy":
            init_database(conn)
            status_result = build_crawl_policy_status(
                conn,
                policy_file=args.policy_file,
                enabled_only=not args.include_disabled,
                limit=args.limit,
                check_robots=args.check_robots,
                robots_timeout=args.robots_timeout,
                allow_insecure_tls=args.allow_insecure_tls,
            )
            output_path = write_crawl_policy_dashboard(
                args.output,
                conn,
                policy_file=args.policy_file,
                enabled_only=not args.include_disabled,
                limit=args.limit,
                check_robots=args.check_robots,
                robots_timeout=args.robots_timeout,
                allow_insecure_tls=args.allow_insecure_tls,
            )
            result = {"dashboard_path": output_path, **status_result}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = status_result.get("summary") or {}
                print(f"crawl_policy: {output_path}")
                print(
                    f"sources: {summary.get('source_count', 0)} "
                    f"ready: {summary.get('policy_ready', 0)} needs_review: {summary.get('needs_review', 0)}"
                )
            return 0
        if args.command == "attachment-parsers":
            status_result = build_attachment_parser_status(args.parser_file)
            output_path = write_attachment_parser_dashboard(
                args.output,
                parser_file=args.parser_file,
            )
            result = {"dashboard_path": output_path, **status_result}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = status_result.get("summary") or {}
                print(f"attachment_parsers: {output_path}")
                print(
                    f"parsers: {summary.get('parser_count', 0)} "
                    f"ready: {summary.get('ready_count', 0)} "
                    f"partial: {summary.get('partial_count', 0)} planned: {summary.get('planned_count', 0)}"
                )
            return 0
        if args.command == "setup-wizard":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            wizard = build_setup_wizard(
                content_conn=content_conn,
                secure_dir=args.secure_dir,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
                interpretation_source_file=args.interpretation_source_file,
            )
            output_path = write_setup_wizard_dashboard(
                args.output,
                content_conn=content_conn,
                secure_dir=args.secure_dir,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
                interpretation_source_file=args.interpretation_source_file,
            )
            content_conn.close()
            result = {"dashboard_path": output_path, **wizard}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = wizard.get("readiness_summary") or {}
                print(f"setup_wizard: {output_path}")
                print(
                    f"search_ready: {summary.get('search_api_ready', 0)} "
                    f"platform_auth: {summary.get('platform_auth_available', 0)} "
                    f"pending_gaps: {summary.get('pending_gaps', 0)}"
                )
            return 0
        if args.command == "access-readiness":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            try:
                report = build_access_readiness(
                    content_conn=content_conn,
                    search_secrets_file=args.search_secrets_file,
                    platform_auth_file=args.platform_auth_file,
                    parser_file=args.parser_file,
                    interpretation_source_file=args.interpretation_source_file,
                )
                output_path = write_access_readiness_dashboard(
                    args.output,
                    content_conn=content_conn,
                    search_secrets_file=args.search_secrets_file,
                    platform_auth_file=args.platform_auth_file,
                    parser_file=args.parser_file,
                    interpretation_source_file=args.interpretation_source_file,
                )
            finally:
                content_conn.close()
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"access_readiness: {output_path}")
                print(
                    f"status: {report.get('overall_status')} "
                    f"search_ready: {summary.get('search_ready', 0)} "
                    f"platform_available: {summary.get('platform_available', 0)} "
                    f"p0: {summary.get('p0_status')}"
                )
            return 0
        if args.command == "credential-doctor":
            report = build_credential_doctor(
                secure_dir=args.secure_dir,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
            )
            output_path = write_credential_doctor_dashboard(
                args.output,
                secure_dir=args.secure_dir,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
            )
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"credential_doctor: {output_path}")
                print(
                    f"search_ready: {summary.get('search_ready', 0)} "
                    f"platform_available: {summary.get('platform_available', 0)} "
                    f"errors: {summary.get('errors', 0)} warnings: {summary.get('warnings', 0)}"
                )
            return 0
        if args.command == "search-validate":
            report = build_search_validation(
                search_secrets_file=args.search_secrets_file,
                query=args.query,
                timeout=args.timeout,
                retries=args.retries,
                allow_insecure_tls=args.allow_insecure_tls,
                online=not args.offline,
            )
            output_path = write_search_validation_dashboard(
                args.output,
                search_secrets_file=args.search_secrets_file,
                query=args.query,
                timeout=args.timeout,
                retries=args.retries,
                allow_insecure_tls=args.allow_insecure_tls,
                online=not args.offline,
            )
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"search_validation: {output_path}")
                print(
                    f"configured: {summary.get('configured_count', 0)} "
                    f"checked: {summary.get('online_checked_count', 0)} "
                    f"passed: {summary.get('passed_count', 0)} failed: {summary.get('failed_count', 0)}"
                )
            return 0
        if args.command == "search-secret-import":
            result = import_search_secret(
                args.provider,
                value_file=args.value_file,
                value_env=args.value_env,
                engine_id_file=args.engine_id_file,
                engine_id_env=args.engine_id_env,
                secure_dir=args.secure_dir,
                search_secrets_file=args.search_secrets_file,
                force=args.force,
                dry_run=args.dry_run,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"search_secret_import: {result.get('provider')} {result.get('status')}")
                print(f"target: {result.get('search_secrets_file')}")
                print(f"ready: {result.get('provider_ready_after_import')}")
                for command in result.get("next_commands") or []:
                    print(command)
            return 0
        if args.command == "search-secret-bulk-import":
            result = import_search_secret_bundle(
                args.source_file,
                secure_dir=args.secure_dir,
                search_secrets_file=args.search_secrets_file,
                force=args.force,
                dry_run=args.dry_run,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(
                    f"search_secret_bulk_import: {result.get('status')} "
                    f"imported={result.get('imported_count')} skipped={result.get('skipped_count')} invalid={result.get('invalid_count')}"
                )
                print(
                    f"ready: {result.get('ready_count_after_import')}/{result.get('total_provider_count')}"
                )
                for item in result.get("results") or []:
                    print(f"{item.get('provider')}: {item.get('status')}")
                for command in result.get("next_commands") or []:
                    print(command)
            return 0
        if args.command == "search-secret-intake":
            report = build_search_secret_intake(
                secure_dir=args.secure_dir,
                search_secrets_file=args.search_secrets_file,
            )
            output_path = write_search_secret_intake_dashboard(
                args.output,
                secure_dir=args.secure_dir,
                search_secrets_file=args.search_secrets_file,
            )
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"search_secret_intake: {output_path}")
                print(
                    f"ready: {summary.get('ready_count', 0)}/{summary.get('total', 0)} "
                    f"p0_minimum_ready: {summary.get('p0_minimum_ready')}"
                )
            return 0
        if args.command == "platform-auth-validate":
            report = build_platform_auth_validation(
                platform_auth_file=args.platform_auth_file,
                platforms=args.platform,
                online=args.online,
                timeout=args.timeout,
                retries=args.retries,
                allow_insecure_tls=args.allow_insecure_tls,
            )
            output_path = write_platform_auth_validation_dashboard(
                args.output,
                platform_auth_file=args.platform_auth_file,
                platforms=args.platform,
                online=args.online,
                timeout=args.timeout,
                retries=args.retries,
                allow_insecure_tls=args.allow_insecure_tls,
            )
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"platform_auth_validation: {output_path}")
                print(
                    f"configured: {summary.get('configured_count', 0)} "
                    f"available: {summary.get('available_count', 0)} "
                    f"checked: {summary.get('online_checked_count', 0)} "
                    f"passed: {summary.get('passed_count', 0)}"
                )
            return 0
        if args.command == "platform-auth-intake":
            report = build_platform_auth_intake(
                secure_dir=args.secure_dir,
                platform_auth_file=args.platform_auth_file,
            )
            output_path = write_platform_auth_intake_dashboard(
                args.output,
                secure_dir=args.secure_dir,
                platform_auth_file=args.platform_auth_file,
            )
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"platform_auth_intake: {output_path}")
                print(
                    f"p0_ready: {summary.get('p0_ready', 0)}/{summary.get('p0_total', 0)} "
                    f"available: {summary.get('available_count', 0)} missing: {summary.get('missing_file_count', 0)}"
                )
            return 0
        if args.command == "platform-auth-import":
            result = import_platform_auth_cookie(
                args.platform,
                source_file=args.source_file,
                cookie_env=args.cookie_env,
                secure_dir=args.secure_dir,
                platform_auth_file=args.platform_auth_file,
                target_file=args.target_file,
                force=args.force,
                dry_run=args.dry_run,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"platform_auth_import: {result.get('platform')} {result.get('status')}")
                print(f"target: {result.get('target_file')}")
                print(f"marker: {result.get('marker_status')}")
                for command in result.get("next_commands") or []:
                    print(command)
            return 0
        if args.command == "platform-auth-session-import":
            result = import_platform_auth_session_reference(
                args.platform,
                session_file=args.session_file,
                secure_dir=args.secure_dir,
                platform_auth_file=args.platform_auth_file,
                auth_method=args.auth_method,
                dry_run=args.dry_run,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"platform_auth_session_import: {result.get('platform')} {result.get('status')}")
                print(f"session_reference: {result.get('session_reference')}")
                print(f"collector_ready: {result.get('collector_ready')}")
                for command in result.get("next_commands") or []:
                    print(command)
            return 0
        if args.command == "platform-auth-bulk-import":
            result = import_platform_auth_cookie_directory(
                args.source_dir,
                platforms=args.platform,
                secure_dir=args.secure_dir,
                platform_auth_file=args.platform_auth_file,
                force=args.force,
                dry_run=args.dry_run,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(
                    f"platform_auth_bulk_import: {result.get('status')} "
                    f"imported={result.get('imported_count')} missing={result.get('missing_count')}"
                )
                if result.get("missing_platforms"):
                    print("missing: " + ", ".join(result.get("missing_platforms") or []))
                for item in result.get("results") or []:
                    print(f"{item.get('platform')}: {item.get('status')} marker={item.get('marker_status')}")
                for command in result.get("next_commands") or []:
                    print(command)
            return 0
        if args.command == "platform-auth-bundle-import":
            result = import_platform_auth_cookie_bundle(
                args.source_file,
                platforms=args.platform,
                secure_dir=args.secure_dir,
                platform_auth_file=args.platform_auth_file,
                force=args.force,
                dry_run=args.dry_run,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(
                    f"platform_auth_bundle_import: {result.get('status')} "
                    f"imported={result.get('imported_count')} missing={result.get('missing_count')}"
                )
                if result.get("missing_platforms"):
                    print("missing: " + ", ".join(result.get("missing_platforms") or []))
                for item in result.get("results") or []:
                    print(f"{item.get('platform')}: {item.get('status')} marker={item.get('marker_status')}")
                for command in result.get("next_commands") or []:
                    print(command)
            return 0
        if args.command == "chrome-bilibili-discovery":
            report = build_chrome_bilibili_discovery(
                chrome_profile_dir=args.chrome_profile_dir,
                history_file=args.history_file,
                cookies_file=args.cookies_file,
                limit=args.limit,
                keyword=args.keyword,
            )
            output_path = write_chrome_bilibili_discovery_dashboard(
                args.output,
                chrome_profile_dir=args.chrome_profile_dir,
                history_file=args.history_file,
                cookies_file=args.cookies_file,
                limit=args.limit,
                keyword=args.keyword,
            )
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"chrome_bilibili_discovery: {output_path}")
                print(
                    f"history: {summary.get('bilibili_history_count', 0)} "
                    f"candidates: {summary.get('candidate_count', 0)} "
                    f"cookie_rows: {summary.get('bilibili_cookie_row_count', 0)}"
                )
            return 0
        if args.command == "benchmark-dashboard":
            status_result = build_benchmark_status(args.benchmark_file)
            output_path = write_benchmark_dashboard(
                args.output,
                benchmark_file=args.benchmark_file,
            )
            result = {"dashboard_path": output_path, **status_result}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = status_result.get("summary") or {}
                print(f"benchmark_dashboard: {output_path}")
                print(
                    f"models: {summary.get('model_count', 0)} "
                    f"capabilities: {summary.get('capability_count', 0)} "
                    f"partial: {summary.get('partial_count', 0)} planned: {summary.get('planned_count', 0)}"
                )
            return 0
        if args.command == "quality-gates":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            target_analysis_mode = (
                CODEX_ANALYSIS_MODE if args.analysis_mode == "codex" else TEMPLATE_ANALYSIS_MODE
            )
            thresholds = _quality_thresholds(args)
            status_result = write_monitor_status(
                content_conn,
                args.data_dir,
                target_analysis_mode,
                min_external_references=thresholds["min_external_references"],
                min_external_platforms=thresholds["min_external_platforms"],
                quality_rules_file=args.quality_rules_file,
            )
            report = build_quality_gate_status(
                rule_file=args.quality_rules_file,
                monitor_status=status_result,
            )
            output_path = write_quality_gates_dashboard(
                args.output,
                rule_file=args.quality_rules_file,
                monitor_status=status_result,
            )
            content_conn.close()
            result = {"dashboard_path": output_path, **report}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = report.get("summary") or {}
                print(f"quality_gates: {output_path}")
                print(
                    f"passed: {summary.get('passed_count', 0)} "
                    f"failed: {summary.get('failed_count', 0)} "
                    f"not_checked: {summary.get('not_checked_count', 0)}"
                )
            return 0
        if args.command == "report-check":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            report_path = args.report_path or _latest_report_path(content_conn)
            check = inspect_report_artifacts(report_path)
            output_path = write_report_artifact_dashboard(args.output, report_path=report_path)
            content_conn.close()
            result = {**check, "dashboard_path": output_path}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                summary = check.get("summary") or {}
                print(f"report_check: {output_path}")
                print(
                    f"passed: {summary.get('passed_count', 0)} "
                    f"failed: {summary.get('failed_count', 0)} "
                    f"warning: {summary.get('warning_count', 0)}"
                )
            return 0
        if args.command == "readiness":
            content_conn = connect_content(args.content_db)
            init_content_database(content_conn)
            status_result = build_readiness_status(
                content_conn=content_conn,
                search_secrets_file=args.search_secrets_file,
                platform_auth_file=args.platform_auth_file,
                interpretation_source_file=args.interpretation_source_file,
            )
            content_conn.close()
            if args.json:
                print(json.dumps(status_result, ensure_ascii=False, indent=2))
            else:
                _print_readiness(status_result)
            return 0
        if args.command == "setup-config":
            setup = write_config_setup(
                secure_dir=args.secure_dir,
                search_secrets_path=args.search_secrets_path,
                platform_auth_path=args.platform_auth_path,
                force=args.force,
                dry_run=args.dry_run,
            )
            if args.json:
                print(json.dumps(_public_setup_config(setup), ensure_ascii=False, indent=2))
            else:
                _print_setup_config(setup)
            return 0
        if args.command == "ai-research-priority":
            result = write_ai_research_priority_file(args.request_file, args.base_file, args.output)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"wrote {result['output']} focused={result['focused_count']}")
            return 0
        if args.command == "run":
            thresholds = _quality_thresholds(args)
            result = run_pipeline(
                PipelineConfig(
                    source_db_path=db_path,
                    content_db_path=Path(args.content_db),
                    data_dir=Path(args.data_dir),
                    report_dir=Path(args.report_dir),
                    max_sources=args.max_sources,
                    max_pages_per_source=args.max_pages_per_source,
                    max_links_per_page=args.max_links_per_page,
                    max_analyze=args.max_analyze,
                    max_interpretation_documents=args.max_interpretation_documents,
                    min_external_references_per_report=thresholds["min_external_references"],
                    min_external_platforms_per_report=thresholds["min_external_platforms"],
                    fetch_interpretation_results=args.fetch_interpretation_results,
                    bilibili_cookie_file=Path(args.bilibili_cookie_file)
                    if args.bilibili_cookie_file
                    else None,
                    search_secrets_file=Path(args.search_secrets_file)
                    if args.search_secrets_file
                    else None,
                    platform_auth_file=Path(args.platform_auth_file)
                    if args.platform_auth_file
                    else None,
                    fetch_search_result_pages=args.fetch_search_result_pages,
                    interpretation_request_timeout=args.interpretation_request_timeout,
                    interpretation_request_retries=args.interpretation_request_retries,
                    interpretation_request_delay_seconds=args.interpretation_request_delay_seconds,
                    min_authority_score=args.min_authority_score,
                    analysis_mode=args.analysis_mode,
                    mode=args.mode,
                    allow_insecure_tls=args.allow_insecure_tls,
                    interpretation_source_file=Path(args.interpretation_source_file),
                    industry_priority_file=Path(args.industry_priority_file),
                    document_since=args.document_since,
                    quality_rules_file=Path(args.quality_rules_file),
                )
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"{result['status']} {result['run_id']}")
                print(f"report: {result['report_path']}")
                print(f"stats: {result['stats']}")
            return 0
    except (KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        conn.close()

    return 1


def _quality_thresholds(args) -> dict[str, int]:
    thresholds = quality_rule_thresholds(getattr(args, "quality_rules_file", None))
    min_refs = getattr(args, "min_external_references", None)
    min_platforms = getattr(args, "min_external_platforms", None)
    if min_refs is None:
        min_refs = thresholds.get("external_reference_count", 5)
    if min_platforms is None:
        min_platforms = thresholds.get("external_platform_count", 2)
    return {
        "min_external_references": int(min_refs or 0),
        "min_external_platforms": int(min_platforms or 0),
    }


def _latest_report_path(content_conn) -> str:
    row = content_conn.execute(
        """
        SELECT report_path
        FROM pipeline_runs
        WHERE report_path IS NOT NULL AND report_path != ''
        ORDER BY started_at DESC, run_id DESC
        LIMIT 1
        """
    ).fetchone()
    return str(row["report_path"] if row else "")


def _gap_line(row: dict) -> str:
    title = str(row.get("title") or row.get("document_title") or "未命名缺口")
    if len(title) > 72:
        title = title[:69] + "..."
    return (
        f"{row.get('gap_id')} | {row.get('status')} | "
        f"{row.get('priority_score')} | {row.get('platform')} | "
        f"{gap_type_label(str(row.get('gap_type') or ''))} | "
        f"{gap_action_label(str(row.get('required_action') or ''))} | "
        f"{title}"
    )


def _print_readiness(status: dict) -> None:
    print(f"overall: {status.get('overall_status')}")
    search = status.get("search_api") or {}
    print(f"search_api: ready {search.get('ready_count', 0)}/{len(search.get('providers') or [])}")
    for provider in search.get("providers") or []:
        required = ",".join(provider.get("required") or [])
        print(
            f"  {provider.get('provider')}: {provider.get('status')} "
            f"key={provider.get('key_present')} engine={provider.get('engine_present')} required={required}"
        )
    chinese = status.get("chinese_search_entries") or {}
    print(f"chinese_search_entries: configured {chinese.get('configured_count', 0)}/3 {chinese.get('entries')}")
    auth = status.get("platform_auth") or {}
    print(
        f"platform_auth: configured {auth.get('configured_count', 0)}, "
        f"available {auth.get('available_count', 0)}/{len(auth.get('platforms') or [])}"
    )
    for platform in auth.get("platforms") or []:
        print(
            f"  {platform.get('platform')}: {platform.get('status')} "
            f"configured={platform.get('configured')} available={platform.get('available')}"
        )
    gaps = status.get("external_reference_gaps") or {}
    print(f"reference_gaps: pending {gaps.get('pending_count', 0)} by_action={gaps.get('by_action') or {}}")
    actions = status.get("next_actions") or []
    if actions:
        print("next_actions:")
        for action in actions:
            targets = ",".join(str(item) for item in action.get("targets") or [])
            count = f" count={action.get('count')}" if action.get("count") is not None else ""
            print(f"  {action.get('label') or action.get('action')}: {targets}{count}")


def _public_setup_config(setup: dict) -> dict:
    return {
        "secure_dir": setup.get("secure_dir"),
        "search_secrets_path": setup.get("search_secrets_path"),
        "platform_auth_path": setup.get("platform_auth_path"),
        "cookie_dir": setup.get("cookie_dir"),
        "search_api_bundle_example_path": setup.get("search_api_bundle_example_path"),
        "platform_auth_bundle_example_path": setup.get("platform_auth_bundle_example_path"),
        "env_exports": setup.get("env_exports"),
        "shell_exports": setup.get("shell_exports"),
        "writes": setup.get("writes"),
        "dry_run": setup.get("dry_run"),
        "force": setup.get("force"),
        "security_note": setup.get("security_note"),
        "next_steps": setup.get("next_steps"),
    }


def _print_setup_config(setup: dict) -> None:
    print(f"secure_dir: {setup.get('secure_dir')}")
    print(f"search_api_bundle_example: {setup.get('search_api_bundle_example_path')}")
    print(f"platform_auth_bundle_example: {setup.get('platform_auth_bundle_example_path')}")
    for item in setup.get("writes") or []:
        print(f"{item.get('action')}: {item.get('path')}")
    print("exports:")
    for line in setup.get("shell_exports") or []:
        print(f"  {line}")
    print(f"security: {setup.get('security_note')}")
    print("next_steps:")
    for step in setup.get("next_steps") or []:
        print(f"  - {step}")
