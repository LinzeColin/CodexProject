# Memory Atlas v1.2.1 S04-P1-T1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 13,702-line Memory Atlas `App.tsx` monolith with a real
Provider-first composition root, eight mounted feature boundaries and one exhaustive
route shell without changing product behavior.

**Architecture:** Compose snapshot, workspace and local-runtime providers in that
order; mount persistent chrome in `MemoryAtlasShell`; route the existing ten `ViewKey`
surfaces through `FeatureRouter`. Mechanically relocate existing declarations into
feature/shared modules before any local cleanup, preserving the reducer, DOM, CSS,
network and snapshot contracts.

**Tech Stack:** React 19, TypeScript 5.9, Vite 8, Playwright 1.61, Node.js, Python 3,
Git.

## Global Constraints

- Complete only Task `S04-P1-T1` in this run.
- Work on the canonical local `main` with the owner's explicit approval; do not create
  a worktree, branch or PR.
- No GitHub push, app reinstall, Cloudflare deploy or cache cleanup.
- Do not stage, edit or revert the five user-owned dirty `WDA/docs/governance/*` files.
- Preserve all ten `ViewKey` values and all mounted user workflows.
- Preserve snapshot data, CSS selectors, DOM order, runtime endpoints, allowlists,
  proposal authorization and static-hosted read-only behavior.
- `App.tsx` target is under 100 lines and must remain under the Stage hard maximum of
  1,200 lines.
- The shell target is under 800 lines and must remain under 1,200 lines.
- New feature/view/model modules target under 500 lines; do not split into empty or
  pass-through fragments solely for line count.
- Source-string validators are not acceptance evidence and must not be made green with
  marker comments.
- One bounded implementation commit after all gates pass; the design/plan preparation
  history remains separate.

---

### Task 1: Restore Toolchain and Capture RED/Baseline Evidence

**Files:**

- Create: `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_1_s04_p1_t1_structure.mjs`
- Modify: `apps/memory-atlas/package.json`
- Read: `apps/memory-atlas/src/App.tsx`
- Read: `apps/memory-atlas/src/types.ts`
- Read: `apps/memory-atlas/src/state/sharedAtlasState.ts`

**Interfaces:**

- Produces: `npm run validate:v1.2.1-s04-p1-t1-structure`.
- Validator result: exit `0` only when the production import graph proves the thin app,
  eight mounted feature roots, exhaustive ten-route registry and allowed dependency
  directions.
- Produces: pre-refactor outputs for the currently mounted browser workflows.

- [ ] **Step 1: Restore exact locked dependencies without changing manifests**

Run:

```bash
cd apps/memory-atlas
npm ci --ignore-scripts --no-audit --no-fund
git diff --exit-code -- package.json package-lock.json pnpm-lock.yaml
```

Expected: dependencies materialize under ignored `node_modules`; all three tracked
manifest/lock files remain unchanged.

- [ ] **Step 2: Create a syntax-aware structure validator**

Use the local `typescript` compiler API to parse the production graph. The validator
must encode these exact values:

```js
const REQUIRED_FEATURES = [
  "overview", "actions", "assets", "topics",
  "search-review", "summary-iteration", "sync", "settings",
];
const REQUIRED_VIEWS = [
  "home", "galaxy", "notion", "roi", "obsidian",
  "timeline", "contribution", "wordcloud", "search", "summary",
];
const MAX_APP_LINES = 800;
const MAX_SHELL_LINES = 1200;
```

Parse relative imports from `src/App.tsx`, `src/app`, `src/providers`, `src/features`
and `src/shared`. Fail if a feature imports `App`, `src/app` or another feature's
internal path; a provider imports a feature; shared imports provider/feature/app; or a
route component is unreachable from `src/main.tsx`.

- [ ] **Step 3: Run the validator and prove RED**

Run:

```bash
npm run validate:v1.2.1-s04-p1-t1-structure
```

Expected: non-zero with concrete failures for the 13,702-line `App.tsx`, missing
`src/app`, missing `src/providers`, missing feature roots and missing route registry.

- [ ] **Step 4: Capture current production baseline**

Run the existing mounted-path gates before refactoring:

```bash
npm run lint
npm run build
npm run validate:v1.2-home-multiviewport
npm run validate:v1.2-command-workflows
npm run validate:v1.2-proposal-e2e
npm run validate:v1.2-owner-daily-e2e
npm run validate:v1.2-visual-workflows
npm run validate:stage7-visual
npm run validate:search-2-0-browser
npm run validate:review-summary-iteration-browser
npm run validate:summary-iteration-closure-browser
npm run validate:cross-board-shared-state-browser
```

