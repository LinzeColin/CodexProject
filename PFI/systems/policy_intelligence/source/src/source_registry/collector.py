from __future__ import annotations

import re
import ssl
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from .content_db import content_hash
from .normalization import canonical_domain, normalize_url

DOC_KEYWORDS = (
    "政策",
    "文件",
    "通知",
    "公告",
    "意见",
    "办法",
    "规定",
    "规划",
    "方案",
    "白皮书",
    "蓝皮书",
    "报告",
    "解读",
    "公报",
    "决定",
)
ATTACHMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx")


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class HttpFetcher:
    def __init__(
        self,
        timeout: int = 20,
        user_agent: str | None = None,
        delay_seconds: float = 0.5,
        allow_insecure_tls: bool = False,
    ):
        self.timeout = timeout
        self.user_agent = user_agent or "PolicySourceRegistryBot/0.1 (+local research)"
        self.delay_seconds = delay_seconds
        self.allow_insecure_tls = allow_insecure_tls

    def fetch(self, url: str) -> FetchResult:
        time.sleep(self.delay_seconds)
        normalized = normalize_url(url)
        request = Request(normalized, headers={"User-Agent": self.user_agent})
        context = ssl._create_unverified_context() if self.allow_insecure_tls else None
        with urlopen(request, timeout=self.timeout, context=context) as response:
            return FetchResult(
                url=normalized,
                status_code=int(response.status),
                content_type=response.headers.get("content-type", ""),
                body=response.read(),
            )


class FixtureFetcher:
    def __init__(self, fixtures: dict[str, bytes | str]):
        self.fixtures = {normalize_url(k): v for k, v in fixtures.items()}

    def fetch(self, url: str) -> FetchResult:
        normalized = normalize_url(url)
        if normalized not in self.fixtures:
            raise KeyError(f"fixture not found: {normalized}")
        body = self.fixtures[normalized]
        if isinstance(body, str):
            payload = body.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        else:
            payload = body
            content_type = "application/octet-stream"
        return FetchResult(normalized, 200, content_type, payload)


class SimpleHtmlExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.links: list[tuple[str, str]] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "a" and attrs_dict.get("href"):
            self._current_href = attrs_dict["href"]
            self._current_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag == "a" and self._current_href:
            label = compact_text("".join(self._current_text))
            self.links.append((self._current_href, label))
            self._current_href = None
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title += data
        if self._current_href:
            self._current_text.append(data)
        stripped = compact_text(data)
        if stripped:
            self.text_parts.append(stripped)


def parse_html(html: str) -> SimpleHtmlExtractor:
    parser = SimpleHtmlExtractor()
    parser.feed(html)
    parser.title = clean_title(parser.title)
    return parser


def discover_documents(
    source: dict,
    page_url: str,
    html: str,
    max_links: int,
) -> list[dict]:
    parser = parse_html(html)
    candidates: list[dict] = []
    page_text = compact_text(" ".join(parser.text_parts))
    if _looks_like_document(parser.title, page_url):
        candidates.append(
            _doc_from_link(
                source,
                page_url,
                clean_title(parser.title or source["name"]),
                text_excerpt=page_text[:800],
                status="fetched",
                body=html,
            )
        )

    seen = {normalize_url(page_url)}
    source_domain = str(source.get("canonical_domain") or canonical_domain(source["official_url"]))
    for href, label in parser.links:
        if len(candidates) >= max_links:
            break
        absolute = normalize_url(urljoin(page_url, href))
        if not absolute or absolute in seen or _skip_url(absolute):
            continue
        if not _same_research_surface(source_domain, absolute):
            continue
        if not _looks_like_document(label, absolute):
            continue
        seen.add(absolute)
        candidates.append(_doc_from_link(source, absolute, label or absolute))
    return candidates


def save_snapshot(root: Path, run_id: str, source_id: str, url: str, body: bytes, content_type: str) -> str:
    suffix = _suffix_for(url, content_type)
    digest = content_hash(url)[:12]
    run_date = run_id.split("_", 1)[1][:8] if "_" in run_id else run_id[:8]
    path = root / "snapshots" / run_date / f"{source_id}_{digest}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return str(path)


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def clean_title(value: str) -> str:
    title = compact_text(value)
    suffixes = (
        "_国务院办公厅政府信息公开指南（试行）_信息公开_政策_中国政府网",
        "_其他_中国政府网",
        "__中国政府网",
        "_中国政府网",
        "_其他",
    )
    for suffix in suffixes:
        if title.endswith(suffix):
            title = title[: -len(suffix)]
    return title.strip(" _-")


def _doc_from_link(
    source: dict,
    url: str,
    title: str,
    text_excerpt: str | None = None,
    status: str = "discovered",
    body: str | bytes | None = None,
) -> dict:
    document_type = "attachment" if _is_attachment(url) else "webpage"
    payload_hash = content_hash(body or title or url)
    return {
        "source_id": source["source_id"],
        "source_name": source["name"],
        "source_url": source["official_url"],
        "authority_tier_snapshot": source.get("effective_tier"),
        "authority_score_snapshot": source.get("effective_score"),
        "title": clean_title(title)[:240] or url,
        "url": url,
        "document_type": document_type,
        "content_hash": payload_hash,
        "text_excerpt": text_excerpt,
        "status": status,
    }


def _looks_like_document(label: str, url: str) -> bool:
    text = f"{label} {url}"
    if _is_attachment(url):
        return True
    if any(keyword in text for keyword in DOC_KEYWORDS):
        return True
    return False


def _skip_url(url: str) -> bool:
    lowered = url.lower()
    return lowered.startswith(("mailto:", "javascript:")) or "#" in lowered


def _is_attachment(url: str) -> bool:
    return urlsplit(url).path.lower().endswith(ATTACHMENT_EXTENSIONS)


def _same_research_surface(source_domain: str, url: str) -> bool:
    domain = canonical_domain(url)
    if not domain:
        return False
    if source_domain and domain == source_domain:
        return True
    return domain.endswith(".gov.cn") or domain.endswith(".cssn.cn")


def _suffix_for(url: str, content_type: str) -> str:
    path = urlsplit(url).path.lower()
    for suffix in (*ATTACHMENT_EXTENSIONS, ".html", ".htm"):
        if path.endswith(suffix):
            return suffix if suffix != ".htm" else ".html"
    if "pdf" in content_type:
        return ".pdf"
    if "html" in content_type:
        return ".html"
    return ".bin"
