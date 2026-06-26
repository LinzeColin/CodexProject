from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class CredentialScope(str, Enum):
    READ_PROFILE = "READ_PROFILE"
    READ_STATEMENT = "READ_STATEMENT"
    READ_BALANCE = "READ_BALANCE"
    READ_POSITIONS = "READ_POSITIONS"
    READ_ORDERS = "READ_ORDERS"
    READ_FILLS = "READ_FILLS"
    IMPORT_FILE = "IMPORT_FILE"


class AcquisitionMode(str, Enum):
    CSV = "CSV"
    ZIP = "ZIP"
    EXCEL = "EXCEL"
    PDF = "PDF"
    HTML = "HTML"
    STATEMENT = "STATEMENT"
    API_READ_ONLY = "API_READ_ONLY"
    OPEND_READ_ONLY = "OPEND_READ_ONLY"
    WATCH_FOLDER = "WATCH_FOLDER"
    BROWSER_ASSISTED_READ = "BROWSER_ASSISTED_READ"
    MANUAL_SNAPSHOT = "MANUAL_SNAPSHOT"


class DataSourceCapability(str, Enum):
    BALANCES = "BALANCES"
    POSITIONS = "POSITIONS"
    ORDERS = "ORDERS"
    FILLS = "FILLS"
    STATEMENTS = "STATEMENTS"
    TRANSACTIONS = "TRANSACTIONS"
    HOLDING_SNAPSHOT = "HOLDING_SNAPSHOT"
    VALUATION = "VALUATION"
    RECONCILIATION = "RECONCILIATION"


class AccountType(str, Enum):
    PAYMENT = "PAYMENT"
    BANK = "BANK"
    BROKERAGE = "BROKERAGE"
    FUND_PLATFORM = "FUND_PLATFORM"
    BULLION_PLATFORM = "BULLION_PLATFORM"
    CREDIT_CARD = "CREDIT_CARD"
    CASH = "CASH"
    LIABILITY = "LIABILITY"


class AssetType(str, Enum):
    CASH = "CASH"
    EQUITY = "EQUITY"
    ETF = "ETF"
    FUND = "FUND"
    BULLION = "BULLION"
    CREDIT = "CREDIT"
    FX = "FX"
    OTHER = "OTHER"


class LedgerEventType(str, Enum):
    CASH = "CASH"
    TRANSFER = "TRANSFER"
    BUY_ASSET = "BUY_ASSET"
    SELL_ASSET = "SELL_ASSET"
    FUND = "FUND"
    FEE = "FEE"
    TAX = "TAX"
    FX = "FX"
    REFUND = "REFUND"
    VALUATION = "VALUATION"


@dataclass(frozen=True)
class CredentialRef:
    credential_id: str
    allowed_scopes: tuple[CredentialScope, ...]
    storage_hint: str = "PFI_PRIVATE_CREDENTIAL_STORE"
    trading_password_required: bool = False

    def validate(self) -> None:
        if self.trading_password_required:
            raise ValueError("Trading password is forbidden in PFI Stage 1.")


@dataclass(frozen=True)
class DataSource:
    source_id: str
    platform: str
    display_name: str
    capabilities: tuple[DataSourceCapability, ...]
    acquisition_modes: tuple[AcquisitionMode, ...]
    credential_ref: CredentialRef | None
    freshness_target: str
    read_only: bool = True

    def validate(self) -> None:
        if not self.read_only:
            raise ValueError("PFI Stage 1 data sources must be read-only.")
        if self.credential_ref is not None:
            self.credential_ref.validate()


@dataclass(frozen=True)
class Account:
    account_id: str
    source_id: str
    account_type: AccountType
    display_name: str
    currency: str
    lifecycle_state: str = "ACTIVE"


@dataclass(frozen=True)
class AssetInstrument:
    instrument_id: str
    asset_type: AssetType
    display_name: str
    currency: str
    symbol: str | None = None
    unit: str | None = None


@dataclass(frozen=True)
class ImportBatch:
    batch_id: str
    source_id: str
    acquired_at: str
    parser_version: str
    content_sha256: str
    raw_record_count: int


@dataclass(frozen=True)
class RawRecord:
    raw_id: str
    batch_id: str
    source_record_id: str
    payload_sha256: str
    raw_payload_ref: str


@dataclass(frozen=True)
class NormalizedTransaction:
    transaction_id: str
    source_id: str
    raw_id: str
    account_id: str
    event_type: LedgerEventType
    amount: float
    currency: str
    occurred_at: str
    description: str
    confidence: float
    review_state: str = "ACCEPTED"


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    transaction_id: str
    event_type: LedgerEventType
    account_id: str
    amount: float
    currency: str
    evidence_ref: str
    affects_consumption: bool
    affects_investment: bool


@dataclass(frozen=True)
class AccountSnapshot:
    snapshot_id: str
    account_id: str
    as_of: str
    balance: float
    currency: str
    source_id: str


