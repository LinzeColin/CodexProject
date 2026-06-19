from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .boards import BOARD_CONFIGS
from .model_compare import MODEL_COMPARISON_JSON


LOCAL_REFERENCE_FILES = [
    Path("/Users/linzezhang/Downloads/2026 FIFA.xlsx"),
    Path("/Users/linzezhang/Downloads/fifa_world_cup_team_tables_1930_2022.xlsx"),
]


def build_evidence_bundle(output_dir: Path, manifest: Dict, boards: Iterable = BOARD_CONFIGS) -> Dict:
    output_dir = Path(output_dir)
    outputs = manifest.get("outputs", {})
    public_sources = load_json_ref(output_dir, outputs, "public_source_audit", "public_source_audit_v0_11.json")
    event_monitor = load_json_ref(output_dir, outputs, "event_monitor", "event_monitor_v0_11.json")
    raw_refresh = load_json_ref(output_dir, outputs, "raw_refresh_manifest", "raw_refresh_manifest_latest.json")
    preflight = load_json_ref(output_dir, outputs, "automation_preflight", "automation_preflight_latest.json")
    safety = load_json_ref(output_dir, outputs, "safety_gate", "automation_safety_gate.json")
    portfolio = load_json_ref(output_dir, outputs, "portfolio_gate", "portfolio_automation_gate_v0_12.json")
    model_comparison = load_json_ref(output_dir, outputs, "model_comparison_json", MODEL_COMPARISON_JSON)
    source_logs = build_source_logs(public_sources, event_monitor, model_comparison)
    source_logs.extend(local_reference_source_logs())
    audit_logs = build_audit_logs(raw_refresh, preflight, safety, portfolio)
    decision_records = build_decision_records(output_dir, boards)
    missing_data_logs = build_missing_data_logs(public_sources, event_monitor, raw_refresh, preflight, safety, portfolio)
    manual_review_queue = build_manual_review_queue(missing_data_logs, decision_records, model_comparison)
    return {
        "schema_version": 1,
        "run_id": manifest.get("run_id", ""),
        "source_logs": source_logs,
        "audit_logs": audit_logs,
        "decision_records": decision_records,
        "missing_data_logs": missing_data_logs,
        "manual_review_queue": manual_review_queue,
        "summary": {
            "source_count": len(source_logs),
            "source_ok_count": sum(1 for item in source_logs if item.get("status") == "ok"),
            "audit_count": len(audit_logs),
            "audit_blocker_count": sum(1 for item in audit_logs if item.get("status") not in {"ok", "pass"}),
            "decision_count": len(decision_records),
            "buy_decision_count": sum(1 for item in decision_records if item.get("action") == "buy"),
            "missing_data_count": len(missing_data_logs),
            "manual_review_count": len(manual_review_queue),
        },
    }


def load_json_ref(output_dir: Path, outputs: Dict, key: str, fallback_name: str) -> Dict:
    value = outputs.get(key)
    if value:
        path = Path(value)
        if not path.is_absolute():
            path = output_dir / path
        payload = load_optional_json(path)
        if payload:
            return payload
    return load_optional_json(output_dir / fallback_name)


def load_optional_json(path: Path) -> Dict:
    try:
        if not path.exists():
            return {}
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def build_source_logs(public_sources: Dict, event_monitor: Dict, model_comparison: Dict) -> List[Dict]:
    rows: List[Dict] = []
    for source in public_sources.get("sources", []):
        rows.append(
            {
                "source_type": "official_public_source",
                "name": source.get("name", ""),
                "url_or_ref": source.get("url", ""),
                "usage": source.get("usage", ""),
                "status": "ok" if source.get("ok") else "blocked",
                "status_code": source.get("status_code"),
                "freshness": "fresh",
                "evidence_layer": "FACT",
                "message": "; ".join(source.get("missing_terms", [])) if source.get("missing_terms") else "source validation passed",
                "raw": source,
            }
        )
    for feed in event_monitor.get("feeds", []):
        rows.append(
            {
                "source_type": "event_news_feed",
                "name": feed.get("team", ""),
                "url_or_ref": feed.get("url", ""),
                "usage": "injury/squad/lineup/suspension monitor",
                "status": "ok" if feed.get("ok") else "blocked",
                "status_code": feed.get("status_code"),
                "freshness": "fresh",
                "evidence_layer": "OBSERVATION",
                "message": feed.get("error") or f"{feed.get('item_count', 0)} flagged items",
                "raw": feed,
            }
        )
    for ref in model_comparison.get("references", []):
        rows.append(
            {
                "source_type": "open_source_model",
                "name": ref.get("name", ""),
                "url_or_ref": ref.get("url", ""),
                "usage": ref.get("report_usage", ""),
                "status": "ok" if ref.get("adoption_status") == "implemented_proxy" else "watch",
                "status_code": None,
                "freshness": "reference",
                "evidence_layer": "INFERENCE",
                "message": f"{ref.get('method_family', '')}; {ref.get('adoption_status', '')}",
                "raw": ref,
            }
        )
    return rows


def local_reference_source_logs(paths: Iterable[Path] = LOCAL_REFERENCE_FILES) -> List[Dict]:
    rows = []
    for path in paths:
        exists = path.exists()
        rows.append(
            {
                "source_type": "local_reference_file",
                "name": path.name,
                "url_or_ref": path.name,
                "usage": "local ChatGPT/user workbook reference; private values are not exported",
                "status": "ok" if exists else "missing",
                "status_code": None,
                "freshness": "local_file",
                "evidence_layer": "OBSERVATION",
                "message": "available" if exists else "file missing",
                "raw": {"file_name": path.name, "exists": exists, "size_bytes": path.stat().st_size if exists else 0},
            }
        )
    return rows


