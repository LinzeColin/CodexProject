# Memory Atlas v1.2.1 S04-P1-T2 Mounted UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that every production Memory Atlas UI module is mounted, remove the
unreachable pre-split implementations, and preserve the one `ProposalEditor`
implementation across its two intentional user surfaces.

**Architecture:** Build a TypeScript-AST import graph from `src/main.tsx` that follows
static imports, re-exports and dynamic imports. Compare that graph with runtime source
files outside `src/experiments` and declaration files, then enforce component runtime
references and the exact ProposalEditor mount contract.

**Tech Stack:** React 19, TypeScript 5.9 compiler API, Vite 8, Playwright 1.61, Node.js,
Git.

## Global Constraints

- Complete only `S04-P1-T2`; do not begin `S04-P1-T3`.
- Preserve product behavior, DOM, CSS, data and shared-state semantics.
- Keep `src/experiments` isolated and unchanged; production must not import it.
- Keep one `ProposalEditor` implementation and its two existing proposal-only mounts.
- Do not stage, modify or revert the five dirty `WDA/docs/governance/*` files.
- Do not push, deploy, reinstall, clean caches or create a branch/PR.
- Use one bounded local implementation commit after all gates pass.

---

### Task 1: Add the Production Mount Gate and Prove RED

**Files:**

- Create: `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_1_s04_p1_t2_mounts.mjs`
- Modify: `apps/memory-atlas/package.json`

**Interfaces:**

- Produces: `npm run validate:v1.2.1-s04-p1-t2-mounts`.
- The command exits `1` with sorted orphan/module diagnostics or `0` with reachable
  module, runtime source and mounted component counts.

- [x] **Step 1: Implement graph and component inspection before production cleanup**

The validator must:

```js
const EXCLUDED_RUNTIME_PREFIXES = ["experiments/"];
const PROPOSAL_MOUNTS = new Map([
  ["features/actions/WritebackProposalPanel.tsx", "inspector_writeback_panel"],
  ["features/topics/DataGuideMap.tsx", "data_guide_detail_panel"],
]);
```

Parse `ImportDeclaration`, `ExportDeclaration` and literal dynamic `import()` calls.
Exclude `*.d.ts` from runtime reachability. Fail on unreachable runtime modules,
production-to-experiment imports, top-level uppercase TSX component declarations with
no JSX mount, ProposalEditor declarations other than exactly one, mount files
or source-surface values outside the map, and ProposalDiffPreview mounts outside the
editor.

- [x] **Step 2: Register the package command**

Add exactly:

```json
"validate:v1.2.1-s04-p1-t2-mounts": "node scripts/validate_memory_atlas_v1_2_1_s04_p1_t2_mounts.mjs"
```

- [x] **Step 3: Run the gate and verify the expected RED**

Run:

```bash
npm run validate:v1.2.1-s04-p1-t2-mounts
```

Expected: non-zero and diagnostics for exactly these runtime orphans:

```text
features/overview/WorkflowQuestionPanels.tsx
shared/atlas/graphLayouts.ts
shared/runtime/evidence.ts
```

ProposalEditor must already report one implementation and two approved mount surfaces;
otherwise stop and reconcile the baseline before cleanup.

---

### Task 2: Remove Runtime Orphans and Make Ambient Type Ownership Explicit

**Files:**

- Delete: `apps/memory-atlas/src/features/overview/WorkflowQuestionPanels.tsx`
- Delete: `apps/memory-atlas/src/shared/atlas/graphLayouts.ts`
- Rename: `apps/memory-atlas/src/shared/runtime/evidence.ts` to
  `apps/memory-atlas/src/shared/runtime/evidence.d.ts`
- Modify: `apps/memory-atlas/src/features/overview/HomeOverviewView.tsx`
- Rename/reduce: `apps/memory-atlas/src/features/overview/BehaviorClioEconomicPanels.tsx`
  to `apps/memory-atlas/src/features/overview/BehaviorIntelligencePanel.tsx`
- Modify: `apps/memory-atlas/src/shared/ui/primitives.tsx`
- Modify: `apps/memory-atlas/src/shared/atlas/layoutContracts.ts`
- Modify: `apps/memory-atlas/src/app/FeatureRouter.tsx`
- Modify: `apps/memory-atlas/src/app/routeRegistry.tsx`

**Interfaces:**

- Preserves: all Window runtime evidence types through a declaration-only module.
- Removes: only functions with zero pre-split and current runtime uses.
- Preserves: workflow/question models used by current runtime evidence hooks.

- [x] **Step 1: Delete the two proven runtime-orphan implementation files**

Delete only the workflow panel and graph layout files listed above. Do not delete their
model contracts because `FeatureRouter` still uses those models for the established
runtime evidence functions.

