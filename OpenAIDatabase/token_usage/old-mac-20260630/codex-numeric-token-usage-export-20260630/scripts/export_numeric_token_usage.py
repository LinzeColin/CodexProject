#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/linzezhang")
OUT = Path("/Users/linzezhang/Documents/Codex/2026-06-29/wo/work/codex-numeric-token-usage-export-20260630/data")

DATABASES = [
    ("codex_root_logs_2", ROOT / ".codex/logs_2.sqlite"),
    ("codex_sqlite_logs_2", ROOT / ".codex/sqlite/logs_2.sqlite"),
]

NUMERIC_FIELDS = [
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cached_input_tokens",
    "reasoning_output_tokens",
]


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


def usage_objects(body: str) -> list[dict]:
    results: list[dict] = []
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


def int_value(value) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def normalize_usage(usage: dict) -> dict[str, int]:
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


def usage_signature(row: dict) -> str:
    # Deliberately excludes log id and process uuid so mirrored log targets do not double-count.
    bucket = row["ts_utc"][:19]
    parts = [
        row["thread_id"],
        bucket,
        *(str(row[field]) for field in NUMERIC_FIELDS),
    ]
    return hashlib.sha256("\t".join(parts).encode()).hexdigest()


def export() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_rows: list[dict] = []
    db_inventory: list[dict] = []

    for source_name, db_path in DATABASES:
        if not db_path.exists():
            continue
        con = sqlite3.connect(str(db_path))
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
            objects = usage_objects(body)
            if not objects:
                continue
            # The last usage object is the final response-level usage in the observed Codex log format.
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
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cached_input_tokens",
        "reasoning_output_tokens",
        "usage_signature",
    ]
    with (OUT / "raw_extracted_usage_rows.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=raw_fields)
        writer.writeheader()
        writer.writerows(raw_rows)

    seen: set[str] = set()
    deduped: list[dict] = []
    for row in sorted(raw_rows, key=lambda r: (r["ts"], r["source_name"], r["source_log_id"])):
        sig = row["usage_signature"]
        if sig in seen:
            continue
        seen.add(sig)
        deduped.append(row)
    with (OUT / "deduped_usage_rows.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=raw_fields)
        writer.writeheader()
        writer.writerows(deduped)

    daily = defaultdict(Counter)
    monthly = defaultdict(Counter)
    by_source = defaultdict(Counter)
    for row in deduped:
        day = row["ts_utc"][:10] or "unknown"
        month = row["ts_utc"][:7] or "unknown"
        for field in NUMERIC_FIELDS:
            daily[day][field] += int(row[field])
            monthly[month][field] += int(row[field])
            by_source[row["source_name"]][field] += int(row[field])
        daily[day]["records"] += 1
        monthly[month]["records"] += 1
        by_source[row["source_name"]]["records"] += 1

    with (OUT / "daily_usage_summary.csv").open("w", newline="") as f:
        fields = ["date", "records", *NUMERIC_FIELDS]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for day in sorted(daily):
            writer.writerow({"date": day, **daily[day]})

    with (OUT / "monthly_usage_summary.csv").open("w", newline="") as f:
        fields = ["month", "records", *NUMERIC_FIELDS]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for month in sorted(monthly):
            writer.writerow({"month": month, **monthly[month]})

    with (OUT / "summary.json").open("w") as f:
        json.dump(
            {
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
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    export()
