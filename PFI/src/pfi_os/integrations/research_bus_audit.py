from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pfi_os.config import DATA_DIR, PROJECT_ROOT
from pfi_os.integrations.research_bus import DEFAULT_AI_RESEARCH_ROOT, research_bus_db_path
from pfi_os.integrations.research_bus_api import CHAT_DROPBOX_DIR
from pfi_os.storage import atomic_write_json


AUDIT_OUTPUT_PATH = DATA_DIR / "researchBus" / "ResearchBusInteropAudit.json"
SCHEMA_PATH = PROJECT_ROOT / "docs" / "ResearchBusSchema.json"

REQUIRED_TABLES = (
    "system_state",
    "system_registry",
    "system_artifacts",
    "orchestration_runs",
    "research_reports",
    "validation_tasks",
    "pfi_os_results",
    "holdings_master",
    "holding_symbol_mappings",
    "portfolio_transactions",
    "holding_update_candidates",
    "consumer_behavior_state",
    "independent_validation_runs",
    "independent_validation_shards",
    "bus_api_requests",
    "bus_chat_inputs",
    "bus_system_outbox",
    "bus_heartbeats",
    "sync_events",
)

REQUIRED_REQUEST_TYPES = (
    "sync_all",
    "sync_industry_reports",
    "sync_pfi_os_results",
    "sync_holdings",
    "sync_holding_symbol_mappings",
    "sync_system_registry",
    "sync_system_artifacts",
    "orchestrate_system",
    "independent_validation_dry_run",
    "independent_validation_checksum",
    "pull_pfi_os_results",
    "pull_validation_tasks",
    "pull_independent_validation_runs",
    "pull_consumer_behavior_state",
    "pull_holdings_master",
    "pull_holding_symbol_mappings",
    "pull_system_registry",
    "pull_system_artifacts",
    "pull_orchestration_runs",
    "pull_portfolio_transactions",
    "pull_holding_update_candidates",
    "chat_general_note",
    "holding_update_candidate",
    "confirm_holding_update_candidate",
    "validation_task_from_chat",
    "system_update_request",
)

REQUIRED_REGISTERED_SYSTEMS = (
    "PFIOS",
    "AI-Research-System",
    "finance_ledger",
    "industry_research",
    "policy_intelligence",
    "FIFA-Research-System",
    "GovernmentPolicySystem",
    "IndependentValidation",
)

REQUIRED_ARTIFACT_SYSTEMS = (
    "FIFA-Research-System",
    "GovernmentPolicySystem",
    "finance_ledger",
    "industry_research",
    "policy_intelligence",
)

REQUIRED_AI_BRIDGE_FILES = (
    "PFIOSResultsFromBus.json",
    "ValidationTasksFromBus.json",
    "IndependentValidationRunsFromBus.json",
    "ConsumerBehaviorStateFromBus.json",
    "HoldingsMasterFromBus.json",
    "HoldingSymbolMappingsFromBus.json",
    "PortfolioTransactionsFromBus.json",
    "HoldingUpdateCandidatesFromBus.json",
)

REQUIRED_AI_AUTOMATION_FILES = (
    "scripts/run_report_automation.sh",
    "scripts/watch_research_bus.sh",
)


@dataclass(frozen=True)
class AuditItem:
    requirement: str
    status: str
    evidence: str
    remediation: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "requirement": self.requirement,
            "status": self.status,
            "evidence": self.evidence,
            "remediation": self.remediation,
        }


