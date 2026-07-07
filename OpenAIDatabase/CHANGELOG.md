# Changelog

## Unreleased - Memory Atlas v1.1.7 Stage 2 Phase 2.2

- Added `apps/memory-atlas/src/components/ProposalEditor.tsx` to expose the
  first proposal UI controls for `importance` and `priority`.
- Added `apps/memory-atlas/src/components/ProposalDiffPreview.tsx` to show
  `original_value`, `proposed_value`, `impact_summary` and `rollback_metadata`.
- Integrated `ProposalEditor` into the existing Inspector writeback panel while
  preserving `proposal_only`, no direct writeback and human/agent apply gates.
- Updated `docs/architecture/proposal_edit_model.md` with
  `proposal_ui_v1_1_7_stage2_phase2`, `memory_atlas_proposal_export.v1` and the
  Export / Rollback Contract.
- Added
  `docs/acceptance/memory_atlas_v1_1_7_stage2_phase2_proposal_ui_acceptance.md`.
- Added `validate:v1.1.7-stage2-phase2` and registered
  `MA-V117-S2P02` / `ACC-MA-V117-S2P02` with status
  `phase_2_2_proposal_ui_completed_pending_stage2_review`.

No Search 2.0 runtime, Review workflow runtime, Data Map 2.0 runtime,
raw/private data read, direct writeback, agent apply, production build, local
app install, browser screenshot, deploy or GitHub main upload was added.

Machine-readable boundary summary: Proposal UI; ProposalEditor;
ProposalDiffPreview; Export / Rollback Contract; No GitHub main upload before
whole Stage 0-10 completion.

## Unreleased - Memory Atlas v1.1.7 Stage 2 Phase 2.1

- Added `docs/architecture/proposal_edit_model.md` with the
  `proposal_edit_model_v1_1_7_stage2_phase1` contract for Editable Draft Model.
- Added
  `docs/acceptance/memory_atlas_v1_1_7_stage2_phase1_editable_draft_acceptance.md`.
- Added `apps/memory-atlas/src/state/proposalDraftStore.ts` with the
  `memory_atlas_proposal_draft.v1` schema, `memory-atlas.proposal-drafts.v1`
  local draft store key, refresh warning helper, undo draft change helper and
  proposal-only safety metadata.
- Updated `config/visualization/model_parameters.universe_state.yaml` to
  register `MA-V117-S2P01` / `ACC-MA-V117-S2P01`, the editable whitelist
  `importance`, `priority`, `status`, `theme_override`, `action_state`, `note`,
  draft target types and draft statuses.
- Added `validate:v1.1.7-stage2-phase1` to verify the Editable Draft Model,
  Draft State Store, records, package script and changed-path boundary.
- Registered status
  `phase_2_1_editable_draft_model_completed_pending_stage2_review`.

No Proposal UI, Proposal Diff Preview, proposal JSON export, Search 2.0
runtime, Review workflow runtime, Data Map 2.0 runtime, raw/private data read,
direct writeback, agent apply, production build, local app install, browser
screenshot, deploy or GitHub main upload was added.

Machine-readable boundary summary: Editable Draft Model; Draft State Store; No
Proposal UI; No GitHub main upload before whole Stage 0-10 completion.

## Unreleased - Memory Atlas v1.1.7 Stage 1 Review

- Added `docs/reviews/memory_atlas_v1_1_7_stage1_review.md` to pin the
  completed Stage 1 review gate.
- Added `validate:v1.1.7-stage1` to validate Stage 0 review continuity, Phase
  1.1 Universe State, Phase 1.2 Next Action, Phase 1.3 Level Asset, Phase 1.4
  Topic Classification, records, package script and no-upload boundary.
- Registered `MA-V117-S1-REVIEW` / `ACC-MA-V117-S1-REVIEW` with status
  `stage_1_review_passed_pending_stage2_no_github_main_upload`.
- Marked Stage 1 as review-passed and pending Stage 2 while preserving
  `No GitHub main upload` before the whole Stage 0-10 project is complete.

No Stage 2 work, proposal editor, Search 2.0 runtime, Review workflow runtime,
Data Map 2.0 runtime, raw/private data read, direct writeback, proposal write,
agent apply, production build, local app install, browser screenshot, deploy or
GitHub main upload was added.

## Unreleased - Memory Atlas Phase 1 Live URL Readiness Repair

- Added the `validate:stage8-local-app-packaging` alias for the canonical local app packaging gate.
- Repaired Stage 3, Stage 6, whole-project, and visual audit validators so local readiness gates do not fail on known false positives.
- Removed a tracked encrypted session-history key from the release branch and recorded the governance boundary for the repair.
- Re-ran local lint, build, Stage 8 release safety, local app, packaging, whole-project, offline Cloudflare Pages + Access preflight, and changed-only governance gates.

No Cloudflare live deploy, Access policy mutation, memoryatlas.linzezhang.com publish, raw export ingestion, plaintext secret persistence, dist commit, or node_modules commit was added.

## Unreleased - macdata proM2 Controlled Archive

- Added `OpenAIDatabase/macdata/proM2` as a controlled Codex Automation task pack for this MacBook Pro.
- Updated the device preflight to use the owner-confirmed local hardware truth: MacBook Pro / Mac14,5 / Apple M2 Max / 32GB.
- Added owner confirmations for GitHub upload, plaintext non-credential device metrics, no Time Machine, no iCloud, and verified-upload-before-cleanup.
- Added remote-verified cleanup policy for Docker, Homebrew, system cache best-effort purge, and project cache whitelist deletion.
- Added focused package tests and governance records for the macdata setup.
- Fixed `last_run_status.json` so it records raw archive, report archive, top-level `ok`, archive branch, and final remote verification after the report upload completes.
- Added post-run GitHub/Codex hygiene so verified runs can close/delete managed, merged temporary PRs/branches/issues while protecting `main` and `macdata-proM2`.
- Restored proM2 MacData Chinese report artifacts to Markdown `.md` files for latest, draft, and final reports per owner instruction.

