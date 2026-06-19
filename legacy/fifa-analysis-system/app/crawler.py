import re
import ssl
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any, Dict, List, Tuple


USER_AGENT = "fifa-analysis-mvp/0.1 compliant-public-source-research"


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def _fetch(url: str, timeout: int = 15) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = None
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read()


def _robots_allowed(url: str) -> Tuple[bool, str]:
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False, "Invalid URL."
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return True, "robots.txt unavailable; proceeding only for configured public source."
    return parser.can_fetch(USER_AGENT, url), f"robots.txt checked: {robots_url}"


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", "".join(value.itertext()) if hasattr(value, "itertext") else str(value or "")).strip()


def _first_node(item: ET.Element, *paths: str) -> Any:
    for path in paths:
        node = item.find(path)
        if node is not None:
            return node
    return None


def _parse_rss(payload: bytes, source_name: str) -> List[Dict[str, str]]:
    root = ET.fromstring(payload)
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    articles: List[Dict[str, str]] = []
    for item in items[:50]:
        title_node = _first_node(item, "title", "{http://www.w3.org/2005/Atom}title")
        link_node = _first_node(item, "link", "{http://www.w3.org/2005/Atom}link")
        published_node = _first_node(
            item,
            "pubDate",
            "published",
            "updated",
            "{http://www.w3.org/2005/Atom}published",
            "{http://www.w3.org/2005/Atom}updated",
        )
        title = _text(title_node)
        link = ""
        if link_node is not None:
            link = link_node.attrib.get("href", "") or _text(link_node)
        if title:
            articles.append(
                {
                    "title": title,
                    "url": link,
                    "source": source_name,
                    "published_at": _text(published_node),
                }
            )
    return articles


def _parse_webpage(payload: bytes, url: str, source_name: str) -> List[Dict[str, str]]:
    parser = TitleParser()
    parser.feed(payload.decode("utf-8", errors="ignore"))
    title = parser.title.strip() or url
    return [{"title": title, "url": url, "source": source_name, "published_at": ""}]


def crawl_source(conn: sqlite3.Connection, source: Dict[str, Any], job_id: int) -> Dict[str, Any]:
    source_type = str(source.get("source_type") or "public").lower()
    url = str(source["base_url"])
    allowed, robots_note = _robots_allowed(url)
    conn.execute("INSERT INTO crawl_logs(job_id, level, message) VALUES (?, 'INFO', ?)", (job_id, robots_note))
    if not allowed:
        conn.execute("INSERT INTO crawl_logs(job_id, level, message) VALUES (?, 'WARN', ?)", (job_id, "Blocked by robots.txt; crawl skipped."))
        return {"status": "skipped", "inserted": 0, "summary": "Skipped because robots.txt disallows this crawler."}

    try:
        payload = _fetch(url)
        if source_type in {"rss", "atom", "feed"}:
            articles = _parse_rss(payload, str(source["name"]))
        elif source_type in {"public", "webpage", "html"}:
            articles = _parse_webpage(payload, url, str(source["name"]))
        else:
            return {"status": "skipped", "inserted": 0, "summary": f"Unsupported source_type: {source_type}"}
    except (urllib.error.URLError, TimeoutError, ET.ParseError, ValueError) as exc:
        conn.execute("INSERT INTO crawl_logs(job_id, level, message) VALUES (?, 'ERROR', ?)", (job_id, str(exc)))
        return {"status": "failed", "inserted": 0, "summary": f"Crawl failed: {exc}"}

    inserted = 0
    for article in articles:
        existing = conn.execute(
            "SELECT id FROM news_articles WHERE url = ? AND url IS NOT NULL AND url != ''",
            (article["url"],),
        ).fetchone()
        if existing:
            continue
        conn.execute(
            """
            INSERT INTO news_articles(title, url, source, sentiment, published_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (article["title"], article["url"], article["source"], article["published_at"]),
        )
        inserted += 1

    summary = f"Fetched {len(articles)} public items; inserted {inserted} new articles."
    conn.execute("INSERT INTO crawl_logs(job_id, level, message) VALUES (?, 'INFO', ?)", (job_id, summary))
    return {"status": "completed", "inserted": inserted, "summary": summary}
