# Memory Atlas v1.1.7 Stage 0 Phase 2 Usage Help Contract

Contract ID: `memory_atlas_v1_1_7_stage0_phase2_usage_help_contract`

Stage: `v1.1.7 Stage 0`

Phase: `0.2`

Task ID: `MA-V117-S0P02`

Acceptance ID: `ACC-MA-V117-S0P02`

Status: `phase_0_2_usage_help_completed_pending_stage0_review`

## Purpose

Stage 0 Phase 0.2 makes the system understandable before deeper visual or data
model work. It adds a 3-minute usage path, Help panel entry, empty state and
error state explanations for the critical cases named in Roadmap v2:

1. Empty Memory Atlas snapshot.
2. Filtered result set with no matches.
3. WebGL renderer unavailable.
4. Proposal-only panel not writable.

This phase does not implement the Stage 0.3 detail visibility contract, Stage 1
Universe State schema, Search 2.0, Review workflow, Data Map 2.0, Memory River
replacement, Memory Starfield replacement, browser screenshot matrix,
production build, deployment or GitHub main upload.

## Required Runtime Surfaces

| Surface | Requirement | Evidence |
|---|---|---|
| Help panel | The app must expose a visible Help entry and a panel explaining the path `看状态 -> 看建议 -> 看证据 -> 调整 proposal -> 导出/回滚`. | `src/components/help/MemoryAtlasHelpPanel.tsx`, `src/App.tsx` |
| 3-minute path | The Help panel must show three timed steps: current state, advice/evidence, proposal/review. | `src/i18n/zh-CN.ts` |
| Presentation / Analysis | Help copy must explain the difference between fast global reading and deep diagnostic reading. | `src/components/help/MemoryAtlasHelpPanel.tsx` |
| Empty snapshot | If the loaded Atlas has no visible data, the user must know why and what to do next. | `src/components/EmptyState.tsx`, `src/App.tsx` |
| No filtered results | If filters clear the current slice, the user must see a reset-filter action and Chinese explanation. | `src/components/EmptyState.tsx`, `src/App.tsx` |
| Load error | Snapshot load failure must use a clear Chinese error state with the underlying detail preserved. | `src/components/ErrorState.tsx`, `src/App.tsx` |
| WebGL unavailable | Galaxy fallback must explain WebGL unavailability and the Legacy/search recovery path. | `src/components/GalaxyScene.tsx` |
| Proposal not writable | The proposal panel must explain why controls are read-only when writeback policy is not safe. | `src/components/ErrorState.tsx`, `src/App.tsx` |

## Required Copy Registry Groups

The Chinese UI registry must now include:

- `help`
- extended `states.loadFailed*`
- extended `states.emptyAtlas*`
- extended `states.noFilteredResults*`
- extended `states.webglUnavailable*`
- extended `states.proposalUnavailable*`

## Runtime Boundaries

- No new external data source.
- No raw/private/cookie/session/secret read.
- No direct active-memory writeback.
- No proposal write as part of validation.
- No agent apply.
- No browser screenshot or production build in this phase.
- No GitHub main upload in this phase.

## Validation

Required commands:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage0-phase2
pnpm --dir OpenAIDatabase/apps/memory-atlas run lint
git diff --check -- OpenAIDatabase
```

## Rollback

Revert the Stage 0 Phase 0.2 commit. This removes Help/EmptyState/ErrorState
components, the usage guide, validator, contract, acceptance and related copy
without changing data files, proposal queue or long-term memory state.
