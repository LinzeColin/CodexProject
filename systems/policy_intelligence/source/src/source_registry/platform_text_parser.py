from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from xml.etree import ElementTree


@dataclass(frozen=True)
class TextExcerpt:
    text: str
    item_count: int
    parser: str
    status: str


def subtitle_excerpt_from_payload(payload: Mapping[str, Any], limit: int = 700) -> TextExcerpt:
    lines: list[str] = []
    for entry in payload.get("body") or []:
        content = _clean_text(str(entry.get("content") or ""))
        if content:
            lines.append(content)
        if len(" ".join(lines)) >= limit:
            break
    text = _join(lines, " ", limit)
    return TextExcerpt(text, len(lines), "bilibili_subtitle_json", "parsed" if text else "empty_subtitle")


def subtitle_excerpt_from_text(text: str, *, fmt: str = "auto", limit: int = 700) -> TextExcerpt:
    parser = _subtitle_format(fmt, text)
    if parser == "json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return TextExcerpt("", 0, "subtitle_json", "parse_failed:json")
        parsed = subtitle_excerpt_from_payload(payload, limit=limit) if isinstance(payload, Mapping) else TextExcerpt("", 0, "subtitle_json", "empty_subtitle")
        return TextExcerpt(parsed.text, parsed.item_count, "subtitle_json", parsed.status)
    if parser == "vtt":
        lines = _timed_text_lines(text, is_vtt=True)
        excerpt = _join(lines, " ", limit)
        return TextExcerpt(excerpt, len(lines), "webvtt", "parsed" if excerpt else "empty_subtitle")
    if parser == "srt":
        lines = _timed_text_lines(text, is_vtt=False)
        excerpt = _join(lines, " ", limit)
        return TextExcerpt(excerpt, len(lines), "srt", "parsed" if excerpt else "empty_subtitle")
    cleaned = _clean_text(text)
    return TextExcerpt(cleaned[:limit], 1 if cleaned else 0, "plain_subtitle", "parsed" if cleaned else "empty_subtitle")


def comment_excerpt_from_replies(replies: Iterable[Mapping[str, Any]], limit: int = 500) -> TextExcerpt:
    parts: list[str] = []
    for reply in replies:
        content = ((reply.get("content") or {}).get("message") or reply.get("message") or "")
        text = _clean_text(str(content))
        if text:
            parts.append(text)
        if len(" ".join(parts)) >= limit:
            break
    excerpt = _join(parts, "；", limit)
    return TextExcerpt(excerpt, len(parts), "comment_replies", "parsed" if excerpt else "empty_comments")


def danmaku_excerpt_from_xml(xml_text: str, limit: int = 500) -> TextExcerpt:
    parts: list[str] = []
    try:
        root = ElementTree.fromstring(xml_text or "")
        for node in root.iter():
            if _local_name(node.tag) == "d" and node.text:
                text = _clean_text(node.text)
                if text:
                    parts.append(text)
                if len(" ".join(parts)) >= limit or len(parts) >= 80:
                    break
    except ElementTree.ParseError:
        values = re.findall(r"<d\b[^>]*>(.*?)</d>", xml_text or "", flags=re.S)
        for value in values[:80]:
            text = _clean_text(value)
            if text:
                parts.append(text)
            if len(" ".join(parts)) >= limit:
                break
    excerpt = _join(parts, "；", limit)
    return TextExcerpt(excerpt, len(parts), "danmaku_xml", "parsed" if excerpt else "empty_danmaku")


def _subtitle_format(fmt: str, text: str) -> str:
    lowered = (fmt or "auto").lower()
    if lowered in {"json", "vtt", "webvtt", "srt"}:
        return "vtt" if lowered == "webvtt" else lowered
    stripped = (text or "").lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    if stripped.startswith("WEBVTT"):
        return "vtt"
    if re.search(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}", text or ""):
        return "srt"
    return "plain"


def _timed_text_lines(text: str, *, is_vtt: bool) -> list[str]:
    lines: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if is_vtt and (line == "WEBVTT" or line.startswith(("NOTE", "STYLE", "REGION"))):
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue
        cleaned = _clean_text(re.sub(r"<[^>]+>", "", line))
        if cleaned:
            lines.append(cleaned)
    return lines


def _clean_text(value: str) -> str:
    unescaped = html.unescape(value or "")
    without_tags = re.sub(r"<[^>]+>", " ", unescaped)
    return re.sub(r"\s+", " ", without_tags).strip()


def _join(values: list[str], sep: str, limit: int) -> str:
    return re.sub(r"\s+", " ", sep.join(values)).strip()[:limit]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
