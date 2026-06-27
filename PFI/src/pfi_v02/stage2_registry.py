from __future__ import annotations

from dataclasses import asdict, dataclass


REQUIRED_STAGE2_SOURCE_IDS = (
    "alipay_daily",
    "alipay_fund",
    "moomoo_au",
    "cn_broker",
    "abc_bullion",
    "cba_bank",
    "wechat_pay",
    "other_connector",
)


@dataclass(frozen=True)
class Stage2SourceProfile:
    source_id: str
    display_name: str
    domains: tuple[str, ...]
    primary_acquisition: tuple[str, ...]
    secondary_acquisition: tuple[str, ...]
    credential_requirements: tuple[str, ...]
    freshness_target: str
    parser_contracts: tuple[str, ...]
    ledger_boundaries: tuple[str, ...]
    extension_kind: str = "BUILT_IN"
    low_trust_candidate_modes: tuple[str, ...] = ()
    active_runtime_refs: tuple[str, ...] = ()
    read_only: bool = True
    requires_trading_password: bool = False

    def validate(self) -> None:
        if not self.read_only:
            raise ValueError(f"{self.source_id} must be read-only.")
        if self.requires_trading_password:
            raise ValueError(f"{self.source_id} must not require a trading password.")
        if not self.primary_acquisition:
            raise ValueError(f"{self.source_id} must declare acquisition modes.")
        if not self.freshness_target:
            raise ValueError(f"{self.source_id} must declare a freshness target.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_stage2_registry() -> dict[str, Stage2SourceProfile]:
    profiles = (
        Stage2SourceProfile(
            source_id="alipay_daily",
            display_name="支付宝日常账单",
            domains=("consumption", "transfer", "income", "refund", "investment_candidate"),
            primary_acquisition=("EMAIL_ZIP", "BILL_EXPORT_CSV", "BILL_EXPORT_ZIP", "WATCH_FOLDER"),
            secondary_acquisition=("BROWSER_ASSISTED_READ", "MANUAL_UPLOAD"),
            credential_requirements=("READ_STATEMENT", "IMPORT_FILE"),
            freshness_target="daily",
            parser_contracts=("alipay_bill_csv_v1", "alipay_bill_zip_v1"),
            ledger_boundaries=(
                "fund_subscription_is_investment_not_consumption",
                "fund_redemption_is_pending_cash_not_ordinary_income",
                "transfer_is_not_consumption",
                "low_confidence_goes_to_review",
            ),
            low_trust_candidate_modes=("OCR_CANDIDATE_ONLY", "SCREENSHOT_ASSISTED_REVIEW"),
        ),
        Stage2SourceProfile(
            source_id="alipay_fund",
            display_name="支付宝基金",
            domains=("investment", "fund", "holding_snapshot", "valuation"),
            primary_acquisition=(
                "ALIPAY_DAILY_CROSS_MATCH",
                "FUND_PAGE_READ",
                "APP_ASSISTED_READ",
                "MANUAL_HOLDING_SNAPSHOT",
                "EXTERNAL_NAV_SOURCE",
            ),
            secondary_acquisition=("STATEMENT_IF_AVAILABLE",),
            credential_requirements=("READ_STATEMENT", "READ_POSITIONS"),
            freshness_target="daily",
            parser_contracts=(
                "fund_transaction_line",
                "fund_holding_snapshot_line",
                "fund_nav_snapshot_line",
                "fund_reconciliation_result",
            ),
            ledger_boundaries=(
                "do_not_assume_csv",
                "holding_snapshot_does_not_replace_transactions",
                "external_nav_does_not_replace_owner_trade_records",
            ),
        ),
        Stage2SourceProfile(
            source_id="moomoo_au",
            display_name="Moomoo AU",
            domains=("investment", "brokerage", "positions", "orders", "fills"),
            primary_acquisition=("OPEND_READ_ONLY_PROBE", "API_READ_ONLY"),
            secondary_acquisition=("STATEMENT_EXPORT", "MANUAL_SNAPSHOT"),
            credential_requirements=("READ_BALANCE", "READ_POSITIONS", "READ_ORDERS", "READ_FILLS"),
            freshness_target="intraday",
            parser_contracts=("account_funds_positions_contract", "orders_fills_contract"),
            ledger_boundaries=("no_live_order_submission", "no_trading_password", "do_not_fabricate_when_unavailable"),
            active_runtime_refs=(
                "QBVS/qbvs/datasources.py",
                "QBVS/qbvs/moomoo_batch.py",
            ),
        ),
        Stage2SourceProfile(
            source_id="cn_broker",
            display_name="中国大陆券商",
            domains=("investment", "brokerage", "cn_market", "positions", "fills"),
            primary_acquisition=(
                "CN_BROKER_QMT_READONLY",
                "CN_BROKER_PTRADE_READONLY",
                "CN_BROKER_TERMINAL_READ",
                "CN_BROKER_HTML_STATEMENT",
                "CN_BROKER_PDF_STATEMENT",
                "CN_BROKER_EXCEL_STATEMENT",
                "CN_BROKER_MANUAL_SNAPSHOT",
            ),
            secondary_acquisition=("IMAGE_OCR_CANDIDATE_ONLY",),
            credential_requirements=("READ_STATEMENT", "READ_POSITIONS"),
            freshness_target="daily",
            parser_contracts=("cn_broker_profile_v1", "cn_broker_statement_v1"),
            ledger_boundaries=(
                "do_not_assume_universal_csv",
                "bank_to_broker_transfer_is_not_consumption",
                "commission_stamp_tax_transfer_fee_are_separate_fees",
            ),
            extension_kind="PLUGIN",
            low_trust_candidate_modes=("IMAGE_OCR_CANDIDATE_ONLY",),
        ),
        Stage2SourceProfile(
            source_id="abc_bullion",
            display_name="ABC Bullion",
            domains=("investment", "bullion", "holding_snapshot", "valuation"),
            primary_acquisition=(
                "ABC_ACCOUNT_PAGE_READ",
                "ABC_TRANSACTION_STATEMENT_HTML",
                "ABC_TRANSACTION_STATEMENT_PDF",
                "ABC_BROWSER_ASSISTED_READ",
                "ABC_HOLDING_SNAPSHOT",
            ),
            secondary_acquisition=("ABC_OPTIONAL_CSV", "IMAGE_OCR_CANDIDATE_ONLY"),
            credential_requirements=("READ_STATEMENT", "READ_POSITIONS"),
            freshness_target="weekly",
            parser_contracts=("abc_statement_contract_v1", "abc_holding_snapshot_v1", "abc_valuation_snapshot_v1"),
            ledger_boundaries=(
                "do_not_rely_on_csv",
                "gold_silver_buy_is_asset_purchase",
                "storage_delivery_platform_fee_is_fee",
                "bank_payment_needs_reconciliation",
            ),
            low_trust_candidate_modes=("IMAGE_OCR_CANDIDATE_ONLY",),
        ),
        Stage2SourceProfile(
            source_id="cba_bank",
            display_name="CBA 银行",
            domains=("bank", "cashflow", "consumption", "reconciliation"),
            primary_acquisition=("CBA_CSV_IMPORT", "WATCH_FOLDER"),
            secondary_acquisition=("PDF_STATEMENT_LATER", "CDR_OPEN_BANKING_LATER"),
            credential_requirements=("IMPORT_FILE",),
            freshness_target="daily",
            parser_contracts=("cba_csv_v1", "cba_watch_folder_v1", "cba_transfer_matching_v1"),
            ledger_boundaries=(
                "investment_deposit_is_not_consumption",
                "credit_card_repayment_is_not_duplicate_consumption",
                "bank_to_bullion_payment_requires_reconciliation",
            ),
        ),
        Stage2SourceProfile(
            source_id="wechat_pay",
            display_name="微信",
            domains=("consumption", "transfer", "refund", "red_packet"),
            primary_acquisition=("WECHAT_EMAIL_ZIP", "WECHAT_CSV", "WECHAT_XLS", "WECHAT_XLSX", "WATCH_FOLDER"),
            secondary_acquisition=("APP_ASSISTED_READ",),
            credential_requirements=("IMPORT_FILE", "READ_STATEMENT"),
            freshness_target="weekly",
            parser_contracts=("wechat_bill_file_contract_v1", "wechat_payment_normalizer_v1"),
            ledger_boundaries=(
                "wechat_transfer_is_not_consumption",
                "refund_is_not_new_consumption",
                "low_confidence_goes_to_review",
            ),
        ),
        Stage2SourceProfile(
            source_id="other_connector",
            display_name="其他平台扩展",
            domains=("extension",),
            primary_acquisition=("CONNECTOR_PROFILE", "PLUGIN_FIELD_MAPPING", "MANUAL_SAMPLE_MAPPING"),
            secondary_acquisition=("LOW_TRUST_CANDIDATE_ONLY",),
            credential_requirements=("SOURCE_SPECIFIC_READ_ONLY",),
            freshness_target="source_defined",
            parser_contracts=("plugin_profile_v1", "field_mapping_v1"),
            ledger_boundaries=("new_platform_must_not_rewrite_core_ledger",),
            extension_kind="PLUGIN",
            low_trust_candidate_modes=("LOW_TRUST_CANDIDATE_ONLY",),
        ),
    )
    return {profile.source_id: profile for profile in profiles}


def build_connector_profile(
    *,
    source_id: str,
    display_name: str,
    domains: tuple[str, ...],
    primary_acquisition: tuple[str, ...],
    field_mapping: tuple[str, ...],
) -> Stage2SourceProfile:
    return Stage2SourceProfile(
        source_id=source_id,
        display_name=display_name,
        domains=domains,
        primary_acquisition=primary_acquisition,
        secondary_acquisition=("LOW_TRUST_CANDIDATE_ONLY",),
        credential_requirements=("SOURCE_SPECIFIC_READ_ONLY",),
        freshness_target="source_defined",
        parser_contracts=("plugin_profile_v1",) + field_mapping,
        ledger_boundaries=("new_platform_must_not_rewrite_core_ledger",),
        extension_kind="PLUGIN",
        low_trust_candidate_modes=("LOW_TRUST_CANDIDATE_ONLY",),
    )


def validate_stage2_registry(registry: dict[str, Stage2SourceProfile]) -> None:
    missing = [source_id for source_id in REQUIRED_STAGE2_SOURCE_IDS if source_id not in registry]
    if missing:
        raise ValueError(f"Missing Stage 2 data sources: {', '.join(missing)}")

    for profile in registry.values():
        profile.validate()

    for source_id in ("alipay_fund", "cn_broker", "abc_bullion"):
        text = " ".join(registry[source_id].primary_acquisition + registry[source_id].ledger_boundaries).lower()
        if "csv_import" in text or text == "csv":
            raise ValueError(f"{source_id} must not assume CSV as its primary contract.")

    if registry["other_connector"].extension_kind != "PLUGIN":
        raise ValueError("Other connectors must be profile/plugin based.")


def build_stage2_registry_contract() -> dict[str, object]:
    registry = build_stage2_registry()
    validate_stage2_registry(registry)
    return {
        "stage": "PFI V0.2 Stage 2",
        "goal": "数据源与低操作自动同步 MVP",
        "required_sources": REQUIRED_STAGE2_SOURCE_IDS,
        "sources": {source_id: profile.to_dict() for source_id, profile in registry.items()},
        "boundaries": (
            "No trading password",
            "No automatic real-money order submission",
            "Non-CSV sources must remain first-class contracts",
            "Low-confidence records go to review before owner-visible ledger acceptance",
            "New platforms extend by profile/plugin and do not rewrite core ledger",
        ),
    }
