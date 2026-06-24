# whkmSalary Model Specification

Project: `whkmSalary`
Governance spec version: `1.0.0`

- model_count: 2
- formula_count: 10
- parameter_count: 80

## Canonical Sources

- `docs/governance/model_registry.yaml`
- `docs/governance/formula_registry.yaml`
- `docs/governance/parameter_registry.csv`
- `docs/governance/delivery_tasks.yaml`
- `docs/governance/TRACEABILITY_MATRIX.csv`

Legacy files `功能清单`, `开发记录`, and `模型参数文件` are compatibility indexes only.

## Model Overview

| ID | Name | Kind | Status | Evidence |
|---|---|---|---|---|
| MOD-001 | Quarterly performance salary calculation | business_calculation_model | active | `whkmSalary/salary_logic.py:134` |
| MOD-002 | Streamlit input constraints | deterministic_rule_engine | active | `whkmSalary/streamlit_app.py:32` |

## Assumptions And Policy Source

- `ASM-001` EXTRACTED: code implements a quarterly sales performance salary calculator.
- `ASM-002` UNKNOWN: jurisdiction, policy/source reference, effective date, statutory tax rule, and approval owner are not evidenced. Open task: `TASK-WHKM-B-001`.
- `ASM-003` EXTRACTED: no real employee payroll records or personal identifiers are present in the repo snapshot.

## Formula Summary

`FORM-001` selects province weights. `FORM-002` through `FORM-008` implement piecewise scoring for performance, margin, settlement, invoice, payback, audit bias, and customer cost. `FORM-004`, `FORM-005`, and `FORM-006` now reject settlement/invoice/payback workday inputs below 1 with `ValueError` before weighted scoring. `FORM-009` computes weighted total, performance pay, total salary, and after-tax retained salary. `FORM-010` records Streamlit input constraints.

Important formula: `performance_rate = quarter_actual / (year_target / 4)`, `weighted_total = sum(score_i * weight_i)`, `perf_money = 36000 * weighted_total / 100`, `total_salary = 6000 * 3 + perf_money`, `after_tax_salary = total_salary * tax_keep_rate`.

## Required Salary Governance Fields

- Jurisdiction: UNKNOWN, linked to `TASK-WHKM-B-001`.
- Policy/source reference: UNKNOWN, linked to `TASK-WHKM-B-001`.
- Effective date: UNKNOWN, linked to `TASK-WHKM-B-001`.
- Currency: UI labels use `元`; formal currency is UNKNOWN.
- Unit: yuan label, ratio, working days, and score points are recorded in `parameter_registry.csv`.
- Rounding: output display rounds with Streamlit format strings; breakdown uses `round(..., 2)` and weights use `round(..., 4)` in `salary_logic.py:172`.
- Minimum/maximum: UI constraints and formula boundaries are recorded. S3PAT01 sets settlement/invoice/payback UI `min_value` to 1 and salary logic direct calls raise `ValueError` for day inputs below 1. The business meaning of zero-day work items remains owner-blocked under `TASK-WHKM-B-001`.
- Inclusion/exclusion: only code-evidenced metrics and province weights are included.

## Validation

Focused checks for this baseline:

- `python -m compileall salary_logic.py streamlit_app.py`
- `python - <<'PY' ... salary_logic.calculate(...) ... PY`
- `python scripts/validate_project_governance.py --project whkmSalary`
- `python -B -m unittest discover -s whkmSalary\tests -q`

Known gaps remain blocked under `TASK-WHKM-B-001`; S3PAT01 only changes invalid workday boundary handling and does not prove payroll policy, tax, rounding, or historical reconciliation correctness.