def run_research_bus_interop_audit(
    db_path: Path | str | None = None,
    *,
    schema_path: Path | str | None = None,
    ai_research_root: Path | str | None = None,
    output_path: Path | str | None = AUDIT_OUTPUT_PATH,
) -> dict[str, Any]:
    target_db = research_bus_db_path(db_path)
    target_schema = Path(schema_path).expanduser() if schema_path is not None else SCHEMA_PATH
    target_ai_root = Path(ai_research_root).expanduser() if ai_research_root is not None else DEFAULT_AI_RESEARCH_ROOT
    items: list[AuditItem] = []
    table_columns: dict[str, list[str]] = {}
    table_counts: dict[str, int] = {}
    schema_payload = _load_schema(target_schema)

    if not target_db.exists():
        items.append(
            AuditItem(
                "共享 SQLite 数据库",
                "Fail",
                f"未找到数据库：{target_db}",
                "运行 scripts/syncResearchBus.sh --json 初始化并同步 ResearchBus。",
            )
        )
        return _finalize(items, target_db, target_schema, target_ai_root, table_counts, output_path)

    try:
        with _connect_readonly(target_db) as conn:
            table_columns = _db_table_columns(conn)
            table_counts = _table_counts(conn, REQUIRED_TABLES)
    except Exception as exc:
        items.append(
            AuditItem(
                "共享 SQLite 数据库",
                "Fail",
                f"数据库无法读取：{exc}",
                "检查 SQLite 文件权限和 WAL/SHM 状态。",
            )
        )
        return _finalize(items, target_db, target_schema, target_ai_root, table_counts, output_path)

    items.extend(_schema_items(target_schema, schema_payload, table_columns))
    items.append(_shared_database_item(target_db, table_columns))
    items.append(_system_registry_item(table_counts, target_db))
    items.append(_system_artifacts_item(table_counts, target_db))
    items.append(_bidirectional_api_item(schema_payload, table_columns, table_counts))
    items.append(_chat_input_item(table_columns, table_counts))
    items.append(_industry_report_item(table_counts))
    items.append(_pfi_os_result_item(table_counts, target_ai_root))
    items.append(_consumer_state_item(table_counts))
    items.append(_holdings_item(table_counts))
    items.append(_independent_validation_item(schema_payload, table_counts))
    items.append(_independent_worker_pool_item(target_db, table_counts))
    items.append(_heartbeat_item(table_counts, target_db))
    items.append(_ai_bridge_artifact_item(target_ai_root))
    items.append(_ai_automation_item(target_ai_root))

    return _finalize(items, target_db, target_schema, target_ai_root, table_counts, output_path)


def _schema_items(schema_path: Path, schema_payload: dict[str, Any], table_columns: dict[str, list[str]]) -> list[AuditItem]:
    if not schema_path.exists():
        return [
            AuditItem(
                "共享 JSON schema 合约",
                "Fail",
                f"未找到 schema 文件：{schema_path}",
                "恢复 docs/ResearchBusSchema.json，并确保两侧 bridge 按该合约更新。",
            )
        ]
    tables = schema_payload.get("tables", {}) if isinstance(schema_payload, dict) else {}
    request_types = schema_payload.get("requestTypes", []) if isinstance(schema_payload, dict) else []
    missing_tables = [table for table in REQUIRED_TABLES if table not in tables]
    missing_requests = [item for item in REQUIRED_REQUEST_TYPES if item not in request_types]
    if missing_tables or missing_requests:
        return [
            AuditItem(
                "共享 JSON schema 合约",
                "Fail",
                f"缺少表：{missing_tables or '无'}；缺少请求类型：{missing_requests or '无'}",
                "更新 docs/ResearchBusSchema.json，并同步 PFIOS 和行研 bridge。",
            )
        ]

    missing_columns: dict[str, list[str]] = {}
    for table, expected_columns in tables.items():
        if table not in table_columns:
            continue
        actual = set(table_columns[table])
        missing = [column for column in expected_columns if column not in actual]
        if missing:
            missing_columns[table] = missing
    if missing_columns:
        return [
            AuditItem(
                "共享 JSON schema 合约",
                "Fail",
                f"数据库字段缺失：{missing_columns}",
                "运行 schema migration 或恢复 _create_schema 中缺失字段。",
            )
        ]
    return [
        AuditItem(
            "共享 JSON schema 合约",
            "Pass",
            f"schema 覆盖 {len(REQUIRED_TABLES)} 张核心表和 {len(REQUIRED_REQUEST_TYPES)} 个请求类型。",
        )
    ]


def _shared_database_item(db_path: Path, table_columns: dict[str, list[str]]) -> AuditItem:
    missing = [table for table in REQUIRED_TABLES if table not in table_columns]
    if missing:
        return AuditItem("共享 SQLite 数据库", "Fail", f"数据库存在，但缺少表：{missing}", "运行 syncResearchBus 初始化 schema。")
    return AuditItem("共享 SQLite 数据库", "Pass", f"数据库可读：{db_path}；核心表完整。")


def _bidirectional_api_item(schema_payload: dict[str, Any], table_columns: dict[str, list[str]], table_counts: dict[str, int]) -> AuditItem:
    api_tables = ["bus_api_requests", "bus_system_outbox", "bus_chat_inputs", "bus_heartbeats"]
    missing = [table for table in api_tables if table not in table_columns]
    if missing:
        return AuditItem("双向 API 和消息队列", "Fail", f"缺少 API 表：{missing}", "恢复 ResearchBus API schema。")
    request_types = schema_payload.get("requestTypes", []) if isinstance(schema_payload, dict) else []
    missing_requests = [item for item in REQUIRED_REQUEST_TYPES if item not in request_types]
    if missing_requests:
        return AuditItem("双向 API 和消息队列", "Fail", f"schema 缺少请求类型：{missing_requests}", "补齐 requestTypes。")
    count = table_counts.get("bus_api_requests", 0)
    status = "Pass" if count else "Warn"
    remediation = "" if count else "提交一次 submit-chat 或 submit-request 验证双向请求落库。"
    return AuditItem("双向 API 和消息队列", status, f"API 表完整；历史请求数={count}。", remediation)


