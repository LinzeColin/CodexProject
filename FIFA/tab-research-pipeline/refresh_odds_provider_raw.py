from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from tab_research.io import atomic_write_json
from tab_research.odds_provider_adapter import (
    DEFAULT_PROVIDER_SCOPE,
    ODDS_PROVIDER_BLOCKED_LATEST,
    ODDS_PROVIDER_COVERAGE_LATEST,
    ODDS_PROVIDER_RAW_LATEST,
    OddsProviderError,
    adapt_provider_payloads,
    build_opticodds_requests,
    build_provider_coverage,
    build_the_odds_api_event_markets_requests,
    build_the_odds_api_event_odds_requests,
    build_the_odds_api_requests,
    default_the_odds_api_markets,
    event_market_probe_plan,
    fetch_the_odds_api_sports,
    fetch_provider_requests,
    historical_market_covered_event_ids,
    load_manual_verification,
    merge_historical_provider_raws,
    normalize_the_odds_api_sports_config,
    provider_refresh_id,
    provider_event_descriptors,
    publish_verified_provider_raw,
    resolve_target_board_ids,
    resolve_the_odds_api_sports_from_catalog,
    split_env_list,
    write_provider_staging_bundle,
)
from tab_research.provider_alternate_plan import (
    PROVIDER_ALTERNATE_PLAN_JSON_LATEST,
    write_provider_alternate_plan_bundle,
)
from tab_research.provider_kpi import (
    PROVIDER_KPI_JSON_LATEST,
    write_provider_kpi_bundle,
)
from tab_research.paths import resolve_output_dir


