from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from pfi_v02.stage2_import import Stage2ImportResult, parse_alipay_bill_bytes, sha256_bytes


@dataclass(frozen=True)
class AlipayImportFileSummary:
    file_name: str
    content_sha256: str
    bytes_count: int
    raw_record_count: int
    transaction_count: int
    review_count: int
    date_start: str
    date_end: str
    status: str
    error: str = ""


@dataclass(frozen=True)
class AlipayImportPreview:
    schema: str
    generated_at: str
    file_count: int
    valid_file_count: int
    bytes_count: int
    raw_record_count: int
    transaction_count: int
    review_count: int
    date_start: str
    date_end: str
    file_summaries: tuple[AlipayImportFileSummary, ...]
    event_counts: dict[str, int]

    def as_dict(self) -> dict:
        return {
            **asdict(self),
            "file_summaries": [asdict(item) for item in self.file_summaries],
        }


def discover_local_alipay_raw_files(search_roots: Sequence[Path] | None = None) -> tuple[Path, ...]:
    home = Path.home()
    roots = tuple(search_roots or (
        home / "Documents/Codex/2026-06-03/files-mentioned-by-the-user-20250604/data/finance_ledger/sources",
        home / "Documents/Codex/2026-06-04/files-mentioned-by-the-user-01/data/raw",
    ))
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        candidates.extend(root.rglob("支付宝交易明细*.csv"))
        candidates.extend(root.rglob("alipay_*.csv"))

    unique: dict[str, Path] = {}
    for path in sorted(candidates):
        if not path.is_file() or path.stat().st_size < 10_000:
            continue
        digest = sha256_bytes(path.read_bytes())
        unique.setdefault(digest, path)
    return tuple(sorted(unique.values(), key=lambda item: str(item)))


def payloads_from_paths(paths: Iterable[Path]) -> tuple[tuple[str, bytes], ...]:
    return tuple((path.name, path.read_bytes()) for path in paths if path.is_file())


def build_alipay_import_preview(payloads: Sequence[tuple[str, bytes]]) -> AlipayImportPreview:
    generated_at = datetime.now(timezone.utc).isoformat()
    summaries: list[AlipayImportFileSummary] = []
    event_counts: dict[str, int] = {}
    all_dates: list[str] = []
    total_raw = 0
    total_transactions = 0
    total_review = 0
    total_bytes = 0

    for file_name, content in payloads:
        total_bytes += len(content)
        digest = sha256_bytes(content)
        try:
            result = parse_alipay_bill_bytes(content)
        except Exception as exc:  # pragma: no cover - exercised through status in UI
            summaries.append(
                AlipayImportFileSummary(
                    file_name=file_name,
                    content_sha256=digest,
                    bytes_count=len(content),
                    raw_record_count=0,
                    transaction_count=0,
                    review_count=0,
                    date_start="",
                    date_end="",
                    status="Error",
                    error=str(exc),
                )
            )
            continue

        dates = sorted(txn.occurred_at for txn in result.transactions if _is_iso_date(txn.occurred_at))
        all_dates.extend(dates)
        total_raw += result.import_batch.raw_record_count
        total_transactions += len(result.transactions)
        total_review += len(result.review_queue)
        for txn in result.transactions:
            key = str(getattr(txn.event_type, "value", txn.event_type))
            event_counts[key] = event_counts.get(key, 0) + 1
        summaries.append(
            AlipayImportFileSummary(
                file_name=file_name,
                content_sha256=digest,
                bytes_count=len(content),
                raw_record_count=result.import_batch.raw_record_count,
                transaction_count=len(result.transactions),
                review_count=len(result.review_queue),
                date_start=dates[0] if dates else "",
                date_end=dates[-1] if dates else "",
                status="Ready",
            )
        )

    valid_count = sum(1 for item in summaries if item.status == "Ready")
    sorted_dates = sorted(all_dates)
    return AlipayImportPreview(
        schema="PFIAlipayLocalImportPreviewV1",
        generated_at=generated_at,
        file_count=len(payloads),
        valid_file_count=valid_count,
        bytes_count=total_bytes,
        raw_record_count=total_raw,
        transaction_count=total_transactions,
        review_count=total_review,
        date_start=sorted_dates[0] if sorted_dates else "",
        date_end=sorted_dates[-1] if sorted_dates else "",
        file_summaries=tuple(summaries),
        event_counts=dict(sorted(event_counts.items())),
    )


