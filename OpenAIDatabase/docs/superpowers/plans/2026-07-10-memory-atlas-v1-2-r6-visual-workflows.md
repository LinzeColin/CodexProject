# Memory Atlas v1.2 R6 P0 Visualization And Filtering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all twelve retained P0 visualizations real decision workflows with
derived source/time/project/task filtering, evidence drill-down, actionable opportunity
details and a no-write Formula what-if interaction.

**Architecture:** Extend the redacted visualization snapshot with bounded facet events
and the tracked Formula preview. Add a pure TypeScript filtering/formula module, then
feed the existing S11 panels from one shared visual workbench. A self-building
Playwright gate verifies all four filter axes and every P0 interaction at three
viewports.

**Tech Stack:** Python 3 standard library, React 19, TypeScript, Vite, Playwright,
`unittest`.

## Global Constraints

- Complete only `R6_P0_VISUALIZATION_AND_FILTERING` in this run.
- Work on canonical local `main`; create no branch, PR, merge or rebase.
- No GitHub push, app reinstall or Cloudflare deployment before R8.
- Preserve the R2 ten-route information architecture and the R3 six-command registry.
- Export only derived facet metadata; no transcript text, credentials, cookies, tokens,
  private imports, absolute paths or raw payloads.
- The exact P0 inventory is twelve IDs from the approved R6 design.
- The literal filter axes are source, time, project and task; theme/category aliases do
  not satisfy acceptance.
- Every retained visual needs a Chinese question, action, evidence and rendered state
  change.
- Formula what-if is no-write preview only and never financial advice.
- Acceptance must exercise `1470x661`, `1440x900` and `390x844`.
- Release status remains `FAIL_REMEDIATION_REQUIRED` after R6.

---

### Task 1: Redacted Facet And Formula Snapshot Contract

**Files:**

- Modify: `scripts/build_memory_atlas_data.py`
- Create: `tests/test_memory_atlas_visual_workflows.py`
- Modify generated: `data/derived/visualization/memory_atlas.json`
- Modify: `apps/memory-atlas/src/types.ts`

**Interfaces:**

- Python: `summarize_behavior_event(item: dict) -> dict`
- Python: `build_visual_workflow_registry(database_dir: Path) -> dict`
- Python: `build_formula_what_if_summary(database_dir: Path) -> dict`
- JSON: `visual_workflows`
- JSON: `behavior_intelligence.facet_events[]`
- JSON: `behavior_intelligence.facet_filter_options`
- JSON: `formula_what_if`

- [ ] Write a failing unit test that creates synthetic Human Question Map, event and
  Formula inputs and requires an exact twelve-entry registry, deterministic normalized
  source/project/task/time metadata, bounded evidence refs and exact no-write safety
  flags.
- [ ] Run `python3 -m unittest tests.test_memory_atlas_visual_workflows -q` and confirm it
  fails because the new snapshot fields are absent.
- [ ] Add failing assertions that transcript/message/credential/token/raw payload keys
  cannot appear in any exported facet event or Formula summary.
- [ ] Implement `HUMAN_QUESTION_MAP_SOURCE`, `BEHAVIOR_EVENT_SOURCE`,
  `FORMULA_WHAT_IF_SOURCE`, strict registry sanitization, stable event sorting, the
  1,000-event cap, normalized `未标注` values and deterministic options.
- [ ] Implement the bounded Formula summary from the tracked preview, preserving
  defaults, bounds, baseline signals, formula source, scenarios and safety.
- [ ] Extend `MemoryAtlas` TypeScript types with the exact optional read-only contracts.
- [ ] Re-run the focused unit test until green.
- [ ] Rebuild `data/derived/visualization/memory_atlas.json`, parse it with
  `python3 -m json.tool`, and confirm raw/private files are unchanged.
- [ ] Commit the data contract locally.

### Task 2: Pure Four-Axis Filtering And Formula Model

**Files:**

- Create: `apps/memory-atlas/src/visualWorkflows.ts`
- Create: `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_visual_models.mjs`
- Modify: `apps/memory-atlas/package.json`

**Interfaces:**

- `VisualWorkflowFilters`
- `buildVisualWorkflowOptions(events) -> VisualWorkflowOptions`
- `filterVisualFacetEvents(events, filters) -> VisualFacetEvent[]`
- `buildVisualFilterSignature(events, filters) -> string`
- `computeFormulaWhatIfScore(preview, weights) -> FormulaWhatIfResult`

- [ ] Write the model validator first using synthetic events with distinct sources,
  dates, projects and tasks plus a synthetic Formula preview.
- [ ] Run `npm run validate:v1.2-visual-models` and confirm failure because the module or
  functions do not exist.
- [ ] Require every filter axis independently and conjunctively changes the exact event
  IDs, with time anchored to the latest valid event.
