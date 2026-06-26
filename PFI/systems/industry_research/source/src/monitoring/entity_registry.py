from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.config import ROOT
from src.monitoring.data_trust import SYSTEM_AUDIT_DIRNAME, _write_pdf


_ALIAS_REMOVE_CHARS = set(" \t\r\n_-.\\/·•（）()【】[]{}:：,，;；'\"“”")


@dataclass(frozen=True)
class EntityRecord:
    entity_id: str
    entity_type: str
    canonical_name: str
    symbol: str
    market: str
    source_system: str
    evidence_classification: str
    decision_grade: str
    alias_count: int
    source_count: int
    source_paths: str
    issues: str


@dataclass(frozen=True)
class AliasRecord:
    alias_id: str
    entity_id: str
    entity_type: str
    alias: str
    alias_type: str
    alias_scope: str
    normalized_alias: str
    source_path: str
    confidence: str
    conflict_status: str


class _RegistryBuilder:
    def __init__(self) -> None:
        self.entities: dict[str, dict[str, Any]] = {}
        self.aliases: list[dict[str, Any]] = []

    def add_entity(
        self,
        entity_type: str,
        canonical_name: str,
        *,
        symbol: str = "",
        market: str = "",
        source_system: str = "",
        source_path: Path | str = "",
        aliases: Iterable[tuple[str, str, str]] = (),
        evidence: str = "FACT",
        decision: str = "Observe",
        issues: str = "",
    ) -> str:
        name = str(canonical_name or symbol or "").strip()
        if not name:
            return ""
        clean_symbol = str(symbol or "").strip()
        clean_market = str(market or "").strip()
        key = _entity_key(entity_type, name, clean_symbol, clean_market)
        entity = self.entities.setdefault(
            key,
            {
                "entity_type": entity_type,
                "canonical_name": name,
                "symbol": clean_symbol,
                "market": clean_market,
                "source_systems": set(),
                "source_paths": set(),
                "issues": set(),
                "evidence": evidence,
                "decision": decision,
            },
        )
        if source_system:
            entity["source_systems"].add(str(source_system))
        if source_path:
            entity["source_paths"].add(str(source_path))
        if issues:
            entity["issues"].add(str(issues))
        entity["evidence"] = _stronger_evidence(entity["evidence"], evidence)
        entity["decision"] = _stronger_decision(entity["decision"], decision)
        if not entity["symbol"] and clean_symbol:
            entity["symbol"] = clean_symbol
        if not entity["market"] and clean_market:
            entity["market"] = clean_market
        entity_id = _stable_id("entity", entity_type, key)
        base_aliases = [(name, "canonical_name", "High")]
        if clean_symbol and entity_type == "FinancialInstrument":
            base_aliases.append((clean_symbol, "symbol", "High"))
        for alias, alias_type, confidence in [*base_aliases, *aliases]:
            self.add_alias(entity_id, alias, alias_type, source_path, confidence, entity_type=entity["entity_type"], market=entity["market"])
        return entity_id

    def add_alias(
        self,
        entity_id: str,
        alias: str,
        alias_type: str,
        source_path: Path | str,
        confidence: str = "Medium",
        entity_type: str = "",
        market: str = "",
    ) -> None:
        text = str(alias or "").strip()
        if not entity_id or not text:
            return
        normalized = normalize_alias(text)
        if not normalized:
            return
        scope = _alias_scope(entity_type, market)
        self.aliases.append(
            {
                "alias_id": _stable_id("alias", entity_id, scope, normalized, alias_type),
                "entity_id": entity_id,
                "entity_type": entity_type,
                "alias": text,
                "alias_type": alias_type,
                "alias_scope": scope,
                "normalized_alias": normalized,
                "source_path": str(source_path or ""),
                "confidence": confidence,
            }
        )

    def build(self) -> tuple[list[EntityRecord], list[AliasRecord]]:
        alias_by_entity: dict[str, set[str]] = defaultdict(set)
        normalized_to_entities: dict[str, set[str]] = defaultdict(set)
        deduped_aliases: dict[tuple[str, str, str], dict[str, Any]] = {}
        for alias in self.aliases:
            key = (alias["entity_id"], alias["alias_scope"], alias["normalized_alias"], alias["alias_type"])
            deduped_aliases.setdefault(key, alias)
            alias_by_entity[alias["entity_id"]].add(alias["normalized_alias"])
            normalized_to_entities[f"{alias['alias_scope']}:{alias['normalized_alias']}"].add(alias["entity_id"])
        alias_records = []
        for alias in deduped_aliases.values():
            conflict_key = f"{alias['alias_scope']}:{alias['normalized_alias']}"
            conflict_status = "Conflict" if len(normalized_to_entities[conflict_key]) > 1 else "Unique"
            alias_records.append(AliasRecord(conflict_status=conflict_status, **alias))
        entities = []
        for key, data in self.entities.items():
            entity_id = _stable_id("entity", data["entity_type"], key)
            entities.append(
                EntityRecord(
                    entity_id=entity_id,
                    entity_type=data["entity_type"],
                    canonical_name=data["canonical_name"],
                    symbol=data["symbol"],
                    market=data["market"],
                    source_system="; ".join(sorted(data["source_systems"])),
                    evidence_classification=data["evidence"],
                    decision_grade=data["decision"],
                    alias_count=len(alias_by_entity.get(entity_id, set())),
                    source_count=len(data["source_paths"]),
                    source_paths="; ".join(sorted(data["source_paths"])),
                    issues="; ".join(sorted(data["issues"])),
                )
            )
        return sorted(entities, key=lambda row: (row.entity_type, row.canonical_name, row.symbol)), sorted(
            alias_records, key=lambda row: (row.conflict_status, row.entity_id, row.alias_type, row.alias)
        )


