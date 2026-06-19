import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple
from uuid import uuid4

from tab_research.automation_config import load_automation_authorization
from tab_research.artifacts import public_artifact_name, sanitize_public_manifest
from tab_research.automation_candidate import (
    AUTOMATION_CANDIDATE_LATEST,
    AUTOMATION_CANDIDATE_PDF_LATEST,
    AUTOMATION_CANDIDATE_REPORT_LATEST,
    write_automation_candidate,
    write_automation_candidate_pdf,
    write_automation_candidate_report,
)
from tab_research.automation_readiness import (
    AUTOMATION_READINESS_LATEST,
    AUTOMATION_READINESS_PDF_LATEST,
    AUTOMATION_READINESS_REPORT_LATEST,
    write_automation_readiness_pdf,
    write_automation_readiness_report,
    write_automation_readiness_summary,
)
from tab_research.available_board_strategy import write_available_board_strategy_bundle
from tab_research.boards import BOARD_CONFIGS, audit_portfolio, render_portfolio_markdown
from tab_research.compare import compact_portfolio_baseline, compare_portfolio_recommendations, load_baseline
from tab_research.daily_boards import (
    BoardRunContext,
    board_input_paths,
    daily_board_registry,
    pre_pdf_gate_map,
    response_metrics,
    run_daily_boards,
    current_matches_board,
)
from tab_research.io import atomic_copy, atomic_write_json, atomic_write_text, single_instance_lock
from tab_research.live_board_discovery import LIVE_BOARD_DISCOVERY_RAW_LATEST, write_live_board_discovery_bundle
from tab_research.model_compare import MODEL_COMPARISON_JSON, MODEL_COMPARISON_MD, MODEL_COMPARISON_PDF, write_model_comparison
from tab_research.model_divergence_review import write_model_divergence_review_bundle
from tab_research.pdf_qa import audit_pdf_report
from tab_research.partial_daily_research import write_partial_daily_research_bundle
from tab_research.pipeline import CORE_MAIN_MARKETS, EXPECTED_MATCHES, has_full_core_markets, match_is_in_play
from tab_research.preflight import audit_automation_preflight
from tab_research.event_monitor import audit_event_feeds
from tab_research.public_sources import audit_sources
from tab_research.raw_refresh import audit_raw_refresh, audit_staged_raw_refresh, raw_refresh_health, write_raw_refresh_batch_manifest
from tab_research.raw_refresh_recovery import write_raw_refresh_recovery_bundle
from tab_research.recommendation_operations import write_recommendation_operations_bundle
from tab_research.recommendations import apply_execution_stakes_to_board_results, enrich_match_recommendations_with_model_comparison
from tab_research.dashboard import publish_dashboard_latest, write_dashboard
from tab_research.report_store import (
    REPORT_INDEX_PDF_LATEST,
    REPORT_INDEX_REPORT_LATEST,
    store_daily_run,
    update_run_dashboard_paths,
    write_report_index,
    write_report_index_pdf,
    write_report_index_report,
)
from tab_research.report_intelligence import (
    REPORT_INTELLIGENCE_JSON_LATEST,
    REPORT_INTELLIGENCE_MD_LATEST,
    REPORT_INTELLIGENCE_PDF_LATEST,
    report_intelligence_run_json,
    report_intelligence_run_md,
    report_intelligence_run_pdf,
    write_report_intelligence_bundle,
)
from tab_research.safety import audit_output_safety, audit_public_artifact_safety, audit_safety, ensure_private_tree_permissions
from tab_research.paths import resolve_output_dir, resolve_private_dir, resolve_workspace_root
from tab_research.source_model_metadata import write_source_model_github_metadata
from tab_research.source_model_registry import write_source_model_registry_bundle
from generate_business_pdf_report import BANKROLL_PLAN_PATH, OUTPUT_COPY_PATH, PDF_PATH, REPORT_DATE, REPORT_TZ, render_pdf


ROOT = resolve_workspace_root(Path(__file__))
OUT = resolve_output_dir(Path(__file__))
PRIVATE_DATA_DIR = resolve_private_dir(Path(__file__))
MATCHES_BOARD = current_matches_board()
RAW = OUT / MATCHES_BOARD.raw_snapshot
VERSION = MATCHES_BOARD.version
PUBLIC_AUDIT = OUT / f"public_source_audit_{VERSION}.json"
EVENT_AUDIT = OUT / f"event_monitor_{VERSION}.json"
PREVIOUS_BASELINE_FALLBACK = OUT / "previous_report_baseline_v0_10.json"
PREVIOUS_BASELINE_LATEST = OUT / "previous_report_baseline_latest.json"
CURRENT_BASELINE = OUT / f"previous_report_baseline_{VERSION}.json"
PORTFOLIO_BASELINE_LATEST = OUT / "portfolio_report_baseline_latest.json"
PORTFOLIO_BASELINE_CURRENT = OUT / f"portfolio_report_baseline_{VERSION}.json"
PORTFOLIO_COMPARE_LATEST = OUT / "portfolio_daily_compare_latest.json"
PORTFOLIO_COMPARE_CURRENT = OUT / f"portfolio_daily_compare_{VERSION}.json"
LOCK_PATH = OUT / ".tab_fifa_daily_report.lock"
LATEST_MANIFEST = OUT / "daily_report_manifest_latest.json"
LATEST_COMMIT = OUT / "latest_commit.json"
PREFLIGHT_PATH = OUT / "automation_preflight_latest.json"
RAW_REFRESH_PATH = OUT / "raw_refresh_manifest_latest.json"
RAW_REFRESH_BATCH_PATH = OUT / "raw_refresh_batch_latest.json"
RAW_REFRESH_HEALTH_PATH = OUT / "raw_refresh_health_latest.json"
RAW_REFRESH_DIAGNOSTICS_PATH = OUT / "raw_refresh_diagnostics_latest.json"
RAW_REFRESH_RESEARCH_ONLY_LATEST = "raw_refresh_research_only_latest.json"
RAW_REFRESH_RESEARCH_ONLY_DIR = "research_only_raw"
PDF_QA_LATEST = OUT / "pdf_qa_latest.json"
DEFAULT_REFRESH_PROCESS_TIMEOUT_SECONDS = 180
MATCHES_REFRESH_PROCESS_TIMEOUT_SECONDS = 180
DEFAULT_MATCHES_REFRESH_CHUNK_SIZE = 5
DEFAULT_MATCHES_MERGED_REPAIR_LIMIT = 4
REPORT_DB = OUT / "tab_fifa_reports.sqlite3"
REPORT_INDEX_LATEST = OUT / "report_index_latest.json"
REPORT_INDEX_REPORT_LATEST_PATH = OUT / REPORT_INDEX_REPORT_LATEST
REPORT_INDEX_PDF_LATEST_PATH = OUT / REPORT_INDEX_PDF_LATEST
REPORT_INTELLIGENCE_LATEST_PATH = OUT / REPORT_INTELLIGENCE_JSON_LATEST
REPORT_INTELLIGENCE_MD_LATEST_PATH = OUT / REPORT_INTELLIGENCE_MD_LATEST
REPORT_INTELLIGENCE_PDF_LATEST_PATH = OUT / REPORT_INTELLIGENCE_PDF_LATEST
AUTOMATION_READINESS_PATH = OUT / AUTOMATION_READINESS_LATEST
AUTOMATION_READINESS_REPORT_PATH = OUT / AUTOMATION_READINESS_REPORT_LATEST
AUTOMATION_READINESS_PDF_PATH = OUT / AUTOMATION_READINESS_PDF_LATEST
AUTOMATION_CANDIDATE_PATH = OUT / AUTOMATION_CANDIDATE_LATEST
AUTOMATION_CANDIDATE_REPORT_PATH = OUT / AUTOMATION_CANDIDATE_REPORT_LATEST
AUTOMATION_CANDIDATE_PDF_PATH = OUT / AUTOMATION_CANDIDATE_PDF_LATEST
PRIVATE_OUTPUT_MODE = True
AUTOMATION_AUTHORIZATION = load_automation_authorization()
USER_AUTOMATION_AUTHORIZED = AUTOMATION_AUTHORIZATION.entry_authorized
RAW_REFRESH_MODE = os.getenv("TAB_FIFA_REFRESH_RAW", "1")
RAW_REFRESH_ENABLED = RAW_REFRESH_MODE != "0"
NO_LATEST_PUBLISH = str(os.getenv("TAB_FIFA_NO_LATEST_PUBLISH", "0")).lower() in {"1", "true", "yes", "y", "on"}
BACKFILL_RECONSTRUCTION = str(os.getenv("TAB_FIFA_BACKFILL_RECONSTRUCTION", "0")).lower() in {"1", "true", "yes", "y", "on"}
DEFAULT_NODE_BIN = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
NODE_BIN = Path(os.getenv("TAB_FIFA_NODE_BIN") or str(DEFAULT_NODE_BIN if DEFAULT_NODE_BIN.exists() else (shutil.which("node") or DEFAULT_NODE_BIN))).expanduser()
RAW_REFRESH_SCRIPT = Path(__file__).resolve().parent / "scripts" / "refresh_tab_readonly.mjs"
LIVE_BOARD_DISCOVERY_SCRIPT = Path(__file__).resolve().parent / "scripts" / "discover_tab_live_boards.mjs"
RAW_REFRESH_BOARDS = [
    (board.refresh_board_id, OUT / board.raw_snapshot)
    for board in BOARD_CONFIGS
    if board.required_for_full_automation and board.raw_snapshot and board.refresh_board_id
]


