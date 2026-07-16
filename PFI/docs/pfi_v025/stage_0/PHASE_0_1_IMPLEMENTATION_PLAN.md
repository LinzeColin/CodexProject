# PFI v0.2.5 Stage 0 Phase 0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a reproducible, privacy-safe current-fact baseline for `S0-P1-T1..T4` and evaluate `ACC-PFI-V025-S0-P01-BASELINE` without changing business code, real data, App bundles, or later-Phase state.

**Architecture:** Run bounded read-only probes against Git, current files, installed App metadata, processes, Git-tree data, and immutable SQLite. Normalize the outputs into three primary inventories plus a command log, then reconcile them through one schema-valid evidence file, one exact changed-file ledger, and one risk/rollback record.

**Tech Stack:** zsh on macOS, Git, Node.js, Python 3.9 system runtime, project Python 3.12 virtualenv, `pytest`, `jsonschema`, `jq`, `sqlite3`, `plutil`, `codesign`, `lsof`, `curl`, and Markdown/JSON evidence.

## Global Constraints

- Execute only `PFI v0.2.5 Stage 0 / Phase 0.1`; do not enter Phase 0.2, Phase 0.3, whole-stage review, or Stage 1.
- Phase acceptance is `ACC-PFI-V025-S0-P01-BASELINE`; Roadmap tasks remain `S0-P1-T1`, `S0-P1-T2`, `S0-P1-T3`, and `S0-P1-T4`.
- Create exactly seven Phase artifacts under `PFI/reports/pfi_v025/stage_0/phase_0_1/`.
- Do not modify application code, tests, schemas, canonical governance, UI, routes, formulas, raw data, SQLite, App bundles, launchers, services, or installed entries.
- Do not start or stop services, run installers or launchers, run full tests, open a browser, create screenshots/traces, migrate data, fetch private data, or install dependencies.
- Financial evidence may contain only hashes, counts, date ranges, schema/table counts, status enums, and redacted identifiers; never emit rows, descriptions, counterparties, accounts, credentials, holdings, or amounts.
- Use `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-B`, and `-p no:cacheprovider` for Python/pytest probes.
- Local commits are allowed. Do not push to GitHub and do not reinstall App entries until Stage 0-12 and overall acceptance complete.
- No per-Stage GitHub upload gate is created for v0.2.5.
- v0.2.4 is carried forward as `evidence_commit_uploaded_remote_advanced`; do not create a second v0.2.4 closeout commit or reuse per-Stage upload gates.
- A failed command remains a real failure. Missing real input is `blocked/not_run`, never a fixture-backed pass.
- Use `apply_patch` for every file creation or edit.

---

## File Map

**Pre-implementation references — read only:**

- `PFI/docs/pfi_v025/stage_0/PHASE_0_1_DESIGN.md`: approved scope, acceptance, privacy, carry-forward, and rollback contract.
- `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md`: authoritative Stage/Phase/Task requirements.
- `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip`: evidence schema and supporting contracts, read with `unzip -p`/Python `zipfile` only.

**Create — Phase artifacts:**

- `PFI/reports/pfi_v025/stage_0/phase_0_1/git_state.txt`: reproducible Git and v0.2.4 ancestry snapshot.
- `PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json`: formal UI, launch paths, App metadata, release identities, active ports, and provenance.
- `PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json`: bounded repository/data-root/SQLite/read-model inventory.
- `PFI/reports/pfi_v025/stage_0/phase_0_1/terminal.log`: exact command, exit code, and concise redacted output records.
- `PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json`: phase-level acceptance and evidence reconciliation.
- `PFI/reports/pfi_v025/stage_0/phase_0_1/changed_files.txt`: exact seven-file whitelist.
- `PFI/reports/pfi_v025/stage_0/phase_0_1/risk_and_rollback.md`: failures, unresolved facts, stop conditions, and rollback.

**No source/test file is created.** Phase 0.1 validates evidence behavior through deterministic command checks and the Task Pack JSON schema rather than adding a generator outside the allowed-file boundary.

