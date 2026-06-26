from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from pfi_os.config import DATA_DIR, PROJECT_ROOT, REPORT_ROOT_DIR


DEFAULT_INDUSTRY_REPORT_DIR = Path.home() / "Downloads" / "行研报告"
DEFAULT_CONSUMER_HOLDINGS_DIRS = (
    PROJECT_ROOT / "data" / "external" / "consumerHoldings",
    Path.home() / "Downloads" / "消费行为分析",
    Path.home() / "Downloads" / "消费行为分析系统",
)
DEFAULT_PFI_HOLDINGS_DIRS = (
    PROJECT_ROOT / "data" / "holdings",
    PROJECT_ROOT / "data" / "external" / "pfi_osHoldings",
)
SUPPORTED_HOLDING_SUFFIXES = {".csv", ".xlsx", ".xls", ".json"}
MAX_HOLDING_SOURCE_FILE_SIZE_BYTES = 20 * 1024 * 1024
IGNORED_HOLDING_FILENAMES = {
    "HoldingsBook.json",
    "HoldingsBook.csv",
    "HoldingsImportHistory.json",
    "HoldingsBook.lock",
    "pending_orders.csv",
    "trade_ledger.csv",
    "orders.csv",
    "transactions.csv",
    "cash_balance.csv",
}
IGNORED_HOLDING_FILENAME_PREFIXES = (
    "video_position_candidates_",
    "video_trade_candidates_",
    "pending_",
    "candidate_",
)


@dataclass(frozen=True)
class IndustryReport:
    name: str
    report_date: str
    category: str
    period: str
    size_kb: float
    modified_time: str
    path: str

    def to_row(self) -> dict[str, object]:
        return {
            "name": self.name,
            "report_date": self.report_date,
            "category": self.category,
            "period": self.period,
            "size_kb": self.size_kb,
            "modified_time": self.modified_time,
            "path": self.path,
        }


def collect_industry_reports(root: Path | str | None = None) -> pd.DataFrame:
    report_root = _industry_report_root(root)
    columns = ["name", "report_date", "category", "period", "size_kb", "modified_time", "path"]
    if not report_root.exists():
        return pd.DataFrame(columns=columns)
    reports = []
    for path in sorted(report_root.rglob("*"), key=lambda item: item.stat().st_mtime if item.is_file() else 0, reverse=True):
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".docx", ".doc", ".md", ".txt"}:
            continue
        reports.append(
            IndustryReport(
                name=path.name,
                report_date=_extract_report_date(path),
                category=_infer_report_category(path.name),
                period=_infer_period(path),
                size_kb=round(path.stat().st_size / 1024, 2),
                modified_time=datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                path=str(path),
            ).to_row()
        )
    return pd.DataFrame(reports, columns=columns)


def filter_industry_reports(
    reports: pd.DataFrame,
    date_from: date | str | None = None,
    date_to: date | str | None = None,
    query: str = "",
) -> pd.DataFrame:
    if reports.empty:
        return reports.copy()
    frame = reports.copy()
    parsed = pd.to_datetime(frame["report_date"], errors="coerce")
    if date_from:
        frame = frame[parsed >= pd.Timestamp(date_from)]
        parsed = pd.to_datetime(frame["report_date"], errors="coerce")
    if date_to:
        frame = frame[parsed <= pd.Timestamp(date_to)]
    normalized_query = query.strip().lower()
    if normalized_query:
        searchable = frame[["name", "category", "period", "path"]].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
        frame = frame[searchable.str.contains(normalized_query, regex=False)]
    return frame.sort_values(["report_date", "modified_time"], ascending=[False, False]).reset_index(drop=True)