class GateFailure(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_manifest() -> Tuple[Dict, Path]:
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    manifest_path = OUT / f"daily_report_manifest_{run_id}.json"
    previous_baseline = select_previous_baseline_path(OUT)
    manifest = {
        "run_id": run_id,
        "started_at": utc_now(),
        "finished_at": None,
        "status": "running",
        "user_automation_authorized": USER_AUTOMATION_AUTHORIZED,
        "automation_authorization": AUTOMATION_AUTHORIZATION.to_public_dict(),
        "private_output_mode": PRIVATE_OUTPUT_MODE,
        "raw_refresh_enabled": RAW_REFRESH_ENABLED,
        "raw_refresh_mode": RAW_REFRESH_MODE,
        "report_date": REPORT_DATE,
        "report_timezone": str(REPORT_TZ),
        "inputs": {
            **board_input_paths(OUT),
            "previous_baseline": str(previous_baseline),
            "previous_baseline_latest": str(PREVIOUS_BASELINE_LATEST),
            "previous_portfolio_baseline": str(select_previous_portfolio_baseline_path(OUT) or ""),
            "previous_portfolio_baseline_latest": str(PORTFOLIO_BASELINE_LATEST),
                "raw_refresh_script": str(RAW_REFRESH_SCRIPT),
                "raw_refresh_batch_manifest": str(RAW_REFRESH_BATCH_PATH),
                "report_date": REPORT_DATE,
            "report_timezone": str(REPORT_TZ),
        },
        "steps": [],
        "outputs": {},
    }
    write_manifest(manifest, manifest_path)
    return manifest, manifest_path


def write_manifest(manifest: Dict, manifest_path: Path, publish_latest: bool = False) -> None:
    public_manifest = sanitize_public_manifest(manifest)
    atomic_write_json(manifest_path, public_manifest)
    if publish_latest:
        atomic_write_json(LATEST_MANIFEST, public_manifest)


def emit_public_response(response: Dict) -> None:
    payload = json.dumps(sanitize_public_manifest(response), indent=2)
    print(payload)


def record_step(manifest: Dict, manifest_path: Path, name: str, details: Dict | None = None, status: str = "ok") -> None:
    manifest["steps"].append(
        {
            "name": name,
            "status": status,
            "completed_at": utc_now(),
            "details": details or {},
        }
    )
    write_manifest(manifest, manifest_path)


def select_previous_baseline_path(output_dir: Path = OUT) -> Path:
    committed = committed_artifact_path(output_dir, "current_baseline")
    if committed:
        return committed
    latest = output_dir / "previous_report_baseline_latest.json"
    fallback = output_dir / "previous_report_baseline_v0_10.json"
    return latest if latest.exists() else fallback


def select_previous_portfolio_baseline_path(output_dir: Path = OUT) -> Path | None:
    committed = committed_artifact_path(output_dir, "portfolio_baseline")
    if committed:
        return committed
    latest = output_dir / "portfolio_report_baseline_latest.json"
    return latest if latest.exists() else None


def committed_artifact_path(output_dir: Path, artifact_key: str) -> Path | None:
    payload = read_latest_commit(output_dir)
    if not payload:
        return None
    if payload.get("status") != "ready_for_manual_report":
        return None
    if not payload.get("public_artifact_safety_ready"):
        return None
    artifact_name = (payload.get("artifacts") or {}).get(artifact_key)
    if not artifact_name or "/" in str(artifact_name):
        return None
    path = Path(output_dir) / str(artifact_name)
    return path if path.exists() else None


def read_latest_commit(output_dir: Path = OUT) -> Dict:
    path = Path(output_dir) / "latest_commit.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def publish_latest_baseline(output_dir: Path = OUT, version: str = VERSION) -> Path:
    current = output_dir / f"previous_report_baseline_{version}.json"
    latest = output_dir / "previous_report_baseline_latest.json"
    if not current.exists():
        raise RuntimeError(f"current baseline missing; refusing to update latest baseline: {current}")
    atomic_copy(current, latest)
    return latest


def publish_latest_portfolio_baseline(output_dir: Path = OUT, version: str = VERSION) -> Path:
    current = output_dir / f"portfolio_report_baseline_{version}.json"
    latest = output_dir / "portfolio_report_baseline_latest.json"
    if not current.exists():
        raise RuntimeError(f"current portfolio baseline missing; refusing to update latest portfolio baseline: {current}")
    atomic_copy(current, latest)
    return latest


def publish_convenience_latest_artifacts(
    pdf_run_copy: Path,
    bankroll_run_copy: Path,
    dashboard_run_copy: Path,
    dashboard_data_run_copy: Path,
    output_pdf: Path = OUTPUT_COPY_PATH,
    output_bankroll: Path = BANKROLL_PLAN_PATH,
    downloads_pdf: Path | None = None,
    version: str = VERSION,
    output_dir: Path = OUT,
) -> Dict:
    result = {"ready": True, "artifacts": {}, "errors": []}

    def attempt(name: str, operation, artifact_path: Path | None = None) -> object | None:
        try:
            value = operation()
            if artifact_path is not None:
                result["artifacts"][name] = str(artifact_path)
            return value
        except Exception as exc:
            result["ready"] = False
            result["errors"].append({"artifact": name, "error": str(exc)})
            return None

    attempt("pdf_latest_copy", lambda: atomic_copy(pdf_run_copy, output_pdf), output_pdf)
    if downloads_pdf is not None:
        attempt("downloads_pdf_copy", lambda: atomic_copy(pdf_run_copy, downloads_pdf), downloads_pdf)
    attempt("bankroll_plan_latest", lambda: atomic_copy(bankroll_run_copy, output_bankroll), output_bankroll)
    dashboard_result = attempt("dashboard_latest", lambda: publish_dashboard_latest(output_dir, dashboard_run_copy, dashboard_data_run_copy))
    if isinstance(dashboard_result, dict):
        result["artifacts"]["dashboard_latest"] = dashboard_result.get("dashboard", "")
        result["artifacts"]["dashboard_data_latest"] = dashboard_result.get("dashboard_data", "")
    attempt("latest_baseline", lambda: publish_latest_baseline(output_dir, version), output_dir / "previous_report_baseline_latest.json")
    attempt("portfolio_baseline_latest", lambda: publish_latest_portfolio_baseline(output_dir, version), output_dir / "portfolio_report_baseline_latest.json")
    attempt(
        "portfolio_daily_compare_latest",
        lambda: atomic_copy(output_dir / f"portfolio_daily_compare_{version}.json", output_dir / "portfolio_daily_compare_latest.json"),
        output_dir / "portfolio_daily_compare_latest.json",
    )
    return result


def latest_commit_payload(manifest: Dict, response: Dict, latest_artifacts: Dict[str, Path]) -> Dict:
    public_safety = response.get("public_artifact_safety", {})
    return {
        "schema_version": 1,
        "committed_at": utc_now(),
        "run_id": manifest["run_id"],
        "report_date": manifest.get("report_date"),
        "status": manifest.get("status"),
        "technical_automation_ready": bool(manifest.get("technical_automation_ready")),
        "automation_entry_ready": bool(manifest.get("automation_entry_ready")),
        "user_automation_authorized": bool(manifest.get("user_automation_authorized")),
        "automation_authorization": manifest.get("automation_authorization", {}),
        "public_artifact_safety_ready": bool(public_safety.get("public_artifact_safety_ready")),
        "ready_required_boards": response.get("ready_required_boards"),
        "time_adjusted_new_exposure_aud": response.get("time_adjusted_new_exposure_aud"),
        "artifacts": {key: public_artifact_name(path) for key, path in latest_artifacts.items()},
        "run_artifacts": {
            "pdf_run_copy": public_artifact_name(response.get("pdf_run_copy")),
            "bankroll_plan_run_copy": public_artifact_name(response.get("bankroll_plan_run_copy")),
            "dashboard_run_copy": public_artifact_name(response.get("dashboard_run_copy")),
            "dashboard_data_run_copy": public_artifact_name(response.get("dashboard_data_run_copy")),
            "manifest": public_artifact_name(response.get("manifest")),
        },
    }


def publish_latest_commit(manifest: Dict, response: Dict, latest_artifacts: Dict[str, Path], path: Path = LATEST_COMMIT) -> Path:
    atomic_write_json(path, latest_commit_payload(manifest, response, latest_artifacts))
    return path


def preflight_run_path(run_id: str) -> Path:
    return OUT / f"automation_preflight_{run_id}.json"


def pdf_qa_run_path(run_id: str) -> Path:
    return OUT / f"pdf_qa_{run_id}.json"


def report_index_run_path(run_id: str) -> Path:
    return OUT / f"report_index_{run_id}.json"


def report_index_report_run_path(run_id: str) -> Path:
    return OUT / f"report_index_{run_id}.md"


def report_index_pdf_run_path(run_id: str) -> Path:
    return OUT / f"report_index_{run_id}.pdf"


def report_intelligence_run_path(run_id: str) -> Path:
    return OUT / report_intelligence_run_json(run_id)


def report_intelligence_md_run_path(run_id: str) -> Path:
    return OUT / report_intelligence_run_md(run_id)


def report_intelligence_pdf_run_path(run_id: str) -> Path:
    return OUT / report_intelligence_run_pdf(run_id)


def refresh_process_timeout_seconds(board_id: str | None = None) -> int:
    default = MATCHES_REFRESH_PROCESS_TIMEOUT_SECONDS if board_id == "matches" else DEFAULT_REFRESH_PROCESS_TIMEOUT_SECONDS
    raw = os.getenv("TAB_FIFA_REFRESH_PROCESS_TIMEOUT_SECONDS", str(default))
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(30, min(value, 900))


def source_model_metadata_timeout_seconds() -> int:
    raw = os.getenv("TAB_FIFA_SOURCE_METADATA_TIMEOUT_SECONDS", "8")
    try:
        value = int(raw)
    except ValueError:
        return 8
    return max(3, min(value, 30))


def matches_refresh_chunk_size() -> int:
    raw = os.getenv("TAB_FIFA_MATCHES_REFRESH_CHUNK_SIZE", str(DEFAULT_MATCHES_REFRESH_CHUNK_SIZE))
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MATCHES_REFRESH_CHUNK_SIZE
    return max(1, min(value, len(EXPECTED_MATCHES)))


def matches_merged_repair_limit() -> int:
    raw = os.getenv("TAB_FIFA_MATCHES_MERGED_REPAIR_LIMIT", str(DEFAULT_MATCHES_MERGED_REPAIR_LIMIT))
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MATCHES_MERGED_REPAIR_LIMIT
    return max(0, min(value, len(EXPECTED_MATCHES)))


def main() -> None:
    with single_instance_lock(LOCK_PATH):
        ensure_private_tree_permissions(PRIVATE_DATA_DIR)
        manifest, manifest_path = start_manifest()
        raw_refresh_succeeded = not RAW_REFRESH_ENABLED
        raw_refresh_diagnostics_path = run_raw_refresh_diagnostics_path(manifest["run_id"])
        try:
            if RAW_REFRESH_ENABLED:
                existing_raw_refresh = audit_raw_refresh(OUT) if RAW_REFRESH_MODE == "reuse_fresh" else None
                if existing_raw_refresh and existing_raw_refresh.get("raw_refresh_ready"):
                    raw_refresh_succeeded = True
                    write_reused_raw_refresh_diagnostics(manifest["run_id"], existing_raw_refresh)
                    record_step(
                        manifest,
                        manifest_path,
                        "raw_snapshot_refresh",
                        {
                            "reused_fresh_validated_raw": True,
                            "ready_required_targets": f"{existing_raw_refresh['ready_required_target_count']}/{existing_raw_refresh['required_target_count']}",
                            "diagnostics": str(raw_refresh_diagnostics_path),
                        },
                    )
                else:
                    try:
                        live_discovery = write_live_board_discovery_before_raw_refresh()
                        record_step(
                            manifest,
                            manifest_path,
                            "live_board_discovery_pre_raw",
                            {
                                "status": live_discovery.get("status", ""),
                                "artifact": live_discovery.get("artifact", ""),
                                "raw_output": live_discovery.get("raw_output", ""),
                                "listed_expected_count": live_discovery.get("listed_expected_count", 0),
                                "missing_expected_count": live_discovery.get("missing_expected_count", 0),
                            },
                        )
                        refresh_summary = refresh_raw_snapshots(manifest["run_id"])
                        raw_refresh_succeeded = True
                    except Exception as exc:
                        raw_refresh_succeeded = False
                        failed_raw_refresh = audit_raw_refresh(OUT)
                        raw_refresh_diagnostics = load_raw_refresh_diagnostics(raw_refresh_diagnostics_path)
                        atomic_write_json(
                            RAW_REFRESH_HEALTH_PATH,
                            raw_refresh_health(
                                failed_raw_refresh,
                                refresh_error=str(exc),
                                refresh_diagnostics=raw_refresh_diagnostics,
                            ),
                        )
                        live_discovery = write_live_board_discovery_after_raw_failure(str(exc))
                        partial_research = write_partial_research_sidecars_after_raw_failure()
                        record_step(
                            manifest,
                            manifest_path,
                            "raw_snapshot_refresh",
                            {
                                "error": str(exc),
                                "health": str(RAW_REFRESH_HEALTH_PATH),
                                "diagnostics": str(raw_refresh_diagnostics_path),
                                "live_board_discovery": live_discovery.get("artifact", ""),
                                "live_board_discovery_status": live_discovery.get("status", ""),
                                "partial_daily_research": partial_research.get("partial_daily_research_pdf", ""),
                                "partial_daily_report_ready": partial_research.get("partial_daily_report_ready", False),
                            },
                            status="failed",
                        )
                        raise GateFailure(f"raw snapshot refresh failed; refusing to generate report: {exc}") from exc
                    record_step(
                        manifest,
                        manifest_path,
                        "raw_snapshot_refresh",
                        {
                            "board_count": len(refresh_summary.get("results", [])),
                            "outputs": [item.get("output") for item in refresh_summary.get("results", [])],
                            "diagnostics": refresh_summary.get("diagnostics"),
                        },
                    )
            else:
                write_disabled_raw_refresh_diagnostics(manifest["run_id"])
                record_step(
                    manifest,
                    manifest_path,
                    "raw_snapshot_refresh",
                    {"skipped": True, "diagnostics": str(raw_refresh_diagnostics_path)},
                )

            source_audit = audit_sources()
            atomic_write_json(PUBLIC_AUDIT, source_audit)
            record_step(manifest, manifest_path, "public_source_audit", {"ready": source_audit["all_sources_ok"]})

            event_audit = audit_event_feeds()
            atomic_write_json(EVENT_AUDIT, event_audit)
            record_step(manifest, manifest_path, "event_monitor", {"ready": event_audit["all_feeds_ok"]})

            board_results = run_daily_boards(
                BoardRunContext(
                    output_dir=OUT,
                    previous_baseline_path=select_previous_baseline_path(OUT),
                    public_source_audit_path=PUBLIC_AUDIT,
                    event_audit_path=EVENT_AUDIT,
                )
            )
            for board, runner in daily_board_registry():
                result = board_results[board.board_id]
                record_step(
                    manifest,
                    manifest_path,
                    runner.step_name,
                    {"recommendations": len(result.get("recommendations", []))},
                )

            previous_portfolio = load_baseline(select_previous_portfolio_baseline_path(OUT))
            portfolio_compare = compare_portfolio_recommendations(board_results, previous_portfolio)
            portfolio_baseline = compact_portfolio_baseline(board_results)
            atomic_write_json(PORTFOLIO_COMPARE_CURRENT, portfolio_compare)
            atomic_write_json(PORTFOLIO_BASELINE_CURRENT, portfolio_baseline)
            record_step(
                manifest,
                manifest_path,
                "portfolio_daily_compare",
                {
                    "added": portfolio_compare["summary"]["added_count"],
                    "removed": portfolio_compare["summary"]["removed_count"],
                    "changed": portfolio_compare["summary"]["changed_count"],
                    "retained": portfolio_compare["summary"]["retained_count"],
                },
            )

            model_comparison = write_model_comparison(json.loads(RAW.read_text()), OUT)
            enriched_matches = enrich_match_recommendations_with_model_comparison(
                board_results.get("world_cup_matches", {}),
                model_comparison,
            )
            if enriched_matches:
                board_results["world_cup_matches"] = enriched_matches
                atomic_write_json(OUT / MATCHES_BOARD.recommendations_artifact, enriched_matches)
            record_step(
                manifest,
                manifest_path,
                "model_comparison",
                {
                    "ready": model_comparison["ready"],
                    "match_count": model_comparison["match_count"],
                    "high_divergence_count": model_comparison["summary"]["high_divergence_count"],
                    "recommendations_enriched": len(enriched_matches.get("recommendations", [])) if enriched_matches else 0,
                },
            )

            source_metadata = write_source_model_github_metadata(
                OUT,
                timeout_seconds=source_model_metadata_timeout_seconds(),
            )
            source_registry = write_source_model_registry_bundle(OUT, REPORT_DB)
            record_step(
                manifest,
                manifest_path,
                "source_model_metadata",
                {
                    "metadata_status": source_metadata.get("status"),
                    "fetched_count": source_metadata.get("fetched_count", 0),
                    "source_count": source_metadata.get("source_count", 0),
                    "registry_status": (source_registry.get("executive_status") or {}).get("status", ""),
                    "live_metadata_ready_count": (source_registry.get("summary") or {}).get("live_metadata_ready_count", 0),
                    "github_stars_total": (source_registry.get("summary") or {}).get("github_stars_total", 0),
                },
            )

            raw_refresh = audit_raw_refresh(OUT)
            atomic_write_json(RAW_REFRESH_PATH, raw_refresh)
            atomic_write_json(RAW_REFRESH_HEALTH_PATH, raw_refresh_health(raw_refresh))
            record_step(
                manifest,
                manifest_path,
                "raw_refresh_gate",
                {
                    "raw_refresh_ready": raw_refresh["raw_refresh_ready"],
                    "driver_ready": raw_refresh["refresh_driver_ready"],
                },
            )

            portfolio = audit_portfolio(OUT)
            portfolio_version = "v0_12"
            portfolio_gate = OUT / f"portfolio_automation_gate_{portfolio_version}.json"
            portfolio_report = OUT / f"tab_fifa_portfolio_readiness_{portfolio_version}.md"
            atomic_write_json(portfolio_gate, portfolio)
            atomic_write_text(portfolio_report, render_portfolio_markdown(portfolio))
            record_step(
                manifest,
                manifest_path,
                "portfolio_gate",
                {"ready_required_boards": f"{portfolio['ready_required_board_count']}/{portfolio['required_board_count']}"},
            )

            safety = audit_safety(
                Path(__file__).resolve().parent,
                OUT,
                private_dir=PRIVATE_DATA_DIR,
                allow_private_positions=PRIVATE_OUTPUT_MODE,
            )
            safety_path = OUT / "automation_safety_gate.json"
            atomic_write_json(safety_path, safety)
            record_step(manifest, manifest_path, "safety_gate", {"ready": safety["automation_safety_ready"]})

            assert_pre_pdf_gates(
                pre_pdf_gate_map(board_results),
                raw_refresh,
                portfolio,
                safety,
            )

            pdf_run_copy = OUT / f"{REPORT_DATE}_{manifest['run_id']}.pdf"
            bankroll_run_copy = OUT / f"tab_fifa_bankroll_plan_{REPORT_DATE}_{manifest['run_id']}.json"
            with tempfile.TemporaryDirectory(prefix="tab-fifa-public-report-") as tmp:
                public_stage = Path(tmp)
                staged_pdf = public_stage / pdf_run_copy.name
                staged_bankroll = public_stage / bankroll_run_copy.name
                pdf_summary = render_pdf(
                    portfolio_compare_override=portfolio_compare,
                    public_pdf_path=staged_pdf,
                    public_bankroll_path=staged_bankroll,
                )
                staged_public_safety = audit_public_artifact_safety([staged_pdf, staged_bankroll])
                if not staged_public_safety["public_artifact_safety_ready"]:
                    reasons = "; ".join(staged_public_safety.get("blocking_reasons", [])) or "public report staging safety gate failed"
                    raise GateFailure(f"public report staging safety gate failed; refusing to publish run copies: {reasons}")
                atomic_copy(staged_pdf, pdf_run_copy)
                atomic_copy(staged_bankroll, bankroll_run_copy)
            pdf_summary["pdf_output_copy"] = str(pdf_run_copy)
            pdf_qa_path = pdf_qa_run_path(manifest["run_id"])
            pdf_qa = audit_pdf_report(pdf_run_copy, visual_smoke=True, require_visual_smoke=True)
            atomic_write_json(pdf_qa_path, pdf_qa)
            record_step(
                manifest,
                manifest_path,
                "pdf_quality_gate",
                {
                    "ready": pdf_qa["pdf_qa_ready"],
                    "page_count": pdf_qa["page_count"],
                    "missing_terms": len(pdf_qa["missing_terms"]),
                    "visual_smoke_ready": pdf_qa.get("visual_smoke", {}).get("ready"),
                    "visual_smoke_renderer": pdf_qa.get("visual_smoke", {}).get("renderer"),
                },
                status="ok" if pdf_qa["pdf_qa_ready"] else "failed",
            )
            if not pdf_qa["pdf_qa_ready"]:
                reasons = "; ".join(pdf_qa.get("blocking_reasons", [])) or "PDF QA failed"
                raise GateFailure(f"PDF QA failed; refusing to publish report: {reasons}")
            board_results = apply_execution_stakes_to_board_results(board_results, pdf_summary.get("match_stakes", []))
            portfolio_compare = compare_portfolio_recommendations(board_results, previous_portfolio)
            portfolio_baseline = compact_portfolio_baseline(board_results)
            atomic_write_json(PORTFOLIO_COMPARE_CURRENT, portfolio_compare)
            atomic_write_json(PORTFOLIO_BASELINE_CURRENT, portfolio_baseline)
            record_step(
                manifest,
                manifest_path,
                "portfolio_execution_stakes",
                {
                    "time_adjusted_new_exposure_aud": pdf_summary["time_adjusted_new_exposure_aud"],
                    "match_stake_count": len(pdf_summary.get("match_stakes", [])),
                },
            )
            record_step(manifest, manifest_path, "business_pdf", {"time_adjusted_new_exposure_aud": pdf_summary["time_adjusted_new_exposure_aud"]})

            preflight = audit_automation_preflight(
                code_dir=Path(__file__).resolve().parent,
                output_dir=OUT,
                private_dir=PRIVATE_DATA_DIR,
                safety=safety,
                portfolio=portfolio,
                raw_refresh=raw_refresh,
                report_date=PDF_PATH.stem,
                downloads_pdf=None,
                output_pdf=pdf_run_copy,
                bankroll_plan=bankroll_run_copy,
                private_output_mode=PRIVATE_OUTPUT_MODE,
                raw_refresh_enabled=RAW_REFRESH_ENABLED,
                raw_refresh_succeeded=raw_refresh_succeeded,
                user_automation_authorized=USER_AUTOMATION_AUTHORIZED,
                automation_authorization=AUTOMATION_AUTHORIZATION.to_public_dict(),
            )
            preflight_path = preflight_run_path(manifest["run_id"])
            atomic_write_json(preflight_path, preflight)
            record_step(
                manifest,
                manifest_path,
                "automation_preflight",
                {
                    "technical_preflight_ready": preflight["technical_preflight_ready"],
                    "automation_entry_ready": preflight["automation_entry_ready"],
                },
            )

            technical_automation_ready = preflight["technical_preflight_ready"]
            if not technical_automation_ready:
                technical_reasons = [
                    check.get("message", check.get("name", "preflight check failed"))
                    for check in preflight.get("checks", [])
                    if not check.get("passed")
                ]
                reasons = "; ".join(reason for reason in technical_reasons if reason) or "technical preflight failed"
                raise GateFailure(f"technical automation preflight failed; refusing to publish latest artifacts: {reasons}")
            dashboard_latest = OUT / "tab_fifa_dashboard_latest.html"
            dashboard_data_latest = OUT / "tab_fifa_dashboard_data_latest.json"
            dashboard_run_copy = OUT / f"tab_fifa_dashboard_{manifest['run_id']}.html"
            dashboard_data_run_copy = OUT / f"tab_fifa_dashboard_data_{manifest['run_id']}.json"
            report_index_path = report_index_run_path(manifest["run_id"])
            report_index_report_path = report_index_report_run_path(manifest["run_id"])
            report_index_pdf_path = report_index_pdf_run_path(manifest["run_id"])
            report_intelligence_path = report_intelligence_run_path(manifest["run_id"])
            report_intelligence_md_path = report_intelligence_md_run_path(manifest["run_id"])
            report_intelligence_pdf_path = report_intelligence_pdf_run_path(manifest["run_id"])
            metrics = response_metrics(board_results)
            response = {
                "version": VERSION,
                "run_id": manifest["run_id"],
                **metrics,
                "portfolio_automation_ready": portfolio["portfolio_automation_ready"],
                "automation_safety_ready": safety["automation_safety_ready"],
                "raw_refresh_ready": raw_refresh["raw_refresh_ready"],
                "refresh_driver_ready": raw_refresh["refresh_driver_ready"],
                "raw_refresh_succeeded": raw_refresh_succeeded,
                "technical_automation_ready": technical_automation_ready,
                "private_output_mode": PRIVATE_OUTPUT_MODE,
                "raw_refresh_enabled": RAW_REFRESH_ENABLED,
                "raw_refresh_mode": RAW_REFRESH_MODE,
                "report_date": REPORT_DATE,
                "report_timezone": str(REPORT_TZ),
                "previous_baseline_used": manifest["inputs"]["previous_baseline"],
                "previous_portfolio_baseline_used": manifest["inputs"]["previous_portfolio_baseline"],
                "latest_baseline": str(PREVIOUS_BASELINE_LATEST),
                "portfolio_daily_compare": str(PORTFOLIO_COMPARE_CURRENT),
                "portfolio_daily_compare_latest": str(PORTFOLIO_COMPARE_LATEST),
                "portfolio_baseline": str(PORTFOLIO_BASELINE_CURRENT),
                "portfolio_baseline_latest": str(PORTFOLIO_BASELINE_LATEST),
                "automation_user_authorized": USER_AUTOMATION_AUTHORIZED,
                "automation_authorization": AUTOMATION_AUTHORIZATION.to_public_dict(),
                "automation_entry_ready": technical_automation_ready and USER_AUTOMATION_AUTHORIZED,
                "ready_required_boards": f"{portfolio['ready_required_board_count']}/{portfolio['required_board_count']}",
                "pdf_time_adjusted_new_exposure_aud": pdf_summary["time_adjusted_new_exposure_aud"],
                "time_adjusted_new_exposure_aud": pdf_summary["time_adjusted_new_exposure_aud"],
                "model_comparison_ready": model_comparison["ready"],
                "model_comparison_match_count": model_comparison["match_count"],
                "model_comparison_high_divergence_count": model_comparison["summary"]["high_divergence_count"],
                "report": str(OUT / MATCHES_BOARD.report_artifact),
                "portfolio_report": str(portfolio_report),
                "portfolio_gate": str(portfolio_gate),
                "private_pdf_available": bool(pdf_summary.get("private_pdf_available")),
                "private_pdf_path_omitted": bool(pdf_summary.get("private_pdf_path_omitted", True)),
                "pdf_output_copy": str(pdf_run_copy),
                "pdf_run_copy": str(pdf_run_copy),
                "bankroll_plan": str(bankroll_run_copy),
                "bankroll_plan_run_copy": str(bankroll_run_copy),
                "model_comparison_json": str(OUT / MODEL_COMPARISON_JSON),
                "model_comparison_report": str(OUT / MODEL_COMPARISON_MD),
                "model_comparison_pdf": str(OUT / MODEL_COMPARISON_PDF),
                "current_baseline": str(CURRENT_BASELINE),
                "safety_gate": str(safety_path),
                "raw_refresh_manifest": str(RAW_REFRESH_PATH),
                "raw_refresh_batch_manifest": str(RAW_REFRESH_BATCH_PATH),
                "raw_refresh_health": str(RAW_REFRESH_HEALTH_PATH),
                "raw_refresh_diagnostics": str(raw_refresh_diagnostics_path),
                "raw_refresh_diagnostics_latest": str(RAW_REFRESH_DIAGNOSTICS_PATH),
                "pdf_qa": str(pdf_qa_path),
                "pdf_qa_latest": str(PDF_QA_LATEST),
                "pdf_qa_ready": pdf_qa["pdf_qa_ready"],
                "automation_preflight": str(preflight_path),
                "automation_preflight_latest": str(PREFLIGHT_PATH),
                "report_database": str(REPORT_DB),
                "report_index": str(report_index_path),
                "report_index_latest": str(REPORT_INDEX_LATEST),
                "report_index_report": str(report_index_report_path),
                "report_index_report_latest": str(REPORT_INDEX_REPORT_LATEST_PATH),
                "report_index_pdf": str(report_index_pdf_path),
                "report_index_pdf_latest": str(REPORT_INDEX_PDF_LATEST_PATH),
                "report_intelligence": str(report_intelligence_path),
                "report_intelligence_latest": str(REPORT_INTELLIGENCE_LATEST_PATH),
                "report_intelligence_report": str(report_intelligence_md_path),
                "report_intelligence_report_latest": str(REPORT_INTELLIGENCE_MD_LATEST_PATH),
                "report_intelligence_pdf": str(report_intelligence_pdf_path),
                "report_intelligence_pdf_latest": str(REPORT_INTELLIGENCE_PDF_LATEST_PATH),
                "automation_readiness": str(AUTOMATION_READINESS_PATH),
                "automation_readiness_report": str(AUTOMATION_READINESS_REPORT_PATH),
                "automation_readiness_pdf": str(AUTOMATION_READINESS_PDF_PATH),
                "automation_candidate": str(AUTOMATION_CANDIDATE_PATH),
                "automation_candidate_report": str(AUTOMATION_CANDIDATE_REPORT_PATH),
                "automation_candidate_pdf": str(AUTOMATION_CANDIDATE_PDF_PATH),
                "dashboard": str(dashboard_latest),
                "dashboard_run_copy": str(dashboard_run_copy),
                "dashboard_data": str(dashboard_data_latest),
                "dashboard_data_run_copy": str(dashboard_data_run_copy),
                "manifest": str(manifest_path),
                "latest_manifest": str(LATEST_MANIFEST),
                "latest_commit": str(LATEST_COMMIT),
            }
            manifest["status"] = "publishing"
            manifest["technical_automation_ready"] = technical_automation_ready
            manifest["automation_entry_ready"] = response["automation_entry_ready"]
            manifest["outputs"] = response
            automation_candidate = write_automation_candidate(OUT, AUTOMATION_CANDIDATE_PATH)
            response["automation_candidate_summary"] = {
                "status": automation_candidate.get("status", ""),
                "recommended_cadence": automation_candidate.get("recommended_cadence", ""),
                "installed": bool(automation_candidate.get("installed")),
            }
            response["automation_candidate_report_summary"] = write_automation_candidate_report(
                OUT,
                AUTOMATION_CANDIDATE_REPORT_PATH,
                candidate=automation_candidate,
            )
            response["automation_candidate_pdf_summary"] = write_automation_candidate_pdf(
                OUT,
                AUTOMATION_CANDIDATE_PDF_PATH,
                candidate=automation_candidate,
            )
            manifest["outputs"] = response
            write_manifest(manifest, manifest_path)

            manifest["finished_at"] = utc_now()
            manifest["status"] = "safety_pending"
            manifest["outputs"] = response
            db_summary = store_daily_run(REPORT_DB, manifest, OUT)
            dashboard_summary = write_dashboard(OUT, REPORT_DB, manifest, publish_latest=False)
            update_run_dashboard_paths(
                REPORT_DB,
                manifest["run_id"],
                Path(dashboard_summary["dashboard_run_copy"]),
                Path(dashboard_summary["dashboard_data_run_copy"]),
            )
            response.update(
                {
                    "dashboard": str(dashboard_latest),
                    "dashboard_latest": str(dashboard_latest),
                    "dashboard_run_copy": dashboard_summary["dashboard_run_copy"],
                    "dashboard_data": str(dashboard_data_latest),
                    "dashboard_data_latest": str(dashboard_data_latest),
                    "dashboard_data_run_copy": dashboard_summary["dashboard_data_run_copy"],
                    "report_database": str(REPORT_DB),
                    "report_database_summary": db_summary,
                }
            )
            manifest["outputs"] = response
            db_summary = store_daily_run(REPORT_DB, manifest, OUT)
            write_report_index(REPORT_DB, OUT, report_index_path)
            response["report_database_summary"] = db_summary
            manifest["outputs"] = response
            public_artifacts_to_publish = {
                "pdf_run_copy": pdf_run_copy,
                "bankroll_plan_run_copy": bankroll_run_copy,
                "dashboard_run_copy": Path(dashboard_summary["dashboard_run_copy"]),
                "dashboard_data_run_copy": Path(dashboard_summary["dashboard_data_run_copy"]),
                "manifest": manifest_path,
                "current_baseline": CURRENT_BASELINE,
                "portfolio_baseline": PORTFOLIO_BASELINE_CURRENT,
                "portfolio_daily_compare": PORTFOLIO_COMPARE_CURRENT,
                "portfolio_report": portfolio_report,
                "portfolio_gate": portfolio_gate,
                "model_comparison_json": OUT / MODEL_COMPARISON_JSON,
                "model_comparison_report": OUT / MODEL_COMPARISON_MD,
                "model_comparison_pdf": OUT / MODEL_COMPARISON_PDF,
                "raw_refresh_manifest": RAW_REFRESH_PATH,
                "raw_refresh_batch_manifest": RAW_REFRESH_BATCH_PATH,
                "raw_refresh_health": RAW_REFRESH_HEALTH_PATH,
                "raw_refresh_diagnostics": raw_refresh_diagnostics_path,
                "pdf_qa": pdf_qa_path,
                "automation_preflight": preflight_path,
                "report_index": report_index_path,
                "safety_gate": safety_path,
                "report_database": REPORT_DB,
                "automation_candidate": AUTOMATION_CANDIDATE_PATH,
                "automation_candidate_report": AUTOMATION_CANDIDATE_REPORT_PATH,
                "automation_candidate_pdf": AUTOMATION_CANDIDATE_PDF_PATH,
            }
            public_artifact_safety = audit_public_artifact_safety(public_artifacts_to_publish.values())
            response["public_artifact_safety_ready"] = public_artifact_safety["public_artifact_safety_ready"]
            response["public_artifact_safety"] = public_artifact_safety
            manifest["outputs"] = response
            record_step(
                manifest,
                manifest_path,
                "public_artifact_safety",
                {
                    "ready": public_artifact_safety["public_artifact_safety_ready"],
                    "issue_count": public_artifact_safety["public_artifact_issue_count"],
                },
            )
            if not public_artifact_safety["public_artifact_safety_ready"]:
                reasons = "; ".join(public_artifact_safety.get("blocking_reasons", [])) or "public artifact safety gate failed"
                raise GateFailure(f"public artifact safety gate failed; refusing to publish latest artifacts: {reasons}")

            manifest["status"] = "ready_for_manual_report"
            manifest["outputs"] = response
            write_manifest(manifest, manifest_path)
            final_db_summary = store_daily_run(REPORT_DB, manifest, OUT)
            dashboard_summary = write_dashboard(OUT, REPORT_DB, manifest, publish_latest=False)
            update_run_dashboard_paths(
                REPORT_DB,
                manifest["run_id"],
                Path(dashboard_summary["dashboard_run_copy"]),
                Path(dashboard_summary["dashboard_data_run_copy"]),
            )
            response.update(
                {
                    "dashboard_run_copy": dashboard_summary["dashboard_run_copy"],
                    "dashboard_data_run_copy": dashboard_summary["dashboard_data_run_copy"],
                }
            )
            response["report_database_summary"] = final_db_summary
            manifest["outputs"] = response
            final_db_summary = store_daily_run(REPORT_DB, manifest, OUT)
            response["report_database_summary"] = final_db_summary
            write_manifest(manifest, manifest_path)
            public_artifact_safety = audit_public_artifact_safety(public_artifacts_to_publish.values())
            response["public_artifact_safety_ready"] = public_artifact_safety["public_artifact_safety_ready"]
            response["public_artifact_safety"] = public_artifact_safety
            manifest["outputs"] = response
            if not public_artifact_safety["public_artifact_safety_ready"]:
                reasons = "; ".join(public_artifact_safety.get("blocking_reasons", [])) or "public artifact safety gate failed"
                raise GateFailure(f"final public artifact safety gate failed; refusing to publish latest artifacts: {reasons}")
            if NO_LATEST_PUBLISH:
                manifest["status"] = "backfill_ready_no_latest_publish" if BACKFILL_RECONSTRUCTION else "ready_no_latest_publish"
                response["status"] = manifest["status"]
                response["latest_publish_disabled"] = True
                response["backfill_reconstruction"] = BACKFILL_RECONSTRUCTION
                response["truthfulness_note"] = (
                    "本次为历史缺口补跑重建，不发布 latest_commit，不替代原时点真实盘口快照。"
                    if BACKFILL_RECONSTRUCTION
                    else "本次显式禁用 latest 发布，仅保留 run-scoped 产物。"
                )
                manifest["outputs"] = response
                write_manifest(manifest, manifest_path, publish_latest=False)
                response["report_database_summary"] = store_daily_run(REPORT_DB, manifest, OUT)
                emit_public_response(response)
                return
            atomic_copy(preflight_path, PREFLIGHT_PATH)
            atomic_copy(pdf_qa_path, PDF_QA_LATEST)
            public_artifacts_to_publish["automation_preflight_latest"] = PREFLIGHT_PATH
            public_artifacts_to_publish["pdf_qa_latest"] = PDF_QA_LATEST

            report_index_commit_payload = latest_commit_payload(manifest, response, public_artifacts_to_publish)
            report_index_payload = write_report_index(REPORT_DB, OUT, report_index_path, latest_commit=report_index_commit_payload)
            write_report_index_report(report_index_payload, report_index_report_path)
            write_report_index_pdf(report_index_payload, report_index_pdf_path)
            public_artifacts_to_publish["report_index_report"] = report_index_report_path
            public_artifacts_to_publish["report_index_pdf"] = report_index_pdf_path

            latest_artifact_safety = audit_public_artifact_safety(public_artifacts_to_publish.values())
            response["public_artifact_safety_ready"] = latest_artifact_safety["public_artifact_safety_ready"]
            response["public_artifact_safety"] = latest_artifact_safety
            manifest["outputs"] = response
            if not latest_artifact_safety["public_artifact_safety_ready"]:
                reasons = "; ".join(latest_artifact_safety.get("blocking_reasons", [])) or "latest public artifact safety gate failed"
                raise GateFailure(f"latest public artifact safety gate failed; refusing to publish latest_commit: {reasons}")

            readiness_commit_payload = latest_commit_payload(manifest, response, public_artifacts_to_publish)
            readiness = write_automation_readiness_summary(
                OUT,
                AUTOMATION_READINESS_PATH,
                command_status={"mode": "daily", "exit_code": 0},
                latest_commit_override=readiness_commit_payload,
            )
            readiness_report = write_automation_readiness_report(
                OUT,
                AUTOMATION_READINESS_REPORT_PATH,
                summary=readiness,
            )
            readiness_pdf = write_automation_readiness_pdf(
                OUT,
                AUTOMATION_READINESS_PDF_PATH,
                summary=readiness,
            )
            readiness_safety = audit_public_artifact_safety([AUTOMATION_READINESS_PATH, AUTOMATION_READINESS_REPORT_PATH, AUTOMATION_READINESS_PDF_PATH])
            response["automation_readiness_summary"] = {
                "status": readiness.get("status", ""),
                "formal_report_publish_ready": bool(readiness.get("formal_report_publish_ready")),
                "recurring_automation_ready": bool(readiness.get("recurring_automation_ready")),
                "blocker_count": len(readiness.get("blockers", [])),
            }
            response["automation_readiness_report_summary"] = readiness_report
            response["automation_readiness_pdf_summary"] = readiness_pdf
            response["automation_readiness_safety"] = readiness_safety
            manifest["outputs"] = response
            if not readiness_safety["public_artifact_safety_ready"]:
                reasons = "; ".join(readiness_safety.get("blocking_reasons", [])) or "automation readiness safety gate failed"
                raise GateFailure(f"automation readiness safety gate failed; refusing to publish latest_commit: {reasons}")
            public_artifacts_to_publish["automation_readiness"] = AUTOMATION_READINESS_PATH
            public_artifacts_to_publish["automation_readiness_report"] = AUTOMATION_READINESS_REPORT_PATH
            public_artifacts_to_publish["automation_readiness_pdf"] = AUTOMATION_READINESS_PDF_PATH

            report_intelligence = write_report_intelligence_bundle(
                OUT,
                REPORT_DB,
                json_name=report_intelligence_path.name,
                markdown_name=report_intelligence_md_path.name,
                pdf_name=report_intelligence_pdf_path.name,
                latest_commit_override=readiness_commit_payload,
                report_index_override=report_index_payload,
                readiness_override=readiness,
                candidate_override=automation_candidate,
            )
            response["report_intelligence_summary"] = {
                "path": report_intelligence_path.name,
                "markdown": report_intelligence_md_path.name,
                "pdf": report_intelligence_pdf_path.name,
                "buy_count": int((report_intelligence.get("recommendation_summary") or {}).get("buy_count") or 0),
                "backfill_queue_count": int((report_intelligence.get("timeline_health") or {}).get("backfill_queue_count") or 0),
            }
            manifest["outputs"] = response
            response["report_database_summary"] = store_daily_run(REPORT_DB, manifest, OUT)
            manifest["outputs"] = response
            public_artifacts_to_publish["report_intelligence"] = report_intelligence_path
            public_artifacts_to_publish["report_intelligence_report"] = report_intelligence_md_path
            public_artifacts_to_publish["report_intelligence_pdf"] = report_intelligence_pdf_path

            final_artifact_safety = audit_public_artifact_safety(public_artifacts_to_publish.values())
            response["public_artifact_safety_ready"] = final_artifact_safety["public_artifact_safety_ready"]
            response["public_artifact_safety"] = final_artifact_safety
            manifest["outputs"] = response
            if not final_artifact_safety["public_artifact_safety_ready"]:
                reasons = "; ".join(final_artifact_safety.get("blocking_reasons", [])) or "final public artifact safety gate failed"
                raise GateFailure(f"final public artifact safety gate failed; refusing to publish latest_commit: {reasons}")
            write_manifest(manifest, manifest_path, publish_latest=True)
            commit_artifacts = dict(public_artifacts_to_publish)
            response["latest_commit"] = str(LATEST_COMMIT)
            manifest["outputs"] = response
            record_step(
                manifest,
                manifest_path,
                "latest_commit_publish",
                {
                    "latest_commit": str(LATEST_COMMIT),
                    "artifact_count": len(commit_artifacts),
                },
            )
            write_manifest(manifest, manifest_path, publish_latest=True)
            publish_latest_commit(manifest, response, commit_artifacts)
            convenience_latest = publish_convenience_latest_artifacts(
                pdf_run_copy=pdf_run_copy,
                bankroll_run_copy=bankroll_run_copy,
                dashboard_run_copy=Path(dashboard_summary["dashboard_run_copy"]),
                dashboard_data_run_copy=Path(dashboard_summary["dashboard_data_run_copy"]),
                downloads_pdf=PDF_PATH,
                output_dir=OUT,
                version=VERSION,
            )
            post_commit_latest = {
                "ready": bool(convenience_latest.get("ready")),
                "artifacts": dict(convenience_latest.get("artifacts", {})),
                "errors": list(convenience_latest.get("errors", [])),
            }
            for key, src, dst in [
                ("report_index_latest", report_index_path, REPORT_INDEX_LATEST),
                ("report_index_report_latest", report_index_report_path, REPORT_INDEX_REPORT_LATEST_PATH),
                ("report_index_pdf_latest", report_index_pdf_path, REPORT_INDEX_PDF_LATEST_PATH),
                ("report_intelligence_latest", report_intelligence_path, REPORT_INTELLIGENCE_LATEST_PATH),
                ("report_intelligence_report_latest", report_intelligence_md_path, REPORT_INTELLIGENCE_MD_LATEST_PATH),
                ("report_intelligence_pdf_latest", report_intelligence_pdf_path, REPORT_INTELLIGENCE_PDF_LATEST_PATH),
            ]:
                try:
                    atomic_copy(src, dst)
                    post_commit_latest["artifacts"][key] = str(dst)
                    response[key] = str(dst)
                except Exception as exc:
                    post_commit_latest["ready"] = False
                    post_commit_latest["errors"].append({"artifact": key, "error": str(exc)})
            response["post_commit_latest_publish"] = post_commit_latest
            response["convenience_latest_publish"] = convenience_latest
            for key, value in convenience_latest.get("artifacts", {}).items():
                response[key] = value
            manifest["outputs"] = response
            record_step(
                manifest,
                manifest_path,
                "post_commit_latest_publish",
                {
                    "ready": post_commit_latest["ready"],
                    "artifact_count": len(post_commit_latest.get("artifacts", {})),
                    "error_count": len(post_commit_latest.get("errors", [])),
                },
                status="ok" if post_commit_latest["ready"] else "warning",
            )
            recommendation_operations = write_recommendation_operations_bundle(OUT, REPORT_DB)
            model_divergence_review = write_model_divergence_review_bundle(OUT, REPORT_DB)
            research_sidecar_paths = [
                OUT / str((recommendation_operations.get("artifacts") or {}).get("json", "recommendation_operations_latest.json")),
                OUT / str((recommendation_operations.get("artifacts") or {}).get("markdown", "recommendation_operations_latest.md")),
                OUT / str((recommendation_operations.get("artifacts") or {}).get("pdf", "recommendation_operations_latest.pdf")),
                OUT / str((model_divergence_review.get("artifacts") or {}).get("json", "model_divergence_review_latest.json")),
                OUT / str((model_divergence_review.get("artifacts") or {}).get("markdown", "model_divergence_review_latest.md")),
                OUT / str((model_divergence_review.get("artifacts") or {}).get("pdf", "model_divergence_review_latest.pdf")),
            ]
            research_sidecar_safety = audit_public_artifact_safety(research_sidecar_paths)
            response["recommendation_operations_summary"] = {
                "pdf": (recommendation_operations.get("artifacts") or {}).get("pdf", ""),
                "candidate_count": int((recommendation_operations.get("summary") or {}).get("candidate_count") or 0),
                "executable_new_stake_aud": float((recommendation_operations.get("summary") or {}).get("executable_new_stake_aud") or 0),
                "edge_threshold_pass_count": int((recommendation_operations.get("summary") or {}).get("edge_threshold_pass_count") or 0),
                "max_risk_of_ruin": float((recommendation_operations.get("summary") or {}).get("max_risk_of_ruin") or 0),
            }
            response["model_divergence_review_summary"] = {
                "pdf": (model_divergence_review.get("artifacts") or {}).get("pdf", ""),
                "match_count": int((model_divergence_review.get("summary") or {}).get("match_count") or 0),
                "high_divergence_count": int((model_divergence_review.get("summary") or {}).get("high_divergence_count") or 0),
                "high_priority_review_count": int((model_divergence_review.get("summary") or {}).get("high_priority_review_count") or 0),
                "execution_unlock": str((model_divergence_review.get("summary") or {}).get("execution_unlock") or ""),
            }
            response["post_commit_research_sidecar_safety"] = research_sidecar_safety
            manifest["outputs"] = response
            record_step(
                manifest,
                manifest_path,
                "post_commit_research_sidecars",
                {
                    "recommendation_operations": response["recommendation_operations_summary"],
                    "model_divergence_review": response["model_divergence_review_summary"],
                    "public_artifact_safety_ready": research_sidecar_safety["public_artifact_safety_ready"],
                    "issue_count": research_sidecar_safety["public_artifact_issue_count"],
                },
                status="ok" if research_sidecar_safety["public_artifact_safety_ready"] else "warning",
            )
            write_manifest(manifest, manifest_path, publish_latest=True)
            print(json.dumps(sanitize_public_manifest(response), indent=2))
        except Exception as exc:
            manifest["finished_at"] = utc_now()
            manifest["status"] = "blocked_by_gate" if isinstance(exc, GateFailure) else "failed"
            manifest["error"] = {"type": type(exc).__name__, "message": str(exc)}
            write_manifest(manifest, manifest_path)
            failed_preflight_path = write_failed_preflight(manifest["run_id"], exc, publish_latest=True)
            try:
                publish_failed_readiness_sidecars(
                    manifest,
                    command_status={"mode": "daily", "exit_code": 1, "failure_type": type(exc).__name__},
                    failed_preflight_path=failed_preflight_path,
                )
            except Exception:
                pass
            try:
                store_daily_run(REPORT_DB, manifest, OUT)
            except Exception:
                pass
            raise


def run_raw_refresh_diagnostics_path(run_id: str) -> Path:
    return OUT / f"raw_refresh_diagnostics_{run_id}.json"


def write_raw_refresh_diagnostics(run_id: str, payload: Dict) -> Path:
    public_payload = sanitize_public_manifest(payload)
    run_path = run_raw_refresh_diagnostics_path(run_id)
    atomic_write_json(run_path, public_payload)
    atomic_write_json(RAW_REFRESH_DIAGNOSTICS_PATH, public_payload)
    return run_path


def write_reused_raw_refresh_diagnostics(run_id: str, raw_refresh: Dict) -> Path:
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": utc_now(),
        "status": "reused_fresh_validated_raw",
        "raw_refresh_ready": bool(raw_refresh.get("raw_refresh_ready")),
        "ready_required_target_count": raw_refresh.get("ready_required_target_count", 0),
        "required_target_count": raw_refresh.get("required_target_count", 0),
        "targets": [
            {
                "board_id": target.get("board_id"),
                "name": target.get("name"),
                "raw_snapshot": public_artifact_name(target.get("raw_snapshot")),
                "raw_timestamp": target.get("raw_timestamp"),
                "raw_age_hours": target.get("raw_age_hours"),
                "raw_fresh": bool(target.get("raw_fresh")),
                "raw_valid": bool(target.get("raw_valid")),
                "refresh_ready": bool(target.get("refresh_ready")),
            }
            for target in raw_refresh.get("targets", [])
        ],
        "attempts": [],
    }
    return heartbeat_raw_refresh_diagnostics(run_id, payload)


