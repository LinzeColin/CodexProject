#!/usr/bin/env python3
"""Resolve S06-P2 candidates under an explicit private user authorization.

The resolver is deliberately narrow: eight project PDFs are reconciled from
their own top-level figures; the unmatched cross-source workbook is rejected.
No private value is emitted to stdout or the tracked tree.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from KMFA.tools import v015_s06_p2_golden_baseline_lock as kernel


POLICY_VERSION = "S06P2_AUTHORIZED_RESOLUTION_V1"
EXPECTED_SOURCE_REFS = {f"S06P1-SRC-{value:03d}" for value in range(1, 10)}
WORKBOOK_SOURCE_REF = "S06P1-SRC-008"
PDF_SOURCE_REFS = EXPECTED_SOURCE_REFS - {WORKBOOK_SOURCE_REF}

CATEGORY_RULES = (
    ("原材料", "MATERIAL", "原材料成本"),
    ("租赁费", "RENTAL", "租赁成本"),
    ("保险费", "INSURANCE", "保险成本"),
    ("现场管理费", "SITE_MANAGEMENT", "现场管理成本"),
    ("工资", "LABOR", "人工及承包成本"),
    ("信息费", "INFORMATION_FEE", "信息费成本"),
    ("税金", "TAX", "税金成本"),
    ("资金利息", "CAPITAL_INTEREST", "资金占用成本"),
    ("管理费用", "MANAGEMENT_ALLOCATION", "管理费用分摊"),
)


class ResolutionError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ResolutionError(message)


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON object required: {path.name}")
    return value


def _number_groups(token: str) -> list[str]:
    return re.findall(r"\d+", token.replace(",", "").replace("，", ""))


def _cents_from_groups(groups: list[str], negative: bool = False) -> int:
    _require(len(groups) >= 2 and len(groups[-1]) == 2, "spaced money token has no cent group")
    cents = int("".join(groups[:-1]) or "0") * 100 + int(groups[-1])
    return -cents if negative else cents


def _standard_cents(token: str) -> int:
    normalized = token.strip().replace(",", "").replace("，", "")
    _require("%" not in normalized, "percentage is not a money token")
    if " " in normalized:
        return _cents_from_groups(_number_groups(normalized), normalized.startswith("-"))
    value = Decimal(normalized)
    cents = value * Decimal(100)
    _require(cents == cents.to_integral_value(), "money has sub-cent precision")
    return int(cents)


def money_cents(candidate: dict[str, Any]) -> int:
    """Parse the authoritative money display while preserving integer cents."""

    raw_text = str(candidate.get("raw_text") or "")
    for original in candidate.get("original_display_tokens") or []:
        token = str(original).strip()
        if not token or re.fullmatch(r"1\.[12]", token) or token == "2%":
            continue
        if token.endswith("%"):
            groups = _number_groups(token)
            if " " in token and len(groups) >= 4:
                return _cents_from_groups(groups[:-2], token.startswith("-"))
            if len(groups) == 2 and all(int(value) == 0 for value in groups):
                return 0
            continue
        if "合同的2" in raw_text and token.startswith("2 "):
            token = token[2:].strip()
        return _standard_cents(token)
    if candidate.get("field_family") == "COST_CATEGORY":
        return 0
    raise ResolutionError("authoritative money token is unavailable")


def margin_basis_points(candidate: dict[str, Any]) -> int:
    for original in reversed(candidate.get("original_display_tokens") or []):
        token = str(original).strip()
        if not token.endswith("%") or token == "2%":
            continue
        normalized = token[:-1].strip().replace(",", "").replace("，", "")
        if " " in normalized:
            groups = _number_groups(normalized)
            _require(len(groups) >= 2 and len(groups[-1]) == 2, "margin token is invalid")
            value = int(groups[-2]) * 100 + int(groups[-1])
            return -value if normalized.startswith("-") else value
        basis_points = Decimal(normalized) * Decimal(100)
        _require(basis_points == basis_points.to_integral_value(), "margin has sub-basis-point precision")
        return int(basis_points)
    raise ResolutionError("authoritative margin token is unavailable")


def project_identity(candidate: dict[str, Any]) -> str:
    raw_text = str(candidate.get("raw_text") or "").strip()
    value = re.sub(r"^项目名称[：:]\s*", "", raw_text).strip()
    _require(bool(value), "project identity is unavailable")
    return value


def category_definition(candidate: dict[str, Any]) -> tuple[str, str]:
    raw_text = str(candidate.get("raw_text") or "")
    matches = [(key, meaning) for marker, key, meaning in CATEGORY_RULES if marker in raw_text]
    _require(len(matches) == 1, "cost category is ambiguous or unsupported")
    return matches[0]


def _reject(candidate: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"], "decision": "REJECT",
        "project_ref": None, "canonical_value": None, "unit": None,
        "tax_status": None, "business_meaning": None,
        "confirmed_source_locator": None, "category_key": None,
        "rejection_reason": reason,
    }


def _accept(
    candidate: dict[str, Any], project_ref: str, value: str | int,
    meaning: str, category_key: str | None = None,
) -> dict[str, Any]:
    family = candidate["field_family"]
    return {
        "candidate_id": candidate["candidate_id"], "decision": "ACCEPT",
        "project_ref": project_ref, "canonical_value": value,
        "unit": kernel.EXPECTED_UNITS[family],
        "tax_status": (
            "NOT_APPLICABLE" if family in {"PROJECT_IDENTITY", "GROSS_MARGIN"}
            else "SOURCE_NOT_STATED"
        ),
        "business_meaning": meaning,
        "confirmed_source_locator": candidate["source_locator"],
        "category_key": category_key, "rejection_reason": None,
    }


def build_decisions(packet: dict[str, Any]) -> list[dict[str, Any]]:
    kernel.validate_candidate_packet(packet)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in packet["candidate_records"]:
        grouped[candidate["source_ref"]].append(candidate)
    _require(set(grouped) == EXPECTED_SOURCE_REFS, "source set differs from authorized resolution scope")
    _require(packet["candidate_count"] == 157, "candidate set differs from reviewed packet")

    decisions = {
        candidate["candidate_id"]: _reject(candidate, "未选为本项目权威字段")
        for candidate in packet["candidate_records"]
    }
    for candidate in grouped[WORKBOOK_SOURCE_REF]:
        decisions[candidate["candidate_id"]] = _reject(
            candidate, "跨来源表格无法与八个项目精确绑定，禁止猜测归属",
        )

    for source_ref in sorted(PDF_SOURCE_REFS):
        rows = grouped[source_ref]
        by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_family[row["field_family"]].append(row)

        identity = [row for row in by_family["PROJECT_IDENTITY"] if row.get("identity_component") == "PROJECT_NAME"]
        contract = by_family["CONTRACT_AMOUNT"]
        totals = by_family["TOTAL_EXPENDITURE"]
        costs = by_family["COST_CATEGORY"]
        _require(len(identity) == 1 and len(contract) == 1, f"{source_ref} identity/contract cardinality mismatch")
        _require(len(costs) == 8, f"{source_ref} cost-category cardinality mismatch")
        primary_totals = [row for row in totals if row.get("candidate_role") == "PRIMARY_FIELD"]
        chosen_total = primary_totals[0] if primary_totals else totals[0]
        _require(len(primary_totals) <= 1 and chosen_total is not None, f"{source_ref} total selection mismatch")

        decisions[identity[0]["candidate_id"]] = _accept(
            identity[0], source_ref, project_identity(identity[0]), "项目名称",
        )
        decisions[contract[0]["candidate_id"]] = _accept(
            contract[0], source_ref, money_cents(contract[0]), "合同收入金额",
        )
        decisions[chosen_total["candidate_id"]] = _accept(
            chosen_total, source_ref, money_cents(chosen_total), "项目总成本",
        )

        seen_categories: set[str] = set()
        category_total = 0
        for cost in costs:
            category_key, meaning = category_definition(cost)
            _require(category_key not in seen_categories, f"{source_ref} duplicate cost category")
            seen_categories.add(category_key)
            value = money_cents(cost)
            category_total += value
            decisions[cost["candidate_id"]] = _accept(
                cost, source_ref, value, meaning, category_key,
            )
        total_cents = money_cents(chosen_total)
        _require(category_total == total_cents, f"{source_ref} category sum differs from total")
        revenue_cents = money_cents(contract[0])
        _require(revenue_cents != 0, f"{source_ref} contract amount cannot be zero")
        derived_profit = revenue_cents - total_cents
        derived_margin = int(
            (Decimal(derived_profit) * Decimal(10000) / Decimal(revenue_cents)).quantize(Decimal("1"))
        )

        for profit in by_family["GROSS_PROFIT"]:
            if money_cents(profit) == derived_profit:
                decisions[profit["candidate_id"]] = _accept(
                    profit, source_ref, derived_profit, "项目毛利润",
                )
            else:
                decisions[profit["candidate_id"]] = _reject(
                    profit, "原资料毛利与已核对合同额及总成本不一致，改由两者精确重算",
                )
        for margin in by_family["GROSS_MARGIN"]:
            if margin_basis_points(margin) == derived_margin:
                decisions[margin["candidate_id"]] = _accept(
                    margin, source_ref, derived_margin, "项目毛利率",
                )
            else:
                decisions[margin["candidate_id"]] = _reject(
                    margin, "原资料毛利率与已核对合同额及总成本不一致，改由两者精确重算",
                )

    result = [decisions[row["candidate_id"]] for row in packet["candidate_records"]]
    _require(all(row["decision"] in {"ACCEPT", "REJECT"} for row in result), "unresolved decision remains")
    return result


def build_authorization(user_message: str, source_thread_id: str, received_at: str) -> dict[str, Any]:
    body = {
        "schema_version": kernel.PRIVATE_AUTHORIZATION_SCHEMA,
        "project_id": "KMFA", "target_release": "v1.5", "phase_id": kernel.RUN_PHASE_ID,
        "authorizer_type": "USER", "source_thread_id": source_thread_id,
        "user_message": user_message, "received_at": received_at,
        "decision_authority_granted": True,
        "scope": "核对并锁定S06-P2八个项目财务基准；冲突数据不得猜测",
    }
    return {**body, "record_digest": kernel._sha256(body)}


def build_signoff(
    packet: dict[str, Any], authorization: dict[str, Any], confirmed_at: str,
) -> dict[str, Any]:
    digest = kernel.validate_authorization_record(authorization)
    signoff = kernel.build_signoff_template(packet)
    signoff.update({
        "confirmer": {
            "identity": kernel.AUTHORIZED_AGENT_IDENTITY,
            "role": kernel.AUTHORIZED_AGENT_ROLE,
            "confirmed_at": confirmed_at,
            "basis": f"{POLICY_VERSION};AUTHORIZATION_RECORD_DIGEST={digest}",
        },
        "authorization_statement": kernel.AUTHORIZATION_STATEMENT,
        "decision_rows": build_decisions(packet),
    })
    return signoff


def _write_new_private(path: Path, value: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(path, 0o600)


def resolve(
    user_message: str, source_thread_id: str, received_at: str, *, apply: bool,
) -> dict[str, Any]:
    packet = _json(kernel.PRIVATE_PACKET_PATH)
    authorization = build_authorization(user_message, source_thread_id, received_at)
    signoff = build_signoff(packet, authorization, received_at)
    accepted = [row for row in signoff["decision_rows"] if row["decision"] == "ACCEPT"]
    summaries = kernel.build_project_summaries([
        {
            **row,
            "source_ref": next(
                candidate["source_ref"] for candidate in packet["candidate_records"]
                if candidate["candidate_id"] == row["candidate_id"]
            ),
            "source_locator": row["confirmed_source_locator"],
            "field_family": next(
                candidate["field_family"] for candidate in packet["candidate_records"]
                if candidate["candidate_id"] == row["candidate_id"]
            ),
        }
        for row in accepted
    ])
    summary = {
        "candidate_count": packet["candidate_count"],
        "accepted_field_count": len(accepted),
        "rejected_candidate_count": len(signoff["decision_rows"]) - len(accepted),
        "project_summary_count": len(summaries),
        "money_difference_cents": sum(row["money_difference_cents"] for row in summaries),
        "decision_counts": dict(Counter(row["decision"] for row in signoff["decision_rows"])),
        "applied": apply,
    }
    if apply:
        _require(not kernel.PRIVATE_AUTHORIZATION_PATH.exists(), "authorization record already exists")
        _require(not kernel.PRIVATE_SIGNOFF_PATH.exists(), "final signoff already exists")
        _require(not kernel.PRIVATE_VERSION_LEDGER_PATH.exists(), "golden ledger already exists")
        kernel.PRIVATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(kernel.PRIVATE_OUTPUT_DIR, 0o700)
        _write_new_private(kernel.PRIVATE_AUTHORIZATION_PATH, authorization)
        _write_new_private(kernel.PRIVATE_SIGNOFF_PATH, signoff)
        kernel.append_version(signoff, packet)
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S06-P2 authorized project reconciliation")
    parser.add_argument("--user-message", required=True)
    parser.add_argument("--source-thread-id", required=True)
    parser.add_argument("--received-at", default=datetime.now().astimezone().isoformat())
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = resolve(
        args.user_message, args.source_thread_id, args.received_at, apply=args.apply,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
