from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


PERIOD_TABLES = {
    "week": "summary_by_week",
    "month": "summary_by_month",
    "quarter": "summary_by_quarter",
    "half": "summary_by_half",
    "year": "summary_by_year",
}

QUESTION_TEMPLATES = [
    {
        "id": "latest_month_cashflow",
        "title": "最近月度现金流",
        "keywords": ["最近", "本月", "月度", "现金流", "收入", "支出"],
        "view": "summary_by_month",
        "description": "查看最近月份收入、支出、净现金流和待复核金额。",
    },
    {
        "id": "top_categories",
        "title": "钱主要花在哪些主类/子类",
        "keywords": ["分类", "主类", "子类", "花在哪", "占比", "最多"],
        "view": "summary_by_category",
        "description": "按金额查看主类和子类支出排行。",
    },
    {
        "id": "risk_exposure",
        "title": "风险标签暴露",
        "keywords": ["风险", "放血", "标签", "暴露", "长期扣费", "信用"],
        "view": "summary_by_risk_tag",
        "description": "按风险标签查看金额和支出占比。",
    },
    {
        "id": "pending_large_review",
        "title": "一万元以上待复核",
        "keywords": ["待复核", "大额", "一万", "10000", "确认", "候选"],
        "view": "manual_review_status_summary + manual_review_queue",
        "description": "查看大额复核闭环状态和待确认交易。",
    },
    {
        "id": "control_actions",
        "title": "降低消费建议",
        "keywords": ["建议", "降低", "控制", "优化", "省钱", "压缩"],
        "view": "spending_control_plan",
        "description": "查看按优先级生成的消费控制动作。",
    },
    {
        "id": "daily_cashflow",
        "title": "日度现金流",
        "keywords": ["日度", "每天", "每日", "哪天", "现金流"],
        "view": "v_mart_daily_cashflow",
        "description": "查看最近日度收入、支出、净现金流和待复核金额。",
    },
]