def write_disabled_raw_refresh_diagnostics(run_id: str) -> Path:
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": utc_now(),
        "status": "raw_refresh_disabled",
        "raw_refresh_ready": True,
        "attempts": [],
    }
    return heartbeat_raw_refresh_diagnostics(run_id, payload)


def write_live_board_discovery_after_raw_failure(refresh_error: str) -> Dict:
    try:
        discovery = run_live_board_discovery()
        bundle = write_live_board_discovery_bundle(OUT)
        return {
            "status": (bundle.get("executive_status") or {}).get("status", "written"),
            "artifact": (bundle.get("artifacts") or {}).get("json", "live_board_discovery_latest.json"),
            "raw_output": discovery.get("raw_output", LIVE_BOARD_DISCOVERY_RAW_LATEST),
        }
    except Exception as exc:
        atomic_write_json(
            OUT / LIVE_BOARD_DISCOVERY_RAW_LATEST,
            {
                "generated_at": utc_now(),
                "source": "playwright_read_only_tab_soccer_live_nav",
                "status": "failed",
                "refresh_error": str(refresh_error),
                "discovery_error": str(exc),
                "truthfulness_note": "live board discovery failed; do not use old odds for current betting advice.",
            },
        )
        bundle = write_live_board_discovery_bundle(OUT)
        return {
            "status": "failed",
            "artifact": (bundle.get("artifacts") or {}).get("json", "live_board_discovery_latest.json"),
            "error": str(exc),
        }