def _system_registry_item(table_counts: dict[str, int], db_path: Path) -> AuditItem:
    count = table_counts.get("system_registry", 0)
    if not count:
        return AuditItem("本地母子系统注册表", "Warn", "system_registry=0。", "运行 scripts/orchestrateSystems.sh register --json。")
    with _connect_readonly(db_path) as conn:
        rows = conn.execute("SELECT system_name, role, status FROM system_registry").fetchall()
    systems = {str(row["system_name"]): {"role": str(row["role"]), "status": str(row["status"])} for row in rows}
    missing = [name for name in REQUIRED_REGISTERED_SYSTEMS if name not in systems]
    if missing:
        return AuditItem("本地母子系统注册表", "Warn", f"registered={sorted(systems)}；缺少：{missing}", "运行 orchestrateSystems register 并确认系统路径。")
    return AuditItem("本地母子系统注册表", "Pass", f"已注册系统：{sorted(systems)}。")


def _system_artifacts_item(table_counts: dict[str, int], db_path: Path) -> AuditItem:
    count = table_counts.get("system_artifacts", 0)
    if not count:
        return AuditItem("子系统产物索引", "Warn", "system_artifacts=0。", "运行 scripts/orchestrateSystems.sh sync-artifacts --json。")
    with _connect_readonly(db_path) as conn:
        rows = conn.execute("SELECT system_name, COUNT(*) AS count FROM system_artifacts GROUP BY system_name").fetchall()
    counts = {str(row["system_name"]): int(row["count"]) for row in rows}
    missing = [name for name in REQUIRED_ARTIFACT_SYSTEMS if counts.get(name, 0) <= 0]
    if missing:
        return AuditItem("子系统产物索引", "Warn", f"artifact_counts={counts}；缺少产物：{missing}", "确认 FIFA/政策系统输出目录并同步产物。")
    return AuditItem("子系统产物索引", "Pass", f"artifact_counts={counts}。")


def _chat_input_item(table_columns: dict[str, list[str]], table_counts: dict[str, int]) -> AuditItem:
    if "bus_chat_inputs" not in table_columns:
        return AuditItem("任意聊天框输入同步", "Fail", "缺少 bus_chat_inputs。", "恢复聊天输入表。")
    if not CHAT_DROPBOX_DIR.exists():
        return AuditItem("任意聊天框输入同步", "Warn", f"投递箱不存在：{CHAT_DROPBOX_DIR}", "运行 researchBusApi.sh dropbox-path 或 process-dropbox 创建目录。")
    count = table_counts.get("bus_chat_inputs", 0)
    status = "Pass" if count else "Warn"
    remediation = "" if count else "通过 researchBusApi.sh submit-chat 或投递箱提交一次文本。"
    return AuditItem("任意聊天框输入同步", status, f"投递箱存在；聊天输入记录数={count}。", remediation)


def _industry_report_item(table_counts: dict[str, int]) -> AuditItem:
    reports = table_counts.get("research_reports", 0)
    tasks = table_counts.get("validation_tasks", 0)
    if reports and tasks:
        return AuditItem("行研报告解析为待验证任务", "Pass", f"research_reports={reports}；validation_tasks={tasks}。")
    return AuditItem(
        "行研报告解析为待验证任务",
        "Warn",
        f"research_reports={reports}；validation_tasks={tasks}。",
        "运行 syncResearchBus.sh --mode industry --json 或 AI research-bus-sync。",
    )


def _pfi_os_result_item(table_counts: dict[str, int], ai_root: Path) -> AuditItem:
    count = table_counts.get("pfi_os_results", 0)
    bridge_path = ai_root / "data" / "report_artifacts" / "research_bus_bridge" / "PFIOSResultsFromBus.json"
    direct_path = ai_root / "data" / "report_artifacts" / "pfi_os_bridge" / "PFIOSResults.json"
    if count and (bridge_path.exists() or direct_path.exists()):
        return AuditItem("PFIOS 回测结论回写行研系统", "Pass", f"pfi_os_results={count}；桥接文件存在。")
    if count:
        return AuditItem(
            "PFIOS 回测结论回写行研系统",
            "Warn",
            f"pfi_os_results={count}；未找到行研桥接文件。",
            "在行研系统运行 python3 -m src.cli research-bus-sync --json。",
        )
    return AuditItem("PFIOS 回测结论回写行研系统", "Warn", "pfi_os_results=0。", "生成或同步至少一份 PFIOS 回测报告。")


