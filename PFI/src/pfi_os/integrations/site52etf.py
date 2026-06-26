from __future__ import annotations

from pathlib import Path
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from pfi_os.config import PROJECT_ROOT
from pfi_os.storage import atomic_write_json, read_json_state


SITE52ETF_URL = "https://52etf.site/"
SITE52ETF_TIMEOUT_SECONDS = 6
SITE52ETF_PUBLIC_SNAPSHOT_SCHEMA = "PFIOS52ETFPublicSnapshotV1"
SITE52ETF_COMPARISON_SCHEMA = "PFIOS52ETFHotspotComparisonV1"
SITE52ETF_OUTPUT_RELATIVE = "data/integrations/site52etf"

_KNOWN_BOARDS = ("A股全图", "上证A股", "深证A股", "沪深300", "中证A500", "创业板", "科创板")
_KNOWN_METRICS = ("上涨", "平盘", "下跌", "成交额", "比昨日 放量")
_KNOWN_NOTES = ("面积代表流通市值", "颜色代表涨跌幅度", "每8秒更新数据", "双击色块查看K线", "全屏观看效果更好", "按键盘方向键复盘")


@dataclass(frozen=True)
class Site52EtfSnapshot:
    status: str
    source_url: str
    fetched_at: str
    title: str
    boards: tuple[str, ...]
    metrics: tuple[str, ...]
    operating_notes: tuple[str, ...]
    evidence_status: str
    risk_note: str
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.texts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(str(data).split())
        if text:
            self.texts.append(text)


def parse_52etf_public_page(
    html_text: str,
    *,
    source_url: str = SITE52ETF_URL,
    fetched_at: str | None = None,
) -> Site52EtfSnapshot:
    parser = _VisibleTextParser()
    parser.feed(html_text or "")
    texts = tuple(parser.texts)
    visible_text = "\n".join(texts)
    title = "大盘云图" if "大盘云图" in visible_text else ""
    boards = tuple(board for board in _KNOWN_BOARDS if board in visible_text)
    metrics = tuple(metric for metric in _KNOWN_METRICS if metric in visible_text)
    notes = tuple(note for note in _KNOWN_NOTES if note in visible_text)
    evidence_status = "Pass" if title and boards and notes else "Review"
    return Site52EtfSnapshot(
        status="Available" if evidence_status == "Pass" else "Partial",
        source_url=source_url,
        fetched_at=fetched_at or _now_iso(),
        title=title,
        boards=boards,
        metrics=metrics,
        operating_notes=notes,
        evidence_status=evidence_status,
        risk_note="52ETF is used as a public read-only market-cloud reference, not as a broker, order route, or verified historical data provider.",
    )


def fetch_52etf_public_snapshot(
    *,
    source_url: str = SITE52ETF_URL,
    timeout_seconds: int = SITE52ETF_TIMEOUT_SECONDS,
    fetch_html=None,
) -> Site52EtfSnapshot:
    fetched_at = _now_iso()
    try:
        html_text = fetch_html(source_url, timeout_seconds) if fetch_html else _fetch_html(source_url, timeout_seconds)
    except (HTTPError, URLError, TimeoutError, OSError, subprocess.CalledProcessError) as exc:
        return Site52EtfSnapshot(
            status="Unavailable",
            source_url=source_url,
            fetched_at=fetched_at,
            title="",
            boards=(),
            metrics=(),
            operating_notes=(),
            evidence_status="Review",
            risk_note="52ETF reference could not be read; keep the PFI hotspot workflow on local/provider data and retry later.",
            error=str(exc),
        )
    return parse_52etf_public_page(html_text, source_url=source_url, fetched_at=fetched_at)


