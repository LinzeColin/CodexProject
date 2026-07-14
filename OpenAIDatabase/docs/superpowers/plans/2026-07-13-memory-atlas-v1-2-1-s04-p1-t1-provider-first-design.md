# Memory Atlas v1.2.1 S04-P1-T1 Provider-first Design

**Status:** Provider-first direction approved; written design pending owner review before implementation planning.

**Task:** `S04-P1-T1`

**Source contract:**

- Action: split the frontend by overview, actions, assets, topics, search/review,
  summary/iteration, sync and settings.
- Output: feature directories and a route shell.
- Task acceptance: `App.tsx` only owns providers, routing and high-level
  orchestration.
- Stage target: `App.tsx <= 800` lines, hard maximum `1200` lines.
- Stage invariant: visual, data and behavioral output remains aligned with the S01
  baseline; this task introduces no product feature.

## 1. Decision

Adopt a Provider-first extraction around the existing React/Vite application.

`App.tsx` becomes a composition root. Data loading, shared workspace state and local
runtime workflows move behind three focused providers. A shell renders the persistent
navigation and workspace chrome. A feature router selects the current primary view.
The current behavior is relocated without semantic redesign.

```tsx
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

This design was selected over a temporary legacy wrapper because a wrapper would leave
the 13,702-line implementation as the real application and would not establish the
required ownership boundaries. It was selected over a route-props-first extraction
because the current shell coordinates snapshot reloads, cross-view selection and local
runtime actions; stabilizing those dependencies first produces smaller route contracts.

## 2. Current Baseline

The implementation plan must use the current repository state as its baseline, not the
historical source-level validators.

| Object | Current state |
|---|---:|
| `src/App.tsx` | 13,702 lines |
| `src/styles.css` | 11,577 lines |
| `src/state/sharedAtlasState.ts` | 322 lines |
| Stable primary views | 10 |
| Required feature domains | 8 |

The ten stable `ViewKey` values are:

```text
home, galaxy, notion, roi, obsidian, timeline,
contribution, wordcloud, search, summary
```

The existing `sharedAtlasReducer` remains the sole authority for active view, filters,
selection, time range and cross-board focus. This task may relocate its wiring but must
not change reducer semantics. Shared-state semantic changes belong to `S04-P1-T3`.

## 3. Scope

### In scope

- Create the eight required feature directories.
- Create provider, shell and router boundaries.
- Mechanically relocate declarations currently embedded in `App.tsx` into owned
  modules.
- Preserve all ten view keys, navigation labels, DOM behavior, runtime API contracts,
  CSS selectors and data transforms.
- Add structure and dependency tests that prove the new boundary is real.
- Run rendered browser regression for the current critical workflows.

### Out of scope

- No new product feature, route, visualization, filter or command.
- No CSS redesign or selector renaming.
- No data schema, snapshot or derived-data change.
- No change to proposal authorization, command allowlists, Owner Daily behavior,
  heartbeat/release semantics or static-hosted read-only behavior.
- No reducer action or selector semantic change.
- No orphan or duplicate component deletion; that audit belongs to `S04-P1-T2`.
- No old validator consolidation; that belongs to `S04-P3`.
- No app reinstall, Cloudflare deploy, GitHub push, branch or PR.

## 4. Target Structure

The implementation should converge on this ownership shape. File names may be adjusted
only when the implementation plan identifies a concrete existing naming conflict.

```text
src/
  App.tsx
  app/
    AppProviders.tsx
    FeatureRouter.tsx
    MemoryAtlasShell.tsx
    routeRegistry.ts
  providers/
    AtlasDataProvider.tsx
    AtlasRuntimeProvider.tsx
    AtlasWorkspaceProvider.tsx
  features/
    overview/
      index.ts
      HomeOverviewView.tsx
      RoiDashboard.tsx
      ContributionGrid.tsx
      WordCloudView.tsx
    actions/
      index.ts
      ActionWorkspace.tsx
      ProposalWorkspace.tsx
      WritebackProposalPanel.tsx
    assets/
      index.ts
      GalaxyView.tsx
      ObsidianGraph.tsx
      TimelineView.tsx
    topics/
      index.ts
      DataGuideMap.tsx
      ThemeWorkspaces.tsx
    search-review/
      index.ts
      SearchReview.tsx
      reviewModels.ts
    summary-iteration/
      index.ts
      SummaryIterationView.tsx
      recommendationPanels.tsx
    sync/
      index.ts
      CommandPalettePanel.tsx
      OwnerDailyWorkspace.tsx
    settings/
      index.ts
      AtlasControls.tsx
      InspectorWorkspace.tsx
      MemoryAtlasHelpWorkspace.tsx
  shared/
    atlas/
      filters.ts
      models.ts
      selectors.ts
    runtime/
      guards.ts
      types.ts
