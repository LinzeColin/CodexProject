from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import DATA_DIR, PROJECT_ROOT
from pfi_os.integrations.permissions import assert_system_permission
from pfi_os.integrations.research_bus import initialize_research_bus, research_bus_db_path
from pfi_os.integrations.workspace_systems import WorkspaceSystemSummary, load_workspace_system_summaries
from pfi_os.storage import atomic_write_text


DEFAULT_WORKSPACE_ROOT = PROJECT_ROOT
DEFAULT_SYSTEMS_ROOT = DEFAULT_WORKSPACE_ROOT / "systems"
DEFAULT_REPORT_ROOT = DEFAULT_WORKSPACE_ROOT / "reports"
ORCHESTRATION_LOG_DIR = DATA_DIR / "researchBus" / "orchestrationLogs"


TRUTHY_ENV_VALUES = {"1", "true", "yes", "y", "on", "allow", "allowed"}


def _configured_path(env_name: str, default: Path) -> Path:
    raw_value = os.environ.get(env_name, "").strip()
    return Path(raw_value).expanduser() if raw_value else default


def _workspace_root() -> Path:
    return _configured_path("PFI_WORKSPACE_ROOT", DEFAULT_WORKSPACE_ROOT)


def _systems_root() -> Path:
    return _configured_path("PFI_SYSTEMS_ROOT", _workspace_root() / "systems")


def _report_root() -> Path:
    return _configured_path("PFI_REPORT_ROOT", _workspace_root() / "reports")


@dataclass(frozen=True)
class ChildSystemDefinition:
    system_name: str
    role: str
    root_path: str
    standalone_command: tuple[str, ...]
    health_command: tuple[str, ...]
    sync_command: tuple[str, ...]
    capabilities: tuple[str, ...]
    output_globs: tuple[str, ...]
    environment: dict[str, str]
    payload: dict[str, Any]

    def to_record(self) -> dict[str, Any]:
        return {
            "system_name": self.system_name,
            "role": self.role,
            "root_path": self.root_path,
            "standalone_command_json": list(self.standalone_command),
            "health_command_json": list(self.health_command),
            "sync_command_json": list(self.sync_command),
            "capabilities_json": list(self.capabilities),
            "outputs_json": list(self.output_globs),
            "payload_json": {"environment": self.environment, **self.payload},
        }


@dataclass(frozen=True)
class OrchestrationRun:
    run_id: str
    parent_system: str
    target_system: str
    action: str
    mode: str
    status: str
    started_at: str
    completed_at: str
    command: tuple[str, ...]
    exit_code: int
    stdout_path: str
    stderr_path: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["command_json"] = list(payload.pop("command"))
        payload["payload_json"] = payload.pop("payload")
        return payload


