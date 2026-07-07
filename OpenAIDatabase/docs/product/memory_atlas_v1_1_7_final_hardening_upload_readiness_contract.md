# Memory Atlas v1.1.7 Final Hardening Upload Readiness Contract

Contract ID: `memory_atlas_v1_1_7_final_hardening_upload_readiness_contract`

Stage: `v1.1.7 Stage 10 Phase 10.1`

Task ID: `MA-V117-S10P01`

Acceptance ID: `ACC-MA-V117-S10P01`

Status: `phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review`

## Purpose

Stage 10 Phase 10.1 defines the final hardening and upload readiness contract
for the v1.1.7 Stage 0-10 delivery. It turns Stage 10 into a deterministic
evidence gate covering performance, safety, accessibility, release/rollback,
final validation, GitHub main upload readiness, governance sync and new-machine
recovery.

This phase does not run the Stage 10 review, does not perform final validation,
does not upload GitHub main, does not create a remote branch or PR, does not
deploy, and does not change production runtime code.

## Entry Condition

- Stage 9 review must be complete.
- Current work must remain on `codex/memory-atlas-v117-stage0-10-local`.
- `origin/main` must be an ancestor of the local continuation branch before
  final upload readiness work is recorded.
- No intermediate GitHub upload is allowed before all Stage 0-10 tasks are
  complete and final validation passes.

## Final Hardening Surfaces

The later Stage 10 review and final upload gate must prove each surface with
explicit evidence:

| Surface | Required proof |
|---|---|
| performance_safety_accessibility_matrix | Desktop target 45-60 FPS, reduced-motion fallback, cleanup proof, keyboard/focus coverage, accessible labels for icon controls, no text overlap in core flows, no blank canvas fallback and no console/runtime errors in critical browser gates. |
| release_rollback_matrix | Feature flags, legacy fallback paths, rollback notes, local app/runtime manifest proof, release artifact audit, Cloudflare/Access owner gate and no-live-deploy boundary are explicit before upload. |
| final_validation_matrix | `validate:v1.1.7-pre-stage0`, `validate:v1.1.7-stage0` through `validate:v1.1.7-stage9`, `validate:v1.1.7-stage10-phase1`, Stage 10 review validator, `validate:whole-project`, lint, build, diff check and required browser validators pass from the same checkout. |
| github_main_upload_matrix | Clean tracked tree, canonical remote `LinzeColin/CodexProject`, final push target `main`, no open development branch, no PR, no intermediate upload, `origin/main` integration, sparse-checkout boundary and final upload stop line are documented. |
| governance_sync_matrix | `CHANGELOG.md`, `功能清单.md`, `开发记录.md`, `模型参数文件.md`, delivery record, project model parameters and universe-state model parameters agree on status, validator, evidence, risks and rollback. |
| new_machine_recovery_matrix | GitHub main tree must contain all source, docs, validators, acceptance contracts, governance records and model parameters needed for another agent to clone, install, validate and continue without this temporary machine. |

## Evidence Record Shape

The later Stage 10 review artifact should expose this minimum shape:

```json
{
  "acceptance_id": "ACC-MA-V117-S10-REVIEW",
  "parent_stage": "v1.1.7 Stage 10",
  "phase_10_1_status": "phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review",
  "performance_safety_accessibility_status": "pending_stage10_review",
  "release_rollback_status": "pending_stage10_review",
  "final_validation_status": "pending_stage10_review",
  "github_main_upload_status": "pending_final_one_time_upload",
  "rollback_hint": "revert the final upload commit or restore the pre-upload main commit after owner confirmation"
}
```

## Phase 10.1 Acceptance

- This product contract and the matching acceptance file exist.
- `validate:v1.1.7-stage10-phase1` exists and checks Stage 9 continuity,
  contract coverage, records, package script, branch boundary, no remote
  development branch, changed-file scope and runtime boundary.
- Records mark the status as
  `phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review`.
- Records state that this phase does not run Stage 10 review, final upload,
  live deploy, app install, browser screenshot, raw/private read, direct
  active-memory writeback or proposal queue write.

## Non-Goals

- No production UI, CSS, route, app shell, renderer, feature flag default,
  scoring, fixture or schema change.
- No production build artifact committed, installer run, local app install,
  browser screenshot, Cloudflare deploy, Access policy change, GitHub branch
  creation, PR creation or GitHub main upload in this phase.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No GitHub main upload in this phase.

## Rollback

Revert the Stage 10 Phase 10.1 commit. This removes the readiness contract,
acceptance file, validator, package script and governance record entries
without changing Stage 9 runtime behavior or uploading GitHub main.

Machine-readable boundary summary: Stage 10 Phase 10.1; MA-V117-S10P01; ACC-MA-V117-S10P01; phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review; memory_atlas_v1_1_7_final_hardening_upload_readiness_contract; validate:v1.1.7-stage10-phase1; performance_safety_accessibility_matrix; release_rollback_matrix; final_validation_matrix; github_main_upload_matrix; governance_sync_matrix; new_machine_recovery_matrix; desktop target 45-60 FPS; reduced-motion fallback; Stage 9 review must be complete; pending Stage 10 review; No intermediate GitHub upload; No GitHub main upload in this phase; No raw/private/cookie/session/secret data access; No direct active-memory writeback; No proposal queue write.