```

The tree is a responsibility map, not a mandate to create empty or one-function files.
Only files with extracted behavior are created. Existing specialized components such as
`GalaxyScene`, `ObsidianGraphScene`, `VisualWorkflowWorkbench`, `ProposalEditor` and the
help components are connected through the relevant feature index and are not copied.

## 5. Provider Contracts

### `AtlasDataProvider`

Owns snapshot lifecycle only:

- `atlas`
- `loadState: "loading" | "ready" | "error"`
- `loadError`
- `snapshotLoadedAt`
- `reloadAtlas()`

It calls `loadMemoryAtlas`, cancels stale requests with `AbortController`, retains the
current Chinese error behavior and exposes no feature-specific derived model. A reload
must update the same snapshot object consumed by every feature.

### `AtlasWorkspaceProvider`

Owns user workspace state and deterministic atlas selectors:

- existing `sharedAtlasReducer` state and dispatch
- `activeView`
- canonical `AtlasFilters`
- selected node and selected contribution period
- timeline range
- source-scoped atlas, node map, options and filtered slice
- stable actions for view switch, selection, filter update and reset

It may consume `AtlasDataProvider` to select the same initial node after load/reload.
The first-node rule, reducer action source values and contribution reset behavior remain
byte-for-byte equivalent in observable behavior. Provider extraction is not permission
to alter `sharedAtlasState.ts` semantics.

### `AtlasRuntimeProvider`

Owns local/static runtime detection and operation workspaces:

- runtime state and heartbeat/release lifecycle
- command selection and execution
- proposal review/action state
- Owner Daily open/result state
- fixed local handoff URL and API capability flags

It may consume data/workspace hooks only for existing post-command reload and navigation
effects. Browser callers still cannot provide filesystem paths, argv, validators,
content, environment values or arbitrary URLs. Static hosting remains read-only. The
same-origin endpoints and version identities remain unchanged.

### Composition and update isolation

`AppProviders` composes providers in this order:

```text
AtlasDataProvider
  -> AtlasWorkspaceProvider
    -> AtlasRuntimeProvider