Stage-level `baseline.json`, `current_state_matrix.md`,
`data_root_inventory.json`, and `history_deprecation.md` remain Phase 0.2/0.3
or whole-stage assembly work; Phase 0.1 must not pre-create them. Phase 0.1
does not launch a browser or App, so it creates no screenshot or trace.
`entry_inventory.json` carries App manifest/hash/codesign evidence, while
`repository_inventory.json` carries database before/after metadata and
immutable integrity evidence.

---

### Task 1: Freeze the clean Git and source-input snapshot

**Files:**

- Create: `PFI/reports/pfi_v025/stage_0/phase_0_1/git_state.txt`
- Create/append: `PFI/reports/pfi_v025/stage_0/phase_0_1/terminal.log`

**Interfaces:**

- Consumes: current `codex/pfi` branch; `origin/main`; live `refs/heads/main`; v0.2.4 commits `17b9f59794740f927c5f531ba1aa334621a832e5` and `5e48e739774575f4d198d6268271e557de434897`; the two external v0.2.5 source files.
- Produces: exact base commit, branch/upstream/remote facts, source hashes, v0.2.4 ancestry classification, and command-result records used by `evidence.json`.

- [ ] **Step 1: Prove the worktree is clean before Phase artifacts exist**

Run:

```bash
pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse --abbrev-ref '@{upstream}'
git remote get-url origin
git rev-parse HEAD
git rev-parse origin/main
git ls-remote origin refs/heads/main
git rev-list --left-right --count HEAD...origin/main
GIT_OPTIONAL_LOCKS=0 git status --porcelain=v1 --untracked-files=all
git sparse-checkout list
git log -5 --oneline --decorate
```

Expected:

- `pwd` and Git root are `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi`.
- branch is `codex/pfi`; upstream is `origin/main`; remote is `git@github.com:LinzeColin/CodexProject.git`.
- live remote main equals local `origin/main`; local HEAD may be ahead only by committed v0.2.5 design/plan work.
- porcelain status is empty. If live remote differs from `origin/main` or status is non-empty, stop without fetching/rebasing or writing Phase artifacts.

- [ ] **Step 2: Prove the v0.2.4 carry-forward classification**

Run:

```bash
git rev-parse 5e48e739774575f4d198d6268271e557de434897^1
git merge-base --is-ancestor 5e48e739774575f4d198d6268271e557de434897 origin/main
git diff --quiet 5e48e739774575f4d198d6268271e557de434897..origin/main -- PFI
git log --oneline --ancestry-path 5e48e739774575f4d198d6268271e557de434897..origin/main
```

Expected:

- evidence parent is exactly `17b9f59794740f927c5f531ba1aa334621a832e5`;
- evidence commit is an ancestor of `origin/main`;
- PFI subtree diff exits `0`;
- later commits are retained as history, not reclassified as PFI delivery work.

- [ ] **Step 3: Hash and verify the approved source inputs**

Run:

```bash
openssl dgst -sha256 \
  /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md \
  /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip
unzip -t /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip
```

Expected source hashes:

- Roadmap: `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b`.
- Task Pack: `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2`.
- ZIP integrity reports no compressed-data errors.

- [ ] **Step 4: Create `git_state.txt` using the literal outputs from Steps 1-3**

Create the allowed directory, then use `apply_patch` for the file:

```bash
mkdir -p PFI/reports/pfi_v025/stage_0/phase_0_1
```

The file must contain these labelled sections in this order:

```text
PFI v0.2.5 Stage 0 Phase 0.1 Git State
captured_at_utc: the exact UTC timestamp from date -u +%Y-%m-%dT%H:%M:%SZ
cwd:
git_root:
branch:
upstream:
remote_url:
base_head:
origin_main:
live_remote_main:
ahead_behind:
worktree_porcelain: CLEAN
sparse_checkout:
recent_commits:
v024_product_commit:
v024_evidence_commit:
v024_evidence_parent:
v024_evidence_in_remote_history: true
v024_pfi_subtree_changed_after_evidence: false
v024_current_live_verifier: not_replayable_after_unrelated_main_advance
roadmap_sha256:
taskpack_sha256:
```