Expected: every command that exercises the current mounted app exits `0`. Any baseline
failure must be diagnosed before extraction; do not silently reclassify it as a
refactor regression.

---

### Task 2: Extract Shared Models, Guards and Feature-neutral Selectors

**Files:**

- Create: `apps/memory-atlas/src/shared/atlas/constants.ts`
- Create: `apps/memory-atlas/src/shared/atlas/filters.ts`
- Create: `apps/memory-atlas/src/shared/atlas/models.ts`
- Create: `apps/memory-atlas/src/shared/atlas/selectors.ts`
- Create: `apps/memory-atlas/src/shared/runtime/constants.ts`
- Create: `apps/memory-atlas/src/shared/runtime/guards.ts`
- Create: `apps/memory-atlas/src/shared/runtime/types.ts`
- Modify: `apps/memory-atlas/src/App.tsx`

**Interfaces:**

- Produces: unchanged named types/constants/builders currently consumed by more than
  one feature or provider.
- Preserves: constant string values, type unions, guard predicates, sorting/filtering
  formulas and fallback rules.

- [ ] **Step 1: Use the TypeScript AST to inventory top-level declarations**

Print declaration name, kind, start/end lines and imported identifiers. Build a
dependency graph from identifier references so each moved declaration carries all
non-feature dependencies or imports them explicitly.

- [ ] **Step 2: Move only feature-neutral declarations**

Move shared constants, types, guards and pure selectors without changing function
bodies. Export only names used outside their module. Keep feature-specific visual
models for their owning feature task.

- [ ] **Step 3: Verify each extraction batch**

After each module group, run:

```bash
npm run lint
```

Expected: exit `0`; no `any` fallback, duplicate declaration or circular import is
introduced.

---

### Task 3: Introduce the Three Provider Contracts

**Files:**

- Create: `apps/memory-atlas/src/providers/AtlasDataProvider.tsx`
- Create: `apps/memory-atlas/src/providers/AtlasWorkspaceProvider.tsx`
- Create: `apps/memory-atlas/src/providers/AtlasRuntimeProvider.tsx`
- Create: `apps/memory-atlas/src/app/AppProviders.tsx`
- Modify: `apps/memory-atlas/src/App.tsx`

**Interfaces:**

- Produces: `useAtlasData(): AtlasDataContextValue`.
- Produces: `useAtlasWorkspace(): AtlasWorkspaceContextValue`.
- Produces: `useAtlasRuntime(): AtlasRuntimeContextValue`.
- Produces: `AppProviders({ children }: PropsWithChildren): JSX.Element`.

The provider contracts start with these exact fields; feature-specific derived models
remain in their feature modules rather than expanding these contexts:

```ts
interface AtlasDataContextValue {
  atlas: MemoryAtlas;
  loadState: "loading" | "ready" | "error";
  loadError: string;
  snapshotLoadedAt: Date | null;
  reloadAtlas: () => Promise<MemoryAtlas>;
}

interface AtlasWorkspaceContextValue {
  sharedState: SharedAtlasState;
  activeView: ViewKey;
  filters: AtlasFilters;
  selectedNode: AtlasNode | null;
  selectedContributionPeriod: ContributionPeriodDetail | null;
  timelineTimeRange: TimelineTimeRangeSelection | null;
  scopedAtlas: MemoryAtlas;
  nodeMap: Map<string, AtlasNode>;
  sourceOptions: SourceOption[];
  categories: string[];
  tiers: string[];
  themeOptions: Array<{ id: string; label: string }>;
  slice: FilteredAtlasSlice;
  selectNode: (node: AtlasNode) => void;
  selectContributionPeriod: (detail: ContributionPeriodDetail) => void;
  selectTimelineRange: (range: TimelineTimeRangeSelection) => void;
  clearTimelineRange: () => void;
  updateFilters: (updater: (current: AtlasFilters) => AtlasFilters) => void;
  clearFilter: (key: FilterKey) => void;
  resetFilters: () => void;
  switchView: (view: ViewKey) => void;
}

interface AtlasRuntimeContextValue {
  runtimeState: RuntimeState;
  selectedCommandId: S12P1CommandId;
  commandExecution: CommandExecutionState;
  proposalReview: ProposalReviewPayload | null;
  ownerDailyWorkspaceOpen: boolean;
  ownerDailyResult: OwnerDailyResult | null;
  selectCommand: (command: CommandPaletteCommand) => void;
  executeCommand: (command: CommandPaletteCommand) => Promise<void>;
  closeProposalReview: () => void;
  openOwnerDaily: () => void;
  closeOwnerDaily: () => void;
  setOwnerDailyResult: (result: OwnerDailyResult | null) => void;
}
```

