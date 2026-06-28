from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable


STAGE3_SOURCE_TYPES = (
    "wallet",
    "bank",
    "broker",
    "fund_platform",
    "bullion_platform",
    "payment_platform",
    "manual_snapshot",
    "other",
)

STAGE3_CAPABILITIES = (
    "cash_ledger",
    "investment_trade",
    "fund_trade",
    "bullion_trade",
    "balance_snapshot",
    "fee",
    "refund",
    "transfer",
)

STAGE3_CAPABILITY_LABELS_ZH = {
    "cash_ledger": "现金流水",
    "investment_trade": "投资交易",
    "fund_trade": "基金交易",
    "bullion_trade": "黄金交易",
    "balance_snapshot": "余额快照",
    "fee": "费用",
    "refund": "退款",
    "transfer": "转账",
}

STAGE3_ACCOUNT_ROLES = (
    "main_wallet",
    "consumption_account",
    "investment_funding_source",
    "income_account",
    "investment_account",
    "asset_custody",
    "liability_account",
    "savings_account",
    "external_counterparty",
)

STAGE3_ACCOUNT_ROLE_LABELS_ZH = {
    "main_wallet": "主钱包",
    "consumption_account": "消费账户",
    "investment_funding_source": "投资入金来源",
    "income_account": "收入接收账户",
    "investment_account": "投资账户",
    "asset_custody": "资产托管账户",
    "liability_account": "负债账户",
    "savings_account": "储蓄账户",
    "external_counterparty": "外部对手方",
}

SOURCE_PROFILE_SCHEMA_FIELDS = (
    "source_id",
    "source_label_zh",
    "source_type",
    "supported_file_types",
    "capabilities",
    "account_roles_allowed",
    "parser_version",
    "role_effective_date_required",
)

ACCOUNT_ROLE_SCHEMA_FIELDS = (
    "account_id",
    "source_id",
    "role",
    "role_effective_from",
    "role_effective_to",
)

STAGE3_LEDGER_EVENT_TYPES = (
    "consumption",
    "investment_deposit",
    "fund_subscription",
    "bullion_purchase",
    "investment_buy",
    "investment_sell",
    "refund",
    "fee",
    "credit_card_repayment",
    "internal_transfer",
    "income",
    "valuation",
    "fx_conversion",
)


@dataclass(frozen=True)
class SourceProfile:
    source_id: str
    source_label_zh: str
    source_type: str
    supported_file_types: tuple[str, ...]
    capabilities: tuple[str, ...]
    account_roles_allowed: tuple[str, ...]
    parser_version: str
    role_effective_date_required: bool = True
    profile_status: str = "active"

    def validate(self) -> None:
        if self.source_type not in STAGE3_SOURCE_TYPES:
            raise ValueError(f"unsupported source_type: {self.source_type}")
        invalid_capabilities = set(self.capabilities) - set(STAGE3_CAPABILITIES)
        if invalid_capabilities:
            raise ValueError(f"unsupported capabilities: {sorted(invalid_capabilities)}")
        invalid_roles = set(self.account_roles_allowed) - set(STAGE3_ACCOUNT_ROLES)
        if invalid_roles:
            raise ValueError(f"unsupported account roles: {sorted(invalid_roles)}")
        if not self.role_effective_date_required:
            raise ValueError("role_effective_date_required must be true")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class AccountRoleAssignment:
    account_id: str
    source_id: str
    role: str
    role_effective_from: date
    role_effective_to: date | None = None

    def validate(self) -> None:
        if self.role not in STAGE3_ACCOUNT_ROLES:
            raise ValueError(f"unsupported role: {self.role}")
        if self.role_effective_to is not None and self.role_effective_to < self.role_effective_from:
            raise ValueError("role_effective_to cannot be earlier than role_effective_from")

    def active_on(self, event_date: date) -> bool:
        self.validate()
        if event_date < self.role_effective_from:
            return False
        if self.role_effective_to is not None and event_date > self.role_effective_to:
            return False
        return True

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "account_id": self.account_id,
            "source_id": self.source_id,
            "role": self.role,
            "role_effective_from": self.role_effective_from.isoformat(),
            "role_effective_to": self.role_effective_to.isoformat() if self.role_effective_to else None,
        }


