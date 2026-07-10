# Memory Atlas v1.2 R6 P0 Visualization And Filtering Design

## Decision Status

This design implements only `R6_P0_VISUALIZATION_AND_FILTERING` from the approved
R0-R8 remediation plan. It does not implement R7 snapshot parity/raw recovery, R8
overall acceptance, Git reconciliation, GitHub push, app reinstall or Cloudflare
deployment.

The restored TaskPack, R0 gap matrix and current runtime agree that source markers and
visual configuration files do not prove a visual workflow. R6 requires every retained
P0 chart to answer a Chinese human question, expose an action and real evidence, accept
the exact source/time/project/task filters, and change rendered state after interaction.

## Authoritative P0 Inventory

The restored Roadmap and UI/UX specification require the union of the ten machine-
registry visuals plus Topic/Cluster Explorer and Opportunity Radar:

1. `cluster_tree`
2. `bubble_map`
3. `topic_cluster_explorer`
4. `task_treemap`
5. `automation_vs_augmentation`
6. `roi_scatter`
7. `opportunity_radar`
8. `agent_decision_sankey`
9. `friction_heatmap`
10. `latent_radar`
11. `evidence_timeline`
12. `formula_explorer`

All twelve remain P0 because they already have an accepted human question and action
value in `human_question_map.v1_2_s11_p4.json`. Decorative density clouds and raw
conversation heat glow remain excluded.

## Current-State Contradiction

The current UI labels four filter dimensions but does not implement their literal
contract:

- source is a real `AtlasFilters.source` value;
- time is only a Memory River range selected elsewhere;
- project is displayed from `filters.theme`;
- task is displayed from `filters.category`.

The public `memory_atlas.json` does not carry the safe event facets that already exist
in `data/derived/behavior_intelligence/events.json`. Consequently the browser cannot
choose real project/task values or prove that those selections change chart data. R6
must repair the data contract before changing UI labels or adding acceptance markers.

## Rejected Approaches

### Keep Theme And Category Aliases

Renaming theme to project and category to task would preserve the current mismatch and
could pass only source-level validators. It is rejected because the restored source
package explicitly defines project and task type as independent canonical facets.

### Add Hidden Data Attributes Only

Adding `data-filter-project` and `data-interactive=true` without visible controls,
changed marks and an evidence result would repeat the failed historical acceptance
pattern. R6 data attributes may aid automation but never substitute for rendered
behavior.

### Build A New Route And Rewrite Every Visualization

A new navigation route would disturb the ten-route R2 information architecture and
duplicate the accepted S11 panels. R6 keeps the existing Home decision surface and
adds one compact shared workbench immediately before the retained visual families.

## Safe Derived Snapshot Contract

`scripts/build_memory_atlas_data.py` adds three bounded, redacted contracts to the
public derived snapshot.

### Visual Workflow Registry

`visual_workflows` is a sanitized copy of the tracked Human Question Map. It contains
the schema version, exact twelve P0 entries, excluded candidates and the four declared
filter dimensions. Each retained entry is limited to:

```text
id, family, title_zh, insight_header_zh, human_question_zh,
action_value_zh, visual_roi_gate_pass, p0_included
```

The builder fails closed to an empty registry if the source schema is invalid. The
frontend uses this contract as the source of displayed questions/actions and verifies
that the exact twelve IDs are present; `App.tsx` marker strings are not the registry.

### Facet Events

`behavior_intelligence.facet_events` contains only derived event metadata:

```text
event_id, occurred_at, source_id, project, task_type, topic,
intent, friction, value_signal, evidence_refs
```

It excludes transcript text, user/assistant messages, credentials, cookies, tokens,
absolute paths and raw payloads. Null project and unknown task values normalize to the
Chinese label `未标注`, while the original source file remains unchanged. Evidence refs
are limited to three bounded entries per event and use the existing public metadata
shape.

The snapshot also records `facet_event_count` and deterministic option sets for source,
project and task. The builder caps the exported events at 1,000 after stable sorting by
`occurred_at,event_id`; the current source has 217 events.

### Formula What-If Preview

`formula_what_if` summarizes the existing derived preview without introducing a new
formula or writing configuration. It includes:

```text
schema_version, simulator_mode, base_score, summary_zh,
default_weights, adjustable_weight_bounds, baseline_signals,
rework_score, formula_source, scenarios, safety
```

Safety is explicit: `active_config_write=false`,
`proposal_required_before_apply=true`, `raw_mutation=false`,
`financial_advice=false` and `precise_income_prediction=false`.

## Four-Axis Filter Contract

R6 owns a visual-only state separate from the global R2 filters:

```ts
interface VisualWorkflowFilters {
  source: string;  // all or exact facet source_id
  time: "all" | "30d" | "90d" | "365d";
  project: string; // all or exact normalized project
  task: string;    // all or exact normalized task_type
}
```

`filterVisualFacetEvents()` applies all four predicates conjunctively. Time windows are
anchored to the latest valid facet event, not the current wall clock, so a restored
snapshot remains deterministic. Invalid dates never receive fabricated timestamps and
do not match a bounded time window.

