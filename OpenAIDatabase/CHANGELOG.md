# Changelog

## Unreleased - Memory Atlas v1.1.5 Part 10 Stage 9 Review

- Completed the Part 10 review for Stage 9.1 / 9.2 / Stage 9 overall:
  Obsidian Graph E Iteration, Visual Semantics Enrichment, and whole-stage
  Stage 9 review.
- Added `validate:part10-stage9` to verify Stage 9 review docs, Obsidian
  local graph contracts, visual semantics runtime contracts, visual acceptance
  hooks, production experiment isolation, Stage 9 validators, release audit,
  overall acceptance, and Part 10 records.
- Updated the Stage 9 next gate: part-level review completion now leads to
  whole-project review first; GitHub main upload remains blocked until
  whole-project review passes and final remote checks are complete.

No whole-project review, GitHub main upload, Cloudflare live deploy, Access
policy change, raw/private data access, direct writeback, production runtime
feature work, or external account operation was added.

Machine-readable boundary summary: Stage 9.1 / 9.2 / Stage 9 overall;
whole-project review next; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 9 Stage 8 Review

- Completed the Part 9 review for Stage 8.1 / 8.2 / Stage 8 overall: Local
  App Packaging, Release Safety, and whole-stage Stage 8 review.
- Added `validate:part9-stage8` to verify Stage 8 review docs, local app and
  runtime contracts, renderer rollback contracts, production experiment
  isolation, Stage 8 validators, installed app/runtime acceptance, and Part 9
  records.
- Reinstalled `~/Downloads/Memory Atlas.app` and `/Applications/Memory Atlas.app`
  after the pre-check found `/Applications/Memory Atlas.app` missing and the
  runtime manifest pointing at an older commit.
- Replaced the Stage 8.1 model parameter hard-coded runtime `git_commit` with a
  live audit contract: exact commit is validated by audit, not hard-coded.

No Part 10 review, Stage 9 review, whole-project review, GitHub main upload,
Cloudflare live deploy, Access policy change, raw/private data access, direct
writeback, production runtime feature work, or external account operation was
added.

Machine-readable boundary summary: Stage 8.1 / 8.2 / Stage 8 overall; No Part
10 review; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 8 Stage 7 Review

- Completed the Part 8 review for Stage 7.1 / 7.2 / 7.3 / Stage 7 overall:
  Visual Acceptance, Performance Acceptance, Privacy and Accessibility, and
  whole-stage Stage 7 review.
- Added `validate:part8-stage7` to verify the Stage 7 phase reviews, current
  visual/performance/privacy runtime contracts, visual acceptance hooks,
  production experiment isolation, Stage 7 browser validators, TypeScript /
  Vite build, release audit, and visual and overall acceptance audits.
- Updated stale Stage 7.1 / 7.2 / 7.3 model parameter status lines that still
  said `Stage 7 整体复审未完成` after Stage 7 overall had already passed.

No Part 9 review, Stage 8 review, whole-project review, GitHub main upload,
Cloudflare live deploy, Access policy change, raw/private data access, direct
writeback, production runtime feature work, or external account operation was
added.

Machine-readable boundary summary: Stage 7.1 / 7.2 / 7.3 / Stage 7 overall; No
Part 9 review; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 7 Stage 6 Review

- Completed the Part 7 review for Stage 6.1 / 6.2 / Stage 6 overall: Shared
  State Store, Inspector and Proposal, and whole-stage cross-board sync and
  Inspector review.
- Added `validate:part7-stage6` to verify the Stage 6 phase reviews, current
  shared-state and Inspector/Proposal runtime markers, visual acceptance hooks,
  production experiment isolation, Stage 6 validators, TypeScript / Vite build,
  release audit, and visual and overall acceptance audits.
- Confirmed the app keeps one typed shared selection/filter/time-range/focus
  reducer, exposes shared focus across Home/Galaxy/Timeline/Inspector/ROI, and
  keeps Inspector writeback proposal-only with Debug fields default-closed
  without adding new runtime work in this review.

No Part 8 review, Stage 7 review, whole-project review, GitHub main upload,
Cloudflare live deploy, Access policy change, raw/private data access, direct
writeback, production runtime feature work, or external account operation was
added.