@dataclass(frozen=True)
class HoldingSnapshot:
    snapshot_id: str
    account_id: str
    instrument_id: str
    as_of: str
    quantity: float
    market_value: float
    currency: str
    source_id: str


@dataclass(frozen=True)
class ValuationSnapshot:
    snapshot_id: str
    instrument_id: str
    as_of: str
    unit_price: float
    currency: str
    source_id: str


def default_stage1_sources() -> tuple[DataSource, ...]:
    return (
        DataSource(
            "alipay_daily",
            "Alipay",
            "支付宝日常账单",
            (DataSourceCapability.TRANSACTIONS, DataSourceCapability.STATEMENTS),
            (AcquisitionMode.CSV, AcquisitionMode.ZIP, AcquisitionMode.STATEMENT),
            CredentialRef("cred_alipay_read", (CredentialScope.READ_STATEMENT, CredentialScope.IMPORT_FILE)),
            "daily",
        ),
        DataSource(
            "alipay_fund",
            "Alipay Fund",
            "支付宝基金",
            (DataSourceCapability.TRANSACTIONS, DataSourceCapability.HOLDING_SNAPSHOT, DataSourceCapability.VALUATION),
            (AcquisitionMode.STATEMENT, AcquisitionMode.BROWSER_ASSISTED_READ, AcquisitionMode.MANUAL_SNAPSHOT),
            CredentialRef("cred_alipay_fund_read", (CredentialScope.READ_STATEMENT, CredentialScope.READ_POSITIONS)),
            "daily",
        ),
        DataSource(
            "moomoo_au",
            "Moomoo AU",
            "Moomoo AU",
            (DataSourceCapability.BALANCES, DataSourceCapability.POSITIONS, DataSourceCapability.ORDERS, DataSourceCapability.FILLS),
            (AcquisitionMode.OPEND_READ_ONLY, AcquisitionMode.API_READ_ONLY, AcquisitionMode.MANUAL_SNAPSHOT),
            CredentialRef("cred_moomoo_read", (CredentialScope.READ_BALANCE, CredentialScope.READ_POSITIONS, CredentialScope.READ_ORDERS, CredentialScope.READ_FILLS)),
            "intraday",
        ),
        DataSource(
            "cn_broker",
            "China Broker",
            "中国券商",
            (DataSourceCapability.BALANCES, DataSourceCapability.POSITIONS, DataSourceCapability.FILLS, DataSourceCapability.STATEMENTS),
            (AcquisitionMode.HTML, AcquisitionMode.PDF, AcquisitionMode.EXCEL, AcquisitionMode.MANUAL_SNAPSHOT),
            None,
            "daily",
        ),
        DataSource(
            "abc_bullion",
            "ABC Bullion",
            "ABC Bullion",
            (DataSourceCapability.HOLDING_SNAPSHOT, DataSourceCapability.STATEMENTS, DataSourceCapability.VALUATION),
            (AcquisitionMode.STATEMENT, AcquisitionMode.PDF, AcquisitionMode.HTML, AcquisitionMode.BROWSER_ASSISTED_READ, AcquisitionMode.MANUAL_SNAPSHOT),
            None,
            "weekly",
        ),
        DataSource(
            "cba_bank",
            "CBA",
            "CBA 银行",
            (DataSourceCapability.TRANSACTIONS, DataSourceCapability.BALANCES, DataSourceCapability.RECONCILIATION),
            (AcquisitionMode.CSV, AcquisitionMode.PDF, AcquisitionMode.WATCH_FOLDER),
            None,
            "daily",
        ),
        DataSource(
            "wechat_pay",
            "WeChat",
            "微信支付",
            (DataSourceCapability.TRANSACTIONS, DataSourceCapability.STATEMENTS),
            (AcquisitionMode.CSV, AcquisitionMode.ZIP, AcquisitionMode.EXCEL),
            None,
            "daily",
        ),
    )


def build_stage1_model_contract() -> dict[str, object]:
    return {
        "schema": "PFIV02Stage1CoreModelContractV1",
        "models": {
            "CredentialRef": "non-trading credential pointer with read/import scopes only",
            "DataSource": "where data is read from",
            "Account": "where money or liability is held",
            "AssetInstrument": "what asset is held",
            "ImportBatch": "dedupe and parser-version boundary for each ingest",
            "RawRecord": "source evidence pointer",
            "NormalizedTransaction": "normalized financial fact",
            "LedgerEvent": "ledger event used by investment, consumption, recommendation, and reports",
            "AccountSnapshot": "point-in-time account balance",
            "HoldingSnapshot": "point-in-time position state",
            "ValuationSnapshot": "point-in-time price or valuation state",
        },
        "ledger_event_types": [item.value for item in LedgerEventType],
        "account_types": [item.value for item in AccountType],
        "asset_types": [item.value for item in AssetType],
        "default_sources": [asdict(source) for source in default_stage1_sources()],
        "boundary": "No trading password, no write credential, no broker order submission.",
    }
