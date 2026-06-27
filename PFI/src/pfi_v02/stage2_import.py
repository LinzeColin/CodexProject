from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pfi_v02.classification_rules import ClassificationInput, classify_transaction
from pfi_v02.core_models import ImportBatch, LedgerEventType, NormalizedTransaction, RawRecord


@dataclass(frozen=True)
class FileCandidate:
    path: str
    source_id: str
    content_sha256: str
    parser_hint: str


@dataclass(frozen=True)
class ReviewQueueItem:
    transaction_id: str
    reason: str
    choices: tuple[str, ...]


@dataclass(frozen=True)
class Stage2ImportResult:
    import_batch: ImportBatch
    raw_records: tuple[RawRecord, ...]
    transactions: tuple[NormalizedTransaction, ...]
    review_queue: tuple[ReviewQueueItem, ...]


@dataclass(frozen=True)
class TransferMatch:
    transaction_id: str
    match_type: str
    affects_consumption: bool
    confidence: float
    reason: str


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def detect_watch_folder_files(inbox: Path) -> tuple[FileCandidate, ...]:
    candidates: list[FileCandidate] = []
    seen_hashes: set[str] = set()
    for path in sorted(inbox.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        suffix = path.suffix.lower()
        name = path.name.lower()
        source_id = ""
        parser_hint = ""
        if suffix == ".csv" and ("cba" in name or "commbank" in name):
            source_id = "cba_bank"
            parser_hint = "cba_csv_v1"
        elif suffix in {".csv", ".zip"} and ("alipay" in name or "支付宝" in path.name):
            source_id = "alipay_daily"
            parser_hint = "alipay_bill_zip_v1" if suffix == ".zip" else "alipay_bill_csv_v1"
        elif suffix in {".csv", ".xls", ".xlsx", ".zip"} and ("wechat" in name or "微信" in path.name):
            source_id = "wechat_pay"
            parser_hint = "wechat_bill_file_contract_v1"
        if not source_id:
            continue
        digest = sha256_file(path)
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        candidates.append(FileCandidate(str(path), source_id, digest, parser_hint))
    return tuple(candidates)


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _clean_row(row: dict[str | None, str | None]) -> dict[str, str]:
    return {
        str(key).strip(): str(value or "").strip()
        for key, value in row.items()
        if key is not None and str(key).strip()
    }


def _csv_rows_after_header(content: bytes, *, required_headers: tuple[str, ...]) -> list[dict[str, str]]:
    text = _decode_text(content)
    lines = text.splitlines()
    header_index = 0
    for index, line in enumerate(lines):
        try:
            cells = next(csv.reader([line]))
        except csv.Error:
            continue
        normalized = {cell.strip() for cell in cells}
        if all(header in normalized for header in required_headers):
            header_index = index
            break
    rows: list[dict[str, str]] = []
    for row in csv.DictReader(io.StringIO("\n".join(lines[header_index:]))):
        cleaned = _clean_row(row)
        if any(cleaned.values()):
            rows.append(cleaned)
    return rows


def _canonical_row(row: dict[str, str]) -> str:
    return json.dumps({key: value for key, value in sorted(_clean_row(row).items())}, ensure_ascii=False, sort_keys=True)


def _field(row: dict[str, str], *names: str) -> str:
    lower = {key.strip().lower(): value.strip() for key, value in _clean_row(row).items()}
    for name in names:
        key = name.strip().lower()
        if key in lower:
            return lower[key]
    return ""


def _parse_money(value: str) -> float:
    cleaned = value.strip().replace(",", "").replace("$", "").replace("￥", "").replace("AUD", "").replace("CNY", "")
    cleaned = cleaned.strip()
    if not cleaned:
        return 0.0
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    amount = float(cleaned)
    return -amount if negative else amount


def _parse_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d %b %Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return value


def _make_batch(source_id: str, parser_version: str, content: bytes, raw_record_count: int) -> ImportBatch:
    digest = sha256_bytes(content)
    return ImportBatch(
        batch_id=f"{source_id}:{parser_version}:{digest[:16]}",
        source_id=source_id,
        acquired_at=datetime.now(timezone.utc).isoformat(),
        parser_version=parser_version,
        content_sha256=digest,
        raw_record_count=raw_record_count,
    )


def parse_cba_csv_bytes(content: bytes, *, account_id: str = "acct_cba_main", currency: str = "AUD") -> Stage2ImportResult:
    rows = list(csv.DictReader(io.StringIO(_decode_text(content))))
    batch = _make_batch("cba_bank", "cba_csv_v1", content, len(rows))
    raw_records: list[RawRecord] = []
    transactions: list[NormalizedTransaction] = []
    review_queue: list[ReviewQueueItem] = []

    for index, row in enumerate(rows, start=1):
        canonical = _canonical_row(row)
        raw_id = f"{batch.batch_id}:row:{index}"
        raw_records.append(
            RawRecord(
                raw_id=raw_id,
                batch_id=batch.batch_id,
                source_record_id=f"row-{index}",
                payload_sha256=sha256_bytes(canonical.encode("utf-8")),
                raw_payload_ref=f"private://imports/{batch.batch_id}#row={index}",
            )
        )
        description = _field(row, "Description", "Transaction Description", "Narrative", "描述", "交易说明")
        date = _parse_date(_field(row, "Date", "Transaction Date", "日期"))
        amount_text = _field(row, "Amount", "金额")
        if amount_text:
            amount = _parse_money(amount_text)
        else:
            debit = _parse_money(_field(row, "Debit", "Withdrawal", "支出", "借方"))
            credit = _parse_money(_field(row, "Credit", "Deposit", "收入", "贷方"))
            amount = credit - abs(debit) if debit else credit
        classification = classify_transaction(
            ClassificationInput("cba_bank", description, amount, currency, account_id, "")
        )
        confidence = 0.96 if classification.review_state == "ACCEPTED" else 0.55
        transaction = NormalizedTransaction(
            transaction_id=f"txn_cba_{index:04d}_{sha256_bytes(canonical.encode('utf-8'))[:8]}",
            source_id="cba_bank",
            raw_id=raw_id,
            account_id=_field(row, "Account", "Account Number", "账号") or account_id,
            event_type=classification.event_type,
            amount=amount,
            currency=currency,
            occurred_at=date,
            description=description,
            confidence=confidence,
            review_state=classification.review_state,
        )
        transactions.append(transaction)
        if transaction.review_state != "ACCEPTED":
            review_queue.append(_review_item(transaction.transaction_id, "CBA classification needs owner review."))

    return Stage2ImportResult(batch, tuple(raw_records), tuple(transactions), tuple(review_queue))


def _normalise_alipay_amount(row: dict[str, str]) -> float:
    amount = abs(_parse_money(_field(row, "金额", "Amount", "交易金额")))
    direction = _field(row, "收/支", "收支", "Direction", "资金流向")
    text = " ".join(row.values())
    if "支出" in direction or "付款" in direction or "支出" in text or "付款" in text:
        return -amount
    if "收入" in direction or "收款" in direction or "退款" in text or "到账" in text:
        return amount
    raw_amount = _field(row, "金额", "Amount", "交易金额")
    return _parse_money(raw_amount)


def parse_alipay_bill_bytes(content: bytes, *, account_id: str = "acct_alipay", currency: str = "CNY") -> Stage2ImportResult:
    if zipfile.is_zipfile(io.BytesIO(content)):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError("Alipay ZIP contains no CSV bill file.")
            content = archive.read(csv_names[0])

    rows = _csv_rows_after_header(content, required_headers=("交易时间", "金额"))
    rows = [
        row
        for row in rows
        if _field(row, "交易时间", "日期", "Date", "Time") and _field(row, "金额", "Amount", "交易金额")
    ]
    batch = _make_batch("alipay_daily", "alipay_bill_csv_v1", content, len(rows))
    raw_records: list[RawRecord] = []
    transactions: list[NormalizedTransaction] = []
    review_queue: list[ReviewQueueItem] = []

    for index, row in enumerate(rows, start=1):
        canonical = _canonical_row(row)
        raw_id = f"{batch.batch_id}:row:{index}"
        raw_records.append(
            RawRecord(
                raw_id=raw_id,
                batch_id=batch.batch_id,
                source_record_id=f"row-{index}",
                payload_sha256=sha256_bytes(canonical.encode("utf-8")),
                raw_payload_ref=f"private://imports/{batch.batch_id}#row={index}",
            )
        )
        description = " ".join(
            part
            for part in (
                _field(row, "商品说明", "商品名称", "Description", "交易说明"),
                _field(row, "交易对方", "Counterparty"),
                _field(row, "交易类型", "交易分类", "Type", "分类"),
            )
            if part
        )
        amount = _normalise_alipay_amount(row)
        date = _parse_date(_field(row, "交易时间", "日期", "Date", "Time"))
        classification = classify_transaction(
            ClassificationInput("alipay_daily", description, amount, currency, account_id, "")
        )
        if "退款" in description or "refund" in description.lower():
            event_type = LedgerEventType.REFUND
            review_state = "ACCEPTED"
            confidence = 0.93
        else:
            event_type = classification.event_type
            unknown = "未知" in description or not description.strip()
            review_state = "NEEDS_REVIEW" if unknown else classification.review_state
            confidence = 0.45 if unknown else (0.95 if review_state == "ACCEPTED" else 0.55)
        transaction = NormalizedTransaction(
            transaction_id=f"txn_alipay_{index:04d}_{sha256_bytes(canonical.encode('utf-8'))[:8]}",
            source_id="alipay_daily",
            raw_id=raw_id,
            account_id=account_id,
            event_type=event_type,
            amount=amount,
            currency=currency,
            occurred_at=date,
            description=description,
            confidence=confidence,
            review_state=review_state,
        )
        transactions.append(transaction)
        if transaction.review_state != "ACCEPTED":
            review_queue.append(_review_item(transaction.transaction_id, "Alipay low-confidence classification needs owner review."))

    return Stage2ImportResult(batch, tuple(raw_records), tuple(transactions), tuple(review_queue))


def _review_item(transaction_id: str, reason: str) -> ReviewQueueItem:
    return ReviewQueueItem(
        transaction_id=transaction_id,
        reason=reason,
        choices=("A accept suggested classification", "B mark as transfer", "C mark as consumption", "D keep pending"),
    )


def reconcile_cba_transfer(transaction: NormalizedTransaction) -> TransferMatch | None:
    text = transaction.description.lower()
    if "credit card" in text or "信用卡" in text or "repayment" in text or "还款" in text:
        return TransferMatch(
            transaction.transaction_id,
            "credit_card_repayment",
            affects_consumption=False,
            confidence=0.94,
            reason="Credit card repayment is not duplicate consumption.",
        )
    if transaction.event_type == LedgerEventType.TRANSFER or "moomoo" in text or "券商" in text:
        return TransferMatch(
            transaction.transaction_id,
            "investment_deposit",
            affects_consumption=False,
            confidence=0.92,
            reason="Bank-to-broker transfer is excluded from ordinary consumption.",
        )
    if "abc bullion" in text or "gold" in text or "bullion" in text or "黄金" in text:
        return TransferMatch(
            transaction.transaction_id,
            "bullion_payment",
            affects_consumption=False,
            confidence=0.88,
            reason="Bank payment to bullion account requires investment reconciliation.",
        )
    return None