Every blank value label above must be filled from the exact command output. Do not copy secrets or private financial content.

- [ ] **Step 5: Create the initial `terminal.log`**

Use `apply_patch`. For every command from Steps 1-3, add one block:

```text
COMMAND: exact command
EXIT_CODE: exact integer
SUMMARY: concise redacted factual output
```

Do not claim the Phase passed. End the initial log with `PHASE_STATUS: evidence_assembly_in_progress`.

---

### Task 2: Inventory formal UI, launch paths, App bundles, and runtime provenance

**Files:**

- Create: `PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json`
- Modify: `PFI/reports/pfi_v025/stage_0/phase_0_1/terminal.log`

**Interfaces:**

- Consumes: `PFI/VERSION`, `PFI/web/index.html`, `PFI/web/app/shell.js`, `PFI/StartPFI.command`, `PFI/scripts/startPFI.sh`, `PFI/macos/PFI.app`, `/Applications/PFI.app`, `/Users/linzezhang/Downloads/PFI.app`, `/Users/linzezhang/Desktop/PFI.app`, and existing listener/process metadata.
- Produces: `PFIV025Stage0Phase01EntryInventoryV1`, consumed by Task 4 acceptance reconciliation.

- [ ] **Step 1: Record release-identity sources without launching anything**

Run:

```bash
sed -n '1,10p' PFI/VERSION
rg -n -i 'pfi-version|pfi-app-version|pfi-target-version|pfi-build-id|repair-label|apiBaseUrl' \
  PFI/web/index.html PFI/web/app/shell.js
rg -n 'PFI_ACTIVE_BUILD_ID|PFI_VERSION_QUERY|PORT=|streamlit_app.py' \
  PFI/StartPFI.command PFI/scripts/startPFI.sh
openssl dgst -sha256 PFI/web/index.html PFI/web/app/shell.js \
  PFI/web/app/routes.js PFI/web/app/home.js
```

Expected: each source is reported independently. Mixed versions remain conflicts; do not normalize them in this phase.

- [ ] **Step 2: Audit each App path using metadata-only commands**

Run this exact metadata-only loop:

```bash
for app in \
  "/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI/macos/PFI.app" \
  "/Applications/PFI.app" \
  "/Users/linzezhang/Downloads/PFI.app" \
  "/Users/linzezhang/Desktop/PFI.app"; do
  printf 'APP=%s\n' "$app"
  if [ -L "$app" ]; then
    readlink "$app"
    realpath "$app"
  fi
  if [ ! -e "$app" ]; then
    echo 'exists=false'
    continue
  fi
  stat -f '%N|%HT|%Sp|%z|%Sm' -t '%Y-%m-%dT%H:%M:%S%z' "$app"
  /usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$app/Contents/Info.plist"
  /usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$app/Contents/Info.plist"
  /usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$app/Contents/Info.plist"
  /usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$app/Contents/Info.plist"
  openssl dgst -sha256 "$app/Contents/Info.plist"
  openssl dgst -sha256 "$app/Contents/MacOS/PFI"
  codesign --verify --deep --strict "$app"
done
```

Do not execute the App or launcher.

- [ ] **Step 3: Inventory existing PFI services and prove their cwd**

Run:

```bash
lsof -nP -iTCP:8501-8510 -sTCP:LISTEN
ps ax -o pid=,ppid=,command= | rg -i '[p]fi|[s]treamlit.*850[0-9]'
```

For each returned process, run:

```bash
for pid in $(lsof -nP -iTCP:8501-8510 -sTCP:LISTEN -t 2>/dev/null | sort -u); do
  printf 'PID=%s\n' "$pid"
  ps -p "$pid" -o pid=,ppid=,command=
  lsof -a -p "$pid" -d cwd -Fn
  port=$(lsof -nP -a -p "$pid" -iTCP -sTCP:LISTEN -Fn 2>/dev/null \
    | sed -nE 's/^n.*:([0-9]+)$/\1/p' | head -1)
  if [ -n "$port" ]; then
    curl -sS --max-time 2 -o /dev/null -w '%{http_code}\n' \
      "http://127.0.0.1:$port/_stcore/health"
  fi
done
```

