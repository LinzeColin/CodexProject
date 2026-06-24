# Changelog

## Unreleased - 2026-06-24

- S4PCT02 establishes the minimal `src/`, `tests/`, `config/`, and Chinese owner-entry structure: runtime implementation now lives under `src/whkm_salary/`, root `salary_logic.py` and `streamlit_app.py` remain compatibility wrappers, and `Procfile` startup stays unchanged.
- Added `config/structure_contract.yaml` and `docs/whkm_structure_report.md`; no salary formulas, active parameter values, Streamlit defaults, or payroll readiness claims changed.
- S3PAT03 adds explicit Decimal half-up cent rounding for monetary outputs and keeps the existing 湖北 regression fixture unchanged.
- Pinned deployment dependencies to `streamlit==1.58.0` and `pandas==3.0.3`; local Streamlit runtime smoke is not claimed because those packages are not installed in the local environment.
- S3PAT02 consolidates Streamlit province weights to the `salary_logic.projects` single source.
- Added runtime validation that weight keys exactly match the salary metrics, all values are finite and non-negative, and the total equals 1.0 before weighted salary calculation.
- Added focused tests for configured project weights, explicit invalid weights, and UI single-source weight usage; weight policy approval remains blocked under `TASK-WHKM-B-001`.
- S3PAT01 rejects settlement, invoice, and payback workday inputs below 1 in `salary_logic.py` to prevent `None` entering weighted salary calculation.
- Set the Streamlit settlement, invoice, and payback day inputs to `min_value=1`; existing defaults remain unchanged.
- Added boundary tests for zero/negative direct calls and preserved owner blockers for zero-day business meaning, policy source, rounding, tax, and payroll readiness.

## 0.0.0 - 2026-06-20

- Established CodexProject governance baseline for whkmSalary without changing salary calculation behavior.
- Recorded salary formulas, province weights, UI defaults, version dimensions, and traceability.
- Marked policy/source reference, jurisdiction, effective date, legal tax basis, and boundary repair decisions as UNKNOWN under `TASK-WHKM-B-001`.