- [x] **Step 2: Rename the Window evidence file to declaration-only ownership**

Move the file byte-for-byte to `evidence.d.ts`. Its `declare global` contract remains
in the TypeScript project while Vite no longer sees it as a possible runtime module.

- [x] **Step 3: Remove the four unused Home and route component props**

Remove `clioLikeVisualModel`, `economicLikeVisualModel`,
`workflowLatentGovernanceVisualModel` and `humanQuestionMapModel` from
`HomeOverviewView`, the route props contract and the Home route invocation. Keep the
model construction and evidence-hook use in `FeatureRouter`.

- [x] **Step 4: Remove the three symbol-level component orphans found by RED**

Reduce the old behavior/clio/economic module to its only mounted component,
`BehaviorIntelligencePanel`, delete `GraphSvgNode`, and remove the now-unused layout
contracts that only supported that primitive.

- [x] **Step 5: Run TypeScript and mount GREEN**

Run:

```bash
npm run lint
npm run validate:v1.2.1-s04-p1-t1-structure
npm run validate:v1.2.1-s04-p1-t2-mounts
```

Expected: all exit `0`; no runtime orphan or unmounted TSX component remains.

---

### Task 3: Verify Both ProposalEditor Surfaces and Product Regression

**Files:**

- Test only; modify implementation only if a regression is proven.

**Interfaces:**

- Inspector mount: `sourceSurface="inspector_writeback_panel"`.
- Data Guide mount: `sourceSurface="data_guide_detail_panel"`.
- Both surfaces: proposal-only, local draft/export, no active-memory mutation.

- [x] **Step 1: Run build and proposal surface gates**

Run:

```bash
npm run build
npm run validate:inspector-proposal
npm run validate:v1.2-proposal-e2e
```

Start a temporary Vite server on port `5173`, run
`npm run validate:data-map-detail-proposal-browser`, then stop the server. That browser
gate must navigate through stable `data-nav-view` attributes and exercise both the Data
Guide and Inspector proposal surfaces.

Expected: all exit `0`; Data Guide and Inspector both reach the same editor contract.

- [x] **Step 2: Run the mounted product regression set**

Run:

```bash
npm run validate:v1.2-home-multiviewport
npm run validate:v1.2-visual-workflows
npm run validate:stage7-visual
```

Expected: all exit `0`, screenshots/canvas checks remain nonblank and no old workflow
panel is newly mounted.

- [x] **Step 3: Run independent read-only review**

Ask the existing reviewer to inspect runtime graph exclusions, component-use detection,
ProposalEditor mount proof and deletion safety. Resolve every Blocking or Important
finding before commit.

---

### Task 4: Scope Audit and Local Implementation Commit

**Files:**

- Include: this plan and the exact app files listed above.
- Exclude: WDA, data, runtime outputs, screenshots, build outputs and caches.

- [x] **Step 1: Audit diff, protected scope and listeners**

Run:

```bash
git diff --check
git diff --name-status
git status --short --branch
lsof -nP -iTCP:4177 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

Expected: clean diff; only S04-P1-T2 plus five unstaged WDA files; no validation server.

- [x] **Step 2: Stage only the Task and commit locally**

Run:

```bash
git add -- OpenAIDatabase/apps/memory-atlas \
  OpenAIDatabase/docs/superpowers/plans/2026-07-13-memory-atlas-v1-2-1-s04-p1-t2-mounted-ui.md
git diff --cached --check
git diff --cached --name-status
git -c gc.auto=0 commit -m "refactor(memory-atlas): remove orphan UI paths (S04-P1-T2)"
```

- [x] **Step 3: Verify the durable stop state**

Run:

```bash
git fsck --connectivity-only --no-dangling
git status --short --branch
git rev-list --left-right --count HEAD...origin/main
```

Expected: only five WDA files remain dirty, local main is ahead, origin is not ahead,
and no push occurred. Stop before `S04-P1-T3`.

## Execution Notes

- The RED gate found the three expected runtime orphans and three additional
  symbol-level component orphans: `ClioLikeVisualPanel`, `EconomicLikeVisualPanel` and
  `GraphSvgNode`.
- The four visual models remain constructed in `FeatureRouter` for evidence contracts;
  only unused component-prop plumbing was removed.
- `validate_inspector_proposal.mjs` now inspects the split implementation modules and
  the current advanced-detail copy instead of the compatibility shell.
- `validate_shared_state_store.mjs` now inspects the provider and mounted view modules
  that own the shared-state bindings instead of the compatibility shell.
- `validate_data_map_detail_proposal_browser.cjs` now uses stable route attributes and
  proves both approved ProposalEditor mount surfaces without mutating active memory.
- Reviewer regression coverage proved that a metadata-only reference no longer counts
  as a component mount; the gate now requires an actual JSX mount.
