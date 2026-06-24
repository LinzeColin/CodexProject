# Project Governance Status

## Snapshot Metadata

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:b190230ef658988d8c88a0d5f6e1d3d4c388c3d60ee185a96f7dbf2bbcf64359`
- snapshot_event_time: `2026-06-22T00:24:25Z`
- generator_version: `4.0.0`
- final_commit_binding: `CI_ATTESTED:governance/run_manifests/GOV-REVIEW6-FINAL-PORTFOLIO-001.json`

## Current State

- Project: `whkmSalary`
- Path: `whkmSalary`
- Product version: `0.0.0`
- Phase/Gate: `B / S3PA-WHKM-weight-validation-partial`
- Models/Formulas/Parameters total: `2 / 10 / 80`
- Active formulas/parameters: `10 / 80`
- Machine checked formulas/parameters: `9 / 78`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `whkmSalary/docs/governance/parameter_registry.csv, whkmSalary/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `whkmSalary/docs/governance/parameter_registry.csv` |
| methodological_rationale | `UNVERIFIED` | `whkmSalary/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| operational_validation | `FAILED` | `whkmSalary/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `whkmSalary/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `whkmSalary/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `S3PA-WHKM-weight-validation-partial`
- Next executable task: `S3PA rounding owner decision evidence`
- Pending/stale events: `4`
- Tree-bound events: `0`
- Commit-bound events: `1`
- Legacy unbound events: `4`
- Unresolved fact IDs: `7`

## S3PAT01 Boundary Update

- `score_settlement`, `score_invoice`, and `score_payback` now reject workday inputs below 1 with `ValueError` before weighted total calculation.
- Streamlit settlement, invoice, and payback day inputs now use `min_value=1`; defaults remain `10`, `10`, and `30`.
- Readiness remains `FAILED`; zero-day business meaning, policy source, tax basis, rounding, and payroll reconciliation remain blocked under `TASK-WHKM-B-001`.

## S3PAT02 Weight Validation Update

- `resolve_weights` now validates metric keys, finite non-negative values, and total weight 1.0 before weighted salary calculation.
- Streamlit no longer carries a duplicate `province_weights` table; province choices and weights come from `salary_logic.projects`.
- No weight active values were recalibrated or owner-approved in this task; weight policy source, rounding, tax basis, and payroll reconciliation remain blocked under `TASK-WHKM-B-001`.
