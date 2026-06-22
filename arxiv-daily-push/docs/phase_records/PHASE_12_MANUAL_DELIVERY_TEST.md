# Phase 12 Manual Release And SMTP Delivery Test

Date: 2026-06-22
Version: 0.12.2
Status: workflow prepared; real manual test not yet run

## Scope

- Add a default-branch-only GitHub Actions workflow for one controlled manual delivery test.
- Build all-arXiv daily input, candidate queue, and lightweight MP4 before any delivery side effect.
- Create a GitHub Release containing the MP4 and JSON evidence artifacts.
- Send one Gmail SMTP email to `linzezhang35@gmail.com` with Chinese lesson text, Release link, video link, and candidate queue summary.

## Implemented

- Added `.github/workflows/arxiv-daily-push-manual-delivery-test.yml`.
- Required exact confirmation string `SEND_TEST_EMAIL_TO_LINZEZHANG35_GMAIL_COM`.
- Required default branch execution after PR CI and merge.
- Used GitHub-hosted `ubuntu-latest`; no local Mac runner, CPU, memory, cache, storage, or GPU dependency.
- Reused `run-scheduled-production --mode daily-run` so the email is built after Release creation and contains the Release-hosted `.mp4` link.
- Added workflow and scheduled-execution tests proving the manual email path includes GitHub Release/video links and candidate queue summary.

## Not Yet Executed

- No real Gmail SMTP email has been sent in this preparation commit.
- No real GitHub Release has been uploaded in this preparation commit.
- `ADP_PRODUCTION_ENABLED` remains false.
- Production scheduled execution remains disabled and must not be enabled until this manual test passes and the owner explicitly approves.

## Required Secrets

- Required: `ADP_SMTP_PASSWORD`.
- Optional overrides: `ADP_SMTP_HOST`, `ADP_SMTP_PORT`, `ADP_SMTP_USERNAME`.
- Defaults: Gmail SMTP host `smtp.gmail.com`, port `587`, username `linzezhang35@gmail.com`.

## Evidence

- `.github/workflows/arxiv-daily-push-manual-delivery-test.yml`
- `arxiv-daily-push/tests/test_manual_delivery_workflow.py`
- `arxiv-daily-push/tests/test_scheduled_execution.py`

## Next Step

After PR CI is green and the PR is merged to the default branch, manually run `arXiv Daily Push manual Release and SMTP test` from GitHub Actions with the confirmation string. Inspect the generated Release/video links and confirm the email arrived before considering scheduled production enablement.
