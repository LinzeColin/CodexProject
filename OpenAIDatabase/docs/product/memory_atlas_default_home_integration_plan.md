# Memory Atlas v1.1.5 Stage 2.1 Default Home Integration Plan

- Date: 2026-06-30
- Stage source: `memory_atlas_final_taskpack_v1.md` Stage 2 / Task 2.1
- Run mode: integration planning only
- Current production route status: default view remains `galaxy`
- Implementation status: not started in this phase

## Goal

Make `记忆总览` the default startup board for Memory Atlas while preserving the
left sidebar navigation and all existing visual boards.

This phase produces the integration plan only. It does not change the runtime
default route, import the isolated spikes into production, or modify writeback
behavior.

## Verified Current State

| Area | Current evidence | Impact |
|---|---|---|
| Default view | `apps/memory-atlas/src/App.tsx` initializes `activeView` with `galaxy` | Stage 3 must change this only after overview skeleton exists |
| Navigation | `views` is rendered inside the left `aside.sidebar` navigation | Left navigation can be preserved by prepending `overview` to `views` |
| Runtime data | App fetches only redacted `/memory_atlas.json` through `loadMemoryAtlas` | Overview must not introduce raw/private fetch paths |
| Universe State | `src/fixtures/universe_state.sample.json` and schema exist from Stage 1 | Stage 3 can use the redacted sample before runtime generator wiring |
| Existing boards | Galaxy, data guide, ROI, Obsidian, timeline, contribution, word cloud, search, summary exist | New default must deep-link to existing boards, not replace them |

## Target UX

`记忆总览` is the first screen after startup. It should be an operational
overview, not a marketing page or a text-only status screen.

Minimum first version:

1. `Memory Weather` compact status card.
2. `Black Hole` risk card with reduction action.
3. `Proto-Star` opportunity card with validation action.
4. `Next Best Actions` list from redacted Universe State recommendations.
5. `Mini Starfield` preview that links to `记忆星系`.
6. `River Pulse` preview that links to `记忆时间河`.
7. Inspector focus remains synchronized with selected nodes where possible.

## Proposed Implementation Sequence

### Stage 3.1.1 Home Page Skeleton

Files likely touched:

- `apps/memory-atlas/src/types.ts`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`

Steps:

1. Add `overview` to `ViewKey`.
2. Add `记忆总览` as the first `views` entry.
3. Add a small `DEFAULT_MEMORY_ATLAS_VIEW` constant with value `overview`.
4. Render `MemoryOverviewView` when `activeView === "overview"`.
5. Keep `aside.sidebar` and current filter controls visible.
6. Keep existing boards accessible from the left sidebar.

Acceptance for this task:

- Startup H1 is `记忆总览`.
- Left sidebar still contains all existing board labels.
- Switching from `记忆总览` to `银河星云` and back works.
- Existing `galaxy` route remains one click away.

Rollback:

- Set `DEFAULT_MEMORY_ATLAS_VIEW` back to `galaxy`.
- Remove `overview` from `views`.

### Stage 3.1.2 Universe State Cards

Files likely touched:

- `apps/memory-atlas/src/models/universeState.ts`
- `apps/memory-atlas/src/fixtures/universe_state.sample.json`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`

Steps:

1. Define a narrow reader for `UniverseStateSnapshot`.
2. For first integration, consume the Stage 1 redacted sample fixture.
3. Display Memory Weather, dominant cluster, black hole and proto-star cards.
4. Do not display diagnostics by default; reserve them for Analysis/debug mode.

Acceptance for this task:

- No raw/private/cookie/session/secret fields are rendered.
- Cards have Chinese labels and action-oriented summaries.
- Missing sample data degrades to a clear empty state, not a blank screen.

Rollback:

- Hide Universe State cards and leave the overview skeleton active.

### Stage 3.1.3 Next Actions and Deep Links

Files likely touched:

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`

Steps:

1. Render `recommended_next_actions` as proposal-only next steps.
2. Add mini starfield and river pulse preview buttons.
3. Preview clicks call `setActiveView("galaxy")` or `setActiveView("timeline")`.
4. Do not mutate active memory or write proposal records from previews.

Acceptance for this task:

- Clicking mini starfield opens `银河星云`.
- Clicking river pulse opens `时间轴` until the production river view exists.
- Actions remain proposal-only and do not write local memory state.

Rollback:

- Remove preview deep links; leave cards read-only.

## Validation Plan

Run from the repository root unless noted:

```bash
PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas lint

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas build

python3 scripts/audit_memory_atlas_acceptance.py --publish-dir apps/memory-atlas/dist
```

Browser smoke after Stage 3.1 implementation:

1. Open local preview.
2. Confirm first H1 is `记忆总览`.
3. Confirm left sidebar labels are still visible.
4. Switch to `银河星云`, `时间轴`, and back to `记忆总览`.
5. Confirm console errors are zero.
6. Confirm no port `4177` background listener remains after closing preview.

## Stop Conditions

Stop and do not continue implementation if any of the following occurs:

1. Overview requires raw exports, private imports, cookies, sessions, or
   plaintext secrets.
2. Left navigation must be removed to make the overview work.
3. The first screen becomes a marketing/hero page instead of the app workspace.
4. Existing Galaxy or Timeline behavior regresses during the route change.
5. Writeback changes from proposal-only to direct active-memory mutation.

## Stage 2.1 Completion Criteria

This planning phase is complete when:

1. The current route/nav state is documented with evidence.
2. The default-home implementation sequence is explicit.
3. Rollback and validation commands are explicit.
4. The plan preserves left navigation and redacted-only data boundaries.

Runtime default-home behavior remains a later Stage 3 implementation item.
