from __future__ import annotations

import html
import json
import math
import os
import re
import ssl
import time
from pathlib import Path
from html.parser import HTMLParser
from typing import Any, Mapping
from urllib.parse import parse_qsl, quote, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from .content_db import (
    list_interpretation_sources,
    upsert_interpretation_item,
    upsert_interpretation_source,
)
from .platform_auth import bilibili_cookie_file_from_auth, platform_auth_state
from .platform_page_parser import extract_platform_page_metadata
from .platform_text_parser import (
    comment_excerpt_from_replies,
    danmaku_excerpt_from_xml,
    subtitle_excerpt_from_payload,
)
from .web_article import extract_article_text, fetch_public_article
from .web_search import collect_search_results


def seed_interpretation_sources(conn, path: str | Path) -> int:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    sources = payload.get("sources", payload if isinstance(payload, list) else [])
    count = 0
    for source in sources:
        upsert_interpretation_source(conn, source)
        count += 1
    return count


def collect_interpretation_items(
    conn,
    run_id: str,
    documents: list[Mapping[str, Any]],
    max_documents: int = 10,
    min_reference_items: int = 5,
    fetch_online: bool = False,
    allow_insecure_tls: bool = False,
    bilibili_cookie_file: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    fetch_search_result_pages: bool = False,
    request_timeout: int = 20,
    request_retries: int = 1,
    request_delay_seconds: float = 0.0,
) -> list[dict[str, Any]]:
    sources = list_interpretation_sources(conn, enabled=True)
    items: list[dict[str, Any]] = []
    scan_limit = min(len(documents), max(max_documents, min_reference_items))
    for document in documents[:scan_limit]:
        query = _query_for_document(document)
        for source in sources:
            collected = []
            auth_state = platform_auth_state(
                str(source.get("platform") or ""),
                platform_auth_file,
                bilibili_cookie_file if source.get("platform") == "bilibili" else None,
            )
            if fetch_online and source.get("collector_type") == "bilibili_api":
                collected = _collect_bilibili_items(
                    source=source,
                    document=document,
                    run_id=run_id,
                    query=query,
                    allow_insecure_tls=allow_insecure_tls,
                    cookie_file=bilibili_cookie_file_from_auth(
                        platform_auth_file,
                        bilibili_cookie_file,
                    ),
                    timeout=request_timeout,
                    retries=request_retries,
                )
            elif fetch_online and str(source.get("collector_type") or "").startswith("search_api_"):
                collected = _collect_search_api_items(
                    source=source,
                    document=document,
                    run_id=run_id,
                    query=query,
                    allow_insecure_tls=allow_insecure_tls,
                    secrets_file=search_secrets_file,
                    fetch_result_pages=fetch_search_result_pages,
                    timeout=request_timeout,
                    retries=request_retries,
                )
            elif fetch_online and source.get("collector_type") == "public_site_search":
                collected = _collect_public_site_search_items(
                    source=source,
                    document=document,
                    run_id=run_id,
                    query=query,
                    allow_insecure_tls=allow_insecure_tls,
                    timeout=request_timeout,
                    retries=request_retries,
                )
            elif fetch_online and source.get("collector_type") == "public_search_html":
                collected = _collect_public_search_html_items(
                    source=source,
                    document=document,
                    run_id=run_id,
                    query=query,
                    allow_insecure_tls=allow_insecure_tls,
                    timeout=request_timeout,
                    retries=request_retries,
                )
            elif fetch_online and source.get("collector_type") == "authorized_public_search":
                collected = _collect_authorized_public_search_items(
                    source=source,
                    document=document,
                    run_id=run_id,
                    query=query,
                    auth_state=auth_state,
                    allow_insecure_tls=allow_insecure_tls,
                    timeout=request_timeout,
                    retries=request_retries,
                )
            elif fetch_online and source.get("collector_type") == "local_related_documents":
                collected = _collect_local_related_document_items(
                    conn=conn,
                    source=source,
                    document=document,
                    run_id=run_id,
                    query=query,
                )
            elif fetch_online and source.get("collector_type") == "local_historical_references":
                collected = _collect_local_historical_reference_items(
                    conn=conn,
                    source=source,
                    document=document,
                    run_id=run_id,
                    query=query,
                )
            if not collected:
                collected = [
                    _search_landing_item(
                        source,
                        document,
                        run_id,
                        query,
                        fetch_online,
                        auth_state=auth_state,
                    )
                ]
            for item in collected:
                upsert_interpretation_item(conn, item)
                items.append(item)
            if fetch_online and request_delay_seconds > 0:
                time.sleep(request_delay_seconds)
    return items


