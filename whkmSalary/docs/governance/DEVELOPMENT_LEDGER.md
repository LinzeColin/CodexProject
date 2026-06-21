# whkmSalary Development Ledger

Product version: `0.0.0`
Governance spec version: `1.0.0`

## Current State

- Product version: `0.0.0`
- Product version status: `provisional`
- Current phase: `B`
- Current gate: `GOV-SEMANTIC-WHKM-in-progress`
- Confirmed iterations: 2
- Reconstructed development events: 1
- Current task: `GOV-SEMANTIC-WHKM-001`
- Blockers: `TASK-WHKM-B-001` for policy/source/effective date/rounding/boundary evidence; `GOV-SEMANTIC-WHKM-001` retains human review for `PARAM-004`, `PARAM-005`, and `FORM-010`.

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