Record zero services as a valid fact. Stop if any PFI service cwd resolves outside the canonical `PFI/` directory. Do not start, stop, or refresh a service.

- [ ] **Step 4: Create `entry_inventory.json`**

Use `apply_patch`. The JSON contract is:

| Field | Exact value source and type |
|---|---|
| `schema` | string constant `PFIV025Stage0Phase01EntryInventoryV1` |
| `version` | string constant `v0.2.5` |
| `stage` | integer `0` |
| `phase` | string `0.1` |
| `captured_at_utc` | Task 1 UTC timestamp string |
| `canonical_pfi_root` | string `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI` |
| `formal_ui` | object populated from `PFI/web/index.html` and shell hashes |
| `release_identity_sources` | array populated from VERSION/web/plist/startup sources |
| `startup_entries` | array populated from the two startup scripts without executing them |
| `app_bundles` | array populated from the exact metadata-only loop |
| `runtime_services` | array populated from listener/PID/cwd/health probes; empty is valid |
| `conflicts` | array of concrete mismatches or unavailable facts; empty only if none exist |
| `privacy` | object `{contains_private_values: false, financial_rows_emitted: 0, credentials_emitted: 0}` |

Each object includes the exact source path, existence/status, hashes, versions,
codesign result, or process provenance gathered above. Use JSON `null` for an
unavailable fact and give its concrete reason in `conflicts`; never invent a
default.

- [ ] **Step 5: Validate and log the entry inventory**

Run:

```bash
jq -e '.schema == "PFIV025Stage0Phase01EntryInventoryV1"
  and .privacy.contains_private_values == false
  and (.app_bundles | type == "array")
  and (.runtime_services | type == "array")' \
  PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json
```

Append the release, App, service, and jq commands with real exit codes and redacted summaries to `terminal.log` using `apply_patch`.

---

### Task 3: Inventory repository, data roots, SQLite, and current read-model state

**Files:**

- Create: `PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json`
- Modify: `PFI/reports/pfi_v025/stage_0/phase_0_1/terminal.log`

**Interfaces:**

- Consumes: bounded PFI directories; sparse Git objects under `MetaDatabase/PFI`; `$PFI_DATA_HOME`; `PFI/MetaDatabase`; `/Users/linzezhang/.pfi`; existing v0.2.3/v0.2.4 read-only builders.
- Produces: `PFIV025Stage0Phase01RepositoryInventoryV1`, including App/data/SQLite before-and-after invariants used by Task 4.

- [ ] **Step 1: Count only bounded repository surfaces**

Run:

```bash
for d in PFI/src PFI/tests PFI/web PFI/config PFI/docs PFI/reports PFI/macos PFI/scripts; do
  files=$(rg --files "$d" 2>/dev/null | wc -l | tr -d ' ')
  bytes=$(du -sk "$d" 2>/dev/null | awk '{print $1 * 1024}')
  printf '%s|files=%s|bytes=%s\n' "$d" "$files" "$bytes"
done
```

Do not scan unrelated project roots, dependencies, `.venv`, caches, artifacts, backups, or private content.

- [ ] **Step 2: Audit candidate data roots without materializing sparse data**

Run:

```bash
printf 'PFI_DATA_HOME=%s\n' "${PFI_DATA_HOME:-UNSET}"
for root in MetaDatabase/PFI PFI/MetaDatabase "$HOME/.pfi"; do
  if [ -e "$root" ]; then
    stat -f '%N|%HT|%Sp|%z|%Sm' -t '%Y-%m-%dT%H:%M:%S%z' "$root"
    find "$root" -type f 2>/dev/null | wc -l
  else
    printf '%s|exists=false\n' "$root"
  fi
done
git rev-parse HEAD:MetaDatabase/PFI
git ls-tree -r -l HEAD MetaDatabase/PFI \
  | awk '{files++; bytes += $4; path=$5; sub(/^.*\./, "", path); ext[tolower(path)]++}
    END {printf "files=%d|bytes=%d|csv=%d|json=%d|sqlite=%d\n",
      files, bytes, ext["csv"], ext["json"], ext["db"]+ext["sqlite"]+ext["sqlite3"]}'
```

