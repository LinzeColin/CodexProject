# Memory Atlas v1.1.7 Stage 1 Phase 1 Universe State Acceptance

- Task ID: `MA-V117-S1P01`
- Acceptance ID: `ACC-MA-V117-S1P01`
- Status: `phase_1_1_universe_state_schema_completed_pending_stage1_review`
- Validator: `validate:v1.1.7-stage1-phase1`

## Scope

This phase accepts the shared Universe State schema and consumer map needed by
Roadmap v2 Stage 1. It makes the state layer usable by detail visibility,
Data Map 2.0, Search 2.0 and Review / Summary / Iteration without implementing
those later runtime workflows.

## Required Evidence

| Evidence | Required proof |
|---|---|
| Architecture contract | `docs/architecture/universe_state_snapshot.md` records `MA-V117-S1P01`, all required state fields and the v1.1.7 consumer map. |
| Parameter template | `config/visualization/model_parameters.universe_state.yaml` records task ID, acceptance ID, status, validator, required fields and consumer maps. |
| Generator model | `apps/memory-atlas/src/models/universeState.ts` emits the required consumer map while preserving `universe_state_snapshot.v1`. |
| JSON schema | `apps/memory-atlas/src/fixtures/universe_state.schema.json` requires `data_map_2_0`, `search_2_0` and `review_summary_iteration`. |
| Deterministic sample | `apps/memory-atlas/src/fixtures/universe_state.sample.json` matches the generator output and contains the required consumer map. |
| Safety | All `recommended_next_actions` remain `proposal_only: true`; privacy flags remain false. |
| Records | Changelog, feature list, development record, model parameter records and delivery record register this phase. |

## Required State Fields

The state object must contain:

1. `memory_weather`
2. `dominant_clusters`
3. `rising_clusters`
4. `declining_clusters`
5. `conflict_zones`
6. `black_holes`
7. `proto_stars`
8. `stale_orbits`
9. `memory_terrain`
10. `river_pulse`
11. `mini_starfield`
12. `recommended_next_actions`

## Required Consumer Map

The sample, schema and model must expose these consumers:

1. `memory_overview`
2. `memory_starfield`
3. `memory_river`
4. `data_map_2_0`
5. `search_2_0`
6. `review_summary_iteration`
7. `inspector`
8. `roi_dashboard`

## Failure Conditions

This phase fails if any of the following is true:

1. `data_map_2_0`, `search_2_0` or `review_summary_iteration` is missing from
   the consumer map.
2. The sample does not match deterministic generator output.
3. Any recommended action is not proposal-only.
4. Raw/private/cookie/session/secret data is read or referenced.
5. A runtime UI component, route, CSS feature, proposal editor, writeback
   apply path, browser screenshot, production build, deploy or GitHub main
   upload is included in this phase.

Machine-readable safety phrase: No raw/private data read.

## Validation

Required command:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase1
```

Recommended regression checks:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage0
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:universe-state-spike
pnpm --dir OpenAIDatabase/apps/memory-atlas run lint
git diff --check -- OpenAIDatabase
```

## Stop Boundary

Stop after this phase is validated and committed locally. Do not enter Stage 1
Phase 1.2, do not implement Action Detail Drawer, do not implement tier asset
or topic detail runtime, and do not upload to GitHub main before the full
Stage 0-8 project is complete.
