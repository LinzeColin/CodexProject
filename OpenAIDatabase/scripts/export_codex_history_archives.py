#!/usr/bin/env python3
"""Export numeric Codex token telemetry without session or bundle payloads."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NUMERIC_FIELDS = [
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cached_input_tokens",
    "reasoning_output_tokens",
]
def remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def iso_from_ts(ts: int | float | None) -> str:
    if ts is None:
        return ""
    try:
        value = float(ts)
    except Exception:
        return ""
    if value > 10_000_000_000:
        value = value / 1000.0
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def extract_balanced_object(text: str, start: int) -> str | None:
    if start < 0 or start >= len(text) or text[start] != "{":
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def usage_objects(body: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for match in re.finditer(r'"usage"\s*:\s*{', body):
        obj_start = body.find("{", match.start())
        raw = extract_balanced_object(body, obj_start)
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue
        if isinstance(parsed, dict):
            results.append(parsed)
    return results


def int_value(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def normalize_usage(usage: dict[str, Any]) -> dict[str, int]:
    input_tokens = int_value(usage.get("input_tokens") or usage.get("prompt_tokens"))
    output_tokens = int_value(usage.get("output_tokens") or usage.get("completion_tokens"))
    total_tokens = int_value(usage.get("total_tokens"))
    input_details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or usage.get("completion_tokens_details") or {}
    if not isinstance(input_details, dict):
        input_details = {}
    if not isinstance(output_details, dict):
        output_details = {}
    cached_input_tokens = int_value(input_details.get("cached_tokens")) or int_value(usage.get("cached_input_tokens"))
    reasoning_output_tokens = int_value(output_details.get("reasoning_tokens")) or int_value(
        usage.get("reasoning_output_tokens")
    )
    if not total_tokens and (input_tokens or output_tokens):
        total_tokens = input_tokens + output_tokens
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached_input_tokens,
        "reasoning_output_tokens": reasoning_output_tokens,
    }


def usage_signature(row: dict[str, Any]) -> str:
    bucket = str(row["ts_utc"])[:19]
    parts = [str(row["thread_id"]), bucket, *(str(row[field]) for field in NUMERIC_FIELDS)]
    return hashlib.sha256("\t".join(parts).encode()).hexdigest()


def sqlite_connection(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA busy_timeout=5000")
    return con


def export_token_usage(codex_home: Path, output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    data_dir = output_dir / "data"
    remove_tree(output_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_rows: list[dict[str, Any]] = []
    db_inventory: list[dict[str, Any]] = []
    databases = [
        ("codex_root_logs_2", codex_home / "logs_2.sqlite"),
        ("codex_sqlite_logs_2", codex_home / "sqlite/logs_2.sqlite"),
    ]

    for source_name, db_path in databases:
        if not db_path.exists():
            continue
        try:
            con = sqlite_connection(db_path)
        except sqlite3.Error as exc:
            db_inventory.append({"source_name": source_name, "path": str(db_path), "quick_check": f"open_failed: {exc}"})
            continue
        try:
            ok = con.execute("PRAGMA quick_check").fetchone()[0]
            total_rows = con.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
            db_inventory.append(
                {
                    "source_name": source_name,
                    "path": str(db_path),
                    "bytes": db_path.stat().st_size,
                    "quick_check": ok,
                    "log_rows": total_rows,
                }
            )
            query = """
                SELECT id, ts, ts_nanos, level, target, thread_id, process_uuid, estimated_bytes, feedback_log_body
                FROM logs
                WHERE feedback_log_body IS NOT NULL
                  AND feedback_log_body LIKE '%"usage"%'
                  AND feedback_log_body LIKE '%tokens%'
            """
            for log_id, ts, ts_nanos, level, target, thread_id, process_uuid, estimated_bytes, body in con.execute(query):
                objects = usage_objects(body or "")
                if not objects:
                    continue
                usage = normalize_usage(objects[-1])
                if not any(usage.values()):
                    continue
                row = {
                    "source_name": source_name,
                    "source_log_id": log_id,
                    "ts": ts,
                    "ts_nanos": ts_nanos,
                    "ts_utc": iso_from_ts(ts),
                    "level": level,
                    "target": target,
                    "thread_id": thread_id or "",
                    "process_uuid": process_uuid or "",
                    "estimated_bytes": estimated_bytes,
                    "usage_object_count_in_log": len(objects),
                    **usage,
                }
                row["usage_signature"] = usage_signature(row)
                raw_rows.append(row)
        finally:
            con.close()

    raw_fields = [
        "source_name",
        "source_log_id",
        "ts",
        "ts_nanos",
        "ts_utc",
        "level",
        "target",
        "thread_id",
        "process_uuid",
        "estimated_bytes",
        "usage_object_count_in_log",
        *NUMERIC_FIELDS,
        "usage_signature",
    ]
    with (data_dir / "raw_extracted_usage_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=raw_fields)
        writer.writeheader()
        writer.writerows(raw_rows)

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in sorted(raw_rows, key=lambda r: (r["ts"] or 0, r["source_name"], r["source_log_id"])):
        sig = row["usage_signature"]
        if sig in seen:
            continue
        seen.add(sig)
        deduped.append(row)
    with (data_dir / "deduped_usage_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=raw_fields)
        writer.writeheader()
        writer.writerows(deduped)

    daily: defaultdict[str, Counter[str]] = defaultdict(Counter)
    monthly: defaultdict[str, Counter[str]] = defaultdict(Counter)
    by_source: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in deduped:
        day = str(row["ts_utc"])[:10] or "unknown"
        month = str(row["ts_utc"])[:7] or "unknown"
        for field in NUMERIC_FIELDS:
            value = int(row[field])
            daily[day][field] += value
            monthly[month][field] += value
            by_source[str(row["source_name"])][field] += value
        daily[day]["records"] += 1
        monthly[month]["records"] += 1
        by_source[str(row["source_name"])]["records"] += 1

    with (data_dir / "daily_usage_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["date", "records", *NUMERIC_FIELDS]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for day in sorted(daily):
            writer.writerow({"date": day, **daily[day]})
    with (data_dir / "monthly_usage_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["month", "records", *NUMERIC_FIELDS]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for month in sorted(monthly):
            writer.writerow({"month": month, **monthly[month]})

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "numeric token usage only; no prompt/response/session body exported",
        "databases": db_inventory,
        "raw_record_count": len(raw_rows),
        "deduped_record_count": len(deduped),
        "raw_duplicate_count": len(raw_rows) - len(deduped),
        "dedupe_rule": "sha256(thread_id + second-level timestamp + numeric usage fields)",
        "deduped_totals": {field: sum(int(row[field]) for row in deduped) for field in NUMERIC_FIELDS},
        "raw_totals": {field: sum(int(row[field]) for row in raw_rows) for field in NUMERIC_FIELDS},
        "by_source_deduped": {source: dict(counter) for source, counter in by_source.items()},
        "notes": [
            "This is a local log-derived export, not an official billing statement.",
            "Raw rows may contain mirrored log events; use deduped rows for rough local history totals.",
            "No feedback_log_body, prompt text, response text, or session JSONL is exported.",
        ],
    }
    write_text(data_dir / "summary.json", json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    write_text(
        output_dir / "README.md",
        "# Current Mac Numeric Token Usage\n\n"
        "This directory is regenerated by the scheduled Memory Atlas Codex auto-update.\n"
        "It contains numeric token usage only and does not include prompt, response, or session bodies.\n",
    )
    write_checksums(output_dir)
    return {"status": "PASS", "output_dir": str(output_dir), **summary}


def write_checksums(root: Path) -> None:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        rows.append(f"{sha256_file(path)}  {path.relative_to(root)}")
    write_text(root / "SHA256SUMS", "\n".join(rows) + ("\n" if rows else ""))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export numeric Codex token telemetry; raw sessions are never bundled."
    )
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--token-usage", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    codex_home = args.codex_home.expanduser().resolve()
    result: dict[str, Any] = {"status": "PASS", "exports": {}}
    if args.token_usage:
        result["exports"]["token_usage"] = export_token_usage(
            codex_home,
            database_dir / "data/run_logs/token_usage",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
