#!/usr/bin/env python3
"""Build a user-triggered ChatGPT deep exploration prompt payload."""

from __future__ import annotations

import argparse
import json
import re
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


TASK_ID = "MA-V12-S12P3"
ACCEPTANCE_ID = "ACC-MA-V12-S12P3"
STATUS = "phase_s12_p3_chatgpt_deep_explore_completed_pending_s12_review"
CONTRACT_VERSION = "chatgpt_deep_explore.v1_2_s12_p3"
SCHEMA_VERSION = "openai_database.chatgpt_deep_explore.v1_2_s12_p3"

CONFIG_PATH = Path("机器治理/运行门禁/chatgpt_deep_explore.v1_2_s12_p3.json")
OUTPUT_DIR = Path("data/derived/chatgpt_deep_explore")
PROMPT_OUTPUT = OUTPUT_DIR / "latest_memory_analysis_prompt.md"
MACHINE_OUTPUT = OUTPUT_DIR / "chatgpt_deep_explore_export.json"

SOURCE_REPORTS = [
    "data/derived/personalization/personalization_export.json",
    "data/derived/personalization/personalization_prompt_human_zh.md",
    "data/derived/behavior_intelligence/latent_signals.json",
    "data/derived/behavior_intelligence/self_iteration_suggestions.json",
    "data/derived/behavior_intelligence/decision_debt_ledger.json",
    "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)authorization:\s*\S+"),
    re.compile(r"(?i)cookie:\s*\S+"),
    re.compile(r"(?i)sessionid=\S+"),
    re.compile(r"(?i)(access_token|refresh_token)\s*[:=]\s*\S+"),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path, limit: int = 2400) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore").strip()[:limit]


def compact_text(value: Any, fallback: str = "") -> str:
    text = str(value or fallback).strip()
    return " ".join(text.split())


def sanitize_prompt(text: str) -> tuple[str, list[str]]:
    findings: list[str] = []
    sanitized = text
    for pattern in SECRET_PATTERNS:
        if pattern.search(sanitized):
            findings.append(pattern.pattern)
            sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized, findings


def source_report_freshness(database_dir: Path) -> dict[str, dict[str, Any]]:
    freshness: dict[str, dict[str, Any]] = {}
    for relative in SOURCE_REPORTS:
        path = database_dir / relative
        item: dict[str, Any] = {"path": relative, "exists": path.exists()}
        if path.exists() and path.suffix == ".json":
            payload = read_json(path)
            item.update({
                "status": compact_text(payload.get("status"), "UNKNOWN"),
                "task_id": compact_text(payload.get("task_id")),
                "acceptance_id": compact_text(payload.get("acceptance_id")),
                "generated_at": compact_text(payload.get("generated_at")),
            })
        elif path.exists():
            item["size_bytes"] = path.stat().st_size
        freshness[relative] = item
    return freshness


def collect_report_lines(database_dir: Path) -> list[str]:
    personalization = read_json(database_dir / "data/derived/personalization/personalization_export.json")
    latent = read_json(database_dir / "data/derived/behavior_intelligence/latent_signals.json")
    suggestions = read_json(database_dir / "data/derived/behavior_intelligence/self_iteration_suggestions.json")
    debt = read_json(database_dir / "data/derived/behavior_intelligence/decision_debt_ledger.json")
    collaboration = read_json(database_dir / "data/derived/agent_collaboration/agent_collaboration_quality_report.json")
    human_prompt = read_text(database_dir / "data/derived/personalization/personalization_prompt_human_zh.md", limit=1600)

    lines = [
        f"- Personalization prompt: {compact_text(personalization.get('status'), 'UNKNOWN')} / {compact_text(personalization.get('prompt_version'), 'no prompt_version')}",
        f"- Prompt targets: {', '.join(personalization.get('targets') or []) or 'UNKNOWN'}",
        f"- Latent signals: {compact_text(latent.get('signal_count') or latent.get('latent_signal_count'), 'UNKNOWN')}",
        f"- Self-iteration suggestions: {compact_text(suggestions.get('suggestion_count') or suggestions.get('self_iteration_suggestion_count'), 'UNKNOWN')}",
        f"- Decision debt candidates: {compact_text(debt.get('decision_debt_count') or debt.get('candidate_count'), 'UNKNOWN')}",
        f"- Agent collaboration status: {compact_text(collaboration.get('status'), 'UNKNOWN')}",
    ]
    if human_prompt:
        lines.extend(["", "### Personalization Prompt 中文摘要", "", human_prompt])
    return lines


