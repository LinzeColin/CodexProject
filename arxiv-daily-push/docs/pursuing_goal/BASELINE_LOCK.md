# arXiv Daily Push V5 Baseline + V6 Roadmap Lock

Status: `LOCKED_FOR_STAGE1_TEXT_DELIVERY_EXECUTION_WITH_V6_TASK_ROADMAP`
Task ID: `S1P5T04`
Evidence level: `EXTRACTED`

This file locks the two-stage text-delivery V5 package and V6 task roadmap into
the project tree as the current long-running goal baseline. It is an index and
integrity record, not a second editable fact source. Governance facts remain in
`docs/governance/`.

## Source Package

- Source ZIP: `/Users/linzezhang/Downloads/arxiv_daily_push_two_stage_text_delivery_codex_pack_v5_2026-06-22.zip`
- Source ZIP SHA-256: `b2b2a7ce490e7c89b1fc29adcf40d51bcc478dbfc8fa33d46c16b56fa74e3106`
- Source prompt: `/Users/linzezhang/Downloads/FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt`
- Source prompt SHA-256: `a79af57bce62caa8176773f76f10e058ee8f7bed96e7140592137674877b812a`
- Source roadmap: `/Users/linzezhang/Downloads/ARXIV_DAILY_PUSH_TWO_STAGE_ROADMAP_V6.md`
- Source roadmap SHA-256: `76b2d29a6d5cd62de472f1a8c265a89fcf03dc7031f7d4e209f85c650b498f10`
- Import date: `2026-06-22`
- V6 roadmap import date: `2026-06-23`
- Imported by: `S1-02-V5-BASELINE-GOVERNANCE-CALIBRATION-001`; `S1P5T04`

## Locked Files

| File | SHA-256 | Role |
|---|---:|---|
| `START_HERE_MASTER_TASK_PACK_TWO_STAGE_TEXT_DELIVERY_V5.md` | `2ce872967c063c6a1da51133e2422159dd181607bea8c17f1ef1608db93b6f74` | Human-readable task pack entry point |
| `FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt` | `a79af57bce62caa8176773f76f10e058ee8f7bed96e7140592137674877b812a` | Authoritative two-stage execution prompt |
| `ARXIV_DAILY_PUSH_TWO_STAGE_ROADMAP_V6.md` | `76b2d29a6d5cd62de472f1a8c265a89fcf03dc7031f7d4e209f85c650b498f10` | Authoritative task-numbering roadmap: 2 stages, 12 phases, 49 tasks |

The hashes above must be treated as immutable for this baseline. Any content
change must be intentional, task-bound, and recorded in
`development_events.jsonl`.

## Superseded Baseline

The Review8 V4 files remain in `docs/pursuing_goal/` for history only:

- `START_HERE_MASTER_TASK_PACK_TWO_STAGE_V4.md`
- `FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_V4.txt`

V4 is no longer the active execution contract. Any V4 or Phase 12 video/Release
requirement that conflicts with V5 text delivery is inactive for the current
goal unless a later owner decision explicitly restores it.

## Stage Contract

- Stage 1: B1/arXiv single-source vertical slice and production acceptance.
- Stage 2: source/board promotion and final full-system acceptance.
- Stage 1 target state: `ARXIV_PRODUCTION_ACCEPTED`.
- Final target state after Stage 2: `PRODUCTION_ACCEPTED -> DAILY_OPERATION`.
- Current V6 task: `S1P5T04` - controlled live B1 email evidence and Stage 1 acceptance.
- Current state: `ARXIV_PRODUCTION_ACCEPTED` from PR #82 cloud artifact
  `7818287996`; scheduled production send remains fail-closed until GitHub
  repository variables/secrets are explicitly verified or enabled.

## V6 Roadmap Rule

The V6 roadmap controls task numbering and progress reporting from this point
forward. Every implementation closeout must state the current V6 Task ID.

The V5 text-delivery baseline remains the product boundary: high-density text
reports, independent emails, Markdown/HTML/JSON audit artifacts, and zero
required video/TTS/media work.

Where the V6 calendar/new-machine wording conflicts with later owner-approved
GitHub/cloud-runner execution, the later owner instruction controls the runner
choice for Stage 1 evidence collection. Production scheduling remains a
separate fail-closed enablement step after Stage 1 acceptance.

## V5 Delivery Boundary

Current external delivery for this goal is text-first:

- high-density Chinese explanation reports;
- independent emails;
- Markdown, HTML, and JSON audit artifacts.

Video, MP4 generation, GitHub Release video links, TTS, voice samples, and media
rendering are legacy evidence paths only. They are not Stage 1 acceptance
requirements under V5.

## Current Evidence Boundary

S1-03, S1-04, and S1-05 provide reusable foundations for owner controls,
SQLite/WAL/FTS5 storage, and the arXiv connector contract.

Stage 1 acceptance is evidenced by `governance/run_manifests/ADP-S1P5T04-ARXIV-PRODUCTION-ACCEPTED-20260623.json`,
PR #82, and GitHub Actions run `28019921500`. The acceptance artifact reports
49 real arXiv candidates, 30 selected samples, 20/20 primary archive buckets,
two controlled SMTP refs, no blockers, no Release/video requirement, and
`production_schedule_enabled=false`.