@dataclass(frozen=True)
class RoleAwareLedgerEvent:
    event_id: str
    account_id: str
    event_date: date
    event_type: str
    amount_cny: Decimal
    affects_consumption: bool

    def validate(self) -> None:
        if self.event_type not in STAGE3_LEDGER_EVENT_TYPES:
            raise ValueError(f"unsupported event_type: {self.event_type}")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        payload = asdict(self)
        payload["event_date"] = self.event_date.isoformat()
        payload["amount_cny"] = str(self.amount_cny)
        return payload


def other_source_template() -> SourceProfile:
    return SourceProfile(
        source_id="other_source_template",
        source_label_zh="其它数据源模板",
        source_type="other",
        supported_file_types=("csv", "xlsx", "json", "pdf", "manual"),
        capabilities=("cash_ledger", "balance_snapshot", "fee", "refund", "transfer"),
        account_roles_allowed=(
            "main_wallet",
            "consumption_account",
            "income_account",
            "investment_funding_source",
            "savings_account",
            "external_counterparty",
        ),
        parser_version="profile-template-v1",
        role_effective_date_required=True,
        profile_status="template",
    )


def build_custom_source_profile(
    *,
    source_id: str,
    source_label_zh: str,
    source_type: str = "other",
    supported_file_types: Iterable[str] = ("csv",),
    capabilities: Iterable[str] = ("cash_ledger",),
    account_roles_allowed: Iterable[str] = ("consumption_account",),
    parser_version: str = "custom-profile-v1",
) -> SourceProfile:
    profile = SourceProfile(
        source_id=source_id,
        source_label_zh=source_label_zh,
        source_type=source_type,
        supported_file_types=tuple(supported_file_types),
        capabilities=tuple(capabilities),
        account_roles_allowed=tuple(account_roles_allowed),
        parser_version=parser_version,
        role_effective_date_required=True,
        profile_status="custom",
    )
    profile.validate()
    return profile


def build_stage3_source_profiles(extra_profiles: Iterable[SourceProfile] = ()) -> tuple[SourceProfile, ...]:
    profiles = (
        SourceProfile(
            "alipay_daily",
            "支付宝日常账单",
            "payment_platform",
            ("csv", "zip"),
            ("cash_ledger", "fee", "refund", "transfer"),
            ("main_wallet", "consumption_account", "income_account", "investment_funding_source", "external_counterparty"),
            "alipay-daily-v2",
        ),
        SourceProfile(
            "alipay_fund",
            "支付宝基金",
            "fund_platform",
            ("statement", "manual", "screenshot"),
            ("fund_trade", "balance_snapshot", "fee", "refund", "transfer"),
            ("investment_account", "investment_funding_source", "asset_custody"),
            "fund-profile-v1",
        ),
        SourceProfile(
            "moomoo_au",
            "Moomoo AU",
            "broker",
            ("csv", "pdf", "manual"),
            ("investment_trade", "balance_snapshot", "fee", "transfer"),
            ("investment_account", "investment_funding_source", "asset_custody"),
            "broker-profile-v1",
        ),
        SourceProfile(
            "cn_broker",
            "中国大陆券商",
            "broker",
            ("csv", "xlsx", "pdf", "manual"),
            ("investment_trade", "balance_snapshot", "fee", "transfer"),
            ("investment_account", "investment_funding_source", "asset_custody"),
            "cn-broker-profile-v1",
        ),
        SourceProfile(
            "abc_bullion",
            "ABC Bullion",
            "bullion_platform",
            ("statement", "pdf", "manual"),
            ("bullion_trade", "balance_snapshot", "fee", "transfer"),
            ("investment_account", "asset_custody"),
            "bullion-profile-v1",
        ),
        SourceProfile(
            "cba_bank",
            "CBA 银行",
            "bank",
            ("csv", "ofx"),
            ("cash_ledger", "balance_snapshot", "fee", "refund", "transfer"),
            ("main_wallet", "consumption_account", "income_account", "investment_funding_source", "savings_account"),
            "bank-profile-v1",
        ),
        SourceProfile(
            "wechat_pay",
            "微信支付",
            "wallet",
            ("csv", "xlsx", "zip"),
            ("cash_ledger", "fee", "refund", "transfer"),
            ("main_wallet", "consumption_account", "income_account", "investment_funding_source", "external_counterparty"),
            "wallet-profile-v1",
        ),
        SourceProfile(
            "manual_snapshot",
            "手工资产快照",
            "manual_snapshot",
            ("manual", "json", "xlsx"),
            ("balance_snapshot",),
            ("asset_custody", "investment_account", "main_wallet"),
            "manual-snapshot-v1",
        ),
        other_source_template(),
    )
    combined = profiles + tuple(extra_profiles)
    for profile in combined:
        profile.validate()
    return combined


