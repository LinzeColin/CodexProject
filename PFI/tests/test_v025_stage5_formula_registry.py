from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

import jsonschema
import pytest

from pfi_os.application.metrics.formula_governance import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_IDS,
    build_confidence_dimensions,
    build_formula_governance_ui_payload,
    build_parameter_consistency_report,
    build_phase51_contract,
    convert_to_cny,
    formula_payload_hash,
    load_formula_registry,
    validate_confidence_dimensions,
    validate_formula_lifecycle_transition,
    validate_formula_registry,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "formulas" / "v025_formula_registry.json"
REGISTRY_SCHEMA_PATH = ROOT / "config" / "schemas" / "v025" / "formula_registry.schema.json"
CONFIDENCE_SCHEMA_PATH = ROOT / "config" / "schemas" / "v025" / "confidence_dimensions.schema.json"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_phase_contract_stops_before_phase52() -> None:
    contract = build_phase51_contract()

    assert PHASE_ID == "V025-S5-P5.1"
    assert TASK_IDS == ("S5-P1-T1", "S5-P1-T2", "S5-P1-T3", "S5-P1-T4")
    assert ACCEPTANCE_ID == "ACC-PFI-V025-STAGE5-WHOLE-REVIEW"
    assert contract["current_phase_only"] is True
    assert contract["phase_5_2_started"] is False
    assert contract["finder_used"] is False
    assert contract["push_performed"] is False
    assert contract["app_install_performed"] is False


def test_registry_is_complete_schema_valid_and_hash_rebuildable() -> None:
    registry = load_formula_registry(REGISTRY_PATH)
    jsonschema.validate(registry, _json(REGISTRY_SCHEMA_PATH))
    validate_formula_registry(registry)

    formulas = registry["formulas"]
    assert isinstance(formulas, list)
    assert {item["formula_id"] for item in formulas} == {
        f"FORM-PFI-{number:03d}" for number in range(1, 21)
    }
    required = {
        "formula_id",
        "version",
        "label_zh",
        "definition_zh",
        "inputs",
        "output",
        "outputs",
        "unit",
        "parameters",
        "boundaries_zh",
        "dependencies",
        "test_refs",
        "effective_from",
        "formula_hash",
        "validation_status",
        "lifecycle_status",
    }
    for formula in formulas:
        assert required <= set(formula)
        assert formula["formula_hash"] == formula_payload_hash(formula)
        assert formula["test_refs"]


def test_active_formula_versions_are_immutable_and_transitions_are_explicit() -> None:
    assert validate_formula_lifecycle_transition("draft", "active") is None
    assert validate_formula_lifecycle_transition("active", "deprecated") is None
    assert (
        validate_formula_lifecycle_transition(
            "active",
            "superseded",
            replacement_formula_version="pfi-v0.2.5-cny-conversion-v2",
        )
        is None
    )
    with pytest.raises(ValueError, match="unsupported lifecycle transition"):
        validate_formula_lifecycle_transition("active", "draft")
    with pytest.raises(ValueError, match="replacement_formula_version"):
        validate_formula_lifecycle_transition("active", "superseded")

    formula = load_formula_registry(REGISTRY_PATH)["formulas"][-1]
    mutated = deepcopy(formula)
    mutated["definition_zh"] = "attempted in-place mutation"
    with pytest.raises(ValueError, match="active formula version is immutable"):
        validate_formula_lifecycle_transition(
            "active",
            "active",
            current_formula=formula,
            candidate_formula=mutated,
        )


def test_markdown_yaml_code_and_ui_parameter_carriers_have_zero_conflict() -> None:
    report = build_parameter_consistency_report()
    ui_payload = build_formula_governance_ui_payload()

    assert report["conflict_count"] == 0
    assert report["status"] == "pass"
    assert report["carriers"] == [
        "formula_registry_json",
        "pfi_parameters_yaml",
        "python_runtime",
        "ui_payload",
        "模型参数文件.md",
    ]
    assert ui_payload["base_currency"] == "CNY"
    assert ui_payload["fx_pair"] == "AUD/CNY"
    assert ui_payload["fx_definition_zh"] == "1 AUD = X CNY"
    assert ui_payload["example_fx_rate"] == "4.81"
    assert ui_payload["example_only"] is True
    assert ui_payload["production_default_fx_rate"] is None
    assert "overall_confidence" not in ui_payload


def test_cny_fx_formula_uses_fixed_direction_and_exact_decimal_units() -> None:
    assert convert_to_cny(Decimal("10.00"), original_currency="CNY") == Decimal("10.00")
    assert convert_to_cny(
        Decimal("10.00"),
        original_currency="AUD",
        fx_rate=Decimal("4.81"),
        fx_direction="AUD_TO_CNY",
        rate_unit="CNY/AUD",
    ) == Decimal("48.1000")

    with pytest.raises(ValueError, match="AUD_TO_CNY"):
        convert_to_cny(
            Decimal("10.00"),
            original_currency="AUD",
            fx_rate=Decimal("4.81"),
            fx_direction="CNY_TO_AUD",
            rate_unit="AUD/CNY",
        )
    with pytest.raises(ValueError, match="positive finite Decimal"):
        convert_to_cny(
            Decimal("10.00"),
            original_currency="AUD",
            fx_rate=Decimal("0"),
            fx_direction="AUD_TO_CNY",
            rate_unit="CNY/AUD",
        )
    with pytest.raises(TypeError, match="float"):
        convert_to_cny(
            10.0,
            original_currency="AUD",
            fx_rate=Decimal("4.81"),
            fx_direction="AUD_TO_CNY",
            rate_unit="CNY/AUD",
        )


def test_confidence_is_six_dimensions_and_preserves_classification_policy() -> None:
    payload = build_confidence_dimensions()
    jsonschema.validate(payload, _json(CONFIDENCE_SCHEMA_PATH))
    validate_confidence_dimensions(payload)

    assert list(payload) == [
        "classification_confidence",
        "source_coverage",
        "reconciliation_coverage",
        "valuation_coverage",
        "model_validation",
        "report_completeness",
    ]
    assert payload["classification_confidence"]["review_threshold"] == 70
    assert payload["classification_confidence"]["source_layered_thresholds_allowed"] is False
    assert payload["classification_confidence"]["weights"] == {
        "field_completeness": 30,
        "amount_direction": 10,
        "rule_match": 20,
        "counterparty": 15,
        "interconnection": 15,
        "history_consistency": 10,
    }
    assert sum(payload["classification_confidence"]["weights"].values()) == 100

    invalid = deepcopy(payload)
    invalid["overall_confidence"] = {"value": 99}
    with pytest.raises(ValueError, match="overall_confidence"):
        validate_confidence_dimensions(invalid)
