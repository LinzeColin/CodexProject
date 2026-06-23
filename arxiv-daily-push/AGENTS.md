# arXiv Daily Push Agent Rules

This project follows the root `AGENTS.md` and `docs/governance/STANDARD.md`.

## Permanent Rules

- Work one phase, one task ID, and one acceptance target at a time.
- Use `docs/pursuing_goal/BASELINE_LOCK.md`,
  `docs/pursuing_goal/START_HERE_MASTER_TASK_PACK_TWO_STAGE_TEXT_DELIVERY_V5.md`,
  and `docs/pursuing_goal/FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt`
  as the current long-term goal baseline. V4 and
  `docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md` are legacy baselines,
  not the current execution contract.
- Stage 1 starts with arXiv as the only production-acceptance source; Stage 2
  may promote additional sources and boards only after the arXiv gates pass.
- Do not use OpenAI Platform API keys or paid API fallbacks.
- Do not read, print, or commit Codex auth, GitHub tokens, SMTP secrets, cookies,
  voice samples, model weights, or release media.
- Do not commit MP4, WAV, FLAC, MOV, model weights, render cache, `node_modules`,
  or virtualenv directories.
- V5 Stage 1 delivery is text-first: high-density reports, independent emails,
  Markdown/HTML/JSON audit artifacts, and no required video generation.
- 30-day-grade evidence means 30 independent unique-date artifacts and coverage
  checks, not waiting 30 wall-clock days when real-data evidence can be
  generated and verified faster.
- Email is the notification channel; dry-run rendering is allowed before real
  SMTP transport exists.
- Any unsupported key factual claim must block publication.

## Stage 1 Window A Boundary

Allowed:

- code, schemas, fixtures, governance files, and tests.
- at most 10 online arXiv metadata records.
- small local artifacts needed for validation.

Forbidden:

- PDFs or bulk source downloads.
- large models, TTS model downloads, or media generation.
- formal scheduler installation before migration readiness.
- 30-day replay or production-acceptance claims.
- broad non-arXiv source expansion before Stage 1 gates pass.
