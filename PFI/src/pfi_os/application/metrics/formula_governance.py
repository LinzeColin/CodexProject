"""PFI v0.2.5 Stage 5.1 formula, parameter, FX-unit and confidence governance."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from pfi_v02.stage_v022_formula_scoring import (
    STAGE7_CONFIDENCE_WEIGHTS,
    STAGE7_REVIEW_THRESHOLD,
)


PHASE_ID = "V025-S5-P5.1"
TASK_IDS = ("S5-P1-T1", "S5-P1-T2", "S5-P1-T3", "S5-P1-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE5-WHOLE-REVIEW"
REGISTRY_VERSION = "pfi-v0.2.5-formula-registry-v1"
BASE_CURRENCY = "CNY"
FX_PAIR = "AUD/CNY"
FX_DIRECTION = "AUD_TO_CNY"
FX_DEFINITION_ZH = "1 AUD = X CNY"
FX_RATE_UNIT = "CNY/AUD"
EXAMPLE_FX_RATE = "4.81"
CONFIDENCE_DIMENSION_IDS = (
    "classification_confidence",
    "source_coverage",
    "reconciliation_coverage",
    "valuation_coverage",
    "model_validation",
    "report_completeness",
)
LIFECYCLE_STATUSES = ("draft", "active", "deprecated", "superseded")

PFI_ROOT = Path(__file__).resolve().parents[4]
FORMULA_REGISTRY_PATH = PFI_ROOT / "config" / "formulas" / "v025_formula_registry.json"
PARAMETER_CATALOG_PATH = PFI_ROOT / "config" / "pfi_parameters.yaml"
HUMAN_PARAMETER_PATH = PFI_ROOT / "模型参数文件.md"


def _json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def canonical_hash(payload: object) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def formula_payload_hash(formula: Mapping[str, Any]) -> str:
    return canonical_hash({key: value for key, value in formula.items() if key != "formula_hash"})


def load_formula_registry(path: Path = FORMULA_REGISTRY_PATH) -> dict[str, Any]:
    registry = _json_object(path)
    validate_formula_registry(registry)
    return registry


def validate_formula_registry(registry: Mapping[str, Any]) -> None:
    required_top = {
        "schema",
        "registry_version",
        "base_currency",
        "fx_contract",
        "lifecycle",
        "formulas",
    }
    missing_top = sorted(required_top - set(registry))
    if missing_top:
        raise ValueError(f"formula registry missing fields: {', '.join(missing_top)}")
    if registry["registry_version"] != REGISTRY_VERSION:
        raise ValueError("formula registry version does not match runtime")
    if registry["base_currency"] != BASE_CURRENCY:
        raise ValueError("base currency must be CNY")
    fx_contract = registry["fx_contract"]
    if not isinstance(fx_contract, Mapping):
        raise ValueError("fx_contract must be an object")
    expected_fx = {
        "pair": FX_PAIR,
        "direction": FX_DIRECTION,
        "definition_zh": FX_DEFINITION_ZH,
        "rate_unit": FX_RATE_UNIT,
        "example_rate": EXAMPLE_FX_RATE,
        "example_only": True,
        "production_default": None,
    }
    for key, expected in expected_fx.items():
        if fx_contract.get(key) != expected:
            raise ValueError(f"fx_contract.{key} conflicts with runtime contract")
    lifecycle = registry["lifecycle"]
    if not isinstance(lifecycle, Mapping) or lifecycle.get("statuses") != list(LIFECYCLE_STATUSES):
        raise ValueError("formula lifecycle statuses conflict with runtime contract")
    if lifecycle.get("active_versions_immutable") is not True:
        raise ValueError("active formula versions must be immutable")

    formulas = registry["formulas"]
    if not isinstance(formulas, list) or not formulas:
        raise ValueError("formula registry must contain formulas")
    required_formula = {
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
    identities: set[tuple[str, str]] = set()
    for formula in formulas:
        if not isinstance(formula, Mapping):
            raise ValueError("formula entry must be an object")
        missing = sorted(required_formula - set(formula))
        if missing:
            raise ValueError(f"formula entry missing fields: {', '.join(missing)}")
        identity = (str(formula["formula_id"]), str(formula["version"]))
        if identity in identities:
            raise ValueError(f"duplicate formula version: {identity[0]} {identity[1]}")
        identities.add(identity)
        if formula["lifecycle_status"] not in LIFECYCLE_STATUSES:
            raise ValueError(f"unsupported lifecycle status: {formula['lifecycle_status']}")
        if not isinstance(formula["test_refs"], list) or not formula["test_refs"]:
            raise ValueError(f"{formula['formula_id']} requires test_refs")
        if formula["formula_hash"] != formula_payload_hash(formula):
            raise ValueError(f"{formula['formula_id']} formula_hash is not rebuildable")


def validate_formula_lifecycle_transition(
    current_status: str,
    next_status: str,
    *,
    replacement_formula_version: str | None = None,
    current_formula: Mapping[str, Any] | None = None,
    candidate_formula: Mapping[str, Any] | None = None,
) -> None:
    allowed = {
        "draft": {"draft", "active"},
        "active": {"active", "deprecated", "superseded"},
        "deprecated": {"deprecated"},
        "superseded": {"superseded"},
    }
    if current_status not in allowed or next_status not in allowed[current_status]:
        raise ValueError(f"unsupported lifecycle transition: {current_status} -> {next_status}")
    if next_status == "superseded" and not replacement_formula_version:
        raise ValueError("superseded transition requires replacement_formula_version")
    if (
        current_status == "active"
        and next_status == "active"
        and current_formula is not None
        and candidate_formula is not None
        and formula_payload_hash(current_formula) != formula_payload_hash(candidate_formula)
    ):
        raise ValueError("active formula version is immutable; publish a new version")


def _require_decimal(name: str, value: object) -> Decimal:
    if isinstance(value, float):
        raise TypeError(f"{name} must be Decimal; float is forbidden")
    if not isinstance(value, Decimal) or not value.is_finite():
        raise TypeError(f"{name} must be a finite Decimal")
    return value


def convert_to_cny(
    amount: Decimal,
    *,
    original_currency: str,
    fx_rate: Decimal | None = None,
    fx_direction: str | None = None,
    rate_unit: str | None = None,
) -> Decimal:
    """Convert CNY/AUD amounts without rounding or reciprocal-direction inference."""

    amount_decimal = _require_decimal("amount", amount)
    currency = original_currency.strip().upper()
    if currency == BASE_CURRENCY:
        if fx_rate is not None and _require_decimal("fx_rate", fx_rate) != Decimal("1"):
            raise ValueError("CNY identity conversion only permits rate 1")
        if fx_direction not in {None, "CNY_IDENTITY"} or rate_unit not in {None, "CNY/CNY"}:
            raise ValueError("CNY identity conversion cannot use a foreign FX direction or unit")
        return amount_decimal
    if currency != "AUD":
        raise ValueError(f"unsupported original_currency for Phase 5.1: {currency}")
    if fx_direction != FX_DIRECTION:
        raise ValueError("AUD conversion requires fixed AUD_TO_CNY direction")
    if rate_unit != FX_RATE_UNIT:
        raise ValueError("AUD conversion requires CNY/AUD rate unit")
    rate = _require_decimal("fx_rate", fx_rate)
    if rate <= 0:
        raise ValueError("fx_rate must be a positive finite Decimal")
    return amount_decimal * rate


def build_confidence_dimensions() -> dict[str, dict[str, Any]]:
    return {
        "classification_confidence": {
            "label_zh": "记录分类置信度",
            "value_type": "score_0_100",
            "weights": dict(STAGE7_CONFIDENCE_WEIGHTS),
            "review_threshold": STAGE7_REVIEW_THRESHOLD,
            "source_layered_thresholds_allowed": False,
            "missing_policy": "进入人工复核，不提升为其他质量维度的替代分数",
        },
        "source_coverage": {
            "label_zh": "来源覆盖",
            "value_type": "ratio_0_1_or_null",
            "missing_policy": "null_and_blocked",
        },
        "reconciliation_coverage": {
            "label_zh": "对账覆盖",
            "value_type": "ratio_0_1_or_null",
            "missing_policy": "null_and_blocked",
        },
        "valuation_coverage": {
            "label_zh": "估值覆盖",
            "value_type": "ratio_0_1_or_null",
            "missing_policy": "null_and_blocked",
        },
        "model_validation": {
            "label_zh": "模型验证",
            "value_type": "blocked_or_partial_or_validated",
            "missing_policy": "blocked",
        },
        "report_completeness": {
            "label_zh": "报告完整度",
            "value_type": "incomplete_or_partial_or_complete",
            "missing_policy": "incomplete",
        },
    }


def validate_confidence_dimensions(payload: Mapping[str, Any]) -> None:
    if "overall_confidence" in payload:
        raise ValueError("overall_confidence is forbidden; keep six dimensions separate")
    if tuple(payload) != CONFIDENCE_DIMENSION_IDS:
        raise ValueError("confidence payload must contain exactly the six ordered dimensions")
    classification = payload["classification_confidence"]
    if not isinstance(classification, Mapping):
        raise ValueError("classification_confidence must be an object")
    if classification.get("weights") != STAGE7_CONFIDENCE_WEIGHTS:
        raise ValueError("v0.2.2 classification weights must be preserved")
    if classification.get("review_threshold") != 70:
        raise ValueError("classification review threshold must remain 70")
    if classification.get("source_layered_thresholds_allowed") is not False:
        raise ValueError("source-layered classification thresholds are forbidden")


def _governance_config() -> dict[str, Any]:
    catalog = _json_object(PARAMETER_CATALOG_PATH)
    config = catalog.get("formula_governance_v025")
    if not isinstance(config, dict):
        raise ValueError("pfi_parameters.yaml missing formula_governance_v025")
    return config


def build_formula_governance_ui_payload() -> dict[str, Any]:
    config = _governance_config()
    confidence = build_confidence_dimensions()
    validate_confidence_dimensions(confidence)
    return {
        "schema": "PFIV025FormulaGovernanceUIPayloadV1",
        "registry_version": config["registry_version"],
        "base_currency": config["base_currency"],
        "fx_pair": config["fx_pair"],
        "fx_direction": config["fx_direction"],
        "fx_definition_zh": config["fx_definition_zh"],
        "fx_rate_unit": config["fx_rate_unit"],
        "example_fx_rate": config["example_fx_rate"],
        "example_only": config["example_only"],
        "production_default_fx_rate": config["production_default_fx_rate"],
        "formula_lifecycle_statuses": config["formula_lifecycle_statuses"],
        "confidence_dimensions": confidence,
        "aggregate_confidence_score_allowed": config["aggregate_confidence_score_allowed"],
    }


def _markdown_parameter_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in HUMAN_PARAMETER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| PARAM-PFI-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2:
            values[cells[1]] = line
    return values


def build_parameter_consistency_report() -> dict[str, Any]:
    registry = load_formula_registry()
    config = _governance_config()
    ui = build_formula_governance_ui_payload()
    markdown = _markdown_parameter_values()
    expected = {
        "registry_version": REGISTRY_VERSION,
        "base_currency": BASE_CURRENCY,
        "fx_contract": f"{FX_DIRECTION};{FX_DEFINITION_ZH};{FX_RATE_UNIT}",
        "fx_example_policy": f"{EXAMPLE_FX_RATE};example_only=true;production_default=null",
        "lifecycle": "|".join(LIFECYCLE_STATUSES),
        "classification_policy": "threshold=70;source_layered=false;weights=30|10|20|15|15|10",
        "confidence_dimensions": "|".join(CONFIDENCE_DIMENSION_IDS),
        "aggregate_confidence_score_allowed": "false",
    }
    registry_values = {
        "registry_version": registry["registry_version"],
        "base_currency": registry["base_currency"],
        "fx_contract": ";".join(
            [
                registry["fx_contract"]["direction"],
                registry["fx_contract"]["definition_zh"],
                registry["fx_contract"]["rate_unit"],
            ]
        ),
        "fx_example_policy": (
            f"{registry['fx_contract']['example_rate']};example_only="
            f"{str(registry['fx_contract']['example_only']).lower()};production_default=null"
        ),
        "lifecycle": "|".join(registry["lifecycle"]["statuses"]),
        "classification_policy": expected["classification_policy"],
        "confidence_dimensions": "|".join(CONFIDENCE_DIMENSION_IDS),
        "aggregate_confidence_score_allowed": "false",
    }
    config_values = {
        "registry_version": config["registry_version"],
        "base_currency": config["base_currency"],
        "fx_contract": ";".join(
            [config["fx_direction"], config["fx_definition_zh"], config["fx_rate_unit"]]
        ),
        "fx_example_policy": (
            f"{config['example_fx_rate']};example_only={str(config['example_only']).lower()};"
            "production_default=null"
        ),
        "lifecycle": "|".join(config["formula_lifecycle_statuses"]),
        "classification_policy": (
            f"threshold={config['classification_review_threshold']};source_layered="
            f"{str(config['source_layered_thresholds_allowed']).lower()};weights="
            + "|".join(str(value) for value in config["classification_confidence_weights"].values())
        ),
        "confidence_dimensions": "|".join(config["confidence_dimension_ids"]),
        "aggregate_confidence_score_allowed": str(
            config["aggregate_confidence_score_allowed"]
        ).lower(),
    }
    runtime_values = dict(expected)
    ui_values = {
        "registry_version": ui["registry_version"],
        "base_currency": ui["base_currency"],
        "fx_contract": ";".join(
            [ui["fx_direction"], ui["fx_definition_zh"], ui["fx_rate_unit"]]
        ),
        "fx_example_policy": (
            f"{ui['example_fx_rate']};example_only={str(ui['example_only']).lower()};"
            "production_default=null"
        ),
        "lifecycle": "|".join(ui["formula_lifecycle_statuses"]),
        "classification_policy": expected["classification_policy"],
        "confidence_dimensions": "|".join(ui["confidence_dimensions"]),
        "aggregate_confidence_score_allowed": str(
            ui["aggregate_confidence_score_allowed"]
        ).lower(),
    }
    markdown_symbols = {
        "registry_version": "formula_registry_version",
        "base_currency": "formula_base_currency",
        "fx_contract": "fx_direction_contract",
        "fx_example_policy": "fx_example_rate_policy",
        "lifecycle": "formula_lifecycle_statuses",
        "classification_policy": "classification_confidence_policy",
        "confidence_dimensions": "confidence_dimension_ids",
        "aggregate_confidence_score_allowed": "aggregate_confidence_score_allowed",
    }
    markdown_values = {
        key: expected[key]
        if expected[key] in markdown.get(symbol, "")
        else markdown.get(symbol)
        for key, symbol in markdown_symbols.items()
    }
    carriers = {
        "formula_registry_json": registry_values,
        "pfi_parameters_yaml": config_values,
        "python_runtime": runtime_values,
        "ui_payload": ui_values,
        "模型参数文件.md": markdown_values,
    }
    conflicts = [
        {"carrier": carrier, "key": key, "expected": expected[key], "actual": values.get(key)}
        for carrier, values in carriers.items()
        for key in expected
        if values.get(key) != expected[key]
    ]
    return {
        "schema": "PFIV025Stage5Phase51ParameterConsistencyV1",
        "status": "pass" if not conflicts else "fail",
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "carriers": list(carriers),
        "expected": expected,
    }


def build_phase51_contract() -> dict[str, object]:
    return {
        "version": "v0.2.5",
        "stage": 5,
        "phase": "5.1",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "current_phase_only": True,
        "phase_5_2_started": False,
        "stage_5_whole_stage_review_done": False,
        "finder_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_default_fx_rate": None,
        "aggregate_confidence_score_allowed": False,
        "explicitly_not_done": [
            "Phase 5.2 dual consumption and financial model implementation",
            "Phase 5.3 real-data invariants, sensitivity and model validation",
            "Stage 5 whole-stage independent review, remediation, re-review and transition acceptance",
            "GitHub push and canonical PFI.app reinstall",
        ],
    }
