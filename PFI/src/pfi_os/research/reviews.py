from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from pfi_os.config import DATA_DIR
from pfi_os.storage import locked_json_update, read_json_state


TRADE_REVIEW_DIR = DATA_DIR / "reviews"
TRADE_REVIEW_PATH = TRADE_REVIEW_DIR / "TradeReviewRecords.json"

ERROR_TYPES = (
    "信息错误",
    "估值错误",
    "时间错误",
    "仓位错误",
    "纪律错误",
    "情绪错误",
    "成本错误",
    "数据错误",
    "外部冲击",
    "运气因素",
    "无明显错误",
)

RETURN_ATTRIBUTION_TYPES = (
    "风险溢价",
    "行为偏差",
    "信息优势",
    "结构性约束",
    "执行优势",
    "组合优势",
    "未确认",
)

ACTION_TYPES = ("增加暴露", "降低暴露", "保持观察", "复盘记录")


@dataclass(frozen=True)
class TradeReviewRecord:
    review_id: str
    created_at: str
    symbol: str
    market: str
    strategy_id: str
    research_status: str
    decision_quality_score: int
    action_type: str
    planned_exposure_amount: float
    planned_exposure_ratio: float
    original_plan: str
    observation_reason: str
    backtest_reference: str
    actual_execution_time: str
    actual_price: float
    executed_as_planned: bool
    discipline_violation: bool
    early_exit: bool
    news_impulse: bool
    emotional_add: bool
    chase_up: bool
    final_pnl_amount: float
    final_pnl_ratio: float
    return_attribution: str
    error_type: str
    market_environment: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_trade_review_record(payload: dict[str, Any]) -> TradeReviewRecord:
    return TradeReviewRecord(
        review_id=str(payload.get("review_id") or f"review_{uuid4().hex[:12]}"),
        created_at=str(payload.get("created_at") or datetime.now().isoformat(timespec="seconds")),
        symbol=str(payload.get("symbol", "")).strip(),
        market=str(payload.get("market", "")).strip(),
        strategy_id=str(payload.get("strategy_id", "")).strip(),
        research_status=str(payload.get("research_status", "")).strip(),
        decision_quality_score=int(_safe_float(payload.get("decision_quality_score", 0))),
        action_type=_choice(payload.get("action_type"), ACTION_TYPES, "复盘记录"),
        planned_exposure_amount=_safe_float(payload.get("planned_exposure_amount", 0.0)),
        planned_exposure_ratio=_safe_float(payload.get("planned_exposure_ratio", 0.0)),
        original_plan=str(payload.get("original_plan", "")).strip(),
        observation_reason=str(payload.get("observation_reason", "")).strip(),
        backtest_reference=str(payload.get("backtest_reference", "")).strip(),
        actual_execution_time=str(payload.get("actual_execution_time", "")).strip(),
        actual_price=_safe_float(payload.get("actual_price", 0.0)),
        executed_as_planned=bool(payload.get("executed_as_planned", False)),
        discipline_violation=bool(payload.get("discipline_violation", False)),
        early_exit=bool(payload.get("early_exit", False)),
        news_impulse=bool(payload.get("news_impulse", False)),
        emotional_add=bool(payload.get("emotional_add", False)),
        chase_up=bool(payload.get("chase_up", False)),
        final_pnl_amount=_safe_float(payload.get("final_pnl_amount", 0.0)),
        final_pnl_ratio=_safe_float(payload.get("final_pnl_ratio", 0.0)),
        return_attribution=_choice(payload.get("return_attribution"), RETURN_ATTRIBUTION_TYPES, "未确认"),
        error_type=_choice(payload.get("error_type"), ERROR_TYPES, "未确认") if str(payload.get("error_type", "")).strip() else "未确认",
        market_environment=str(payload.get("market_environment", "")).strip(),
        notes=str(payload.get("notes", "")).strip(),
    )


