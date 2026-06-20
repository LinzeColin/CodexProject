# MODEL_SPEC

Project: `<project_id>`
Fact level: `PROPOSED`
Governance spec version: `1.0.0`

## Scope

Describe the project boundary and the evidence used to identify models.

## Model Inventory Summary

machine_summary:

- model_count: 0
- formula_count: 0
- parameter_count: 0

## A. Model Overview

The machine-readable source is `model_registry.yaml`.

### `MOD-001` - `<model_name>`

- Name:
- Kind:
- Purpose:
- Owner:
- Status:
- Model version:
- Implementation reference:
- Inputs:
- Outputs:
- Use cases:
- Non-use cases:
- Fact level:
- Evidence references:

## B. Assumptions

### `ASM-001`

- Statement:
- Why needed:
- Evidence or source:
- Applicable scope:
- Impact if violated:
- How to falsify or validate:
- Current status:

## C. Functions and Formulas

The machine-readable source is `formula_registry.yaml`.

### `FORM-001`

- Mathematical formula or exact pseudocode:
- Plain-language explanation:
- Variables:
- Data types and units:
- Input domain:
- Output range:
- Normalization:
- Constraints:
- Missing data handling:
- Boundary conditions:
- Fallback:
- Implementation reference:
- Test reference:

## D. Parameters

The machine-readable source is `parameter_registry.csv`.

Keep default value, initial or prior value, active value, and calibrated value
separate. Do not mix planned values with active values.

## E. Methodology

- Why this method:
- Alternatives considered:
- Objective or optimization target:
- Calibration method:
- Training, backtest, or experiment method:
- Baseline:
- Data split:
- In-sample / out-of-sample:
- Sensitivity analysis:
- Robustness checks:
- Known bias and limitations:

## F. Strategy Logic

- Signal formation:
- Gate filtering:
- Score-to-decision mapping:
- Risk limits:
- Fallback:
- Deactivation conditions:
- Human approval points:
- Safe behavior on failure:

## G. Validation

- Metrics:
- Baseline:
- Dataset or fixture:
- Test command:
- Current result:
- Result date:
- Uncovered scenarios:
- Release gate:

## NOT_APPLICABLE Evidence

If the project has no model, explain why with evidence and link the confirming
or unresolved task. Do not leave this file blank.