def build_prompt_text(database_dir: Path) -> tuple[str, list[str]]:
    report_lines = collect_report_lines(database_dir)
    prompt = "\n".join([
        "# ChatGPT Deep Exploration Payload",
        "",
        f"Task: {TASK_ID}",
        f"Acceptance: {ACCEPTANCE_ID}",
        f"Contract: {CONTRACT_VERSION}",
        "Mode: prefill_only by default; auto_submit is gated by explicit config and confirmation.",
        "",
        "## 最新记忆分析报告",
        "",
        *report_lines,
        "",
        "## 深度探索提示",
        "",
        "请基于上面的 Memory Atlas v1.2 最新记忆分析结果做一次深度探索：",
        "1. 找出最值得继续推进的 3 个高 ROI 行动，并说明证据、收益和风险。",
        "2. 找出最应该暂缓或降权的 3 个低价值循环，并给出停止条件。",
        "3. 判断哪些内容应该进入 ChatGPT personalization、Codex AGENTS.md 或 other agent handoff。",
        "4. 输出中文，先给结论，再给证据，不要要求读取 cookies、tokens、secrets 或未授权 raw 数据。",
        "",
        "## Safety",
        "",
        "- User trigger required.",
        "- prefill_only 默认只填入，不静默发送。",
        "- auto_submit 必须由配置和显式确认共同开启。",
        "- No silent send.",
        "- No cookie/token/secret export.",
        "- No raw mutation.",
        "- No proposal apply execution.",
    ])
    return sanitize_prompt(prompt)


def load_config(database_dir: Path) -> dict[str, Any]:
    config = read_json(database_dir / CONFIG_PATH)
    if config:
        return config
    return {
        "schema_version": CONTRACT_VERSION,
        "default_mode": "prefill_only",
        "allowed_modes": ["prefill_only", "auto_submit"],
        "chatgpt_base_url": "https://chatgpt.com/",
        "max_prefill_chars": 6000,
        "auto_submit_enabled": False,
        "failure_explanations_zh": {
            "auto_submit_not_enabled": "auto_submit 未开启：S12 P3 默认只允许 prefill_only，需要配置和显式确认后才可发送。",
            "open_failed": "无法自动打开 ChatGPT，请复制机器可复制文本后手动粘贴。",
        },
    }


def equivalent_without_generated_at(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_copy = dict(left)
    right_copy = dict(right)
    left_copy.pop("generated_at", None)
    right_copy.pop("generated_at", None)
    return left_copy == right_copy


def write_text_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8", errors="ignore") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    existing = read_json(path)
    if existing and equivalent_without_generated_at(payload, existing):
        payload["generated_at"] = str(existing.get("generated_at") or payload["generated_at"])
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return write_text_if_changed(path, text)


def build_launch_url(config: dict[str, Any], prompt_text: str) -> str:
    max_prefill_chars = int(config.get("max_prefill_chars") or 6000)
    base_url = str(config.get("chatgpt_base_url") or "https://chatgpt.com/")
    query = urlencode({"q": prompt_text[:max_prefill_chars]})
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{query}"


def build_payload(database_dir: Path, mode: str) -> tuple[dict[str, Any], str, list[str]]:
    config = load_config(database_dir)
    prompt_text, secret_findings = build_prompt_text(database_dir)
    launch_url = build_launch_url(config, prompt_text)
    freshness = source_report_freshness(database_dir)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "contract_version": CONTRACT_VERSION,
        "generated_at": now_utc(),
        "mode": mode,
        "default_mode": "prefill_only",
        "allowed_modes": ["prefill_only", "auto_submit"],
        "chatgpt_base_url": str(config.get("chatgpt_base_url") or "https://chatgpt.com/"),
        "launch_url": launch_url,
        "source_reports": SOURCE_REPORTS,
        "source_report_freshness": freshness,
        "prompt_payload": {
            "human_explanation_zh": "用户触发后，把最新记忆分析报告和深度探索提示预填入 ChatGPT。",
            "machine_copyable_text": prompt_text,
            "prompt_path": PROMPT_OUTPUT.as_posix(),
        },
        "safety": {
            "user_trigger_required": True,
            "sends_to_chatgpt": False,
            "no_silent_send": True,
            "no_cookie_token_secret_export": True,
            "raw_mutation": False,
            "proposal_apply_execution": False,
            "auto_submit_requires_explicit_config": True,
        },
        "failure_explanation_zh": {
            "auto_submit_not_enabled": config.get("failure_explanations_zh", {}).get(
                "auto_submit_not_enabled",
                "auto_submit 未开启：S12 P3 默认只允许 prefill_only，需要配置和显式确认后才可发送。",
            ),
            "open_failed": config.get("failure_explanations_zh", {}).get(
                "open_failed",
                "无法自动打开 ChatGPT，请复制机器可复制文本后手动粘贴。",
            ),
        },
        "secret_sanitize_findings": secret_findings,
        "outputs": [PROMPT_OUTPUT.as_posix(), MACHINE_OUTPUT.as_posix()],
    }
    return payload, prompt_text, secret_findings


