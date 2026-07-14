# Memory Atlas v1.2 R3 Real Command Workflows Design

## Decision Status

This design implements Task 3 of the approved R0-R8 remediation plan only. It
connects the six accepted Command Palette actions to a controlled local runtime.
It does not implement proposal apply or rollback, owner-daily, final audit wiring,
Git reconciliation, app installation, Cloudflare deployment or GitHub push.

R3 is not accepted by source-string validators. Acceptance requires real HTTP,
process, filesystem and browser evidence for every command plus a hosted-static
read-only test.

## Problem

The current Command Palette has the right six labels, but a click only changes the
selected explanation and sometimes switches view. The local app server exposes only
runtime state, heartbeat and release endpoints. Cloudflare and the local app therefore
show the same non-executable surface.

Replacing this with six arbitrary shell strings would create a loopback remote-code
execution boundary. Mapping every action to a dry-run would be safe but would preserve
the user's core complaint: the product would still describe work instead of doing it.

## Selected Architecture

### 1. Tracked Runtime Server And Command Bridge

Move the runtime HTTP server out of the installer heredoc into a tracked Python
module. The installer still launches it from the Application Support source copy.
The server delegates only `/__memory_atlas_command` to a separate command bridge.

The bridge owns:

- the exact six-command allowlist;
- fixed argv construction with `shell=False`;
- workspace and import-inbox validation;
- a scrubbed child-process environment;
- one-command-at-a-time locking and timeouts;
- bounded, normalized Chinese results;
- atomic publication of a refreshed visualization snapshot;
- a metadata-only machine-local audit log.

No HTTP request field can supply a path, flag, command string, environment variable,
URL, shell fragment or target.

### 2. Installed-Copy Write Boundary

Commands may execute only when these paths have the exact relationship below:

```text
<app-support>/source   # installer-created source workspace
<app-support>/runtime  # served static runtime
```

`source/memory_atlas_source_workspace.json` must identify the installer copy. The
bridge refuses a canonical checkout, a missing manifest or a source/runtime pair with
different parents. R3 may write derived data and redacted sync results in the source
copy, but never the canonical Git worktree, installed Cloudflare assets or GitHub.

### 3. Loopback HTTP Contract

Endpoint: `POST /__memory_atlas_command`

Accepted request body:

```json
{"command_id":"sync_codex"}
```

Controls:

- server binds `127.0.0.1` only;
- client address must be loopback;
- `Host` must be the active `127.0.0.1` or `localhost` origin;
- `Origin` must exactly match the active local origin;
- JSON content type and a small bounded body are required;
- the JSON object must contain exactly `command_id`;
- unknown IDs, extra fields and concurrent execution are rejected;
- no CORS response headers are emitted.

Valid workflow outcomes use `success`, `needs_input` or `error`. Transport and
validation failures use HTTP errors. Every valid outcome has a Chinese title and next
step. Raw stdout, transcript content, absolute source paths and process environment are
not returned to the browser or written to the audit log.

## Six Command Mappings

| Command ID | Local action | Side effects | Browser action |
|---|---|---|---|
| `sync_chatgpt` | Accept exactly one regular `.zip` from the fixed local import inbox, run the existing official-export sync, rebuild the atlas and atomically publish the snapshot. With no ZIP, create the inbox and return `needs_input`. | Redacted/public sync and derived files in the installed source copy; runtime snapshot only. No browser login, cookie or token access. | Reload the atlas after success; show the fixed inbox instruction when input is missing. |
| `sync_codex` | Run the existing redacted Codex sync against configured local Codex home, rebuild the atlas and atomically publish the snapshot. | Redacted processed/public/derived files in the installed source copy; runtime snapshot only. | Reload the atlas after success. |
| `generate_weekly_report` | Build a deterministic Chinese weekly report from the current redacted visualization snapshot. | One derived Markdown report in the installed source copy. No raw read or write. | Navigate to Summary and show the relative output path. |
| `view_pending_proposals` | Run the proposal state-machine read path without apply. | None. | Navigate to Summary and show the pending count/status. |
| `generate_personalization_prompt` | Generate all ChatGPT, Codex and other-agent prompt exports from current redacted derived reports. | Derived prompt exports and their local export log in the installed source copy. | Navigate to Summary and list relative outputs. |
| `chatgpt_deep_explore` | Generate the deep-explore prompt in `prefill_only` mode without asking Python to open or submit a browser session. | Derived prompt and machine export in the installed source copy. | The explicit Execute click pre-opens a blank tab; after a successful response it navigates only to a validated `https://chatgpt.com/?q=...` URL. It never submits the prompt. |