No API key, token, password, cookie, session, Keychain item, shell history, full environment dump, `.env` raw content, Time Machine data, or iCloud data is collected.
## Unreleased - Memory Atlas v1.1.7 Stage 1 Phase 1.4

- Added `docs/architecture/theme_category_model.md` with the
  `theme_category_model_v1_1_7_stage1_phase4` model contract for concrete
  Topic Classification details.
- Added
  `docs/acceptance/memory_atlas_v1_1_7_stage1_phase4_topic_classification_acceptance.md`.
- Added `apps/memory-atlas/src/components/ThemeDetailPanel.tsx` and updated
  `App.tsx` / `styles.css` so Home Overview renders Topic Classification cards
  and a `ThemeDetailPanel` with `topic_strength`, `trend`, `roi_score`,
  `conflict_score`, `matched_reason`, representative records, evidence,
  linked assets/actions, Starfield handoff, River handoff and `proposal_only`
  safety hints.
- Updated `config/visualization/model_parameters.universe_state.yaml` to
  register `MA-V117-S1P04` / `ACC-MA-V117-S1P04`, required topic fields,
  `topic_classification_sort_weights`, `top_topic_limit: 10` and proposal-only
  gates.
- Added `validate:v1.1.7-stage1-phase4` to verify the model contract,
  runtime implementation, panel, styles, records and changed-path boundary.
- Registered status
  `phase_1_4_topic_classification_detail_completed_pending_stage1_review`.

No Stage 1 review, Stage 2 proposal editor, Search 2.0 runtime, Review
workflow runtime, Data Map 2.0 runtime, raw/private data read, direct
writeback, proposal write, agent apply, production build, local app install,
browser screenshot, deploy or GitHub main upload was added.

Machine-readable boundary summary: Topic Classification runtime detail only;
ThemeDetailPanel is proposal_only; No direct writeback; No GitHub main upload
before whole Stage 0-8 completion.

## Unreleased - Memory Atlas v1.1.7 Stage 1 Phase 1.3

- Added `docs/architecture/level_asset_model.md` with the
  `level_asset_model_v1_1_7_stage1_phase3` model contract for concrete
  Level Asset details.
- Added
  `docs/acceptance/memory_atlas_v1_1_7_stage1_phase3_tier_asset_acceptance.md`.
- Added `apps/memory-atlas/src/components/AssetDetailPanel.tsx` and updated
  `App.tsx` / `styles.css` so Home Overview renders Level Asset cards and an
  `AssetDetailPanel` with `value_score`, `staleness_status`, theme, updated
  time, evidence, linked actions/topics, recommended asset action and
  `proposal_only` safety hints.
- Updated `config/visualization/model_parameters.universe_state.yaml` to
  register `MA-V117-S1P03` / `ACC-MA-V117-S1P03`, required asset fields,
  `tier_asset_sort_weights`, `top_asset_limit: 7` and proposal-only gates.
- Added `validate:v1.1.7-stage1-phase3` to verify the model contract,
  runtime implementation, panel, styles, records and changed-path boundary.
- Registered status
  `phase_1_3_tier_asset_detail_completed_pending_stage1_review`.

No Phase 1.4 topic classification model, proposal editor, raw/private data
read, direct writeback, proposal write, agent apply, production build, local
app install, browser screenshot, deploy or GitHub main upload was added.

Machine-readable boundary summary: Level Asset runtime detail only;
AssetDetailPanel is proposal_only; No direct writeback; No GitHub main upload
before whole Stage 0-8 completion.

## Unreleased - Memory Atlas v1.1.7 Stage 1 Phase 1.2

- Added `docs/architecture/next_action_model.md` with the
  `next_action_model_v1_1_7_stage1_phase2` model contract for sortable
  Next Action details.
- Added
  `docs/acceptance/memory_atlas_v1_1_7_stage1_phase2_next_action_acceptance.md`.
- Added `apps/memory-atlas/src/components/ActionDetailDrawer.tsx` and updated
  `App.tsx` / `styles.css` so Home Overview renders Top 5 Next Action cards
  and an Action Detail Drawer with `roi_score`, effort cost, `urgency`,
  source, evidence, status, linked context, next step and `proposal_only`
  safety hints.
- Updated `config/visualization/model_parameters.universe_state.yaml` to
  register `MA-V117-S1P02` / `ACC-MA-V117-S1P02`, required action fields,
  `next_action_sort_weights`, `top_action_limit: 5` and proposal-only gates.
- Added `validate:v1.1.7-stage1-phase2` to verify the model contract,
  runtime implementation, drawer, styles, records and changed-path boundary.
- Registered status
  `phase_1_2_next_action_detail_completed_pending_stage1_review`.

No Phase 1.3 tier asset model, Phase 1.4 topic classification model,
proposal editor, raw/private data read, direct writeback, proposal write,
agent apply, production build, local app install, browser screenshot, deploy or
GitHub main upload was added.

Machine-readable boundary summary: Next Action runtime detail only; Action
Detail Drawer is proposal_only; No direct writeback; No GitHub main upload
before whole Stage 0-8 completion.

## Unreleased - Memory Atlas v1.1.7 Stage 1 Phase 1

- Updated `docs/architecture/universe_state_snapshot.md` with the v1.1.7
  Stage 1 Phase 1 Universe State schema and consumer-map addendum.
- Updated `config/visualization/model_parameters.universe_state.yaml` to
  register `MA-V117-S1P01` / `ACC-MA-V117-S1P01`, required state fields,
  required consumers and deferred later-phase work.
