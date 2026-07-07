# Memory Atlas v1.1.7 Stage 9 Phase 9.1 Cross-board Shared State Contract

Task ID: `MA-V117-S9P01`

Acceptance ID: `ACC-MA-V117-S9P01`

Status: `phase_9_1_cross_board_shared_state_completed_pending_stage9_review`

Runtime version: `cross_board_shared_state.v1_1_7_stage9_phase1`

Inspector layer version: `inspector_explanation_layer.v1_1_7_stage9_phase1`

## Purpose

Stage 9 Phase 9.1 turns the existing Memory Atlas shared-state reducer into a
versioned cross-board runtime contract. It keeps the app on one source of truth
for selected node, cluster, record, time range, contribution period and filters
while exposing an Inspector explanation layer that can be verified by browser
automation.

This phase implements Cross-board shared state, synchronized filters and
Inspector explanation layer coverage only. It does not complete Stage 9 review,
Stage 10 hardening or final GitHub main upload.

## Required Runtime Contract

| Surface | Requirement |
|---|---|
| Shared state runtime | The app shell exposes `cross_board_shared_state.v1_1_7_stage9_phase1`. |
| Inspector layer | The Inspector explanation panel exposes `inspector_explanation_layer.v1_1_7_stage9_phase1`. |
| Debug hook | `window.__memoryAtlasStage9Phase1()` reports runtime version, Inspector layer version, surfaces, synchronized filters, shared focus and safety flags. |
| Cross-board surfaces | home, galaxy, notion, roi, obsidian, timeline, contribution, wordcloud, search and summary are included in the shared-state surface list. |
| shared_state_filters | The debug hook and DOM markers expose the shared query, source, tier, category, theme, timeRange and roi filter state. |
| synchronized_filters | Search input changes must remain synchronized after switching boards. |
| inspector_explanation_layer | The selected node explanation must report formula rows, evidence rows, safety notes and redacted-derived source scope. |
| Safety | Runtime uses redacted derived snapshots only and reports no direct active-memory writeback, no proposal queue write and no raw/private data inclusion. |

## Acceptance

Stage 9 Phase 9.1 is accepted only when:

1. `validate:v1.1.7-stage9-phase1` passes.
2. `validate:cross-board-shared-state-browser` passes against the local
   production runtime.
3. Product contract, acceptance file, package scripts and records all contain
   `MA-V117-S9P01`, `ACC-MA-V117-S9P01`, the status, runtime version,
   Inspector layer version and no-upload boundary.
4. Browser validation proves the same search filter persists from one board to
   another and the Inspector focus stays synchronized.
5. Browser validation proves the Inspector explanation layer is mounted with
   formula rows, evidence rows and safety notes.

## Explicitly Not Proven

- This phase does not prove Stage 9 review completion.
- This phase does not prove Stage 10 performance, accessibility, release,
  rollback or final upload readiness.
- This phase does not mutate active memory or proposal queues.
- This phase does not upload GitHub main.

## Required Commands

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage9-phase1
python /Users/linzezhang/.codex/skills/webapp-testing/scripts/with_server.py --server "pnpm --dir OpenAIDatabase/apps/memory-atlas exec vite --host 127.0.0.1 --port 5204" --port 5204 -- node OpenAIDatabase/apps/memory-atlas/scripts/validate_cross_board_shared_state_browser.cjs --url http://127.0.0.1:5204/ --output-dir /tmp/cross-board-shared-state-stage9-phase1
```

## Safety Boundary

- No Stage 9 review.
- No Stage 10.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Cross-board shared state; MA-V117-S9P01; ACC-MA-V117-S9P01; phase_9_1_cross_board_shared_state_completed_pending_stage9_review; validate:v1.1.7-stage9-phase1; validate:cross-board-shared-state-browser; cross_board_shared_state.v1_1_7_stage9_phase1; inspector_explanation_layer.v1_1_7_stage9_phase1; shared_state_filters; synchronized_filters; inspector_explanation_layer; Inspector explanation layer; No Stage 9 review; No Stage 10; No raw/private/cookie/session/secret data access; No direct active-memory writeback; No proposal queue write; No GitHub main upload before the whole Stage 0-10 project is complete.
