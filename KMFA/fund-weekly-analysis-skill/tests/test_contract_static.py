from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_required_files_exist():
    for rel in [
        "README.md", "SKILL.md", "references/runbook.md", "references/configuration.md",
        "references/operating_contract.md", "references/source_of_truth_contract.md",
        "references/validation_checks.md", "references/excel_master_review_checklist.md",
        "templates/excel_sheet_spec.yaml",
        "automation/weekly_mon_sat_1100_sydney.prompt.md",
        "templates/资金与税费管理母版_真实数据预览_v2.xlsx",
    ]:
        assert (ROOT / rel).exists(), rel

def test_skill_has_no_branch_rule():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "Do not create branches" in text
    assert "main" in text
    assert "Australia/Sydney" in text
    assert "11:00" in text
    assert "Monday and Saturday" in text
    assert "No simulation" in text or "simulated" in text

def test_excel_template_exists():
    assert (ROOT / "templates/资金与税费管理母版_真实数据预览_v2.xlsx").exists()