def interpretation_context_by_document(
    items: list[Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for item in items:
        document_id = str(item.get("document_id") or "")
        if document_id:
            grouped.setdefault(document_id, []).append(item)
    for values in grouped.values():
        values.sort(
            key=lambda item: (
                int(item.get("relevance_score") or 0),
                int(item.get("view_count") or 0),
            ),
            reverse=True,
        )
    return grouped


def reference_items(items: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    references: list[Mapping[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if not is_reference_item(item):
            continue
        key = _reference_dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)
        references.append(item)
    return references


def count_reference_items(items: list[Mapping[str, Any]]) -> int:
    return len(reference_items(items))


def reference_platforms(items: list[Mapping[str, Any]]) -> list[str]:
    platforms: list[str] = []
    for item in reference_items(items):
        platform = str(item.get("platform") or "未知平台")
        if platform not in platforms:
            platforms.append(platform)
    return platforms


def _reference_dedupe_key(item: Mapping[str, Any]) -> tuple[str, str]:
    url = str(item.get("url") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        normalized_url = parsed._replace(fragment="", query="").geturl().rstrip("/")
    else:
        normalized_url = url.rstrip("/")
    title = re.sub(r"\s+", "", _strip_markup(str(item.get("title") or "")))
    return (normalized_url, title)


def is_reference_item(item: Mapping[str, Any]) -> bool:
    title = _strip_markup(str(item.get("title") or ""))
    url = str(item.get("url") or "").strip()
    item_type = str(item.get("item_type") or "")
    status = str(item.get("evidence_status") or "")
    excerpt = _strip_markup(str(item.get("content_excerpt") or item.get("summary") or ""))
    raw_metadata = _metadata_for_item(item)
    article_status = str(raw_metadata.get("article_fetch_status") or "")
    relevance = int(item.get("relevance_score") or 0)
    if not title or not url:
        return False
    if "需登录" in status or "入口" in status or "未返回结果" in status or "正文受限" in status:
        return False
    if "待接入平台解析器" in status or "授权文件不存在" in status:
        return False
    if article_status and article_status != "article_excerpt_extracted":
        return False
    if item_type == "video" and _looks_like_low_value_video(title, excerpt):
        return False
    if item_type in {"video", "search_result"} and relevance and relevance < 60:
        return False
    if item_type in {"video", "search_result"} and not _has_policy_research_signal(
        title, excerpt, str(item.get("query") or "")
    ):
        return False
    if item_type in {"video", "search_result"} and not has_subject_relevance(
        title, excerpt, str(item.get("query") or "")
    ):
        return False
    if item_type in {"article", "news", "research"}:
        if relevance and relevance < 58:
            return False
        if _looks_like_generic_policy_index(title, url):
            return False
        if not _has_policy_research_signal(title, excerpt, str(item.get("query") or "")):
            return False
        if not has_subject_relevance(title, excerpt, str(item.get("query") or "")):
            return False
        return True
    if item_type in {"video", "search_result"}:
        return True
    return len(excerpt) >= 80


def research_digest(items: list[Mapping[str, Any]], limit: int = 5) -> list[str]:
    digest: list[str] = []
    ordered = reference_items(items) + [item for item in items if not is_reference_item(item)]
    for item in ordered[:limit]:
        platform = str(item.get("platform") or "外部来源")
        title = _strip_markup(str(item.get("title") or "未命名解读资料"))
        author = str(item.get("author_name") or "").strip()
        views = _format_count(item.get("view_count"))
        excerpt = _strip_markup(str(item.get("content_excerpt") or item.get("summary") or ""))
        meta_parts = [platform]
        if author:
            meta_parts.append(f"作者/UP主：{author}")
        if views:
            meta_parts.append(f"播放/阅读：{views}")
        if item.get("relevance_score"):
            meta_parts.append(f"相关度：{item.get('relevance_score')}")
        if is_reference_item(item):
            meta_parts.append("计入参考")
        line = f"{'，'.join(meta_parts)}｜《{title}》"
        if excerpt:
            line += f"｜{excerpt[:160]}"
        digest.append(line)
    return digest


def _has_policy_research_signal(title: str, excerpt: str, query: str) -> bool:
    text = f"{title} {excerpt}"
    policy_terms = (
        "政策",
        "解读",
        "规划",
        "文件",
        "条例",
        "办法",
        "通知",
        "意见",
        "规定",
        "细则",
        "执法",
        "监管",
        "发布",
        "部门",
        "新闻发布会",
    )
    if any(term in text for term in policy_terms):
        return True
    tokens = _query_tokens(query)
    return bool(tokens and any(token in title for token in tokens))


def has_subject_relevance(title: str, excerpt: str, query: str) -> bool:
    terms = _subject_query_terms(query)
    if not terms:
        return True
    text = _strip_markup(f"{title} {excerpt}")
    compact_text = re.sub(r"\s+", "", text)
    matched = [term for term in terms if term in text or term in compact_text]
    if not matched:
        return False
    return any(not _is_weak_subject_term(term) for term in matched) or len(matched) >= 2


def interpretation_health_stats(items: list[Mapping[str, Any]]) -> dict[str, int]:
    stats = {
        "interpretation_attempts": len(items),
        "interpretation_reference_successes": 0,
        "interpretation_leads": 0,
        "interpretation_missing_api_keys": 0,
        "interpretation_auth_required": 0,
        "interpretation_failed_requests": 0,
        "interpretation_search_landings": 0,
        "interpretation_auth_configured": 0,
        "interpretation_auth_missing": 0,
        "interpretation_auth_parser_pending": 0,
        "article_pages_fetched": 0,
        "article_excerpts_extracted": 0,
        "article_pages_blocked": 0,
        "article_pages_failed": 0,
        "public_site_searches": 0,
        "public_site_results": 0,
        "public_search_html_searches": 0,
        "public_search_html_results": 0,
        "authorized_public_searches": 0,
        "authorized_public_results": 0,
        "authorized_public_blocked": 0,
        "video_details_enriched": 0,
        "video_author_profiles_enriched": 0,
        "video_subtitles_extracted": 0,
        "video_comments_extracted": 0,
        "video_danmaku_extracted": 0,
    }
    for item in items:
        status = str(item.get("evidence_status") or "")
        raw_metadata = _metadata_for_item(item)
        if is_reference_item(item):
            stats["interpretation_reference_successes"] += 1
        else:
            stats["interpretation_leads"] += 1
        if status.startswith("missing_api_key") or status == "missing_google_cse_id":
            stats["interpretation_missing_api_keys"] += 1
        if "需登录" in status or "验证码" in status or "反爬" in status:
            stats["interpretation_auth_required"] += 1
        if "未配置授权文件" in status:
            stats["interpretation_auth_missing"] += 1
        if "授权文件已配置" in status or "授权文件可用" in status:
            stats["interpretation_auth_configured"] += 1
        if "待接入平台解析器" in status:
            stats["interpretation_auth_parser_pending"] += 1
        if status.startswith("request_failed") or "未返回结果" in status:
            stats["interpretation_failed_requests"] += 1
        if "入口" in status:
            stats["interpretation_search_landings"] += 1
        if raw_metadata.get("detail_enriched"):
            stats["video_details_enriched"] += 1
        if raw_metadata.get("author_profile_enriched"):
            stats["video_author_profiles_enriched"] += 1
        if raw_metadata.get("subtitle_excerpt"):
            stats["video_subtitles_extracted"] += 1
        if raw_metadata.get("comment_excerpt"):
            stats["video_comments_extracted"] += 1
        if raw_metadata.get("danmaku_excerpt"):
            stats["video_danmaku_extracted"] += 1
        article_status = str(raw_metadata.get("article_fetch_status") or "")
        if raw_metadata.get("public_site_search"):
            stats["public_site_searches"] += 1
        if raw_metadata.get("public_site_result"):
            stats["public_site_results"] += 1
        if raw_metadata.get("public_search_html"):
            stats["public_search_html_searches"] += 1
        if raw_metadata.get("public_search_result"):
            stats["public_search_html_results"] += 1
        if raw_metadata.get("authorized_public_search"):
            stats["authorized_public_searches"] += 1
        if raw_metadata.get("authorized_public_result"):
            stats["authorized_public_results"] += 1
        if str(status).startswith("授权搜索受限"):
            stats["authorized_public_blocked"] += 1
        if article_status:
            stats["article_pages_fetched"] += 1
        if article_status == "article_excerpt_extracted":
            stats["article_excerpts_extracted"] += 1
        if article_status.startswith("article_fetch_blocked"):
            stats["article_pages_blocked"] += 1
        if article_status.startswith("article_fetch_failed"):
            stats["article_pages_failed"] += 1
    return stats


def _metadata_for_item(item: Mapping[str, Any]) -> Mapping[str, Any]:
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


def _looks_like_exam_or_recruiting_noise(title: str, excerpt: str) -> bool:
    text = f"{title} {excerpt}"
    noise_terms = ("备考", "刷题", "招聘", "笔试", "公考", "事业单位", "考证", "进面", "讲义")
    policy_terms = ("政策解读", "产业影响", "新闻发布会", "主管部门", "权威资讯")
    return any(term in text for term in noise_terms) and not any(term in text for term in policy_terms)


def _looks_like_low_value_video(title: str, excerpt: str) -> bool:
    text = f"{title} {excerpt}"
    if _looks_like_exam_or_recruiting_noise(title, excerpt):
        return True
    entertainment_terms = (
        "我的世界",
        "MC",
        "mod",
        "MOD",
        "模组",
        "服务器",
        "单机游戏",
        "游戏攻略",
        "高考作文",
        "高中作文",
        "广州一模",
        "满分作文",
    )
    policy_context_terms = (
        "政策解读",
        "专项规划",
        "耕地保护",
        "永久基本农田",
        "粮食安全",
        "国土空间",
        "自然资源",
        "乡村振兴",
        "一号文件",
        "主管部门",
    )
    if any(term in text for term in entertainment_terms) and not any(term in text for term in policy_context_terms):
        return True
    if any(term in text for term in ("我的世界", "单机游戏", "模组", "MOD")):
        return True
    trading_terms = (
        "明天再看",
        "不动",
        "抄底",
        "涨停",
        "跌停",
        "短线",
        "盘中",
        "复盘",
        "个股",
        "ETF",
        "etf",
        "白酒",
        "消费",
        "牛市",
        "熊市",
    )
    policy_terms = (
        "政策解读",
        "指导意见",
        "监管",
        "条例",
        "办法",
        "规定",
        "实施细则",
        "新闻发布会",
        "主管部门",
        "国务院",
        "证监会",
        "金融监管",
    )
    return any(term in text for term in trading_terms) and not any(term in text for term in policy_terms)


def _looks_like_generic_policy_index(title: str, url: str) -> bool:
    normalized_title = re.sub(r"\s+", "", _strip_markup(title)).strip("｜|-_")
    generic_titles = {
        "政策",
        "政策文件",
        "政策解读",
        "最新政策",
        "最新文件",
        "国务院文件",
        "国务院公报",
        "省政府公报",
        "政府公报",
        "公报",
        "文件库",
        "搜索结果",
        "站内搜索",
        "首页",
        "栏目首页",
        "粤企政策通",
    }
    if normalized_title in generic_titles:
        return True
    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")
    index_paths = (
        "/zhengce",
        "/zhengce/index.htm",
        "/zhengce/index.html",
        "/policy",
        "/policy/index.htm",
        "/policy/index.html",
        "/search",
        "/search/index.htm",
        "/search/index.html",
    )
    return path in index_paths and len(normalized_title) <= 8


def _query_for_document(document: Mapping[str, Any]) -> str:
    title = str(document.get("title") or "")
    source_name = str(document.get("source_name") or "").strip()
    title = _clean_query_title(title)
    if source_name:
        title = title.replace(source_name, " ")
    title = _strip_consultation_noise(title)
    for token in ("国务院办公厅", "国务院", "关于", "印发", "通知"):
        title = title.replace(token, " ")
    compact = " ".join(title.split())
    compact = re.sub(r"的$", "", compact)
    if not compact:
        compact = str(document.get("source_name") or "政策")
    if "政策解读" in compact or compact.endswith("解读"):
        return compact
    return f"{compact} 政策解读"


def _clean_query_title(title: str) -> str:
    value = html.unescape(title or "")
    value = re.sub(r"__?中国政府网$", "", value)
    value = re.sub(r"[_-]+中国政府网$", "", value)
    value = re.sub(r"[_-]+[^_-]{2,18}人民政府门户网站$", "", value)
    value = re.sub(r"[_-]+(政策解读|文件解读|图解|全文|原文)$", "", value)
    value = re.sub(r"\s*(中国政府网|[^\s_\-]{2,18}人民政府门户网站)$", "", value)
    value = re.sub(r"[\t\r\n]+", " ", value)
    value = value.replace("_", " ").replace("-", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" ｜|·")


def _strip_consultation_noise(title: str) -> str:
    value = title
    formal_title = re.search(r"公开征求《([^》]{4,160})》[（(]?征求意见稿[）)]?意见?", value)
    if formal_title:
        return formal_title.group(1).strip()
    value = re.sub(r"关于公开征求", " ", value)
    value = re.sub(r"公开征求", " ", value)
    value = re.sub(r"《([^》]{4,120})》[（(]?征求意见稿[）)]?意见?", r"\1", value)
    value = re.sub(r"[（(]?征求意见稿[）)]?意见?", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _search_landing_item(
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
    attempted_online: bool,
    auth_state=None,
) -> dict[str, Any]:
    url = source["url_template"].format(query=quote(query), raw_query=query)
    status = "公开搜索入口"
    if source.get("auth_required"):
        if auth_state and auth_state.available:
            status = "授权文件可用；待接入平台解析器"
        elif auth_state and auth_state.configured:
            status = "需登录/反爬验证；授权文件不存在或不可读"
        else:
            status = "需登录/反爬验证；未配置授权文件"
    if attempted_online and source.get("collector_type") == "bilibili_api":
        status = "公开 API 未返回结果，保留搜索入口"
        if auth_state and auth_state.available:
            status = "授权文件已配置；公开 API 未返回结果，保留搜索入口"
    metadata = {}
    if auth_state:
        metadata["platform_auth"] = auth_state.as_metadata()
    return {
        "run_id": run_id,
        "document_id": document["document_id"],
        "interpretation_source_id": source["interpretation_source_id"],
        "platform": source["platform"],
        "item_type": "search_entry",
        "title": f"{source['name']}：{query}",
        "url": url,
        "query": query,
        "evidence_status": status,
        "summary": _summary_for_source(source, document),
        "relevance_score": 30,
        "raw_metadata": metadata,
    }


def _collect_bilibili_items(
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
    allow_insecure_tls: bool,
    cookie_file: str | Path | None,
    timeout: int,
    retries: int,
) -> list[dict[str, Any]]:
    api_template = source.get("api_url_template")
    if not api_template:
        return []
    api_url = api_template.format(query=quote(query), raw_query=query)
    payload = _fetch_json(api_url, allow_insecure_tls, cookie_file, timeout, retries)
    if not payload or payload.get("code") != 0:
        return []
    results = (payload.get("data") or {}).get("result") or []
    max_results = max(1, int(source.get("max_results") or 3))
    items: list[dict[str, Any]] = []
    for raw in results:
        if raw.get("type") != "video":
            continue
        title = _strip_markup(str(raw.get("title") or ""))
        if not title:
            continue
        bvid = raw.get("bvid")
        url = f"https://www.bilibili.com/video/{bvid}/" if bvid else str(raw.get("arcurl") or "")
        if not url:
            continue
        enrichment = _bilibili_video_enrichment(
            raw,
            allow_insecure_tls=allow_insecure_tls,
            cookie_file=cookie_file,
            timeout=timeout,
            retries=retries,
        )
        excerpt = _bilibili_excerpt(raw, enrichment)
        metadata = {
            "bvid": raw.get("bvid"),
            "aid": raw.get("aid"),
            "author_mid": enrichment.get("author_mid") or raw.get("mid"),
            "typename": raw.get("typename"),
            "tag": raw.get("tag"),
            "favorites": raw.get("favorites"),
            "like": raw.get("like"),
            "review": raw.get("review"),
            "danmaku": raw.get("danmaku"),
            "pubdate": raw.get("pubdate"),
            **enrichment,
        }
        evidence_status = "公开视频搜索结果"
        if enrichment.get("subtitle_excerpt"):
            evidence_status = "公开视频搜索结果；字幕已摘录"
        elif enrichment.get("comment_excerpt") or enrichment.get("danmaku_excerpt"):
            evidence_status = "公开视频搜索结果；互动摘录已采集"
        elif enrichment.get("author_profile_enriched"):
            evidence_status = "公开视频搜索结果；作者页已增强"
        elif enrichment.get("detail_enriched"):
            evidence_status = "公开视频搜索结果；详情已增强"
        author_mid = enrichment.get("author_mid") or raw.get("mid")
        author_name = (
            enrichment.get("author_profile_name")
            or enrichment.get("owner_name")
            or _strip_markup(str(raw.get("author") or ""))
        )
        item = {
            "run_id": run_id,
            "document_id": document["document_id"],
            "interpretation_source_id": source["interpretation_source_id"],
            "platform": "bilibili",
            "item_type": "video",
            "title": title,
            "url": url,
            "query": query,
            "evidence_status": evidence_status,
            "summary": _bilibili_summary(raw),
            "author_name": author_name,
            "author_url": f"https://space.bilibili.com/{author_mid}" if author_mid else None,
            "published_at": _timestamp_to_utc(raw.get("pubdate")),
            "duration_seconds": _duration_seconds(str(raw.get("duration") or "")),
            "view_count": _int_or_none(raw.get("play")),
            "engagement_count": _engagement_count(raw),
            "content_excerpt": excerpt,
            "relevance_score": _relevance_score(raw, query),
            "raw_metadata": metadata,
        }
        if is_reference_item(item) or len(items) < max_results:
            items.append(item)
        if len(reference_items(items)) >= max_results:
            break
    return items


def _collect_search_api_items(
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
    allow_insecure_tls: bool,
    secrets_file: str | Path | None,
    fetch_result_pages: bool,
    timeout: int,
    retries: int,
) -> list[dict[str, Any]]:
    collector_type = str(source.get("collector_type") or "")
    provider = collector_type.replace("search_api_", "", 1)
    max_results = max(1, int(source.get("max_results") or 5))
    results, status = collect_search_results(
        provider=provider,
        query=query,
        max_results=max_results,
        timeout=timeout,
        allow_insecure_tls=allow_insecure_tls,
        secrets_file=secrets_file,
        retries=retries,
    )
    if status != "ok":
        return [
            {
                "run_id": run_id,
                "document_id": document["document_id"],
                "interpretation_source_id": source["interpretation_source_id"],
                "platform": source["platform"],
                "item_type": "search_entry",
                "title": f"{source['name']}：{query}",
                "url": source["url_template"].format(query=quote(query), raw_query=query),
                "query": query,
                "evidence_status": status,
                "summary": _summary_for_source(source, document),
                "relevance_score": 15,
                "raw_metadata": {"provider": provider, "status": status},
            }
        ]
    items: list[dict[str, Any]] = []
    for result in results:
        excerpt = _strip_markup(result.snippet)
        article_metadata = {}
        evidence_status = f"{provider}公开搜索结果"
        if fetch_result_pages:
            article = fetch_public_article(
                result.url,
                timeout=timeout,
                allow_insecure_tls=allow_insecure_tls,
                retries=retries,
            )
            article_metadata = {
                "article_fetch_status": article.status,
                "article_content_type": article.content_type,
                "article_fetched_url": article.fetched_url,
                "article_title": article.title,
            }
            if article.status == "article_excerpt_extracted":
                excerpt = article.text
                evidence_status = f"{provider}公开搜索结果；正文已摘录"
            elif article.status.startswith("article_fetch_blocked"):
                evidence_status = f"{provider}公开搜索结果；正文受限"
        items.append(
            {
                "run_id": run_id,
                "document_id": document["document_id"],
                "interpretation_source_id": source["interpretation_source_id"],
                "platform": source["platform"],
                "item_type": "search_result",
                "title": _strip_markup(result.title),
                "url": result.url,
                "query": query,
                "evidence_status": evidence_status,
                "summary": excerpt or _summary_for_source(source, document),
                "author_name": result.source or None,
                "published_at": result.published_at,
                "content_excerpt": excerpt,
                "relevance_score": _text_relevance_score(result.title, excerpt, query),
                "raw_metadata": {
                    "provider": provider,
                    "source": result.source,
                    "raw": result.raw,
                    **article_metadata,
                },
            }
        )
    return items


def _collect_public_site_search_items(
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
    allow_insecure_tls: bool,
    timeout: int,
    retries: int,
) -> list[dict[str, Any]]:
    search_url = source["url_template"].format(query=quote(query), raw_query=query)
    html_text = _fetch_html(search_url, allow_insecure_tls, timeout, retries)
    if not html_text:
        return []
    max_results = max(1, int(source.get("max_results") or 3))
    platform = str(source.get("platform") or "")
    candidates = _public_site_result_links(html_text, search_url, platform, query)
    items: list[dict[str, Any]] = []
    for candidate in candidates[: max_results * 3]:
        article = fetch_public_article(
            candidate["url"],
            timeout=timeout,
            allow_insecure_tls=allow_insecure_tls,
            retries=retries,
        )
        metadata = {
            "public_site_search": True,
            "public_site_result": True,
            "search_url": search_url,
            "article_fetch_status": article.status,
            "article_content_type": article.content_type,
            "article_fetched_url": article.fetched_url,
            "article_title": article.title,
        }
        excerpt = article.text or candidate["text"]
        title = article.title or candidate["text"] or source["name"]
        evidence_status = f"{platform}公开站内搜索结果"
        if article.status == "article_excerpt_extracted":
            evidence_status = f"{platform}公开站内搜索结果；正文已摘录"
        elif article.status.startswith("article_fetch_blocked"):
            evidence_status = f"{platform}公开站内搜索结果；正文受限"
        item = {
            "run_id": run_id,
            "document_id": document["document_id"],
            "interpretation_source_id": source["interpretation_source_id"],
            "platform": platform,
            "item_type": "article",
            "title": _strip_markup(title)[:180] or source["name"],
            "url": article.fetched_url or candidate["url"],
            "query": query,
            "evidence_status": evidence_status,
            "summary": excerpt or _summary_for_source(source, document),
            "author_name": platform or None,
            "content_excerpt": excerpt,
            "relevance_score": _text_relevance_score(title, excerpt, query),
            "raw_metadata": metadata,
        }
        if is_reference_item(item) or len(items) < max_results:
            items.append(item)
        if len(reference_items(items)) >= max_results:
            break
    if items:
        return items
    return [
        {
            "run_id": run_id,
            "document_id": document["document_id"],
            "interpretation_source_id": source["interpretation_source_id"],
            "platform": platform,
            "item_type": "search_entry",
            "title": f"{source['name']}：{query}",
            "url": search_url,
            "query": query,
            "evidence_status": "公开站内搜索未返回可用结果，保留搜索入口",
            "summary": _summary_for_source(source, document),
            "relevance_score": 20,
            "raw_metadata": {"public_site_search": True, "search_url": search_url},
        }
    ]


def _collect_public_search_html_items(
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
    allow_insecure_tls: bool,
    timeout: int,
    retries: int,
) -> list[dict[str, Any]]:
    search_url = source["url_template"].format(query=quote(query), raw_query=query)
    html_text = _fetch_html(search_url, allow_insecure_tls, timeout, retries)
    if not html_text:
        return []
    max_results = max(1, int(source.get("max_results") or 3))
    search_platform = str(source.get("platform") or "")
    candidates = _public_search_result_links(html_text, search_url, query)
    items: list[dict[str, Any]] = []
    for candidate in candidates[: max_results * 4]:
        article = fetch_public_article(
            candidate["url"],
            timeout=timeout,
            allow_insecure_tls=allow_insecure_tls,
            retries=retries,
        )
        resolved_url = article.fetched_url or candidate["url"]
        result_platform = _platform_from_url(resolved_url) or search_platform
        metadata = {
            "public_search_html": True,
            "public_search_result": True,
            "search_platform": search_platform,
            "search_url": search_url,
            "article_fetch_status": article.status,
            "article_content_type": article.content_type,
            "article_fetched_url": article.fetched_url,
            "article_title": article.title,
        }
        excerpt = article.text or candidate["text"]
        title = article.title or candidate["text"] or source["name"]
        evidence_status = f"{search_platform}公开搜索结果"
        if article.status == "article_excerpt_extracted":
            evidence_status = f"{search_platform}公开搜索结果；正文已摘录"
        elif article.status.startswith("article_fetch_blocked"):
            evidence_status = f"{search_platform}公开搜索结果；正文受限"
        item = {
            "run_id": run_id,
            "document_id": document["document_id"],
            "interpretation_source_id": source["interpretation_source_id"],
            "platform": result_platform,
            "item_type": "article",
            "title": _strip_markup(title)[:180] or source["name"],
            "url": resolved_url,
            "query": query,
            "evidence_status": evidence_status,
            "summary": excerpt or _summary_for_source(source, document),
            "author_name": result_platform or None,
            "content_excerpt": excerpt,
            "relevance_score": _text_relevance_score(title, excerpt, query),
            "raw_metadata": metadata,
        }
        items.append(item)
        if len(items) >= max_results:
            break
    if items:
        return items
    return [
        {
            "run_id": run_id,
            "document_id": document["document_id"],
            "interpretation_source_id": source["interpretation_source_id"],
            "platform": search_platform,
            "item_type": "search_entry",
            "title": f"{source['name']}：{query}",
            "url": search_url,
            "query": query,
            "evidence_status": "公开搜索未返回可用结果，保留搜索入口",
            "summary": _summary_for_source(source, document),
            "relevance_score": 20,
            "raw_metadata": {"public_search_html": True, "search_url": search_url},
        }
    ]


def _collect_authorized_public_search_items(
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
    auth_state,
    allow_insecure_tls: bool,
    timeout: int,
    retries: int,
) -> list[dict[str, Any]]:
    platform = str(source.get("platform") or "")
    if not auth_state or not auth_state.available or not auth_state.cookie_file:
        return []
    search_url = source["url_template"].format(query=quote(query), raw_query=query)
    search_html, fetch_status, content_type, fetched_url = _fetch_authorized_html(
        search_url,
        auth_state.cookie_file,
        allow_insecure_tls=allow_insecure_tls,
        timeout=timeout,
        retries=retries,
    )
    auth_metadata = auth_state.as_metadata()
    if fetch_status != "ok":
        return [
            _authorized_search_audit_item(
                source,
                document,
                run_id,
                query,
                search_url,
                platform,
                f"授权搜索请求失败：{fetch_status}",
                {"authorized_public_search": True, "fetch_status": fetch_status, "platform_auth": auth_metadata},
            )
        ]
    blocked_status = _authorized_block_status(
        search_html,
        login_required_markers=auth_state.login_required_markers,
        captcha_markers=auth_state.captcha_markers,
    )
    if blocked_status:
        return [
            _authorized_search_audit_item(
                source,
                document,
                run_id,
                query,
                fetched_url or search_url,
                platform,
                f"授权搜索受限：{blocked_status}",
                {
                    "authorized_public_search": True,
                    "fetch_status": fetch_status,
                    "content_type": content_type,
                    "fetched_url": fetched_url,
                    "platform_auth": auth_metadata,
                },
            )
        ]
    max_results = max(1, int(source.get("max_results") or 2))
    candidates = _public_search_result_links(search_html, fetched_url or search_url, query)
    items: list[dict[str, Any]] = []
    for candidate in candidates[: max_results * 4]:
        article_html, article_fetch_status, article_content_type, article_fetched_url = _fetch_authorized_html(
            candidate["url"],
            auth_state.cookie_file,
            allow_insecure_tls=allow_insecure_tls,
            timeout=timeout,
            retries=retries,
        )
        metadata = {
            "authorized_public_search": True,
            "authorized_public_result": True,
            "search_platform": platform,
            "search_url": search_url,
            "search_fetch_status": fetch_status,
            "article_fetch_status": "",
            "article_content_type": article_content_type,
            "article_fetched_url": article_fetched_url,
            "platform_auth": auth_metadata,
        }
        title = candidate["text"] or source["name"]
        excerpt = candidate["text"]
        evidence_status = f"{platform}授权公开搜索结果"
        resolved_url = article_fetched_url or candidate["url"]
        if article_fetch_status != "ok":
            metadata["article_fetch_status"] = f"article_fetch_failed:{article_fetch_status}"
            page_metadata = None
        else:
            article = extract_article_text(
                article_html,
                content_type=article_content_type,
                fetched_url=article_fetched_url,
            )
            page_metadata = extract_platform_page_metadata(
                article_html,
                url=article_fetched_url or candidate["url"],
                platform=platform,
            )
            metadata["article_fetch_status"] = article.status
            metadata["article_title"] = article.title
            metadata["page_metadata_status"] = page_metadata.status
            metadata.update(dict(page_metadata.raw_metadata or {}))
            title = article.title or title
            if page_metadata.title and (not title or title == candidate["text"]):
                title = page_metadata.title
            excerpt = article.text or excerpt
            resolved_url = article.fetched_url or resolved_url
            if article.status == "article_excerpt_extracted":
                evidence_status = f"{platform}授权公开搜索结果；正文已摘录"
            elif article.status.startswith("article_fetch_blocked"):
                evidence_status = f"{platform}授权公开搜索结果；正文受限"
        item_type = page_metadata.content_type if page_metadata else "article"
        result_platform = _platform_from_url(resolved_url) or platform
        item = {
            "run_id": run_id,
            "document_id": document["document_id"],
            "interpretation_source_id": source["interpretation_source_id"],
            "platform": result_platform,
            "item_type": item_type,
            "title": _strip_markup(title)[:180] or source["name"],
            "url": resolved_url,
            "query": query,
            "evidence_status": evidence_status,
            "summary": excerpt or _summary_for_source(source, document),
            "author_name": (page_metadata.author_name if page_metadata else "") or result_platform or None,
            "author_url": (page_metadata.author_url if page_metadata else "") or None,
            "published_at": (page_metadata.published_at if page_metadata else "") or None,
            "view_count": page_metadata.view_count if page_metadata else None,
            "engagement_count": page_metadata.engagement_count if page_metadata else None,
            "content_excerpt": excerpt,
            "relevance_score": _text_relevance_score(title, excerpt, query),
            "raw_metadata": metadata,
        }
        items.append(item)
        if len(reference_items(items)) >= max_results:
            break
    if items:
        return items
    return [
        _authorized_search_audit_item(
            source,
            document,
            run_id,
            query,
            fetched_url or search_url,
            platform,
            "授权搜索未返回可用公开结果，保留搜索入口",
            {
                "authorized_public_search": True,
                "fetch_status": fetch_status,
                "content_type": content_type,
                "fetched_url": fetched_url,
                "platform_auth": auth_metadata,
            },
        )
    ]


def _authorized_search_audit_item(
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
    url: str,
    platform: str,
    evidence_status: str,
    raw_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "document_id": document["document_id"],
        "interpretation_source_id": source["interpretation_source_id"],
        "platform": platform,
        "item_type": "search_entry",
        "title": f"{source['name']}：{query}",
        "url": url,
        "query": query,
        "evidence_status": evidence_status,
        "summary": _summary_for_source(source, document),
        "relevance_score": 20,
        "raw_metadata": dict(raw_metadata),
    }


def _collect_local_related_document_items(
    conn,
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT document_id, source_name, source_url, title, canonical_url, published_date, text_excerpt,
               authority_tier_snapshot, authority_score_snapshot
        FROM documents
        WHERE document_id != ?
        ORDER BY COALESCE(published_date, discovered_at) DESC,
                 authority_score_snapshot DESC,
                 title ASC
        LIMIT 200
        """,
        (document["document_id"],),
    ).fetchall()
    max_results = max(1, int(source.get("max_results") or 3))
    candidates: list[dict[str, Any]] = []
    for row in rows:
        candidate = dict(row)
        title = _strip_markup(str(candidate.get("title") or ""))
        excerpt = _strip_markup(str(candidate.get("text_excerpt") or ""))
        if not title or _same_policy_document_title(title, str(document.get("title") or "")):
            continue
        if _looks_like_generic_policy_index(title, str(candidate.get("canonical_url") or "")):
            continue
        score = _text_relevance_score(title, excerpt, query)
        if score < 58:
            continue
        text = f"{title} {excerpt}"
        if not has_subject_relevance(title, excerpt, query):
            continue
        candidates.append({**candidate, "relevance_score": score})
    candidates.sort(
        key=lambda item: (
            int(item.get("relevance_score") or 0),
            int(item.get("authority_score_snapshot") or 0),
        ),
        reverse=True,
    )
    items: list[dict[str, Any]] = []
    for candidate in candidates[:max_results]:
        url = str(candidate.get("canonical_url") or "")
        platform = _platform_from_url(url) or _platform_from_url(str(candidate.get("source_url") or "")) or "local_corpus"
        items.append(
            {
                "run_id": run_id,
                "document_id": document["document_id"],
                "interpretation_source_id": source["interpretation_source_id"],
                "platform": platform,
                "item_type": "article",
                "title": _strip_markup(str(candidate.get("title") or ""))[:180],
                "url": url,
                "query": query,
                "evidence_status": "已入库公开相关文件/解读",
                "summary": _strip_markup(str(candidate.get("text_excerpt") or ""))[:500]
                or f"{candidate.get('source_name')} 已入库相关公开文件。",
                "author_name": candidate.get("source_name"),
                "published_at": candidate.get("published_date"),
                "content_excerpt": _strip_markup(str(candidate.get("text_excerpt") or ""))[:1200]
                or _strip_markup(str(candidate.get("title") or "")),
                "relevance_score": int(candidate.get("relevance_score") or 0),
                "raw_metadata": {
                    "local_related_document": True,
                    "related_document_id": candidate.get("document_id"),
                    "authority_tier_snapshot": candidate.get("authority_tier_snapshot"),
                    "authority_score_snapshot": candidate.get("authority_score_snapshot"),
                    "source_name": candidate.get("source_name"),
                },
            }
        )
    return items


def _collect_local_historical_reference_items(
    conn,
    source: Mapping[str, Any],
    document: Mapping[str, Any],
    run_id: str,
    query: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM interpretation_items
        WHERE document_id = ?
          AND run_id != ?
          AND COALESCE(json_extract(raw_metadata_json, '$.local_related_document'), 0) = 0
        ORDER BY CASE WHEN platform = 'mp.weixin.qq.com' THEN 0 ELSE 1 END,
                 run_id DESC,
                 relevance_score DESC
        LIMIT 300
        """,
        (document["document_id"], run_id),
    ).fetchall()
    max_results = max(1, int(source.get("max_results") or 1))
    seen_urls: set[str] = set()
    seen_subjects: set[tuple[str, str]] = set()
    items: list[dict[str, Any]] = []
    for row in rows:
        original = dict(row)
        url = str(original.get("url") or "")
        if not url or url in seen_urls:
            continue
        if not is_reference_item(original):
            continue
        platform = str(original.get("platform") or _platform_from_url(url) or "historical_reference")
        subject_key = (platform, re.sub(r"\s+", "", _strip_markup(str(original.get("title") or ""))))
        if subject_key in seen_subjects:
            continue
        raw_metadata = dict(_metadata_for_item(original))
        raw_metadata.update(
            {
                "historical_public_reference": True,
                "original_run_id": original.get("run_id"),
                "original_interpretation_source_id": original.get("interpretation_source_id"),
                "original_evidence_status": original.get("evidence_status"),
            }
        )
        seen_urls.add(url)
        seen_subjects.add(subject_key)
        items.append(
            {
                "run_id": run_id,
                "document_id": document["document_id"],
                "interpretation_source_id": source["interpretation_source_id"],
                "platform": platform,
                "item_type": original.get("item_type") or "article",
                "title": original.get("title") or source["name"],
                "url": url,
                "query": query,
                "evidence_status": f"历史成功公开参考复用；原状态：{original.get('evidence_status') or '已验证'}",
                "summary": original.get("summary"),
                "author_name": original.get("author_name"),
                "author_url": original.get("author_url"),
                "published_at": original.get("published_at"),
                "duration_seconds": original.get("duration_seconds"),
                "view_count": original.get("view_count"),
                "engagement_count": original.get("engagement_count"),
                "content_excerpt": original.get("content_excerpt"),
                "relevance_score": int(original.get("relevance_score") or 0),
                "raw_metadata": raw_metadata,
            }
        )
        if len(items) >= max_results:
            break
    return items


def _same_policy_document_title(left: str, right: str) -> bool:
    clean_left = _clean_query_title(left)
    clean_right = _clean_query_title(right)
    return bool(clean_left and clean_right and clean_left == clean_right)


def _fetch_html(
    url: str,
    allow_insecure_tls: bool,
    timeout: int,
    retries: int = 1,
) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    request = Request(url, headers=headers)
    for attempt in range(max(1, retries + 1)):
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                body = response.read(2_000_000)
                content_type = str(response.headers.get("Content-Type") or "")
            charset = _charset_from_content_type(content_type) or "utf-8"
            return body.decode(charset, "replace")
        except Exception:
            if attempt >= retries:
                return None
            time.sleep(min(2.0, 0.4 * (attempt + 1)))
    return None


def _fetch_authorized_html(
    url: str,
    cookie_file: str | Path,
    *,
    allow_insecure_tls: bool,
    timeout: int,
    retries: int = 1,
) -> tuple[str, str, str, str]:
    cookie = _load_cookie(cookie_file, env_fallback=False)
    if not cookie:
        return "", "cookie_file_unavailable", "", url
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*",
        "Cookie": cookie,
    }
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    request = Request(url, headers=headers)
    for attempt in range(max(1, retries + 1)):
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                body = response.read(2_000_000)
                content_type = str(response.headers.get("Content-Type") or "")
                fetched_url = response.geturl() or url
            charset = _charset_from_content_type(content_type) or "utf-8"
            return body.decode(charset, "replace"), "ok", content_type, fetched_url
        except Exception as exc:
            if attempt >= retries:
                return "", f"request_failed:{type(exc).__name__}", "", url
            time.sleep(min(2.0, 0.4 * (attempt + 1)))
    return "", "request_failed", "", url


def _authorized_block_status(
    html_text: str,
    *,
    login_required_markers: tuple[str, ...],
    captcha_markers: tuple[str, ...],
) -> str:
    text = _strip_markup(html_text).lower()
    if any(marker.lower() in text for marker in captcha_markers):
        return "captcha"
    if any(marker.lower() in text for marker in login_required_markers):
        return "login_required"
    generic_captcha = ("验证码", "安全验证", "captcha", "verify you are human")
    generic_login = ("请登录", "登录后查看", "login required")
    if any(marker.lower() in text for marker in generic_captcha):
        return "captcha"
    if any(marker.lower() in text for marker in generic_login):
        return "login_required"
    return ""


class _SearchLinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[dict[str, str]] = []
        self._href_stack: list[list[str]] = []
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return
        attr_map = {str(key).lower(): str(value) for key, value in attrs if value is not None}
        hrefs = []
        for attr_name in ("data-url", "data-href", "data-link", "mu"):
            href = attr_map.get(attr_name, "")
            if href:
                absolute = urljoin(self.base_url, href)
                if absolute not in hrefs:
                    hrefs.append(absolute)
        if not hrefs:
            href = attr_map.get("href", "")
            if href:
                hrefs.append(urljoin(self.base_url, href))
        if hrefs:
            self._href_stack.append(hrefs)
            self._text_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href_stack:
            return
        hrefs = self._href_stack.pop()
        text = _strip_markup(" ".join(self._text_parts)).strip()
        for href in hrefs:
            self.links.append({"url": href, "text": text})
        self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._href_stack:
            self._text_parts.append(data)


def _public_site_result_links(html_text: str, search_url: str, platform: str, query: str) -> list[dict[str, str]]:
    parser = _SearchLinkParser(search_url)
    try:
        parser.feed(html_text)
    except Exception:
        pass
    seen: set[str] = set()
    results: list[dict[str, str]] = []
    for link in parser.links:
        url = _clean_result_url(link["url"])
        text = _strip_markup(link.get("text") or "")
        if not url or url in seen:
            continue
        if not _is_allowed_public_result_url(url, platform):
            continue
        if not _looks_like_article_url(url, search_url):
            continue
        if not text:
            text = url
        score = _text_relevance_score(text, "", query)
        if score < 42 and not any(token in f"{text} {url}" for token in _query_tokens(query)):
            continue
        seen.add(url)
        results.append({"url": url, "text": text})
    return results


def _public_search_result_links(html_text: str, search_url: str, query: str) -> list[dict[str, str]]:
    parser = _SearchLinkParser(search_url)
    try:
        parser.feed(html_text)
    except Exception:
        pass
    search_host = urlparse(search_url).netloc.lower()
    seen: set[str] = set()
    results: list[dict[str, str]] = []
    for link in parser.links:
        url = _clean_result_url(link["url"])
        text = _strip_markup(link.get("text") or "")
        if not url or url in seen:
            continue
        if not _is_allowed_public_search_result_url(url, search_host):
            continue
        if not _looks_like_article_url(url, search_url):
            continue
        if not text:
            text = url
        score = _text_relevance_score(text, "", query)
        if score < 42 and not any(token in f"{text} {url}" for token in _query_tokens(query)):
            continue
        seen.add(url)
        results.append({"url": url, "text": text})
    return results


def _clean_result_url(url: str) -> str:
    if not url:
        return ""
    url = _repair_search_href(html.unescape(url).strip())
    url = _redirect_target_from_search_url(url) or url
    if url.startswith(("javascript:", "mailto:", "tel:", "#")):
        return ""
    url = _prefer_https_for_known_result_hosts(url)
    return url


def _repair_search_href(url: str) -> str:
    # Some search result pages emit raw "&timestamp"; HTMLParser treats "&times"
    # as the multiplication sign and corrupts the URL before we can fetch it.
    return url.replace("×tamp=", "&timestamp=")


def _redirect_target_from_search_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not any(host == root or host.endswith("." + root) for root in ("baidu.com", "sogou.com", "so.com")):
        return ""
    redirect_keys = {"url", "u", "target", "to", "link", "redirect", "dest", "destination", "href"}
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        if key.lower() not in redirect_keys:
            continue
        candidate = _decode_redirect_value(value)
        if candidate:
            return candidate
    return ""


def _decode_redirect_value(value: str) -> str:
    candidate = (value or "").strip()
    for _ in range(3):
        if candidate.startswith("//"):
            candidate = "https:" + candidate
        parsed = urlparse(candidate)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return candidate
        decoded = unquote(candidate)
        if decoded == candidate:
            break
        candidate = decoded
    return ""


def _prefer_https_for_known_result_hosts(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme == "http" and parsed.netloc.lower() in {"mp.weixin.qq.com"}:
        return "https://" + parsed.netloc + parsed.path + (("?" + parsed.query) if parsed.query else "")
    return url


def _is_allowed_public_result_url(url: str, platform: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = parsed.netloc.lower()
    platform = platform.lower()
    if not platform:
        return True
    aliases = {
        "gov.cn": ("gov.cn", "www.gov.cn"),
        "people.cn": ("people.cn",),
        "cctv.com": ("cctv.com", "cntv.cn"),
        "yicai.com": ("yicai.com",),
    }.get(platform, (platform,))
    return any(host == alias or host.endswith("." + alias) for alias in aliases)


def _is_allowed_public_search_result_url(url: str, search_host: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if _is_search_engine_self_link(host, path, search_host):
        return False
    if any(token in path for token in ("/login", "/passport", "/user", "/settings", "/profile/")):
        return False
    return True


def _platform_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _is_search_engine_self_link(host: str, path: str, search_host: str) -> bool:
    if host == search_host and path in {"", "/", "/s", "/web", "/search", "/search_result"}:
        return True
    engine_roots = ("baidu.com", "sogou.com", "so.com")
    if not any(host == root or host.endswith("." + root) for root in engine_roots):
        return False
    redirect_paths = ("/link", "/url")
    if any(path.startswith(prefix) for prefix in redirect_paths):
        return False
    return True


def _looks_like_article_url(url: str, search_url: str = "") -> bool:
    parsed = urlparse(url)
    search = urlparse(search_url) if search_url else None
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if search and host == search.netloc.lower() and path == search.path.lower():
        return False
    if host.startswith("search.") and path in {"", "/", "/index.php", "/search.php"}:
        return False
    if any(token in path for token in ("/search", "/sousuo", "/login", "/user", "/tag", "/video/list")):
        return False
    if path in {"", "/", "/index.php"}:
        return False
    if path.endswith((".jpg", ".jpeg", ".png", ".gif", ".css", ".js", ".ico")):
        return False
    return bool(path and path != "/")


def _charset_from_content_type(content_type: str) -> str:
    match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
    return match.group(1) if match else ""


def _fetch_json(
    url: str,
    allow_insecure_tls: bool,
    cookie_file: str | Path | None,
    timeout: int,
    retries: int = 1,
) -> dict[str, Any] | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Referer": "https://search.bilibili.com/",
        "Accept": "application/json, text/plain, */*",
    }
    cookie = _load_cookie(cookie_file)
    if cookie:
        headers["Cookie"] = cookie
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    request = Request(url, headers=headers)
    body = ""
    for attempt in range(max(1, retries + 1)):
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                body = response.read(2_000_000).decode("utf-8", "replace")
            break
        except Exception:
            if attempt >= retries:
                return None
            time.sleep(min(2.0, 0.4 * (attempt + 1)))
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _fetch_text(
    url: str,
    allow_insecure_tls: bool,
    cookie_file: str | Path | None,
    timeout: int,
    retries: int = 1,
) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Referer": "https://www.bilibili.com/",
        "Accept": "text/plain,text/xml,application/xml,*/*",
    }
    cookie = _load_cookie(cookie_file)
    if cookie:
        headers["Cookie"] = cookie
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    request = Request(url, headers=headers)
    for attempt in range(max(1, retries + 1)):
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                return response.read(2_000_000).decode("utf-8", "replace")
        except Exception:
            if attempt >= retries:
                return None
            time.sleep(min(2.0, 0.4 * (attempt + 1)))
    return None


def _load_cookie(cookie_file: str | Path | None, *, env_fallback: bool = True) -> str | None:
    env_cookie = os.environ.get("BILIBILI_COOKIE") if env_fallback else ""
    if env_cookie:
        return env_cookie.strip()
    if not cookie_file:
        cookie_file = os.environ.get("BILIBILI_COOKIE_FILE") if env_fallback else ""
    if not cookie_file:
        return None
    path = Path(cookie_file).expanduser()
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


def _bilibili_video_enrichment(
    raw: Mapping[str, Any],
    allow_insecure_tls: bool,
    cookie_file: str | Path | None,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    bvid = str(raw.get("bvid") or "").strip()
    if not bvid:
        return {}
    enrichment: dict[str, Any] = {}
    view = _fetch_json(
        f"https://api.bilibili.com/x/web-interface/view?bvid={quote(bvid)}",
        allow_insecure_tls,
        cookie_file,
        timeout,
        retries,
    )
    if view and view.get("code") == 0:
        data = view.get("data") or {}
        stat = data.get("stat") or {}
        owner = data.get("owner") or {}
        enrichment.update(
            {
                "detail_enriched": True,
                "aid": data.get("aid"),
                "cid": data.get("cid"),
                "desc": data.get("desc"),
                "owner_name": owner.get("name"),
                "author_mid": owner.get("mid") or raw.get("mid"),
                "view": stat.get("view"),
                "reply": stat.get("reply"),
                "favorite": stat.get("favorite"),
                "coin": stat.get("coin"),
                "share": stat.get("share"),
                "like": stat.get("like"),
            }
        )
    author_mid = enrichment.get("author_mid") or raw.get("mid")
    if author_mid:
        enrichment.update(
            _bilibili_author_profile(
                str(author_mid),
                allow_insecure_tls,
                cookie_file,
                timeout,
                retries,
            )
        )
    cid = enrichment.get("cid") or raw.get("cid")
    if not cid:
        pages = _fetch_json(
            f"https://api.bilibili.com/x/player/pagelist?bvid={quote(bvid)}&jsonp=jsonp",
            allow_insecure_tls,
            cookie_file,
            timeout,
            retries,
        )
        page_list = (pages.get("data") if pages else None) or []
        if page_list:
            cid = page_list[0].get("cid")
            enrichment["cid"] = cid
            enrichment["page_count"] = len(page_list)
    if cid:
        subtitle = _bilibili_subtitle_for_video(
            bvid,
            str(cid),
            allow_insecure_tls,
            cookie_file,
            timeout,
            retries,
        )
        enrichment.update(subtitle)
        danmaku = _bilibili_danmaku_for_video(
            str(cid),
            allow_insecure_tls,
            cookie_file,
            timeout,
            retries,
        )
        enrichment.update(danmaku)
    aid = raw.get("aid") or enrichment.get("aid")
    if aid:
        comments = _bilibili_comments_for_video(
            str(aid),
            allow_insecure_tls,
            cookie_file,
            timeout,
            retries,
        )
        enrichment.update(comments)
    return enrichment


def _bilibili_author_profile(
    mid: str,
    allow_insecure_tls: bool,
    cookie_file: str | Path | None,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    if not mid:
        return {"author_profile_status": "missing_author_mid"}
    payload = _fetch_json(
        f"https://api.bilibili.com/x/web-interface/card?mid={quote(mid)}&photo=true",
        allow_insecure_tls,
        cookie_file,
        timeout,
        retries,
    )
    if not payload:
        return {"author_mid": mid, "author_profile_status": "author_profile_request_failed"}
    if payload.get("code") != 0:
        return {"author_mid": mid, "author_profile_status": f"author_profile_unavailable:{payload.get('code')}"}
    data = payload.get("data") or {}
    card = data.get("card") or {}
    official = card.get("official_verify") or card.get("Official") or {}
    level_info = card.get("level_info") or {}
    name = _strip_markup(str(card.get("name") or ""))
    sign = _strip_markup(str(card.get("sign") or ""))
    return {
        "author_profile_enriched": True,
        "author_profile_status": "parsed",
        "author_mid": card.get("mid") or mid,
        "author_profile_name": name,
        "author_sign": sign[:240],
        "author_follower_count": _int_or_none(card.get("fans") or data.get("follower")),
        "author_following_count": _int_or_none(card.get("friend") or card.get("attention")),
        "author_level": _int_or_none(level_info.get("current_level")),
        "author_verified_type": official.get("type"),
        "author_verified_desc": _strip_markup(str(official.get("desc") or ""))[:120],
    }


def _bilibili_subtitle_for_video(
    bvid: str,
    cid: str,
    allow_insecure_tls: bool,
    cookie_file: str | Path | None,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    payload = _fetch_json(
        f"https://api.bilibili.com/x/player/v2?bvid={quote(bvid)}&cid={quote(cid)}",
        allow_insecure_tls,
        cookie_file,
        timeout,
        retries,
    )
    subtitles = (((payload or {}).get("data") or {}).get("subtitle") or {}).get("subtitles") or []
    if not subtitles:
        return {"subtitle_status": "no_public_subtitle"}
    selected = subtitles[0]
    url = str(selected.get("subtitle_url") or "")
    if url.startswith("//"):
        url = "https:" + url
    if not url:
        return {"subtitle_status": "missing_subtitle_url", "subtitle_count": len(subtitles)}
    body = _fetch_json(url, allow_insecure_tls, cookie_file, timeout, retries)
    excerpt = _subtitle_excerpt(body or {})
    return {
        "subtitle_status": "parsed" if excerpt else "empty_subtitle",
        "subtitle_count": len(subtitles),
        "subtitle_url": url,
        "subtitle_lan": selected.get("lan") or selected.get("lan_doc"),
        "subtitle_excerpt": excerpt,
    }


def _subtitle_excerpt(payload: Mapping[str, Any], limit: int = 700) -> str:
    return subtitle_excerpt_from_payload(payload, limit=limit).text


def _bilibili_comments_for_video(
    aid: str,
    allow_insecure_tls: bool,
    cookie_file: str | Path | None,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    payload = _fetch_json(
        f"https://api.bilibili.com/x/v2/reply?type=1&oid={quote(aid)}&sort=2&ps=10",
        allow_insecure_tls,
        cookie_file,
        timeout,
        retries,
    )
    if not payload:
        return {"comment_status": "comment_request_failed"}
    if payload.get("code") != 0:
        return {"comment_status": f"comment_unavailable:{payload.get('code')}"}
    replies = ((payload.get("data") or {}).get("replies") or [])[:10]
    excerpt = _comment_excerpt(replies)
    return {
        "comment_status": "parsed" if excerpt else "empty_comments",
        "comment_count": len(replies),
        "comment_excerpt": excerpt,
    }


def _bilibili_danmaku_for_video(
    cid: str,
    allow_insecure_tls: bool,
    cookie_file: str | Path | None,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    body = _fetch_text(
        f"https://comment.bilibili.com/{quote(cid)}.xml",
        allow_insecure_tls,
        cookie_file,
        timeout,
        retries,
    )
    if not body:
        return {"danmaku_status": "danmaku_request_failed"}
    excerpt = _danmaku_excerpt(body)
    return {
        "danmaku_status": "parsed" if excerpt else "empty_danmaku",
        "danmaku_excerpt": excerpt,
    }


def _comment_excerpt(replies: list[Mapping[str, Any]], limit: int = 500) -> str:
    return comment_excerpt_from_replies(replies, limit=limit).text


def _danmaku_excerpt(xml_text: str, limit: int = 500) -> str:
    return danmaku_excerpt_from_xml(xml_text, limit=limit).text


def _bilibili_excerpt(raw: Mapping[str, Any], enrichment: Mapping[str, Any] | None = None) -> str:
    enrichment = enrichment or {}
    parts = [
        _strip_markup(str(raw.get("description") or "")),
        _strip_markup(str(raw.get("desc") or "")),
        _strip_markup(str(enrichment.get("desc") or "")),
        f"字幕摘录：{_strip_markup(str(enrichment.get('subtitle_excerpt') or ''))}"
        if enrichment.get("subtitle_excerpt")
        else "",
        f"评论摘录：{_strip_markup(str(enrichment.get('comment_excerpt') or ''))}"
        if enrichment.get("comment_excerpt")
        else "",
        f"弹幕摘录：{_strip_markup(str(enrichment.get('danmaku_excerpt') or ''))}"
        if enrichment.get("danmaku_excerpt")
        else "",
        (
            "作者页："
            + "，".join(
                part
                for part in [
                    _strip_markup(str(enrichment.get("author_profile_name") or enrichment.get("owner_name") or "")),
                    f"粉丝{_format_count(enrichment.get('author_follower_count'))}"
                    if enrichment.get("author_follower_count") is not None
                    else "",
                    _strip_markup(str(enrichment.get("author_verified_desc") or "")),
                    _strip_markup(str(enrichment.get("author_sign") or ""))[:120],
                ]
                if part
            )
        )
        if enrichment.get("author_profile_enriched")
        else "",
        f"标签：{_strip_markup(str(raw.get('tag') or ''))}" if raw.get("tag") else "",
        f"分区：{_strip_markup(str(raw.get('typename') or ''))}" if raw.get("typename") else "",
    ]
    text = "；".join(part for part in parts if part and part != "-")
    return re.sub(r"\s+", " ", text).strip()[:900]


def _bilibili_summary(raw: Mapping[str, Any]) -> str:
    views = _format_count(raw.get("play")) or "未知"
    likes = _format_count(raw.get("like")) or "未知"
    duration = str(raw.get("duration") or "未知时长")
    return f"B 站公开视频结果，可用于观察市场/公众解读角度与传播热度；播放{views}，点赞{likes}，时长{duration}。"


def _relevance_score(raw: Mapping[str, Any], query: str) -> int:
    title = _strip_markup(str(raw.get("title") or ""))
    text = " ".join(
        [
            title,
            _strip_markup(str(raw.get("description") or "")),
            _strip_markup(str(raw.get("tag") or "")),
            _strip_markup(str(raw.get("typename") or "")),
        ]
    )
    score = 45
    for keyword in ("政策", "解读", "分析", "文件", "规划", "条例", "办法", "财政", "金融", "投资"):
        if keyword in text:
            score += 4
    for token in _query_tokens(query):
        if token and token in text:
            score += 5
    for term in _subject_query_terms(query):
        if term in text or term in re.sub(r"\s+", "", text):
            score += 8
    play = _int_or_none(raw.get("play")) or 0
    if play > 0:
        score += min(12, int(math.log10(play + 1) * 3))
    if raw.get("description") and raw.get("description") != "-":
        score += 4
    return max(0, min(100, score))


def _text_relevance_score(title: str, excerpt: str, query: str) -> int:
    text = " ".join([_strip_markup(title), _strip_markup(excerpt)])
    compact_text = re.sub(r"\s+", "", text)
    score = 42
    for keyword in ("政策", "解读", "分析", "文件", "规划", "条例", "办法", "影响", "产业", "市场"):
        if keyword in text:
            score += 4
    for token in _query_tokens(query):
        if token and token in text:
            score += 6
    for term in _subject_query_terms(query):
        if term in text or term in compact_text:
            score += 8
    if len(excerpt) >= 80:
        score += 6
    if len(excerpt) >= 180:
        score += 4
    return max(0, min(100, score))


def _query_tokens(query: str) -> list[str]:
    stopwords = {"政策", "解读", "通知", "关于", "国务院"}
    clean = re.sub(r"[“”\"'`]", "", query or "")
    tokens = [
        token
        for token in re.split(r"[\s，,。；;：:《》【】（）()、]+", clean)
        if len(token) >= 2 and token not in stopwords
    ]
    domain_terms = (
        "十五五",
        "五年规划",
        "农业农村",
        "农业",
        "农村",
        "现代化",
        "乡村振兴",
        "人工智能",
        "AI",
        "半导体",
        "芯片",
        "机器人",
        "算力",
        "数据中心",
        "云计算",
        "化工",
        "新材料",
    )
    for term in domain_terms:
        if term in clean and term not in tokens:
            tokens.append(term)
    deduped: list[str] = []
    for token in tokens:
        if token not in deduped:
            deduped.append(token)
    return deduped[:12]


def _subject_query_terms(query: str) -> list[str]:
    clean = re.sub(r"[“”\"'`]", "", query or "")
    compact = re.sub(r"\s+", "", clean)
    subject_terms = (
        "药品零售",
        "药品监督管理局",
        "药品监管",
        "药监局",
        "零售许可",
        "许可验收",
        "验收实施细则",
        "实施细则",
        "药品",
        "医疗器械",
        "生物医药",
        "海洋生物医药",
        "医药",
        "医保",
        "医疗服务",
        "人工智能",
        "AI",
        "半导体",
        "芯片",
        "机器人",
        "算力",
        "数据中心",
        "云计算",
        "化工",
        "新材料",
        "软件",
        "信创",
        "工业软件",
        "新能源汽车",
        "智能汽车",
        "金融",
        "银行",
        "证券",
        "保险",
        "私募投资基金",
        "私募基金",
        "资本市场",
        "证监会",
        "金融监管",
        "防范风险",
        "高质量发展",
        "电池",
        "储能",
        "高端装备",
        "工业母机",
        "通信",
        "5G",
        "6G",
        "卫星互联网",
        "航空航天",
        "低空经济",
        "电力",
        "电网",
        "耕地保护专项规划",
        "耕地保护",
        "永久基本农田",
        "基本农田",
        "粮食安全",
        "土地管理",
        "国土空间",
        "自然资源",
        "留用地",
        "集体土地",
        "农业农村",
        "种业",
        "农机",
        "农业",
        "农村",
        "煤炭",
        "油气",
        "房地产",
        "城市更新",
        "保障房",
        "风电",
        "光伏",
        "氢能",
        "数据要素",
        "数字经济",
        "军工",
        "国企改革",
        "央国企",
        "平台经济",
        "互联网监管",
        "消费",
        "商贸零售",
        "食品饮料",
        "建筑建材",
        "财政税收",
        "政府债务",
        "外贸",
        "跨境投资",
        "自贸区",
        "文化传媒",
        "游戏",
        "影视",
        "教育",
        "环保",
        "双碳",
        "循环经济",
        "公共安全",
        "网络安全",
        "就业",
        "社保",
        "养老",
        "旅游",
        "文旅",
        "水利",
        "防灾",
        "应急管理",
        "十五五",
        "五年规划",
        "区域战略",
        "现代化",
        "乡村振兴",
    )
    terms = [term for term in subject_terms if term in compact]
    for token in _query_tokens(query):
        token_compact = re.sub(r"\s+", "", token)
        if _is_generic_query_token(token_compact):
            continue
        if len(token_compact) >= 4 and token_compact not in terms:
            terms.append(token_compact)
    deduped: list[str] = []
    for term in terms:
        if term and term not in deduped:
            deduped.append(term)
    return deduped[:12]


def _is_generic_query_token(token: str) -> bool:
    if not token:
        return True
    generic_exact = {
        "政策",
        "解读",
        "政策解读",
        "文件",
        "通知",
        "意见",
        "规定",
        "办法",
        "公开征求",
        "征求意见",
        "征求意见稿",
        "2026年修订",
        "广东省",
        "广东",
        "中国政府网",
        "广东省人民政府门户网站",
        "人民政府门户网站",
        "门户网站",
        "国务院",
        "关于",
    }
    if token in generic_exact:
        return True
    generic_parts = ("人民政府", "门户网站", "公开征求", "征求意见", "年修订")
    return any(part in token for part in generic_parts)


def _is_weak_subject_term(term: str) -> bool:
    return term in {
        "药品",
        "医药",
        "医保",
        "软件",
        "金融",
        "农业",
        "农村",
        "电力",
        "教育",
        "旅游",
        "文旅",
        "就业",
        "社保",
        "养老",
        "现代化",
        "实施细则",
        "五年规划",
        "区域战略",
    }


def _duration_seconds(value: str) -> int | None:
    if not value:
        return None
    parts = [part for part in value.split(":") if part.isdigit()]
    if not parts:
        return None
    total = 0
    for part in parts:
        total = total * 60 + int(part)
    return total


def _timestamp_to_utc(value: object) -> str | None:
    number = _int_or_none(value)
    if not number:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(number, tz=timezone.utc).isoformat()


def _engagement_count(raw: Mapping[str, Any]) -> int | None:
    values = [
        _int_or_none(raw.get("favorites")),
        _int_or_none(raw.get("like")),
        _int_or_none(raw.get("review")),
        _int_or_none(raw.get("danmaku")),
    ]
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present)


def _int_or_none(value: object) -> int | None:
    try:
        if value in (None, "", "-"):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_count(value: object) -> str:
    number = _int_or_none(value)
    if number is None:
        return ""
    if number >= 10000:
        return f"{number / 10000:.1f}万"
    return str(number)


def _strip_markup(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value or "")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _summary_for_source(source: Mapping[str, Any], document: Mapping[str, Any]) -> str:
    if source.get("platform") == "bilibili":
        return "B 站视频解读适合补充舆论热度、专家表达、产业自媒体观点；正式结论仍以官方原文为准。"
    return "作为非原文解读资料，用于补充背景、观点差异和传播热度，不替代官方文件。"
