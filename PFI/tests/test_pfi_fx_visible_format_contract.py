from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_current_fx_badge_format_is_slash_date_not_compact_date() -> None:
    visible_files = (
        ROOT / "web" / "index.html",
        ROOT / "web" / "interconnection-map.html",
        ROOT / "web" / "pfi_v022_logic_review.html",
        ROOT / "web" / "pfi_v022_tag_views.html",
        ROOT / "config" / "pfi_parameters.yaml",
        ROOT / "docs" / "governance" / "STATUS.md",
        ROOT / "docs" / "pfi_v022" / "STAGE2_CNY_FX_GOVERNANCE.md",
    )
    forbidden = (
        "AUD/CNY=4.69（20260628--06:00）",
        "AUD/CNY=4.69（YYYYMMDD--HH:MM）",
        "CNY/AUD=4.70（YYYYMMDD--HH:MM）",
        "CNY/AUD=4.70（YYYY/MM/DD HH:MM）",
        "20260628--06:00",
        "YYYYMMDD--HH:MM",
    )

    for path in visible_files:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in text, f"{term} leaked in {path.relative_to(ROOT)}"

    index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    interconnection = (ROOT / "web" / "interconnection-map.html").read_text(encoding="utf-8")
    params = (ROOT / "config" / "pfi_parameters.yaml").read_text(encoding="utf-8")
    assert "AUD/CNY=4.69（2026/06/28 06:00）" in index
    assert "AUD/CNY=4.69（2026/06/28 06:00）" in interconnection
    assert "AUD/CNY=4.69（YYYY/MM/DD HH:MM）" in params

