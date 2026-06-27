from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable

from pfi_v02.core_models import LedgerEventType, NormalizedTransaction
from pfi_v02.stage2_import import (
    ReviewQueueItem,
    Stage2ImportResult,
    TransferMatch,
    parse_alipay_bill_bytes,
    parse_cba_csv_bytes,
    reconcile_cba_transfer,
)
from pfi_v02.stage2_registry import build_stage2_registry


SIMPLE_STATUS_LANGUAGE = ("正常", "需要同步", "需要复核", "有异常", "有建议")

STAGE3_REQUIRED_ACCOUNT_SOURCES = (
    "alipay_daily",
    "alipay_fund",
    "moomoo_au",
    "cn_broker",
    "abc_bullion",
    "cba_bank",
    "wechat_pay",
)

STAGE3_FX_TO_AUD = {
    "AUD": 1.0,
    "CNY": 0.21,
    "USD": 1.52,
    "HKD": 0.195,
}

STAGE3_CBA_FIXTURE = """Date,Description,Debit,Credit,Account
27/06/2026,Salary from employer,,3200.00,acct_cba_main
28/06/2026,CBA transfer to Moomoo brokerage,5000.00,,acct_cba_main
29/06/2026,Credit card repayment,1200.00,,acct_cba_main
30/06/2026,ABC Bullion gold purchase,700.00,,acct_cba_main
"""

STAGE3_ALIPAY_FIXTURE = """交易时间,商品说明,交易对方,交易类型,金额,收/支
2026-06-27 10:00:00,咖啡,本地商户,消费,18.50,支出
2026-06-27 11:00:00,支付宝基金申购,易方达基金,基金申购,800.00,支出
2026-06-28 12:00:00,基金赎回到账,易方达基金,基金赎回,500.00,收入
2026-06-28 13:00:00,退款,电商平台,退款,30.00,收入
2026-06-29 14:00:00,未知,,未知,12.00,支出
"""


@dataclass(frozen=True)
class Stage3AccountView:
    account_id: str
    source_id: str
    platform: str
    display_name: str
    category: str
    currency: str
    platform_balance: float
    ledger_balance: float
    source_status: str
    evidence_ref: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Stage3Recommendation:
    recommendation_id: str
    domain: str
    evidence_refs: tuple[str, ...]
    action: str
    status: str
    expected_effect: str
    tradeoff: str
    target_entry: str
    priority: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Stage3SyncAction:
    source_id: str
    display_name: str
    action: str
    owner_status: str
    does_not_execute: bool
    boundary: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_stage3_demo_accounts() -> tuple[Stage3AccountView, ...]:
    return (
        Stage3AccountView("acct_alipay_daily", "alipay_daily", "支付宝", "支付宝日常", "daily", "CNY", 1500.0, 1500.0, "正常", "src:alipay_daily"),
        Stage3AccountView("acct_alipay_fund", "alipay_fund", "支付宝基金", "支付宝基金持仓", "investment", "CNY", 12000.0, 11980.0, "需要复核", "src:alipay_fund"),
        Stage3AccountView("acct_moomoo_au", "moomoo_au", "Moomoo AU", "Moomoo AU 证券", "investment", "USD", 18500.0, 18500.0, "正常", "src:moomoo_au"),
        Stage3AccountView("acct_cn_broker", "cn_broker", "中国券商", "中国大陆券商", "investment", "CNY", 66000.0, 66000.0, "需要同步", "src:cn_broker"),
        Stage3AccountView("acct_abc_bullion", "abc_bullion", "ABC Bullion", "ABC 贵金属", "asset", "AUD", 4200.0, 4200.0, "正常", "src:abc_bullion"),
        Stage3AccountView("acct_cba_main", "cba_bank", "CBA", "CBA 主账户", "cash", "AUD", 8200.0, 8150.0, "需要复核", "src:cba_bank"),
        Stage3AccountView("acct_wechat_pay", "wechat_pay", "微信", "微信支付", "daily", "CNY", 400.0, 400.0, "需要同步", "src:wechat_pay"),
        Stage3AccountView("acct_credit_card", "cba_bank", "CBA", "信用卡负债", "liability", "AUD", -1200.0, -1200.0, "正常", "src:cba_credit"),
        Stage3AccountView("acct_hk_cash", "other_connector", "其他平台", "HKD 现金观察", "cash", "HKD", 2500.0, 2500.0, "有建议", "src:other_connector"),
    )


