# Phase 12 Manual Delivery Release Asset Dedupe

Date: 2026-06-22
Version: 0.12.3
Status: prepared

## Scope

- Fix the manual Release plus Gmail SMTP workflow after run `27926461430` failed closed during GitHub Release creation.
- Deduplicate Release asset paths by filename before invoking `run-scheduled-production`.
- Preserve the required order: preflight, all-arXiv daily input, MP4 render, Release-backed scheduled execution, then SMTP.

## Evidence From Failed Manual Run

- GitHub Actions run `27926461430` ran on GitHub-hosted Ubuntu, not a local Mac.
- Preflight, all-arXiv daily input, candidate queue artifact upload, MP4 render, and scheduled execution report upload completed.
- The scheduled execution report ended `status=degraded` because Release creation failed before SMTP.
- SMTP stayed fail-closed: no real email was sent without a Release-hosted video link.

## Safety Boundary

- No production schedule is enabled by this patch.
- No secret values are logged.
- No video attachment is sent by email.
- The next required evidence is a new default-branch manual workflow dispatch that creates the Release and sends one Gmail SMTP test email to `linzezhang35@gmail.com`.