def write_live_board_discovery_before_raw_refresh() -> Dict:
    try:
        discovery = run_live_board_discovery()
        bundle = write_live_board_discovery_bundle(OUT)
        summary = bundle.get("summary") or {}
        return {
            "status": (bundle.get("executive_status") or {}).get("status", "written"),
            "artifact": (bundle.get("artifacts") or {}).get("json", "live_board_discovery_latest.json"),
            "raw_output": discovery.get("raw_output", LIVE_BOARD_DISCOVERY_RAW_LATEST),
            "quality_status": summary.get("quality_status", discovery.get("quality_status", "")),
            "listed_expected_count": int(summary.get("listed_expected_count") or 0),
            "missing_expected_count": int(summary.get("missing_expected_count") or 0),
        }
    except Exception as exc:
        atomic_write_json(
            OUT / LIVE_BOARD_DISCOVERY_RAW_LATEST,
            {
                "generated_at": utc_now(),
                "source": "playwright_read_only_tab_soccer_live_nav",
                "status": "failed",
                "stage": "pre_raw_refresh",
                "discovery_error": public_tail(str(exc), limit=500),
                "truthfulness_note": "raw refresh 前必须先刷新 TAB live board list；失败时不能沿用旧 match targets 抓取盘口。",
            },
        )
        bundle = write_live_board_discovery_bundle(OUT)
        raise RuntimeError(
            "pre raw live board discovery failed; refusing to use stale TAB match targets: "
            f"{public_tail(str(exc), limit=500)}"
        ) from exc