Machine-readable boundary summary: Stage 6.1 / 6.2 / Stage 6 overall; No Part
8 review; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 6 Stage 5 Review

- Completed the Part 6 review for Stage 5.1 / 5.2 / 5.3 / Stage 5 overall:
  River Rendering, River Interaction, Evidence Layers, and whole-stage Memory
  River production integration review.
- Added `validate:part6-stage5` to verify the Stage 5 phase reviews, current
  Memory River runtime markers, visual acceptance hooks, production experiment
  isolation, Memory River phase validators, TypeScript / Vite build, release
  audit, and visual and overall acceptance audits.
- Updated `validate_memory_river_interaction.mjs` to accept the current
  `TimelineTimeRangeSelection = SharedTimelineTimeRangeSelection` alias while
  preserving the selected-range sync contract.
- Confirmed the Timeline board keeps `memory-river` as the default renderer,
  preserves legacy rollback, uses UTC date scaling, exposes Macro/Meso/Micro
  river lanes, supports Pan/Brush, redacted event cards, safe feedback defaults,
  and renders black-hole lifecycle, proto-star lifecycle and stale/deprecated
  evidence layers without adding new runtime work in this review.

No Part 7 review, Stage 6 review, whole-project review, GitHub main upload,
Cloudflare live deploy, Access policy change, raw/private data access, direct
writeback, production runtime feature work, or external account operation was
added.

Machine-readable boundary summary: Stage 5.1 / 5.2 / 5.3 / Stage 5 overall; No
Part 7 review; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 5 Stage 4 Review

- Completed the Part 5 review for Stage 4.1 / 4.2 / 4.3 / Stage 4 overall:
  Rendering Integration, Data Mapping, Starfield Interaction, and whole-stage
  Memory Starfield production integration review.
- Added `validate:part5-stage4` to verify the Stage 4 phase reviews, current
  Starfield runtime markers, visual acceptance hooks, production experiment
  isolation, Starfield mapping and interaction validators, TypeScript / Vite
  build, and visual and overall acceptance audits.
- Updated `validate_memory_starfield_mapping.mjs` to accept the current
  `Memory Terrain v2 analysis panel` runtime marker instead of the older
  Terrain panel marker.
- Confirmed the Galaxy board keeps `memory-starfield` as the default renderer,
  preserves legacy rollback, maps mass/particles/terrain from
  `model_parameters.memory_starfield.yaml`, and exposes transient hover, capped
  click focus, Freeze/Resume Flow, and Presentation/Analysis mode without
  adding new runtime work in this review.

No Part 6 review, Stage 5 review, whole-project review, GitHub main upload,
Cloudflare live deploy, Access policy change, raw/private data access, direct
writeback, production runtime feature work, or external account operation was
added.

Machine-readable boundary summary: Stage 4.1 / 4.2 / 4.3 / Stage 4 overall; No
Part 6 review; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 4 Stage 3 Review

- Completed the Part 4 review for Stage 3.1 / 3.2 / Stage 3 overall: Home
  Information Architecture, Preview Widgets, and whole-stage Home Default Page
  review.
- Added `validate:part4-stage3` to verify the Stage 3 phase reviews, current
  Home runtime markers, visual acceptance hooks, production experiment
  isolation, TypeScript / Vite build, and visual and overall acceptance audits.
- Confirmed the Home board remains the default entry, exposes Memory Weather,
  Black Hole, Proto-Star, proposal-only actions, Mini Starfield, River Pulse
  and Inspector Deep Link without adding new runtime work in this review.

No Part 5 review, whole-project review, GitHub main upload, Cloudflare live
deploy, Access policy change, raw/private data access, direct writeback,
production runtime feature work, or external account operation was added.

Machine-readable boundary summary: Stage 3.1 / 3.2 / Stage 3 overall; No Part
5 review; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 3 Stage 2 Review

- Completed the Part 3 review for Phase 2.1 / 2.2 / 2.3: Default Home
  Integration Plan, Galaxy Replacement Plan, and Timeline Replacement Plan.
- Added `validate:part3-stage2` to verify the three planning contracts, mark
  the Stage 2 runtime assertions as historical, confirm current later-stage
  runtime markers, check production experiment isolation, run the TypeScript /
  Vite build, and run visual and overall acceptance audits.
