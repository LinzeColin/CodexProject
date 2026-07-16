from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence
from uuid import uuid4

from pfi_os.infrastructure.operational_holding_settings_store import (
    HoldingSettingsOperationalStore,
)


HOLDINGS_SCHEMA = "PFIV025Stage7HoldingsV1"
HOLDING_PROJECTION_SCHEMA = "PFIV025Stage7HoldingProjectionV1"
HOLDING_REPORT_SCHEMA = "PFIV025Stage7HoldingReportV1"
SETTINGS_SCHEMA = "PFIV025Stage7SettingsPreferencesV1"
SETTINGS_SCOPE = "local_user_preferences"

DEFAULT_SETTINGS: dict[str, object] = {
    "default_account": "主账户",
    "theme_language": "中文优先",
    "feedback_haptic": True,
    "feedback_sound": False,
    "feedback_motion": True,
}

ALLOWED_DEFAULT_ACCOUNTS = {"主账户", "投资复盘", "消费复盘"}
ALLOWED_THEME_LANGUAGES = {"中文优先", "跟随系统"}


class HoldingSettingsWorkflowError(RuntimeError):
    """Actionable validation or concurrency failure for the local workflow."""


class HoldingSettingsPersistenceService:
    """Atomic holding CRUD and settings persistence for PFI v0.2.5 Phase 7.2."""

    def __init__(
        self,
        db_path: Any = None,
        backup_dir: Any = None,
    ) -> None:
        self.store = HoldingSettingsOperationalStore(db_path=db_path, backup_dir=backup_dir)
        self.store.initialize()
        self.db_path = self.store.db_path

    @staticmethod
    def phase_contract() -> dict[str, Any]:
        return {
            "schema": "PFIV025Stage7Phase72RunContractV1",
            "version": "v0.2.5",
            "stage": 7,
            "phase_id": "V025-S7-P7.2",
            "task_ids": ["S7-P2-T1", "S7-P2-T2", "S7-P2-T3", "S7-P2-T4"],
            "acceptance_id": "ACC-PFI-V025-S7-P72-HOLDINGS-SETTINGS",
            "current_phase_only": True,
            "financial_sentinel_counts_as_real_acceptance": False,
            "finder_used": False,
            "external_network_allowed": False,
            "phase_7_3_started": False,
            "whole_stage_review_started": False,
        }

    def list_holdings(self, *, include_deleted: bool = False) -> dict[str, Any]:
        with self.store.connect() as conn:
            rows = self._select_rows(conn, include_deleted=include_deleted)
            active_rows = [row for row in rows if str(row["status"]) == "active"]
            deleted_count = int(
                conn.execute("SELECT COUNT(*) FROM v025_holding_records WHERE status = 'deleted'").fetchone()[0]
            )
            event_count = int(conn.execute("SELECT COUNT(*) FROM v025_holding_events").fetchone()[0])
            change_set_count = int(conn.execute("SELECT COUNT(*) FROM v025_holding_change_sets").fetchone()[0])
        payload_rows = [self._row_payload(row) for row in rows]
        projection = self._projection([self._row_payload(row) for row in active_rows])
        return {
            "schema": HOLDINGS_SCHEMA,
            "rows": payload_rows,
            "summary": {
                "active_count": len(active_rows),
                "deleted_count": deleted_count,
                "snapshot_count": len(active_rows),
                "event_count": event_count,
                "adjustment_count": event_count,
                "change_set_count": change_set_count,
                "storage_mode": "sqlite_operational_private",
                "tables": [
                    "v025_holding_records",
                    "v025_holding_change_sets",
                    "v025_holding_events",
                ],
            },
            "projection": projection,
        }

    def commit_holdings(
        self,
        *,
        request_id: str,
        operations: Sequence[Mapping[str, Any]],
        expected_projection_hash: str = "",
    ) -> dict[str, Any]:
        clean_request_id = _validated_text(request_id, "request_id", maximum=128)
        if not isinstance(operations, Sequence) or isinstance(operations, (str, bytes)):
            raise HoldingSettingsWorkflowError("operations must be a list")
        if not operations:
            raise HoldingSettingsWorkflowError("operations must contain at least one create, update, or delete")
        if len(operations) > 100:
            raise HoldingSettingsWorkflowError("operations exceeds the 100 item transaction limit")
        if any(not isinstance(item, Mapping) for item in operations):
            raise HoldingSettingsWorkflowError("each holding operation must be an object")
        expected = str(expected_projection_hash or "").strip()
        command_hash = _hash_json(
            {"expected_projection_hash": expected, "operations": [dict(item) for item in operations]}
        )

        replay = False
        try:
            with self.store.connect(immediate=True) as conn:
                existing_request = conn.execute(
                    "SELECT request_id, command_hash FROM v025_holding_change_sets WHERE request_id = ?",
                    (clean_request_id,),
                ).fetchone()
                if existing_request is not None:
                    if not str(existing_request["command_hash"] or "") or str(existing_request["command_hash"]) != command_hash:
                        raise HoldingSettingsWorkflowError(
                            "request_id conflict: the same id cannot be reused for a different holding command"
                        )
                    replay = True
                else:
                    before_rows = [self._row_payload(row) for row in self._select_rows(conn, include_deleted=False)]
                    before_hash = self._projection_hash(before_rows)
                    if expected and expected != before_hash:
                        raise HoldingSettingsWorkflowError(
                            "projection revision conflict: refresh holdings before saving"
                        )
                    now = _now()
                    conn.execute(
                        """
                        INSERT INTO v025_holding_change_sets(
                            request_id, operation_count, projection_hash_before,
                            projection_hash_after, command_hash, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (clean_request_id, len(operations), before_hash, before_hash, command_hash, now),
                    )
                    for index, raw_operation in enumerate(operations):
                        self._apply_holding_operation(
                            conn,
                            request_id=clean_request_id,
                            index=index,
                            raw_operation=raw_operation,
                            now=now,
                        )
                    after_rows = [self._row_payload(row) for row in self._select_rows(conn, include_deleted=False)]
                    after_hash = self._projection_hash(after_rows)
                    conn.execute(
                        "UPDATE v025_holding_change_sets SET projection_hash_after = ? WHERE request_id = ?",
                        (after_hash, clean_request_id),
                    )
        except HoldingSettingsWorkflowError:
            raise
        except (sqlite3.DatabaseError, ValueError, TypeError) as exc:
            raise HoldingSettingsWorkflowError(f"holding transaction failed: {exc}") from exc

        payload = self.list_holdings()
        payload["request_id"] = clean_request_id
        payload["command_hash"] = command_hash
        payload["idempotent_replay"] = replay
        return payload

    def build_holding_projection(self) -> dict[str, Any]:
        holdings = self.list_holdings()
        projection = holdings["projection"]
        return {
            "schema": HOLDING_PROJECTION_SCHEMA,
            "source": "SQLite private operational holding records",
            "projection": projection,
            "home": dict(projection["home"]),
            "investment": dict(projection["investment"]),
            "report": dict(projection["report"]),
            "consistency": {
                "surface_projection_hash_same": len(
                    {
                        projection["home"]["projection_hash"],
                        projection["investment"]["projection_hash"],
                        projection["report"]["projection_hash"],
                    }
                )
                == 1,
                "financial_values_emitted": projection["financial_values_emitted"],
                "financial_sentinel_counts_as_real_acceptance": False,
            },
        }

    def build_holding_report(self) -> dict[str, Any]:
        holdings = self.list_holdings()
        projection = holdings["projection"]
        return {
            "schema": HOLDING_REPORT_SCHEMA,
            "title": "持仓持久化状态",
            "projection_hash": projection["projection_hash"],
            "holding_count": projection["holding_count"],
            "valuation_status": projection["valuation_status"],
            "market_value_cny": None,
            "financial_values_emitted": 0,
            "blocked_reason_zh": projection["blocked_reason_zh"],
            "rows": holdings["rows"],
        }

    def get_settings(self) -> dict[str, Any]:
        with self.store.connect() as conn:
            row = conn.execute(
                "SELECT * FROM v025_settings_preferences WHERE scope = ?",
                (SETTINGS_SCOPE,),
            ).fetchone()
        if row is None:
            preferences = dict(DEFAULT_SETTINGS)
            revision = 0
            persisted = False
            updated_at = None
            payload_hash = _hash_json(preferences)
        else:
            preferences = _settings_payload(json.loads(str(row["payload_json"])))
            revision = int(row["revision"])
            persisted = True
            updated_at = str(row["updated_at"])
            payload_hash = str(row["payload_hash"])
        return {
            "schema": SETTINGS_SCHEMA,
            "scope": SETTINGS_SCOPE,
            "surface_scope": "settings_only",
            "preferences": preferences,
            "revision": revision,
            "persisted": persisted,
            "updated_at": updated_at,
            "settings_hash": payload_hash,
        }

    def save_settings(
        self,
        preferences: Mapping[str, Any],
        *,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        normalized = _settings_payload(preferences)
        payload_hash = _hash_json(normalized)
        replay = False
        try:
            with self.store.connect(immediate=True) as conn:
                row = conn.execute(
                    "SELECT * FROM v025_settings_preferences WHERE scope = ?",
                    (SETTINGS_SCOPE,),
                ).fetchone()
                current_revision = int(row["revision"]) if row is not None else 0
                if expected_revision is not None and int(expected_revision) != current_revision:
                    raise HoldingSettingsWorkflowError(
                        "settings revision conflict: refresh settings before saving"
                    )
                if row is not None and str(row["payload_hash"]) == payload_hash:
                    replay = True
                else:
                    revision = current_revision + 1
                    now = _now()
                    conn.execute(
                        """
                        INSERT INTO v025_settings_preferences(
                            scope, payload_json, payload_hash, revision, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(scope) DO UPDATE SET
                            payload_json=excluded.payload_json,
                            payload_hash=excluded.payload_hash,
                            revision=excluded.revision,
                            updated_at=excluded.updated_at
                        """,
                        (SETTINGS_SCOPE, _json(normalized), payload_hash, revision, now, now),
                    )
                    conn.execute(
                        """
                        INSERT INTO v025_settings_events(event_id, scope, revision, payload_hash, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (f"settings-event:{uuid4().hex}", SETTINGS_SCOPE, revision, payload_hash, now),
                    )
        except HoldingSettingsWorkflowError:
            raise
        except (sqlite3.DatabaseError, ValueError, TypeError) as exc:
            raise HoldingSettingsWorkflowError(f"settings transaction failed: {exc}") from exc

        payload = self.get_settings()
        payload["idempotent_replay"] = replay
        return payload

    def _apply_holding_operation(
        self,
        conn: sqlite3.Connection,
        *,
        request_id: str,
        index: int,
        raw_operation: Mapping[str, Any],
        now: str,
    ) -> None:
        if not isinstance(raw_operation, Mapping):
            raise HoldingSettingsWorkflowError("each holding operation must be an object")
        operation = str(raw_operation.get("operation") or "").strip().lower()
        if operation == "create":
            client_ref = _validated_text(raw_operation.get("client_ref"), "client_ref", maximum=128)
            holding = _holding_payload(raw_operation.get("holding"))
            holding_id = f"holding:{hashlib.sha256(f'{request_id}:{client_ref}'.encode()).hexdigest()[:24]}"
            if conn.execute(
                "SELECT 1 FROM v025_holding_records WHERE client_ref = ? OR holding_id = ?",
                (client_ref, holding_id),
            ).fetchone() is not None:
                raise HoldingSettingsWorkflowError("client_ref already exists; refresh holdings before saving")
            conn.execute(
                """
                INSERT INTO v025_holding_records(
                    holding_id, client_ref, portfolio_id, instrument_id, display_name,
                    quantity, average_cost, market_price, currency, source_id, as_of,
                    note, status, revision, created_at, updated_at, deleted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual_user_entry', ?, ?, 'active', 1, ?, ?, NULL)
                """,
                (
                    holding_id,
                    client_ref,
                    holding["portfolio_id"],
                    holding["instrument_id"],
                    holding["display_name"],
                    holding["quantity"],
                    holding["average_cost"],
                    holding["market_price"],
                    holding["currency"],
                    holding["as_of"],
                    holding["note"],
                    now,
                    now,
                ),
            )
            after = conn.execute(
                "SELECT * FROM v025_holding_records WHERE holding_id = ?",
                (holding_id,),
            ).fetchone()
            self._insert_holding_event(
                conn,
                request_id=request_id,
                index=index,
                holding_id=holding_id,
                operation=operation,
                revision=1,
                before_hash=None,
                after_hash=_hash_json(self._row_payload(after)),
                now=now,
            )
            return

        if operation not in {"update", "delete"}:
            raise HoldingSettingsWorkflowError("operation must be create, update, or delete")
        holding_id = _validated_text(raw_operation.get("holding_id"), "holding_id", maximum=128)
        expected_revision = _positive_integer(raw_operation.get("expected_revision"), "expected_revision")
        current = conn.execute(
            "SELECT * FROM v025_holding_records WHERE holding_id = ?",
            (holding_id,),
        ).fetchone()
        if current is None or str(current["status"]) != "active":
            raise HoldingSettingsWorkflowError("holding does not exist or is already deleted")
        if int(current["revision"]) != expected_revision:
            raise HoldingSettingsWorkflowError("holding revision conflict: refresh holdings before saving")
        before_hash = _hash_json(self._row_payload(current))
        revision = expected_revision + 1

        if operation == "update":
            holding = _holding_payload(raw_operation.get("holding"))
            conn.execute(
                """
                UPDATE v025_holding_records SET
                    portfolio_id = ?, instrument_id = ?, display_name = ?, quantity = ?,
                    average_cost = ?, market_price = ?, currency = ?, as_of = ?, note = ?,
                    revision = ?, updated_at = ?
                WHERE holding_id = ?
                """,
                (
                    holding["portfolio_id"],
                    holding["instrument_id"],
                    holding["display_name"],
                    holding["quantity"],
                    holding["average_cost"],
                    holding["market_price"],
                    holding["currency"],
                    holding["as_of"],
                    holding["note"],
                    revision,
                    now,
                    holding_id,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE v025_holding_records
                SET status = 'deleted', revision = ?, updated_at = ?, deleted_at = ?
                WHERE holding_id = ?
                """,
                (revision, now, now, holding_id),
            )
        after = conn.execute(
            "SELECT * FROM v025_holding_records WHERE holding_id = ?",
            (holding_id,),
        ).fetchone()
        self._insert_holding_event(
            conn,
            request_id=request_id,
            index=index,
            holding_id=holding_id,
            operation=operation,
            revision=revision,
            before_hash=before_hash,
            after_hash=_hash_json(self._row_payload(after)),
            now=now,
        )

    @staticmethod
    def _insert_holding_event(
        conn: sqlite3.Connection,
        *,
        request_id: str,
        index: int,
        holding_id: str,
        operation: str,
        revision: int,
        before_hash: str | None,
        after_hash: str,
        now: str,
    ) -> None:
        event_id = f"holding-event:{hashlib.sha256(f'{request_id}:{index}:{operation}'.encode()).hexdigest()[:24]}"
        conn.execute(
            """
            INSERT INTO v025_holding_events(
                event_id, request_id, holding_id, operation, revision,
                before_hash, after_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, request_id, holding_id, operation, revision, before_hash, after_hash, now),
        )

    @staticmethod
    def _select_rows(conn: sqlite3.Connection, *, include_deleted: bool) -> list[sqlite3.Row]:
        where = "" if include_deleted else "WHERE status = 'active'"
        return conn.execute(
            f"""
            SELECT * FROM v025_holding_records {where}
            ORDER BY portfolio_id, instrument_id, holding_id
            """
        ).fetchall()

    @staticmethod
    def _row_payload(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "holding_id": str(row["holding_id"]),
            "client_ref": str(row["client_ref"]),
            "portfolio_id": str(row["portfolio_id"]),
            "instrument_id": str(row["instrument_id"]),
            "display_name": str(row["display_name"]),
            "quantity": str(row["quantity"]),
            "average_cost": str(row["average_cost"]) if row["average_cost"] is not None else None,
            "market_price": str(row["market_price"]) if row["market_price"] is not None else None,
            "currency": str(row["currency"]),
            "source_id": str(row["source_id"]),
            "as_of": str(row["as_of"]),
            "note": str(row["note"]),
            "status": str(row["status"]),
            "soft_deleted": str(row["status"]) == "deleted",
            "revision": int(row["revision"]),
            "updated_at": str(row["updated_at"]),
        }

    @classmethod
    def _projection(cls, rows: list[dict[str, Any]]) -> dict[str, Any]:
        projection_hash = cls._projection_hash(rows)
        holding_count = len(rows)
        valuation_status = "valuation_missing" if rows else "not_loaded"
        blocked_reason = (
            "持仓已保存，但缺少可验证的市场价格、FX 与成本口径；金额保持空值。"
            if rows
            else "尚未保存真实持仓；金额保持空值。"
        )
        surface_base = {
            "holding_count": holding_count,
            "projection_hash": projection_hash,
            "valuation_status": valuation_status,
        }
        return {
            "schema": HOLDING_PROJECTION_SCHEMA,
            "projection_hash": projection_hash,
            "holding_count": holding_count,
            "valuation_status": valuation_status,
            "financial_acceptance_input": False,
            "financial_values_emitted": 0,
            "blocked_reason_zh": blocked_reason,
            "home": {**surface_base, "investment_market_value_cny": None},
            "investment": {
                **surface_base,
                "market_value_cny": None,
                "cost_basis_cny": None,
                "unrealized_pnl_cny": None,
            },
            "report": {**surface_base, "market_value_cny": None},
        }

    @staticmethod
    def _projection_hash(rows: list[dict[str, Any]]) -> str:
        semantic = [
            {
                key: row.get(key)
                for key in (
                    "holding_id",
                    "client_ref",
                    "portfolio_id",
                    "instrument_id",
                    "display_name",
                    "quantity",
                    "average_cost",
                    "market_price",
                    "currency",
                    "source_id",
                    "as_of",
                    "note",
                    "status",
                    "revision",
                )
            }
            for row in rows
        ]
        return "sha256:" + _hash_json(semantic)


def _holding_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise HoldingSettingsWorkflowError("holding must be an object")
    quantity = _decimal_string(value.get("quantity"), "quantity", positive=True)
    average_cost = _decimal_string(value.get("average_cost"), "average_cost", optional=True)
    market_price = _decimal_string(value.get("market_price"), "market_price", optional=True)
    currency = _validated_text(value.get("currency"), "currency", maximum=3).upper()
    if len(currency) != 3 or not currency.isalpha() or not currency.isascii():
        raise HoldingSettingsWorkflowError("currency must be a three-letter ISO code")
    as_of = _validated_as_of(value.get("as_of"))
    return {
        "portfolio_id": _validated_text(value.get("portfolio_id"), "portfolio_id", maximum=80),
        "instrument_id": _validated_text(value.get("instrument_id"), "instrument_id", maximum=80),
        "display_name": _validated_text(value.get("display_name"), "display_name", maximum=120),
        "quantity": quantity,
        "average_cost": average_cost,
        "market_price": market_price,
        "currency": currency,
        "as_of": as_of,
        "note": _validated_text(value.get("note", ""), "note", maximum=500, allow_empty=True),
    }


def _settings_payload(value: Any) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise HoldingSettingsWorkflowError("preferences must be an object")
    expected_keys = set(DEFAULT_SETTINGS)
    actual_keys = set(value)
    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)
    if missing:
        raise HoldingSettingsWorkflowError(f"preferences missing required keys: {', '.join(missing)}")
    if extra:
        raise HoldingSettingsWorkflowError(f"preferences contain unsupported keys: {', '.join(extra)}")
    default_account = str(value.get("default_account") or "").strip()
    if default_account not in ALLOWED_DEFAULT_ACCOUNTS:
        raise HoldingSettingsWorkflowError("default_account is not supported")
    theme_language = str(value.get("theme_language") or "").strip()
    if theme_language not in ALLOWED_THEME_LANGUAGES:
        raise HoldingSettingsWorkflowError("theme_language is not supported")
    booleans: dict[str, bool] = {}
    for key in ("feedback_haptic", "feedback_sound", "feedback_motion"):
        raw = value.get(key)
        if not isinstance(raw, bool):
            raise HoldingSettingsWorkflowError(f"{key} must be boolean")
        booleans[key] = raw
    return {
        "default_account": default_account,
        "theme_language": theme_language,
        **booleans,
    }


def _decimal_string(
    value: Any,
    field_name: str,
    *,
    positive: bool = False,
    optional: bool = False,
) -> str | None:
    if value is None or str(value).strip() == "":
        if optional:
            return None
        raise HoldingSettingsWorkflowError(f"{field_name} is required")
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise HoldingSettingsWorkflowError(f"{field_name} must be a decimal number") from exc
    try:
        finite_float = math.isfinite(float(number))
    except (OverflowError, ValueError) as exc:
        raise HoldingSettingsWorkflowError(f"{field_name} must be finite") from exc
    if not number.is_finite() or not finite_float:
        raise HoldingSettingsWorkflowError(f"{field_name} must be finite")
    if positive and number <= 0:
        raise HoldingSettingsWorkflowError(f"{field_name} must be greater than zero")
    if not positive and number < 0:
        raise HoldingSettingsWorkflowError(f"{field_name} must be non-negative")
    normalized = format(number.normalize(), "f")
    return "0" if normalized in {"-0", ""} else normalized


def _positive_integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise HoldingSettingsWorkflowError(f"{field_name} must be a positive integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise HoldingSettingsWorkflowError(f"{field_name} must be a positive integer") from exc
    if number < 1 or str(value).strip() not in {str(number), f"{number}.0"}:
        raise HoldingSettingsWorkflowError(f"{field_name} must be a positive integer")
    return number


def _validated_text(
    value: Any,
    field_name: str,
    *,
    maximum: int,
    allow_empty: bool = False,
) -> str:
    text = str(value if value is not None else "").strip()
    if not text and not allow_empty:
        raise HoldingSettingsWorkflowError(f"{field_name} is required")
    if len(text) > maximum:
        raise HoldingSettingsWorkflowError(f"{field_name} exceeds {maximum} characters")
    if any(ord(character) < 32 and character not in {"\t", "\n"} for character in text):
        raise HoldingSettingsWorkflowError(f"{field_name} contains control characters")
    return text


def _validated_as_of(value: Any) -> str:
    text = _validated_text(value, "as_of", maximum=40)
    clean = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        datetime.fromisoformat(clean)
    except ValueError:
        try:
            date.fromisoformat(clean)
        except ValueError as exc:
            raise HoldingSettingsWorkflowError("as_of must be an ISO date or datetime") from exc
    return text


def _hash_json(payload: Any) -> str:
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def _json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
