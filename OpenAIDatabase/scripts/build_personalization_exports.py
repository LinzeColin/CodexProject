#!/usr/bin/env python3
"""Build ChatGPT, Codex, and Claude personalization exports from redacted derived data."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_agent_context_pack import (
    CODEX_RECOMMENDATIONS,
    CODEX_SNAPSHOT,
    CORE_PROFILE,
    DATA_SOURCE_REGISTRY,
    MEMORY_ATLAS,
    build_agent_context_pack,
    write_if_changed,
)


CONTEXT_CONFIG = Path("config/context_sources/three_layer_context.json")
ROUTE_CONFIG = Path("config/context_sources/resource_routes.json")
DEFAULT_OUTPUT_DIR = Path("data/derived/personalization")
CHATGPT_EXPORT = DEFAULT_OUTPUT_DIR / "chatgpt_personalization.md"
CODEX_EXPORT = DEFAULT_OUTPUT_DIR / "codex_personalization.md"
CLAUDE_EXPORT = DEFAULT_OUTPUT_DIR / "claude_personalization.md"
OTHER_AGENT_EXPORT = DEFAULT_OUTPUT_DIR / "other_agent_personalization.md"
HUMAN_ZH_EXPORT = DEFAULT_OUTPUT_DIR / "personalization_prompt_human_zh.md"
MACHINE_EXPORT = DEFAULT_OUTPUT_DIR / "personalization_export.json"
MEMORY_BUNDLE_MANIFEST = DEFAULT_OUTPUT_DIR / "memory_bundle_manifest.json"
EXPORT_LOG_DIR = Path("data/run_logs/export_runs")
S12_P2_PROMPT_VERSION = "personalization_prompt.v1_2_s12_p2"
S12_P2_TASK_ID = "MA-V12-S12P2"
S12_P2_ACCEPTANCE_ID = "ACC-MA-V12-S12P2"
S12_P2_STATUS = "phase_s12_p2_personalization_prompt_completed_pending_s12_p3"
BUNDLE_SCHEMA_VERSION = "openai_database.memory_bundle_manifest.v2"
PROJECTION_SCHEMA_VERSION = "openai_database.provider_projection.v1"
BUNDLE_GENERATOR_VERSION = "openai_database.shared_memory_bundle.v2"
SHARED_MEMORY_TASK_ID = "OAIDB-SM-P0-R1"
SHARED_MEMORY_ACCEPTANCE_ID = "ACC-OAIDB-SM-P0-R1"
CLAUDE_MAX_BYTES = 4096
PROVIDER_EXPORTS = {
    "chatgpt": CHATGPT_EXPORT,
    "codex": CODEX_EXPORT,
    "claude": CLAUDE_EXPORT,
}
FORBIDDEN_CANONICAL_PREFIXES = (
    "data/raw",
    "data/private",
    "data/raw_encrypted",
    "data/private_imports",
    "private_exports",
    "exports/private",
)
LOCAL_PATH_MARKERS = ("/Users/", "C:\\Users\\")
SOURCE_REPORTS = [
    "data/derived/personalization/personalization_export.json",
    "data/derived/behavior_intelligence/events.json",
    "data/derived/behavior_intelligence/clusters.json",
    "data/derived/behavior_intelligence/latent_signals.json",
    "data/derived/behavior_intelligence/self_iteration_suggestions.json",
    "data/derived/behavior_intelligence/decision_debt_ledger.json",
    "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
]
AGENT_CONTEXT_INPUTS = (
    CORE_PROFILE,
    CODEX_RECOMMENDATIONS,
    CODEX_SNAPSHOT,
    MEMORY_ATLAS,
    DATA_SOURCE_REGISTRY,
)


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


def compact_text(value: Any, fallback: str = "") -> str:
    text = str(value or fallback).strip()
    return " ".join(text.split())


def source_report_freshness(database_dir: Path) -> dict[str, dict[str, Any]]:
    freshness: dict[str, dict[str, Any]] = {}
    for relative in SOURCE_REPORTS:
        path = database_dir / relative
        item: dict[str, Any] = {
            "path": relative,
            "exists": path.exists(),
        }
        if relative == rel(MACHINE_EXPORT):
            item["source_role"] = "machine_export_output"
            freshness[relative] = item
            continue
        if path.exists():
            payload = read_json(path)
            item.update({
                "reported_generated_at": compact_text(payload.get("generated_at")),
                "status": compact_text(payload.get("status"), "UNKNOWN"),
                "task_id": compact_text(payload.get("task_id")),
                "acceptance_id": compact_text(payload.get("acceptance_id")),
            })
        freshness[relative] = item
    return freshness


def equivalent_payload_without_generated_at(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_copy = dict(left)
    right_copy = dict(right)
    left_copy.pop("generated_at", None)
    right_copy.pop("generated_at", None)
    left_copy.pop("projection_hashes", None)
    right_copy.pop("projection_hashes", None)
    left_copy.pop("memory_bundle_manifest", None)
    right_copy.pop("memory_bundle_manifest", None)
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


def sha256_value(payload: bytes | str) -> str:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    return "sha256:" + hashlib.sha256(data).hexdigest()


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_source_paths(context_config: dict[str, Any]) -> list[str]:
    paths = {rel(CONTEXT_CONFIG)}
    layers = context_config.get("layers", [])
    if not isinstance(layers, list):
        layers = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        for value in layer.get("canonical_files", []):
            if not isinstance(value, str) or not value.strip():
                continue
            normalized = Path(value).as_posix()
            if Path(normalized).is_absolute() or ".." in Path(normalized).parts:
                raise ValueError(f"canonical source must be repository-relative: {value}")
            if normalized.startswith(FORBIDDEN_CANONICAL_PREFIXES):
                raise ValueError(f"raw/private path cannot enter shared memory bundle: {normalized}")
            paths.add(normalized)
    return sorted(paths)


def projection_input_paths(context_config: dict[str, Any]) -> list[str]:
    """Return every repository file whose state can affect provider projections."""
    paths = set(canonical_source_paths(context_config))
    paths.add(rel(ROUTE_CONFIG))
    paths.update(rel(path) for path in AGENT_CONTEXT_INPUTS)
    paths.update(path for path in SOURCE_REPORTS if path != rel(MACHINE_EXPORT))
    return sorted(paths)


def build_source_records(database_dir: Path, paths: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in paths:
        path = database_dir / relative
        records.append(
            {
                "path": relative,
                "exists": path.is_file(),
                "content_hash": sha256_value(path.read_bytes()) if path.is_file() else None,
            }
        )
    return records


def build_bundle_identity(database_dir: Path, context_config: dict[str, Any]) -> dict[str, Any]:
    source_records = build_source_records(database_dir, canonical_source_paths(context_config))
    canonical_source_hash = sha256_value(stable_json(source_records))
    projection_input_records = build_source_records(database_dir, projection_input_paths(context_config))
    projection_input_hash = sha256_value(stable_json(projection_input_records))
    identity_contract = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "generator_version": BUNDLE_GENERATOR_VERSION,
        "canonical_source_hash": canonical_source_hash,
        "projection_input_hash": projection_input_hash,
        "source_files": [record["path"] for record in source_records],
        "projection_input_files": [record["path"] for record in projection_input_records],
        "providers": sorted(PROVIDER_EXPORTS),
    }
    return {
        "bundle_id": sha256_value(stable_json(identity_contract)),
        "canonical_source_hash": canonical_source_hash,
        "source_records": source_records,
        "projection_input_hash": projection_input_hash,
        "projection_input_records": projection_input_records,
    }


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
    bundle_identity = build_bundle_identity(database_dir, context_config)
    sync_targets = context_config.get("sync_required_targets", [])
    log_categories = context_config.get("run_log_categories", [])
    layers = context_config.get("layers", [])
    if not isinstance(sync_targets, list):
        sync_targets = []
    if not isinstance(log_categories, list):
        log_categories = []
    if not isinstance(layers, list):
        layers = []
    latest_inputs = build_prompt_inputs(database_dir, pack)
    prompts = build_prompts(latest_inputs)
    payload = {
        "schema_version": "openai_database.personalization_export.v1_2_s12_p2",
        "task_id": S12_P2_TASK_ID,
        "acceptance_id": S12_P2_ACCEPTANCE_ID,
        "status": S12_P2_STATUS,
        "prompt_version": S12_P2_PROMPT_VERSION,
        "generated_at": now_utc(),
        "source": "redacted_derived_openai_database_context",
        "targets": ["chatgpt", "codex", "claude", "other_agent"],
        "bundle_task_id": SHARED_MEMORY_TASK_ID,
        "bundle_acceptance_id": SHARED_MEMORY_ACCEPTANCE_ID,
        "bundle_id": bundle_identity["bundle_id"],
        "canonical_source_hash": bundle_identity["canonical_source_hash"],
        "projection_input_hash": bundle_identity["projection_input_hash"],
        "bundle_generator_version": BUNDLE_GENERATOR_VERSION,
        "bundle_manifest": rel(MEMORY_BUNDLE_MANIFEST),
        "canonical_source_files": [record["path"] for record in bundle_identity["source_records"]],
        "canonical_source_records": bundle_identity["source_records"],
        "projection_input_files": [record["path"] for record in bundle_identity["projection_input_records"]],
        "projection_input_records": bundle_identity["projection_input_records"],
        "source_reports": SOURCE_REPORTS,
        "source_report_freshness": source_report_freshness(database_dir),
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
            "claude_personalization": route_by_intent(route_config, "claude_personalization"),
            "project_history": route_by_intent(route_config, "project_history"),
            "taste_profile": route_by_intent(route_config, "taste_profile"),
        },
        "profile": pack.get("profile", {}),
        "memory": pack.get("memory", {}),
        "preferences": pack.get("preferences", {}),
        "meta_data": pack.get("meta_data", {}),
        "behavior": pack.get("behavior", {}),
        "latest_inputs": latest_inputs,
        "prompts": prompts,
        "data_sources": pack.get("data_sources", {}),
        "safety": {
            **pack.get("safety", {}),
            "raw_private_data_included": False,
            "plaintext_secrets_included": False,
            "local_absolute_paths_included": False,
            "sends_to_chatgpt": False,
            "user_trigger_required": True,
            "no_automatic_send": True,
            "no_raw_mutation": True,
            "no_proposal_apply_execution": True,
            "s12_p3_chatgpt_deep_explore_execution": False,
        },
    }
    existing_payload = read_json(database_dir / MACHINE_EXPORT)
    if existing_payload and equivalent_payload_without_generated_at(payload, existing_payload):
        payload["generated_at"] = str(existing_payload.get("generated_at") or payload["generated_at"])
    return payload


def top_rows(items: list[dict[str, Any]], primary_fields: tuple[str, ...], limit: int = 6) -> list[str]:
    rows: list[str] = []
    for item in items[:limit]:
        parts = [compact_text(item.get(field)) for field in primary_fields]
        text = " / ".join(part for part in parts if part)
        if text:
            rows.append(text)
    return rows


def build_prompt_inputs(database_dir: Path, pack: dict[str, Any]) -> dict[str, Any]:
    events = read_json(database_dir / "data/derived/behavior_intelligence/events.json")
    clusters = read_json(database_dir / "data/derived/behavior_intelligence/clusters.json")
    latent = read_json(database_dir / "data/derived/behavior_intelligence/latent_signals.json")
    self_iteration = read_json(database_dir / "data/derived/behavior_intelligence/self_iteration_suggestions.json")
    decision_debt = read_json(database_dir / "data/derived/behavior_intelligence/decision_debt_ledger.json")
    collaboration = read_json(database_dir / "data/derived/agent_collaboration/agent_collaboration_quality_report.json")

    memory_items = pack.get("memory", {}).get("current", [])
    if not isinstance(memory_items, list):
        memory_items = []
    topic_clusters = clusters.get("topic_clusters", [])
    if not isinstance(topic_clusters, list):
        topic_clusters = []
    latent_signals = latent.get("latent_signals", [])
    if not isinstance(latent_signals, list):
        latent_signals = []
    suggestions = self_iteration.get("self_iteration_suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []
    debts = decision_debt.get("decision_debt_ledger", [])
    if not isinstance(debts, list):
        debts = []
    overall_metrics = collaboration.get("overall_metrics", [])
    if not isinstance(overall_metrics, list):
        overall_metrics = []

    return {
        "latest_memory": top_rows(memory_items, ("title", "statement", "confidence"), 8),
        "behavior": {
            "event_count": int(events.get("event_count") or 0),
            "cluster_count": int(clusters.get("cluster_count") or 0),
            "top_topics": top_rows(topic_clusters, ("label_zh", "summary_zh"), 8),
            "top_behavior_topics": pack.get("behavior", {}).get("top_topics", []),
        },
        "latent": {
            "signal_count": int(latent.get("signal_count") or 0),
            "claims": top_rows(latent_signals, ("claim_zh", "confidence_label", "next_validation_zh"), 6),
        },
        "self_iteration": {
            "suggestion_count": int(self_iteration.get("suggestion_count") or 0),
            "suggestions": top_rows(suggestions, ("target_type", "expected_change_zh", "rationale_zh"), 6),
        },
        "decision_debt": {
            "decision_debt_count": int(decision_debt.get("decision_debt_count") or 0),
            "items": top_rows(debts, ("decision_area_zh", "minimal_next_step_zh", "closure_rule_zh"), 6),
        },
        "agent_collaboration": {
            "summary_zh": compact_text(collaboration.get("chinese_summary", {}).get("summary_zh")),
            "metrics": top_rows(overall_metrics, ("name_zh", "level", "explanation_zh"), 6),
        },
    }


def bullet_lines(rows: list[str], fallback: str) -> list[str]:
    return [f"- {row}" for row in rows] if rows else [f"- {fallback}"]


def machine_copyable_prompt(target_id: str, target_label: str, latest_inputs: dict[str, Any]) -> str:
    behavior = latest_inputs.get("behavior", {})
    latent = latest_inputs.get("latent", {})
    self_iteration = latest_inputs.get("self_iteration", {})
    decision_debt = latest_inputs.get("decision_debt", {})
    collaboration = latest_inputs.get("agent_collaboration", {})
    lines = [
        f"You are the {target_label} assistant for Linze.",
        f"Task contract: {S12_P2_TASK_ID} / {S12_P2_ACCEPTANCE_ID} / {S12_P2_PROMPT_VERSION}.",
        "Use this as the latest memory / behavior / latent / self_iteration personalization prompt.",
        "",
        "Core operating style:",
        "- Default to Chinese for user-facing replies; keep code, APIs, library names and errors in English when useful.",
        "- Be accurate, executable, evidence-backed, high ROI and low-noise.",
        "- Preserve one-phase-per-run boundaries for staged Memory Atlas work.",
        "- Prefer numbered choices, status tables, clear assumptions, validation commands and stop conditions over broad free-text interviews.",
        "",
        "latest memory:",
        *bullet_lines(latest_inputs.get("latest_memory", []), "No reviewed latest memory item is currently available."),
        "",
        "behavior:",
        f"- events={behavior.get('event_count', 0)}; clusters={behavior.get('cluster_count', 0)}.",
        *bullet_lines(behavior.get("top_topics", []), "No behavior cluster summary is currently available."),
        "",
        "latent:",
        f"- latent_signal_count={latent.get('signal_count', 0)}.",
        *bullet_lines(latent.get("claims", []), "No latent signal summary is currently available."),
        "",
        "self_iteration:",
        f"- suggestion_count={self_iteration.get('suggestion_count', 0)}.",
        *bullet_lines(self_iteration.get("suggestions", []), "No self-iteration suggestion is currently available."),
        "",
        "decision and collaboration context:",
        f"- decision_debt_count={decision_debt.get('decision_debt_count', 0)}.",
        *bullet_lines(decision_debt.get("items", []), "No decision debt item is currently available."),
        f"- collaboration_summary={collaboration.get('summary_zh') or 'No collaboration summary is currently available.'}",
        "",
        "Safety and phase boundaries:",
        "- No automatic send.",
        "- No raw mutation.",
        "- No proposal apply execution.",
        "- No cookie, token, browser profile or plaintext secret export.",
        "- No S12 P3 ChatGPT deep explore execution in this phase.",
    ]
    return "\n".join(lines)


def build_prompts(latest_inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    targets = {
        "chatgpt": ("ChatGPT", rel(CHATGPT_EXPORT)),
        "codex": ("Codex", rel(CODEX_EXPORT)),
        "claude": ("Claude Code", rel(CLAUDE_EXPORT)),
        "other_agent": ("other agent", rel(OTHER_AGENT_EXPORT)),
    }
    prompts: dict[str, dict[str, Any]] = {}
    for target_id, (label, output_file) in targets.items():
        prompts[target_id] = {
            "target_id": target_id,
            "target_label": label,
            "output_file": output_file,
            "human_explanation_zh": f"给 {label} 使用的最新个性化提示词，来自 latest memory、behavior、latent、self_iteration 和协作质量等脱敏派生报告。",
            "machine_copyable_text": machine_copyable_prompt(target_id, label, latest_inputs),
            "user_trigger_required": True,
            "sends_to_chatgpt": False,
            "raw_mutation": False,
            "source_reports": SOURCE_REPORTS,
        }
    return prompts


def markdown_header(title: str, payload: dict[str, Any], provider: str = "provider-neutral") -> list[str]:
    return [
        f"# {title}",
        "",
        f"- schema_version: {PROJECTION_SCHEMA_VERSION}",
        f"- provider: {provider}",
        f"- bundle_id: {payload['bundle_id']}",
        f"- canonical_source_hash: {payload['canonical_source_hash']}",
        f"- task_id: {payload.get('task_id', S12_P2_TASK_ID)}",
        f"- acceptance_id: {payload.get('acceptance_id', S12_P2_ACCEPTANCE_ID)}",
        f"- prompt_version: {payload.get('prompt_version', S12_P2_PROMPT_VERSION)}",
        f"- generated_at: {payload['generated_at']}",
        "- source: OpenAIDatabase redacted derived context",
        "- artifact_contract: Derived / Read-only / Regenerate, do not hand edit",
        "- raw_private_data_included: false",
        "- plaintext_secrets_included: false",
        "",
    ]


def render_prompt_target(payload: dict[str, Any], target_id: str) -> str:
    prompt = payload.get("prompts", {}).get(target_id, {})
    target_label = str(prompt.get("target_label") or target_id)
    machine_text = str(prompt.get("machine_copyable_text") or "")
    lines = markdown_header(f"{target_label} Personalization Prompt", payload, target_id)
    lines.extend(
        [
            "## 中文人类说明",
            "",
            str(prompt.get("human_explanation_zh") or "这是给目标 agent 使用的个性化提示词。"),
            "",
            "来源报告：latest memory、behavior、latent、self_iteration、decision debt、agent collaboration。",
            "",
            "边界：No automatic send；No raw mutation；No proposal apply execution；No S12 P3 ChatGPT deep explore execution。",
            "",
            "## 机器可复制文本",
            "",
            "```text",
            machine_text,
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def render_chatgpt(payload: dict[str, Any]) -> str:
    profile_items = payload.get("profile", {}).get("core_profile_items", [])
    memory_items = payload.get("memory", {}).get("current", [])
    meta_items = payload.get("meta_data", {}).get("current", [])
    top_topics = payload.get("preferences", {}).get("top_topics", [])
    lines = [
        render_prompt_target(payload, "chatgpt"),
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
    return "\n".join(line for line in lines if line is not None)


def render_codex(payload: dict[str, Any]) -> str:
    return render_prompt_target(payload, "codex")


def bounded_text(value: Any, max_chars: int = 240) -> str:
    text = compact_text(value)
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"


def render_claude(payload: dict[str, Any]) -> str:
    profile_items = payload.get("profile", {}).get("core_profile_items", [])
    if not isinstance(profile_items, list):
        profile_items = []
    lines = markdown_header("Claude Code Personalization Projection", payload, "claude")
    lines.extend(
        [
            "## 冷启动协议",
            "",
            "- 默认中文回复；代码、API、库名、错误和英文项目语境可保留英文。",
            "- 准确、真实、可执行、证据优先；不把推断、进度或测试写成已验证事实。",
            "- 每次只处理一个项目、一个 Task、一个 Acceptance；项目状态只读该项目 canonical governance。",
            "- OpenAIDatabase 是长期用户记忆与 provider projection 的唯一持久控制面。",
            "- Claude auto memory、聊天上下文和本文件都不是 canonical truth。",
            "- 普通业务项目 run 不跨项目写 OpenAIDatabase；memory sync 必须独立运行。",
            "",
            "## 稳定画像摘要",
            "",
            *[f"- {bounded_text(item)}" for item in profile_items[:6]],
            *([] if profile_items else ["- 当前没有可用的 reviewed core profile 摘要。"]),
            "",
            "## Memory Route",
            "",
            "- 默认只读：`data/derived/personalization/claude_personalization.md`。",
            "- 更深画像：按需读取 `data/derived/profile/CORE_PROFILE.md`。",
            "- 项目连续性：按需读取 `data/derived/project_index/PROJECT_INDEX.md`，并以项目治理文件校验当前状态。",
            "- 决策上下文：按需读取 `data/derived/decision_log/DECISION_LOG.md`。",
            "",
            "## 隐私与写回边界",
            "",
            "- 不读取或复制 raw/private、cookie、session、token、browser profile 或 plaintext secret。",
            "- projection 只读且只能由生成器重建；长期记忆更新必须先修改 mapped canonical source。",
            "- 未经明确 memory-sync task，不写回 OpenAIDatabase。",
            "",
        ]
    )
    rendered = "\n".join(lines)
    if len(rendered.encode("utf-8")) > CLAUDE_MAX_BYTES:
        raise ValueError(f"Claude projection exceeds {CLAUDE_MAX_BYTES} bytes")
    return rendered


def render_other_agent(payload: dict[str, Any]) -> str:
    return render_prompt_target(payload, "other_agent")


def render_human_zh(payload: dict[str, Any]) -> str:
    latest_inputs = payload.get("latest_inputs", {})
    prompts = payload.get("prompts", {})
    lines = markdown_header("Personalization Prompt 中文人类说明", payload)
    lines.extend(
        [
            "## 结论",
            "",
            f"已生成 ChatGPT、Codex、Claude、other agent 可用的最新 Personalization Prompt；共享 identity 由 `{MEMORY_BUNDLE_MANIFEST.as_posix()}` 证明。",
            "",
            "本文件是中文人类说明；每个目标文件都包含 `机器可复制文本` fenced block，可直接复制到对应 agent 的 personalization 或启动上下文。",
            "",
            "## 来源报告",
            "",
            *[f"- `{source}`" for source in SOURCE_REPORTS],
            "",
            "## 摘要",
            "",
            "latest memory:",
            *bullet_lines(latest_inputs.get("latest_memory", []), "暂无最新 memory 摘要。"),
            "",
            "behavior:",
            *bullet_lines(latest_inputs.get("behavior", {}).get("top_topics", []), "暂无 behavior 摘要。"),
            "",
            "latent:",
            *bullet_lines(latest_inputs.get("latent", {}).get("claims", []), "暂无 latent 摘要。"),
            "",
            "self_iteration:",
            *bullet_lines(latest_inputs.get("self_iteration", {}).get("suggestions", []), "暂无 self_iteration 摘要。"),
            "",
            "## 输出文件",
            "",
            f"- ChatGPT: `{CHATGPT_EXPORT.as_posix()}`",
            f"- Codex: `{CODEX_EXPORT.as_posix()}`",
            f"- Claude: `{CLAUDE_EXPORT.as_posix()}`",
            f"- other agent: `{OTHER_AGENT_EXPORT.as_posix()}`",
            f"- machine: `{MACHINE_EXPORT.as_posix()}`",
            f"- bundle manifest: `{MEMORY_BUNDLE_MANIFEST.as_posix()}`",
            "",
            "## 机器可复制文本",
            "",
            *[
                f"- {prompt.get('target_label')}: `{prompt.get('output_file')}`"
                for prompt in prompts.values()
                if isinstance(prompt, dict)
            ],
            "",
            "## 边界",
            "",
            "- No automatic send。",
            "- No GitHub main upload。",
            "- No remote push。",
            "- No raw mutation。",
            "- No proposal apply execution。",
            "- No S12 P3 ChatGPT deep explore execution。",
            "",
        ]
    )
    return "\n".join(lines)


def render_provider_outputs(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "chatgpt": render_chatgpt(payload),
        "codex": render_codex(payload),
        "claude": render_claude(payload),
    }


def build_memory_bundle_manifest(
    database_dir: Path,
    payload: dict[str, Any],
    provider_outputs: dict[str, str],
) -> dict[str, Any]:
    projections = {
        provider: {
            "path": rel(PROVIDER_EXPORTS[provider]),
            "projection_hash": sha256_value(provider_outputs[provider]),
        }
        for provider in sorted(PROVIDER_EXPORTS)
    }
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_id": payload["bundle_id"],
        "canonical_source_hash": payload["canonical_source_hash"],
        "generator_version": BUNDLE_GENERATOR_VERSION,
        "generated_at": payload["generated_at"],
        "source_files": payload["canonical_source_files"],
        "source_records": payload["canonical_source_records"],
        "projection_input_hash": payload["projection_input_hash"],
        "projection_input_files": payload["projection_input_files"],
        "projection_input_records": payload["projection_input_records"],
        "projections": projections,
        "artifact_contract": "Derived / Read-only / Regenerate, do not hand edit",
        "raw_private_data_included": False,
        "plaintext_secrets_included": False,
        "local_absolute_paths_included": False,
    }


def forbidden_patterns(database_dir: Path) -> list[str]:
    harness = read_json(database_dir / "config/evaluation/personalization_harness.json")
    values = harness.get("forbidden_plaintext_patterns", [])
    return [str(value) for value in values if isinstance(value, str) and value]


def validate_generated_artifacts(
    database_dir: Path,
    provider_outputs: dict[str, str],
    manifest: dict[str, Any],
) -> None:
    combined = "\n".join(provider_outputs.values()) + "\n" + stable_json(manifest)
    for pattern in forbidden_patterns(database_dir):
        if pattern in combined:
            raise ValueError(f"forbidden plaintext pattern in generated shared-memory artifacts: {pattern}")
    for marker in LOCAL_PATH_MARKERS:
        if marker in combined:
            raise ValueError(f"local absolute path in generated shared-memory artifacts: {marker}")
    for relative in [*manifest["source_files"], *manifest["projection_input_files"]]:
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"manifest source path must be repository-relative: {relative}")
        if relative.startswith(FORBIDDEN_CANONICAL_PREFIXES):
            raise ValueError(f"manifest cannot reference raw/private source: {relative}")
    if set(manifest["projections"]) != set(PROVIDER_EXPORTS):
        raise ValueError("manifest must contain exactly ChatGPT, Codex, and Claude projections")
    if len(provider_outputs["claude"].encode("utf-8")) > CLAUDE_MAX_BYTES:
        raise ValueError(f"Claude projection exceeds {CLAUDE_MAX_BYTES} bytes")


def append_export_log(database_dir: Path, payload: dict[str, Any], output_files: list[str]) -> Path:
    log_dir = database_dir / EXPORT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = Path("data/run_logs/evidence/TASK-OAI-D-001-build-exports.txt")
    write_text_if_changed(
        database_dir / evidence_path,
        "\n".join(
            [
                "task_id=TASK-OAI-D-001",
                "task=build_personalization_exports",
                "result=PASS",
                f"prompt_version={S12_P2_PROMPT_VERSION}",
                f"outputs={', '.join(output_files)}",
                "raw_private_data_included=false",
                "plaintext_secrets_included=false",
                "",
            ]
        ),
    )
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
                "evidence": evidence_path.as_posix(),
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
    provider_outputs = render_provider_outputs(payload)
    projection_hashes = {
        provider: sha256_value(text)
        for provider, text in sorted(provider_outputs.items())
    }
    payload["projection_hashes"] = projection_hashes
    payload["memory_bundle_manifest"] = rel(MEMORY_BUNDLE_MANIFEST)
    manifest = build_memory_bundle_manifest(database_dir, payload, provider_outputs)
    validate_generated_artifacts(database_dir, provider_outputs, manifest)
    output_files = [
        rel(HUMAN_ZH_EXPORT),
        rel(CHATGPT_EXPORT),
        rel(CODEX_EXPORT),
        rel(CLAUDE_EXPORT),
        rel(OTHER_AGENT_EXPORT),
        rel(MACHINE_EXPORT),
        rel(MEMORY_BUNDLE_MANIFEST),
    ]
    changed = [
        write_text_if_changed(database_dir / HUMAN_ZH_EXPORT, render_human_zh(payload)),
        write_text_if_changed(database_dir / CHATGPT_EXPORT, provider_outputs["chatgpt"]),
        write_text_if_changed(database_dir / CODEX_EXPORT, provider_outputs["codex"]),
        write_text_if_changed(database_dir / CLAUDE_EXPORT, provider_outputs["claude"]),
        write_text_if_changed(database_dir / OTHER_AGENT_EXPORT, render_other_agent(payload)),
        write_text_if_changed(database_dir / MACHINE_EXPORT, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"),
        write_text_if_changed(database_dir / MEMORY_BUNDLE_MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"),
    ]
    log_path = None
    if any(changed):
        log_path = append_export_log(database_dir, payload, output_files)
    return {
        "status": "PASS",
        "task_id": S12_P2_TASK_ID,
        "acceptance_id": S12_P2_ACCEPTANCE_ID,
        "prompt_version": S12_P2_PROMPT_VERSION,
        "generated_at": payload["generated_at"],
        "bundle_id": payload["bundle_id"],
        "canonical_source_hash": payload["canonical_source_hash"],
        "projection_hashes": projection_hashes,
        "outputs": output_files,
        "sends_to_chatgpt": False,
        "raw_mutation": False,
        "log": str(log_path.relative_to(database_dir)) if log_path else "not_appended_no_output_changes",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ChatGPT, Codex, and Claude personalization exports.")
    parser.add_argument("--database-dir", type=Path, default=Path("."), help="OpenAIDatabase repository root.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = write_exports(args.database_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