- Updated `apps/memory-atlas/src/models/universeState.ts`,
  `apps/memory-atlas/src/fixtures/universe_state.schema.json` and
  `apps/memory-atlas/src/fixtures/universe_state.sample.json` so the
  deterministic Universe State fixture exposes `data_map_2_0`,
  `search_2_0` and `review_summary_iteration` consumer maps.
- Added
  `docs/acceptance/memory_atlas_v1_1_7_stage1_phase1_universe_state_acceptance.md`.
- Added `validate:v1.1.7-stage1-phase1` to rerun the Universe State spike
  validator, check proposal-only actions, privacy flags, sample/schema/model
  alignment, records and changed-path boundaries.
- Registered status
  `phase_1_1_universe_state_schema_completed_pending_stage1_review`.

No Phase 1.2 suggested-action UI, tier asset model, topic model, runtime UI,
CSS, browser screenshot, production build, local app install, raw/private data
read, direct writeback, proposal write, agent apply, deploy or GitHub main
upload was added.

Machine-readable boundary summary: No Phase 1.2 work; No raw/private data read;
No direct writeback; No proposal write; No GitHub main upload before whole
Stage 0-8 completion.

## Unreleased - Memory Atlas v1.1.7 Stage 0 Review

- Added `docs/reviews/memory_atlas_v1_1_7_stage0_review.md`.
- Added `validate:v1.1.7-stage0` to run Phase 0.1, Phase 0.2 and Phase 0.3
  validators, verify the Stage 0 review artifact, confirm canonical remote /
  sparse boundary and check governance records.
- Registered `MA-V117-S0-REVIEW` / `ACC-MA-V117-S0-REVIEW` with status
  `stage_0_review_passed_pending_stage1_no_github_main_upload`.

No Stage 1 work, runtime UI implementation, screenshot, production build, local
app install, Cloudflare deploy, Access policy change, raw/private data read,
direct writeback, proposal write, agent apply or GitHub main upload was added.

Machine-readable boundary summary: No Stage 1 work; No raw/private data read;
No direct writeback; No proposal write; No GitHub main upload before whole
Stage 0-8 completion.

## Unreleased - Memory Atlas v1.1.7 Stage 0 Phase 3

- Added `docs/product/detail_visibility_contract.md` for the v1.1.7 Stage 0
  Phase 0.3 detail visibility field contract.
- Added `docs/acceptance/memory_atlas_v1_1_7_stage0_phase3_detail_visibility_acceptance.md`.
- Added `validate:v1.1.7-stage0-phase3` to verify the suggested action, tier
  asset and topic classification field contract, source/display/edit permission
  columns, proposal-only boundary, fallback policy, package script and
  governance records.
- Registered `MA-V117-S0P03` / `ACC-MA-V117-S0P03` with status
  `phase_0_3_detail_visibility_contract_completed_pending_stage0_review`.

No runtime UI, CSS, data generation, Search 2.0, Review workflow, Data Map 2.0,
Memory River, Memory Starfield, screenshot, production build, local app install,
Cloudflare deploy, Access policy change, raw/private data read, direct
writeback, proposal write, agent apply or GitHub main upload was added.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No proposal write; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.7 Stage 0 Phase 2

- Added `docs/product/memory_atlas_v1_1_7_stage0_phase2_usage_help_contract.md`.
- Added `docs/acceptance/memory_atlas_v1_1_7_stage0_phase2_usage_help_acceptance.md`.
- Added `docs/product/memory_atlas_usage_guide.md`.
- Added `apps/memory-atlas/src/components/help/MemoryAtlasHelpPanel.tsx`.
- Added `apps/memory-atlas/src/components/EmptyState.tsx` and
  `apps/memory-atlas/src/components/ErrorState.tsx`.
- Added `validate:v1.1.7-stage0-phase2` to verify the Help panel, 3-minute
  usage path, empty snapshot state, no-filtered-results state, load error
  state, WebGL fallback explanation, proposal-not-writable explanation,
  contract/acceptance/guide and governance records.
- Updated `App.tsx` to expose the Help entry, render empty/error states and
  explain unsafe proposal writeback policy.
- Updated `GalaxyScene.tsx` to use Chinese registry copy for WebGL fallback
  recovery guidance.
- Registered `MA-V117-S0P02` / `ACC-MA-V117-S0P02` with status
  `phase_0_2_usage_help_completed_pending_stage0_review`.

No Stage 0.3 detail visibility contract, Stage 1 schema, Search 2.0, Review
workflow, Data Map 2.0, Memory River replacement, Memory Starfield replacement,
browser screenshot, production build, local app install, Cloudflare deploy,
Access policy change, raw/private data read, direct writeback, proposal write,
agent apply or GitHub main upload was added.

Machine-readable boundary summary: No raw/private data read; No direct
writeback; No proposal write; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.7 Stage 0 Phase 1

- Added `docs/product/memory_atlas_v1_1_7_stage0_phase1_chinese_display_contract.md`.
- Added `docs/acceptance/memory_atlas_v1_1_7_stage0_phase1_chinese_display_acceptance.md`.
- Added `apps/memory-atlas/src/i18n/types.ts` and `apps/memory-atlas/src/i18n/zh-CN.ts`.
- Added `validate:v1.1.7-stage0-phase1` to scan selected UTF-8 text surfaces,
  verify the Chinese UI copy registry, confirm runtime registry usage and check
  Chinese font/layout tolerance.
- Updated `App.tsx` to consume the registry for navigation, filters, load
  states, overview, Inspector and proposal labels.
- Updated `styles.css` with Chinese font fallback and long-text layout
  tolerance.
- Registered `MA-V117-S0P01` / `ACC-MA-V117-S0P01` with status
  `phase_0_1_chinese_display_foundation_completed_pending_stage0_review`.

No Help panel, empty/error workflow implementation, detail visibility workbench,
browser screenshot, production build, local app install, Cloudflare deploy,
Access policy change, raw/private data read, direct writeback, proposal write,
agent apply or GitHub main upload was added.

