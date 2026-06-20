from pathlib import Path

from pfi_os.application import (
    PFI007_RESEARCH_POLICY_ACCEPTANCE_SCHEMA,
    PFI007_RESEARCH_POLICY_UI_READ_MODEL_SCHEMA,
    OperationalStore,
    build_pfi007_research_policy_golden_fixture,
    build_pfi007_research_policy_ui_read_model,
    build_research_policy_workflow,
    record_research_policy_workflow,
    rollback_pfi007_research_policy_records,
    run_pfi007_research_policy_acceptance,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pfi007_acceptance_runs_policy_citation_report_task_evidence_and_rollback_chain():
    payload = run_pfi007_research_policy_acceptance()

    assert payload["schema"] == PFI007_RESEARCH_POLICY_ACCEPTANCE_SCHEMA
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["pass"] >= 14
    check_names = {row["name"] for row in payload["checks"]}
    for required in {
        "DataChain:PolicyRadar",
        "Domain:ReportGapTasks",
        "API:UIReadModel",
        "UI:ChineseJourney",
        "CitationLocator:OfficialSource",
        "ReportManifest:Present",
        "TasksEvidence:Source",
        "TasksEvidence:Evidence",
        "TasksEvidence:Job",
        "TasksEvidence:ReviewTask",
        "Decision:ReviewOnly",
        "Safety:NoExecution",
        "GoldenMetrics:StableWorkflow",
        "RollbackProof",
    }:
        assert required in check_names
    assert payload["ui_read_model"]["schema"] == PFI007_RESEARCH_POLICY_UI_READ_MODEL_SCHEMA
    assert payload["rollback_proof"]["status"] == "Pass"
    assert payload["safety_boundary"] == {
        "research_only": True,
        "provider_fetch_required": False,
        "government_portal_required": False,
        "broker_required": False,
        "llm_required": False,
        "no_live_trading": True,
        "no_broker_calls": True,
        "no_order_execution": True,
        "no_government_portal_action": True,
        "no_legal_or_tax_advice": True,
        "no_private_holdings_used": True,
        "human_review_required": True,
    }


def test_pfi007_golden_metrics_are_deterministic_and_review_only():
    first = run_pfi007_research_policy_acceptance()
    second = run_pfi007_research_policy_acceptance()

    first_metrics = first["golden_metrics"]
    second_metrics = second["golden_metrics"]
    assert first_metrics["workflow_id"] == second_metrics["workflow_id"]
    assert first_metrics["policy_record_count"] == 2
    assert first_metrics["authoritative_source_records"] == 1
    assert first_metrics["official_citation_count"] >= 1
    assert first_metrics["report_gap_count"] >= 3
    assert first_metrics["report_manifest_count"] == 1
    assert first_metrics["target_weight_change"] == 0.0
    assert 0.0 <= first_metrics["confidence"] <= 0.85


def test_pfi007_ui_read_model_exposes_research_journey_citation_locator_and_report_manifest(tmp_path: Path):
    fixture = build_pfi007_research_policy_golden_fixture()
    workflow = build_research_policy_workflow(
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        opportunities=fixture["opportunities"],
        report_decision_payload=fixture["report_decision_payload"],
        project_root=tmp_path,
        report_root=tmp_path / "reports",
    )
    ids = {
        "source_id": "src-pfi007",
        "evidence_id": "evidence-pfi007",
        "job_id": "job-pfi007",
        "task_id": "task-pfi007",
    }

    ui = build_pfi007_research_policy_ui_read_model(workflow, ids)

    assert ui["schema"] == PFI007_RESEARCH_POLICY_UI_READ_MODEL_SCHEMA
    assert ui["workspace"] == "research"
    assert ui["workspace_label"] == "研究"
    assert ui["primary_feature_view"] == "research_policy_slice"
    assert set(ui["secondary_feature_views"]) == {"citation_locator", "report_manifest", "policy"}
    assert {card["label"] for card in ui["cards"]} == {"政策权威来源", "政策机会", "研究证据缺口"}
    assert any(item["authority_status"] == "OfficialEvidence" and item["source_url"] for item in ui["citation_locator"])
    assert any(item["authority_status"] == "EvidenceRepairRequired" and item["evidence_path"] for item in ui["citation_locator"])
    assert len(ui["report_manifest"]) == 1
    assert ui["report_manifest"][0]["gap_count"] >= 3
    assert ui["report_manifest"][0]["readonly"] is True
    assert "打开一级入口：研究" in ui["journey"]
    assert ui["decision"]["target_weight_change"] == 0.0
    assert ui["decision"]["human_review_required"] is True
    assert ui["safety_boundary"]["no_government_portal_action"] is True
    assert ui["safety_boundary"]["no_order_execution"] is True


def test_pfi007_rollback_removes_temporary_source_evidence_job_and_task_records(tmp_path: Path):
    fixture = build_pfi007_research_policy_golden_fixture()
    workflow = build_research_policy_workflow(
        source_id=fixture["source_id"],
        as_of=fixture["as_of"],
        opportunities=fixture["opportunities"],
        report_decision_payload=fixture["report_decision_payload"],
        project_root=tmp_path,
        report_root=tmp_path / "reports",
    )
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    ids = record_research_policy_workflow(store, workflow, artifact_uri="operational_store:pfi007_research_policy_acceptance")

    proof = rollback_pfi007_research_policy_records(store, ids)

    assert proof["schema"] == "PFI007ResearchPolicyRollbackProofV1"
    assert proof["status"] == "Pass"
    assert proof["residue_counts"] == {
        "source_records": 0,
        "evidence_records": 0,
        "job_records": 0,
        "task_records": 0,
    }
    assert proof["deleted_counts"]["source_records"] == 1
    assert proof["deleted_counts"]["evidence_records"] == 1
    assert proof["deleted_counts"]["job_records"] == 1
    assert proof["deleted_counts"]["task_records"] == 1


def test_pfi007_web_shell_exposes_same_shell_research_policy_controls():
    js = _text(WEB_ROOT / "app" / "shell.js")

    for view in ["research_policy_slice", "citation_locator", "report_manifest"]:
        assert f'view: "{view}"' in js
    for label in ["研究与政策垂直切片", "引用定位", "报告清单"]:
        assert label in js
    for text in ["官方链接、证据路径", "官方证据", "待补证据", "证据不足报告清单", "不登录政府门户", "不修改报告、不刷新数据"]:
        assert text in js
    assert '研究与政策切片: { view: "research_policy_slice"' in js
    assert '引用定位: { view: "citation_locator"' in js
    assert '报告清单: { view: "report_manifest"' in js
    assert "window.open" not in js
    assert "location.reload" not in js
    assert "window.location.href" not in js


def test_pfi007_script_and_target_gate_are_wired_without_heavy_smoke():
    script = _text(PROJECT_ROOT / "scripts" / "pfi007ResearchPolicyAcceptance.sh")
    gate = _text(PROJECT_ROOT / "scripts" / "pfiGate.sh")
    gitignore = _text(PROJECT_ROOT / ".gitignore")

    assert "PFI007ResearchPolicyAcceptance" in script
    assert "run_pfi007_research_policy_acceptance" in script
    assert "tests/contract/test_pfi007_research_policy_vertical_acceptance.py" in gate
    assert "data/systemAudit/PFI007ResearchPolicyAcceptance*.json" in gitignore
    assert "finalAcceptanceCheck" not in script
    assert "ciSmoke" not in script
    assert "broker" not in script.lower()
