# ADP Owner Center Entry Rule

- timestamp: `2026-06-26T16:55:00+10:00`
- task_id: `OWNER-CENTER-ENTRY-RULE`
- phase: `S2PI/S2PM`
- acceptance: `ACC-S2PIT01-USER-CENTER`, `ACC-S2PMT06-UX`
- status: `governance_rule_recorded`

## Scope

Record the owner-facing entry rule for ADP Stage 2 user-center and mail-status work:
GitHub-rendered Markdown is the primary human-readable surface, and the shallow
`arxiv-daily-push/用户中心/` folder is the preferred owner entry.

## Decisions

- Owner-facing pages must directly summarize `sent`, `blocked/not sent`, and
  `queued` states.
- Local `.adp` files, SMTP delivery reports, local run JSON, and candidate queue
  JSON remain valid evidence sources, but are not the owner reading entry.
- Deep `arxiv-daily-push/docs/owner/...` pages may remain generated/internal
  references or pointers; they must not be the only owner-facing route.
- This rule does not edit PR #240 owner pages, does not replay email, does not
  mutate queues, and does not change SMTP, scheduler, Release, public schema,
  DB, source adapters, ranking, CURRENT, V7.1, or V7.2 contract files.

## Boundaries

- No production switch.
- No scheduler enablement.
- No SMTP send or replay.
- No queue mutation.
- No public schema or DB migration.
- No inherited P0/P1 closure.
- No `S2PLT02` acceptance.
- No `INTEGRATED_PRODUCTION_ACCEPTED` or `DAILY_OPERATION` claim.

## Evidence

- `arxiv-daily-push/AGENTS.md`
- `governance/run_manifests/ADP-OWNER-CENTER-ENTRY-RULE-20260626.json`
- GitHub PR #240 discussion scope correction comment.
