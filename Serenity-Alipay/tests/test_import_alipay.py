from pathlib import Path

import pytest

from app.adapters.alipay_importer import read_positions_csv


def test_valid_alipay_csv_imports(tmp_path: Path):
    csv_path = tmp_path / "positions.csv"
    csv_path.write_text(
        "asset_code,asset_name,platform,current_amount,current_weight,cost_basis,unrealized_pnl,as_of,source_note\n"
        "FUND001,Fund One,Alipay,1000,50%,900,100,2026-06-12,manual\n"
        "FUND002,Fund Two,Alipay,1000,0.50,1000,0,2026-06-12,manual\n",
        encoding="utf-8",
    )
    result = read_positions_csv(csv_path)
    assert len(result.rows) == 2
    assert result.rows[0]["current_weight"] == 0.5
    assert result.warnings == []


def test_missing_alipay_column_fails(tmp_path: Path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("asset_code,asset_name\nFUND001,Fund One\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        read_positions_csv(csv_path)
