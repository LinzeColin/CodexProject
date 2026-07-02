# Memory Atlas Universe State Fixture Continuity 合同

- Version: v1.1.6 Stage 9 Phase 4
- Contract ID: `universe_state_fixture_continuity_contract`
- Task ID: `MA-V116-S9P04`
- Status: `phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review`

## Goal

Stage 9 Phase 4 fixes the existing Universe State generator spike as the
fourth C3 isolated prototype evidence for Roadmap v2. It verifies that the
redacted input fixture, deterministic sample, schema, score functions and
parameter drift gate still form a safe shared semantic layer for Memory
Overview, Memory Starfield, Memory River, Data Map, Inspector and ROI without
changing production integration.

This phase validates and documents continuity only. It does not modify score
formulas, regenerate sample data, replace production state, import the
experiment README into the app shell, run a production build, start browser
screenshot acceptance, deploy Cloudflare, modify Access policy, read
raw/private data, write proposals or write active memory.

## Prototype Surface

The Universe State fixture continuity surface is:

- `apps/memory-atlas/src/experiments/universe-state-generator-spike/README.md`
- `apps/memory-atlas/src/models/universeState.ts`
- `apps/memory-atlas/src/utils/universeStateScores.ts`
- `apps/memory-atlas/src/fixtures/universe_state.input.fixture.json`
- `apps/memory-atlas/src/fixtures/universe_state.sample.json`
- `apps/memory-atlas/src/fixtures/universe_state.schema.json`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/scripts/validate_universe_state_spike.mjs`

## Required Continuity Features

The spike must continue to expose:

1. `redacted_fixture_adapter`: adapter from redacted input to state model.
2. `deterministic_sample_generation`: generated sample matches committed
   `universe_state.sample.json`.
3. `schema_validation`: sample passes `universe_state.schema.json`.
4. `parameter_drift_gate`: score constants match
   `model_parameters.universe_state.yaml`.
5. `black_hole_score`: Black Hole score function and severity.
6. `proto_star_score`: Proto-Star score function and status.
7. `stale_score`: stale orbit score function and status.
8. `memory_weather`: weather label and drivers.
9. `memory_terrain`: terrain hints for starfield / analysis use.
10. `river_pulse`: Memory River consumer signal.
11. `mini_starfield`: Memory Starfield consumer signal.
12. `consumer_map`: shared consumer map for overview, starfield, river,
    Inspector and ROI.
13. `proposal_only_actions`: all generated next actions remain proposal-only.
14. `privacy_status`: raw/private, plaintext secret, local path and writeback
    flags remain false.

## Required Fixture Contract

`universe_state.input.fixture.json` may contain only deterministic redacted
derived fixture data. It must include:

- `schema_version: memory_atlas_universe_state_fixture.v1`
- `redaction_mode: public_redacted_read_only_visualization`
- `source_safety.raw_private_data_included: false`
- `source_safety.plaintext_secrets_included: false`
- `source_safety.local_absolute_paths_included: false`
- `source_safety.writeback_allowed: false`
- clusters, conflict zones, Black Hole candidates, Proto-Star candidates and
  activity summary

`universe_state.sample.json` must include:

- `schema_version: universe_state_snapshot.v1`
- `memory_weather`
- `dominant_clusters`
- `rising_clusters`
- `declining_clusters`
- `conflict_zones`
- `black_holes`
- `proto_stars`
- `stale_orbits`
- `memory_terrain`
- `river_pulse`
- `mini_starfield`
- `recommended_next_actions`
- `consumer_map`
- `diagnostics.privacy_status`

Forbidden fixture payload:

- raw transcripts
- cookies, sessions, browser state or tokens
- plaintext secrets or private keys
- local absolute paths
- writeback permission or direct active-memory mutation

## Isolation Rules

Fail this phase if:

- production `src/App.tsx`, `src/main.tsx` or production components import or
  reference `experiments/universe-state-generator-spike`;
- this phase changes score weights, sample content or schema without a
  separate model/fixture update gate;
- fixture or sample privacy flags are not false;
- any generated action has `proposal_only` other than true;
- parameter drift check stops tracing to
  `config/visualization/model_parameters.universe_state.yaml`;
- the sample no longer exposes Memory Overview, Starfield, River, Inspector or
  ROI consumer map entries.

## Safety Boundary

- No production runtime integration.
- No production route or navigation change.
- No feature flag default switch.
- No production build in this phase.
- No browser screenshot run in this phase.
- No local app install or rebuild.
- No Cloudflare live deploy.
- No Access policy change.
- No raw/private/cookie/session/secret data read.
- No raw/private data read.
- No direct writeback.
- No proposal write.
- No agent apply.
- No Stage 9 review, Stage 10 work or GitHub main upload.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

## Acceptance Hook

Required continuity command:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:universe-state-spike
```

Stage 9 Phase 4 validator must additionally check v1.1.6 README continuity,
records, package script, changed-path scope and production-isolation boundary.