The bridge has no mapping for `auto_submit`, proposal `apply`, proposal `rollback`,
Git push, deployment, future-agent sync or arbitrary `atlasctl` arguments.

## Weekly Report Contract

R3 adds a narrow builder rather than invoking the full raw-analysis pipeline. It reads
only `data/derived/visualization/memory_atlas.json`, uses the latest memory date as the
report anchor and writes a deterministic Chinese Markdown report containing:

- snapshot and seven-day range;
- total and recent memory counts;
- recent decisions and high-importance changes;
- pending proposal signals;
- current agent recommendations;
- explicit redacted-derived-data and no-remote-write boundaries.

The builder returns machine-readable JSON and writes atomically. It does not read an
OpenAI export, Codex transcript or private archive.

## Frontend Interaction

Command cards remain selectors so a sync does not start from an exploratory click.
The selected detail gains one explicit Execute button and a stable result region.
While a command is running, every Execute path is disabled and the result is announced
with `aria-live`.

Local runtime states are `idle`, `running`, `success`, `needs_input`, `error` and
`local_required`. A successful sync refetches `memory_atlas.json` with no-store cache.
A successful proposal, weekly or personalization command switches to Summary only
after the server result is received.

The static Cloudflare build contains no execution implementation. When runtime-state
detection says `static`, Execute performs no POST and displays:

```text
此操作仅在本地 Memory Atlas app 执行。
```

It also exposes the specific handoff `http://127.0.0.1:4177`. This link is a handoff,
not proof that a local server is running.

## Security And Privacy

- Child processes receive an allowlisted environment containing only required locale,
  path, home and temporary-directory values. Token, secret, key, auth and cookie
  variables are not forwarded.
- ChatGPT import is explicit, local and fixed-directory only. Symlinks, directories,
  non-ZIP files and multiple ambiguous ZIPs fail closed.
- Existing sync privacy guards remain authoritative for transcript redaction and
  plaintext-credential rejection.
- Deep explore accepts only `prefill_only`. The bridge validates scheme, hostname and
  query before returning an external URL; the frontend validates again before use.
- Audit rows contain command ID, outcome, timestamps and duration only.
- No command sends data to ChatGPT. The generated query remains in the browser address
  bar until the user reviews and submits it.

## Test Strategy

Python tests must prove:

- exact six-command registry and fixed argv;
- wrong workspace, arbitrary IDs/fields, bad content type, oversized body, remote
  origin, bad host and concurrent execution fail closed;
- server binding is loopback and runtime state advertises the command API;
- child environment excludes credential-like variables and all subprocess calls use
  list argv with `shell=False`;
- import inbox and deep-explore URL validation are strict;
- normalized failures always contain actionable Chinese text;
- existing launcher lifecycle behavior remains.

The Playwright validator must use a temporary installer-shaped source/runtime pair and
real scripts with synthetic ChatGPT/Codex fixtures. It must execute all six commands,
assert their file or navigation effects, intercept the ChatGPT prefill navigation and
prove there is no automatic submit. A separate Vite preview must prove the hosted
static build emits no command POST and shows the local-app handoff.

Lint, production build, R1/R2 multiviewport acceptance and Stage 7 visual regressions
remain mandatory R3 regressions.

## Requirement Impact

R3 may promote only requirements directly proven by final evidence:

- `S04-AC01` for the executable ChatGPT and Codex UI paths;
- `S12-AC01` for the exact six-command usable surface;
- `S12-AC02` for real all-target prompt generation;
- `S12-AC03` for a real ChatGPT prefill navigation;
- `S12-AC04` remains verified only if no-silent-send evidence passes.

All R4-R8 requirements remain unchanged. The release stays
`FAIL_REMEDIATION_REQUIRED` after R3.

## Rollback And Stop

Revert the local R3 commits. This removes the endpoint, bridge, weekly builder,
frontend execution states, tests and evidence while leaving R0-R2 intact.

Stop after the final local R3 commit. Do not start R4, push, reinstall the app or
deploy Cloudflare in this run.