def write_partial_research_sidecars_after_raw_failure() -> Dict:
    try:
        strategy = write_available_board_strategy_bundle(OUT, REPORT_DB)
        recovery = write_raw_refresh_recovery_bundle(OUT)
        partial = write_partial_daily_research_bundle(OUT, report_date=REPORT_DATE)
        return {
            "status": "written",
            "available_board_strategy_pdf": (strategy.get("artifacts") or {}).get("pdf", ""),
            "raw_refresh_recovery_pdf": (recovery.get("artifacts") or {}).get("pdf", ""),
            "partial_daily_research_pdf": (partial.get("artifacts") or {}).get("pdf", ""),
            "partial_daily_research_dated_pdf": (partial.get("artifacts") or {}).get("dated_pdf", ""),
            "partial_daily_report_ready": bool((partial.get("executive_status") or {}).get("partial_daily_report_ready")),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": public_tail(str(exc), limit=300),
            "partial_daily_report_ready": False,
        }


def run_live_board_discovery() -> Dict:
    assert_node_ready()
    if not LIVE_BOARD_DISCOVERY_SCRIPT.exists():
        raise RuntimeError(f"live board discovery script is missing: {LIVE_BOARD_DISCOVERY_SCRIPT.name}")
    command = [
        str(NODE_BIN),
        str(LIVE_BOARD_DISCOVERY_SCRIPT),
        "--output-dir",
        str(OUT),
        "--timeout-ms",
        str(refresh_process_timeout_seconds("live_board_discovery") * 1000),
    ]
    env = os.environ.copy()
    env.setdefault("TAB_FIFA_HEADLESS", "1")
    first_attempt_headless = str(env.get("TAB_FIFA_HEADLESS", "1")).lower() not in {"0", "false", "no"}
    result = run_live_board_discovery_attempt(command, env=env, headed_fallback=False)
    if result.get("access_denied") and first_attempt_headless:
        annotate_live_discovery_access_policy()
        result["access_policy_status"] = "blocked_by_access_policy"
        result["blocker_code"] = "ai_controlled_access_rejected"
        result["recommended_next_action"] = public_raw_access_policy_next_action()
    return result


def run_live_board_discovery_attempt(command: list[str], env: Dict[str, str], headed_fallback: bool) -> Dict:
    completed = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parent,
        text=True,
        capture_output=True,
        check=False,
        timeout=refresh_process_timeout_seconds("live_board_discovery"),
        env=env,
    )
    if completed.returncode != 0:
        raise RuntimeError(public_tail(completed.stderr or completed.stdout))
    raw_payload = read_live_board_discovery_raw_payload()
    return {
        "status": "written",
        "raw_output": LIVE_BOARD_DISCOVERY_RAW_LATEST,
        "headed_fallback": headed_fallback,
        "access_denied": live_board_discovery_access_denied(raw_payload),
        "quality_status": (raw_payload.get("summary") or {}).get("quality_status", ""),
    }


