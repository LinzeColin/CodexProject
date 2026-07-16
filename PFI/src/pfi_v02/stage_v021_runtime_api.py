from __future__ import annotations

import base64
import csv
import hmac
import hashlib
import importlib.metadata
import json
import os
import re
import secrets
import threading
from dataclasses import replace
from datetime import date, timedelta
from email.utils import formatdate, parsedate_to_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from pfi_os.application.jobs import JobLifecycleError, JobTransitionError, StaleRevisionError
from pfi_os.application.operational_store import default_data_home, default_operational_db_path
from pfi_os.application.read_model_status import (
    build_v024_read_model_status as _ORIGINAL_BUILD_V024_READ_MODEL_STATUS,
)
from pfi_os.application.supervisor import RuntimeJobSupervisor
from pfi_v02.local_imports import write_private_alipay_import
from pfi_v02.stage_v021_holdings_persistence import (
    V021HoldingsPersistenceService,
    V021HoldingSnapshot,
)
from pfi_os.application.read_models.unified import build_current_unified_read_model
from pfi_os.application.use_cases.import_review_ledger import (
    ImportReviewLedgerService,
    ImportWorkflowError,
    MAX_UPLOAD_BYTES,
    UploadedImportFile,
)
from pfi_os.application.use_cases.holding_settings_persistence import (
    DEFAULT_SETTINGS,
    HoldingSettingsPersistenceService,
    HoldingSettingsWorkflowError,
)
from pfi_os.application.use_cases.metric_lineage_drilldown import (
    build_stage7_phase73_payload,
)
from pfi_v02.runtime_diff_v025 import (
    DEPENDENCY_DOMAINS,
    build_dependency_snapshot,
)


V021_RUNTIME_API_SCHEMA = "PFIV021RuntimeAPIV1"
DEFAULT_RUNTIME_API_HOST = "127.0.0.1"
DEFAULT_RUNTIME_API_PORT = 8766
RUNTIME_AUTH_HEADER = "X-PFI-Runtime-Token"
MAX_RUNTIME_REQUEST_BYTES = 140 * 1024 * 1024
MAX_UPLOAD_FILE_COUNT = 20
MAX_UPLOAD_TOTAL_BYTES = 100 * 1024 * 1024
V025_RELEASE_MANIFEST_PATH = Path(__file__).resolve().parents[2] / "config" / "release_manifest.json"
V025_RELEASE_MANIFEST_REQUIRED_FIELDS = (
    "product",
    "version",
    "build_id",
    "git_commit",
    "frontend_bundle_hash",
    "backend_build_hash",
    "generated_at",
)
V025_RELEASE_CACHE_POLICY_SCHEMA = "PFIV025Stage1ReleaseCachePolicyV1"
V025_STREAMLIT_CACHE_TTL_SECONDS = 30
V025_CACHE_DIMENSION_FIELDS = (
    "build_id",
    "git_commit",
    "frontend_bundle_hash",
    "backend_build_hash",
    "data_hash",
    "parameter_hash",
    "formula_hash",
    "fx_snapshot_id",
    "fx_snapshot_hash",
    "read_model_hash",
    "streamlit_version",
    "requirements_lock_hash",
)
V025_BACKEND_BUILD_RELATIVE_PATHS = (
    "StartPFI.command",
    "config/data_domains/stage11_distribution_boundaries.json",
    "config/jobs/v025_dependency_registry.json",
    "macos/PFI_launcher.c",
    "scripts/pfiReleaseIdentity.sh",
    "scripts/pfiRuntime.sh",
    "scripts/v025/pfi_context_export.py",
    "scripts/v025/pfi_operational_backup_restore.py",
    "scripts/v025/release_cache_contract.py",
    "scripts/v025/run_streamlit_with_release_cache.py",
    "scripts/v025/scan_stage11_distribution_boundaries.py",
    "scripts/v025/stage1_phase13_candidate_env.sh",
    "scripts/v025/stage11_readonly_backup_rehearsal.py",
    "shared/context/pfi_context_v1.schema.json",
    "src/pfi_os/app/streamlit_app.py",
    "src/pfi_os/application/homepage_summary.py",
    "src/pfi_os/application/jobs/__init__.py",
    "src/pfi_os/application/jobs/lifecycle.py",
    "src/pfi_os/application/operational_store.py",
    "src/pfi_os/application/read_model_status.py",
    "src/pfi_os/application/supervisor/__init__.py",
    "src/pfi_os/application/supervisor/runtime_jobs.py",
    "src/pfi_os/application/use_cases/__init__.py",
    "src/pfi_os/application/use_cases/holding_settings_persistence.py",
    "src/pfi_os/application/use_cases/import_review_ledger.py",
    "src/pfi_os/application/use_cases/metric_lineage_drilldown.py",
    "src/pfi_os/infrastructure/__init__.py",
    "src/pfi_os/infrastructure/jobs/__init__.py",
    "src/pfi_os/infrastructure/jobs/sqlite_store.py",
    "src/pfi_os/infrastructure/operational_holding_settings_store.py",
    "src/pfi_os/infrastructure/operational_import_store.py",
    "src/pfi_os/infrastructure/operational_store_backup.py",
    "src/pfi_os/infrastructure/operational_store_runtime.py",
    "src/pfi_os/migrations/v025_stage7_holding_idempotency.sql",
    "src/pfi_os/migrations/v025_stage7_holding_settings.sql",
    "src/pfi_os/migrations/v025_stage7_import_review_ledger.sql",
    "src/pfi_os/observability/__init__.py",
    "src/pfi_os/observability/job_trace.py",
    "src/pfi_os/security/__init__.py",
    "src/pfi_os/security/pfi_context_export.py",
    "src/pfi_os/system/shutdown_monitor.py",
    "src/pfi_v02/runtime_diff_v025.py",
    "src/pfi_v02/stage5_advice_report_alpha.py",
    "src/pfi_v02/stage6_e2e_stabilization.py",
    "src/pfi_v02/stage_v021_runtime_api.py",
    "src/pfi_v02/stage_v024_stage2_entry_consistency.py",
)
_V025_FRONTEND_MANIFEST_PATTERN = re.compile(
    r'(<script\s+type="application/json"\s+id="pfi-release-manifest">).*?(</script>)',
    re.DOTALL,
)
_V025_SCRIPT_REF_PATTERN = re.compile(r'<script\s+src="\./([^"?#]+)"')
_V025_HEX64_PATTERN = re.compile(r"^[0-9a-f]{64}$")
FX_TO_CNY = {
    "CNY": 1.0,
    "AUD": 4.6874,
    "USD": 1.52 * 4.6874,
    "HKD": 0.195 * 4.6874,
}

_SERVER_LOCK = threading.Lock()
_SERVER_STATE: dict[str, Any] = {}


def build_v025_backend_build_identity(
    project_root: Path | str | None = None,
) -> dict[str, Any]:
    """Hash the release-critical identity/cache entry closure used by Stage 1."""

    root = (
        Path(project_root).expanduser().resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[2]
    )
    repo_root = root.parent
    records: list[bytes] = []
    files: list[str] = []
    mtimes: list[int] = []
    for relative in V025_BACKEND_BUILD_RELATIVE_PATHS:
        path = root / relative
        if not path.is_file():
            raise ValueError("release backend source is unavailable")
        repo_relative = path.relative_to(repo_root).as_posix()
        payload_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append(repo_relative)
        records.append(f"{repo_relative}\0{payload_hash}\n".encode("utf-8"))
        mtimes.append(int(path.stat().st_mtime))
    return {
        "sha256": hashlib.sha256(b"".join(records)).hexdigest(),
        "files": files,
        "file_count": len(files),
        "latest_mtime": max(mtimes),
    }


_V025_RUNNING_BACKEND_IDENTITY = build_v025_backend_build_identity()
V025_RUNNING_BACKEND_SHA256 = str(_V025_RUNNING_BACKEND_IDENTITY["sha256"])
V025_RUNTIME_SOURCE_MTIME = int(_V025_RUNNING_BACKEND_IDENTITY["latest_mtime"])


