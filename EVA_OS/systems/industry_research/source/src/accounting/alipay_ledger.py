from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.config import ROOT
from src.data_io import read_csv, write_csv

ALIPAY_DIR = ROOT / "data" / "private" / "alipay"
TIMEZONE = "Australia/Sydney"

CURRENT_POSITIONS = ALIPAY_DIR / "current_positions.csv"
TRADE_LEDGER = ALIPAY_DIR / "trade_ledger.csv"
PENDING_ORDERS = ALIPAY_DIR / "pending_orders.csv"
DAILY_UPDATE_LOG = ALIPAY_DIR / "daily_update_log.csv"
IMPORT_LOG = ALIPAY_DIR / "import_log.csv"
RAW_TRANSACTION_FIELDS = [
    "transaction_time",
    "category",
    "counterparty",
    "description",
    "direction",
    "amount",
    "payment_method",
    "status",
    "transaction_id",
    "merchant_order_id",
    "notes",
]

POSITION_FIELDS = [
    "date",
    "source",
    "symbol",
    "name",
    "asset_type",
    "amount",
    "weight",
    "holding_return_amount",
    "holding_return_pct",
    "daily_return_amount",
    "daily_return_pct",
    "units",
    "cost",
    "available_units",
    "status",
    "notes",
]

TRADE_FIELDS = [
    "trade_date",
    "order_time",
    "timezone",
    "symbol",
    "name",
    "side",
    "order_type",
    "order_amount",
    "confirmed_amount",
    "confirmed_units",
    "confirmed_nav",
    "fee",
    "status",
    "source",
    "source_path",
    "notes",
]

UPDATE_FIELDS = [
    "date",
    "updated_at",
    "timezone",
    "status",
    "source_type",
    "source_path",
    "positions_count",
    "trades_count",
    "pending_count",
    "notes",
]

IMPORT_FIELDS = [
    "imported_at",
    "timezone",
    "source_path",
    "source_start_time",
    "source_end_time",
    "total_rows",
    "investment_rows",
    "fund_trade_rows",
    "pending_rows",
    "raw_output_path",
    "notes",
]

UPDATE_STATUSES = {"received", "parsed", "confirmed", "no_trade", "needs_confirmation"}
CANDIDATE_POSITION_STATUSES = {
    "candidate",
    "video_candidate",
    "needs_confirmation",
    "video_visible",
    "video_visible_lowres",
    "carried_forward_unverified",
}
UNVERIFIED_POSITION_STATUSES = {"video_visible_lowres", "carried_forward_unverified"}


@dataclass(frozen=True)
class UpdateSummary:
    start_date: str
    end_date: str
    updated_dates: list[str]
    missing_dates: list[str]
    log_rows: list[dict[str, str]]

    @property
    def updated_count(self) -> int:
        return len(self.updated_dates)

    @property
    def missing_count(self) -> int:
        return len(self.missing_dates)


def ensure_alipay_files() -> None:
    ALIPAY_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_csv(CURRENT_POSITIONS, POSITION_FIELDS)
    _ensure_csv(TRADE_LEDGER, TRADE_FIELDS)
    _ensure_csv(PENDING_ORDERS, TRADE_FIELDS)
    _ensure_csv(DAILY_UPDATE_LOG, UPDATE_FIELDS)
    _ensure_csv(IMPORT_LOG, IMPORT_FIELDS)


def load_current_positions() -> list[dict[str, str]]:
    ensure_alipay_files()
    rows = read_csv(CURRENT_POSITIONS)
    return [row for row in rows if _is_effective_position(row)]


def load_pending_orders() -> list[dict[str, str]]:
    ensure_alipay_files()
    rows = read_csv(PENDING_ORDERS)
    return [row for row in rows if row.get("name") or row.get("symbol")]


def load_position_candidates(as_of: str | None = None) -> list[dict[str, str]]:
    ensure_alipay_files()
    path = _candidate_position_path(as_of)
    if path and path.exists():
        return read_csv(path)
    candidates = sorted(ALIPAY_DIR.glob("video_position_candidates_*.csv"), reverse=True)
    for candidate in candidates:
        rows = read_csv(candidate)
        if rows:
            return rows
    return []