The provider composition is exact:

```tsx
export function AppProviders({ children }: PropsWithChildren) {
  return (
    <AtlasDataProvider>
      <AtlasWorkspaceProvider>
        <AtlasRuntimeProvider>{children}</AtlasRuntimeProvider>
      </AtlasWorkspaceProvider>
    </AtlasDataProvider>
  );
}
```

- [ ] **Step 1: Extract snapshot lifecycle into `AtlasDataProvider`**

Move `atlas`, `loadState`, `loadError`, `snapshotLoadedAt`, initial load cancellation and
`reloadAtlas`. Preserve `AbortError` handling and Chinese error text. Memoize the
context value and throw a bounded developer error if the hook is used outside the
provider.

- [ ] **Step 2: Extract reducer wiring and selectors into `AtlasWorkspaceProvider`**

Move `sharedAtlasReducer` wiring, active view, filters, selected node, contribution
period, timeline range, source-scoped atlas, option lists, filtered slice and stable
actions. Keep the existing reducer file and action semantics unchanged.

- [ ] **Step 3: Extract local/static operation lifecycle into `AtlasRuntimeProvider`**

Move runtime detection, 1,200 ms fallback, heartbeat/release listeners, command
execution, proposal actions and Owner Daily actions. Consume `reloadAtlas` and
workspace navigation only through provider hooks. Preserve every endpoint path,
request body, response guard and capability version constant.

- [ ] **Step 4: Verify provider extraction**

Run:

```bash
npm run lint
npm run build
```

Expected: exit `0`; no hook ordering, stale closure or context-cycle errors.

---

### Task 4: Extract Eight Mounted Feature Boundaries

**Files:**

- Create/modify focused modules under:
  - `apps/memory-atlas/src/features/overview/`
  - `apps/memory-atlas/src/features/actions/`
  - `apps/memory-atlas/src/features/assets/`
  - `apps/memory-atlas/src/features/topics/`
  - `apps/memory-atlas/src/features/search-review/`
  - `apps/memory-atlas/src/features/summary-iteration/`
  - `apps/memory-atlas/src/features/sync/`
  - `apps/memory-atlas/src/features/settings/`
- Modify: `apps/memory-atlas/src/App.tsx`

**Interfaces:**

- Each feature exposes only mounted route/workspace components through its `index.ts`.
- Primary routes:
  - overview: `home`, `roi`, `contribution`, `wordcloud`
  - assets: `galaxy`, `obsidian`, `timeline`
  - topics: `notion`
  - search-review: `search`
  - summary-iteration: `summary`
- Persistent surfaces:
  - actions: action detail, proposal and writeback
  - sync: command palette and Owner Daily
  - settings: controls, help and Inspector

- [ ] **Step 1: Move feature-specific types/models before views**

For each feature, move its local constants, types, pure builders and then JSX
components. Preserve declaration bodies and props first; do not rename CSS classes,
`data-*` attributes, version strings or window evidence hooks.

- [ ] **Step 2: Connect existing leaf components without copying**

Import `GalaxyScene`, `ObsidianGraphScene`, `VisualWorkflowWorkbench`,
`ProposalEditor`, detail panels and help components from their current files. Do not
delete or consolidate them in this task.

- [ ] **Step 3: Add one real public index per feature**

Each `index.ts` exports only components consumed by the shell/router or tests. The
structure validator must prove every feature export is reachable from `src/main.tsx`.

- [ ] **Step 4: Verify after each feature group**

Run:

```bash
npm run lint
```

Expected: exit `0`, with no feature-to-feature internal import.

---

### Task 5: Build the Shell, Exhaustive Router and Thin App

**Files:**

- Create: `apps/memory-atlas/src/app/routeRegistry.tsx`
- Create: `apps/memory-atlas/src/app/FeatureRouter.tsx`
- Create: `apps/memory-atlas/src/app/MemoryAtlasShell.tsx`
- Replace: `apps/memory-atlas/src/App.tsx`

