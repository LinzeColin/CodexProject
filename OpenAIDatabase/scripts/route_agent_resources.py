#!/usr/bin/env python3
"""Return route-specific OpenAIDatabase resources for future agents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROUTE_CONFIG = Path("config/context_sources/resource_routes.json")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def route_resources(database_dir: Path, intent: str | None) -> dict[str, Any]:
    config = read_json(database_dir / ROUTE_CONFIG)
    selected_intent = intent or str(config.get("default_intent") or "startup")
    routes = config.get("routes", [])
    if not isinstance(routes, list):
        routes = []
    route = next((row for row in routes if isinstance(row, dict) and row.get("intent") == selected_intent), None)
    if route is None:
        valid = [str(row.get("intent")) for row in routes if isinstance(row, dict)]
        return {
            "status": "FAIL",
            "reason": "unknown_intent",
            "intent": selected_intent,
            "valid_intents": valid,
        }
    return {
        "status": "PASS",
        "schema_version": config.get("schema_version", ""),
        "intent": selected_intent,
        "description": route.get("description", ""),
        "read_order": route.get("read_order", []),
        "update_targets": route.get("update_targets", []),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route OpenAIDatabase resources by agent intent.")
    parser.add_argument("--database-dir", type=Path, default=Path("."), help="OpenAIDatabase repository root.")
    parser.add_argument("--intent", default=None, help="Route intent, for example startup or taste_profile.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = route_resources(args.database_dir.resolve(), args.intent)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
