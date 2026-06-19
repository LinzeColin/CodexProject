from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.core.intake_bundle_normalizer import normalize_intake_bundle
from app.core.production_intake_pack import build_production_intake_pack
from tests.helpers import copy_sample_data, temp_settings


def _today() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def test_normalize_intake_bundle_writes_pack_and_dry_runs_promotion(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    build_production_intake_pack(settings)
    today = _today()
    alipay = tmp_path / "alipay.csv"
    alipay.write_text(
        "基金代码,基金名称,持有金额,持仓占比,持有收益,日期\n"
        f"FUND001,AI Infrastructure Growth Fund,10000,100%,500,{today}\n",
        encoding="utf-8",
    )
    rules = tmp_path / "fund_rules.csv"
    rules.write_text(
        "基金代码,申购状态,赎回状态,截止时间,确认时间,赎回到账,申购费率,赎回费率,申购费分档规则,赎回费分档规则,管理费率,托管费率,起购金额,来源,日期\n"
        f"FUND001,开放,开放,15:00,T+1,T+3,0.10%,0.50%,M<100万元 0.10%,N<7天 0.50%；N>=7天 0.00%,1.20%,0.20%,10,支付宝基金规则页,{today}\n",
        encoding="utf-8",
    )
    candidates = tmp_path / "candidates.csv"
    candidates.write_text(
        "基金代码,基金名称,市场,基金公司,风险等级,主题,来源,来源类型,官方来源数,日期\n"
        f"FUND001,AI Infrastructure Growth Fund,CN/US,Verified Fund Co,high,AI infrastructure,基金公司官网,official,2,{today}\n",
        encoding="utf-8",
    )

    result = normalize_intake_bundle(
        settings,
        alipay_csv=alipay,
        fund_rules_csv=rules,
        candidates_csv=candidates,
        write_pack=True,
    )

    assert result["status"] == "pass"
    assert result["production_files_touched"] is False
    assert result["mail_sent"] is False
    assert result["trades_placed"] is False
    stages = {stage["name"]: stage for stage in result["stages"]}
    assert stages["source_evidence_audit_pack"]["status"] == "pass"
    assert stages["promote_intake_pack_dry_run"]["status"] == "pass"
    assert stages["promote_intake_pack_dry_run"]["summary"]["production_ready"] is True
    assert (settings.root_dir / "outputs" / "intake_pack" / "01_alipay_positions_to_fill.csv").read_text(encoding="utf-8").find("FUND001") >= 0
    assert (settings.imports_dir / "alipay_positions.csv").read_text(encoding="utf-8").find("sample") >= 0


def test_normalize_intake_bundle_requires_input_source(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    result = normalize_intake_bundle(settings, write_pack=True)

    assert result["status"] == "blocked"
    assert result["production_files_touched"] is False
    stages = {stage["name"]: stage for stage in result["stages"]}
    assert stages["input_check"]["status"] == "block"