def build_account_summary(
    positions: list[dict[str, str]] | None = None,
    pending_orders: list[dict[str, str]] | None = None,
    as_of: str | None = None,
) -> dict[str, object]:
    ensure_alipay_files()
    positions = positions if positions is not None else load_current_positions()
    pending_orders = pending_orders if pending_orders is not None else load_pending_orders()
    if positions:
        return _summary_from_positions(positions, pending_orders)
    return _summary_from_latest_video(pending_orders, as_of)


def record_update(
    update_date: str,
    source_type: str,
    source_path: str = "",
    status: str = "received",
    notes: str = "",
    positions_count: int = 0,
    trades_count: int = 0,
    pending_count: int = 0,
) -> dict[str, str]:
    if status not in UPDATE_STATUSES:
        raise ValueError(f"Unsupported Alipay update status {status!r}; expected one of {sorted(UPDATE_STATUSES)}.")
    date.fromisoformat(update_date)
    ensure_alipay_files()
    rows = read_csv(DAILY_UPDATE_LOG)
    now = datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec="seconds")
    row = {
        "date": update_date,
        "updated_at": now,
        "timezone": TIMEZONE,
        "status": status,
        "source_type": source_type,
        "source_path": source_path,
        "positions_count": str(positions_count),
        "trades_count": str(trades_count),
        "pending_count": str(pending_count),
        "notes": notes,
    }
    rows.append(row)
    write_csv(DAILY_UPDATE_LOG, _normalize_rows(rows, UPDATE_FIELDS))
    return row


def summarize_updates(
    start_date: str | None = None,
    end_date: str | None = None,
    weekdays_only: bool = True,
) -> UpdateSummary:
    ensure_alipay_files()
    rows = read_csv(DAILY_UPDATE_LOG)
    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    end = date.fromisoformat(end_date) if end_date else today
    if start_date:
        start = date.fromisoformat(start_date)
    elif rows:
        start = min(date.fromisoformat(row["date"]) for row in rows if row.get("date"))
    else:
        start = end
    updated = {
        row["date"]
        for row in rows
        if row.get("date") and row.get("status") in {"received", "parsed", "confirmed", "no_trade", "needs_confirmation"}
    }
    expected = [item.isoformat() for item in _date_range(start, end, weekdays_only=weekdays_only)]
    updated_dates = [item for item in expected if item in updated]
    missing_dates = [item for item in expected if item not in updated]
    return UpdateSummary(
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        updated_dates=updated_dates,
        missing_dates=missing_dates,
        log_rows=rows,
    )


def format_update_summary(summary: UpdateSummary) -> str:
    updated = ", ".join(summary.updated_dates) if summary.updated_dates else "无"
    missing = ", ".join(summary.missing_dates) if summary.missing_dates else "无"
    details = _update_status_details(summary)
    return (
        f"Alipay update coverage {summary.start_date} to {summary.end_date}\n"
        f"updated_days={summary.updated_count}: {updated}\n"
        f"missing_days={summary.missing_count}: {missing}"
        + (f"\n{details}" if details else "")
    )


def alipay_execution_state(summary: UpdateSummary, as_of: str) -> dict[str, object]:
    rows = [row for row in summary.log_rows if row.get("date") == as_of]
    if not rows or as_of in summary.missing_dates:
        return {
            "status": "missing",
            "execution_confirmed": False,
            "execution_blocked": True,
            "block_reason": f"{as_of} 无支付宝流水/持仓更新记录",
            "source_type": "",
            "source_path": "",
            "updated_at": "",
        }
    latest = sorted(rows, key=lambda row: row.get("updated_at", ""))[-1]
    status = str(latest.get("status") or "unknown")
    source_type = str(latest.get("source_type") or "")
    source_path = str(latest.get("source_path") or "")
    confirmed = status in {"confirmed", "parsed", "no_trade"}
    if confirmed:
        reason = "当日支付宝更新已达到报告执行计算口径"
    elif status == "needs_confirmation":
        reason = "当日资料为视频/截图/OCR候选数据，仍需官方CSV或人工确认后才能用于执行金额"
    elif status == "received":
        reason = "当日资料已收到但尚未解析确认，不能用于执行金额"
    else:
        reason = f"当日支付宝更新状态为{status}，未达到执行金额计算口径"
    return {
        "status": status,
        "execution_confirmed": confirmed,
        "execution_blocked": not confirmed,
        "block_reason": reason,
        "source_type": source_type,
        "source_path": source_path,
        "updated_at": str(latest.get("updated_at") or ""),
    }


