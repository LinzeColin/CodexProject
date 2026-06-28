from __future__ import annotations

import html
import csv
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Mapping, Sequence


STAGE6_TAG_TABLES = (
    "pfi_tags",
    "pfi_tag_assignments",
    "pfi_tag_rules",
    "pfi_tag_history",
    "pfi_custom_views",
)

STAGE6_DEFAULT_TAG_GROUPS = ("通用", "消费", "投资", "数据质量", "现金流", "复盘")

STAGE6_TAG_RULE_DIMENSIONS = ("amount_cny", "time_window", "l1_category", "event_type", "account_role")
STAGE6_ALIPAY_TRANSACTION_SOURCE = "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv"


@dataclass(frozen=True)
class Stage6TagDefinition:
    tag_id: str
    label_zh: str
    scope: str
    tag_type: str
    group_zh: str
    is_system_default: bool
    is_editable: bool
    is_enabled: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Stage6TagRule:
    rule_id: str
    tag_id: str
    label_zh: str
    conditions: Mapping[str, object]
    is_enabled: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _default_tag(tag_id: str, label_zh: str, group_zh: str, scope: str = "transaction") -> Stage6TagDefinition:
    return Stage6TagDefinition(
        tag_id=tag_id,
        label_zh=label_zh,
        scope=scope,
        tag_type="default",
        group_zh=group_zh,
        is_system_default=True,
        is_editable=False,
    )


def build_stage6_default_tag_library() -> tuple[dict[str, object], ...]:
    tags = (
        _default_tag("tag_general_planned", "计划内", "通用"),
        _default_tag("tag_general_unplanned", "计划外", "通用"),
        _default_tag("tag_general_recurring", "周期性", "通用"),
        _default_tag("tag_general_one_off", "一次性", "通用"),
        _default_tag("tag_general_reimbursable", "可报销", "通用"),
        _default_tag("tag_general_work_related", "工作相关", "通用"),
        _default_tag("tag_general_family_related", "家庭相关", "通用"),
        _default_tag("tag_general_tax_related", "税务相关", "通用"),
        _default_tag("tag_general_cash_related", "现金相关", "通用"),
        _default_tag("tag_general_manual_reviewed", "人工已复核", "通用"),
        _default_tag("tag_consumption_night", "夜间消费", "消费"),
        _default_tag("tag_consumption_large", "大额消费", "消费"),
        _default_tag("tag_consumption_duplicate_suspect", "疑似重复", "消费"),
        _default_tag("tag_consumption_refund_linked", "已关联退款", "消费"),
        _default_tag("tag_consumption_subscription", "订阅扣费", "消费"),
        _default_tag("tag_consumption_fixed", "固定支出", "消费"),
        _default_tag("tag_consumption_flexible", "弹性支出", "消费"),
        _default_tag("tag_consumption_weekend", "周末消费", "消费"),
        _default_tag("tag_consumption_social", "社交消费", "消费"),
        _default_tag("tag_consumption_impulse_candidate", "冲动候选", "消费"),
        _default_tag("tag_investment_deposit", "投资入金", "投资"),
        _default_tag("tag_investment_return", "投资回流", "投资"),
        _default_tag("tag_investment_buy", "买入交易", "投资"),
        _default_tag("tag_investment_sell", "卖出交易", "投资"),
        _default_tag("tag_investment_fund_subscription", "基金申购", "投资"),
        _default_tag("tag_investment_bullion_subscription", "黄金申购", "投资"),
        _default_tag("tag_investment_dividend", "分红收入", "投资"),
        _default_tag("tag_investment_fee", "投资费用", "投资"),
        _default_tag("tag_investment_fx_exposure", "汇率暴露", "投资"),
        _default_tag("tag_investment_chase_candidate", "追涨候选", "投资"),
        _default_tag("tag_investment_panic_sell_candidate", "杀跌候选", "投资"),
        _default_tag("tag_investment_short_hold_candidate", "短持候选", "投资"),
        _default_tag("tag_investment_idle_cash_candidate", "闲置现金候选", "投资"),
        _default_tag("tag_investment_concentration_exposure", "集中度暴露", "投资", "holding"),
        _default_tag("tag_quality_low_confidence", "低置信", "数据质量"),
        _default_tag("tag_quality_unmatched_transfer", "未匹配转账", "数据质量"),
        _default_tag("tag_quality_matched_linked", "已匹配关联", "数据质量"),
        _default_tag("tag_quality_fx_snapshot_stale", "汇率快照过期", "数据质量"),
        _default_tag("tag_quality_missing_counterparty", "缺少对手方", "数据质量"),
        _default_tag("tag_quality_blurry_description", "描述模糊", "数据质量"),
        _default_tag("tag_quality_duplicate_raw", "重复原始记录", "数据质量"),
        _default_tag("tag_quality_parser_warning", "解析器警告", "数据质量"),
        _default_tag("tag_quality_category_user_modified", "分类被用户修改", "数据质量"),
        _default_tag("tag_quality_tag_user_modified", "标签被用户修改", "数据质量"),
        _default_tag("tag_cashflow_pressure", "现金流压力", "现金流"),
        _default_tag("tag_cashflow_safe", "现金流安全", "现金流"),
        _default_tag("tag_cashflow_investment_pressure", "投资挤压现金", "现金流"),
        _default_tag("tag_cashflow_income_related", "收入相关", "现金流"),
        _default_tag("tag_cashflow_refund_inflow", "退款回流", "现金流"),
        _default_tag("tag_cashflow_reserve_watch", "储备金观察", "现金流"),
        _default_tag("tag_review_needs_review", "需要复核", "复盘"),
        _default_tag("tag_review_action_candidate", "行动候选", "复盘"),
        _default_tag("tag_review_behavior_pattern", "行为模式", "复盘"),
        _default_tag("tag_review_monthly_focus", "本月重点", "复盘"),
        _default_tag("tag_review_resolved", "已处理", "复盘"),
        _default_tag("tag_review_follow_up", "后续跟踪", "复盘"),
    )
    return tuple(tag.to_dict() for tag in tags)


