#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.alipay import load_transactions
from econ_bleed_analyzer.classifier import classify_transactions, load_rules


DEFAULT_LEDGER_DB = ROOT / "data" / "finance_ledger" / "finance_ledger.sqlite"
PRIVATE_ROOT = ROOT / "data" / "private" / "alipay_weixin"
DEFAULT_OCR_HELPER = Path(os.environ.get("WEIXIN_OCR_HELPER", ROOT / "scripts" / "ocr_image_macos.swift"))
FUND_KEYWORDS = (
    "基金",
    "蚂蚁财富",
    "ETF",
    "QDII",
    "理财",
    "余额宝",
    "黄金",
    "纳斯达克",
    "财富",
    "投顾",
    "FOF",
    "指数",
    "债券",
    "混合",
    "股票",
    "货币",
    "标普",
    "沪深",
    "中证",
)
ACTION_KEYWORDS = {
    "buy": ("买入", "申购", "定投", "扣款", "付款成功"),
    "sell": ("卖出", "赎回", "转出", "卖出到账"),
    "income": ("收益发放", "分红", "到账"),
}
DESTINATION_SYSTEM = "finance_ledger_alipay_fund_supplement"
ROUTING_KEY = "alipay_fund_weixin_auto_ingest"


@dataclass(frozen=True)
class FundRecord:
    record_id: str
    trade_date: str
    trade_time: str
    action: str
    fund_name: str
    amount: float
    amount_cents: int
    order_id: str
    status: str
    payment_method: str
    source_kind: str
    extraction_method: str
    confidence: float
    raw_text: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def today_key() -> str:
    return dt.datetime.now().astimezone().strftime("%Y%m%d")


def batch_id_for_source(source_sha256: str) -> str:
    return f"alipay_fund_batch_{source_sha256[:16]}"


