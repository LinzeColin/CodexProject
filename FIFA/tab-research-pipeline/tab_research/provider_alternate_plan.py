from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from .artifacts import sanitize_public_payload
from .io import atomic_write_json, atomic_write_text
from .odds_provider_adapter import available_tab_market_keys, canonical_market_key, provider_events
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


PROVIDER_ALTERNATE_PLAN_JSON_LATEST = "provider_alternate_plan_latest.json"
PROVIDER_ALTERNATE_PLAN_MD_LATEST = "provider_alternate_plan_latest.md"
PROVIDER_ALTERNATE_PLAN_PDF_LATEST = "provider_alternate_plan_latest.pdf"
PROVIDER_ALTERNATE_EVIDENCE_JSON_LATEST = "provider_alternate_probe_evidence_latest.json"
REPORT_TZ = ZoneInfo("Australia/Sydney")
TEAM_TOTAL_LOW_YIELD_PROBE_THRESHOLD = 3
DEFAULT_PRIMARY_REFRESH_CREDIT_FLOOR = 3

TARGET_MARKET_FAMILIES = [
    {
        "id": "handicap",
        "label": "Handicap",
        "provider_markets": ["spreads", "alternate_spreads"],
        "required_ratio": 0.70,
        "role": "core_price_context",
    },
    {
        "id": "total_ou",
        "label": "Total Goals Over/Under",
        "provider_markets": ["totals", "alternate_totals"],
        "required_ratio": 0.70,
        "role": "core_price_context",
    },
    {
        "id": "btts",
        "label": "Both Teams to Score",
        "provider_markets": ["btts"],
        "required_ratio": 0.35,
        "role": "value_support",
    },
    {
        "id": "double_chance",
        "label": "Double Chance",
        "provider_markets": ["double_chance"],
        "required_ratio": 0.35,
        "role": "value_support",
    },
    {
        "id": "draw_no_bet",
        "label": "Draw No Bet",
        "provider_markets": ["draw_no_bet"],
        "required_ratio": 0.35,
        "role": "value_support",
    },
    {
        "id": "team_total_ou",
        "label": "Team Total Goals Over/Under",
        "provider_markets": ["team_totals", "alternate_team_totals"],
        "required_ratio": 0.50,
        "role": "manual_or_official_fallback",
    },
]


