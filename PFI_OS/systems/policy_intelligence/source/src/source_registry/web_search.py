from __future__ import annotations

import json
import os
import ssl
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    published_at: str | None = None
    raw: Mapping[str, Any] | None = None


def collect_search_results(
    provider: str,
    query: str,
    max_results: int,
    timeout: int,
    allow_insecure_tls: bool = False,
    secrets_file: str | Path | None = None,
    retries: int = 1,
) -> tuple[list[SearchResult], str]:
    key = _api_key(provider, secrets_file)
    if not key:
        return [], f"missing_api_key:{provider}"
    provider = provider.lower()
    try:
        if provider == "serpapi":
            return _serpapi(query, key, max_results, timeout, allow_insecure_tls, retries), "ok"
        if provider == "bing":
            return _bing(query, key, max_results, timeout, allow_insecure_tls, retries), "ok"
        if provider == "google":
            engine = _secret_value("GOOGLE_CSE_ID", secrets_file)
            if not engine:
                return [], "missing_google_cse_id"
            return _google_cse(query, key, engine, max_results, timeout, allow_insecure_tls, retries), "ok"
    except Exception as exc:
        return [], f"request_failed:{provider}:{type(exc).__name__}"
    return [], f"unsupported_provider:{provider}"


def search_provider_status(secrets_file: str | Path | None = None) -> list[dict[str, Any]]:
    providers = [
        {
            "provider": "serpapi",
            "required": ["SERPAPI_API_KEY"],
            "key_present": bool(_api_key("serpapi", secrets_file)),
            "engine_present": True,
        },
        {
            "provider": "bing",
            "required": ["BING_SEARCH_API_KEY"],
            "key_present": bool(_api_key("bing", secrets_file)),
            "engine_present": True,
        },
        {
            "provider": "google",
            "required": ["GOOGLE_SEARCH_API_KEY", "GOOGLE_CSE_ID"],
            "key_present": bool(_api_key("google", secrets_file)),
            "engine_present": bool(_secret_value("GOOGLE_CSE_ID", secrets_file)),
        },
    ]
    for provider in providers:
        provider["ready"] = bool(provider["key_present"] and provider["engine_present"])
        provider["status"] = "ready" if provider["ready"] else "missing_secret"
    return providers


def _api_key(provider: str, secrets_file: str | Path | None) -> str:
    provider = provider.upper()
    names = {
        "SERPAPI": ["SERPAPI_API_KEY", "SERPAPI_KEY"],
        "BING": ["BING_SEARCH_API_KEY", "AZURE_BING_SEARCH_KEY"],
        "GOOGLE": ["GOOGLE_SEARCH_API_KEY", "GOOGLE_API_KEY"],
    }.get(provider, [f"{provider}_API_KEY"])
    for name in names:
        value = _secret_value(name, secrets_file)
        if value:
            return value
    return ""


def _secret_value(name: str, secrets_file: str | Path | None) -> str:
    value = os.environ.get(name)
    if value:
        return value.strip()
    if not secrets_file:
        return ""
    path = Path(secrets_file).expanduser()
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _dotenv_value(path, name)
    raw = payload.get(name)
    return str(raw).strip() if raw else ""


def _dotenv_value(path: Path, name: str) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return ""


def _serpapi(
    query: str,
    api_key: str,
    max_results: int,
    timeout: int,
    allow_insecure_tls: bool,
    retries: int,
) -> list[SearchResult]:
    params = urlencode(
        {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": max_results,
            "hl": "zh-cn",
        }
    )
    payload = _fetch_json(f"https://serpapi.com/search.json?{params}", {}, timeout, allow_insecure_tls, retries)
    results = []
    for raw in (payload.get("organic_results") or [])[:max_results]:
        link = str(raw.get("link") or "")
        title = str(raw.get("title") or "")
        if not link or not title:
            continue
        results.append(
            SearchResult(
                title=title,
                url=link,
                snippet=str(raw.get("snippet") or ""),
                source=str(raw.get("source") or ""),
                raw=raw,
            )
        )
    return results


def _bing(
    query: str,
    api_key: str,
    max_results: int,
    timeout: int,
    allow_insecure_tls: bool,
    retries: int,
) -> list[SearchResult]:
    params = urlencode({"q": query, "count": max_results, "mkt": "zh-CN"})
    payload = _fetch_json(
        f"https://api.bing.microsoft.com/v7.0/search?{params}",
        {"Ocp-Apim-Subscription-Key": api_key},
        timeout,
        allow_insecure_tls,
        retries,
    )
    results = []
    for raw in ((payload.get("webPages") or {}).get("value") or [])[:max_results]:
        link = str(raw.get("url") or "")
        title = str(raw.get("name") or "")
        if not link or not title:
            continue
        results.append(
            SearchResult(
                title=title,
                url=link,
                snippet=str(raw.get("snippet") or ""),
                source=str(raw.get("displayUrl") or ""),
                raw=raw,
            )
        )
    return results


def _google_cse(
    query: str,
    api_key: str,
    engine_id: str,
    max_results: int,
    timeout: int,
    allow_insecure_tls: bool,
    retries: int,
) -> list[SearchResult]:
    params = urlencode({"key": api_key, "cx": engine_id, "q": query, "num": min(max_results, 10), "hl": "zh-CN"})
    payload = _fetch_json(
        f"https://www.googleapis.com/customsearch/v1?{params}",
        {},
        timeout,
        allow_insecure_tls,
        retries,
    )
    results = []
    for raw in (payload.get("items") or [])[:max_results]:
        link = str(raw.get("link") or "")
        title = str(raw.get("title") or "")
        if not link or not title:
            continue
        results.append(
            SearchResult(
                title=title,
                url=link,
                snippet=str(raw.get("snippet") or ""),
                source=str(raw.get("displayLink") or ""),
                raw=raw,
            )
        )
    return results


def _fetch_json(
    url: str,
    headers: Mapping[str, str],
    timeout: int,
    allow_insecure_tls: bool,
    retries: int,
) -> dict[str, Any]:
    merged_headers = {
        "User-Agent": "PolicyIntelligenceBot/0.1 (+local research automation)",
        "Accept": "application/json",
        **headers,
    }
    context = ssl._create_unverified_context() if allow_insecure_tls else None
    request = Request(url, headers=merged_headers)
    body = ""
    for attempt in range(max(1, retries + 1)):
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                body = response.read(2_000_000).decode("utf-8", "replace")
            break
        except Exception:
            if attempt >= retries:
                raise
            time.sleep(min(2.0, 0.4 * (attempt + 1)))
    return json.loads(body)
