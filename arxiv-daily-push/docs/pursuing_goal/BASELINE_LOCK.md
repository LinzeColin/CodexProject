# arXiv Daily Push V5 Baseline Lock

Status: `LOCKED_FOR_STAGE1_TEXT_DELIVERY_EXECUTION`
Task ID: `S1-02-V5-BASELINE-GOVERNANCE-CALIBRATION-001`
Evidence level: `EXTRACTED`

This file locks the two-stage text-delivery V5 package into the project tree as
the current long-running goal baseline. It is an index and integrity record,
not a second editable fact source. Governance facts remain in `docs/governance/`.

## Source Package

- Source ZIP: `/Users/linzezhang/Downloads/arxiv_daily_push_two_stage_text_delivery_codex_pack_v5_2026-06-22.zip`
- Source ZIP SHA-256: `b2b2a7ce490e7c89b1fc29adcf40d51bcc478dbfc8fa33d46c16b56fa74e3106`
- Source prompt: `/Users/linzezhang/Downloads/FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt`
- Source prompt SHA-256: `a79af57bce62caa8176773f76f10e058ee8f7bed96e7140592137674877b812a`
- Import date: `2026-06-22`
- Imported by: `S1-02-V5-BASELINE-GOVERNANCE-CALIBRATION-001`

## Locked Files

| File | SHA-256 | Role |
|---|---:|---|
| `START_HERE_MASTER_TASK_PACK_TWO_STAGE_TEXT_DELIVERY_V5.md` | `2ce872967c063c6a1da51133e2422159dd181607bea8c17f1ef1608db93b6f74` | Human-readable task pack entry point |
| `FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt` | `a79af57bce62caa8176773f76f10e058ee8f7bed96e7140592137674877b812a` | Authoritative two-stage execution prompt |

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
- Current state after S1-02: `NOT_PRODUCTION_ACCEPTED`.

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
SQLite/WAL/FTS5 storage, and the arXiv connector contract. They do not prove
Stage 1 production acceptance.

Stage 1 remains blocked until the V5 gates pass, including scoring and queue,
content ledger, B1 text report, B1 email contract, local runtime recovery,
migration package, 30 independent historical B1 report/email previews, and two
real natural days of B1 email delivery.