def write_provider_alternate_plan_bundle(
    output_dir: Path,
    *,
    provider_payloads: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    payload = build_provider_alternate_plan(output_dir, provider_payloads=provider_payloads)
    json_path = output_dir / PROVIDER_ALTERNATE_PLAN_JSON_LATEST
    md_path = output_dir / PROVIDER_ALTERNATE_PLAN_MD_LATEST
    pdf_path = output_dir / PROVIDER_ALTERNATE_PLAN_PDF_LATEST
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_provider_alternate_plan_markdown(payload))
    pdf_summary = write_provider_alternate_plan_pdf(payload, pdf_path)
    atomic_write_json(
        output_dir / PROVIDER_ALTERNATE_EVIDENCE_JSON_LATEST,
        {
            "schema_version": 1,
            "generated_at": payload.get("generated_at", ""),
            "source_refresh_id": payload.get("refresh_id", ""),
            "event_probe_evidence": payload.get("event_probe_evidence") or event_probe_evidence([]),
            "truthfulness_note": "累计 event-level provider evidence；用于防止主盘口 refresh 抹掉 Team Total 低收益证据。",
        },
    )
    payload["artifacts"] = {
        "json": json_path.name,
        "markdown": md_path.name,
        "pdf": pdf_path.name,
        "evidence": PROVIDER_ALTERNATE_EVIDENCE_JSON_LATEST,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return payload


def build_provider_alternate_plan(
    output_dir: Path,
    *,
    provider_payloads: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    coverage = load_json(output_dir / "odds_provider_coverage_latest.json")
    manifest = load_json(output_dir / "odds_provider_raw_latest.json")
    previous_plan = load_json(output_dir / PROVIDER_ALTERNATE_PLAN_JSON_LATEST)
    target = first_matches_target(coverage)
    raw = load_staged_matches_raw(output_dir, target)
    matches = [item for item in raw.get("matches") or [] if isinstance(item, Mapping)]
    event_count = int(target.get("event_count") or len(matches) or 0)
    market_coverage = target.get("market_coverage") or {}
    request_usage = coverage.get("request_usage") or manifest.get("request_usage") or {}
    refresh_id = str(coverage.get("refresh_id") or manifest.get("refresh_id") or "")
    evidence = resolve_event_probe_evidence(output_dir, provider_payloads, previous_plan)
    families = annotate_family_provider_status(market_family_gaps(event_count, market_coverage), evidence)
    queue = next_probe_queue(matches, families, evidence)
    families = mark_exhausted_provider_paths(families, queue)
    fallback_queue = fallback_probe_queue(matches, families)
    credit = credit_policy(request_usage, queue, scope=str(coverage.get("scope") or manifest.get("scope") or "matches"))
    status = plan_status(families, queue, credit)
    decision = operational_decision(families, queue, fallback_queue, credit, evidence)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(REPORT_TZ).isoformat(),
        "mode": "provider_alternate_plan",
        "status": status,
        "scope": coverage.get("scope") or manifest.get("scope") or "matches",
        "refresh_id": refresh_id,
        "event_count": event_count,
        "formal_publish_allowed": bool(coverage.get("formal_publish_allowed")),
        "full_automation_allowed": bool(coverage.get("full_automation_allowed")),
        "current_executable_new_stake_aud": 0,
        "market_family_gaps": families,
        "event_probe_evidence": evidence,
        "probe_queue_count": len(queue),
        "recommended_batch_size": int(credit.get("recommended_batch_size") or 0),
        "estimated_next_batch_credit_floor": int(credit.get("estimated_next_batch_credit_floor") or 0),
        "estimated_next_batch_credit_ceiling": int(credit.get("estimated_next_batch_credit_ceiling") or 0),
        "next_probe_queue": queue[:20],
        "fallback_queue_count": len(fallback_queue),
        "fallback_queue": fallback_queue[:20],
        "credit_policy": credit,
        "operational_decision": decision,
        "recommended_command": recommended_command(credit, queue, families),
        "recommended_next_action": recommended_next_action(families, queue, fallback_queue),
        "stop_conditions": [
            "Team Total O/U 连续小样本仍为 0 覆盖时，停止扩大 The Odds API event odds 消耗，改查 OpticOdds 或 TAB 人工最终校验。",
            "reported_remaining 低于 20% 或 provider_error_count 增加时，暂停自动 probe，只保留已缓存证据。",
            "formal publish 和 TAB 人工最终校验未通过前，current_executable_new_stake_aud 保持 AUD 0。",
        ],
        "truthfulness_note": "本计划只描述授权 provider 覆盖缺口和下一批最小 probe，不代表下注建议，也不会自动下注。",
    }
    return sanitize_public_payload(payload)


def first_matches_target(coverage: Mapping[str, Any]) -> Mapping[str, Any]:
    for row in coverage.get("targets") or []:
        if isinstance(row, Mapping) and row.get("board_id") == "world_cup_matches":
            return row
    targets = coverage.get("targets") or []
    return targets[0] if targets and isinstance(targets[0], Mapping) else {}


def resolve_event_probe_evidence(
    output_dir: Path,
    provider_payloads: Sequence[Mapping[str, Any]] | None,
    previous_plan: Mapping[str, Any],
) -> dict[str, Any]:
    stored = load_json(output_dir / PROVIDER_ALTERNATE_EVIDENCE_JSON_LATEST).get("event_probe_evidence") or {}
    previous = previous_plan.get("event_probe_evidence") if isinstance(previous_plan.get("event_probe_evidence"), Mapping) else {}
    current = event_probe_evidence(provider_payloads or [])
    return merge_event_probe_evidence(stored, previous, current)


def load_staged_matches_raw(output_dir: Path, target: Mapping[str, Any]) -> dict[str, Any]:
    staged = str(target.get("provider_staged_path") or "")
    if staged:
        path = output_dir / staged
        if path.exists():
            return load_json(path)
    return {}


def market_family_gaps(event_count: int, market_coverage: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for family in TARGET_MARKET_FAMILIES:
        count = int(market_coverage.get(family["label"]) or 0)
        ratio = count / event_count if event_count else 0.0
        required_ratio = float(family["required_ratio"])
        rows.append(
            {
                "id": family["id"],
                "label": family["label"],
                "covered_count": count,
                "event_count": event_count,
                "coverage_ratio": round(ratio, 4),
                "required_ratio": required_ratio,
                "missing_count": max(0, event_count - count),
                "status": "ready" if ratio >= required_ratio else "gap",
                "provider_markets": list(family["provider_markets"]),
                "role": family.get("role", "coverage"),
            }
        )
    return rows


def annotate_family_provider_status(
    families: Sequence[Mapping[str, Any]],
    evidence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    probe_count = int(evidence.get("market_probe_count") or 0)
    team_total_available = int(evidence.get("team_total_available_probe_count") or 0)
    annotated = []
    for family in families:
        row = dict(family)
        available_probe_count = family_available_probe_count(evidence, row.get("provider_markets") or [])
        row["available_probe_count"] = available_probe_count
        if (
            row.get("id") == "team_total_ou"
            and int(row.get("covered_count") or 0) == 0
            and probe_count >= TEAM_TOTAL_LOW_YIELD_PROBE_THRESHOLD
            and team_total_available == 0
        ):
            row["provider_status"] = "low_yield_in_current_the_odds_api_tab_sample"
            row["status"] = "fallback_required"
            row["sample_evidence"] = f"{probe_count} 个 TAB event-market 样本均未暴露 Team Total market key。"
            row["recommended_provider_action"] = (
                "停止默认扩大 The Odds API team_totals 探测；除非人工指定候选，否则切换 OpticOdds 官方访问或 TAB 人工最终校验。"
            )
        elif available_probe_count > 0:
            row["provider_status"] = "available_in_current_the_odds_api_tab_sample"
            row["sample_evidence"] = f"{available_probe_count}/{probe_count} 个 TAB event-market 样本暴露该盘口族。"
            row["recommended_provider_action"] = "可按 credit-safe 队列拉 event odds；仅补非 Team Total 的已发现 markets。"
        elif probe_count > 0:
            row["provider_status"] = "not_seen_in_current_the_odds_api_tab_sample"
            row["sample_evidence"] = f"当前 {probe_count} 个 TAB event-market 样本未暴露该盘口族。"
            row["recommended_provider_action"] = "暂停扩大该盘口族；只在候选场次或官方 provider 确认可用时再查。"
        else:
            row["provider_status"] = "available_or_unproven"
            row["recommended_provider_action"] = "继续小批量 event-market probe，并只在目标 markets 可用时拉 event odds。"
        annotated.append(row)
    return annotated


def family_available_probe_count(evidence: Mapping[str, Any], provider_markets: Sequence[str]) -> int:
    target = {canonical_market_key(str(item)) for item in provider_markets if str(item or "").strip()}
    count = 0
    for row in evidence.get("market_probes") or []:
        if not isinstance(row, Mapping):
            continue
        available = {canonical_market_key(str(item)) for item in row.get("available_markets") or []}
        if target.intersection(available):
            count += 1
    return count


def operational_decision(
    families: Sequence[Mapping[str, Any]],
    queue: Sequence[Mapping[str, Any]],
    fallback_queue: Sequence[Mapping[str, Any]],
    credit: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    team_total = next((family for family in families if family.get("id") == "team_total_ou"), {})
    total = next((family for family in families if family.get("id") == "total_ou"), {})
    if team_total.get("status") == "fallback_required" and queue:
        return {
            "status": "alternate_probe_plus_team_total_manual",
            "title": "非 Team Total 可小批量补齐，Team Total 转人工",
            "primary_action": f"先按 recommended command 小批量补 {len(queue)} 场非 Team Total alternate/value markets；Team Total 继续 TT-001 人工校验。",
            "why": (
                f"The Odds API 已完成 {int(evidence.get('market_probe_count') or 0)} 个 TAB event-market 样本，"
                f"Team Total 可用样本 {int(evidence.get('team_total_available_probe_count') or 0)}；"
                "但 BTTS/Double Chance/Draw No Bet/alternate spreads/totals 已在样本中可见。"
            ),
            "operator_next_step": "执行推荐命令时保持小批量；完成后重建 KPI。Team Total 不跟随 The Odds API 盲扫，继续 TT-001 人工只读填写。",
            "credit_guidance": (
                f"下一批建议 {int(credit.get('recommended_batch_size') or 0)} 场，预计 "
                f"{credit.get('estimated_next_batch_credit_floor')}-{credit.get('estimated_next_batch_credit_ceiling')} credits。"
            ),
            "stake_policy": "provider event odds 只增加研究覆盖；formal publish、TAB 人工最终校验和持仓 gate 未通过前，新增执行金额保持 AUD 0。",
        }
    if team_total.get("status") == "fallback_required":
        return {
            "status": "manual_or_official_provider_priority",
            "title": "Team Total 转人工/官方访问优先",
            "primary_action": "先处理 TT-001 人工校验或 OpticOdds 官方访问，不再默认扩大 The Odds API Team Total probe。",
            "why": (
                f"The Odds API 已完成 {int(evidence.get('market_probe_count') or 0)} 个 TAB event-market 样本，"
                f"Team Total 可用样本 {int(evidence.get('team_total_available_probe_count') or 0)}；"
                f"Total O/U 已覆盖 {total.get('covered_count', 0)}/{total.get('event_count', 0)}。"
            ),
            "operator_next_step": "打开 provider_manual_next_batch_pair_template_latest.csv，从 TT-001 的 8 场开始人工只读填写 Over/Under 成对赔率。",
            "credit_guidance": "保留 The Odds API 剩余额度给后续候选复核；不做 68 场盲扫。",
            "stake_policy": "formal publish、TAB 人工最终校验和持仓 gate 未通过前，新增执行金额保持 AUD 0。",
        }
    if queue:
        return {
            "status": "credit_safe_probe",
            "title": "小批量补齐可继续",
            "primary_action": f"按下一批 {int(credit.get('recommended_batch_size') or 0)} 场执行 event-market probe。",
            "why": "仍存在未证明的 alternate market 队列，且 provider credit 未低于安全阈值。",
            "operator_next_step": "只按推荐命令执行小批量；成功后重建 KPI，不要全量扫 68 场。",
            "credit_guidance": (
                f"预计下一批消耗 {credit.get('estimated_next_batch_credit_floor')}-{credit.get('estimated_next_batch_credit_ceiling')} credits。"
            ),
            "stake_policy": "provider probe 只改研究覆盖，不解锁下注金额。",
        }
    return {
        "status": "hold_and_verify",
        "title": "暂停 provider probe",
        "primary_action": "保留当前 provider cache，进入 TAB 人工最终校验和正式 publish gate。",
        "why": "没有新的 provider 队列或 credit gate 不允许继续。",
        "operator_next_step": "复核 coverage、manual verification、public snapshot 或 My Bets gate。",
        "credit_guidance": "不消耗 provider credits。",
        "stake_policy": "新增执行金额保持 AUD 0。",
    }


def mark_exhausted_provider_paths(
    families: Sequence[Mapping[str, Any]],
    queue: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    queued_missing = {
        str(label)
        for row in queue
        for label in row.get("missing_families") or []
    }
    annotated = []
    for family in families:
        row = dict(family)
        label = str(row.get("label") or "")
        missing = int(row.get("missing_count") or 0)
        if row.get("status") == "ready" and missing > 0 and label not in queued_missing:
            row["provider_status"] = "coverage_threshold_met_no_remaining_the_odds_api_queue"
            row["recommended_provider_action"] = (
                f"已达到可用阈值但仍缺 {missing} 场；The Odds API 当前没有可继续补齐的 TAB event-level 队列。"
                "保留现有覆盖，只有进入候选下注研究时才做 OpticOdds/TAB 人工最终校验。"
            )
        elif row.get("status") == "gap" and missing > 0 and label not in queued_missing:
            row["provider_status"] = "the_odds_api_queue_exhausted"
            row["status"] = "fallback_required"
            row["recommended_provider_action"] = (
                "The Odds API 当前没有可继续补齐的 TAB event-level 队列；切换 OpticOdds 官方访问或 TAB 人工最终校验。"
            )
        annotated.append(row)
    return annotated


def event_probe_evidence(provider_payloads: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    market_probes = []
    odds_fetches = []
    for payload in provider_payloads:
        kind = str(payload.get("request_kind") or "")
        if kind == "event_markets":
            available = available_tab_market_keys(payload.get("payload"))
            market_probes.append(
                {
                    "event_id": str(payload.get("event_id") or ""),
                    "sport_key": str(payload.get("sport_key") or ""),
                    "ok": payload.get("ok") is not False,
                    "available_markets": available,
                    "has_total_ou": any(canonical_market_key(item) == "totals" for item in available),
                    "has_team_total_ou": any(canonical_market_key(item) in {"team_totals", "alternate_team_totals"} for item in available),
                    "error": str(payload.get("error") or ""),
                }
            )
        elif kind == "event_odds":
            odds_fetches.append(
                {
                    "event_id": str(payload.get("event_id") or ""),
                    "sport_key": str(payload.get("sport_key") or ""),
                    "ok": payload.get("ok") is not False,
                    "requested_markets": [str(item) for item in payload.get("market_keys") or []],
                    "returned_event_count": len(provider_events(payload.get("payload"))),
                    "error": str(payload.get("error") or ""),
                }
            )
    probed_event_ids = {row["event_id"] for row in market_probes if row.get("event_id")}
    odds_event_ids = {row["event_id"] for row in odds_fetches if row.get("event_id")}
    canonical_counts: dict[str, int] = {}
    for row in market_probes:
        seen = {canonical_market_key(str(item)) for item in row.get("available_markets") or [] if str(item or "").strip()}
        for key in seen:
            canonical_counts[key] = canonical_counts.get(key, 0) + 1
    return {
        "market_probe_count": len(market_probes),
        "event_odds_count": len(odds_fetches),
        "probed_event_ids": sorted(probed_event_ids),
        "event_odds_event_ids": sorted(odds_event_ids),
        "team_total_available_probe_count": sum(1 for row in market_probes if row.get("has_team_total_ou")),
        "total_available_probe_count": sum(1 for row in market_probes if row.get("has_total_ou")),
        "canonical_available_market_counts": canonical_counts,
        "market_probes": market_probes[:20],
        "event_odds_fetches": odds_fetches[:20],
    }


def merge_event_probe_evidence(*evidences: Mapping[str, Any]) -> dict[str, Any]:
    market_probe_by_event: dict[str, dict[str, Any]] = {}
    event_odds_by_event: dict[str, dict[str, Any]] = {}
    max_market_probe_count = 0
    max_event_odds_count = 0
    max_team_total_available = 0
    max_total_available = 0
    canonical_counts: dict[str, int] = {}
    probed_event_ids: set[str] = set()
    event_odds_event_ids: set[str] = set()

    for evidence in evidences:
        if not isinstance(evidence, Mapping):
            continue
        max_market_probe_count = max(max_market_probe_count, int(evidence.get("market_probe_count") or 0))
        max_event_odds_count = max(max_event_odds_count, int(evidence.get("event_odds_count") or 0))
        max_team_total_available = max(max_team_total_available, int(evidence.get("team_total_available_probe_count") or 0))
        max_total_available = max(max_total_available, int(evidence.get("total_available_probe_count") or 0))
        for key, value in (evidence.get("canonical_available_market_counts") or {}).items():
            key = str(key)
            canonical_counts[key] = max(canonical_counts.get(key, 0), int(value or 0))
        probed_event_ids.update(str(item) for item in evidence.get("probed_event_ids") or [] if str(item or "").strip())
        event_odds_event_ids.update(str(item) for item in evidence.get("event_odds_event_ids") or [] if str(item or "").strip())
        for row in evidence.get("market_probes") or []:
            if not isinstance(row, Mapping):
                continue
            event_id = str(row.get("event_id") or "").strip()
            if not event_id:
                continue
            market_probe_by_event[event_id] = dict(row)
            probed_event_ids.add(event_id)
            for market in row.get("available_markets") or []:
                key = canonical_market_key(str(market))
                canonical_counts[key] = max(canonical_counts.get(key, 0), 1)
        for row in evidence.get("event_odds_fetches") or []:
            if not isinstance(row, Mapping):
                continue
            event_id = str(row.get("event_id") or "").strip()
            if not event_id:
                continue
            event_odds_by_event[event_id] = dict(row)
            event_odds_event_ids.add(event_id)

    market_probes = list(market_probe_by_event.values())
    event_odds_fetches = list(event_odds_by_event.values())
    merged_canonical_counts: dict[str, int] = {}
    for row in market_probes:
        seen = {canonical_market_key(str(item)) for item in row.get("available_markets") or [] if str(item or "").strip()}
        for key in seen:
            merged_canonical_counts[key] = merged_canonical_counts.get(key, 0) + 1
    for key, value in merged_canonical_counts.items():
        canonical_counts[key] = max(canonical_counts.get(key, 0), value)
    market_probe_count = max(max_market_probe_count, len(market_probes), len(probed_event_ids))
    event_odds_count = max(max_event_odds_count, len(event_odds_fetches), len(event_odds_event_ids))
    team_total_available = max(
        max_team_total_available,
        sum(1 for row in market_probes if row.get("has_team_total_ou")),
    )
    total_available = max(
        max_total_available,
        sum(1 for row in market_probes if row.get("has_total_ou")),
    )
    return {
        "market_probe_count": market_probe_count,
        "event_odds_count": event_odds_count,
        "probed_event_ids": sorted(probed_event_ids),
        "event_odds_event_ids": sorted(event_odds_event_ids),
        "team_total_available_probe_count": team_total_available,
        "total_available_probe_count": total_available,
        "canonical_available_market_counts": canonical_counts,
        "market_probes": market_probes[:20],
        "event_odds_fetches": event_odds_fetches[:20],
    }


def next_probe_queue(
    matches: Sequence[Mapping[str, Any]],
    families: Sequence[Mapping[str, Any]],
    evidence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    target_families = sorted(
        [
            family
            for family in families
            if family.get("status") not in {"ready", "fallback_required"}
            and family.get("provider_status") != "not_seen_in_current_the_odds_api_tab_sample"
        ],
        key=market_family_priority,
        reverse=True,
    )
    already_event_odds = set(evidence.get("event_odds_event_ids") or [])
    queue = []
    for match in matches:
        event_id = str(match.get("provider_event_id") or "")
        request_kinds = {str(item) for item in match.get("provider_request_kinds") or []}
        if not event_id or event_id in already_event_odds or "event_odds" in request_kinds:
            continue
        markets = match.get("markets") or {}
        missing_families = [family for family in target_families if family.get("label") not in markets]
        if not missing_families:
            continue
        recommended_markets = []
        for family in missing_families:
            recommended_markets.extend(str(item) for item in family.get("provider_markets") or [])
        queue.append(
            {
                "event_id": event_id,
                "match": str(match.get("match") or ""),
                "commence_time": str(match.get("commence_time") or ""),
                "covered_markets": sorted(str(key) for key in markets.keys()),
                "missing_families": [str(family.get("label") or "") for family in missing_families],
                "recommended_markets": unique(recommended_markets),
                "recommended_action": "先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。",
            }
        )
    return queue


def fallback_probe_queue(
    matches: Sequence[Mapping[str, Any]],
    families: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    fallback_families = [family for family in families if family.get("status") == "fallback_required"]
    if not fallback_families:
        return []
    queue = []
    for match in matches:
        markets = match.get("markets") or {}
        missing = [family for family in fallback_families if family.get("label") not in markets]
        if not missing:
            continue
        queue.append(
            {
                "event_id": str(match.get("provider_event_id") or ""),
                "match": str(match.get("match") or ""),
                "commence_time": str(match.get("commence_time") or ""),
                "missing_families": [str(family.get("label") or "") for family in missing],
                "recommended_action": "OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。",
            }
        )
    return queue


def market_family_priority(family: Mapping[str, Any]) -> float:
    required = float(family.get("required_ratio") or 0)
    current = float(family.get("coverage_ratio") or 0)
    coverage_gap = max(0.0, required - current)
    role_bonus = 0.02 if family.get("role") == "value_support" else 0.0
    scarcity_bonus = 0.01 if int(family.get("available_probe_count") or 0) < int(family.get("event_count") or 0) else 0.0
    return coverage_gap + role_bonus + scarcity_bonus


def credit_policy(request_usage: Mapping[str, Any], queue: Sequence[Mapping[str, Any]], *, scope: str = "matches") -> dict[str, Any]:
    queue_count = len(queue)
    used = to_int(request_usage.get("reported_requests_used_max"))
    remaining = to_int(request_usage.get("reported_requests_remaining_min"))
    last = to_int(request_usage.get("reported_last_request_cost"))
    monthly_limit = used + remaining if used is not None and remaining is not None else None
    ratio = remaining / monthly_limit if remaining is not None and monthly_limit else None
    primary_floor = primary_refresh_credit_floor(request_usage, scope=scope)
    if ratio is None:
        recommended_batch = min(3, queue_count)
        status = "watch"
    elif ratio >= 0.80:
        recommended_batch = min(5, queue_count)
        status = "ready"
    elif ratio >= 0.50:
        recommended_batch = min(3, queue_count)
        status = "ready"
    elif ratio >= 0.20:
        recommended_batch = min(1, queue_count)
        status = "partial"
    else:
        recommended_batch = 0
        status = "blocked"
    event_floor = recommended_batch
    event_ceiling = estimated_next_batch_credit_ceiling(queue, recommended_batch)
    total_floor = primary_floor + event_floor if recommended_batch > 0 else 0
    total_ceiling = primary_floor + event_ceiling if recommended_batch > 0 else 0
    return {
        "status": status,
        "reported_used": used,
        "reported_remaining": remaining,
        "reported_last_request_cost": last,
        "inferred_monthly_limit": monthly_limit,
        "remaining_ratio": round(ratio, 4) if ratio is not None else None,
        "recommended_batch_size": max(0, recommended_batch),
        "queue_count": queue_count,
        "primary_refresh_credit_floor": primary_floor,
        "estimated_event_probe_credit_floor": event_floor,
        "estimated_event_probe_credit_ceiling": event_ceiling,
        "estimated_next_batch_credit_floor": total_floor,
        "estimated_next_batch_credit_ceiling": total_ceiling,
    }


def primary_refresh_credit_floor(request_usage: Mapping[str, Any], *, scope: str = "matches") -> int:
    kinds = request_usage.get("request_kind_counts") if isinstance(request_usage.get("request_kind_counts"), Mapping) else {}
    if int(kinds.get("odds") or 0) <= 0:
        return 0
    markets = {str(item) for item in request_usage.get("markets") or [] if str(item or "").strip()}
    if scope in {"matches", "all"}:
        primary = {"h2h", "spreads", "totals"}
    elif scope == "futures":
        primary = {"outrights"}
    else:
        primary = set()
    observed = len(markets.intersection(primary))
    if observed:
        return observed
    return DEFAULT_PRIMARY_REFRESH_CREDIT_FLOOR if scope in {"matches", "all"} else 1


def plan_status(families: Sequence[Mapping[str, Any]], queue: Sequence[Mapping[str, Any]], credit: Mapping[str, Any]) -> str:
    if all(row.get("status") == "ready" for row in families):
        return "ready"
    if any(row.get("status") == "fallback_required" for row in families):
        non_fallback = [row for row in families if row.get("status") != "fallback_required"]
        if non_fallback and all(row.get("status") == "ready" for row in non_fallback):
            return "fallback_required"
    if not queue:
        return "blocked"
    if credit.get("status") == "blocked":
        return "blocked"
    return "in_progress"


def estimated_next_batch_credit_ceiling(queue: Sequence[Mapping[str, Any]], batch: int) -> int:
    if batch <= 0:
        return 0
    sample = queue[:batch]
    max_market_count = max([len(row.get("recommended_markets") or []) for row in sample], default=0)
    return batch * (1 + max_market_count)


def recommended_command(
    credit: Mapping[str, Any],
    queue: Sequence[Mapping[str, Any]],
    families: Sequence[Mapping[str, Any]],
) -> str:
    batch = int(credit.get("recommended_batch_size") or 0)
    if batch <= 0:
        if any(family.get("status") == "fallback_required" for family in families):
            return "暂停 The Odds API team_totals；改查 OpticOdds 或 TAB 人工最终校验候选比赛。"
        return "暂停 probe；保留现有缓存并检查 provider credit。"
    markets = unique([market for row in queue[:batch] for market in row.get("recommended_markets") or []])
    if not markets:
        markets = ["totals", "alternate_totals"]
    return (
        "python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches "
        f"--event-market-probe-limit {batch} --event-odds-limit {batch} "
        f"--event-odds-markets {','.join(markets)}"
    )


def recommended_next_action(
    families: Sequence[Mapping[str, Any]],
    queue: Sequence[Mapping[str, Any]],
    fallback_queue: Sequence[Mapping[str, Any]],
) -> str:
    if fallback_queue and any(family.get("id") == "team_total_ou" and family.get("status") == "fallback_required" for family in families):
        if not queue:
            total = next((family for family in families if family.get("id") == "total_ou"), {})
            return (
                f"The Odds API Total O/U 队列已耗尽，当前覆盖 {total.get('covered_count', 0)}/{total.get('event_count', 0)}，"
                "已达到可用阈值；Team Total 转入 OpticOdds 官方访问或 TAB 人工最终校验，不再消耗 The Odds API team_totals credits。"
            )
        return "The Odds API 当前 TAB sample 未提供 Team Total；继续用小批量 event odds 补非 Team Total 的 alternate/value-support markets，同时把 Team Total 转入 OpticOdds/TAB 人工校验。"
    if queue:
        return "继续按队列小批量 probe，不全量扫 68 场。"
    return "进入 TAB 人工最终校验和正式 publish gate 复核。"


def render_provider_alternate_plan_markdown(payload: Mapping[str, Any]) -> str:
    credit = payload.get("credit_policy") or {}
    decision = payload.get("operational_decision") or {}
    lines = [
        "# Provider Alternate Markets Plan",
        "",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- status: `{payload.get('status', '')}`",
        f"- refresh_id: `{payload.get('refresh_id', '')}`",
        f"- event_count: `{payload.get('event_count', 0)}`",
        f"- probe_queue_count: `{payload.get('probe_queue_count', 0)}`",
        f"- recommended_batch_size: `{credit.get('recommended_batch_size', 0)}`",
        f"- current_executable_new_stake_aud: `AUD {payload.get('current_executable_new_stake_aud', 0)}`",
        "",
        "## Operational Decision",
        "",
        f"- status: `{decision.get('status', '')}`",
        f"- title: {md(decision.get('title'))}",
        f"- primary_action: {md(decision.get('primary_action'))}",
        f"- why: {md(decision.get('why'))}",
        f"- operator_next_step: {md(decision.get('operator_next_step'))}",
        f"- credit_guidance: {md(decision.get('credit_guidance'))}",
        f"- stake_policy: {md(decision.get('stake_policy'))}",
        "",
        "## Market Family Gaps",
        "",
        "| Market family | Covered | Coverage | Required | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for row in payload.get("market_family_gaps") or []:
        lines.append(
            f"| {md(row.get('label'))} | {row.get('covered_count', 0)}/{row.get('event_count', 0)} | "
            f"{pct(row.get('coverage_ratio'))} | {pct(row.get('required_ratio'))} | `{row.get('status', '')}` |"
        )
    lines.extend(["", "## Next Probe Queue", "", "| Match | Missing | Markets | Action |", "|---|---|---|---|"])
    for row in payload.get("next_probe_queue") or []:
        lines.append(
            f"| {md(row.get('match'))} | {md(', '.join(row.get('missing_families') or []))} | "
            f"{md(', '.join(row.get('recommended_markets') or []))} | {md(row.get('recommended_action'))} |"
        )
    lines.extend(["", "## Fallback Queue", "", "| Match | Missing | Action |", "|---|---|---|"])
    for row in payload.get("fallback_queue") or []:
        lines.append(
            f"| {md(row.get('match'))} | {md(', '.join(row.get('missing_families') or []))} | {md(row.get('recommended_action'))} |"
        )
    lines.extend(
        [
            "",
            "## Recommended Command",
            "",
            "```bash",
            str(payload.get("recommended_command") or ""),
            "```",
            "",
            f"Truthfulness: {payload.get('truthfulness_note', '')}",
        ]
    )
    return "\n".join(lines) + "\n"


def write_provider_alternate_plan_pdf(payload: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    credit = payload.get("credit_policy") or {}
    decision = payload.get("operational_decision") or {}
    table_rows = [
        [
            str(row.get("match", "")),
            ", ".join(row.get("missing_families") or []),
            ", ".join(row.get("recommended_markets") or []),
            str(row.get("recommended_action", "")),
        ]
        for row in payload.get("next_probe_queue") or []
    ]
    return render_sidecar_pdf(
        output_path,
        title="TAB FIFA Alternate Markets Plan",
        subtitle="Credit-aware event-level probe plan for Total O/U and Team Total O/U coverage. Research only, no betting.",
        summary_rows=[
            ("Status", str(payload.get("status", ""))),
            ("Refresh", str(payload.get("refresh_id", ""))),
            ("Events", str(payload.get("event_count", 0))),
            ("Queue", str(payload.get("probe_queue_count", 0))),
            ("Fallback Queue", str(payload.get("fallback_queue_count", 0))),
            ("Recommended Batch", str(credit.get("recommended_batch_size", 0))),
            ("Decision", str(decision.get("title", ""))),
            ("Executable Stake", "AUD 0"),
        ],
        charts=[
            chart_from_items(
                "Market Family Coverage",
                [(row.get("label", ""), float(row.get("coverage_ratio") or 0) * 100) for row in payload.get("market_family_gaps") or []],
                "#1D4ED8",
            )
        ],
        table_headers=["Match", "Missing", "Markets", "Action"],
        table_rows=table_rows,
    )


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def unique(items: Sequence[str]) -> list[str]:
    out = []
    seen = set()
    for item in items:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "待校准"


def md(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")