Machine-readable boundary summary: No raw/private data read; No direct
writeback; No proposal write; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.7 Pre Stage 0

- Added `docs/product/memory_atlas_v1_1_7_gap_remediation_upgrade_contract.md`.
- Added `docs/acceptance/memory_atlas_v1_1_7_pre_stage0_acceptance.md`.
- Added `docs/reviews/memory_atlas_v1_1_7_pre_stage0_review.md`.
- Added `validate:v1.1.7-pre-stage0` to pin the v1.1.7 gap remediation
  upgrade package, Stage 0-10 stage map, acceptance matrix, baseline boundary,
  record alignment, changed-path boundary and final one-time GitHub main upload
  gate.
- Registered `MA-V117-PRESTAGE0` / `ACC-MA-V117-PRESTAGE0` with status
  `pre_stage_0_review_passed_pending_github_main_upload`.

No production runtime feature work, production React/CSS/route change, feature
flag default switch, raw/private data read, direct writeback, proposal write,
agent apply, production build, browser screenshot, local app install,
Cloudflare live deploy, Access policy change or GitHub main upload was added by
the pre-stage review artifact.

Machine-readable boundary summary: No production runtime feature work; No
raw/private data read; No direct writeback; No GitHub main upload in review
artifact.

## Unreleased - Memory Atlas v1.1.6 Stage 10 Review

- Added `docs/reviews/memory_atlas_v1_1_6_stage10_review.md`.
- Added `validate:v1.1.6-stage10` to pin Stage 10 Phase 1 readiness,
  whole-project final acceptance evidence, review artifact, records,
  changed-path boundary and final upload gate.
- Re-ran `validate:whole-project` as Stage 10 review evidence; it returned
  `PASS` with production build, 49 unittest checks, visual acceptance, release
  audit, overall acceptance and offline Cloudflare preflight.
- Marked Stage 10 as review-passed and pending GitHub main upload.
- Stage 10 review status: `stage_10_review_passed_pending_github_main_upload`.

No production runtime feature work, production React/CSS/route change, feature
flag default switch, browser screenshot run, local app install, Cloudflare live
deploy, Access policy change, raw/private data read, direct writeback, proposal
write, agent apply, GitHub main upload, or live deploy was added by the review
itself.

Machine-readable boundary summary: No production runtime feature work; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 10 Phase 1

- Added `docs/product/memory_atlas_final_acceptance_readiness_contract.md`.
- Added `docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md`.
- Added `validate:v1.1.6-stage10-phase1` to pin the Stage 10 final
  acceptance readiness contract, acceptance file, records, uploaded-baseline
  ancestry check, changed-file boundary and runtime non-goals.
- Marked Stage 10 Phase 1 as
  `phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review`.

No production UI, CSS, route, app shell, feature flag default, production build,
browser screenshot run, local app install, Cloudflare live deploy, Access policy
change, raw/private data read, direct writeback, proposal write, agent apply,
Stage 10 review, GitHub main upload, or live deploy was added.

Machine-readable boundary summary: No production UI; No production build; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 9 Review

- Added `docs/reviews/memory_atlas_v1_1_6_stage9_review.md`.
- Added `validate:v1.1.6-stage9` to pin Stage 9 Phase 1 through Phase 4
  contracts, acceptance files, validators, review artifact, production
  isolation, changed-path boundary and final upload gate.
- Marked Stage 9 as review-passed and pending GitHub main upload; Stage 10
  must start in a separate bounded run after upload verification.
- Stage 9 review status: `stage_9_review_passed_pending_github_main_upload`.

No production integration, production UI implementation, CSS change, feature
flag default switch, experiment import into the app shell, score formula
change, Universe State parameter YAML/input fixture/sample/schema mutation,
browser screenshot run, production build, local app install, Cloudflare live
deploy, Access policy change, raw/private data read, direct writeback,
proposal write, agent apply, Stage 10 work, No GitHub main upload, or live
deploy was added by the review itself.

Machine-readable boundary summary: No production integration; No production UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 9 Phase 4

- Added `docs/product/universe_state_fixture_continuity_contract.md` to define
  the Universe State fixture continuity contract for Stage 9 Phase 4.
- Added `docs/acceptance/universe_state_fixture_continuity_acceptance.md`.
- Added `validate:v1.1.6-stage9-phase4`.
- Updated `universe-state-generator-spike/README.md` with v1.1.6 Stage 9
  Phase 4 continuity, safety and no-upload boundaries.
- Reused `validate:universe-state-spike` as the required deterministic
  generator, schema, parameter drift and privacy gate.
- Stage 9 Phase 4 status:
  `phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review`.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

No score formula change, parameter YAML change, fixture/sample/schema mutation,
production integration, route, navigation, feature flag default, production
build, browser screenshot run, local app install, Cloudflare deploy, Access
policy change, raw/private data read, direct writeback, proposal write, agent
apply, Stage 9 review, Stage 10 work or No GitHub main upload was added.

## Unreleased - Memory Atlas v1.1.6 Stage 9 Phase 3

- Added isolated `data-map-spike` prototype files under
  `apps/memory-atlas/src/experiments/data-map-spike/`.
- Added `docs/product/data_map_c3_spike_contract.md` to define the Data Map C3
  isolated prototype contract for Stage 9 Phase 3.
- Added `docs/acceptance/data_map_c3_spike_acceptance.md`.
- Added `validate:v1.1.6-stage9-phase3`.
- Stage 9 Phase 3 status:
  `phase_9_3_data_map_c3_spike_ready_pending_stage_review`.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

No production Data Map replacement, route, navigation, feature flag default,
production build, browser screenshot run, local app install, Cloudflare deploy,
Access policy change, raw/private data read, direct writeback, proposal write,
agent apply, Stage 9 review, Stage 10 work or No GitHub main upload was added.

