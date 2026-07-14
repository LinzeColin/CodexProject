# Memory Atlas v1.2.1 S04-P1-T3 Shared State Design

## Scope

This design completes only Task `S04-P1-T3`: establish one contract for global
filters, selection, Memory River time range and Inspector state. It does not start
`S04-P2-T1`, redesign a feature, add a product workflow, or merge the later S15 visual
facet controls into the global filter model.

S04 remains function-frozen. Existing labels, layouts, data, proposal safety and user
journeys must remain unchanged. The only observable synchronization change is that the
Search page query input becomes the same query as the global filter input instead of a
second local copy.

## Current conflicts

The existing reducer already owns the global Atlas filters, selected node and Memory
River range, but three seams can diverge:

- `SearchReview` copies `filters.query` into `useState<Search2Filters>` and then edits
  the copy without writing it back to the shared filter.
- `AtlasWorkspaceProvider` stores a full contribution-period selection in local React
  state while the reducer separately stores only its id. Filter and route actions can
  clear one without clearing the other.
- Inspector focus lives implicitly at `focus.inspector`, Inspector visibility is
  recomputed in the shell, and advanced-detail state is local to `NodeInspector`.

## Selected approach

Evolve the existing reducer rather than add another Context.

`SharedAtlasState` will expose four explicit domains:

1. `filters`: global query/source/tier/category/theme plus shared time range and ROI.
2. `selection`: selected node/cluster/record, time range and contribution-period ids.
3. `focus`: synchronized Home/Galaxy/Timeline/ROI focus targets.
4. `inspector`: one Inspector focus, subject, visibility and advanced-detail state.

The Inspector contract is:

```ts
export type SharedAtlasInspectorSubject = "none" | "node" | "contribution_period";
export type SharedAtlasInspectorVisibility = "side" | "hidden";

export interface SharedAtlasInspectorState {
  focus: SharedAtlasFocusTarget;
  subject: SharedAtlasInspectorSubject;
  visibility: SharedAtlasInspectorVisibility;
  advancedDetailsOpen: boolean;
}
```

`focus.inspector` is removed. Every consumer must use `inspector.focus`, so no legacy
and new Inspector target can disagree.

## State transitions

- `select_node` sets the node selection and Inspector subject, synchronizes every
  focus target, clears contribution-period selection, and closes advanced details.
- `select_time_range` stores one range in `filters.timeRange` and its id in selection;
  route switches do not create a second range.
- `select_contribution_period` sets the shared id and Inspector subject. The full
  render detail remains a provider cache and is returned only when its derived id
  equals the reducer selection id.
- filter mutation/reset and leaving Contribution clear the shared contribution id.
- `switch_view` receives the already-derived Inspector visibility. Hidden Inspector
  state closes advanced details; side-to-side navigation preserves it.
- `set_inspector_advanced_details` is the only writer for advanced-detail visibility.

All selection transitions flow through shared helpers that construct focus and
Inspector state together. No feature component owns a second selected node, global
query, global range, Inspector target or Inspector advanced-details flag.

## Search boundary

Search-specific tier/topic/recency/importance/evidence-only facets remain local because
they are not Atlas-global filters. `query` is removed from local state and derived from
`AtlasFilters.query`. Editing or resetting the Search query dispatches the shared
`set_filter` action through the workspace provider.

`VisualWorkflowWorkbench` source/time/project/task controls remain a local read-only
what-if surface. Their eventual cross-view unification belongs to the explicit S15
tasks and is outside this structural Task.

## Verification

Extend `validate_shared_state_store.mjs` test-first. It must fail until all of these are
true:

- the schema contains the explicit Inspector contract and no `focus.inspector`;
- reducer transitions keep filters, selection, time range and Inspector atomic;
- contribution detail is a cache keyed by the shared selection id, not local selected
  state;
- Search has no local query copy;
- `NodeInspector` has no local advanced-detail state.

Extend the real browser cross-board test to prove:

- changing Search query updates the global filter and persists through route switches;
- a selected node remains the Inspector focus across boards;
- a real Memory River brush range remains shared when navigating to Galaxy/Home;
- Inspector advanced details are reducer-controlled and close when another node is
  selected;
- no actionable console or response errors occur.

Run TypeScript, production build, S04-P1-T1/T2 gates, shared-state unit/browser tests,
Home multi-viewport, proposal E2E, visual workflows and Stage 7 canvas checks. Complete
one read-only reviewer pass, create one bounded local implementation commit, and stop
before `S04-P2-T1`. Do not push, deploy, reinstall or clean caches.