def parse_args() -> argparse.Namespace:
    load_local_env_files(default_env_files([]))
    parser = argparse.ArgumentParser(
        description=(
            "Refresh TAB-labeled FIFA odds through authorized third-party providers. "
            "This does not control TAB, does not click odds, and does not publish formal raw unless manual TAB verification passes."
        )
    )
    parser.add_argument("--provider", choices=["the_odds_api", "opticodds", "both"], default="both")
    parser.add_argument("--output-dir", type=Path, default=resolve_output_dir(Path(__file__)))
    parser.add_argument("--input-json", action="append", type=Path, help="Use provider payload JSON from disk instead of live API.")
    parser.add_argument("--scope", choices=["matches", "futures", "all"], default=os.environ.get("TAB_FIFA_PROVIDER_SCOPE", DEFAULT_PROVIDER_SCOPE))
    parser.add_argument("--include-region-markets", action="store_true", help="Include region-specific boards such as Australia Markets. Default is ignored.")
    parser.add_argument("--env-file", action="append", type=Path, help="Optional local env file. Real keys must not be committed.")
    parser.add_argument("--refresh-id", default="")
    parser.add_argument("--publish-verified", action="store_true", help="Publish staged provider raw into formal raw snapshots after manual verification.")
    parser.add_argument("--verification-file", type=Path, help="Manual TAB final verification JSON.")
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument(
        "--event-market-probe-limit",
        type=int,
        default=int(os.environ.get("TAB_FIFA_THE_ODDS_API_EVENT_MARKET_PROBE_LIMIT", "0") or 0),
        help="Credit-aware probe count for The Odds API event markets. Default 0 to avoid surprise credit use.",
    )
    parser.add_argument(
        "--event-odds-limit",
        type=int,
        default=int(os.environ.get("TAB_FIFA_THE_ODDS_API_EVENT_ODDS_LIMIT", "3") or 3),
        help="Maximum event-odds requests after market probing finds target alternate markets.",
    )
    parser.add_argument(
        "--event-odds-markets",
        default=os.environ.get(
            "TAB_FIFA_THE_ODDS_API_EVENT_ODDS_MARKETS",
            "alternate_totals,alternate_spreads,btts,double_chance,draw_no_bet",
        ),
        help="Comma-separated event-level markets to fetch only when event-market probe shows TAB availability.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_local_env_files(default_env_files(args.env_file))
    if args.scope == DEFAULT_PROVIDER_SCOPE and os.environ.get("TAB_FIFA_PROVIDER_SCOPE"):
        args.scope = os.environ["TAB_FIFA_PROVIDER_SCOPE"]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    refresh_id = args.refresh_id or provider_refresh_id()
    ignore_region_markets = not args.include_region_markets
    target_board_ids = resolve_target_board_ids(args.scope, ignore_region_markets=ignore_region_markets)
    try:
        provider_payloads = load_input_payloads(args.input_json) if args.input_json else fetch_live_payloads(args)
        generated_at = latest_fetched_at(provider_payloads)
        raws = adapt_provider_payloads(
            provider_payloads,
            refresh_id=refresh_id,
            generated_at=generated_at,
            target_board_ids=target_board_ids,
        )
        raws = merge_historical_provider_raws(
            raws,
            output_dir,
            current_refresh_id=refresh_id,
            market_keys=historical_merge_market_keys(args),
        )
        manifest = write_provider_staging_bundle(
            output_dir,
            raws,
            refresh_id=refresh_id,
            generated_at=generated_at,
            scope=args.scope,
            target_board_ids=target_board_ids,
            ignore_region_markets=ignore_region_markets,
            provider_payloads=provider_payloads,
        )
        verification = load_manual_verification(args.verification_file)
        coverage = build_provider_coverage(output_dir, manifest, verification=verification)
        alternate_plan = write_provider_alternate_plan_bundle(output_dir, provider_payloads=provider_payloads)
        provider_kpi = write_provider_kpi_bundle(output_dir)
        result = {
            "ok": True,
            "mode": "provider_raw_staged",
            "refresh_id": refresh_id,
            "scope": args.scope,
            "target_board_ids": target_board_ids,
            "provider_payload_count": len(provider_payloads),
            "staged_artifact_count": manifest.get("artifact_count", 0),
            "formal_publish_allowed": coverage.get("formal_publish_allowed", False),
            "full_automation_allowed": coverage.get("full_automation_allowed", False),
            "current_executable_new_stake_aud": 0,
            "manifest": ODDS_PROVIDER_RAW_LATEST,
            "coverage": ODDS_PROVIDER_COVERAGE_LATEST,
            "alternate_plan": PROVIDER_ALTERNATE_PLAN_JSON_LATEST,
            "alternate_plan_status": alternate_plan.get("status", ""),
            "alternate_probe_queue_count": alternate_plan.get("probe_queue_count", 0),
            "provider_kpi": PROVIDER_KPI_JSON_LATEST,
            "provider_kpi_refresh_id": provider_kpi.get("refresh_id", ""),
            "provider_kpi_status": (provider_kpi.get("executive_status") or {}).get("status", ""),
            "provider_kpi_primary_gap": (provider_kpi.get("executive_status") or {}).get("primary_gap", ""),
        }
        if args.publish_verified:
            result["publish"] = publish_verified_provider_raw(output_dir, coverage)
            result["mode"] = "provider_raw_published_verified"
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except OddsProviderError as exc:
        payload = write_blocked_provider_payload(
            output_dir,
            provider=args.provider,
            refresh_id=refresh_id,
            scope=args.scope,
            target_board_ids=target_board_ids,
            error=str(exc),
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2


def load_input_payloads(paths: list[Path]) -> list[dict]:
    payloads = []
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict) and {"provider", "payload"} <= set(data):
            payloads.append(data)
        else:
            provider = provider_from_path(path)
            payloads.append({"provider": provider, "fetched_at": "", "request_url": str(path), "payload": data})
    return payloads


def provider_from_path(path: Path) -> str:
    name = path.name.lower()
    if "optic" in name:
        return "opticodds"
    return "the_odds_api"


def fetch_live_payloads(args: argparse.Namespace) -> list[dict]:
    requests = []
    provider_payloads: list[dict] = []
    if args.provider in {"the_odds_api", "both"}:
        api_key = os.environ.get("THE_ODDS_API_KEY", "")
        markets_env = os.environ.get("TAB_FIFA_THE_ODDS_API_MARKETS")
        match_markets_env = os.environ.get("TAB_FIFA_THE_ODDS_API_MATCH_MARKETS")
        markets = split_env_list(markets_env or match_markets_env, [])
        extra_markets = split_env_list(os.environ.get("TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS"), [])
        requested_sports = split_env_list(os.environ.get("TAB_FIFA_THE_ODDS_API_SPORTS"), [])
        sports = normalize_the_odds_api_sports_config(requested_sports, args.scope)
        if os.environ.get("TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY", "1").strip().lower() not in {"0", "false", "no"}:
            catalog = fetch_the_odds_api_sports(api_key=api_key, timeout_seconds=args.timeout_seconds)
            sports = resolve_the_odds_api_sports_from_catalog(catalog, requested_sports=requested_sports, scope=args.scope)
            if not sports:
                raise OddsProviderError(
                    "the_odds_api has no active FIFA World Cup sport for the requested scope. "
                    "Provider refresh blocked fail-closed; check /v4/sports coverage before spending odds credits."
                )
        requests.extend(
            build_the_odds_api_requests(
                api_key=api_key,
                sports=sports,
                markets=markets,
                scope=args.scope,
                extra_markets=extra_markets,
            )
        )
        primary_payloads = fetch_provider_requests(requests, timeout_seconds=args.timeout_seconds)
        provider_payloads.extend(primary_payloads)
        provider_payloads.extend(fetch_the_odds_api_event_level_payloads(args, api_key, sports, primary_payloads))
        requests = []
    if args.provider in {"opticodds", "both"}:
        requests.extend(build_opticodds_requests(api_key=os.environ.get("OPTICODDS_API_KEY", "")))
    if requests:
        provider_payloads.extend(fetch_provider_requests(requests, timeout_seconds=args.timeout_seconds))
    return provider_payloads


def fetch_the_odds_api_event_level_payloads(
    args: argparse.Namespace,
    api_key: str,
    sports: list[str],
    primary_payloads: list[dict],
) -> list[dict]:
    if args.scope not in {"matches", "all"}:
        return []
    probe_limit = max(0, int(args.event_market_probe_limit or 0))
    if probe_limit <= 0:
        return []
    sport = sports[0] if sports else ""
    if not sport:
        return []
    target_markets = split_env_list(args.event_odds_markets, [])
    descriptors = select_event_descriptors_for_event_level_probe(
        output_dir=Path(args.output_dir),
        primary_payloads=primary_payloads,
        sport=sport,
        target_markets=target_markets,
        probe_limit=probe_limit,
    )
    event_ids = [item["event_id"] for item in descriptors[:probe_limit]]
    if not event_ids:
        return []
    event_market_requests = build_the_odds_api_event_markets_requests(
        api_key=api_key,
        sport=sport,
        event_ids=event_ids,
        scope=args.scope,
    )
    event_market_payloads = fetch_provider_requests(
        event_market_requests,
        timeout_seconds=args.timeout_seconds,
        fail_fast=False,
    )
    plan = event_market_probe_plan(
        event_market_payloads,
        target_markets=target_markets,
        max_event_odds_requests=max(0, int(args.event_odds_limit or 0)),
    )
    if not plan:
        return event_market_payloads
    event_odds_requests = build_the_odds_api_event_odds_requests(
        api_key=api_key,
        sport=sport,
        event_market_plan=plan,
        scope=args.scope,
    )
    event_odds_payloads = fetch_provider_requests(
        event_odds_requests,
        timeout_seconds=args.timeout_seconds,
        fail_fast=False,
    )
    return [*event_market_payloads, *event_odds_payloads]


def select_event_descriptors_for_event_level_probe(
    *,
    output_dir: Path,
    primary_payloads: list[dict],
    sport: str,
    target_markets: list[str],
    probe_limit: int,
) -> list[dict]:
    if probe_limit <= 0:
        return []
    output_dir = Path(output_dir)
    historical_covered = historical_market_covered_event_ids(output_dir, target_markets)
    previous_event_odds = previous_event_odds_event_ids(output_dir)
    previous_event_probes = previous_event_market_probe_event_ids(output_dir)
    descriptors = [
        item
        for item in provider_event_descriptors(primary_payloads)
        if item.get("sport_key") == sport and item.get("event_id") not in historical_covered
    ]
    by_event_id = {str(item.get("event_id") or ""): item for item in descriptors if str(item.get("event_id") or "")}
    selected: list[dict] = []
    selected_ids: set[str] = set()
    for event_id in planned_event_probe_ids(output_dir, target_markets):
        if len(selected) >= probe_limit:
            break
        if event_id in selected_ids or event_id in historical_covered or event_id in previous_event_probes:
            continue
        item = by_event_id.get(event_id)
        if not item:
            continue
        selected.append(item)
        selected_ids.add(event_id)
    if len(selected) >= probe_limit:
        return selected
    for item in descriptors:
        event_id = str(item.get("event_id") or "")
        if not event_id or event_id in selected_ids or event_id in previous_event_odds or event_id in previous_event_probes:
            continue
        selected.append(item)
        selected_ids.add(event_id)
        if len(selected) >= probe_limit:
            break
    return selected


def planned_event_probe_ids(output_dir: Path, target_markets: list[str]) -> list[str]:
    plan_path = Path(output_dir) / PROVIDER_ALTERNATE_PLAN_JSON_LATEST
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    target = {item.strip() for item in target_markets if str(item or "").strip()}
    event_ids: list[str] = []
    for row in plan.get("next_probe_queue") or []:
        if not isinstance(row, dict):
            continue
        recommended = {str(item).strip() for item in row.get("recommended_markets") or [] if str(item or "").strip()}
        if target and recommended and not target.intersection(recommended):
            continue
        event_id = str(row.get("event_id") or "").strip()
        if event_id and event_id not in event_ids:
            event_ids.append(event_id)
    return event_ids


def previous_event_market_probe_event_ids(output_dir: Path) -> set[str]:
    event_ids: set[str] = set()
    for evidence in provider_evidence_payloads(output_dir):
        event_ids.update(str(item) for item in evidence.get("probed_event_ids") or [] if str(item or "").strip())
    return event_ids


def previous_event_odds_event_ids(output_dir: Path) -> set[str]:
    event_ids: set[str] = set()
    for evidence in provider_evidence_payloads(output_dir):
        event_ids.update(str(item) for item in evidence.get("event_odds_event_ids") or [] if str(item or "").strip())
    return event_ids


def provider_evidence_payloads(output_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for name in ["provider_alternate_probe_evidence_latest.json", PROVIDER_ALTERNATE_PLAN_JSON_LATEST]:
        path = Path(output_dir) / name
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        evidence = payload.get("event_probe_evidence") if isinstance(payload.get("event_probe_evidence"), dict) else payload
        if isinstance(evidence, dict):
            rows.append(evidence)
    return rows


def historical_merge_market_keys(args: argparse.Namespace) -> list[str]:
    markets_env = os.environ.get("TAB_FIFA_THE_ODDS_API_MARKETS")
    match_markets_env = os.environ.get("TAB_FIFA_THE_ODDS_API_MATCH_MARKETS")
    primary_markets = split_env_list(markets_env or match_markets_env, [])
    if not primary_markets:
        primary_markets = default_the_odds_api_markets(args.scope)
    extra_markets = split_env_list(os.environ.get("TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS"), [])
    event_markets = split_env_list(args.event_odds_markets, [])
    merged = []
    for market in [*primary_markets, *extra_markets, *event_markets]:
        if market and market not in merged:
            merged.append(market)
    return merged


def default_env_files(extra_files: list[Path] | None) -> list[Path]:
    base = Path(__file__).resolve().parent
    files = [
        base / "config" / "odds_providers.local.env",
        base / ".env",
        base / "config" / "odds_providers.local.env.example",
    ]
    files.extend(extra_files or [])
    return files


def load_local_env_files(paths: list[Path]) -> list[str]:
    loaded = []
    for path in paths:
        path = Path(path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not should_load_env_value(value):
                continue
            if key and key not in os.environ:
                os.environ[key] = value
        loaded.append(str(path))
    return loaded


def should_load_env_value(value: str) -> bool:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return False
    return not normalized.startswith("replace_with")


def latest_fetched_at(payloads: list[dict]) -> str:
    fetched = [str(item.get("fetched_at") or "") for item in payloads if item.get("fetched_at")]
    return max(fetched) if fetched else datetime.now(timezone.utc).isoformat()


def write_blocked_provider_payload(
    output_dir: Path,
    *,
    provider: str,
    refresh_id: str,
    scope: str,
    target_board_ids: list[str],
    error: str,
) -> dict:
    coverage_path = Path(output_dir) / ODDS_PROVIDER_COVERAGE_LATEST
    has_last_good = has_last_good_provider_coverage(coverage_path)
    payload = {
        "ok": False,
        "mode": "provider_raw_blocked",
        "provider": provider,
        "refresh_id": refresh_id,
        "scope": scope,
        "target_board_ids": target_board_ids,
        "error": error,
        "blocker_code": provider_blocker_code(provider, error),
        "diagnostics": provider_blocked_diagnostics(provider, error),
        "last_good_coverage_preserved": has_last_good,
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "next_safe_action": provider_blocked_next_safe_action(provider, error),
    }
    atomic_write_json(Path(output_dir) / ODDS_PROVIDER_BLOCKED_LATEST, payload)
    if not has_last_good:
        atomic_write_json(coverage_path, payload)
    return payload


def has_last_good_provider_coverage(path: Path) -> bool:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("targets")) and data.get("mode") != "provider_raw_blocked"


def provider_blocker_code(provider: str, error: str) -> str:
    text = f"{provider} {error}".lower()
    if "opticodds" in text and ("1010" in text or "access denied" in text or "cloudflare" in text):
        return "opticodds_access_denied_1010"
    if "key missing" in text or "_api_key missing" in text:
        return "provider_key_missing"
    if "unknown sport" in text:
        return "provider_unknown_sport"
    return "provider_refresh_failed"


def provider_blocked_next_safe_action(provider: str, error: str) -> str:
    blocker = provider_blocker_code(provider, error)
    if blocker == "opticodds_access_denied_1010":
        return (
            "OpticOdds live API 当前被 Cloudflare 1010 阻断；不要绕过 browser signature。"
            "改用 OpticOdds 官方允许的服务端/API 访问方式或让 provider 白名单本机环境；"
            "在此之前保留 The Odds API Total O/U 小批量补齐，并把 Team Total 维持为 OpticOdds/TAB 人工校验 fallback。"
        )
    if blocker == "provider_key_missing":
        return (
            "在本机未入库 env 文件或 shell 环境中配置 THE_ODDS_API_KEY 或 OPTICODDS_API_KEY 后重试；"
            "未取得授权 API 数据和 TAB 人工最终校验前，不发布正式 raw，不生成新增下注金额。"
        )
    return "保留 last-good provider coverage；检查 provider endpoint/query、账户权限、rate limit 与返回 schema 后再重试。"


def provider_blocked_diagnostics(provider: str, error: str) -> dict:
    blocker = provider_blocker_code(provider, error)
    if blocker == "provider_unknown_sport":
        return {
            "category": "the_odds_api_sport_coverage_or_env_mismatch",
            "meaning": "The Odds API /odds 端拒绝当前 sport key；可能是 shell 环境覆盖、本机 env 未加载、provider coverage 短暂不一致，或账号当前不可用。",
            "safe_checks": [
                "确认 TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY=1。",
                "先运行 provider config doctor，不消耗 odds credits。",
                "用 /v4/sports discovery 确认 soccer_fifa_world_cup 是否 active 后再请求 odds。",
                "不要在 Unknown sport 状态下开启 team_totals 或 event market probe。",
            ],
            "credit_policy": "先稳定 matches 主盘口 h2h/totals/spreads；Team Total 继续走官方 API 覆盖确认或 TAB 人工 hash gate。",
        }
    if blocker == "provider_key_missing":
        return {
            "category": "local_env_or_shell_key_missing",
            "meaning": "脚本没有读取到可用 API key；占位值 replace_with... 会被忽略。",
            "safe_checks": [
                "优先使用 ignored 的 config/odds_providers.local.env。",
                "如果不能改文件名，也可临时把真实 key 放在 config/odds_providers.local.env.example，但提交前必须通过 secret scan。",
                "也可用 --env-file 指定任意本机 env 文件。",
            ],
        }
    return {
        "category": blocker,
        "meaning": "provider refresh 未取得可发布 raw；系统已 fail-closed。",
        "safe_checks": [
            "保留 last-good coverage。",
            "检查 endpoint/query、账户权限、rate limit、返回 schema。",
            "未完成 TAB final verification 前 current_executable_new_stake_aud 必须保持 0。",
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
