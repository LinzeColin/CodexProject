from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import DATA_DIR
from pfi_os.data.symbols import normalize_a_share_symbol
from pfi_os.storage import atomic_write_json, atomic_write_text


HOLDING_SYMBOL_MAP_PATH = DATA_DIR / "holdings" / "HoldingSymbolMap.json"
ENTITY_REGISTRY_DIR = DATA_DIR / "entityRegistry"


@dataclass(frozen=True)
class HoldingSymbolProxy:
    symbol: str
    name: str
    market: str
    role: str
    confidence: str
    reason: str
    source: str


@dataclass(frozen=True)
class EntityRecord:
    entity_id: str
    name: str
    market: str
    original_symbol: str
    canonical_symbol: str
    provider_symbol_akshare: str
    provider_symbol_tushare: str
    proxy_symbol: str
    proxy_market: str
    status: str
    confidence: str
    source_system: str
    reason: str
    updated_at: str

    def to_row(self) -> dict[str, object]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "market": self.market,
            "original_symbol": self.original_symbol,
            "canonical_symbol": self.canonical_symbol,
            "provider_symbol_akshare": self.provider_symbol_akshare,
            "provider_symbol_tushare": self.provider_symbol_tushare,
            "proxy_symbol": self.proxy_symbol,
            "proxy_market": self.proxy_market,
            "status": self.status,
            "confidence": self.confidence,
            "source_system": self.source_system,
            "reason": self.reason,
            "updated_at": self.updated_at,
        }


DEFAULT_HOLDING_SYMBOL_PROXY_RULES: tuple[dict[str, object], ...] = (
    {"keywords": ["黄金"], "symbol": "518880", "name": "黄金ETF代理", "market": "CN", "confidence": "ProxyHigh", "reason": "名称包含黄金，使用 A 股黄金 ETF 作为行情代理。"},
    {"keywords": ["半导体", "芯片"], "symbol": "159995", "name": "半导体芯片ETF代理", "market": "CN", "confidence": "ProxyHigh", "reason": "名称包含半导体或芯片，使用国证半导体芯片 ETF 代理。"},
    {"keywords": ["人工智能"], "symbol": "159819", "name": "人工智能ETF代理", "market": "CN", "confidence": "ProxyHigh", "reason": "名称包含人工智能，使用人工智能主题 ETF 代理。"},
    {"keywords": ["银行"], "symbol": "512800", "name": "银行ETF代理", "market": "CN", "confidence": "ProxyMedium", "reason": "名称包含银行，使用银行 ETF 作为行业代理。"},
    {"keywords": ["恒生科技"], "symbol": "3033.HK", "name": "恒生科技ETF代理", "market": "HK", "confidence": "ProxyHigh", "reason": "名称包含恒生科技，使用港股恒生科技 ETF 代理。"},
    {"keywords": ["科创50"], "symbol": "588000", "name": "科创50ETF代理", "market": "CN", "confidence": "ProxyHigh", "reason": "名称包含科创50，使用科创50 ETF 代理。"},
    {"keywords": ["红利低波"], "symbol": "512890", "name": "红利低波ETF代理", "market": "CN", "confidence": "ProxyMedium", "reason": "名称包含红利低波，使用红利低波 ETF 代理。"},
    {"keywords": ["纳斯达克"], "symbol": "QQQ", "name": "纳斯达克100ETF代理", "market": "US", "confidence": "ProxyHigh", "reason": "名称包含纳斯达克，使用 QQQ 作为行情代理。"},
    {"keywords": ["标普500"], "symbol": "SPY", "name": "标普500ETF代理", "market": "US", "confidence": "ProxyHigh", "reason": "名称包含标普500，使用 SPY 作为行情代理。"},
    {"keywords": ["中证500"], "symbol": "510500", "name": "中证500ETF代理", "market": "CN", "confidence": "ProxyHigh", "reason": "名称包含中证500，使用中证500 ETF 代理。"},
    {"keywords": ["农业"], "symbol": "159825", "name": "农业主题ETF代理", "market": "CN", "confidence": "ProxyMedium", "reason": "名称包含农业，使用农业主题 ETF 代理。"},
    {"keywords": ["机器人"], "symbol": "562500", "name": "机器人ETF代理", "market": "CN", "confidence": "ProxyMedium", "reason": "名称包含机器人，使用机器人主题 ETF 代理。"},
    {"keywords": ["石油"], "symbol": "XLE", "name": "能源行业ETF代理", "market": "US", "confidence": "ProxyLow", "reason": "名称包含石油，使用美股能源行业 ETF 作为粗略代理。"},
    {"keywords": ["全球成长"], "symbol": "QQQ", "name": "全球成长风格代理", "market": "US", "confidence": "ProxyLow", "reason": "名称包含全球成长，使用 QQQ 作为成长风格粗略代理。"},
)


def load_holding_symbol_proxy_rules(path: Path | str = HOLDING_SYMBOL_MAP_PATH) -> list[dict[str, object]]:
    custom_rules = _load_custom_rules(Path(path))
    return [*custom_rules, *DEFAULT_HOLDING_SYMBOL_PROXY_RULES]