The final inventory records aggregate counts, total bytes, extension counts, tree hash, permissions, and existence. Do not emit raw filenames from private local roots.

- [ ] **Step 3: Build the canonical redacted read-model audit**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B - <<'PY'
import json
from pfi_os.application.read_model_status import build_v024_data_source_scan, build_v024_read_model_status

scan = build_v024_data_source_scan(project_root="PFI")
status = build_v024_read_model_status(project_root="PFI")
safe = {
    "source": {
        "status": scan.get("status"),
        "storage_mode": scan.get("storage_mode"),
        "raw_file_count": scan.get("raw_file_count"),
        "record_count": scan.get("record_count"),
        "date_range": scan.get("date_range"),
        "as_of": scan.get("as_of"),
        "evidence_hash": scan.get("evidence_hash"),
    },
    "read_model_hash": status.get("read_model_hash"),
    "blocked_metric_ids": status.get("blocked_metric_ids"),
    "metric_states": {
        item.get("metric_id"): item.get("status")
        for item in status.get("core_metric_states", [])
    },
}
print(json.dumps(safe, ensure_ascii=False, sort_keys=True, indent=2))
PY
```

Expected: output contains only status/count/range/hash/metric-ID evidence. If any financial amount or raw row appears, stop and do not copy the output.

- [ ] **Step 4: Audit local SQLite in immutable read-only mode**

Find the configured local database without printing private candidate filenames.
Before opening it, record file count, byte size, mtime, and SHA-256. Run:

```bash
db_count=$(find "$HOME/.pfi" -type f \
  \( -iname '*.db' -o -iname '*.sqlite' -o -iname '*.sqlite3' \) \
  2>/dev/null | wc -l | tr -d ' ')
db_path=$(find "$HOME/.pfi" -type f \
  \( -iname '*.db' -o -iname '*.sqlite' -o -iname '*.sqlite3' \) \
  -print -quit 2>/dev/null)
if [ "$db_count" -eq 0 ]; then
  echo 'local_pfi_sqlite=not_found'
elif [ "$db_count" -ne 1 ]; then
  echo "local_pfi_sqlite=ambiguous|count=$db_count"
  exit 1
else
  stat -f 'bytes=%z|mtime_epoch=%m|mode=%Sp' "$db_path"
  openssl dgst -sha256 "$db_path"
  sqlite3 "file:$db_path?mode=ro&immutable=1" \
    "PRAGMA query_only=ON; PRAGMA quick_check; SELECT 'table_count=' || count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
fi
```

Store the path in evidence as `$PFI_DATA_HOME`/`~/.pfi` plus a redacted
identifier. Recompute file count, size, mtime, and SHA-256 afterward. When a
database exists, all before/after values must match and `quick_check` must
return `ok`. Multiple candidates are an ambiguity stop condition. When none
exists, record `not_found` and do not substitute a test database.

- [ ] **Step 5: Create `repository_inventory.json`**

Use `apply_patch`. The JSON contract is:

| Field | Exact value source and type |
|---|---|
| `schema` | string constant `PFIV025Stage0Phase01RepositoryInventoryV1` |
| `version`, `stage`, `phase` | `v0.2.5`, integer `0`, string `0.1` |
| `captured_at_utc` | Task 1 UTC timestamp string |
| `bounded_surfaces` | array of Task 3 Step 1 path/count/byte objects |
| `candidate_data_roots` | array of existence/permission/count objects without private filenames |
| `git_tree_data` | object containing tree hash and aggregate file/byte/extension counts |
| `read_model` | the exact safe filtered output from Task 3 Step 3 |
| `sqlite` | object containing mode, quick-check/table count, redacted ID, before/after metadata, and unchanged boolean; use JSON `null` only when no DB exists |
| `excluded_surfaces` | array naming every intentionally excluded dependency/cache/private surface and reason |
| `privacy` | object `{contains_private_values: false, financial_rows_emitted: 0, credentials_emitted: 0}` |

Do not include raw filenames, rows, or amounts.

- [ ] **Step 6: Validate and log the repository inventory**

Run:

```bash
jq -e '.schema == "PFIV025Stage0Phase01RepositoryInventoryV1"
  and .privacy.contains_private_values == false
  and (.bounded_surfaces | type == "array")
  and (.candidate_data_roots | type == "array")
  and (.sqlite.unchanged == true or .sqlite.unchanged == null)' \
  PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json
