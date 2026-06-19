from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from .io import atomic_write_json, atomic_write_text
from .odds_provider_adapter import (
    DEFAULT_PROVIDER_SCOPE,
    DEFAULT_THE_ODDS_API_MATCH_MARKETS,
    DEFAULT_THE_ODDS_API_MATCH_SPORTS,
    LEGACY_THE_ODDS_API_SPORT_KEYS,
    normalize_market_list,
    split_env_list,
)
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


PROVIDER_CONFIG_DOCTOR_JSON_LATEST = "provider_config_doctor_latest.json"
PROVIDER_CONFIG_DOCTOR_MD_LATEST = "provider_config_doctor_latest.md"
PROVIDER_CONFIG_DOCTOR_PDF_LATEST = "provider_config_doctor_latest.pdf"
REPORT_TZ = ZoneInfo("Australia/Sydney")
KNOWN_LEGACY_OR_INVALID_SPORT_KEYS = LEGACY_THE_ODDS_API_SPORT_KEYS
LOCAL_ENV_RELATIVE_PATH = "config/odds_providers.local.env"
LOCAL_ENV_EXAMPLE_RELATIVE_PATH = "config/odds_providers.local.env.example"


def write_provider_config_doctor_bundle(output_dir: Path, pipeline_root: Path | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    pipeline_root = Path(pipeline_root or Path(__file__).resolve().parents[1])
    payload = build_provider_config_doctor(pipeline_root)
    json_path = output_dir / PROVIDER_CONFIG_DOCTOR_JSON_LATEST
    md_path = output_dir / PROVIDER_CONFIG_DOCTOR_MD_LATEST
    pdf_path = output_dir / PROVIDER_CONFIG_DOCTOR_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_provider_config_doctor_markdown(payload))
    pdf_summary = write_provider_config_doctor_pdf(payload, pdf_path)
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return payload


