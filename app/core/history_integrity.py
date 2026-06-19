from __future__ import annotations

import fnmatch
import hashlib
import json
import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.db import connect, init_db


PROTECTED_TABLES = (
    "run_log",
    "asset_master",
    "source_log",
    "fund_nav_snapshot",
    "market_kline_snapshot",
    "fund_rule_snapshot",
    "position_snapshot",
    "baseline_snapshot",
    "score_snapshot",
    "recommendation_snapshot",
    "comparison_snapshot",
    "audit_log",
    "notification_log",
    "missing_data_log",
    "manual_review_queue",
    "manual_review_decision",
    "conflict_log",
    "decision_record",
    "rebalance_event_log",
    "automation_tick_log",
    "source_evidence_audit_snapshot",
)

PROTECTED_FILE_PATTERNS = (
    "data/reports/*_report.md",
    "data/reports/*_report.html",
    "data/notifications/**",
    "data/moomoo/**",
)


@dataclass(frozen=True)
class IntegrityViolation:
    area: str
    item: str
    violation_type: str
    detail: str


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _timestamp(settings: Settings, value: float) -> str:
    return datetime.fromtimestamp(value, ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _table_names(conn) -> set[str]:
    return {
        str(row[0])
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if not str(row[0]).startswith("sqlite_")
    }


def _table_columns(conn, table: str) -> list[dict[str, object]]:
    return [dict(row) for row in conn.execute(f'PRAGMA table_info("{table}")')]


def _identity_columns(columns: list[dict[str, object]]) -> list[str]:
    pk_columns = [str(column["name"]) for column in columns if int(column.get("pk") or 0) > 0]
    if pk_columns:
        return pk_columns
    names = [str(column["name"]) for column in columns]
    if "id" in names:
        return ["id"]
    if "run_id" in names and "asset_id" in names:
        return ["run_id", "asset_id"]
    if "run_id" in names:
        return ["run_id"]
    return names


def _row_identity(row: dict[str, object], identity_columns: list[str]) -> str:
    return "|".join(f"{column}={row.get(column)}" for column in identity_columns)


def _table_manifest(conn, table: str) -> dict[str, object]:
    columns = _table_columns(conn, table)
    column_names = [str(column["name"]) for column in columns]
    identity = _identity_columns(columns)
    order_by = ", ".join(f'"{column}"' for column in identity if column in column_names) or "rowid"
    rows: dict[str, str] = {}
    for sqlite_row in conn.execute(f'SELECT * FROM "{table}" ORDER BY {order_by}'):
        row = dict(sqlite_row)
        row_id = _row_identity(row, identity)
        if row_id in rows:
            row_id = f"{row_id}|row_hash={_sha256_text(_canonical_json(row))[:12]}"
        rows[row_id] = _sha256_text(_canonical_json(row))
    table_material = "\n".join(f"{row_id}:{row_hash}" for row_id, row_hash in sorted(rows.items()))
    return {
        "columns": column_names,
        "identity_columns": identity,
        "row_count": len(rows),
        "table_hash": _sha256_text(table_material),
        "rows": rows,
    }


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _protected_files(settings: Settings) -> dict[str, dict[str, object]]:
    files: dict[str, dict[str, object]] = {}
    for path in sorted(settings.root_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(settings.root_dir).as_posix()
        if not _matches(rel, PROTECTED_FILE_PATTERNS):
            continue
        stat = path.stat()
        files[rel] = {
            "sha256": _sha256_bytes(path.read_bytes()),
            "size_bytes": stat.st_size,
            "file_created_at": _timestamp(settings, getattr(stat, "st_birthtime", stat.st_ctime)),
            "file_modified_at": _timestamp(settings, stat.st_mtime),
            "file_metadata_changed_at": _timestamp(settings, stat.st_ctime),
        }
    return files


def build_history_manifest(settings: Settings) -> dict[str, object]:
    init_db(settings.db_path)
    sqlite_tables: dict[str, object] = {}
    with connect(settings.db_path) as conn:
        existing = _table_names(conn)
        for table in PROTECTED_TABLES:
            if table in existing:
                sqlite_tables[table] = _table_manifest(conn, table)
    return {
        "schema_version": 1,
        "generated_at": _now(settings),
        "db_path": str(settings.db_path),
        "protected_tables": list(sqlite_tables),
        "protected_file_patterns": list(PROTECTED_FILE_PATTERNS),
        "sqlite": {"tables": sqlite_tables},
        "files": _protected_files(settings),
    }


def _compare_table_rows(
    table: str,
    baseline_table: dict[str, object],
    current_table: dict[str, object] | None,
) -> list[IntegrityViolation]:
    violations: list[IntegrityViolation] = []
    if current_table is None:
        return [
            IntegrityViolation(
                area="sqlite",
                item=table,
                violation_type="table_missing",
                detail="Protected table from baseline is missing in current database.",
            )
        ]
    baseline_rows = baseline_table.get("rows") if isinstance(baseline_table.get("rows"), dict) else {}
    current_rows = current_table.get("rows") if isinstance(current_table.get("rows"), dict) else {}
    for row_id, baseline_hash in baseline_rows.items():
        current_hash = current_rows.get(row_id)
        if current_hash is None:
            violations.append(
                IntegrityViolation("sqlite", f"{table}:{row_id}", "row_deleted", "Previously observed history row is missing.")
            )
        elif current_hash != baseline_hash:
            violations.append(
                IntegrityViolation("sqlite", f"{table}:{row_id}", "row_changed", "Previously observed history row hash changed.")
            )
    return violations


def compare_manifests(baseline: dict[str, object], current: dict[str, object]) -> list[IntegrityViolation]:
    violations: list[IntegrityViolation] = []
    baseline_tables = ((baseline.get("sqlite") or {}).get("tables") or {}) if isinstance(baseline.get("sqlite"), dict) else {}
    current_tables = ((current.get("sqlite") or {}).get("tables") or {}) if isinstance(current.get("sqlite"), dict) else {}
    if isinstance(baseline_tables, dict) and isinstance(current_tables, dict):
        for table, baseline_table in baseline_tables.items():
            if isinstance(baseline_table, dict):
                current_table = current_tables.get(table)
                violations.extend(_compare_table_rows(table, baseline_table, current_table if isinstance(current_table, dict) else None))

    baseline_files = baseline.get("files") if isinstance(baseline.get("files"), dict) else {}
    current_files = current.get("files") if isinstance(current.get("files"), dict) else {}
    for rel, baseline_file in baseline_files.items():
        if not isinstance(baseline_file, dict):
            continue
        current_file = current_files.get(rel) if isinstance(current_files, dict) else None
        if not isinstance(current_file, dict):
            violations.append(IntegrityViolation("file", str(rel), "file_deleted", "Previously observed historical artifact is missing."))
        elif current_file.get("sha256") != baseline_file.get("sha256"):
            violations.append(IntegrityViolation("file", str(rel), "file_changed", "Previously observed historical artifact hash changed."))
    return violations


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _artifact_type(rel_path: str) -> str:
    if rel_path.endswith("_report.md"):
        return "analysis_report_markdown"
    if rel_path.endswith("_report.html"):
        return "analysis_report_html"
    if rel_path.startswith("data/notifications/"):
        return "notification_artifact"
    if rel_path.startswith("data/moomoo/") and rel_path.endswith("snapshot.json"):
        return "moomoo_snapshot"
    if rel_path.startswith("data/moomoo/"):
        return "moomoo_raw_data"
    return "historical_artifact"


def _rel_from_path_value(settings: Settings, value: object) -> str:
    if not value:
        return ""
    path = Path(str(value))
    if not path.is_absolute():
        path = settings.root_dir / path
    try:
        return path.relative_to(settings.root_dir).as_posix()
    except ValueError:
        return str(value)


def _run_lookup(settings: Settings) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    by_run_id: dict[str, dict[str, object]] = {}
    by_artifact: dict[str, dict[str, object]] = {}
    if not settings.db_path.exists():
        return by_run_id, by_artifact
    with connect(settings.db_path) as conn:
        rows = conn.execute(
            """
            SELECT run_id, schedule_slot, run_time_bj, run_time_au, created_at, status,
                   data_quality_status, report_path, offline_html_path
            FROM run_log
            ORDER BY created_at, rowid
            """
        ).fetchall()
    for sqlite_row in rows:
        row = dict(sqlite_row)
        by_run_id[str(row["run_id"])] = row
        for key in ("report_path", "offline_html_path"):
            rel = _rel_from_path_value(settings, row.get(key))
            if rel:
                by_artifact[rel] = row
    return by_run_id, by_artifact


def _run_for_artifact(rel_path: str, by_run_id: dict[str, dict[str, object]], by_artifact: dict[str, dict[str, object]]) -> dict[str, object]:
    direct = by_artifact.get(rel_path)
    if direct:
        return direct
    name = Path(rel_path).name
    for run_id in sorted(by_run_id, key=len, reverse=True):
        if name.startswith(run_id) or rel_path.startswith(f"data/moomoo/{run_id}/"):
            return by_run_id[run_id]
    return {}


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _write_artifact_timeline(settings: Settings, current_manifest: dict[str, object], path: Path) -> list[dict[str, object]]:
    by_run_id, by_artifact = _run_lookup(settings)
    files = current_manifest.get("files") if isinstance(current_manifest.get("files"), dict) else {}
    rows: list[dict[str, object]] = []
    for rel_path, info in sorted(files.items()):
        if not isinstance(info, dict):
            continue
        run = _run_for_artifact(str(rel_path), by_run_id, by_artifact)
        rows.append(
            {
                "artifact_type": _artifact_type(str(rel_path)),
                "path": rel_path,
                "run_id": run.get("run_id", ""),
                "schedule_slot": run.get("schedule_slot", ""),
                "run_time_bj": run.get("run_time_bj", ""),
                "run_time_au": run.get("run_time_au", ""),
                "run_created_at": run.get("created_at", ""),
                "run_status": run.get("status", ""),
                "data_quality_status": run.get("data_quality_status", ""),
                "file_created_at": info.get("file_created_at", ""),
                "file_modified_at": info.get("file_modified_at", ""),
                "file_metadata_changed_at": info.get("file_metadata_changed_at", ""),
                "size_bytes": info.get("size_bytes", ""),
                "sha256": info.get("sha256", ""),
            }
        )
    _write_csv(
        path,
        [
            "artifact_type",
            "path",
            "run_id",
            "schedule_slot",
            "run_time_bj",
            "run_time_au",
            "run_created_at",
            "run_status",
            "data_quality_status",
            "file_created_at",
            "file_modified_at",
            "file_metadata_changed_at",
            "size_bytes",
            "sha256",
        ],
        rows,
    )
    return rows


def _snapshot_run_bounds(settings: Settings, table: str) -> dict[str, object]:
    if not settings.db_path.exists():
        return {}
    with connect(settings.db_path) as conn:
        columns = {row["name"] for row in conn.execute(f'PRAGMA table_info("{table}")')}
        if "run_id" not in columns:
            return {}
        row = conn.execute(
            f"""
            SELECT count(DISTINCT t.run_id) AS run_count,
                   min(r.run_time_bj) AS first_run_time_bj,
                   max(r.run_time_bj) AS last_run_time_bj,
                   min(r.created_at) AS first_run_created_at,
                   max(r.created_at) AS last_run_created_at
            FROM "{table}" t
            LEFT JOIN run_log r ON r.run_id=t.run_id
            """
        ).fetchone()
    return dict(row) if row else {}


def _write_snapshot_timeline(settings: Settings, current_manifest: dict[str, object], path: Path) -> list[dict[str, object]]:
    tables = ((current_manifest.get("sqlite") or {}).get("tables") or {}) if isinstance(current_manifest.get("sqlite"), dict) else {}
    rows: list[dict[str, object]] = []
    if isinstance(tables, dict):
        for table, table_info in sorted(tables.items()):
            if not isinstance(table_info, dict):
                continue
            bounds = _snapshot_run_bounds(settings, str(table))
            rows.append(
                {
                    "table": table,
                    "row_count": table_info.get("row_count", ""),
                    "table_hash": table_info.get("table_hash", ""),
                    "run_count": bounds.get("run_count", ""),
                    "first_run_time_bj": bounds.get("first_run_time_bj", ""),
                    "last_run_time_bj": bounds.get("last_run_time_bj", ""),
                    "first_run_created_at": bounds.get("first_run_created_at", ""),
                    "last_run_created_at": bounds.get("last_run_created_at", ""),
                }
            )
    _write_csv(
        path,
        [
            "table",
            "row_count",
            "table_hash",
            "run_count",
            "first_run_time_bj",
            "last_run_time_bj",
            "first_run_created_at",
            "last_run_created_at",
        ],
        rows,
    )
    return rows


def _write_timeline_markdown(path: Path, artifact_rows: list[dict[str, object]], snapshot_rows: list[dict[str, object]]) -> None:
    report_rows = [row for row in artifact_rows if str(row.get("artifact_type", "")).startswith("analysis_report")]
    moomoo_rows = [row for row in artifact_rows if str(row.get("artifact_type", "")).startswith("moomoo")]
    lines = [
        "# 历史报告与快照时间线",
        "",
        f"- 历史文件总数：{len(artifact_rows)}",
        f"- 分析报告文件：{len(report_rows)}",
        f"- MooMoo 快照/原始数据文件：{len(moomoo_rows)}",
        f"- SQLite 快照表：{len(snapshot_rows)}",
        "",
        "## 口径",
        "",
        "- `file_created_at` 来自文件系统创建时间；不支持创建时间的平台回退为 metadata change time。",
        "- `file_modified_at` 是文件最后内容修改时间，可用于识别旧报告是否被后续编辑。",
        "- `run_created_at` 和 `run_time_bj` 来自 SQLite `run_log`，用于区分“运行事实发生时间”和“文件被写入/编辑时间”。",
        "- 该时间线是审计索引；不会改写任何旧报告、旧快照或历史 SQLite 行。",
        "",
        "## 最近 20 个历史文件",
        "",
    ]
    for row in sorted(artifact_rows, key=lambda item: str(item.get("file_modified_at", "")), reverse=True)[:20]:
        lines.append(
            f"- `{row.get('path')}` | 创建 `{row.get('file_created_at')}` | 修改 `{row.get('file_modified_at')}` | run `{row.get('run_id') or '-'}`"
        )
    lines.extend(["", "## SQLite 快照表", ""])
    for row in snapshot_rows:
        lines.append(
            f"- `{row.get('table')}`：rows={row.get('row_count')}，runs={row.get('run_count') or '-'}，first_created={row.get('first_run_created_at') or '-'}，last_created={row.get('last_run_created_at') or '-'}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_markdown(path: Path, result: dict[str, object]) -> None:
    violations = result.get("violations") if isinstance(result.get("violations"), list) else []
    current = result.get("current_manifest") if isinstance(result.get("current_manifest"), dict) else {}
    sqlite_tables = ((current.get("sqlite") or {}).get("tables") or {}) if isinstance(current.get("sqlite"), dict) else {}
    file_count = len(current.get("files") or {}) if isinstance(current.get("files"), dict) else 0
    row_count = 0
    if isinstance(sqlite_tables, dict):
        row_count = sum(int(table.get("row_count") or 0) for table in sqlite_tables.values() if isinstance(table, dict))
    lines = [
        "# 历史完整性审计",
        "",
        f"- 状态：{result.get('status')}",
        f"- 生成时间：{result.get('generated_at')}",
        f"- 基线文件：`{result.get('baseline_path') or '-'}`",
        f"- 报告/文件时间线：`{result.get('artifact_timeline_csv_path') or '-'}`",
        f"- 快照表时间线：`{result.get('snapshot_timeline_csv_path') or '-'}`",
        f"- SQLite 保护表：{len(sqlite_tables)}",
        f"- SQLite 保护行：{row_count}",
        f"- 历史文件：{file_count}",
        f"- 违规数：{len(violations)}",
        "",
        "## 规则",
        "",
        "- 允许新增新的运行、新的快照、新的报告和新的通知记录。",
        "- 不允许修改、删除或覆盖已经进入基线的历史行和历史文件。",
        "- UI、报告模板、策略逻辑和功能迭代只能生成新的事实，不得重写旧事实。",
        "",
    ]
    if violations:
        lines.extend(["## 违规", ""])
        for violation in violations[:100]:
            if isinstance(violation, dict):
                lines.append(
                    f"- `{violation.get('area')}` `{violation.get('violation_type')}` `{violation.get('item')}`：{violation.get('detail')}"
                )
        if len(violations) > 100:
            lines.append(f"- ... {len(violations) - 100} more")
    else:
        lines.extend(["## 违规", "", "- None"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_history_integrity(
    settings: Settings,
    *,
    baseline_path: Path | None = None,
    write_baseline: bool = False,
    overwrite_baseline: bool = False,
) -> dict[str, object]:
    output_dir = settings.root_dir / "outputs" / "audit"
    latest_json_path = output_dir / "history_integrity_latest.json"
    latest_md_path = output_dir / "history_integrity_latest.md"
    artifact_timeline_csv_path = output_dir / "history_artifact_timeline.csv"
    snapshot_timeline_csv_path = output_dir / "history_snapshot_table_timeline.csv"
    timeline_md_path = output_dir / "history_artifact_timeline.md"
    default_baseline_path = output_dir / "history_integrity_baseline.json"
    baseline = baseline_path or default_baseline_path

    current_manifest = build_history_manifest(settings)
    artifact_rows = _write_artifact_timeline(settings, current_manifest, artifact_timeline_csv_path)
    snapshot_rows = _write_snapshot_timeline(settings, current_manifest, snapshot_timeline_csv_path)
    _write_timeline_markdown(timeline_md_path, artifact_rows, snapshot_rows)
    violations: list[IntegrityViolation] = []
    compared = False
    baseline_exists = baseline.exists()
    if baseline_exists:
        compared = True
        baseline_manifest = json.loads(baseline.read_text(encoding="utf-8"))
        violations = compare_manifests(baseline_manifest, current_manifest)
    elif baseline_path and not write_baseline:
        violations = [
            IntegrityViolation(
                "baseline",
                str(baseline),
                "baseline_missing",
                "Requested history integrity baseline does not exist.",
            )
        ]

    status = "pass" if not violations else "block"
    baseline_written = False
    if write_baseline:
        if baseline_exists and not overwrite_baseline:
            violations.append(
                IntegrityViolation(
                    "baseline",
                    str(baseline),
                    "baseline_exists",
                    "Refusing to overwrite an existing history baseline without --overwrite-baseline.",
                )
            )
            status = "block"
        elif not violations:
            _write_json(baseline, current_manifest)
            baseline_written = True

    result = {
        "generated_at": _now(settings),
        "status": status,
        "compared": compared,
        "baseline_path": str(baseline),
        "baseline_exists": baseline_exists,
        "baseline_written": baseline_written,
        "violations": [asdict(violation) for violation in violations],
        "violation_count": len(violations),
        "current_manifest": current_manifest,
        "json_path": str(latest_json_path),
        "markdown_path": str(latest_md_path),
        "artifact_timeline_csv_path": str(artifact_timeline_csv_path),
        "snapshot_timeline_csv_path": str(snapshot_timeline_csv_path),
        "artifact_timeline_markdown_path": str(timeline_md_path),
    }
    _write_json(latest_json_path, result)
    _write_markdown(latest_md_path, result)
    return result