def _update_status_details(summary: UpdateSummary) -> str:
    rows = []
    for update_date in summary.updated_dates:
        state = alipay_execution_state(summary, update_date)
        execution = "confirmed" if state["execution_confirmed"] else "blocked"
        source = str(state.get("source_type") or "unknown")
        updated_at = str(state.get("updated_at") or "unknown")
        reason = str(state.get("block_reason") or "")
        rows.append(
            f"update_status[{update_date}]: status={state['status']}; execution={execution}; source={source}; updated_at={updated_at}; reason={reason}"
        )
    return "\n".join(rows)


def write_video_observations(
    update_date: str,
    account_rows: list[dict[str, object]],
    position_rows: list[dict[str, object]],
    trade_rows: list[dict[str, object]],
) -> dict[str, Path]:
    ensure_alipay_files()
    suffix = update_date.replace("-", "")
    account_path = ALIPAY_DIR / f"video_account_summary_{suffix}.csv"
    positions_path = ALIPAY_DIR / f"video_position_candidates_{suffix}.csv"
    trades_path = ALIPAY_DIR / f"video_trade_candidates_{suffix}.csv"
    if account_rows:
        write_csv(account_path, account_rows)
    if position_rows:
        write_csv(positions_path, position_rows)
    if trade_rows:
        write_csv(trades_path, trade_rows)
    return {"account": account_path, "positions": positions_path, "trades": trades_path}


def import_alipay_transactions(path: str | Path) -> dict[str, object]:
    ensure_alipay_files()
    source = Path(path)
    parsed = _read_alipay_export(source)
    raw_rows = [_raw_transaction_row(row) for row in parsed["rows"]]
    suffix = _range_suffix(str(parsed.get("source_start_time") or ""), str(parsed.get("source_end_time") or ""))
    raw_output_path = ALIPAY_DIR / f"raw_transactions_{suffix}.csv"
    write_csv(raw_output_path, raw_rows)

    fund_rows = [_fund_trade_row(row, str(source)) for row in parsed["rows"] if _is_fund_trade(row)]
    pending_rows = [row for row in fund_rows if _is_pending_status(str(row.get("status", "")))]
    confirmed_rows = [row for row in fund_rows if not _is_pending_status(str(row.get("status", "")))]
    write_csv(TRADE_LEDGER, confirmed_rows)
    write_csv(PENDING_ORDERS, pending_rows)

    imported_at = datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec="seconds")
    log_rows = read_csv(IMPORT_LOG)
    log_row = {
        "imported_at": imported_at,
        "timezone": TIMEZONE,
        "source_path": str(source),
        "source_start_time": str(parsed.get("source_start_time", "")),
        "source_end_time": str(parsed.get("source_end_time", "")),
        "total_rows": str(len(parsed["rows"])),
        "investment_rows": str(sum(1 for row in parsed["rows"] if _is_investment_row(row))),
        "fund_trade_rows": str(len(fund_rows)),
        "pending_rows": str(len(pending_rows)),
        "raw_output_path": str(raw_output_path),
        "notes": "Imported from official Alipay transaction detail CSV; personal header metadata is not copied into raw transaction output.",
    }
    log_rows.append(log_row)
    write_csv(IMPORT_LOG, _normalize_rows(log_rows, IMPORT_FIELDS))

    if parsed.get("source_end_time"):
        update_date = str(parsed["source_end_time"])[:10]
        record_update(
            update_date=update_date,
            source_type="csv",
            source_path=str(source),
            status="confirmed",
            notes=f"Imported official Alipay transaction detail CSV covering {parsed.get('source_start_time')} to {parsed.get('source_end_time')}.",
            positions_count=0,
            trades_count=len(fund_rows),
            pending_count=len(pending_rows),
        )
    return {
        "source_path": str(source),
        "source_start_time": parsed.get("source_start_time", ""),
        "source_end_time": parsed.get("source_end_time", ""),
        "total_rows": len(parsed["rows"]),
        "investment_rows": sum(1 for row in parsed["rows"] if _is_investment_row(row)),
        "fund_trade_rows": len(fund_rows),
        "confirmed_trade_rows": len(confirmed_rows),
        "pending_rows": len(pending_rows),
        "raw_output_path": str(raw_output_path),
        "trade_ledger_path": str(TRADE_LEDGER),
        "pending_orders_path": str(PENDING_ORDERS),
    }