## Unreleased - Memory Atlas v1.1.6 Stage 9 Phase 2

- Added `docs/product/memory_river_c3_spike_contract.md` to define the Memory
  River C3 isolated prototype contract for Stage 9 Phase 2.
- Added `docs/acceptance/memory_river_c3_spike_acceptance.md`.
- Added `validate:v1.1.6-stage9-phase2`.
- Updated `memory-river-spike/README.md` with v1.1.6 Stage 9 Phase 2
  continuity, safety and no-upload boundaries.
- Stage 9 Phase 2 status:
  `phase_9_2_memory_river_c3_spike_ready_pending_stage_review`.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

No production Timeline replacement, route, navigation, feature flag default,
production build, browser screenshot run, local app install, Cloudflare deploy,
Access policy change, raw/private data read, direct writeback, proposal write,
agent apply, Stage 9 review, Stage 10 work or No GitHub main upload was added.

## Unreleased - Memory Atlas v1.1.6 Stage 9 Phase 1

- Added `docs/product/memory_starfield_c3_spike_contract.md` to define the
  Memory Starfield C3 isolated prototype contract for Stage 9 Phase 1.
- Added `docs/acceptance/memory_starfield_c3_spike_acceptance.md`.
- Added `validate:v1.1.6-stage9-phase1`.
- Added v1.1.6 continuity notes to
  `apps/memory-atlas/src/experiments/memory-starfield-spike/README.md`.
- Stage 9 Phase 1 status:
  `phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review`.

No production integration, runtime UI change, CSS change, browser screenshot
run, production build, local app install, installer run, Cloudflare live
deploy, Access policy change, raw/private data read, direct writeback, agent
apply, Stage 9 review, Stage 10 work or No GitHub main upload was added.

Machine-readable boundary summary: No production integration; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 8 Review

- Added `validate:v1.1.6-stage8` to pin Stage 8 Phase 1 contract,
  acceptance, records, review artifact, changed-path boundary and final upload
  gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage8_review.md`.
- Marked Stage 8 as review-passed and pending GitHub main upload; Stage 9 must
  start in a separate bounded run after upload verification.
- Stage 8 review status: `stage_8_review_passed_pending_github_main_upload`.

No runtime UI implementation, CSS change, browser screenshot run, production
build, local app install, installer run, app bundle mutation, Cloudflare live
deploy, Access policy change, external account operation, raw/private data
read, direct writeback, agent apply, Stage 9 work, No GitHub main upload, or
live deploy was added by the review itself.

Machine-readable boundary summary: No runtime UI implementation; No production build; No raw/private data read; No direct writeback; No GitHub main upload; No live deploy.

## Unreleased - Memory Atlas v1.1.6 Stage 8 Phase 1

- Added `docs/product/memory_atlas_release_rollback_contract.md` to define the
  Release Rollback Contract, including local app bundle targets, runtime
  manifest, redacted static artifact, offline Cloudflare preflight, live deploy
  authorization gate, rollback matrix, proposal-only writeback gate and cleanup
  guard.
- Added `docs/acceptance/memory_atlas_release_rollback_acceptance.md`.
- Added `validate:v1.1.6-stage8-phase1`.
- Contract title: Release Rollback Contract.
- Registered `MA-V116-S8P01` in delivery, feature, development and model
  parameter records.
- Stage 8 Phase 1 status: `phase_8_1_contract_created_pending_stage_review`.

No runtime UI implementation, CSS change, browser screenshot run, production
build, local app install, installer run, Cloudflare live deploy, Access policy
change, external account operation, raw/private data read, direct writeback,
agent apply, Stage 8 review, Stage 9/10 work, No GitHub main upload, or live
deploy was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload; No live deploy.

## Unreleased - Memory Atlas v1.1.6 Stage 7 Review

- Added `validate:v1.1.6-stage7` to pin Stage 7 Phase 1 contract,
  acceptance, records, review artifact, changed-path boundary and final upload
  gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage7_review.md`.
- Marked Stage 7 as review-passed and pending GitHub main upload; Stage 8 must
  start in a separate bounded run after upload verification.
- Stage 7 review status: `stage_7_review_passed_pending_github_main_upload`.

No runtime UI implementation, CSS change, browser screenshot run, Memory
Starfield runtime implementation, experiment directory import, feature flag
default switch, raw/private data read, direct writeback, agent apply, Stage 8
work, No GitHub main upload, Cloudflare deployment, or Access policy change was
added by the review itself.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 7 Phase 1

- Added `docs/product/memory_starfield_rebuild_contract.md` to define the
  Memory Starfield Rebuild Contract, including `memory_starfield`,
  `nebula_field`, `flow_field`, `trajectory_trails`, `gravity_sources`,
  `black_hole_core`, `proto_star_cloud`, `memory_terrain_layer`,
  `cluster_constellations`, search/river jumps, Inspector handoff and
  reduced-motion requirements.
- Added `docs/acceptance/memory_starfield_rebuild_acceptance.md`.
- Added `validate:v1.1.6-stage7-phase1`.
- Contract title: Memory Starfield Rebuild Contract.
- Registered `MA-V116-S7P01` in delivery, feature, development and model
  parameter records.
- Stage 7 Phase 1 status: `phase_7_1_contract_created_pending_stage_review`.

No runtime UI implementation, CSS change, browser screenshot run, Memory
Starfield runtime implementation, experiment directory import, feature flag
default switch, raw/private data read, direct writeback, agent apply, Stage 7
review, Stage 8/9/10 work, No GitHub main upload, Cloudflare deployment, or
Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 6 Review

