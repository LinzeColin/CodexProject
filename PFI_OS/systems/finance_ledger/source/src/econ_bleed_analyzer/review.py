from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .classifier import ClassifiedTransaction


INCLUDE_VALUES = {"include", "included", "yes", "y", "true", "1", "纳入", "计入", "确认", "已确认"}
EXCLUDE_VALUES = {"exclude", "excluded", "no", "n", "false", "0", "剔除", "排除", "不计入"}


@dataclass(frozen=True)
class ManualAllocation:
    main_category: str
    sub_category: str
    risk_tags: list[str]
    amount_cents: int | None = None
    pct: float | None = None
    note: str = ""


@dataclass
class ReviewDecisions:
    included: dict[str, list[ManualAllocation]] = field(default_factory=dict)
    excluded: set[str] = field(default_factory=set)
    source_path: str = ""
    invalid_rows: list[dict[str, Any]] = field(default_factory=list)

    def key_for(self, row: ClassifiedTransaction) -> str:
        return review_key(row)

    def has_decision(self, row: ClassifiedTransaction) -> bool:
        key = self.key_for(row)
        return key in self.included or key in self.excluded

    def is_excluded(self, row: ClassifiedTransaction) -> bool:
        return self.key_for(row) in self.excluded

    def allocations_for(self, row: ClassifiedTransaction) -> list[dict[str, Any]]:
        key = self.key_for(row)
        decisions = self.included.get(key, [])
        if not decisions:
            return []

        explicit_total = sum(item.amount_cents or 0 for item in decisions)
        pct_total = sum(item.pct or 0 for item in decisions if item.amount_cents is None)
        output: list[dict[str, Any]] = []
        allocated = 0
        for index, decision in enumerate(decisions):
            if decision.amount_cents is not None:
                amount = decision.amount_cents
            elif decision.pct is not None:
                amount = round(row.amount_cents * decision.pct / 100)
            elif len(decisions) == 1:
                amount = row.amount_cents
            elif pct_total > 0:
                amount = round(row.amount_cents * (decision.pct or 0) / 100)
            else:
                amount = 0

            if index == len(decisions) - 1 and explicit_total == 0 and pct_total in {0, 100}:
                amount = row.amount_cents - allocated
            allocated += amount
            output.append(
                {
                    "row": row,
                    "main_category": decision.main_category,
                    "sub_category": decision.sub_category,
                    "amount_cents": amount,
                    "risk_tags": decision.risk_tags or _row_risk_tags(row),
                    "review_decision": "manual_include",
                    "review_note": decision.note,
                }
            )
        return [item for item in output if item["amount_cents"] > 0]


def review_key(row: ClassifiedTransaction) -> str:
    if row.order_id:
        return row.order_id
    return f"{row.transaction_time}|{row.counterparty}|{row.amount_cents}|{row.description}"


def _value(raw: dict[str, str], *names: str) -> str:
    for name in names:
        if name in raw and raw[name] is not None:
            return str(raw[name]).strip()
    return ""


def _amount_to_cents(value: str) -> int | None:
    cleaned = value.strip().replace(",", "").replace("¥", "")
    if not cleaned:
        return None
    sign = -1 if cleaned.startswith("-") else 1
    cleaned = cleaned.lstrip("+-")
    if "." in cleaned:
        yuan, cents = cleaned.split(".", 1)
        cents = (cents + "00")[:2]
    else:
        yuan, cents = cleaned, "00"
    if not yuan:
        yuan = "0"
    return sign * (int(yuan) * 100 + int(cents))


def _pct(value: str) -> float | None:
    cleaned = value.strip().replace("%", "")
    if not cleaned:
        return None
    return float(cleaned)


def _tags(value: str) -> list[str]:
    return [item.strip() for item in value.replace("，", "|").replace(",", "|").split("|") if item.strip()]


def _row_risk_tags(row: ClassifiedTransaction) -> list[str]:
    return [item for item in row.risk_tags.split("|") if item] or ["基础支出"]


def load_review_decisions(path: str | Path | None) -> ReviewDecisions:
    decisions = ReviewDecisions(source_path=str(path or ""))
    if not path:
        return decisions
    source = Path(path).expanduser()
    decisions.source_path = str(source)
    if not source.exists():
        return decisions

    with source.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for line_number, raw in enumerate(reader, start=2):
            key = _value(raw, "review_key", "order_id", "交易订单号")
            status = _value(raw, "decision", "decision_status", "复核决定", "是否纳入").casefold()
            if not key or not status:
                continue
            if status in EXCLUDE_VALUES:
                decisions.excluded.add(key)
                continue
            if status not in INCLUDE_VALUES:
                decisions.invalid_rows.append({"line": line_number, "reason": "unknown_decision", "row": dict(raw)})
                continue

            main = _value(raw, "main_category", "allocation_main_category", "主类")
            sub = _value(raw, "sub_category", "allocation_sub_category", "子类")
            if not main or not sub:
                decisions.invalid_rows.append({"line": line_number, "reason": "missing_category", "row": dict(raw)})
                continue
            try:
                amount_cents = _amount_to_cents(_value(raw, "allocation_amount", "amount", "分摊金额"))
                pct = _pct(_value(raw, "allocation_pct", "pct", "分摊比例"))
            except ValueError as exc:
                decisions.invalid_rows.append({"line": line_number, "reason": f"invalid_number:{exc}", "row": dict(raw)})
                continue
            risk_tags = _tags(_value(raw, "risk_tags", "风险标签"))
            note = _value(raw, "note", "备注")
            decisions.included.setdefault(key, []).append(
                ManualAllocation(
                    main_category=main,
                    sub_category=sub,
                    risk_tags=risk_tags,
                    amount_cents=amount_cents,
                    pct=pct,
                    note=note,
                )
            )
    return decisions
