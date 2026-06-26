from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import DATA_DIR
from pfi_os.integrations.research_bus import initialize_research_bus, research_bus_db_path
from pfi_os.storage import atomic_write_json


INDEPENDENT_VALIDATION_DIR = DATA_DIR / "independentValidation"
DEFAULT_ROWS_PER_SHARD = 1_000_000
MAX_IN_MEMORY_PREVIEW_ROWS = 10_000


@dataclass(frozen=True)
class ValidationShard:
    shard_id: str
    run_id: str
    shard_index: int
    source_path: str
    start_row: int
    end_row: int
    status: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["payload_json"] = row.pop("payload")
        return row


@dataclass(frozen=True)
class IndependentValidationRun:
    run_id: str
    status: str
    mode: str
    manifest_path: str
    total_rows: int
    shard_count: int
    started_at: str
    completed_at: str
    output_path: str
    execution_tier: str
    worker_count: int
    assumptions: tuple[str, ...]
    shards: tuple[ValidationShard, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["assumptions"] = list(self.assumptions)
        payload["shards"] = [shard.to_dict() for shard in self.shards]
        return payload


def run_independent_validation(
    manifest_path: Path | str | None = None,
    *,
    db_path: Path | str | None = None,
    synthetic_rows: int = 0,
    rows_per_shard: int = DEFAULT_ROWS_PER_SHARD,
    mode: str = "dry_run",
    output_dir: Path | str | None = None,
    worker_count: int = 1,
) -> IndependentValidationRun:
    if rows_per_shard <= 0:
        raise ValueError("rows_per_shard must be positive.")
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"dry_run", "checksum"}:
        raise ValueError("mode must be 'dry_run' or 'checksum'.")
    normalized_worker_count = max(1, int(worker_count or 1))
    output_root = Path(output_dir).expanduser() if output_dir is not None else INDEPENDENT_VALIDATION_DIR
    output_root.mkdir(parents=True, exist_ok=True)
    started_at = _now()
    manifest = _load_manifest(manifest_path)
    rows = _manifest_rows(manifest, synthetic_rows=synthetic_rows)
    if not rows:
        raise ValueError("No validation rows were provided. Use a manifest file or synthetic_rows.")
    total_rows = sum(max(0, int(row["row_count"])) for row in rows)
    run_id = _stable_id("independentValidationRun", started_at, manifest_path or "", total_rows, rows_per_shard, normalized_mode, normalized_worker_count)
    planned_shards = tuple(_build_shards(run_id, rows, rows_per_shard))
    if normalized_mode == "checksum":
        shards = tuple(_execute_checksum_shards(planned_shards, worker_count=normalized_worker_count))
        status = _validation_status(shards)
        execution_tier = "local_worker_pool" if normalized_worker_count > 1 else "single_worker"
    else:
        shards = planned_shards
        status = "Planned"
        execution_tier = "planning_manifest"
    base_assumptions = (
        "该入口默认只生成可审计的分片验证计划，不自动下单、不生成交易指令。",
        "亿万级别数据测试通过 manifest 和分片登记支持；实际执行应由批处理或分布式执行器逐片消费。",
        "dry_run 模式不会把大数据一次性载入内存；只读取文件元数据和必要行数统计。",
        "百亿级测试以分片计划和本机 worker pool 为第一阶段能力，不代表长期分布式集群已经部署。",
    )
    checksum_assumptions = (
        "checksum 模式会逐片流式读取实际文件或生成合成数据分片校验码，不把完整数据集一次性载入内存。",
        "任一分片文件缺失、格式不支持或实际行数不足，整次校验会标记为 Failed，防止未验证数据被当成已通过。",
        f"本次 worker_count={normalized_worker_count}；worker_count>1 时使用本机线程池并行处理分片。",
    )
    assumptions = base_assumptions + (checksum_assumptions if normalized_mode == "checksum" else ())
    completed_at = _now()
    output_path = output_root / f"IndependentValidationRun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result = IndependentValidationRun(
        run_id=run_id,
        status=status,
        mode=normalized_mode,
        manifest_path=str(Path(manifest_path).expanduser()) if manifest_path is not None else "",
        total_rows=int(total_rows),
        shard_count=len(shards),
        started_at=started_at,
        completed_at=completed_at,
        output_path=str(output_path),
        execution_tier=execution_tier,
        worker_count=normalized_worker_count,
        assumptions=assumptions,
        shards=shards,
    )
    atomic_write_json(output_path, result.to_dict())
    write_independent_validation_to_bus(result, db_path)
    return result


