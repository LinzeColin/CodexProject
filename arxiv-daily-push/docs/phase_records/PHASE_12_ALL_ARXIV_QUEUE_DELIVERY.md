# Phase 12 - All-arXiv Scan, Candidate Queue, ROI Ranking, and Mail Video Link

Date: 2026-06-22
Project: `arxiv-daily-push`
Version: `0.12.0`

## Goal

Upgrade the production path from the old single-query arXiv test default to a
bounded all-arXiv daily scan that can run in GitHub Actions, persist a candidate
queue, select one daily lead paper by ROI and learning value, publish daily
artifacts to GitHub Release, and send an email containing Chinese explanation
text, a video artifact link, and a candidate queue summary.

## Scope

- Added `global_scan.py` with the Phase 12 scan plan, candidate scoring,
  candidate queue persistence, daily input construction, video artifact
  manifest, Release link extraction, and email delivery package.
- Added CLI commands:
  - `plan-all-arxiv-scan`
  - `build-all-arxiv-daily-input`
- Updated scheduled production workflow to:
  - restore `adp-candidate-queue` from a configured path or previous workflow
    artifact;
  - scan the primary arXiv archive buckets rather than a single `cat:cs.AI`
    query;
  - upload `adp-scheduled-daily-input`, `adp-phase12-delivery-artifacts`, and
    `adp-candidate-queue`;
  - pass Phase 12 JSON artifacts as GitHub Release assets.
- Updated scheduled execution so real SMTP is allowed to count only when a
  GitHub Release video artifact link exists and the email package contains
  Chinese lesson content plus candidate queue summary.
- Updated trial-start workflow and gate validation so default-branch production
  startup also uses all-arXiv Phase 12 input evidence instead of a legacy
  single source batch.

## Evidence

- Official arXiv category taxonomy confirms the major groups and primary
  archive families used by the scan plan:
  `https://arxiv.org/category_taxonomy`.
- Official arXiv API documentation confirms the Atom API query surface used by
  the existing source ingest:
  `https://info.arxiv.org/help/api/user-manual.html`.
- Focused tests:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_phase12_pycache_trial PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_global_scan.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_production_scheduler.py arxiv-daily-push/tests/test_trial_start.py arxiv-daily-push/tests/test_trial_start_workflow.py -q`
  passed with 23 tests.

## Acceptance

- All-arXiv scan plan includes the primary archive set and explicitly rejects a
  collapsed `cat:cs.AI` production plan.
- Daily build selects exactly one lead paper and persists high-value unselected
  candidates.
- If no new high-value candidate exists, the builder can consume a queued
  candidate.
- Production-ready scheduled daily evidence requires a GitHub Release video
  artifact link, Chinese lesson content, candidate queue summary, real Release
  evidence, and real SMTP evidence.
- `ADP_PRODUCTION_ENABLED`, `ADP_SCHEDULED_RUN_ENABLED`,
  `ADP_ALLOW_SMTP_SEND`, and `ADP_ALLOW_RELEASE_UPLOAD` remain disabled by
  default and were not enabled in this phase.

## Remaining Risks

- This phase does not prove a live runner can fetch all archive buckets; that
  still depends on owner-provisioned GitHub Actions runner networking and TLS.
- Phase 12 currently creates a lightweight video artifact manifest and Release
  link gate; real MP4 rendering remains a later production hardening step.
- Real production launch still requires owner-provisioned SMTP, Release target,
  runner refs, default-branch workflow evidence, and 30-day operational
  evidence.

## Rollback

Revert `global_scan.py`, Phase 12 CLI commands, scheduled/trial-start workflow
changes, scheduled execution delivery package checks, tests, runbook/config
updates, governance entries, and restore version `0.11.27`.