- Added `validate:v1.1.6-stage6` to pin Stage 6 Phase 1 contract,
  acceptance, records, review artifact, changed-path boundary and final upload
  gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage6_review.md`.
- Marked Stage 6 as review-passed and pending GitHub main upload; Stage 7 must
  start in a separate bounded run after upload verification.
- Stage 6 review status: `stage_6_review_passed_pending_github_main_upload`.

No runtime UI implementation, CSS change, browser screenshot run, Memory River
runtime implementation, raw/private data read, direct writeback, agent apply,
Stage 7 work, No GitHub main upload, Cloudflare deployment, or Access policy
change was added by the review itself.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 6 Phase 1

- Added `docs/product/memory_river_rebuild_contract.md` to define the Memory
  River Rebuild Contract, including `time_river`, `theme_bands`,
  `event_pulses`, `decision_nodes`, `black_hole_band`, `proto_star_marker`,
  `evidence_density_lane`, zoom, brush, hover card, Inspector handoff and
  reduced-motion requirements.
- Added `docs/acceptance/memory_river_rebuild_acceptance.md`.
- Added `validate:v1.1.6-stage6-phase1`.
- Contract title: Memory River Rebuild Contract.
- Registered `MA-V116-S6P01` in delivery, feature, development and model
  parameter records.
- Stage 6 Phase 1 status: `phase_6_1_contract_created_pending_stage_review`.

No runtime UI implementation, CSS change, browser screenshot run, Memory River
runtime implementation, raw/private data read, direct writeback, agent apply,
Stage 6 review, Stage 7/8/9/10 work, No GitHub main upload, Cloudflare
deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 5 Review

- Added `validate:v1.1.6-stage5` to pin Stage 5 Phase 1 contract,
  acceptance, records, review artifact, changed-path boundary and final upload
  gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage5_review.md`.
- Marked Stage 5 as review-passed and pending Stage 1-5 final upload; GitHub
  main upload remains deferred until final upload gates are run.
- Stage 5 review status: `stage_5_review_passed_pending_stage1_5_final_upload`.

No runtime UI implementation, CSS change, browser screenshot run, Data Map
runtime implementation, raw/private data read, direct writeback, agent apply,
Stage 6 work, No GitHub main upload, Cloudflare deployment, or Access policy
change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 5 Phase 1

- Added `docs/product/data_map_2_0_workflow_contract.md` to define the
  Data Map 2.0 Workflow Contract, including the source, topic, asset and action
  layers, data-to-action flow, map card anatomy, cross-workflow handoffs and
  proposal-only boundary.
- Added `docs/acceptance/data_map_2_0_workflow_acceptance.md`.
- Added `validate:v1.1.6-stage5-phase1`.
- Registered `MA-V116-S5P01` in delivery, feature, development and model
  parameter records.
- Stage 5 Phase 1 status: `phase_5_1_contract_created_pending_stage_review`.

No runtime UI implementation, CSS change, browser screenshot run, Data Map
runtime implementation, raw/private data read, direct writeback, agent apply,
Stage 5 review, No GitHub main upload, Cloudflare deployment, or Access policy
change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 4 Review

- Added `validate:v1.1.6-stage4` to pin Stage 4 Phase 1 / 2 contracts,
  acceptance files, records, review artifact, changed-path boundary and upload
  gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage4_review.md`.
- Marked Stage 4 as review-passed and still pending Stage 5; GitHub main
  upload remains deferred until Stage 1-5 are complete and final upload gates
  are run.
- Stage 4 review status: `stage_4_review_passed_pending_stage5`.

No runtime UI implementation, CSS change, browser screenshot run, search index
implementation, Review / Summary / Iteration runtime implementation,
raw/private data read, direct writeback, Data Map runtime work, Stage 5 work,
No GitHub main upload, Cloudflare deployment, or Access policy change was
added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 4 Phase 2

- Added `docs/product/review_summary_iteration_workflow_contract.md` to define
  the Review / Summary / Iteration Workflow Contract, including the eight
  required review questions, theme change panels, opportunity and low-value
  loop panels, decision changes, next actions, proposal decision and iteration
  backlog boundary.
- Added `docs/acceptance/review_summary_iteration_workflow_acceptance.md`.
- Added `validate:v1.1.6-stage4-phase2`.
- Registered `MA-V116-S4P02` in delivery, feature, development and model
  parameter records.
- Stage 4 Phase 2 status: `phase_4_2_contract_created_pending_stage_review`.

No runtime UI implementation, CSS change, browser screenshot run, Review /
Summary / Iteration runtime implementation, raw/private data read, direct
writeback, Data Map runtime work, Stage 5 work, No GitHub main upload,
Cloudflare deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 4 Phase 1

- Added `docs/product/search_2_0_workflow_contract.md` to define the
  Search 2.0 Workflow Contract query regions, result list anatomy, `matched_reason`,
  Starfield/River/Inspector jump actions, session summary, zero-result
  recovery and proposal-only handoff boundary.
- Added `docs/acceptance/search_2_0_workflow_acceptance.md`.
- Added `validate:v1.1.6-stage4-phase1`.
- Registered `MA-V116-S4P01` in delivery, feature, development and model
  parameter records.
- Stage 4 Phase 1 status: `phase_4_1_contract_created_pending_stage_review`.

No runtime UI implementation, CSS change, browser screenshot run, search index
implementation, raw/private data read, direct writeback, Review / Summary /
Iteration runtime work, Data Map runtime work, Stage 5 work, No GitHub main
upload, Cloudflare deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 3 Review

- Added `validate:v1.1.6-stage3` to pin Stage 3 Phase 1 / 2 contracts,
  acceptance files, records, review artifact, changed-path boundary and upload
  gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage3_review.md`.
- Marked Stage 3 as review-passed and still pending Stage 4; GitHub main
  upload remains deferred until Stage 1-5 are complete and final upload gates
  are run.
- Stage 3 review status: `stage_3_review_passed_pending_stage4`.

