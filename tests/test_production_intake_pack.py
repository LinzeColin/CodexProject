from pathlib import Path

from app.core.production_intake_pack import build_production_intake_pack
from tests.helpers import copy_sample_data, temp_settings


def test_production_intake_pack_writes_fill_ready_files(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    review_dir = settings.root_dir / "outputs" / "preflight"
    review_dir.mkdir(parents=True)
    (review_dir / "alipay_holdings_review_matrix.csv").write_text(
        "\n".join(
            [
                "asset_code,asset_name,current_amount,current_weight,unrealized_pnl,as_of,quality_status,stale_days,special_fund_rule_check_required,row_production_candidate,review_action,source_file",
                "ALIPAY_TEST,Test QDII,100,0.1,1,2026-06-05,video_visible,7,1,0,manual_review_required: stale_7_days; special_fund_rule_check_required,/Users/example/Downloads/video.mp4",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_production_intake_pack(settings)

    assert result["production_ready"] is True
    assert result["block_count"] == 0
    files = result["files"]
    for key in [
        "README",
        "field_guide",
        "evidence_guide",
        "alipay_positions_to_fill",
        "fund_rules_to_fill",
        "candidates_to_fill",
        "gap_actions",
        "review_prefill",
        "special_rule_checklist",
        "fund_rule_review_checklist",
        "candidate_source_review_prefill",
        "summary_json",
    ]:
        assert Path(files[key]).exists(), key

    alipay_text = Path(files["alipay_positions_to_fill"]).read_text(encoding="utf-8")
    assert "REPLACE_WITH_REAL_ALIPAY_EXPORT_OR_VERIFIED_CURRENT_HOLDINGS" in alipay_text

    readme = Path(files["README"]).read_text(encoding="utf-8")
    assert "Acceptance Commands" in readme
    assert "promote-intake-pack --apply" in readme
    assert "blocks placeholders" in readme
    evidence_guide = Path(files["evidence_guide"]).read_text(encoding="utf-8")
    assert "source-evidence-audit --pack-dir outputs/intake_pack" in evidence_guide
    assert "evidence/alipay_positions_YYYY-MM-DD.csv" in evidence_guide

    review_prefill = Path(files["review_prefill"]).read_text(encoding="utf-8")
    assert "ALIPAY_TEST" in review_prefill
    assert "REPLACE_WITH_CURRENT_ALIPAY_PAGE_CONFIRMATION" in review_prefill
    assert "/Users/" not in review_prefill
    assert "external:video.mp4" in review_prefill
    special_checklist = Path(files["special_rule_checklist"]).read_text(encoding="utf-8")
    assert "Test QDII" in special_checklist
    assert "/Users/" not in special_checklist
    fund_rule_checklist = Path(files["fund_rule_review_checklist"]).read_text(encoding="utf-8")
    assert "REPLACE_WITH_OFFICIAL_FUND_CODE_OR_PLATFORM_ID" in fund_rule_checklist
    assert "REPLACE_WITH_ALIPAY_OR_FUND_COMPANY_RULE_EVIDENCE" in fund_rule_checklist
    assert "QDII/HK/global/special funds" in fund_rule_checklist
    assert "/Users/" not in fund_rule_checklist
    candidate_prefill = Path(files["candidate_source_review_prefill"]).read_text(encoding="utf-8")
    assert "REPLACE_WITH_MOOMOO_OR_ALIPAY_CURRENT_SOURCE" in candidate_prefill
    assert "After verification, map into 03_candidates_to_fill.csv" in candidate_prefill
    assert "/Users/" not in candidate_prefill

    readme = Path(files["README"]).read_text(encoding="utf-8")
    assert str(settings.root_dir) not in readme
    gap_actions = Path(files["gap_actions"]).read_text(encoding="utf-8")
    assert str(settings.root_dir) not in gap_actions
    discovered = Path(files["discovered_files"]).read_text(encoding="utf-8")
    assert str(settings.root_dir) not in discovered
