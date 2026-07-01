# Changelog

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