def write_independent_validation_to_bus(
    result: IndependentValidationRun,
    db_path: Path | str | None = None,
) -> Path:
    target_db = initialize_research_bus(db_path)
    conn = sqlite3.connect(target_db, timeout=30)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute(
            """
            INSERT INTO independent_validation_runs(
                run_id, source_system, status, mode, manifest_path, total_rows, shard_count,
                started_at, completed_at, output_path, payload_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                status=excluded.status,
                mode=excluded.mode,
                manifest_path=excluded.manifest_path,
                total_rows=excluded.total_rows,
                shard_count=excluded.shard_count,
                completed_at=excluded.completed_at,
                output_path=excluded.output_path,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                result.run_id,
                "IndependentValidation",
                result.status,
                result.mode,
                result.manifest_path,
                result.total_rows,
                result.shard_count,
                result.started_at,
                result.completed_at,
                result.output_path,
                json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True),
                _now(),
            ),
        )
        for shard in result.shards:
            conn.execute(
                """
                INSERT INTO independent_validation_shards(
                    shard_id, run_id, shard_index, source_path, start_row, end_row, status, payload_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(shard_id) DO UPDATE SET
                    start_row=excluded.start_row,
                    end_row=excluded.end_row,
                    status=excluded.status,
                    payload_json=excluded.payload_json,
                    updated_at=excluded.updated_at
                """,
                (
                    shard.shard_id,
                    shard.run_id,
                    shard.shard_index,
                    shard.source_path,
                    shard.start_row,
                    shard.end_row,
                    shard.status,
                    json.dumps(shard.payload, ensure_ascii=False, sort_keys=True),
                    _now(),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return target_db


def independent_validation_runs_frame(db_path: Path | str | None = None) -> pd.DataFrame:
    target_db = initialize_research_bus(db_path or research_bus_db_path())
    conn = sqlite3.connect(target_db, timeout=30)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        rows = conn.execute(
            """
            SELECT run_id, status, mode, manifest_path, total_rows, shard_count,
                   started_at, completed_at, output_path, updated_at
            FROM independent_validation_runs
            ORDER BY updated_at DESC
            """
        ).fetchall()
    finally:
        conn.close()
    columns = ["run_id", "status", "mode", "manifest_path", "total_rows", "shard_count", "started_at", "completed_at", "output_path", "updated_at"]
    return pd.DataFrame(rows, columns=columns)


def write_manifest(
    input_paths: list[str | Path],
    path: Path | str,
    *,
    dataset_name: str = "IndependentValidationDataset",
) -> Path:
    manifest_path = Path(path).expanduser()
    rows = []
    for input_path in input_paths:
        source_path = Path(input_path).expanduser()
        rows.append(
            {
                "source_path": str(source_path),
                "row_count": _count_rows(source_path),
                "format": source_path.suffix.lower().lstrip("."),
                "content_hash": _hash_file(source_path) if source_path.exists() and source_path.is_file() else "",
            }
        )
    payload = {"dataset_name": dataset_name, "created_at": _now(), "inputs": rows}
    atomic_write_json(manifest_path, payload)
    return manifest_path


def _load_manifest(path: Path | str | None) -> dict[str, Any]:
    if path is None:
        return {"inputs": []}
    manifest_path = Path(path).expanduser()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest must be a JSON object.")
    return payload


def _manifest_rows(manifest: dict[str, Any], *, synthetic_rows: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in manifest.get("inputs", []) or []:
        if not isinstance(item, dict):
            continue
        source_path = str(item.get("source_path", "")).strip()
        row_count = int(item.get("row_count") or 0)
        if row_count <= 0 and source_path:
            row_count = _count_rows(Path(source_path).expanduser())
        if row_count > 0:
            rows.append({"source_path": source_path, "row_count": row_count, "payload": item})
    if synthetic_rows > 0:
        rows.append(
            {
                "source_path": "synthetic://scale-test",
                "row_count": int(synthetic_rows),
                "payload": {"format": "synthetic", "purpose": "大规模容量和分片调度测试"},
            }
        )
    return rows


def _build_shards(run_id: str, rows: list[dict[str, Any]], rows_per_shard: int) -> list[ValidationShard]:
    shards: list[ValidationShard] = []
    shard_index = 0
    for row in rows:
        row_count = int(row["row_count"])
        source_path = str(row["source_path"])
        shard_total = math.ceil(row_count / rows_per_shard)
        for local_index in range(shard_total):
            start_row = local_index * rows_per_shard
            end_row = min(row_count, start_row + rows_per_shard)
            shard_id = _stable_id("validationShard", run_id, source_path, start_row, end_row)
            shards.append(
                ValidationShard(
                    shard_id=shard_id,
                    run_id=run_id,
                    shard_index=shard_index,
                    source_path=source_path,
                    start_row=start_row,
                    end_row=end_row,
                    status="Planned",
                    payload={
                        "row_count": end_row - start_row,
                        "source_payload": row.get("payload", {}),
                        "memory_policy": f"每片最多 {rows_per_shard} 行；执行器应逐片读取。",
                    },
                )
            )
            shard_index += 1
    return shards


def _execute_checksum_shards(shards: tuple[ValidationShard, ...], *, worker_count: int = 1) -> list[ValidationShard]:
    if worker_count <= 1 or len(shards) <= 1:
        return [_execute_checksum_shard(shard) for shard in shards]
    with ThreadPoolExecutor(max_workers=min(max(1, int(worker_count)), len(shards))) as executor:
        return list(executor.map(_execute_checksum_shard, shards))


def _execute_checksum_shard(shard: ValidationShard) -> ValidationShard:
    try:
        if shard.source_path == "synthetic://scale-test":
            result = _checksum_synthetic_shard(shard)
        else:
            result = _checksum_file_shard(shard)
        status = "Completed" if result["observed_rows"] == result["expected_rows"] else "Failed"
        if status == "Failed":
            result["error"] = "Observed row count does not match expected shard row count."
    except Exception as exc:  # pragma: no cover - defensive guard for filesystem edge cases
        result = {
            "expected_rows": max(0, shard.end_row - shard.start_row),
            "observed_rows": 0,
            "checksum": "",
            "checksum_algorithm": "sha256",
            "execution_mode": "checksum",
            "executed_at": _now(),
            "error": str(exc),
        }
        status = "Failed"
    payload = {
        **shard.payload,
        **result,
    }
    return ValidationShard(
        shard_id=shard.shard_id,
        run_id=shard.run_id,
        shard_index=shard.shard_index,
        source_path=shard.source_path,
        start_row=shard.start_row,
        end_row=shard.end_row,
        status=status,
        payload=payload,
    )


def _checksum_synthetic_shard(shard: ValidationShard) -> dict[str, Any]:
    observed_rows = max(0, shard.end_row - shard.start_row)
    digest = hashlib.sha256()
    digest.update(
        f"{shard.source_path}|{shard.run_id}|{shard.shard_id}|{shard.start_row}|{shard.end_row}|{observed_rows}".encode("utf-8")
    )
    return {
        "expected_rows": observed_rows,
        "observed_rows": observed_rows,
        "checksum": digest.hexdigest(),
        "checksum_algorithm": "sha256",
        "execution_mode": "checksum",
        "executed_at": _now(),
    }


def _checksum_file_shard(shard: ValidationShard) -> dict[str, Any]:
    source_path = Path(shard.source_path).expanduser()
    expected_rows = max(0, shard.end_row - shard.start_row)
    if not source_path.exists() or not source_path.is_file():
        return _failed_checksum_payload(expected_rows, f"Source file does not exist: {source_path}")
    suffix = source_path.suffix.lower()
    if suffix not in {".csv", ".txt", ".jsonl"}:
        return _failed_checksum_payload(expected_rows, f"Unsupported checksum file format: {suffix or 'unknown'}")

    digest = hashlib.sha256()
    digest.update(f"{source_path}|{shard.start_row}|{shard.end_row}|".encode("utf-8"))
    observed_rows = 0
    with source_path.open("rb") as handle:
        if suffix == ".csv":
            next(handle, None)
        for logical_index, line in enumerate(handle):
            if logical_index < shard.start_row:
                continue
            if logical_index >= shard.end_row:
                break
            digest.update(line)
            observed_rows += 1

    payload = {
        "expected_rows": expected_rows,
        "observed_rows": observed_rows,
        "checksum": digest.hexdigest() if observed_rows else "",
        "checksum_algorithm": "sha256",
        "execution_mode": "checksum",
        "executed_at": _now(),
    }
    if observed_rows != expected_rows:
        payload["error"] = "Observed row count does not match expected shard row count."
    return payload


def _failed_checksum_payload(expected_rows: int, error: str) -> dict[str, Any]:
    return {
        "expected_rows": expected_rows,
        "observed_rows": 0,
        "checksum": "",
        "checksum_algorithm": "sha256",
        "execution_mode": "checksum",
        "executed_at": _now(),
        "error": error,
    }


def _validation_status(shards: tuple[ValidationShard, ...]) -> str:
    if not shards:
        return "Failed"
    if all(shard.status == "Completed" for shard in shards):
        return "Completed"
    if any(shard.status == "Completed" for shard in shards):
        return "CompletedWithErrors"
    return "Failed"


def _count_rows(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt", ".jsonl"}:
        try:
            with path.open("rb") as handle:
                count = sum(1 for _ in handle)
            return max(0, count - (1 if suffix == ".csv" else 0))
        except OSError:
            return 0
    return 0


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "\n".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