def load_holdings_frame(
    consumer_dirs: list[str | Path] | tuple[str | Path, ...] | None = None,
    pfi_os_dirs: list[str | Path] | tuple[str | Path, ...] | None = None,
) -> pd.DataFrame:
    rows = []
    rows.extend(_load_holding_sources(_configured_dirs("PFI_CONSUMER_HOLDINGS_DIR", consumer_dirs or DEFAULT_CONSUMER_HOLDINGS_DIRS), "消费行为分析系统"))
    rows.extend(_load_holding_sources(_configured_dirs("PFI_HOLDINGS_DIR", pfi_os_dirs or DEFAULT_PFI_HOLDINGS_DIRS), "量化回测系统"))
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=holding_columns())
    frame = frame[holding_columns()].copy()
    for column in ["quantity", "cost_basis", "position_value", "unrealized_pnl", "weight"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    if frame["weight"].abs().sum() <= 0 and frame["position_value"].abs().sum() > 0:
        total = frame["position_value"].abs().sum()
        frame["weight"] = frame["position_value"].abs() / total
    return frame.sort_values(["source_system", "weight", "position_value"], ascending=[True, False, False]).reset_index(drop=True)


def load_holding_sources_from_dirs(source_system: str, paths: list[str | Path] | tuple[str | Path, ...]) -> pd.DataFrame:
    rows = _load_holding_sources([Path(item).expanduser() for item in paths], source_system)
    if not rows:
        return pd.DataFrame(columns=holding_columns())
    frame = pd.DataFrame(rows)
    return frame[holding_columns()].copy()


def holding_columns() -> list[str]:
    return _holding_columns()


def holdings_summary(holdings: pd.DataFrame) -> dict[str, Any]:
    if holdings.empty:
        return {
            "total_position_value": 0.0,
            "holding_count": 0,
            "top1_weight": 0.0,
            "top3_weight": 0.0,
            "market_count": 0,
            "source_count": 0,
            "concentration_hhi": 0.0,
        }
    weights = pd.to_numeric(holdings["weight"], errors="coerce").fillna(0.0).abs().sort_values(ascending=False)
    return {
        "total_position_value": float(pd.to_numeric(holdings["position_value"], errors="coerce").fillna(0.0).abs().sum()),
        "holding_count": int(len(holdings)),
        "top1_weight": float(weights.iloc[0]) if not weights.empty else 0.0,
        "top3_weight": float(weights.head(3).sum()) if not weights.empty else 0.0,
        "market_count": int(holdings["market"].replace("", pd.NA).dropna().nunique()),
        "source_count": int(holdings["source_system"].replace("", pd.NA).dropna().nunique()),
        "concentration_hhi": float((weights**2).sum()),
    }


def build_personal_profile(
    holdings: pd.DataFrame,
    runs: pd.DataFrame | None = None,
    reviews: pd.DataFrame | None = None,
    validation_tasks: pd.DataFrame | None = None,
) -> dict[str, Any]:
    runs = runs if isinstance(runs, pd.DataFrame) else pd.DataFrame()
    reviews = reviews if isinstance(reviews, pd.DataFrame) else pd.DataFrame()
    validation_tasks = validation_tasks if isinstance(validation_tasks, pd.DataFrame) else pd.DataFrame()
    summary = holdings_summary(holdings)
    habits = _profile_habits(runs, reviews, validation_tasks)
    risks = _profile_risks(summary, runs, reviews, validation_tasks)
    suggestions = _profile_suggestions(summary, runs, reviews, validation_tasks)
    return {
        "summary": summary,
        "habits": habits,
        "risks": risks,
        "suggestions": suggestions,
    }


def external_system_status(
    industry_report_root: Path | str | None = None,
    consumer_dirs: list[str | Path] | tuple[str | Path, ...] | None = None,
    pfi_os_dirs: list[str | Path] | tuple[str | Path, ...] | None = None,
) -> pd.DataFrame:
    rows = []
    industry_root = _industry_report_root(industry_report_root)
    reports = collect_industry_reports(industry_root)
    rows.append(_status_row("行研报告系统", industry_root, "Ready" if not reports.empty else ("ConfiguredNoData" if industry_root.exists() else "NeedsConfig"), "PDF/Word/文本报告目录"))
    for path in _configured_dirs("PFI_CONSUMER_HOLDINGS_DIR", consumer_dirs or DEFAULT_CONSUMER_HOLDINGS_DIRS):
        rows.append(_status_row("消费行为分析系统持仓", path, _holding_path_status(path), "CSV/XLSX/JSON 持仓数据"))
    for path in _configured_dirs("PFI_HOLDINGS_DIR", pfi_os_dirs or DEFAULT_PFI_HOLDINGS_DIRS):
        rows.append(_status_row("量化回测系统持仓", path, _holding_path_status(path), "CSV/XLSX/JSON 持仓数据"))
    return pd.DataFrame(rows)


def _status_row(name: str, path: Path, status: str, expected: str) -> dict[str, object]:
    return {
        "system": name,
        "status": status,
        "path": str(path),
        "expected": expected,
    }


def _industry_report_root(root: Path | str | None = None) -> Path:
    configured = os.getenv("PFI_INDUSTRY_REPORT_DIR", "").strip()
    if root is not None:
        return Path(root).expanduser()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_INDUSTRY_REPORT_DIR


def _configured_dirs(env_name: str, defaults: list[str | Path] | tuple[str | Path, ...]) -> list[Path]:
    configured = os.getenv(env_name, "").strip()
    if configured:
        return [Path(item).expanduser() for item in configured.split(":") if item.strip()]
    return [Path(item).expanduser() for item in defaults]


def _load_holding_sources(paths: list[Path], source_system: str) -> list[dict[str, object]]:
    rows = []
    seen_files: set[str] = set()
    for path in paths:
        files = _supported_files(path)
        for file_path in files:
            file_key = str(file_path.resolve())
            if file_key in seen_files:
                continue
            seen_files.add(file_key)
            frame = _read_holding_file(file_path)
            for row in frame.to_dict("records"):
                rows.append(_normalize_holding_row(row, file_path, source_system))
    return rows


def _supported_files(path: Path) -> list[Path]:
    expanded = path.expanduser()
    if expanded.name in IGNORED_HOLDING_FILENAMES or expanded.is_symlink():
        return []
    if expanded.is_file():
        return [expanded] if _is_supported_holding_file(expanded) else []
    if not expanded.exists() or not expanded.is_dir():
        return []
    return [
        item
        for item in sorted(expanded.rglob("*"), key=lambda p: p.stat().st_mtime if p.is_file() else 0, reverse=True)
        if _is_supported_holding_file(item)
    ]


def _holding_path_status(path: Path) -> str:
    if not path.expanduser().exists():
        return "NeedsConfig"
    files = _supported_files(path)
    if not files:
        return "ConfiguredNoData"
    return "Ready" if any(not _read_holding_file(file).empty for file in files[:10]) else "ConfiguredInvalid"


def _is_supported_holding_file(path: Path) -> bool:
    if path.is_symlink() or path.name in IGNORED_HOLDING_FILENAMES:
        return False
    if any(path.name.startswith(prefix) for prefix in IGNORED_HOLDING_FILENAME_PREFIXES):
        return False
    if not path.is_file() or path.suffix.lower() not in SUPPORTED_HOLDING_SUFFIXES:
        return False
    try:
        return path.stat().st_size <= MAX_HOLDING_SOURCE_FILE_SIZE_BYTES
    except OSError:
        return False


def _read_holding_file(path: Path) -> pd.DataFrame:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        if path.suffix.lower() == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return pd.DataFrame(raw)
            if isinstance(raw, dict):
                for key in ["holdings", "positions", "data", "items"]:
                    if isinstance(raw.get(key), list):
                        return pd.DataFrame(raw[key])
                return pd.DataFrame([raw])
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()


def _normalize_holding_row(row: dict[str, Any], path: Path, source_system: str) -> dict[str, object]:
    return {
        "source_system": source_system,
        "source_file": _source_file_label(path),
        "symbol": _value(row, "symbol", "代码", "证券代码", "标的", "ticker"),
        "name": _value(row, "name", "名称", "证券名称", "标的名称"),
        "market": _value(row, "market", "市场", "交易所", "exchange"),
        "quantity": _float(_value(row, "quantity", "持仓数量", "数量", "份额", "units", "shares", "volume")),
        "cost_basis": _float(_value(row, "cost_basis", "成本", "持仓成本", "成本价", "average_cost", "cost")),
        "position_value": _float(_value(row, "position_value", "持仓金额", "市值", "market_value", "value", "amount", "资产金额")),
        "unrealized_pnl": _float(_value(row, "unrealized_pnl", "浮动盈亏", "未实现盈亏", "持仓收益", "holding_return_amount", "pnl", "profit")),
        "weight": _float(_value(row, "weight", "权重", "比例", "position_weight")),
        "updated_at": _value(row, "updated_at", "更新时间", "日期", "date"),
        "source_modified_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else "",
    }


def _source_file_label(path: Path) -> str:
    try:
        parent = path.parent.name
        return f"{parent}/{path.name}" if parent else path.name
    except Exception:
        return path.name


def _holding_columns() -> list[str]:
    return [
        "source_system",
        "source_file",
        "symbol",
        "name",
        "market",
        "quantity",
        "cost_basis",
        "position_value",
        "unrealized_pnl",
        "weight",
        "updated_at",
        "source_modified_time",
    ]


def _value(row: dict[str, Any], *keys: str) -> object:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        if key in row:
            return row[key]
        lower = key.strip().lower()
        if lower in normalized:
            return normalized[lower]
    return ""


def _extract_report_date(path: Path) -> str:
    text = " ".join([path.name, *path.parts[-3:]])
    for pattern in [r"(?<!\d)(\d{2})(\d{2})(20\d{2})(?!\d)", r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)"]:
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            if len(match.group(1)) == 2:
                day, month, year = match.group(1), match.group(2), match.group(3)
            else:
                year, month, day = match.group(1), match.group(2), match.group(3)
            return date(int(year), int(month), int(day)).isoformat()
        except ValueError:
            continue
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def _infer_report_category(name: str) -> str:
    for keyword in ["盘前", "盘中", "盘后", "K线", "周一", "周报", "月报", "策略", "行业"]:
        if keyword.lower() in name.lower():
            return keyword
    return "未分类"


def _infer_period(path: Path) -> str:
    for part in reversed(path.parts):
        if re.search(r"\d{4}|\d{2}\d{2}", part):
            return part
    return ""


def _profile_habits(runs: pd.DataFrame, reviews: pd.DataFrame, validation_tasks: pd.DataFrame) -> list[dict[str, str]]:
    habits = []
    if not runs.empty:
        habits.append({"维度": "研究频率", "观察": f"已记录 {len(runs)} 次回测运行。"})
        if "research_status" in runs.columns:
            needs = int((runs["research_status"].astype(str) == "NeedsMoreEvidence").sum())
            habits.append({"维度": "证据习惯", "观察": f"其中 {needs} 次研究状态为 NeedsMoreEvidence。"})
    else:
        habits.append({"维度": "研究频率", "观察": "暂无可读取的回测运行元数据。"})
    if not reviews.empty:
        discipline_rate = pd.to_numeric(reviews.get("executed_as_planned", False), errors="coerce").fillna(0).mean()
        habits.append({"维度": "复盘纪律", "观察": f"已记录 {len(reviews)} 条复盘，按计划执行率约 {discipline_rate:.2%}。"})
    else:
        habits.append({"维度": "复盘纪律", "观察": "暂无复盘记录，行为偏差只能初步判断。"})
    if not validation_tasks.empty:
        pending = int((validation_tasks["status"].astype(str) == "待验证").sum())
        habits.append({"维度": "验证队列", "观察": f"验证任务 {len(validation_tasks)} 条，其中待验证 {pending} 条。"})
    return habits


def _profile_risks(summary: dict[str, Any], runs: pd.DataFrame, reviews: pd.DataFrame, validation_tasks: pd.DataFrame) -> list[dict[str, str]]:
    risks = []
    if summary["holding_count"] <= 0:
        risks.append({"风险": "持仓数据缺失", "说明": "未读取到消费行为分析系统或 PFI OS 持仓数据，无法判断真实组合集中度。"})
    if summary["top1_weight"] >= 0.35:
        risks.append({"风险": "单一标的集中", "说明": f"最大单一标的权重约 {summary['top1_weight']:.2%}。"})
    if summary["top3_weight"] >= 0.65:
        risks.append({"风险": "前三持仓集中", "说明": f"前三持仓权重约 {summary['top3_weight']:.2%}。"})
    if not runs.empty and "missing_evidence_count" in runs.columns:
        avg_missing = pd.to_numeric(runs["missing_evidence_count"], errors="coerce").fillna(0).mean()
        if avg_missing > 0:
            risks.append({"风险": "证据链不完整", "说明": f"历史回测平均缺失证据数约 {avg_missing:.2f}。"})
    if not reviews.empty:
        for column, label in [("news_impulse", "新闻冲动"), ("emotional_add", "情绪补仓"), ("chase_up", "追高"), ("discipline_violation", "纪律违反")]:
            if column in reviews.columns and reviews[column].astype(bool).mean() > 0:
                risks.append({"风险": label, "说明": f"复盘记录中出现过 {label}。"})
    if not validation_tasks.empty and (validation_tasks["status"].astype(str) == "待验证").sum() >= 3:
        risks.append({"风险": "待验证积压", "说明": "待验证任务较多，研究结论可能滞后。"})
    return risks or [{"风险": "暂无高优先级风险", "说明": "当前可读数据未触发主要风险规则。"}]


def _profile_suggestions(summary: dict[str, Any], runs: pd.DataFrame, reviews: pd.DataFrame, validation_tasks: pd.DataFrame) -> list[dict[str, str]]:
    suggestions = []
    if summary["holding_count"] <= 0:
        suggestions.append({"建议": "配置持仓数据", "行动": "把消费行为分析系统或 PFI OS 持仓 CSV/XLSX/JSON 放入 data/external/consumerHoldings 或 data/holdings。"})
    if summary["top1_weight"] >= 0.35 or summary["top3_weight"] >= 0.65:
        suggestions.append({"建议": "降低集中度风险", "行动": "先用组合风险视图观察单一标的和前三持仓冲击，不直接生成实盘调仓指令。"})
    if not runs.empty and "research_status" in runs.columns and (runs["research_status"].astype(str) == "NeedsMoreEvidence").sum() > 0:
        suggestions.append({"建议": "补齐关键证据", "行动": "优先补多源交叉校验、样本外验证、walk-forward 和数据质量检查。"})
    if validation_tasks.empty:
        suggestions.append({"建议": "建立验证任务", "行动": "把行研报告中的研究假设拆成待验证信号，进入验证任务队列。"})
    if reviews.empty:
        suggestions.append({"建议": "补复盘记录", "行动": "把实际执行偏差、情绪原因和最终盈亏记录到复盘错误页签。"})
    return suggestions


def _float(value: object) -> float:
    try:
        text = str(value).strip().replace(",", "").replace("%", "")
        if text == "":
            return 0.0
        number = float(text)
        return number / 100 if "%" in str(value) else number
    except (TypeError, ValueError):
        return 0.0
