# Memory Atlas v1.2 R5 Owner Daily Product Entry Design

## Decision Status

This design implements only `R5_OWNER_DAILY_PRODUCT_ENTRY` from the approved R0-R8
remediation plan. It does not implement R6 visualization closure, R7 snapshot parity,
R8 final audit or recovery, Git reconciliation, GitHub push, app reinstall or
Cloudflare deployment.

R5 supersedes the old S14 P1 plan-only proof for product acceptance. Returning eight
command strings, passing source-marker checks or executing each command in a separate
validator does not prove an owner can run and understand the workflow. R5 requires one
rendered local product entry, one real sequential no-write run, visible partial failure
and a fixed single-step retry path.

## Source Requirements

The restored Roadmap defines one low-burden `owner-daily` profile covering:

1. `sync`
2. `analyze`
3. `build-atlas`
4. `audit`
5. `push`
6. `proposals`
7. `generate-personalization-prompt`
8. `deep-explore`

Every child operation must run in dry-run mode. The product must expose a small number
of clear maintenance controls, Chinese conclusions and queryable step status without
claiming that the R8 final audit or release is complete.

## Rejected Approaches

### Keep The Historical Plan-Only Profile

The old `atlasctl run --profile owner-daily --dry-run` returns only fixed invocations.
That proves allowlisting but not execution, sequencing, partial failure, conclusions or
retry. R5 keeps the historical plan fields for compatibility and adds real bounded
results from those fixed invocations.

### Add Owner Daily As A Seventh Command Card

R3 acceptance fixes the command palette at exactly six workflows. Owner Daily is an
orchestration surface, not another single command. It therefore receives a separate
maintenance band and modal workspace while the six R3 command IDs remain unchanged.

### Let The Browser Supply Commands Or Retry Arguments

Accepting argv, paths, environment, URLs or arbitrary step names would create a local
command-execution primitive. The browser may request only `run` or retry one server-
known `step_id`; the server maps that ID to an immutable invocation.

### Show Raw Child Output

The facets dry-run can emit thousands of lines. Returning stdout would make the UI
unusable and could expose machine details. The runner parses JSON, retains only
allowlisted metrics and bounded Chinese errors, and never returns raw event arrays,
environment values or absolute source paths.

## Fixed Runner Contract

The shared module `scripts/memory_atlas_owner_daily.py` is the single source of truth
for both CLI and loopback execution. It defines:

- API version `memory_atlas_owner_daily_api.v1_2_r5`;
- result schema `memory_atlas_owner_daily_result.v1_2_r5`;
- fixed profile `owner-daily`;
- the eight historical step IDs and exact dry-run argv;
- a per-step timeout and bounded captured output;
- an injectable process runner for deterministic tests.

The runner executes steps sequentially and continues after a child failure so that the
owner receives one complete maintenance picture. `run` executes all eight steps.
`retry` executes exactly one fixed known step and returns a one-step result for the UI
to merge into the existing view. Unknown step IDs and all extra request fields fail
closed before process creation.

The top-level result includes:

```text
schema_version, action, status, profile, dry_run, conclusion_zh,
completed_count, failed_count, retryable_step_ids, commands, steps, safety
```

`commands` preserves the S14 P1 plan contract. Each `steps` item includes only:

```text
step_id, order, label_zh, status, conclusion_zh, failure_zh,
retryable, duration_ms, invocation, metrics
```

The only successful aggregate status is `PASS`; one or more failed steps produce
`PARTIAL_FAILURE`. A child exit code of zero is insufficient: stdout must contain one
JSON object with an accepted success status and explicit no-write fields appropriate
to that command. Malformed, oversized, timed-out or semantically unsafe output fails
that step.

The aggregate safety object is always explicit:

```json
{
  "writes_files": false,
  "remote_push": false,
  "raw_mutation": false,
  "sends_to_chatgpt": false,
  "proposal_apply_execution": false,
  "canonical_repo_mutation": false
}
```

## CLI Compatibility

`atlasctl.py` continues to expose `owner_daily_profile_contract()` and the historical
S14 fields: task ID, acceptance ID, contract version, phase status, commands and phase
boundary. `run --profile owner-daily --dry-run` now executes the shared runner and
returns those fields plus bounded results. An optional `--step` accepts only the fixed
eight choices and performs the same single-step retry contract for an operator.

Calling the profile without `--dry-run` remains fail-closed. The profile does not run
the R8 final audit, mutate source/runtime/raw data, push Git, send to ChatGPT, apply a
proposal, open a browser or install/deploy anything.

