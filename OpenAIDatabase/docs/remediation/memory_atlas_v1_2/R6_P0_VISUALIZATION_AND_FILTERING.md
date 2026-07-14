# Memory Atlas v1.2 Remediation R6: P0 Visualization And Filtering

## Status

- Phase: `R6_P0_VISUALIZATION_AND_FILTERING`
- Phase result: `R6_COMPLETE_LOCAL_ONLY`
- Release result: `FAIL_REMEDIATION_REQUIRED`
- R5 closeout base: `2295074a200f7b4ccd10b1eff8222746a51cd60e`
- R6 design: `78e67369a`
- R6 implementation/review head: `cf47e65f9`
- `origin/main`: `07a6e50d593c7b9c74b8f3870b614be86a87160d`
- Pre-record divergence: local `main` is ahead 33 and behind 12.
- Push, app reinstall and Cloudflare deployment: `false`.
- Next phase: `R7_DATA_PARITY_RAW_EVIDENCE_AND_RECOVERY`.

R6 replaces the historical source-marker-only visual claim with one rendered decision
workbench backed by a bounded public snapshot. It keeps the R2 ten-route information
architecture and the R3 six-command registry unchanged. All twelve approved P0 visuals
now share literal source/time/project/task filters, keyboard-operable data, an inline
evidence workspace and visible decision copy. This phase does not claim online, installed
app, snapshot parity, clean recovery or final release completion.

## Safe Snapshot Contract

- `visual_workflows` contains exactly 12 approved visual IDs and excludes decorative
  density candidates that do not pass the Visual ROI gate.
- `behavior_intelligence.facet_events` exports 217 deterministic derived events, capped
  at 1,000, with source/project/task/time metadata and bounded evidence references.
- Transcript text, messages, credentials, tokens, cookies, absolute paths and raw
  payloads are excluded from the public facet contract.
- Unknown project/task values normalize to `未标注`; bounded time windows anchor to the
  latest valid event rather than wall-clock time.
- `formula_what_if` preserves the tracked formula, defaults and bounds. It is a local
  no-write preview with `active_config_write=false`, proposal-before-apply, no raw
  mutation, no precise income prediction and no financial-advice claim.

The current tracked web snapshot remains 278 memories / 340 nodes / 1,771 edges and
contains 217 facet events. R6 does not resolve the separate installed-runtime/parity gap;
that is an explicit R7 requirement.

## Rendered Workbench

The exact retained visual IDs are:

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

Each card renders a Chinese question, action value, filtered event count and at least one
keyboard-operable datum/control. Selecting a datum updates the shared inline evidence
workspace before any route navigation. Opportunity Radar joins opportunity evidence
references to the currently filtered facet events by exact `ref_id`; its detail includes
evidence, next step, half-life, Why Not Now/defer reason and the no-pressure-list boundary.

Formula Explorer exposes bounded time-saved, reuse-value and skill-compounding sliders.
The browser gate changed the proxy score from 80 to 84 and Reset restored 80 on every
target viewport. No non-GET request or file/config write is part of this interaction.

## Browser Acceptance

`validate:v1.2-visual-workflows` builds the current frontend and repeats the complete
interaction suite at `1470x661`, `1440x900` and `390x844`. Final tracked evidence proves:

- exact 12/12 visual inventory and 12/12 evidence interactions on every viewport;
- source/time/project/task selections change 11/10/11/11 event-backed card contents,
  respectively, on every viewport;
- every one of the 11 event-backed cards changes content/count/datum IDs or reaches zero
  on at least one axis; Formula is tested separately as a bounded control;
- Opportunity Radar rendered event IDs exactly match its filtered evidence join;
- Formula changes and resets with zero write requests;
- overlap count, clipped-card count and horizontal overflow are all zero;
- all three screenshots are nonblank and were visually inspected.

## Verification And Review

- Focused Python snapshot/data tests: `4 tests`, PASS.
- Pure TypeScript model validator: PASS; synthetic event count 4, score `71 -> 75`.
- TypeScript lint: PASS.
- Production build: PASS with the existing non-blocking chunk-size warning.
- R6 three-viewport browser gate: PASS.
- R1 Home, R3 command, R4 proposal, R5 Owner Daily and Stage 7 browser regressions: PASS.
- Historical S06/S07/S08/S09/S11 validators: PASS as regressions only; they are not R6
  product acceptance.
- Visual source audit: PASS, 39 checks.
- Privacy guard: PASS, zero high-risk secret hits and zero tracked raw/private files.
- Independent review initially found 1 High, 3 Medium and 2 Low issues. Opportunity
  filtering/evidence joining, all-viewport interactions, per-card content-matrix rigor,
  selector compatibility and Formula wording were corrected. Final result:
  `0 High / 0 Medium`.

## Requirement Delta

- `S06-AC03`: `PARTIAL -> VERIFIED`.
- `S07-AC02`: `PARTIAL -> VERIFIED`.
- `S07-AC04`: `PARTIAL -> VERIFIED`.
- `S11-AC01`: `PARTIAL -> VERIFIED`.
- `S11-AC02`: `PARTIAL -> VERIFIED`.
- `S11-AC03`: `FAILED -> VERIFIED`.
- `S11-AC04`: `NOT_VERIFIED -> VERIFIED`.

Aggregate after R6: `VERIFIED 48 / PARTIAL 5 / FAILED 4 / NOT_VERIFIED 1` across 58
requirements. R7 and R8 gaps remain, so the release stays FAIL.

## Evidence

- `机器治理/证据与日志/remediation/v1_2_r6/status.json`
- `机器治理/证据与日志/remediation/v1_2_r6/requirements_gap_delta.csv`
- `机器治理/证据与日志/remediation/v1_2_r6/browser/final/status.json`
- `机器治理/证据与日志/remediation/v1_2_r6/browser/final/visual-workflows-desktop-low-height-1470x661.png`
- `机器治理/证据与日志/remediation/v1_2_r6/browser/final/visual-workflows-desktop-standard-1440x900.png`
- `机器治理/证据与日志/remediation/v1_2_r6/browser/final/visual-workflows-mobile-390x844.png`

## Rollback And Stop

Revert all R6 commits after R5 closeout `2295074a2` while retaining R0-R5. Rebuild the
prior derived snapshot from the prior builder if the tracked snapshot is reverted. This
removes only the R6 derived contract, pure model, workbench, browser gate and records;
raw data, credentials, installed apps, Cloudflare and GitHub main remain untouched.

Stop after the R6 closeout commit. Do not start R7, reconcile remote history, push,
reinstall or deploy in this run. R8 remains the only phase permitted to perform the
single final GitHub upload and release delivery after R7 and overall acceptance pass.