def _consumer_state_item(table_counts: dict[str, int]) -> AuditItem:
    count = table_counts.get("consumer_behavior_state", 0)
    if count:
        return AuditItem("消费行为系统状态实时同步", "Pass", f"consumer_behavior_state={count}。")
    return AuditItem(
        "消费行为系统状态实时同步",
        "Warn",
        "consumer_behavior_state=0。",
        "运行 syncResearchBus.sh --mode consumer --json，或确认消费行为系统数据库路径。",
    )


def _holdings_item(table_counts: dict[str, int]) -> AuditItem:
    holdings = table_counts.get("holdings_master", 0)
    mappings = table_counts.get("holding_symbol_mappings", 0)
    transactions = table_counts.get("portfolio_transactions", 0)
    if holdings and mappings:
        return AuditItem("持仓统一主数据表", "Pass", f"holdings_master={holdings}；holding_symbol_mappings={mappings}；portfolio_transactions={transactions}。")
    return AuditItem(
        "持仓统一主数据表",
        "Warn",
        f"holdings_master={holdings}；holding_symbol_mappings={mappings}；portfolio_transactions={transactions}。",
        "同步持仓簿并运行 sync_holding_symbol_mappings。",
    )


def _independent_validation_item(schema_payload: dict[str, Any], table_counts: dict[str, int]) -> AuditItem:
    request_types = schema_payload.get("requestTypes", []) if isinstance(schema_payload, dict) else []
    missing = [item for item in ("independent_validation_dry_run", "independent_validation_checksum") if item not in request_types]
    if missing:
        return AuditItem("独立验证系统任意入口运行", "Fail", f"缺少独立验证请求类型：{missing}", "补齐 schema 和 ResearchBus API handler。")
    runs = table_counts.get("independent_validation_runs", 0)
    status = "Pass" if runs else "Warn"
    remediation = "" if runs else "提交“请运行百万行独立验证”并处理 ResearchBus 请求。"
    return AuditItem("独立验证系统任意入口运行", status, f"请求类型完整；independent_validation_runs={runs}。", remediation)