def build_site52etf_public_snapshot(
    *,
    source_url: str = SITE52ETF_URL,
    timeout_seconds: int = SITE52ETF_TIMEOUT_SECONDS,
    html_text: str | None = None,
    fetch_html=None,
    fetched_at: str | None = None,
) -> dict[str, object]:
    snapshot = (
        parse_52etf_public_page(html_text, source_url=source_url, fetched_at=fetched_at)
        if html_text is not None
        else fetch_52etf_public_snapshot(source_url=source_url, timeout_seconds=timeout_seconds, fetch_html=fetch_html)
    )
    payload = snapshot.to_dict()
    return {
        "schema": SITE52ETF_PUBLIC_SNAPSHOT_SCHEMA,
        "system": "PFI_OS",
        "subsystem": "52ETF Public Market Cloud Snapshot",
        "status": snapshot.status,
        "artifact_status": "Pass" if snapshot.evidence_status == "Pass" and snapshot.status == "Available" else "NeedsReview",
        "source_url": payload["source_url"],
        "source_status": snapshot.status,
        "fetched_at": payload["fetched_at"],
        "title": payload["title"],
        "boards": list(payload["boards"]),
        "metrics": list(payload["metrics"]),
        "operating_notes": list(payload["operating_notes"]),
        "board_count": len(payload["boards"]),
        "metric_count": len(payload["metrics"]),
        "operating_note_count": len(payload["operating_notes"]),
        "refresh_cadence_seconds": _refresh_cadence_seconds(payload["operating_notes"]),
        "interactions": {
            "double_click_kline": "双击色块查看K线" in payload["operating_notes"],
            "keyboard_replay": "按键盘方向键复盘" in payload["operating_notes"],
            "fullscreen_hint": "全屏观看效果更好" in payload["operating_notes"],
        },
        "evidence_status": payload["evidence_status"],
        "evidence_gate": _snapshot_evidence_gate(snapshot),
        "risk_note": payload["risk_note"],
        "error": payload.get("error", ""),
        "token_policy": "Compact public-page contract only; raw HTML is not stored in the snapshot artifact.",
        "safety_boundary": (
            "Read-only public market-cloud reference. No broker calls, no orders, no holdings mutation, no backtest input, "
            "and no replacement for PFI local/provider data-quality gates."
        ),
    }


def write_site52etf_public_snapshot(
    *,
    project_root: Path | str = PROJECT_ROOT,
    output_dir: Path | str | None = None,
    source_url: str = SITE52ETF_URL,
    timeout_seconds: int = SITE52ETF_TIMEOUT_SECONDS,
    html_text: str | None = None,
    fetch_html=None,
    fetched_at: str | None = None,
) -> dict[str, object]:
    root = Path(project_root).expanduser()
    target = Path(output_dir).expanduser() if output_dir else root / SITE52ETF_OUTPUT_RELATIVE
    payload = build_site52etf_public_snapshot(
        source_url=source_url,
        timeout_seconds=timeout_seconds,
        html_text=html_text,
        fetch_html=fetch_html,
        fetched_at=fetched_at,
    )
    target.mkdir(parents=True, exist_ok=True)
    stamp = _date_stamp(str(payload.get("fetched_at", "")))
    dated_path = target / f"Site52ETFPublicSnapshot_{stamp}.json"
    latest_path = target / "Site52ETFPublicSnapshot_latest.json"
    payload["outputs"] = {
        "json": _relative_path(dated_path, root),
        "latest_json": _relative_path(latest_path, root),
    }
    atomic_write_json(dated_path, payload)
    atomic_write_json(latest_path, payload)
    return payload


def load_site52etf_public_snapshot_latest(
    *,
    project_root: Path | str = PROJECT_ROOT,
    latest_path: Path | str | None = None,
) -> dict[str, object] | None:
    root = Path(project_root).expanduser()
    path = Path(latest_path).expanduser() if latest_path else root / SITE52ETF_OUTPUT_RELATIVE / "Site52ETFPublicSnapshot_latest.json"
    payload = read_json_state(path, {}, expected_type=dict, fail_closed=True)
    if payload.get("schema") != SITE52ETF_PUBLIC_SNAPSHOT_SCHEMA:
        return None
    return payload