def build_stage3_demo_imports() -> tuple[Stage2ImportResult, ...]:
    return (
        parse_cba_csv_bytes(STAGE3_CBA_FIXTURE.encode("utf-8")),
        parse_alipay_bill_bytes(STAGE3_ALIPAY_FIXTURE.encode("utf-8")),
    )


def simple_status_language(status: str) -> str:
    text = status.strip().lower().replace("-", "_").replace(" ", "_")
    if text in {"ok", "pass", "ready", "available", "completed", "matched", "accepted", "normal", "正常"}:
        return "正常"
    if text in {"stale", "missing", "needs_data", "needs_sync", "unavailable", "待补", "需要同步"}:
        return "需要同步"
    if text in {"review", "needs_review", "pending_review", "mismatch", "partial", "需要复核"}:
        return "需要复核"
    if text in {"blocked", "failed", "error", "exception", "有异常"}:
        return "有异常"
    if text in {"watch", "suggestion", "recommended", "有建议"}:
        return "有建议"
    return "需要复核"


def build_stage3_read_model(
    *,
    accounts: tuple[Stage3AccountView, ...] | None = None,
    imports: tuple[Stage2ImportResult, ...] | None = None,
    fx_to_aud: dict[str, float] | None = None,
    now: datetime | None = None,
    top_n: int = 3,
) -> dict[str, object]:
    account_rows = accounts or build_stage3_demo_accounts()
    import_results = imports or build_stage3_demo_imports()
    fx = fx_to_aud or dict(STAGE3_FX_TO_AUD)
    generated_at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    transactions = tuple(txn for result in import_results for txn in result.transactions)
    review_items = tuple(item for result in import_results for item in result.review_queue)
    transfer_matches = tuple(match for txn in transactions if (match := reconcile_cba_transfer(txn)) is not None)
    evidence_index = _evidence_index(import_results)
    home = _home_summary(account_rows, transactions, review_items, fx)
    account_map = _account_map(account_rows)
    ledger_view = _ledger_view(transactions, evidence_index)
    reconciliation = _reconciliation(account_rows, fx)
    recommendations = _recommendations(account_rows, review_items, reconciliation, top_n=top_n)
    sync_plan = build_sync_all_plan()
    review_checklist = build_owner_review_checklist(review_items)
    return {
        "schema": "PFIV02Stage3ReadableMVPV1",
        "stage": "PFI V0.2 Stage 3",
        "generated_at": generated_at,
        "home": home,
        "account_map": account_map,
        "accounts": [account.to_dict() for account in account_rows],
        "fx_view": _fx_view(account_rows, fx),
        "reconciliation": reconciliation,
        "ledger": ledger_view,
        "review_queue": review_checklist,
        "transfer_matching": [transfer_match_decision(match, "confirm") for match in transfer_matches],
        "recommendations": [item.to_dict() for item in recommendations],
        "quick_actions": _quick_actions(sync_plan, review_checklist, recommendations),
        "sync_all_plan": [item.to_dict() for item in sync_plan],
        "status_language": SIMPLE_STATUS_LANGUAGE,
        "boundaries": (
            "synthetic_or_local_read_model_only",
            "no_trading_password",
            "no_broker_order_submission",
            "no_payment_submission",
            "sync_all_plan_does_not_execute_external_actions",
        ),
    }


