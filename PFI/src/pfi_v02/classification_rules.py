from __future__ import annotations

from dataclasses import dataclass

from pfi_v02.core_models import AssetType, LedgerEventType


@dataclass(frozen=True)
class ClassificationInput:
    source_id: str
    description: str
    amount: float
    currency: str
    account_hint: str = ""
    counterparty_hint: str = ""


@dataclass(frozen=True)
class ClassificationResult:
    event_type: LedgerEventType
    affects_consumption: bool
    affects_investment: bool
    asset_type: AssetType | None
    review_state: str
    reason: str
    dedupe_key: str | None = None


TRANSFER_MARKERS = (
    "transfer",
    "转账",
    "bank transfer",
    "to moomoo",
    "moomoo deposit",
    "券商入金",
    "银证转账",
    "alipay to bank",
    "支付宝到银行",
)

FUND_MARKERS = (
    "fund subscription",
    "fund redemption",
    "基金申购",
    "基金赎回",
    "基金到账",
    "基金费用",
)

BULLION_MARKERS = (
    "abc bullion",
    "gold",
    "silver",
    "黄金",
    "白银",
    "bullion",
)

CREDIT_REPAYMENT_MARKERS = (
    "credit card repayment",
    "card repayment",
    "信用卡还款",
    "还款",
)


def classify_transaction(item: ClassificationInput) -> ClassificationResult:
    text = " ".join([item.source_id, item.description, item.account_hint, item.counterparty_hint]).lower()

    if any(marker in text for marker in CREDIT_REPAYMENT_MARKERS):
        return ClassificationResult(
            LedgerEventType.TRANSFER,
            affects_consumption=False,
            affects_investment=False,
            asset_type=AssetType.CREDIT,
            review_state="ACCEPTED",
            reason="Credit card repayment is a liability transfer, not a new consumption event.",
            dedupe_key=f"credit_repayment:{abs(item.amount):.2f}:{item.currency}",
        )

    if any(marker in text for marker in TRANSFER_MARKERS):
        return ClassificationResult(
            LedgerEventType.TRANSFER,
            affects_consumption=False,
            affects_investment="moomoo" in text or "券商" in text,
            asset_type=None,
            review_state="ACCEPTED",
            reason="Transfer between own accounts is excluded from ordinary consumption.",
            dedupe_key=f"transfer:{abs(item.amount):.2f}:{item.currency}",
        )

    if any(marker in text for marker in FUND_MARKERS):
        event_type = LedgerEventType.FUND
        return ClassificationResult(
            event_type,
            affects_consumption=False,
            affects_investment=True,
            asset_type=AssetType.FUND,
            review_state="ACCEPTED",
            reason="Fund subscription/redemption is classified as an investment fund event.",
            dedupe_key=None,
        )

    if any(marker in text for marker in BULLION_MARKERS):
        return ClassificationResult(
            LedgerEventType.BUY_ASSET if item.amount < 0 else LedgerEventType.SELL_ASSET,
            affects_consumption=False,
            affects_investment=True,
            asset_type=AssetType.BULLION,
            review_state="ACCEPTED",
            reason="Bullion purchase/sale is an investment asset event, not shopping consumption.",
            dedupe_key=None,
        )

    return ClassificationResult(
        LedgerEventType.CASH,
        affects_consumption=item.amount < 0,
        affects_investment=False,
        asset_type=AssetType.CASH,
        review_state="NEEDS_REVIEW" if abs(item.amount) >= 1000 else "ACCEPTED",
        reason="Default cash event; large or unclear items require review.",
        dedupe_key=None,
    )


def stage1_classification_fixtures() -> tuple[ClassificationInput, ...]:
    return (
        ClassificationInput("cba_bank", "CBA transfer to Moomoo brokerage", -5000.0, "AUD", "CBA", "Moomoo AU"),
        ClassificationInput("alipay_daily", "支付宝基金申购 易方达基金", -800.0, "CNY", "Alipay", "Alipay Fund"),
        ClassificationInput("abc_bullion", "ABC Bullion gold purchase", -1200.0, "AUD", "ABC Bullion", "Gold"),
        ClassificationInput("cba_bank", "Credit card repayment from CBA account", -2200.0, "AUD", "CBA", "Credit Card"),
    )