def build_provider_config_doctor(pipeline_root: Path, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    pipeline_root = Path(pipeline_root)
    local_env_path = pipeline_root / LOCAL_ENV_RELATIVE_PATH
    example_env_path = pipeline_root / LOCAL_ENV_EXAMPLE_RELATIVE_PATH
    local_env = read_env_file(local_env_path)
    example_env = read_env_file(example_env_path)
    local_env_available = local_env_path.exists() or bool(example_env)
    using_example_fallback = not local_env_path.exists() and bool(example_env)
    effective_env = {**example_env, **local_env, **dict(env or os.environ)}
    generated_at = datetime.now(REPORT_TZ).isoformat()
    scope = (effective_env.get("TAB_FIFA_PROVIDER_SCOPE") or DEFAULT_PROVIDER_SCOPE).strip() or DEFAULT_PROVIDER_SCOPE
    requested_sports = split_env_list(
        effective_env.get("TAB_FIFA_THE_ODDS_API_SPORTS"),
        DEFAULT_THE_ODDS_API_MATCH_SPORTS,
    )
    match_markets = split_env_list(
        effective_env.get("TAB_FIFA_THE_ODDS_API_MATCH_MARKETS"),
        DEFAULT_THE_ODDS_API_MATCH_MARKETS,
    )
    extra_markets = split_env_list(effective_env.get("TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS"), [])
    event_markets = split_env_list(
        effective_env.get("TAB_FIFA_THE_ODDS_API_EVENT_ODDS_MARKETS"),
        ["alternate_totals", "alternate_spreads", "btts", "double_chance", "draw_no_bet"],
    )
    sports_discovery_enabled = env_flag(effective_env.get("TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY", "1"), default=True)
    ignored_region_markets = env_flag(effective_env.get("TAB_FIFA_IGNORE_REGION_MARKETS", "1"), default=True)
    event_probe_limit = int_or_zero(effective_env.get("TAB_FIFA_THE_ODDS_API_EVENT_MARKET_PROBE_LIMIT", "0"))
    event_odds_limit = int_or_zero(effective_env.get("TAB_FIFA_THE_ODDS_API_EVENT_ODDS_LIMIT", "3"))
    legacy_sports = [sport for sport in requested_sports if sport in KNOWN_LEGACY_OR_INVALID_SPORT_KEYS]
    recommended_sports = normalize_market_list([sport for sport in requested_sports if sport not in KNOWN_LEGACY_OR_INVALID_SPORT_KEYS])
    if not recommended_sports:
        recommended_sports = list(DEFAULT_THE_ODDS_API_MATCH_SPORTS)
    issues = build_config_issues(
        local_env_exists=local_env_available,
        using_example_fallback=using_example_fallback,
        the_odds_key_present=bool(effective_env.get("THE_ODDS_API_KEY")),
        opticodds_key_present=bool(effective_env.get("OPTICODDS_API_KEY")),
        sports_discovery_enabled=sports_discovery_enabled,
        legacy_sports=legacy_sports,
        extra_markets=extra_markets,
        event_probe_limit=event_probe_limit,
    )
    status = "ready_with_warnings" if issues else "ready"
    if any(issue["severity"] == "critical" for issue in issues):
        status = "blocked"
    elif any(issue["severity"] == "high" for issue in issues):
        status = "needs_attention"
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "mode": "provider_config_doctor",
        "status": status,
        "local_env": {
            "relative_path": LOCAL_ENV_RELATIVE_PATH,
            "exists": local_env_path.exists(),
            "effective_exists": local_env_available,
            "fallback_example_relative_path": LOCAL_ENV_EXAMPLE_RELATIVE_PATH,
            "fallback_example_exists": example_env_path.exists(),
            "using_example_fallback": using_example_fallback,
            "tracked_by_git": False,
            "truthfulness_note": "本产物只输出 key 是否存在，不输出真实 API key；example fallback 可用于本机临时运行，但提交前必须 secret scan。",
        },
        "the_odds_api": {
            "api_key_present": bool(effective_env.get("THE_ODDS_API_KEY")),
            "requested_sports": requested_sports,
            "recommended_sports": recommended_sports,
            "known_invalid_or_legacy_sports": legacy_sports,
            "sports_discovery_enabled": sports_discovery_enabled,
            "match_markets": match_markets,
            "extra_match_markets": extra_markets,
            "event_market_probe_limit": event_probe_limit,
            "event_odds_limit": event_odds_limit,
            "event_odds_markets": event_markets,
            "unknown_sport_guard": "enabled" if sports_discovery_enabled else "disabled",
        },
        "opticodds": {
            "api_key_present": bool(effective_env.get("OPTICODDS_API_KEY")),
            "endpoint": effective_env.get("TAB_FIFA_OPTICODDS_ENDPOINT", "/fixtures/odds"),
            "query": effective_env.get("TAB_FIFA_OPTICODDS_QUERY", "sport=soccer&sportsbook=TAB"),
            "note": "只显示 endpoint/query；真实 key 不写入 artifact。",
        },
        "credit_policy": {
            "matches_first": True,
            "ignore_region_markets": ignored_region_markets,
            "event_market_probe_limit": event_probe_limit,
            "event_odds_limit": event_odds_limit,
            "team_total_policy": "The Odds API event odds 只补已验证可见的非 Team Total alternate/value-support markets；Team Total 走 OpticOdds 官方访问或 TAB 人工最终校验。",
        },
        "issues": issues,
        "recommended_env_patch": {
            "TAB_FIFA_THE_ODDS_API_SPORTS": ",".join(recommended_sports),
            "TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY": "1",
            "TAB_FIFA_THE_ODDS_API_MATCH_MARKETS": ",".join(match_markets or DEFAULT_THE_ODDS_API_MATCH_MARKETS),
            "TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS": "",
            "TAB_FIFA_THE_ODDS_API_EVENT_MARKET_PROBE_LIMIT": str(max(0, event_probe_limit)),
            "TAB_FIFA_THE_ODDS_API_EVENT_ODDS_MARKETS": ",".join(event_markets),
            "TAB_FIFA_IGNORE_REGION_MARKETS": "1",
        },
        "recommended_commands": build_recommended_commands(event_probe_limit=event_probe_limit),
        "formal_publish_allowed": False,
        "full_automation_allowed": False,
        "current_executable_new_stake_aud": 0,
        "safety_boundary": "该诊断只检查 provider 配置和 credit-safe 参数；不请求 odds、不登录 TAB、不点击赔率、不下注。",
    }
    payload["summary"] = {
        "status": payload["status"],
        "issue_count": len(issues),
        "critical_issue_count": sum(1 for issue in issues if issue["severity"] == "critical"),
        "legacy_sport_count": len(legacy_sports),
        "the_odds_api_key_present": payload["the_odds_api"]["api_key_present"],
        "opticodds_key_present": payload["opticodds"]["api_key_present"],
        "sports_discovery_enabled": sports_discovery_enabled,
        "next_safe_action": next_safe_action(payload),
    }
    return payload


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if is_placeholder_env_value(value):
            continue
        values[key.strip()] = value
    return values