No runtime UI implementation, CSS change, browser screenshot run, localStorage
write, raw/private data read, direct writeback, complete agent apply work,
Search 2.0 runtime work, Review / Summary / Iteration runtime work, Data Map
runtime work, Stage 4 work, Stage 5 work, No GitHub main upload, Cloudflare
deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 3 Phase 2

- Added `docs/product/proposal_queue_persistence_contract.md` to define the
  proposal queue persistence storage key, browser-local scope, append-only
  mutation policy, proposal record schema, revision chain, proposal history,
  rollback proposal and forbidden-payload boundary.
- Added `docs/acceptance/proposal_queue_persistence_acceptance.md`.
- Added `validate:v1.1.6-stage3-phase2`.
- Registered `MA-V116-S3P02` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, localStorage
write, raw/private data read, direct writeback, complete agent apply work,
Search 2.0 runtime work, Review / Summary / Iteration runtime work, Data Map
runtime work, Stage 4 work, Stage 5 work, No GitHub main upload, Cloudflare
deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 3 Phase 1

- Added `docs/product/proposal_only_adjustment_workspace_contract.md` to
  define the proposal-only adjustment workspace regions, allowed targets,
  allowed fields, draft schema, proposal states, diff preview, safety review,
  Inspector handoff, rollback panel and future agent-apply boundary.
- Added `docs/acceptance/proposal_only_adjustment_workspace_acceptance.md`.
- Added `validate:v1.1.6-stage3-phase1`.
- Registered `MA-V116-S3P01` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, complete agent apply work, Search 2.0 runtime
work, Review / Summary / Iteration runtime work, Data Map runtime work,
Stage 4 work, Stage 5 work, No GitHub main upload, Cloudflare deployment, or
Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 2 Review

- Added `validate:v1.1.6-stage2` to pin Stage 2 Phase 1 / 2 / 3 / 4
  contracts, acceptance files, records, review artifact, changed-path boundary,
  and upload gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage2_review.md`.
- Marked Stage 2 as review-passed and still pending Stage 3; GitHub main
  upload remains deferred until Stage 1-5 are complete and final upload gates
  are run.
- Stage 2 review status: `stage_2_review_passed_pending_stage3`.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, complete proposal editor work, agent apply work,
Search 2.0 runtime work, Review / Summary / Iteration runtime work, Data Map
runtime work, Stage 3 work, No GitHub main upload, Cloudflare deployment, or
Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 2 Phase 4

- Added `docs/product/topic_classification_lane_visibility_contract.md` to
  define the concrete `topic_classification_lane` visibility hierarchy,
  required fields, topic-state grouping, sorting, badges,
  expand/compare/pin/review interactions, linked asset/action/starfield/river
  jumps, Inspector handoff, proposal-only adjustment boundary and
  empty/error/conflict/black-hole/stale states.
- Added `docs/acceptance/topic_classification_lane_visibility_acceptance.md`.
- Added `validate:v1.1.6-stage2-phase4`.
- Registered `MA-V116-S2P04` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, complete proposal editor work, agent apply work,
Search 2.0 runtime work, Review / Summary / Iteration runtime work, Data Map
runtime work, No GitHub main upload, Cloudflare deployment, or Access policy
change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 2 Phase 3

- Added `docs/product/tier_asset_lane_visibility_contract.md` to define the
  concrete `tier_asset_lane` visibility hierarchy, required fields, asset
  tier grouping, sorting, badges, expand/compare/pin/review interactions,
  linked-action jump, Inspector handoff, proposal-only adjustment boundary and
  empty/error/stale states.
- Added `docs/acceptance/tier_asset_lane_visibility_acceptance.md`.
- Added `validate:v1.1.6-stage2-phase3`.
- Registered `MA-V116-S2P03` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, complete proposal editor work, agent apply work,
Search 2.0 runtime work, Review / Summary / Iteration runtime work, Data Map
runtime work, No GitHub main upload, Cloudflare deployment, or Access policy
change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 2 Phase 2

- Added `docs/product/suggested_action_lane_visibility_contract.md` to define
  the concrete `suggested_action_lane` visibility hierarchy, required fields,
  grouping, sorting, badges, expand/compare/pin/review interactions,
  Inspector handoff, proposal-only adjustment boundary and empty/error states.
- Added `docs/acceptance/suggested_action_lane_visibility_acceptance.md`.
- Added `validate:v1.1.6-stage2-phase2`.
- Registered `MA-V116-S2P02` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, complete proposal editor work, agent apply work,
Search 2.0 runtime work, Review / Summary / Iteration runtime work, Data Map
runtime work, No GitHub main upload, Cloudflare deployment, or Access policy
change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 2 Phase 1

- Added `docs/product/detail_visibility_workbench_contract.md` to define the
  detail visibility workbench IA, three detail lanes, expand/collapse
  behavior, workbench filters, default sorting, Inspector handoff,
  proposal-only hints, empty/error states and future screenshot gates.
- Added `docs/acceptance/detail_visibility_workbench_acceptance.md`.
- Added `validate:v1.1.6-stage2-phase1`.
- Registered `MA-V116-S2P01` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, complete proposal editor work, agent apply work,
Search 2.0 runtime work, Review / Summary / Iteration runtime work, Data Map
runtime work, No GitHub main upload, Cloudflare deployment, or Access policy
change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 1 Review

- Added `validate:v1.1.6-stage1` to pin Stage 1 Phase 1 / 2 / 3 / 4 / 5
  contracts, acceptance files, records, review artifact, changed-path boundary,
  and upload gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage1_review.md`.
- Marked Stage 1 as review-passed and still pending Stage 2; GitHub main
  upload remains deferred until Stage 1-5 are complete and final upload gates
  are run.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, complete proposal editor work, agent apply work,
Search 2.0 runtime work, Review / Summary / Iteration runtime work, Data Map
runtime work, No GitHub main upload, Cloudflare deployment, or Access policy
change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 1 Phase 5

