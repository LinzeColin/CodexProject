# Changelog

## Unreleased - 2026-06-24

- S3PAT01 rejects settlement, invoice, and payback workday inputs below 1 in `salary_logic.py` to prevent `None` entering weighted salary calculation.
- Set the Streamlit settlement, invoice, and payback day inputs to `min_value=1`; existing defaults remain unchanged.
- Added boundary tests for zero/negative direct calls and preserved owner blockers for zero-day business meaning, policy source, rounding, tax, and payroll readiness.

## 0.0.0 - 2026-06-20

- Established CodexProject governance baseline for whkmSalary without changing salary calculation behavior.
- Recorded salary formulas, province weights, UI defaults, version dimensions, and traceability.
- Marked policy/source reference, jurisdiction, effective date, legal tax basis, and boundary repair decisions as UNKNOWN under `TASK-WHKM-B-001`.