- Added a Stage 2 historical runtime note so current Stage 3-9 runtime features
  are not mistaken as contradictions of the original planning-stage review.

No Part 4 review, whole-project review, GitHub main upload, Cloudflare live
deploy, Access policy change, raw/private data access, direct writeback,
production runtime feature work, or external account operation was added.

Machine-readable boundary summary: Phase 2.1 / 2.2 / 2.3; Stage 2 historical
runtime note; No Part 4 review; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 2 Stage 1 Review

- Completed the Part 2 review for Phase 1.1 / 1.2 / 1.3: Memory Starfield
  Spike, Memory River Spike, and Universe State Generator Spike.
- Added `validate:part2-stage1` to import the isolated spike fixtures, rerun
  `validate:universe-state-spike`, verify source/runtime contracts, confirm
  production isolation, run the TypeScript/Vite build, and check review,
  delivery and model records.
- Confirmed the Stage 1 spikes remain isolated prototypes with redacted fixture
  data, all-false privacy/writeback flags, and no production React/Three/D3
  integration change.

No Part 3 review, whole-project review, GitHub main upload, Cloudflare live
deploy, Access policy change, raw/private data access, direct writeback,
production React/Three/D3 integration change, or external account operation was
added.

Machine-readable boundary summary: Phase 1.1 / 1.2 / 1.3; No Part 3 review;
No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Part 1 Stage 0 Review

- Completed the Part 1 review for Phase 0.1 Scope & Naming Freeze, Phase 0.2
  product/interaction contracts, and Phase 0.3 isolated spike scaffold
  continuity.
- Added `validate:part1-stage0` to check the Stage 0 scope freeze, Memory
  Overview / Starfield / River / Universe State contracts, visualization
  parameter boundaries, isolated spike fixture safety, production isolation,
  review documentation and delivery/model records.
- Added explicit Phase 0.3 scaffold continuity notes to both runnable Stage 1
  spike README files so the original scaffold evidence remains clear after the
  prototypes became runnable.

No Part 2 review, whole-project review, GitHub main upload, Cloudflare live
deploy, Access policy change, raw/private data access, direct writeback,
production React/Three/D3 integration change, or external account operation was
added.

Machine-readable boundary summary: Phase 0.3 scaffold continuity; No Part 2
review; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Stage 9 Whole-Stage Review

- Completed the Stage 9 whole-stage review across Obsidian Graph E Iteration
  and Visual Semantics Enrichment.
- Added `validate:stage9` to run Stage 9.1 Obsidian validation, Stage 9.2
  visual semantics validation, visual acceptance, release audit, overall
  acceptance, Stage 9 documentation consistency checks, and 4177 cleanup.
- Confirmed Stage 9 keeps bounded Obsidian local graph behavior, sparse/focused
  label rules, Galaxy shared-focus sync, explainable Memory Terrain v2,
  Memory Weather v2, and Galaxy/Memory River ROI capability gradients.

No Cloudflare live deploy, Access policy change, raw/private data access,
direct writeback, external account operation, or Stage 10 feature work was
added.

Whole-project review remains required before GitHub main upload.

## Unreleased - Memory Atlas v1.1.5 Stage 9.2 Visual Semantics Enrichment

- Added Memory Weather v2 on the Home overview with stability, momentum, risk,
  opportunity and confidence signals derived from the existing redacted
  Universe State slice.
- Upgraded Galaxy Analysis Mode to Memory Terrain v2 with semantic roles,
  coverage evidence, terrain intensity and an analysis-only rollback boundary.
- Added ROI capability gradients in Galaxy and Memory River so high-leverage
  and capability-growth trends are visible without changing Presentation mode
  or timeline selection behavior.
- Added `validate:stage9-visual-semantics` and visual acceptance coverage for
  Stage 9.2.

No Stage 9 whole-stage review, GitHub main upload, Cloudflare live deploy,
Access policy change, raw/private data access, direct writeback, or external
account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 9.1 Obsidian Graph E Iteration

- Added bounded local graph neighborhoods for Obsidian Graph so high-connectivity
  focus nodes expose primary/secondary/local-hidden budget evidence without
  flooding the scene.
