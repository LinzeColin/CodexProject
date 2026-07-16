from __future__ import annotations

import codecs
import hashlib
import json
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Sequence
from uuid import uuid4

from pfi_os.infrastructure.operational_import_store import ImportOperationalStore
from pfi_v02.stage2_import import (
    Stage2ImportResult,
    parse_alipay_bill_bytes,
    validated_alipay_zip_csv_bytes,
)


PREVIEW_SCHEMA = "PFIV025Stage7ImportPreviewV1"
BATCH_SCHEMA = "PFIV025Stage7ImportBatchV1"
REVIEW_SCHEMA = "PFIV025Stage7ReviewQueueV1"
LEDGER_SCHEMA = "PFIV025Stage7UnifiedLedgerV1"
MAX_UPLOAD_BYTES = 100 * 1024 * 1024

FIELD_MAPPING = (
    {"source_fields": ["交易时间"], "canonical_field": "occurred_at", "required": True},
    {"source_fields": ["金额", "收/支"], "canonical_field": "amount", "required": True},
    {"source_fields": ["固定 CNY"], "canonical_field": "currency", "required": True},
    {"source_fields": ["支付宝账户"], "canonical_field": "account_id", "required": True},
    {"source_fields": ["商品说明", "交易对方", "交易类型"], "canonical_field": "description", "required": True},
)


class ImportWorkflowError(RuntimeError):
    """A human-readable import workflow error that preserves transaction safety."""


@dataclass(frozen=True)
class UploadedImportFile:
    name: str
    content: bytes
    media_type: str = "application/octet-stream"


@dataclass(frozen=True)
class _ParsedFile:
    file_name: str
    content_sha256: str
    bytes_count: int
    source_id: str | None
    parser_version: str | None
    raw_store_ref: str
    status: str
    error_code: str | None
    error_text: str | None
    result: Stage2ImportResult | None


