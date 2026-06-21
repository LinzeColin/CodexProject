# arXiv Daily Push Agent Rules

This project follows the root `AGENTS.md` and `docs/governance/STANDARD.md`.

## Permanent Rules

- Work one phase, one task ID, and one acceptance target at a time.
- Use `docs/pursuing_goal/06_PURSUING_GOAL_READY_PROMPT.md` as the long-term
  goal baseline.
- Phase 1-11 start with arXiv as the only implemented source, but core
  interfaces must stay source-adapter based.
- Do not use OpenAI Platform API keys or paid API fallbacks.
- Do not read, print, or commit Codex auth, GitHub tokens, SMTP secrets, cookies,
  voice samples, model weights, or release media.
- Do not commit MP4, WAV, FLAC, MOV, model weights, render cache, `node_modules`,
  or virtualenv directories.
- Email is the notification channel; dry-run rendering is allowed before real
  SMTP transport exists.
- Any unsupported key factual claim must block publication.

## Phase 1 Boundary

Allowed:

- CLI skeleton.
- `doctor` and `version`.
- config examples.
- schemas.
- dry-run notification renderer.
- governance files and tests.

Forbidden:

- arXiv ingest implementation.
- scoring/ranking implementation.
- Claim Ledger extraction.
- TTS/video dependencies or downloads.
- GitHub Actions runner configuration.
- real email sending.