- Added label visibility rules for selected, hover, local-neighbor, zoom-priority
  and hub states so default labels stay sparse while focused neighborhoods stay
  readable.
- Synced Galaxy cluster focus into Obsidian Graph through shared focus state so
  a Galaxy-selected cluster opens as a bounded local cluster graph.
- Added `validate:stage9-obsidian` and visual acceptance coverage for Stage 9.1.

No Stage 9.2 visual semantics enrichment, Stage 9 whole-stage review,
Cloudflare live deploy, Access policy change, raw/private data access, direct
writeback, or external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 8 Whole-Stage Review

- Completed the Stage 8 whole-stage review across Local App Packaging and
  Release Safety.
- Added `validate:stage8` to run Stage 8.1 packaging validation, Stage 8.2
  release-safety validation, offline Cloudflare Pages + Access preflight,
  Stage 8 documentation consistency checks, and 4177 cleanup assertion.
- Confirmed the reviewed Stage 8 state keeps local app packaging, default
  `记忆总览` routing, Galaxy/Timeline rollback paths, redacted release artifact
  safety, proposal-only writeback, and static deploy readiness.

No Cloudflare live deploy, Access policy change, raw/private data access,
direct writeback, external account operation, or Stage 9 feature work was
added. No raw/private data access or direct writeback was introduced. No direct writeback path was added.

## Unreleased - Memory Atlas v1.1.5 Stage 8.2 Release Safety

- Added `validate:stage8-release-safety` to run a production build, release
  audit, overall acceptance audit, source-contract checks, real-browser
  renderer rollback checks, screenshot capture, console/network checks, docs
  checks, and 4177 cleanup assertion.
- Verified Galaxy rollback through URL, localStorage, environment contract and
  in-app toggle: `memory-starfield` remains the default renderer and `legacy`
  remains the rollback path.
- Verified Timeline rollback through URL, localStorage, environment contract
  and in-app toggle: `memory-river` remains the default renderer and `legacy`
  remains the rollback path.
- Added Stage 8 release notes and Stage 8.2 acceptance/review docs covering
  rollback, safety boundaries, and the next whole-stage review gate.

No Stage 8 whole-stage review, Cloudflare live deploy, Access policy change,
raw/private data access, direct writeback, GitHub main upload, or external
account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 8.1 Local App Packaging

- Added `validate:stage8-local-app` to run a production build, create a
  temporary macOS app bundle, verify launcher single-window behavior, and
  confirm the default production route opens `记忆总览`.
- Hardened `scripts/install_memory_atlas_app.py` for local packaging by adding
  a standard-library `.icns` fallback when Pillow is unavailable, npm-first /
  pnpm-fallback dependency installation and build paths, pnpm dependency
  readiness checks, and managed pid cleanup on normal runtime shutdown.
- Reinstalled and validated the local app bundles at `~/Downloads/Memory
  Atlas.app` and `/Applications/Memory Atlas.app`; the Application Support
  runtime manifest matches the current git HEAD.

No Stage 8.2 release safety work, Cloudflare live deploy, Access policy change,
raw/private data access, direct writeback, GitHub main upload, or external
account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 7 Whole-Stage Review

- Completed the Stage 7 whole-stage review across Visual Acceptance,
  Performance Acceptance, and Privacy/Accessibility.
- Added `validate:stage7` to keep Stage 7 phase review documents, package
  validators, visual acceptance hooks, model parameters, changelog and
  delivery-record status aligned.
- Confirmed the reviewed Stage 7 state keeps real-browser Galaxy and Memory
  River visual gates, FPS/adaptive-quality/cleanup gates, release artifact
  privacy scan, reduced-motion behavior and silent feedback defaults.

No ingestion, raw/private data access, direct writeback, Cloudflare live deploy,
GitHub main upload, or external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 7.3 Privacy and Accessibility

- Added explicit Timeline feedback DOM contracts for reduced motion,
  pseudo-haptic feedback, audio feedback and silent-by-default state.
- Added `validate:stage7-privacy-accessibility` to run a release artifact
  privacy scan, verify the public redacted read-only snapshot contract, confirm
  sourcemaps are absent by default, and test reduced-motion behavior in a real
  browser.
