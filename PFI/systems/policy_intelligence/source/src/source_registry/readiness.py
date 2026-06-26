from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .content_db import external_reference_gap_summary
from .platform_auth import DEFAULT_CAPABILITIES, platform_auth_state
from .web_search import search_provider_status


CORE_PLATFORMS = [
    "bilibili",
    "douyin",
    "kuaishou",
    "weibo",
    "zhihu",
    "wechat",
    "xiaohongshu",
    "toutiao",
]

CHINESE_SEARCH_ENTRIES = ["baidu", "sogou", "360"]


def build_readiness_status(
    *,
    content_conn=None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    interpretation_source_file: str | Path | None = "config/interpretation_sources.json",
) -> dict[str, Any]:
    search_api = search_provider_status(search_secrets_file)
    platform_auth = [_platform_status(platform, platform_auth_file) for platform in CORE_PLATFORMS]
    chinese_entries = _chinese_search_entry_status(interpretation_source_file)
    gap_summary = external_reference_gap_summary(content_conn) if content_conn is not None else {}
    ready_search = sum(1 for item in search_api if item.get("ready"))
    ready_platforms = sum(1 for item in platform_auth if item.get("available"))
    configured_platforms = sum(1 for item in platform_auth if item.get("configured"))
    return {
        "overall_status": _overall_status(search_api, platform_auth, gap_summary),
        "search_api": {
            "ready_count": ready_search,
            "providers": search_api,
        },
        "chinese_search_entries": chinese_entries,
        "platform_auth": {
            "configured_count": configured_platforms,
            "available_count": ready_platforms,
            "platforms": platform_auth,
        },
        "external_reference_gaps": gap_summary,
        "next_actions": _next_actions(search_api, platform_auth, gap_summary),
    }


def _platform_status(platform: str, platform_auth_file: str | Path | None) -> dict[str, Any]:
    state = platform_auth_state(platform, platform_auth_file)
    return {
        "platform": platform,
        "configured": state.configured,
        "available": state.available,
        "status": state.status,
        "auth_method": state.auth_method,
        "cookie_file_configured": bool(state.cookie_file),
        "session_file_configured": bool(state.session_file),
        "allowed_capabilities": list(state.allowed_capabilities or DEFAULT_CAPABILITIES.get(platform, [])),
        "note": state.note,
    }


def _chinese_search_entry_status(path: str | Path | None) -> dict[str, Any]:
    entries = {name: False for name in CHINESE_SEARCH_ENTRIES}
    if not path:
        return {"configured_count": 0, "entries": entries}
    config_path = Path(path)
    if not config_path.exists():
        return {"configured_count": 0, "entries": entries}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"configured_count": 0, "entries": entries}
    raw_sources = payload.get("sources", payload if isinstance(payload, list) else [])
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        platform = str(source.get("platform") or "").lower()
        name = str(source.get("name") or "").lower()
        source_id = str(source.get("interpretation_source_id") or "").lower()
        for entry in list(entries):
            if entry in platform or entry in name or entry in source_id:
                entries[entry] = bool(source.get("enabled", True))
    return {"configured_count": sum(1 for ready in entries.values() if ready), "entries": entries}


def _overall_status(
    search_api: list[dict[str, Any]],
    platform_auth: list[dict[str, Any]],
    gap_summary: dict[str, Any],
) -> str:
    if any(item.get("ready") for item in search_api) and any(item.get("available") for item in platform_auth):
        return "ready_with_partial_coverage"
    if any(item.get("ready") for item in search_api) or any(item.get("available") for item in platform_auth):
        return "partial"
    if int(gap_summary.get("pending_count", 0) or 0) > 0:
        return "needs_configuration"
    return "not_configured"


def _next_actions(
    search_api: list[dict[str, Any]],
    platform_auth: list[dict[str, Any]],
    gap_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    missing_search = [item["provider"] for item in search_api if not item.get("ready")]
    if missing_search:
        actions.append(
            {
                "action": "provide_search_api_key",
                "label": "补充搜索 API key",
                "targets": missing_search,
                "priority": 95,
            }
        )
    missing_auth = [item["platform"] for item in platform_auth if not item.get("available")]
    if missing_auth:
        actions.append(
            {
                "action": "provide_platform_auth",
                "label": "提供本地平台授权文件",
                "targets": missing_auth,
                "priority": 90,
            }
        )
    by_action = gap_summary.get("by_action") or {}
    for action, count in sorted(by_action.items(), key=lambda item: int(item[1] or 0), reverse=True):
        if action in {"provide_search_api_key", "provide_platform_auth"}:
            continue
        actions.append(
            {
                "action": action,
                "label": action,
                "targets": [],
                "count": int(count or 0),
                "priority": 70,
            }
        )
    return sorted(actions, key=lambda item: int(item.get("priority") or 0), reverse=True)