```

Provider values must be memoized. Hooks are domain-specific (`useAtlasData`,
`useAtlasWorkspace`, `useAtlasRuntime`) so a feature cannot depend on an untyped global
bag. Provider modules may depend on data/state/shared modules but never on a feature.

## 6. Shell and Routing

### `MemoryAtlasShell`

The shell owns persistent page composition, not feature business logic:

- top bar and release identity
- navigation groups
- shared controls and interaction lens
- command palette placement
- content grid and persistent side workspaces
- help, action detail, proposal and Owner Daily overlay mounting points

The shell consumes provider hooks and renders feature-owned panels. It does not build
visual models or branch on all ten routes.

### `FeatureRouter`

The router consumes only `activeView` and route-level provider data. It preserves the
exact ten `ViewKey` values and uses an exhaustive route registry. Unknown values fail
closed to the existing search route only if the type/runtime contract already produces
that behavior; otherwise the router must render a bounded error rather than invent a
new redirect.

Primary route ownership is:

| Feature | Primary views |
|---|---|
| overview | `home`, `roi`, `contribution`, `wordcloud` |
| assets | `galaxy`, `obsidian`, `timeline` |
| topics | `notion` |
| search-review | `search` |
| summary-iteration | `summary` |

The other feature domains are persistent or overlay workspaces:

| Feature | Existing surfaces |
|---|---|
| actions | action detail, proposal review/editor, writeback proposal |
| sync | command palette, Owner Daily |
| settings | controls, help, Inspector/explanation |

`routeRegistry.ts` is the single mapping from `ViewKey` to feature route component and
navigation metadata. Feature modules do not import `App`, the shell or another feature.
Cross-feature coordination occurs only through provider contracts or shared typed
models.

## 7. Dependency Rules

Allowed dependency direction:

```text
App -> app shell/router/providers
app shell/router -> feature public indexes + provider hooks
features -> provider hooks + shared + existing leaf components
providers -> data/state/shared
shared -> data/types/config/models
```

Forbidden directions:

- feature -> `App.tsx`
- feature -> `MemoryAtlasShell.tsx`
- feature -> another feature's internal file
- provider -> feature
- shared -> feature/provider/app
- duplicate copies of reducer, runtime request or proposal authorization logic

The structure validator must parse relative imports and fail on these directions. It
must not pass based on marker strings or comments.

## 8. Migration Method

Implementation is a behavior-preserving extraction in dependency order:

1. Add failing structure tests for the thin app, required directories, exhaustive
   route registry and forbidden import directions.
2. Extract pure types, guards, selectors and model builders without changing bodies.
3. Introduce providers around the existing state/effects and prove their public
   contracts with focused tests.
4. Extract feature views and panels, preserving props and DOM order.
5. Introduce the route registry and shell.
6. Replace `App.tsx` with the composition root.
7. Run static, build and rendered user-path regressions.

Moves should be reviewable by preserving function bodies first. Renaming, deduplication
and behavior cleanup are deferred unless TypeScript requires a local name collision to
be resolved. No compatibility wrapper or parallel legacy app remains after the final
step.

## 9. Size and Cohesion Rules

- `App.tsx`: target under 100 lines; absolute task acceptance under 800 lines.
- `MemoryAtlasShell.tsx`: target under 800 lines; hard maximum 1,200 lines.
- Newly extracted feature view/model modules: target under 500 lines.
- Existing specialized renderer components are not split solely for a metric in this
  task, but they must not grow.
- No file is split into pass-through fragments merely to satisfy line counts.
- A module exists only when it has one clear owner and testable contract.

## 10. Error and Loading Behavior

- Snapshot loading and failure remain centralized and cancel-safe.
- Empty-atlas and no-filter-results states remain visually and semantically identical.
- Runtime capability detection retains the 1,200 ms static fallback.
- Heartbeat, `pagehide`, `beforeunload`, visibility and release cleanup remain paired.
- Command/proposal/Owner Daily errors keep bounded Chinese user messages and do not
  expose tokens, absolute paths, payload contents or exceptions.
- Lazy visual imports retain `Suspense` behavior; a failed feature import must surface
  an actionable bounded error, not a blank workspace.

## 11. Verification Contract

### Test-first structural gate

Create a dedicated `S04-P1-T1` validator before implementation. It must fail against the
current monolith and then prove:

- all eight feature directories contain real mounted exports;
- `App.tsx` is below the accepted line limit and contains only provider/shell/router
  orchestration;
- all ten `ViewKey` values appear exactly once in an exhaustive route registry;
- relative import direction follows Section 7;
- no second reducer, runtime endpoint client or legacy app wrapper exists;
- route components are reachable from the production entry graph.

The validator should use the TypeScript compiler API or an equivalent syntax-aware
parser. Comment and substring checks are insufficient evidence.

### Static and build gates

```bash
npm run lint
npm run build
git diff --check
```

### Rendered regression gates

Run the current rendered/runtime validators covering:

- home at `1470x661`, `1440x900` and `390x844`
- six command workflows and static-host handoff
- proposal review, apply, validation rollback and manual rollback
- Owner Daily start, partial failure and retry
- P0 visual workflows and shared filters
- Stage 7 visual/canvas checks
- search/review, summary/iteration and cross-board shared state

The implementation plan must name the exact existing npm scripts after confirming they
still exercise mounted production routes. Source-level legacy validators may be logged
as expected failures only when they inspect historical `App.tsx` strings; they may not
block the refactor or be made green with fake marker comments. Their replacement/removal
is governed by `S04-P3`.

### Baseline comparison

Before editing, capture route/DOM anchors, viewport bounding boxes and deterministic
screenshots for the critical paths. After extraction, compare:

- navigation labels and route keys
- element presence/order and overflow/intersection results
- snapshot counts and selected-filter results
- command/proposal/Owner Daily network request shapes
- canvas nonblank pixel checks for visual routes

Dynamic timestamps and animation frames must use explicit tolerances; broad screenshot
similarity alone is not acceptance.

## 12. Stop and Rollback

Stop the task without claiming completion if any of these occurs:

- a current critical rendered journey regresses;
- data, route or runtime behavior changes beyond mechanical extraction;
- the thin app can be achieved only through a legacy wrapper or duplicated logic;
- a required feature is no longer mounted from the production entry graph;
- the provider graph becomes cyclic;
- `App.tsx` exceeds 1,200 lines or the shell becomes another unbounded monolith;
- disk pressure prevents a complete build, browser run or durable local commit;
- the remote main race reappears before commit and the integration choice is not
  explicitly resolved.

Rollback is a single local commit revert because this task does not mutate raw data,
runtime snapshots, app installations or hosted deployments. Existing user-owned dirty
files outside the task scope remain untouched.

## 13. Acceptance Evidence

`S04-P1-T1` is complete only when all evidence agrees:

1. The production source graph contains the eight feature boundaries and one route
   shell.
2. `App.tsx` is a real composition root, not a marker-bearing wrapper.
3. All ten existing views and persistent action/sync/settings workspaces are mounted.
4. Static checks, production build and relevant rendered browser paths pass.
5. No product, data, authorization, CSS or public behavior change was introduced.
6. The implementation change set has one bounded local commit, separate from this
   preparatory design commit, with no push, branch, PR, deploy or reinstall.

Passing a source-string validator without these runtime proofs is insufficient.