def load_trade_reviews(path: Path | str = TRADE_REVIEW_PATH) -> list[TradeReviewRecord]:
    review_path = Path(path)
    records = read_json_state(review_path, [], expected_type=list)
    return [create_trade_review_record(item) for item in records if isinstance(item, dict)]


def save_trade_review_record(record: TradeReviewRecord, path: Path | str = TRADE_REVIEW_PATH) -> Path:
    review_path = Path(path)

    def append_review(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item for item in records if isinstance(item, dict)] + [record.to_dict()]

    return locked_json_update(review_path, [], append_review, expected_type=list)


def trade_review_frame(path: Path | str = TRADE_REVIEW_PATH) -> pd.DataFrame:
    records = load_trade_reviews(path)
    if not records:
        return pd.DataFrame(columns=_review_columns())
    frame = pd.DataFrame([record.to_dict() for record in records])
    return frame[_review_columns()]


def review_dashboard_cards(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return [
            {"label": "复盘记录", "value": 0, "help": "已保存的研究复盘记录数量"},
            {"label": "纪律执行率", "value": "N/A", "help": "按计划执行的记录占比"},
            {"label": "平均盈亏", "value": "N/A", "help": "已记录最终盈亏的平均值"},
            {"label": "最常见错误", "value": "N/A", "help": "出现次数最多的错误类型"},
        ]
    executed = frame["executed_as_planned"].astype(bool)
    pnl = pd.to_numeric(frame["final_pnl_amount"], errors="coerce").fillna(0.0)
    error_type = frame["error_type"].astype(str).replace("", "未确认")
    common_error = error_type.value_counts().index[0] if not error_type.empty else "N/A"
    return [
        {"label": "复盘记录", "value": int(len(frame)), "help": "已保存的研究复盘记录数量"},
        {"label": "纪律执行率", "value": f"{executed.mean():.2%}", "help": "按计划执行的记录占比"},
        {"label": "平均盈亏", "value": f"{pnl.mean():,.2f}", "help": "已记录最终盈亏的平均值"},
        {"label": "最常见错误", "value": common_error, "help": "出现次数最多的错误类型"},
    ]


def error_profile_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["error_type", "count", "avg_pnl", "avg_pnl_ratio", "discipline_violation_rate"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    work = frame.copy()
    work["error_type"] = work["error_type"].astype(str).replace("", "未确认")
    work["final_pnl_amount"] = pd.to_numeric(work["final_pnl_amount"], errors="coerce").fillna(0.0)
    work["final_pnl_ratio"] = pd.to_numeric(work["final_pnl_ratio"], errors="coerce").fillna(0.0)
    work["discipline_violation"] = work["discipline_violation"].astype(bool)
    grouped = (
        work.groupby("error_type", dropna=False)
        .agg(
            count=("error_type", "size"),
            avg_pnl=("final_pnl_amount", "mean"),
            avg_pnl_ratio=("final_pnl_ratio", "mean"),
            discipline_violation_rate=("discipline_violation", "mean"),
        )
        .reset_index()
        .sort_values(["count", "avg_pnl"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return grouped[columns]


def _review_columns() -> list[str]:
    return [
        "review_id",
        "created_at",
        "symbol",
        "market",
        "strategy_id",
        "research_status",
        "decision_quality_score",
        "action_type",
        "planned_exposure_amount",
        "planned_exposure_ratio",
        "original_plan",
        "observation_reason",
        "backtest_reference",
        "actual_execution_time",
        "actual_price",
        "executed_as_planned",
        "discipline_violation",
        "early_exit",
        "news_impulse",
        "emotional_add",
        "chase_up",
        "final_pnl_amount",
        "final_pnl_ratio",
        "return_attribution",
        "error_type",
        "market_environment",
        "notes",
    ]


def _choice(value: object, options: tuple[str, ...], default: str) -> str:
    text = str(value or "").strip()
    return text if text in options else default


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
