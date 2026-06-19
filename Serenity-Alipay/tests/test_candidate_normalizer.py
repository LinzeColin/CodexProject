from pathlib import Path

from app.core.candidate_normalizer import normalize_candidates
from tests.helpers import temp_settings


def test_normalize_candidates_supports_chinese_candidate_csv_and_pack_evidence(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source = tmp_path / "候选池.csv"
    source.write_text(
        "基金代码,基金名称,市场,基金公司,风险等级,主题,来源,来源类型,官方来源数,日期\n"
        "FUND001,测试AI成长基金,CN/US,测试基金公司,高风险,AI infrastructure,支付宝基金详情页,支付宝,2,2026-06-13\n",
        encoding="utf-8",
    )

    result = normalize_candidates(settings, csv_path=source)

    assert result["status"] == "pass"
    assert result["row_count"] == 1
    assert result["evidence_ref"].startswith("evidence/")
    output = Path(str(result["output_csv"]))
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "FUND001" in text
    assert "测试AI成长基金" in text
    assert "off_platform_fund" in text
    assert "alipay" in text
    assert "evidence/" in text
    assert "outputs/intake_pack/evidence" in result["copied_evidence_path"]


def test_normalize_candidates_excludes_conservative_assets(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source = tmp_path / "候选池.csv"
    source.write_text(
        "基金代码,基金名称,市场,基金公司,主题,官方来源数,日期\n"
        "BOND001,稳健债券基金,CN,测试基金公司,债券,2,2026-06-13\n",
        encoding="utf-8",
    )

    result = normalize_candidates(settings, csv_path=source)

    assert result["status"] == "pass"
    output = Path(str(result["output_csv"]))
    text = output.read_text(encoding="utf-8")
    assert "bond_fund" in text
    assert "true" in text
    assert "conservative asset exclusion" in text


def test_normalize_candidates_requires_core_fields(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source = tmp_path / "candidates.csv"
    source.write_text("备注\nfoo\n", encoding="utf-8")

    result = normalize_candidates(settings, csv_path=source)

    assert result["status"] == "blocked"
    assert result["block_count"] >= 3
    assert any(issue["field"] == "asset_code" for issue in result["issues"])
    assert any(issue["field"] == "asset_name" for issue in result["issues"])
    assert any(issue["field"] == "as_of" for issue in result["issues"])