def default_child_systems() -> tuple[ChildSystemDefinition, ...]:
    fifa_root = _configured_path("PFI_FIFA_ROOT", _systems_root() / "fifa_research")
    fifa_output_root = _configured_path("PFI_FIFA_OUTPUT_ROOT", _report_root() / "fifa_research")
    government_policy_root = _configured_path("PFI_GOVERNMENT_POLICY_ROOT", _systems_root() / "policy_intelligence")
    ai_research_root = _configured_path("PFI_AI_RESEARCH_ROOT", _systems_root() / "industry_research")
    legacy_systems = (
        ChildSystemDefinition(
            system_name="PFIOS",
            role="MotherSystem",
            root_path=str(PROJECT_ROOT),
            standalone_command=("./scripts/startPFI.sh",),
            health_command=("./scripts/statusPFI.sh",),
            sync_command=("./scripts/syncResearchBus.sh", "--json"),
            capabilities=("mother_orchestrator", "quant_backtest", "research_bus", "report_center", "holdings"),
            output_globs=("data/researchBus/*.json", "docs/*.md"),
            environment={},
            payload={"boundary": "研究验证，不接实盘交易。"},
        ),
        ChildSystemDefinition(
            system_name="AI-Research-System",
            role="ChildSystem",
            root_path=str(ai_research_root),
            standalone_command=("python3", "-m", "src.cli", "research-bus-sync", "--json"),
            health_command=("python3", "-m", "src.cli", "research-bus-sync", "--json"),
            sync_command=("python3", "-m", "src.cli", "research-bus-sync", "--json"),
            capabilities=("industry_research", "report_bridge", "validation_task_publish", "pfi_os_result_pull"),
            output_globs=("data/report_artifacts/research_bus_bridge/*.json", "data/report_artifacts/pfi_os_bridge/*.json"),
            environment={"PYTHONDONTWRITEBYTECODE": "1"},
            payload={"boundary": "行研生成和证据链整理，不输出实盘指令。"},
        ),
        ChildSystemDefinition(
            system_name="FIFA-Research-System",
            role="ChildSystem",
            root_path=str(fifa_root),
            standalone_command=("./scripts/run_tab_fifa_daily_automation.sh",),
            health_command=("./scripts/verify_fifa_automation_readiness.sh", "--hermetic"),
            sync_command=("./scripts/run_tab_fifa_daily_automation.sh", "--verify-only"),
            capabilities=("fifa_research", "tab_readonly_refresh", "public_source_audit", "pdf_report"),
            output_globs=(
                str(fifa_output_root / "latest_commit.json"),
                str(fifa_output_root / "automation_run_latest.json"),
                str(fifa_output_root / "report_index_latest.json"),
                str(fifa_output_root / "*.pdf"),
                str(fifa_output_root / "*latest*.json"),
            ),
            environment={"PYTHONDONTWRITEBYTECODE": "1"},
            payload={"boundary": "只读公开赔率/公开资料研究，不登录、不下注、不加入 Bet Slip。"},
        ),
        ChildSystemDefinition(
            system_name="GovernmentPolicySystem",
            role="ChildSystem",
            root_path=str(government_policy_root),
            standalone_command=("./scripts/run_policy_report.sh",),
            health_command=("python3", "-m", "source_registry", "--db", "data/source_registry.sqlite", "status", "--json"),
            sync_command=("python3", "-m", "source_registry", "--db", "data/source_registry.sqlite", "readiness", "--json"),
            capabilities=("policy_document_interpretation", "source_authority_scoring", "quality_gate", "pdf_report"),
            output_globs=("reports/*.pdf", "reports/*.md", "data/automation/latest_run.json", "data/monitor/latest_status.json"),
            environment={"PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
            payload={"boundary": "政策文件解读和质量门禁；证据不足时保留 quality_gap。"},
        ),
        ChildSystemDefinition(
            system_name="IndependentValidation",
            role="WorkerPoolChildSystem",
            root_path=str(PROJECT_ROOT),
            standalone_command=(
                "./scripts/runIndependentValidation.sh",
                "run",
                "--synthetic-rows",
                "10000000000",
                "--rows-per-shard",
                "100000000",
                "--mode",
                "dry_run",
                "--json",
            ),
            health_command=("./scripts/runIndependentValidation.sh", "status", "--json"),
            sync_command=("./scripts/runIndependentValidation.sh", "status", "--json"),
            capabilities=("independent_validation", "ten_billion_scale_plan", "local_worker_pool", "checksum"),
            output_globs=("data/independentValidation/*.json",),
            environment={},
            payload={"tiers": ["planning_manifest", "local_worker_pool"], "max_planned_rows": 10_000_000_000},
        ),
    )
    return (*legacy_systems, *_workspace_child_systems())


def _workspace_child_systems() -> tuple[ChildSystemDefinition, ...]:
    definitions: list[ChildSystemDefinition] = []
    summary_command = str(PROJECT_ROOT / "scripts" / "syncWorkspaceSystemSummaries.sh")
    for summary in load_workspace_system_summaries(systems_root=_systems_root()):
        definitions.append(
            ChildSystemDefinition(
                system_name=summary.system_id,
                role="WorkspaceChildSystem",
                root_path=str(_systems_root() / summary.system_id),
                standalone_command=(summary_command, "--system", summary.system_id, "--json"),
                health_command=(summary_command, "--system", summary.system_id, "--check", "--json"),
                sync_command=(summary_command, "--system", summary.system_id, "--json"),
                capabilities=_workspace_capabilities(summary),
                output_globs=_workspace_output_globs(summary),
                environment={"PYTHONDONTWRITEBYTECODE": "1"},
                payload={
                    "boundary": "workspace manifest summary only; no private runtime data copied",
                    "manifest_summary": summary.to_dict(),
                },
            )
        )
    return tuple(definitions)


def _workspace_capabilities(summary: WorkspaceSystemSummary) -> tuple[str, ...]:
    defaults = ("workspace_manifest", "research_bus_summary", "low_token_status")
    if summary.system_id == "finance_ledger":
        return (*defaults, "finance_ledger", "consumption_analysis")
    if summary.system_id == "industry_research":
        return (*defaults, "industry_research", "validation_task_publish")
    if summary.system_id == "policy_intelligence":
        return (*defaults, "policy_intelligence", "quality_gate_summary")
    return defaults


def _workspace_output_globs(summary: WorkspaceSystemSummary) -> tuple[str, ...]:
    return (
        "SYSTEM_MANIFEST.json",
        "README.md",
        "source/README.md",
        "source/HANDOFF.md",
        "source/data/sample/*.json",
        "samples/*.csv",
        "samples/*.json",
    )


def register_default_systems(db_path: Path | str | None = None) -> dict[str, Any]:
    return register_child_systems(default_child_systems(), db_path=db_path)


def register_child_systems(
    systems: tuple[ChildSystemDefinition, ...] | list[ChildSystemDefinition],
    *,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    now = _now()
    registered = 0
    warnings: list[str] = []
    with _connect(target_db) as conn:
        for system in systems:
            exists = Path(system.root_path).expanduser().exists()
            status = "Ready" if exists else "MissingRoot"
            if not exists:
                warnings.append(f"{system.system_name} root missing: {system.root_path}")
            _upsert_system_registry(conn, system, status=status, now=now)
            _upsert_system_state(conn, system, status=status, now=now)
            registered += 1
        _record_event(conn, "system_registry_sync", "PFIOS", "ResearchBus", "success", f"registered_systems={registered}", {"warnings": warnings})
    return {"registered_systems": registered, "warnings": warnings, "db_path": str(target_db)}


def sync_default_system_artifacts(db_path: Path | str | None = None, *, limit_per_system: int = 200) -> dict[str, Any]:
    return sync_child_system_artifacts(default_child_systems(), db_path=db_path, limit_per_system=limit_per_system)


def sync_child_system_artifacts(
    systems: tuple[ChildSystemDefinition, ...] | list[ChildSystemDefinition],
    *,
    db_path: Path | str | None = None,
    limit_per_system: int = 200,
) -> dict[str, Any]:
    target_db = initialize_research_bus(db_path)
    artifact_count = 0
    warnings: list[str] = []
    now = _now()
    with _connect(target_db) as conn:
        for system in systems:
            paths = _artifact_paths(system, limit=max(0, int(limit_per_system)))
            for path in paths:
                try:
                    _upsert_system_artifact(conn, system.system_name, path, now=now)
                    artifact_count += 1
                except Exception as exc:
                    warnings.append(f"{system.system_name} artifact skipped: {path}: {exc}")
        _record_event(conn, "system_artifacts_sync", "PFIOS", "ResearchBus", "success", f"system_artifacts={artifact_count}", {"warnings": warnings})
    return {"system_artifacts": artifact_count, "warnings": warnings, "db_path": str(target_db)}


def orchestrate_child_system(
    system_name: str,
    *,
    action: str = "health",
    execute: bool = False,
    db_path: Path | str | None = None,
    timeout_seconds: int = 120,
    requester_system: str = "PFIOS",
    approval_token: str = "",
) -> OrchestrationRun:
    target_db = initialize_research_bus(db_path)
    systems = {system.system_name: system for system in default_child_systems()}
    if system_name not in systems:
        raise ValueError(f"Unknown child system: {system_name}")
    system = systems[system_name]
    normalized_action = str(action or "health").strip().lower()
    command = _command_for_action(system, normalized_action)
    started_at = _now()
    run_id = _stable_id("orchestrationRun", system.system_name, normalized_action, started_at, command)
    mode = "execute" if execute else "dry_run"
    stdout_path = ""
    stderr_path = ""
    exit_code = 0
    payload: dict[str, Any] = {
        "root_path": system.root_path,
        "role": system.role,
        "capabilities": list(system.capabilities),
        "requester_system": requester_system,
        "authorization": "dry_run" if not execute else "pending_execution_gate",
    }
    if execute:
        _assert_execution_allowed(system, normalized_action, requester_system=requester_system, approval_token=approval_token)
        payload["authorization"] = "execution_allowed"
        stdout_path, stderr_path = _log_paths(run_id)
        exit_code = _run_command(system, command, stdout_path=Path(stdout_path), stderr_path=Path(stderr_path), timeout_seconds=timeout_seconds)
        status = "Completed" if exit_code == 0 else "Failed"
    else:
        status = "Planned"
        payload["message"] = "dry_run 只登记母系统将调用的命令；加 --execute 才实际运行子系统。"
    completed_at = _now()
    result = OrchestrationRun(
        run_id=run_id,
        parent_system="PFIOS",
        target_system=system.system_name,
        action=normalized_action,
        mode=mode,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        command=tuple(command),
        exit_code=exit_code,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        payload=payload,
    )
    with _connect(target_db) as conn:
        _upsert_orchestration_run(conn, result)
        _record_event(
            conn,
            "system_orchestration",
            "PFIOS",
            system.system_name,
            "success" if status in {"Planned", "Completed"} else "failed",
            f"{system.system_name} {normalized_action} {status}",
            result.to_dict(),
        )
    return result


def system_registry_frame(db_path: Path | str | None = None) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute("SELECT * FROM system_registry ORDER BY role, system_name").fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def system_artifacts_frame(db_path: Path | str | None = None, limit: int = 500) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT system_name, artifact_type, title, path, size_bytes, modified_at, updated_at
            FROM system_artifacts
            ORDER BY modified_at DESC, updated_at DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def orchestration_runs_frame(db_path: Path | str | None = None, limit: int = 500) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path)
    with _connect(target_db) as conn:
        rows = conn.execute(
            """
            SELECT run_id, parent_system, target_system, action, mode, status, started_at,
                   completed_at, command_json, exit_code, stdout_path, stderr_path, updated_at
            FROM orchestration_runs
            ORDER BY updated_at DESC, started_at DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def _command_for_action(system: ChildSystemDefinition, action: str) -> tuple[str, ...]:
    if action in {"health", "status", "check"}:
        return system.health_command
    if action in {"sync", "refresh"}:
        return system.sync_command
    if action in {"standalone", "run", "start"}:
        return system.standalone_command
    raise ValueError(f"Unsupported orchestration action: {action}")


def _assert_execution_allowed(
    system: ChildSystemDefinition,
    action: str,
    *,
    requester_system: str,
    approval_token: str,
) -> None:
    requester = str(requester_system or "").strip() or "UnknownRequester"
    approval_id = str(approval_token or os.environ.get("PFI_ORCHESTRATOR_APPROVAL_ID", "")).strip()
    assert_system_permission(
        requester,
        system.system_name,
        f"system.{action}",
        action=action,
        execute=True,
        approval_id=approval_id,
    )
    allowed_callers = _allowed_execute_callers()
    if requester not in allowed_callers:
        raise PermissionError(
            f"Execution denied: requester={requester} is not allowed to execute {system.system_name}.{action}."
        )
    if os.environ.get("PFI_ORCHESTRATOR_EXECUTE_ALLOWED", "").strip().lower() not in TRUTHY_ENV_VALUES:
        raise PermissionError(
            "Execution denied: set PFI_ORCHESTRATOR_EXECUTE_ALLOWED=1 only for an approved local run."
        )
    expected_token = os.environ.get("PFI_ORCHESTRATOR_APPROVAL_TOKEN", "").strip()
    if expected_token and str(approval_token or "") != expected_token:
        raise PermissionError("Execution denied: approval token mismatch.")


def _allowed_execute_callers() -> set[str]:
    raw = os.environ.get("PFI_ORCHESTRATOR_EXECUTE_CALLERS", "PFIOS,PFI_OS,ResearchBus")
    return {item.strip() for item in raw.split(",") if item.strip()}


def _artifact_paths(system: ChildSystemDefinition, *, limit: int) -> list[Path]:
    paths: list[Path] = []
    root = Path(system.root_path).expanduser()
    for pattern in system.output_globs:
        pattern_path = Path(pattern).expanduser()
        matches = sorted(
            (pattern_path.parent.glob(pattern_path.name) if pattern_path.is_absolute() else root.glob(pattern)),
            key=lambda item: item.stat().st_mtime if item.exists() else 0,
            reverse=True,
        )
        for path in matches:
            if path.is_file() and path not in paths:
                paths.append(path)
            if limit and len(paths) >= limit:
                break
        if limit and len(paths) >= limit:
            break
    return paths


def _run_command(
    system: ChildSystemDefinition,
    command: tuple[str, ...],
    *,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
) -> int:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(system.environment)
    root = Path(system.root_path).expanduser()
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        try:
            completed = subprocess.run(
                list(command),
                cwd=str(root),
                env=env,
                stdout=stdout,
                stderr=stderr,
                timeout=max(1, int(timeout_seconds)),
                check=False,
                text=True,
            )
            return int(completed.returncode)
        except subprocess.TimeoutExpired:
            stderr.write(f"\nTIMEOUT after {timeout_seconds} seconds\n")
            return 124


def _upsert_system_registry(conn: sqlite3.Connection, system: ChildSystemDefinition, *, status: str, now: str) -> None:
    record = system.to_record()
    conn.execute(
        """
        INSERT INTO system_registry(
            system_name, role, root_path, standalone_command_json, health_command_json,
            sync_command_json, capabilities_json, outputs_json, status, last_seen_at,
            payload_json, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(system_name) DO UPDATE SET
            role=excluded.role,
            root_path=excluded.root_path,
            standalone_command_json=excluded.standalone_command_json,
            health_command_json=excluded.health_command_json,
            sync_command_json=excluded.sync_command_json,
            capabilities_json=excluded.capabilities_json,
            outputs_json=excluded.outputs_json,
            status=excluded.status,
            last_seen_at=excluded.last_seen_at,
            payload_json=excluded.payload_json,
            updated_at=excluded.updated_at
        """,
        (
            system.system_name,
            system.role,
            system.root_path,
            _json_dumps(record["standalone_command_json"]),
            _json_dumps(record["health_command_json"]),
            _json_dumps(record["sync_command_json"]),
            _json_dumps(record["capabilities_json"]),
            _json_dumps(record["outputs_json"]),
            status,
            now,
            _json_dumps(record["payload_json"]),
            now,
        ),
    )


def _upsert_system_state(conn: sqlite3.Connection, system: ChildSystemDefinition, *, status: str, now: str) -> None:
    summary = {"role": system.role, "capabilities": list(system.capabilities), "orchestrated_by": "PFIOS"}
    if system.payload:
        summary.update({key: value for key, value in system.payload.items() if key in {"boundary", "manifest_summary", "tiers", "max_planned_rows"}})
    conn.execute(
        """
        INSERT INTO system_state(system_name, status, root_path, last_sync_at, summary_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(system_name) DO UPDATE SET
            status=excluded.status,
            root_path=excluded.root_path,
            last_sync_at=excluded.last_sync_at,
            summary_json=excluded.summary_json
        """,
        (
            system.system_name,
            status,
            system.root_path,
            now,
            _json_dumps(summary),
        ),
    )


def _upsert_system_artifact(conn: sqlite3.Connection, system_name: str, path: Path, *, now: str) -> None:
    stat = path.stat()
    modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    artifact_type = _artifact_type(path)
    artifact_id = _stable_id("systemArtifact", system_name, str(path.resolve()), modified_at, stat.st_size)
    conn.execute(
        """
        INSERT INTO system_artifacts(
            artifact_id, system_name, artifact_type, title, path, content_hash,
            size_bytes, modified_at, payload_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(artifact_id) DO UPDATE SET
            artifact_type=excluded.artifact_type,
            title=excluded.title,
            path=excluded.path,
            content_hash=excluded.content_hash,
            size_bytes=excluded.size_bytes,
            modified_at=excluded.modified_at,
            payload_json=excluded.payload_json,
            updated_at=excluded.updated_at
        """,
        (
            artifact_id,
            system_name,
            artifact_type,
            path.name,
            str(path),
            _hash_file(path),
            int(stat.st_size),
            modified_at,
            _json_dumps({"suffix": path.suffix.lower()}),
            now,
            now,
        ),
    )


def _upsert_orchestration_run(conn: sqlite3.Connection, result: OrchestrationRun) -> None:
    conn.execute(
        """
        INSERT INTO orchestration_runs(
            run_id, parent_system, target_system, action, mode, status, started_at,
            completed_at, command_json, exit_code, stdout_path, stderr_path, payload_json, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            status=excluded.status,
            completed_at=excluded.completed_at,
            exit_code=excluded.exit_code,
            stdout_path=excluded.stdout_path,
            stderr_path=excluded.stderr_path,
            payload_json=excluded.payload_json,
            updated_at=excluded.updated_at
        """,
        (
            result.run_id,
            result.parent_system,
            result.target_system,
            result.action,
            result.mode,
            result.status,
            result.started_at,
            result.completed_at,
            _json_dumps(result.command),
            result.exit_code,
            result.stdout_path,
            result.stderr_path,
            _json_dumps(result.payload),
            _now(),
        ),
    )


def _record_event(
    conn: sqlite3.Connection,
    event_type: str,
    source_system: str,
    target_system: str,
    status: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> None:
    event_id = _stable_id("event", event_type, source_system, target_system, status, message, _now())
    conn.execute(
        """
        INSERT INTO sync_events(event_id, event_type, source_system, target_system, status, message, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, event_type, source_system, target_system, status, message, _json_dumps(payload or {}), _now()),
    )


def _connect(path: Path | str):
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        yield_conn = conn
        return _ConnectionContext(yield_conn)
    except Exception:
        conn.close()
        raise


class _ConnectionContext:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def __enter__(self) -> sqlite3.Connection:
        return self.conn

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.conn.commit()
        self.conn.close()


def _artifact_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf_report"
    if suffix in {".md", ".txt"}:
        return "text_report"
    if suffix == ".json":
        return "json_state"
    if suffix in {".html", ".htm"}:
        return "dashboard"
    return suffix.lstrip(".") or "artifact"


def _log_paths(run_id: str) -> tuple[str, str]:
    ORCHESTRATION_LOG_DIR.mkdir(parents=True, exist_ok=True)
    return (
        str(ORCHESTRATION_LOG_DIR / f"{run_id}.stdout.log"),
        str(ORCHESTRATION_LOG_DIR / f"{run_id}.stderr.log"),
    )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "\n".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