```

Append every Task 3 command and result to `terminal.log` using `apply_patch`.

---

### Task 4: Run Phase validation and assemble the acceptance evidence

**Files:**

- Modify: `PFI/reports/pfi_v025/stage_0/phase_0_1/terminal.log`
- Create: `PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json`
- Create: `PFI/reports/pfi_v025/stage_0/phase_0_1/changed_files.txt`
- Create: `PFI/reports/pfi_v025/stage_0/phase_0_1/risk_and_rollback.md`

**Interfaces:**

- Consumes: Task 1-3 artifacts and command results; Task Pack `evidence_pack.schema.json` streamed from ZIP.
- Produces: candidate/fail/blocked/not-run Phase decision and the exact local commit input set.

- [ ] **Step 1: Record before-state invariants for validation**

Run before pytest collection:

```bash
find PFI -path PFI/.venv -prune -o -type d \( -name __pycache__ -o -name .pytest_cache \) -print | wc -l
git status --porcelain=v1 --untracked-files=all -- PFI
for app in \
  "/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI/macos/PFI.app" \
  "/Applications/PFI.app" \
  "/Users/linzezhang/Downloads/PFI.app" \
  "/Users/linzezhang/Desktop/PFI.app"; do
  if [ -e "$app" ]; then
    openssl dgst -sha256 "$app/Contents/Info.plist" "$app/Contents/MacOS/PFI"
    if [ -f "$app/Contents/Resources/PFI_PROJECT_ROOT" ]; then
      openssl dgst -sha256 "$app/Contents/Resources/PFI_PROJECT_ROOT"
    fi
  elif [ -L "$app" ]; then
    printf 'broken_symlink=%s\n' "$app"
  else
    printf 'missing=%s\n' "$app"
  fi
done
```

Also reuse the SQLite before-state from Task 3. The only expected PFI changes are the seven Phase artifact paths.

- [ ] **Step 2: Run the required runtime, syntax, SQLite, and collection commands**

Run:

```bash
python3 --version
node --version
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PFI/.venv/bin/python -B -m pytest PFI/tests -q --collect-only \
  -p no:cacheprovider