def read_live_board_discovery_raw_payload() -> Dict:
    path = OUT / LIVE_BOARD_DISCOVERY_RAW_LATEST
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def live_board_discovery_access_denied(payload: Dict) -> bool:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    markers = payload.get("page_markers") if isinstance(payload.get("page_markers"), dict) else {}
    return bool(summary.get("access_denied") or markers.get("access_denied"))


def annotate_live_discovery_access_policy() -> None:
    payload = read_live_board_discovery_raw_payload()
    if not payload:
        return
    summary = payload.setdefault("summary", {})
    if isinstance(summary, dict):
        issues = summary.setdefault("quality_issues", [])
        if isinstance(issues, list) and "ai_controlled_access_rejected" not in issues:
            issues.append("ai_controlled_access_rejected")
        summary["automation_decision"] = "blocked_by_access_policy"
        summary["blocker_code"] = "ai_controlled_access_rejected"
    payload["access_policy"] = {
        "status": "blocked_by_access_policy",
        "blocker_code": "ai_controlled_access_rejected",
        "reason": "TAB 返回 Access Denied，表示自动化受控访问不可作为公开 raw 数据来源。",
        "forbidden_recovery": ["headed_fallback", "captcha_bypass", "fingerprint_spoofing", "stealth_browser"],
        "allowed_recovery": ["official_data_feed", "user_authorized_manual_export_import", "research_only_from_existing_fresh_partial_raw"],
        "next_safe_action": public_raw_access_policy_next_action(),
    }
    atomic_write_json(OUT / LIVE_BOARD_DISCOVERY_RAW_LATEST, payload)


def public_raw_access_policy_next_action() -> str:
    return (
        "TAB 明确拒绝 AI controlled access；自动 raw 刷新必须 fail-closed。"
        "下一步只能接入官方/授权数据源，或由用户在本机导出后导入快照；"
        "已有 partial raw 仅可用于 research-only 诊断，新增执行金额保持 AUD 0。"
    )


def refresh_raw_snapshots(run_id: str) -> Dict:
    with tempfile.TemporaryDirectory(prefix="tab-fifa-refresh-") as tmp:
        staging = Path(tmp)
        refresh_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        board_summaries = []
        diagnostics = {
            "schema_version": 1,
            "run_id": run_id,
            "generated_at": utc_now(),
            "refresh_id": refresh_id,
            "status": "running",
            "attempts": [],
            "results": [],
        }
        heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
        try:
            for board_id, output_path in RAW_REFRESH_BOARDS:
                attempts = 2 if board_id == "matches" else 1
                try:
                    board_summaries.append(
                        refresh_board_to_staging(
                            board_id,
                            staging,
                            attempts=attempts,
                            refresh_id=refresh_id,
                            run_id=run_id,
                            diagnostics=diagnostics,
                        )
                    )
                except Exception as board_exc:
                    failure = {
                        "board_id": board_id,
                        "output": public_artifact_name(output_path.name),
                        "error": public_tail(str(board_exc), limit=500),
                    }
                    diagnostics.setdefault("board_failures", []).append(failure)
                    diagnostics["board_failure_count"] = len(diagnostics.get("board_failures") or [])
                    diagnostics["failed_board_ids"] = [item.get("board_id") for item in diagnostics.get("board_failures") or []]
                    diagnostics["status"] = "running_with_board_failures"
                    heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
                    continue
            board_failures = diagnostics.get("board_failures") or []
            if board_failures:
                diagnostics["continued_after_board_failure"] = True
                diagnostics["status"] = "partial_attempts_completed"
                heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
            staged_batch_manifest = None
            if not board_failures:
                staged_batch_manifest = write_raw_refresh_batch_manifest(staging, refresh_id, generated_at=utc_now())
            else:
                diagnostics["staged_batch_manifest_skipped"] = True
                diagnostics["staged_batch_manifest_skip_reason"] = "board_refresh_failures"
                heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
            staged_safety = audit_output_safety(staging)
            diagnostics["staged_safety_ready"] = bool(staged_safety["automation_safety_ready"])
            diagnostics["status"] = "staging_safety_checked"
            heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
            if not staged_safety["automation_safety_ready"]:
                reasons = "; ".join(staged_safety.get("blocking_reasons", [])) or "staged raw safety gate failed"
                raise RuntimeError(f"staged raw safety gate failed; refusing to publish raw snapshots: {reasons}")
            staged_raw_gate = audit_staged_raw_refresh(staging, expected_refresh_id=refresh_id)
            diagnostics["staged_raw_ready"] = bool(staged_raw_gate["staged_raw_ready"])
            diagnostics["ready_required_target_count"] = staged_raw_gate.get("ready_required_target_count", 0)
            diagnostics["required_target_count"] = staged_raw_gate.get("required_target_count", 0)
            diagnostics["status"] = "staged_raw_checked"
            heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
            if not staged_raw_gate["staged_raw_ready"]:
                try:
                    research_only_manifest = write_research_only_staged_raw_manifest(
                        staging,
                        refresh_id=refresh_id,
                        diagnostics=diagnostics,
                        staged_raw_gate=staged_raw_gate,
                        staged_safety=staged_safety,
                    )
                    diagnostics["research_only_staged_raw_status"] = research_only_manifest.get("status", "")
                    diagnostics["research_only_staged_raw_manifest"] = RAW_REFRESH_RESEARCH_ONLY_LATEST
                    diagnostics["research_only_successful_board_count"] = int(
                        research_only_manifest.get("successful_board_count") or 0
                    )
                    diagnostics["research_only_execution_allowed"] = False
                    diagnostics["research_only_current_executable_new_stake_aud"] = 0
                except Exception as manifest_exc:
                    diagnostics["research_only_staged_raw_status"] = "manifest_failed"
                    diagnostics["research_only_staged_raw_error"] = public_tail(str(manifest_exc), limit=300)
                heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
                reasons = "; ".join(staged_raw_gate.get("blocking_reasons", [])) or "staged raw validation gate failed"
                if board_failures:
                    failure_text = "; ".join(f"{item.get('board_id')}: {item.get('error')}" for item in board_failures)
                    reasons = f"board refresh failures: {failure_text}; {reasons}"
                raise RuntimeError(f"staged raw validation gate failed; refusing to publish raw snapshots: {reasons}")
            if staged_batch_manifest is None:
                staged_batch_manifest = write_raw_refresh_batch_manifest(staging, refresh_id, generated_at=utc_now())
            backup_dir = PRIVATE_DATA_DIR / "raw_backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-daily")
            backup_dir.mkdir(parents=True, exist_ok=True)
            ensure_private_tree_permissions(PRIVATE_DATA_DIR)
            for _board_id, output_path in RAW_REFRESH_BOARDS:
                staged = staging / output_path.name
                if not staged.exists():
                    raise RuntimeError(f"raw refresh did not create expected staged file: {staged}")
                if output_path.exists():
                    atomic_copy(output_path, backup_dir / output_path.name)
                atomic_copy(staged, output_path)
            batch_manifest_path = write_raw_refresh_batch_manifest(OUT, refresh_id, generated_at=utc_now())
            results = [item for summary in board_summaries for item in summary.get("results", [])]
            diagnostics["status"] = "published"
            diagnostics["published_at"] = utc_now()
            diagnostics["result_count"] = len(results)
            diagnostics["results"] = [public_refresh_result(item) for item in results]
            diagnostics_path = heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
            return {
                "generated_at": utc_now(),
                "refresh_id": refresh_id,
                "staging_dir": str(staging),
                "backup_dir": str(backup_dir),
                "staged_batch_manifest": str(staged_batch_manifest),
                "batch_manifest": str(batch_manifest_path),
                "diagnostics": str(diagnostics_path),
                "staged_safety": staged_safety,
                "staged_raw_gate": staged_raw_gate,
                "results": results,
            }
        except KeyboardInterrupt as exc:
            diagnostics["status"] = "interrupted"
            diagnostics["interrupted_at"] = utc_now()
            diagnostics["error"] = "raw refresh interrupted before completion"
            diagnostics["interrupt_reason"] = "KeyboardInterrupt"
            heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
            raise
        except Exception as exc:
            diagnostics["status"] = "failed"
            diagnostics["failed_at"] = utc_now()
            diagnostics["error"] = str(exc)
            heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
            raise


def heartbeat_raw_refresh_diagnostics(run_id: str, diagnostics: Dict) -> Path:
    diagnostics["updated_at"] = utc_now()
    diagnostics["heartbeat_count"] = len(diagnostics.get("attempts", []))
    return write_raw_refresh_diagnostics(run_id, diagnostics)


def load_raw_refresh_diagnostics(path: Path) -> Dict:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_research_only_staged_raw_manifest(
    staging: Path,
    *,
    refresh_id: str,
    diagnostics: Dict,
    staged_raw_gate: Dict,
    staged_safety: Dict,
) -> Dict:
    staging = Path(staging)
    target_dir = OUT / RAW_REFRESH_RESEARCH_ONLY_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / RAW_REFRESH_RESEARCH_ONLY_LATEST
    board_by_board_id = {board.board_id: board for board in BOARD_CONFIGS}
    board_by_refresh_id = {board.refresh_board_id: board for board in BOARD_CONFIGS}
    copied_paths: list[Path] = []
    successful_boards = []
    failed_boards = []
    attempt_warnings = []

    for target in staged_raw_gate.get("targets") or []:
        if not isinstance(target, dict):
            continue
        board = board_by_board_id.get(str(target.get("board_id") or "")) or board_by_refresh_id.get(
            str(target.get("board_id") or "")
        )
        refresh_board_id = board.refresh_board_id if board else str(target.get("board_id") or "")
        raw_snapshot = public_artifact_name(target.get("raw_snapshot"))
        if bool(target.get("refresh_ready")) and raw_snapshot:
            staged = staging / raw_snapshot
            if staged.exists():
                copy_name = safe_research_only_raw_name(refresh_id, refresh_board_id, raw_snapshot)
                copy_path = target_dir / copy_name
                atomic_copy(staged, copy_path)
                copied_paths.append(copy_path)
                successful_boards.append(
                    {
                        "board_id": board.board_id if board else target.get("board_id", ""),
                        "refresh_board_id": refresh_board_id,
                        "name": board.name if board else target.get("name", ""),
                        "raw_snapshot": raw_snapshot,
                        "research_only_raw_snapshot": f"{RAW_REFRESH_RESEARCH_ONLY_DIR}/{copy_name}",
                        "raw_timestamp": target.get("raw_timestamp"),
                        "refresh_id": target.get("refresh_id"),
                        "sha256": target.get("sha256"),
                        "raw_fresh": bool(target.get("raw_fresh")),
                        "raw_valid": bool(target.get("raw_valid")),
                        "refresh_ready": True,
                    }
                )
                continue
        failed_boards.append(
            {
                "board_id": board.board_id if board else target.get("board_id", ""),
                "refresh_board_id": refresh_board_id,
                "name": board.name if board else target.get("name", ""),
                "raw_snapshot": raw_snapshot,
                "raw_exists": bool(target.get("raw_exists")),
                "raw_fresh": bool(target.get("raw_fresh")),
                "raw_valid": bool(target.get("raw_valid")),
                "refresh_ready": False,
                "raw_validation_errors": target.get("raw_validation_errors") or [],
            }
        )

    successful_by_refresh = {str(row.get("refresh_board_id") or row.get("board_id") or "") for row in successful_boards}
    failed_by_refresh = {str(row.get("refresh_board_id") or row.get("board_id") or "") for row in failed_boards}
    for failure in diagnostics.get("board_failures") or []:
        if not isinstance(failure, dict):
            continue
        refresh_board_id = str(failure.get("board_id") or "")
        if not refresh_board_id or refresh_board_id in failed_by_refresh:
            continue
        board = board_by_refresh_id.get(refresh_board_id)
        if refresh_board_id in successful_by_refresh:
            attempt_warnings.append(
                {
                    "board_id": board.board_id if board else refresh_board_id,
                    "refresh_board_id": refresh_board_id,
                    "name": board.name if board else refresh_board_id,
                    "outcome": "valid_staged_raw_kept_research_only",
                    "warning": public_tail(failure.get("error", ""), limit=300),
                }
            )
            continue
        failed_boards.append(
            {
                "board_id": board.board_id if board else refresh_board_id,
                "refresh_board_id": refresh_board_id,
                "name": board.name if board else refresh_board_id,
                "raw_snapshot": board.raw_snapshot if board else "",
                "raw_exists": False,
                "raw_fresh": False,
                "raw_valid": False,
                "refresh_ready": False,
                "raw_validation_errors": [public_tail(failure.get("error", ""), limit=300)],
            }
        )

    payload = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "refresh_id": refresh_id,
        "status": "partial_ready_research_only" if successful_boards else "blocked",
        "mode": "research_only_staged_raw_sidecar",
        "manifest": RAW_REFRESH_RESEARCH_ONLY_LATEST,
        "research_only_raw_dir": RAW_REFRESH_RESEARCH_ONLY_DIR,
        "full_publish_allowed": False,
        "executable_report_allowed": False,
        "execution_allowed": False,
        "current_executable_new_stake_aud": 0,
        "official_raw_promoted": False,
        "official_batch_manifest_written": False,
        "staged_safety_ready": bool(staged_safety.get("automation_safety_ready")),
        "staged_raw_ready": bool(staged_raw_gate.get("staged_raw_ready")),
        "required_target_count": int(staged_raw_gate.get("required_target_count") or 0),
        "ready_required_target_count": int(staged_raw_gate.get("ready_required_target_count") or len(successful_boards)),
        "successful_board_count": len(successful_boards),
        "failed_board_count": len(failed_boards),
        "attempt_warning_count": len(attempt_warnings),
        "successful_boards": successful_boards,
        "failed_boards": failed_boards,
        "attempt_warnings": attempt_warnings,
        "blocking_reasons": staged_raw_gate.get("blocking_reasons") or [],
        "source_diagnostics": "raw_refresh_diagnostics_latest.json",
        "truthfulness_note": (
            "该 sidecar 只保存 staged gate 已验证成功的板块供当日研究诊断；"
            "它不是正式 latest raw，不允许解锁新增下注或正式日报发布。"
        ),
    }
    atomic_write_json(manifest_path, sanitize_public_manifest(payload))
    safety = audit_public_artifact_safety([manifest_path, *copied_paths])
    payload["public_artifact_safety_ready"] = bool(safety.get("public_artifact_safety_ready"))
    payload["public_artifact_issue_count"] = int(safety.get("public_artifact_issue_count") or 0)
    if not payload["public_artifact_safety_ready"]:
        for copy_path in copied_paths:
            copy_path.unlink(missing_ok=True)
        payload["status"] = "blocked_public_safety"
        payload["successful_boards"] = []
        payload["successful_board_count"] = 0
        payload["ready_required_target_count"] = 0
        payload["public_artifact_issues"] = safety.get("public_artifact_issues") or []
    atomic_write_json(manifest_path, sanitize_public_manifest(payload))
    return sanitize_public_manifest(payload)


