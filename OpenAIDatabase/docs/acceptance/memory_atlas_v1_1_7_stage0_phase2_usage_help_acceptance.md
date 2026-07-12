# Memory Atlas v1.1.7 Stage 0 Phase 2 Usage Help Acceptance

Acceptance ID: `ACC-MA-V117-S0P02`

Task ID: `MA-V117-S0P02`

Required validator: `validate:v1.1.7-stage0-phase2`

Status: `phase_0_2_usage_help_completed_pending_stage0_review`

## Acceptance Checklist

| Check | Pass condition |
|---|---|
| Help entry | `App.tsx` exposes a Help button using the Chinese copy registry and opens `MemoryAtlasHelpPanel`. |
| 3-minute path | Help copy and panel include the sequence `看状态`, `看建议`, `看证据`, `调整 proposal`, and review/export/rollback guidance. |
| Mode explanation | Help panel explains Presentation and Analysis reading modes. |
| Empty snapshot | `ViewRouter` can render `EmptyState` with `data-memory-atlas-empty-state="empty-atlas"`. |
| No filtered results | `ViewRouter` can render `EmptyState` with `data-memory-atlas-empty-state="no-filtered-results"` and a reset-filter action. |
| Load error | `ViewRouter` and the top banner use `ErrorState` for snapshot load failure while preserving error details. |
| WebGL fallback | `GalaxyScene.tsx` has `data-memory-atlas-error-state="webgl-unavailable"` and Chinese recovery guidance. |
| Proposal not writable | `WritebackProposalPanel` shows `data-memory-atlas-error-state="proposal-not-writable"` when writeback policy is not safe. |
| Registry | `types.ts` and `zh-CN.ts` contain the `help` group and extended `states` fields for all four empty/error cases. |
| Boundary | This phase does not implement Stage 0.3 detail fields, Stage 1 schema, direct writeback, agent apply, build, deploy or GitHub upload. |

## Deferred Proof

This acceptance is static and TypeScript-checked. It does not prove Playwright
screenshot quality, real WebGL failure in a browser, full responsive visual QA,
the Stage 0.3 detail visibility contract, Search 2.0, Review / Summary /
Iteration, Data Map 2.0, Memory River or Memory Starfield.

## Failure Conditions

- The Help path is absent or cannot be opened from the UI.
- The user cannot tell what to do when the snapshot is empty or filters hide all
  results.
- WebGL fallback still reads like a low-level renderer failure without a recovery
  path.
- Proposal controls are disabled without an explanation.
- Validation writes active memory, creates a proposal, reads raw/private data or
  uploads to GitHub.

## Rollback

Revert the Stage 0 Phase 0.2 commit. No data migration rollback is required.
