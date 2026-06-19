from pathlib import Path

from pfi_os.application import (
    OperationalStore,
    append_private_reviewed_input_entry,
    load_private_reviewed_input_entries,
    private_reviewed_input_contract,
    private_reviewed_input_output_dir,
)
from pfi_os.business import build_cashflow_command, create_cashflow_entry, write_cashflow_command
from pfi_os.consumption import build_consumption_guard, create_consumption_event
from pfi_os.policy import build_policy_radar, create_policy_opportunity


def test_private_reviewed_inputs_store_user_ledgers_outside_public_git(tmp_path: Path):
    store = OperationalStore(tmp_path / "private" / "operational" / "pfi.sqlite")
    store.initialize()
    cashflow = _cashflow_entry()
    policy = _policy_opportunity()
    consumption = _consumption_event()

    cashflow_result = append_private_reviewed_input_entry(
        store,
        ledger="company_cashflow",
        entry=cashflow,
        entry_id_key="entry_id",
        as_of_key="entry_date",
    )
    append_private_reviewed_input_entry(
        store,
        ledger="policy_radar",
        entry=policy,
        entry_id_key="policy_id",
        as_of_key="published_date",
    )
    append_private_reviewed_input_entry(
        store,
        ledger="consumption_guard",
        entry=consumption,
        entry_id_key="event_id",
        as_of_key="event_date",
    )

    cashflow_entries = load_private_reviewed_input_entries(store, ledger="company_cashflow")
    policy_entries = load_private_reviewed_input_entries(store, ledger="policy_radar")
    consumption_entries = load_private_reviewed_input_entries(store, ledger="consumption_guard")
    sources = store.table_rows("source_records")
    evidence = store.table_rows("evidence_records")

    assert cashflow_result["schema"] == "PFIOSPrivateReviewedInputEntryV1"
    assert cashflow_entries[0]["entry_id"] == cashflow["entry_id"]
    assert policy_entries[0]["policy_id"] == policy["policy_id"]
    assert consumption_entries[0]["event_id"] == consumption["event_id"]
    assert {row["domain"] for row in sources} == {"PRIVATE_USER"}
    assert all(row["uri"].startswith("operational://private-reviewed-input/") for row in sources)
    assert {row["evidence_class"] for row in evidence} == {"private_reviewed_input_entry"}
    assert "data/cashflow/CompanyCashFlowEntries.json" not in "\n".join(row["artifact_uri"] for row in evidence)


def test_business_builders_accept_private_operational_rows_without_ledger_files(tmp_path: Path):
    cashflow_payload = build_cashflow_command(project_root=tmp_path, entries=[_cashflow_entry()])
    policy_payload = build_policy_radar(project_root=tmp_path, opportunities=[_policy_opportunity()])
    consumption_payload = build_consumption_guard(project_root=tmp_path, events=[_consumption_event()])

    assert cashflow_payload["entry_path"] == "operational_store:private_reviewed_inputs/company_cashflow"
    assert cashflow_payload["entries"][0]["entry_id"]
    assert policy_payload["entry_path"] == "operational_store:private_reviewed_inputs/policy_radar"
    assert policy_payload["opportunities"][0]["policy_id"]
    assert consumption_payload["event_path"] == "operational_store:private_reviewed_inputs/consumption_guard"
    assert consumption_payload["events"][0]["event_id"]


def test_private_reviewed_output_dir_and_write_use_private_data_home(tmp_path: Path):
    output_dir = private_reviewed_input_output_dir("company_cashflow", data_home=tmp_path)
    payload = write_cashflow_command(project_root=tmp_path, entries=[_cashflow_entry()], output_dir=output_dir)
    contract = private_reviewed_input_contract(data_home=tmp_path)

    assert output_dir == tmp_path / "private" / "derived" / "company_cashflow"
    assert contract["domain"] == "PRIVATE_USER"
    assert contract["operational_store_only"] is True
    assert contract["public_git_ledgers"] == []
    assert str(tmp_path / "private" / "derived" / "company_cashflow") in payload["outputs"]["latest_json"]
    assert Path(payload["outputs"]["latest_json"]).exists()


def test_streamlit_private_input_views_do_not_reference_public_ledger_files():
    streamlit_app = (Path(__file__).resolve().parents[2] / "src" / "pfi_os" / "app" / "streamlit_app.py").read_text(
        encoding="utf-8"
    )

    assert "CompanyCashFlowEntries.json" not in streamlit_app
    assert "PolicyOpportunityEntries.json" not in streamlit_app
    assert "ConsumptionGuardEvents.json" not in streamlit_app
    assert 'ROOT / "data" / "cashflow"' not in streamlit_app
    assert 'ROOT / "data" / "policy"' not in streamlit_app
    assert 'ROOT / "data" / "consumption"' not in streamlit_app
    assert "append_private_reviewed_input_entry" in streamlit_app
    assert "private_reviewed_input_output_dir" in streamlit_app


def _cashflow_entry() -> dict:
    return create_cashflow_entry(
        entry_date="2026-06-19",
        direction="BalanceSnapshot",
        category="Other",
        amount=1000.0,
        currency="AUD",
        account="Cash reserve",
        counterparty="Manual ledger",
        description="Reviewed balance fixture.",
        evidence_link="manual-review",
        review_status="Reviewed",
    )


def _policy_opportunity() -> dict:
    return create_policy_opportunity(
        published_date="2026-06-19",
        title="Policy fixture",
        source_name="Official fixture",
        source_type="Official",
        source_url="https://example.invalid/policy",
        jurisdiction="AU",
        policy_level="National",
        opportunity_type="IndustrySupport",
        sectors="AI",
        affected_entities="PFI",
        impact_summary="Fixture policy opportunity.",
        required_action="Manual review.",
        authority_score=80,
        relevance_score=70,
        urgency_score=60,
        feasibility_score=50,
        review_status="Reviewed",
    )


def _consumption_event() -> dict:
    return create_consumption_event(
        event_date="2026-06-19",
        event_type="Discretionary",
        category="Other",
        amount=42.0,
        currency="AUD",
        merchant="Manual merchant",
        payment_method="Manual",
        planned=False,
        recurring=False,
        necessity_score=20,
        impulse_score=30,
        regret_score=10,
        evidence_link="manual-review",
        review_status="Reviewed",
    )
