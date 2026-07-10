# Memory Atlas v1.2 Remediation R3: Real Command Palette Workflows

## Status

- Phase: `R3_REAL_COMMAND_PALETTE_WORKFLOWS`
- Phase result: `R3_COMPLETE_LOCAL_ONLY`
- Release result: `FAIL_REMEDIATION_REQUIRED`
- R2 base commit: `d758c0af871430bee9d736d0d6e09a7028a4e193`
- R3 design commit: `6e831ab843b993784e2bd034d4d3955d25477509`
- R3 implementation commit: `b0c11acb7645bb3a7b65b6e20beb418c77e04bf8`
- Final fetched `origin/main`: `bd06ee38c1b8c52bcafd68b3c3b0a752a53cae62`
- Pre-record closeout divergence: local `main` is ahead 6 and behind 10.
- Remote push, app reinstall and Cloudflare deployment: `false`.
- Next phase: `R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW`.

R3 turns the six Command Palette actions into real, allowlisted local workflows. The
acceptance run used a temporary installer-shaped `source/runtime` pair and synthetic
ChatGPT/Codex fixtures; it did not mutate the canonical checkout. The currently
installed app and online website were not updated and must not be presented as R3.

## Runtime Contract

- The tracked `scripts/memory_atlas_runtime_server.py` binds only to `127.0.0.1` and
  exposes `POST /__memory_atlas_command` for an exact `{"command_id":"..."}` body.
- Host, Origin, `Sec-Fetch-Site`, content type, body length and exact key set are
  validated. The same-origin checks also protect heartbeat and release lifecycle
  endpoints; no CORS headers are emitted.
- `scripts/memory_atlas_command_bridge.py` accepts exactly six IDs, builds fixed argv,
  uses `shell=False`, scrubs child environment variables and permits one command at a
  time.
- Commands execute only inside an installer-shaped `<app-support>/source` paired with
  `<app-support>/runtime`. Symlinks, `.git`, source/runtime path escape and a manifest
  naming the canonical checkout are rejected.
- Timeout handling terminates the complete child process group with SIGTERM and then
  SIGKILL if needed before the command lock is released.
- Audit rows contain command ID, outcome, timestamps and duration only. They do not
  contain stdout, transcript content, absolute source paths or environment values.

## Six Real Workflows

| Command | Real local result | User and safety boundary |
|---|---|---|
| `sync_chatgpt` | Reads exactly one regular ZIP from the fixed import inbox, runs the existing redacted sync, rebuilds the atlas and atomically refreshes the runtime snapshot. | No cookies, tokens, login session or arbitrary path input. Missing input returns `needs_input`. |
| `sync_codex` | Runs the existing redacted Codex sync, rebuilds the atlas and refreshes the runtime snapshot. | Writes only to the installer-shaped source/runtime fixture in acceptance. |
| `generate_weekly_report` | Builds a deterministic Chinese seven-day report from `data/derived/visualization/memory_atlas.json`. | No raw input and no remote write. |
| `view_pending_proposals` | Reads proposal state and reports the pending count. | No apply or rollback route exists in R3. |
| `generate_personalization_prompt` | Generates ChatGPT, Codex and other-agent prompt artifacts. | Artifacts remain local; nothing is sent automatically. |
| `chatgpt_deep_explore` | Generates a `prefill_only` prompt/export and returns a validated ChatGPT URL. | The explicit browser click preopens a blank tab and performs one GET to the prefilled URL; it never submits. |

The frontend keeps command cards as selectors and adds one explicit Execute button.
The stable result region reports `idle`, `running`, `success`, `needs_input`, `error`
or `local_required`; all command controls are disabled while one action runs. Sync
success refetches the snapshot. Result navigation remains an explicit second action so
the execution result stays visible.

## Hosted Static Boundary

The production static surface has no command backend. The separate hosted-static
browser case observed `command_post_count=0` and displayed the exact local handoff
`http://127.0.0.1:4177`. A static click therefore cannot invoke the loopback command
endpoint or imply that a local server is running.

## Real Browser Acceptance

The R3 validator built the current frontend, created a temporary installer-shaped
workspace, launched the tracked runtime server and executed all six commands through
the rendered UI. It proved:

- six exact request IDs and successful normalized Chinese outcomes;
- ChatGPT and Codex sync artifacts plus an atomically refreshed runtime snapshot;
- weekly, personalization and deep-explore output files;
- proposal read without apply;
- remote Origin, remote lifecycle Origin and extra request fields rejected;
- no CORS, metadata-only audit, no canonical-repo mutation and no remote push;
- deep explore issued only one intercepted `GET`, with no silent submit;
- three nonblank local/static screenshots and no static command POST.

The three-viewport Home regression also passed at `1470x661`, `1440x900` and
`390x844`: overlap, horizontal overflow and viewport escape remain zero; all six
actions are scroll-reachable; the nine Chinese behavior summaries remain reachable.
Stage 7 also passed with 67,201 Galaxy lit samples, 11,828 points, 64 Memory River
markers and 48 density bands.

## Verification And Review

- Focused Python contracts: `36 tests`, PASS.
- TypeScript lint: PASS.
- Production build: PASS; the existing chunk-size warning is non-blocking.
- `validate:v1.2-command-workflows`: PASS.
- `validate:v1.2-home-multiviewport`: PASS for all three target viewports.
- `validate:stage7-visual`: PASS.
- Privacy scan: zero high-risk secret hits and zero tracked raw-private files.
- Independent review initially found one High and three Medium issues: descendant
  timeout cleanup, source symlink bypass, lifecycle same-origin validation and stale
  `dist` acceptance. Regression tests reproduced all four before implementation fixes.
- Final reviewer result: `0 High / 0 Medium` open findings.
- Residual Low risks: a future trusted child that deliberately double-forks/creates a
  new session could escape process-group termination; installed-workspace trust still
  depends on the installer manifest. Neither is exposed through the current fixed
  allowlist.

## Requirement Delta

R3 promotes four previously incomplete requirements and preserves one verified
requirement with stronger evidence:

- `S04-AC01`: `PARTIAL -> VERIFIED`.
- `S12-AC01`: `PARTIAL -> VERIFIED`.
- `S12-AC02`: `PARTIAL -> VERIFIED`.
- `S12-AC03`: `FAILED -> VERIFIED`.
- `S12-AC04`: `VERIFIED -> VERIFIED` with explicit no-silent-send browser evidence.

The aggregate after R3 is `VERIFIED 38 / PARTIAL 13 / FAILED 5 / NOT_VERIFIED 2`
across 58 requirements. R4-R8 gaps remain unchanged, so the release stays FAIL.

## Evidence

- `机器治理/证据与日志/remediation/v1_2_r3/status.json`
- `机器治理/证据与日志/remediation/v1_2_r3/requirements_gap_delta.csv`
- `机器治理/证据与日志/remediation/v1_2_r3/browser/final/`
- `机器治理/证据与日志/remediation/v1_2_r3/regression/home/`
- `机器治理/证据与日志/remediation/v1_2_r3/regression/stage7/`
- `docs/superpowers/specs/2026-07-10-memory-atlas-v1-2-r3-command-workflows-design.md`

## Rollback And Stop

Revert the two local R3 commits while retaining R0-R2. This removes the endpoint,
bridge, weekly builder, execution UI, tests and R3 evidence without touching raw data,
credentials, installed apps, Cloudflare or GitHub main.

Stop after the local R3 closeout commit. Do not start R4, merge/rebase the remote
Cloudflare history, push, reinstall or deploy in this run. R8 must reconcile both Git
histories and run the single final delivery only after all remaining phases pass.
