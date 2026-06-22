# Phase 12 Production Enablement Cloud Gate

Date: 2026-06-22
Version: 0.12.1
Status: completed for cloud enablement preparation; production remains disabled

## Scope

- Move active arXiv Daily Push workflows to GitHub-hosted `ubuntu-latest`.
- Add a cloud dry-run workflow that verifies all 20 arXiv primary archive buckets and renders a real lightweight MP4 artifact.
- Keep Gmail SMTP sending, GitHub Release uploading, scheduled production, and production acceptance fail-closed until explicit evidence passes.

## Implemented

- Added `.github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml`.
- Added `run-live-all-arxiv-dry-run` CLI path with `sample_daily_input` artifact output.
- Added `render-lightweight-mp4` CLI path using `ffmpeg` to produce a non-empty `.mp4` artifact and transcript.
- Updated scheduled, trial-start, production-trial, and provisioning-audit workflows to avoid self-hosted runner targeting.
- Tightened Release video-link selection so only `.mp4` assets satisfy email video-link readiness.
- Lowered production preflight disk threshold to the lightweight MP4 cloud profile while preserving command, secret, memory, Git hygiene, and cache gates.

## Not Enabled

- `ADP_PRODUCTION_ENABLED` remains false.
- `ADP_SCHEDULED_RUN_ENABLED` remains false.
- `ADP_ALLOW_SMTP_SEND` remains false unless the owner intentionally runs a controlled manual test.
- `ADP_ALLOW_RELEASE_UPLOAD` remains false unless the owner intentionally runs a controlled manual test.

## Evidence

- `arxiv-daily-push/tests/test_cloud_dry_run_workflow.py`
- `arxiv-daily-push/tests/test_global_scan.py`
- `arxiv-daily-push/tests/test_video.py`
- `arxiv-daily-push/tests/test_production_scheduler.py`
- `arxiv-daily-push/tests/test_trial_start_workflow.py`

## Remaining External Gates

- Run the new cloud dry-run workflow on GitHub and archive `adp-phase12-cloud-dry-run`.
- Confirm the workflow verifies 20 primary archive buckets with live arXiv data.
- Confirm the workflow uploads a real `.mp4` artifact and render report.
- Run a controlled manual Release upload and Gmail SMTP test only after the dry-run passes.
- Enable scheduled production variables only after PR/CI, Release, SMTP, and artifact evidence pass.
