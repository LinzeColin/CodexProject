from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional
from urllib.parse import quote_plus

from .public_sources import fetch_url


EVENT_KEYWORDS = [
    "injury",
    "injured",
    "fitness",
    "doubt",
    "squad",
    "lineup",
    "line-up",
    "suspension",
    "suspended",
    "ruled out",
    "ankle",
    "hamstring",
]

REQUIRED_CONTEXT_TERMS = ["world cup"]
EXCLUDED_CONTEXT_TERMS = [
    "club world cup",
    "afcon",
    "uel",
    "europa league",
    "laliga",
    "la liga",
    "premier league",
    "serie a",
    "bundesliga",
    "chelsea",
    "napoli",
    "stuttgart",
]

MONITORED_TEAMS = [
    "Brazil",
    "Morocco",
    "France",
    "Senegal",
    "England",
    "Croatia",
    "Netherlands",
    "Japan",
    "Belgium",
    "Egypt",
    "South Korea",
    "Czechia",
]


@dataclass(frozen=True)
class EventItem:
    team: str
    title: str
    link: str
    source: str
    published: str
    matched_keywords: List[str]


def google_news_rss_url(team: str) -> str:
    query = quote_plus(f'"{team}" "FIFA World Cup 2026" injury OR squad OR lineup OR suspension')
    return f"https://news.google.com/rss/search?q={query}&hl=en-AU&gl=AU&ceid=AU:en"


def parse_google_news_rss(team: str, xml_text: str, limit: int = 8) -> List[EventItem]:
    root = ET.fromstring(xml_text)
    items: List[EventItem] = []
    for node in root.findall("./channel/item")[:limit]:
        title = text_of(node, "title")
        link = text_of(node, "link")
        source = text_of(node, "source")
        published = text_of(node, "pubDate")
        blob = f"{title} {source}".lower()
        if not is_relevant_event_blob(team, blob):
            continue
        matched = [keyword for keyword in EVENT_KEYWORDS if keyword in blob]
        if not matched:
            continue
        items.append(
            EventItem(
                team=team,
                title=normalize_space(title),
                link=link,
                source=source,
                published=published,
                matched_keywords=matched,
            )
        )
    return items


def is_relevant_event_blob(team: str, blob: str) -> bool:
    if team.lower() not in blob:
        return False
    if not any(term in blob for term in REQUIRED_CONTEXT_TERMS):
        return False
    if any(term in blob for term in EXCLUDED_CONTEXT_TERMS):
        return False
    return True


def text_of(node: ET.Element, tag: str) -> str:
    value = node.findtext(tag)
    return value or ""


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def audit_event_feeds(
    teams: Iterable[str] = MONITORED_TEAMS,
    fetcher: Callable[[str], tuple[int, str]] = fetch_url,
) -> Dict:
    feed_results = []
    event_items: List[EventItem] = []
    for team in teams:
        url = google_news_rss_url(team)
        try:
            status_code, body = fetcher(url)
            items = parse_google_news_rss(team, body)
            event_items.extend(items)
            feed_results.append(
                {
                    "team": team,
                    "url": url,
                    "ok": 200 <= status_code < 300,
                    "status_code": status_code,
                    "item_count": len(items),
                    "error": None,
                }
            )
        except Exception as exc:
            feed_results.append(
                {
                    "team": team,
                    "url": url,
                    "ok": False,
                    "status_code": None,
                    "item_count": 0,
                    "error": str(exc),
                }
            )
    item_dicts = [asdict(item) for item in event_items]
    flagged = [item for item in item_dicts if item["matched_keywords"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feed_count": len(feed_results),
        "ok_count": sum(1 for item in feed_results if item["ok"]),
        "all_feeds_ok": all(item["ok"] for item in feed_results),
        "event_item_count": len(item_dicts),
        "flagged_item_count": len(flagged),
        "feeds": feed_results,
        "flagged_items": flagged[:40],
    }


def load_event_audit(path: Optional[Path]) -> Optional[Dict]:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text())


def event_risk_for_match(match: str, event_audit: Optional[Dict]) -> Dict:
    if not event_audit:
        return {"flag_count": 0, "teams": [], "items": []}
    teams = [part.strip() for part in match.split(" v ")]
    items = [
        item
        for item in event_audit.get("flagged_items", [])
        if item.get("team") in teams
    ]
    return {
        "flag_count": len(items),
        "teams": sorted({item.get("team") for item in items if item.get("team")}),
        "items": items[:5],
    }