- The Stage 7.3 browser gate emulates `prefers-reduced-motion: reduce`,
  verifies Memory River reduced-motion settings and disabled playback, and
  confirms pseudo-haptic/audio feedback default off without calling vibration
  or `AudioContext`.
- Extended visual acceptance with `stage7_3_privacy_accessibility_ready`.

No Stage 7 whole-stage review, raw/private data access, direct writeback,
Cloudflare live deploy, GitHub main upload, or external account operation was
added.

## Unreleased - Memory Atlas v1.1.5 Stage 7.2 Performance Acceptance

- Added sampled Galaxy FPS metrics, target/min FPS fields and render tick
  telemetry to the WebGL acceptance signal.
- Added an Analysis-mode FPS overlay and an adaptive quality toggle. Adaptive
  quality starts from `mid`, can downgrade or upgrade by sustained FPS, and
  manual `high` / `mid` / `low` selection remains the rollback path.
- Added cleanup lifecycle evidence for Galaxy unmount, including RAF cancel,
  renderer disposal, WebGL context loss, and explicit no Worker/AudioContext
  resources.
- Added `validate:stage7-performance` to run a real-browser production
  preview check for high quality `>=45 FPS`, mid quality `>=30 FPS`, low
  quality non-blank fallback, adaptive quality resume and 4177 cleanup.
- Extended visual acceptance with `stage7_2_performance_acceptance_ready`.

No Stage 7.3 privacy/accessibility gate, Stage 7 whole-stage review, raw/private
data access, direct writeback, Cloudflare live deploy, GitHub main upload, or
external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 7.1 Visual Acceptance

- Added a real-browser Stage 7.1 visual acceptance gate that starts Vite
  preview, captures Galaxy and Memory River screenshots, verifies Galaxy
  WebGL non-empty pixel signal, and releases port 4177 after validation.
- The Galaxy gate checks `memory-starfield` renderer mode, non-legacy fallback,
  lit/alpha/max pixel thresholds, WebGL render stats, terrain features and
  flow-field signal.
- The Memory River gate checks Macro / Meso / Micro labels, UTC scale, lane
  flows, density context, black-hole / proto-star / stale-deprecated evidence
  layers, and required marker types.
- Added `validate:stage7-visual` and extended visual acceptance with
  `stage7_1_visual_acceptance_ready`.

No Stage 7.2 performance gate, Stage 7.3 privacy/accessibility gate, Stage 7
whole-stage review, raw/private data access, direct writeback, Cloudflare live
deploy, GitHub main upload, or external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 6 Whole-Stage Review

- Completed the Stage 6 whole-stage review across Shared State Store and
  Inspector/Proposal.
- Added `validate:stage6` to keep Stage 6 phase reviews, package validators,
  visual acceptance hooks, model parameters, changelog and delivery-record
  status aligned.
- Confirmed the reviewed Stage 6 state keeps typed selection/filter/time-range
  focus sync across Home, Galaxy, Timeline, Inspector and ROI Dashboard, and
  keeps Inspector writeback proposal-only with Debug fields default-closed.

No ingestion, raw/private data access, direct writeback, agent apply CLI,
Cloudflare live deploy, GitHub main upload, or external account operation was
added.

## Unreleased - Memory Atlas v1.1.5 Stage 6.2 Inspector and Proposal

- Added the Inspector explanation panel with human-readable summary, model
  formulas, parameters, redacted evidence and explicit no-raw default marker.
- Moved agent-structured memory/meta fields and low-sensitivity database
  summary behind a default-closed Debug / Agent Inspector toggle.
- Added proposal-only JSON preview and safety strip for writeback; the frontend
  keeps `direct_frontend_mutation_of_active_memory=false` and requires
  agent/human apply.
- Added `validate:inspector-proposal` and extended visual acceptance with
  `stage6_2_inspector_proposal_ready`.

No Stage 6 whole-stage review, agent apply CLI, raw/private data access, direct
active memory writeback, Cloudflare live deploy, GitHub main upload, or external
account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 6.1 Shared State Store

- Added a typed shared-state reducer for Memory Atlas selection, filter, time
  range and focus sync.
