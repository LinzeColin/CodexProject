# Phase 12 Manual Delivery Internal Release Dedupe

Status: prepared for PR review; production schedule remains disabled.

## Context

- First manual run `27926461430` failed closed during GitHub Release creation because duplicate Release asset names reached `gh release create`.
- Version `0.12.3` deduplicated assets at the manual workflow command construction layer.
- Second manual run `27927785092` ran on GitHub-hosted `ubuntu-latest` from `main` commit `0da8463ad03c94c73c784213199bde8fee110a8d`.
- In run `27927785092`, preflight, all-arXiv daily input, candidate queue artifacts, MP4 render, and the scheduled delivery command step completed, but final fail-closed validation still failed because `release_delivery` internally passed repeated JSON asset paths to `gh release create`.

## Repair

- `release_delivery._inspect_assets` now skips repeated identical resolved asset paths before building the `gh release create` command.
- It blocks distinct files that would publish with the same Release asset filename, preserving fail-closed behavior for true filename conflicts.
- Focused tests cover both identical-path dedupe and conflicting duplicate-name blocking.
- PR CI run `27928505758` also showed the live all-ArXiv cloud dry-run can hit transient arXiv HTTP 429/rate-limit blocks after partial success.
- `build_live_all_arxiv_dry_run` now retries bounded transient 429/timeout blocks before declaring an archive failed, while still requiring all 20 primary archive buckets to pass before cloud readiness can pass.

## Safety

- No production schedule is enabled.
- No secret values are logged.
- No video is sent as an email attachment.
- Real SMTP remains blocked unless a GitHub Release video link is created.
- Transient retry does not relax the all-ArXiv acceptance gate: fewer than 20 verified archive buckets remains blocked.

## Next Gate

Open PR, wait for CI green, merge to `main`, then rerun the controlled manual workflow once more with the same confirmation string.