- Added `docs/product/proposal_only_adjustment_entry_contract.md` to define
  proposal-only adjustment entry surfaces, target types, allowed fields, draft
  schema, user-readable safety copy, Inspector handoff, no-direct-writeback
  boundaries and future-phase exclusions.
- Added `docs/acceptance/proposal_only_adjustment_entry_acceptance.md`.
- Added `validate:v1.1.6-stage1-phase5`.
- Registered `MA-V116-S1P05` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, full proposal editor work, agent apply work,
Search 2.0 work, review / summary / iteration work, Data Map work, No GitHub
main upload, Cloudflare deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 1 Phase 4

- Added `docs/product/topic_classification_detail_contract.md` to define topic
  classification detail fields, seven topic states, strength / trend /
  confidence / record-count / evidence requirements, cross-board links,
  Inspector handoff, proposal-only boundaries and future-phase exclusions.
- Added `docs/acceptance/topic_classification_detail_acceptance.md`.
- Added `validate:v1.1.6-stage1-phase4`.
- Registered `MA-V116-S1P04` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, proposal editor work, Search 2.0 work, review /
summary / iteration work, Data Map work, No GitHub main upload, Cloudflare
deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 1 Phase 3

- Added `docs/product/tier_asset_detail_contract.md` to define tier asset
  detail fields, seven asset tiers, importance / priority / confidence /
  staleness requirements, Inspector handoff, proposal-only boundaries and
  future-phase exclusions.
- Added `docs/acceptance/tier_asset_detail_acceptance.md`.
- Added `validate:v1.1.6-stage1-phase3`.
- Registered `MA-V116-S1P03` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, topic model work, proposal editor work, Search
2.0 work, Data Map work, No GitHub main upload, Cloudflare deployment, or
Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 1 Phase 2

- Added `docs/product/suggested_action_detail_contract.md` to define suggested
  action detail fields, action types, ROI / effort / urgency / evidence /
  next-step requirements, Inspector handoff, proposal-only boundaries and
  future-phase exclusions.
- Added `docs/acceptance/suggested_action_detail_acceptance.md`.
- Added `validate:v1.1.6-stage1-phase2`.
- Registered `MA-V116-S1P02` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, layer-asset model work, topic model work, Search
2.0 work, Data Map work, No GitHub main upload, Cloudflare deployment, or
Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 1 Phase 1

- Added `docs/product/memory_overview_usage_contract.md` to define `记忆总览`
  as the system entry point with 今日状态, Memory Weather, suggested actions,
  low-value loops, proto-star opportunities, tier asset summary, topic summary,
  Mini 记忆星系, 记忆时间河脉冲, system usage instructions, Presentation /
  Analysis mode, Inspector and proposal-only boundaries.
- Added `docs/acceptance/memory_overview_usage_acceptance.md`.
- Added `validate:v1.1.6-stage1-phase1`.
- Registered `MA-V116-S1P01` in delivery, feature, development and model
  parameter records.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, Stage 2-5 work, No GitHub main upload, Cloudflare
deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 0 Review

- Added `validate:v1.1.6-stage0` to pin the Stage 0 Phase 0.1 / 0.2
  contracts, records, review artifact, changed-path boundary, and upload gate.
- Added `docs/reviews/memory_atlas_v1_1_6_stage0_review.md`.
- Marked Stage 0 as review-passed and still pending final remote checks and
  GitHub main upload.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, Stage 1 work, No GitHub main upload, Cloudflare
deployment, or Access policy change was added.

Machine-readable boundary summary: No runtime UI implementation; No raw/private data read; No direct writeback; No GitHub main upload.

## Unreleased - Memory Atlas v1.1.6 Stage 0 Phase 0.2

- Added the visual density baseline for Memory Overview, Memory Starfield,
  Memory River, and Data Map.
- Defined minimum visualization thresholds, required primary visual regions,
  failure conditions, screenshot matrix, and anti-regression rules.
- Registered Stage 0 as locally phase-complete and pending whole-stage review.

No runtime UI implementation, CSS change, browser screenshot run, raw/private
data read, direct writeback, Stage 1 work, No GitHub main upload, Cloudflare
deployment, or Access policy change was added.

## Unreleased - Memory Atlas v1.1.6 Stage 0 Phase 0.1

- Added the Chinese UI quality contract for UTF-8, mojibake blocking,
  Chinese-first labels, text length rules, table content boundaries,
  Inspector readability, proposal-only wording, and low-width viewport
  expectations.
- Added the Chinese text audit acceptance document with static text checks and
  future browser screenshot gates.
- Registered the v1.1.6 Stage 0 Phase 0.1 record in Memory Atlas delivery and
  model-parameter documentation.

No runtime UI implementation, CSS change, raw/private data read, direct
writeback, Stage 0 Phase 0.2 work, No GitHub main upload, Cloudflare
deployment, or Access policy change was added.

## Unreleased - Memory Atlas v1.1.5 Whole-Project Review

- Completed the whole-project review after Part 1 through Part 10 review gates
  (Part 1-10).
- Added `validate:whole-project` to rerun Part 1-10 validators, production
  build, OpenAIDatabase unittest discovery, visual acceptance, release audit,
  overall acceptance, offline Cloudflare Pages + Access preflight,
  diff-driven governance sync, Roadmap v2 final acceptance coverage, upload
  boundary checks, and 4177 cleanup.
- Identified the installed local app runtime as a post-commit verification
  requirement: the runtime manifest must be refreshed after this review commit
  and re-audited with `--require-local-apps` before final upload.

No GitHub main upload, Cloudflare live deploy, Access policy change,
raw/private data access, direct writeback, production runtime feature work, or
external account operation was added.

Machine-readable boundary summary: whole-project review passed; final remote
ancestry and local runtime refresh remain required before GitHub main upload.

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