- The shared state now records selected node, cluster, record, time range,
  contribution period, signal, data source, layer/tier, theme and ROI filter
  schema fields.
- Home, Galaxy, Timeline, Inspector and ROI Dashboard now expose the same
  shared focus target contract instead of relying only on isolated local
  state.
- Added `validate:shared-state` and extended visual acceptance with
  `stage6_1_shared_state_store_ready`.

No Stage 6.2 Inspector proposal work, raw/private data access, direct active
memory writeback, Cloudflare live deploy, or external account operation was
added.

## Unreleased - Memory Atlas v1.1.5 Stage 5 Whole-Stage Review

- Completed the Stage 5 whole-stage review across Memory River rendering,
  interaction, and evidence layers.
- Added `validate:memory-river-stage5` to keep phase review documents,
  package validators, visual acceptance hooks, model parameters, changelog and
  delivery-record status aligned.
- Confirmed the reviewed Stage 5 state keeps the `memory-river` default,
  `legacy` rollback, UTC scale, Pan/Brush interaction, redacted event card,
  safe feedback defaults, black-hole lifecycle bands, proto-star growth paths
  and stale/deprecated fade layer.

No ingestion, raw/private data access, direct writeback, Cloudflare live
deploy, or external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 5.3 Evidence Layers

- Added Stage 5.3 Memory River evidence layers:
  `black-hole-lifecycle`, `proto-star-lifecycle`, and `stale-deprecated`.
- The black-hole lifecycle band uses the same redacted derived stale /
  needs-review / deprecated / temporary candidate logic as Home Overview risk
  loops, so Timeline and Home stay semantically aligned.
- The proto-star lifecycle layer connects recent opportunity, decision,
  project-context, high-importance and high-leverage signals into a visible
  growth path rather than isolated event dots.
- The stale/deprecated fade layer keeps cooling and deprecated states readable
  without exposing raw transcript data or mutating memory.
- Updated Memory River model parameters, visual acceptance and deterministic
  validators for Stage 5.3.

No Stage 5 whole-stage review, ingestion, raw/private data access, direct
writeback, Cloudflare live deploy, or external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 5.2 Memory River Interaction

- Added Memory River interaction modes: `Pan` for horizontal pointer panning
  and `Brush` for selecting a UTC time range directly on the river canvas.
- Added shared selected-time-range state. Brush selections now render as a
  Memory River range overlay and surface in Interaction Lens, Home Overview and
  Galaxy headings so the selection is visible outside the Timeline page.
- Added hover/click Memory River event cards backed only by redacted derived
  event data. Hover previews the event; click locks it and syncs the Inspector
  when the event has a linked node.
- Added safe feedback settings for Reduced Motion, optional pseudo-haptic
  vibration and optional low-gain audio. Defaults remain no sound and no
  vibration; Reduced Motion stops playback and suppresses optional feedback.
- Updated Memory River model parameters, visual acceptance and deterministic
  validators for Stage 5.2.

No Stage 5.3 evidence layers, Stage 5 whole-stage review, ingestion,
raw/private data access, direct writeback, Cloudflare live deploy, or external
account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 5.1 Memory River Rendering

- Added the production Timeline renderer flag with `memory-river` as the
  explicit default and `legacy` as the rollback mode through URL, localStorage,
  `VITE_MEMORY_ATLAS_TIMELINE_RENDERER`, or the in-app renderer toggle.
- Replaced the default Timeline canvas with a UTC-based Memory River rendering
  path that exposes Macro / Meso / Micro levels, grouped river lanes, readable
  lane labels, density context and UTC cursor/date ticks.
- Added black-hole, proto-star and event markers for high-signal memories while
  preserving the existing legacy Timeline path for rollback.
- Updated the Memory River model parameter file from a Stage 0 template to the
  real Stage 5.1 production contract and marked brush/event-card/multimodal
  interaction as deferred to Stage 5.2.
- Added deterministic `validate:memory-river-rendering` coverage and extended
  visual acceptance with `timeline_stage5_1_river_rendering_ready`.

No Stage 5.2 brush interaction, hover/click event-card workflow, multimodal
feedback, ingestion, raw/private data access, direct writeback, Cloudflare live
deploy, or external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 4.3 Starfield Interaction