def _independent_worker_pool_item(db_path: Path, table_counts: dict[str, int]) -> AuditItem:
    if table_counts.get("independent_validation_runs", 0) <= 0:
        return AuditItem("独立验证两级架构与本机 worker pool", "Warn", "尚无 independent_validation_runs。", "运行百亿 dry-run 或 checksum worker pool smoke。")
    with _connect_readonly(db_path) as conn:
        row = conn.execute(
            """
            SELECT total_rows, shard_count, payload_json
            FROM independent_validation_runs
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ).fetchone()
    if not row:
        return AuditItem("独立验证两级架构与本机 worker pool", "Warn", "没有可读运行记录。", "运行独立验证。")
    payload = _safe_json_text(row["payload_json"])
    tier = str(payload.get("execution_tier", ""))
    worker_count = int(payload.get("worker_count") or 1)
    if int(row["total_rows"]) >= 10_000_000_000 or tier in {"planning_manifest", "local_worker_pool"}:
        return AuditItem(
            "独立验证两级架构与本机 worker pool",
            "Pass",
            f"latest_total_rows={int(row['total_rows'])}；shards={int(row['shard_count'])}；execution_tier={tier or 'legacy'}；worker_count={worker_count}。",
        )
    return AuditItem(
        "独立验证两级架构与本机 worker pool",
        "Warn",
        f"latest_total_rows={int(row['total_rows'])}；execution_tier={tier or 'legacy'}。",
        "运行 scripts/runIndependentValidation.sh run --synthetic-rows 10000000000 --rows-per-shard 100000000 --mode dry_run --json。",
    )


def _heartbeat_item(table_counts: dict[str, int], db_path: Path) -> AuditItem:
    count = table_counts.get("bus_heartbeats", 0)
    if not count:
        return AuditItem("系统心跳与内部状态", "Warn", "bus_heartbeats=0。", "运行双方 heartbeat 命令。")
    with _connect_readonly(db_path) as conn:
        rows = conn.execute("SELECT system_name FROM bus_heartbeats ORDER BY system_name").fetchall()
    systems = [str(row["system_name"]) for row in rows]
    expected = {"ResearchBus", "AI-Research-System"}
    missing = sorted(expected - set(systems))
    if missing:
        return AuditItem("系统心跳与内部状态", "Warn", f"已有心跳：{systems}；缺少：{missing}", "运行 syncResearchSystemsOnce.sh 或双方 heartbeat 命令。")
    return AuditItem("系统心跳与内部状态", "Pass", f"已有心跳：{systems}。")


def _ai_bridge_artifact_item(ai_root: Path) -> AuditItem:
    if not ai_root.exists():
        return AuditItem("行研系统桥接输出", "Warn", f"未找到行研系统目录：{ai_root}", "确认 AI-Research-System 路径。")
    bridge_dir = ai_root / "data" / "report_artifacts" / "research_bus_bridge"
    missing = [name for name in REQUIRED_AI_BRIDGE_FILES if not (bridge_dir / name).exists()]
    if missing:
        return AuditItem("行研系统桥接输出", "Warn", f"桥接目录={bridge_dir}；缺少文件：{missing}", "在行研系统运行 research-bus-sync。")
    invalid = [name for name in REQUIRED_AI_BRIDGE_FILES if not _json_file_valid(bridge_dir / name)]
    if invalid:
        return AuditItem("行研系统桥接输出", "Fail", f"桥接 JSON 无法解析：{invalid}", "重新生成桥接文件。")
    return AuditItem("行研系统桥接输出", "Pass", f"桥接文件完整：{bridge_dir}。")


def _ai_automation_item(ai_root: Path) -> AuditItem:
    if not ai_root.exists():
        return AuditItem("行研系统 automation 保留", "Warn", f"未找到行研系统目录：{ai_root}", "确认 AI-Research-System 路径。")
    missing = [relative for relative in REQUIRED_AI_AUTOMATION_FILES if not (ai_root / relative).exists()]
    if missing:
        return AuditItem("行研系统 automation 保留", "Warn", f"缺少 automation 文件：{missing}", "恢复行研系统 automation 脚本。")
    return AuditItem(
        "行研系统 automation 保留",
        "Pass",
        "关键 automation 脚本存在：" + "；".join(str(ai_root / relative) for relative in REQUIRED_AI_AUTOMATION_FILES),
    )


def _finalize(
    items: list[AuditItem],
    db_path: Path,
    schema_path: Path,
    ai_root: Path,
    table_counts: dict[str, int],
    output_path: Path | str | None,
) -> dict[str, Any]:
    status = "Pass"
    if any(item.status == "Fail" for item in items):
        status = "Fail"
    elif any(item.status == "Warn" for item in items):
        status = "Warn"
    payload = {
        "schema": "ResearchBusInteropAuditV1",
        "generated_at": _now(),
        "status": status,
        "db_path": str(db_path),
        "schema_path": str(schema_path),
        "ai_research_root": str(ai_root),
        "table_counts": table_counts,
        "summary": {
            "pass": sum(1 for item in items if item.status == "Pass"),
            "warn": sum(1 for item in items if item.status == "Warn"),
            "fail": sum(1 for item in items if item.status == "Fail"),
        },
        "items": [item.to_dict() for item in items],
    }
    if output_path is not None:
        atomic_write_json(Path(output_path).expanduser(), payload)
        payload["output_path"] = str(Path(output_path).expanduser())
    return payload


def _load_schema(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _db_table_columns(conn: sqlite3.Connection) -> dict[str, list[str]]:
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    result: dict[str, list[str]] = {}
    for row in tables:
        name = str(row["name"])
        columns = conn.execute(f"PRAGMA table_info({name})").fetchall()
        result[name] = [str(column["name"]) for column in columns]
    return result


def _table_counts(conn: sqlite3.Connection, tables: tuple[str, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    available = set(_db_table_columns(conn))
    for table in tables:
        if table not in available:
            counts[table] = 0
            continue
        counts[table] = int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])
    return counts


def _json_file_valid(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except Exception:
        return False


def _safe_json_text(value: object) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


@contextmanager
def _connect_readonly(path: Path):
    target = Path(path).expanduser()
    conn = None
    try:
        conn = _open_readonly_connection(target)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn is not None:
            conn.close()


def _open_readonly_connection(path: Path) -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
        conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()
        return conn
    except sqlite3.OperationalError as exc:
        if "conn" in locals():
            conn.close()
        if not path.exists() or "unable to open database file" not in str(exc).lower():
            raise
        conn = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True, timeout=30)
        conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()
        return conn


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
