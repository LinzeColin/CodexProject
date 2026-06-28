from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pfi_v02.stage_v022_source_profile import (
    STAGE3_ACCOUNT_ROLE_LABELS_ZH,
    STAGE3_ACCOUNT_ROLES,
    build_custom_source_profile,
    build_stage3_profile_contract,
    roles_for_account,
)


ROOT = Path(__file__).resolve().parents[1]
REVIEW_REPORT = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE3_REVIEW_20260628.md"

STAGE3_TASK_IDS = (
    "S3-P1-T1",
    "S3-P1-T2",
    "S3-P1-T3",
    "S3-P2-T1",
    "S3-P2-T2",
    "S3-P2-T3",
)

STOP_CONDITIONS = (
    "新增数据源必须改核心代码时停止",
    "数据源能力写死在名称里时停止",
    "无法添加新 source 时停止",
    "一个账户只能有一个角色时停止",
    "角色历史无法追踪时停止",
    "公式按 source 名称写死时停止",
)

TASKPACK_DEFAULT_ROLE_LABELS = (
    "主钱包",
    "消费账户",
    "投资入金来源",
    "投资账户",
    "收入接收账户",
    "负债账户",
    "储蓄账户",
    "外部对手方",
)


def test_stage3_review_report_covers_acceptance_fixes_and_stop_conditions() -> None:
    text = REVIEW_REPORT.read_text(encoding="utf-8")

    assert "v0.2.2 Stage 3 复审并解决" in text
    assert "本轮只复审解决 Stage 3" in text
    assert "不复审 Stage 4-13" in text
    assert "复审结论：通过" in text
    assert "上线阻塞项：0" in text
    assert "修复 1：补齐 taskpack 默认账户角色" in text
    assert "修复 2：新增 source profile 角色扩展示例" in text

    for task_id in STAGE3_TASK_IDS:
        assert task_id in text
    for stop_condition in STOP_CONDITIONS:
        assert stop_condition in text
    for role_label in TASKPACK_DEFAULT_ROLE_LABELS:
        assert role_label in text

    required_evidence_terms = (
        "PFI/src/pfi_v02/stage_v022_source_profile.py",
        "PFI/config/pfi_parameters.yaml",
        "PFI/tests/test_v022_stage3_source_account_profiles.py",
        "PFI/tests/test_v022_review_stage3.py",
        "验证命令",
        "证据来源",
        "停止条件复核",
        "剩余风险",
    )
    for term in required_evidence_terms:
        assert term in text


def test_stage3_account_roles_cover_taskpack_default_labels() -> None:
    assert "savings_account" in STAGE3_ACCOUNT_ROLES
    assert "external_counterparty" in STAGE3_ACCOUNT_ROLES
    assert STAGE3_ACCOUNT_ROLE_LABELS_ZH["income_account"] == "收入接收账户"
    assert STAGE3_ACCOUNT_ROLE_LABELS_ZH["savings_account"] == "储蓄账户"
    assert STAGE3_ACCOUNT_ROLE_LABELS_ZH["external_counterparty"] == "外部对手方"

    profile_contract = build_stage3_profile_contract()
    labels = set(profile_contract["account_role_labels_zh"].values())
    for role_label in TASKPACK_DEFAULT_ROLE_LABELS:
        assert role_label in labels


def test_stage3_parameter_catalog_exposes_extended_roles() -> None:
    catalog = json.loads((ROOT / "config" / "pfi_parameters.yaml").read_text(encoding="utf-8"))
    account_roles = catalog["parameters"]["account_roles"]

    role_registry = account_roles["role_registry"]["value"]
    schema_roles = account_roles["account_role_schema"]["roles"]
    role_labels = account_roles["role_labels_zh"]

    for role in ("savings_account", "external_counterparty"):
        assert role in role_registry
        assert role in schema_roles
    assert role_labels["income_account"] == "收入接收账户"
    assert role_labels["savings_account"] == "储蓄账户"
    assert role_labels["external_counterparty"] == "外部对手方"


def test_stage3_future_source_can_use_savings_and_external_counterparty_roles() -> None:
    custom = build_custom_source_profile(
        source_id="family_savings_and_counterparty",
        source_label_zh="家庭储蓄与外部对手方",
        source_type="other",
        supported_file_types=("csv", "manual"),
        capabilities=("cash_ledger", "transfer"),
        account_roles_allowed=("savings_account", "external_counterparty"),
    )

    assert custom.source_type == "other"
    assert "savings_account" in custom.account_roles_allowed
    assert "external_counterparty" in custom.account_roles_allowed

    savings_roles = roles_for_account("acct_cba_savings", date(2026, 6, 28))
    counterparty_roles = roles_for_account("acct_external_counterparty", date(2026, 6, 28))
    assert "savings_account" in savings_roles
    assert "external_counterparty" in counterparty_roles
