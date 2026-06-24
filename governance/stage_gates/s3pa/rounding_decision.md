# S3PAT03 whkmSalary Rounding Decision

timestamp: 2026-06-24T00:00:00+10:00
scope: whkmSalary only
acceptance: ACC-S3PAT03-WHKM-ROUNDING-REGRESSION

## Decision

- Money outputs from `calculate` are rounded to cents through `round_money`.
- `round_money` uses `Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
- The rounded fields are `perf_money`, `total_salary`, and `after_tax_salary`.
- Score and weight display fields keep their existing `round(..., 2)` and `round(..., 4)` behavior.

## Regression Evidence

- `python -B -m unittest discover -s whkmSalary\tests -q`: PASS, 9 tests OK.
- `python -B -m py_compile whkmSalary\salary_logic.py whkmSalary\streamlit_app.py whkmSalary\tests\test_salary_logic_rounding.py`: PASS.
- `python -B scripts\validate_semantic_extractors.py whkmSalary`: PASS after FORM-009 fingerprint synchronization.
- Historical 湖北 fixture remains `total_score=13.875`, `perf_money=4995.0`, `total_salary=22995.0`, `after_tax_salary=22305.15`.

## Dependency Lock

- `streamlit==1.58.0`
- `pandas==3.0.3`
- Versions were verified as available by `python -B -m pip index versions streamlit` and `python -B -m pip index versions pandas`.
- Packages are not installed in the local test environment; no Streamlit runtime smoke test is claimed.

## Owner Boundary

- This is a technical rounding decision to remove ambiguity from current code outputs.
- It does not approve payroll policy, statutory tax handling, jurisdiction, effective date, or historical payroll reconciliation.
- Owner approval remains required under `TASK-WHKM-B-001`.