The historical S14 validator is upgraded to assert real eight-step results and safety,
not only source fragments or command plans. Individual child dry-run checks remain as
regression coverage.

## Runtime API

R5 adds one local-only endpoint beside, not inside, the R3 command registry:

```text
POST /__memory_atlas_owner_daily
```

The only accepted JSON bodies are:

```json
{"action":"run"}
```

```json
{"action":"retry","step_id":"audit"}
```

The endpoint reuses the existing loopback Host, same-origin, `Sec-Fetch-Site`, JSON,
body-size and no-CORS controls. It shares the command/proposal operation lock so Owner
Daily cannot overlap with R3 execution or R4 apply/rollback. A busy request returns
HTTP 409. Transport errors expose bounded Chinese text without traceback, stdout,
tokens, absolute paths or environment data.

The runtime state advertises the exact Owner Daily API version. An optional append-only
audit file under Application Support may record timestamp, action, requested fixed
step, aggregate status and counts only. It cannot contain child output or source paths.

## Product Interaction

The Home maintenance band is visually separate from the six-command palette and uses
`data-r5-owner-daily-entry`. It shows the profile's no-write boundary and one clear
action. In local runtime mode the action opens a modal workspace and starts only after
the owner selects `开始 no-write 检查`.

The workspace presents information in this order:

1. human Chinese conclusion and pass/failure counts;
2. eight ordered step results with clear pass/failure labels;
3. an actionable Chinese reason and retry button for each failed step;
4. collapsed machine details containing fixed invocation and duration only.

A retry posts only the failed fixed `step_id`. The UI merges that response into the
existing eight-step result and recalculates the aggregate summary. A successful retry
must visibly change `7/1 PARTIAL_FAILURE` to `8/0 PASS`; it must not silently rerun the
other seven steps.

Hosted static mode never POSTs to the Owner Daily endpoint, never opens a fake result
workspace and displays the exact local handoff `http://127.0.0.1:4177`.

The band and workspace must fit without overlap, clipping or horizontal overflow at
`1470x661`, `1440x900` and `390x844`. Modal content may scroll vertically; controls
and text must remain reachable by keyboard.

## Test Strategy

Python tests are written first and prove:

- the fixed ordered registry and immutable dry-run argv;
- all eight steps execute sequentially and produce a bounded PASS result;
- one failed step does not prevent later steps and yields PARTIAL_FAILURE;
- retry accepts only one known step and invokes only that fixed child;
- malformed, oversized, timed-out and semantically write-capable output fails closed;
- no request can inject argv, path, environment or URL;
- R3, R4 and R5 share one operation lock;
- runtime exact-body, same-origin and bounded-error controls remain enforced.

The Playwright validator builds the current frontend and runs a temporary installer-
shaped source/runtime fixture. A fixed test `atlasctl.py` makes `audit` fail once and
pass on retry using only a marker under temporary Application Support. It proves:

- the rendered local entry and explicit start action;
- first result `7 PASS / 1 failed` with a Chinese actionable reason;
- retry POST contains only `action` and fixed `step_id`;
- only `audit` reruns and the merged result becomes `8 PASS / 0 failed`;
- source/runtime tree hashes remain byte-for-byte unchanged;
- static hosting sends zero Owner Daily POSTs and shows the local handoff;
- all three required viewports have no overlap or horizontal overflow.

Real acceptance separately executes the canonical eight dry-run steps through the
shared CLI with before/after Git and source evidence. Lint, build, R3 command E2E, R4
proposal E2E, Home multiviewport, Stage 7 visual, launcher/runtime tests and privacy
guard remain mandatory regressions.

## Requirement Impact

R5 may promote only `S14-AC04` from PARTIAL to VERIFIED because the owner-facing
maintenance control becomes rendered and executable. `S14-AC01` remains VERIFIED with
stronger runtime evidence. `S14-AC02` and `S14-AC05` remain FAILED for R8; R5 does not
rewrite historical stage truth.

Expected aggregate after R5:

```text
VERIFIED 41 / PARTIAL 10 / FAILED 5 / NOT_VERIFIED 2
```

Release status remains `FAIL_REMEDIATION_REQUIRED`.

## Rollback And Stop

Revert only the local R5 commits while retaining R0-R4. This removes the shared runner,
endpoint, maintenance workspace, tests and R5 evidence without touching source/raw
data, installed apps, Cloudflare or GitHub main.

Stop after the local R5 closeout commit and cache cleanup. Do not start R6, reconcile
Git, push, reinstall or deploy in this run.
