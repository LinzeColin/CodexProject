# Memory Atlas v1.1.7 Stage 5 Phase 5.3 Timeline Integration Acceptance

- Task ID: `MA-V117-S5P03`
- Acceptance ID: `ACC-MA-V117-S5P03`
- Status: `phase_5_3_timeline_integration_completed_pending_stage5_review`
- Integration version: `memory_river_integration.v1_1_7_stage5_phase3`
- Static validator: `validate:v1.1.7-stage5-phase3`
- Browser validator: `validate:memory-river-integration-browser`

## Scope

Stage 5 Phase 5.3 replaces the old production Timeline default with the Memory
River page while keeping old Timeline rollback available. The new page default
enabled condition is default memory-river in `DEFAULT_TIMELINE_RENDERER_MODE`.
The rollback condition is legacy rollback via in-app toggle,
`timelineRenderer=legacy`, `timeline=legacy`, localStorage and env override.

## Acceptance Checks

1. Production Timeline exposes `memory_river_integration.v1_1_7_stage5_phase3`
   through `TIMELINE_RENDERER_FEATURE_FLAG_VERSION`.
2. Production Timeline defaults to default memory-river and renders
   `.memory-river-canvas`.
3. Old Timeline rollback available through in-app `Legacy` and URL
   `timelineRenderer=legacy`.
4. Browser validator performs brush interaction and verifies selected range
   metadata through `window.__memoryAtlasStage5Phase3()`.
5. Memory River keeps Macro/Meso/Micro lanes, Black Hole lifecycle,
   Proto-Star lifecycle, stale/deprecated fade and ROI gradient evidence
   layers.
6. Safety metadata reports `rawPrivateDataIncluded=false`,
   `directActiveMemoryWriteback=false` and `proposalWrite=false`.

## Validation Commands

- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage5-phase3`
- `python /Users/linzezhang/.codex/skills/webapp-testing/scripts/with_server.py --server "pnpm --dir OpenAIDatabase/apps/memory-atlas exec vite --host 127.0.0.1 --port 5197" --port 5197 -- node OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_river_integration_browser.cjs --url http://127.0.0.1:5197/ --output-dir /tmp/memory-river-stage5-phase3`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage5-phase2`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run lint`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run build`
- `git diff --check -- OpenAIDatabase`

## Boundaries

No Stage 5 review. No Stage 6. No raw/private data read. No direct
active-memory writeback. No agent apply. No deploy. No GitHub main upload
before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Phase 5.3; MA-V117-S5P03; ACC-MA-V117-S5P03; phase_5_3_timeline_integration_completed_pending_stage5_review; validate:v1.1.7-stage5-phase3; validate:memory-river-integration-browser; memory_river_integration.v1_1_7_stage5_phase3; default memory-river; legacy rollback; timelineRenderer=legacy; brush interaction; old Timeline rollback available; new page default enabled; No Stage 5 review; No Stage 6; No raw/private data read; No direct active-memory writeback; No agent apply; No deploy; No GitHub main upload.
