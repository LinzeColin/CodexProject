from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ReconciliationResult:
    result_id: str
    source_ids: tuple[str, ...]
    input_refs: tuple[str, ...]
    status: str
    confidence: float
    reason: str
    requires_review: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CnBrokerProfile:
    broker_name: str
    terminal_type: str
    supports_qmt: bool
    supports_ptrade: bool
    supports_excel_statement: bool
    supports_pdf_statement: bool
    supports_html_table: bool
    supports_browser_read: bool
    supports_manual_snapshot: bool
    account_fields: tuple[str, ...]
    position_fields: tuple[str, ...]
    trade_fields: tuple[str, ...]
    parser_profile: str
    login_profile: str
    field_mapping: dict[str, str]


def build_alipay_fund_non_csv_contract() -> dict[str, object]:
    return {
        "source_id": "alipay_fund",
        "csv_assumption": False,
        "transaction_line": ("fund_transaction_line", "fund_subscription", "fund_redemption", "cash_arrival", "fee"),
        "holding_line": ("fund_page_read", "app_assisted_read", "manual_holding_snapshot"),
        "nav_line": ("external_nav_source", "independent_qbvs_nav_reference"),
        "models": (
            "fund_transaction",
            "fund_holding_snapshot",
            "fund_nav_snapshot",
            "fund_rule_profile",
            "fund_reconciliation_result",
        ),
        "rules": (
            "fund_subscription_not_consumption",
            "fund_redemption_not_ordinary_income",
            "pending_shares_not_confirmed_holding",
            "redemption_request_not_available_cash",
            "holding_snapshot_does_not_replace_trade_history",
            "external_nav_does_not_replace_owner_transactions",
        ),
    }


def reconcile_alipay_fund_triangle(
    *,
    transaction_refs: tuple[str, ...],
    holding_snapshot_refs: tuple[str, ...],
    nav_snapshot_refs: tuple[str, ...],
    expected_market_value: float,
    observed_market_value: float,
) -> ReconciliationResult:
    refs = transaction_refs + holding_snapshot_refs + nav_snapshot_refs
    if not transaction_refs or not holding_snapshot_refs or not nav_snapshot_refs:
        return ReconciliationResult(
            "fund_recon_missing_input",
            ("alipay_daily", "alipay_fund", "external_nav"),
            refs,
            "NEEDS_REVIEW",
            0.4,
            "Transaction, holding, and NAV lines are all required before marking fund reconciliation successful.",
            True,
        )
    tolerance = max(1.0, abs(expected_market_value) * 0.01)
    diff = abs(expected_market_value - observed_market_value)
    if diff <= tolerance:
        return ReconciliationResult(
            "fund_recon_matched",
            ("alipay_daily", "alipay_fund", "external_nav"),
            refs,
            "MATCHED",
            0.92,
            "Transaction line, holding snapshot, and NAV valuation agree within tolerance.",
            False,
        )
    return ReconciliationResult(
        "fund_recon_mismatch",
        ("alipay_daily", "alipay_fund", "external_nav"),
        refs,
        "MISMATCH",
        0.66,
        "Fund transaction, holding, and NAV lines disagree; owner review required.",
        True,
    )


def build_moomoo_read_only_contract() -> dict[str, object]:
    return {
        "source_id": "moomoo_au",
        "probe": "OpenD/API read-only availability probe",
        "read_contracts": ("account_list", "funds", "positions", "orders", "fills"),
        "ledger_outputs": ("investment_ledger_events", "holding_snapshot", "investment_summary"),
        "external_qbvs_reference": True,
        "external_runtime_refs": (
            "QBVS/qbvs/datasources.py",
            "QBVS/qbvs/moomoo_batch.py",
        ),
        "boundaries": ("no_trading_password", "no_live_order_submission", "do_not_fabricate_unavailable_data"),
    }


def probe_moomoo_opend_contract(*, opend_available: bool, sdk_available: bool) -> dict[str, object]:
    available = opend_available and sdk_available
    return {
        "source_id": "moomoo_au",
        "opend_available": opend_available,
        "sdk_available": sdk_available,
        "status": "AVAILABLE" if available else "UNAVAILABLE",
        "can_emit_synthetic_data": False,
        "next_action": "read_accounts_funds_positions" if available else "owner_or_environment_setup_required",
    }


