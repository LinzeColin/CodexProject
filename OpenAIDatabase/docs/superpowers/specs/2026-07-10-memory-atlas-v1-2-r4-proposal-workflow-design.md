# Memory Atlas v1.2 R4 Proposal Approval, Apply And Rollback Design

## Decision Status

This design implements only `R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW` from the
approved R0-R8 remediation plan. It does not implement owner-daily, P0 visualization
workflows, snapshot parity, Git recovery, app installation, Cloudflare deployment or
GitHub push.

R4 supersedes the old S13 proof for product acceptance. A static approved fixture,
`would_apply=true`, source markers or a simulated failure do not prove this phase. R4
requires a rendered user review, a real isolated file mutation, post-write validation
and byte-for-byte rollback evidence.

## Source Requirements

The restored TaskPack requires this sequence:

```text
proposal-only -> human approval -> automatic apply -> validation -> commit/rollback
```

The product must prove:

- an unauthorized proposal cannot apply;
- a human-authorized proposal can apply automatically;
- the review presents Chinese sections for what changes, why, affected surfaces,
  validation and rollback;
- validation failure restores the pre-apply state;
- `data/public_raw/`, `data/raw/` and raw transcript archives can never be targets.

## Rejected Approaches

### Reuse The Static Approved Fixture

The current S13 P3 config declares `sample` approved before any current user action.
Calling its builder from the browser would preserve the exact false-positive that R0
reopened: the UI would only activate a pre-approved test contract. R4 therefore blocks
all direct non-dry-run `atlasctl apply` calls and never treats this fixture as live
human authorization.

### Pass Proposal Paths Or Validation Commands From The Browser

A request containing a target path, patch, argv or validation command would turn the
loopback service into a file-write or command-execution primitive. R4 accepts only a
proposal ID, a server-issued review token and an exact confirmation string.

### Apply Existing Suggestion Records Directly

The five current state-machine proposals identify broad directories and do not carry
an exact after-content payload or expected target hash. They remain reviewable but are
`review_only`; the UI explains which apply-ready fields are missing.

## Apply-Ready Bundle

Apply-ready bundles live only under:

```text
data/derived/proposals/apply_ready/*.json
```

Each file must be a regular, non-symlink JSON document with schema
`memory_atlas_apply_ready_proposal.v1_2_r4` and these exact concepts:

- unique `proposal_id` and state `pending_human_review`;
- supported `target_type`;
- non-expired `expires_at`, risk level and action half-life;
- Chinese human reason and five complete diff-narrator sections;
- one or more full-file replace operations, each containing one relative target,
  `expected_sha256` (`missing` for a new file) and bounded UTF-8 content;
- one or more fixed validation IDs;
- a Chinese rollback plan.

The browser never receives operation content or machine diff. It receives the target
paths, hashes, validation labels and human narrator only.

## Target Policy

Every target is resolved beneath the installer-created `source` root. Absolute paths,
`..`, empty components, directories, symlinks and symlinked parents fail closed. The
target-type mapping is fixed:

| Target type | Allowed local source paths |
|---|---|
| `memory` | `.codex/memories/extensions/ad_hoc/notes/` |
| `agents_rule` | `AGENTS.md`, `.agents/` |
| `config` | `config/`, `机器治理/运行门禁/` |
| `formula` | `机器治理/参数与公式/` |
| `ui_text` | `人类可读/` |
| `taxonomy` | `config/taxonomy/`, `data/derived/taxonomy/` |
| `report_template` | `人类可读/`, `config/report_templates/` |

All raw/private/credential/session/cookie/token/key fragments, `.git`, executable
source paths and the canonical repository remain forbidden regardless of target type.
The current file bytes must still match `expected_sha256` immediately before apply.

## Runtime API

R3 keeps its exact six-command API. Executing `view_pending_proposals` now returns a
sanitized review collection and a short-lived, single-use token for each apply-ready
proposal. This command remains read-only.

R4 adds one local-only endpoint:

```text
POST /__memory_atlas_proposal_action
```

