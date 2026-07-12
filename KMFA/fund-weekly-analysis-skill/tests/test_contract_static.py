from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_required_files_exist():
    for rel in [
        "README.md", "SKILL.md", "references/runbook.md", "references/configuration.md",
        "references/operating_contract.md", "references/source_of_truth_contract.md",
        "references/validation_checks.md", "references/excel_master_review_checklist.md",
        "references/owner_review_handoff.md",
        "templates/excel_sheet_spec.yaml",
        "tools/check_delivery_acceptance.py",
        "automation/weekly_mon_sat_1100_sydney.prompt.md",
    ]:
        assert (ROOT / rel).exists(), rel

def test_skill_has_no_branch_rule():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "Do not create branches" in text
    assert "main" in text
    assert "Australia/Sydney" in text
    assert "11:00" in text
    assert "Monday" in text
    assert "Saturday" in text
    assert "No simulation" in text or "simulated" in text
    assert "资金与税费管理报告_<run_id>.pdf" in text
    assert "user-facing deliverables" in text
    assert "check_delivery_acceptance.py" in text
    assert "DELIVERY_ACCEPTANCE_READY_WITH_OWNER_BLOCKERS" in text

def test_excel_template_exists():
    assert not list((ROOT / "templates").glob("*.xlsx"))
    runner = (ROOT / "tools/run_fund_weekly_analysis.py").read_text(encoding="utf-8")
    assert "PRIVATE_TEMPLATE_MISSING" in runner
    assert "KMFA_FUND_TEMPLATE_PATH" in runner
