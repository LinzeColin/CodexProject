import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STREAMLIT_APP = PROJECT_ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py"


def test_streamlit_root_data_paths_are_explicitly_classified():
    source = STREAMLIT_APP.read_text(encoding="utf-8")
    top_level_dirs = set(re.findall(r'ROOT / "data" / "([^"]+)"', source))

    assert top_level_dirs == {"cache", "commandCenter", "reportDecision", "strategyLibrary", "validationQueue"}


def test_streamlit_private_user_inputs_do_not_write_public_data_ledgers():
    source = STREAMLIT_APP.read_text(encoding="utf-8")

    forbidden = [
        'ROOT / "data" / "cashflow"',
        'ROOT / "data" / "policy"',
        'ROOT / "data" / "consumption"',
        'ROOT / "data" / "holdings"',
        'ROOT / "data" / "systemAudit"',
        'ROOT / "data" / "vectorized"',
        'ROOT / "data" / "cache" / "_uploaded.csv"',
        "CompanyCashFlowEntries.json",
        "PolicyOpportunityEntries.json",
        "ConsumptionGuardEvents.json",
    ]
    for pattern in forbidden:
        assert pattern not in source


def test_uploaded_market_csv_uses_private_runtime_uploads():
    source = STREAMLIT_APP.read_text(encoding="utf-8")

    assert "_private_runtime_upload_path" in source
    assert 'default_data_home() / "runtime" / "uploads"' in source
    assert "market_bars_" in source
    assert "csv_file.read()" in source
