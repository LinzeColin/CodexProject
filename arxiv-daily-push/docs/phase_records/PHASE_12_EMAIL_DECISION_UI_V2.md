# PHASE 12 EMAIL DECISION UI V2

Project: `arxiv-daily-push`
Task: `ADP-PHASE12-EMAIL-DECISION-UI-V2-038`
Iteration: `ITER-20260621-055`
Date: 2026-06-22
Status: `ready for PR CI and controlled manual rerun`

## Objective

Rebuild the daily email frontstage as a high-density Chinese decision brief,
based on the V2 mockup and owner correction notes, without changing all-arXiv
scanning, ROI ranking, candidate queue persistence, Release upload gates, SMTP
enablement gates, or scheduled production variables.

## Implemented

- Added a Lesson `frontstage` payload with read/skim/skip decision, attention
  score, evidence level, estimated reading time, one-line takeaway,
  first-principles chain, decision mappings, three key questions, evidence
  gaps, default action, and video-card metadata.
- Rendered daily delivery email as concise Chinese plain text plus responsive
  HTML alternative.
- Changed the email subject to the V2 decision format:
  `[QF Daily｜扫读 3.8/5] <one-line takeaway>`.
- Removed user-visible Claim Ledger IDs, backend ROI score, delivery policy
  text, Release landing-page link clutter, and repeated English summary from
  the frontstage email.
- Kept video as a Release-hosted `.mp4` watching/download link card. The video
  is not attached to the email.
- Filtered frontstage candidate queue summaries so q-fin emails do not show
  irrelevant quant-ph or q-bio candidates unless a cross-domain finance or
  market mapping reason is explicit.
- Added feedback actions: `值得深入`, `相关性低`, `太浅`, `太长`, `需要实验`.
- Updated SMTP delivery to include an HTML alternative and record only body
  hashes, never raw email body content.

## Non-Scope

- No production schedule enablement.
- No new real SMTP send in this code-change commit.
- No direct GitHub Release upload in this code-change commit.
- No change to all-arXiv scan scope, ROI ranking, or candidate queue persistence.
- No secret value logging.
- No video attachment in email.

## Validation

Already run before governance updates:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_v2_pycache_focus3 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_notifications.py arxiv-daily-push/tests/test_lesson.py arxiv-daily-push/tests/test_global_scan.py arxiv-daily-push/tests/test_video.py arxiv-daily-push/tests/test_scheduled_execution.py -q`
  - Result: `Ran 35 tests in 0.223s OK`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_v2_pycache_all2 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q`
  - Result: `Ran 185 tests in 2.272s OK`
- In-memory q-fin render probe:
  - Subject: `[QF Daily｜扫读 3.8/5] 同步提高产出，也可能制造拥挤交易脆弱性。`
  - Plain text length: `678`
  - HTML alternative length: `5322`
  - Verified absent: `Claim Ledger`, `roi_total_score`, `ROI score`,
    `delivery_policy`, Release landing-page tag link, irrelevant quant-ph title,
    irrelevant q-bio title.

Post-S1-04 validation completed locally: focused email V2 tests 35 OK; semantic extractor checked 39 active formulas and 278 active parameters; arxiv-daily-push tests 189 OK; governance dashboard PASS; root governance tests 128 OK; changed-only governance sync errors 0 warnings 0; information quality PASS; manifest JSON and CSV width checks PASS. PR CI and controlled manual real-email rerun remain required before replacing the latest owner-visible proof.

## Acceptance Boundary

This phase is accepted locally only when focused tests, full ADP tests,
semantic governance validation, changed-only governance sync, information
quality validation, JSON parsing, diff check, and cache check pass. It does not
claim production readiness. The next real owner-visible proof must be a
controlled GitHub Actions manual delivery rerun after PR CI passes and the PR is
merged to `main`.

## Rollback

Revert version `0.14.1` email decision UI V2 code, tests, schema updates,
governance records, phase record, manifest, and event; restore version
`0.14.0`; keep production variables disabled.