def build_stage6_tag_rules() -> tuple[dict[str, object], ...]:
    rules = (
        Stage6TagRule(
            "rule_large_consumption_cny",
            "tag_consumption_large",
            "CNY 大额消费",
            {"amount_cny_gte": "2000", "event_types": ("consumption", "ordinary_consumption")},
        ),
        Stage6TagRule(
            "rule_night_consumption",
            "tag_consumption_night",
            "夜间消费窗口",
            {"time_window": "22:00-06:00", "event_types": ("consumption", "ordinary_consumption")},
        ),
        Stage6TagRule(
            "rule_subscription_category",
            "tag_consumption_subscription",
            "订阅服务分类",
            {"l1_categories": ("订阅服务",), "event_types": ("consumption", "ordinary_consumption")},
        ),
        Stage6TagRule(
            "rule_investment_deposit_event",
            "tag_investment_deposit",
            "投资入金事件",
            {"event_types": ("investment_deposit",)},
        ),
        Stage6TagRule(
            "rule_investment_buy_event",
            "tag_investment_buy",
            "投资买入事件",
            {"event_types": ("investment_buy",)},
        ),
        Stage6TagRule(
            "rule_investment_funding_role",
            "tag_cashflow_investment_pressure",
            "投资入金来源账户",
            {"account_roles": ("investment_funding_source",)},
        ),
    )
    return tuple(rule.to_dict() for rule in rules)


