#!/usr/bin/env python3
"""Statically validate a KMFA PostgreSQL load plan against the repo schema."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.lower())


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def split_top_level_csv(text: str) -> list[str]:
    values: list[str] = []
    start = 0
    depth = 0
    in_single_quote = False
    for idx, char in enumerate(text):
        if char == "'" and (idx == 0 or text[idx - 1] != "\\"):
            in_single_quote = not in_single_quote
        elif not in_single_quote:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                values.append(text[start:idx].strip())
                start = idx + 1
    tail = text[start:].strip()
    if tail:
        values.append(tail)
    return values


def extract_table_blocks(sql: str) -> dict[str, str]:
    pattern = re.compile(r"create\s+table\s+if\s+not\s+exists\s+([a-zA-Z_][\w]*)\s*\(", re.I)
    blocks: dict[str, str] = {}
    for match in pattern.finditer(sql):
        name = match.group(1).lower()
        open_paren = match.end() - 1
        depth = 0
        end = None
        for idx in range(open_paren, len(sql)):
            char = sql[idx]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = idx
                    break
        if end is not None:
            blocks[name] = sql[open_paren + 1 : end]
    return blocks


def table_columns(table_block: str) -> set[str]:
    columns: set[str] = set()
    for item in split_top_level_csv(table_block):
        item = item.strip()
        if not item or item.lower().startswith(("unique ", "check ", "primary key", "constraint ")):
            continue
        match = re.match(r"([a-zA-Z_][\w]*)\s+", item)
        if match:
            columns.add(match.group(1).lower())
    return columns


def unique_targets(table_block: str) -> set[tuple[str, ...]]:
    targets: set[tuple[str, ...]] = set()
    for item in split_top_level_csv(table_block):
        item_norm = normalize_sql(item)
        unique_match = re.search(r"\bunique\s*\(([^)]*)\)", item_norm)
        if unique_match:
            targets.add(tuple(col.strip() for col in unique_match.group(1).split(",") if col.strip()))
        primary_inline = re.match(r"\s*([a-zA-Z_][\w]*)\s+[^,]*\bprimary\s+key\b", item_norm)
        if primary_inline:
            targets.add((primary_inline.group(1),))
        primary_table = re.search(r"\bprimary\s+key\s*\(([^)]*)\)", item_norm)
        if primary_table:
            targets.add(tuple(col.strip() for col in primary_table.group(1).split(",") if col.strip()))
    return targets


def parse_insert_blocks(sql: str) -> dict[str, dict[str, Any]]:
    pattern = re.compile(
        r"insert\s+into\s+([a-zA-Z_][\w]*)\s*\((.*?)\)\s*select\b.*?on\s+conflict\s*\((.*?)\)\s+do\s+nothing",
        re.I | re.S,
    )
    inserts: dict[str, dict[str, Any]] = {}
    for match in pattern.finditer(sql):
        table = match.group(1).lower()
        columns = tuple(col.strip().lower() for col in split_top_level_csv(match.group(2)))
        conflict = tuple(col.strip().lower() for col in match.group(3).split(",") if col.strip())
        inserts[table] = {"columns": columns, "conflict": conflict}
    return inserts


def validate(schema_path: Path, bundle_dir: Path, sql_path: Path) -> dict[str, Any]:
    schema_sql = schema_path.read_text(encoding="utf-8")
    load_sql = sql_path.read_text(encoding="utf-8")
    table_blocks = extract_table_blocks(schema_sql)
    schema_columns = {table: table_columns(block) for table, block in table_blocks.items()}
    schema_uniques = {table: unique_targets(block) for table, block in table_blocks.items()}
    inserts = parse_insert_blocks(load_sql)
    load_order = load_json(bundle_dir / "load_order.json").get("tables", [])
    plan_manifest = load_json(bundle_dir / "postgres_load_plan_manifest.json")
    manifest_tables = plan_manifest.get("tables", [])
    failures: list[str] = []

    if load_order != manifest_tables:
        failures.append("load_order_manifest_mismatch")
    if load_order != list(inserts):
        failures.append("load_order_sql_insert_mismatch")
    if plan_manifest.get("postgres_connection_used") is not False:
        failures.append("postgres_connection_used_not_false")
    if plan_manifest.get("database_mutation_performed") is not False:
        failures.append("database_mutation_performed_not_false")
    if plan_manifest.get("live_dws_performed") is not False:
        failures.append("live_dws_performed_not_false")

    payloads = plan_manifest.get("payloads", {}) if isinstance(plan_manifest.get("payloads"), dict) else {}
    for table in load_order:
        if table not in table_blocks:
            failures.append(f"table_missing_in_schema:{table}")
            continue
        if table not in inserts:
            failures.append(f"table_missing_in_load_sql:{table}")
            continue
        if table not in payloads:
            failures.append(f"payload_missing:{table}")
        else:
            payload_path = Path(str(payloads[table].get("path", "")))
            if not payload_path.is_file():
                failures.append(f"payload_file_missing:{table}")
            if int(payloads[table].get("rows") or 0) <= 0:
                failures.append(f"payload_empty:{table}")
        missing_columns = sorted(set(inserts[table]["columns"]) - schema_columns[table])
        if missing_columns:
            failures.append(f"insert_columns_not_in_schema:{table}:{','.join(missing_columns)}")
        conflict = tuple(inserts[table]["conflict"])
        if conflict not in schema_uniques[table]:
            failures.append(f"conflict_target_not_backed_by_schema:{table}:{','.join(conflict)}")

    checks = {
        "load_order_matches_manifest": load_order == manifest_tables,
        "load_order_matches_sql": load_order == list(inserts),
        "insert_columns_in_schema": not any(f.startswith("insert_columns_not_in_schema:") for f in failures),
        "conflict_targets_backed_by_schema": not any(f.startswith("conflict_target_not_backed_by_schema:") for f in failures),
        "payload_files_present": not any(f.startswith("payload_") for f in failures),
    }
    return {
        "status": "fail" if failures else "pass",
        "mode": "offline_postgres_load_plan_static_validation",
        "schema": str(schema_path),
        "bundle_dir": str(bundle_dir),
        "sql": str(sql_path),
        "tables_checked": load_order,
        "checks": checks,
        "failures": failures,
        "postgres_connection_used": False,
        "database_mutation_performed": False,
        "live_dws_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a generated KMFA PostgreSQL load plan without connecting to PostgreSQL.")
    parser.add_argument("--schema", required=True)
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--sql", default="")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    bundle_dir = Path(args.bundle_dir)
    sql_path = Path(args.sql) if args.sql else bundle_dir / "postgres_load_plan.sql"
    result = validate(Path(args.schema), bundle_dir, sql_path)
    if args.print_json or result["status"] == "fail":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
