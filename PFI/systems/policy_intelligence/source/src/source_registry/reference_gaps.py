from __future__ import annotations

import json
from collections import Counter
from typing import Any, Mapping

from .interpretation import has_subject_relevance, is_reference_item


GAP_ACTION_LABELS = {
    "provide_search_api_key": "补充搜索 API key",
    "provide_platform_auth": "提供本地平台授权文件",
    "implement_platform_parser": "接入平台解析器",
    "refine_public_site_search": "优化公开站内搜索",
    "review_candidate_url": "人工复核候选链接",
    "retry_request": "重试请求或检查网络",
    "improve_relevance_filter": "优化相关性过滤",
    "review_source": "复核来源配置",
}


GAP_TYPE_LABELS = {
    "missing_api_key": "搜索 API key 缺口",
    "platform_auth_missing": "平台授权缺口",
    "platform_parser_pending": "平台解析器待接入",
    "search_landing": "仅搜索入口",
    "public_site_no_result": "公开站内搜索无结果",
    "public_article_blocked": "公开网页正文受限",
    "public_article_failed": "公开网页抓取失败",
    "public_article_too_short": "公开网页摘录过短",
    "request_failed": "请求失败",
    "low_relevance_candidate": "相关性不足",
    "subject_mismatch": "主题不匹配",
    "other_unverified_lead": "其他未验证线索",
}


def external_reference_gaps_for_items(items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for item in items:
        gap = external_reference_gap_for_item(item)
        if gap:
            gaps.append(gap)
    return gaps


def external_reference_gap_for_item(item: Mapping[str, Any]) -> dict[str, Any] | None:
    if is_reference_item(item):
        return None
    gap_type, required_action, priority_score = _classify_gap(item)
    return {
        "run_id": str(item.get("run_id") or ""),
        "document_id": item.get("document_id"),
        "interpretation_source_id": item.get("interpretation_source_id"),
        "platform": item.get("platform") or "unknown",
        "gap_type": gap_type,
        "title": item.get("title") or "未命名外部参考缺口",
        "url": item.get("url") or "",
        "query": item.get("query") or "",
        "evidence_status": item.get("evidence_status") or "",
        "required_action": required_action,
        "priority_score": priority_score,
        "raw_metadata": _sanitized_metadata(item),
    }


def external_reference_gap_summary_for_items(items: list[Mapping[str, Any]]) -> dict[str, Any]:
    gaps = external_reference_gaps_for_items(items)
    by_type = Counter(gap["gap_type"] for gap in gaps)
    by_action = Counter(gap["required_action"] for gap in gaps)
    return {
        "pending_count": len(gaps),
        "by_type": dict(by_type),
        "by_action": dict(by_action),
        "preview": sorted(gaps, key=lambda gap: int(gap.get("priority_score") or 0), reverse=True)[:5],
    }


def gap_type_label(gap_type: str) -> str:
    return GAP_TYPE_LABELS.get(gap_type, gap_type)


def gap_action_label(action: str) -> str:
    return GAP_ACTION_LABELS.get(action, action)


def _classify_gap(item: Mapping[str, Any]) -> tuple[str, str, int]:
    status = str(item.get("evidence_status") or "")
    raw_metadata = _metadata_mapping(item)
    article_status = str(raw_metadata.get("article_fetch_status") or "")
    relevance = int(item.get("relevance_score") or 0)
    if status.startswith("missing_api_key") or status == "missing_google_cse_id":
        return "missing_api_key", "provide_search_api_key", 95
    if "未配置授权文件" in status or "授权文件不存在" in status:
        return "platform_auth_missing", "provide_platform_auth", 90
    if "待接入平台解析器" in status:
        return "platform_parser_pending", "implement_platform_parser", 85
    if not has_subject_relevance(
        str(item.get("title") or ""),
        str(item.get("content_excerpt") or item.get("summary") or ""),
        str(item.get("query") or ""),
    ):
        return "subject_mismatch", "review_candidate_url", 70
    if "公开 API 未返回结果" in status or "未返回结果" in status:
        return "public_site_no_result", "refine_public_site_search", 72
    if article_status.startswith("article_fetch_blocked") or "正文受限" in status:
        return "public_article_blocked", "review_candidate_url", 65
    if article_status.startswith("article_fetch_failed") or status.startswith("request_failed"):
        return "public_article_failed", "retry_request", 62
    if article_status == "article_excerpt_too_short":
        return "public_article_too_short", "review_candidate_url", 68
    if "入口" in status:
        return "search_landing", "review_candidate_url", 55
    if relevance and relevance < 50:
        return "low_relevance_candidate", "improve_relevance_filter", 45
    return "other_unverified_lead", "review_source", 40


def _sanitized_metadata(item: Mapping[str, Any]) -> dict[str, Any]:
    raw = _metadata_mapping(item)
    allowed = {
        "article_fetch_status",
        "public_site_search",
        "public_site_result",
        "public_search_html",
        "public_search_result",
        "search_platform",
        "detail_enriched",
        "author_profile_enriched",
        "subtitle_excerpt",
        "comment_excerpt",
        "danmaku_excerpt",
        "provider",
        "result_count",
        "bvid",
        "aid",
        "author_mid",
        "typename",
        "tag",
    }
    sanitized = {key: raw.get(key) for key in allowed if key in raw}
    auth = raw.get("platform_auth")
    if isinstance(auth, Mapping):
        sanitized["platform_auth"] = {
            "platform": auth.get("platform"),
            "configured": bool(auth.get("configured")),
            "available": bool(auth.get("available")),
            "status": auth.get("status"),
            "auth_method": auth.get("auth_method"),
            "cookie_file_configured": bool(auth.get("cookie_file_configured")),
            "session_file_configured": bool(auth.get("session_file_configured")),
            "allowed_capabilities": auth.get("allowed_capabilities") or [],
        }
    return sanitized


def _metadata_mapping(item: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = item.get("raw_metadata")
    if isinstance(raw, Mapping):
        return raw
    raw_json = item.get("raw_metadata_json")
    if isinstance(raw_json, str) and raw_json.strip():
        try:
            decoded = json.loads(raw_json)
        except json.JSONDecodeError:
            return {}
        return decoded if isinstance(decoded, Mapping) else {}
    return {}
