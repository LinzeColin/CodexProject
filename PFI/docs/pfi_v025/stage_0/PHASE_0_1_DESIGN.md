# PFI v0.2.5 Stage 0 Phase 0.1 Design

- Status: `approved_for_implementation_planning`
- Approval reference: `active goal continuation on 2026-07-11; no design changes requested`
- Date: `2026-07-11 Australia/Sydney`
- Phase: `Stage 0 / Phase 0.1 - 当前事实重基线`
- Roadmap tasks: `S0-P1-T1`, `S0-P1-T2`, `S0-P1-T3`, `S0-P1-T4`
- Phase acceptance: `ACC-PFI-V025-S0-P01-BASELINE`
- Roadmap SHA-256: `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b`
- Task Pack ZIP SHA-256: `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2`

## 1. Goal

Create a reproducible, privacy-safe snapshot of the current PFI repository,
Git state, active entry surfaces, installed App bundles, release identities,
runtime ports, databases, and candidate data roots. The phase records facts and
conflicts; it does not repair them or claim that Stage 0 is complete.

The latest user delivery policy is binding for v0.2.5:

- At most one Phase is executed per run.
- Every Stage is reviewed and its findings are resolved before the next Stage.
- No per-Stage GitHub upload gate is created.
- Local Phase commits are allowed; GitHub main upload and final App reinstall
  occur once, after Stage 0-12 and the overall acceptance are complete.
- Real raw data is introduced only in its Roadmap Phase, under read-only or
  isolated-copy controls until a write path is explicitly authorized.

## 2. v0.2.4 Carry-forward Decision

The v0.2.4 evidence commit
`5e48e739774575f4d198d6268271e557de434897` is present in live GitHub main
history and is the direct child of product commit
`17b9f59794740f927c5f531ba1aa334621a832e5`. Two later commits advanced main
without changing the `PFI/` subtree.

The v0.2.4 live verifier is time-dependent: it requires the current HEAD to be
both remote main and the direct child of the product commit. That predicate
cannot be replayed after unrelated main advancement. Phase 0.1 therefore:

- records v0.2.4 as `evidence_commit_uploaded_remote_advanced`;
- records the present live-verifier result as `not_replayable_after_unrelated_main_advance`;
- does not create a second v0.2.4 closeout commit;
- does not reuse v0.2.4 per-Stage upload artifacts as a v0.2.5 pattern; and
- treats the tracked `pending_live_verifier` wording as a historical truth
  conflict for Phase 0.2/0.3, not as permission to rewrite it in Phase 0.1.

## 3. Scope

### In scope

- `S0-P1-T1`: Git root, branch, upstream, remote, HEAD, local tracking ref,
  live remote main, worktree, sparse-checkout, recent commits, and v0.2.4
  evidence ancestry.
- `S0-P1-T2`: formal UI source, startup scripts, App bundles, binding paths,
  ports, process cwd, release identity sources, bundle hashes, plist identity,
  and codesign status using metadata-only checks.
- `S0-P1-T3`: bounded repository inventory; test/report/config counts;
  candidate data roots; Git-tree data; local SQLite metadata; record counts,
  date coverage, hashes, permissions, and read-model status without private
  values.
- `S0-P1-T4`: syntax check, runtime versions, SQLite version and read-only
  integrity check, and pytest collection only.

### Explicitly out of scope

- Phase 0.2 or 0.3 artifacts, Active Requirements, history deprecation, or gap
  prioritization.
- Business UI, routes, financial formulas, application code, tests, schemas,
  App installation, services, database migrations, or raw-data mutation.
- Full test execution, browser UAT, screenshots, traces, GitHub push, pull
  request, release, or production-side effects.
- Canonical governance rewrites. Any v0.2.5 registration gap is reported for
  Phase 0.2 instead of bypassing the Phase 0.1 allowed-file boundary.

## 4. Artifacts

Phase 0.1 writes exactly these seven files under
`PFI/reports/pfi_v025/stage_0/phase_0_1/`:

1. `git_state.txt`
2. `entry_inventory.json`
3. `repository_inventory.json`
4. `terminal.log`
5. `evidence.json`
6. `changed_files.txt`
7. `risk_and_rollback.md`

The design document itself is a pre-implementation artifact and is not counted
as a Phase 0.1 completion artifact.

### Artifact responsibilities

- `git_state.txt` is the reproducible Git snapshot and includes exact commands,
  timestamps, refs, ancestry, and worktree state.