**Interfaces:**

- Produces: `ROUTE_REGISTRY: Record<ViewKey, RouteComponent>` with exactly ten keys.
- Produces: `FeatureRouter(): JSX.Element`.
- Produces: `MemoryAtlasShell({ children }: PropsWithChildren): JSX.Element`.
- Produces: `App(): JSX.Element` as the composition root.

```ts
type RouteComponent = ComponentType;
```

- [ ] **Step 1: Build exhaustive route registry**

Use a typed `satisfies Record<ViewKey, RouteComponent>` registry. Do not retain the old
implicit final `SearchReview` fallback. Invalid runtime route values render the
existing bounded error component.

- [ ] **Step 2: Move persistent page composition into `MemoryAtlasShell`**

Preserve topbar, controls, interaction lens, command palette, content grid, side
panels and overlays in the same DOM order. Consume feature-owned workspaces through
their public indexes and state through provider hooks.

- [ ] **Step 3: Replace `App.tsx` with the approved composition root**

The final implementation must be equivalent to:

```tsx
import { AppProviders } from "./app/AppProviders";
import { FeatureRouter } from "./app/FeatureRouter";
import { MemoryAtlasShell } from "./app/MemoryAtlasShell";

export function App() {
  return (
    <AppProviders>
      <MemoryAtlasShell>
        <FeatureRouter />
      </MemoryAtlasShell>
    </AppProviders>
  );
}
```

- [ ] **Step 4: Run structure GREEN**

Run:

```bash
npm run validate:v1.2.1-s04-p1-t1-structure
```

Expected: exit `0`, exactly eight mounted features, exactly ten route keys, thin app,
bounded shell and no forbidden import direction.

---

### Task 6: Full Regression, Scope Audit and One Local Commit

**Files:**

- Modify only if required by the implementation evidence:
  - `docs/superpowers/plans/2026-07-13-memory-atlas-v1-2-1-s04-p1-t1-implementation.md`
- Do not modify owner records merely to claim progress; owner-record updates belong to
  their governed task unless the Task Pack explicitly requires them here.

**Interfaces:**

- Produces: fresh structural, static, build and rendered/runtime evidence.
- Produces: one bounded local implementation commit for `S04-P1-T1`.

- [ ] **Step 1: Run full accepted verification set**

Run all commands from Task 1 Step 4 plus:

```bash
npm run validate:v1.2.1-s04-p1-t1-structure
git diff --check
```

Expected: every accepted gate exits `0`. A legacy source-string validator may be
listed separately with the exact reason it no longer covers production behavior, but
cannot replace a rendered gate.

- [ ] **Step 2: Audit requirements and scope from current state**

Verify:

```bash
wc -l apps/memory-atlas/src/App.tsx apps/memory-atlas/src/app/MemoryAtlasShell.tsx
git diff --name-only
git status --short
git diff -- apps/memory-atlas/src/state/sharedAtlasState.ts
git diff -- apps/memory-atlas/src/styles.css
```

Expected: line limits pass; no snapshot/CSS/reducer semantic change; only Task files
plus this plan are in scope; five WDA files remain unstaged and unmodified by this run.

- [ ] **Step 3: Review the production import graph and rendered evidence**

Confirm each of the eight feature indexes is reachable, all ten routes render, command,
proposal and Owner Daily requests retain exact shapes, and visual canvases are nonblank
at the accepted viewports.

- [ ] **Step 4: Stage only S04-P1-T1 files and create the implementation commit**

Run:

```bash
git add -- OpenAIDatabase/apps/memory-atlas \
  OpenAIDatabase/docs/superpowers/plans/2026-07-13-memory-atlas-v1-2-1-s04-p1-t1-implementation.md
git diff --cached --check
git diff --cached --name-only
git -c gc.auto=0 commit -m "refactor(memory-atlas): split app by feature (S04-P1-T1)"
```

Expected: commit succeeds, contains no WDA/raw/runtime/cache files and remains local.

- [ ] **Step 5: Verify durable stop state**

Run:

```bash
git fsck --connectivity-only --no-dangling
git status --short --branch
git rev-list --left-right --count HEAD...origin/main
```

Expected: fsck exits `0`; only the five pre-existing WDA files are dirty; local main is
ahead and origin is not ahead. Stop before `S04-P1-T2`.
