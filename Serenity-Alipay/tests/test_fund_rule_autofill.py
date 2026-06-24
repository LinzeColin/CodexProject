from tests.test_scoring import _candidate

from app.core.fund_rule_autofill import parse_fund_rule_from_fee_page


def test_parse_fund_rule_from_eastmoney_fee_page_html():
    html = """
    <td>买入确认日</td><td>T+2</td><td>卖出确认日</td><td>T+5</td>
    <td>管理费率</td><td>1.20%（每年）</td>
    <td>托管费率</td><td>0.20%（每年）</td>
    <td>销售服务费率</td><td>0.40%（每年）</td>
    <h4><label>申购费率</label></h4>
    <table><tbody><tr><td>M&lt;100万元</td><td>1.00%</td></tr><tr><td>M≥100万元</td><td>1000元/笔</td></tr></tbody></table>
    <h4><label>赎回费率</label></h4>
    <table><tbody><tr><td>小于7天</td><td>1.50%</td></tr><tr><td>大于等于7天</td><td>0.00%</td></tr></tbody></table>
    注：
    """

    rule = parse_fund_rule_from_fee_page(
        _candidate(asset_code="016668", asset_name="测试半导体基金"),
        html,
        as_of="2026-06-24T12:00:00+08:00",
        source_url="https://fundf10.eastmoney.com/jjfl_016668.html",
    )

    assert rule.subscription_status == "open"
    assert rule.redemption_status == "open"
    assert rule.confirm_lag == "T+2"
    assert rule.redeem_lag == "T+5"
    assert rule.subscription_fee == 0.01
    assert rule.redemption_fee == 0.015
    assert rule.management_fee == 0.012
    assert rule.custody_fee == 0.002
    assert rule.sales_service_fee == 0.004
    assert "M<100万元 1.00%" in rule.subscription_fee_schedule
    assert "小于7天 1.50%" in rule.redemption_fee_schedule
