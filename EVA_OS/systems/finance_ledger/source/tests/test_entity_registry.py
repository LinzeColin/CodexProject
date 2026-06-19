from __future__ import annotations

from econ_bleed_analyzer.classifier import ClassifiedTransaction
from econ_bleed_analyzer.entity_registry import build_entity_layer, entity_registry_report_markdown


def _row(counterparty: str, *, amount: float = 100.0, needs_review: bool = False) -> ClassifiedTransaction:
    return ClassifiedTransaction(
        transaction_time="2026-01-01 10:00:00",
        date="2026-01-01",
        hour=10,
        transaction_type="购物",
        counterparty=counterparty,
        description="测试",
        direction="支出",
        amount=amount,
        amount_cents=int(amount * 100),
        payment_method="支付宝",
        status="交易成功",
        order_id=f"order-{counterparty}",
        source_file="sample.csv",
        source_platform="alipay",
        primary_bucket="real_consumption",
        main_category="生活刚需",
        sub_category="餐饮日用",
        cash_flow_type="expense",
        risk_tags="餐饮日用|基础支出",
        needs_review=needs_review,
        mechanism="基础消费",
        risk_level="low",
        rule_name="demo",
        classification_reason="demo",
        is_real_consumption=True,
        is_risk_spending=False,
        is_optimizable_spending=False,
        is_social_spending=False,
        is_financial_spending=False,
        is_business_personal_mixed=False,
        is_account_transfer=False,
        is_late_night=False,
        is_huabei_or_credit=False,
    )


def test_entity_layer_builds_registry_and_aliases():
    layer = build_entity_layer([_row("美团外卖"), _row("美团 外卖", amount=200.0, needs_review=True)])
    registry = layer["entity_registry"]
    aliases = layer["alias_map"]
    summary = layer["entity_registry_summary"]

    counterparty_entities = [row for row in registry if row["entity_type"] == "counterparty"]
    assert len(counterparty_entities) == 1
    assert counterparty_entities[0]["review_required"] == "true"
    assert counterparty_entities[0]["decision_grade"] == "Watch"
    assert any(row["entity_type"] == "risk_tag" for row in registry)
    assert len(aliases) >= len(registry)
    assert any(row["entity_type"] == "counterparty" for row in summary)


def test_entity_registry_report_contains_machine_contract():
    layer = build_entity_layer([_row("瑞幸咖啡")])
    report = entity_registry_report_markdown(
        layer["entity_registry"],
        layer["alias_map"],
        layer["entity_registry_summary"],
    )

    assert "audit/entity_registry.csv" in report
    assert "v_entity_alias_conflicts" in report
    assert "证据等级" in report