def resolve_holding_symbol_proxy(
    name: str,
    symbol: str = "",
    market: str = "",
    path: Path | str = HOLDING_SYMBOL_MAP_PATH,
) -> HoldingSymbolProxy | None:
    clean_symbol = str(symbol or "").strip()
    clean_name = str(name or "").strip()
    clean_market = str(market or "").strip().upper()
    if clean_symbol:
        return HoldingSymbolProxy(
            symbol=clean_symbol,
            name=clean_name or clean_symbol,
            market=clean_market or "CN",
            role="持仓",
            confidence="ConfirmedSymbol",
            reason="持仓记录已包含行情代码。",
            source="HoldingBook",
        )
    normalized_name = _normalize_name(clean_name)
    if not normalized_name:
        return None
    for rule in load_holding_symbol_proxy_rules(path):
        keywords = [str(item).strip() for item in rule.get("keywords", []) if str(item).strip()]
        if not keywords:
            continue
        normalized_keywords = [_normalize_name(item) for item in keywords]
        if not any(keyword and keyword in normalized_name for keyword in normalized_keywords):
            continue
        return HoldingSymbolProxy(
            symbol=str(rule.get("symbol", "")).strip(),
            name=str(rule.get("name", "")).strip() or clean_name,
            market=str(rule.get("market", clean_market or "CN")).strip().upper(),
            role=str(rule.get("role", "持仓代理")).strip() or "持仓代理",
            confidence=str(rule.get("confidence", "Proxy")).strip() or "Proxy",
            reason=str(rule.get("reason", "根据持仓名称匹配行情代理代码。")).strip(),
            source=str(rule.get("source", "HoldingSymbolMap")).strip() or "HoldingSymbolMap",
        )
    return None


def holdings_symbol_proxy_frame(holdings: pd.DataFrame, market: str = "") -> pd.DataFrame:
    if holdings.empty:
        return pd.DataFrame(columns=["name", "market", "symbol", "proxy_symbol", "proxy_name", "proxy_market", "status", "confidence", "reason"])
    data = holdings.copy()
    for column in ["symbol", "name", "market"]:
        if column not in data.columns:
            data[column] = ""
        data[column] = data[column].fillna("").astype(str).str.strip()
    rows: list[dict[str, object]] = []
    for row in data.to_dict("records"):
        proxy = resolve_holding_symbol_proxy(row.get("name", ""), row.get("symbol", ""), row.get("market", market))
        status = "MissingSymbol"
        if proxy and proxy.confidence == "ConfirmedSymbol":
            status = "ConfirmedSymbol"
        elif proxy:
            status = "ProxyMapped"
        rows.append(
            {
                "name": row.get("name", ""),
                "market": row.get("market", market),
                "symbol": row.get("symbol", ""),
                "proxy_symbol": proxy.symbol if proxy else "",
                "proxy_name": proxy.name if proxy else "",
                "proxy_market": proxy.market if proxy else "",
                "status": status,
                "confidence": proxy.confidence if proxy else "",
                "reason": proxy.reason if proxy else "缺少代码，且没有匹配到本地代理规则。",
            }
        )
    return pd.DataFrame(rows)


def build_entity_registry(holdings: pd.DataFrame, *, as_of: str | None = None) -> dict[str, Any]:
    generated_at = as_of or datetime.now().isoformat(timespec="seconds")
    records = _entity_records_from_holdings(holdings, generated_at)
    return {
        "schema": "PFIOSEntityRegistryV1",
        "system": "PFIOS",
        "generated_at": generated_at,
        "record_count": len(records),
        "status_counts": _count_entity_records(records, "status"),
        "market_counts": _count_entity_records(records, "market"),
        "assumptions": [
            "Entity registry is a derived index and does not overwrite holdings.",
            "ProxyMapped means the holding name was mapped to a research proxy, not a confirmed tradable security.",
            "MissingSymbol entities must not be used for backtests, sentiment, or market-hotspot analysis until confirmed.",
        ],
        "records": [record.to_row() for record in records],
    }


def write_entity_registry(
    holdings: pd.DataFrame,
    *,
    output_dir: Path | str = ENTITY_REGISTRY_DIR,
    as_of: str | None = None,
) -> dict[str, Any]:
    registry = build_entity_registry(holdings, as_of=as_of)
    out_dir = Path(output_dir)
    json_path = out_dir / "EntityRegistry.json"
    csv_path = out_dir / "EntityRegistry.csv"
    markdown_path = out_dir / "EntityRegistry.md"

    frame = entity_registry_frame(registry)
    atomic_write_text(csv_path, frame.to_csv(index=False))
    atomic_write_text(markdown_path, _entity_registry_markdown(registry))

    registry = {
        **registry,
        "outputs": {
            "json": str(json_path),
            "csv": str(csv_path),
            "markdown": str(markdown_path),
        },
    }
    atomic_write_json(json_path, registry)
    return registry