def write_private_alipay_import(
    payloads: Sequence[tuple[str, bytes]],
    data_home: Path,
    *,
    metadatabase_root: Path | None = None,
) -> dict:
    preview = build_alipay_import_preview(payloads)
    upload_dir = data_home / "runtime" / "uploads" / "alipay_daily"
    import_dir = data_home / "runtime" / "imports" / "alipay_daily"
    metadatabase_dir = metadatabase_root or _default_metadatabase_alipay_root()
    metadatabase_raw_dir = metadatabase_dir / "raw"
    metadatabase_processed_dir = metadatabase_dir / "processed"
    upload_dir.mkdir(parents=True, exist_ok=True)
    import_dir.mkdir(parents=True, exist_ok=True)
    metadatabase_raw_dir.mkdir(parents=True, exist_ok=True)
    metadatabase_processed_dir.mkdir(parents=True, exist_ok=True)

    transaction_rows: list[dict[str, object]] = []
    seen_transaction_ids: set[str] = set()
    private_files: list[dict[str, object]] = []
    metadatabase_files: list[dict[str, object]] = []
    for file_name, content in payloads:
        digest = sha256_bytes(content)
        suffix = Path(file_name).suffix.lower() if Path(file_name).suffix.lower() in {".csv", ".zip"} else ".csv"
        private_name = f"{digest[:16]}_{_safe_file_stem(file_name)}{suffix}"
        private_path = upload_dir / private_name
        metadatabase_path = metadatabase_raw_dir / private_name
        private_path.write_bytes(content)
        metadatabase_path.write_bytes(content)
        private_files.append({"file_name": file_name, "sha256": digest, "private_path": str(private_path)})
        metadatabase_files.append({"file_name": file_name, "sha256": digest, "metadatabase_path": str(metadatabase_path)})
        try:
            result = parse_alipay_bill_bytes(content)
        except Exception:
            continue
        transaction_rows.extend(_transaction_rows(result, seen_transaction_ids))

    transactions_path = import_dir / "alipay_transactions.csv"
    manifest_path = import_dir / "alipay_import_manifest.json"
    metadatabase_transactions_path = metadatabase_processed_dir / "alipay_transactions.csv"
    metadatabase_manifest_path = metadatabase_processed_dir / "alipay_import_manifest.json"
    if transaction_rows:
        _write_transaction_rows(transactions_path, transaction_rows)
        _write_transaction_rows(metadatabase_transactions_path, transaction_rows)
    else:
        transactions_path.write_text("", encoding="utf-8")
        metadatabase_transactions_path.write_text("", encoding="utf-8")

    manifest = {
        **preview.as_dict(),
        "private_upload_dir": str(upload_dir),
        "private_transactions_path": str(transactions_path),
        "private_manifest_path": str(manifest_path),
        "private_files": private_files,
        "metadatabase_raw_dir": str(metadatabase_raw_dir),
        "metadatabase_transactions_path": str(metadatabase_transactions_path),
        "metadatabase_manifest_path": str(metadatabase_manifest_path),
        "metadatabase_files": metadatabase_files,
        "privacy_boundary": "owner_authorized_metadatabase_archive_and_local_private_runtime",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    metadatabase_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def copy_discovered_alipay_raw_files_to_data_home(data_home: Path, search_roots: Sequence[Path] | None = None) -> dict:
    paths = discover_local_alipay_raw_files(search_roots)
    return write_private_alipay_import(payloads_from_paths(paths), data_home)


def _transaction_rows(result: Stage2ImportResult, seen_transaction_ids: set[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for txn in result.transactions:
        if txn.transaction_id in seen_transaction_ids:
            continue
        seen_transaction_ids.add(txn.transaction_id)
        rows.append(
            {
                "transaction_id": txn.transaction_id,
                "batch_id": result.import_batch.batch_id,
                "source_id": txn.source_id,
                "raw_id": txn.raw_id,
                "account_id": txn.account_id,
                "event_type": str(getattr(txn.event_type, "value", txn.event_type)),
                "amount": txn.amount,
                "currency": txn.currency,
                "occurred_at": txn.occurred_at,
                "description": txn.description,
                "confidence": txn.confidence,
                "review_state": txn.review_state,
            }
        )
    return rows


def _write_transaction_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _default_metadatabase_alipay_root() -> Path:
    return Path(__file__).resolve().parents[3] / "MetaDatabase" / "PFI" / "alipay_daily"


def _safe_file_stem(file_name: str) -> str:
    stem = Path(file_name).stem or "alipay_bill"
    cleaned = re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", stem).strip("._")
    return cleaned[:80] or "alipay_bill"


def _is_iso_date(value: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(value or "")))