- Added Memory Starfield `Freeze Flow Field` / `Resume Flow Field` control so
  users can pause motion for reading and resume the same flow without leaving
  the Galaxy board.
- Promoted the terrain explanation toggle into a formal Presentation /
  Analysis mode selector. Presentation stays clean; Analysis shows formula
  summary, terrain legend and selected-node Inspector context.
- Preserved transient hover preview and capped click-focus behavior while
  adding deterministic interaction contract validation and visual acceptance
  coverage for Stage 4.3.
- Completed the Stage 4 whole-stage review for visual roadmap `记忆星系生产集成`
  with Chrome CDP desktop/mobile screenshot, canvas-pixel and FPS evidence.
- Tightened mobile Galaxy layout so visual-focus controls, delta cards and
  Galaxy scene no longer inherit desktop/tablet minimum widths on 390px
  viewports.

No Timeline replacement, ingestion, raw/private data access, direct writeback,
Cloudflare live deploy, or external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 4.2 Data Mapping

- Added a parameter-backed Memory Starfield mapping module that reads
  `config/visualization/model_parameters.memory_starfield.yaml` through the
  frontend build and exposes the v1.1.5 mass, particle, terrain and quality
  settings to the Galaxy renderer.
- Replaced hardcoded Galaxy mass, particle size, brightness, color and
  trajectory strength calculations with mappings from importance, recency,
  confidence and interaction density.
- Added a subtle Memory Terrain layer for ridge, shoreline, valley, basin and
  fault-line semantics, plus an opt-in Analysis panel explaining the current
  terrain mapping.
- Extended visual acceptance with a deterministic Stage 4.2 data-mapping
  contract.

No Stage 4.3 interaction expansion, Timeline replacement, ingestion,
raw/private data access, direct writeback, Cloudflare live deploy, or external
account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 4.1 Galaxy Rendering Integration

- Added a production Galaxy renderer feature flag with `memory-starfield` as
  the explicit default and `legacy` as the rollback mode through URL,
  localStorage or `VITE_MEMORY_ATLAS_GALAXY_RENDERER`.
- Integrated the Memory Starfield rendering path into the Galaxy board with
  Flow Field motion, trajectory lines, semantic signal markers, compact quality
  controls and a low-quality fallback mode.
- Preserved the existing static nebula fallback for WebGL initialization
  failure and kept legacy Galaxy reachable without changing routes.
- Extended visual acceptance with a deterministic Stage 4.1 Galaxy rendering
  integration contract.

No Stage 4.2 data mapping, Stage 4.3 interaction expansion, Timeline
replacement, ingestion, raw/private data access, direct writeback, Cloudflare
live deploy, or external account operation was added.

## Unreleased - Memory Atlas v1.1.5 Stage 3.2 Preview Widgets

- Added Home Overview preview widgets for Stage 3.2: a lightweight static
  `Mini Starfield`, a recent-topic `River Pulse`, and `Inspector Deep Link`
  cards that preserve the selected focus before switching boards.
- Kept the preview starfield as SVG/CSS only and explicitly avoided loading a
  new WebGL scene on the default home board.
- Extended visual acceptance with a deterministic preview-widget contract check.
- Completed Stage 3 whole-stage review after Stage 3.1 and Stage 3.2 passed
  local validation.

No Galaxy replacement, Timeline replacement, ingestion, raw/private data
access, direct writeback, Cloudflare live deploy, or external account operation
was added.

## Unreleased - Memory Atlas v1.1.5 Stage 3.1 Default Home

- Made `记忆总览` the default Memory Atlas startup board while preserving the
  left sidebar navigation and all existing visual boards.
- Added the first production Home Overview surface with Memory Weather,
  dominant/rising/declining state cards, Black Hole risk, Proto-Star
  opportunity signals, Next Best Actions, and topic/tier/category summaries.
- Kept frontend writeback proposal-only; the Home actions navigate to existing
  review surfaces and never directly mutate active memory.
- Extended visual acceptance with a deterministic default-home contract check.

No Galaxy replacement, Timeline replacement, ingestion, raw/private data access,
direct writeback, Cloudflare live deploy, or external account operation was
added.

