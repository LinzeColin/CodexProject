from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Any, Mapping
from urllib.parse import urlparse


@dataclass(frozen=True)
class PlatformPageMetadata:
    title: str = ""
    author_name: str = ""
    author_url: str = ""
    published_at: str = ""
    view_count: int | None = None
    engagement_count: int | None = None
    content_type: str = "article"
    status: str = "empty_metadata"
    raw_metadata: Mapping[str, Any] | None = None


def extract_platform_page_metadata(html_text: str, *, url: str = "", platform: str = "") -> PlatformPageMetadata:
    parser = _MetadataHTMLParser()
    try:
        parser.feed(html_text or "")
    except Exception:
        pass
    json_objects = _json_objects(parser.json_ld_blocks + parser.state_json_blocks)
    meta = {key.lower(): value for key, value in parser.meta.items() if value}
    title = _first(
        meta.get("og:title"),
        meta.get("twitter:title"),
        _json_find_string(json_objects, ("headline", "name", "title")),
        parser.title,
    )
    author_name = _first(
        meta.get("author"),
        meta.get("article:author"),
        _json_author_name(json_objects),
    )
    author_url = _first(_json_author_url(json_objects), _author_url_from_meta(meta))
    published_at = _first(
        meta.get("article:published_time"),
        meta.get("pubdate"),
        meta.get("publishdate"),
        meta.get("date"),
        _json_find_string(json_objects, ("datePublished", "uploadDate", "pubDate", "created_at", "createdAt")),
    )
    metrics = _metrics_from_json(json_objects)
    if not any(value is not None for value in metrics.values()):
        metrics = _metrics_from_text(html_text or "")
    content_type = _content_type(meta, json_objects, url=url, platform=platform)
    raw = {
        "page_metadata_status": "parsed",
        "page_metadata_platform": platform or _platform_from_url(url),
        "page_metadata_content_type": content_type,
        "page_metadata_sources": _metadata_sources(parser, json_objects),
    }
    status = "parsed" if any([title, author_name, published_at, metrics]) else "empty_metadata"
    return PlatformPageMetadata(
        title=_clean(title)[:180],
        author_name=_clean(author_name)[:120],
        author_url=author_url[:500],
        published_at=_clean(published_at)[:80],
        view_count=metrics.get("view_count"),
        engagement_count=metrics.get("engagement_count"),
        content_type=content_type,
        status=status,
        raw_metadata=raw,
    )


class _MetadataHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.title = ""
        self.title_parts: list[str] = []
        self.json_ld_blocks: list[str] = []
        self.state_json_blocks: list[str] = []
        self._in_title = False
        self._script_kind = ""
        self._script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        attr_map = {str(key).lower(): str(value) for key, value in attrs if value is not None}
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            key = attr_map.get("property") or attr_map.get("name") or attr_map.get("itemprop")
            content = attr_map.get("content")
            if key and content:
                self.meta[key] = content
        if tag == "script":
            script_type = attr_map.get("type", "").lower()
            script_id = attr_map.get("id", "").lower()
            if "ld+json" in script_type:
                self._script_kind = "json_ld"
                self._script_parts = []
            elif script_id in {"__next_data__", "initial-state", "__nuxt__"} or "json" in script_type:
                self._script_kind = "state_json"
                self._script_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
            self.title = _clean(" ".join(self.title_parts))
        if tag == "script" and self._script_kind:
            text = "".join(self._script_parts).strip()
            if self._script_kind == "json_ld":
                self.json_ld_blocks.append(text)
            elif self._script_kind == "state_json":
                self.state_json_blocks.append(text)
            self._script_kind = ""
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._script_kind:
            self._script_parts.append(data)


def _json_objects(blocks: list[str]) -> list[Any]:
    objects: list[Any] = []
    for block in blocks:
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        objects.append(parsed)
    return objects


def _json_find_string(objects: list[Any], keys: tuple[str, ...]) -> str:
    lowered = {key.lower() for key in keys}
    for value in _walk_json(objects):
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).lower() in lowered and isinstance(item, (str, int, float)):
                    return str(item)
    return ""