def default_cn_broker_profile() -> CnBrokerProfile:
    return CnBrokerProfile(
        broker_name="Generic China Broker",
        terminal_type="profile_selected",
        supports_qmt=True,
        supports_ptrade=True,
        supports_excel_statement=True,
        supports_pdf_statement=True,
        supports_html_table=True,
        supports_browser_read=True,
        supports_manual_snapshot=True,
        account_fields=("account_id", "currency", "available_cash", "market_value"),
        position_fields=("symbol", "name", "quantity", "available_quantity", "market_value", "cost_basis"),
        trade_fields=("trade_id", "occurred_at", "side", "symbol", "quantity", "price", "commission", "stamp_tax", "transfer_fee"),
        parser_profile="cn_broker_profile_v1",
        login_profile="read_only_or_manual_snapshot",
        field_mapping={
            "银证转账": "TRANSFER",
            "买入": "BUY_ASSET",
            "卖出": "SELL_ASSET",
            "佣金": "FEE",
            "印花税": "TAX",
            "过户费": "FEE",
        },
    )


def select_cn_broker_acquisition(profile: CnBrokerProfile) -> tuple[str, ...]:
    modes: list[str] = []
    if profile.supports_qmt:
        modes.append("CN_BROKER_QMT_READONLY")
    if profile.supports_ptrade:
        modes.append("CN_BROKER_PTRADE_READONLY")
    if profile.supports_html_table or profile.supports_browser_read:
        modes.append("CN_BROKER_HTML_STATEMENT")
    if profile.supports_pdf_statement:
        modes.append("CN_BROKER_PDF_STATEMENT")
    if profile.supports_excel_statement:
        modes.append("CN_BROKER_EXCEL_STATEMENT")
    if profile.supports_manual_snapshot:
        modes.append("CN_BROKER_MANUAL_SNAPSHOT")
    return tuple(modes)


def build_abc_bullion_non_csv_contract() -> dict[str, object]:
    return {
        "source_id": "abc_bullion",
        "csv_required": False,
        "acquisition_modes": (
            "ABC_ACCOUNT_PAGE_READ",
            "ABC_TRANSACTION_STATEMENT_HTML",
            "ABC_TRANSACTION_STATEMENT_PDF",
            "ABC_BROWSER_ASSISTED_READ",
            "ABC_HOLDING_SNAPSHOT",
            "ABC_OPTIONAL_CSV",
            "IMAGE_OCR_CANDIDATE_ONLY",
        ),
        "event_model": (
            "metal",
            "unit",
            "quantity",
            "currency",
            "buy_sell_side",
            "storage_fee",
            "delivery_fee",
            "platform_fee",
            "valuation_timestamp",
        ),
        "rules": (
            "gold_silver_buy_is_buy_asset_not_consumption",
            "gold_silver_sell_is_sell_asset_not_ordinary_income",
            "fees_are_fee_events",
        ),
    }


def reconcile_abc_triangle(
    *,
    statement_refs: tuple[str, ...],
    bank_payment_refs: tuple[str, ...],
    valuation_refs: tuple[str, ...],
) -> ReconciliationResult:
    refs = statement_refs + bank_payment_refs + valuation_refs
    if statement_refs and bank_payment_refs and valuation_refs:
        return ReconciliationResult(
            "abc_recon_matched",
            ("abc_bullion", "cba_bank", "valuation_source"),
            refs,
            "MATCHED",
            0.9,
            "ABC statement, bank payment, and valuation snapshot are linked.",
            False,
        )
    return ReconciliationResult(
        "abc_recon_missing_input",
        ("abc_bullion", "cba_bank", "valuation_source"),
        refs,
        "NEEDS_REVIEW",
        0.45,
        "ABC Bullion reconciliation requires statement, bank payment, and valuation evidence.",
        True,
    )


def build_wechat_contract() -> dict[str, object]:
    return {
        "source_id": "wechat_pay",
        "file_contracts": ("EMAIL_ZIP", "CSV", "XLS", "XLSX", "WATCH_FOLDER"),
        "normalizer": "wechat_payment_normalizer_v1",
        "recognized_events": ("消费", "转账", "红包", "收款", "退款", "提现", "充值", "商户支付", "个人转账", "未知"),
        "rules": (
            "transfer_not_consumption",
            "refund_not_new_consumption",
            "unknown_or_low_confidence_goes_to_review",
        ),
    }


def build_stage2_contract_summary() -> dict[str, object]:
    return {
        "alipay_fund": build_alipay_fund_non_csv_contract(),
        "moomoo_au": build_moomoo_read_only_contract(),
        "cn_broker": asdict(default_cn_broker_profile()),
        "abc_bullion": build_abc_bullion_non_csv_contract(),
        "wechat_pay": build_wechat_contract(),
    }
