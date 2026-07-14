# Memory Atlas v1.2 Remediation R5: Owner Daily Product Entry

## Status

- Phase: `R5_OWNER_DAILY_PRODUCT_ENTRY`
- Phase result: `R5_COMPLETE_LOCAL_ONLY`
- Release result: `FAIL_REMEDIATION_REQUIRED`
- R4 closeout base: `47d32d59d18f396ec07bfab3e01ce325a0ef2644`
- R5 design: `121e9c292`
- R5 shared runner: `ea8915872`
- R5 executed-step validator: `e5b5f18ce`
- R5 loopback API: `acb1ab117`
- R5 rendered workspace: `75e02962b`
- R5 acceptance hardening: `dc7932883`
- Final fetched `origin/main`: `07a6e50d593c7b9c74b8f3870b614be86a87160d`
- Pre-record divergence: local `main` is ahead 20 and behind 12.
- Push, app reinstall and Cloudflare deployment: `false`.
- Next phase: `R6_P0_VISUALIZATION_AND_FILTERING`.

R5 turns the historical Owner Daily plan into a real local product path. The same
fixed runner now powers `atlasctl`, the local loopback API and the rendered workspace.
It executes eight ordered no-write checks, continues after a failed step and permits
retry only for the failed step ID selected from the server-side allowlist. Acceptance
used a temporary installer-shaped runtime and did not mutate the canonical checkout,
raw data, installed app, online site or GitHub.

## Fixed Runner Contract

The exact ordered step IDs are:

1. `sync`
2. `analyze`
3. `build-atlas`
4. `audit`
5. `push`
6. `proposals`
7. `generate-personalization-prompt`
8. `deep-explore`

Every child argv is generated server-side, runs with `shell=false`, a scrubbed
environment and process-group cleanup. Child output is capped at 1 MiB and the final
result at 64 KiB. The aggregate result scans every nested dictionary and list for an
explicit unsafe `true` flag before accepting a step. Full runs continue after failure;
retry accepts one exact allowlisted step ID and cannot receive argv, paths, environment
or mode from the browser.

`atlasctl run --profile owner-daily --dry-run` delegates to this shared runner. A
non-dry-run request fails closed. The installed-source `push --dry-run` path recognizes
only a valid installer-shaped source copy without Git metadata and still forbids
`--apply`.

## Local API And Product Path

- `POST /__memory_atlas_owner_daily` accepts only `{"action":"run"}` or
  `{"action":"retry","step_id":"<fixed-id>"}`.
- Host and Origin must match the same exact loopback spelling; CORS is disabled.
- Owner Daily shares the R3/R4 execution lock and records only bounded metadata in
  `owner_daily_audit.jsonl`.
- The existing six R3 Command Palette cards remain exactly six. Owner Daily is a
  separate compact maintenance band, not a seventh command or another workspace row.
- Opening the modal does not execute. The user must explicitly start the run.
- Human conclusion and completed/failed counts precede eight ordered step results.
- Only a failed step exposes retry. A successful retry merges back into the same
  eight-step result.
- Initial focus moves to Start, Tab/Shift+Tab remain trapped in the dialog and Escape
  closes only while no action is running.
- Hosted static performs zero Owner Daily POSTs and exposes only the exact local-app
  handoff `http://127.0.0.1:4177`.

## Browser Acceptance

`validate:v1.2-owner-daily-e2e` built the current frontend and exercised the real
runtime server, bridge and shared runner against a fixed stub `atlasctl`. It proved:

- the initial eight-step run returns `7 passed / 1 failed` and keeps all steps visible;
- retry invokes only `audit`, then merges to `8 passed / 0 failed`;
- browser request bodies are exactly Run followed by Retry Audit;
- remote Origin, extra argv/body fields and unknown step IDs are rejected;
- source and runtime SHA-256 values remain unchanged;
- the audit contains metadata only and reports no canonical mutation or remote push;
- static hosting sends zero POSTs and opens no fake executable workspace;
- the modal has no horizontal overflow at `1470x661`, `1440x900` or `390x844`;
- five screenshots cover partial desktop/mobile, pass after retry and static fallback.

## Verification And Review

- Owner Daily/runtime focused tests: `39 tests`, PASS.
- Broad R3-R5 runtime, launcher, sync and personalization tests: `74 tests`, PASS.
- `validate:v1.2-s14-p1`: PASS with eight actually executed no-write steps.
- TypeScript lint: PASS.
- Production build: PASS with the existing non-blocking chunk-size warning.
- `validate:v1.2-owner-daily-e2e`: PASS.
- `validate:v1.2-proposal-e2e`: PASS, including real apply and rollback fixtures.
- `validate:v1.2-command-workflows`: PASS, six commands, static POST=0.
- `validate:v1.2-home-multiviewport`: PASS at all three required viewports.
- `validate:stage7-visual`: PASS; 11,828 Galaxy points, 64 River markers and 48
  density bands.
- Privacy guard: PASS, zero high-risk secret hits and zero tracked raw/private files.
- `npm ci --ignore-scripts --no-audit --no-fund` recovered Playwright `1.61.1` from
  committed npm metadata; a fresh build and R5 E2E passed.
- Independent review found zero High and three Medium issues across two passes: exact
  Host/Origin matching and unsafe child flags at top-level and arbitrary nesting. All
  were covered by regressions and fixed. The Low modal focus issue was also fixed.
  Final reviewer result: `0 High / 0 Medium`.

## Requirement Delta

- `S14-AC01`: `VERIFIED -> VERIFIED`, now backed by shared runner, API and rendered
  browser execution rather than CLI-only evidence.
- `S14-AC04`: `PARTIAL -> VERIFIED`, with a clear local maintenance entry, human result
  summary, eight steps and actionable fixed retry.
- `S14-AC02`: remains `FAILED`; final audit integration is reserved for R8.
- `S14-AC03`: remains `VERIFIED`; R8 must keep the current-state records authoritative.
- `S14-AC05`: remains `FAILED`; corrected aggregate stage-gate truth is reserved for R8.

Aggregate after R5: `VERIFIED 41 / PARTIAL 10 / FAILED 5 / NOT_VERIFIED 2` across 58
requirements. R6-R8 gaps remain, so the release stays FAIL.

## Evidence

- `机器治理/证据与日志/remediation/v1_2_r5/status.json`
- `机器治理/证据与日志/remediation/v1_2_r5/requirements_gap_delta.csv`
- `机器治理/证据与日志/remediation/v1_2_r5/browser/final/`
- `机器治理/证据与日志/remediation/v1_2_r5/regression/command/`
- `机器治理/证据与日志/remediation/v1_2_r5/regression/proposal/`
- `机器治理/证据与日志/remediation/v1_2_r5/regression/home/`
- `机器治理/证据与日志/remediation/v1_2_r5/regression/stage7/`

## Rollback And Stop

Revert all R5 commits after R4 closeout `47d32d59d` while retaining R0-R4. This removes
the shared Owner Daily runner, endpoint, rendered workspace, tests, Playwright recovery
metadata and R5 evidence without touching raw data, credentials, installed apps,
Cloudflare or GitHub main.

Stop after the R5 closeout commit. Do not start R6, merge/rebase remote history, push,
reinstall or deploy in this run. R8 must reconcile both histories and perform the only
final upload after all remaining requirements pass.
