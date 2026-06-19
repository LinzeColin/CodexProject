from pathlib import Path

from app.core.holdings_discovery import discover_holdings
from tests.helpers import temp_settings


def test_discover_holdings_converts_quantlab_candidate(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    csv_path = source_dir / "HoldingsBook.csv"
    csv_path.write_text(
        "\n".join(
            [
                "source_system,source_file,symbol,name,market,asset_type,quantity,cost_basis,position_value,unrealized_pnl,weight,updated_at,source_modified_time,quality_status,notes",
                "AlipayVideo,video.mp4,,Test Fund,CN,fund,0,90,100,10,1.0,2026-06-12T12:00:00+08:00,2026-06-12T12:00:00+08:00,video_visible,evidence",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = discover_holdings(settings, [source_dir])

    assert result["production_ready_candidate_found"] is True
    assert result["converted_candidate_csv"]
    converted = Path(str(result["converted_candidate_csv"]))
    assert converted.exists()
    assert "Test Fund" in converted.read_text(encoding="utf-8")
    assert result["review_matrix_csv"]
    review_matrix = Path(str(result["review_matrix_csv"]))
    assert review_matrix.exists()
    assert "row_production_candidate" in review_matrix.read_text(encoding="utf-8")
    markdown = Path(str(result["markdown_path"])).read_text(encoding="utf-8")
    assert settings.root_dir.as_posix() not in markdown
    assert "/Users/" not in markdown
    assert "source/HoldingsBook.csv" in markdown


def test_discover_holdings_review_matrix_flags_special_funds(tmp_path: Path):
    settings = temp_settings(tmp_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    csv_path = source_dir / "HoldingsBook.csv"
    csv_path.write_text(
        "\n".join(
            [
                "source_system,source_file,symbol,name,market,asset_type,quantity,cost_basis,position_value,unrealized_pnl,weight,updated_at,source_modified_time,quality_status,notes",
                "AlipayVideo,video.mp4,,QDII Fund QDII,CN,fund,0,90,100,10,1.0,2026-06-12T12:00:00+08:00,2026-06-12T12:00:00+08:00,video_visible,evidence",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = discover_holdings(settings, [source_dir])

    assert result["review_summary"]["special_fund_rule_check_required_count"] == 1
    assert result["review_summary"]["row_production_candidate_count"] == 0
    matrix = Path(str(result["review_matrix_csv"])).read_text(encoding="utf-8")
    assert "special_fund_rule_check_required" in matrix