def _json_author_name(objects: list[Any]) -> str:
    for value in _walk_json(objects):
        if not isinstance(value, Mapping):
            continue
        for key in ("author", "publisher", "creator", "owner"):
            item = value.get(key)
            if isinstance(item, str):
                return item
            if isinstance(item, Mapping):
                name = item.get("name") or item.get("nickname") or item.get("screen_name")
                if name:
                    return str(name)
    return ""


def _json_author_url(objects: list[Any]) -> str:
    for value in _walk_json(objects):
        if not isinstance(value, Mapping):
            continue
        for key in ("author", "publisher", "creator", "owner"):
            item = value.get(key)
            if isinstance(item, Mapping):
                url = item.get("url") or item.get("@id") or item.get("profileUrl")
                if isinstance(url, str) and url.startswith(("http://", "https://")):
                    return url
    return ""


def _metrics_from_json(objects: list[Any]) -> dict[str, int | None]:
    views = []
    engagements = []
    view_keys = {"viewcount", "playcount", "readcount", "views", "view_count", "play_count"}
    engagement_keys = {"likecount", "commentcount", "sharecount", "favoritecount", "diggcount", "repostcount", "点赞", "评论", "转发"}
    for value in _walk_json(objects):
        if not isinstance(value, Mapping):
            continue
        if value.get("interactionType") and value.get("userInteractionCount") is not None:
            interaction_count = _number(value.get("userInteractionCount"))
            if interaction_count is not None:
                engagements.append(interaction_count)
        for key, item in value.items():
            lowered = str(key).lower()
            number = _number(item)
            if number is None:
                continue
            if lowered in view_keys:
                views.append(number)
            if lowered in engagement_keys:
                engagements.append(number)
    return {
        "view_count": max(views) if views else None,
        "engagement_count": sum(engagements) if engagements else None,
    }


def _metrics_from_text(text: str) -> dict[str, int | None]:
    cleaned = _clean(text)
    views = [_chinese_number(match.group(1)) for match in re.finditer(r"([\d.]+万?)\s*(?:播放|阅读|浏览|观看)", cleaned)]
    likes = [_chinese_number(match.group(1)) for match in re.finditer(r"([\d.]+万?)\s*(?:赞|点赞|评论|转发|收藏)", cleaned)]
    return {
        "view_count": max([item for item in views if item is not None], default=None),
        "engagement_count": sum(item for item in likes if item is not None) if likes else None,
    }


def _content_type(meta: Mapping[str, str], objects: list[Any], *, url: str, platform: str) -> str:
    og_type = (meta.get("og:type") or "").lower()
    if "video" in og_type:
        return "video"
    for value in _walk_json(objects):
        if isinstance(value, Mapping):
            type_value = str(value.get("@type") or value.get("type") or "").lower()
            if "video" in type_value:
                return "video"
            if "article" in type_value or "posting" in type_value:
                return "article"
    host = urlparse(url).netloc.lower()
    if platform in {"douyin", "kuaishou", "bilibili"} or "bilibili.com" in host or "douyin.com" in host:
        return "video"
    return "article"


def _metadata_sources(parser: _MetadataHTMLParser, objects: list[Any]) -> list[str]:
    sources = []
    if parser.meta:
        sources.append("meta")
    if parser.title:
        sources.append("title")
    if objects:
        sources.append("json")
    return sources


def _walk_json(value: Any):
    if isinstance(value, Mapping):
        yield value
        for item in value.values():
            yield from _walk_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_json(item)


def _number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        return _chinese_number(value)
    return None


def _chinese_number(value: str) -> int | None:
    text = _clean(value)
    match = re.search(r"(\d+(?:\.\d+)?)\s*(万)?", text)
    if not match:
        return None
    number = float(match.group(1))
    if match.group(2):
        number *= 10000
    return int(number)


def _author_url_from_meta(meta: Mapping[str, str]) -> str:
    for key in ("article:author:url", "author:url"):
        value = meta.get(key)
        if value and value.startswith(("http://", "https://")):
            return value
    return ""


def _first(*values: Any) -> str:
    for value in values:
        if value:
            return str(value)
    return ""


def _clean(value: str) -> str:
    text = unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _platform_from_url(url: str) -> str:
    host = urlparse(url or "").netloc.lower()
    return host[4:] if host.startswith("www.") else host