```

Expected:

- version commands exit `0`;
- Node syntax exits `0`;
- pytest collection exits `0` and reports the exact collected count;
- no test is executed, and the collected count is not described as passing tests.

- [ ] **Step 3: Prove validation did not mutate caches, App, data, or SQLite**

Repeat the Task 4 Step 1 probes and Task 3 SQLite metadata probes. Expected:

- cache-directory count unchanged;
- App plist hashes unchanged;
- SQLite file count, size, mtime, and SHA-256 unchanged;
- no data-root metadata change attributable to the run;
- only the seven Phase artifact paths appear in PFI status.

Append all commands, real exit codes, concise outputs, and before/after comparisons to `terminal.log`. Replace its final status with the real provisional phase status.

- [ ] **Step 4: Create the exact changed-file ledger**

Use `apply_patch` so `changed_files.txt` contains exactly:

```text
PFI/reports/pfi_v025/stage_0/phase_0_1/changed_files.txt
PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json
PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json
PFI/reports/pfi_v025/stage_0/phase_0_1/git_state.txt
PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json
PFI/reports/pfi_v025/stage_0/phase_0_1/risk_and_rollback.md
PFI/reports/pfi_v025/stage_0/phase_0_1/terminal.log
```

- [ ] **Step 5: Create `risk_and_rollback.md`**

Use `apply_patch`. It must include:

- confirmed v0.2.4 remote-ancestry fact and non-replayable dynamic-verifier risk;
- every version/App/UI/data/read-model conflict observed in Tasks 1-3;
- any command that failed or was not run and why;
- explicit non-goals: Phase 0.2/0.3, Stage review/1, business code, real-data mutation, push, and App reinstall;
- rollback before commit: delete only the seven listed artifacts;
- rollback after commit: revert only the Phase 0.1 local commit;
- statement that no private values, database writes, App changes, or uploads occurred.

- [ ] **Step 6: Create `evidence.json` from real results**

Use `apply_patch`. Required constants are:

| Field | Exact value |
|---|---|
| `version` | `v0.2.5` |
| `stage` | integer `0` |
| `phase` | string `0.1` |
| `git_commit_semantics` | `audited_clean_base_commit_before_phase_artifacts` |
| `rollback` | `remove the seven artifacts before commit or revert the local Phase commit after commit` |
| `requires_user_acceptance` | boolean `true` |
| `contains_private_values` | boolean `false` |
| `acceptance_id` | `ACC-PFI-V025-S0-P01-BASELINE` |

Runtime-derived required fields are:

- `status`: choose exactly one of `candidate_pass`, `fail`, `blocked`, or
  `not_run` from actual evidence;
- `git_commit`: exact Task 1 clean base SHA;
- `allowed_files_obeyed`: the real seven-file reconciliation result;
- `commands`, `changed_files`, `explicitly_not_done`, `risks`: arrays described
  below.

Optional schema extensions used by this Phase are `evidence_files`, `tasks`,
`source_hashes`, `privacy`, and `v024_carry_forward`. Populate:

- `commands` with `{command, exit_code, summary}` for every validation command;
- `changed_files` and `evidence_files` with the seven exact paths;
- `tasks` with all four Roadmap task IDs, real status, and their artifacts;
- `source_hashes` with the exact Roadmap and Task Pack hashes;
- `privacy` with zero private-value/row/credential counts and the redaction rules;
- `v024_carry_forward` with product/evidence commits, parent/ancestry/subtree facts, and the non-replayable current verifier classification;
- `explicitly_not_done` with every later Phase/Stage, full tests, browser UAT, data mutation, GitHub push, and App reinstall;
- `risks` with every unresolved current conflict, not generic language.

Set `allowed_files_obeyed` to `false` and status to `fail` if the whitelist check fails. Candidate-pass is forbidden when any required command fails or a stop condition occurs.

- [ ] **Step 7: Validate every JSON file and the Task Pack evidence schema**

Run:

```bash
jq -e . PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json
jq -e . PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json
jq -e . PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - <<'PY'
import json
import zipfile
from pathlib import Path
from jsonschema import Draft202012Validator

archive = Path("/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip")
member = "PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"
evidence_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json")
with zipfile.ZipFile(archive) as zf:
    schema = json.loads(zf.read(member))
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
Draft202012Validator(schema).validate(evidence)
print("evidence_schema_valid=true")
PY
```

Expected: all commands exit `0`; schema output is exactly `evidence_schema_valid=true`.

- [ ] **Step 8: Reconcile privacy and the seven-file scope**

Run:

```bash
diff -u \
  <(sort PFI/reports/pfi_v025/stage_0/phase_0_1/changed_files.txt) \
  <(git status --porcelain=v1 --untracked-files=all -- PFI \
    | sed -E 's/^.. //' | sort)
if rg -n -i '(password|secret|credential|account_number|card_number|transaction_description|counterparty)[[:space:]]*[:=][[:space:]]*[^"[:space:]]' \
  PFI/reports/pfi_v025/stage_0/phase_0_1; then
  echo 'private_value_scan=fail'
  exit 1
else
  rc=$?
  if [ "$rc" -eq 1 ]; then
    echo 'private_value_scan=pass|matches=0'
  else
    exit "$rc"
  fi
