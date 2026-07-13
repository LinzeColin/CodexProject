# Memory Atlas v1.2.1 S04-P1-T2 Mounted UI Design

## Scope and decision

This design completes only Task `S04-P1-T2`: migrate the remaining component/type
ownership left by `S04-P1-T1`, remove production modules that are not mounted, and
prove that every production UI component has a runtime path. Product behavior, DOM,
CSS, data, shared-state semantics and proposal safety remain frozen.

The selected approach is a strict production import graph. It includes static imports,
re-exports and dynamic `import()` calls from `src/main.tsx`; it excludes declaration
files and the explicitly isolated `src/experiments` prototypes. Production code must
not import those experiments.

Two alternatives are rejected:

- Mounting the old workflow/question panels would add UI that was not rendered before
  the feature split and would violate the functional freeze.
- Deleting the isolated experiments now would break explicit spike validators and
  model-parameter references; final prototype cleanup belongs to the later release
  cleanup Task.

## Component ownership

The current graph has three non-experiment runtime orphans:

- `features/overview/WorkflowQuestionPanels.tsx` contains old component declarations
  that were present but never rendered in the pre-split `App.tsx`.
- `shared/atlas/graphLayouts.ts` contains layout helpers that were never called in the
  pre-split app and are not used by the current renderers.
- `shared/runtime/evidence.ts` is not runtime code. It is an ambient `Window` type
  contract and will become `evidence.d.ts` so its compile-time role is explicit.

The first two modules will be deleted. `HomeOverviewView` and the route shell will stop
accepting four unused visual-model props. The models themselves remain in
`FeatureRouter` because the established runtime evidence hooks still consume them. No
live component will be moved solely to make the directory tree look cleaner,
especially the large scene renderers whose split is outside this Task.

The test-first RED run also found three symbol-level component orphans inside reachable
modules: `ClioLikeVisualPanel`, `EconomicLikeVisualPanel` and `GraphSvgNode`. The first
two are removed by reducing the old overview module to its only mounted export,
`BehaviorIntelligencePanel`; the primitive is deleted directly.

## ProposalEditor contract

`ProposalEditor` is one shared implementation with two intentional mount surfaces:

1. `features/actions/WritebackProposalPanel.tsx` for the Inspector writeback path.
2. `features/topics/DataGuideMap.tsx` for the wide Data Guide detail path, where the
   side Inspector is intentionally not mounted.

These are not duplicate implementations. Both must resolve to the same
`components/ProposalEditor.tsx`, use distinct fixed `sourceSurface` values, remain
proposal-only and never mutate active memory directly. `ProposalDiffPreview` remains
reachable only through this editor.

## Acceptance validator

Add `validate_memory_atlas_v1_2_1_s04_p1_t2_mounts.mjs` and its package command. It
must fail when:

- a non-declaration production source module is unreachable from `src/main.tsx`;
- production imports an isolated experiment;
- an uppercase top-level TSX component has no JSX mount;
- `ProposalEditor` has more than one implementation or differs from its two approved
  mount files/source-surface values;
- `ProposalDiffPreview` is mounted outside `ProposalEditor`.

Existing proposal validators must read the split implementation modules rather than
the compatibility `App.tsx` shell. The browser validator must navigate by stable route
attributes and prove both approved ProposalEditor surfaces in the real app.
The shared-state source validator must likewise inspect its provider and mounted views,
not the compatibility shell left by `S04-P1-T1`.

The validator must first fail against the current three orphan modules. After cleanup,
it must report the reachable module and mounted component counts.

## Verification and stop state

Run TypeScript, production build, the `S04-P1-T1` structure gate, the new mount gate,
Home multi-viewport, Data Guide proposal, Inspector proposal, visual workflows and
proposal E2E. Compare ProposalEditor mount behavior with the pre-split baseline and
run an independent read-only review.

Create one bounded local implementation commit after all checks pass. Do not stage the
five existing WDA changes, push, deploy, reinstall, clean caches or begin
`S04-P1-T3`. Rollback is `git revert` of the bounded implementation commit.