def site52etf_summary_rows(snapshot: Site52EtfSnapshot | dict[str, object]) -> list[dict[str, str]]:
    payload = snapshot.to_dict() if isinstance(snapshot, Site52EtfSnapshot) else dict(snapshot)
    return [
        {"项目": "来源", "状态": str(payload.get("source_url", "")), "说明": "公开页面，只读参考。"},
        {"项目": "可用性", "状态": str(payload.get("status", "")), "说明": str(payload.get("error", "") or "读取成功。")},
        {"项目": "证据状态", "状态": str(payload.get("evidence_status", "")), "说明": str(payload.get("risk_note", ""))},
        {"项目": "覆盖板块", "状态": ", ".join(payload.get("boards", ()) or ()), "说明": "用于对照 PFI 自有热点对象池。"},
        {"项目": "页面提示", "状态": ", ".join(payload.get("operating_notes", ()) or ()), "说明": "用于学习市场云图交互，不作为交易信号。"},
        {"项目": "读取时间", "状态": str(payload.get("fetched_at", "")), "说明": "本地缓存后展示。"},
        {"项目": "缓存来源", "状态": str(payload.get("schema", "LiveFetch")), "说明": str(payload.get("token_policy", "页面内缓存。"))},
    ]


def build_site52etf_hotspot_comparison(
    snapshot: Site52EtfSnapshot | dict[str, object],
    hotspot_history: pd.DataFrame,
    *,
    market: str,
    snapshot_time: str | None = None,
) -> dict[str, object]:
    payload = snapshot.to_dict() if isinstance(snapshot, Site52EtfSnapshot) else dict(snapshot)
    current = _current_hotspot_slice(hotspot_history, snapshot_time)
    boards = tuple(str(board) for board in (payload.get("boards", ()) or ()))
    matches = _board_matches(boards, current)
    match_count = len(matches)
    available = str(payload.get("status", "")) == "Available" and str(payload.get("evidence_status", "")) == "Pass"
    market_status = "Pass" if str(market).upper() == "CN" else "Review"
    coverage_status = "Pass" if match_count >= 3 else "Review" if match_count else "Block"
    status = "Pass" if available and market_status == "Pass" and coverage_status == "Pass" else "Review"
    strong_count = int(current["hotspot_state"].isin(["强势扩散", "局部偏强"]).sum()) if "hotspot_state" in current.columns else 0
    weak_count = int(current["hotspot_state"].isin(["局部偏弱", "风险降温"]).sum()) if "hotspot_state" in current.columns else 0
    return {
        "schema": SITE52ETF_COMPARISON_SCHEMA,
        "status": status,
        "source_url": str(payload.get("source_url", SITE52ETF_URL)),
        "source_status": str(payload.get("status", "")),
        "source_evidence_status": str(payload.get("evidence_status", "")),
        "market": str(market).upper(),
        "market_status": market_status,
        "coverage_status": coverage_status,
        "board_count": len(boards),
        "matched_board_count": match_count,
        "matched_boards": matches,
        "unmatched_boards": [board for board in boards if board not in {item["board"] for item in matches}],
        "eva_snapshot_time": str(current["snapshot_time"].max()) if not current.empty and "snapshot_time" in current.columns else "",
        "eva_object_count": int(current["symbol"].nunique()) if not current.empty and "symbol" in current.columns else 0,
        "eva_strong_count": strong_count,
        "eva_weak_count": weak_count,
        "comparison_note": (
            "52ETF public page is an A-share market-cloud interaction reference; PFI hotspot analysis uses local/provider "
            "bars, technical heat, evidence gates, and a 3600-second cache. Use this comparison for UI and coverage review only."
        ),
        "safety_boundary": "Read-only comparison; no scraping beyond public page text, broker calls, orders, or holdings mutation.",
    }


def site52etf_comparison_rows(comparison: dict[str, object]) -> list[dict[str, str]]:
    matches = comparison.get("matched_boards", [])
    matched_text = "; ".join(
        f"{item.get('board', '')}: {', '.join(item.get('eva_matches', [])[:3])}"
        for item in matches
        if isinstance(item, dict)
    )
    return [
        {
            "项目": "对照状态",
            "状态": str(comparison.get("status", "")),
            "说明": "Pass 表示公开参考、市场适配和板块映射都可用于只读 UI 对照；Review 只作观察。",
        },
        {
            "项目": "市场适配",
            "状态": str(comparison.get("market_status", "")),
            "说明": f"52ETF 当前公开页是 A 股云图；当前 PFI 市场为 {comparison.get('market', '')}。",
        },
        {
            "项目": "板块映射",
            "状态": f"{comparison.get('matched_board_count', 0)}/{comparison.get('board_count', 0)}",
            "说明": matched_text or "未找到可直接映射的 PFI 热点对象。",
        },
        {
            "项目": "PFI热点切片",
            "状态": str(comparison.get("eva_snapshot_time", "")),
            "说明": f"对象 {comparison.get('eva_object_count', 0)} 个；偏强 {comparison.get('eva_strong_count', 0)} 个；偏弱 {comparison.get('eva_weak_count', 0)} 个。",
        },
        {
            "项目": "口径差异",
            "状态": "Review",
            "说明": str(comparison.get("comparison_note", "")),
        },
        {
            "项目": "安全边界",
            "状态": "Pass",
            "说明": str(comparison.get("safety_boundary", "")),
        },
    ]