def entity_registry_frame(registry: dict[str, Any]) -> pd.DataFrame:
    rows = registry.get("records", []) if isinstance(registry, dict) else []
    columns = list(EntityRecord.__dataclass_fields__)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=columns)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    return frame[columns].copy()


def _load_custom_rules(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows: Any
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("mappings", [])
    else:
        rows = []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _normalize_name(value: str) -> str:
    return (
        str(value or "")
        .lower()
        .replace("（", "(")
        .replace("）", ")")
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def _entity_records_from_holdings(holdings: pd.DataFrame, generated_at: str) -> list[EntityRecord]:
    if holdings.empty:
        return []
    data = holdings.copy()
    for column in ["name", "symbol", "market", "source_system", "updated_at"]:
        if column not in data.columns:
            data[column] = ""
        data[column] = data[column].fillna("").astype(str).str.strip()
    proxy_frame = holdings_symbol_proxy_frame(data)
    records: list[EntityRecord] = []
    for index, row in data.reset_index(drop=True).iterrows():
        proxy = proxy_frame.iloc[index].to_dict() if index < len(proxy_frame) else {}
        original_symbol = str(row.get("symbol", "")).strip()
        market = str(row.get("market", "")).strip().upper()
        proxy_symbol = str(proxy.get("proxy_symbol", "")).strip()
        proxy_market = str(proxy.get("proxy_market", "")).strip().upper()
        canonical_symbol = original_symbol or proxy_symbol
        canonical_market = market or proxy_market
        provider_symbols = _provider_symbols(canonical_symbol, canonical_market)
        proxy_status = str(proxy.get("status", "")).strip()
        records.append(
            EntityRecord(
                entity_id=_stable_entity_id(canonical_market, canonical_symbol, row.get("name", "")),
                name=str(row.get("name", "")).strip() or canonical_symbol,
                market=canonical_market,
                original_symbol=original_symbol,
                canonical_symbol=canonical_symbol,
                provider_symbol_akshare=provider_symbols["akshare"],
                provider_symbol_tushare=provider_symbols["tushare"],
                proxy_symbol=proxy_symbol,
                proxy_market=proxy_market,
                status=_entity_status(proxy_status),
                confidence=str(proxy.get("confidence", "")).strip(),
                source_system=str(row.get("source_system", "")).strip() or "HoldingsBook",
                reason=str(proxy.get("reason", "")).strip(),
                updated_at=str(row.get("updated_at", "")).strip() or generated_at,
            )
        )
    return sorted(records, key=lambda item: (item.status, item.market, item.name, item.canonical_symbol))


def _entity_status(proxy_status: str) -> str:
    if proxy_status == "ConfirmedSymbol":
        return "TradableSymbol"
    if proxy_status == "ProxyMapped":
        return "ProxyMapped"
    return "MissingSymbol"


def _provider_symbols(symbol: str, market: str) -> dict[str, str]:
    if market == "CN" and symbol:
        try:
            normalized = normalize_a_share_symbol(symbol)
            return {"akshare": normalized.akshare, "tushare": normalized.tushare}
        except ValueError:
            if symbol.isdigit() and len(symbol) == 6 and symbol.startswith("5"):
                return {"akshare": symbol, "tushare": f"{symbol}.SH"}
            if symbol.isdigit() and len(symbol) == 6 and symbol.startswith("1"):
                return {"akshare": symbol, "tushare": f"{symbol}.SZ"}
            return {"akshare": symbol, "tushare": ""}
    return {"akshare": "", "tushare": ""}


def _count_entity_records(records: list[EntityRecord], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(getattr(record, field) or "Unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _entity_registry_markdown(registry: dict[str, Any]) -> str:
    records = registry.get("records", [])
    status_counts = registry.get("status_counts", {})
    market_counts = registry.get("market_counts", {})
    lines = [
        "# Entity Registry",
        "",
        f"- Schema: `{registry.get('schema', '')}`",
        f"- Generated At: `{registry.get('generated_at', '')}`",
        f"- Record Count: `{registry.get('record_count', 0)}`",
        f"- Status Counts: `{json.dumps(status_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- Market Counts: `{json.dumps(market_counts, ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Status Meaning",
        "",
        "- `TradableSymbol`: 持仓已有可直接查询行情的确认代码。",
        "- `ProxyMapped`: 持仓没有确认代码，但已映射到研究代理标的；只能用于研究代理，不等于真实持仓。",
        "- `MissingSymbol`: 缺少确认代码且没有代理，禁止进入回测、情绪分析和热点分析。",
        "",
        "## Records",
        "",
        "| Name | Market | Canonical Symbol | Status | Confidence | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in records:
        lines.append(
            "| {name} | {market} | {symbol} | {status} | {confidence} | {reason} |".format(
                name=_markdown_cell(row.get("name", "")),
                market=_markdown_cell(row.get("market", "")),
                symbol=_markdown_cell(row.get("canonical_symbol", "")),
                status=_markdown_cell(row.get("status", "")),
                confidence=_markdown_cell(row.get("confidence", "")),
                reason=_markdown_cell(row.get("reason", "")),
            )
        )
    return "\n".join(lines) + "\n"


def _markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _stable_entity_id(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