def confirm_current_positions(
    update_date: str,
    *,
    source_path: str = "",
    notes: str = "",
    allow_unverified: bool = False,
) -> dict[str, object]:
    date.fromisoformat(update_date)
    ensure_alipay_files()
    rows = read_csv(CURRENT_POSITIONS)
    target_rows = [row for row in rows if row.get("date") == update_date and _is_effective_position(row)]
    if not target_rows:
        raise ValueError(f"No current position rows are available for {update_date}.")

    unverified = [
        row
        for row in target_rows
        if str(row.get("status") or "").strip().lower() in UNVERIFIED_POSITION_STATUSES
    ]
    if unverified and not allow_unverified:
        names = ", ".join(row.get("name", "") for row in unverified[:5])
        more = "..." if len(unverified) > 5 else ""
        raise ValueError(
            "Position confirmation is blocked because low-confidence rows exist. "
            f"Review or provide official evidence before confirming: {names}{more}"
        )

    confirmed_rows = []
    for row in rows:
        if row.get("date") != update_date or not _is_effective_position(row):
            confirmed_rows.append(row)
            continue
        updated = dict(row)
        updated["source"] = "alipay_manual_confirmed"
        updated["status"] = "confirmed_manual"
        base_notes = str(updated.get("notes") or "")
        confirmation_note = f"manual_confirmed_at={datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec='seconds')}"
        if source_path:
            confirmation_note += f"; confirmation_source={Path(source_path).name}"
        if notes:
            confirmation_note += f"; confirmation_notes={notes}"
        updated["notes"] = f"{base_notes}; {confirmation_note}" if base_notes else confirmation_note
        confirmed_rows.append(updated)

    write_csv(CURRENT_POSITIONS, _normalize_rows(confirmed_rows, POSITION_FIELDS))
    log_row = record_update(
        update_date=update_date,
        source_type="manual",
        source_path=source_path,
        status="confirmed",
        notes=notes or "Manually confirmed current_positions.csv candidate rows for execution calculations.",
        positions_count=len(target_rows),
        trades_count=0,
        pending_count=len(load_pending_orders()),
    )
    return {
        "date": update_date,
        "confirmed_positions": len(target_rows),
        "unverified_rows": len(unverified),
        "allow_unverified": allow_unverified,
        "current_positions_path": str(CURRENT_POSITIONS),
        "update_log_path": str(DAILY_UPDATE_LOG),
        "log_row": log_row,
    }


def _summary_from_positions(
    positions: list[dict[str, str]],
    pending_orders: list[dict[str, str]],
) -> dict[str, object]:
    total_amount = sum(_safe_float(row.get("amount") or row.get("holding_amount")) for row in positions)
    total_return_amount = sum(_position_return_amount(row) for row in positions)
    total_daily_return = sum(_safe_float(row.get("daily_return_amount")) for row in positions)
    cost_basis = total_amount - total_return_amount
    statuses = {str(row.get("status") or "").strip().lower() for row in positions}
    is_candidate = bool(statuses & CANDIDATE_POSITION_STATUSES)
    return {
        "source_status": "video_candidate" if is_candidate else "confirmed_positions",
        "source_label": "支付宝视频候选持仓" if is_candidate else "支付宝确认持仓",
        "total_holding_amount": total_amount,
        "total_holding_return_amount": total_return_amount,
        "total_holding_return_pct": total_return_amount / cost_basis if cost_basis > 0 else 0.0,
        "daily_return_amount": total_daily_return,
        "daily_return_pct": total_daily_return / total_amount if total_amount > 0 else 0.0,
        "position_count": len(positions),
        "pending_order_count": len(pending_orders),
        "pending_order_amount": sum(_safe_float(row.get("order_amount")) for row in pending_orders),
        "notes": "基于 current_positions.csv 的视频候选持仓汇总；需用官方导出文件核对。" if is_candidate else "基于 current_positions.csv 的确认持仓汇总。",
    }


