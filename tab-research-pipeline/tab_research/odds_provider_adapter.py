from __future__ import annotations

import hashlib
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .boards import BOARD_CONFIGS, BoardConfig
from .io import atomic_copy, atomic_write_json
from .pipeline import CORE_MAIN_MARKETS
from .raw_refresh import audit_staged_raw_refresh, sha256_file, validate_raw_snapshot, write_raw_refresh_batch_manifest


THE_ODDS_API_BASE_URL = "https://api.the-odds-api.com"
OPTICODDS_BASE_URL = "https://api.opticodds.com/api/v3"

ODDS_PROVIDER_RAW_LATEST = "odds_provider_raw_latest.json"
ODDS_PROVIDER_COVERAGE_LATEST = "odds_provider_coverage_latest.json"
ODDS_PROVIDER_BLOCKED_LATEST = "odds_provider_blocked_latest.json"
ODDS_PROVIDER_DIR = "provider_raw"
TAB_FINAL_VERIFICATION_LATEST = "provider_tab_final_verification_latest.json"

DEFAULT_PROVIDER_SCOPE = "matches"
DEFAULT_THE_ODDS_API_MATCH_SPORTS = ["soccer_fifa_world_cup"]
DEFAULT_THE_ODDS_API_FUTURES_SPORTS = ["soccer_fifa_world_cup_winner"]
DEFAULT_THE_ODDS_API_SPORTS = DEFAULT_THE_ODDS_API_MATCH_SPORTS
LEGACY_THE_ODDS_API_SPORT_KEYS = {"soccer_world_cup"}
DEFAULT_THE_ODDS_API_MATCH_MARKETS = ["h2h", "totals", "spreads"]
DEFAULT_THE_ODDS_API_FUTURES_MARKETS = ["outrights"]
OPTIONAL_TEAM_TOTAL_MARKETS = ["team_totals", "alternate_team_totals"]
DEFAULT_OPTICODDS_ENDPOINT = "/fixtures/odds"
REGION_MARKET_BOARD_IDS = {"world_cup_australia_markets"}
MATCHES_BOARD_IDS = ["world_cup_matches"]
FUTURES_BOARD_IDS = ["world_cup_futures"]

BOARD_BY_ID = {board.board_id: board for board in BOARD_CONFIGS}


class OddsProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderRequest:
    provider: str
    url: str
    headers: Mapping[str, str]
    redacted_url: str
    sport_key: str = ""
    market_keys: Sequence[str] = ()
    board_scope: str = DEFAULT_PROVIDER_SCOPE
    estimated_credit_cost: int = 0
    request_kind: str = "odds"
    event_id: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def split_env_list(value: str | None, default: Sequence[str]) -> List[str]:
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def default_the_odds_api_markets(scope: str) -> List[str]:
    normalized = (scope or DEFAULT_PROVIDER_SCOPE).strip().lower()
    if normalized == "futures":
        return list(DEFAULT_THE_ODDS_API_FUTURES_MARKETS)
    if normalized == "all":
        return normalize_market_list([*DEFAULT_THE_ODDS_API_MATCH_MARKETS, *DEFAULT_THE_ODDS_API_FUTURES_MARKETS])
    return list(DEFAULT_THE_ODDS_API_MATCH_MARKETS)


def default_the_odds_api_sports(scope: str) -> List[str]:
    normalized = (scope or DEFAULT_PROVIDER_SCOPE).strip().lower()
    if normalized == "futures":
        return list(DEFAULT_THE_ODDS_API_FUTURES_SPORTS)
    if normalized == "all":
        return normalize_market_list([*DEFAULT_THE_ODDS_API_MATCH_SPORTS, *DEFAULT_THE_ODDS_API_FUTURES_SPORTS])
    return list(DEFAULT_THE_ODDS_API_MATCH_SPORTS)


def normalize_the_odds_api_sports_config(sports: Sequence[str] | None, scope: str) -> List[str]:
    requested = normalize_market_list(sports or default_the_odds_api_sports(scope))
    normalized_scope = (scope or DEFAULT_PROVIDER_SCOPE).strip().lower()
    resolved: List[str] = []
    for sport in requested:
        if sport in LEGACY_THE_ODDS_API_SPORT_KEYS:
            if normalized_scope == "futures":
                resolved.extend(DEFAULT_THE_ODDS_API_FUTURES_SPORTS)
            elif normalized_scope == "all":
                resolved.extend(default_the_odds_api_sports("all"))
            else:
                resolved.extend(DEFAULT_THE_ODDS_API_MATCH_SPORTS)
            continue
        resolved.append(sport)
    return normalize_market_list(resolved or default_the_odds_api_sports(scope))


