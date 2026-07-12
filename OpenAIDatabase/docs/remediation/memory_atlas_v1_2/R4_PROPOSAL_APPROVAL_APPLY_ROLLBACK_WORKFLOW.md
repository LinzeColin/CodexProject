# Memory Atlas v1.2 Remediation R4: Proposal Approval, Apply And Rollback

## Status

- Phase: `R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW`
- Phase result: `R4_COMPLETE_LOCAL_ONLY`
- Release result: `FAIL_REMEDIATION_REQUIRED`
- R3 closeout base: `e1a3d670d60673730d6b1b0c83c1b343403c9e69`
- R4 design: `8dd2e3c568b3c82917a8f60efbcb251211024f6c`
- R4 transaction engine: `8f75c0b8da334e3b2dd5d3f0a45a4dbb7abe7829`
- R4 endpoint: `a87cfbf782506f5957a997ef022912db67fc31d3`
- R4 rendered workspace: `c9910b6ed8ab01be7c14358a5dae7787164cf2cb`
- R4 security/recovery hardening: `b86d4b4435a3b89f92de721de7f46b3b193b1996`
- Final fetched `origin/main`: `07a6e50d593c7b9c74b8f3870b614be86a87160d`
- Pre-record divergence: local `main` is ahead 12 and behind 12.
- Push, app reinstall and Cloudflare deployment: `false`.
- Next phase: `R5_OWNER_DAILY_PRODUCT_ENTRY`.

R4 replaces fixture-only proposal evidence with a rendered local user workflow. It
reviews server-side apply-ready bundles, requires a one-time human authorization,
performs an exact full-file replacement inside an installer-shaped source copy, runs
fixed validation and preserves a durable rollback transaction. Acceptance used only a
temporary Application Support-shaped fixture; it did not mutate the canonical checkout,
raw data, the installed app or the online website.

## Authorization And Target Contract

- `view_pending_proposals` remains one of the exact six R3 commands and performs review
  only. Mutating actions use the separate same-origin endpoint
  `POST /__memory_atlas_proposal_action`.
- Approve/apply accepts only proposal ID, one-use review token and the exact Chinese
  confirmation. Rollback accepts only transaction ID, one-use rollback token and its
  exact confirmation. Browser callers cannot supply paths, content, argv, environment,
  validation commands or URLs.
- Review tokens are bound to proposal ID, bundle digest and TTL, then consumed once.
- Apply-ready bundles live only under
  `data/derived/proposals/apply_ready/*.json`, use full-file `replace_text`, carry an
  expected SHA-256 and select only `utf8_nonempty` and `json_document` validators.
- Seven target types map to fixed tracked roots. Raw, private, credential, archive,
  executable and Git paths are forbidden. Missing parent directories remain review-only
  and are never created before a transaction exists.

## Filesystem And Recovery Safety

- Target parents are opened from the installed source root with directory file
  descriptors and `O_NOFOLLOW | O_DIRECTORY`. Expected-hash reads, writes and in-process
  rollback use those held descriptors, so a parent path change cannot redirect a write.
- Atomic replacements use a same-directory staged regular file, `fsync` and descriptor-
  relative `os.replace`. Validation rereads targets through the same no-follow boundary.
- Before bytes, hashes and modes are stored under
  `<app-support>/proposal_transactions/<transaction>/`; metadata never stores operation
  content, authorization tokens or absolute source paths.
- Validation failure restores every target and verifies the original SHA-256 before
  returning `rollback_or_needs_revision`.
- A later review automatically restores interrupted `applying`, `applied` or
  `failed_validation` transactions. If a filesystem blocker prevents recovery, the UI
  exposes `manual_rollback_required`; after the blocker is removed, a separately
  acknowledged rollback restores the snapshot.
- Committed rollback points remain visible after closing and reopening the proposal
  workspace. The user can therefore roll back without relying on in-memory action state.

## Rendered User Path