- `entry_inventory.json` contains UI/App/launcher/runtime identity and
  metadata-only App evidence. It does not run installers or launchers.
- `repository_inventory.json` contains bounded code/test/report/data-root and
  SQLite evidence. Database inspection uses read-only immutable mode and
  records before/after file count, size, mtime, and hash.
- `terminal.log` records every validation command, exit code, and concise
  output. Private values and financial rows are forbidden.
- `evidence.json` follows the Task Pack `PFI Phase Evidence Pack` schema and
  adds `acceptance_id`, `tasks`, `source_hashes`, `privacy`, and
  `v024_carry_forward` fields, which the schema permits.
- The schema-required `git_commit` is the audited clean base commit before the
  seven Phase artifacts are written. `git_commit_semantics` must state this
  explicitly; the later local Phase commit hash is reported in the run handoff
  and is not written through a self-referential second commit.
- `changed_files.txt` must list exactly the seven Phase artifacts.
- `risk_and_rollback.md` states unresolved facts, stop conditions, and removal
  or local-commit-revert rollback.

## 5. Data Flow and Privacy

```text
authoritative files and process metadata
  -> read-only bounded commands
  -> redact paths or values where required
  -> normalized inventories
  -> evidence.json and terminal.log reconciliation
```

Rules:

- No transaction descriptions, counterparties, account numbers, credentials,
  holdings, financial amounts, or raw rows are emitted.
- Allowed financial-data evidence is limited to hashes, file/record counts,
  date ranges, schema/table counts, status enums, and redacted identifiers.
- Git-tree reads use object access without materializing sparse-excluded data.
- SQLite opens with `mode=ro&immutable=1`, `query_only=ON`, or an equivalent
  proven zero-write mode. File metadata is compared before and after.
- Existing services may be queried for health and provenance but are neither
  started nor stopped.

## 6. Validation

The implementation plan must use zero-cache variants where the Task Pack's
bare commands can write:

```text
git status --short --branch
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git ls-remote origin refs/heads/main
git log -5 --oneline
python3 --version
node --version
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PFI/.venv/bin/python -B -m pytest PFI/tests -q --collect-only \
  -p no:cacheprovider
```

Additional gates:

- all JSON parses and `evidence.json` validates against the Task Pack schema;
- command entries use `command`, `exit_code`, and `summary`;
- changed files reconcile exactly with the seven-file whitelist;
- private-value scanning reports zero findings;
- App/data/database before-and-after metadata remains unchanged;
- `git diff --check -- PFI` passes; and
- no Phase 0.2, business code, data, App, or upload path is changed.

Collection count is evidence of discovery only. It is never reported as tests
passing.

## 7. Acceptance and Stop Conditions

`ACC-PFI-V025-S0-P01-BASELINE` is candidate-pass only when:

- all four Roadmap tasks have a corresponding artifact and reproducible
  command evidence;
- branch, upstream, local tracking ref, and live remote main are confirmed;
- all current UI/App/runtime/version sources and conflicts are listed;
- all candidate data roots and databases have redacted count/range/hash and
  permission evidence;
- syntax, runtime, SQLite, and collection commands have real exit codes;
- the seven-file boundary and privacy rules are satisfied; and
- evidence explicitly states that Phase 0.2, Phase 0.3, Stage 0 review, Stage 1,
  GitHub upload, App reinstall, and real-data mutation were not done.

Stop immediately if:

- the worktree contains unexplained changes;
- branch, upstream, or live remote main cannot be confirmed;
- a running instance resolves outside the canonical worktree;
- data inspection requires moving, decrypting, uploading, or mutating private
  files;
- any command creates cache or changes App/database/data metadata; or
- completing an artifact would require writing outside the seven-file Phase
  boundary.

## 8. Error Handling and Rollback

- A failed command is recorded with its real exit code; the phase becomes
  `fail`, `blocked`, or `not_run` according to the Task Pack schema.
- Missing real input remains `blocked/not_run`; no fixture or fallback may turn
  it into pass.
- Partial artifacts are not labelled candidate-pass.
- Before a local Phase commit, rollback is deletion of the seven new files.
- After a local Phase commit, rollback is a normal revert of that local commit.
- No Phase 0.1 commit is pushed to GitHub.

## 9. Next Gate

After this design is approved, write an implementation plan for Phase 0.1 and
execute only that Phase. Stop with a candidate result and request explicit
permission before entering Phase 0.2.