def normalize_market_list(markets: Sequence[str]) -> List[str]:
    normalized = []
    seen = set()
    for market in markets:
        key = str(market or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append(key)
    return normalized


def resolve_target_board_ids(scope: str = DEFAULT_PROVIDER_SCOPE, *, ignore_region_markets: bool = True) -> List[str]:
    normalized = (scope or DEFAULT_PROVIDER_SCOPE).strip().lower()
    if normalized == "futures":
        targets = list(FUTURES_BOARD_IDS)
    elif normalized == "all":
        targets = [board.board_id for board in BOARD_CONFIGS if board.required_for_full_automation]
    else:
        targets = list(MATCHES_BOARD_IDS)
    if ignore_region_markets:
        targets = [board_id for board_id in targets if board_id not in REGION_MARKET_BOARD_IDS]
    return targets


def build_the_odds_api_requests(
    *,
    api_key: str,
    sports: Sequence[str] | None = None,
    markets: Sequence[str] | None = None,
    scope: str = DEFAULT_PROVIDER_SCOPE,
    extra_markets: Sequence[str] | None = None,
    event_ids: Sequence[str] | None = None,
    base_url: str = THE_ODDS_API_BASE_URL,
) -> List[ProviderRequest]:
    if not api_key:
        raise OddsProviderError("THE_ODDS_API_KEY missing; provider refresh blocked fail-closed.")
    sports = normalize_the_odds_api_sports_config(sports, scope)
    markets = normalize_market_list(markets or default_the_odds_api_markets(scope))
    markets = normalize_market_list([*markets, *(extra_markets or [])])
    requests = []
    for sport in sports:
        params = {
            "apiKey": api_key,
            "regions": "au",
            "bookmakers": "tab",
            "markets": ",".join(markets),
            "oddsFormat": "decimal",
            "dateFormat": "iso",
            "includeLinks": "false",
            "includeSids": "true",
        }
        if event_ids:
            params["eventIds"] = ",".join(event_ids)
        query = urllib.parse.urlencode(params)
        redacted = urllib.parse.urlencode({**params, "apiKey": "REDACTED"})
        requests.append(
            ProviderRequest(
                provider="the_odds_api",
                url=f"{base_url.rstrip('/')}/v4/sports/{urllib.parse.quote(sport)}/odds/?{query}",
                headers={"Accept": "application/json"},
                redacted_url=f"{base_url.rstrip('/')}/v4/sports/{urllib.parse.quote(sport)}/odds/?{redacted}",
                sport_key=sport,
                market_keys=tuple(markets),
                board_scope=scope,
                estimated_credit_cost=len(markets),
                request_kind="odds",
            )
        )
    return requests


def build_the_odds_api_event_markets_requests(
    *,
    api_key: str,
    sport: str,
    event_ids: Sequence[str],
    scope: str = DEFAULT_PROVIDER_SCOPE,
    base_url: str = THE_ODDS_API_BASE_URL,
) -> List[ProviderRequest]:
    if not api_key:
        raise OddsProviderError("THE_ODDS_API_KEY missing; provider event-market probe blocked fail-closed.")
    requests = []
    for event_id in normalize_market_list(event_ids):
        params = {
            "apiKey": api_key,
            "regions": "au",
            "bookmakers": "tab",
            "dateFormat": "iso",
        }
        query = urllib.parse.urlencode(params)
        redacted = urllib.parse.urlencode({**params, "apiKey": "REDACTED"})
        path = f"/v4/sports/{urllib.parse.quote(sport)}/events/{urllib.parse.quote(event_id)}/markets"
        requests.append(
            ProviderRequest(
                provider="the_odds_api",
                url=f"{base_url.rstrip('/')}{path}?{query}",
                headers={"Accept": "application/json"},
                redacted_url=f"{base_url.rstrip('/')}{path}?{redacted}",
                sport_key=sport,
                board_scope=scope,
                estimated_credit_cost=1,
                request_kind="event_markets",
                event_id=event_id,
            )
        )
    return requests


def build_the_odds_api_event_odds_requests(
    *,
    api_key: str,
    sport: str,
    event_market_plan: Sequence[Mapping[str, Any]],
    scope: str = DEFAULT_PROVIDER_SCOPE,
    base_url: str = THE_ODDS_API_BASE_URL,
) -> List[ProviderRequest]:
    if not api_key:
        raise OddsProviderError("THE_ODDS_API_KEY missing; provider event-odds refresh blocked fail-closed.")
    requests = []
    for plan in event_market_plan:
        event_id = str(plan.get("event_id") or "").strip()
        markets = normalize_market_list([str(item) for item in plan.get("markets") or []])
        if not event_id or not markets:
            continue
        params = {
            "apiKey": api_key,
            "regions": "au",
            "bookmakers": "tab",
            "markets": ",".join(markets),
            "oddsFormat": "decimal",
            "dateFormat": "iso",
            "includeLinks": "false",
            "includeSids": "true",
        }
        query = urllib.parse.urlencode(params)
        redacted = urllib.parse.urlencode({**params, "apiKey": "REDACTED"})
        path = f"/v4/sports/{urllib.parse.quote(sport)}/events/{urllib.parse.quote(event_id)}/odds"
        requests.append(
            ProviderRequest(
                provider="the_odds_api",
                url=f"{base_url.rstrip('/')}{path}?{query}",
                headers={"Accept": "application/json"},
                redacted_url=f"{base_url.rstrip('/')}{path}?{redacted}",
                sport_key=sport,
                market_keys=tuple(markets),
                board_scope=scope,
                estimated_credit_cost=len(markets),
                request_kind="event_odds",
                event_id=event_id,
            )
        )
    return requests


def provider_ssl_attempts() -> List[tuple[str, ssl.SSLContext | None]]:
    attempts: List[tuple[str, ssl.SSLContext | None]] = [("urllib_default_ssl", None)]
    try:
        import certifi  # type: ignore

        attempts.append(("urllib_certifi_ssl", ssl.create_default_context(cafile=certifi.where())))
    except Exception:
        pass
    return attempts


def urlopen_provider_json(
    request: urllib.request.Request,
    *,
    timeout_seconds: float,
) -> tuple[Any, Dict[str, str], str]:
    errors = []
    for ssl_mode, context in provider_ssl_attempts():
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:
                data = json.loads(response.read().decode("utf-8"))
                response_headers = {
                    key.lower(): response.headers.get(key, "")
                    for key in ("x-requests-remaining", "x-requests-used", "x-requests-last")
                }
                return data, response_headers, ssl_mode
        except urllib.error.HTTPError:
            raise
        except json.JSONDecodeError as exc:
            raise OddsProviderError(f"{ssl_mode}: JSONDecodeError: {exc}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            errors.append(f"{ssl_mode}: {type(exc).__name__}: {exc}")
    raise OddsProviderError("; ".join(errors[-3:]) or "provider request failed before response.")


def fetch_the_odds_api_sports(
    *,
    api_key: str,
    base_url: str = THE_ODDS_API_BASE_URL,
    timeout_seconds: float = 30.0,
) -> List[Dict[str, Any]]:
    if not api_key:
        raise OddsProviderError("THE_ODDS_API_KEY missing; provider refresh blocked fail-closed.")
    query = urllib.parse.urlencode({"apiKey": api_key})
    request = urllib.request.Request(f"{base_url.rstrip('/')}/v4/sports/?{query}", headers={"Accept": "application/json"})
    try:
        data, _, _transport_ssl_mode = urlopen_provider_json(request, timeout_seconds=timeout_seconds)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise OddsProviderError(f"the_odds_api sports discovery HTTP {exc.code}: {detail}") from exc
    except OddsProviderError as exc:
        raise OddsProviderError(f"the_odds_api sports discovery failed: {exc}") from exc
    if not isinstance(data, list):
        raise OddsProviderError("the_odds_api sports discovery returned a non-list payload.")
    return [item for item in data if isinstance(item, dict)]


def resolve_the_odds_api_sports_from_catalog(
    catalog: Sequence[Mapping[str, Any]],
    *,
    requested_sports: Sequence[str] | None = None,
    scope: str = DEFAULT_PROVIDER_SCOPE,
) -> List[str]:
    active_by_key = {
        str(row.get("key") or "").strip(): row
        for row in catalog
        if str(row.get("key") or "").strip() and bool(row.get("active", True))
    }
    requested = normalize_the_odds_api_sports_config(requested_sports, scope)
    valid_requested = [sport for sport in requested if sport in active_by_key]
    if valid_requested:
        return valid_requested

    normalized = (scope or DEFAULT_PROVIDER_SCOPE).strip().lower()
    preferred = default_the_odds_api_sports(normalized)
    valid_preferred = [sport for sport in preferred if sport in active_by_key]
    if valid_preferred:
        return valid_preferred

    candidates = []
    for key, row in active_by_key.items():
        haystack = " ".join(
            str(row.get(field) or "").lower()
            for field in ("key", "group", "title", "description")
        )
        is_world_cup = "soccer" in haystack and ("world cup" in haystack or "world_cup" in haystack or "fifa" in haystack)
        if not is_world_cup:
            continue
        if normalized == "matches" and "winner" in haystack:
            continue
        if normalized == "futures" and "winner" not in haystack and not bool(row.get("has_outrights")):
            continue
        candidates.append(key)
    return normalize_market_list(candidates)


def build_opticodds_requests(
    *,
    api_key: str,
    endpoint: str | None = None,
    query: str | None = None,
    base_url: str = OPTICODDS_BASE_URL,
) -> List[ProviderRequest]:
    if not api_key:
        raise OddsProviderError("OPTICODDS_API_KEY missing; provider refresh blocked fail-closed.")
    endpoint = endpoint or os.environ.get("TAB_FIFA_OPTICODDS_ENDPOINT") or DEFAULT_OPTICODDS_ENDPOINT
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    query = query if query is not None else os.environ.get("TAB_FIFA_OPTICODDS_QUERY", "sport=soccer&sportsbook=TAB")
    url = f"{base_url.rstrip('/')}{endpoint}"
    if query:
        url = f"{url}?{query}"
    return [
        ProviderRequest(
            provider="opticodds",
            url=url,
            headers={"Accept": "application/json", "x-api-key": api_key},
            redacted_url=url,
        )
    ]


def fetch_provider_requests(
    requests: Iterable[ProviderRequest],
    timeout_seconds: float = 30.0,
    *,
    fail_fast: bool = True,
) -> List[Dict]:
    payloads = []
    for request in requests:
        http_request = urllib.request.Request(request.url, headers=dict(request.headers))
        try:
            data, response_headers, transport_ssl_mode = urlopen_provider_json(http_request, timeout_seconds=timeout_seconds)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            context = provider_request_error_context(request)
            if not fail_fast:
                payloads.append(provider_error_payload(request, f"{request.provider} HTTP {exc.code}: {detail}; {context}"))
                continue
            raise OddsProviderError(f"{request.provider} HTTP {exc.code}: {detail}; {context}") from exc
        except OddsProviderError as exc:
            if not fail_fast:
                payloads.append(provider_error_payload(request, f"{request.provider} request failed: {exc}"))
                continue
            raise OddsProviderError(f"{request.provider} request failed: {exc}") from exc
        payloads.append(
            {
                "provider": request.provider,
                "fetched_at": utc_now(),
                "request_url": request.redacted_url,
                "sport_key": request.sport_key,
                "market_keys": list(request.market_keys),
                "board_scope": request.board_scope,
                "estimated_credit_cost": request.estimated_credit_cost,
                "request_kind": request.request_kind,
                "event_id": request.event_id,
                "ok": True,
                "transport_ssl_mode": transport_ssl_mode,
                "usage": provider_usage_from_headers(response_headers),
                "payload": data,
            }
        )
    return payloads


def provider_request_error_context(request: ProviderRequest) -> str:
    market_keys = ",".join(str(item) for item in request.market_keys if item)
    parts = [
        f"request_kind={request.request_kind}",
        f"sport_key={request.sport_key or 'unknown'}",
    ]
    if market_keys:
        parts.append(f"markets={market_keys}")
    if request.event_id:
        parts.append(f"event_id={request.event_id}")
    parts.append(f"redacted_url={request.redacted_url}")
    return "provider_request_context(" + "; ".join(parts) + ")"


def provider_error_payload(request: ProviderRequest, error: str) -> Dict[str, Any]:
    return {
        "provider": request.provider,
        "fetched_at": utc_now(),
        "request_url": request.redacted_url,
        "sport_key": request.sport_key,
        "market_keys": list(request.market_keys),
        "board_scope": request.board_scope,
        "estimated_credit_cost": request.estimated_credit_cost,
        "request_kind": request.request_kind,
        "event_id": request.event_id,
        "ok": False,
        "error": error,
        "usage": provider_usage_from_headers({}),
        "payload": {"error": error},
    }


def provider_usage_from_headers(headers: Mapping[str, str]) -> Dict[str, Any]:
    return {
        "requests_remaining": parse_int(headers.get("x-requests-remaining")),
        "requests_used": parse_int(headers.get("x-requests-used")),
        "requests_last": parse_int(headers.get("x-requests-last")),
    }


def parse_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def provider_events(payload: Any) -> List[Dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("events", "fixtures", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    if payload.get("bookmakers") or payload.get("odds"):
        return [payload]
    return []


def provider_event_descriptors(payloads: Sequence[Mapping[str, Any]]) -> List[Dict[str, str]]:
    descriptors: List[Dict[str, str]] = []
    seen = set()
    for provider_payload in payloads:
        if provider_payload.get("ok") is False:
            continue
        sport_key = str(provider_payload.get("sport_key") or "")
        for event in provider_events(provider_payload.get("payload")):
            event_id = str(event.get("id") or event.get("fixture_id") or "").strip()
            if not event_id:
                continue
            descriptor = {
                "event_id": event_id,
                "sport_key": str(event.get("sport_key") or sport_key),
                "match": event_match_name(event),
                "commence_time": str(event.get("commence_time") or event.get("start_date") or event.get("start_time") or ""),
            }
            key = (descriptor["sport_key"], descriptor["event_id"])
            if key in seen:
                continue
            seen.add(key)
            descriptors.append(descriptor)
    return descriptors


def provider_market_labels_for_keys(market_keys: Sequence[str]) -> List[str]:
    canonical = {canonical_market_key(str(item)) for item in market_keys if str(item or "").strip()}
    labels = []
    if "totals" in canonical:
        labels.append("Total Goals Over/Under")
    if "team_totals" in canonical or "alternate_team_totals" in canonical:
        labels.append("Team Total Goals Over/Under")
    if "spreads" in canonical:
        labels.append("Handicap")
    if "double_chance" in canonical:
        labels.append("Double Chance")
    if "h2h" in canonical:
        labels.append("Result")
    if "btts" in canonical:
        labels.append("Both Teams to Score")
    if "draw_no_bet" in canonical:
        labels.append("Draw No Bet")
    return normalize_market_list(labels)


def historical_market_covered_event_ids(output_dir: Path, market_keys: Sequence[str]) -> set[str]:
    labels = set(provider_market_labels_for_keys(market_keys))
    if not labels:
        return set()
    covered: set[str] = set()
    for _refresh_id, raw in historical_provider_matches_raws(output_dir):
        for match in raw.get("matches") or []:
            if not isinstance(match, Mapping):
                continue
            event_id = str(match.get("provider_event_id") or "").strip()
            markets = match.get("markets") or {}
            if event_id and isinstance(markets, Mapping) and all(str(markets.get(label) or "").strip() for label in labels):
                covered.add(event_id)
    return covered


def historical_provider_matches_raws(output_dir: Path, *, exclude_refresh_id: str = "") -> List[tuple[str, Dict[str, Any]]]:
    provider_dir = Path(output_dir) / ODDS_PROVIDER_DIR
    board = BOARD_BY_ID.get("world_cup_matches")
    if not board or not board.raw_snapshot or not provider_dir.exists():
        return []
    rows: List[tuple[str, Dict[str, Any]]] = []
    for path in sorted(provider_dir.glob(f"*/{board.raw_snapshot}"), reverse=True):
        refresh_id = path.parent.name
        if exclude_refresh_id and refresh_id == exclude_refresh_id:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(raw, dict):
            rows.append((refresh_id, raw))
    return rows


def merge_historical_provider_raws(
    raws: Mapping[str, Dict[str, Any]],
    output_dir: Path,
    *,
    current_refresh_id: str = "",
    market_keys: Sequence[str] | None = None,
) -> Dict[str, Dict[str, Any]]:
    merged = json.loads(json.dumps(raws))
    matches_raw = merged.get("world_cup_matches")
    if not isinstance(matches_raw, dict):
        return merged
    allowed_labels = set(provider_market_labels_for_keys(market_keys or []))
    current_matches = [item for item in matches_raw.get("matches") or [] if isinstance(item, dict)]
    by_key = {provider_match_key(match): match for match in current_matches if provider_match_key(match)}
    historical_market_count = 0
    for refresh_id, historical_raw in historical_provider_matches_raws(output_dir, exclude_refresh_id=current_refresh_id):
        for historical_match in historical_raw.get("matches") or []:
            if not isinstance(historical_match, Mapping):
                continue
            row = by_key.get(provider_match_key(historical_match))
            if not row:
                continue
            row_markets = row.setdefault("markets", {})
            historical_markets = historical_match.get("markets") or {}
            if not isinstance(row_markets, dict) or not isinstance(historical_markets, Mapping):
                continue
            imported = []
            for market_name, market_text in historical_markets.items():
                if allowed_labels and str(market_name) not in allowed_labels:
                    continue
                if str(row_markets.get(market_name) or "").strip() or not str(market_text or "").strip():
                    continue
                row_markets[str(market_name)] = market_text
                imported.append(str(market_name))
            if not imported:
                continue
            historical_market_count += len(imported)
            request_kinds = row.setdefault("provider_request_kinds", [])
            if "historical_event_odds" not in request_kinds:
                request_kinds.append("historical_event_odds")
            row["provider_historical_merge"] = True
            row.setdefault("provider_historical_sources", []).append(
                {"refresh_id": refresh_id, "markets": imported[:8]}
            )
    if historical_market_count:
        matches_raw["provider_historical_merge"] = True
        matches_raw["provider_historical_market_count"] = historical_market_count
        matches_raw["provider_historical_merge_warning"] = (
            "历史 provider event odds 仅用于研究覆盖与候选发现；正式发布和新增下注仍必须通过 TAB 人工最终校验。"
        )
        for row in current_matches:
            markets = row.get("markets") or {}
            missing = [market for market in CORE_MAIN_MARKETS if market not in markets]
            row["errors"] = [f"provider market coverage missing {market}" for market in missing]
            row["partial_core_only"] = bool(missing)
    return merged


def provider_match_key(match: Mapping[str, Any]) -> str:
    return str(match.get("provider_event_id") or match.get("match") or "").strip()


def event_market_probe_plan(
    event_market_payloads: Sequence[Mapping[str, Any]],
    *,
    target_markets: Sequence[str],
    max_event_odds_requests: int,
) -> List[Dict[str, Any]]:
    target = {canonical_market_key(str(item)) for item in target_markets if str(item or "").strip()}
    plan = []
    for provider_payload in event_market_payloads:
        if provider_payload.get("ok") is False:
            continue
        event_id = str(provider_payload.get("event_id") or "")
        sport_key = str(provider_payload.get("sport_key") or "")
        available = available_tab_market_keys(provider_payload.get("payload"))
        selected = [market for market in available if canonical_market_key(market) in target]
        if event_id and selected:
            plan.append(
                {
                    "event_id": event_id,
                    "sport_key": sport_key,
                    "available_markets": available,
                    "markets": normalize_market_list(selected),
                }
            )
        if len(plan) >= max_event_odds_requests:
            break
    return plan


def available_tab_market_keys(payload: Any) -> List[str]:
    keys: List[str] = []
    for event in provider_events(payload):
        bookmaker = tab_bookmaker(event)
        markets = bookmaker.get("markets") if isinstance(bookmaker, Mapping) else []
        if not isinstance(markets, list):
            continue
        for market in markets:
            if not isinstance(market, Mapping):
                continue
            key = str(market.get("key") or market.get("market") or market.get("name") or "").strip()
            if key:
                keys.append(key)
    return normalize_market_list(keys)


def tab_bookmaker(event: Mapping[str, Any]) -> Dict | None:
    bookmakers = event.get("bookmakers")
    if isinstance(bookmakers, list):
        exact = [item for item in bookmakers if is_tab_bookmaker(item)]
        return exact[0] if exact else None
    odds_rows = event.get("odds")
    if isinstance(odds_rows, list):
        tab_rows = [row for row in odds_rows if is_tab_bookmaker(row)]
        if tab_rows:
            return {"key": "tab", "title": "TAB", "markets": market_rows_from_flat_odds(tab_rows)}
    return None


def is_tab_bookmaker(row: Mapping[str, Any] | Any) -> bool:
    if not isinstance(row, Mapping):
        return False
    key = str(row.get("key") or row.get("sportsbook") or row.get("sportsbook_id") or "").strip().lower()
    title = str(row.get("title") or row.get("sportsbook_name") or row.get("name") or "").strip().lower()
    return key == "tab" or title == "tab"


def market_rows_from_flat_odds(rows: List[Mapping[str, Any]]) -> List[Dict]:
    grouped: Dict[str, List[Dict]] = {}
    last_update = ""
    for row in rows:
        market_key = str(row.get("market") or row.get("market_key") or row.get("market_id") or "").strip()
        if not market_key:
            continue
        outcome = str(row.get("selection") or row.get("name") or row.get("outcome") or "").strip()
        price = parse_price(row.get("price") or row.get("odds") or row.get("decimal"))
        point = row.get("point") or row.get("line")
        if not outcome or price is None:
            continue
        grouped.setdefault(market_key, []).append({"name": outcome, "price": price, "point": point})
        last_update = str(row.get("last_update") or row.get("timestamp") or last_update)
    return [{"key": key, "last_update": last_update, "outcomes": outcomes} for key, outcomes in grouped.items()]


def event_match_name(event: Mapping[str, Any]) -> str:
    home = (
        event.get("home_team")
        or event.get("home_team_display")
        or event.get("home")
        or nested_team_name(event.get("home_competitors"))
    )
    away = (
        event.get("away_team")
        or event.get("away_team_display")
        or event.get("away")
        or nested_team_name(event.get("away_competitors"))
    )
    if home and away:
        return f"{normalize_team_name(str(home))} v {normalize_team_name(str(away))}"
    name = event.get("name") or event.get("fixture_name") or event.get("title") or ""
    return normalize_fixture_name(str(name))


def nested_team_name(value: Any) -> str:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, Mapping):
            return str(first.get("name") or first.get("display") or "")
    return ""


def normalize_team_name(value: str) -> str:
    aliases = {
        "United States": "USA",
        "Bosnia Herzegovina": "Bosnia-Herzegovina",
        "Bosn-Herzegovina": "Bosnia-Herzegovina",
        "Korea Republic": "South Korea",
        "Congo DR": "DR Congo",
    }
    return aliases.get(value.strip(), value.strip())


def normalize_fixture_name(value: str) -> str:
    text = " ".join(value.replace("@", " v ").replace(" vs ", " v ").split())
    if " v " in text:
        left, right = text.split(" v ", 1)
        return f"{normalize_team_name(left)} v {normalize_team_name(right)}"
    return text


def market_map_from_bookmaker(bookmaker: Mapping[str, Any]) -> Dict[str, str]:
    markets = bookmaker.get("markets") if isinstance(bookmaker, Mapping) else []
    mapped: Dict[str, str] = {}
    if not isinstance(markets, list):
        return mapped
    for market in markets:
        if not isinstance(market, Mapping):
            continue
        key = canonical_market_key(str(market.get("key") or market.get("market") or market.get("name") or ""))
        outcomes = [item for item in market.get("outcomes", []) if isinstance(item, Mapping)]
        if key == "h2h":
            mapped["Result"] = result_market_text(outcomes)
        elif key == "double_chance":
            mapped["Double Chance"] = generic_market_text("Double Chance", outcomes)
        elif key == "spreads":
            mapped["Handicap"] = generic_market_text("Handicap", outcomes, include_point=True)
        elif key == "totals":
            mapped["Total Goals Over/Under"] = generic_market_text("Total Goals Over/Under", outcomes, include_point=True)
        elif key in {"team_totals", "alternate_team_totals"}:
            mapped["Team Total Goals Over/Under"] = generic_market_text(
                "Team Total Goals Over/Under",
                outcomes,
                include_point=True,
            )
        elif key == "btts":
            mapped["Both Teams to Score"] = generic_market_text("Both Teams to Score", outcomes)
        elif key == "draw_no_bet":
            mapped["Draw No Bet"] = generic_market_text("Draw No Bet", outcomes)
    return {key: value for key, value in mapped.items() if value.strip()}


def canonical_market_key(value: str) -> str:
    text = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "head_to_head": "h2h",
        "moneyline": "h2h",
        "match_winner": "h2h",
        "winner": "h2h",
        "h2h_3_way": "h2h",
        "3_way_result": "h2h",
        "total": "totals",
        "alternate_total": "totals",
        "alternate_totals": "totals",
        "over_under": "totals",
        "handicap": "spreads",
        "spread": "spreads",
        "alternate_spread": "spreads",
        "alternate_spreads": "spreads",
        "team_total": "team_totals",
        "team_totals": "team_totals",
        "team_total_score": "team_totals",
        "team_total_goals": "team_totals",
        "team_total_over_under": "team_totals",
        "alternate_team_total": "alternate_team_totals",
        "alternate_team_totals": "alternate_team_totals",
        "both_teams_to_score": "btts",
        "both_teams_score": "btts",
        "btts_yes_no": "btts",
        "double_chance": "double_chance",
        "dnb": "draw_no_bet",
        "draw_no_bet": "draw_no_bet",
    }
    return aliases.get(text, text)


def result_market_text(outcomes: List[Mapping[str, Any]]) -> str:
    ordered = sorted(outcomes, key=result_sort_key)
    return generic_market_text("Result", ordered)


def result_sort_key(outcome: Mapping[str, Any]) -> int:
    name = str(outcome.get("name") or "").strip().lower()
    if name == "draw":
        return 1
    return 0 if outcome.get("home") is True else 2 if outcome.get("away") is True else 0


def generic_market_text(label: str, outcomes: List[Mapping[str, Any]], include_point: bool = False) -> str:
    lines = [label]
    for outcome in outcomes:
        raw_name = str(outcome.get("name") or outcome.get("selection") or "").strip()
        price = parse_price(outcome.get("price") or outcome.get("odds") or outcome.get("decimal"))
        if not raw_name or price is None:
            continue
        point = outcome.get("point")
        description = str(
            outcome.get("description")
            or outcome.get("team")
            or outcome.get("team_name")
            or outcome.get("participant")
            or ""
        ).strip()
        name = format_outcome_name(label, raw_name, point, include_point=include_point, description=description)
        lines.extend([name, f"{price:.2f}"])
    return "\n".join(lines) + "\n" if len(lines) > 1 else ""


def format_outcome_name(label: str, name: str, point: Any, *, include_point: bool, description: str = "") -> str:
    if label == "Total Goals Over/Under" and point not in (None, ""):
        side = name.strip().title()
        if side in {"Over", "Under"}:
            return f"{side} {point} Goals"
    if label == "Team Total Goals Over/Under" and point not in (None, ""):
        side = name.strip().title()
        if side in {"Over", "Under"}:
            team_prefix = f"{normalize_team_name(description)} " if description else ""
            return f"{team_prefix}{side} {point} Goals".strip()
    if include_point and point not in (None, "") and str(point) not in name:
        return f"{name} {point}"
    return name


def parse_price(value: Any) -> float | None:
    if value is None:
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if price > 1.0 else None


def adapt_matches_raw(payloads: List[Dict], *, refresh_id: str, generated_at: str) -> Dict:
    merged: Dict[str, Dict[str, Any]] = {}
    for provider_payload in payloads:
        if provider_payload.get("ok") is False or provider_payload.get("request_kind") == "event_markets":
            continue
        provider = provider_payload.get("provider", "unknown")
        for event in provider_events(provider_payload.get("payload")):
            match_name = event_match_name(event)
            bookmaker = tab_bookmaker(event)
            if not match_name or not bookmaker:
                continue
            markets = market_map_from_bookmaker(bookmaker)
            if not markets:
                continue
            event_id = str(event.get("id") or event.get("fixture_id") or "")
            key = event_id or match_name
            row = merged.setdefault(
                key,
                {
                    "match": match_name,
                    "provider": provider,
                    "provider_event_id": event_id,
                    "commence_time": event.get("commence_time") or event.get("start_date") or event.get("start_time") or "",
                    "bookmaker": "TAB",
                    "last_update": "",
                    "markets": {},
                    "provider_request_kinds": [],
                },
            )
            row["markets"].update(markets)
            request_kind = str(provider_payload.get("request_kind") or "odds")
            if request_kind not in row["provider_request_kinds"]:
                row["provider_request_kinds"].append(request_kind)
            row["last_update"] = bookmaker.get("last_update") or row.get("last_update") or ""
    matches = []
    for row in merged.values():
        missing = [market for market in CORE_MAIN_MARKETS if market not in row["markets"]]
        row["errors"] = [f"provider market coverage missing {market}" for market in missing]
        row["partial_core_only"] = bool(missing)
        matches.append(row)
    target_matches = [row["match"] for row in matches]
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "captured_at": generated_at,
        "refresh_id": refresh_id,
        "source": "authorized_odds_provider",
        "source_mode": "third_party_tab_labeled_api",
        "board": "2026 World Cup Matches",
        "target_source": "authorized_odds_provider",
        "target_matches": target_matches,
        "matches": matches,
    }


def adapt_futures_raw(payloads: List[Dict], *, refresh_id: str, generated_at: str) -> Dict | None:
    outcomes = []
    for provider_payload in payloads:
        for event in provider_events(provider_payload.get("payload")):
            bookmaker = tab_bookmaker(event)
            if not bookmaker:
                continue
            for market in bookmaker.get("markets") or []:
                if not isinstance(market, Mapping) or canonical_market_key(str(market.get("key") or "")) != "outrights":
                    continue
                for outcome in market.get("outcomes") or []:
                    if not isinstance(outcome, Mapping):
                        continue
                    name = str(outcome.get("name") or "").strip()
                    price = parse_price(outcome.get("price"))
                    if name and price is not None:
                        outcomes.append((normalize_team_name(name), price))
    if not outcomes:
        return None
    lines = [
        "Home",
        "Soccer",
        "2026 World Cup Futures",
        "2026 World Cup",
        "2026 World Cup Winner",
    ]
    seen = set()
    for name, price in outcomes:
        if name in seen:
            continue
        seen.add(name)
        lines.extend([name, f"{price:.2f}"])
    lines.extend(["Show All Selections", "Top Goal Scorer", "Language:"])
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "captured_at": generated_at,
        "refresh_id": refresh_id,
        "source": "authorized_odds_provider",
        "source_mode": "third_party_tab_labeled_api",
        "board": "2026 World Cup Futures",
        "text": "\n".join(lines),
    }