- [ ] Require invalid dates to fail a bounded time window and `all` to preserve them.
- [ ] Require deterministic option ordering and filter signatures.
- [ ] Require a bounded weight change to alter the Formula score, out-of-range values to
  clamp and Reset/default weights to restore the baseline result.
- [ ] Implement the pure module with no DOM, file, network or runtime API dependency.
- [ ] Run the model validator and TypeScript lint until green.
- [ ] Commit the pure model locally.

### Task 3: Rendered Visual Workbench And RED Browser Gate

**Files:**

- Create first: `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_visual_workflows.cjs`
- Modify: `apps/memory-atlas/package.json`
- Modify: `apps/memory-atlas/src/App.tsx`
- Modify: `apps/memory-atlas/src/styles.css`

**Interfaces:**

- Workbench: `[data-r6-visual-workbench="memory_atlas_visual_workflows.v1_2_r6"]`
- Filters: `[data-r6-filter="source|time|project|task"]`
- Visual cards: `[data-r6-visual-id]`
- Interactive datum/control: `[data-r6-datum]`
- Evidence region: `[data-r6-evidence-workspace]`
- Opportunity detail: `[data-r6-opportunity-detail]`
- Formula score: `[data-r6-formula-score]`

- [ ] Create the Playwright validator before UI changes. It must build the current app,
  serve the tracked snapshot and require all twelve IDs, four real axes, evidence,
  opportunities, Formula change/reset, three-view layout and nonblank screenshots.
- [ ] Run `npm run validate:v1.2-visual-workflows` and confirm expected failure because
  the R6 workbench and literal project/task filters are absent.
- [ ] Add visual-only filter state and four native selects populated from the derived
  facet option sets. Keep global R2 controls unchanged.
- [ ] Filter the facet events once and rebuild all three visual family models from that
  same result. Render matched count, human summary and shared signature.
- [ ] Add one keyboard-operable datum/control to each of the twelve visual cards. Chart
  activation updates selected state and the inline evidence region before navigation.
- [ ] Add the shared evidence region with question, action, next route, event metadata,
  bounded evidence refs and collapsed machine paths.
- [ ] Convert every rendered opportunity item to a button and add inline detail with
  evidence, next step, half-life, defer/Why Not Now and no-pressure boundary.
- [ ] Add bounded Formula range inputs for time saved, reuse and skill compounding,
  visible proxy score/delta and reset; perform no POST or file write.
- [ ] Add responsive styles without nested decorative cards, side-stripe accents,
  fluid type or new routes. Preserve keyboard focus and reduced-motion behavior.
- [ ] Run the browser validator until every required viewport passes.
- [ ] Visually inspect all generated screenshots and fix any overlap, clipping,
  illegible text or incoherent hierarchy.
- [ ] Commit the rendered workflow locally.

### Task 4: Regression, Review And R6 Closeout

**Files:**

- Create: `docs/remediation/memory_atlas_v1_2/R6_P0_VISUALIZATION_AND_FILTERING.md`
- Create: `机器治理/证据与日志/remediation/v1_2_r6/status.json`
- Create: `机器治理/证据与日志/remediation/v1_2_r6/requirements_gap_delta.csv`
- Modify: `docs/remediation/memory_atlas_v1_2/HANDOFF.md`
- Modify: `docs/superpowers/plans/2026-07-10-memory-atlas-v1-2-remediation.md`
- Modify: `功能清单.md`
- Modify: `模型参数文件.md`
- Modify: `开发记录.md`
- Modify: `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
- Modify: `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
- Modify: `CHANGELOG.md`

- [ ] Run focused Python/model tests, `npm run lint`, production build and
  `npm run validate:v1.2-visual-workflows` with tracked R6 evidence output.
- [ ] Re-run R1 Home multiviewport, R3 command, R4 proposal, R5 Owner Daily, Stage 7
  visual and privacy gates.
- [ ] Run the existing S06/S07/S11 validators only as regression evidence; do not use
  their source markers as R6 acceptance.
- [ ] Obtain an independent correctness/security/UX review. Reproduce every High/Medium
  finding with a failing regression before fixing and re-review until none remain.
- [ ] Promote only `S06-AC03`, `S07-AC02`, `S07-AC04`, `S11-AC01`, `S11-AC02`,
  `S11-AC03` and `S11-AC04`. Expected aggregate: `VERIFIED 48 / PARTIAL 5 /
  FAILED 4 / NOT_VERIFIED 1`.
- [ ] Record online/installed app unchanged and release status
  `FAIL_REMEDIATION_REQUIRED`.
- [ ] Mark R5 and R6 plan checkboxes accurately, commit R6 records locally, remove only
  reproducible caches, verify clean worktree/ports/branch/stash and stop before R7.