## Unreleased - Memory Atlas v1.1.5 Stage 2 Planning

- Added the Stage 2.1 default-home integration plan for making `记忆总览`
  the future startup board while preserving the left sidebar navigation.
- Recorded the current route evidence: production still defaults to `galaxy`,
  and the runtime change is deferred to Stage 3 implementation.
- Added the Stage 2.2 Galaxy replacement plan, including a legacy/new renderer
  feature-flag strategy, starfield extraction boundary, rollback path, and
  screenshot/FPS/privacy validation plan.
- Added the Stage 2.3 Timeline replacement plan, including a legacy/new river
  feature-flag strategy, UTC scale, theme-lane, brush, hover, Inspector sync
  and reduced-motion validation plan.
- Added the Stage 2 review report confirming that Stage 2 changed planning
  artifacts only and did not replace production routes or visual boards.

No production route, raw/private data access, direct writeback, Cloudflare live
deployment, or visual board replacement was added.

## Unreleased - OpenAIDatabase CI Repair

- Restored OpenAIDatabase CI by accepting legacy `sync_runs` records in the evaluator while making future sync logs emit the task-run evidence schema.
- Stabilized generated path strings across Windows/Linux and made the memory-analysis archive step fail closed when `openssl` is unavailable.
- Verified local OpenAIDatabase unittest discovery, personalization export, startup routing, evaluator, py_compile, and changed-scope governance.

No raw export ingestion, plaintext secret persistence, Cloudflare live deployment, Access verification, model calibration claim, or delivery-readiness promotion was added.

## Unreleased - Memory Atlas Data Guide and Cloudflare Preflight

- Renamed the Memory Atlas Notion relationship map to `数据导图` and changed it to a four-column framework map for source/theme, profile/preference, project/decision, and action/opportunity analysis.
- Refreshed the redacted Memory Atlas visualization snapshot for the main-branch deployment build.
- Added Codex memory auto-update runtime support for Monday/Friday 03:00 scheduled refresh and backup flow.
- Re-ran local release, visual, acceptance, Cloudflare Pages + Access preflight, and unit-test gates after merging to main.
- Recorded that live Cloudflare Pages deployment remains blocked by missing local Wrangler authentication and missing `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `MEMORY_ATLAS_ACCESS_HOSTNAME`, and `MEMORY_ATLAS_ALLOWED_EMAIL` environment variables.

No raw exports, plaintext secrets, cookies, browser profiles, direct frontend active-memory mutation, model-calibration claim, or production delivery-readiness promotion was added.

## Unreleased - Other8 S3PDT01 Privacy Boundary

- Added `scripts/privacy_guard.py` to import raw private sources only from external or ignored private locations and persist redacted derived outputs with an audit log.
- Added focused S3PDT01 unittest coverage for synthetic private import redaction, raw-source deletion recovery, rejected leaky derived-tree imports, and current repo privacy scan.
- Extended `.gitignore` to keep `data/raw/` and `data/private_imports/` out of Git by default.
- Recorded S3PD privacy scan evidence without approving real raw export ingestion, cookies, browser profiles, plaintext secrets, or delivery readiness.

No memory extraction heuristic, active parameter value, retrieval behavior, writeback behavior, or production privacy readiness changed.

## 0.2.0 - 2026-06-21

- Added the three-layer private context architecture for core profile, project memory, and behavior history.
- Added generated ChatGPT/Codex personalization exports, Codex config templates, resource routing, evaluation harness, and four redacted run-log categories.
- Added explicit sync-run baseline evidence and tightened the evaluation harness so required run-log categories must contain JSONL records, not only directories.
- Wired Codex sync to regenerate personalization exports after derived data refresh.
- Added focused tests and governance records for `MOD-011`, `FORM-011`, and `PARAM-083` through `PARAM-092`.

## 0.1.0 - 2026-06-20

- Added the first OpenAIDatabase governance baseline for 10 deterministic models, 10 formulas, and 82 documented active parameters.
- Separated product version, model versions, parameter profile versions, data snapshot version, governance spec version, and current gate in `docs/governance/VERSION_MATRIX.yaml`.
- Kept runtime model behavior unchanged; this is a governance documentation and CI mode change only.
