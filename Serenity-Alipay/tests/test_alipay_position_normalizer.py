from pathlib import Path

from app.core.alipay_position_normalizer import normalize_alipay_positions
from tests.helpers import temp_settings


def test_normalize_alipay_positions_supports_chinese_csv_and_pack_evidence(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source = tmp_path / "支付宝持仓.csv"
    source.write_text(
        "\n".join(
            [
                "基金名称,持有金额,持仓占比,持有收益",
                "测试成长基金,1,234.56,12.5%,23.45",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    # Rewrite with quoted amount so csv parsing keeps the comma in the amount.
    source.write_text("基金名称,持有金额,持仓占比,持有收益\n测试成长基金,\"1,234.56\",12.5%,23.45\n", encoding="utf-8")

    result = normalize_alipay_positions(settings, csv_path=source, as_of="2026-06-13")

    assert result["status"] == "pass"
    assert result["row_count"] == 1
    assert result["evidence_ref"].startswith("evidence/")
    output = Path(str(result["output_csv"]))
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "测试成长基金" in text
    assert "0.125" in text
    assert "evidence=" in text
    assert "outputs/intake_pack/evidence" in result["copied_evidence_path"]


def test_normalize_alipay_positions_requires_core_fields(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source = tmp_path / "alipay.csv"
    source.write_text("备注\nfoo\n", encoding="utf-8")

    result = normalize_alipay_positions(settings, csv_path=source)

    assert result["status"] == "blocked"
    assert result["block_count"] >= 2
    assert any(issue["field"] == "asset_name" for issue in result["issues"])
    assert any(issue["field"] == "current_amount" for issue in result["issues"])
