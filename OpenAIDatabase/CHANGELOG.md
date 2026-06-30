# Changelog

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