def safe_research_only_raw_name(refresh_id: str, refresh_board_id: str, raw_snapshot: str) -> str:
    prefix = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in f"{refresh_id}_{refresh_board_id}")
    return f"{prefix}_{public_artifact_name(raw_snapshot)}"


def record_refresh_attempt(run_id: str | None, diagnostics: Dict | None, attempt_diagnostic: Dict) -> None:
    if diagnostics is None or run_id is None:
        return
    if attempt_diagnostic.get("access_denied"):
        attempt_diagnostic["ai_controlled_access_rejected"] = True
        attempt_diagnostic["access_policy_status"] = "blocked_by_access_policy"
        attempt_diagnostic.setdefault("next_safe_action", public_raw_access_policy_next_action())
        diagnostics["access_policy_status"] = "blocked_by_access_policy"
        diagnostics["access_policy_blocker_code"] = "ai_controlled_access_rejected"
        diagnostics["automated_public_raw_refresh_allowed"] = False
        diagnostics["recommended_next_action"] = public_raw_access_policy_next_action()
    diagnostics.setdefault("attempts", []).append(attempt_diagnostic)
    diagnostics["status"] = "running"
    diagnostics["last_attempt"] = {
        "board_id": attempt_diagnostic.get("board_id"),
        "attempt": attempt_diagnostic.get("attempt"),
        "headed_fallback": bool(attempt_diagnostic.get("headed_fallback")),
        "exit_code": attempt_diagnostic.get("exit_code"),
        "access_denied": bool(attempt_diagnostic.get("access_denied")),
        "ai_controlled_access_rejected": bool(attempt_diagnostic.get("ai_controlled_access_rejected")),
    }
    heartbeat_raw_refresh_diagnostics(run_id, diagnostics)


def refresh_board_to_staging(
    board_id: str,
    staging: Path,
    attempts: int = 1,
    refresh_id: str | None = None,
    run_id: str | None = None,
    diagnostics: Dict | None = None,
) -> Dict:
    if board_id == "matches":
        return refresh_matches_board_to_staging(
            staging,
            attempts=attempts,
            refresh_id=refresh_id,
            run_id=run_id,
            diagnostics=diagnostics,
        )
    assert_node_ready()
    last_error = ""
    for attempt in range(1, attempts + 1):
        summary, last_error, attempt_diagnostic = run_refresh_attempt(board_id, staging, refresh_id, attempt, headed_fallback=False)
        record_refresh_attempt(run_id, diagnostics, attempt_diagnostic)
        if summary:
            return summary
        if attempt_diagnostic.get("access_denied"):
            break
    if looks_like_access_denied(last_error):
        raise RuntimeError(f"{board_id} refresh blocked: {access_policy_rejection_message(board_id)}")
    raise RuntimeError(f"{board_id} refresh failed after {attempts} attempt(s): {last_error}")


def refresh_matches_board_to_staging(
    staging: Path,
    attempts: int = 2,
    refresh_id: str | None = None,
    run_id: str | None = None,
    diagnostics: Dict | None = None,
) -> Dict:
    assert_node_ready()
    chunk_size = matches_refresh_chunk_size()
    match_targets = live_discovery_match_targets()
    target_count = len(match_targets) if match_targets else len(EXPECTED_MATCHES)
    match_target_env = (
        {"TAB_FIFA_MATCH_TARGETS_JSON": json.dumps(match_targets, ensure_ascii=False)}
        if match_targets
        else None
    )
    output_path = staging / MATCHES_BOARD.raw_snapshot
    merged_matches = []
    chunk_summaries = []
    attempt_index = 0
    last_error = ""
    chunk_attempts = max(attempts, 3)
    if diagnostics is not None:
        diagnostics["matches_target_source"] = "live_board_discovery" if match_targets else "configured_expected_matches"
        diagnostics["matches_target_count"] = target_count
        if run_id is not None:
            heartbeat_raw_refresh_diagnostics(run_id, diagnostics)
    for chunk_index, offset in enumerate(range(0, target_count, chunk_size), start=1):
        limit = min(chunk_size, target_count - offset)
        chunk_summary = None
        chunk_raw = None
        chunk_total_attempts = chunk_attempts
        for retry in range(1, chunk_attempts + 1):
            attempt_index += 1
            summary, last_error, attempt_diagnostic = run_refresh_attempt(
                "matches",
                staging,
                refresh_id,
                attempt_index,
                headed_fallback=False,
                extra_args=["--smoke", "--limit", str(limit), "--offset", str(offset)],
                extra_env=match_target_env,
            )
            attempt_diagnostic["chunk_index"] = chunk_index
            attempt_diagnostic["chunk_offset"] = offset
            attempt_diagnostic["chunk_limit"] = limit
            attempt_diagnostic["chunk_retry"] = retry
            attempt_diagnostic["match_target_source"] = "live_board_discovery" if match_targets else "configured_expected_matches"
            attempt_diagnostic["match_target_count"] = target_count
            if summary:
                chunk_raw = json.loads(output_path.read_text(encoding="utf-8"))
                quality_errors = matches_chunk_quality_errors(chunk_raw)
                attempt_diagnostic["chunk_quality_errors"] = quality_errors
                record_refresh_attempt(run_id, diagnostics, attempt_diagnostic)
                if not quality_errors:
                    chunk_summary = summary
                    break
                last_error = "; ".join(quality_errors)
            else:
                record_refresh_attempt(run_id, diagnostics, attempt_diagnostic)
            if attempt_diagnostic.get("access_denied"):
                break
        if not chunk_summary:
            if looks_like_access_denied(last_error):
                raise RuntimeError(f"matches chunk {offset}-{offset + limit - 1} blocked: {access_policy_rejection_message('matches')}")
            raise RuntimeError(f"matches chunk {offset}-{offset + limit - 1} failed after {chunk_total_attempts} attempt(s): {last_error}")
        merged_matches.extend(chunk_raw.get("matches", []))
        chunk_summaries.append(chunk_summary)
    repair_summaries = []
    merged_matches, repair_summaries, attempt_index = repair_merged_matches(
        merged_matches=merged_matches,
        staging=staging,
        refresh_id=refresh_id,
        run_id=run_id,
        diagnostics=diagnostics,
        attempt_index=attempt_index,
        match_targets=match_targets,
        match_target_env=match_target_env,
    )
    payload = {
        "generated_at": utc_now(),
        "source": "playwright_read_only_match_detail_chunked",
        "scope": "2026 World Cup Matches main markets",
        "count": len(merged_matches),
        "matches": merged_matches,
        "refresh_id": refresh_id,
        "target_source": "live_board_discovery" if match_targets else "configured_expected_matches",
        "available_match_count": target_count,
        "target_matches": [target["match"] for target in match_targets] if match_targets else list(EXPECTED_MATCHES),
    }
    atomic_write_json(output_path, payload)
    return {
        "generated_at": utc_now(),
        "refresh_id": refresh_id,
        "dry_run": False,
        "smoke": False,
        "headless": bool(chunk_summaries and chunk_summaries[0].get("headless")),
        "chunk_size": chunk_size,
        "chunk_count": len(chunk_summaries),
        "merged_repair_attempt_count": len(repair_summaries),
        "merged_repair_success_count": len([item for item in repair_summaries if item.get("repaired")]),
        "target_source": "live_board_discovery" if match_targets else "configured_expected_matches",
        "available_match_count": target_count,
        "boards": [
            {
                "board_id": "matches",
                "board": MATCHES_BOARD.name,
                "output": str(output_path),
            }
        ],
        "results": [
            {
                "board_id": "matches",
                "output": str(output_path),
                "text_length": 0,
                "match_count": len(merged_matches),
                "market_count": sum(len(match.get("markets", {})) for match in merged_matches),
                "error_count": sum(len(match.get("errors", [])) for match in merged_matches),
                "link_count": 0,
            }
        ],
    }


def repair_merged_matches(
    *,
    merged_matches: list[Dict],
    staging: Path,
    refresh_id: str | None,
    run_id: str | None,
    diagnostics: Dict | None,
    attempt_index: int,
    match_targets: list[Dict[str, str]],
    match_target_env: Dict[str, str] | None,
) -> tuple[list[Dict], list[Dict], int]:
    target_names = [target["match"] for target in match_targets] if match_targets else list(EXPECTED_MATCHES)
    repair_targets = merged_match_repair_targets(merged_matches, target_names)
    limit = matches_merged_repair_limit()
    if not repair_targets or limit <= 0:
        return order_merged_matches(merged_matches, target_names), [], attempt_index
    output_path = staging / MATCHES_BOARD.raw_snapshot
    by_match = {str(match.get("match") or ""): match for match in merged_matches if match.get("match")}
    summaries = []
    for repair_index, target in enumerate(repair_targets[:limit], start=1):
        attempt_index += 1
        summary, last_error, attempt_diagnostic = run_refresh_attempt(
            "matches",
            staging,
            refresh_id,
            attempt_index,
            headed_fallback=False,
            extra_args=["--match", target["match"]],
            extra_env=match_target_env,
        )
        attempt_diagnostic["repair_index"] = repair_index
        attempt_diagnostic["repair_match"] = target["match"]
        attempt_diagnostic["repair_reason"] = target["reason"]
        attempt_diagnostic["match_target_source"] = "live_board_discovery" if match_targets else "configured_expected_matches"
        attempt_diagnostic["match_target_count"] = len(target_names)
        repaired = False
        repair_quality_errors = []
        if summary and output_path.exists():
            repair_raw = json.loads(output_path.read_text(encoding="utf-8"))
            repair_quality_errors = merged_repair_quality_errors(repair_raw, target["match"])
            attempt_diagnostic["repair_quality_errors"] = repair_quality_errors
            if not repair_quality_errors:
                repaired_match = next(
                    (match for match in repair_raw.get("matches", []) if match.get("match") == target["match"]),
                    None,
                )
                if repaired_match:
                    by_match[target["match"]] = repaired_match
                    repaired = True
            elif not last_error:
                last_error = "; ".join(repair_quality_errors)
        else:
            attempt_diagnostic["repair_quality_errors"] = [last_error] if last_error else ["repair raw output missing"]
        attempt_diagnostic["repair_success"] = repaired
        record_refresh_attempt(run_id, diagnostics, attempt_diagnostic)
        summaries.append(
            {
                "match": target["match"],
                "reason": target["reason"],
                "repaired": repaired,
                "quality_errors": repair_quality_errors,
                "last_error": last_error,
            }
        )
    repaired_matches = order_merged_matches(list(by_match.values()), target_names)
    return repaired_matches, summaries, attempt_index


def merged_match_repair_targets(merged_matches: list[Dict], target_names: list[str]) -> list[Dict[str, str]]:
    by_match = {str(match.get("match") or ""): match for match in merged_matches if match.get("match")}
    targets = []
    for name in target_names:
        match = by_match.get(name)
        if not match:
            targets.append({"match": name, "reason": "missing_detail_match"})
            continue
        if match_is_in_play(match):
            continue
        if match.get("errors"):
            targets.append({"match": name, "reason": "market_expansion_errors"})
            continue
        if not has_full_core_markets(match):
            targets.append({"match": name, "reason": "partial_core_markets"})
    return targets