def _canonical_json_sha256(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_v025_stage1_candidate_read_model_status() -> dict[str, Any]:
    """Return a path-free empty status for the official isolated candidate."""

    metric_ids = (
        "net_worth_cny",
        "cash_balance_cny",
        "investment_market_value_cny",
        "consumption_outflow_cny",
        "report_summary_status",
    )
    metrics = [
        {
            "metric_id": metric_id,
            "value": None,
            "currency": None,
            "status": "not_loaded",
            "source_id": None,
            "record_count": None,
            "as_of": None,
            "formula_id": None,
            "confidence": None,
            "blocking_reason_zh": "隔离验收未读取财务数据",
            "calculation_state": "not_evaluated",
        }
        for metric_id in metric_ids
    ]
    semantic_state = {
        "contract_version": "PFI-V025-STAGE1-OFFICIAL-UI-ISOLATED-EMPTY",
        "source": {
            "type": "isolated_candidate",
            "status": "not_loaded",
            "storage_mode": "isolated_empty",
            "record_count": 0,
            "raw_file_count": 0,
            "as_of": None,
            "evidence_hash": None,
            "blocking_reason_zh": "隔离验收未读取财务数据",
        },
        "metrics": metrics,
    }
    return {
        "schema": "PFIV024Stage4ReadModelStatusV1",
        "isolated_candidate": True,
        "target_version": "v0.2.5",
        "stage": "Stage 1",
        "phase_id": "Phase 1.3 whole-review remediation",
        "contract_version": semantic_state["contract_version"],
        "source": semantic_state["source"],
        "as_of": None,
        "read_model_hash": _canonical_json_sha256(semantic_state),
        "core_metric_states": metrics,
        "blocked_metric_ids": list(metric_ids),
        "surface_ids": ["home", "accounts", "investment", "consumption", "insights"],
        "generated_at_utc": "",
    }


def build_v025_stage1_candidate_holdings_payload() -> dict[str, Any]:
    """Return the official holdings API shape without opening any canonical store."""

    return {
        "schema": V021_RUNTIME_API_SCHEMA,
        "rows": [],
        "summary": {
            "storage_mode": "isolated_empty",
            "db_path": None,
            "snapshot_count": 0,
            "adjustment_count": 0,
            "tables": [],
        },
    }


def build_v025_stage1_candidate_sync_read_model() -> dict[str, Any]:
    """Return a path-free, null-valued sync model for the isolated candidate."""

    return {
        "schema": "PFIV0211Stage4HoldingsSyncReadModelV1",
        "source": "isolated empty candidate",
        "sqlite": {
            "db_path": None,
            "snapshot_count": 0,
            "adjustment_count": 0,
            "tables": [],
        },
        "home": {
            "net_worth_cny": None,
            "cash_cny": None,
            "investment_market_value_cny": None,
            "holding_count": 0,
        },
        "investment": {
            "market_value_cny": None,
            "cost_basis_cny": None,
            "total_return_cny": None,
            "unrealized_pnl_cny": None,
            "cash_position_cny": None,
            "holding_count": 0,
        },
        "report": {
            "title": "持仓同步报告",
            "holding_count": 0,
            "market_value_cny": None,
            "cost_basis_cny": None,
            "unrealized_pnl_cny": None,
            "adjustment_count": 0,
            "empty_state": "隔离验收未读取持仓数据。",
            "rows": [],
        },
        "consistency": {
            "home_investment_report_market_value_same": True,
            "read_model_schema": "PFIV021OperationalReadModelV1",
            "report_schema": "PFIV0211Stage4HoldingsReportV1",
        },
    }


def _candidate_empty_trend(scope: str, title: str) -> dict[str, Any]:
    return {
        "scope": scope,
        "title": title,
        "unit": "CNY",
        "source": "isolated empty candidate",
        "emptyState": "隔离验收未读取财务数据。",
        "periods": [],
        "series": [],
    }


def build_v025_stage1_candidate_trends() -> dict[str, Any]:
    """Return the production trends API shape without reading MetaDatabase or SQLite."""

    read_model = {
        "schema": "PFIV021OperationalReadModelV1",
        "accounts": {
            "cash_cny": None,
            "net_worth_cny": None,
            "total_assets_cny": None,
            "total_liabilities_cny": None,
        },
        "investment": {
            "market_value_cny": None,
            "cost_basis_cny": None,
            "total_return_cny": None,
            "unrealized_pnl_cny": None,
            "cash_position_cny": None,
            "holding_count": 0,
            "adjustment_count": 0,
        },
        "consumption": {
            "has_real_transactions": False,
            "empty_state": "隔离验收未读取交易数据。",
        },
    }
    trends = {
        "accounts": _candidate_empty_trend("账户与资产", "账户趋势"),
        "investment": _candidate_empty_trend("投资管理", "投资趋势"),
        "consumption": _candidate_empty_trend("消费管理", "消费趋势"),
    }
    return {
        "schema": "PFIV021OperationalTrendReadModelV1",
        "readModel": read_model,
        "trends": trends,
        **trends,
    }


def _v025_candidate_data_headers(read_model_status: dict[str, Any]) -> dict[str, str]:
    return {
        "X-PFI-Running-Backend-SHA256": V025_RUNNING_BACKEND_SHA256,
        "X-PFI-Read-Model-SHA256": str(read_model_status.get("read_model_hash") or ""),
        "X-PFI-Data-Boundary": "isolated-empty-read-only",
    }


def stable_v025_read_model_hash(read_model_status: dict[str, Any]) -> str:
    """Hash semantic read-model state without timestamps or private paths."""

    if not isinstance(read_model_status, dict):
        raise ValueError("read model status must be an object")
    declared = str(read_model_status.get("read_model_hash") or "")
    declared_digest = declared.removeprefix("sha256:")
    if (
        read_model_status.get("schema") == "PFIV025UnifiedReadModelV1"
        and _V025_HEX64_PATTERN.fullmatch(declared_digest)
    ):
        return declared_digest
    source = read_model_status.get("source") if isinstance(read_model_status.get("source"), dict) else {}
    source_projection = {
        field: source.get(field)
        for field in (
            "status",
            "evidence_hash",
            "as_of",
            "record_count",
            "raw_file_count",
            "date_range",
        )
    }
    metric_fields = (
        "metric_id",
        "status",
        "currency",
        "record_count",
        "as_of",
        "formula_id",
        "confidence",
        "blocking_reason_zh",
        "calculation_state",
    )
    raw_metrics = read_model_status.get("core_metric_states")
    metrics = [
        {field: metric.get(field) for field in metric_fields}
        for metric in (raw_metrics if isinstance(raw_metrics, list) else [])
        if isinstance(metric, dict)
    ]
    metrics.sort(key=lambda item: str(item.get("metric_id") or ""))
    projection = {
        "schema": read_model_status.get("schema"),
        "contract_version": read_model_status.get("contract_version"),
        "source": source_projection,
        "core_metric_states": metrics,
        "blocked_metric_ids": sorted(str(item) for item in (read_model_status.get("blocked_metric_ids") or [])),
        "surface_ids": sorted(str(item) for item in (read_model_status.get("surface_ids") or [])),
    }
    return _canonical_json_sha256(projection)


def compute_v025_streamlit_cache_key(dimensions: dict[str, Any]) -> str:
    if not isinstance(dimensions, dict):
        raise ValueError("cache dimensions must be an object")
    normalized: dict[str, str] = {}
    for field in V025_CACHE_DIMENSION_FIELDS:
        value = dimensions.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"cache dimension {field} is required")
        normalized[field] = value
    return _canonical_json_sha256(normalized)