def build_audit_logs(raw_refresh: Dict, preflight: Dict, safety: Dict, portfolio: Dict) -> List[Dict]:
    rows = [
        audit_row("raw_refresh", bool(raw_refresh.get("raw_refresh_ready")), raw_refresh.get("blocking_reasons", []), raw_refresh),
        audit_row("automation_preflight", bool(preflight.get("technical_preflight_ready")), preflight.get("blocking_reasons", []), preflight),
        audit_row("public_safety", bool(safety.get("automation_safety_ready")), safety.get("blocking_reasons", []), safety),
        audit_row("portfolio_gate", bool(portfolio.get("portfolio_automation_ready")), portfolio.get("blocking_reasons", []), portfolio),
    ]
    for check in preflight.get("checks", []):
        rows.append(
            {
                "check_name": f"preflight:{check.get('name', '')}",
                "status": "ok" if check.get("passed") else "blocked",
                "severity": "blocker" if not check.get("passed") else "info",
                "message": check.get("message", ""),
                "raw": check,
            }
        )
    return rows


def audit_row(name: str, ok: bool, reasons: List[str], raw: Dict) -> Dict:
    return {
        "check_name": name,
        "status": "ok" if ok else "blocked",
        "severity": "blocker" if not ok else "info",
        "message": "; ".join(reasons) if reasons else ("passed" if ok else "failed"),
        "raw": raw,
    }


def build_decision_records(output_dir: Path, boards: Iterable) -> List[Dict]:
    rows: List[Dict] = []
    for board in boards:
        if not board.recommendations_artifact:
            continue
        payload = load_optional_json(output_dir / board.recommendations_artifact)
        for rank, item in enumerate(payload.get("recommendations", []), start=1):
            stake = float(item.get("time_adjusted_stake_aud") or item.get("stake_aud") or 0)
            rows.append(
                {
                    "board_id": board.board_id,
                    "board_name": board.name,
                    "rank": rank,
                    "event_name": item.get("match") or item.get("team") or (f"Group {item.get('group')}" if item.get("group") else item.get("market", "")),
                    "market": item.get("market", ""),
                    "selection": item.get("selection") or item.get("team", ""),
                    "action": "buy" if stake > 0 else item.get("decision", "watch_or_no_bet"),
                    "stake_aud": stake,
                    "probability": item.get("model_probability", item.get("no_vig_probability", item.get("probability"))),
                    "expected_value": item.get("expected_value"),
                    "evidence_layer": "INFERENCE",
                    "reason": item.get("rationale", ""),
                    "raw": item,
                }
            )
    return rows


def build_missing_data_logs(public_sources: Dict, event_monitor: Dict, raw_refresh: Dict, preflight: Dict, safety: Dict, portfolio: Dict) -> List[Dict]:
    rows: List[Dict] = []
    for source in public_sources.get("sources", []):
        if not source.get("ok"):
            rows.append(missing_row("public_source", source.get("name", ""), "blocker", "; ".join(source.get("missing_terms", [])) or source.get("error", "")))
    for feed in event_monitor.get("feeds", []):
        if not feed.get("ok"):
            rows.append(missing_row("event_feed", feed.get("team", ""), "blocker", feed.get("error") or "feed failed"))
    for target in raw_refresh.get("targets", []):
        if not target.get("refresh_ready"):
            rows.append(missing_row("raw_refresh", target.get("name", target.get("board_id", "")), "blocker", "; ".join(target.get("blocking_reasons", [])) or "raw refresh target not ready"))
    for board in portfolio.get("board_statuses", []):
        missing = board.get("missing") or []
        if missing:
            rows.append(missing_row("board_gate", board.get("name", ""), "blocker", ", ".join(missing)))
    for reason in preflight.get("blocking_reasons", []):
        if is_authorization_reason(reason):
            continue
        rows.append(missing_row("automation_preflight", "preflight", "blocker", reason))
    for reason in safety.get("blocking_reasons", []):
        rows.append(missing_row("public_safety", "safety", "blocker", reason))
    return rows


def is_authorization_reason(reason: str) -> bool:
    text = str(reason or "").lower()
    return "authorized" in text or "authorization" in text or "recurring automation" in text


def missing_row(category: str, item: str, severity: str, message: str) -> Dict:
    return {
        "category": category,
        "item": item,
        "severity": severity,
        "status": "open",
        "message": message,
        "raw": {"category": category, "item": item, "message": message},
    }


def build_manual_review_queue(missing_rows: List[Dict], decision_records: List[Dict], model_comparison: Dict) -> List[Dict]:
    rows = [
        {
            "queue_type": "missing_data",
            "item": item.get("item", ""),
            "severity": item.get("severity", "blocker"),
            "status": "open",
            "message": item.get("message", ""),
            "raw": item,
        }
        for item in missing_rows
    ]
    high_divergence = [row for row in model_comparison.get("rows", []) if row.get("disagreement", {}).get("high_divergence")]
    for row in high_divergence[:12]:
        rows.append(
            {
                "queue_type": "model_divergence",
                "item": row.get("match", ""),
                "severity": "review",
                "status": "open",
                "message": f"{row.get('consensus', {}).get('selection', '')}: {row.get('disagreement', {}).get('max_abs_current_vs_elo_dc', 0):.1%} max model gap",
                "raw": row,
            }
        )
    for decision in decision_records:
        if decision.get("action") == "buy" and not decision.get("reason"):
            rows.append(
                {
                    "queue_type": "decision_reason",
                    "item": f"{decision.get('event_name')} / {decision.get('selection')}",
                    "severity": "review",
                    "status": "open",
                    "message": "buy decision lacks rationale",
                    "raw": decision,
                }
            )
    return rows