def connect_readonly(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path).expanduser().resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite 数据库不存在：{db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def query_months(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return _rows(conn, "select period, period_start, period_end from summary_by_month order by period_start")


def query_stats(conn: sqlite3.Connection, period: str, limit: int) -> list[dict[str, Any]]:
    table = PERIOD_TABLES[period]
    return _rows(
        conn,
        f"""
        select period, period_start, period_end, transactions, total_expense, total_income,
               net_cash_flow, total_transfer, pending_review, real_consumption,
               risk_spending, optimizable_spending, social_spending, financial_spending
        from {table}
        order by period_start desc
        limit ?
        """,
        (limit,),
    )


def query_categories(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select main_category, sub_category, amount, count, main_pct, sub_pct
        from summary_by_category
        order by cast(amount as real) desc
        limit ?
        """,
        (limit,),
    )


def query_risks(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select risk_tag, amount, count, expense_pct
        from summary_by_risk_tag
        order by cast(amount as real) desc
        limit ?
        """,
        (limit,),
    )


def query_control_plan(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select priority, focus_area, trigger_metric, current_amount, current_pct,
               recommended_action, suggested_cap, estimated_saving, review_needed
        from spending_control_plan
        order by priority, cast(estimated_saving as real) desc
        limit ?
        """,
        (limit,),
    )


def query_review(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select transaction_time, counterparty, description, amount, main_category,
               sub_category, risk_tags, order_id
        from manual_review_queue
        order by cast(amount_cents as real) desc
        limit ?
        """,
        (limit,),
    )


def query_review_status(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select status, status_label, count, amount, count_pct, amount_pct,
               production_effect, next_action
        from manual_review_status_summary
        order by status
        """,
    )


def query_review_candidates(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select review_key, candidate_action, candidate_label, candidate_confidence,
               candidate_reason, candidate_main_category, candidate_sub_category,
               candidate_risk_tags, amount, transaction_time, source_platform,
               counterparty, description, order_id
        from manual_review_decision_candidates
        order by cast(amount as real) desc
        limit ?
        """,
        (limit,),
    )


def query_review_candidate_groups(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select group_type, group_key, count, amount, include_candidate_count,
               manual_review_count, high_confidence_count, medium_confidence_count,
               low_confidence_count, top_reason
        from manual_review_decision_candidate_groups
        order by group_type, cast(amount as real) desc
        limit ?
        """,
        (limit,),
    )


def query_source_platforms(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select platform, transaction_count, source_file_count, production_expense,
               expense_pct, pending_review_count
        from source_platform_summary
        order by cast(production_expense as real) desc
        """,
    )


def query_daily_cashflow(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    return _rows(
        conn,
        """
        select date, month, year, total_expense, total_income, net_cash_flow,
               total_transfer, pending_review
        from v_mart_daily_cashflow
        order by date desc
        limit ?
        """,
        (limit,),
    )


def query_transactions(
    conn: sqlite3.Connection,
    *,
    month: str = "",
    main_category: str = "",
    sub_category: str = "",
    risk_tag: str = "",
    counterparty: str = "",
    min_amount: float | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []
    if month:
        clauses.append("substr(date, 1, 7) = ?")
        params.append(month)
    if main_category:
        clauses.append("main_category = ?")
        params.append(main_category)
    if sub_category:
        clauses.append("sub_category = ?")
        params.append(sub_category)
    if risk_tag:
        clauses.append("instr('|' || risk_tags || '|', ?) > 0")
        params.append(f"|{risk_tag}|")
    if counterparty:
        clauses.append("counterparty like ?")
        params.append(f"%{counterparty}%")
    if min_amount is not None:
        clauses.append("cast(allocated_amount as real) >= ?")
        params.append(min_amount)
    params.append(limit)
    where = " and ".join(clauses)
    return _rows(
        conn,
        f"""
        select transaction_time, counterparty, description, allocated_amount as amount,
               main_category, sub_category, risk_tags, review_decision, review_key
        from production_expense_allocations
        where {where}
        order by date desc, cast(allocated_amount as real) desc
        limit ?
        """,
        tuple(params),
    )


def list_question_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "description": item["description"],
            "view": item["view"],
            "keywords": item["keywords"],
        }
        for item in QUESTION_TEMPLATES
    ]


def _match_question_template(question: str) -> dict[str, Any] | None:
    normalized = question.casefold().strip()
    if not normalized:
        return None
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, template in enumerate(QUESTION_TEMPLATES):
        score = sum(1 for keyword in template["keywords"] if str(keyword).casefold() in normalized)
        if score:
            scored.append((score, -index, template))
    if not scored:
        return None
    return sorted(scored, reverse=True)[0][2]


def query_question(conn: sqlite3.Connection, question: str, limit: int = 20) -> dict[str, Any]:
    template = _match_question_template(question)
    if template is None:
        return {
            "ok": False,
            "question": question,
            "matched_template": "",
            "message": "未匹配到固定只读问题模板；不会执行任意 SQL。",
            "suggested_templates": list_question_templates(),
            "data": [],
        }
    template_id = str(template["id"])
    if template_id == "latest_month_cashflow":
        data: Any = query_stats(conn, "month", min(limit, 12))
    elif template_id == "top_categories":
        data = query_categories(conn, limit)
    elif template_id == "risk_exposure":
        data = query_risks(conn, limit)
    elif template_id == "pending_large_review":
        data = {
            "status": query_review_status(conn),
            "transactions": query_review(conn, limit),
            "candidate_groups": query_review_candidate_groups(conn, min(limit, 50)),
        }
    elif template_id == "control_actions":
        data = query_control_plan(conn, limit)
    elif template_id == "daily_cashflow":
        data = query_daily_cashflow(conn, limit)
    else:
        data = []
    return {
        "ok": True,
        "question": question,
        "matched_template": template_id,
        "title": template["title"],
        "description": template["description"],
        "view": template["view"],
        "read_only": True,
        "data": data,
    }


def _print_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("无结果")
        return
    headers = list(rows[0].keys())
    widths = {
        header: min(32, max(len(str(header)), *(len(str(row.get(header, ""))) for row in rows)))
        for header in headers
    }
    print("  ".join(header.ljust(widths[header]) for header in headers))
    print("  ".join("-" * widths[header] for header in headers))
    for row in rows:
        cells = []
        for header in headers:
            value = str(row.get(header, ""))
            if len(value) > widths[header]:
                value = value[: widths[header] - 1] + "…"
            cells.append(value.ljust(widths[header]))
        print("  ".join(cells))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query generated economic bleed SQLite outputs in read-only mode.")
    parser.add_argument("--db", default="data/finance_ledger/finance_ledger.sqlite", help="Shared ledger or generated consumption.sqlite path.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of a compact table.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_json_flag(command: argparse.ArgumentParser) -> argparse.ArgumentParser:
        command.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Output JSON instead of a compact table.")
        return command

    add_json_flag(sub.add_parser("months", help="List months available in the generated database."))

    stats = add_json_flag(sub.add_parser("stats", help="Show period cashflow summaries."))
    stats.add_argument("--period", choices=sorted(PERIOD_TABLES), default="month")
    stats.add_argument("--limit", type=int, default=12)

    categories = add_json_flag(sub.add_parser("categories", help="Show category and subcategory totals."))
    categories.add_argument("--limit", type=int, default=30)

    risks = add_json_flag(sub.add_parser("risks", help="Show risk tag totals."))
    risks.add_argument("--limit", type=int, default=20)

    transactions = add_json_flag(sub.add_parser("transactions", help="Search production-statistics transactions."))
    transactions.add_argument("--month", default="", help="Filter by YYYY-MM.")
    transactions.add_argument("--main-category", default="")
    transactions.add_argument("--sub-category", default="")
    transactions.add_argument("--risk-tag", default="")
    transactions.add_argument("--counterparty", default="")
    transactions.add_argument("--min-amount", type=float)
    transactions.add_argument("--limit", type=int, default=50)

    review = add_json_flag(sub.add_parser("review", help="Show pending large-review transactions."))
    review.add_argument("--limit", type=int, default=30)

    control = add_json_flag(sub.add_parser("control-plan", help="Show spending-control actions."))
    control.add_argument("--limit", type=int, default=20)

    ask = add_json_flag(sub.add_parser("ask", help="Ask a fixed-template read-only question."))
    ask.add_argument("question", help="Question text. It is matched against safe built-in templates; arbitrary SQL is never executed.")
    ask.add_argument("--limit", type=int, default=20)
    return parser


def run_query(args: argparse.Namespace) -> list[dict[str, Any]] | dict[str, Any]:
    with connect_readonly(args.db) as conn:
        if args.command == "months":
            return query_months(conn)
        if args.command == "stats":
            return query_stats(conn, args.period, args.limit)
        if args.command == "categories":
            return query_categories(conn, args.limit)
        if args.command == "risks":
            return query_risks(conn, args.limit)
        if args.command == "transactions":
            return query_transactions(
                conn,
                month=args.month,
                main_category=args.main_category,
                sub_category=args.sub_category,
                risk_tag=args.risk_tag,
                counterparty=args.counterparty,
                min_amount=args.min_amount,
                limit=args.limit,
            )
        if args.command == "review":
            return query_review(conn, args.limit)
        if args.command == "control-plan":
            return query_control_plan(conn, args.limit)
        if args.command == "ask":
            return query_question(conn, args.question, args.limit)
    raise ValueError(f"Unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_query(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if args.command == "ask":
            if result.get("ok"):  # type: ignore[union-attr]
                print(f"问题模板：{result['title']} ({result['matched_template']})")  # type: ignore[index]
                print(f"数据视图：{result['view']}")  # type: ignore[index]
                data = result.get("data")  # type: ignore[union-attr]
                if isinstance(data, dict):
                    for key, rows in data.items():
                        print(f"\n[{key}]")
                        _print_table(rows)
                else:
                    _print_table(data)
            else:
                print(result["message"])  # type: ignore[index]
                _print_table(result["suggested_templates"])  # type: ignore[index]
        else:
            _print_table(result)  # type: ignore[arg-type]
    if args.command == "ask" and isinstance(result, dict) and not result.get("ok"):
        return 1
    return 0