def build_v025_release_cache_policy_record(
    dimensions: dict[str, Any],
    *,
    process_cache_key: str | None,
    running_backend_hash: str,
    asset_identity_valid: bool,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = {field: str(dimensions.get(field) or "") for field in V025_CACHE_DIMENSION_FIELDS}
    expected_key = compute_v025_streamlit_cache_key(normalized)
    process_key = str(process_cache_key or "")
    dependency_fields: dict[str, Any] = {}
    dependency_valid = True
    if dependency_snapshot is not None:
        hashes = (
            dependency_snapshot.get("hashes")
            if isinstance(dependency_snapshot.get("hashes"), dict)
            else {}
        )
        observations = (
            dependency_snapshot.get("observations")
            if isinstance(dependency_snapshot.get("observations"), dict)
            else {}
        )
        snapshot_hash = str(dependency_snapshot.get("snapshot_hash") or "")
        registry_hash = str(dependency_snapshot.get("registry_sha256") or "")
        normalized_hashes = {
            domain_id: str(hashes.get(domain_id) or "") for domain_id in DEPENDENCY_DOMAINS
        }
        dependency_valid = bool(
            _V025_HEX64_PATTERN.fullmatch(snapshot_hash)
            and _V025_HEX64_PATTERN.fullmatch(registry_hash)
            and all(_V025_HEX64_PATTERN.fullmatch(value) for value in normalized_hashes.values())
            and snapshot_hash == normalized["data_hash"]
            and normalized_hashes["parameter"] == normalized["parameter_hash"]
            and normalized_hashes["formula"] == normalized["formula_hash"]
            and normalized_hashes["fx"] == normalized["fx_snapshot_hash"]
            and normalized_hashes["read_model"] == normalized["read_model_hash"]
            and dependency_snapshot.get("contains_private_values") is False
            and dependency_snapshot.get("financial_values_emitted") == 0
            and dependency_snapshot.get("network_calls") == 0
        )
        dependency_fields = {
            "dependency_registry_sha256": registry_hash,
            "dependency_snapshot_hash": snapshot_hash,
            "dependency_hashes": normalized_hashes,
            "dependency_statuses": {
                domain_id: str(
                    observations.get(domain_id, {}).get("status")
                    if isinstance(observations.get(domain_id), dict)
                    else ""
                )
                for domain_id in DEPENDENCY_DOMAINS
            },
            "frontend_cache_key": expected_key,
            "ordinary_run_network_allowed": False,
            "no_diff_network_allowed": False,
            "no_diff_recompute_scope": "none",
            "no_diff_codex_allowed": False,
            "no_diff_llm_allowed": False,
            "dependency_snapshot_valid": dependency_valid,
        }
    return {
        "schema": V025_RELEASE_CACHE_POLICY_SCHEMA,
        **normalized,
        **dependency_fields,
        "streamlit_cache_key": expected_key,
        "process_cache_key": process_key,
        "ttl_seconds": V025_STREAMLIT_CACHE_TTL_SECONDS,
        "cache_mode": "streamlit_cache_data_composite_key_v1",
        "persistent": False,
        "invalidation": list(V025_CACHE_DIMENSION_FIELDS),
        "running_backend_hash": str(running_backend_hash or ""),
        "asset_identity_valid": bool(asset_identity_valid),
        "valid": bool(
            _V025_HEX64_PATTERN.fullmatch(process_key)
            and process_key == expected_key
            and running_backend_hash == normalized["backend_build_hash"]
            and asset_identity_valid
            and dependency_valid
        ),
    }


def _v025_project_root(project_root: Path | str | None = None) -> Path:
    return Path(project_root).expanduser().resolve() if project_root is not None else Path(__file__).resolve().parents[2]


def build_v025_stage4_read_model_status(
    project_root: Path | str | None = None,
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Build the tracked aggregate-only Phase 4.3 unified snapshot."""

    root = _v025_project_root(project_root)
    return build_current_unified_read_model(root.parent, observed_at=observed_at)


def _v025_frontend_bundle_hash(project_root: Path) -> tuple[str, list[str]]:
    index_path = project_root / "web" / "index.html"
    source = index_path.read_text(encoding="utf-8")
    canonical_index, count = _V025_FRONTEND_MANIFEST_PATTERN.subn(r"\1{}\2", source, count=1)
    if count != 1:
        raise ValueError("release manifest block is not canonicalizable")
    paths = {
        index_path,
        project_root / "web" / "styles" / "tokens.css",
        project_root / "web" / "styles.css",
        *(project_root / "web" / ref for ref in _V025_SCRIPT_REF_PATTERN.findall(source)),
    }
    repo_root = project_root.parent
    records: list[bytes] = []
    relative_paths: list[str] = []
    for path in sorted(paths, key=lambda item: item.relative_to(repo_root).as_posix()):
        if not path.is_file():
            raise ValueError("release frontend source is unavailable")
        payload = canonical_index.encode("utf-8") if path == index_path else path.read_bytes()
        relative = path.relative_to(repo_root).as_posix()
        relative_paths.append(relative)
        records.append(f"{relative}\0{hashlib.sha256(payload).hexdigest()}\n".encode("utf-8"))
    return hashlib.sha256(b"".join(records)).hexdigest(), relative_paths


def build_v025_release_asset_identity(
    project_root: Path | str | None = None,
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = _v025_project_root(project_root)
    release_manifest = dict(manifest) if isinstance(manifest, dict) else load_v025_release_manifest(
        manifest_path=root / "config" / "release_manifest.json"
    )
    frontend_hash, frontend_files = _v025_frontend_bundle_hash(root)
    backend_identity = build_v025_backend_build_identity(root)
    disk_backend_hash = str(backend_identity["sha256"])
    manifest_frontend_hash = str(release_manifest.get("frontend_bundle_hash") or "")
    manifest_backend_hash = str(release_manifest.get("backend_build_hash") or "")
    frontend_valid = frontend_hash == manifest_frontend_hash
    disk_backend_valid = disk_backend_hash == manifest_backend_hash
    running_backend_valid = V025_RUNNING_BACKEND_SHA256 == manifest_backend_hash
    return {
        "frontend_bundle_hash": frontend_hash,
        "manifest_frontend_bundle_hash": manifest_frontend_hash,
        "backend_build_hash": disk_backend_hash,
        "manifest_backend_build_hash": manifest_backend_hash,
        "running_backend_hash": V025_RUNNING_BACKEND_SHA256,
        "frontend_file_count": len(frontend_files),
        "backend_files": list(backend_identity["files"]),
        "backend_file_count": int(backend_identity["file_count"]),
        "frontend_valid": frontend_valid,
        "disk_backend_valid": disk_backend_valid,
        "running_backend_valid": running_backend_valid,
        "valid": frontend_valid and disk_backend_valid and running_backend_valid,
    }


def _normalized_data_hash(read_model_status: dict[str, Any]) -> str:
    dependencies = (
        read_model_status.get("dependency_hashes")
        if isinstance(read_model_status.get("dependency_hashes"), dict)
        else {}
    )
    dependency_candidate = str(dependencies.get("stage2_source_manifest") or "").removeprefix(
        "sha256:"
    )
    if _V025_HEX64_PATTERN.fullmatch(dependency_candidate):
        return dependency_candidate
    source = read_model_status.get("source") if isinstance(read_model_status.get("source"), dict) else {}
    candidate = str(source.get("evidence_hash") or "").removeprefix("sha256:")
    if _V025_HEX64_PATTERN.fullmatch(candidate):
        return candidate
    return _canonical_json_sha256(
        {
            "status": source.get("status"),
            "as_of": source.get("as_of"),
            "record_count": source.get("record_count"),
            "raw_file_count": source.get("raw_file_count"),
        }
    )


def _latest_v025_fx_snapshot(project_root: Path) -> tuple[str, str]:
    candidates: list[tuple[str, str, Path, dict[str, Any]]] = []
    for path in project_root.glob("data/fx_snapshots/*/*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        snapshot_id = str(payload.get("snapshot_id") or "")
        if not snapshot_id:
            continue
        candidates.append((str(payload.get("effective_date") or ""), snapshot_id, path, payload))
    if not candidates:
        return "fx_snapshot_missing", _canonical_json_sha256({"state": "missing"})
    _effective_date, snapshot_id, path, _payload = max(candidates, key=lambda item: (item[0], item[1], item[2].as_posix()))
    return snapshot_id, hashlib.sha256(path.read_bytes()).hexdigest()


def build_v025_release_cache_context(
    project_root: Path | str | None = None,
    *,
    read_model_status: dict[str, Any] | None = None,
    db_path: Path | str | None = None,
    streamlit_version: str | None = None,
) -> dict[str, Any]:
    root = _v025_project_root(project_root)
    manifest = load_v025_release_manifest(manifest_path=root / "config" / "release_manifest.json")
    candidate_mode = os.environ.get("PFI_STAGE1_CANDIDATE_MODE") == "1"
    if isinstance(read_model_status, dict):
        status = dict(read_model_status)
        resolved_db_path = Path(db_path).expanduser() if db_path is not None else None
    elif candidate_mode:
        status = build_v025_stage1_candidate_read_model_status()
        resolved_db_path = None
    else:
        status = None
        resolved_db_path = (
            Path(db_path).expanduser()
            if db_path is not None
            else default_data_home() / "private" / "operational" / "pfi.sqlite"
        )
    dependency_snapshot = build_dependency_snapshot(
        root,
        read_model_status=status,
        db_path=resolved_db_path,
        isolated_candidate=candidate_mode,
    )
    dependency_hashes = dependency_snapshot["hashes"]
    fx_observation = dependency_snapshot["observations"]["fx"]
    if candidate_mode:
        fx_snapshot_id = "candidate_fx_not_loaded"
    else:
        fx_snapshot_id = str(fx_observation.get("snapshot_id") or "fx_snapshot_missing")
    resolved_streamlit_version = streamlit_version or importlib.metadata.version("streamlit")
    dimensions = {
        "build_id": str(manifest.get("build_id") or ""),
        "git_commit": str(manifest.get("git_commit") or ""),
        "frontend_bundle_hash": str(manifest.get("frontend_bundle_hash") or ""),
        "backend_build_hash": str(manifest.get("backend_build_hash") or ""),
        "data_hash": str(dependency_snapshot["snapshot_hash"]),
        "parameter_hash": str(dependency_hashes["parameter"]),
        "formula_hash": str(dependency_hashes["formula"]),
        "fx_snapshot_id": fx_snapshot_id,
        "fx_snapshot_hash": str(dependency_hashes["fx"]),
        "read_model_hash": str(dependency_hashes["read_model"]),
        "streamlit_version": str(resolved_streamlit_version),
        "requirements_lock_hash": hashlib.sha256((root / "requirements.lock").read_bytes()).hexdigest(),
    }
    return {
        "dimensions": dimensions,
        "dependency_snapshot": dependency_snapshot,
        "read_model_status": status,
        "db_observation_mode": "isolated_candidate"
        if candidate_mode
        else "explicit_status_projection"
        if resolved_db_path is None
        else "sqlite_read_only_hash_projection",
    }


def build_v025_release_cache_dimensions(
    project_root: Path | str | None = None,
    *,
    read_model_status: dict[str, Any] | None = None,
    db_path: Path | str | None = None,
    streamlit_version: str | None = None,
) -> dict[str, str]:
    context = build_v025_release_cache_context(
        project_root,
        read_model_status=read_model_status,
        db_path=db_path,
        streamlit_version=streamlit_version,
    )
    return dict(context["dimensions"])


def build_v025_release_cache_policy(
    project_root: Path | str | None = None,
    *,
    read_model_status: dict[str, Any] | None = None,
    db_path: Path | str | None = None,
    process_cache_key: str | None = None,
    streamlit_version: str | None = None,
) -> dict[str, Any]:
    root = _v025_project_root(project_root)
    manifest = load_v025_release_manifest(manifest_path=root / "config" / "release_manifest.json")
    context = build_v025_release_cache_context(
        root,
        read_model_status=read_model_status,
        db_path=db_path,
        streamlit_version=streamlit_version,
    )
    dimensions = context["dimensions"]
    asset_identity = build_v025_release_asset_identity(root, manifest=manifest)
    return build_v025_release_cache_policy_record(
        dimensions,
        process_cache_key=process_cache_key if process_cache_key is not None else os.environ.get("PFI_STREAMLIT_CACHE_KEY"),
        running_backend_hash=V025_RUNNING_BACKEND_SHA256,
        asset_identity_valid=bool(asset_identity["valid"]),
        dependency_snapshot=context["dependency_snapshot"],
    )


def load_v025_release_manifest_record(
    *, manifest_path: Path | str | None = None
) -> tuple[dict[str, Any], bytes, str]:
    """Load the public release identity and raw-file hash without financial state."""
    path = Path(manifest_path).expanduser() if manifest_path is not None else V025_RELEASE_MANIFEST_PATH
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("release manifest is unavailable or invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("release manifest must be a JSON object")
    missing = [field for field in V025_RELEASE_MANIFEST_REQUIRED_FIELDS if not payload.get(field)]
    if missing:
        raise ValueError(f"release manifest missing required fields: {', '.join(missing)}")
    if payload.get("product") != "PFI":
        raise ValueError("release manifest product must be PFI")
    return dict(payload), raw, hashlib.sha256(raw).hexdigest()


def load_v025_release_manifest(*, manifest_path: Path | str | None = None) -> dict[str, Any]:
    """Load the public release identity without touching financial state."""

    manifest, _raw, _manifest_sha256 = load_v025_release_manifest_record(
        manifest_path=manifest_path
    )
    return manifest


def load_v021_holdings_payload(*, db_path: Path | str | None = None) -> dict[str, Any]:
    service = V021HoldingsPersistenceService(db_path)
    rows = [_snapshot_to_frontend(row) for row in service.list_snapshots(include_deleted=True)]
    return {
        "schema": V021_RUNTIME_API_SCHEMA,
        "rows": rows,
        "summary": service.persistence_summary(),
    }


def save_v021_holdings_payload(payload: dict[str, Any], *, db_path: Path | str | None = None) -> dict[str, Any]:
    service = V021HoldingsPersistenceService(db_path)
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")

    for raw_row in rows:
        snapshot = _snapshot_from_frontend(raw_row)
        existing = service.get_snapshot(snapshot.snapshot_id)
        if snapshot.soft_deleted:
            if existing is not None and not existing.soft_deleted:
                service.soft_delete_snapshot(snapshot.snapshot_id, reason="用户在持仓编辑页软删除")
            continue

        service.upsert_snapshot(snapshot)
        if existing is None:
            service.create_adjustment(
                snapshot_id=snapshot.snapshot_id,
                portfolio_id=snapshot.portfolio_id,
                instrument_id=snapshot.instrument_id,
                adjustment_type="ADD",
                changes=snapshot.to_dict(),
                reason="用户在持仓编辑页新增",
            )
            continue

        changes = _snapshot_changes(existing, snapshot)
        if changes:
            service.create_adjustment(
                snapshot_id=snapshot.snapshot_id,
                portfolio_id=snapshot.portfolio_id,
                instrument_id=snapshot.instrument_id,
                adjustment_type="UPDATE",
                changes=changes,
                reason="用户在持仓编辑页保存修改",
            )
        elif existing.soft_deleted and not snapshot.soft_deleted:
            service.create_adjustment(
                snapshot_id=snapshot.snapshot_id,
                portfolio_id=snapshot.portfolio_id,
                instrument_id=snapshot.instrument_id,
                adjustment_type="RESTORE",
                changes={"soft_deleted": False},
                reason="用户在持仓编辑页恢复持仓",
            )

    return load_v021_holdings_payload(db_path=db_path)


def build_v021_holdings_sync_read_model(*, db_path: Path | str | None = None) -> dict[str, Any]:
    holdings = load_v021_holdings_payload(db_path=db_path)
    read_model = build_v021_operational_read_model(db_path=db_path)
    investment = read_model["investment"]
    accounts = read_model["accounts"]
    report = build_v021_holdings_report(db_path=db_path)
    market_value = float(investment["market_value_cny"])
    return {
        "schema": "PFIV0211Stage4HoldingsSyncReadModelV1",
        "source": "SQLite operational database",
        "sqlite": {
            "db_path": holdings["summary"]["db_path"],
            "snapshot_count": holdings["summary"]["snapshot_count"],
            "adjustment_count": holdings["summary"]["adjustment_count"],
            "tables": holdings["summary"]["tables"],
        },
        "home": {
            "net_worth_cny": accounts["net_worth_cny"],
            "cash_cny": accounts["cash_cny"],
            "investment_market_value_cny": investment["market_value_cny"],
            "holding_count": investment["holding_count"],
        },
        "investment": {
            "market_value_cny": investment["market_value_cny"],
            "cost_basis_cny": investment["cost_basis_cny"],
            "total_return_cny": investment["total_return_cny"],
            "unrealized_pnl_cny": investment["unrealized_pnl_cny"],
            "cash_position_cny": investment["cash_position_cny"],
            "holding_count": investment["holding_count"],
        },
        "report": report["report"],
        "consistency": {
            "home_investment_report_market_value_same": (
                float(report["report"]["market_value_cny"]) == market_value
                and float(read_model["accounts"]["total_assets_cny"]) >= market_value
            ),
            "read_model_schema": read_model["schema"],
            "report_schema": report["schema"],
        },
    }


def build_v021_holdings_report(*, db_path: Path | str | None = None) -> dict[str, Any]:
    service = V021HoldingsPersistenceService(db_path)
    snapshots = service.list_snapshots()
    read_model = build_v021_operational_read_model(db_path=db_path)
    investment = read_model["investment"]
    rows = [_snapshot_to_frontend(row) for row in snapshots]
    return {
        "schema": "PFIV0211Stage4HoldingsReportV1",
        "source": "SQLite operational database",
        "report": {
            "title": "持仓同步报告",
            "holding_count": len(rows),
            "market_value_cny": investment["market_value_cny"],
            "cost_basis_cny": investment["cost_basis_cny"],
            "unrealized_pnl_cny": investment["unrealized_pnl_cny"],
            "adjustment_count": len(service.list_adjustments()),
            "empty_state": "暂无真实持仓，报告不生成模拟收益。" if not rows else "",
            "rows": rows,
        },
    }


def build_v021_operational_read_model(*, db_path: Path | str | None = None) -> dict[str, Any]:
    service = V021HoldingsPersistenceService(db_path)
    snapshots = service.list_snapshots()
    consumption = _real_alipay_consumption_model()
    investment_value = round(sum(_snapshot_market_value_cny(item) for item in snapshots), 2)
    investment_cost = round(sum(_snapshot_cost_cny(item) for item in snapshots), 2)
    unrealized_pnl = round(investment_value - investment_cost, 2)
    cash_cny = _cash_position_from_snapshots(snapshots)
    total_assets = round(investment_value + cash_cny, 2)
    total_liabilities = 0.0
    net_worth = round(total_assets - total_liabilities, 2)
    adjustment_count = len(service.list_adjustments())

    return {
        "schema": "PFIV021OperationalReadModelV1",
        "accounts": {
            "cash_cny": cash_cny,
            "net_worth_cny": net_worth,
            "total_assets_cny": total_assets,
            "total_liabilities_cny": total_liabilities,
        },
        "investment": {
            "market_value_cny": investment_value,
            "cost_basis_cny": investment_cost,
            "total_return_cny": unrealized_pnl,
            "unrealized_pnl_cny": unrealized_pnl,
            "cash_position_cny": cash_cny,
            "holding_count": len(snapshots),
            "adjustment_count": adjustment_count,
        },
        "consumption": consumption,
    }


def build_v021_operational_trends(*, db_path: Path | str | None = None) -> dict[str, Any]:
    model = build_v021_operational_read_model(db_path=db_path)
    accounts = model["accounts"]
    investment = model["investment"]
    cost_basis = float(investment["cost_basis_cny"])
    market_value = float(investment["market_value_cny"])
    total_return = float(investment["total_return_cny"])
    cash_position = float(investment["cash_position_cny"])
    periods = ["成本基准", "当前"]
    has_holdings = investment["holding_count"] > 0

    payload = {
        "schema": "PFIV021OperationalTrendReadModelV1",
        "readModel": model,
        "trends": {
            "accounts": {
                "scope": "账户与资产",
                "title": "现金、净资产、总资产与负债趋势",
                "unit": "CNY",
                "source": "SQLite 运行读模型",
                "emptyState": "账户趋势需要先保存持仓或导入账户流水。",
                "periods": periods if has_holdings else [],
                "series": [
                    _series("cash_cny", "现金", "--pfi-teal", [cash_position, cash_position] if has_holdings else []),
                    _series("net_worth_cny", "净资产", "--pfi-blue", [cost_basis + cash_position, accounts["net_worth_cny"]] if has_holdings else []),
                    _series("total_assets_cny", "总资产", "--pfi-amber", [cost_basis + cash_position, accounts["total_assets_cny"]] if has_holdings else []),
                    _series("total_liabilities_cny", "总负债", "--pfi-red", [0.0, accounts["total_liabilities_cny"]] if has_holdings else []),
                ],
            },
            "investment": {
                "scope": "投资管理",
                "title": "投资市值、收益、未实现盈亏与现金仓位趋势",
                "unit": "CNY",
                "source": "SQLite 运行读模型",
                "emptyState": "投资趋势需要先保存持仓，当前不伪造收益。",
                "periods": periods if has_holdings else [],
                "series": [
                    _series("market_value_cny", "投资市值", "--pfi-blue", [cost_basis, market_value] if has_holdings else []),
                    _series("total_return_cny", "总收益", "--pfi-teal", [0.0, total_return] if has_holdings else []),
                    _series("unrealized_pnl_cny", "未实现盈亏", "--pfi-amber", [0.0, total_return] if has_holdings else []),
                    _series("cash_position_cny", "现金仓位", "--pfi-red", [cash_position, cash_position] if has_holdings else []),
                ],
            },
            "consumption": _consumption_trend_from_real_alipay(model["consumption"]),
        },
    }
    payload.update(payload["trends"])
    return payload


def build_v025_stage7_operational_trends(*, db_path: Path | str | None = None) -> dict[str, Any]:
    """Build Stage 7 runtime trends exclusively from its SQLite authorities."""

    holding_model = HoldingSettingsPersistenceService(db_path=db_path).build_holding_projection()
    ledger_service = ImportReviewLedgerService(db_path=db_path)
    ledger_model = ledger_service.build_ledger_projection()
    ledger_runtime = ledger_service.build_ledger_runtime_read_model()
    projection = dict(holding_model["projection"])
    accounts = {
        "cash_cny": None,
        "net_worth_cny": None,
        "total_assets_cny": None,
        "total_liabilities_cny": None,
        "valuation_status": "blocked_missing_authoritative_cash_and_liability_sources",
    }
    investment = {
        "market_value_cny": None,
        "cost_basis_cny": None,
        "total_return_cny": None,
        "unrealized_pnl_cny": None,
        "cash_position_cny": None,
        "holding_count": int(projection["holding_count"]),
        "adjustment_count": None,
        "valuation_status": str(projection["valuation_status"]),
        "projection_hash": str(projection["projection_hash"]),
    }
    empty_series = lambda *items: [_series(item[0], item[1], item[2], []) for item in items]
    account_trend = {
        "scope": "账户与资产",
        "title": "现金、净资产、总资产与负债趋势",
        "unit": "CNY",
        "source": "SQLite v0.2.5 canonical sources（依赖不完整时 fail-closed）",
        "emptyState": "权威现金与负债来源未接入，账户数值趋势保持阻断。",
        "periods": [],
        "series": empty_series(
            ("cash_cny", "现金", "--pfi-teal"),
            ("net_worth_cny", "净资产", "--pfi-blue"),
            ("total_assets_cny", "总资产", "--pfi-amber"),
            ("total_liabilities_cny", "总负债", "--pfi-red"),
        ),
    }
    investment_trend = {
        "scope": "投资管理",
        "title": "投资市值、收益、未实现盈亏与现金仓位趋势",
        "unit": "CNY",
        "source": "SQLite v0.2.5 持仓投影（估值缺失时 fail-closed）",
        "emptyState": "持仓已接入；估值依赖未完成前不生成投资数值趋势。",
        "periods": [],
        "series": empty_series(
            ("market_value_cny", "投资市值", "--pfi-blue"),
            ("total_return_cny", "总收益", "--pfi-teal"),
            ("unrealized_pnl_cny", "未实现盈亏", "--pfi-amber"),
            ("cash_position_cny", "现金仓位", "--pfi-red"),
        ),
    }
    consumption = dict(ledger_runtime["consumption"])
    has_ledger = bool(consumption.get("has_real_transactions"))
    rolling_spend = float(consumption.get("cashflow_forecast_cny") or 0)
    month_spend = float(consumption.get("month_spend_cny") or 0)
    consumption_trend = {
        "scope": "消费管理",
        "title": "本月支出、预算剩余、固定/弹性支出与现金流预测",
        "unit": "CNY",
        "source": "SQLite v0.2.5 unified operational ledger",
        "emptyState": "" if has_ledger else consumption.get("empty_state"),
        "periods": ["最近30天", "本月"] if has_ledger else [],
        "series": [
            _series("month_spend_cny", "本月支出", "--pfi-blue", [rolling_spend, month_spend] if has_ledger else []),
            _series("budget_remaining_cny", "预算剩余", "--pfi-teal", []),
            _series("fixed_spend_cny", "固定支出", "--pfi-amber", []),
            _series("flex_spend_cny", "弹性支出", "--pfi-red", [rolling_spend, month_spend] if has_ledger else []),
            _series("cashflow_forecast_cny", "现金流预测", "--pfi-blue", [rolling_spend, rolling_spend] if has_ledger else []),
        ],
        "unknown_series": ["budget_remaining_cny", "fixed_spend_cny"],
    }
    trends = {
        "accounts": account_trend,
        "investment": investment_trend,
        "consumption": consumption_trend,
    }
    read_model = {
        "schema": "PFIV025Stage7OperationalReadModelV1",
        "accounts": accounts,
        "investment": investment,
        "consumption": consumption,
        "holding_projection": projection,
        "operational_ledger": ledger_model,
        "operational_ledger_runtime": ledger_runtime,
        "holding_source_authority": "v025_sqlite_holding_records",
        "ledger_source_authority": "v025_sqlite_unified_operational_ledger",
        "legacy_accounts_values_suppressed": True,
        "legacy_investment_values_suppressed": True,
        "legacy_metadatabase_consumption_suppressed": True,
    }
    payload = {
        "schema": "PFIV025Stage7OperationalTrendReadModelV1",
        "readModel": read_model,
        "trends": trends,
        "stage7HoldingProjection": holding_model,
        "stage7OperationalLedger": ledger_model,
        **trends,
    }
    return payload


def build_v025_stage7_operational_read_model_status(
    *, db_path: Path | str | None = None
) -> dict[str, Any]:
    """Expose one fail-closed status authority for every formal Stage 7 surface."""

    operational = build_v025_stage7_operational_trends(db_path=db_path)["readModel"]
    ledger = dict(operational["operational_ledger_runtime"])
    holding = dict(operational["holding_projection"])
    ledger_status = str(ledger.get("status") or "not_loaded")
    if ledger_status == "partial_pending_review":
        ledger_reason = "SQLite ledger 含待复核流水；未决记录与财务指标均不发布为零。"
    elif ledger_status == "blocked_economic_event_adapter":
        ledger_reason = (
            "SQLite ledger 已接入，但 economic_event/interconnection adapter 尚未完成；"
            "消费与活动指标不发布值。"
        )
    else:
        ledger_status = "not_loaded"
        ledger_reason = "SQLite ledger 尚无已确认来源；财务指标保持未加载。"
    dependencies_reason = "账户现金、负债或持仓估值权威依赖未完成；指标保持阻断。"
    consumption_metric_status = {
        "not_loaded": "not_loaded",
        "partial_pending_review": "partial_coverage",
        "blocked_economic_event_adapter": "calculation_failed",
    }[ledger_status]
    investment_metric_status = (
        "valuation_missing" if int(holding.get("holding_count") or 0) else "not_loaded"
    )
    metric_specs = (
        ("net_worth_cny", "FORM-PFI-012", None, "source_missing", dependencies_reason),
        ("cash_balance_cny", "FORM-PFI-008", None, "source_missing", dependencies_reason),
        (
            "investment_market_value_cny", "FORM-PFI-010",
            "v025_sqlite_holding_records", investment_metric_status, dependencies_reason,
        ),
        (
            "consumption_outflow_cny", "FORM-PFI-015",
            "v025_sqlite_unified_operational_ledger", consumption_metric_status, ledger_reason,
        ),
        (
            "report_summary_status", None, None, "calculation_failed",
            "财务指标输入阻断，报告摘要不发布结论。",
        ),
    )
    metrics = [
        {
            "metric_id": metric_id,
            "value": None,
            "currency": "CNY" if metric_id != "report_summary_status" else None,
            "status": status,
            "source_id": source_id,
            "record_count": (
                int(ledger.get("ledger_count") or 0)
                if source_id == "v025_sqlite_unified_operational_ledger"
                else int(holding.get("holding_count") or 0)
                if source_id == "v025_sqlite_holding_records"
                else None
            ),
            "as_of": (
                ledger.get("data_range", {}).get("end")
                if source_id == "v025_sqlite_unified_operational_ledger"
                else None
            ),
            "formula_id": formula_id,
            "confidence": None,
            "blocking_reason_zh": reason,
            "calculation_state": "blocked",
        }
        for metric_id, formula_id, source_id, status, reason in metric_specs
    ]
    semantic_state = {
        "contract_version": "PFI-V025-STAGE7-SQLITE-FAIL-CLOSED-AUTHORITY",
        "ledger_data_hash": ledger.get("data_hash"),
        "holding_projection_hash": holding.get("projection_hash"),
        "metrics": metrics,
    }
    return {
        "schema": "PFIV024Stage4ReadModelStatusV1",
        "target_version": "v0.2.5",
        "stage": "Stage 7",
        "contract_version": semantic_state["contract_version"],
        "stage7_operational_authority": True,
        "legacy_metadatabase_suppressed": True,
        "source": {
            "type": "sqlite_operational_authorities",
            "status": ledger_status,
            "storage_mode": "local_private_sqlite",
            "record_count": int(ledger.get("ledger_count") or 0),
            "raw_file_count": None,
            "as_of": ledger.get("data_range", {}).get("end"),
            "evidence_hash": ledger.get("data_hash"),
            "blocking_reason_zh": ledger_reason,
        },
        "as_of": ledger.get("data_range", {}).get("end"),
        "read_model_hash": _canonical_json_sha256(semantic_state),
        "core_metric_states": metrics,
        "blocked_metric_ids": [row["metric_id"] for row in metrics],
        "surface_ids": ["home", "accounts", "investment", "consumption", "insights"],
        "generated_at_utc": "",
    }


def import_v021_alipay_payloads(
    payload: dict[str, Any],
    *,
    data_home: Path | str | None = None,
    metadatabase_root: Path | str | None = None,
) -> dict[str, Any]:
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list) or not files:
        raise ValueError("files must contain uploaded real Alipay files")

    decoded_payloads: list[tuple[str, bytes]] = []
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("each uploaded file must be an object")
        name = _clean(item.get("name") or item.get("fileName") or "")
        if not name:
            raise ValueError("uploaded file name is required")
        encoded = _clean(item.get("contentBase64") or item.get("base64") or "")
        if "," in encoded and encoded.lower().startswith("data:"):
            encoded = encoded.split(",", 1)[1]
        if not encoded:
            raise ValueError(f"{name} has no uploaded file content")
        try:
            content = base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise ValueError(f"{name} is not valid base64") from exc
        if not content:
            raise ValueError(f"{name} is empty")
        decoded_payloads.append((name, content))

    resolved_data_home = Path(data_home).expanduser() if data_home is not None else default_data_home()
    resolved_metadatabase = Path(metadatabase_root).expanduser() if metadatabase_root is not None else _default_alipay_metadatabase_root()
    return write_private_alipay_import(tuple(decoded_payloads), resolved_data_home, metadatabase_root=resolved_metadatabase)


def ensure_v021_runtime_api_server(
    *,
    db_path: Path | str | None = None,
    host: str = DEFAULT_RUNTIME_API_HOST,
    port: int | None = None,
) -> str:
    requested_port = int(os.environ.get("PFI_V021_RUNTIME_API_PORT", port or DEFAULT_RUNTIME_API_PORT))
    with _SERVER_LOCK:
        existing = _SERVER_STATE.get("server")
        if existing is not None:
            return str(_SERVER_STATE["base_url"])

        auth_token = secrets.token_urlsafe(32)
        release_cache_policy = build_v025_release_cache_policy(db_path=db_path)
        handler = _handler_factory(
            db_path,
            auth_token=auth_token,
            release_cache_policy=release_cache_policy,
        )
        server = ThreadingHTTPServer((host, requested_port), handler)
        thread = threading.Thread(target=server.serve_forever, name="pfi-v021-runtime-api", daemon=True)
        thread.start()
        base_url = f"http://{host}:{server.server_port}"
        _SERVER_STATE.update(
            {
                "server": server,
                "thread": thread,
                "base_url": base_url,
                "db_path": db_path,
                "auth_token": auth_token,
                "release_cache_policy": dict(release_cache_policy),
            }
        )
        return base_url


def v021_runtime_api_client_token() -> str:
    """Return the process-local browser token after the server has started."""

    token = str(_SERVER_STATE.get("auth_token") or "")
    if not token:
        raise RuntimeError("PFI runtime API client token is unavailable")
    return token


def _handler_factory(
    db_path: Path | str | None,
    *,
    auth_token: str,
    release_cache_policy: dict[str, Any] | None = None,
):
    candidate_read_only = os.environ.get("PFI_STAGE1_CANDIDATE_MODE") == "1"
    frozen_release_cache_policy = (
        dict(release_cache_policy)
        if isinstance(release_cache_policy, dict)
        else None
    )
    candidate_status = (
        build_v025_stage1_candidate_read_model_status() if candidate_read_only else None
    )
    candidate_headers = (
        _v025_candidate_data_headers(candidate_status)
        if isinstance(candidate_status, dict)
        else {}
    )
    job_supervisor_lock = threading.Lock()
    job_supervisor: RuntimeJobSupervisor | None = None

    def resolve_job_supervisor() -> RuntimeJobSupervisor:
        nonlocal job_supervisor
        if candidate_read_only:
            raise JobLifecycleError("isolated candidate has no writable runtime jobs")
        with job_supervisor_lock:
            if job_supervisor is None:
                resolved_db_path = (
                    Path(db_path).expanduser()
                    if db_path is not None
                    else default_operational_db_path()
                )

                def build_cache_policy() -> dict[str, Any]:
                    return (
                        build_v025_release_cache_policy()
                        if db_path is None
                        else build_v025_release_cache_policy(db_path=db_path)
                    )

                job_supervisor = RuntimeJobSupervisor(
                    resolved_db_path,
                    cache_policy_builder=build_cache_policy,
                )
                job_supervisor.recover_and_resume()
            return job_supervisor

    class V021RuntimeApiHandler(BaseHTTPRequestHandler):
        server_version = "PFI-V021-RuntimeAPI/1.0"

        def do_OPTIONS(self) -> None:  # noqa: N802
            origin = self._cors_origin()
            requested_headers = {
                item.strip().lower()
                for item in str(self.headers.get("Access-Control-Request-Headers") or "").split(",")
                if item.strip()
            }
            if not self._host_is_allowed() or origin is None or RUNTIME_AUTH_HEADER.lower() not in requested_headers:
                self._send_json(
                    {"error": "forbidden", "message": "本机服务拒绝未授权跨源请求"},
                    status=403,
                )
                return
            self.send_response(204)
            self._send_cors_headers(origin)
            self.send_header(
                "Access-Control-Allow-Methods",
                "GET, OPTIONS" if candidate_read_only else "GET, POST, OPTIONS",
            )
            self.send_header("Access-Control-Allow-Headers", f"Content-Type, {RUNTIME_AUTH_HEADER}")
            self.send_header("Access-Control-Max-Age", "300")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            if not self._authorized():
                self._send_json(
                    {"error": "forbidden", "message": "本机服务令牌无效"},
                    status=403,
                    cache_control="no-store, private",
                )
                return
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query = parse_qs(parsed_url.query)
            try:
                if path == "/health":
                    self._send_json({"status": "ok", "schema": V021_RUNTIME_API_SCHEMA})
                    return
                if path == "/api/release-manifest":
                    manifest, manifest_raw, manifest_sha256 = load_v025_release_manifest_record()
                    self._send_json(
                        manifest,
                        raw_body=manifest_raw,
                        cache_control="no-store, private",
                        last_modified_epoch=int(V025_RELEASE_MANIFEST_PATH.stat().st_mtime),
                        extra_headers={
                            "X-PFI-Release-Manifest-SHA256": manifest_sha256,
                            "X-PFI-Running-Backend-SHA256": V025_RUNNING_BACKEND_SHA256,
                        },
                    )
                    return
                if path == "/api/release-cache-policy":
                    policy = (
                        dict(frozen_release_cache_policy)
                        if frozen_release_cache_policy is not None
                        else build_v025_release_cache_policy()
                        if db_path is None
                        else build_v025_release_cache_policy(db_path=db_path)
                    )
                    self._send_json(
                        policy,
                        cache_control="no-store, private",
                        last_modified_epoch=V025_RUNTIME_SOURCE_MTIME,
                        extra_headers={
                            "X-PFI-Running-Backend-SHA256": V025_RUNNING_BACKEND_SHA256,
                            "X-PFI-Streamlit-Cache-Key": str(policy.get("streamlit_cache_key") or ""),
                        },
                    )
                    return
                if path == "/api/jobs":
                    if candidate_read_only:
                        self._send_json(
                            {
                                "schema": "PFIV025RuntimeJobSupervisorV1",
                                "jobs": [],
                                "job_count": 0,
                                "candidate_read_only": True,
                                "external_network_calls": 0,
                            },
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                        return
                    supervisor = resolve_job_supervisor()
                    supervisor.recover_and_resume()
                    status_filter = str((query.get("status") or [""])[0])
                    raw_limit = str((query.get("limit") or ["50"])[0])
                    if not raw_limit.isdigit():
                        raise ValueError("job list limit must be an integer")
                    self._send_json(
                        supervisor.list(status=status_filter, limit=int(raw_limit)),
                        cache_control="no-store, private",
                    )
                    return
                if path.startswith("/api/jobs/"):
                    if candidate_read_only:
                        self._send_json(
                            {"error": "candidate_read_only", "message": "隔离候选没有后台任务"},
                            status=404,
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                        return
                    job_id = path.removeprefix("/api/jobs/")
                    if not job_id or "/" in job_id:
                        raise ValueError("job_id is invalid")
                    supervisor = resolve_job_supervisor()
                    supervisor.recover_and_resume()
                    self._send_json(
                        supervisor.get(job_id),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/holdings":
                    if candidate_read_only:
                        self._send_json(
                            build_v025_stage1_candidate_holdings_payload(),
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                    else:
                        self._send_json(
                            HoldingSettingsPersistenceService(db_path=db_path).list_holdings(),
                            cache_control="no-store, private",
                        )
                    return
                if path == "/api/read-model":
                    if candidate_read_only:
                        self._send_json(
                            build_v025_stage1_candidate_sync_read_model(),
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                    else:
                        self._send_json(
                            HoldingSettingsPersistenceService(db_path=db_path).build_holding_projection(),
                            cache_control="no-store, private",
                        )
                    return
                if path == "/api/read-model-status":
                    if candidate_read_only:
                        self._send_json(
                            candidate_status,
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                        return
                    self._send_json(
                        build_v025_stage7_operational_read_model_status(db_path=db_path),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/reports/holdings":
                    if candidate_read_only:
                        self._send_json(
                            {
                                "schema": "PFIV0211Stage4HoldingsReportV1",
                                "source": "isolated empty candidate",
                                "report": build_v025_stage1_candidate_sync_read_model()["report"],
                            },
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                    else:
                        self._send_json(
                            HoldingSettingsPersistenceService(db_path=db_path).build_holding_report(),
                            cache_control="no-store, private",
                        )
                    return
                if path == "/api/trends":
                    if candidate_read_only:
                        self._send_json(
                            build_v025_stage1_candidate_trends(),
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                    else:
                        self._send_json(
                            build_v025_stage7_operational_trends(db_path=db_path),
                            cache_control="no-store, private",
                        )
                    return
                if path == "/api/imports/review-queue":
                    if candidate_read_only:
                        self._send_json(
                            {
                                "schema": "PFIV025Stage7ReviewQueueV1",
                                "status_filter": "pending",
                                "pending_count": 0,
                                "item_count": 0,
                                "items": [],
                                "candidate_read_only": True,
                            },
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                    else:
                        status_filter = str((query.get("status") or ["pending"])[0])
                        self._send_json(
                            ImportReviewLedgerService(db_path=db_path).list_review_queue(status=status_filter),
                            cache_control="no-store, private",
                        )
                    return
                if path == "/api/ledger":
                    if candidate_read_only:
                        self._send_json(
                            {
                                "schema": "PFIV025Stage7UnifiedLedgerV1",
                                "batch_id": None,
                                "ledger_count": 0,
                                "posted_count": 0,
                                "pending_review_count": 0,
                                "excluded_count": 0,
                                "entries": [],
                                "candidate_read_only": True,
                            },
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                    else:
                        batch_id = str((query.get("batch_id") or [""])[0])
                        self._send_json(
                            ImportReviewLedgerService(db_path=db_path).list_ledger(batch_id=batch_id),
                            cache_control="no-store, private",
                        )
                    return
                if path == "/api/imports/alipay":
                    if candidate_read_only:
                        self._send_json(
                            {"error": "candidate_read_only", "message": "隔离候选没有导入批次"},
                            status=404,
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                    else:
                        batch_id = str((query.get("batch_id") or [""])[0])
                        if not batch_id:
                            raise ImportWorkflowError("读取导入批次需要 batch_id")
                        self._send_json(
                            ImportReviewLedgerService(db_path=db_path).get_batch(batch_id),
                            cache_control="no-store, private",
                        )
                    return
                if path == "/api/settings/preferences":
                    if candidate_read_only:
                        self._send_json(
                            {
                                "schema": "PFIV025Stage7SettingsPreferencesV1",
                                "scope": "local_user_preferences",
                                "surface_scope": "settings_only",
                                "preferences": dict(DEFAULT_SETTINGS),
                                "revision": 0,
                                "persisted": False,
                                "updated_at": None,
                                "candidate_read_only": True,
                            },
                            cache_control="no-store, private",
                            extra_headers=candidate_headers,
                        )
                    else:
                        self._send_json(
                            HoldingSettingsPersistenceService(db_path=db_path).get_settings(),
                            cache_control="no-store, private",
                        )
                    return
                if path == "/api/lineage":
                    operational_ledger = None
                    if not candidate_read_only:
                        operational_ledger = ImportReviewLedgerService(
                            db_path=db_path
                        ).build_ledger_runtime_read_model()
                    self._send_json(
                        build_stage7_phase73_payload(
                            read_model_status=candidate_status if candidate_read_only else None,
                            operational_ledger=operational_ledger,
                        ),
                        cache_control="no-store, private",
                        extra_headers=candidate_headers if candidate_read_only else None,
                    )
                    return
                self._send_json({"error": "not_found", "message": "未找到接口"}, status=404)
            except KeyError:
                self._send_json(
                    {"error": "job_not_found", "message": "未找到后台任务"},
                    status=404,
                    cache_control="no-store, private",
                )
            except (
                ImportWorkflowError,
                HoldingSettingsWorkflowError,
                JobLifecycleError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                self._send_json(
                    {"error": "workflow_error", "message": str(exc)},
                    status=400,
                    cache_control="no-store, private",
                )
            except Exception as exc:  # pragma: no cover - exercised through browser runtime
                if path in {"/api/release-manifest", "/api/release-cache-policy"}:
                    self._send_json(
                        {"error": "release_contract_unavailable", "message": "发布身份或缓存策略不可用"},
                        status=500,
                        cache_control="no-store, private",
                        last_modified_epoch=V025_RUNTIME_SOURCE_MTIME,
                    )
                    return
                if path.startswith("/api/jobs"):
                    self._send_json(
                        {"error": "runtime_job_unavailable", "message": "后台任务状态暂不可用"},
                        status=500,
                        cache_control="no-store, private",
                    )
                    return
                self._send_json({"error": "server_error", "message": str(exc)}, status=500)

        def do_POST(self) -> None:  # noqa: N802
            if not self._authorized():
                self._send_json(
                    {"error": "forbidden", "message": "本机服务令牌无效"},
                    status=403,
                    cache_control="no-store, private",
                )
                return
            path = urlparse(self.path).path
            try:
                if candidate_read_only:
                    self._send_json(
                        {"error": "candidate_read_only", "message": "隔离候选禁止写入"},
                        status=403,
                        cache_control="no-store, private",
                    )
                    return
                payload = self._read_json()
                if path == "/api/jobs/cache-refresh":
                    result = resolve_job_supervisor().submit_cache_refresh(
                        request_id=_clean(payload.get("request_id") or ""),
                    )
                    self._send_json(
                        result,
                        status=202,
                        cache_control="no-store, private",
                    )
                    return
                if path.startswith("/api/jobs/") and path.endswith("/cancel"):
                    job_id = path.removeprefix("/api/jobs/").removesuffix("/cancel")
                    if not job_id or "/" in job_id:
                        raise ValueError("job_id is invalid")
                    expected_revision = payload.get("expected_revision")
                    if isinstance(expected_revision, bool) or not isinstance(expected_revision, int):
                        raise ValueError("expected_revision must be an integer")
                    result = resolve_job_supervisor().cancel(
                        job_id,
                        expected_revision=expected_revision,
                        reason=_clean(payload.get("reason") or "owner requested cancellation"),
                    )
                    self._send_json(
                        result,
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/holdings":
                    raise HoldingSettingsWorkflowError(
                        "legacy holdings write endpoint is retired; use /api/holdings/commit"
                    )
                if path == "/api/holdings/commit":
                    service = HoldingSettingsPersistenceService(db_path=db_path)
                    operations = payload.get("operations")
                    if not isinstance(operations, list):
                        raise HoldingSettingsWorkflowError("operations must be a list")
                    self._send_json(
                        service.commit_holdings(
                            request_id=_clean(payload.get("request_id") or ""),
                            operations=operations,
                            expected_projection_hash=_clean(payload.get("expected_projection_hash") or ""),
                        ),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/settings/preferences":
                    service = HoldingSettingsPersistenceService(db_path=db_path)
                    preferences = payload.get("preferences")
                    if not isinstance(preferences, dict):
                        raise HoldingSettingsWorkflowError("preferences must be an object")
                    expected_revision = payload.get("expected_revision")
                    self._send_json(
                        service.save_settings(preferences, expected_revision=expected_revision),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/imports/alipay":
                    service = ImportReviewLedgerService(db_path=db_path)
                    self._send_json(
                        service.preview_upload(_uploaded_import_files(payload)),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/imports/alipay/confirm":
                    service = ImportReviewLedgerService(db_path=db_path)
                    self._send_json(
                        service.confirm_batch(_clean(payload.get("batch_id") or "")),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/imports/alipay/rollback":
                    service = ImportReviewLedgerService(db_path=db_path)
                    self._send_json(
                        service.rollback_batch(_clean(payload.get("batch_id") or "")),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/imports/alipay/retry":
                    service = ImportReviewLedgerService(db_path=db_path)
                    self._send_json(
                        service.retry_batch(_clean(payload.get("batch_id") or "")),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/imports/review":
                    service = ImportReviewLedgerService(db_path=db_path)
                    self._send_json(
                        service.resolve_review(
                            _clean(payload.get("review_id") or ""),
                            decision=_clean(payload.get("decision") or ""),
                            category=_clean(payload.get("category") or ""),
                        ),
                        cache_control="no-store, private",
                    )
                    return
                if path == "/api/imports/review/undo":
                    service = ImportReviewLedgerService(db_path=db_path)
                    self._send_json(
                        service.undo_review(_clean(payload.get("review_id") or "")),
                        cache_control="no-store, private",
                    )
                    return
                self._send_json({"error": "not_found", "message": "未找到接口"}, status=404)
            except KeyError:
                self._send_json(
                    {"error": "job_not_found", "message": "未找到后台任务"},
                    status=404,
                    cache_control="no-store, private",
                )
            except (
                ImportWorkflowError,
                HoldingSettingsWorkflowError,
                JobLifecycleError,
                JobTransitionError,
                StaleRevisionError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                self._send_json(
                    {"error": "workflow_error", "message": str(exc)},
                    status=400,
                    cache_control="no-store, private",
                )
            except Exception as exc:  # pragma: no cover - exercised through browser runtime
                if path.startswith("/api/jobs"):
                    self._send_json(
                        {"error": "runtime_job_unavailable", "message": "后台任务操作失败"},
                        status=500,
                        cache_control="no-store, private",
                    )
                    return
                self._send_json({"error": "server_error", "message": str(exc)}, status=500)

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            media_type = str(self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            if media_type != "application/json":
                raise ValueError("Content-Type must be application/json")
            raw_length = str(self.headers.get("Content-Length") or "0")
            if not raw_length.isdigit():
                raise ValueError("Content-Length is invalid")
            length = int(raw_length)
            if length < 0 or length > MAX_RUNTIME_REQUEST_BYTES:
                raise ValueError("request body exceeds the local runtime limit")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(raw or "{}")
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def _host_is_allowed(self) -> bool:
            port = int(self.server.server_address[1])
            host = str(self.headers.get("Host") or "").strip().lower()
            return host in {f"127.0.0.1:{port}", f"localhost:{port}"}

        def _cors_origin(self) -> str | None:
            origin = str(self.headers.get("Origin") or "").strip()
            if not origin:
                return None
            parsed = urlparse(origin)
            if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
                return None
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                return None
            return origin

        def _authorized(self) -> bool:
            supplied = str(self.headers.get(RUNTIME_AUTH_HEADER) or "")
            return self._host_is_allowed() and bool(supplied) and hmac.compare_digest(supplied, auth_token)

        def _send_cors_headers(self, origin: str) -> None:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

        def _send_json(
            self,
            payload: dict[str, Any],
            *,
            status: int = 200,
            raw_body: bytes | None = None,
            cache_control: str | None = None,
            last_modified_epoch: int | None = None,
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            body = bytes(raw_body) if raw_body is not None else json.dumps(
                payload, ensure_ascii=False
            ).encode("utf-8")
            release_validators = last_modified_epoch is not None
            etag = f'"{hashlib.sha256(body).hexdigest()}"' if release_validators else None
            modified_epoch = int(last_modified_epoch) if release_validators else None
            last_modified = formatdate(modified_epoch, usegmt=True) if modified_epoch is not None else None
            not_modified = False
            if release_validators and etag is not None and status == 200:
                if_none_match = self.headers.get("If-None-Match")
                if if_none_match is not None:
                    not_modified = _if_none_match_matches(if_none_match, etag)
                elif self.headers.get("If-Modified-Since"):
                    try:
                        requested_time = parsedate_to_datetime(str(self.headers["If-Modified-Since"]))
                        not_modified = int(requested_time.timestamp()) >= int(modified_epoch)
                    except (TypeError, ValueError, OverflowError):
                        not_modified = False
            if not_modified:
                self.send_response(304)
                self.send_header("ETag", str(etag))
                self.send_header("Last-Modified", str(last_modified))
                if cache_control:
                    self.send_header("Cache-Control", cache_control)
                origin = self._cors_origin()
                if origin is not None:
                    self._send_cors_headers(origin)
                for header, value in (extra_headers or {}).items():
                    self.send_header(header, value)
                self.end_headers()
                return
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            if release_validators:
                self.send_header("ETag", str(etag))
                self.send_header("Last-Modified", str(last_modified))
            if cache_control:
                self.send_header("Cache-Control", cache_control)
            origin = self._cors_origin()
            if origin is not None:
                self._send_cors_headers(origin)
            exposed_headers = (
                "X-PFI-Release-Manifest-SHA256, X-PFI-Running-Backend-SHA256, "
                "X-PFI-Streamlit-Cache-Key, X-PFI-Read-Model-SHA256, "
                "X-PFI-Data-Boundary"
            )
            if release_validators:
                exposed_headers = (
                    "X-PFI-Release-Manifest-SHA256, X-PFI-Running-Backend-SHA256, "
                    "X-PFI-Streamlit-Cache-Key, ETag, Last-Modified"
                )
            self.send_header("Access-Control-Expose-Headers", exposed_headers)
            for header, value in (extra_headers or {}).items():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(body)

    return V021RuntimeApiHandler


def _if_none_match_matches(header_value: str, current_etag: str) -> bool:
    """Apply weak entity-tag comparison for GET/HEAD If-None-Match lists."""

    def normalize(value: str) -> str:
        candidate = value.strip()
        if candidate[:2].lower() == "w/":
            candidate = candidate[2:].lstrip()
        return candidate

    for candidate in str(header_value).split(","):
        if candidate.strip() == "*":
            return True
        if normalize(candidate) == normalize(current_etag):
            return True
    return False


def _uploaded_import_files(payload: dict[str, Any]) -> tuple[UploadedImportFile, ...]:
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list) or not files:
        raise ImportWorkflowError("files 必须包含至少一个本机上传文件")
    if len(files) > MAX_UPLOAD_FILE_COUNT:
        raise ImportWorkflowError(f"一次最多上传 {MAX_UPLOAD_FILE_COUNT} 个文件")
    decoded: list[UploadedImportFile] = []
    total_bytes = 0
    for item in files:
        if not isinstance(item, dict):
            raise ImportWorkflowError("每个上传文件必须是对象")
        name = _clean(item.get("name") or item.get("fileName") or "")
        encoded = _clean(item.get("contentBase64") or item.get("base64") or "")
        if "," in encoded and encoded.lower().startswith("data:"):
            encoded = encoded.split(",", 1)[1]
        if not name or not encoded:
            raise ImportWorkflowError("上传文件必须包含 name 和 contentBase64")
        if len(encoded) > ((MAX_UPLOAD_BYTES + 2) // 3) * 4 + 4:
            raise ImportWorkflowError(f"{name} 的编码内容超过单文件限制")
        try:
            content = base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise ImportWorkflowError(f"{name} 的 base64 内容无效") from exc
        if len(content) > MAX_UPLOAD_BYTES:
            raise ImportWorkflowError(f"{name} 超过 {MAX_UPLOAD_BYTES // 1024 // 1024}MB")
        total_bytes += len(content)
        if total_bytes > MAX_UPLOAD_TOTAL_BYTES:
            raise ImportWorkflowError(
                f"上传文件总量超过 {MAX_UPLOAD_TOTAL_BYTES // 1024 // 1024}MB"
            )
        decoded.append(
            UploadedImportFile(
                name=name,
                content=content,
                media_type=_clean(item.get("type") or item.get("mediaType") or "application/octet-stream"),
            )
        )
    return tuple(decoded)


def _snapshot_from_frontend(row: Any) -> V021HoldingSnapshot:
    if not isinstance(row, dict):
        raise ValueError("holding row must be an object")
    snapshot_id = _clean(row.get("snapshotId") or row.get("snapshot_id") or "")
    instrument_id = _clean(row.get("instrumentId") or row.get("instrument_id") or "")
    if not snapshot_id:
        snapshot_id = f"v021-manual-{instrument_id or 'holding'}"
    if not instrument_id:
        instrument_id = "待补标的"
    raw_metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    metadata = dict(raw_metadata)
    note = _clean(row.get("note") or row.get("memo") or metadata.get("note") or "")
    if note:
        metadata["note"] = note
    portfolio_id = _clean(
        row.get("portfolioId")
        or row.get("portfolio_id")
        or row.get("account")
        or row.get("accountName")
        or "manual"
    )
    as_of = _clean(row.get("asOf") or row.get("as_of") or row.get("updatedAt") or row.get("updated_at") or "2026-06-28")
    return V021HoldingSnapshot(
        snapshot_id=snapshot_id,
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        display_name=_clean(row.get("displayName") or row.get("display_name") or instrument_id),
        quantity=_non_negative(row.get("quantity")),
        average_cost=_non_negative(row.get("averageCost") if "averageCost" in row else row.get("average_cost")),
        market_price=_non_negative(row.get("marketPrice") if "marketPrice" in row else row.get("market_price")),
        currency=_clean(row.get("currency") or "CNY").upper(),
        source_id=_clean(row.get("sourceId") or row.get("source_id") or "manual_review"),
        as_of=as_of,
        soft_deleted=bool(row.get("softDeleted") or row.get("soft_deleted")),
        metadata=metadata,
    )


def _snapshot_to_frontend(snapshot: V021HoldingSnapshot) -> dict[str, Any]:
    return {
        "snapshotId": snapshot.snapshot_id,
        "portfolioId": snapshot.portfolio_id,
        "instrumentId": snapshot.instrument_id,
        "displayName": snapshot.display_name,
        "quantity": snapshot.quantity,
        "averageCost": snapshot.average_cost,
        "marketPrice": snapshot.market_price,
        "marketValue": snapshot.market_value,
        "currency": snapshot.currency,
        "account": snapshot.portfolio_id,
        "sourceId": snapshot.source_id,
        "asOf": snapshot.as_of,
        "updatedAt": snapshot.as_of,
        "note": snapshot.metadata.get("note", "") if isinstance(snapshot.metadata, dict) else "",
        "softDeleted": snapshot.soft_deleted,
        "metadata": snapshot.metadata,
    }


def _snapshot_changes(existing: V021HoldingSnapshot, new: V021HoldingSnapshot) -> dict[str, Any]:
    fields = ("portfolio_id", "instrument_id", "display_name", "quantity", "average_cost", "market_price", "currency", "source_id", "as_of", "soft_deleted")
    changes: dict[str, Any] = {}
    for field in fields:
        old_value = getattr(existing, field)
        new_value = getattr(new, field)
        if old_value != new_value:
            changes[field] = {"before": old_value, "after": new_value}
    return changes


def _snapshot_market_value_cny(snapshot: V021HoldingSnapshot) -> float:
    return round(snapshot.market_value * _fx_rate(snapshot.currency), 2)


def _snapshot_cost_cny(snapshot: V021HoldingSnapshot) -> float:
    return round(snapshot.quantity * snapshot.average_cost * _fx_rate(snapshot.currency), 2)


def _cash_position_from_snapshots(snapshots: list[V021HoldingSnapshot]) -> float:
    total = 0.0
    for snapshot in snapshots:
        cash_value = snapshot.metadata.get("cash_cny") if isinstance(snapshot.metadata, dict) else None
        if cash_value is not None:
            total += _non_negative(cash_value)
    return round(total, 2)


def _real_alipay_consumption_model() -> dict[str, Any]:
    transactions_path = _alipay_transactions_path()
    manifest_path = _alipay_manifest_path()
    if not transactions_path.exists():
        return {
            "has_real_transactions": False,
            "empty_state": "消费趋势需要先导入真实流水，当前不伪造支出或预算。",
        }

    rows = _read_alipay_transaction_rows(transactions_path)
    spending_rows = [row for row in rows if row.get("event_type") == "CASH" and _signed_float(row.get("amount")) < 0]
    if not rows or not spending_rows:
        return {
            "has_real_transactions": False,
            "empty_state": "已读取真实流水，但没有可计入消费支出的现金流出。",
            "source": "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "transaction_count": len(rows),
        }

    dated_spending = [
        (_parse_iso_date(row.get("occurred_at")), abs(_signed_float(row.get("amount"))))
        for row in spending_rows
    ]
    dated_spending = [(item_date, amount) for item_date, amount in dated_spending if item_date is not None]
    latest_date = max(item_date for item_date, _amount in dated_spending)
    latest_month = latest_date.strftime("%Y-%m")
    latest_month_spend = round(sum(amount for item_date, amount in dated_spending if item_date.strftime("%Y-%m") == latest_month), 2)
    rolling_start = latest_date - timedelta(days=29)
    rolling_30_spend = round(sum(amount for item_date, amount in dated_spending if rolling_start <= item_date <= latest_date), 2)
    review_count = _manifest_review_count(manifest_path)
    if review_count is None:
        review_count = sum(1 for row in rows if str(row.get("review_state") or "").upper() != "ACCEPTED")

    return {
        "has_real_transactions": True,
        "source": "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
        "transaction_count": len(rows),
        "spending_transaction_count": len(spending_rows),
        "review_count": int(review_count),
        "latest_month": latest_month,
        "latest_date": latest_date.isoformat(),
        "month_spend_cny": latest_month_spend,
        "budget_remaining_cny": 0.0,
        "fixed_spend_cny": 0.0,
        "flex_spend_cny": latest_month_spend,
        "cashflow_forecast_cny": rolling_30_spend,
        "fixed_flex_policy": "未配置固定支出规则；全部真实消费流出暂列弹性支出。",
        "empty_state": "",
    }


def _consumption_trend_from_real_alipay(consumption: dict[str, Any]) -> dict[str, Any]:
    if not consumption.get("has_real_transactions"):
        return {
            "scope": "消费管理",
            "title": "本月支出、预算剩余、固定/弹性支出与现金流预测",
            "unit": "CNY",
            "source": "MetaDatabase 真实支付宝流水",
            "emptyState": consumption.get("empty_state") or "消费趋势需要先导入真实流水，当前不伪造支出或预算。",
            "periods": [],
            "series": [
                _series("month_spend_cny", "本月支出", "--pfi-blue", []),
                _series("budget_remaining_cny", "预算剩余", "--pfi-teal", []),
                _series("fixed_spend_cny", "固定支出", "--pfi-amber", []),
                _series("flex_spend_cny", "弹性支出", "--pfi-red", []),
                _series("cashflow_forecast_cny", "现金流预测", "--pfi-blue", []),
            ],
        }

    rolling_30 = float(consumption.get("cashflow_forecast_cny") or 0)
    month_spend = float(consumption.get("month_spend_cny") or 0)
    fixed_spend = float(consumption.get("fixed_spend_cny") or 0)
    flex_spend = float(consumption.get("flex_spend_cny") or 0)
    budget_remaining = float(consumption.get("budget_remaining_cny") or 0)
    return {
        "scope": "消费管理",
        "title": "本月支出、预算剩余、固定/弹性支出与现金流预测",
        "unit": "CNY",
        "source": "MetaDatabase 真实支付宝流水",
        "emptyState": "",
        "periods": ["最近30天", "本月"],
        "series": [
            _series("month_spend_cny", "本月支出", "--pfi-blue", [rolling_30, month_spend]),
            _series("budget_remaining_cny", "预算剩余", "--pfi-teal", [budget_remaining, budget_remaining]),
            _series("fixed_spend_cny", "固定支出", "--pfi-amber", [0.0, fixed_spend]),
            _series("flex_spend_cny", "弹性支出", "--pfi-red", [rolling_30, flex_spend]),
            _series("cashflow_forecast_cny", "现金流预测", "--pfi-blue", [rolling_30, rolling_30]),
        ],
    }


def _read_alipay_transaction_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as file_obj:
            return [dict(row) for row in csv.DictReader(file_obj)]
    except OSError:
        return []


def _manifest_review_count(path: Path) -> int | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return int(payload.get("review_count"))
    except (TypeError, ValueError):
        return None


def _alipay_transactions_path() -> Path:
    return _default_alipay_metadatabase_root() / "processed" / "alipay_transactions.csv"


def _alipay_manifest_path() -> Path:
    return _default_alipay_metadatabase_root() / "processed" / "alipay_import_manifest.json"


def _default_alipay_metadatabase_root() -> Path:
    return Path(__file__).resolve().parents[3] / "MetaDatabase" / "PFI" / "alipay_daily"


def _parse_iso_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def _signed_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fx_rate(currency: str) -> float:
    return FX_TO_CNY.get(str(currency or "CNY").upper(), 1.0)


def _series(series_id: str, label: str, color: str, values: list[float]) -> dict[str, Any]:
    return {"id": series_id, "label": label, "color": color, "unit": "CNY", "values": [round(float(item), 2) for item in values]}


def _non_negative(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return numeric if numeric >= 0 else 0.0


def _clean(value: Any) -> str:
    return str(value or "").strip()