def adapt_provider_payloads(
    payloads: List[Dict],
    *,
    refresh_id: str,
    generated_at: str | None = None,
    target_board_ids: Sequence[str] | None = None,
) -> Dict[str, Dict]:
    generated_at = generated_at or utc_now()
    target_board_ids = list(target_board_ids or MATCHES_BOARD_IDS)
    raws: Dict[str, Dict] = {}
    if "world_cup_matches" in target_board_ids:
        matches = adapt_matches_raw(payloads, refresh_id=refresh_id, generated_at=generated_at)
        if matches["matches"]:
            raws["world_cup_matches"] = matches
    if "world_cup_futures" in target_board_ids:
        futures = adapt_futures_raw(payloads, refresh_id=refresh_id, generated_at=generated_at)
        if futures:
            raws["world_cup_futures"] = futures
    return raws


def write_provider_staging_bundle(
    output_dir: Path,
    raws: Mapping[str, Dict],
    *,
    refresh_id: str,
    generated_at: str,
    scope: str = DEFAULT_PROVIDER_SCOPE,
    target_board_ids: Sequence[str] | None = None,
    ignore_region_markets: bool = True,
    provider_payloads: Sequence[Mapping[str, Any]] | None = None,
) -> Dict:
    output_dir = Path(output_dir)
    staging_dir = output_dir / ODDS_PROVIDER_DIR / refresh_id
    staging_dir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for board_id, raw in raws.items():
        board = BOARD_BY_ID.get(board_id)
        if not board or not board.raw_snapshot:
            continue
        path = staging_dir / board.raw_snapshot
        atomic_write_json(path, raw)
        artifacts.append(
            {
                "board_id": board_id,
                "name": board.name,
                "raw_snapshot": board.raw_snapshot,
                "provider_staged_path": str(Path(ODDS_PROVIDER_DIR) / refresh_id / board.raw_snapshot),
                "sha256": sha256_file(path),
                "event_count": provider_event_count(raw),
                "market_coverage": provider_market_coverage(raw),
            }
        )
    manifest = {
        "schema_version": 1,
        "generated_at": generated_at,
        "refresh_id": refresh_id,
        "scope": scope,
        "source_mode": "third_party_tab_labeled_api",
        "target_board_ids": list(target_board_ids or raws.keys()),
        "ignored_board_ids": sorted(REGION_MARKET_BOARD_IDS) if ignore_region_markets else [],
        "region_markets_ignored": bool(ignore_region_markets),
        "request_usage": provider_request_usage(provider_payloads or []),
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "manual_tab_verification_required": True,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    atomic_write_json(staging_dir / ODDS_PROVIDER_RAW_LATEST, manifest)
    atomic_write_json(output_dir / ODDS_PROVIDER_RAW_LATEST, manifest)
    return manifest


def provider_request_usage(payloads: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    estimated = sum(int(item.get("estimated_credit_cost") or 0) for item in payloads)
    last_costs = [to_int((item.get("usage") or {}).get("requests_last")) for item in payloads]
    used_values = [to_int((item.get("usage") or {}).get("requests_used")) for item in payloads]
    remaining_values = [to_int((item.get("usage") or {}).get("requests_remaining")) for item in payloads]
    request_kind_counts: Dict[str, int] = {}
    for item in payloads:
        kind = str(item.get("request_kind") or "odds")
        request_kind_counts[kind] = request_kind_counts.get(kind, 0) + 1
    return {
        "provider_payload_count": len(payloads),
        "provider_error_count": sum(1 for item in payloads if item.get("ok") is False),
        "request_kind_counts": request_kind_counts,
        "estimated_credit_cost": estimated,
        "reported_last_request_cost": sum(value for value in last_costs if value is not None),
        "reported_requests_used_max": max([value for value in used_values if value is not None], default=None),
        "reported_requests_remaining_min": min([value for value in remaining_values if value is not None], default=None),
        "sports": sorted({str(item.get("sport_key") or "") for item in payloads if item.get("sport_key")}),
        "markets": sorted({market for item in payloads for market in item.get("market_keys", []) if market}),
    }


def to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_provider_coverage(
    output_dir: Path,
    manifest: Mapping[str, Any],
    *,
    verification: Mapping[str, Any] | None = None,
) -> Dict:
    output_dir = Path(output_dir)
    refresh_id = str(manifest.get("refresh_id") or "")
    artifacts = [item for item in manifest.get("artifacts") or [] if isinstance(item, Mapping)]
    verified = verified_artifact_keys(verification, refresh_id=refresh_id)
    rows = []
    for artifact in artifacts:
        board_id = str(artifact.get("board_id") or "")
        board = BOARD_BY_ID.get(board_id)
        staged_path = output_dir / str(artifact.get("provider_staged_path") or "")
        raw = json.loads(staged_path.read_text()) if staged_path.exists() else None
        validation = validate_raw_snapshot(board_id, raw) if raw else {"valid": False, "errors": ["provider staged raw missing"]}
        provider_validation = validate_provider_analysis_snapshot(board_id, raw)
        sha = artifact.get("sha256")
        approved = (board_id, sha) in verified
        rows.append(
            {
                "board_id": board_id,
                "name": board.name if board else board_id,
                "raw_snapshot": artifact.get("raw_snapshot", ""),
                "provider_staged_path": artifact.get("provider_staged_path", ""),
                "sha256": sha,
                "raw_valid": bool(validation["valid"]),
                "validation_errors": validation["errors"],
                "provider_analysis_ready": bool(provider_validation["valid"]),
                "provider_analysis_errors": provider_validation["errors"],
                "provider_analysis_warnings": provider_validation.get("warnings", []),
                "provider_analysis_coverage": provider_validation.get("coverage", {}),
                "event_count": provider_event_count(raw),
                "market_coverage": provider_market_coverage(raw),
                "tab_manual_verified": approved,
                "formal_publish_ready": bool(validation["valid"] and approved),
            }
        )
    target_ids = {str(item) for item in manifest.get("target_board_ids") or [] if item}
    if not target_ids:
        target_ids = {board.board_id for board in BOARD_CONFIGS if board.required_for_full_automation}
    ignored_ids = {str(item) for item in manifest.get("ignored_board_ids") or [] if item}
    full_required_ids = {board.board_id for board in BOARD_CONFIGS if board.required_for_full_automation} - ignored_ids
    staged_ids = {row["board_id"] for row in rows}
    ready_ids = {row["board_id"] for row in rows if row["formal_publish_ready"]}
    analysis_ready_ids = {row["board_id"] for row in rows if row["provider_analysis_ready"]}
    missing_ids = sorted(target_ids - staged_ids)
    coverage = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "refresh_id": refresh_id,
        "scope": manifest.get("scope", DEFAULT_PROVIDER_SCOPE),
        "source_mode": "third_party_tab_labeled_api",
        "target_board_ids": sorted(target_ids),
        "ignored_board_ids": sorted(ignored_ids),
        "region_markets_ignored": bool(manifest.get("region_markets_ignored", False)),
        "request_usage": manifest.get("request_usage", {}),
        "required_target_count": len(target_ids),
        "staged_required_target_count": len(staged_ids & target_ids),
        "provider_analysis_ready_target_count": len(analysis_ready_ids & target_ids),
        "formal_publish_ready_target_count": len(ready_ids & target_ids),
        "formal_publish_allowed": ready_ids >= target_ids and bool(target_ids),
        "full_automation_allowed": ready_ids >= full_required_ids and bool(full_required_ids),
        "full_automation_required_target_count": len(full_required_ids),
        "full_automation_ready_target_count": len(ready_ids & full_required_ids),
        "current_executable_new_stake_aud": 0,
        "manual_tab_verification_required": True,
        "manual_tab_verification_status": "verified" if ready_ids >= target_ids and target_ids else "pending",
        "missing_required_boards": missing_ids,
        "targets": rows,
        "blocking_reasons": provider_blocking_reasons(rows, missing_ids),
        "next_safe_action": (
            "优先刷新 Matches 主盘口；只对进入推荐下注候选的 Result、Total O/U、Team Total O/U 做 TAB 页面人工最终校验，"
            "校验 hash 匹配后才允许发布对应 raw。未验证前新增执行金额保持 AUD 0。"
        ),
    }
    atomic_write_json(output_dir / ODDS_PROVIDER_COVERAGE_LATEST, coverage)
    return coverage


def validate_provider_analysis_snapshot(board_id: str, raw: Dict | None) -> Dict:
    if raw is None:
        return {"valid": False, "errors": ["provider staged raw missing"], "warnings": [], "coverage": {}}
    if board_id != "world_cup_matches":
        validation = validate_raw_snapshot(board_id, raw)
        return {"valid": bool(validation.get("valid")), "errors": validation.get("errors", []), "warnings": [], "coverage": {}}
    matches = [item for item in raw.get("matches", []) if isinstance(item, Mapping)]
    detail_count = len(matches)
    result_count = sum(1 for item in matches if market_text_has_price(item, "Result"))
    handicap_count = sum(1 for item in matches if market_text_has_price(item, "Handicap"))
    total_count = sum(1 for item in matches if market_text_has_price(item, "Total Goals Over/Under"))
    team_total_count = sum(1 for item in matches if market_text_has_price(item, "Team Total Goals Over/Under"))
    errors = []
    warnings = []
    if detail_count <= 0:
        errors.append("no TAB-labeled matches staged from provider")
    minimum_result_count = max(1, int(detail_count * 0.9)) if detail_count else 1
    if result_count < minimum_result_count:
        errors.append(f"Result market coverage {result_count}/{detail_count} below 90% provider analysis threshold")
    if total_count <= 0 and team_total_count <= 0:
        warnings.append("Total O/U and Team Total O/U are not returned by the current TAB-labeled provider payload")
    if max(total_count, team_total_count, handicap_count) <= 0:
        errors.append("no secondary market family returned by provider staging")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "coverage": {
            "match_count": detail_count,
            "result_market_count": result_count,
            "handicap_market_count": handicap_count,
            "total_ou_market_count": total_count,
            "team_total_ou_market_count": team_total_count,
            "primary_market_focus": ["Result", "Total Goals Over/Under", "Team Total Goals Over/Under"],
            "secondary_market_available": (
                "Total Goals Over/Under"
                if total_count > 0
                else "Team Total Goals Over/Under"
                if team_total_count > 0
                else "Handicap"
                if handicap_count > 0
                else ""
            ),
        },
    }