def build_sync_all_plan() -> tuple[Stage3SyncAction, ...]:
    registry = build_stage2_registry()
    actions: list[Stage3SyncAction] = []
    for source_id in STAGE3_REQUIRED_ACCOUNT_SOURCES:
        profile = registry[source_id]
        modes = " ".join(profile.primary_acquisition)
        if any(marker in modes for marker in ("CSV", "ZIP", "XLS", "WATCH_FOLDER", "STATEMENT")):
            action = "扫描本地导入收件箱"
        elif "OPEND" in modes or "API" in modes or "READ" in modes:
            action = "只读同步预检"
        else:
            action = "等待手动快照"
        actions.append(
            Stage3SyncAction(
                source_id=source_id,
                display_name=profile.display_name,
                action=action,
                owner_status=simple_status_language("needs_sync"),
                does_not_execute=True,
                boundary="只生成同步/导入计划，不登录、不下单、不支付、不写真实账户。",
            )
        )
    return tuple(actions)


def build_owner_review_checklist(review_items: Iterable[ReviewQueueItem]) -> list[dict[str, object]]:
    rows = []
    for item in review_items:
        rows.append(
            {
                "transaction_id": item.transaction_id,
                "reason": item.reason,
                "status": "需要复核",
                "choices": (
                    "A 接受建议分类",
                    "B 标记为转账",
                    "C 标记为消费",
                    "D 保持待复核",
                ),
            }
        )
    return rows


def transfer_match_decision(match: TransferMatch, decision: str) -> dict[str, object]:
    if decision == "confirm":
        return {
            "transaction_id": match.transaction_id,
            "decision": "confirm",
            "status": "正常",
            "affects_consumption": False,
            "reason": match.reason,
        }
    if decision == "reject":
        return {
            "transaction_id": match.transaction_id,
            "decision": "reject",
            "status": "需要复核",
            "affects_consumption": True,
            "reason": "Owner rejected the transfer match; classify manually before ledger acceptance.",
        }
    if decision == "modify":
        return {
            "transaction_id": match.transaction_id,
            "decision": "modify",
            "status": "需要复核",
            "affects_consumption": False,
            "reason": "Owner modified the transfer match; keep the item in review until evidence is updated.",
        }
    raise ValueError("decision must be confirm, reject, or modify")


def _home_summary(
    accounts: tuple[Stage3AccountView, ...],
    transactions: tuple[NormalizedTransaction, ...],
    review_items: tuple[ReviewQueueItem, ...],
    fx: dict[str, float],
) -> dict[str, object]:
    net_worth = sum(_to_aud(account.ledger_balance, account.currency, fx) for account in accounts)
    cash = sum(
        _to_aud(account.ledger_balance, account.currency, fx)
        for account in accounts
        if account.category in {"cash", "daily"}
    )
    investment_assets = sum(
        _to_aud(account.ledger_balance, account.currency, fx)
        for account in accounts
        if account.category in {"investment", "asset"}
    )
    monthly_spending = sum(abs(_to_aud(txn.amount, txn.currency, fx)) for txn in transactions if _is_consumption(txn))
    data_health = "需要复核" if review_items or any(account.source_status != "正常" for account in accounts) else "正常"
    return {
        "financial_status_cards": (
            _home_card("net_worth", "净资产", _money(net_worth, "AUD"), "账户账本余额折算 AUD；使用本地 fixture 汇率。"),
            _home_card("cash", "现金", _money(cash, "AUD"), "日常账户、现金账户和观察现金合计。"),
            _home_card("investment_assets", "投资资产", _money(investment_assets, "AUD"), "投资账户和贵金属资产合计。"),
            _home_card("monthly_spending", "本月支出", _money(monthly_spending, "AUD"), "已分类消费流水合计；转账、基金和贵金属买卖排除。"),
            _home_card("data_health", "数据健康", data_health, f"{len(review_items)} 条待复核；{sum(1 for account in accounts if account.source_status != '正常')} 个账户需处理。"),
        ),
        "snapshots": (
            _snapshot("投资快照", "投资管理", ("accounts:investment", "ledger:investment"), "查看投资资产、基金、券商和贵金属状态。"),
            _snapshot("消费快照", "消费管理", ("ledger:consumption", "review_queue"), "查看本月支出、低置信度流水和转账排除。"),
            _snapshot("现金流快照", "账本流水", ("accounts:cash", "ledger:cashflow"), "查看现金账户、收入支出和信用卡还款。"),
        ),
        "owner_status": data_health,
    }


