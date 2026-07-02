# Memory Atlas v1.1.7 Gap Remediation Upgrade Contract

Contract ID: `memory_atlas_v1_1_7_gap_remediation_upgrade_contract`

Stage: `v1.1.7 Pre Stage 0`

Task ID: `MA-V117-PRESTAGE0`

Acceptance ID: `ACC-MA-V117-PRESTAGE0`

Status: `pre_stage_0_review_passed_pending_github_main_upload`

## Purpose

This pre-stage turns the Roadmap v2 gap remediation input into a controlled
v1.1.7 upgrade package. It is a planning and governance gate before Stage 0.
It does not replace UI, route users to a new page, change CSS, read
raw/private data, write proposals, write long-term memory or deploy.

The v1.1.6 baseline already created many C2 and C3 contracts. v1.1.7 therefore
does not repeat those files as new implementation. It records the remaining
product gap, stage map, acceptance matrix and final one-time GitHub main upload
gate for the next Stage 0-10 execution series.

## Source Inputs

| Input | Use in this pre-stage |
|---|---|
| `memory_atlas_visual_roadmap_v2_gap_remediation.md` | Roadmap v2 remediation source, acceptance matrix and first C2 prompt. |
| v1.1.6 Stage 10 review | Baseline proof that prior contracts and whole-project acceptance were locally review-passed. |
| Current canonical worktree | `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/memory-atlas`. |
| Canonical remote | `git@github.com:LinzeColin/CodexProject.git`. |

## Entry Conditions

- Work starts from the canonical `memory-atlas` worktree.
- Sparse checkout remains project-bound to `OpenAIDatabase`.
- `origin/main` is included before any v1.1.7 file is written.
- Tracked worktree state is clean except for this pre-stage change set.
- Local `.DS_Store` remains untracked and must not be staged.

## v1.1.7 Stage Map

The user-facing request is Stage 0-10. Roadmap v2 Stage 11 release/rollback is
therefore merged into the v1.1.7 Stage 10 final hardening and upload gate unless
a later owner decision splits it back out.

| v1.1.7 stage | Scope | Must not claim early |
|---|---|---|
| Pre Stage 0 | This upgrade package, gap map, acceptance and upload boundary. | Runtime remediation or visual acceptance. |
| Stage 0 | Baseline usability evidence refresh: mojibake, Chinese readability, UI help, screenshots and current gap inventory. | Code-level fix unless evidence proves a narrow bug. |
| Stage 1 | Detail visibility runtime plan and first implementation slice for suggested actions, tier assets and topic categories. | Full proposal editor or Search 2.0. |
| Stage 2 | Proposal-only adjustment runtime path with diff, rollback and no-direct-writeback gates. | Long-term memory mutation or agent apply. |
| Stage 3 | Memory overview as default operating surface with usage path and Inspector handoff. | Production replacement of starfield or river. |
| Stage 4 | Memory Starfield production integration from the isolated spike, with Flow Field nebula anti-regression gates. | Obsidian-like graph or dots-only view. |
| Stage 5 | Memory River production integration from the isolated spike, replacing the old date-list timeline. | Static timeline list. |
| Stage 6 | Data Map 2.0 runtime integration: source, topic, asset and action layers with evidence. | Static diagram with no evidence or handoff. |
| Stage 7 | Search 2.0 and Review / Summary / Iteration workflow integration. | Search results without matched reasons or review queues without actions. |
| Stage 8 | Summary and iteration closure: change comparison, stale/conflict signals and proposal candidates. | Direct database writeback. |
| Stage 9 | Cross-board shared state, synchronized filters and Inspector explanation layer. | Divergent per-page state. |
| Stage 10 | Performance, safety, accessibility, release/rollback, final validation, review and one-time GitHub main upload. | Live deploy without owner authorization. |

## Required Acceptance Matrix

Every later stage must preserve these Roadmap v2 acceptance surfaces:

| Surface | v1.1.7 requirement |
|---|---|
| Chinese readability | No mojibake, replacement glyphs, broken fallback font or text overflow in core flows. |
| Usage path | A user can follow state -> suggestion -> evidence -> proposal -> review/export. |
| Suggested actions | Actions are visible, ranked, explainable and connected to evidence. |
| Tier assets | Core profile, project, decision, workflow, knowledge, opportunity and stale assets have details. |
| Topic categories | Topics show strength, trend, confidence, evidence count and related actions. |
| Proposal-only editing | Frontend changes create proposals only; no direct long-term memory write. |
| Search 2.0 | Results show matched reason, filters, evidence and jumps to Starfield/River/Inspector. |
| Review workflow | Review answers the eight roadmap questions and can produce proposal candidates. |
| Summary iteration | Changes, stale loops, conflicts, opportunities and next actions are visible. |
| Data Map 2.0 | Source -> topic -> asset -> action flow is explainable with evidence. |
| Memory River | Not a date list; must contain time river, theme bands, pulses, decision nodes and lifecycle markers. |
| Memory Starfield | Must contain nebula, flow field, trails, gravity sources, black hole, proto-star and terrain layer. |
| Safety | No raw/private/cookie/session/secret data read; redacted derived evidence only. |
| Performance | Desktop target 45-60 FPS, reduced-motion fallback and cleanup proof. |
| Rollback | Feature flags, fallback paths and rollback notes are explicit before final upload. |

## Pre Stage 0 Outputs

- Product contract:
  `docs/product/memory_atlas_v1_1_7_gap_remediation_upgrade_contract.md`
- Acceptance checklist:
  `docs/acceptance/memory_atlas_v1_1_7_pre_stage0_acceptance.md`
- Review artifact:
  `docs/reviews/memory_atlas_v1_1_7_pre_stage0_review.md`
- Validator:
  `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_pre_stage0.cjs`
- Package script:
  `validate:v1.1.7-pre-stage0`
- Records:
  `CHANGELOG.md`, `功能清单.md`, `开发记录.md`, `模型参数文件.md`,
  `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`,
  `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`

## Non-Goals

- No production UI, route, CSS, app shell or feature flag default change.
- No new external data source, raw export, cookie, session, secret, private
  transcript or local runtime cache read.
- No direct active-memory writeback, proposal write or agent apply.
- No production build, browser screenshot, local app install, Cloudflare live
  deploy or Access policy change in pre-stage.
- No Stage 0 implementation in this run.

## One-Time Upload Gate

The final upload for this pre-stage is allowed only after:

1. `validate:v1.1.7-pre-stage0` passes.
2. `git diff --check -- OpenAIDatabase` passes.
3. The tracked tree is clean after commit.
4. `origin/main` is fetched and either already included or integrated.
5. The push target is the canonical `LinzeColin/CodexProject` main tree.

## Rollback

Revert the v1.1.7 pre-stage commit. This removes the contract, acceptance,
review artifact, validator, package script and record entries without changing
production runtime behavior or the v1.1.6 baseline.