fi
git diff --check -- PFI
```

Expected:

- scope diff exits `0`;
- private-value wrapper exits `0` and reports `private_value_scan=pass|matches=0`;
- `git diff --check` exits `0`.

Process substitution is transient and creates no persistent evidence artifact.

---

### Task 5: Independent review, stage, and create the single local Phase commit

**Files:**

- Review only: all seven Phase artifacts.
- Stage/commit only: the seven paths in `changed_files.txt`.

**Interfaces:**

- Consumes: complete candidate evidence from Tasks 1-4.
- Produces: one local Phase commit and a clean worktree; no remote mutation.

- [ ] **Step 1: Run an independent evidence review before staging**

The reviewer must verify:

- all `S0-P1-T1..T4` outputs are present and agree;
- every claim maps to a command result or authoritative source;
- collection is not called test pass;
- App/DB/data before-and-after evidence is unchanged;
- v0.2.4 is classified exactly as the approved carry-forward decision;
- no private financial values are present;
- no Phase 0.2/0.3, business code, data, upload, or App work is implied;
- status is not `candidate_pass` if any mandatory check failed.

Any finding is fixed only inside the seven Phase artifacts, then Tasks 4.7-4.8 are rerun. Do not widen the file set.

- [ ] **Step 2: Stage exactly the seven artifacts and validate the staged diff**

Run:

```bash
git add -- \
  PFI/reports/pfi_v025/stage_0/phase_0_1/changed_files.txt \
  PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json \
  PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json \
  PFI/reports/pfi_v025/stage_0/phase_0_1/git_state.txt \
  PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json \
  PFI/reports/pfi_v025/stage_0/phase_0_1/risk_and_rollback.md \
  PFI/reports/pfi_v025/stage_0/phase_0_1/terminal.log
git diff --cached --check
git diff --cached --name-only | sort
```

Expected: staged names exactly equal sorted `changed_files.txt`; no design, plan, governance, source, test, App, or data path is staged.

- [ ] **Step 3: Create one local Phase commit**

Run:

```bash
git commit -m "docs(PFI): record v0.2.5 stage 0 phase 0.1 baseline"
```

Expected: one commit containing exactly seven new files.

- [ ] **Step 4: Verify the local stop state without pushing**

Run:

```bash
git status --short --branch
git show --stat --oneline --summary HEAD
git rev-list --left-right --count HEAD...origin/main
git ls-remote origin refs/heads/main
```

Expected:

- worktree clean;
- current branch is ahead of `origin/main` by local design, plan, and Phase commits only;
- live remote main is unchanged by this run;
- no push and no App reinstall occurred.

Stop with: `Stage 0 / Phase 0.1 candidate result; waiting for user acceptance or explicit Phase 0.2 instruction.`

---

## Completion Evidence Map

| Requirement | Authoritative evidence |
|---|---|
| `S0-P1-T1` reproducible Git state | `git_state.txt`, matching command blocks in `terminal.log` |
| `S0-P1-T2` entry/App/runtime inventory | `entry_inventory.json`, metadata/hash/codesign/process command blocks |
| `S0-P1-T3` bounded repository/data/DB inventory | `repository_inventory.json`, Git-tree/read-model/immutable-SQLite command blocks |
| `S0-P1-T4` syntax/runtime/collection | `terminal.log` real exit codes and before/after invariants |
| Task Pack evidence schema | streamed ZIP schema validation exit `0` |
| Privacy and real-data boundary | both JSON privacy blocks, scan result, `risk_and_rollback.md` |
| Seven-file allowed boundary | `changed_files.txt`, status reconciliation, staged-name reconciliation |
| No auto-advance/upload/reinstall | `evidence.json.explicitly_not_done`, Git/App post-state |
| Phase acceptance | `evidence.json.acceptance_id == ACC-PFI-V025-S0-P01-BASELINE` and actual status |

Phase 0.1 completion does not complete Stage 0. Phase 0.2, Phase 0.3, whole-stage review, review-finding remediation, later Stages, real-data write flows, final GitHub upload, and final App reinstall remain required by the full v0.2.5 goal.
