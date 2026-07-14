# Memory Atlas v1.1.7 Stage 3 Phase 3.1 Default Home Acceptance

Contract ID: `memory_overview_default_home.v1_1_7_stage3_phase1`

Task ID: `MA-V117-S3P01`

Acceptance ID: `ACC-MA-V117-S3P01`

Status: `phase_3_1_default_home_structure_completed_pending_stage3_review`

Validator: `validate:v1.1.7-stage3-phase1`

## Default Home Structure

Stage 3 Phase 3.1 is accepted when `App.tsx` makes the default route `home`,
marks the app root with a default-route data contract, and marks the Memory
Overview root with `memory_overview_default_home.v1_1_7_stage3_phase1`.

`styles.css` must keep the structure rail compact and responsive so the page
does not become a pile of cards. The product source of truth is
`memory_overview_product_contract.md`.

Acceptance guardrail: the page must stay a guided work surface, not a pile of cards.

Required sections:

- `status_summary`: status summary
- `suggested_actions`: suggested actions
- `weather`: weather
- `black_holes`: black holes
- `proto_stars`: proto-stars
- `assets`: assets
- `themes`: themes
- `entry_points`: entry points

Rollback keeps the core 4 sections only:

- `status_summary`
- `suggested_actions`
- `weather`
- `entry_points`

## Validation

- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage3-phase1`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage2`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run lint`
- `git diff --check -- OpenAIDatabase`

## Boundaries

- No Stage 3 Phase 3.2.
- No Search 2.0 runtime.
- No Review workflow runtime.
- No Data Map 2.0 runtime.
- No raw/private/cookie/session/secret data read.
- No direct active-memory writeback.
- No agent apply.
- No GitHub main upload before whole Stage 0-10 completion.