class ImportReviewLedgerService:
    """Preview, confirm, review, compensate, and retry one local import batch."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        raw_store_dir: Path | str | None = None,
    ) -> None:
        self.store = ImportOperationalStore(db_path=db_path, raw_store_dir=raw_store_dir)
        self.store.initialize()
        self.db_path = self.store.db_path
        self.raw_store_dir = self.store.raw_store_dir

    def preview_upload(self, files: Sequence[UploadedImportFile]) -> dict[str, Any]:
        normalized_input = tuple(self._normalize_upload(item) for item in files)
        unique: dict[str, UploadedImportFile] = {}
        for item in normalized_input:
            unique.setdefault(hashlib.sha256(item.content).hexdigest(), item)
        normalized = tuple(unique[key] for key in sorted(unique))
        if not normalized:
            raise ImportWorkflowError("至少需要一个本机上传文件")

        with self.store.preview_lock():
            return self._preview_upload_locked(normalized)

    def _preview_upload_locked(
        self, normalized: tuple[UploadedImportFile, ...]
    ) -> dict[str, Any]:
        """Run raw persistence through DB reference commit under one file lock."""

        digests = sorted(hashlib.sha256(item.content).hexdigest() for item in normalized)
        fingerprint = _hash_json({"contract": "v025-stage7-p71", "content_sha256": digests})
        with self.store.connect() as conn:
            existing = conn.execute(
                "SELECT batch_id FROM import_batches WHERE batch_fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        if existing is not None:
            return self.get_batch(str(existing["batch_id"]), idempotent_replay=True)

        batch_id = f"import:alipay:{fingerprint[:24]}"
        try:
            parsed = self._parse_files(normalized)
            if parsed["status"] == "preview_ready":
                self._filter_already_confirmed_transactions(parsed)
            persisted_batch_id, idempotent_replay = self._persist_new_preview(
                batch_id, fingerprint, parsed
            )
        except Exception:
            for item in normalized:
                self.store.discard_raw_if_unreferenced(hashlib.sha256(item.content).hexdigest())
            raise
        if idempotent_replay:
            for item in normalized:
                self.store.discard_raw_if_unreferenced(hashlib.sha256(item.content).hexdigest())
            return self.get_batch(persisted_batch_id, idempotent_replay=True)
        return self.get_batch(batch_id, idempotent_replay=False)

    def get_batch(self, batch_id: str, *, idempotent_replay: bool = False) -> dict[str, Any]:
        with self.store.connect() as conn:
            batch = conn.execute("SELECT * FROM import_batches WHERE batch_id = ?", (batch_id,)).fetchone()
            if batch is None:
                raise ImportWorkflowError("导入批次不存在")
            files = conn.execute(
                """
                SELECT file_name, content_sha256, bytes_count, source_id, parser_version, status, error_code
                FROM import_files WHERE batch_id = ? ORDER BY file_name, content_sha256
                """,
                (batch_id,),
            ).fetchall()
            ledger_count = int(
                conn.execute("SELECT COUNT(*) FROM ledger_entries WHERE batch_id = ?", (batch_id,)).fetchone()[0]
            )
            pending_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM import_review_queue WHERE batch_id = ? AND status = 'pending'",
                    (batch_id,),
                ).fetchone()[0]
            )

        status = str(batch["status"])
        schema = PREVIEW_SCHEMA if status in {"preview_ready", "failed"} else BATCH_SCHEMA
        return {
            "schema": schema,
            "batch_id": str(batch["batch_id"]),
            "source_id": str(batch["source_id"]),
            "status": status,
            "write_state": {
                "preview_ready": "staged_only",
                "confirmed": "ledger_committed",
                "failed": "no_ledger_write",
                "rolled_back": "compensated",
            }[status],
            "idempotent_replay": bool(idempotent_replay),
            "file_count": int(batch["file_count"]),
            "valid_file_count": int(batch["valid_file_count"]),
            "bytes_count": int(batch["bytes_count"]),
            "raw_record_count": int(batch["raw_record_count"]),
            "transaction_count": int(batch["transaction_count"]),
            "review_count": int(batch["review_count"]),
            "ledger_count": ledger_count,
            "pending_review_count": pending_count,
            "date_start": str(batch["date_start"]),
            "date_end": str(batch["date_end"]),
            "attempt_count": int(batch["attempt_count"]),
            "field_mapping": json.loads(str(batch["field_mapping_json"])),
            "errors": json.loads(str(batch["errors_json"])),
            "file_summaries": [
                {
                    "file_name": str(row["file_name"]),
                    "content_sha256": str(row["content_sha256"]),
                    "bytes_count": int(row["bytes_count"]),
                    "source_id": str(row["source_id"]) if row["source_id"] is not None else None,
                    "parser_version": str(row["parser_version"]) if row["parser_version"] is not None else None,
                    "status": str(row["status"]),
                    "error_code": str(row["error_code"]) if row["error_code"] is not None else None,
                }
                for row in files
            ],
        }

    def confirm_batch(self, batch_id: str) -> dict[str, Any]:
        try:
            with self.store.connect(immediate=True) as conn:
                batch = self._locked_batch(conn, batch_id)
                if str(batch["status"]) == "confirmed":
                    replay = True
                else:
                    replay = False
                    if str(batch["status"]) != "preview_ready":
                        raise ImportWorkflowError("只有解析预览通过的批次可以确认入账")
                    now = _now()
                    rows = conn.execute(
                        "SELECT * FROM import_staged_transactions WHERE batch_id = ? ORDER BY occurred_at, transaction_id",
                        (batch_id,),
                    ).fetchall()
                    inserted_count = 0
                    duplicate_count = 0
                    for row in rows:
                        ledger_entry_id = f"ledger:{row['transaction_id']}"
                        ledger_state = "posted" if str(row["review_state"]) == "ACCEPTED" else "pending_review"
                        inserted = conn.execute(
                            """
                            INSERT INTO ledger_entries(
                                ledger_entry_id, batch_id, transaction_id, source_id, raw_id, account_id,
                                event_type, amount, currency, occurred_at, description, confidence,
                                ledger_state, category, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?)
                            ON CONFLICT(ledger_entry_id) DO NOTHING
                            """,
                            (
                                ledger_entry_id,
                                batch_id,
                                str(row["transaction_id"]),
                                str(row["source_id"]),
                                str(row["raw_id"]),
                                str(row["account_id"]),
                                str(row["event_type"]),
                                str(row["amount"]),
                                str(row["currency"]),
                                str(row["occurred_at"]),
                                str(row["description"]),
                                float(row["confidence"]),
                                ledger_state,
                                now,
                                now,
                            ),
                        )
                        if inserted.rowcount != 1:
                            duplicate_count += 1
                            continue
                        inserted_count += 1
                        if ledger_state == "pending_review":
                            review_id = f"review:{hashlib.sha256(ledger_entry_id.encode()).hexdigest()[:24]}"
                            conn.execute(
                                """
                                INSERT INTO import_review_queue(
                                    review_id, ledger_entry_id, batch_id, transaction_id, status, reason,
                                    decision, category, version, created_at, updated_at, resolved_at
                                ) VALUES (?, ?, ?, ?, 'pending', ?, NULL, '', 1, ?, ?, NULL)
                                ON CONFLICT(ledger_entry_id) DO NOTHING
                                """,
                                (
                                    review_id,
                                    ledger_entry_id,
                                    batch_id,
                                    str(row["transaction_id"]),
                                    "分类置信度不足，需要人工确认后发布到账本",
                                    now,
                                    now,
                                ),
                            )
                    conn.execute(
                        "UPDATE import_batches SET status = 'confirmed', confirmed_at = ?, rolled_back_at = NULL, updated_at = ? WHERE batch_id = ?",
                        (now, now, batch_id),
                    )
                    self._audit(
                        conn,
                        batch_id,
                        "batch_confirmed",
                        {
                            "staged_transaction_count": len(rows),
                            "inserted_transaction_count": inserted_count,
                            "duplicate_transaction_count": duplicate_count,
                        },
                    )
        except ImportWorkflowError:
            raise
        except sqlite3.DatabaseError as exc:
            raise ImportWorkflowError(f"确认入账事务失败：{exc}") from exc
        return self.get_batch(batch_id, idempotent_replay=replay)

    def list_review_queue(self, *, status: str = "pending") -> dict[str, Any]:
        if status not in {"pending", "resolved", "all"}:
            raise ImportWorkflowError("复核状态必须是 pending、resolved 或 all")
        where = "" if status == "all" else "WHERE q.status = ?"
        params: tuple[Any, ...] = () if status == "all" else (status,)
        with self.store.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT q.*, l.ledger_state, l.event_type, l.amount, l.currency, l.occurred_at,
                       l.description, l.confidence
                FROM import_review_queue q
                JOIN ledger_entries l ON l.ledger_entry_id = q.ledger_entry_id
                {where}
                ORDER BY l.occurred_at, q.review_id
                """,
                params,
            ).fetchall()
            pending_count = int(
                conn.execute("SELECT COUNT(*) FROM import_review_queue WHERE status = 'pending'").fetchone()[0]
            )
        return {
            "schema": REVIEW_SCHEMA,
            "status_filter": status,
            "pending_count": pending_count,
            "item_count": len(rows),
            "items": [self._review_payload(row) for row in rows],
        }

    def resolve_review(self, review_id: str, *, decision: str, category: str = "") -> dict[str, Any]:
        if decision not in {"accept", "reclassify", "exclude"}:
            raise ImportWorkflowError("复核决定必须是 accept、reclassify 或 exclude")
        if decision == "reclassify" and not str(category).strip():
            raise ImportWorkflowError("重新分类必须提供分类")
        with self.store.connect(immediate=True) as conn:
            row = self._locked_review(conn, review_id)
            if str(row["status"]) == "resolved":
                return self._review_payload(row)
            ledger_state = "excluded" if decision == "exclude" else "posted"
            normalized_category = str(category).strip() if decision == "reclassify" else str(row["category"] or "")
            now = _now()
            conn.execute(
                "UPDATE ledger_entries SET ledger_state = ?, category = ?, updated_at = ? WHERE ledger_entry_id = ?",
                (ledger_state, normalized_category, now, str(row["ledger_entry_id"])),
            )
            conn.execute(
                """
                UPDATE import_review_queue
                SET status = 'resolved', decision = ?, category = ?, version = version + 1,
                    resolved_at = ?, updated_at = ?
                WHERE review_id = ?
                """,
                (decision, normalized_category, now, now, review_id),
            )
            self._audit(conn, str(row["batch_id"]), "review_resolved", {"decision": decision}, review_id=review_id)
        return self.get_review(review_id)

    def undo_review(self, review_id: str) -> dict[str, Any]:
        with self.store.connect(immediate=True) as conn:
            row = self._locked_review(conn, review_id)
            if str(row["status"]) == "pending":
                return self._review_payload(row)
            now = _now()
            conn.execute(
                "UPDATE ledger_entries SET ledger_state = 'pending_review', category = '', updated_at = ? WHERE ledger_entry_id = ?",
                (now, str(row["ledger_entry_id"])),
            )
            conn.execute(
                """
                UPDATE import_review_queue
                SET status = 'pending', decision = NULL, category = '', version = version + 1,
                    resolved_at = NULL, updated_at = ? WHERE review_id = ?
                """,
                (now, review_id),
            )
            self._audit(conn, str(row["batch_id"]), "review_undone", {}, review_id=review_id)
        return self.get_review(review_id)

    def get_review(self, review_id: str) -> dict[str, Any]:
        with self.store.connect() as conn:
            row = conn.execute(
                """
                SELECT q.*, l.ledger_state, l.event_type, l.amount, l.currency, l.occurred_at,
                       l.description, l.confidence
                FROM import_review_queue q
                JOIN ledger_entries l ON l.ledger_entry_id = q.ledger_entry_id
                WHERE q.review_id = ?
                """,
                (review_id,),
            ).fetchone()
        if row is None:
            raise ImportWorkflowError("复核项不存在")
        return self._review_payload(row)

    def list_ledger(self, *, batch_id: str = "") -> dict[str, Any]:
        where = "WHERE batch_id = ?" if batch_id else ""
        params: tuple[Any, ...] = (batch_id,) if batch_id else ()
        with self.store.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM ledger_entries {where} ORDER BY occurred_at, ledger_entry_id",
                params,
            ).fetchall()
        return {
            "schema": LEDGER_SCHEMA,
            "batch_id": batch_id or None,
            "ledger_count": len(rows),
            "posted_count": sum(str(row["ledger_state"]) == "posted" for row in rows),
            "pending_review_count": sum(str(row["ledger_state"]) == "pending_review" for row in rows),
            "excluded_count": sum(str(row["ledger_state"]) == "excluded" for row in rows),
            "entries": [
                {
                    "ledger_entry_id": str(row["ledger_entry_id"]),
                    "batch_id": str(row["batch_id"]),
                    "transaction_id": str(row["transaction_id"]),
                    "source_id": str(row["source_id"]),
                    "event_type": str(row["event_type"]),
                    "amount": str(row["amount"]),
                    "currency": str(row["currency"]),
                    "occurred_at": str(row["occurred_at"]),
                    "description": str(row["description"]),
                    "confidence": float(row["confidence"]),
                    "ledger_state": str(row["ledger_state"]),
                    "category": str(row["category"]),
                }
                for row in rows
            ],
        }

    def build_ledger_projection(self) -> dict[str, Any]:
        """Expose the operational ledger to the runtime read-model without leaking values."""

        with self.store.connect() as conn:
            rows = conn.execute(
                """
                SELECT ledger_entry_id, batch_id, transaction_id, source_id,
                       event_type, occurred_at, ledger_state, updated_at
                FROM ledger_entries
                ORDER BY occurred_at, ledger_entry_id
                """
            ).fetchall()
        records = [
            {
                "ledger_entry_id": str(row["ledger_entry_id"]),
                "batch_id": str(row["batch_id"]),
                "transaction_id": str(row["transaction_id"]),
                "source_id": str(row["source_id"]),
                "event_type": str(row["event_type"]),
                "occurred_at": str(row["occurred_at"]),
                "ledger_state": str(row["ledger_state"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]
        dates = sorted(item["occurred_at"] for item in records if item["occurred_at"])
        source_ids = sorted({item["source_id"] for item in records if item["source_id"]})
        state_counts = {
            state: sum(item["ledger_state"] == state for item in records)
            for state in ("posted", "pending_review", "excluded")
        }
        return {
            "schema": "PFIV025Stage7OperationalLedgerProjectionV1",
            "source": "SQLite unified operational ledger",
            "runtime_route": "/api/trends",
            "status": "ready" if records else "not_loaded",
            "ledger_count": len(records),
            "state_counts": state_counts,
            "source_ids": source_ids,
            "data_range": {
                "start": dates[0] if dates else None,
                "end": dates[-1] if dates else None,
            },
            "ledger_projection_hash": "sha256:" + _hash_json(records),
            "financial_values_emitted": 0,
            "contains_private_values": False,
        }

    def build_ledger_runtime_read_model(self) -> dict[str, Any]:
        """Build the private in-process value model consumed by runtime routes.

        Persistent review evidence must use ``build_ledger_projection`` instead;
        this model intentionally contains values and never writes them to disk.
        """

        with self.store.connect() as conn:
            rows = conn.execute(
                """
                SELECT ledger_entry_id, source_id, event_type, amount, currency,
                       occurred_at, ledger_state, description, updated_at
                FROM ledger_entries
                ORDER BY occurred_at, ledger_entry_id
                """
            ).fetchall()
        records = [
            {
                "ledger_entry_id": str(row["ledger_entry_id"]),
                "source_id": str(row["source_id"]),
                "event_type": str(row["event_type"]),
                "amount": format(Decimal(str(row["amount"])), "f"),
                "currency": str(row["currency"]),
                "occurred_at": str(row["occurred_at"]),
                "ledger_state": str(row["ledger_state"]),
                "description": str(row["description"]),
                "updated_at": str(row["updated_at"]),
            }
            for row in rows
        ]
        posted = [row for row in records if row["ledger_state"] == "posted"]
        consumption = [
            row
            for row in posted
            if row["event_type"] == "CASH" and Decimal(row["amount"]) < 0
        ]
        parsed_dates = [date.fromisoformat(row["occurred_at"][:10]) for row in posted]
        latest_date = max(parsed_dates) if parsed_dates else None
        latest_month = latest_date.strftime("%Y-%m") if latest_date else ""
        month_spend = sum(
            -Decimal(row["amount"])
            for row in consumption
            if row["occurred_at"].startswith(latest_month)
        ) if latest_month else Decimal("0")
        rolling_start = latest_date - timedelta(days=29) if latest_date else None
        rolling_spend = sum(
            -Decimal(row["amount"])
            for row in consumption
            if rolling_start is not None
            and rolling_start <= date.fromisoformat(row["occurred_at"][:10]) <= latest_date
        )
        event_type_counts = {
            event_type: sum(row["event_type"] == event_type for row in posted)
            for event_type in sorted({row["event_type"] for row in posted})
        }
        pending_review_count = sum(row["ledger_state"] == "pending_review" for row in records)
        # Ledger rows alone do not prove FORM-PFI-015 economic-event coverage
        # (deduplication, refund offsets, and confirmed-zero semantics).  Until
        # that adapter exists, trend values remain unpublished even when every
        # ledger row is posted.
        financial_values_publishable = False
        runtime_status = (
            "blocked_economic_event_adapter" if records and pending_review_count == 0
            else "partial_pending_review" if records
            else "not_loaded"
        )
        model_hash = "sha256:" + _hash_json(records)
        return {
            "schema": "PFIV025Stage7OperationalLedgerRuntimeReadModelV1",
            "status": runtime_status,
            "source": "SQLite unified operational ledger",
            "source_ids": sorted({row["source_id"] for row in records}),
            "ledger_count": len(records),
            "posted_count": len(posted),
            "pending_review_count": pending_review_count,
            "excluded_count": sum(row["ledger_state"] == "excluded" for row in records),
            "event_type_counts": event_type_counts,
            "economic_event_adapter_ready": False,
            "financial_values_publishable": financial_values_publishable,
            "data_range": {
                "start": min(parsed_dates).isoformat() if parsed_dates else None,
                "end": latest_date.isoformat() if latest_date else None,
            },
            "consumption": {
                "has_real_transactions": financial_values_publishable,
                "source": "SQLite unified operational ledger",
                "transaction_count": len(posted),
                "spending_transaction_count": len(consumption),
                "review_count": pending_review_count,
                "coverage_status": (
                    "complete_published_partition" if financial_values_publishable
                    else "partial_pending_review" if pending_review_count
                    else "blocked_economic_event_adapter" if records
                    else "not_loaded"
                ),
                "latest_month": latest_month,
                "latest_date": latest_date.isoformat() if latest_date else None,
                "month_spend_cny": float(month_spend) if financial_values_publishable else None,
                "budget_remaining_cny": None,
                "fixed_spend_cny": None,
                "flex_spend_cny": float(month_spend) if financial_values_publishable else None,
                "cashflow_forecast_cny": float(rolling_spend) if financial_values_publishable else None,
                "fixed_flex_policy": "未配置固定支出规则；已发布 CASH 流出暂列弹性支出。",
                "empty_state": (
                    "" if financial_values_publishable else
                    "流水仍在人工复核，未发布值不显示为零。" if pending_review_count else
                    "流水已发布，但 economic_event/interconnection adapter 尚未完成，财务值保持阻断。" if records else
                    "请先确认导入流水；不读取 legacy MetaDatabase 值。"
                ),
            },
            "read_model_hash": model_hash,
            "data_hash": model_hash,
            "contains_private_values": True,
            "persistence_allowed": False,
        }

    def rollback_batch(self, batch_id: str) -> dict[str, Any]:
        with self.store.connect(immediate=True) as conn:
            batch = self._locked_batch(conn, batch_id)
            if str(batch["status"]) == "rolled_back":
                replay = True
            else:
                replay = False
                if str(batch["status"]) != "confirmed":
                    raise ImportWorkflowError("只有已确认批次可以执行补偿回滚")
                owned_entries = conn.execute(
                    "SELECT ledger_entry_id, transaction_id FROM ledger_entries WHERE batch_id = ?",
                    (batch_id,),
                ).fetchall()
                transferred_count = 0
                deleted_count = 0
                for entry in owned_entries:
                    replacement = conn.execute(
                        """
                        SELECT staged.batch_id
                        FROM import_staged_transactions staged
                        JOIN import_batches batch ON batch.batch_id = staged.batch_id
                        WHERE staged.transaction_id = ?
                          AND staged.batch_id != ?
                          AND batch.status = 'confirmed'
                        ORDER BY batch.confirmed_at, staged.batch_id
                        LIMIT 1
                        """,
                        (str(entry["transaction_id"]), batch_id),
                    ).fetchone()
                    if replacement is not None:
                        replacement_batch_id = str(replacement["batch_id"])
                        conn.execute(
                            "UPDATE ledger_entries SET batch_id = ?, updated_at = ? WHERE ledger_entry_id = ?",
                            (replacement_batch_id, _now(), str(entry["ledger_entry_id"])),
                        )
                        conn.execute(
                            "UPDATE import_review_queue SET batch_id = ?, updated_at = ? WHERE ledger_entry_id = ?",
                            (replacement_batch_id, _now(), str(entry["ledger_entry_id"])),
                        )
                        transferred_count += 1
                    else:
                        conn.execute(
                            "DELETE FROM import_review_queue WHERE ledger_entry_id = ?",
                            (str(entry["ledger_entry_id"]),),
                        )
                        conn.execute(
                            "DELETE FROM ledger_entries WHERE ledger_entry_id = ?",
                            (str(entry["ledger_entry_id"]),),
                        )
                        deleted_count += 1
                now = _now()
                conn.execute(
                    "UPDATE import_batches SET status = 'rolled_back', rolled_back_at = ?, updated_at = ? WHERE batch_id = ?",
                    (now, now, batch_id),
                )
                self._audit(
                    conn,
                    batch_id,
                    "batch_rolled_back",
                    {
                        "ownership_transferred_count": transferred_count,
                        "ledger_deleted_count": deleted_count,
                    },
                )
        return self.get_batch(batch_id, idempotent_replay=replay)

    def retry_batch(self, batch_id: str) -> dict[str, Any]:
        with self.store.connect() as conn:
            batch = conn.execute("SELECT * FROM import_batches WHERE batch_id = ?", (batch_id,)).fetchone()
            if batch is None:
                raise ImportWorkflowError("导入批次不存在")
            if str(batch["status"]) not in {"failed", "rolled_back"}:
                raise ImportWorkflowError("只有失败或已回滚批次可以重试")
            expected_status = str(batch["status"])
            expected_attempt_count = int(batch["attempt_count"])
            file_rows = conn.execute(
                "SELECT file_name, content_sha256 FROM import_files WHERE batch_id = ? ORDER BY file_name",
                (batch_id,),
            ).fetchall()
        files = tuple(
            UploadedImportFile(
                name=str(row["file_name"]),
                content=self.store.read_raw(str(row["content_sha256"])),
            )
            for row in file_rows
        )
        parsed = self._parse_files(files)
        if parsed["status"] == "preview_ready":
            self._filter_already_confirmed_transactions(parsed, excluding_batch_id=batch_id)
        replaced = self._replace_preview(
            batch_id,
            parsed,
            expected_status=expected_status,
            expected_attempt_count=expected_attempt_count,
        )
        return self.get_batch(batch_id, idempotent_replay=not replaced)

    def _persist_new_preview(
        self, batch_id: str, fingerprint: str, parsed: dict[str, Any]
    ) -> tuple[str, bool]:
        now = _now()
        with self.store.connect(immediate=True) as conn:
            existing = conn.execute(
                "SELECT batch_id FROM import_batches WHERE batch_fingerprint = ?",
                (fingerprint,),
            ).fetchone()
            if existing is not None:
                return str(existing["batch_id"]), True
            conn.execute(
                """
                INSERT INTO import_batches(
                    batch_id, batch_fingerprint, source_id, status, file_count, valid_file_count,
                    bytes_count, raw_record_count, transaction_count, review_count, date_start, date_end,
                    field_mapping_json, errors_json, attempt_count, created_at, updated_at
                ) VALUES (?, ?, 'alipay_daily', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    batch_id,
                    fingerprint,
                    parsed["status"],
                    len(parsed["files"]),
                    parsed["valid_file_count"],
                    parsed["bytes_count"],
                    parsed["raw_record_count"],
                    int(parsed.get("new_transaction_count", len(parsed["transactions"]))),
                    parsed["review_count"],
                    parsed["date_start"],
                    parsed["date_end"],
                    _json(FIELD_MAPPING),
                    _json(parsed["errors"]),
                    now,
                    now,
                ),
            )
            self._insert_files(conn, batch_id, parsed["files"], now)
            self._insert_staged(conn, batch_id, parsed["transactions"], now)
            self._audit(conn, batch_id, "preview_created", {"status": parsed["status"]})
        return batch_id, False

    def _replace_preview(
        self,
        batch_id: str,
        parsed: dict[str, Any],
        *,
        expected_status: str,
        expected_attempt_count: int,
    ) -> bool:
        now = _now()
        with self.store.connect(immediate=True) as conn:
            batch = self._locked_batch(conn, batch_id)
            if (
                str(batch["status"]) != expected_status
                or int(batch["attempt_count"]) != expected_attempt_count
            ):
                return False
            conn.execute("DELETE FROM import_staged_transactions WHERE batch_id = ?", (batch_id,))
            conn.execute("DELETE FROM import_files WHERE batch_id = ?", (batch_id,))
            conn.execute(
                """
                UPDATE import_batches SET
                    status = ?, file_count = ?, valid_file_count = ?, bytes_count = ?, raw_record_count = ?,
                    transaction_count = ?, review_count = ?, date_start = ?, date_end = ?, errors_json = ?,
                    attempt_count = ?, updated_at = ?, confirmed_at = NULL, rolled_back_at = NULL
                WHERE batch_id = ?
                """,
                (
                    parsed["status"],
                    len(parsed["files"]),
                    parsed["valid_file_count"],
                    parsed["bytes_count"],
                    parsed["raw_record_count"],
                    int(parsed.get("new_transaction_count", len(parsed["transactions"]))),
                    parsed["review_count"],
                    parsed["date_start"],
                    parsed["date_end"],
                    _json(parsed["errors"]),
                    int(batch["attempt_count"]) + 1,
                    now,
                    batch_id,
                ),
            )
            self._insert_files(conn, batch_id, parsed["files"], now)
            self._insert_staged(conn, batch_id, parsed["transactions"], now)
            self._audit(conn, batch_id, "batch_retried", {"status": parsed["status"]})
        return True

    def _parse_files(self, files: Sequence[UploadedImportFile]) -> dict[str, Any]:
        parsed_files: list[_ParsedFile] = []
        staged: dict[str, dict[str, Any]] = {}
        errors: list[dict[str, str]] = []
        all_dates: list[str] = []
        raw_count = 0
        review_count = 0
        total_bytes = 0

        for item in files:
            digest = hashlib.sha256(item.content).hexdigest()
            total_bytes += len(item.content)
            raw_ref = self.store.write_raw(digest, item.content)
            source_id, parser_version, detection_error = _detect_source(item)
            if detection_error:
                parsed_files.append(
                    _ParsedFile(
                        item.name, digest, len(item.content), source_id, parser_version, raw_ref,
                        "error", detection_error, "无法识别受支持的本机财务来源", None,
                    )
                )
                errors.append({"file_sha256": digest, "code": detection_error, "message": "来源或格式不受支持"})
                continue
            try:
                result = parse_alipay_bill_bytes(item.content)
                if not result.transactions:
                    raise ValueError("解析结果没有有效流水；不会生成空白或虚构预览")
            except Exception as exc:
                parsed_files.append(
                    _ParsedFile(
                        item.name, digest, len(item.content), source_id, parser_version, raw_ref,
                        "error", "parse_failed", str(exc), None,
                    )
                )
                errors.append({"file_sha256": digest, "code": "parse_failed", "message": str(exc)})
                continue

            parsed_files.append(
                _ParsedFile(
                    item.name, digest, len(item.content), source_id, parser_version, raw_ref,
                    "ready", None, None, result,
                )
            )
            raw_count += len(result.raw_records)
            raw_by_id = {record.raw_id: record for record in result.raw_records}
            review_ids = {review.transaction_id for review in result.review_queue}
            for transaction in result.transactions:
                raw = raw_by_id.get(transaction.raw_id)
                payload_sha = str(raw.payload_sha256 if raw is not None else hashlib.sha256(transaction.raw_id.encode()).hexdigest())
                staged_id = f"staged:{source_id}:{payload_sha}"
                if staged_id in staged:
                    continue
                occurred_at = str(transaction.occurred_at)
                if occurred_at:
                    all_dates.append(occurred_at)
                transaction_id = f"txn:{source_id}:{payload_sha[:24]}"
                needs_review = transaction.transaction_id in review_ids or str(transaction.review_state) != "ACCEPTED"
                if needs_review:
                    review_count += 1
                staged[staged_id] = {
                    "staged_transaction_id": staged_id,
                    "transaction_id": transaction_id,
                    "source_id": str(source_id),
                    "raw_id": str(transaction.raw_id),
                    "account_id": str(transaction.account_id),
                    "event_type": str(getattr(transaction.event_type, "value", transaction.event_type)),
                    "amount": format(Decimal(str(transaction.amount)), "f"),
                    "currency": str(transaction.currency),
                    "occurred_at": occurred_at,
                    "description": str(transaction.description),
                    "confidence": float(transaction.confidence),
                    "review_state": "NEEDS_REVIEW" if needs_review else "ACCEPTED",
                    "payload_sha256": payload_sha,
                }

        status = "failed" if errors else "preview_ready"
        if status == "failed":
            staged = {}
            all_dates = []
            raw_count = 0
            review_count = 0
        dates = sorted(all_dates)
        return {
            "status": status,
            "files": parsed_files,
            "transactions": list(staged.values()),
            "errors": errors,
            "valid_file_count": sum(item.status == "ready" for item in parsed_files),
            "bytes_count": total_bytes,
            "raw_record_count": raw_count,
            "review_count": review_count,
            "date_start": dates[0] if dates else "",
            "date_end": dates[-1] if dates else "",
        }

    def _filter_already_confirmed_transactions(
        self,
        parsed: dict[str, Any],
        *,
        excluding_batch_id: str = "",
    ) -> None:
        """Improve preview clarity; confirm still enforces global dedup atomically."""

        with self.store.connect() as conn:
            params: tuple[Any, ...] = (excluding_batch_id,) if excluding_batch_id else ()
            exclusion = "AND batch.batch_id != ?" if excluding_batch_id else ""
            confirmed_hashes = {
                str(row[0])
                for row in conn.execute(
                    f"""
                    SELECT DISTINCT staged.payload_sha256
                    FROM import_staged_transactions staged
                    JOIN import_batches batch ON batch.batch_id = staged.batch_id
                    WHERE batch.status = 'confirmed' {exclusion}
                    """,
                    params,
                ).fetchall()
            }
        rows = list(parsed["transactions"])
        duplicate_count = sum(
            str(row["payload_sha256"]) in confirmed_hashes for row in rows
        )
        # Keep every staged claim.  Confirm remains globally idempotent, while
        # rollback can transfer ledger ownership to another confirmed batch
        # that contained the same source transaction.
        parsed["duplicate_transaction_count"] = duplicate_count
        parsed["new_transaction_count"] = len(rows) - duplicate_count
        parsed["review_count"] = sum(
            1
            for row in rows
            if row["review_state"] == "NEEDS_REVIEW"
            and str(row["payload_sha256"]) not in confirmed_hashes
        )

    @staticmethod
    def _normalize_upload(item: UploadedImportFile) -> UploadedImportFile:
        if not isinstance(item, UploadedImportFile):
            raise ImportWorkflowError("上传文件对象无效")
        name = Path(str(item.name or "")).name.strip()
        content = bytes(item.content or b"")
        if not name:
            raise ImportWorkflowError("上传文件名不能为空")
        if not content:
            raise ImportWorkflowError(f"{name} 是空文件")
        if len(content) > MAX_UPLOAD_BYTES:
            raise ImportWorkflowError(f"{name} 超过 {MAX_UPLOAD_BYTES // 1024 // 1024}MB")
        return UploadedImportFile(name=name, content=content, media_type=str(item.media_type or "application/octet-stream"))

    @staticmethod
    def _insert_files(conn: sqlite3.Connection, batch_id: str, files: Iterable[_ParsedFile], now: str) -> None:
        for item in files:
            file_id = f"file:{batch_id.split(':')[-1]}:{item.content_sha256[:20]}"
            conn.execute(
                """
                INSERT INTO import_files(
                    file_id, batch_id, file_name, content_sha256, bytes_count, source_id, parser_version,
                    raw_store_ref, status, error_code, error_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id, batch_id, item.file_name, item.content_sha256, item.bytes_count,
                    item.source_id, item.parser_version, item.raw_store_ref, item.status,
                    item.error_code, item.error_text, now,
                ),
            )

    @staticmethod
    def _insert_staged(conn: sqlite3.Connection, batch_id: str, rows: Iterable[dict[str, Any]], now: str) -> None:
        for row in rows:
            staged_transaction_id = f"staged:{batch_id.split(':')[-1]}:{row['payload_sha256'][:24]}"
            conn.execute(
                """
                INSERT INTO import_staged_transactions(
                    staged_transaction_id, batch_id, transaction_id, source_id, raw_id, account_id,
                    event_type, amount, currency, occurred_at, description, confidence,
                    review_state, payload_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    staged_transaction_id, batch_id, row["transaction_id"], row["source_id"],
                    row["raw_id"], row["account_id"], row["event_type"], row["amount"], row["currency"],
                    row["occurred_at"], row["description"], row["confidence"], row["review_state"],
                    row["payload_sha256"], now,
                ),
            )

    @staticmethod
    def _locked_batch(conn: sqlite3.Connection, batch_id: str) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM import_batches WHERE batch_id = ?", (batch_id,)).fetchone()
        if row is None:
            raise ImportWorkflowError("导入批次不存在")
        return row

    @staticmethod
    def _locked_review(conn: sqlite3.Connection, review_id: str) -> sqlite3.Row:
        row = conn.execute(
            """
            SELECT q.*, l.ledger_state, l.event_type, l.amount, l.currency, l.occurred_at,
                   l.description, l.confidence
            FROM import_review_queue q
            JOIN ledger_entries l ON l.ledger_entry_id = q.ledger_entry_id
            WHERE q.review_id = ?
            """,
            (review_id,),
        ).fetchone()
        if row is None:
            raise ImportWorkflowError("复核项不存在")
        return row

    @staticmethod
    def _review_payload(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "review_id": str(row["review_id"]),
            "batch_id": str(row["batch_id"]),
            "transaction_id": str(row["transaction_id"]),
            "status": str(row["status"]),
            "reason": str(row["reason"]),
            "decision": str(row["decision"]) if row["decision"] is not None else None,
            "category": str(row["category"]),
            "version": int(row["version"]),
            "ledger_state": str(row["ledger_state"]),
            "event_type": str(row["event_type"]),
            "amount": str(row["amount"]),
            "currency": str(row["currency"]),
            "occurred_at": str(row["occurred_at"]),
            "description": str(row["description"]),
            "confidence": float(row["confidence"]),
        }

    @staticmethod
    def _audit(
        conn: sqlite3.Connection,
        batch_id: str,
        event_type: str,
        metadata: dict[str, Any],
        *,
        review_id: str | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO import_audit_events(event_id, batch_id, review_id, event_type, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (f"event:{uuid4().hex}", batch_id, review_id, event_type, _json(metadata), _now()),
        )


def _detect_source(item: UploadedImportFile) -> tuple[str | None, str | None, str | None]:
    lower_name = item.name.lower()
    suffix = Path(lower_name).suffix
    if suffix not in {".csv", ".zip"}:
        return None, None, "unsupported_source"
    if suffix == ".zip":
        if not zipfile.is_zipfile(BytesIO(item.content)):
            return None, None, "parse_failed"
        try:
            csv_content = validated_alipay_zip_csv_bytes(item.content)
        except (ValueError, zipfile.BadZipFile):
            return None, None, "parse_failed"
        probe = _decode_probe(csv_content)
        if "交易时间" not in probe or "金额" not in probe or "收/支" not in probe:
            return None, None, "unsupported_source"
        return "alipay_daily", "alipay_bill_zip_v1", None
    text = _decode_probe(item.content)
    headers_say_alipay = "交易时间" in text and "金额" in text and "收/支" in text
    if headers_say_alipay:
        return "alipay_daily", "alipay_bill_csv_v1", None
    return None, None, "unsupported_source"


def _decode_probe(content: bytes) -> str:
    probe = content[:65536]
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            # The fixed-size probe can end in the middle of a multibyte
            # character.  Incremental decoding keeps that incomplete suffix
            # buffered while remaining strict about malformed bytes earlier
            # in the probe.
            decoder = codecs.getincrementaldecoder(encoding)(errors="strict")
            return decoder.decode(probe, final=False)
        except UnicodeDecodeError:
            continue
    return ""


def _hash_json(payload: Any) -> str:
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def _json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
