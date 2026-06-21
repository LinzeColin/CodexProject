# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `whkmSalary`
- Path: `whkmSalary`
- CI mode: `required`
- Product version: `0.0.0`
- Model versions: `MOD-001:salary-logic-v0, MOD-002:streamlit-input-v0`
- Parameter profile versions: `province_weights:salary-logic-v0, salary_logic_constants:salary-logic-v0, streamlit_defaults:streamlit-input-v0`
- Current iteration: `ITER-20260620-WHKM-001`
- Current phase: `E`
- Current gate: `GOV-G4-WHKM-REQUIRED`
- Model count: `2`
- Formula count: `10`
- Parameter count: `80`
- Task count: `5`
- Unbound event count: `2`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `158`

## Latest Run

- Event: `EVENT-WHKM-20260620-002`
- Task: `GOV-G4-WHKM-PROMOTE-001`
- Summary: Verified whkmSalary governance baseline and promoted whkmSalary enforcement from advisory to required.
- Model delta: UNKNOWN
- Parameter delta: UNKNOWN
- Tests: python scripts/validate_project_governance.py --project whkmSalary, python -m compileall salary_logic.py streamlit_app.py, salary_logic.calculate fixture, python scripts/validate_project_governance.py --all, git diff --check
- Evidence: whkmSalary/docs/governance/DEVELOPMENT_LEDGER.md, governance/projects.yaml
- Result: `PASS`
- Rollback: Set whkmSalary ci_mode back to advisory and restore whkmSalary governance task status if promotion is reverted.

## Current Blockers

`TASK-WHKM-B-001` for policy/source/effective date/rounding/boundary evidence.

## Next Task

`TASK-WHKM-B-001` - Resolve salary policy source, jurisdiction, effective date, tax basis, boundary behavior, and rounding policy evidence.

- Status: `blocked`
- Acceptance: ACC-WHKM-B-001
- Selection rationale: status=blocked; phase=B; current_phase=E; unmet_dependencies=none; score=108