def dry_run_contract(database_dir: Path, mode: str) -> dict[str, Any]:
    return {
        "status": "PASS",
        "command": "chatgpt-deep-explore",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "contract_version": CONTRACT_VERSION,
        "dry_run": True,
        "mode": mode,
        "writes_files": False,
        "opens_browser": False,
        "sends_to_chatgpt": False,
        "source_reports": SOURCE_REPORTS,
        "output_contract": {
            "prompt": PROMPT_OUTPUT.as_posix(),
            "machine": MACHINE_OUTPUT.as_posix(),
            "chatgpt_launch_url": "https://chatgpt.com/?q=<encoded_prompt>",
        },
        "boundary": {
            "user_trigger_required": True,
            "default_mode": "prefill_only",
            "allowed_modes": ["prefill_only", "auto_submit"],
            "no_silent_send": True,
            "no_cookie_token_secret_export": True,
            "raw_mutation": False,
            "proposal_apply_execution": False,
            "auto_submit_requires_explicit_config": True,
        },
        "config": (database_dir / CONFIG_PATH).as_posix(),
    }


def run(args: argparse.Namespace) -> int:
    database_dir = args.database_dir.resolve()
    if args.mode == "auto_submit" and not args.confirm_auto_submit:
        config = load_config(database_dir)
        result = {
            "status": "FAIL_CLOSED",
            "command": "chatgpt-deep-explore",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "contract_version": CONTRACT_VERSION,
            "mode": "auto_submit",
            "sends_to_chatgpt": False,
            "failure_explanation_zh": config.get("failure_explanations_zh", {}).get(
                "auto_submit_not_enabled",
                "auto_submit 未开启：S12 P3 默认只允许 prefill_only，需要配置和显式确认后才可发送。",
            ),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    if args.dry_run:
        print(json.dumps(dry_run_contract(database_dir, args.mode), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    payload, prompt_text, _secret_findings = build_payload(database_dir, args.mode)
    prompt_changed = write_text_if_changed(database_dir / PROMPT_OUTPUT, prompt_text + "\n")
    machine_changed = write_json_if_changed(database_dir / MACHINE_OUTPUT, payload)
    opened = False
    if args.open:
        opened = bool(webbrowser.open(payload["launch_url"]))
        if not opened:
            payload["status"] = "FAIL_CLOSED"
            payload["failure_explanation_zh"]["open_result"] = payload["failure_explanation_zh"]["open_failed"]
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
    result = {
        "status": "PASS",
        "command": "chatgpt-deep-explore",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "contract_version": CONTRACT_VERSION,
        "mode": args.mode,
        "dry_run": False,
        "writes_files": True,
        "prompt_changed": prompt_changed,
        "machine_changed": machine_changed,
        "opens_browser": bool(args.open),
        "opened_chatgpt": opened,
        "sends_to_chatgpt": False,
        "launch_url": payload["launch_url"],
        "outputs": payload["outputs"],
        "boundary": payload["safety"],
        "failure_explanation_zh": payload["failure_explanation_zh"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Memory Atlas S12 P3 ChatGPT deep exploration prompt.")
    parser.add_argument("--database-dir", type=Path, default=Path.cwd())
    parser.add_argument("--mode", choices=["prefill_only", "auto_submit"], default="prefill_only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--confirm-auto-submit", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