def load_stage6_alipay_records_from_metadatabase(
    metadatabase_root: str | Path | None = None,
    *,
    limit: int | None = None,
) -> list[dict[str, object]]:
    root = Path(metadatabase_root) if metadatabase_root is not None else _default_stage6_alipay_metadatabase_root()
    transactions_path = root / "processed" / "alipay_transactions.csv"
    if not transactions_path.exists():
        return []

    records: list[dict[str, object]] = []
    with transactions_path.open(encoding="utf-8-sig", newline="") as file_obj:
        for row in csv.DictReader(file_obj):
            record = _stage6_record_from_alipay_row(row)
            if record is None:
                continue
            records.append(record)
            if limit is not None and len(records) >= limit:
                break
    return records


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_bool(value: object) -> bool:
    return bool(int(value)) if isinstance(value, int) else bool(value)


def _json_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_loads(value: str | None, default: object) -> object:
    return default if not value else json.loads(value)


def _row_to_tag(row: sqlite3.Row) -> dict[str, object]:
    return {
        "tag_id": row["tag_id"],
        "label_zh": row["label_zh"],
        "scope": row["scope"],
        "tag_type": row["tag_type"],
        "group_zh": row["group_zh"],
        "is_system_default": _as_bool(row["is_system_default"]),
        "is_editable": _as_bool(row["is_editable"]),
        "is_enabled": _as_bool(row["is_enabled"]),
        "deleted_at": row["deleted_at"],
    }