def provider_event_count(raw: Mapping[str, Any] | None) -> int:
    if not isinstance(raw, Mapping):
        return 0
    if isinstance(raw.get("matches"), list):
        return len(raw.get("matches") or [])
    if isinstance(raw.get("teams"), list):
        return len(raw.get("teams") or [])
    if isinstance(raw.get("outcomes"), list):
        return len(raw.get("outcomes") or [])
    return 0


def provider_market_coverage(raw: Mapping[str, Any] | None) -> Dict[str, int]:
    coverage: Dict[str, int] = {}
    if not isinstance(raw, Mapping):
        return coverage
    for match in raw.get("matches") or []:
        if not isinstance(match, Mapping):
            continue
        markets = match.get("markets")
        if not isinstance(markets, Mapping):
            continue
        for market_name, text in markets.items():
            if str(text or "").strip():
                coverage[str(market_name)] = coverage.get(str(market_name), 0) + 1
    return coverage


def market_text_has_price(match: Mapping[str, Any], market_name: str) -> bool:
    text = str((match.get("markets") or {}).get(market_name) or "")
    return any(parse_price(line.strip()) is not None for line in text.splitlines())


def provider_blocking_reasons(rows: List[Dict], missing_ids: List[str]) -> List[str]:
    reasons = []
    for board_id in missing_ids:
        board = BOARD_BY_ID.get(board_id)
        reasons.append(f"{board.name if board else board_id} provider raw is missing.")
    for row in rows:
        if row.get("provider_analysis_ready"):
            for warning in row.get("provider_analysis_warnings") or []:
                reasons.append(f"{row['name']} provider analysis warning: {warning}")
        else:
            reasons.extend(f"{row['name']} provider analysis failed: {error}" for error in row.get("provider_analysis_errors") or [])
        if not row.get("raw_valid") and row.get("provider_analysis_ready"):
            reasons.append(
                f"{row['name']} primary-market provider analysis is ready, but strict formal raw publish is still blocked."
            )
        elif not row.get("raw_valid"):
            reasons.extend(f"{row['name']} provider validation failed: {error}" for error in row.get("validation_errors") or [])
        if row.get("raw_valid") and not row.get("tab_manual_verified"):
            reasons.append(f"{row['name']} provider raw requires TAB manual final verification.")
    return reasons


