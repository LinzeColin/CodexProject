from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_A_DOC = PROJECT_ROOT / "docs" / "phase" / "PHASE_A_DATA_FOUNDATION.md"
AUDIT_DOC = PROJECT_ROOT / "docs" / "phase" / "PHASE_A_COMPLETION_AUDIT.md"
DEV_RECORD = PROJECT_ROOT / "docs" / "development" / "PFI_PHASE_0_TO_A_RECORD.md"
HANDOFF = PROJECT_ROOT / "HANDOFF.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase_a_completion_audit_declares_gate_and_scope():
    text = _read(AUDIT_DOC)

    assert "PFIOSPhaseACompletionAuditV1" in text
    assert "Status: completion gate passed for the Phase A data-foundation boundary." in text
    assert "This audit closes the Phase A data-foundation gate." in text
    assert "does not claim" in text
    assert "every legacy workflow has been migrated" in text
    assert "Phase 5 runtime" in text
    assert "acceptance package is complete" in text


def test_phase_a_completion_audit_covers_required_evidence_surfaces():
    text = _read(AUDIT_DOC)

    required_terms = [
        "Operational Store",
        "source_versions",
        "source_ingestion.py",
        "data_home_audit.py",
        "homepage_ingestion.py",
        "repositories.py",
        "command_center_read_model.py",
        "vectorized_read_model.py",
        "macos_runtime_read_model.py",
        "private_reviewed_inputs.py",
        "test_phase_a_streamlit_data_boundary.py",
    ]
    for term in required_terms:
        assert term in text


def test_phase_a_completion_audit_preserves_product_non_regression_constraints():
    text = _read(AUDIT_DOC)

    assert "Market-feel training remains retained under Strategy Lab training mode." in text
    assert "Strategy backtesting remains a core workflow." in text
    assert "No autonomous real-money trading" in text
    assert "Public Git must not contain secrets" in text


def test_phase_a_status_and_handoff_reference_completion_audit():
    phase_text = _read(PHASE_A_DOC)
    handoff_text = _read(HANDOFF)
    dev_record = _read(DEV_RECORD)

    assert "Status: completed data-boundary gate" in phase_text
    assert "docs/phase/PHASE_A_COMPLETION_AUDIT.md" in phase_text
    assert "Phase A data foundation: complete for the data-boundary gate." in handoff_text
    assert "docs/phase/PHASE_A_COMPLETION_AUDIT.md" in handoff_text
    assert "| Phase A completion audit | Complete |" in dev_record
    assert "tests/contract/test_phase_a_completion_audit.py" in dev_record
