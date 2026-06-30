# Universe State Generator Spike

- Product target: Memory Atlas v1.1.5
- Stage: 1 C3 isolated prototypes
- Current phase contribution: Task 1.3 Universe State Generator Spike
- Status: isolated generator spike; no production integration
- Last updated: 2026-06-30

## Goal

This spike generates a deterministic `universe_state_snapshot.v1` sample from a
small redacted fixture. It validates the adapter, score functions and JSON
shape before any production Memory Overview, Starfield or River integration.

## Boundary

Hard boundaries:

1. Do not import this spike from `src/App.tsx`, `src/main.tsx` or production
   components during Stage 1.
2. Do not read raw exports, full transcripts, cookies, sessions, browser state,
   plaintext secrets or local private paths.
3. Do not write active memory, writeback proposals or runtime app snapshots.
4. Keep all generated actions `proposal_only=true`.

## Files

1. `src/models/universeState.ts` implements the adapter and snapshot generator.
2. `src/utils/universeStateScores.ts` implements parameterized score functions.
3. `src/fixtures/universe_state.input.fixture.json` is the redacted input.
4. `src/fixtures/universe_state.sample.json` is the generated output sample.
5. `src/fixtures/universe_state.schema.json` is the minimal schema gate.
6. `scripts/validate_universe_state_spike.mjs` runs unit checks, schema checks,
   parameter drift checks and privacy checks.

## Feature List

Implemented in this isolated spike:

1. Redacted fixture adapter.
2. Black Hole score function.
3. Proto-Star score function.
4. Stale score function.
5. Memory Weather label selection.
6. Dominant, rising, declining, conflict, black hole, proto-star and stale
   fields.
7. River Pulse, Mini Starfield and consumer map sample fields.
8. JSON schema validation and deterministic sample comparison.
9. Parameter drift check against
   `config/visualization/model_parameters.universe_state.yaml`.
10. Privacy scan for secrets, local absolute paths and raw transcript wording.

## Model Parameters

The score constants are mirrored from
`config/visualization/model_parameters.universe_state.yaml`:

1. `black_hole`: interaction `0.28`, recency `0.22`, repetition `0.25`, ROI
   penalty `0.15`, growth penalty `0.10`.
2. `proto_star`: recency growth `0.30`, cross signal `0.20`, capability
   relation `0.25`, ROI potential `0.20`, uncertainty penalty `0.05`.
3. `stale`: inactive days `0.55`, low recent usage `0.25`, confidence decay
   `0.20`.
4. Weather thresholds: storm conflict `0.72`, Black Hole warning `0.65`,
   Proto-Star notice `0.58`.

The validator fails if these mirrored values drift from the YAML template.

## Acceptance Criteria

This Stage 1 spike is accepted when:

1. Adapter unit check parses clusters, conflicts, Black Hole candidates and
   Proto-Star candidates.
2. Score unit checks cover Black Hole, Proto-Star and stale formulas.
3. Sample JSON contains dominant, rising, declining, conflict, black_hole,
   proto_star and stale fields.
4. Score formulas trace to the parameter YAML.
5. Sample JSON passes schema validation.
6. Sample JSON contains no raw/private content, local absolute paths,
   plaintext secrets or writeback permission.
7. Production app does not import the spike.

## Development Record

2026-06-30 phase result:

1. Built `universeState.ts`, `universeStateScores.ts`, redacted input fixture,
   generated sample JSON, schema and validator.
2. Added package script `validate:universe-state-spike`.
3. No production route, component or navigation integration was added.
4. Validation command passed:
   `pnpm --dir OpenAIDatabase/apps/memory-atlas validate:universe-state-spike`.
5. Validation output covered weather `black_hole_warning`, dominant `3`,
   rising `3`, declining `1`, conflict `1`, Black Hole `1`, Proto-Star `2`,
   stale `1`, parameter source and all-false privacy status.
6. Production build command passed:
   `pnpm --dir OpenAIDatabase/apps/memory-atlas build`.
7. Build warning remained the existing Vite chunk-size warning; no new build
   failure was introduced.

## Rollback

Delete the files listed above and remove the package script. No production app
rollback is required while no production code imports these files.
