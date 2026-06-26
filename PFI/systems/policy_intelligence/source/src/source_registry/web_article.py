from __future__ import annotations

import re
import ssl
import time
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ArticleExtraction:
    status: str
    title: str = ""
    text: str = ""
    content_type: str = ""
    fetched_url: str = ""


BLOCKED_MARKERS = (
    "验证码",
    "安全验证",
    "登录后查看",
    "请登录",
    "付费阅读",
    "会员专享",
    "access denied",
    "captcha",
    "robot check",
    "verify you are human",
)

SKIP_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "form",
    "nav",
    "header",
    "footer",
    "aside",
    "iframe",
}

TEXT_TAGS = {
    "article",
    "section",
    "main",
    "p",
    "li",
    "h1",
    "h2",
    "h3",
    "blockquote",
}


def fetch_public_article(
    url: str,
    timeout: int = 20,
    allow_insecure_tls: bool = False,
    retries: int = 1,
    max_bytes: int = 2_000_000,
) -> ArticleExtraction:
    return _fetch_public_article_inner(
        url,
        timeout=timeout,
        allow_insecure_tls=allow_insecure_tls,
        retries=retries,
        max_bytes=max_bytes,
        redirect_depth=0,
    )


def _fetch_public_article_inner(
    url: str,
    timeout: int,
    allow_insecure_tls: bool,
    retries: int,
    max_bytes: int,
    redirect_depth: int,
) -> ArticleExtraction:
    url = _prefer_https_for_known_hosts(url)
    if not _is_http_url(url):
        return ArticleExtraction(status="article_fetch_skipped:unsupported_url")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    request = Request(url, headers=headers)
    body = b""
    content_type = ""
    fetched_url = url
    for attempt in range(max(1, retries + 1)):
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                content_type = str(response.headers.get("Content-Type") or "")
                fetched_url = response.geturl() or url
                body = response.read(max_bytes)
            break
        except Exception as exc:
            if attempt >= retries:
                return ArticleExtraction(status=f"article_fetch_failed:{type(exc).__name__}")
            time.sleep(min(2.0, 0.4 * (attempt + 1)))
    if "html" not in content_type.lower() and not _looks_like_html(body):
        return ArticleExtraction(
            status="article_fetch_skipped:non_html",
            content_type=content_type,
            fetched_url=fetched_url,
        )
    html_text = body.decode(_charset(content_type) or "utf-8", "replace")
    client_redirect = _client_redirect_url(html_text, fetched_url)
    if redirect_depth < 2 and client_redirect and client_redirect != fetched_url:
        return _fetch_public_article_inner(
            client_redirect,
            timeout=timeout,
            allow_insecure_tls=allow_insecure_tls,
            retries=retries,
            max_bytes=max_bytes,
            redirect_depth=redirect_depth + 1,
        )
    return extract_article_text(html_text, content_type=content_type, fetched_url=fetched_url)


def extract_article_text(
    html_text: str,
    content_type: str = "",
    fetched_url: str = "",
    max_chars: int = 2400,
) -> ArticleExtraction:
    compact = _clean_text(html_text)
    if _blocked_status(compact):
        return ArticleExtraction(
            status=_blocked_status(compact),
            content_type=content_type,
            fetched_url=fetched_url,
        )
    parser = _ArticleParser()
    try:
        parser.feed(html_text)
    except Exception:
        pass
    text = _clean_text(" ".join(parser.parts))
    if len(text) < 80:
        fallback = _text_from_body(html_text)
        text = _clean_text(fallback)
    if _blocked_status(text):
        return ArticleExtraction(
            status=_blocked_status(text),
            title=parser.title,
            content_type=content_type,
            fetched_url=fetched_url,
        )
    if len(text) < 80:
        return ArticleExtraction(
            status="article_excerpt_too_short",
            title=parser.title,
            text=text[:max_chars],
            content_type=content_type,
            fetched_url=fetched_url,
        )
    return ArticleExtraction(
        status="article_excerpt_extracted",
        title=parser.title,
        text=text[:max_chars],
        content_type=content_type,
        fetched_url=fetched_url,
    )


class _ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self.title = ""
        self._skip_depth = 0
        self._text_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        if tag in TEXT_TAGS:
            self._text_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag in TEXT_TAGS and self._text_depth:
            self._text_depth -= 1
        if tag == "title":
            self._in_title = False
            self.title = _clean_text(" ".join(self.title_parts))[:160]

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        if self._text_depth:
            clean = _clean_text(data)
            if clean:
                self.parts.append(clean)


def _text_from_body(value: str) -> str:
    text = re.sub(r"(?is)<(script|style|noscript|svg|canvas|form|nav|header|footer|aside).*?</\1>", " ", value)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    return unescape(text)


def _clean_text(value: str) -> str:
    text = unescape(value or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _blocked_status(text: str) -> str:
    lower = text.lower()
    for marker in BLOCKED_MARKERS:
        if marker.lower() in lower:
            if marker in {"付费阅读", "会员专享"}:
                return "article_fetch_blocked:paywall"
            if marker.lower() in {"验证码", "安全验证", "captcha", "robot check", "verify you are human"}:
                return "article_fetch_blocked:captcha"
            return "article_fetch_blocked:login_required"
    return ""


def _charset(content_type: str) -> str:
    match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
    return match.group(1) if match else ""


def _looks_like_html(body: bytes) -> bool:
    sample = body[:300].lower()
    return b"<html" in sample or b"<!doctype html" in sample or b"<body" in sample


def _is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _client_redirect_url(html_text: str, base_url: str) -> str:
    patterns = (
        r"window\.location\.(?:replace|assign)\(\s*['\"]([^'\"]+)['\"]\s*\)",
        r"location\.href\s*=\s*['\"]([^'\"]+)['\"]",
        r"<meta[^>]+http-equiv=['\"]?refresh['\"]?[^>]+content=['\"][^'\"]*url=([^'\"]+)['\"]",
        r"<meta[^>]+content=['\"][^'\"]*url=([^'\"]+)['\"][^>]+http-equiv=['\"]?refresh['\"]?",
    )
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.I)
        if not match:
            continue
        target = unescape(match.group(1)).strip().strip("'\" ")
        resolved = _prefer_https_for_known_hosts(urljoin(base_url, target))
        if _is_http_url(resolved):
            return resolved
    return ""


def _prefer_https_for_known_hosts(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    https_preferred = ("mp.weixin.qq.com",)
    if parsed.scheme == "http" and host in https_preferred:
        return "https://" + parsed.netloc + parsed.path + (("?" + parsed.query) if parsed.query else "")
    return url