def merged_repair_quality_errors(raw: Dict, expected_match: str) -> list[str]:
    matches = [match for match in raw.get("matches", []) if match.get("match") == expected_match]
    if not matches:
        return [f"repair did not capture expected match: {expected_match}"]
    match = matches[0]
    if match.get("errors"):
        return [f"repair market expansion errors remain: {'; '.join(str(error) for error in match.get('errors', []))}"]
    if not has_full_core_markets(match):
        missing = [market for market in CORE_MAIN_MARKETS if not market_has_prices_for_repair(match, market)]
        return [f"repair partial core markets remain for {expected_match}: {', '.join(missing)}"]
    return []


def market_has_prices_for_repair(match: Dict, market_name: str) -> bool:
    from tab_research.pipeline import market_has_prices

    return market_has_prices(match, market_name)


def order_merged_matches(matches: list[Dict], target_names: list[str]) -> list[Dict]:
    by_match = {str(match.get("match") or ""): match for match in matches if match.get("match")}
    ordered = [by_match[name] for name in target_names if name in by_match]
    extras = [match for match in matches if match.get("match") not in set(target_names)]
    return ordered + extras


def matches_chunk_quality_errors(raw: Dict) -> list[str]:
    matches = raw.get("matches", [])
    market_errors = [
        f"{match.get('match')}: {'; '.join(str(error) for error in match.get('errors', []))}"
        for match in matches
        if match.get("errors")
    ]
    errors = []
    if market_errors:
        errors.append(f"chunk market expansion errors remain: {' | '.join(market_errors)}")
    return errors


def run_refresh_attempt(
    board_id: str,
    staging: Path,
    refresh_id: str | None,
    attempt: int,
    headed_fallback: bool = False,
    extra_args: list[str] | None = None,
    extra_env: Dict[str, str] | None = None,
) -> Tuple[Dict | None, str, Dict]:
    requested_headed_fallback = headed_fallback
    if headed_fallback:
        headed_fallback = False
    command = [
        str(NODE_BIN),
        str(RAW_REFRESH_SCRIPT),
        "--board",
        board_id,
        "--output-dir",
        str(staging),
        "--timeout-ms",
        "45000",
    ]
    if extra_args:
        command.extend(extra_args)
    if refresh_id:
        command.extend(["--refresh-id", refresh_id])
    env = os.environ.copy()
    env["TAB_FIFA_HEADLESS"] = "1"
    if extra_env:
        env.update(extra_env)
    env["TAB_FIFA_HEADLESS"] = "1"
    route_override = live_discovery_href_for_board(board_id)
    if route_override:
        env[f"TAB_FIFA_BOARD_URL_{board_id.upper()}"] = route_override
    try:
        completed = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parent,
            text=True,
            capture_output=True,
            timeout=refresh_process_timeout_seconds(board_id),
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = stream_text(getattr(exc, "stdout", None) or getattr(exc, "output", None))
        stderr = stream_text(getattr(exc, "stderr", None))
        timeout_seconds = exc.timeout or refresh_process_timeout_seconds(board_id)
        error = f"refresh command timed out after {timeout_seconds} seconds"
        access_denied = looks_like_access_denied(stderr) or looks_like_access_denied(stdout)
        diagnostic = {
            "board_id": board_id,
            "attempt": attempt,
            "headed_fallback": headed_fallback,
            "requested_headed_fallback": requested_headed_fallback,
            "headed_fallback_ignored_by_access_policy": bool(requested_headed_fallback),
            "exit_code": "timeout",
            "timeout": True,
            "timeout_seconds": timeout_seconds,
            "access_denied": access_denied,
            "stderr_tail": public_tail(stderr),
            "stdout_tail": public_tail(stdout),
            "error": error,
            "url_source": "live_discovery_matched_link" if route_override else "configured_default",
        }
        if access_denied:
            attach_access_policy_diagnostic(diagnostic, board_id)
        if route_override:
            diagnostic["route_override_host"] = route_host(route_override)
        return None, error, diagnostic
    access_denied = looks_like_access_denied(completed.stderr) or looks_like_access_denied(completed.stdout)
    diagnostic = {
        "board_id": board_id,
        "attempt": attempt,
        "headed_fallback": headed_fallback,
        "requested_headed_fallback": requested_headed_fallback,
        "headed_fallback_ignored_by_access_policy": bool(requested_headed_fallback),
        "exit_code": completed.returncode,
        "access_denied": access_denied,
        "stderr_tail": public_tail(completed.stderr),
        "stdout_tail": public_tail(completed.stdout),
        "url_source": "live_discovery_matched_link" if route_override else "configured_default",
    }
    if access_denied:
        attach_access_policy_diagnostic(diagnostic, board_id)
    if route_override:
        diagnostic["route_override_host"] = route_host(route_override)
    if completed.returncode == 0:
        try:
            summary = json.loads(completed.stdout)
        except json.JSONDecodeError:
            diagnostic["stdout_json"] = False
            diagnostic["error"] = "stdout was not valid JSON"
            return None, f"invalid JSON: {public_tail(completed.stdout, limit=500)}", diagnostic
        summary["attempt"] = attempt
        summary["headed_fallback"] = headed_fallback
        summary["requested_headed_fallback"] = requested_headed_fallback
        summary["headed_fallback_ignored_by_access_policy"] = bool(requested_headed_fallback)
        diagnostic["stdout_json"] = True
        diagnostic["summary"] = public_refresh_summary(summary)
        return summary, "", diagnostic
    last_error = public_tail(completed.stderr.strip() or completed.stdout.strip())
    diagnostic["error"] = last_error
    return None, last_error, diagnostic


def stream_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def live_discovery_href_for_board(board_id: str) -> str:
    payload = read_live_board_discovery_raw_payload()
    if not payload:
        return ""
    for row in payload.get("expected_boards") or []:
        if str(row.get("refresh_board_id") or "") != str(board_id):
            continue
        for link in row.get("matched_links") or []:
            href = str(link.get("href") or "").strip()
            if usable_tab_competition_href(href):
                return href
    return ""


def usable_tab_competition_href(href: str) -> bool:
    if not href.startswith("https://www.tab.com.au/sports/betting/Soccer/competitions/"):
        return False
    return "/matches/" not in href


def live_discovery_match_targets() -> list[Dict[str, str]]:
    payload = read_live_board_discovery_raw_payload()
    if not payload:
        return []
    targets: list[Dict[str, str]] = []
    seen = set()
    for row in payload.get("expected_boards") or []:
        if str(row.get("refresh_board_id") or "") != "matches":
            continue
        for link in row.get("matched_links") or []:
            href = str(link.get("href") or "").strip()
            label = str(link.get("text") or "").strip()
            if not usable_tab_match_href(href) or " v " not in label:
                continue
            key = (label, href)
            if key in seen:
                continue
            seen.add(key)
            targets.append({"match": label, "href": href})
    return targets


def usable_tab_match_href(href: str) -> bool:
    return href.startswith("https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches/matches/")


def route_host(href: str) -> str:
    return href.split("/sports/", 1)[0] if "/sports/" in href else href[:80]


def public_tail(text, limit: int = 700) -> str:
    sanitized = sanitize_public_manifest({"text": stream_text(text)}).get("text", "")
    return sanitized[-limit:]


def public_refresh_summary(summary: Dict) -> Dict:
    return {
        "generated_at": summary.get("generated_at"),
        "refresh_id": summary.get("refresh_id"),
        "dry_run": bool(summary.get("dry_run")),
        "smoke": bool(summary.get("smoke")),
        "headless": bool(summary.get("headless")),
        "attempt": summary.get("attempt"),
        "headed_fallback": bool(summary.get("headed_fallback")),
        "boards": [
            {
                "board_id": board.get("board_id"),
                "board": board.get("board"),
                "output": public_artifact_name(board.get("output")),
            }
            for board in summary.get("boards", [])
        ],
        "results": [public_refresh_result(item) for item in summary.get("results", [])],
    }


def public_refresh_result(item: Dict) -> Dict:
    return {
        "board_id": item.get("board_id"),
        "output": public_artifact_name(item.get("output")),
        "text_length": item.get("text_length"),
        "match_count": item.get("match_count"),
        "market_count": item.get("market_count"),
        "error_count": item.get("error_count"),
        "link_count": item.get("link_count"),
    }


def looks_like_access_denied(message: str) -> bool:
    return "access denied" in str(message or "").lower()


def should_try_headed_refresh_fallback() -> bool:
    return False


def access_policy_rejection_message(scope: str) -> str:
    return (
        f"{scope} received Access Denied from TAB; treating this as ai_controlled_access_rejected. "
        "Do not retry with headed fallback, CAPTCHA bypass, fingerprint spoofing, or stealth browser. "
        "Use an official/authorized data feed or user-authorized manual export/import instead."
    )


def attach_access_policy_diagnostic(diagnostic: Dict, scope: str) -> None:
    diagnostic["ai_controlled_access_rejected"] = True
    diagnostic["access_policy_status"] = "blocked_by_access_policy"
    diagnostic["blocker_code"] = "ai_controlled_access_rejected"
    diagnostic["forbidden_recovery"] = ["headed_fallback", "captcha_bypass", "fingerprint_spoofing", "stealth_browser"]
    diagnostic["next_safe_action"] = public_raw_access_policy_next_action()
    diagnostic["error_class"] = "ai_controlled_access_rejected"


def assert_node_ready() -> None:
    if not NODE_BIN.exists():
        raise RuntimeError(f"TAB_FIFA_NODE_BIN does not exist: {NODE_BIN}")
    if not os.access(NODE_BIN, os.X_OK):
        raise RuntimeError(f"TAB_FIFA_NODE_BIN is not executable: {NODE_BIN}")


def assert_pre_pdf_gates(board_gates: Dict[str, Dict], raw_refresh: Dict, portfolio: Dict, safety: Dict) -> None:
    failures = []
    for board_id, gate in board_gates.items():
        if not gate.get("automation_ready"):
            reasons = "; ".join(gate.get("blocking_reasons", [])) or "automation gate is false"
            failures.append(f"{board_id}: {reasons}")
    if not raw_refresh.get("raw_refresh_ready"):
        failures.append("raw_refresh: " + ("; ".join(raw_refresh.get("blocking_reasons", [])) or "raw refresh gate is false"))
    if not portfolio.get("portfolio_automation_ready"):
        failures.append("portfolio: " + ("; ".join(portfolio.get("blocking_reasons", [])) or "portfolio gate is false"))
    if not safety.get("automation_safety_ready"):
        failures.append("safety: " + ("; ".join(safety.get("blocking_reasons", [])) or "safety gate is false"))
    if failures:
        raise GateFailure("pre-PDF gates failed; refusing to publish report: " + " | ".join(failures))


def write_failed_preflight(run_id: str, exc: Exception, publish_latest: bool = False) -> Path:
    path = preflight_run_path(run_id)
    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
    payload = {
        **existing,
        "technical_preflight_ready": False,
        "automation_entry_ready": False,
        "user_automation_authorized": USER_AUTOMATION_AUTHORIZED,
        "automation_authorization": AUTOMATION_AUTHORIZATION.to_public_dict(),
        "run_id": run_id,
        "failed_at": utc_now(),
        "failure_type": type(exc).__name__,
    }
    payload["blocking_reasons"] = list(dict.fromkeys([*(existing.get("blocking_reasons") or []), str(exc)]))
    atomic_write_json(
        path,
        sanitize_public_manifest(payload),
    )
    if publish_latest:
        atomic_write_json(PREFLIGHT_PATH, sanitize_public_manifest(payload))
    return path


def publish_failed_readiness_sidecars(
    manifest: Dict,
    command_status: Dict,
    failed_preflight_path: Path | None = None,
) -> Dict:
    readiness = write_automation_readiness_summary(
        OUT,
        AUTOMATION_READINESS_PATH,
        command_status=command_status,
    )
    write_automation_readiness_report(
        OUT,
        AUTOMATION_READINESS_REPORT_PATH,
        summary=readiness,
    )
    write_automation_readiness_pdf(
        OUT,
        AUTOMATION_READINESS_PDF_PATH,
        summary=readiness,
    )
    readiness_safety = audit_public_artifact_safety(
        [AUTOMATION_READINESS_PATH, AUTOMATION_READINESS_REPORT_PATH, AUTOMATION_READINESS_PDF_PATH]
    )
    manifest.setdefault("outputs", {})
    manifest["outputs"]["automation_readiness"] = str(AUTOMATION_READINESS_PATH)
    manifest["outputs"]["automation_readiness_report"] = str(AUTOMATION_READINESS_REPORT_PATH)
    manifest["outputs"]["automation_readiness_pdf"] = str(AUTOMATION_READINESS_PDF_PATH)
    manifest["outputs"]["automation_readiness_summary"] = {
        "status": readiness.get("status", ""),
        "formal_report_publish_ready": bool(readiness.get("formal_report_publish_ready")),
        "recurring_automation_ready": bool(readiness.get("recurring_automation_ready")),
        "blocker_count": len(readiness.get("blockers", [])),
    }
    manifest["outputs"]["automation_readiness_safety"] = readiness_safety
    if failed_preflight_path is not None:
        manifest["outputs"]["automation_preflight"] = str(failed_preflight_path)
        manifest["outputs"]["automation_preflight_latest"] = str(PREFLIGHT_PATH)
    return {
        "readiness": readiness,
        "safety": readiness_safety,
    }


if __name__ == "__main__":
    main()
