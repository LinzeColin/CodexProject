from pathlib import Path

from app.core.fund_rule_normalizer import normalize_fund_rules
from tests.helpers import temp_settings


def test_normalize_fund_rules_supports_chinese_rule_csv_and_pack_evidence(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source = tmp_path / "基金规则.csv"
    source.write_text(
        "基金代码,申购状态,赎回状态,截止时间,确认时间,赎回到账,申购费率,赎回费率,申购费分档规则,赎回费分档规则,管理费率,托管费率,起购金额,支付宝交易可用性,MooMoo交易可用性,平台交易备注,来源\n"
        "FUND001,开放,开放,15:00,T+1,T+3,0.15%,0.50%,M<100万 0.15%,N<7天 0.50%,1.20%,0.20%,10,待支付宝交易页确认,MooMoo未验证交易,只作建议不参与排除,支付宝基金规则页\n",
        encoding="utf-8",
    )

    result = normalize_fund_rules(settings, csv_path=source, as_of="2026-06-13")

    assert result["status"] == "pass"
    assert result["row_count"] == 1
    assert result["evidence_ref"].startswith("evidence/")
    output = Path(str(result["output_csv"]))
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "FUND001" in text
    assert "0.0015" in text
    assert "0.005" in text
    assert "M<100万 0.15%" in text
    assert "N<7天 0.50%" in text
    assert "待支付宝交易页确认" in text
    assert "MooMoo未验证交易" in text
    assert "只作建议不参与排除" in text
    assert "alipay" in text
    assert "outputs/intake_pack/evidence" in result["copied_evidence_path"]


def test_normalize_fund_rules_requires_core_fields(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source = tmp_path / "fund-rules.csv"
    source.write_text("备注\nfoo\n", encoding="utf-8")

    result = normalize_fund_rules(settings, csv_path=source)

    assert result["status"] == "blocked"
    assert result["block_count"] >= 2
    assert any(issue["field"] == "asset_code" for issue in result["issues"])
    assert any(issue["field"] == "subscription_fee" for issue in result["issues"])