def _summary_from_latest_video(pending_orders: list[dict[str, str]], as_of: str | None) -> dict[str, object]:
    row = _latest_video_account_row(as_of)
    if not row:
        return {
            "source_status": "missing",
            "source_label": "未导入确认持仓",
            "total_holding_amount": 0.0,
            "total_holding_return_amount": 0.0,
            "total_holding_return_pct": 0.0,
            "daily_return_amount": 0.0,
            "daily_return_pct": 0.0,
            "position_count": 0,
            "pending_order_count": len(pending_orders),
            "pending_order_amount": sum(_safe_float(item.get("order_amount")) for item in pending_orders),
            "notes": "尚无确认持仓。请导入支付宝持仓截图、CSV、Excel 或 PDF 后再生成完整实盘结论。",
        }
    total_amount = _safe_float(row.get("total_assets") or row.get("account_total_assets"))
    return_amount = _safe_float(row.get("holding_return_amount"))
    daily_return = _safe_float(row.get("yesterday_return_amount"))
    pending_amount = max(
        _safe_float(row.get("pending_buy_amount")),
        sum(_safe_float(item.get("order_amount")) for item in pending_orders),
    )
    cost_basis = total_amount - return_amount
    return {
        "source_status": "video_candidate",
        "source_label": "支付宝视频候选数据",
        "total_holding_amount": total_amount,
        "total_holding_return_amount": return_amount,
        "total_holding_return_pct": return_amount / cost_basis if cost_basis > 0 else 0.0,
        "daily_return_amount": daily_return,
        "daily_return_pct": daily_return / total_amount if total_amount > 0 else 0.0,
        "accumulated_return_amount": _safe_float(row.get("accumulated_return_amount") or row.get("cumulative_return_amount")),
        "position_count": int(_safe_float(row.get("visible_position_count"))),
        "pending_order_count": len(pending_orders),
        "pending_order_amount": pending_amount,
        "notes": "当前为视频关键帧候选汇总；只有支付宝确认持仓或导出文件金额一致时，才作为正式持仓。",
    }


def _latest_video_account_row(as_of: str | None) -> dict[str, str]:
    candidates = sorted(ALIPAY_DIR.glob("video_account_summary_*.csv"), reverse=True)
    if as_of:
        expected = ALIPAY_DIR / f"video_account_summary_{as_of.replace('-', '')}.csv"
        candidates = [expected] + [path for path in candidates if path != expected]
    for path in candidates:
        if not path.exists():
            continue
        rows = read_csv(path)
        if rows:
            return rows[-1]
    return {}


def _candidate_position_path(as_of: str | None) -> Path | None:
    if not as_of:
        return None
    return ALIPAY_DIR / f"video_position_candidates_{as_of.replace('-', '')}.csv"


def _ensure_csv(path: Path, fields: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=fields).writeheader()


def _read_alipay_export(path: Path) -> dict[str, object]:
    text = _read_text_any(path)
    lines = text.splitlines()
    header_idx = next((idx for idx, line in enumerate(lines) if line.startswith("交易时间,")), None)
    if header_idx is None:
        raise ValueError(f"Could not find Alipay transaction header in {path}.")
    metadata = "\n".join(lines[:header_idx])
    source_start = _metadata_time(metadata, "起始时间")
    source_end = _metadata_time(metadata, "终止时间")
    reader = csv.DictReader(lines[header_idx:])
    return {"rows": list(reader), "source_start_time": source_start, "source_end_time": source_end}


def _read_text_any(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("gb18030", errors="replace")


def _metadata_time(metadata: str, label: str) -> str:
    match = re.search(label + r"：\[([^\]]+)\]", metadata)
    return match.group(1) if match else ""


def _raw_transaction_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "transaction_time": row.get("交易时间", ""),
        "category": row.get("交易分类", ""),
        "counterparty": row.get("交易对方", ""),
        "description": row.get("商品说明", ""),
        "direction": row.get("收/支", ""),
        "amount": row.get("金额", ""),
        "payment_method": row.get("收/付款方式", ""),
        "status": row.get("交易状态", ""),
        "transaction_id": str(row.get("交易订单号", "")).strip(),
        "merchant_order_id": str(row.get("商家订单号", "")).strip(),
        "notes": row.get("备注", ""),
    }


