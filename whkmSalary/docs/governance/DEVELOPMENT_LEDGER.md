# whkmSalary Development Ledger

Product version: `0.0.0`
Governance spec version: `1.0.0`

## Current State

- Product version: `0.0.0`
- Product version status: `provisional`
- Current phase: `B`
- Current gate: `S3PA-WHKM-boundary-partial`
- Confirmed iterations: 3
- Reconstructed development events: 1
- Current task: `S3PAT01`
- Blockers: `TASK-WHKM-B-001` for policy/source/effective date/rounding/zero-day business meaning evidence; `GOV-SEMANTIC-WHKM-001` retains human review for `PARAM-004`, `PARAM-005`, and `FORM-010`.

## Confirmed Iterations

### `ITER-20260620-WHKM-001`

- Date: 2026-06-20
- Fact level: EXTRACTED
- Version before: UNKNOWN
- Version after: `0.0.0`
- Base commit: `9516776`
- Result commit: `PENDING`
- Task IDs: `TASK-WHKM-A-001`, `TASK-WHKM-A-002`
- Goal: establish whkmSalary governance baseline without changing salary outputs.
- Model changes: documentation only; 2 active models recorded.
- Parameter changes: documentation only; salary constants, piecewise constants, province weights, and UI defaults recorded.
- Commands: `python scripts/validate_project_governance.py --project whkmSalary`; `python -m compileall salary_logic.py streamlit_app.py`; `salary_logic.calculate fixture`; `python scripts/validate_project_governance.py --all`; `git diff --check`.
- Test results: whkmSalary project validator exit 0 with errors 0 warnings 0; compileall exit 0; fixture calculation exit 0 with total_score 13.875 and after_tax_salary 22305.15; all-project validator exit 0 with advisory warnings only outside required projects; diff check exit 0.
- Rollback: remove `whkmSalary/docs/governance` and restore indexes/VERSION/CHANGELOG.
- Next step: continue with OpMe_System P10.

### `ITER-20260621-WHKM-001`

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: `0.0.0`
- Version after: `0.0.0`
- Base commit: `5712cb6666d2abf5c9426d4ad282899774090a85`
- Result commit: `PENDING`
- Task IDs: `GOV-SEMANTIC-WHKM-001`
- Goal: add Review6 semantic extraction metadata for whkmSalary without changing salary calculation behavior.
- Model changes: none to runtime models; governance records now bind salary formulas and constants to machine evidence where possible.
- Parameter changes: 78 active parameters machine-verified; `PARAM-004` and `PARAM-005` remain `HUMAN_REVIEW_REQUIRED`.
- Commands: `python3 scripts/validate_semantic_extractors.py whkmSalary`; final project/all/changed-only validation pending in `GOV-SEMANTIC-WHKM-EXTRACT-001`.
- Test results: semantic extractor exit 0 with 78 parameters and 9 formulas checked; final validation pending.
- Rollback: revert this iteration's governance metadata, root semantic coverage update, generated status pages, and run manifest.
- Next step: complete final validator, focused compile/fixture tests, GitHub PR, and CI attestation.

### `ITER-20260624-WHKM-S3PAT01`

- Date: 2026-06-24
- Fact level: EXTRACTED
- Version before: `0.0.0`
- Version after: `0.0.0`
- Base commit: `896c6e67`
- Result commit: `PENDING`
- Task IDs: `S3PAT01`
- Goal: eliminate direct-call 0-day/negative-day crashes by rejecting invalid settlement, invoice, and payback workday inputs before weighted salary calculation.
- Model changes: `salary_logic.py` now raises `ValueError` for day inputs below 1 in `score_settlement`, `score_invoice`, and `score_payback`; Streamlit day inputs now have `min_value=1`.
- Parameter changes: UI day default values remain 10, 10, and 30; recorded UI minimum for settlement/invoice/payback day inputs is now 1.
- Commands: `python -B -m unittest discover -s whkmSalary\tests -q`; `python -B -m py_compile whkmSalary\salary_logic.py whkmSalary\streamlit_app.py whkmSalary\tests\test_salary_logic_boundaries.py`; `python -B scripts\validate_semantic_extractors.py whkmSalary`.
- Test results: unittest boundary tests passed; py_compile passed; semantic extractor passed with 78 parameters and 9 formulas checked.
- Tooling note: `python -B -m pytest whkmSalary\tests -q` could not run locally because pytest is not installed.
- Rollback: revert S3PAT01 code, tests, governance metadata, stage-gate evidence, and run manifest; keep `TASK-WHKM-B-001` blocked.
- Next step: S3PA weight validation and rounding decision evidence.

## Reconstructed Development Events

- `EVENT-RECON-WHKM-20260619-001`: project import/continuity reconstructed from Git history and legacy notes; not counted as a confirmed iteration.

## Unknown Historical Periods

- Product version before this baseline is UNKNOWN.
- Policy/source provenance is UNKNOWN and task-linked.

## Validation History

| Command | Result | Evidence |
|---|---|---|
| `python scripts/validate_project_governance.py --project whkmSalary` | PASS | exit 0; errors 0 warnings 0 |
| `python -m compileall salary_logic.py streamlit_app.py` | PASS | exit 0 |
| `salary_logic.calculate fixture` | PASS | exit 0; total_score 13.875 |
| `python scripts/validate_project_governance.py --all` | PASS | exit 0; advisory warnings only outside required projects |
| `git diff --check` | PASS | exit 0 |
| `python -B -m unittest discover -s whkmSalary\tests -q` | PASS | S3PAT01 boundary tests reject zero/negative day inputs and preserve one-day scores |
| `python -B scripts\validate_semantic_extractors.py whkmSalary` | PASS | semantic_parameters_checked=78; semantic_formulas_checked=9 |