class Stage6TagViewStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS pfi_tags (
                    tag_id TEXT PRIMARY KEY,
                    label_zh TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    tag_type TEXT NOT NULL CHECK (tag_type IN ('default', 'custom')),
                    group_zh TEXT NOT NULL,
                    is_system_default INTEGER NOT NULL CHECK (is_system_default IN (0, 1)),
                    is_editable INTEGER NOT NULL CHECK (is_editable IN (0, 1)),
                    is_enabled INTEGER NOT NULL CHECK (is_enabled IN (0, 1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    deleted_at TEXT
                );
                CREATE TABLE IF NOT EXISTS pfi_tag_assignments (
                    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    tag_id TEXT NOT NULL,
                    assigned_by TEXT NOT NULL,
                    assigned_at TEXT NOT NULL,
                    FOREIGN KEY(tag_id) REFERENCES pfi_tags(tag_id),
                    UNIQUE(target_type, target_id, tag_id)
                );
                CREATE TABLE IF NOT EXISTS pfi_tag_rules (
                    rule_id TEXT PRIMARY KEY,
                    tag_id TEXT NOT NULL,
                    label_zh TEXT NOT NULL,
                    conditions_json TEXT NOT NULL,
                    is_enabled INTEGER NOT NULL CHECK (is_enabled IN (0, 1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(tag_id) REFERENCES pfi_tags(tag_id)
                );
                CREATE TABLE IF NOT EXISTS pfi_tag_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    impact_object TEXT,
                    reason_zh TEXT,
                    changed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pfi_custom_views (
                    view_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_zh TEXT NOT NULL,
                    required_tag_ids_json TEXT NOT NULL,
                    description_zh TEXT NOT NULL,
                    target_route TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def seed_default_tags(self) -> None:
        now = _now()
        with self._connect() as conn:
            for tag in build_stage6_default_tag_library():
                conn.execute(
                    """
                    INSERT INTO pfi_tags (
                        tag_id, label_zh, scope, tag_type, group_zh,
                        is_system_default, is_editable, is_enabled,
                        created_at, updated_at, deleted_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    ON CONFLICT(tag_id) DO UPDATE SET
                        label_zh=excluded.label_zh,
                        scope=excluded.scope,
                        group_zh=excluded.group_zh,
                        is_enabled=excluded.is_enabled,
                        updated_at=excluded.updated_at
                    """,
                    (
                        tag["tag_id"],
                        tag["label_zh"],
                        tag["scope"],
                        tag["tag_type"],
                        tag["group_zh"],
                        int(bool(tag["is_system_default"])),
                        int(bool(tag["is_editable"])),
                        int(bool(tag["is_enabled"])),
                        now,
                        now,
                    ),
                )
            for rule in build_stage6_tag_rules():
                conn.execute(
                    """
                    INSERT INTO pfi_tag_rules (
                        rule_id, tag_id, label_zh, conditions_json,
                        is_enabled, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(rule_id) DO UPDATE SET
                        tag_id=excluded.tag_id,
                        label_zh=excluded.label_zh,
                        conditions_json=excluded.conditions_json,
                        is_enabled=excluded.is_enabled,
                        updated_at=excluded.updated_at
                    """,
                    (
                        rule["rule_id"],
                        rule["tag_id"],
                        rule["label_zh"],
                        _json_dumps(rule["conditions"]),
                        int(bool(rule["is_enabled"])),
                        now,
                        now,
                    ),
                )

    def list_tags(self, include_disabled: bool = False) -> list[dict[str, object]]:
        where = "" if include_disabled else "WHERE is_enabled=1 AND deleted_at IS NULL"
        with self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM pfi_tags {where} ORDER BY tag_id").fetchall()
        return [_row_to_tag(row) for row in rows]

    def _get_tag(self, conn: sqlite3.Connection, tag_id: str) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM pfi_tags WHERE tag_id=?", (tag_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown tag_id: {tag_id}")
        return row

    def _record_history(
        self,
        conn: sqlite3.Connection,
        tag_id: str,
        action: str,
        old_value: object | None,
        new_value: object | None,
        impact_object: str,
        reason_zh: str = "",
    ) -> None:
        conn.execute(
            """
            INSERT INTO pfi_tag_history (
                tag_id, action, old_value, new_value, impact_object, reason_zh, changed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tag_id,
                action,
                _json_dumps(old_value) if old_value is not None else None,
                _json_dumps(new_value) if new_value is not None else None,
                impact_object,
                reason_zh,
                _now(),
            ),
        )

    def create_custom_tag(self, label_zh: str, scope: str, tag_type: str = "custom", group_zh: str = "自定义") -> dict[str, object]:
        if tag_type != "custom":
            raise ValueError("Stage 6 only lets users create custom tags")
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM pfi_tags WHERE tag_type='custom'").fetchone()[0]
            tag_id = f"custom_tag_{count + 1:03d}"
            now = _now()
            payload = {
                "tag_id": tag_id,
                "label_zh": label_zh,
                "scope": scope,
                "tag_type": "custom",
                "group_zh": group_zh,
                "is_system_default": False,
                "is_editable": True,
                "is_enabled": True,
            }
            conn.execute(
                """
                INSERT INTO pfi_tags (
                    tag_id, label_zh, scope, tag_type, group_zh,
                    is_system_default, is_editable, is_enabled,
                    created_at, updated_at, deleted_at
                )
                VALUES (?, ?, ?, ?, ?, 0, 1, 1, ?, ?, NULL)
                """,
                (tag_id, label_zh, scope, tag_type, group_zh, now, now),
            )
            self._record_history(conn, tag_id, "create", None, payload, "pfi_tags")
        return payload

    def rename_tag(self, tag_id: str, new_label_zh: str) -> dict[str, object]:
        with self._connect() as conn:
            row = self._get_tag(conn, tag_id)
            if not _as_bool(row["is_editable"]):
                raise ValueError("Only editable custom tags can be renamed")
            old = _row_to_tag(row)
            now = _now()
            conn.execute("UPDATE pfi_tags SET label_zh=?, updated_at=? WHERE tag_id=?", (new_label_zh, now, tag_id))
            new = dict(old)
            new["label_zh"] = new_label_zh
            self._record_history(conn, tag_id, "rename", old, new, "pfi_tags")
        return new

    def disable_tag(self, tag_id: str, reason_zh: str = "") -> dict[str, object]:
        with self._connect() as conn:
            row = self._get_tag(conn, tag_id)
            if not _as_bool(row["is_editable"]):
                raise ValueError("Only editable custom tags can be disabled by user action")
            old = _row_to_tag(row)
            now = _now()
            conn.execute("UPDATE pfi_tags SET is_enabled=0, updated_at=? WHERE tag_id=?", (now, tag_id))
            new = dict(old)
            new["is_enabled"] = False
            self._record_history(conn, tag_id, "disable", old, new, "pfi_tags", reason_zh)
        return new

    def delete_custom_tag(self, tag_id: str, reason_zh: str = "") -> dict[str, object]:
        with self._connect() as conn:
            row = self._get_tag(conn, tag_id)
            if _as_bool(row["is_system_default"]) or row["tag_type"] != "custom":
                raise ValueError("System default tags cannot be physically deleted")
            old = _row_to_tag(row)
            deleted_at = _now()
            conn.execute(
                "UPDATE pfi_tags SET is_enabled=0, deleted_at=?, updated_at=? WHERE tag_id=?",
                (deleted_at, deleted_at, tag_id),
            )
            new = dict(old)
            new["is_enabled"] = False
            new["deleted_at"] = deleted_at
            self._record_history(conn, tag_id, "delete", old, new, "pfi_tags", reason_zh)
        return new

    def assign_tags(
        self,
        target_type: str,
        target_id: str,
        tag_ids: Sequence[str],
        assigned_by: str = "system",
    ) -> list[dict[str, object]]:
        assigned_at = _now()
        rows: list[dict[str, object]] = []
        with self._connect() as conn:
            for tag_id in tag_ids:
                self._get_tag(conn, tag_id)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO pfi_tag_assignments (
                        target_type, target_id, tag_id, assigned_by, assigned_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (target_type, target_id, tag_id, assigned_by, assigned_at),
                )
                rows.append({"target_type": target_type, "target_id": target_id, "tag_id": tag_id})
        return rows

    def get_assignments(self, target_type: str, target_id: str) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.target_type, a.target_id, a.tag_id, a.assigned_by, a.assigned_at, t.label_zh
                FROM pfi_tag_assignments a
                JOIN pfi_tags t ON t.tag_id=a.tag_id
                WHERE a.target_type=? AND a.target_id=?
                ORDER BY a.tag_id
                """,
                (target_type, target_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_tag_history(self, tag_id: str) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM pfi_tag_history WHERE tag_id=? ORDER BY history_id",
                (tag_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _enabled_rules(self) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM pfi_tag_rules WHERE is_enabled=1 ORDER BY rule_id").fetchall()
        return [
            {
                "rule_id": row["rule_id"],
                "tag_id": row["tag_id"],
                "label_zh": row["label_zh"],
                "conditions": _json_loads(row["conditions_json"], {}),
            }
            for row in rows
        ]

    def apply_tag_rules(self, records: Iterable[Mapping[str, object]]) -> dict[str, tuple[str, ...]]:
        applied: dict[str, tuple[str, ...]] = {}
        for record in records:
            record_id = str(record["record_id"])
            tag_ids = tuple(rule["tag_id"] for rule in self._enabled_rules() if _record_matches_conditions(record, rule["conditions"]))
            if tag_ids:
                self.assign_tags("transaction", record_id, tag_ids, assigned_by="tag_rule")
            applied[record_id] = tag_ids
        return applied

    def filter_ledger_by_tags(
        self,
        records: Iterable[Mapping[str, object]],
        required_tag_ids: Sequence[str],
        match: str = "all",
    ) -> list[Mapping[str, object]]:
        required = set(required_tag_ids)
        result: list[Mapping[str, object]] = []
        for record in records:
            record_id = str(record["record_id"])
            assigned = {item["tag_id"] for item in self.get_assignments("transaction", record_id)}
            matched = required.issubset(assigned) if match == "all" else bool(required & assigned)
            if matched:
                result.append(record)
        return result

    def build_tag_report(self, records: Iterable[Mapping[str, object]]) -> dict[str, object]:
        by_record = {str(record["record_id"]): record for record in records}
        by_tag: dict[str, dict[str, object]] = {}
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.target_id, a.tag_id, t.label_zh, t.group_zh
                FROM pfi_tag_assignments a
                JOIN pfi_tags t ON t.tag_id=a.tag_id
                WHERE a.target_type='transaction'
                ORDER BY a.tag_id, a.target_id
                """
            ).fetchall()
        for row in rows:
            record = by_record.get(row["target_id"])
            if record is None:
                continue
            amount = _decimal(record.get("amount_cny", 0))
            bucket = by_tag.setdefault(
                row["tag_id"],
                {"tag_id": row["tag_id"], "label_zh": row["label_zh"], "group_zh": row["group_zh"], "record_count": 0, "amount_cny": Decimal("0")},
            )
            bucket["record_count"] = int(bucket["record_count"]) + 1
            bucket["amount_cny"] = _decimal(bucket["amount_cny"]) + amount
        return {
            "schema": "PFIV022Stage6TagDrivenReportV1",
            "currency": "CNY",
            "by_tag": by_tag,
            "report_surfaces": ("消费管理", "投资管理", "报告与洞察", "建议与复盘"),
        }

    def save_custom_view(
        self,
        name_zh: str,
        required_tag_ids: Sequence[str],
        description_zh: str,
        target_route: str = "#/ledger",
    ) -> dict[str, object]:
        now = _now()
        with self._connect() as conn:
            for tag_id in required_tag_ids:
                self._get_tag(conn, tag_id)
            cur = conn.execute(
                """
                INSERT INTO pfi_custom_views (
                    name_zh, required_tag_ids_json, description_zh, target_route, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name_zh, _json_dumps(tuple(required_tag_ids)), description_zh, target_route, now, now),
            )
            view_id = int(cur.lastrowid)
        return {
            "view_id": view_id,
            "name_zh": name_zh,
            "required_tag_ids": tuple(required_tag_ids),
            "description_zh": description_zh,
            "target_route": target_route,
        }

    def list_custom_views(self) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM pfi_custom_views ORDER BY view_id").fetchall()
        return [
            {
                "view_id": row["view_id"],
                "name_zh": row["name_zh"],
                "required_tag_ids": tuple(_json_loads(row["required_tag_ids_json"], [])),
                "description_zh": row["description_zh"],
                "target_route": row["target_route"],
            }
            for row in rows
        ]

    def render_custom_views_html(self) -> str:
        cards = []
        for view in self.list_custom_views():
            tags = " + ".join(html.escape(tag_id) for tag_id in view["required_tag_ids"])
            cards.append(
                "<article class=\"view-card\">"
                f"<h2>{html.escape(str(view['name_zh']))}</h2>"
                f"<p>{html.escape(str(view['description_zh']))}</p>"
                f"<p class=\"tags\">标签筛选：{tags}</p>"
                f"<a href=\"{html.escape(str(view['target_route']))}\">打开账本筛选</a>"
                "</article>"
            )
        return (
            "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
            "<title>Stage 6 - 标签系统与自定义视图</title></head><body>"
            "<main><h1>Stage 6 - 标签系统与自定义视图</h1>"
            "<p>本地 HTML 展示标签筛选和自定义视图，数据来自 pfi_custom_views 与 pfi_tag_assignments。</p>"
            f"{''.join(cards) or '<p>暂无自定义视图。</p>'}"
            "</main></body></html>"
        )


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _default_stage6_alipay_metadatabase_root() -> Path:
    return Path(__file__).resolve().parents[3] / "MetaDatabase" / "PFI" / "alipay_daily"


def _stage6_record_from_alipay_row(row: Mapping[str, object]) -> dict[str, object] | None:
    raw_event_type = str(row.get("event_type") or "").strip().upper()
    amount = _decimal(row.get("amount") or "0")
    stage6_event_type = _stage6_event_type(raw_event_type, amount)
    if not stage6_event_type:
        return None

    record_id = str(row.get("transaction_id") or "").strip()
    if not record_id:
        return None

    return {
        "record_id": record_id,
        "amount_cny": abs(amount),
        "local_time": _stage6_local_time(row.get("occurred_at")),
        "l1_category": _stage6_l1_category(row.get("description"), stage6_event_type),
        "event_type": stage6_event_type,
        "account_roles": _stage6_account_roles(stage6_event_type),
        "occurred_at": str(row.get("occurred_at") or "").strip(),
        "description": str(row.get("description") or "").strip(),
        "source_id": str(row.get("source_id") or "alipay_daily").strip(),
        "real_data_source": STAGE6_ALIPAY_TRANSACTION_SOURCE,
    }


def _stage6_event_type(raw_event_type: str, amount: Decimal) -> str:
    if raw_event_type == "CASH" and amount < 0:
        return "ordinary_consumption"
    if raw_event_type == "FUND" and amount < 0:
        return "investment_deposit"
    if raw_event_type == "FUND" and amount >= 0:
        return "investment_return"
    if raw_event_type == "BUY_ASSET":
        return "investment_buy"
    if raw_event_type == "REFUND":
        return "refund"
    return ""


def _stage6_local_time(value: object) -> str:
    text = str(value or "").strip()
    if "T" in text:
        time_part = text.split("T", 1)[1]
    elif " " in text:
        time_part = text.split(" ", 1)[1]
    else:
        return "12:00"
    chunks = time_part.split(":", 2)
    return ":".join(chunks[:2]) if len(chunks) >= 2 else "12:00"


def _stage6_l1_category(description: object, event_type: str) -> str:
    text = str(description or "")
    if "订阅" in text or "会员" in text:
        return "订阅服务"
    if event_type.startswith("investment_"):
        return "投资资金流出"
    if event_type == "refund":
        return "退款"
    return "真实支付宝流水"


def _stage6_account_roles(event_type: str) -> tuple[str, ...]:
    if event_type in {"investment_deposit", "investment_buy"}:
        return ("investment_funding_source",)
    return ("consumer_wallet",)


def _record_matches_conditions(record: Mapping[str, object], conditions: Mapping[str, object]) -> bool:
    if "amount_cny_gte" in conditions and _decimal(record.get("amount_cny", 0)) < _decimal(conditions["amount_cny_gte"]):
        return False
    if "time_window" in conditions and not _time_in_window(str(record.get("local_time", "")), str(conditions["time_window"])):
        return False
    if "l1_categories" in conditions and str(record.get("l1_category", "")) not in set(conditions["l1_categories"]):
        return False
    if "event_types" in conditions and str(record.get("event_type", "")) not in set(conditions["event_types"]):
        return False
    if "account_roles" in conditions:
        roles = set(record.get("account_roles", ()) or ())
        if not roles & set(conditions["account_roles"]):
            return False
    return True


def _minutes(hhmm: str) -> int | None:
    try:
        hour, minute = hhmm.split(":", 1)
        return int(hour) * 60 + int(minute)
    except Exception:
        return None


def _time_in_window(local_time: str, window: str) -> bool:
    current = _minutes(local_time)
    if current is None:
        return False
    start_s, end_s = window.split("-", 1)
    start = _minutes(start_s)
    end = _minutes(end_s)
    if start is None or end is None:
        return False
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def build_stage6_contract_payload() -> dict[str, object]:
    return {
        "tag_tables": STAGE6_TAG_TABLES,
        "default_tag_groups": STAGE6_DEFAULT_TAG_GROUPS,
        "default_tag_library": build_stage6_default_tag_library(),
        "tag_rules": build_stage6_tag_rules(),
        "tag_rule_dimensions": STAGE6_TAG_RULE_DIMENSIONS,
        "custom_view_surfaces": ("账本流水", "报告与洞察", "本地 HTML"),
        "persistence": "SQLite operational DB or local equivalent store",
    }