It uses the existing loopback, Host, Origin, `Sec-Fetch-Site`, JSON, body-size and no-
CORS controls. Exact bodies are:

```json
{
  "action": "approve_apply",
  "proposal_id": "proposal-id",
  "review_token": "server-issued-token",
  "confirmation": "授权应用 proposal-id"
}
```

```json
{
  "action": "rollback",
  "transaction_id": "transaction-id",
  "rollback_token": "server-issued-token",
  "confirmation": "确认回滚 transaction-id"
}
```

Unknown/extra keys, stale/replayed tokens, wrong confirmation, changed bundle digest,
expired proposal and concurrent R3/R4 execution fail closed. The command bridge and
proposal action share one operation lock.

## Transaction And Validation

Before the first write, the service creates a machine-local transaction under
`<app-support>/proposal_transactions/<transaction_id>/`. It stores metadata and an
exact snapshot for every target. Writes use sibling temporary files plus `os.replace`.

Validation IDs map to in-process validators; bundles cannot supply commands. R4 starts
with `utf8_nonempty` and `json_document`. Validation runs after all writes:

- success records state transitions through `committed` and returns a rollback token;
- failure restores all snapshots before returning, verifies restored hashes and ends
  at `rollback_or_needs_revision`;
- manual rollback first verifies each target still matches the committed post-apply
  hash, then restores all snapshots and consumes its token.

Audit rows contain IDs, states, timestamps, target-relative paths and hashes only. No
file content, raw transcript, environment, stdout or absolute source path is logged.

## Product Interaction

The existing `查看待授权提案` command remains the entry. A successful read opens a
dedicated modal workspace rather than expanding the height-limited command panel.

The modal provides:

- proposal list with apply-ready/review-only, risk and expiry status;
- one selected proposal with all five Chinese narrator sections;
- exact target files and fixed validation labels;
- explicit acknowledgement before `授权并应用` becomes enabled;
- state history and validation result after apply;
- a second explicit acknowledgement before manual rollback;
- actionable explanations for review-only, stale, unauthorized and failed states.

The modal must fit and scroll correctly at `1470x661`, `1440x900` and `390x844`.
Hosted static execution continues to emit no command or proposal-action POST and shows
the exact local handoff `http://127.0.0.1:4177`.

## Test Strategy

Python tests must first fail and then prove:

- the bundle parser, target map, expected hash, symlink/path/raw deny and content bounds;
- direct `atlasctl apply` without an R4 UI token cannot write;
- missing/stale/replayed review tokens and extra HTTP fields fail closed;
- R3 and R4 operations share one lock;
- successful apply changes a real temporary target and manual rollback restores bytes;
- failed validation restores all target bytes before returning;
- transaction and audit metadata contain no content or absolute source path.

The Playwright validator must build the current frontend and use a temporary
installer-shaped source/runtime pair. Synthetic bundles cover unauthorized direct
apply, successful authorized apply, manual rollback, validation failure and raw target
rejection. It must exercise the rendered modal at all three required viewports and
prove the static build makes zero proposal-action requests.

R3 six-command E2E, Home multiviewport, Stage 7 visual, lint, production build and
privacy guard remain mandatory regressions.

## Requirement Impact

R4 may promote only requirements directly proven by final runtime evidence:

- `S13-AC02`: `PARTIAL -> VERIFIED` for real human-authorized apply;
- `S13-AC04`: `PARTIAL -> VERIFIED` for automatic and manual real rollback.

`S13-AC01`, `S13-AC03` and `S13-AC05` remain VERIFIED only if R4 adds stronger
rendered/runtime regression evidence. All R5-R8 requirements remain unchanged and the
release remains `FAIL_REMEDIATION_REQUIRED`.

## Rollback And Stop

Revert the local R4 commits while retaining R0-R3. This removes the bundle workflow,
endpoint, modal, tests and R4 evidence without touching raw data, credentials,
installed apps, Cloudflare or GitHub main.

Stop after the local R4 closeout commit. Do not start R5, reconcile Git, push,
reinstall or deploy in this run.
