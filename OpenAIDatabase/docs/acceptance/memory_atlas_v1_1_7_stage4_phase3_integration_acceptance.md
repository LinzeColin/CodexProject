# Memory Atlas v1.1.7 Stage 4 Phase 4.3 Integration Acceptance

- Task ID: `MA-V117-S4P03`
- Acceptance ID: `ACC-MA-V117-S4P03`
- Status: `phase_4_3_integration_completed_pending_stage4_review`
- Integration version: `memory_starfield_integration.v1_1_7_stage4_phase3`
- Mapping version: `memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3`
- Static validator: `validate:v1.1.7-stage4-phase3`
- Browser validator: `validate:memory-starfield-integration-browser`
- Snapshot source: redacted universe_state.sample.json

## Scope

Stage 4 Phase 4.3 replaces the production Galaxy default with the new
memory-starfield renderer while preserving the old `legacy` renderer as a
feature flag rollback path. It also connects a redacted
`universe_state.sample.json` snapshot mapping layer to production starfield
particle attributes.

## Acceptance Criteria

Stage 4 Phase 4.3 passes only when:

1. Stage 4 Phase 4.2 continuity is preserved.
2. Feature Flag defaults to new memory-starfield while `legacy rollback` remains
   available through URL/env/localStorage/UI controls.
3. Snapshot Mapping uses the redacted `universe_state.sample.json` fixture as
   the preferred source and falls back to atlas nodes when unavailable.
4. Quality, color, brightness and trajectory trail values come from explicit
   formulas in `starfieldMapping.ts`.
5. Production Galaxy exposes machine-readable integration and mapping metadata
   through DOM attributes and browser debug signals.
6. Browser validation proves default new memory-starfield, legacy rollback,
   snapshot mapping metadata, formula panel and screenshot.
7. No Stage 5, raw/private read, direct active-memory writeback, agent apply,
   deployment or GitHub main upload is included.

## Validation

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage4-phase3
python /Users/linzezhang/.codex/skills/webapp-testing/scripts/with_server.py \
  --server "pnpm --dir OpenAIDatabase/apps/memory-atlas exec vite --host 127.0.0.1 --port 5195" \
  --port 5195 \
  -- node OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_starfield_integration_browser.cjs \
    --url http://127.0.0.1:5195/ \
    --output-dir /tmp/memory-starfield-stage4-phase3
```

## Boundary

- No Stage 5.
- No GitHub main upload.
- No raw/private data read.
- No direct active-memory writeback.
- No agent apply.
- No deployment.

Machine-readable boundary summary: Stage 4 Phase 4.3 Integration;
MA-V117-S4P03; ACC-MA-V117-S4P03;
phase_4_3_integration_completed_pending_stage4_review;
memory_starfield_integration.v1_1_7_stage4_phase3;
memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3; Feature Flag;
Snapshot Mapping; new memory-starfield; legacy rollback; redacted
universe_state.sample.json; validate:v1.1.7-stage4-phase3;
validate:memory-starfield-integration-browser; No Stage 5; No GitHub main
upload.
