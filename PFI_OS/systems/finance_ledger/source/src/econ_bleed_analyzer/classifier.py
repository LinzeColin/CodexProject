from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .alipay import Transaction


@dataclass
class ClassifiedTransaction:
    transaction_time: str
    date: str
    hour: int
    transaction_type: str
    counterparty: str
    description: str
    direction: str
    amount: float
    amount_cents: int
    payment_method: str
    status: str
    order_id: str
    source_file: str
    source_platform: str
    primary_bucket: str
    main_category: str
    sub_category: str
    cash_flow_type: str
    risk_tags: str
    needs_review: bool
    mechanism: str
    risk_level: str
    rule_name: str
    classification_reason: str
    is_real_consumption: bool
    is_risk_spending: bool
    is_optimizable_spending: bool
    is_social_spending: bool
    is_financial_spending: bool
    is_business_personal_mixed: bool
    is_account_transfer: bool
    is_late_night: bool
    is_huabei_or_credit: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_rules(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _contains_any(haystack: str, needles: list[str] | None) -> bool:
    if not needles:
        return True
    folded = haystack.casefold()
    return any(needle.casefold() in folded for needle in needles if needle)


def _contains_all(haystack: str, needles: list[str] | None) -> bool:
    if not needles:
        return True
    folded = haystack.casefold()
    return all(needle.casefold() in folded for needle in needles if needle)


def _in_list(value: str, allowed: list[str] | None) -> bool:
    if not allowed:
        return True
    return any(value == item for item in allowed)


def _amount_match(amount_cents: int, rule: dict[str, Any]) -> bool:
    amount = amount_cents / 100
    if "amount_min" in rule and amount < float(rule["amount_min"]):
        return False
    if "amount_max" in rule and amount > float(rule["amount_max"]):
        return False
    return True


def _rule_matches(tx: Transaction, rule: dict[str, Any]) -> bool:
    combined = " ".join(
        [
            tx.transaction_type,
            tx.counterparty,
            tx.description,
            tx.direction,
            tx.payment_method,
            tx.status,
            tx.note,
        ]
    )
    if not _in_list(tx.direction, rule.get("directions")):
        return False
    if not _in_list(tx.transaction_type, rule.get("transaction_types")):
        return False
    if not _contains_any(tx.status, rule.get("status_keywords")):
        return False
    if not _contains_any(tx.payment_method, rule.get("method_keywords")):
        return False
    if not _contains_any(tx.counterparty, rule.get("counterparty_keywords")):
        return False
    if not _contains_any(tx.description, rule.get("description_keywords")):
        return False
    if not _contains_any(combined, rule.get("any_keywords")):
        return False
    if not _contains_all(combined, rule.get("all_keywords")):
        return False
    return _amount_match(tx.amount_cents, rule)


def _default_rule(tx: Transaction, rules: dict[str, Any]) -> dict[str, Any]:
    defaults = rules.get("default_buckets", {})
    return defaults.get(
        tx.direction,
        {
            "primary_bucket": "excluded",
            "mechanism": "未识别",
            "risk_level": "none",
            "reason": "无法识别交易方向",
        },
    )


def classify_transaction(tx: Transaction, rules: dict[str, Any]) -> ClassifiedTransaction:
    matched = None
    for rule in rules.get("rules", []):
        if _rule_matches(tx, rule):
            matched = rule
            break
    if matched is None:
        matched = _default_rule(tx, rules)

    bucket = matched["primary_bucket"]
    mechanism = matched["mechanism"]
    risk_level = matched["risk_level"]
    rule_name = matched.get("name", "default")
    main_category, sub_category = _category_for(tx, bucket, mechanism, rule_name)
    cash_flow_type = _cash_flow_type(tx, bucket, mechanism)

    combined_credit_text = f"{tx.transaction_type} {tx.counterparty} {tx.description} {tx.payment_method}"
    is_credit = any(token in combined_credit_text for token in ["花呗", "借呗", "信用卡", "分期", "备用金"])
    is_late_night = tx.transaction_time.hour >= 22 or tx.transaction_time.hour <= 5

    real_buckets = {"real_consumption", "optimizable_spending", "risk_spending", "social_spending", "business_personal_mixed"}
    is_successful_outflow = cash_flow_type == "expense"
    is_real_consumption = cash_flow_type == "expense" and main_category not in {"金融资金", "收入退款"}

    is_risk = (
        bucket == "risk_spending"
        or risk_level in {"medium", "high"}
        or (is_late_night and bucket in {"optimizable_spending", "risk_spending", "real_consumption"})
        or (is_credit and tx.direction == "支出")
    ) and is_successful_outflow
    risk_tags = _risk_tags(tx, main_category, sub_category, cash_flow_type, mechanism, is_credit, is_late_night)

    return ClassifiedTransaction(
        transaction_time=tx.transaction_time.strftime("%Y-%m-%d %H:%M:%S"),
        date=tx.transaction_time.date().isoformat(),
        hour=tx.transaction_time.hour,
        transaction_type=tx.transaction_type,
        counterparty=tx.counterparty,
        description=tx.description,
        direction=tx.direction,
        amount=tx.amount_yuan,
        amount_cents=tx.amount_cents,
        payment_method=tx.payment_method,
        status=tx.status,
        order_id=tx.order_id,
        source_file=tx.source_file,
        source_platform=tx.source_platform,
        primary_bucket=bucket,
        main_category=main_category,
        sub_category=sub_category,
        cash_flow_type=cash_flow_type,
        risk_tags="|".join(risk_tags),
        needs_review=cash_flow_type == "expense" and tx.amount_cents >= 1_000_000,
        mechanism=mechanism,
        risk_level=risk_level,
        rule_name=rule_name,
        classification_reason=matched.get("reason", ""),
        is_real_consumption=is_real_consumption,
        is_risk_spending=is_risk,
        is_optimizable_spending=bucket == "optimizable_spending",
        is_social_spending=bucket == "social_spending",
        is_financial_spending=bucket == "financial_spending",
        is_business_personal_mixed=bucket == "business_personal_mixed",
        is_account_transfer=bucket == "account_transfer",
        is_late_night=is_late_night,
        is_huabei_or_credit=is_credit,
    )


def classify_transactions(transactions: list[Transaction], rules: dict[str, Any]) -> list[ClassifiedTransaction]:
    classified = [classify_transaction(tx, rules) for tx in transactions]
    _mark_investment_impulse(classified)
    return classified


def _mark_investment_impulse(rows: list[ClassifiedTransaction]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        if row.is_financial_spending and row.mechanism == "流动性锁定" and "买入" in row.description:
            counts[row.date] = counts.get(row.date, 0) + 1

    for row in rows:
        if row.is_financial_spending and row.mechanism == "流动性锁定" and counts.get(row.date, 0) >= 3:
            row.mechanism = "投资冲动"
            row.risk_level = "high"
            row.is_risk_spending = True
            tags = [tag for tag in row.risk_tags.split("|") if tag]
            if "投资冲动" not in tags:
                tags.append("投资冲动")
            row.risk_tags = "|".join(tags)
            row.classification_reason = "同日基金/理财买入笔数较多，标记为投资冲动"


def _combined_text(tx: Transaction) -> str:
    return " ".join([tx.transaction_type, tx.counterparty, tx.description, tx.direction, tx.payment_method, tx.status, tx.note])


def _has_any(text: str, keywords: list[str]) -> bool:
    folded = text.casefold()
    return any(keyword.casefold() in folded for keyword in keywords)


def _cash_flow_type(tx: Transaction, bucket: str, mechanism: str) -> str:
    text = _combined_text(tx)
    if bucket == "excluded" or _has_any(tx.status, ["关闭", "失败", "已关闭"]):
        return "excluded"
    if bucket == "income_refund" or tx.direction == "收入" or _has_any(text, ["退款", "返现", "提现到账"]):
        return "income"
    if tx.transaction_type == "投资理财" and _has_any(text, ["卖出", "赎回", "收益"]):
        return "income"
    if bucket == "account_transfer":
        return "transfer"
    if bucket == "financial_spending":
        return "expense"
    if tx.direction == "支出":
        return "expense"
    if tx.direction == "不计收支":
        return "transfer"
    return "excluded"


def _category_for(tx: Transaction, bucket: str, mechanism: str, rule_name: str) -> tuple[str, str]:
    text = _combined_text(tx)
    if bucket == "excluded":
        return "收入退款", "失败关闭"
    if bucket == "income_refund" or tx.direction == "收入" or _has_any(text, ["退款", "返现"]):
        if _has_any(text, ["退款"]):
            return "收入退款", "退款"
        if _has_any(text, ["返现", "优惠", "红包"]):
            return "收入退款", "返现优惠"
        return "收入退款", "收入"

    if bucket == "financial_spending" or bucket == "account_transfer" or tx.transaction_type in {"投资理财", "信用借还", "保险", "账户存取"}:
        if _has_any(text, ["花呗", "借呗", "备用金", "网商贷", "信用卡", "分期", "还款"]):
            return "金融资金", "信用周转"
        if _has_any(text, ["保险", "寿险", "年金", "车险", "承保", "保费"]):
            return "金融资金", "保险保障"
        if bucket == "account_transfer" or _has_any(text, ["余额宝-单次转入", "余额宝-自动转入", "余额宝-转出", "转账收款到余额宝", "余额转入", "网商银行转入", "转出到银行卡", "转出到余额", "提现", "充值"]):
            return "金融资金", "账户搬运"
        return "金融资金", "基金理财"

    if bucket == "social_spending" or tx.transaction_type in {"亲友代付", "转账红包"} or _has_any(text, ["亲情卡", "代付", "请客", "小荷包", "人情"]):
        if _has_any(text, ["小荷包", "家庭", "老婆", "孩子"]):
            return "社交家庭", "家庭共同支出"
        social_detail = " ".join([tx.counterparty, tx.description, tx.note])
        if tx.amount_cents < 1_000_000 and _has_any(social_detail, ["红包"]):
            return "社交家庭", "红包转账"
        return "社交家庭", "亲情卡人情往来"

    if bucket in {"optimizable_spending", "risk_spending"}:
        if _has_any(text, ["会员", "订阅", "自动续费", "月卡", "年卡", "VIP", "话费", "手机充值", "联通", "移动", "电信", "App Store", "Apple Music", "WPS 365"]):
            return "可优化消费", "会员订阅"
        if _has_any(text, ["奶茶", "咖啡", "瑞幸", "星巴克", "茶", "便利店", "罗森", "全家", "711", "小吃"]):
            return "可优化消费", "便利饮品"
        if _has_any(text, ["淘宝", "天猫", "京东", "拼多多", "得物", "数码", "电器", "服饰", "美妆", "美容", "盲盒", "手办", "潮玩", "Chanel", "奢侈", "奢侈品"]):
            return "可优化消费", "低复购购物"
        return "可优化消费", "外卖即时零售"

    if _has_any(text, ["物业", "水费", "电费", "燃气", "供电", "住房", "房租", "宽带"]):
        return "生活刚需", "住房缴费"
    if _has_any(text, ["医疗", "药", "医院", "诊所", "健康", "教育", "学校", "学费"]):
        return "生活刚需", "教育医疗"
    if tx.transaction_type in {"交通出行", "爱车养车"} or _has_any(text, ["高速", "ETC", "停车", "加油", "铁路", "12306", "公交", "地铁", "出行", "车"]):
        return "生活刚需", "交通车辆"
    return "生活刚需", "餐饮日用"


def _risk_tags(
    tx: Transaction,
    main_category: str,
    sub_category: str,
    cash_flow_type: str,
    mechanism: str,
    is_credit: bool,
    is_late_night: bool,
) -> list[str]:
    if cash_flow_type != "expense":
        return []

    text = _combined_text(tx)
    tags: list[str] = []
    if is_credit:
        tags.append("信用工具")
    if is_late_night and main_category != "生活刚需":
        tags.append("夜间冲动")
    if main_category == "可优化消费":
        if sub_category == "外卖即时零售":
            tags.append("平台便利")
        elif sub_category == "便利饮品":
            tags.append("高频小额")
        elif sub_category == "会员订阅":
            tags.append("长期扣费")
        else:
            tags.append("低复购购物")
    if main_category == "社交家庭":
        tags.append("社交家庭")
    if main_category == "金融资金":
        if sub_category == "信用周转":
            tags.append("信用周转")
        elif sub_category == "基金理财":
            tags.append("流动性锁定")
        elif sub_category == "保险保障":
            tags.append("长期扣费")
        else:
            tags.append("账户搬运")
    if _has_any(text, ["办公", "发票", "报销", "差旅", "商旅", "经营码", "商业协作", "WPS"]):
        tags.append("工作经营")
    if tx.amount_cents <= 8000 and main_category in {"可优化消费", "生活刚需"}:
        tags.append("小额频繁")
    if not tags:
        tags.append("基础支出")

    deduped: list[str] = []
    for tag in tags:
        if tag not in deduped:
            deduped.append(tag)
    return deduped
