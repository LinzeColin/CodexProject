#!/usr/bin/env python3
"""Minimal Memory Atlas control CLI introduced stage by stage."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHATGPT_SYNC = ROOT / "scripts" / "sync_chatgpt_memory_data.py"
CODEX_SYNC = ROOT / "scripts" / "sync_codex_memory_data.py"
FUTURE_AGENT_SYNC = ROOT / "scripts" / "sync_future_agent_data.py"
BUILD_ATLAS = ROOT / "scripts" / "build_memory_atlas_data.py"
GITHUB_BACKUP = ROOT / "scripts" / "github_backup.py"
FACET_EXTRACTOR = ROOT / "scripts" / "extract_memory_atlas_facets.py"
CLUSTER_BUILDER = ROOT / "scripts" / "build_memory_atlas_clusters.py"
LOW_VALUE_LOOP_BUILDER = ROOT / "scripts" / "build_memory_atlas_low_value_loops.py"
OPPORTUNITY_BUILDER = ROOT / "scripts" / "build_memory_atlas_opportunities.py"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas control CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync = subparsers.add_parser("sync", help="Run source sync.")
    sync.add_argument("--source", required=True)
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--official-export", type=Path)
    sync.add_argument("--codex-home", type=Path)
    sync.add_argument("--agent-id", default="future-agent")
    sync.add_argument("--input", type=Path)

    build_atlas = subparsers.add_parser("build-atlas", help="Build derived Memory Atlas visualization data.")
    build_atlas.add_argument("--dry-run", action="store_true")

    analyze = subparsers.add_parser("analyze", help="Run derived behavior intelligence analysis.")
    analyze.add_argument("--stage", required=True)
    analyze.add_argument("--dry-run", action="store_true")
    analyze.add_argument("--database-dir", type=Path, default=ROOT)
    analyze.add_argument("--source")
    analyze.add_argument("--time-from")
    analyze.add_argument("--time-to")
    analyze.add_argument("--project")
    analyze.add_argument("--task")
    analyze.add_argument("--language")

    audit = subparsers.add_parser("audit", help="Run Memory Atlas derived evidence audits.")
    audit.add_argument("--check", required=True)
    audit.add_argument("--database-dir", type=Path, default=ROOT)

    push = subparsers.add_parser("push", help="Prepare local GitHub backup scope.")
    mode = push.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    push.add_argument("--database-dir", type=Path, default=ROOT)
    push.add_argument("--message", default="Memory Atlas GitHub backup snapshot")
    return parser.parse_args(argv)


def chatgpt_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "chatgpt",
        "dry_run": True,
        "browser_connector": "readonly_contract",
        "fallback": "official_export",
        "writes_files": False,
        "raw_root": "data/public_raw/chatgpt",
        "derived_summary": "data/derived/chatgpt/chatgpt_sync_summary.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "input_required_for_apply": True,
        "no_browser_mutation": True,
    }


def codex_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "codex",
        "dry_run": True,
        "sync_mode": "codex_local_sync",
        "writes_files": False,
        "raw_root": "data/public_raw/codex",
        "derived_summary": "data/derived/codex/codex_activity_snapshot.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "append_only": True,
    }


def future_agent_contract(agent_id: str) -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "future-agent",
        "agent_id": agent_id,
        "dry_run": True,
        "adapter_mode": "minimal_adapter",
        "writes_files": False,
        "raw_root": f"data/public_raw/agents/{agent_id}",
        "derived_summary": f"data/derived/agents/{agent_id}/agent_sync_summary.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "input_required_for_apply": True,
        "append_only": True,
    }


def run_sync(args: argparse.Namespace) -> int:
    if args.source == "chatgpt" and args.dry_run and not args.official_export:
        print(json.dumps(chatgpt_contract(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "codex" and args.dry_run and not args.codex_home:
        print(json.dumps(codex_contract(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "future-agent" and args.dry_run and not args.input:
        print(json.dumps(future_agent_contract(args.agent_id), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "chatgpt":
        command = [sys.executable, str(CHATGPT_SYNC), "--database-dir", str(ROOT)]
        if args.official_export:
            command.extend(["--official-export", str(args.official_export)])
        if args.dry_run:
            command.append("--dry-run")
    elif args.source == "codex":
        command = [sys.executable, str(CODEX_SYNC), "--database-dir", str(ROOT)]
        if args.codex_home:
            command.extend(["--codex-home", str(args.codex_home)])
        if args.dry_run:
            command.append("--dry-run")
    elif args.source == "future-agent":
        command = [sys.executable, str(FUTURE_AGENT_SYNC), "--database-dir", str(ROOT), "--agent-id", args.agent_id]
        if args.input:
            command.extend(["--input", str(args.input)])
        if args.dry_run:
            command.append("--dry-run")
    else:
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "source_id": args.source,
            "reason": "Unknown sync source. Supported sources: chatgpt, codex, future-agent.",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def run_build_atlas(args: argparse.Namespace) -> int:
    output = "data/derived/visualization/memory_atlas.json"
    if args.dry_run:
        print(json.dumps({
            "status": "PASS",
            "command": "build-atlas",
            "dry_run": True,
            "writes_files": False,
            "output": output,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    command = [sys.executable, str(BUILD_ATLAS), "--database-dir", str(ROOT), "--output", output]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def facet_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "facets",
        "dry_run": True,
        "writes_files": False,
        "extractor": "scripts/extract_memory_atlas_facets.py",
        "output": "data/derived/behavior_intelligence/events.json",
        "input_roots": [
            "data/public_raw/chatgpt",
            "data/public_raw/codex",
            "data/public_raw/agents",
            "data/processed/conversations/conversation_manifest.jsonl",
            "data/processed/codex/codex_session_manifest.jsonl",
            "data/derived/codex",
            "data/derived/agents",
        ],
        "missing_source_policy": "record source_status missing_reason without fake events",
        "raw_mutation": False,
        "task_id": "MA-V12-S05P3",
        "acceptance_id": "ACC-MA-V12-S05P3",
    }


def cluster_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "clusters",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_clusters.py",
        "input": "data/derived/behavior_intelligence/events.json",
        "output": "data/derived/behavior_intelligence/clusters.json",
        "supported_filters": ["source", "time", "project", "task", "language"],
        "raw_mutation": False,
        "task_id": "MA-V12-S06P1",
        "acceptance_id": "ACC-MA-V12-S06P1",
    }


def low_value_loop_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "low-value-loops",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_low_value_loops.py",
        "input": [
            "data/derived/behavior_intelligence/events.json",
            "data/derived/behavior_intelligence/clusters.json",
        ],
        "output": "data/derived/behavior_intelligence/low_value_loops.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S06P2",
        "acceptance_id": "ACC-MA-V12-S06P2",
        "phase_boundary": {
            "does_not_generate_opportunity_cards": True,
            "next_phase": "S06 P3",
        },
    }


def opportunity_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "opportunities",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_opportunities.py",
        "input": [
            "data/derived/behavior_intelligence/events.json",
            "data/derived/behavior_intelligence/clusters.json",
            "data/derived/behavior_intelligence/low_value_loops.json",
        ],
        "output": "data/derived/behavior_intelligence/opportunities.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S06P3",
        "acceptance_id": "ACC-MA-V12-S06P3",
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_create_infinite_pressure_list": True,
            "next_phase": "S06 Review",
        },
    }


def run_analyze(args: argparse.Namespace) -> int:
    if args.stage not in {"facets", "clusters", "low-value-loops", "opportunities"}:
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "command": "analyze",
            "stage": args.stage,
            "reason": "Unknown analyze stage. Supported stages: facets, clusters, low-value-loops, opportunities.",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    if args.stage == "facets":
        if args.dry_run:
            command = [sys.executable, str(FACET_EXTRACTOR), "--database-dir", str(args.database_dir), "--dry-run"]
        else:
            command = [sys.executable, str(FACET_EXTRACTOR), "--database-dir", str(args.database_dir)]
    elif args.stage == "clusters":
        command = [sys.executable, str(CLUSTER_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
        for cli_name, value in [
            ("--source", args.source),
            ("--time-from", args.time_from),
            ("--time-to", args.time_to),
            ("--project", args.project),
            ("--task", args.task),
            ("--language", args.language),
        ]:
            if value:
                command.extend([cli_name, value])
    elif args.stage == "low-value-loops":
        command = [sys.executable, str(LOW_VALUE_LOOP_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "opportunities":
        command = [sys.executable, str(OPPORTUNITY_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def audit_evidence_collection(
    items: list[dict[str, object]],
    collection_name: str,
    id_field: str,
    required_text_fields: tuple[str, ...],
) -> list[str]:
    bad_items = []
    for item in items:
        item_id = item.get(id_field)
        if not item.get("evidence_refs"):
            bad_items.append(f"{collection_name}:{item_id}:missing_evidence_refs")
        for field_name in required_text_fields:
            if not str(item.get(field_name) or "").strip():
                bad_items.append(f"{collection_name}:{item_id}:missing_{field_name}")
    return bad_items


def run_audit(args: argparse.Namespace) -> int:
    if args.check != "insight-evidence":
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "command": "audit",
            "check": args.check,
            "reason": "Unknown audit check. Supported checks: insight-evidence.",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    clusters_path = args.database_dir / "data/derived/behavior_intelligence/clusters.json"
    if not clusters_path.exists():
        print(json.dumps({
            "status": "FAIL",
            "command": "audit",
            "check": "insight-evidence",
            "reason": "clusters output missing",
            "path": "data/derived/behavior_intelligence/clusters.json",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    payload = json.loads(clusters_path.read_text(encoding="utf-8"))
    bad_clusters = []
    for collection_name in ("topic_clusters", "hierarchy_clusters"):
        for cluster in payload.get(collection_name) or []:
            if not cluster.get("evidence_refs"):
                bad_clusters.append(f"{collection_name}:{cluster.get('cluster_id')}:missing_evidence_refs")
            if not cluster.get("summary_zh"):
                bad_clusters.append(f"{collection_name}:{cluster.get('cluster_id')}:missing_summary_zh")
    low_value_path = args.database_dir / "data/derived/behavior_intelligence/low_value_loops.json"
    low_value_payload = {}
    bad_items = []
    if low_value_path.exists():
        low_value_payload = json.loads(low_value_path.read_text(encoding="utf-8"))
        bad_items.extend(audit_evidence_collection(
            low_value_payload.get("loop_clusters") or [],
            "loop_clusters",
            "loop_id",
            ("summary_zh",),
        ))
        bad_items.extend(audit_evidence_collection(
            low_value_payload.get("decision_debt_ledger") or [],
            "decision_debt_ledger",
            "debt_id",
            ("suggested_closure_question",),
        ))
        bad_items.extend(audit_evidence_collection(
            low_value_payload.get("action_half_life") or [],
            "action_half_life",
            "half_life_id",
            ("interpretation_zh",),
        ))
        for item in low_value_payload.get("action_half_life") or []:
            if int(item.get("action_half_life_days") or 0) <= 0:
                bad_items.append(f"action_half_life:{item.get('half_life_id')}:invalid_action_half_life_days")
    opportunities_path = args.database_dir / "data/derived/behavior_intelligence/opportunities.json"
    opportunities_payload = {}
    if opportunities_path.exists():
        opportunities_payload = json.loads(opportunities_path.read_text(encoding="utf-8"))
        bad_items.extend(audit_evidence_collection(
            opportunities_payload.get("opportunity_clusters") or [],
            "opportunity_clusters",
            "opportunity_id",
            ("summary_zh", "next_step_zh"),
        ))
        for item in opportunities_payload.get("opportunity_clusters") or []:
            card = item.get("why_not_now_card") or {}
            if not card.get("reason_zh") or card.get("not_pressure_list") is not True or not card.get("evidence_refs"):
                bad_items.append(f"opportunity_clusters:{item.get('opportunity_id')}:invalid_why_not_now_card")
            if int(item.get("opportunity_half_life_days") or 0) <= 0 and not item.get("defer_reason_zh"):
                bad_items.append(f"opportunity_clusters:{item.get('opportunity_id')}:missing_half_life_or_defer_reason")
    status = "PASS" if not bad_clusters and not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "insight-evidence",
        "task_id": payload.get("task_id"),
        "acceptance_id": payload.get("acceptance_id"),
        "cluster_count": payload.get("cluster_count"),
        "topic_cluster_count": payload.get("topic_cluster_count"),
        "hierarchy_cluster_count": payload.get("hierarchy_cluster_count"),
        "bad_clusters": bad_clusters,
        "low_value_loop_task_id": low_value_payload.get("task_id"),
        "low_value_loop_acceptance_id": low_value_payload.get("acceptance_id"),
        "loop_cluster_count": low_value_payload.get("loop_cluster_count"),
        "decision_debt_count": low_value_payload.get("decision_debt_count"),
        "action_half_life_count": low_value_payload.get("action_half_life_count"),
        "opportunity_task_id": opportunities_payload.get("task_id"),
        "opportunity_acceptance_id": opportunities_payload.get("acceptance_id"),
        "opportunity_count": opportunities_payload.get("opportunity_count"),
        "defer_card_count": opportunities_payload.get("defer_card_count"),
        "bad_items": bad_items,
        "raw_mutation": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_push(args: argparse.Namespace) -> int:
    command = [sys.executable, str(GITHUB_BACKUP), "--database-dir", str(args.database_dir)]
    if args.dry_run:
        command.append("--dry-run")
    if args.apply:
        command.extend(["--apply", "--message", args.message])
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "sync":
        return run_sync(args)
    if args.command == "build-atlas":
        return run_build_atlas(args)
    if args.command == "analyze":
        return run_analyze(args)
    if args.command == "audit":
        return run_audit(args)
    if args.command == "push":
        return run_push(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
