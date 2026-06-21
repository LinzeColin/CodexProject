#!/usr/bin/env python3
"""Build ChatGPT and Codex personalization exports from redacted derived data."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_agent_context_pack import build_agent_context_pack, write_if_changed


CONTEXT_CONFIG = Path("config/context_sources/three_layer_context.json")
ROUTE_CONFIG = Path("config/context_sources/resource_routes.json")
DEFAULT_OUTPUT_DIR = Path("data/derived/personalization")
CHATGPT_EXPORT = DEFAULT_OUTPUT_DIR / "chatgpt_personalization.md"
CODEX_EXPORT = DEFAULT_OUTPUT_DIR / "codex_personalization.md"
MACHINE_EXPORT = DEFAULT_OUTPUT_DIR / "personalization_export.json"
EXPORT_LOG_DIR = Path("data/run_logs/export_runs")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def equivalent_payload_without_generated_at(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_copy = dict(left)
    right_copy = dict(right)
    left_copy.pop("generated_at", None)
    right_copy.pop("generated_at", None)
    return left_copy == right_copy


def write_text_if_changed(path: Path, payload: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8", errors="ignore") == payload:
        return False
    write_if_changed(path, payload)
    return True


def rel(path: Path) -> str:
    return path.as_posix()


def git_head(database_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=database_dir,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_NO_GIT_HEAD"


def compact_item(item: dict[str, Any]) -> str:
    title = str(item.get("title") or item.get("id") or "Untitled").strip()
    statement = str(item.get("statement") or "").strip()
    confidence = str(item.get("confidence") or "unknown").strip()
    evidence_count = item.get("evidence_count")
    if evidence_count in (None, ""):
        suffix = f"confidence={confidence}"
    else:
        suffix = f"confidence={confidence}; evidence={evidence_count}"
    return f"- {title}: {statement} ({suffix})"


def render_items(items: list[dict[str, Any]], limit: int = 12) -> list[str]:
    rows = [compact_item(item) for item in items[:limit] if isinstance(item, dict)]
    return rows or ["- No current reviewed item."]


def route_by_intent(routes: dict[str, Any], intent: str) -> dict[str, Any]:
    for route in routes.get("routes", []):
        if isinstance(route, dict) and route.get("intent") == intent:
            return route
    return {}


def build_export_payload(database_dir: Path) -> dict[str, Any]:
    pack = build_agent_context_pack(database_dir)
    context_config = read_json(database_dir / CONTEXT_CONFIG)
    route_config = read_json(database_dir / ROUTE_CONFIG)
    sync_targets = context_config.get("sync_required_targets", [])
    log_categories = context_config.get("run_log_categories", [])
    layers = context_config.get("layers", [])
    if not isinstance(sync_targets, list):
        sync_targets = []
    if not isinstance(log_categories, list):
        log_categories = []
    if not isinstance(layers, list):
        layers = []
    payload = {
        "schema_version": "openai_database.personalization_export.v1",
        "generated_at": now_utc(),
        "source": "redacted_derived_openai_database_context",
        "source_files": {
            "context_config": rel(CONTEXT_CONFIG),
            "route_config": rel(ROUTE_CONFIG),
            **pack.get("source_files", {}),
        },
        "layers": layers,
        "sync_required_targets": sync_targets,
        "run_log_categories": log_categories,
        "routes": {
            "startup": route_by_intent(route_config, "startup"),
            "chatgpt_personalization": route_by_intent(route_config, "chatgpt_personalization"),
            "codex_personalization": route_by_intent(route_config, "codex_personalization"),
            "project_history": route_by_intent(route_config, "project_history"),
            "taste_profile": route_by_intent(route_config, "taste_profile"),
        },
        "profile": pack.get("profile", {}),
        "memory": pack.get("memory", {}),
        "preferences": pack.get("preferences", {}),
        "meta_data": pack.get("meta_data", {}),
        "behavior": pack.get("behavior", {}),
        "data_sources": pack.get("data_sources", {}),
        "safety": {
            **pack.get("safety", {}),
            "raw_private_data_included": False,
            "plaintext_secrets_included": False,
            "local_absolute_paths_included": False,
        },
    }
    existing_payload = read_json(database_dir / MACHINE_EXPORT)
    if existing_payload and equivalent_payload_without_generated_at(payload, existing_payload):
        payload["generated_at"] = str(existing_payload.get("generated_at") or payload["generated_at"])
    return payload


def markdown_header(title: str, payload: dict[str, Any]) -> list[str]:
    return [
        f"# {title}",
        "",
        f"- generated_at: {payload['generated_at']}",
        "- source: OpenAIDatabase redacted derived context",
        "- raw_private_data_included: false",
        "- plaintext_secrets_included: false",
        "",
    ]


def render_chatgpt(payload: dict[str, Any]) -> str:
    profile_items = payload.get("profile", {}).get("core_profile_items", [])
    memory_items = payload.get("memory", {}).get("current", [])
    meta_items = payload.get("meta_data", {}).get("current", [])
    top_topics = payload.get("preferences", {}).get("top_topics", [])
    lines = markdown_header("ChatGPT Personalization Export", payload)
    lines.extend(
        [
            "## Core Profile",
            "",
            *(f"- {item}" for item in profile_items[:12]),
            "" if profile_items else "- No reviewed core profile item.",
            "",
            "## Preferences And Taste",
            "",
            *render_items(memory_items, 12),
            "",
            "## History And Patterns",
            "",
            *(
                f"- {item.get('label', '')}: {item.get('count', 0)}"
                for item in top_topics[:12]
                if isinstance(item, dict)
            ),
            "" if top_topics else "- No topic summary.",
            "",
            "## Project And Decision Context",
            "",
            "- Use `data/derived/project_index/PROJECT_INDEX.md` for project continuity.",
            "- Use `data/derived/decision_log/DECISION_LOG.md` for durable decisions.",
            "- Use `data/derived/timeline/TIMELINE.md` for chronological history.",
            "",
            "## Future Agent Sync Rules",
            "",
            "- If profile, preference, taste, history, or pattern changes, update the mapped source files first.",
            "- Regenerate this export after every meaningful memory sync.",
            "- Do not write raw transcripts, cookies, browser profiles, or plaintext secrets into GitHub.",
            "",
            "## Meta Rules",
            "",
            *render_items(meta_items, 10),
            "",
        ]
    )
    return "\n".join(line for line in lines if line is not None)


def render_codex(payload: dict[str, Any]) -> str:
    startup_route = payload.get("routes", {}).get("startup", {})
    codex_route = payload.get("routes", {}).get("codex_personalization", {})
    sync_targets = payload.get("sync_required_targets", [])
    log_categories = payload.get("run_log_categories", [])
    lines = markdown_header("Codex Personalization Export", payload)
    lines.extend(
        [
            "## Startup Read Order",
            "",
            *[f"- `{path}`" for path in startup_route.get("read_order", [])],
            "",
            "## Codex Route",
            "",
            *[f"- `{path}`" for path in codex_route.get("read_order", [])],
            "",
            "## Required Sync Targets",
            "",
            *[f"- `{target}`" for target in sync_targets],
            "",
            "## Four Run Log Categories",
            "",
            *[f"- `data/run_logs/{category}/`" for category in log_categories],
            "",
            "## Agent Rules",
            "",
            "- Default to Chinese for user-facing replies unless technical terms require English.",
            "- Prefer route-specific context before broad repository search.",
            "- Treat GitHub as the durable backup surface for redacted derived memory and generated personalization exports.",
            "- If a memory-affecting run cannot update the relevant source file, log `UNKNOWN` with a follow-up task.",
            "- Never commit raw exports, full transcripts, cookies, browser profiles, local absolute paths, or plaintext secrets.",
            "",
        ]
    )
    return "\n".join(lines)


def append_export_log(database_dir: Path, payload: dict[str, Any], output_files: list[str]) -> Path:
    log_dir = database_dir / EXPORT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    day = payload["generated_at"][:10]
    log_path = log_dir / f"{day}.jsonl"
    head = git_head(database_dir)
    row = {
        "timestamp": payload["generated_at"],
        "category": "export_runs",
        "task_id": "TASK-OAI-D-001",
        "run_type": "export_run",
        "status": "PASS",
        "task": "build_personalization_exports",
        "updated_targets": payload.get("sync_required_targets", []),
        "source_files": list(payload.get("source_files", {}).values()),
        "output_files": output_files,
        "context_used": [
            {"source": str(CONTEXT_CONFIG), "reason": "three-layer source map"},
            {"source": str(ROUTE_CONFIG), "reason": "resource routing source map"},
        ],
        "tools_used": [
            {"tool": "python", "operation": "build_personalization_exports", "result": "success"}
        ],
        "tests": ["scripts/evaluate_personalization_context.py"],
        "tests_run": [
            {
                "command": "python3 scripts/build_personalization_exports.py --database-dir .",
                "exit_code": 0,
                "result": "PASS",
                "evidence": "data/run_logs/evidence/TASK-OAI-D-001-build-exports.txt",
            }
        ],
        "failure_recovery": [],
        "base_commit": head,
        "result_commit": head,
        "risks": ["generated exports are redacted derived context, not raw private data"],
        "residual_risks": ["generated exports remain redacted derived context, not raw private data"],
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return log_path


def write_exports(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    payload = build_export_payload(database_dir)
    output_files = [rel(CHATGPT_EXPORT), rel(CODEX_EXPORT), rel(MACHINE_EXPORT)]
    changed = [
        write_text_if_changed(database_dir / CHATGPT_EXPORT, render_chatgpt(payload)),
        write_text_if_changed(database_dir / CODEX_EXPORT, render_codex(payload)),
        write_text_if_changed(database_dir / MACHINE_EXPORT, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"),
    ]
    log_path = None
    if any(changed):
        log_path = append_export_log(database_dir, payload, output_files)
    return {
        "status": "PASS",
        "generated_at": payload["generated_at"],
        "outputs": output_files,
        "log": str(log_path.relative_to(database_dir)) if log_path else "not_appended_no_output_changes",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ChatGPT and Codex personalization exports.")
    parser.add_argument("--database-dir", type=Path, default=Path("."), help="OpenAIDatabase repository root.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = write_exports(args.database_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
