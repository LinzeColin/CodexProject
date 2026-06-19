from pathlib import Path

from app.core.production_unblock_matrix import build_production_unblock_matrix
from tests.helpers import copy_sample_data, temp_settings


def test_production_unblock_matrix_maps_current_gaps_to_evidence_requirements(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    rules_path = settings.manual_dir / "fund_rules.csv"
    rules_text = rules_path.read_text(encoding="utf-8")
    rules_path.write_text(rules_text.replace("https://", "REPLACE_https://", 1), encoding="utf-8")

    result = build_production_unblock_matrix(settings)

    assert result["production_ready"] is False
    assert result["block_count"] > 0
    assert result["row_count"] >= result["block_count"]
    assert result["area_counts"]["fund_rules"] > 0

    csv_text = Path(result["files"]["csv"]).read_text(encoding="utf-8")
    assert "outputs/intake_pack/08_fund_rules_from_review_checklist.csv" in csv_text
    assert "source_type must be moomoo/alipay/official" in csv_text

    md_text = Path(result["files"]["markdown"]).read_text(encoding="utf-8")
    assert "Production remains locked" in md_text
    assert "validate-intake --scan-path ~/Downloads --scan-path ~/Documents --require-production --json" in md_text
    assert "preflight --scan-path ~/Downloads --scan-path ~/Documents --require-production --json" in md_text