def verified_artifact_keys(verification: Mapping[str, Any] | None, *, refresh_id: str) -> set[tuple[str, str]]:
    if not verification or verification.get("refresh_id") != refresh_id:
        return set()
    approved = set()
    for item in verification.get("approvals") or []:
        if not isinstance(item, Mapping) or item.get("approved_by_user") is not True:
            continue
        board_id = str(item.get("board_id") or "")
        sha = str(item.get("sha256") or "")
        if board_id and sha:
            approved.add((board_id, sha))
    return approved


def load_manual_verification(path: Path | None) -> Dict:
    if not path:
        return {}
    path = Path(path)
    if not path.exists():
        raise OddsProviderError(f"TAB manual verification file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def publish_verified_provider_raw(output_dir: Path, coverage: Mapping[str, Any]) -> Dict:
    if not coverage.get("formal_publish_allowed"):
        raise OddsProviderError("provider raw is not formally publishable; coverage/manual verification gate is blocked.")
    output_dir = Path(output_dir)
    refresh_id = str(coverage.get("refresh_id") or "")
    published = []
    for target in coverage.get("targets") or []:
        if not target.get("formal_publish_ready"):
            continue
        source = output_dir / str(target.get("provider_staged_path") or "")
        destination = output_dir / str(target.get("raw_snapshot") or "")
        if not source.exists():
            raise OddsProviderError(f"verified provider raw missing from staging: {source}")
        atomic_copy(source, destination)
        published.append(str(target.get("raw_snapshot") or ""))
    batch_manifest = None
    staged_gate: Dict[str, Any] = {
        "staged_raw_ready": False,
        "scope": coverage.get("scope", DEFAULT_PROVIDER_SCOPE),
        "reason": "scope publish only; full raw batch manifest requires all full-automation boards",
    }
    if coverage.get("full_automation_allowed"):
        batch_manifest = write_raw_refresh_batch_manifest(output_dir, refresh_id, generated_at=utc_now())
        staged_gate = audit_staged_raw_refresh(output_dir, expected_refresh_id=refresh_id)
    result = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "refresh_id": refresh_id,
        "scope": coverage.get("scope", DEFAULT_PROVIDER_SCOPE),
        "published_count": len(published),
        "published_raw_snapshots": published,
        "batch_manifest": str(batch_manifest) if batch_manifest else "",
        "raw_gate_ready": bool(staged_gate.get("staged_raw_ready")),
        "full_automation_allowed": bool(coverage.get("full_automation_allowed")),
        "current_executable_new_stake_aud": 0,
        "raw_gate": staged_gate,
    }
    atomic_write_json(output_dir / "odds_provider_publish_latest.json", result)
    return result


def provider_refresh_id(prefix: str = "provider") -> str:
    digest = hashlib.sha1(utc_now().encode("utf-8")).hexdigest()[:8]
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{prefix}-{digest}"
