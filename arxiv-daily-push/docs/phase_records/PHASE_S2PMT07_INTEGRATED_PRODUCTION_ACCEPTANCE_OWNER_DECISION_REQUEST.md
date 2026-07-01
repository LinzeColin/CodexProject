# S2PMT07 Integrated Production Acceptance Owner Decision Request

Timestamp: `2026-07-01T17:35:58+10:00`

Status: `ready_owner_decision_request_no_acceptance`

This task adds a GitHub-readable owner production-boundary decision request/template at `FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.request.json`.

It is intentionally not an owner approval artifact. The only artifact that can unblock the owner decision artifact gate remains `FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.json`.

## Scope

- Build and validate `owner_production_boundary_decision.request.json`.
- Add CLI support for generating the request state.
- Keep `owner_production_boundary_decision_recorded=false`.
- Keep `acceptance_write_gate_allowed_by_this_request=false`.
- Keep `runtime_enablement_allowed_by_this_request=false`.

## Evidence

- `FINAL_ACCEPTANCE_BUNDLE/owner_production_boundary_decision.request.json`
- `governance/run_manifests/ADP-S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION-REQUEST-20260701.json`
- `governance/run_manifests/ADP-S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-OWNER-DECISION-ARTIFACT-GATE-20260701.json`
- `governance/run_manifests/ADP-S2PMT07-INTEGRATED-PRODUCTION-ACCEPTANCE-WRITE-GATE-20260701.json`
- `governance/run_manifests/ADP-S2PMT07-AUTHORIZED-CONTROLLED-REAL-RUN-ACCEPTANCE-20260701.json`

## Boundary

No `INTEGRATED_PRODUCTION_ACCEPTED`, `DAILY_OPERATION`, SMTP enablement, scheduler enable/install, Release packaging, production restore, public schema, DB migration, source adapter, ranking, queue, CURRENT product contract, V7.1 baseline, or V7.2 contract file was changed by this request.