def build_stage3_account_roles() -> tuple[AccountRoleAssignment, ...]:
    return (
        AccountRoleAssignment("acct_cba_main", "cba_bank", "main_wallet", date(2022, 1, 1)),
        AccountRoleAssignment("acct_cba_main", "cba_bank", "consumption_account", date(2022, 1, 1)),
        AccountRoleAssignment("acct_cba_main", "cba_bank", "investment_funding_source", date(2022, 1, 1)),
        AccountRoleAssignment("acct_cba_main", "cba_bank", "income_account", date(2022, 1, 1)),
        AccountRoleAssignment("acct_alipay_daily", "alipay_daily", "consumption_account", date(2022, 6, 1)),
        AccountRoleAssignment("acct_alipay_daily", "alipay_daily", "income_account", date(2022, 6, 1), date(2025, 12, 31)),
        AccountRoleAssignment("acct_moomoo_au", "moomoo_au", "investment_account", date(2023, 1, 1)),
        AccountRoleAssignment("acct_abc_bullion", "abc_bullion", "asset_custody", date(2024, 1, 1)),
        AccountRoleAssignment("acct_manual_snapshot", "manual_snapshot", "asset_custody", date(2026, 1, 1)),
        AccountRoleAssignment("acct_cba_savings", "cba_bank", "savings_account", date(2022, 1, 1)),
        AccountRoleAssignment("acct_external_counterparty", "wechat_pay", "external_counterparty", date(2022, 1, 1)),
    )


def roles_for_account(
    account_id: str,
    event_date: date,
    assignments: Iterable[AccountRoleAssignment] | None = None,
) -> tuple[str, ...]:
    records = assignments or build_stage3_account_roles()
    return tuple(
        record.role
        for record in records
        if record.account_id == account_id and record.active_on(event_date)
    )


def account_has_role(
    account_id: str,
    role: str,
    event_date: date,
    assignments: Iterable[AccountRoleAssignment] | None = None,
) -> bool:
    if role not in STAGE3_ACCOUNT_ROLES:
        raise ValueError(f"unsupported role: {role}")
    return role in roles_for_account(account_id, event_date, assignments)


def compute_consumption_total_cny(
    events: Iterable[RoleAwareLedgerEvent],
    assignments: Iterable[AccountRoleAssignment] | None = None,
) -> Decimal:
    total = Decimal("0")
    for event in events:
        event.validate()
        if event.affects_consumption and account_has_role(
            event.account_id,
            "consumption_account",
            event.event_date,
            assignments,
        ):
            total += event.amount_cny
    return total


def build_stage3_profile_contract() -> dict[str, object]:
    profiles = build_stage3_source_profiles()
    assignments = build_stage3_account_roles()
    return {
        "schema": "PFIV022Stage3SourceAccountProfileContractV1",
        "source_profile_schema_fields": SOURCE_PROFILE_SCHEMA_FIELDS,
        "source_types": STAGE3_SOURCE_TYPES,
        "capabilities": STAGE3_CAPABILITIES,
        "capability_labels_zh": STAGE3_CAPABILITY_LABELS_ZH,
        "account_role_schema_fields": ACCOUNT_ROLE_SCHEMA_FIELDS,
        "account_roles": STAGE3_ACCOUNT_ROLES,
        "account_role_labels_zh": STAGE3_ACCOUNT_ROLE_LABELS_ZH,
        "role_effective_date_required": True,
        "multiple_roles_per_account": True,
        "unknown_role_policy": "进入复核队列",
        "source_profiles": tuple(profile.to_dict() for profile in profiles),
        "account_role_assignments": tuple(assignment.to_dict() for assignment in assignments),
        "other_source_template": other_source_template().to_dict(),
        "calculation_policy": {
            "metric_basis": "role_and_event_type",
            "forbid_source_name_hardcode": True,
            "consumption_metric_rule": "sum events where affects_consumption=true and account has active consumption_account role",
        },
    }