def _account_map(accounts: tuple[Stage3AccountView, ...]) -> list[dict[str, object]]:
    by_source: dict[str, list[Stage3AccountView]] = {}
    for account in accounts:
        by_source.setdefault(account.source_id, []).append(account)
    registry = build_stage2_registry()
    rows = []
    for source_id in STAGE3_REQUIRED_ACCOUNT_SOURCES:
        matched = by_source.get(source_id, ())
        status = _rollup_status(account.source_status for account in matched) if matched else "需要同步"
        rows.append(
            {
                "source_id": source_id,
                "display_name": registry[source_id].display_name,
                "account_count": len(matched),
                "status": status,
                "target_entry": "账户与资产",
                "detail_route": f"账户与资产/{source_id}",
            }
        )
    return rows


def _fx_view(accounts: tuple[Stage3AccountView, ...], fx: dict[str, float]) -> dict[str, object]:
    rows = []
    for currency in ("AUD", "CNY", "USD", "HKD"):
        native_total = sum(account.ledger_balance for account in accounts if account.currency == currency)
        rows.append(
            {
                "currency": currency,
                "native_total": round(native_total, 2),
                "aud_value": round(_to_aud(native_total, currency, fx), 2),
                "rate_to_aud": fx[currency],
                "rate_source": "stage3_fixture_not_live_market_rate",
            }
        )
    return {
        "base_currency": "AUD",
        "supported_currencies": ("AUD", "CNY", "USD", "HKD"),
        "rows": rows,
    }


def _reconciliation(accounts: tuple[Stage3AccountView, ...], fx: dict[str, float]) -> list[dict[str, object]]:
    rows = []
    for account in accounts:
        diff = account.platform_balance - account.ledger_balance
        status = "正常" if abs(_to_aud(diff, account.currency, fx)) <= 1.0 else "需要复核"
        rows.append(
            {
                "account_id": account.account_id,
                "platform_balance": account.platform_balance,
                "ledger_balance": account.ledger_balance,
                "currency": account.currency,
                "difference": round(diff, 2),
                "status": status,
                "evidence_ref": account.evidence_ref,
            }
        )
    return rows