def normalize_alias(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = "".join(char for char in text if char not in _ALIAS_REMOVE_CHARS)
    return text.strip()


def build_entity_registry_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    project_root = Path(root)
    builder = _RegistryBuilder()
    _collect_watchlist_entities(builder, project_root)
    _collect_alipay_entities(builder, project_root)
    _collect_research_bus_entities(builder, project_root)
    _collect_policy_entities(builder, project_root)
    _collect_report_entities(builder, project_root)
    _collect_system_audit_entities(builder, project_root, as_of)
    entities, aliases = builder.build()
    entity_counts = Counter(entity.entity_type for entity in entities)
    conflict_aliases = [alias for alias in aliases if alias.conflict_status == "Conflict"]
    audit_status = "Review" if conflict_aliases else "Pass"
    return {
        "schema": "AIResearchEntityRegistryV1",
        "system": "AI-Research-System",
        "as_of": as_of,
        "generated_at": _now(),
        "audit_status": audit_status,
        "entity_count": len(entities),
        "alias_count": len(aliases),
        "alias_conflict_count": len(conflict_aliases),
        "entity_type_counts": dict(sorted(entity_counts.items())),
        "assumptions": [
            "This registry is generated from local artifacts only and does not query external data providers.",
            "Aliases are normalized with Unicode NFKC, casefold, whitespace removal, and common punctuation removal.",
            "Alias conflicts are review signals, not automatic merges.",
        ],
        "entities": [asdict(entity) for entity in entities],
        "aliases": [asdict(alias) for alias in aliases],
        "conflicts": [asdict(alias) for alias in conflict_aliases],
    }


def write_entity_registry_audit(
    as_of: str,
    *,
    root: Path | str = ROOT,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    project_root = Path(root)
    audit = build_entity_registry_audit(as_of, root=project_root)
    target_dir = Path(output_dir) if output_dir else project_root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = f"entity_registry_{as_of}"
    json_path = target_dir / f"{stem}.json"
    entity_csv_path = target_dir / f"{stem}.csv"
    alias_csv_path = target_dir / f"alias_map_{as_of}.csv"
    markdown_path = target_dir / f"{stem}.md"
    pdf_path = target_dir / f"{stem}.pdf"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_rows_csv(entity_csv_path, audit["entities"])
    _write_rows_csv(alias_csv_path, audit["aliases"])
    markdown = _audit_markdown(audit)
    markdown_path.write_text(markdown, encoding="utf-8")
    _write_pdf(pdf_path, markdown)
    audit["outputs"] = {
        "json": str(json_path),
        "entity_csv": str(entity_csv_path),
        "alias_csv": str(alias_csv_path),
        "markdown": str(markdown_path),
        "pdf": str(pdf_path),
    }
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


def _collect_watchlist_entities(builder: _RegistryBuilder, root: Path) -> None:
    for path in [root / "data" / "sample" / "watchlist_moomoo.csv", root / "data" / "sample" / "watchlist_snapshot.csv"]:
        for row in _read_csv(path):
            aliases = []
            for field, alias_type in [("code", "code"), ("quote_code", "quote_code"), ("eng_name", "english_name")]:
                if row.get(field):
                    aliases.append((str(row[field]), alias_type, "High" if field in {"code", "quote_code"} else "Medium"))
            builder.add_entity(
                "FinancialInstrument",
                row.get("name") or row.get("symbol") or row.get("quote_code") or "",
                symbol=row.get("symbol", ""),
                market=row.get("exchange", ""),
                source_system=row.get("source_name") or "MoomooWatchlist",
                source_path=path,
                aliases=aliases,
                evidence="FACT",
                decision="Actionable" if row.get("symbol") else "Observe",
                issues="" if row.get("symbol") else "missing symbol",
            )


def _collect_alipay_entities(builder: _RegistryBuilder, root: Path) -> None:
    alipay_dir = root / "data" / "private" / "alipay"
    for name in ["current_positions.csv", "pending_orders.csv", "trade_ledger.csv"]:
        path = alipay_dir / name
        for row in _read_csv(path):
            entity_name = row.get("name") or row.get("symbol") or ""
            if not entity_name:
                continue
            builder.add_entity(
                "FinancialInstrument",
                entity_name,
                symbol=row.get("symbol", ""),
                market="CN",
                source_system=row.get("source") or "Alipay",
                source_path=path,
                aliases=[],
                evidence="OBSERVATION" if "video" in str(row.get("source", "")).lower() or "Pending" in str(row.get("quality_status", "")) else "FACT",
                decision="Watch" if row.get("status") or row.get("quality_status") else "Observe",
                issues="Requires user confirmation" if row.get("quality_status") or "video" in str(row.get("source", "")).lower() else "",
            )
    for path in sorted(alipay_dir.glob("video_position_candidates_*.csv")):
        for row in _read_csv(path):
            if row.get("name"):
                builder.add_entity(
                    "FinancialInstrument",
                    row["name"],
                    market="CN",
                    source_system="AlipayVideoCandidate",
                    source_path=path,
                    aliases=[],
                    evidence="OBSERVATION",
                    decision="Watch",
                    issues="video candidate requires confirmation",
                )
    builder.add_entity(
        "Account",
        "DefaultAccount",
        source_system="AI-Research-System",
        source_path=alipay_dir,
        aliases=[("AlipayAccount", "english_name", "Medium"), ("支付宝账户", "chinese_name", "High")],
        evidence="OBSERVATION",
        decision="Watch",
        issues="account evidence is sourced from user-provided Alipay files",
    )


def _collect_research_bus_entities(builder: _RegistryBuilder, root: Path) -> None:
    bridge = root / "data" / "report_artifacts" / "research_bus_bridge"
    market_hints = _watchlist_market_hints(root)
    holdings = _load_json(bridge / "HoldingsMasterFromBus.json", {}).get("holdings", [])
    for row in holdings if isinstance(holdings, list) else []:
        symbol = row.get("symbol", "")
        market = _preferred_market_for_symbol(market_hints, symbol, row.get("market", ""))
        builder.add_entity(
            "FinancialInstrument",
            row.get("name") or symbol or "",
            symbol=symbol,
            market=market,
            source_system=row.get("source_system") or "ResearchBus",
            source_path=row.get("source_path") or bridge / "HoldingsMasterFromBus.json",
            aliases=[(row.get("holding_id", ""), "holding_id", "High")],
            evidence="OBSERVATION",
            decision="Watch",
            issues="holding evidence requires source-system confirmation" if not row.get("symbol") else "",
        )
        if row.get("account"):
            builder.add_entity("Account", row["account"], source_system="ResearchBus", source_path=bridge / "HoldingsMasterFromBus.json")
    validation_tasks = _load_json(bridge / "ValidationTasksFromBus.json", {}).get("validation_tasks", [])
    for row in validation_tasks if isinstance(validation_tasks, list) else []:
        builder.add_entity(
            "ValidationTask",
            row.get("task_id") or row.get("research_topic") or "",
            symbol=row.get("symbol", ""),
            market=row.get("market", ""),
            source_system="ResearchBus",
            source_path=row.get("source_report_path") or bridge / "ValidationTasksFromBus.json",
            aliases=[(row.get("task_id", ""), "task_id", "High")],
            evidence="OBSERVATION",
            decision="Watch" if row.get("status") else "Observe",
            issues="validation pending" if str(row.get("status", "")).strip() in {"待验证", "Pending"} else "",
        )
        if row.get("symbol"):
            market = _preferred_market_for_symbol(market_hints, row.get("symbol", ""), row.get("market", ""))
            builder.add_entity(
                "FinancialInstrument",
                row.get("symbol", ""),
                symbol=row.get("symbol", ""),
                market=market,
                source_system="ResearchBusValidationTask",
                source_path=row.get("source_report_path") or bridge / "ValidationTasksFromBus.json",
                aliases=[],
                evidence="OBSERVATION",
                decision="Watch",
            )
    runs = _load_json(bridge / "IndependentValidationRunsFromBus.json", {}).get("independent_validation_runs", [])
    for row in runs if isinstance(runs, list) else []:
        builder.add_entity(
            "ValidationRun",
            row.get("run_id") or row.get("output_path") or "",
            source_system=row.get("source_system") or "IndependentValidation",
            source_path=row.get("output_path") or bridge / "IndependentValidationRunsFromBus.json",
            aliases=[(row.get("run_id", ""), "run_id", "High")],
            evidence="FACT",
            decision="Actionable" if row.get("status") == "Completed" else "Watch",
        )
    pfi_os = _load_json(root / "data" / "report_artifacts" / "pfi_os_bridge" / "PFIOSResults.json", {})
    results = pfi_os.get("results", []) if isinstance(pfi_os, dict) else []
    for row in results if isinstance(results, list) else []:
        builder.add_entity(
            "Strategy",
            row.get("strategy_id") or row.get("result_id") or "",
            source_system="PFIOS",
            source_path=row.get("metadata_path") or root / "data" / "report_artifacts" / "pfi_os_bridge" / "PFIOSResults.json",
            aliases=[(row.get("run", ""), "run_id", "High"), (row.get("result_id", ""), "result_id", "High")],
            evidence="OBSERVATION",
            decision="Watch" if row.get("research_status") in {"NeedsMoreEvidence", "DataQualityReview", "DoNotUse"} or row.get("status") == "Review" else "Actionable",
            issues="PFIOS row requires downgrade or review" if row.get("status") == "Review" else "",
        )
    for system_name in ["AI-Research-System", "ResearchBus", "PFIOS", "IndependentValidation", "PolicyBridge", "Alipay"]:
        builder.add_entity("System", system_name, source_system="AI-Research-System", source_path=root)


def _collect_policy_entities(builder: _RegistryBuilder, root: Path) -> None:
    for path in sorted((root / "data" / "report_artifacts" / "policy_bridge" / "events").glob("policy_events_*.csv")):
        for row in _read_csv(path):
            builder.add_entity(
                "PolicyDocument",
                row.get("title") or row.get("source_url") or "",
                symbol=row.get("related_symbols", ""),
                market="CN",
                source_system=row.get("source_name") or "PolicyBridge",
                source_path=path,
                aliases=[(row.get("source_url", ""), "source_url", "High")],
                evidence="FACT" if row.get("policy_original_fetch_status") == "verified" else "OBSERVATION",
                decision="Watch" if row.get("policy_bridge_status") else "Observe",
                issues="" if row.get("policy_original_fetch_status") == "verified" else "policy source not verified",
            )
            if row.get("source_name"):
                builder.add_entity(
                    "DataSource",
                    row["source_name"],
                    source_system="PolicyBridge",
                    source_path=path,
                    aliases=[],
                    evidence="FACT",
                    decision="Actionable",
                )


def _collect_report_entities(builder: _RegistryBuilder, root: Path) -> None:
    for path in sorted((root / "data" / "report_artifacts").glob("**/_source_logs/*.json")):
        payload = _load_json(path, {})
        report_name = str(payload.get("report_name") or path.name.replace("_sources.json", "")) if isinstance(payload, dict) else path.stem
        builder.add_entity(
            "Report",
            report_name,
            source_system="AI-Research-System",
            source_path=path,
            aliases=[(path.name, "file_name", "High")],
            evidence="FACT",
            decision="Actionable",
        )
        sources = payload.get("sources", []) if isinstance(payload, dict) else []
        for source in sources if isinstance(sources, list) else []:
            if not isinstance(source, dict):
                continue
            builder.add_entity(
                "DataSource",
                source.get("source_name") or source.get("source_url") or "",
                source_system="AI-Research-System",
                source_path=path,
                aliases=[(source.get("source_url", ""), "source_url", "High")],
                evidence="FACT" if source.get("source_url") else "OBSERVATION",
                decision="Actionable" if source.get("source_url") else "Watch",
            )


def _collect_system_audit_entities(builder: _RegistryBuilder, root: Path, as_of: str) -> None:
    audit_dir = root / "data" / "report_artifacts" / SYSTEM_AUDIT_DIRNAME
    manual = _load_json(audit_dir / f"manual_review_queue_{as_of}.json", {})
    items = manual.get("items", []) if isinstance(manual, dict) else []
    for row in items if isinstance(items, list) else []:
        builder.add_entity(
            "ReviewItem",
            row.get("review_id") or row.get("item_name") or "",
            source_system=row.get("source_layer") or "ManualReview",
            source_path=audit_dir / f"manual_review_queue_{as_of}.json",
            aliases=[],
            evidence=row.get("evidence_classification") or "OBSERVATION",
            decision=row.get("decision_grade") or "Watch",
            issues=row.get("issue", ""),
        )
    for layer_name, file_name in [
        ("DataTrustAudit", f"data_trust_audit_{as_of}.json"),
        ("ReconciliationAudit", f"reconciliation_audit_{as_of}.json"),
        ("ManualReviewQueue", f"manual_review_queue_{as_of}.json"),
    ]:
        builder.add_entity(
            "SystemArtifact",
            layer_name,
            source_system="AI-Research-System",
            source_path=audit_dir / file_name,
            aliases=[(file_name, "file_name", "High")],
            evidence="FACT",
            decision="Actionable" if (audit_dir / file_name).exists() else "Watch",
            issues="" if (audit_dir / file_name).exists() else "missing audit artifact",
        )


def _entity_key(entity_type: str, name: str, symbol: str, market: str) -> str:
    if entity_type == "FinancialInstrument" and symbol:
        return f"{entity_type}:{normalize_alias(market)}:{normalize_alias(symbol)}"
    return f"{entity_type}:{normalize_alias(name)}"


def _alias_scope(entity_type: str, market: str) -> str:
    clean_type = str(entity_type or "Unknown").strip() or "Unknown"
    if clean_type == "FinancialInstrument":
        return f"{clean_type}:{normalize_alias(market) or 'unknown_market'}"
    return clean_type


def _watchlist_market_hints(root: Path) -> dict[str, str]:
    hints: dict[str, str] = {}
    for path in [root / "data" / "sample" / "watchlist_moomoo.csv", root / "data" / "sample" / "watchlist_snapshot.csv"]:
        for row in _read_csv(path):
            symbol = str(row.get("symbol") or row.get("code") or row.get("quote_code") or "").strip()
            market = str(row.get("exchange") or row.get("market") or "").strip()
            if not symbol or not market or market.upper() == "CN":
                continue
            existing = hints.get(symbol)
            if existing and existing != market:
                hints.pop(symbol, None)
                continue
            hints[symbol] = market
    return hints


def _preferred_market_for_symbol(hints: dict[str, str], symbol: str, market: str) -> str:
    clean_symbol = str(symbol or "").strip()
    clean_market = str(market or "").strip()
    if clean_symbol and clean_market.upper() in {"", "CN"}:
        return hints.get(clean_symbol, clean_market or "CN")
    return clean_market


def _stronger_evidence(current: str, incoming: str) -> str:
    order = {"FACT": 4, "INFERENCE": 3, "OBSERVATION": 2, "OPINION": 1, "": 0}
    return incoming if order.get(incoming, 0) > order.get(current, 0) else current


def _stronger_decision(current: str, incoming: str) -> str:
    order = {"Actionable": 4, "Watch": 3, "Observe": 2, "Reject": 1, "": 0}
    return incoming if order.get(incoming, 0) > order.get(current, 0) else current


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def _load_json(path: Path | str, default: Any) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_rows_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _audit_markdown(audit: dict[str, Any]) -> str:
    entities = list(audit["entities"])
    aliases = list(audit["aliases"])
    conflicts = list(audit["conflicts"])
    lines = [
        f"# AI-Research-System Entity Registry {audit['as_of']}",
        "",
        "## Run Metadata",
        f"- System: {audit['system']}",
        f"- Generated At: {audit['generated_at']}",
        f"- Audit Status: {audit['audit_status']}",
        f"- Entities: {audit['entity_count']}",
        f"- Aliases: {audit['alias_count']}",
        f"- Alias Conflicts: {audit['alias_conflict_count']}",
        "",
        "## Entity Type Summary",
        _markdown_table([{"entity_type": key, "count": value} for key, value in audit["entity_type_counts"].items()], ["entity_type", "count"]),
        "",
        "## Alias Conflicts",
        _markdown_table(conflicts[:40], ["entity_id", "alias", "alias_type", "normalized_alias", "source_path"]),
        "",
        "## Sample Entities",
        _markdown_table(entities[:60], ["entity_type", "canonical_name", "symbol", "market", "decision_grade", "alias_count", "source_count"]),
        "",
        "## Sample Aliases",
        _markdown_table(aliases[:60], ["alias", "alias_type", "normalized_alias", "confidence", "conflict_status"]),
        "",
        "## Assumptions",
        *[f"- {item}" for item in audit["assumptions"]],
    ]
    return "\n".join(lines)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "暂无数据"
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_clean_cell(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, divider, *body])


def _clean_cell(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("|", "/").strip()
    return text[:220] + "..." if len(text) > 220 else text


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{parts[0]}_{digest}"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