def is_placeholder_env_value(value: str) -> bool:
    normalized = str(value or "").strip().lower()
    return not normalized or normalized.startswith("replace_with")


def env_flag(value: str | None, *, default: bool) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def int_or_zero(value: str | None) -> int:
    try:
        return max(0, int(str(value or "0").strip()))
    except ValueError:
        return 0


def build_config_issues(
    *,
    local_env_exists: bool,
    using_example_fallback: bool,
    the_odds_key_present: bool,
    opticodds_key_present: bool,
    sports_discovery_enabled: bool,
    legacy_sports: list[str],
    extra_markets: list[str],
    event_probe_limit: int,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not local_env_exists:
        issues.append(
            {
                "severity": "critical",
                "code": "provider_local_env_missing",
                "message": "缺少 config/odds_providers.local.env；live provider refresh 会 fail-closed。",
                "fix": "复制 config/odds_providers.local.env.example 到 config/odds_providers.local.env，并只在本机填写真实 key。",
            }
        )
    elif using_example_fallback:
        issues.append(
            {
                "severity": "medium",
                "code": "provider_example_env_fallback_in_use",
                "message": "当前使用 config/odds_providers.local.env.example 作为固定文件名 fallback。",
                "fix": "可以继续本机运行，但提交前必须确认该 tracked 示例文件没有真实 key；长期建议改用 ignored local env 或 shell env。",
            }
        )
    if not the_odds_key_present and not opticodds_key_present:
        issues.append(
            {
                "severity": "critical",
                "code": "provider_api_keys_missing",
                "message": "没有可用 provider API key。",
                "fix": "在 ignored local env 中配置 THE_ODDS_API_KEY 或 OPTICODDS_API_KEY。",
            }
        )
    if legacy_sports:
        issues.append(
            {
                "severity": "high" if not sports_discovery_enabled else "medium",
                "code": "the_odds_api_legacy_unknown_sport",
                "message": f"检测到可能触发 Unknown sport 的旧 sport key：{', '.join(legacy_sports)}。",
                "fix": "保留 TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY=1，并把 TAB_FIFA_THE_ODDS_API_SPORTS 收敛到 soccer_fifa_world_cup。",
            }
        )
    if not sports_discovery_enabled:
        issues.append(
            {
                "severity": "high",
                "code": "sports_discovery_disabled",
                "message": "sports discovery 被关闭，无法在 odds 请求前过滤失效 sport key。",
                "fix": "设置 TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY=1。",
            }
        )
    if extra_markets:
        issues.append(
            {
                "severity": "medium",
                "code": "extra_markets_enabled",
                "message": f"额外 match markets 已启用：{', '.join(extra_markets)}，可能浪费 credits 或触发 provider 错误。",
                "fix": "除非已验证 sport/bookmaker 支持，否则保持 TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS 为空。",
            }
        )
    if event_probe_limit > 0:
        issues.append(
            {
                "severity": "low",
                "code": "event_probe_credit_spend_enabled",
                "message": f"event-market probe limit 当前为 {event_probe_limit}，运行 provider refresh 会消耗额外 credits。",
                "fix": "日常 automation 保持 0；只在有明确补齐目标时手动开启小批量 probe。",
            }
        )
    return issues


def build_recommended_commands(*, event_probe_limit: int) -> list[dict[str, str]]:
    commands = [
        {
            "title": "安全配置检查",
            "command": "python3 scripts/build_provider_config_doctor.py",
            "why": "不请求 odds，不消耗 odds credits；只验证本机 provider 配置是否会再次触发 Unknown sport 或 credit 风险。",
        },
        {
            "title": "Matches 主盘口刷新",
            "command": "python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 0",
            "why": "只刷新 Result / Total O/U / Handicap 主盘口；不做 event-level alternate probe。",
        },
        {
            "title": "Team Total 人工下一批",
            "command": "open '/Users/linzezhang/Downloads/FIFA Report/app_assets/provider_manual_next_batch_pair_template_latest.csv'",
            "why": "Team Total 当前走人工最终校验或官方白名单路径，不用 The Odds API 盲扫。",
        },
    ]
    if event_probe_limit > 0:
        commands.append(
            {
                "title": "credit 警告",
                "command": "把 TAB_FIFA_THE_ODDS_API_EVENT_MARKET_PROBE_LIMIT 改回 0，除非正在执行小样本补齐。",
                "why": "保护每月 500 credits 额度。",
            }
        )
    return commands


def next_safe_action(payload: Mapping[str, Any]) -> str:
    summary_status = str(payload.get("status") or "")
    if summary_status == "blocked":
        return "先补齐 ignored local env 或 provider key，再运行 provider refresh。"
    if summary_status == "needs_attention":
        return "先修正 sport discovery / sport key，再运行 provider refresh，避免 Unknown sport。"
    if summary_status == "ready_with_warnings":
        return "配置可用但有警告；建议先应用 recommended_env_patch，再执行主盘口刷新。"
    return "配置可用；下一步执行 matches 主盘口刷新或 Team Total 人工下一批。"


def render_provider_config_doctor_markdown(payload: Mapping[str, Any]) -> str:
    summary = payload.get("summary") or {}
    odds = payload.get("the_odds_api") or {}
    optic = payload.get("opticodds") or {}
    lines = [
        "# Provider Config Doctor",
        "",
        f"- status: `{payload.get('status')}`",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- local_env_exists: `{(payload.get('local_env') or {}).get('exists')}`",
        f"- example_env_fallback: `{(payload.get('local_env') or {}).get('using_example_fallback')}`",
        f"- effective_env_exists: `{(payload.get('local_env') or {}).get('effective_exists')}`",
        f"- the_odds_api_key_present: `{odds.get('api_key_present')}`",
        f"- opticodds_key_present: `{optic.get('api_key_present')}`",
        f"- requested_sports: `{', '.join(odds.get('requested_sports') or [])}`",
        f"- recommended_sports: `{', '.join(odds.get('recommended_sports') or [])}`",
        f"- known_invalid_or_legacy_sports: `{', '.join(odds.get('known_invalid_or_legacy_sports') or []) or 'none'}`",
        f"- sports_discovery_enabled: `{odds.get('sports_discovery_enabled')}`",
        f"- event_market_probe_limit: `{odds.get('event_market_probe_limit')}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        f"Next safe action: {summary.get('next_safe_action', '')}",
        "",
        "## Issues",
    ]
    issues = payload.get("issues") or []
    if not issues:
        lines.append("- none")
    else:
        for issue in issues:
            lines.append(f"- `{issue.get('severity')}` `{issue.get('code')}`: {issue.get('message')} Fix: {issue.get('fix')}")
    lines.extend(["", "## Recommended Commands"])
    for row in payload.get("recommended_commands") or []:
        lines.append(f"- {row.get('title')}: `{row.get('command')}`")
    lines.extend(["", f"Safety boundary: {payload.get('safety_boundary')}"])
    return "\n".join(lines) + "\n"


def write_provider_config_doctor_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    odds = payload.get("the_odds_api") or {}
    rows = [
        [
            issue.get("severity", ""),
            issue.get("code", ""),
            issue.get("message", ""),
            issue.get("fix", ""),
        ]
        for issue in payload.get("issues") or []
    ]
    return render_sidecar_pdf(
        output_path,
        title="Provider Config Doctor",
        subtitle="API 配置、Unknown Sport 防护、credit-safe 参数诊断；不输出真实 key。",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Local Env", "exists" if (payload.get("local_env") or {}).get("effective_exists") else "missing"),
            ("Example Fallback", "yes" if (payload.get("local_env") or {}).get("using_example_fallback") else "no"),
            ("The Odds API Key", "present" if odds.get("api_key_present") else "missing"),
            ("OpticOdds Key", "present" if (payload.get("opticodds") or {}).get("api_key_present") else "missing"),
            ("Discovery", "enabled" if odds.get("sports_discovery_enabled") else "disabled"),
            ("Legacy Sports", str(summary.get("legacy_sport_count", 0))),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Config Readiness",
                [
                    ("local env", 1 if (payload.get("local_env") or {}).get("exists") else 0),
                    ("effective env", 1 if (payload.get("local_env") or {}).get("effective_exists") else 0),
                    ("odds key", 1 if odds.get("api_key_present") else 0),
                    ("optic key", 1 if (payload.get("opticodds") or {}).get("api_key_present") else 0),
                    ("discovery", 1 if odds.get("sports_discovery_enabled") else 0),
                ],
                "#1F4E79",
            ),
            chart_from_items(
                "Issues",
                [
                    ("critical", summary.get("critical_issue_count", 0)),
                    ("legacy sport", summary.get("legacy_sport_count", 0)),
                    ("all issues", summary.get("issue_count", 0)),
                ],
                "#B42318",
            ),
        ],
        table_headers=["Severity", "Code", "Issue", "Fix"],
        table_rows=rows,
    )