def _is_investment_row(row: dict[str, str]) -> bool:
    return row.get("交易分类") == "投资理财" or "蚂蚁财富" in row.get("交易对方", "") or "基金" in row.get("商品说明", "")


def _is_fund_trade(row: dict[str, str]) -> bool:
    desc = row.get("商品说明", "")
    if "蚂蚁财富-" not in desc:
        return False
    return any(token in desc for token in ["-买入", "-卖出", "转换", "退款"])


def _fund_trade_row(row: dict[str, str], source_path: str) -> dict[str, object]:
    trade_time = row.get("交易时间", "")
    desc = row.get("商品说明", "")
    fund_name = _fund_name_from_description(desc)
    side = _side_from_description(desc)
    amount = _safe_float(row.get("金额"))
    status = row.get("交易状态", "")
    confirmed_amount = "" if _is_pending_status(status) else amount
    return {
        "trade_date": trade_time[:10],
        "order_time": trade_time[11:19],
        "timezone": "Asia/Shanghai",
        "symbol": "",
        "name": fund_name,
        "side": side,
        "order_type": "recurring" if "定投" in desc else "manual",
        "order_amount": amount,
        "confirmed_amount": confirmed_amount,
        "confirmed_units": "",
        "confirmed_nav": "",
        "fee": "",
        "status": status,
        "source": "alipay_transaction_csv",
        "source_path": source_path,
        "notes": f"{desc}；交易订单号={str(row.get('交易订单号', '')).strip()}；收支={row.get('收/支', '')}；付款方式={row.get('收/付款方式', '')}",
    }


def _fund_name_from_description(desc: str) -> str:
    text = desc.strip()
    if text.startswith("蚂蚁财富-"):
        text = text[len("蚂蚁财富-") :]
    if "-买入" in text:
        return text.split("-买入", 1)[0]
    if "-卖出" in text:
        return text.split("-卖出", 1)[0]
    if "-买入退款" in text:
        return text.split("-买入退款", 1)[0]
    if "-确认成功退款" in text:
        return text.split("-确认成功退款", 1)[0]
    if "[转换至]" in text:
        return text.split("[转换至]", 1)[0]
    return text


def _side_from_description(desc: str) -> str:
    if "买入退款" in desc or "确认成功退款" in desc:
        return "退款"
    if "卖出" in desc or "赎回" in desc:
        return "卖出"
    if "转换" in desc:
        return "转换"
    if "买入" in desc:
        return "买入"
    return "其他"


def _is_pending_status(status: str) -> bool:
    return "确认中" in status or "交易进行中" in status


def _range_suffix(start_time: str, end_time: str) -> str:
    start = (start_time[:10] or "unknown").replace("-", "")
    end = (end_time[:10] or "unknown").replace("-", "")
    return f"{start}_{end}"


def _normalize_rows(rows: list[dict[str, object]], fields: list[str]) -> list[dict[str, object]]:
    return [{field: row.get(field, "") for field in fields} for row in rows]


def _is_effective_position(row: dict[str, str]) -> bool:
    if row.get("status") in {"cancelled", "invalid"}:
        return False
    return bool(row.get("symbol") or row.get("name"))


def _position_return_amount(row: dict[str, str]) -> float:
    explicit = _safe_float(row.get("holding_return_amount"))
    if explicit:
        return explicit
    amount = _safe_float(row.get("amount") or row.get("holding_amount"))
    pct = _pct_or_float(row.get("holding_return_pct"))
    return amount * pct / (1 + pct) if amount and pct > -1 else 0.0


def _safe_float(value: object) -> float:
    try:
        return float(str(value or "").replace(",", "").replace("元", "").strip() or 0)
    except ValueError:
        return 0.0


def _pct_or_float(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        if text.endswith("%"):
            return float(text[:-1]) / 100
        return float(text)
    except ValueError:
        return 0.0


def _date_range(start: date, end: date, weekdays_only: bool) -> list[date]:
    items: list[date] = []
    current = start
    while current <= end:
        if not weekdays_only or current.weekday() < 5:
            items.append(current)
        current += timedelta(days=1)
    return items
