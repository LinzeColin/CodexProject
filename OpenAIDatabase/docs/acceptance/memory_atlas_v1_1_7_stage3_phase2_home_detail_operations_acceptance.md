# Memory Atlas v1.1.7 Stage 3 Phase 3.2 Home Detail Operations Acceptance

Task ID: `MA-V117-S3P02`

Acceptance ID: `ACC-MA-V117-S3P02`

Status: `phase_3_2_home_detail_operations_completed_pending_stage3_review`

Validator: `validate:v1.1.7-stage3-phase2`

Operation version: `memory_overview_detail_operations.v1_1_7_stage3_phase2`

Section versions:

- Top Actions Section: `top_actions_section.v1_1_7_stage3_phase2`
- Level Assets Section: `level_assets_section.v1_1_7_stage3_phase2`
- Theme Categories Section: `theme_categories_section.v1_1_7_stage3_phase2`

## Home Detail Operations

Stage 3 Phase 3.2 acceptance requires Memory Overview to expose concrete
home-detail operations while preserving the Stage 3.1 default home structure.
The page must remain `proposal-only`, read only, and safe to inspect without
writing active memory.

## Acceptance Checks

1. Top Actions Section shows each suggestion with reason, priority, status,
   ROI, urgency, evidence count and next step.
2. Each top action is a clickable detail entry into `ActionDetailDrawer`.
3. Level Assets Section shows group markers for `core_profile`, `project`,
   `decision`, `temporary` and `stale`.
4. Each level asset is a clickable detail entry into `AssetDetailPanel`.
5. Theme Categories Section shows state markers for `rising`, `declining`,
   `conflict`, `opportunity` and `stable`.
6. Each theme card is a clickable detail entry into `ThemeDetailPanel`.
7. `App.tsx`, `styles.css` and `memory_overview_product_contract.md` include
   the Stage 3 Phase 3.2 machine-readable operation contract.

## Files

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_overview_product_contract.md`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase2.cjs`

## Boundaries

- No Stage 3 Review.
- No Search 2.0 runtime.
- No Review workflow runtime.
- No Data Map 2.0 runtime.
- No raw/private/cookie/session/secret data read.
- No direct active-memory writeback.
- No agent apply.
- No GitHub main upload before whole Stage 0-10 completion.

Rollback: revert the Stage 3 Phase 3.2 commit only; Stage 3.1 default home,
Stage 2 proposal layer and Stage 0-1 records remain intact.