def _current_hotspot_slice(hotspot_history: pd.DataFrame, snapshot_time: str | None) -> pd.DataFrame:
    if hotspot_history.empty or "snapshot_time" not in hotspot_history.columns:
        return pd.DataFrame()
    selected = str(snapshot_time or hotspot_history["snapshot_time"].max())
    current = hotspot_history[hotspot_history["snapshot_time"].astype(str).eq(selected)]
    if current.empty:
        latest = str(hotspot_history["snapshot_time"].max())
        current = hotspot_history[hotspot_history["snapshot_time"].astype(str).eq(latest)]
    return current.copy()


def _board_matches(boards: tuple[str, ...], current: pd.DataFrame) -> list[dict[str, object]]:
    if current.empty:
        return []
    terms: list[str] = []
    for column in ["symbol", "name", "sector"]:
        if column in current.columns:
            terms.extend(str(value) for value in current[column].dropna().unique())
    matches = []
    for board in boards:
        tokens = _board_tokens(board)
        eva_matches = sorted({term for term in terms if any(token and token in term for token in tokens)})
        if eva_matches:
            matches.append({"board": board, "eva_matches": eva_matches[:5]})
    return matches


def _board_tokens(board: str) -> tuple[str, ...]:
    mapping = {
        "A股全图": ("A股", "上证", "深证", "沪深", "创业板", "科创"),
        "上证A股": ("上证",),
        "深证A股": ("深证",),
        "沪深300": ("沪深300", "300ETF"),
        "中证A500": ("中证A500", "A500"),
        "创业板": ("创业板",),
        "科创板": ("科创", "科创板"),
    }
    return mapping.get(str(board), (str(board),))


def _fetch_html(source_url: str, timeout_seconds: int) -> str:
    request = Request(source_url, headers={"User-Agent": "PFI/0.2 read-only research reference"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError, OSError):
        return _fetch_html_with_curl(source_url, timeout_seconds)


def _fetch_html_with_curl(source_url: str, timeout_seconds: int) -> str:
    result = subprocess.run(
        [
            "/usr/bin/curl",
            "--location",
            "--silent",
            "--show-error",
            "--max-time",
            str(max(1, int(timeout_seconds))),
            "--user-agent",
            "PFI/0.2 read-only research reference",
            source_url,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _snapshot_evidence_gate(snapshot: Site52EtfSnapshot) -> list[dict[str, str]]:
    return [
        {
            "gate": "SourceReachability",
            "status": "Pass" if snapshot.status in {"Available", "Partial"} else "Review",
            "evidence": f"source_status={snapshot.status}; error={snapshot.error}",
        },
        {
            "gate": "MarketCloudContract",
            "status": "Pass" if snapshot.title and snapshot.boards else "Review",
            "evidence": f"title={snapshot.title}; boards={len(snapshot.boards)}",
        },
        {
            "gate": "InteractionNotes",
            "status": "Pass" if snapshot.operating_notes else "Review",
            "evidence": f"notes={len(snapshot.operating_notes)}; cadence={_refresh_cadence_seconds(snapshot.operating_notes)}",
        },
        {
            "gate": "ReadOnlyBoundary",
            "status": "Pass",
            "evidence": "public page text only; no broker, order, holding, or backtest mutation",
        },
    ]


def _refresh_cadence_seconds(notes: tuple[str, ...] | list[str]) -> int | None:
    for note in notes:
        text = str(note)
        if "每8秒" in text:
            return 8
    return None


def _date_stamp(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d%m%Y")
    except ValueError:
        return datetime.now(timezone.utc).strftime("%d%m%Y")


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.expanduser().resolve().relative_to(root.expanduser().resolve()))
    except (OSError, ValueError):
        return str(path)