def stable_json_digest(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def staging_checksum(records: list[FundRecord]) -> str:
    rows = []
    for item in records:
        payload = asdict(item)
        payload["raw_text_sha256"] = hashlib.sha256(payload.pop("raw_text", "").encode("utf-8")).hexdigest()
        rows.append(payload)
    return stable_json_digest(rows)


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {str(row[1]) for row in conn.execute(f"pragma table_info({table})").fetchall()}
    except sqlite3.DatabaseError:
        return set()


def ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    if column not in table_columns(conn, table):
        conn.execute(f"alter table {table} add column {column} {ddl}")


def archive_source(path: Path, source_kind: str) -> dict[str, Any]:
    source_hash = sha256_file(path)
    suffix = path.suffix.lower() or ".bin"
    target_dir = PRIVATE_ROOT / "intake" / today_key()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{source_hash[:16]}{suffix}"
    if not target.exists():
        shutil.copy2(path, target)
        target.chmod(0o600)
    return {
        "source_id": source_hash[:16],
        "batch_id": batch_id_for_source(source_hash),
        "source_sha256": source_hash,
        "source_kind": source_kind,
        "original_path": str(path),
        "archived_path": str(target),
        "size_bytes": path.stat().st_size,
        "received_at": now_iso(),
    }


def archive_text_source(text: str) -> dict[str, Any]:
    payload = text.encode("utf-8")
    source_hash = hashlib.sha256(payload).hexdigest()
    target_dir = PRIVATE_ROOT / "intake" / today_key()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{source_hash[:16]}.txt"
    if not target.exists():
        target.write_text(text, encoding="utf-8")
        target.chmod(0o600)
    return {
        "source_id": source_hash[:16],
        "batch_id": batch_id_for_source(source_hash),
        "source_sha256": source_hash,
        "source_kind": "text",
        "original_path": "weixin_text_message",
        "archived_path": str(target),
        "size_bytes": len(payload),
        "received_at": now_iso(),
    }


def infer_source_kind(path: Path, media_type: str = "") -> str:
    suffix = path.suffix.lower()
    media = media_type.lower()
    if suffix in {".csv", ".xlsx", ".zip"}:
        return "official_bill"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"} or media.startswith("image/"):
        return "screenshot"
    if suffix in {".mp4", ".mov", ".webm", ".mkv", ".avi"} or media.startswith("video/"):
        return "video"
    return "file"


def install_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        create table if not exists alipay_fund_intake_batches (
            batch_id text primary key,
            source_count integer not null,
            record_count integer not null,
            staging_checksum text not null,
            status text not null,
            created_at text not null,
            committed_at text default '',
            summary text default ''
        )
        """
    )
    conn.execute(
        """
        create table if not exists weixin_intake_items (
            intake_id text primary key,
            batch_id text default '',
            source_id text not null,
            source_sha256 text not null,
            source_kind text not null,
            media_type text default '',
            original_path text not null,
            archived_path text not null,
            size_bytes integer not null,
            received_at text not null,
            destination_system text not null,
            routing_key text not null,
            data_status text not null,
            review_status text not null,
            extraction_status text not null,
            ledger_effect text not null,
            record_count integer not null,
            text_hint text default '',
            extraction_summary text default ''
        )
        """
    )
    conn.execute(
        """
        create table if not exists alipay_fund_source_files (
            source_id text primary key,
            batch_id text default '',
            source_sha256 text not null,
            source_kind text not null,
            media_type text default '',
            original_path text not null,
            archived_path text not null,
            size_bytes integer not null,
            received_at text not null,
            text_hint text default '',
            extraction_status text not null,
            extraction_summary text default ''
        )
        """
    )
    conn.execute(
        """
        create table if not exists alipay_fund_records (
            record_id text primary key,
            batch_id text default '',
            source_id text not null,
            source_sha256 text not null,
            trade_date text not null,
            trade_time text default '',
            action text not null,
            fund_name text not null,
            amount real not null,
            amount_cents integer not null,
            order_id text default '',
            status text default '',
            payment_method text default '',
            source_kind text not null,
            extraction_method text not null,
            confidence real not null,
            review_status text not null,
            inserted_at text not null,
            raw_text text default ''
        )
        """
    )
    conn.execute(
        """
        create table if not exists alipay_fund_review_runs (
            review_id text primary key,
            batch_id text default '',
            source_id text not null,
            staging_checksum text default '',
            agent text not null,
            pass_no integer not null,
            verdict text not null,
            reason text not null,
            checked_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists alipay_fund_commits (
            commit_id text primary key,
            batch_id text not null,
            source_id text not null,
            db_before_sha256 text default '',
            db_after_sha256 text default '',
            backup_path text default '',
            inserted_records integer not null,
            reviewed_records integer not null,
            staging_checksum text not null,
            integrity_check text not null,
            committed_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists alipay_update_status (
            update_date text primary key,
            batch_id text default '',
            status text not null,
            source_id text not null,
            record_count integer not null,
            updated_at text not null,
            summary text not null
        )
        """
    )
    ensure_column(conn, "weixin_intake_items", "batch_id", "text default ''")
    ensure_column(conn, "alipay_fund_source_files", "batch_id", "text default ''")
    ensure_column(conn, "alipay_fund_source_files", "media_type", "text default ''")
    ensure_column(conn, "alipay_fund_records", "batch_id", "text default ''")
    ensure_column(conn, "alipay_fund_review_runs", "batch_id", "text default ''")
    ensure_column(conn, "alipay_fund_review_runs", "staging_checksum", "text default ''")
    ensure_column(conn, "alipay_update_status", "batch_id", "text default ''")
    conn.execute(
        "create view if not exists v_alipay_fund_records as select * from alipay_fund_records"
    )
    conn.execute(
        "create view if not exists v_alipay_update_status as select * from alipay_update_status"
    )
    conn.execute(
        "create view if not exists v_weixin_intake_items as select * from weixin_intake_items"
    )
    conn.execute(
        """
        create view if not exists v_alipay_fund_confirmed_trades as
        select *
        from alipay_fund_records
        where review_status = 'auto_review_passed'
        """
    )
    conn.execute(
        """
        create view if not exists v_alipay_fund_candidate_positions as
        select *
        from alipay_fund_records
        where source_kind = 'screenshot'
          and review_status = 'auto_review_passed'
        """
    )
    conn.execute(
        """
        create view if not exists v_alipay_fund_pending_orders as
        select *
        from alipay_fund_records
        where status like '%确认中%'
           or status like '%待确认%'
           or status like '%处理中%'
           or lower(status) like '%pending%'
        """
    )


def action_from_text(text: str) -> str:
    for action, keywords in ACTION_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return action
    return "unknown"


def action_from_transaction(tx: Any, text: str) -> str:
    if any(keyword in text for keyword in ACTION_KEYWORDS["sell"]):
        return "sell"
    if any(keyword in text for keyword in ACTION_KEYWORDS["income"]):
        return "income"
    if any(keyword in text for keyword in ACTION_KEYWORDS["buy"]):
        return "buy"
    if getattr(tx, "direction", "") == "支出" or getattr(tx, "cash_flow_type", "") == "expense":
        return "buy"
    if getattr(tx, "direction", "") == "收入" or getattr(tx, "cash_flow_type", "") == "income":
        return "income"
    return "unknown"


def is_fund_text(text: str) -> bool:
    return any(keyword.lower() in text.lower() for keyword in FUND_KEYWORDS)


def fund_name_from_transaction(tx: Any, text: str) -> str:
    description = (getattr(tx, "description", "") or "").strip()
    counterparty = (getattr(tx, "counterparty", "") or "").strip()
    transaction_type = (getattr(tx, "transaction_type", "") or "").strip()
    if description and (is_fund_text(description) or transaction_type == "投资理财"):
        return description
    if counterparty and is_fund_text(counterparty):
        return counterparty
    if is_fund_text(text):
        return description or counterparty
    return ""


def amount_to_cents(value: float) -> int:
    return int(round(value * 100))


def record_id(source_hash: str, order_id: str, raw_key: str) -> str:
    base = order_id.strip() or raw_key
    digest = hashlib.sha256(f"{source_hash}:{base}".encode("utf-8")).hexdigest()
    return f"alipay_fund_{digest[:24]}"


def extract_official_bill(path: Path, source: dict[str, Any]) -> list[FundRecord]:
    rules = load_rules(ROOT / "configs" / "classification_rules.json")
    transactions = load_transactions([path])
    classified = classify_transactions(transactions, rules)
    rows: list[FundRecord] = []
    for tx in classified:
        combined = f"{tx.transaction_type} {tx.counterparty} {tx.description} {tx.direction} {tx.status}"
        if tx.main_category != "金融资金" and tx.transaction_type != "投资理财" and not is_fund_text(combined):
            continue
        fund_name = fund_name_from_transaction(tx, combined)
        if not fund_name:
            continue
        action = action_from_transaction(tx, combined)
        if action == "unknown":
            continue
        amount = abs(float(tx.amount_cents) / 100.0)
        trade_time = str(tx.transaction_time)
        trade_date = str(tx.date)
        raw_key = f"{trade_time}|{tx.counterparty}|{tx.description}|{amount}"
        rows.append(
            FundRecord(
                record_id=record_id(source["source_sha256"], tx.order_id, raw_key),
                trade_date=trade_date,
                trade_time=trade_time,
                action=action,
                fund_name=fund_name,
                amount=amount,
                amount_cents=abs(int(tx.amount_cents)),
                order_id=tx.order_id,
                status=tx.status,
                payment_method=tx.payment_method,
                source_kind="official_bill",
                extraction_method="bill_parser",
                confidence=0.98,
                raw_text=combined[:1000],
            )
        )
    return rows


def run_image_ocr(path: Path, helper: Path) -> str:
    if not helper.exists():
        raise RuntimeError(f"OCR helper missing: {helper}")
    proc = subprocess.run(
        ["/usr/bin/swift", str(helper), str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=90,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout.strip() or f"OCR failed code={proc.returncode}")
    return proc.stdout.strip()


def normalize_ocr_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def today_date() -> dt.date:
    return dt.datetime.now().astimezone().date()


def date_time_from_relative_line(line: str) -> tuple[str, str] | None:
    clean = line.replace(" ", "")
    match = re.search(r"(今天|昨日|昨天|前天)?(\d{1,2}):(\d{2})", clean)
    if not match:
        return None
    label, hour, minute = match.groups()
    trade_date = today_date()
    if label in {"昨日", "昨天"}:
        trade_date -= dt.timedelta(days=1)
    elif label == "前天":
        trade_date -= dt.timedelta(days=2)
    return trade_date.isoformat(), f"{int(hour):02d}:{int(minute):02d}"


def date_from_text(text: str) -> str:
    if "今天" in text:
        return today_date().isoformat()
    if "昨日" in text or "昨天" in text:
        return (today_date() - dt.timedelta(days=1)).isoformat()
    if "前天" in text:
        return (today_date() - dt.timedelta(days=2)).isoformat()
    match = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", text)
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    match = re.search(r"(?<![\d,¥￥])(\d{1,2})[-/.月](\d{1,2})日?(?![\d])", text)
    if match:
        year = today_date().year
        month, day = match.groups()
        return f"{year:04d}-{int(month):02d}-{int(day):02d}"
    return today_date().isoformat()


def amount_from_text(text: str) -> float | None:
    candidates = []
    for match in re.finditer(r"(?:金额|买入|卖出|定投|申购|赎回|¥|￥)\D{0,12}([0-9][0-9,]*(?:\.[0-9]{1,2})?)", text):
        try:
            candidates.append(float(match.group(1).replace(",", "")))
        except ValueError:
            pass
    if not candidates:
        for match in re.finditer(r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*元", text):
            try:
                candidates.append(float(match.group(1).replace(",", "")))
            except ValueError:
                pass
    positives = [value for value in candidates if value > 0]
    return positives[0] if positives else None


def fund_name_from_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    preferred = [line for line in lines if is_fund_text(line) and 2 <= len(line) <= 80]
    if preferred:
        return re.sub(r"^(蚂蚁财富[-—]?)", "", preferred[0]).strip()
    return ""


def order_id_from_text(text: str) -> str:
    match = re.search(r"(20\d{20,}|[A-Z]{1,4}\d{12,})", text)
    return match.group(1) if match else ""


def numeric_amount_lines(lines: list[str]) -> list[float]:
    amounts: list[float] = []
    for line in lines:
        clean = line.strip().replace(",", "")
        if re.fullmatch(r"\d{1,6}(?:\.\d{1,2})", clean):
            value = float(clean)
            if value > 0:
                amounts.append(value)
    return amounts


def list_statuses(lines: list[str]) -> list[str]:
    return [
        line
        for line in lines
        if not line.startswith(("蚂蚁财富", "余额宝-"))
        and any(keyword in line for keyword in ("付款成功", "确认中", "赎回", "卖出", "到账"))
    ]


def action_for_list_item(name: str, status: str) -> str:
    if any(keyword in name + status for keyword in ACTION_KEYWORDS["income"]):
        return "income"
    if any(keyword in name + status for keyword in ACTION_KEYWORDS["sell"]):
        return "sell"
    if any(keyword in name + status for keyword in ACTION_KEYWORDS["buy"]):
        return "buy"
    return "buy"


def extract_alipay_list_screenshot(ocr_text: str, source: dict[str, Any]) -> list[FundRecord]:
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
    if "搜索交易记录" not in ocr_text and "收支分析" not in ocr_text:
        return []
    entries: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        if not is_fund_text(line):
            continue
        if line.startswith(("支出", "收入")):
            continue
        if line in {"投资理财", "收支分析"}:
            continue
        nearby = lines[index + 1 : index + 5]
        trade_date = ""
        trade_time = ""
        for candidate in nearby:
            parsed = date_time_from_relative_line(candidate)
            if parsed:
                trade_date, trade_time = parsed
                break
        if not trade_date:
            continue
        entries.append({"name": line, "trade_date": trade_date, "trade_time": trade_time})

    amounts = numeric_amount_lines(lines)
    statuses = list_statuses(lines)
    rows: list[FundRecord] = []
    for index, entry in enumerate(entries[: len(amounts)]):
        amount = amounts[index]
        status = statuses[index] if index < len(statuses) else ""
        action = action_for_list_item(entry["name"], status)
        raw_key = f"{entry['trade_date']}|{entry['trade_time']}|{entry['name']}|{amount}|{index}"
        rows.append(
            FundRecord(
                record_id=record_id(source["source_sha256"], "", raw_key),
                trade_date=entry["trade_date"],
                trade_time=entry["trade_time"],
                action=action,
                fund_name=entry["name"],
                amount=amount,
                amount_cents=amount_to_cents(amount),
                order_id="",
                status=status or "screenshot_list_auto_reviewed",
                payment_method="",
                source_kind="screenshot",
                extraction_method="macos_vision_ocr_list",
                confidence=0.76,
                raw_text=ocr_text[:3000],
            )
        )
    return rows


def extract_screenshot(path: Path, source: dict[str, Any], helper: Path) -> list[FundRecord]:
    ocr_text = normalize_ocr_text(run_image_ocr(path, helper))
    if not ocr_text or not is_fund_text(ocr_text):
        return []
    list_rows = extract_alipay_list_screenshot(ocr_text, source)
    if list_rows:
        return list_rows
    amount = amount_from_text(ocr_text)
    fund_name = fund_name_from_text(ocr_text)
    action = action_from_text(ocr_text)
    if amount is None or not fund_name or action == "unknown":
        return []
    trade_date = date_from_text(ocr_text)
    order_id = order_id_from_text(ocr_text)
    raw_key = f"{trade_date}|{fund_name}|{action}|{amount}|{order_id}"
    return [
        FundRecord(
            record_id=record_id(source["source_sha256"], order_id, raw_key),
            trade_date=trade_date,
            trade_time="",
            action=action,
            fund_name=fund_name,
            amount=amount,
            amount_cents=amount_to_cents(amount),
            order_id=order_id,
            status="screenshot_auto_reviewed",
            payment_method="",
            source_kind="screenshot",
            extraction_method="macos_vision_ocr",
            confidence=0.82 if order_id else 0.74,
            raw_text=ocr_text[:3000],
        )
    ]


def review_agent_a(records: list[FundRecord], pass_no: int) -> tuple[bool, str]:
    if not records:
        return False, "no parsed fund records"
    for item in records:
        if not item.trade_date or not item.fund_name or item.amount <= 0:
            return False, "missing required date/fund/amount"
        try:
            parsed = dt.date.fromisoformat(item.trade_date)
        except ValueError:
            return False, "invalid trade_date"
        if parsed > dt.datetime.now().astimezone().date() + dt.timedelta(days=2):
            return False, "future trade_date beyond tolerance"
        if item.source_kind == "official_bill" and not item.order_id:
            return False, "official bill record missing order_id"
        if item.action not in {"buy", "sell", "income"}:
            return False, "unknown fund action"
    return True, f"schema/date/action/amount pass {pass_no}"


def review_agent_b(records: list[FundRecord], pass_no: int, conn: sqlite3.Connection) -> tuple[bool, str]:
    seen = set()
    existing_count = 0
    for item in records:
        if item.record_id in seen:
            return False, "duplicate record in source"
        seen.add(item.record_id)
        if item.confidence < (0.95 if item.source_kind == "official_bill" else 0.72):
            return False, "confidence below threshold"
        if not is_fund_text(item.fund_name + " " + item.raw_text):
            return False, "fund keywords missing"
        existing = conn.execute(
            "select count(*) from alipay_fund_records where record_id = ?",
            [item.record_id],
        ).fetchone()[0]
        if existing:
            existing_count += 1
    suffix = f"; existing={existing_count}" if existing_count else ""
    return True, f"dedupe/domain/confidence pass {pass_no}{suffix}"


def run_reviews(
    records: list[FundRecord],
    source: dict[str, Any],
    checksum: str,
    conn: sqlite3.Connection,
) -> tuple[bool, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    verdict = True
    source_id = source["source_id"]
    batch_id = source["batch_id"]
    for pass_no in range(1, 4):
        ok, reason = review_agent_a(records, pass_no)
        verdict = verdict and ok
        rows.append(
            {
                "review_id": f"{source_id}:agent_a:{pass_no}",
                "batch_id": batch_id,
                "source_id": source_id,
                "staging_checksum": checksum,
                "agent": "agent_a_schema",
                "pass_no": pass_no,
                "verdict": "pass" if ok else "fail",
                "reason": reason,
                "checked_at": now_iso(),
            }
        )
    for pass_no in range(1, 4):
        ok, reason = review_agent_b(records, pass_no, conn)
        verdict = verdict and ok
        rows.append(
            {
                "review_id": f"{source_id}:agent_b:{pass_no}",
                "batch_id": batch_id,
                "source_id": source_id,
                "staging_checksum": checksum,
                "agent": "agent_b_domain",
                "pass_no": pass_no,
                "verdict": "pass" if ok else "fail",
                "reason": reason,
                "checked_at": now_iso(),
            }
        )
    return verdict, rows


def backup_ledger(db: Path) -> Path:
    backup_dir = PRIVATE_ROOT / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target = backup_dir / f"finance_ledger_{stamp}.sqlite"
    if db.exists():
        shutil.copy2(db, target)
        target.chmod(0o600)
    return target


def sha256_file_if_exists(path: Path) -> str:
    return sha256_file(path) if path.exists() else ""


def insert_commit_audit(
    conn: sqlite3.Connection,
    source: dict[str, Any],
    *,
    db_before_sha256: str,
    db_after_sha256: str,
    backup_path: Path | None,
    inserted_records: int,
    reviewed_records: int,
    checksum: str,
    integrity_check: str,
) -> None:
    commit_id = f"{source['batch_id']}:{checksum[:12]}"
    conn.execute(
        """
        insert into alipay_fund_commits (
            commit_id, batch_id, source_id, db_before_sha256, db_after_sha256,
            backup_path, inserted_records, reviewed_records, staging_checksum,
            integrity_check, committed_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(commit_id) do update set
            db_after_sha256=excluded.db_after_sha256,
            backup_path=excluded.backup_path,
            inserted_records=excluded.inserted_records,
            reviewed_records=excluded.reviewed_records,
            integrity_check=excluded.integrity_check,
            committed_at=excluded.committed_at
        """,
        [
            commit_id,
            source["batch_id"],
            source["source_id"],
            db_before_sha256,
            db_after_sha256,
            str(backup_path) if backup_path and backup_path.exists() else "",
            inserted_records,
            reviewed_records,
            checksum,
            integrity_check,
            now_iso(),
        ],
    )


def insert_rows(
    conn: sqlite3.Connection,
    source: dict[str, Any],
    records: list[FundRecord],
    reviews: list[dict[str, Any]],
    status: str,
    summary: str,
    text_hint: str,
    checksum: str,
) -> int:
    batch_id = source["batch_id"]
    data_status = "PARSED_CANDIDATE" if records else "NEEDS_REVIEW"
    review_status = "auto_review_passed" if records and status == "inserted" else "auto_review_failed"
    now = now_iso()
    conn.execute(
        """
        insert into alipay_fund_intake_batches (
            batch_id, source_count, record_count, staging_checksum,
            status, created_at, committed_at, summary
        ) values (?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(batch_id) do update set
            record_count=excluded.record_count,
            staging_checksum=excluded.staging_checksum,
            status=excluded.status,
            committed_at=excluded.committed_at,
            summary=excluded.summary
        """,
        [
            batch_id,
            1,
            len(records),
            checksum,
            status,
            source["received_at"],
            now if records and status == "inserted" else "",
            summary[:1000],
        ],
    )
    conn.execute(
        """
        insert into weixin_intake_items (
            intake_id, batch_id, source_id, source_sha256, source_kind, media_type,
            original_path, archived_path, size_bytes, received_at,
            destination_system, routing_key, data_status, review_status,
            extraction_status, ledger_effect, record_count, text_hint, extraction_summary
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(intake_id) do update set
            batch_id=excluded.batch_id,
            data_status=excluded.data_status,
            review_status=excluded.review_status,
            extraction_status=excluded.extraction_status,
            ledger_effect=excluded.ledger_effect,
            record_count=excluded.record_count,
            text_hint=excluded.text_hint,
            extraction_summary=excluded.extraction_summary
        """,
        [
            f"weixin_intake_{source['source_id']}",
            batch_id,
            source["source_id"],
            source["source_sha256"],
            source["source_kind"],
            source.get("media_type", ""),
            source["original_path"],
            source["archived_path"],
            source["size_bytes"],
            source["received_at"],
            DESTINATION_SYSTEM,
            ROUTING_KEY,
            data_status,
            review_status,
            status,
            "pending_record_insert" if records and status == "inserted" else "archive_only",
            len(records),
            text_hint[:500],
            summary[:1000],
        ],
    )
    conn.execute(
        """
        insert into alipay_fund_source_files (
            source_id, batch_id, source_sha256, source_kind, media_type,
            original_path, archived_path, size_bytes, received_at,
            text_hint, extraction_status, extraction_summary
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(source_id) do update set
            batch_id=excluded.batch_id,
            extraction_status=excluded.extraction_status,
            extraction_summary=excluded.extraction_summary,
            media_type=excluded.media_type,
            text_hint=excluded.text_hint
        """,
        [
            source["source_id"],
            batch_id,
            source["source_sha256"],
            source["source_kind"],
            source.get("media_type", ""),
            source["original_path"],
            source["archived_path"],
            source["size_bytes"],
            source["received_at"],
            text_hint[:500],
            status,
            summary[:1000],
        ],
    )
    for row in reviews:
        conn.execute(
            """
            insert or replace into alipay_fund_review_runs
            (review_id, batch_id, source_id, staging_checksum, agent, pass_no, verdict, reason, checked_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row["review_id"],
                row.get("batch_id", batch_id),
                row["source_id"],
                row.get("staging_checksum", checksum),
                row["agent"],
                row["pass_no"],
                row["verdict"],
                row["reason"],
                row["checked_at"],
            ],
        )
    inserted_records = 0
    for item in records:
        payload = asdict(item)
        cursor = conn.execute(
            """
            insert into alipay_fund_records (
                record_id, batch_id, source_id, source_sha256, trade_date, trade_time, action,
                fund_name, amount, amount_cents, order_id, status, payment_method,
                source_kind, extraction_method, confidence, review_status, inserted_at, raw_text
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(record_id) do nothing
            """,
            [
                payload["record_id"],
                batch_id,
                source["source_id"],
                source["source_sha256"],
                payload["trade_date"],
                payload["trade_time"],
                payload["action"],
                payload["fund_name"],
                payload["amount"],
                payload["amount_cents"],
                payload["order_id"],
                payload["status"],
                payload["payment_method"],
                payload["source_kind"],
                payload["extraction_method"],
                payload["confidence"],
                "auto_review_passed",
                now_iso(),
                payload["raw_text"],
            ],
        )
        inserted_records += max(cursor.rowcount, 0)
    dates = sorted({item.trade_date for item in records}) or [dt.datetime.now().astimezone().date().isoformat()]
    for trade_date in dates:
        count = sum(1 for item in records if item.trade_date == trade_date)
        conn.execute(
            """
            insert into alipay_update_status
            (update_date, batch_id, status, source_id, record_count, updated_at, summary)
            values (?, ?, ?, ?, ?, ?, ?)
            on conflict(update_date) do update set
                batch_id=excluded.batch_id,
                status=excluded.status,
                source_id=excluded.source_id,
                record_count=excluded.record_count,
                updated_at=excluded.updated_at,
                summary=excluded.summary
        """,
            [
                trade_date,
                batch_id,
                "confirmed_auto_reviewed" if records else "blocked_unparsed",
                source["source_id"],
                count,
                now_iso(),
                summary,
            ],
        )
    ledger_effect = "archive_only"
    if records and inserted_records:
        ledger_effect = "fund_record_inserted"
    elif records:
        ledger_effect = "idempotent_noop"
    conn.execute(
        """
        update weixin_intake_items
        set ledger_effect = ?,
            record_count = ?
        where intake_id = ?
        """,
        [ledger_effect, len(records), f"weixin_intake_{source['source_id']}"],
    )
    return inserted_records


def extract_records(path: Path, source: dict[str, Any], ocr_helper: Path) -> tuple[list[FundRecord], str]:
    kind = source["source_kind"]
    if kind == "official_bill":
        records = extract_official_bill(path, source)
        return records, f"official bill parsed; fund_records={len(records)}"
    if kind == "screenshot":
        records = extract_screenshot(path, source, ocr_helper)
        return records, f"screenshot OCR parsed; fund_records={len(records)}"
    if kind == "video":
        return [], "video archived, but ffmpeg/frame OCR unavailable in current runtime"
    if kind == "text":
        return [], "text archived as Weixin candidate; no automatic ledger extraction"
    return [], f"{kind} archived, unsupported for automatic fund extraction"


def human_summary(
    status: str,
    records: list[FundRecord],
    source: dict[str, Any],
    reason: str,
    *,
    inserted_records: int = 0,
) -> str:
    if status == "inserted":
        lines = [
            "支付宝基金资料已自动入库",
            f"source_id: {source['source_id']}",
            f"复审通过记录数: {len(records)}",
            f"本次新增记录数: {inserted_records}",
            "复审: schema_agent 3/3 pass; domain_agent 3/3 pass",
            "说明: 已写入支付宝基金补充表；不修改正式消费统计口径表。",
        ]
        return "\n".join(lines)
    if status == "idempotent_noop":
        return (
            "支付宝基金资料已复审，无新增入库\n"
            f"source_id: {source['source_id']}\n"
            f"复审通过记录数: {len(records)}\n"
            "原因: 这些记录已存在，重复上传不会重复写入。"
        )
    return (
        "支付宝基金资料未写入总数据库\n"
        f"source_id: {source['source_id']}\n"
        f"状态: {status}\n"
        f"原因: {reason}\n"
        "说明: 已归档源文件；未通过自动双规则复审门禁时不写记录。"
    )


def process_media(args: argparse.Namespace) -> dict[str, Any]:
    media_path = getattr(args, "media_path", "")
    media_type = getattr(args, "media_type", "")
    text = getattr(args, "text", "")
    ledger_db = Path(getattr(args, "ledger_db", DEFAULT_LEDGER_DB))
    if media_path:
        path = Path(media_path).expanduser().resolve()
        if not path.exists():
            return {"handled": True, "status": "blocked_missing_file", "message": f"文件不存在: {path}"}
        source_kind = infer_source_kind(path, media_type)
        source = archive_source(path, source_kind)
    else:
        if not text.strip():
            return {"handled": False, "status": "blocked_empty_input", "message": "未收到媒体文件或文本。"}
        path = Path("")
        source_kind = "text"
        source = archive_text_source(text)
    source["source_kind"] = source_kind
    source["media_type"] = media_type
    source_path = Path(source["archived_path"])
    reason = ""
    records: list[FundRecord] = []
    reviews: list[dict[str, Any]] = []
    backup: Path | None = None
    inserted_records = 0

    try:
        records, reason = extract_records(source_path, source, Path(args.ocr_helper))
    except Exception as exc:
        reason = f"extract failed: {exc}"
        records = []

    alipay_hint = bool(records) or is_fund_text(text) or "支付宝" in text or "alipay" in text.lower()
    handled = bool(records) or source_kind == "official_bill" or source_kind == "video" or (
        source_kind in {"screenshot", "text"} and alipay_hint
    )
    if not handled:
        return {
            "handled": False,
            "status": "ignored_non_alipay_media",
            "source_id": source["source_id"],
            "source_kind": source_kind,
            "record_count": 0,
            "message": "未识别为支付宝基金资料，已交回普通消息流程。",
            "ledger_db": str(ledger_db),
        }

    checksum = staging_checksum(records)
    ledger_db.parent.mkdir(parents=True, exist_ok=True)
    if ledger_db.exists():
        backup = backup_ledger(ledger_db)

    with sqlite3.connect(ledger_db) as conn:
        install_schema(conn)
        conn.commit()
        verdict, reviews = run_reviews(records, source, checksum, conn)
        failed_reasons = [row["reason"] for row in reviews if row["verdict"] != "pass"]
        if failed_reasons:
            candidate_dates = ",".join(sorted({item.trade_date for item in records})[:4])
            candidate_hint = f"; candidate_count={len(records)}"
            if candidate_dates:
                candidate_hint += f"; candidate_dates={candidate_dates}"
            reason = f"{reason}{candidate_hint}; review failed: {'; '.join(sorted(set(failed_reasons)))}"
        db_before = sha256_file_if_exists(ledger_db)
        conn.execute("begin immediate")
        if records and verdict:
            try:
                inserted_records = insert_rows(
                    conn,
                    source,
                    records,
                    reviews,
                    "inserted",
                    reason,
                    text,
                    checksum,
                )
                integrity = str(conn.execute("pragma integrity_check").fetchone()[0])
                if integrity != "ok":
                    raise RuntimeError(f"sqlite integrity_check failed: {integrity}")
                conn.commit()
            except Exception:
                conn.rollback()
                if backup and backup.exists():
                    shutil.copy2(backup, ledger_db)
                raise
            db_after = sha256_file_if_exists(ledger_db)
            conn.execute("begin immediate")
            insert_commit_audit(
                conn,
                source,
                db_before_sha256=db_before,
                db_after_sha256=db_after,
                backup_path=backup,
                inserted_records=inserted_records,
                reviewed_records=len(records),
                checksum=checksum,
                integrity_check=integrity,
            )
            conn.commit()
            status = "inserted" if inserted_records else "idempotent_noop"
        else:
            insert_rows(
                conn,
                source,
                [],
                reviews,
                "blocked_review_failed",
                reason,
                text,
                checksum,
            )
            integrity = str(conn.execute("pragma integrity_check").fetchone()[0])
            if integrity != "ok":
                conn.rollback()
                if backup and backup.exists():
                    shutil.copy2(backup, ledger_db)
                raise RuntimeError(f"sqlite integrity_check failed: {integrity}")
            conn.commit()
            status = "blocked_review_failed"

    message = human_summary(status, records, source, reason, inserted_records=inserted_records)
    return {
        "handled": handled,
        "status": status,
        "source_id": source["source_id"],
        "source_kind": source_kind,
        "record_count": len(records),
        "inserted_records": inserted_records,
        "message": message,
        "review_passes": reviews,
        "ledger_db": str(ledger_db),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest Weixin media or text into the local finance ledger candidate intake.")
    parser.add_argument("--media-path", default="")
    parser.add_argument("--media-type", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--ledger-db", default=str(DEFAULT_LEDGER_DB))
    parser.add_argument("--ocr-helper", default=str(DEFAULT_OCR_HELPER))
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = process_media(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["message"])
    return 0 if result["status"] in {"inserted", "idempotent_noop"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