The workbench exposes four labelled native selects and one reset icon button. Every
selection visibly changes the matched event count, a human-readable filter summary and
the chart model signature. Options with zero records under the other selected axes may
remain selectable so the empty state can be inspected; empty results explain which
filter to relax.

## Event-Backed Visual Models

The existing React/SVG layouts remain, but their copy comes from `visual_workflows` and
their data is rebuilt from filtered facet events instead of treating theme/category as
project/task:

- Clio visuals aggregate `topic` and source evidence.
- Economic visuals aggregate `task_type`, value signals, freshness and friction.
- Workflow/governance visuals aggregate intent, friction, evidence and time.
- Evidence Timeline uses `occurred_at` and public evidence refs.
- Formula Explorer uses the tracked what-if preview.

Memory nodes remain available only as optional navigation targets. A representative
node is selected by a bounded topic/project/task text match with a deterministic
fallback; it is never used as proof that the facet exists.

Each model exposes the same exact `filterSignature` and `filteredEventCount`. Every
visual section renders both so Playwright can correlate visible chart changes with the
actual filtered event set.

## Evidence And Interaction Contract

The shared visual workbench owns one inline evidence region, not a modal. Selecting a
chart or datum updates:

```text
visual_id, datum_label, Chinese question, action value, next action,
matched event count, source/project/task/time summary, evidence refs
```

Machine paths remain under a collapsed details element. The visible evidence list uses
source, date, topic and evidence level. The action button may navigate to the existing
Galaxy, Search, ROI, Summary or Timeline route after the user has reviewed evidence.

Every P0 chart must contain at least one keyboard-operable datum or parameter control
whose activation changes the inline evidence region, selected state or formula score.
An inspect marker alone is insufficient if chart marks remain inert.

## Opportunity Drill-Down

Every rendered opportunity card becomes a button. The selected detail shows all of:

- Chinese summary;
- evidence refs and evidence count;
- exact next step;
- opportunity half-life;
- defer reason or Why Not Now reason;
- not-pressure-list boundary.

The detail is inline and keeps the opportunity list visible. It does not create or
apply a proposal.

## Formula What-If Interaction

Formula Explorer exposes three bounded range inputs for:

- `time_saved_weight`;
- `reuse_value_weight`;
- `skill_compounding_weight`.

The score uses the tracked baseline signal scores and existing S07 formula:

```text
positive = weighted mean(time, reuse, opportunity, skill, automation)
penalty = max(0, rework_score - neutral_rework_score)
          * rework_cost_weight
          * low_value_loop_penalty_weight
          * rework_penalty_scale
score = clamp(round(positive - penalty), score_floor, score_ceiling)
```

Changing any of the three exposed weights must update the visible proxy score and delta
without writing files, calling the runtime API or applying a proposal. Reset restores
the tracked defaults. The UI states that the result is an internal proxy, not income or
financial advice.

## Browser Acceptance

`validate:v1.2-visual-workflows` builds the current frontend and serves the tracked
snapshot. For each of `1470x661`, `1440x900` and `390x844`, it must prove:

- exactly twelve retained P0 visual IDs are reachable;
- every visual has a non-empty Chinese question, action and evidence interaction;
- source, time, project and task each have a non-all option from real facet events;
- selecting each axis reduces or otherwise changes the matched event set and all visual
  family signatures;
- each visual's real datum/control changes selected state, evidence or formula score;
- every opportunity detail contains evidence, next step, half-life and defer/Why Not
  Now information;
- the Formula Explorer score changes after a bounded parameter input and resets;
- no visual/workbench element has horizontal overflow or incoherent overlap;
- screenshots are nonblank and all preview ports are released.

Source-level S11 validators remain regressions only. R6 PASS requires this rendered
runtime evidence.

## Requirement Impact

R6 may promote:

- `S06-AC03`: PARTIAL -> VERIFIED;
- `S07-AC02`: PARTIAL -> VERIFIED;
- `S07-AC04`: PARTIAL -> VERIFIED;
- `S11-AC01`: PARTIAL -> VERIFIED;
- `S11-AC02`: PARTIAL -> VERIFIED;
- `S11-AC03`: FAILED -> VERIFIED;
- `S11-AC04`: NOT_VERIFIED -> VERIFIED.

The six other R6-assigned rows remain VERIFIED with stronger browser evidence. Expected
aggregate after R6:

```text
VERIFIED 48 / PARTIAL 5 / FAILED 4 / NOT_VERIFIED 1
```

Release status remains `FAIL_REMEDIATION_REQUIRED`.

## Rollback And Stop

Revert only R6 commits after R5 closeout `2295074a2`. Rebuild the prior derived snapshot
from the prior builder if the tracked snapshot is reverted. Raw, credentials, installed
apps, Cloudflare and GitHub main are outside this phase.

Stop after the local R6 closeout commit and reproducible cache cleanup. Do not start R7,
merge/rebase, push, create a PR, reinstall or deploy in this run.