The proposal workspace shows apply-ready and review-only proposals, risk and expiry,
exact target files, fixed validators, rollback scope and five Chinese diff sections:
`改了什么`, `为什么改`, `影响什么`, `如何验证`, `如何回滚`.

Apply is disabled until the user acknowledges the scope. A successful response shows
state history and validation results. Rollback requires a separate checkbox. Static
hosting sends no command/proposal POST and displays only the local handoff
`http://127.0.0.1:4177`.

## Browser Acceptance

`validate:v1.2-proposal-e2e` built the current frontend and exercised the rendered UI
against a temporary runtime. It proved:

- unauthorized, remote-Origin and extra-field requests are rejected;
- an authorized proposal changes a real fixture file;
- a committed rollback point is visible after closing and reopening the workspace;
- manual rollback restores exact original bytes;
- invalid JSON triggers automatic exact rollback;
- a raw-target bundle is review-only and its sentinel hash remains unchanged;
- audit rows are metadata-only and the canonical repo is unchanged;
- hosted static emits zero command/proposal POSTs and opens no fake workspace;
- the modal fits `1470x661`, `1440x900` and `390x844` with no horizontal overflow.

## Verification And Review

- Proposal/runtime tests: `40 tests`, PASS.
- Launcher regression: `1 test`, PASS.
- ChatGPT sync, Codex sync and personalization regressions: `15 tests`, PASS.
- TypeScript lint: PASS.
- Production build: PASS with the existing non-blocking chunk-size warning.
- `validate:v1.2-proposal-e2e`: PASS.
- `validate:v1.2-command-workflows`: PASS, six commands, static POST=0.
- `validate:v1.2-home-multiviewport`: PASS at all three required viewports.
- `validate:stage7-visual`: PASS; 11,828 Galaxy points, 64 River markers and 48
  density bands.
- Privacy guard: PASS, zero high-risk secret hits and zero tracked raw/private files.
- Independent review initially found one High and three Medium issues across two passes:
  target-parent redirection, hidden interrupted transactions, pre-transaction directory
  creation and a parent-fd leak. All were reproduced or covered by regression tests and
  fixed. Final reviewer result: `0 High / 0 Medium`.

## Requirement Delta

- `S13-AC01`: `VERIFIED -> VERIFIED`, stronger unauthorized browser/API evidence.
- `S13-AC02`: `PARTIAL -> VERIFIED`, real human-authorized rendered apply.
- `S13-AC03`: `VERIFIED -> VERIFIED`, five Chinese sections rendered in product UI.
- `S13-AC04`: `PARTIAL -> VERIFIED`, automatic, persistent manual and interrupted
  transaction rollback evidence.
- `S13-AC05`: `VERIFIED -> VERIFIED`, raw proposal review-only and sentinel unchanged.

Aggregate after R4: `VERIFIED 40 / PARTIAL 11 / FAILED 5 / NOT_VERIFIED 2` across 58
requirements. R5-R8 gaps remain, so the release stays FAIL.

## Evidence

- `机器治理/证据与日志/remediation/v1_2_r4/status.json`
- `机器治理/证据与日志/remediation/v1_2_r4/requirements_gap_delta.csv`
- `机器治理/证据与日志/remediation/v1_2_r4/browser/final/`
- `机器治理/证据与日志/remediation/v1_2_r4/regression/command/`
- `机器治理/证据与日志/remediation/v1_2_r4/regression/home/`
- `机器治理/证据与日志/remediation/v1_2_r4/regression/stage7/`

## Rollback And Stop

Revert all R4 commits after R3 closeout `e1a3d670d` while retaining R0-R3. This removes
the proposal transaction service, endpoint, rendered workspace, tests and R4 evidence without
touching raw data, credentials, installed apps, Cloudflare or GitHub main.

Stop after the R4 closeout commit. Do not start R5, merge/rebase remote history, push,
reinstall or deploy in this run. R8 must reconcile both histories and perform the only
final upload after all remaining requirements pass.
