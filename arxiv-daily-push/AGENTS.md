# arXiv Daily Push Agent Rules

This project follows the root `AGENTS.md` and `docs/governance/STANDARD.md`.

## Permanent Rules

- Work one phase, one task ID, and one acceptance target at a time.
- Use `docs/pursuing_goal/v7_1/V7_1_ROOT_LOCK.yaml`,
  `docs/pursuing_goal/v7_1/machine_readable/product_contract_v7.yaml`,
  `docs/pursuing_goal/v7_1/ROADMAP/roadmap_v7.yaml`, and
  `docs/pursuing_goal/v7_1/ROADMAP/ARXIV_DAILY_PUSH_ROADMAP_V7_1_CN.md` as the
  current execution contract. V5/V6/V7.0 files remain historical evidence and
  alias references; they no longer override V7.1.
- Every implementation closeout must state the current V7.1 Task ID and any
  legacy alias. Current development entry is `S2PCT02` (`S2P2T02` legacy alias)
  Science/top-journal metadata-only no-send shadow evidence. `S2PCT01`
  (`S2P2T01` legacy alias) Nature/top-journal metadata-only no-send shadow
  foundation has merged to main and remains a completed D2 shadow foundation
  record, not a D2 source-domain acceptance claim. `S2PBT01`
  (`S2P1T01` legacy alias) bioRxiv/medRxiv no-send replay and shadow evidence
  has passed and remains a D1 alias/history record, not the current task.
  Formal source production inclusion, `STAGE2_PRODUCTION_ACCEPTED`, and
  `INTEGRATED_PRODUCTION_ACCEPTED` remain blocked by V7.1 P0/P1 and final gate
  rules.
  `ADP-S1P5T05` completed the Stage 1 local production and migration prep after
  `ARXIV_PRODUCTION_ACCEPTED`.
  Final Stage 1 production strategy is local Mac + Codex/local runner; GitHub
  is code, PR/CI, evidence, status, and backup only, not the daily production
  runner.
- Stage 1 starts with arXiv as the only production-acceptance source and remains
  `ARXIV_PRODUCTION_ACCEPTED`. Stage 2 may promote additional sources and
  boards only after the V7 contract is readable, hashes match, and source-level
  gates pass, and P0/P1 audit findings are zero. Stage 2 is not complete until
  `S2PMT07 -> INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`.
- Legacy `S2P2T02` maps to V7.1 `S2PCT02`; legacy `S2P2T01` maps to V7.1
  `S2PCT01`; legacy `S2P1T01` maps to V7 `S2PBT01`. Preserve both canonical
  and legacy IDs in events, PR summaries, and closeouts until the Stage2 branch
  has reconciled aliases.
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
- Connectors and source adapters must not generate final emails directly.
  Source output flows through EvidencePacket, routing, quality gates, review,
  action, ROI, and the 3+1 mail product contract.

## Stage 1 Window A Boundary

Allowed:

- code, schemas, fixtures, governance files, and tests.
- at most 10 online arXiv metadata records.
- small local artifacts needed for validation.

Forbidden:

- PDFs or bulk source downloads.
- large models, TTS model downloads, or media generation.
- formal scheduler installation before explicit owner smoke-test approval.
- new 30-day replay or production-acceptance claims unless the task explicitly
  requires them.
- broad non-arXiv source expansion before Stage 1 gates pass.