def _ledger_view(transactions: tuple[NormalizedTransaction, ...], evidence_index: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for txn in transactions:
        evidence = evidence_index.get(txn.raw_id, {})
        rows.append(
            {
                "transaction_id": txn.transaction_id,
                "source_id": txn.source_id,
                "account_id": txn.account_id,
                "event_type": txn.event_type.value,
                "amount": txn.amount,
                "currency": txn.currency,
                "occurred_at": txn.occurred_at,
                "description": txn.description,
                "confidence": txn.confidence,
                "review_state": txn.review_state,
                "source_trace": {
                    "batch_id": evidence.get("batch_id", ""),
                    "raw_id": txn.raw_id,
                    "raw_payload_ref": evidence.get("raw_payload_ref", ""),
                    "parser_version": evidence.get("parser_version", ""),
                },
                "detail_route": f"账本流水/{txn.transaction_id}",
            }
        )
    return rows


def _recommendations(
    accounts: tuple[Stage3AccountView, ...],
    review_items: tuple[ReviewQueueItem, ...],
    reconciliation: list[dict[str, object]],
    *,
    top_n: int,
) -> tuple[Stage3Recommendation, ...]:
    candidates = [
        Stage3Recommendation(
            "rec_sync_all",
            "data_health",
            tuple(f"src:{account.source_id}" for account in accounts if account.source_status != "正常"),
            "同步全部",
            "有建议",
            "补齐过期或待同步来源，减少首页待补状态。",
            "只生成同步计划；真实登录仍需 owner 确认。",
            "数据源与同步",
            1,
        ),
        Stage3Recommendation(
            "rec_review_queue",
            "ledger_review",
            tuple(item.transaction_id for item in review_items),
            "处理待复核",
            "需要复核" if review_items else "正常",
            "低置信度流水先复核，避免 unknown 静默入账。",
            "需要人工选择 A/B/C/D。",
            "账本流水",
            2,
        ),
        Stage3Recommendation(
            "rec_reconcile_accounts",
            "account_reconciliation",
            tuple(str(row["evidence_ref"]) for row in reconciliation if row["status"] != "正常"),
            "查看账户对账",
            "需要复核" if any(row["status"] != "正常" for row in reconciliation) else "正常",
            "平台余额和 PFI 账本余额差异可见。",
            "差异确认前不写成已对账。",
            "账户与资产",
            3,
        ),
        Stage3Recommendation(
            "rec_monthly_report",
            "report",
            ("home:financial_status", "ledger:all"),
            "生成报告",
            "有建议",
            "把首页、账户、账本和待复核状态导出为 owner 可读报告。",
            "报告为本地只读草稿，不代表生产就绪。",
            "报告与洞察",
            4,
        ),
    ]
    return tuple(sorted(candidates, key=lambda item: item.priority)[:top_n])


def _quick_actions(
    sync_plan: tuple[Stage3SyncAction, ...],
    review_checklist: list[dict[str, object]],
    recommendations: tuple[Stage3Recommendation, ...],
) -> tuple[dict[str, object], ...]:
    return (
        {"label": "同步全部", "target_entry": "数据源与同步", "status": "需要同步", "evidence_count": len(sync_plan)},
        {"label": "处理待复核", "target_entry": "账本流水", "status": "需要复核" if review_checklist else "正常", "evidence_count": len(review_checklist)},
        {"label": "查看建议", "target_entry": "建议与复盘", "status": "有建议", "evidence_count": len(recommendations)},
        {"label": "生成报告", "target_entry": "报告与洞察", "status": "有建议", "evidence_count": 2},
    )


def _evidence_index(import_results: tuple[Stage2ImportResult, ...]) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for result in import_results:
        for raw in result.raw_records:
            index[raw.raw_id] = {
                "batch_id": raw.batch_id,
                "raw_payload_ref": raw.raw_payload_ref,
                "parser_version": result.import_batch.parser_version,
            }
    return index


def _is_consumption(txn: NormalizedTransaction) -> bool:
    return txn.event_type == LedgerEventType.CASH and txn.amount < 0 and txn.review_state == "ACCEPTED"


def _to_aud(amount: float, currency: str, fx: dict[str, float]) -> float:
    if currency not in fx:
        raise ValueError(f"Missing FX fixture for {currency}.")
    return amount * fx[currency]


def _money(value: float, currency: str) -> str:
    return f"{currency} {value:,.2f}"


def _home_card(key: str, label: str, value: str, detail: str) -> dict[str, str]:
    return {"key": key, "label": label, "value": value, "detail": detail}


def _snapshot(label: str, target_entry: str, evidence_refs: tuple[str, ...], summary: str) -> dict[str, object]:
    return {
        "label": label,
        "target_entry": target_entry,
        "detail_route": f"{target_entry}/{label}",
        "evidence_refs": evidence_refs,
        "summary": summary,
    }


def _rollup_status(statuses: Iterable[str]) -> str:
    normalized = [simple_status_language(status) for status in statuses]
    for status in ("有异常", "需要复核", "需要同步", "有建议", "正常"):
        if status in normalized:
            return status
    return "需要复核"
