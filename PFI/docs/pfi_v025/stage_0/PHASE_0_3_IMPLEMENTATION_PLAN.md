# PFI v0.2.5 Stage 0 Phase 0.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete `S0-P3-T1`, `S0-P3-T2`, `S0-P3-T3`, and `S0-P3-T4` as an auditable Phase 0.3 candidate: normalize 38 findings, produce 13 executable P0/P1 gaps and an explicit zero-executable P2 disposition, assemble the Stage 0 Evidence Pack, prepare the acceptance request, and stop before Stage 0 whole-stage review or Stage 1.

**Architecture:** The frozen design is the specification source. Thirteen Roadmap core artifacts form a single acyclic evidence graph; twelve existing PFI governance companions register the Phase without changing canonical model/formula/parameter values. Fresh read-only probes supply current facts, a guarded selective shadow supplies PFI-only governance validation, and immutable local `.git/codex-review` artifacts bind the final commit without back-writing future facts into tracked evidence.

**Tech Stack:** macOS zsh, Git, `apply_patch`, Python 3 with bytecode/cache disabled, `jq`, `openssl`, `unzip`, Node.js syntax checks, `pytest`, `sqlite3` query-only immutable mode, `codesign`, `plutil`, `lsof`, `curl`, JSON/JSONL/YAML/CSV/Markdown, and CodexProject Lean Governance v2.

## Global Constraints

- Execute only `PFI v0.2.5 Stage 0 / Phase 0.3`. Stage 0 whole-stage review, remediation, re-review, Codex whole-stage acceptance, user Stage acceptance, and Stage 1 remain `not_started`.
- Authority is the pinned Roadmap, pinned Task Pack, frozen design commit `35ef4148723c5885bf9c2f962390bc9e562f5e50`, then fresh verified facts. Old closeout prose never overrides current evidence.
- Risk tier is `T2`: production truth, financial-data metadata, governance schema, App identity, and release evidence are in scope; product/runtime/data mutation is not.
- The implementation diff is exactly 25 paths: 13 core artifacts plus 12 governance companions. This plan and the design are separate commits and are excluded from the 25-path ledger.
- All repository edits use `apply_patch`. Formatting-only commands may normalize syntax but may not create a 26th path.
- Do not modify README, HANDOFF, `功能清单.md`, `开发记录.md`, `模型参数文件.md`, VERSION, business UI/runtime/tests, Active Requirements, `project.yaml`, `roadmap.yaml`, `DELIVERY_PLAN.md`, `ASSURANCE_STATUS.yaml`, data, database, App, launcher, service, or any other project.
- Do not install dependencies, launch/stop/restart a service or App, open browser UAT, run the full suite, materialize sparse data, use normal fetch/ref updates, rebase, merge, push, or reinstall/copy an App.
- Read private financial content only through the already approved aggregate Git-object/read-model path; output only counts, date ranges, as-of, hashes, status, and redacted IDs. Never emit filenames, rows, amounts, accounts, counterparties, credentials, or private absolute database filenames.
- Existing model/formula/assumption definitions and every parameter value/config ref/version/status/date remain unchanged. Governance registry changes are evidence/provenance/phase-contract metadata only.
- `development_events.jsonl` is append-only and gains exactly one Phase 0.3 event. It binds `$PHASE_BASE`, not its future implementation commit.
- The 25 implementation paths form one atomic local commit. No per-task implementation commit is allowed because the evidence graph and governance registration must describe the same tree.
- All recorded command results are factual. Tracked evidence records only probes and validations completed before its finalization; final-tree and post-commit results live in external immutable attestations.
- Any source/hash/privacy/schema/path/registry/remote/no-side-effect/review failure stops candidate publication. No failure authorizes widening scope.

## Approval and Run Contract

| field | frozen value |
|---|---|
| User standing approval | `批准，再完成前不要再block，全部都同意` |
| Design | `PFI/docs/pfi_v025/stage_0/PHASE_0_3_DESIGN.md` |
| Design commit | `35ef4148723c5885bf9c2f962390bc9e562f5e50` |
| Roadmap SHA-256 | `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b` |
| Task Pack SHA-256 | `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2` |
| Iteration | `ITER-20260711-PFI-V025-S0-P03` |
| Contract | `PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE` |
| Acceptance | `ACC-PFI-V025-S0-P03-GAP-EVIDENCE` |
| Governance override | `PFI-V025-S0-P03-GOVERNANCE-COMPANIONS` |
| Governance conflict | `PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE` |
| Max scope | one Phase |

After this plan is independently reviewed and committed, capture the clean plan commit as `$PHASE_BASE`. Never hardcode the future implementation commit into tracked files.

## Exact File Map

**Create — 13 core artifacts:**

1. `PFI/docs/pfi_v025/stage_0/acceptance_request.md`
2. `PFI/docs/pfi_v025/stage_0/finding_ledger.csv`
3. `PFI/docs/pfi_v025/stage_0/gap_register.md`
4. `PFI/reports/pfi_v025/stage_0/baseline.json`
5. `PFI/reports/pfi_v025/stage_0/current_state_matrix.md`
6. `PFI/reports/pfi_v025/stage_0/data_root_inventory.json`
7. `PFI/reports/pfi_v025/stage_0/git_state.txt`
8. `PFI/reports/pfi_v025/stage_0/history_deprecation.md`
9. `PFI/reports/pfi_v025/stage_0/terminal.log`
10. `PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt`
11. `PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json`
12. `PFI/reports/pfi_v025/stage_0/phase_0_3/risk_and_rollback.md`
13. `PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log`

**Modify — 12 governance companions:**

1. `PFI/CHANGELOG.md`
2. `PFI/docs/governance/DEVELOPMENT_LEDGER.md`
3. `PFI/docs/governance/MODEL_SPEC.md`
4. `PFI/docs/governance/OWNER_STATUS.md`
5. `PFI/docs/governance/STATUS.md`
6. `PFI/docs/governance/TRACEABILITY_MATRIX.csv`
7. `PFI/docs/governance/VERSION_MATRIX.yaml`
8. `PFI/docs/governance/delivery_tasks.yaml`
9. `PFI/docs/governance/development_events.jsonl`
10. `PFI/docs/governance/formula_registry.yaml`
11. `PFI/docs/governance/model_registry.yaml`
12. `PFI/docs/governance/parameter_registry.csv`

Every other path is protected.

---

### Task 1: Freeze the clean base, source identities, remote boundary, and no-side-effect guard

**Files:** Read Git metadata, pinned inputs, Phase 0.2 evidence/attestation, design, and exact path existence. No tracked writes.

- [ ] **Step 1: Capture repository identity and clean Phase base**

Run from the canonical PFI worktree:

```bash
set -euo pipefail
umask 077
export PHASE_BASE="$(git rev-parse HEAD)"
pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
git remote get-url origin
git status --porcelain=v1 --untracked-files=all
test "$(git branch --show-current)" = "codex/pfi"
test "$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}')" = "origin/main"
test "$(git remote get-url origin)" = "git@github.com:LinzeColin/CodexProject.git"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
test "$(git rev-parse 35ef4148723c5885bf9c2f962390bc9e562f5e50^{commit})" = "35ef4148723c5885bf9c2f962390bc9e562f5e50"
test -x PFI/.venv/bin/python
PFI/.venv/bin/python -B -c 'import pytest, jsonschema'
command -v node
command -v jq
command -v sqlite3
export RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
case "$RUN_GUARD_PARENT" in
  /private/tmp/pfi-v025-s0p03-guard-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) exit 2 ;;
esac
mkdir -p -m 700 "$RUN_GUARD_PARENT"
chmod 700 "$RUN_GUARD_PARENT"
export RUN_GUARD_ROOT="$(PHASE_BASE="$PHASE_BASE" PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" <<'PY'
import fcntl
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.excepthook = lambda *_: print("phase_0_3_guard=FAIL|reason=redacted", file=sys.stderr)

parent = Path(sys.argv[1])
base = os.environ["PHASE_BASE"]
pointer = parent / "current.path"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def complete(run: Path) -> bool:
    state_path = run / "run_state.json"
    if not state_path.is_file() or state_path.is_symlink():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if state.get("schema") != "PFIV025Phase03RunStateV1" or state.get("phase_base") != base:
        return False
    if state.get("status") != "baseline_complete":
        return False
    required = {
        "before_sha256": "before.json",
        "git_state_before_sha256": "git_state_before.json",
        "governance_baseline_sha256": "governance_baseline.json",
    }
    return all(
        (run / name).is_file()
        and not (run / name).is_symlink()
        and state.get(field) == digest(run / name)
        for field, name in required.items()
    )

def publish_pointer(run: Path) -> None:
    temporary = pointer.with_name(f".{pointer.name}.tmp.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(str(run) + "\n")
    os.replace(temporary, pointer)

lock_path = parent / "guard.lock"
with lock_path.open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    if pointer.is_file() and not pointer.is_symlink():
        current = Path(pointer.read_text(encoding="utf-8").strip())
        assert current.parent == parent and not current.is_symlink()
        if complete(current):
            print(current)
            raise SystemExit(0)
    run = Path(tempfile.mkdtemp(prefix=f"{base}.run.", dir=parent))
    state_path = run / "run_state.json"
    with state_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "schema": "PFIV025Phase03RunStateV1",
            "status": "initializing",
            "phase_base": base,
            "initial_live_main": None,
            "initial_remote_base": None,
            "initial_remote_object_hydration_performed": None,
            "attempts": [],
        }, sort_keys=True) + "\n")
    state_path.chmod(0o600)
    publish_pointer(run)
    print(run)
PY
)"
case "$RUN_GUARD_ROOT" in "$RUN_GUARD_PARENT/$PHASE_BASE.run."*) ;; *) exit 2 ;; esac
test -d "$RUN_GUARD_ROOT" && test ! -L "$RUN_GUARD_ROOT"
```

Expected: canonical worktree, branch/upstream/remote match, and clean status. `$PHASE_BASE` is the plan commit.

- [ ] **Step 2: Verify pinned inputs and Phase 0.2 final attestation**

```bash
set -euo pipefail
test "$(openssl dgst -sha256 /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md | awk '{print $NF}')" = "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
test "$(openssl dgst -sha256 /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip | awk '{print $NF}')" = "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
unzip -t /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip
P02_ATTEST="$(git rev-parse --git-common-dir)/codex-review/pfi-v025/stage_0/phase_0_2/7433be0d70bdae42959c1b71753d93f8737db60d.attempt.id9uiuo8/phase_0_2_attestation.json"
test "$(openssl dgst -sha256 "$P02_ATTEST" | awk '{print $NF}')" = "8b579f727c9fdbe55fe8e9455ec28a4d7c6c45b4caf47fb7dbe1d6226859c60a"
jq -e '.phase_commit == "7433be0d70bdae42959c1b71753d93f8737db60d" and .status == "resolved_by_approved_override" and .blocks_phase_0_2_candidate == false and .contains_private_values == false' "$P02_ATTEST"
```

Expected: exact hashes, ZIP integrity pass, and immutable Phase 0.2 final attestation pass.

- [ ] **Step 3: Prove current advertised main is usable without ref mutation and has no remote-only PFI drift**

Capture complete refs, `FETCH_HEAD`, and shallow-file states before any exact-object hydration. Set `LIVE_MAIN` from `git ls-remote`. If the advertised commit object is missing, hydrate only that SHA with `--no-write-fetch-head --no-tags --no-prune --no-recurse-submodules`, then prove all three states unchanged. Use `GIT_NO_LAZY_FETCH=1` for object checks, merge-base, and diff:

```bash
set -euo pipefail
PHASE_BASE="$(git rev-parse HEAD)"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
test -f "$RUN_GUARD_PARENT/current.path" && test ! -L "$RUN_GUARD_PARENT/current.path"
RUN_GUARD_ROOT="$(tr -d '\n' < "$RUN_GUARD_PARENT/current.path")"
case "$RUN_GUARD_ROOT" in "$RUN_GUARD_PARENT/$PHASE_BASE.run."*) ;; *) exit 2 ;; esac
test "$(jq -er '.phase_base' "$RUN_GUARD_ROOT/run_state.json")" = "$PHASE_BASE"
export LIVE_MAIN="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
test -n "$LIVE_MAIN"
REFS_BEFORE="$(git for-each-ref --format='%(refname) %(objectname)')"
FETCH_HEAD_PATH="$(git rev-parse --git-path FETCH_HEAD)"
SHALLOW_PATH="$(git rev-parse --git-path shallow)"
if [ -e "$FETCH_HEAD_PATH" ]; then
  FETCH_HEAD_STATE=present
  FETCH_HEAD_BEFORE="$(openssl dgst -sha256 "$FETCH_HEAD_PATH" | awk '{print $NF}')"
else
  FETCH_HEAD_STATE=missing
fi
if [ -e "$SHALLOW_PATH" ]; then
  SHALLOW_STATE=present
  SHALLOW_BEFORE="$(openssl dgst -sha256 "$SHALLOW_PATH" | awk '{print $NF}')"
else
  SHALLOW_STATE=missing
fi
INITIAL_HYDRATED=false
if ! GIT_NO_LAZY_FETCH=1 git cat-file -e "$LIVE_MAIN^{commit}" 2>/dev/null; then
  INITIAL_HYDRATED=true
  GIT_TERMINAL_PROMPT=0 git \
    -c maintenance.auto=false \
    -c fetch.writeCommitGraph=false \
    -c fetch.recurseSubmodules=false \
    fetch --no-auto-maintenance --no-write-commit-graph \
    --no-recurse-submodules --no-prune --no-prune-tags \
    --no-write-fetch-head --no-tags origin "$LIVE_MAIN"
fi
test "$(git for-each-ref --format='%(refname) %(objectname)')" = "$REFS_BEFORE"
if [ "$FETCH_HEAD_STATE" = present ]; then
  test "$(openssl dgst -sha256 "$FETCH_HEAD_PATH" | awk '{print $NF}')" = "$FETCH_HEAD_BEFORE"
else
  test ! -e "$FETCH_HEAD_PATH"
fi
if [ "$SHALLOW_STATE" = present ]; then
  test "$(openssl dgst -sha256 "$SHALLOW_PATH" | awk '{print $NF}')" = "$SHALLOW_BEFORE"
else
  test ! -e "$SHALLOW_PATH"
fi
GIT_NO_LAZY_FETCH=1 git cat-file -e "$LIVE_MAIN^{commit}"
export REMOTE_BASE="$(GIT_NO_LAZY_FETCH=1 git merge-base "$PHASE_BASE" "$LIVE_MAIN")"
GIT_NO_LAZY_FETCH=1 git diff --quiet "$REMOTE_BASE..$LIVE_MAIN" -- PFI
printf 'initial_remote_object_hydration_performed=%s\n' "$INITIAL_HYDRATED"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
export RUN_GUARD_ROOT="$(LIVE_MAIN="$LIVE_MAIN" REMOTE_BASE="$REMOTE_BASE" INITIAL_HYDRATED="$INITIAL_HYDRATED" \
  PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" "$PHASE_BASE" <<'PY'
import fcntl
import json
import os
import sys
import tempfile
from pathlib import Path

parent = Path(sys.argv[1])
base = sys.argv[2]
pointer = parent / "current.path"
baseline_names = ("before.json", "git_state_before.json", "governance_baseline.json")

def publish_pointer(run: Path) -> None:
    temporary = pointer.with_name(f".{pointer.name}.tmp.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(str(run) + "\n")
    os.replace(temporary, pointer)

def new_run() -> tuple[Path, dict]:
    run = Path(tempfile.mkdtemp(prefix=f"{base}.run.", dir=parent))
    state = {
        "schema": "PFIV025Phase03RunStateV1",
        "status": "initializing",
        "phase_base": base,
        "initial_live_main": os.environ["LIVE_MAIN"],
        "initial_remote_base": os.environ["REMOTE_BASE"],
        "initial_remote_object_hydration_performed": os.environ["INITIAL_HYDRATED"] == "true",
        "attempts": [],
    }
    with (run / "run_state.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(state, sort_keys=True) + "\n")
    (run / "run_state.json").chmod(0o600)
    publish_pointer(run)
    return run, state

with (parent / "guard.lock").open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    assert pointer.is_file() and not pointer.is_symlink()
    run = Path(pointer.read_text(encoding="utf-8").strip())
    assert run.parent == parent and not run.is_symlink()
    state_path = run / "run_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["phase_base"] == base
    if state.get("status") == "baseline_complete":
        if (
            state.get("initial_live_main") == os.environ["LIVE_MAIN"]
            and state.get("initial_remote_base") == os.environ["REMOTE_BASE"]
        ):
            print(run)
            raise SystemExit(0)
        run, state = new_run()
        print(run)
        raise SystemExit(0)
    if any((run / name).exists() for name in baseline_names):
        run, state = new_run()
        print(run)
        raise SystemExit(0)
    state.update({
        "initial_live_main": os.environ["LIVE_MAIN"],
        "initial_remote_base": os.environ["REMOTE_BASE"],
        "initial_remote_object_hydration_performed": os.environ["INITIAL_HYDRATED"] == "true",
    })
    temporary = state_path.with_name(f".{state_path.name}.tmp.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(state, sort_keys=True) + "\n")
    temporary.chmod(0o600)
    os.replace(temporary, state_path)
    print(run)
PY
)"
case "$RUN_GUARD_ROOT" in "$RUN_GUARD_PARENT/$PHASE_BASE.run."*) ;; *) exit 2 ;; esac
test -d "$RUN_GUARD_ROOT" && test ! -L "$RUN_GUARD_ROOT"
```

Any ref/FETCH_HEAD/shallow mutation or remote PFI diff stops before writes. Record `initial_remote_object_hydration_performed` as the observed boolean.

- [ ] **Step 4: Verify exact path preconditions and immutable governance baselines**

Run a read-only Python assertion with the exact two arrays above: all 13 core paths must be absent and all 12 companions must be files. Capture hashes/canonical data for existing models, assumptions, formulas, all parameter rows, event prefix, and delivery tasks. Exact current counts are models=1, assumptions=2, formulas=1, parameter rows=23, delivery tasks=10; all must remain unchanged.

```bash
set -euo pipefail
PFI/.venv/bin/python -B - <<'PY'
from pathlib import Path
core = [
    "PFI/docs/pfi_v025/stage_0/acceptance_request.md",
    "PFI/docs/pfi_v025/stage_0/finding_ledger.csv",
    "PFI/docs/pfi_v025/stage_0/gap_register.md",
    "PFI/reports/pfi_v025/stage_0/baseline.json",
    "PFI/reports/pfi_v025/stage_0/current_state_matrix.md",
    "PFI/reports/pfi_v025/stage_0/data_root_inventory.json",
    "PFI/reports/pfi_v025/stage_0/git_state.txt",
    "PFI/reports/pfi_v025/stage_0/history_deprecation.md",
    "PFI/reports/pfi_v025/stage_0/terminal.log",
    "PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt",
    "PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json",
    "PFI/reports/pfi_v025/stage_0/phase_0_3/risk_and_rollback.md",
    "PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log",
]
companions = [
    "PFI/CHANGELOG.md",
    "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
    "PFI/docs/governance/MODEL_SPEC.md",
    "PFI/docs/governance/OWNER_STATUS.md",
    "PFI/docs/governance/STATUS.md",
    "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
    "PFI/docs/governance/VERSION_MATRIX.yaml",
    "PFI/docs/governance/delivery_tasks.yaml",
    "PFI/docs/governance/development_events.jsonl",
    "PFI/docs/governance/formula_registry.yaml",
    "PFI/docs/governance/model_registry.yaml",
    "PFI/docs/governance/parameter_registry.csv",
]
assert len(core) == len(set(core)) == 13 and all(not Path(path).exists() for path in core)
assert len(companions) == len(set(companions)) == 12 and all(Path(path).is_file() for path in companions)
print("phase_0_3_scope_precondition=PASS|core_new=13|companions_existing=12")
PY
```

- [ ] **Step 5: Create an external metadata-only guard under `/private/tmp`**

Recompute `$PHASE_BASE`, derive the fixed guard root, and require its `run_state.json` to bind the same base and non-null initial remote fields. Its `before.json` fingerprints only metadata for `~/.pfi`, `PFI/data`, `PFI/MetaDatabase`, working-tree `MetaDatabase/PFI`, repository `PFI/macos/PFI.app`, `/Applications/PFI.app`, Desktop and Downloads PFI entries. The fingerprint may hash relative names internally but writes only aggregate count/hash; it never opens financial contents or prints member paths. Also store complete Git ref/FETCH_HEAD/shallow hashes in `git_state_before.json` and immutable governance base hashes/prefix lengths in `governance_baseline.json`. This external guard is declared evidence and is never added to Git.

Run this complete block; it writes only aggregate external evidence:

```bash
set -euo pipefail
umask 077
PHASE_BASE="$(git rev-parse HEAD)"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
PHASE_BASE="$PHASE_BASE" PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" <<'PY'
import csv
import fcntl
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.excepthook = lambda *_: print("phase_0_3_guard_baseline=FAIL|reason=redacted", file=sys.stderr)

parent = Path(sys.argv[1])
base = os.environ["PHASE_BASE"]
root = Path.cwd()
pointer = parent / "current.path"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def publish_pointer(run: Path) -> None:
    temporary = pointer.with_name(f".{pointer.name}.tmp.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(str(run) + "\n")
    os.replace(temporary, pointer)

def validate_complete(run: Path, state: dict) -> None:
    assert state["status"] == "baseline_complete"
    required = {
        "before_sha256": "before.json",
        "git_state_before_sha256": "git_state_before.json",
        "governance_baseline_sha256": "governance_baseline.json",
    }
    for field, name in required.items():
        path = run / name
        assert path.is_file() and not path.is_symlink()
        assert state[field] == digest(path)

lock_path = parent / "guard.lock"
with lock_path.open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    assert pointer.is_file() and not pointer.is_symlink()
    guard = Path(pointer.read_text(encoding="utf-8").strip())
    assert guard.parent == parent and not guard.is_symlink()
    state_path = guard / "run_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["phase_base"] == base
    if state.get("status") == "baseline_complete":
        validate_complete(guard, state)
        print(f"phase_0_3_external_guard=REUSED|path={guard}")
        raise SystemExit(0)

    baseline_names = ("before.json", "git_state_before.json", "governance_baseline.json")
    premature_probe_keys = (
        "observed_at", "app_runtime_probe_ref", "app_runtime_probe_sha256",
        "raw_data_probe_ref", "raw_data_probe_sha256", "db_probe_ref", "db_probe_sha256",
    )
    if any((guard / name).exists() for name in baseline_names) or any(state.get(key) for key in premature_probe_keys):
        previous = state
        guard = Path(tempfile.mkdtemp(prefix=f"{base}.run.", dir=parent))
        state_path = guard / "run_state.json"
        state = {
            "schema": "PFIV025Phase03RunStateV1",
            "status": "initializing",
            "phase_base": base,
            "initial_live_main": previous["initial_live_main"],
            "initial_remote_base": previous["initial_remote_base"],
            "initial_remote_object_hydration_performed": previous["initial_remote_object_hydration_performed"],
            "attempts": [],
        }
        with state_path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(state, sort_keys=True) + "\n")
        state_path.chmod(0o600)
        publish_pointer(guard)

    assert state["status"] == "initializing"
    assert state["initial_live_main"] and state["initial_remote_base"]
    assert isinstance(state["initial_remote_object_hydration_performed"], bool)

    targets = {
        "user_pfi": Path.home() / ".pfi",
        "applications_app": Path("/Applications/PFI.app"),
        "desktop_app": Path.home() / "Desktop/PFI.app",
        "downloads_app": Path.home() / "Downloads/PFI.app",
        "repo_app": root / "PFI/macos/PFI.app",
        "repo_data": root / "PFI/data",
        "repo_metadatabase": root / "PFI/MetaDatabase",
        "working_metadatabase": root / "MetaDatabase/PFI",
    }

    def fingerprint(path: Path) -> dict:
        content_digest = hashlib.sha256()
        count = 0
        if not path.exists() and not path.is_symlink():
            return {"state": "missing", "entry_count": 0, "metadata_sha256": hashlib.sha256(b"missing").hexdigest()}
        pending = [path]
        while pending:
            current = pending.pop()
            value = current.lstat()
            relative = "." if current == path else current.relative_to(path).as_posix()
            payload = [relative, str(stat.S_IFMT(value.st_mode)), str(value.st_mode & 0o7777), str(value.st_size), str(value.st_mtime_ns)]
            if current.is_symlink():
                payload.append(os.readlink(current))
            content_digest.update("\0".join(payload).encode("utf-8", "surrogateescape"))
            count += 1
            if current.is_dir() and not current.is_symlink():
                pending.extend(sorted(current.iterdir(), reverse=True))
        return {"state": "present", "entry_count": count, "metadata_sha256": content_digest.hexdigest()}

    def runtime_fingerprint() -> dict:
        records = []
        for port in (8501, 8502):
            probe = subprocess.run(
                ["lsof", "-nP", "-a", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fp"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            assert probe.returncode in (0, 1)
            pids = sorted({line[1:] for line in probe.stdout.splitlines() if line.startswith("p") and line[1:].isdigit()})
            for pid in pids:
                cwd_probe = subprocess.run(
                    ["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                assert cwd_probe.returncode in (0, 1)
                cwd = next((line[1:] for line in cwd_probe.stdout.splitlines() if line.startswith("n")), "UNAVAILABLE")
                records.append(f"{port}\0{pid}\0{cwd}")
        payload = "\n".join(sorted(records)).encode("utf-8", "surrogateescape")
        return {
            "state": "present" if records else "absent",
            "listener_count": len(records),
            "metadata_sha256": hashlib.sha256(payload).hexdigest(),
        }

    before = {key: fingerprint(path) for key, path in targets.items()}
    before["runtime_listeners"] = runtime_fingerprint()
    before_path = guard / "before.json"
    with before_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(before, sort_keys=True) + "\n")
    before_path.chmod(0o600)

    def file_state(path: Path) -> dict:
        if not path.exists():
            return {"state": "missing"}
        return {"state": "present", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    refs = subprocess.check_output(["git", "for-each-ref", "--format=%(refname) %(objectname)"])
    git_state_path = guard / "git_state_before.json"
    with git_state_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "refs_sha256": hashlib.sha256(refs).hexdigest(),
            "fetch_head": file_state(Path(subprocess.check_output(["git", "rev-parse", "--git-path", "FETCH_HEAD"], text=True).strip())),
            "shallow": file_state(Path(subprocess.check_output(["git", "rev-parse", "--git-path", "shallow"], text=True).strip())),
        }, sort_keys=True) + "\n")
    git_state_path.chmod(0o600)

    paths = {
        "changelog": "PFI/CHANGELOG.md",
        "ledger": "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
        "model_spec": "PFI/docs/governance/MODEL_SPEC.md",
        "owner_status": "PFI/docs/governance/OWNER_STATUS.md",
        "status": "PFI/docs/governance/STATUS.md",
        "traceability": "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
        "version_matrix": "PFI/docs/governance/VERSION_MATRIX.yaml",
        "delivery": "PFI/docs/governance/delivery_tasks.yaml",
        "events": "PFI/docs/governance/development_events.jsonl",
        "formula": "PFI/docs/governance/formula_registry.yaml",
        "model": "PFI/docs/governance/model_registry.yaml",
        "parameters": "PFI/docs/governance/parameter_registry.csv",
    }
    base_blobs = {
        key: subprocess.check_output(["git", "show", f"{base}:{path}"])
        for key, path in paths.items()
    }
    parameter_rows = list(csv.DictReader(io.StringIO(base_blobs["parameters"].decode("utf-8"))))
    baseline = {
        "paths": paths,
        "base_sha256": {key: hashlib.sha256(blob).hexdigest() for key, blob in base_blobs.items()},
        "base_lengths": {key: len(blob) for key, blob in base_blobs.items()},
        "model_count": len(re.findall(rb"^\s*- model_id:", base_blobs["model"], re.M)),
        "assumption_count": len(re.findall(rb"^\s*- assumption_id:", base_blobs["model"], re.M)),
        "formula_count": len(re.findall(rb"^\s*- formula_id:", base_blobs["formula"], re.M)),
        "parameter_count": len(parameter_rows),
        "delivery_task_count": len(re.findall(rb"^\s*- task_id:", base_blobs["delivery"], re.M)),
        "event_line_count": len(base_blobs["events"].splitlines()),
    }
    assert len(paths) == 12
    assert (baseline["model_count"], baseline["assumption_count"], baseline["formula_count"], baseline["parameter_count"], baseline["delivery_task_count"]) == (1, 2, 1, 23, 10)
    governance_path = guard / "governance_baseline.json"
    with governance_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(baseline, sort_keys=True) + "\n")
    governance_path.chmod(0o600)

    state["status"] = "baseline_complete"
    state["before_sha256"] = digest(before_path)
    state["git_state_before_sha256"] = digest(git_state_path)
    state["governance_baseline_sha256"] = digest(governance_path)
    temporary = state_path.with_name(f".{state_path.name}.tmp.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(state, sort_keys=True) + "\n")
    temporary.chmod(0o600)
    os.replace(temporary, state_path)
    validate_complete(guard, state)
    print(f"phase_0_3_external_guard=PASS|path={guard}")
PY
```

Validate all four external JSON files and mode 600 before the first tracked write. Every later Task recomputes the fixed guard parent from its freshly read `$PHASE_BASE`, resolves `current.path`, requires a non-symlink `baseline_complete` run, and rechecks all three immutable baseline hashes; no later command depends on inherited shell variables. A partial run is preserved but never reused, and a complete run is reused without rewriting any baseline byte.

**Task acceptance:** clean base, exact authority hashes, no remote PFI drift, core absent/companions present, immutable baseline captured, and guard created before the first tracked write.

---

### Task 2: Collect fresh current evidence without product, data, App, runtime, or Git mutation

**Files:** Read only owner docs, UI source, App metadata/binaries, process metadata, Git objects, aggregate data/read model, immutable SQLite, and selected tests. Later transcribe sanitized results into the two tracked terminal logs using `apply_patch`.

- [ ] **Step 1: Capture one Phase timestamp and source/evidence registries**

Use one Australia/Sydney RFC 3339 `OBSERVED_AT` for the coordinated fresh probe set. Stream the three Task Pack members and verify their member hashes from Design §5.3. Build source selectors exactly as frozen: R native IDs, SUR numbered headings, AUD ordered fact-matrix rows, P01/P02 risk JSON pointers, exact artifact conflict IDs, active conflict IDs, and the typed Phase 0.2 lifecycle pair. Store only selector and source-text hashes, never copied private source text.

Registry canonicalization is fixed: Markdown table payload=`line.strip()+"\n"`; numbered section payload=`section.strip()+"\n"`; JSON pointer payload=`json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))`; collection payload is sorted `path + "\0" + member_sha256 + "\n"`; composite payload is canonical JSON of ordered component artifact hashes and selected values. Records use `selector_type` from `markdown_table_id`, `markdown_table_row`, `markdown_section`, `json_pointer`, `line_contains`, `whole_file`, `collection`, or `composite`. Each record contains `artifact_ref`, optional `zip_member`/`component_artifacts`/`member_hashes`, `artifact_sha256`, `selector`, `selector_type`, `source_text_sha256`, `observed_at`, and `fact_level`.

Persist `OBSERVED_AT` once in the external run state using the standard library `zoneinfo.ZoneInfo("Australia/Sydney")`; refuse to overwrite a non-null value (an exact existing binding is validated and reused). Every later task resolves the non-symlink `current.path` under `/private/tmp/pfi-v025-s0p03-guard-<base12>/`, then reads the nonce run's `run_state.json` and asserts the stored `phase_base` equals the tracked evidence base.

Use this locked atomic non-overwrite binding before any fresh probe. It prints no timestamp or path:

```bash
set -euo pipefail
PHASE_BASE="$(git rev-parse HEAD)"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
RUN_GUARD_ROOT="$(PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" "$PHASE_BASE" <<'PY'
import fcntl, hashlib, json, sys
from pathlib import Path
parent, base = Path(sys.argv[1]), sys.argv[2]
with (parent / "guard.lock").open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    pointer = parent / "current.path"
    assert pointer.is_file() and not pointer.is_symlink()
    run = Path(pointer.read_text(encoding="utf-8").strip())
    assert run.parent == parent and run.name.startswith(f"{base}.run.") and not run.is_symlink()
    state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
    assert state["phase_base"] == base and state["status"] == "baseline_complete"
    for field, name in {"before_sha256":"before.json","git_state_before_sha256":"git_state_before.json","governance_baseline_sha256":"governance_baseline.json"}.items():
        path = run / name
        assert path.is_file() and not path.is_symlink() and (path.stat().st_mode & 0o777) == 0o600
        assert hashlib.sha256(path.read_bytes()).hexdigest() == state[field]
    print(run)
PY
)"
test -f "$RUN_GUARD_ROOT/run_state.json"
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - \
  "$RUN_GUARD_ROOT/run_state.json" "$RUN_GUARD_ROOT/run_state.lock" "$PHASE_BASE" <<'PY'
import fcntl
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

state_path, lock_path = map(Path, sys.argv[1:3])
base = sys.argv[3]
lock_path.touch(mode=0o600, exist_ok=True)
lock_path.chmod(0o600)
with lock_path.open("r+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["phase_base"] == base and state["status"] == "baseline_complete"
    if state.get("observed_at"):
        existing = datetime.fromisoformat(state["observed_at"].replace("Z", "+00:00"))
        assert existing.tzinfo is not None and existing.utcoffset() is not None
        print("phase_0_3_observed_at_binding=REUSED")
        raise SystemExit(0)
    observed_at = datetime.now(ZoneInfo("Australia/Sydney")).isoformat()
    state["observed_at"] = observed_at
    temp_path = state_path.with_name(f".{state_path.name}.observed-at.{os.getpid()}")
    with temp_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(state, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temp_path.chmod(0o600)
    os.replace(temp_path, state_path)
    state_path.chmod(0o600)
print("phase_0_3_observed_at_binding=PASS")
PY
```

- [ ] **Step 2: Recheck Git/owner/web/release/route facts**

Run read-only hashes and targeted searches:

```bash
set -euo pipefail
git log -5 --format='%H %s'
git status --short --branch
test ! -e PFI/web/app/home.js
node --check PFI/web/app/shell.js
node --check PFI/web/app/routes.js
rg -n 'v0\.2\.[0-9]|pfi-v0|AUD/CNY|4\.69|localStorage|setInterval|setTimeout|任务已准备|PFI 处理入口' PFI/web/index.html PFI/web/app/shell.js PFI/web/app/routes.js PFI/web/app/version.js PFI/web/app/pages/reports.js
```

Hash each ordered owner/web member and record an aggregate collection hash. Do not reinterpret old prose as a pass. Record exactly five 40-character commit IDs and one-line subjects for `git_state.txt`.

- [ ] **Step 3: Recheck App and runtime identity without launch/stop/restart**

For repository, `/Applications`, Desktop-resolved, and Downloads bundles, read `Info.plist`, launcher executable hash, and strict `codesign --verify --deep --strict --verbose=2` exit/diagnostic. Resolve symlinks without copying. Enumerate listeners on 8501/8502 with `lsof`, inspect only cwd identity, and make read-only localhost health probes with short timeouts. Record redacted entry IDs, hashes, numeric exits, canonical-root boolean, health code, and listener count; never record process arguments or unrelated environment.

The complete probe writes one sanitized proof exclusively under the current guard, mode 600, and binds its SHA into `run_state.json`. All subprocess diagnostics are discarded; any exception emits only a redacted failure code:

```bash
set -euo pipefail
PHASE_BASE="$(git rev-parse HEAD)"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
RUN_GUARD_ROOT="$(PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" "$PHASE_BASE" <<'PY'
import fcntl, hashlib, json, sys
from pathlib import Path
parent, base = Path(sys.argv[1]), sys.argv[2]
with (parent / "guard.lock").open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    pointer = parent / "current.path"
    assert pointer.is_file() and not pointer.is_symlink()
    run = Path(pointer.read_text(encoding="utf-8").strip())
    assert run.parent == parent and run.name.startswith(f"{base}.run.") and not run.is_symlink()
    state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
    assert state["phase_base"] == base and state["status"] == "baseline_complete"
    for field, name in {"before_sha256":"before.json","git_state_before_sha256":"git_state_before.json","governance_baseline_sha256":"governance_baseline.json"}.items():
        path = run / name
        assert path.is_file() and not path.is_symlink() and (path.stat().st_mode & 0o777) == 0o600
        assert hashlib.sha256(path.read_bytes()).hexdigest() == state[field]
    print(run)
PY
)"
APP_PROOF="$RUN_GUARD_ROOT/app_runtime_probe.json"
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - \
  "$PHASE_BASE" "$RUN_GUARD_ROOT/run_state.json" "$APP_PROOF" <<'PY'
import contextlib
import fcntl
import hashlib
import io
import json
import os
import plistlib
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

base, state_name, output_name = sys.argv[1:4]
state_path = Path(state_name)
output_path = Path(output_name)
sys.excepthook = lambda *_: print("app_runtime_probe=FAIL|reason=redacted", file=sys.stderr)

def bind_proof(ref_key: str, sha_key: str, proof_sha: str) -> None:
    lock_path = state_path.with_name("run_state.lock")
    lock_path.touch(mode=0o600, exist_ok=True)
    with lock_path.open("r+", encoding="utf-8") as lock_stream:
        fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["phase_base"] == base and state["status"] == "baseline_complete"
        assert state.get(sha_key) in {None, ""}
        state.update({ref_key: output_path.name, sha_key: proof_sha})
        temporary = state_path.with_name(f".{state_path.name}.{sha_key}.{os.getpid()}")
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(state, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, state_path)

if output_path.exists():
    assert not output_path.is_symlink() and (output_path.stat().st_mode & 0o777) == 0o600
    existing = json.loads(output_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert existing["schema"] == "PFIV025Phase03AppRuntimeProbeV1"
    assert existing["phase_base"] == base and existing["observed_at"] == state["observed_at"]
    proof_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    if not state.get("app_runtime_probe_sha256"):
        bind_proof("app_runtime_probe_ref", "app_runtime_probe_sha256", proof_sha)
    else:
        assert state["app_runtime_probe_ref"] == output_path.name
        assert state["app_runtime_probe_sha256"] == proof_sha
    print("app_runtime_probe=REUSED")
    raise SystemExit(0)

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def collect() -> dict:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["phase_base"] == base and state["status"] == "baseline_complete" and state.get("observed_at")
    canonical_app = Path("/Applications/PFI.app")
    entries = [
        ("APP-REPOSITORY", Path("PFI/macos/PFI.app")),
        ("APP-CANONICAL", canonical_app),
        ("APP-DESKTOP", Path.home() / "Desktop/PFI.app"),
        ("APP-DOWNLOADS", Path.home() / "Downloads/PFI.app"),
    ]
    apps = []
    canonical_resolved = canonical_app.resolve(strict=False)
    for entry_id, app_path in entries:
        exists = app_path.exists()
        item = {
            "entry_id": entry_id,
            "exists": exists,
            "is_symlink": app_path.is_symlink(),
            "resolves_to_canonical": exists and app_path.resolve(strict=False) == canonical_resolved,
        }
        if exists:
            plist_path = app_path / "Contents/Info.plist"
            plist_raw = plist_path.read_bytes()
            plist = plistlib.loads(plist_raw)
            executable_name = str(plist["CFBundleExecutable"])
            executable_path = app_path / "Contents/MacOS" / executable_name
            result = subprocess.run(
                ["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            item.update({
                "bundle_identifier": str(plist["CFBundleIdentifier"]),
                "short_version": str(plist["CFBundleShortVersionString"]),
                "bundle_version": str(plist["CFBundleVersion"]),
                "plist_sha256": hashlib.sha256(plist_raw).hexdigest(),
                "executable_sha256": sha256(executable_path),
                "codesign_exit_code": int(result.returncode),
            })
        apps.append(item)

    pfi_root = Path("PFI").resolve()
    listeners = []
    for port in (8501, 8502):
        probe = subprocess.run(
            ["lsof", "-nP", "-Fpn", f"-iTCP:{port}", "-sTCP:LISTEN"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
        )
        assert probe.returncode in {0, 1}
        pids = sorted({int(line[1:]) for line in probe.stdout.splitlines() if line.startswith("p")})
        for pid in pids:
            cwd_probe = subprocess.run(
                ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                text=True,
            )
            cwd_values = [line[1:] for line in cwd_probe.stdout.splitlines() if line.startswith("n")]
            canonical = len(cwd_values) == 1 and Path(cwd_values[0]).resolve(strict=False).is_relative_to(pfi_root)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=2) as response:
                    http_status = int(response.status)
            except urllib.error.HTTPError as error:
                http_status = int(error.code)
            except Exception:
                http_status = 0
            listeners.append({
                "listener_id": f"LISTENER-{len(listeners) + 1:02d}",
                "port": port,
                "cwd_within_canonical_pfi_root": canonical,
                "health_http_status": http_status,
            })
    return {
        "schema": "PFIV025Phase03AppRuntimeProbeV1",
        "phase_base": base,
        "observed_at": state["observed_at"],
        "apps": apps,
        "listeners": listeners,
        "listener_count": len(listeners),
        "contains_private_values": False,
    }

try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        proof = collect()
    with output_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(proof, sort_keys=True) + "\n")
    output_path.chmod(0o600)
    proof_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    bind_proof("app_runtime_probe_ref", "app_runtime_probe_sha256", proof_sha)
except Exception:
    print("app_runtime_probe=FAIL|reason=redacted", file=sys.stderr)
    raise SystemExit(1)
print("app_runtime_probe=PASS")
PY
```

- [ ] **Step 4: Recheck exact data-root and read-model metadata**

Use the exact Design §7.4 inventory:

- `ROOT-01..04` in fixed order;
- `GIT-DATA-01` bound to `$PHASE_BASE:MetaDatabase/PFI`;
- `RAW-01..04` assigned by stable sorted Git path but never emit the paths;
- `DB-01` only when fresh candidate count remains one.

For the four raw Git blobs, use `GIT_NO_LAZY_FETCH=1 git show "$PHASE_BASE:<path>"` only in-memory. Reuse the repository Alipay parser to derive count/date range/as-of; emit only redacted IDs, bytes, SHA, count, dates, and `git_object_readable`. Do not write blobs to disk. Re-run `build_v024_data_source_scan` and `build_v024_read_model_status` with `PYTHONDONTWRITEBYTECODE=1`; discard private path fields before output. The exact raw probe is:

```bash
set -euo pipefail
PHASE_BASE="$(git rev-parse HEAD)"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
RUN_GUARD_ROOT="$(PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" "$PHASE_BASE" <<'PY'
import fcntl, hashlib, json, sys
from pathlib import Path
parent, base = Path(sys.argv[1]), sys.argv[2]
with (parent / "guard.lock").open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    pointer = parent / "current.path"
    assert pointer.is_file() and not pointer.is_symlink()
    run = Path(pointer.read_text(encoding="utf-8").strip())
    assert run.parent == parent and run.name.startswith(f"{base}.run.") and not run.is_symlink()
    state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
    assert state["phase_base"] == base and state["status"] == "baseline_complete"
    for field, name in {"before_sha256":"before.json","git_state_before_sha256":"git_state_before.json","governance_baseline_sha256":"governance_baseline.json"}.items():
        path = run / name
        assert path.is_file() and not path.is_symlink() and (path.stat().st_mode & 0o777) == 0o600
        assert hashlib.sha256(path.read_bytes()).hexdigest() == state[field]
    print(run)
PY
)"
RAW_PROOF="$RUN_GUARD_ROOT/raw_data_probe.json"
GIT_NO_LAZY_FETCH=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src \
  PFI/.venv/bin/python -B - \
  "$PHASE_BASE" "$RUN_GUARD_ROOT/run_state.json" "$RAW_PROOF" <<'PY'
import contextlib
import fcntl
import io
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from pfi_v02.stage2_import import parse_alipay_bill_bytes
from pfi_v02.stage_v023_read_model import build_stage6_read_model_input
from pfi_os.application.read_model_status import build_v024_data_source_scan, build_v024_read_model_status

base, state_name, output_name = sys.argv[1:4]
state_path = Path(state_name)
output_path = Path(output_name)
sys.excepthook = lambda *_: print("raw_data_probe=FAIL|reason=redacted", file=sys.stderr)

def bind_proof(ref_key: str, sha_key: str, proof_sha: str) -> None:
    lock_path = state_path.with_name("run_state.lock")
    lock_path.touch(mode=0o600, exist_ok=True)
    with lock_path.open("r+", encoding="utf-8") as lock_stream:
        fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["phase_base"] == base and state["status"] == "baseline_complete"
        assert state.get(sha_key) in {None, ""}
        state.update({ref_key: output_path.name, sha_key: proof_sha})
        temporary = state_path.with_name(f".{state_path.name}.{sha_key}.{os.getpid()}")
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(state, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, state_path)

if output_path.exists():
    assert not output_path.is_symlink() and (output_path.stat().st_mode & 0o777) == 0o600
    existing = json.loads(output_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert existing["schema"] == "PFIV025Phase03RawDataProbeV1"
    assert existing["phase_base"] == base and existing["observed_at"] == state["observed_at"]
    proof_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    if not state.get("raw_data_probe_sha256"):
        bind_proof("raw_data_probe_ref", "raw_data_probe_sha256", proof_sha)
    else:
        assert state["raw_data_probe_ref"] == output_path.name
        assert state["raw_data_probe_sha256"] == proof_sha
    print("raw_data_probe=REUSED")
    raise SystemExit(0)

def collect() -> dict:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["phase_base"] == base and state["status"] == "baseline_complete" and state.get("observed_at")
    env = dict(os.environ)
    env["GIT_NO_LAZY_FETCH"] = "1"
    source = build_stage6_read_model_input(project_root="PFI")
    raw_paths = sorted(source["git_raw_paths"])
    assert source["storage_mode"] == "git_tree" and len(raw_paths) == 4
    raw_sources = []
    for index, raw_path in enumerate(raw_paths, 1):
        result = subprocess.run(
            ["git", "show", f"{base}:{raw_path}"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        assert result.returncode == 0
        content = result.stdout
        parsed = parse_alipay_bill_bytes(content)
        dates = []
        for transaction in parsed.transactions:
            value = transaction.occurred_at[:10]
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)
            datetime.strptime(value, "%Y-%m-%d")
            dates.append(value)
        dates.sort()
        assert dates
        raw_sources.append({
            "raw_source_id": f"RAW-{index:02d}",
            "record_count": len(parsed.transactions),
            "date_range": {"start": dates[0], "end": dates[-1]},
            "as_of": dates[-1],
            "bytes": len(content),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "permission_class": "git_object_readable",
            "source_path_redacted": True,
        })
    scan = build_v024_data_source_scan(project_root="PFI")
    status = build_v024_read_model_status(project_root="PFI")
    root_states = [
        {"root_id": "ROOT-01", "existence": "set" if os.environ.get("PFI_DATA_HOME") else "unset"},
        {"root_id": "ROOT-02", "existence": "present" if Path("MetaDatabase/PFI").exists() else "absent"},
        {"root_id": "ROOT-03", "existence": "present" if Path("PFI/MetaDatabase").exists() else "absent"},
        {"root_id": "ROOT-04", "existence": "present" if (Path.home() / ".pfi").exists() else "absent"},
    ]
    tree_hash = subprocess.run(
        ["git", "rev-parse", f"{base}:MetaDatabase/PFI"], env=env,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, text=True,
    )
    assert tree_hash.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}\n?", tree_hash.stdout)
    tree_listing = subprocess.run(
        ["git", "ls-tree", "-lr", base, "--", "MetaDatabase/PFI"], env=env,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, text=True,
    )
    assert tree_listing.returncode == 0
    surface_files = []
    for line in tree_listing.stdout.splitlines():
        parts = line.split(None, 4)
        assert len(parts) == 5 and parts[1] == "blob" and parts[3].isdigit()
        surface_files.append((int(parts[3]), Path(parts[4]).suffix.lower().removeprefix(".")))
    extension_counts = {suffix: sum(1 for _, ext in surface_files if ext == suffix) for suffix in ("csv", "json", "sqlite")}
    proof = {
        "schema": "PFIV025Phase03RawDataProbeV1",
        "phase_base": base,
        "observed_at": state["observed_at"],
        "root_states": root_states,
        "repository_surface": {
            "surface_id": "GIT-DATA-01",
            "tree_hash": tree_hash.stdout.strip(),
            "file_count": len(surface_files),
            "bytes": sum(size for size, _ in surface_files),
            "extension_counts": extension_counts,
        },
        "raw_sources": raw_sources,
        "read_model": {
            "storage_mode": scan["storage_mode"],
            "raw_file_count": scan["raw_file_count"],
            "record_count": scan["record_count"],
            "date_range": scan["date_range"],
            "as_of": scan["as_of"],
            "evidence_hash": scan["evidence_hash"],
            "read_model_hash": status["read_model_hash"],
            "metric_states": {item["metric_id"]: item["status"] for item in status["core_metric_states"]},
            "blocked_metric_ids": status["blocked_metric_ids"],
        },
        "privacy": {"raw_filenames_emitted": 0, "raw_rows_emitted": 0, "financial_values_emitted": 0},
    }
    assert sum(item["record_count"] for item in raw_sources) >= scan["record_count"]
    return proof

try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        proof = collect()
    with output_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(proof, ensure_ascii=False, sort_keys=True) + "\n")
    output_path.chmod(0o600)
    proof_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    bind_proof("raw_data_probe_ref", "raw_data_probe_sha256", proof_sha)
except Exception:
    print("raw_data_probe=FAIL|reason=redacted", file=sys.stderr)
    raise SystemExit(1)
print("raw_data_probe=PASS")
PY
```

For `DB-01`, locate but never print the private filename. Capture candidate count, bytes, mtime, permission class, and SHA before; open `file:<path>?mode=ro&immutable=1` with `uri=True`, set `PRAGMA query_only=ON` before any query, run `quick_check`, table count, and aggregate user-table row count without emitting table names. Date semantics are typed `metadata_unavailable` with `S2-P1-T3`; do not guess. Capture the same metadata after and require exact equality. Use this read-only probe and transcribe only its sanitized JSON result with `apply_patch`:

```bash
set -euo pipefail
PHASE_BASE="$(git rev-parse HEAD)"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
RUN_GUARD_ROOT="$(PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" "$PHASE_BASE" <<'PY'
import fcntl, hashlib, json, sys
from pathlib import Path
parent, base = Path(sys.argv[1]), sys.argv[2]
with (parent / "guard.lock").open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    pointer = parent / "current.path"
    assert pointer.is_file() and not pointer.is_symlink()
    run = Path(pointer.read_text(encoding="utf-8").strip())
    assert run.parent == parent and run.name.startswith(f"{base}.run.") and not run.is_symlink()
    state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
    assert state["phase_base"] == base and state["status"] == "baseline_complete"
    for field, name in {"before_sha256":"before.json","git_state_before_sha256":"git_state_before.json","governance_baseline_sha256":"governance_baseline.json"}.items():
        path = run / name
        assert path.is_file() and not path.is_symlink() and (path.stat().st_mode & 0o777) == 0o600
        assert hashlib.sha256(path.read_bytes()).hexdigest() == state[field]
    print(run)
PY
)"
DB_PROOF="$RUN_GUARD_ROOT/db_probe.json"
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - \
  "$PHASE_BASE" "$RUN_GUARD_ROOT/run_state.json" "$DB_PROOF" <<'PY'
import contextlib
import fcntl
import hashlib
import io
import json
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

base, state_name, output_name = sys.argv[1:4]
state_path = Path(state_name)
output_path = Path(output_name)
sys.excepthook = lambda *_: print("db_probe=FAIL|reason=redacted", file=sys.stderr)

def bind_proof(ref_key: str, sha_key: str, proof_sha: str) -> None:
    lock_path = state_path.with_name("run_state.lock")
    lock_path.touch(mode=0o600, exist_ok=True)
    with lock_path.open("r+", encoding="utf-8") as lock_stream:
        fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["phase_base"] == base and state["status"] == "baseline_complete"
        assert state.get(sha_key) in {None, ""}
        state.update({ref_key: output_path.name, sha_key: proof_sha})
        temporary = state_path.with_name(f".{state_path.name}.{sha_key}.{os.getpid()}")
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(state, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, state_path)

if output_path.exists():
    assert not output_path.is_symlink() and (output_path.stat().st_mode & 0o777) == 0o600
    existing = json.loads(output_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert existing["schema"] == "PFIV025Phase03DatabaseProbeV1"
    assert existing["phase_base"] == base and existing["observed_at"] == state["observed_at"]
    proof_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    if not state.get("db_probe_sha256"):
        bind_proof("db_probe_ref", "db_probe_sha256", proof_sha)
    else:
        assert state["db_probe_ref"] == output_path.name
        assert state["db_probe_sha256"] == proof_sha
    print("db_probe=REUSED")
    raise SystemExit(0)

def collect() -> dict:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["phase_base"] == base and state["status"] == "baseline_complete" and state.get("observed_at")
    candidates = sorted(
        path for path in (Path.home() / ".pfi").rglob("*")
        if path.is_file() and path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}
    )
    assert len(candidates) == 1
    path = candidates[0]

    def snapshot() -> dict:
        value = path.stat()
        return {
            "candidate_count": 1,
            "bytes": value.st_size,
            "mtime_epoch": int(value.st_mtime),
            "permission_class": "readable_no_write_attempt",
            "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    before = snapshot()
    uri = "file:" + quote(str(path), safe="/") + "?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        aggregate_rows = 0
        for table in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            aggregate_rows += int(connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])
    finally:
        connection.close()
    after = snapshot()
    assert before == after and quick_check == "ok"
    return {
        "schema": "PFIV025Phase03DatabaseProbeV1",
        "phase_base": base,
        "observed_at": state["observed_at"],
        "database_id": "DB-01",
        "before": before,
        "after": after,
        "query_mode": "ro&immutable=1",
        "query_only": True,
        "quick_check": quick_check,
        "table_count": len(tables),
        "aggregate_user_table_record_count": aggregate_rows,
        "database_path_redacted": True,
    }

try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        proof = collect()
    with output_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(proof, sort_keys=True) + "\n")
    output_path.chmod(0o600)
    proof_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    bind_proof("db_probe_ref", "db_probe_sha256", proof_sha)
except Exception:
    print("db_probe=FAIL|reason=redacted", file=sys.stderr)
    raise SystemExit(1)
print("db_probe=PASS")
PY
```

- [ ] **Step 5: Run only the bounded diagnostics approved by the design**

Use no caches or bytecode:

```bash
set -euo pipefail
set +e
PARAM_OUTPUT="$(PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_pfi_parameters_consistency.py -q 2>&1)"
PARAM_RC=$?
set -e
test "$PARAM_RC" -eq 1
printf '%s\n' "$PARAM_OUTPUT" | rg '5 failed, 3 passed'
COLLECT_OUTPUT="$(PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B -m pytest -p no:cacheprovider --collect-only PFI/tests -q 2>&1)"
printf '%s\n' "$COLLECT_OUTPUT" | rg '795 tests collected'
python3 -c 'import sqlite3; print(sqlite3.sqlite_version)'
```

The isolated parameter test is an expected diagnostic baseline, not the Phase gate: record its real result (expected 3 passed/5 failed) without flattening it to pass. Full test execution, browser/UAT, backup/restore, public-shell runtime isolation, temporal/dual-consumption production proof, and other later-Stage work remain `not_run_by_phase_contract` or `blocked_missing_required_proof`.

- [ ] **Step 6: Freeze sanitized probe records before artifact assembly**

Prepare stable IDs and factual outcomes for `CURRENT_OWNER`, `CURRENT_WEB`, `CURRENT_RUNTIME_APP`, data roots, five New findings, Fixed scope checks, and the eight missing-proof findings listed in Design §7.6. Each record must contain exact command summary, integer exit, the guard-bound `OBSERVED_AT`, and one allowed outcome.

The Phase terminal machine surface is fixed and contains no captured raw stdout/stderr:

- exactly ten single-line records prefixed `P03_COMMAND ` followed by canonical compact JSON with `record_id`, `observed_at`, `exit_code`, `outcome`, and `summary`; `APP-001`, `DATA-001`, and `DB-001` additionally contain `proof_id` plus the corresponding guard-bound `proof_sha256`;
- exactly one single-line record prefixed `P03_OUTCOMES ` followed by canonical compact JSON with `record_id=P03-OUTCOMES`, `observed_at`, and `finding_outcomes` keyed by **every** finding whose frozen `current_evidence_refs` contains `P03_TERM`;
- reproduced findings map to `reproduced`, Fixed findings to their exact `fixed_within_*` result, New findings to `new_current_fact`, and FND-011/014/016/018/023/024/025/029 to `not_run_by_phase_contract` or `blocked_missing_required_proof`.

The ten `summary` values are exact non-private enums: `PRE-001=preflight_complete`, `SRC-001=source_registry_verified`, `CUR-001=current_facts_collected`, `APP-001=app_runtime_probe_bound`, `DATA-001=raw_data_probe_bound`, `DB-001=database_probe_bound`, `TEST-001=expected_3_pass_5_fail`, `TEST-002=795_tests_collected`, `STRUCT-001=structure_verified`, `GOV-001=governance_verified`. `outcome=expected_diagnostic_failure` only for TEST-001 and `outcome=pass` for the other nine. Evidence command summaries reuse the same exact enum values.

The `P03_TERM` evidence-registry `outcomes` object is copied exactly from that parsed `P03_OUTCOMES` line; it is never authored independently. `CURRENT_RUNTIME_APP` selects the `APP-001` terminal record, whose proof SHA must equal the current guard proof and the evidence command record.

Tracked evidence command IDs are fixed and unique: `PRE-001`, `SRC-001`, `CUR-001`, `APP-001`, `DATA-001`, `DB-001`, `TEST-001`, `TEST-002`, `STRUCT-001`, `GOV-001`. `TEST-001` records the expected diagnostic exit 1 plus exact 3-pass/5-fail classification; the other nine record exit 0. Do not yet claim final-tree/postcommit pass.

**Task acceptance:** every current finding has traceable fresh or correctly aged evidence; no requirement document is used as a fake current failure; no protected state changed.

---

### Task 3: Create the finding ledger, gap register, and Stage 0 evidence surfaces

**Files:** Create the 11 Layer 0/1 core artifacts with `apply_patch`. Task 5 creates draft evidence; Task 6 creates the request only after preliminary gates pass.

- [ ] **Step 1: Create `finding_ledger.csv` from the frozen crosswalk**

Use the exact 18-column order from Design §5.1. Expand `PFI-V025-FND-001..038` and Design §5.3 exactly; never derive a different universe. Populate source/evidence IDs, RFC 3339 as-of fields, fact/priority bases, exact 114 Roadmap task tokens, both blocker booleans, and nonempty rationale. Frozen counts are:

```text
StillPresent=23 Fixed=7 Regressed=0 N/A=3 New=5
P0=26 P1=10 P2=2
eligible_open=28 non_gap=10
```

All 28 open P0/P1 rows have `blocks_v025_production_acceptance=true`; Fixed/N/A rows have false. Every row has `blocks_phase_0_3_candidate=false` once classification is valid.

Rationale machine markers are mandatory: every Fixed row includes `scope_limit=<matching named scope>`; every N/A row includes `non_gap_reason=<current-contract reason>`; every New row includes `source_universe_non_match=<same-predicate explanation>`. Free prose may follow but cannot replace these markers.

- [ ] **Step 2: Create `gap_register.md`**

Create exactly the 13 primary gaps from Design §6. Each eligible finding occurs once; `GAP-P0-01` contains FND-001/002/027/035 and `GAP-P1-04` contains only FND-030. Include current state, target state, exact tasks, dependency order, required acceptance evidence, stop condition, and `open`. Create one non-gap disposition table for the 10 Fixed/N/A findings. State executable P2 count=0 and do not create a deferred v0.2.5 backlog.

Machine format is fixed: retain the 13 `GAP-Px-NN = <semicolon-delimited FND IDs>` mapping lines and one `NON_GAP = <semicolon-delimited FND IDs>` line. Immediately after the mapping block add `## Non-gap dispositions` with the exact table header `| finding_id | status | priority | disposition | rationale_marker |` and exactly ten sorted `FND-NNN` rows. `disposition=non_gap`; status/priority equal the ledger; `rationale_marker` is the exact `scope_limit=<matching-named-scope>` marker for Fixed or `non_gap_reason=<matching-current-contract-reason>` marker for N/A and must occur verbatim in that ledger row. Then create one `### GAP-Px-NN` section per gap. Each section contains exactly one nonempty bullet for `gap_id`, `priority`, `linked_finding_ids`, `current_state`, `target_state`, `roadmap_resolution_tasks`, `dependencies`, `required_acceptance_evidence`, `stop_condition`, and `status`; status is `open`, priority matches the ID, and linked IDs/tasks exactly match the frozen mapping/crosswalk.

- [ ] **Step 3: Create Stage-level baseline, Git state, matrix, data inventory, and history reference**

- `baseline.json`: authority/source hashes, Phase 0.1/0.2 identities, external attestation hash/status, `$PHASE_BASE`, initial live main, contract/projection hashes, frozen counts, and privacy boundary.
- `git_state.txt`: cwd/root/branch/upstream/base, advertised main, merge-base, PFI remote diff, clean pre-write state, exact last five commit pairs, and `candidate_commit_binding=external_attestation_required`.
- `current_state_matrix.md`: exact status enum and evidence for Git, formal UI, release, App, listeners, roots, read model, nav, owner, privacy, tests, Phase evidence, and Stage acceptance.
- `data_root_inventory.json`: exact typed `PFIV025Stage0DataRootInventoryV1` shape and no null required metadata from Design §7.4. Its exact top-level keys are `schema,version,stage,candidate_roots,repository_object_surfaces,raw_sources,databases,read_model,privacy`; `version=v0.2.5` and `stage=0`. Load `raw_data_probe.json` and `db_probe.json` only through the current guard `run_state.json`, verify mode 600, Phase base, batch timestamp and bound SHA before transcription, and never transcribe console output. Every candidate root and `GIT-DATA-01` uses `source_evidence_ref=guard:raw_data_probe.json` plus the exact guard-bound raw proof SHA; `DB-01` uses `source_evidence_ref=guard:db_probe.json` plus the exact DB proof SHA. `RAW-01..04` and `read_model` must equal the raw proof field-for-field after the fixed typed-measurement wrapping. `DB-01` contains `before` and `after` objects with candidate_count/bytes/mtime_epoch/permission_class/content_sha256 typed measurements; they must equal the DB proof and the corresponding top-level DB measurements. DB `date_range` and `as_of` are exact `metadata_unavailable` measurements with reason `not_exposed_by_phase_0_3_query_only_probe` and sole resolution task `S2-P1-T3`. Every top-level/item/measurement object uses the exact allowlisted keys asserted by Task 6; no source filename/path/table/row/value extension field is permitted.
- Stage `history_deprecation.md`: immutable reference to the canonical Stage 0 history policy, its hash, projection hash, and 21 IDs; no duplicated decision table.

- [ ] **Step 4: Create both terminal logs, changed-files ledger, and risk/rollback**

The detailed log contains only the completed Task 1/2 facts and pre-evidence structural checks, with stable record IDs and numeric exits. The Stage log summarizes Phase 0.1/0.2/0.3 results and known expected failures. `changed_files.txt` is the exact sorted 25-path list. `risk_and_rollback.md` records open P0/P1, P2 disposition, guard path, privacy, exact rollback, compensating-commit rule, and Stage stop.

**Task acceptance:** all Layer 0/1 core artifacts except `evidence.json` and `acceptance_request.md` exist, are truthful, and contain no future validation/commit facts.

---

### Task 4: Synchronize exactly twelve governance companions without changing product or registry truth

**Files:** Modify only the 12 companion paths.

- [ ] **Step 1: Add non-model Phase contracts**

Append the same Phase contract identity to `MODEL_SPEC.md`, `model_registry.yaml`, and `formula_registry.yaml`. Keep existing model/assumption/formula arrays byte/structure equivalent and changed-ID arrays empty. In `parameter_registry.csv`, change only PARAM-PFI-003 `source_or_rationale`; every other cell in that row and every cell in all other rows remains exact.

- [ ] **Step 2: Add ledger, event, delivery, and traceability records**

- Append `ITER-20260711-PFI-V025-S0-P03` to `DEVELOPMENT_LEDGER.md`.
- Append exactly one mutable-before-commit JSONL event `EVENT-20260711-PFI-V025-S0-P03` with `$PHASE_BASE`, exact 25 planned paths, four task IDs, empty changed model/formula/parameter IDs, initial `result=validation_in_progress`, `binding_status=approved_pending_validation`, `contains_private_values=false`, and no future commit. Task 6 updates this same appended line after real gates pass; it never appends a second event.
- Add one Phase contract to `delivery_tasks.yaml`; keep canonical task count=10.
- Add four explicit `TRACEABILITY_MATRIX.csv` rows for S0-P3-T1, T2, T3, T4; model/formula/parameter columns are `NOT_APPLICABLE`.

- [ ] **Step 3: Add status/version/owner/changelog overlays**

Add initial `validation_in_progress` overlays to VERSION_MATRIX, STATUS, OWNER_STATUS, and CHANGELOG. Preserve actual VERSION/runtime/owner truth, keep Phase 0.2 external resolution explicit, and state Stage 0 whole review/Stage 1 not started. Task 6 changes only the overlay lifecycle to pending postcommit attestation after real gates pass. Do not create a new canonical version or owner completion claim.

- [ ] **Step 4: Verify immutable registry baselines**

Compare to Task 1 snapshots: definitions/values/config refs/counts unchanged, one event appended, task count unchanged, and only the permitted PARAM-PFI-003 metadata cells differ.

**Task acceptance:** exact twelve companions, no semantic value drift, no 13th companion, and no completion inflation.

---

### Task 5: Assemble the acyclic draft evidence index

**Files:** Create a truthful draft `phase_0_3/evidence.json`; do not create `acceptance_request.md` until Task 6 gates pass. Do not change Layer 0/1 after its hashes are frozen.

- [ ] **Step 1: Freeze and hash Layer 0/1 artifacts**

Run JSON/CSV/Markdown structural validators against every Layer 0/1 artifact. Compute SHA-256 for pinned inputs, Phase 0.1/0.2 evidence, Phase 0.2 attestation, finding/gap/stage evidence, both terminal logs, changed-files, and risk/rollback. If any Layer 0/1 file changes later, restart this Task.

`artifact_hashes` has exactly these 35 keys; serialize deterministically by sorted key:

```text
/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip
.git/codex-review/pfi-v025/stage_0/phase_0_2/7433be0d70bdae42959c1b71753d93f8737db60d.attempt.id9uiuo8/phase_0_2_attestation.json
PFI/config/pfi_v025_active_requirements.json
PFI/docs/pfi_v025/stage_0/PHASE_0_1_DESIGN.md
PFI/docs/pfi_v025/stage_0/PHASE_0_1_IMPLEMENTATION_PLAN.md
PFI/docs/pfi_v025/stage_0/PHASE_0_2_DESIGN.md
PFI/docs/pfi_v025/stage_0/PHASE_0_2_IMPLEMENTATION_PLAN.md
PFI/docs/pfi_v025/stage_0/PHASE_0_3_DESIGN.md
PFI/docs/pfi_v025/stage_0/PHASE_0_3_IMPLEMENTATION_PLAN.md
PFI/docs/pfi_v025/stage_0/history_deprecation.md
PFI/docs/pfi_v025/stage_0/run_contract.md
PFI/docs/pfi_v025/stage_0/scope_boundary.md
PFI/docs/pfi_v025/stage_0/finding_ledger.csv
PFI/docs/pfi_v025/stage_0/gap_register.md
PFI/reports/pfi_v025/stage_0/baseline.json
PFI/reports/pfi_v025/stage_0/current_state_matrix.md
PFI/reports/pfi_v025/stage_0/data_root_inventory.json
PFI/reports/pfi_v025/stage_0/git_state.txt
PFI/reports/pfi_v025/stage_0/history_deprecation.md
PFI/reports/pfi_v025/stage_0/terminal.log
PFI/reports/pfi_v025/stage_0/phase_0_1/changed_files.txt
PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json
PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json
PFI/reports/pfi_v025/stage_0/phase_0_1/git_state.txt
PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json
PFI/reports/pfi_v025/stage_0/phase_0_1/risk_and_rollback.md
PFI/reports/pfi_v025/stage_0/phase_0_1/terminal.log
PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt
PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json
PFI/reports/pfi_v025/stage_0/phase_0_2/risk_and_rollback.md
PFI/reports/pfi_v025/stage_0/phase_0_2/terminal.log
PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt
PFI/reports/pfi_v025/stage_0/phase_0_3/risk_and_rollback.md
PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log
```

- [ ] **Step 2: Create the draft `phase_0_3/evidence.json`**

Use the Task Pack evidence schema and Design §7.7. Required highlights:

```text
version=v0.2.5 stage=0 phase=0.3 status=not_run
git_commit=$PHASE_BASE
git_commit_semantics=implementation_base_before_phase_commit
allowed_files_obeyed=false
requires_user_acceptance=true
contains_private_values=false
governance_override_state=approved_pending_validation
stage_0_whole_review_status=not_started
stage_1_status=not_started
```

Include exact 25 planned paths, four `not_run` task records, source/evidence/priority registries, frozen counts, 13 gaps, P2 disposition, completed collection/component commands with integer exits, explicit non-goals, risks, rollback, initial remote/hydration facts, and Layer 0/1 hashes. Command records use exact key sets: the common four keys are `command_id,command,exit_code,summary`; `TEST-001` adds only `expected_diagnostic`; `APP-001`, `DATA-001`, and `DB-001` add only `proof_id,proof_sha256` and exactly match the current guard bindings. `artifact_hashes` excludes evidence itself, future acceptance request, and all governance companions.

Registry shape is fixed: `source_registry`, `evidence_registry`, and `priority_registry` are JSON objects keyed by their canonical IDs, not arrays. `source_registry` has exactly the 71 source tokens used by the CSV. `evidence_registry` contains every non-`NOT_APPLICABLE` prior/current ref token and may contain no unresolved key. `priority_registry` keys equal the distinct CSV `priority_basis` values and each record adds `priority=P0|P1|P2`. Every registry record uses the Task 2 canonicalization fields; `observed_at` is timezone-aware RFC 3339 and artifact/source hashes are lowercase 64-hex. Collection aggregate SHA is computed from the canonical sorted member payload, not self-declared. Composite records bind component paths, component hashes, and selected values.

- [ ] **Step 3: Validate the draft evidence schema before candidate gates**

Stream the Task Pack evidence schema from the pinned ZIP and validate without extraction:

```bash
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - <<'PY'
import json
import zipfile
from pathlib import Path
from jsonschema import Draft202012Validator

zip_path = Path("/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip")
member = "PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"
evidence_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json")
with zipfile.ZipFile(zip_path) as archive:
    schema = json.loads(archive.read(member))
instance = json.loads(evidence_path.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(instance)
print("phase_0_3_evidence_schema=PASS")
PY
```

Then run JSON parse and draft privacy/registry shape checks. Do not create `human_acceptance.json` or `acceptance_request.md` yet.

**Task acceptance:** acyclic Layer 0/1 hash graph and schema-valid truthful draft evidence; no candidate-pass or human-acceptance claim precedes validation.

---

### Task 6: Validate the draft, finalize candidate lifecycle, and rerun exact final gates

- [ ] **Step 1: Prove the exact 24-path provisional scope**

```bash
set -euo pipefail
PHASE_BASE="$(jq -er '.git_commit' PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json)"
test "$(git rev-parse "$PHASE_BASE^{commit}")" = "$PHASE_BASE"
git diff --check
git diff --name-only "$PHASE_BASE" | sort
git ls-files --others --exclude-standard | sort
git status --porcelain=v1 --untracked-files=all
```

Compare the exact observed set to the frozen array minus `acceptance_request.md`. There must be 24 unique paths and no protected path. The request is intentionally absent until preliminary gates pass.

- [ ] **Step 2: Run pre-final component and registry gates**

Independently assert every item below except final evidence status, request binding, and exact-25 scope. The draft evidence must remain `not_run/allowed_files_obeyed=false`, the sole event/overlays must remain `validation_in_progress`, and the request must remain absent.

The final verifier, defined next and executed only in Step 6, must independently assert:

- exact 18-column CSV, 38 IDs, frozen status/priority/fact counts;
- exact source families and conflict IDs, AUD-15→FND-023, source/evidence/priority registry hashes/selectors;
- exact 21 history IDs once, five New rationales, zero Regressed, status-specific evidence tuple/as-of rules;
- all 114 resolution tokens in the pinned Roadmap exact ID set;
- exact 28→13 gap mapping, priority purity, 10 non-gaps, zero executable P2;
- exact data root/surface/raw/database IDs/order, typed measurements, database before=after, privacy zeros;
- exact six Stage evidence basenames, evidence hash DAG, request→evidence hash, exact 25 paths/tasks, integer command exits;
- no pending human acceptance artifact, no private-value patterns, no future implementation SHA;
- registry definitions/values/counts unchanged and event append-only.

#### Final semantic verifier definition — execute only in Step 6

Use the following inline verifier after Step 5 finalization so no tracked helper/cache file is created:

```bash
set -euo pipefail
PHASE_BASE="$(jq -er '.git_commit' PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json)"
test "$(git rev-parse "$PHASE_BASE^{commit}")" = "$PHASE_BASE"
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "$PHASE_BASE" <<'PY'
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

base = sys.argv[1]
root = Path.cwd()
design = Path("PFI/docs/pfi_v025/stage_0/PHASE_0_3_DESIGN.md").read_text(encoding="utf-8")
roadmap = Path("/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md").read_text(encoding="utf-8")
valid_tasks = set(re.findall(r"\bS\d+-P\d+-T\d+\b", roadmap))

PINNED_HASHES = {
    "/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md": "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b",
    "/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip": "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2",
    ".git/codex-review/pfi-v025/stage_0/phase_0_2/7433be0d70bdae42959c1b71753d93f8737db60d.attempt.id9uiuo8/phase_0_2_attestation.json": "8b579f727c9fdbe55fe8e9455ec28a4d7c6c45b4caf47fb7dbe1d6226859c60a",
    "PFI/config/pfi_v025_active_requirements.json": "b77e1ac78e8842d9a58d76d07a491f80e7a010b3cc91fb4ca7cf24ba10457d37",
}

guard_parent = Path(f"/private/tmp/pfi-v025-s0p03-guard-{base[:12]}")
guard_pointer = guard_parent / "current.path"
assert guard_pointer.is_file() and not guard_pointer.is_symlink()
guard = Path(guard_pointer.read_text(encoding="utf-8").strip())
assert guard.parent == guard_parent and guard.name.startswith(f"{base}.run.") and not guard.is_symlink()
state_path = guard / "run_state.json"
assert state_path.is_file() and (state_path.stat().st_mode & 0o777) == 0o600
run_state = json.loads(state_path.read_text(encoding="utf-8"))
assert run_state["status"] == "baseline_complete"
assert run_state["phase_base"] == base and run_state.get("observed_at")
for state_key, filename in {
    "before_sha256": "before.json",
    "git_state_before_sha256": "git_state_before.json",
    "governance_baseline_sha256": "governance_baseline.json",
}.items():
    guarded_path = guard / filename
    assert guarded_path.is_file() and not guarded_path.is_symlink()
    assert (guarded_path.stat().st_mode & 0o777) == 0o600
    assert hashlib.sha256(guarded_path.read_bytes()).hexdigest() == run_state[state_key]
batch_observed_at = datetime.fromisoformat(run_state["observed_at"].replace("Z", "+00:00"))
assert batch_observed_at.tzinfo is not None and batch_observed_at.utcoffset() is not None

def load_guard_proof(ref_key: str, sha_key: str) -> tuple[Path, dict]:
    ref = run_state[ref_key]
    assert Path(ref).name == ref and "/" not in ref
    path = guard / ref
    assert path.is_file() and (path.stat().st_mode & 0o777) == 0o600
    assert hashlib.sha256(path.read_bytes()).hexdigest() == run_state[sha_key]
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value["phase_base"] == base and value["observed_at"] == run_state["observed_at"]
    return path, value

app_proof_path, app_proof = load_guard_proof("app_runtime_probe_ref", "app_runtime_probe_sha256")
raw_proof_path, raw_proof = load_guard_proof("raw_data_probe_ref", "raw_data_probe_sha256")
db_proof_path, db_proof = load_guard_proof("db_probe_ref", "db_probe_sha256")

assert set(app_proof) == {
    "schema", "phase_base", "observed_at", "apps", "listeners",
    "listener_count", "contains_private_values",
}
assert app_proof["schema"] == "PFIV025Phase03AppRuntimeProbeV1"
assert app_proof["contains_private_values"] is False
assert [item["entry_id"] for item in app_proof["apps"]] == [
    "APP-REPOSITORY", "APP-CANONICAL", "APP-DESKTOP", "APP-DOWNLOADS",
]
app_base_keys = {"entry_id", "exists", "is_symlink", "resolves_to_canonical"}
app_present_keys = app_base_keys | {
    "bundle_identifier", "short_version", "bundle_version", "plist_sha256",
    "executable_sha256", "codesign_exit_code",
}
for item in app_proof["apps"]:
    assert set(item) == (app_present_keys if item["exists"] else app_base_keys)
    if item["exists"]:
        assert re.fullmatch(r"[0-9a-f]{64}", item["plist_sha256"])
        assert re.fullmatch(r"[0-9a-f]{64}", item["executable_sha256"])
        assert type(item["codesign_exit_code"]) is int
assert all(set(item) == {"listener_id", "port", "cwd_within_canonical_pfi_root", "health_http_status"} for item in app_proof["listeners"])
assert app_proof["listener_count"] == len(app_proof["listeners"])

assert set(raw_proof) == {
    "schema", "phase_base", "observed_at", "root_states", "repository_surface",
    "raw_sources", "read_model", "privacy",
}
assert raw_proof["schema"] == "PFIV025Phase03RawDataProbeV1"
assert raw_proof["root_states"] == [
    {"root_id": "ROOT-01", "existence": "unset"},
    {"root_id": "ROOT-02", "existence": "absent"},
    {"root_id": "ROOT-03", "existence": "present"},
    {"root_id": "ROOT-04", "existence": "present"},
]
assert set(raw_proof["repository_surface"]) == {
    "surface_id", "tree_hash", "file_count", "bytes", "extension_counts",
}
assert all(set(item) == {
    "raw_source_id", "record_count", "date_range", "as_of", "bytes",
    "content_sha256", "permission_class", "source_path_redacted",
} for item in raw_proof["raw_sources"])
assert set(raw_proof["read_model"]) == {
    "storage_mode", "raw_file_count", "record_count", "date_range", "as_of",
    "evidence_hash", "read_model_hash", "metric_states", "blocked_metric_ids",
}
assert raw_proof["privacy"] == {
    "raw_filenames_emitted": 0, "raw_rows_emitted": 0, "financial_values_emitted": 0,
}

assert set(db_proof) == {
    "schema", "phase_base", "observed_at", "database_id", "before", "after",
    "query_mode", "query_only", "quick_check", "table_count",
    "aggregate_user_table_record_count", "database_path_redacted",
}
assert db_proof["schema"] == "PFIV025Phase03DatabaseProbeV1"
assert set(db_proof["before"]) == set(db_proof["after"]) == {
    "candidate_count", "bytes", "mtime_epoch", "permission_class", "content_sha256",
}

def canonical_json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def resolve_ref(ref: str) -> Path:
    if ref.startswith(".git/"):
        common = Path(subprocess.check_output(["git", "rev-parse", "--git-common-dir"], text=True).strip())
        return common / ref.removeprefix(".git/")
    return Path(ref)

for pinned_ref, pinned_sha in PINNED_HASHES.items():
    assert hashlib.sha256(resolve_ref(pinned_ref).read_bytes()).hexdigest() == pinned_sha
p02_attestation = json.loads(resolve_ref(next(ref for ref in PINNED_HASHES if ref.startswith(".git/"))).read_text(encoding="utf-8"))
assert p02_attestation["phase_commit"] == "7433be0d70bdae42959c1b71753d93f8737db60d"
assert p02_attestation["status"] == "resolved_by_approved_override"
assert p02_attestation["blocks_phase_0_2_candidate"] is False
assert p02_attestation["contains_private_values"] is False
active_requirements = json.loads(Path("PFI/config/pfi_v025_active_requirements.json").read_text(encoding="utf-8"))
assert active_requirements["schema"] == "PFIV025ActiveRequirementsV1"
assert active_requirements["version"] == "v0.2.5"
assert active_requirements["contract_id"] == "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS"
assert active_requirements["blocking_conflicts"]["blocks_claims"] == [
    "release_identity_unified", "v0.2.5_accepted", "final_delivery_ready",
]
assert active_requirements["blocking_conflicts"]["evidence_reference_required"] is True
assert active_requirements["blocking_conflicts"]["self_declared_unified_allowed"] is False
assert active_requirements["blocking_conflicts"]["unresolved_result"] == "blocked"
assert len(active_requirements["blocking_conflicts"]["items"]) == 7

def pointer_get(value, pointer: str):
    current = value
    if pointer == "":
        return current
    assert pointer.startswith("/")
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current

def artifact_payload(record: dict) -> bytes:
    if record["selector_type"] == "collection":
        members = record["member_hashes"]
        assert members and list(members) == sorted(members)
        chunks = []
        for path, digest in members.items():
            actual = hashlib.sha256(resolve_ref(path).read_bytes()).hexdigest()
            assert actual == digest
            chunks.append(path.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n")
        return b"".join(chunks)
    if record["selector_type"] == "composite":
        components = record["component_artifacts"]
        observed = []
        for component in components:
            raw = resolve_ref(component["artifact_ref"]).read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            assert digest == component["artifact_sha256"]
            observed.append({"artifact_ref": component["artifact_ref"], "artifact_sha256": digest})
        return canonical_json(observed)
    path = resolve_ref(record["artifact_ref"])
    if "zip_member" in record:
        with zipfile.ZipFile(path) as archive:
            return archive.read(record["zip_member"])
    return path.read_bytes()

def selector_payload(record: dict, artifact: bytes) -> bytes:
    selector_type = record["selector_type"]
    selector = record["selector"]
    if selector_type in {"whole_file", "collection"}:
        return artifact
    if selector_type == "composite":
        selected = []
        for item in record["component_selectors"]:
            raw = resolve_ref(item["artifact_ref"]).read_bytes()
            selected.append({
                "artifact_ref": item["artifact_ref"],
                "json_pointer": item["json_pointer"],
                "value": pointer_get(json.loads(raw), item["json_pointer"]),
            })
        return canonical_json(selected)
    if selector_type == "json_pointer":
        return canonical_json(pointer_get(json.loads(artifact), selector))
    text = artifact.decode("utf-8")
    if selector_type == "line_contains":
        lines = [line.strip() for line in text.splitlines() if selector in line]
        assert len(lines) == 1, (selector, len(lines))
        return (lines[0] + "\n").encode("utf-8")
    if selector_type == "markdown_table_id":
        lines = [line.strip() for line in text.splitlines() if line.strip().startswith(f"| {selector} |")]
        assert len(lines) == 1
        return (lines[0] + "\n").encode("utf-8")
    if selector_type == "markdown_table_row":
        prefix, raw_index = selector.split(":", 1)
        assert prefix == "facts_matrix"
        section = text[text.index("## 事实矩阵"):text.index("## 关键仓库事实")]
        rows = [line.strip() for line in section.splitlines() if line.startswith("|")][2:]
        return (rows[int(raw_index) - 1] + "\n").encode("utf-8")
    if selector_type == "markdown_section":
        number = int(selector.removeprefix("section:"))
        match = re.search(rf"^## {number}\. .*?(?=^## \d+\. |\Z)", text, re.M | re.S)
        assert match
        return (match.group(0).strip() + "\n").encode("utf-8")
    raise AssertionError(selector_type)

expected_paths = sorted([
    "PFI/CHANGELOG.md",
    "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
    "PFI/docs/governance/MODEL_SPEC.md",
    "PFI/docs/governance/OWNER_STATUS.md",
    "PFI/docs/governance/STATUS.md",
    "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
    "PFI/docs/governance/VERSION_MATRIX.yaml",
    "PFI/docs/governance/delivery_tasks.yaml",
    "PFI/docs/governance/development_events.jsonl",
    "PFI/docs/governance/formula_registry.yaml",
    "PFI/docs/governance/model_registry.yaml",
    "PFI/docs/governance/parameter_registry.csv",
    "PFI/docs/pfi_v025/stage_0/acceptance_request.md",
    "PFI/docs/pfi_v025/stage_0/finding_ledger.csv",
    "PFI/docs/pfi_v025/stage_0/gap_register.md",
    "PFI/reports/pfi_v025/stage_0/baseline.json",
    "PFI/reports/pfi_v025/stage_0/current_state_matrix.md",
    "PFI/reports/pfi_v025/stage_0/data_root_inventory.json",
    "PFI/reports/pfi_v025/stage_0/git_state.txt",
    "PFI/reports/pfi_v025/stage_0/history_deprecation.md",
    "PFI/reports/pfi_v025/stage_0/terminal.log",
    "PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt",
    "PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json",
    "PFI/reports/pfi_v025/stage_0/phase_0_3/risk_and_rollback.md",
    "PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log",
])
tracked_paths = subprocess.check_output(
    ["git", "diff", "--name-only", base], text=True
).splitlines()
untracked_paths = subprocess.check_output(
    ["git", "ls-files", "--others", "--exclude-standard"], text=True
).splitlines()
actual_paths = sorted(set(tracked_paths + untracked_paths))
assert actual_paths == expected_paths, (actual_paths, expected_paths)

header = [
    "finding_id", "source_ids", "history_item_ids", "domain", "summary",
    "current_status", "priority", "fact_level", "priority_basis",
    "prior_evidence_refs", "prior_evidence_as_of", "current_evidence_refs",
    "current_evidence_as_of", "current_evidence_result",
    "roadmap_resolution_tasks", "blocks_phase_0_3_candidate",
    "blocks_v025_production_acceptance", "rationale",
]
with Path("PFI/docs/pfi_v025/stage_0/finding_ledger.csv").open(
    encoding="utf-8", newline=""
) as stream:
    reader = csv.DictReader(stream)
    assert reader.fieldnames == header
    rows = list(reader)
assert [row["finding_id"] for row in rows] == [
    f"PFI-V025-FND-{index:03d}" for index in range(1, 39)
]
status_counts = Counter(row["current_status"] for row in rows)
assert status_counts == Counter({"StillPresent": 23, "Fixed": 7, "N/A": 3, "New": 5})
assert status_counts["Regressed"] == 0
assert Counter(row["priority"] for row in rows) == Counter({"P0": 26, "P1": 10, "P2": 2})
assert Counter(row["fact_level"] for row in rows) == Counter({"VERIFIED": 25, "EXTRACTED": 13})

design_table = design[
    design.index("Canonical 38-row crosswalk"):
    design.index("Exact source coverage maps")
]
frozen = {}
for line in design_table.splitlines():
    match = re.match(r"^\| FND-(\d{3}) \|", line)
    if not match:
        continue
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    assert len(cells) == 9
    status, priority = cells[4].rsplit(" / ", 1)
    fact_level, priority_basis = cells[5].rsplit(" / ", 1)
    current_refs, current_result = cells[6].rsplit(" / ", 1)
    frozen[match.group(1)] = {
        "summary": cells[1],
        "source_ids": cells[2],
        "history_item_ids": cells[3],
        "current_status": status,
        "priority": priority,
        "fact_level": fact_level,
        "priority_basis": priority_basis,
        "current_evidence_refs": current_refs,
        "current_evidence_result": current_result,
        "prior_evidence_refs": cells[7],
        "roadmap_resolution_tasks": cells[8],
    }
assert list(frozen) == [f"{index:03d}" for index in range(1, 39)]
for row in rows:
    expected = frozen[row["finding_id"][-3:]]
    for key, value in expected.items():
        assert row[key] == value, (row["finding_id"], key, row[key], value)
    for key in ("domain", "summary", "priority_basis", "fact_level", "current_evidence_as_of", "current_evidence_result", "roadmap_resolution_tasks", "rationale"):
        assert row[key].strip(), (row["finding_id"], key)

terminal_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log")
terminal_lines = terminal_path.read_text(encoding="utf-8").splitlines()
command_records = [json.loads(line.removeprefix("P03_COMMAND ")) for line in terminal_lines if line.startswith("P03_COMMAND ")]
outcome_records = [json.loads(line.removeprefix("P03_OUTCOMES ")) for line in terminal_lines if line.startswith("P03_OUTCOMES ")]
expected_command_ids = {"PRE-001", "SRC-001", "CUR-001", "APP-001", "DATA-001", "DB-001", "TEST-001", "TEST-002", "STRUCT-001", "GOV-001"}
assert {record["record_id"] for record in command_records} == expected_command_ids
assert len(command_records) == len(expected_command_ids) and len(outcome_records) == 1
terminal_commands = {record["record_id"]: record for record in command_records}
expected_command_summaries = {
    "PRE-001": "preflight_complete",
    "SRC-001": "source_registry_verified",
    "CUR-001": "current_facts_collected",
    "APP-001": "app_runtime_probe_bound",
    "DATA-001": "raw_data_probe_bound",
    "DB-001": "database_probe_bound",
    "TEST-001": "expected_3_pass_5_fail",
    "TEST-002": "795_tests_collected",
    "STRUCT-001": "structure_verified",
    "GOV-001": "governance_verified",
}
for record in command_records:
    allowed = {"record_id", "observed_at", "exit_code", "outcome", "summary"}
    if record["record_id"] in {"APP-001", "DATA-001", "DB-001"}:
        allowed |= {"proof_id", "proof_sha256"}
    assert set(record) == allowed
    assert record["observed_at"] == run_state["observed_at"]
    assert type(record["exit_code"]) is int and record["outcome"] and record["summary"]
    assert record["summary"] == expected_command_summaries[record["record_id"]]
    assert record["outcome"] == ("expected_diagnostic_failure" if record["record_id"] == "TEST-001" else "pass")
proof_binding = {
    "APP-001": ("app_runtime_probe", run_state["app_runtime_probe_sha256"]),
    "DATA-001": ("raw_data_probe", run_state["raw_data_probe_sha256"]),
    "DB-001": ("db_probe", run_state["db_probe_sha256"]),
}
for record_id, (proof_id, digest) in proof_binding.items():
    assert terminal_commands[record_id]["proof_id"] == proof_id
    assert terminal_commands[record_id]["proof_sha256"] == digest
terminal_outcome_record = outcome_records[0]
assert set(terminal_outcome_record) == {"record_id", "observed_at", "finding_outcomes"}
assert terminal_outcome_record["record_id"] == "P03-OUTCOMES"
assert terminal_outcome_record["observed_at"] == run_state["observed_at"]

source_tokens = []
history_tokens = []
evidence_tokens = set()
priority_tokens = set()
for row in rows:
    sources = row["source_ids"].split(";")
    source_tokens.extend(sources)
    history_tokens.extend(
        token for token in row["history_item_ids"].split(";")
        if token != "NOT_APPLICABLE"
    )
    for field in ("prior_evidence_refs", "current_evidence_refs"):
        evidence_tokens.update(
            token for token in row[field].split(";") if token != "NOT_APPLICABLE"
        )
    priority_tokens.add(row["priority_basis"])
    tasks = row["roadmap_resolution_tasks"].split(";")
    assert tasks and set(tasks) <= valid_tasks
    assert ".." not in row["roadmap_resolution_tasks"]
    assert row["blocks_phase_0_3_candidate"] == "false"
    is_open = row["current_status"] in {"StillPresent", "Regressed", "New"}
    assert (row["blocks_v025_production_acceptance"] == "true") is is_open
    result = row["current_evidence_result"]
    if row["current_status"] == "Fixed":
        assert result.startswith("fixed_within_")
        assert "scope_limit=" in row["rationale"]
    elif row["current_status"] == "N/A":
        assert result == "superseded_or_non_applicable"
        assert "non_gap_reason=" in row["rationale"]
    elif row["current_status"] == "New":
        assert result == "new_current_fact"
        assert row["prior_evidence_refs"] == "NOT_APPLICABLE"
        assert row["prior_evidence_as_of"] == "NOT_APPLICABLE"
        assert "source_universe_non_match=" in row["rationale"]
    elif row["current_status"] == "StillPresent":
        assert result in {"reproduced", "required_production_proof_missing"}
    else:
        assert result == "fresh_failure"
        assert datetime.fromisoformat(row["prior_evidence_as_of"]) < datetime.fromisoformat(row["current_evidence_as_of"])
assert sum(len(row["roadmap_resolution_tasks"].split(";")) for row in rows) == 114

for prefix, count in (("R-", 15), ("SUR-", 12), ("AUD-", 15), ("P01-RISK-", 10), ("P02-RISK-", 5)):
    observed = Counter(token for token in source_tokens if token.startswith(prefix))
    assert observed == Counter({f"{prefix}{index:02d}": 1 for index in range(1, count + 1)})
assert len(source_tokens) == len(set(source_tokens)) == 71
row_by_id = {row["finding_id"]: row for row in rows}
assert "AUD-15" in row_by_id["PFI-V025-FND-023"]["source_ids"].split(";")
assert [row["finding_id"] for row in rows if row["current_status"] == "New"] == [
    "PFI-V025-FND-005", "PFI-V025-FND-006", "PFI-V025-FND-007",
    "PFI-V025-FND-030", "PFI-V025-FND-031",
]
p03_rows = [row for row in rows if "P03_TERM" in row["current_evidence_refs"].split(";")]
terminal_outcomes = terminal_outcome_record["finding_outcomes"]
assert set(terminal_outcomes) == {row["finding_id"] for row in p03_rows}
missing_proof_ids = {f"PFI-V025-FND-{value}" for value in ("011", "014", "016", "018", "023", "024", "025", "029")}
for row in p03_rows:
    observed = terminal_outcomes[row["finding_id"]]
    if row["finding_id"] in missing_proof_ids:
        assert observed in {"not_run_by_phase_contract", "blocked_missing_required_proof"}
        assert row["current_evidence_result"] == "required_production_proof_missing"
    else:
        assert observed == row["current_evidence_result"]

history = Path("PFI/docs/pfi_v025/stage_0/history_deprecation.md").read_text(encoding="utf-8")
canonical_history = re.findall(
    r"^\| ((?:HIST|ARCH|REF|OVERRIDE)-[A-Z0-9-]+) \|", history, re.M
)
assert len(history_tokens) == len(set(history_tokens)) == 21
assert set(history_tokens) == set(canonical_history)

gap_text = Path("PFI/docs/pfi_v025/stage_0/gap_register.md").read_text(encoding="utf-8")
gap_pairs = re.findall(r"^(GAP-P[01]-\d{2}) = ([^\n]+)$", gap_text, re.M)
gap_map = {
    gap_id: {int(value) for value in re.findall(r"FND-(\d{3})", values)}
    for gap_id, values in gap_pairs
}
assert len(gap_map) == 13
design_gap_block = design[
    design.index("GAP-P0-01 ="):
    design.index("排序规则：", design.index("GAP-P0-01 ="))
]
frozen_gap_map = {
    gap_id: {int(value) for value in re.findall(r"FND-(\d{3})", values)}
    for gap_id, values in re.findall(r"^(GAP-P[01]-\d{2}) = ([^\n]+)$", design_gap_block, re.M)
}
assert gap_map == frozen_gap_map
flat = [finding for values in gap_map.values() for finding in values]
eligible = {
    int(row["finding_id"][-3:]) for row in rows
    if row["current_status"] in {"StillPresent", "Regressed", "New"}
}
assert len(flat) == len(set(flat)) == 28 and set(flat) == eligible
non_gap_line = re.search(r"^NON_GAP = ([^\n]+)$", gap_text, re.M)
assert non_gap_line
non_gap = {int(value) for value in re.findall(r"FND-(\d{3})", non_gap_line.group(1))}
assert non_gap == set(range(1, 39)) - eligible
row_lookup = {int(row["finding_id"][-3:]): row for row in rows}
non_gap_section = re.search(
    r"^## Non-gap dispositions\n(.*?)(?=^## |^### GAP-|\Z)", gap_text, re.M | re.S
)
assert non_gap_section
table_lines = [line.strip() for line in non_gap_section.group(1).splitlines() if line.strip().startswith("|")]
assert table_lines[:2] == [
    "| finding_id | status | priority | disposition | rationale_marker |",
    "|---|---|---|---|---|",
]
non_gap_rows = []
for line in table_lines[2:]:
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    assert len(cells) == 5
    non_gap_rows.append(dict(zip(
        ("finding_id", "status", "priority", "disposition", "rationale_marker"), cells
    )))
assert [row["finding_id"] for row in non_gap_rows] == [f"FND-{value:03d}" for value in sorted(non_gap)]
for disposition in non_gap_rows:
    ledger_row = row_lookup[int(disposition["finding_id"][-3:])]
    assert disposition["status"] == ledger_row["current_status"]
    assert disposition["priority"] == ledger_row["priority"]
    assert disposition["disposition"] == "non_gap"
    expected_prefix = "scope_limit=" if ledger_row["current_status"] == "Fixed" else "non_gap_reason="
    assert disposition["rationale_marker"].startswith(expected_prefix)
    assert disposition["rationale_marker"] in ledger_row["rationale"]
assert "executable_p2_count: 0" in gap_text
for gap_id, members in gap_map.items():
    expected_priority = gap_id.split("-")[1]
    assert {row_lookup[member]["priority"] for member in members} == {expected_priority}
    section = re.search(
        rf"^### {re.escape(gap_id)}\n(.*?)(?=^### GAP-|\Z)", gap_text, re.M | re.S
    )
    assert section, gap_id
    fields = dict(re.findall(r"^- ([a-z_]+): (.+)$", section.group(1), re.M))
    required_fields = {
        "gap_id", "priority", "linked_finding_ids", "current_state", "target_state",
        "roadmap_resolution_tasks", "dependencies", "required_acceptance_evidence",
        "stop_condition", "status",
    }
    assert set(fields) == required_fields, (gap_id, fields)
    assert fields["gap_id"] == gap_id and fields["priority"] == expected_priority
    assert fields["status"] == "open"
    assert {int(value) for value in re.findall(r"FND-(\d{3})", fields["linked_finding_ids"])} == members
    expected_tasks = {
        task for member in members
        for task in row_lookup[member]["roadmap_resolution_tasks"].split(";")
    }
    assert set(fields["roadmap_resolution_tasks"].split(";")) == expected_tasks
    for key in ("current_state", "target_state", "dependencies", "required_acceptance_evidence", "stop_condition"):
        assert fields[key].strip() and fields[key] != "NOT_APPLICABLE"

data = json.loads(Path("PFI/reports/pfi_v025/stage_0/data_root_inventory.json").read_text(encoding="utf-8"))
assert set(data) == {
    "schema", "version", "stage", "candidate_roots", "repository_object_surfaces",
    "raw_sources", "databases", "read_model", "privacy",
}
assert data["schema"] == "PFIV025Stage0DataRootInventoryV1"
assert data["version"] == "v0.2.5" and data["stage"] == 0
candidate_keys = {
    "root_id", "order", "symbolic_path", "existence", "status", "permission_class",
    "file_count", "record_count", "date_range", "as_of", "aggregate_sha256",
    "source_evidence_ref", "source_evidence_sha256",
}
surface_keys = {
    "surface_id", "related_root_id", "git_commit", "tree_hash", "file_count", "bytes",
    "extension_counts", "permission_class", "source_evidence_ref", "source_evidence_sha256",
}
raw_keys = {
    "raw_source_id", "source_surface_id", "source_class", "storage_mode", "status",
    "record_count", "date_range", "as_of", "bytes", "content_sha256", "permission_class",
    "source_path_redacted",
}
database_keys = {
    "database_id", "root_id", "status", "candidate_count", "bytes", "mtime_epoch",
    "permission_class", "content_sha256", "record_count", "date_range", "as_of",
    "query_mode", "query_only", "quick_check", "table_count", "unchanged_before_after",
    "database_path_redacted", "before", "after", "source_evidence_ref", "source_evidence_sha256",
}
read_model_keys = {
    "storage_mode", "raw_file_count", "record_count", "date_range", "as_of",
    "evidence_hash", "read_model_hash", "metric_states", "blocked_metric_ids",
}
assert all(set(item) == candidate_keys for item in data["candidate_roots"])
assert all(set(item) == surface_keys for item in data["repository_object_surfaces"])
assert all(set(item) == raw_keys for item in data["raw_sources"])
assert all(set(item) == database_keys for item in data["databases"])
assert set(data["read_model"]) == read_model_keys
assert [(item["order"], item["root_id"], item["symbolic_path"], item["existence"]) for item in data["candidate_roots"]] == [
    (1, "ROOT-01", "env:PFI_DATA_HOME", "unset"),
    (2, "ROOT-02", "repo-worktree:MetaDatabase/PFI", "absent"),
    (3, "ROOT-03", "repo-worktree:PFI/MetaDatabase", "present"),
    (4, "ROOT-04", "user-state:~/.pfi", "present"),
]
assert all(item["status"] in {"ready", "source_missing", "metadata_only", "blocked"} for item in data["candidate_roots"])
for root_item, proof_item in zip(data["candidate_roots"], raw_proof["root_states"]):
    assert root_item["root_id"] == proof_item["root_id"] and root_item["existence"] == proof_item["existence"]
    assert root_item["source_evidence_ref"] == "guard:raw_data_probe.json"
    assert root_item["source_evidence_sha256"] == run_state["raw_data_probe_sha256"]
assert [item["surface_id"] for item in data["repository_object_surfaces"]] == ["GIT-DATA-01"]
assert [item["raw_source_id"] for item in data["raw_sources"]] == ["RAW-01", "RAW-02", "RAW-03", "RAW-04"]
assert [item["database_id"] for item in data["databases"]] == ["DB-01"]
measurement_fields = {
    "candidate_roots": ["permission_class", "file_count", "record_count", "date_range", "as_of", "aggregate_sha256"],
    "raw_sources": ["record_count", "date_range", "as_of", "bytes", "content_sha256", "permission_class"],
    "databases": ["candidate_count", "bytes", "mtime_epoch", "permission_class", "content_sha256", "record_count", "date_range", "as_of"],
}

def validate_measurement(value: dict) -> None:
    assert set(value) in (
        {"state", "value_type", "value"},
        {"state", "value_type", "reason", "resolution_tasks"},
    )
    assert value["state"] in {"present", "metadata_unavailable", "not_applicable"}
    assert value["value_type"] in {"integer", "epoch_integer", "date", "date_range", "sha256", "permission", "string_enum"}
    if value["state"] != "present":
        assert "value" not in value
        assert value.get("reason") and value.get("resolution_tasks")
        assert set(value["resolution_tasks"]) <= valid_tasks
        return
    assert "value" in value and "reason" not in value and "resolution_tasks" not in value
    actual = value["value"]
    if value["value_type"] in {"integer", "epoch_integer"}:
        assert type(actual) is int and actual >= 0
    elif value["value_type"] == "date":
        datetime.strptime(actual, "%Y-%m-%d")
    elif value["value_type"] == "date_range":
        assert set(actual) == {"start", "end"}
        start = datetime.strptime(actual["start"], "%Y-%m-%d")
        end = datetime.strptime(actual["end"], "%Y-%m-%d")
        assert start <= end
    elif value["value_type"] == "sha256":
        assert isinstance(actual, str) and re.fullmatch(r"[0-9a-f]{64}", actual)
    elif value["value_type"] == "permission":
        assert actual in {"readable_no_write_attempt", "not_readable", "git_object_readable"}
    else:
        assert isinstance(actual, str) and actual

for collection, fields in measurement_fields.items():
    for item in data[collection]:
        for field in fields:
            validate_measurement(item[field])

surface = data["repository_object_surfaces"][0]
assert surface["related_root_id"] == "ROOT-02" and surface["git_commit"] == base
assert surface["file_count"] == 6 and surface["bytes"] == 3870013
assert surface["extension_counts"] == {"csv": 5, "json": 1, "sqlite": 0}
assert surface["source_evidence_ref"] == "guard:raw_data_probe.json"
assert surface["source_evidence_sha256"] == run_state["raw_data_probe_sha256"]
for key in ("surface_id", "tree_hash", "file_count", "bytes", "extension_counts"):
    assert surface[key] == raw_proof["repository_surface"][key]
expected_tree_hash = subprocess.check_output(
    ["git", "rev-parse", f"{base}:MetaDatabase/PFI"],
    text=True,
    env={**dict(__import__("os").environ), "GIT_NO_LAZY_FETCH": "1"},
).strip()
assert surface["tree_hash"] == expected_tree_hash and re.fullmatch(r"[0-9a-f]{40}", expected_tree_hash)
for raw, proof_raw in zip(data["raw_sources"], raw_proof["raw_sources"]):
    assert raw["source_surface_id"] == "GIT-DATA-01"
    assert raw["storage_mode"] == "git_tree_object" and raw["status"] == "ready"
    assert raw["source_path_redacted"] is True
    assert raw["raw_source_id"] == proof_raw["raw_source_id"]
    for key in ("record_count", "date_range", "as_of", "bytes", "content_sha256", "permission_class"):
        assert raw[key] == {"state": "present", "value_type": {
            "record_count": "integer", "date_range": "date_range", "as_of": "date",
            "bytes": "integer", "content_sha256": "sha256", "permission_class": "permission",
        }[key], "value": proof_raw[key]}

db = data["databases"][0]
assert db["root_id"] == "ROOT-04" and db["status"] == "ready"
assert db["query_mode"] == "ro&immutable=1" and db["query_only"] is True
assert db["quick_check"] == "ok" and type(db["table_count"]) is int and db["table_count"] >= 0
assert db["candidate_count"] == {"state": "present", "value_type": "integer", "value": 1}
assert db["database_path_redacted"] is True
assert db["source_evidence_ref"] == "guard:db_probe.json"
assert db["source_evidence_sha256"] == run_state["db_probe_sha256"]
assert db["before"] == db["after"]
for key in ("candidate_count", "bytes", "mtime_epoch", "permission_class", "content_sha256"):
    assert db["before"][key] == db[key]
assert db["unchanged_before_after"] is True
db_type = {
    "candidate_count": "integer", "bytes": "integer", "mtime_epoch": "epoch_integer",
    "permission_class": "permission", "content_sha256": "sha256",
}
assert set(db["before"]) == set(db_type) == set(db["after"])
for key, value_type in db_type.items():
    expected = {"state": "present", "value_type": value_type, "value": db_proof["before"][key]}
    assert db["before"][key] == expected
assert db_proof["before"] == db_proof["after"]
assert db["record_count"] == {
    "state": "present", "value_type": "integer",
    "value": db_proof["aggregate_user_table_record_count"],
}
for field, value_type in (("date_range", "date_range"), ("as_of", "date")):
    assert db[field] == {
        "state": "metadata_unavailable",
        "value_type": value_type,
        "reason": "not_exposed_by_phase_0_3_query_only_probe",
        "resolution_tasks": ["S2-P1-T3"],
    }
assert db["table_count"] == db_proof["table_count"]
assert db["quick_check"] == db_proof["quick_check"]

read_model = data["read_model"]
assert read_model == raw_proof["read_model"]
assert read_model["storage_mode"] == "git_tree" and read_model["raw_file_count"] == 4
assert read_model["record_count"] == 8815
assert read_model["date_range"] == {"start": "2022-06-06", "end": "2026-06-03"}
assert read_model["as_of"] == "2026-06-03"
assert re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", read_model["evidence_hash"])
assert re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", read_model["read_model_hash"])
assert set(read_model["blocked_metric_ids"]) == {"net_worth_cny", "cash_balance_cny", "investment_market_value_cny"}
assert read_model["metric_states"] == {
    "cash_balance_cny": "source_missing",
    "consumption_outflow_cny": "ready",
    "investment_market_value_cny": "source_missing",
    "net_worth_cny": "source_missing",
    "report_summary_status": "ready",
}
assert data["privacy"] == {
    "contains_private_values": False,
    "raw_filenames_emitted": 0,
    "raw_rows_emitted": 0,
    "financial_values_emitted": 0,
    "credentials_emitted": 0,
    "absolute_private_paths_emitted": 0,
}
assert "/Users/" not in json.dumps(data, ensure_ascii=False)

evidence_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json")
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
assert evidence["version"] == "v0.2.5" and evidence["stage"] == 0 and evidence["phase"] == "0.3"
assert evidence["status"] == "candidate_pass" and evidence["git_commit"] == base
assert evidence["git_commit_semantics"] == "implementation_base_before_phase_commit"
assert evidence["allowed_files_obeyed"] is True
assert evidence["requires_user_acceptance"] is True and evidence["contains_private_values"] is False
assert evidence["stage_0_whole_review_status"] == "not_started" and evidence["stage_1_status"] == "not_started"
assert sorted(evidence["changed_files"]) == expected_paths
assert [(task["task_id"], task["status"]) for task in evidence["tasks"]] == [
    ("S0-P3-T1", "candidate_pass"),
    ("S0-P3-T2", "candidate_pass"),
    ("S0-P3-T3", "candidate_pass"),
    ("S0-P3-T4", "candidate_pass"),
]
commands = {command["command_id"]: command for command in evidence["commands"]}
assert set(commands) == {"PRE-001", "SRC-001", "CUR-001", "APP-001", "DATA-001", "DB-001", "TEST-001", "TEST-002", "STRUCT-001", "GOV-001"}
assert len(commands) == len(evidence["commands"])
for command_id, command in commands.items():
    allowed_command_keys = {"command_id", "command", "exit_code", "summary"}
    if command_id == "TEST-001":
        allowed_command_keys.add("expected_diagnostic")
    if command_id in {"APP-001", "DATA-001", "DB-001"}:
        allowed_command_keys |= {"proof_id", "proof_sha256"}
    assert set(command) == allowed_command_keys
    assert type(command["exit_code"]) is int and command["command"] and command["summary"]
    assert command["exit_code"] == (1 if command_id == "TEST-001" else 0)
    assert command["summary"] == expected_command_summaries[command_id]
assert commands["TEST-001"]["expected_diagnostic"] == {"passed": 3, "failed": 5}
for command_id, (proof_id, digest) in proof_binding.items():
    assert commands[command_id]["proof_id"] == proof_id
    assert commands[command_id]["proof_sha256"] == digest
assert set(evidence["source_registry"]) == set(source_tokens)
assert set(evidence["evidence_registry"]) == evidence_tokens
assert set(evidence["priority_registry"]) == priority_tokens
registry_required = {
    "artifact_ref", "artifact_sha256", "selector", "selector_type",
    "source_text_sha256", "observed_at", "fact_level",
}
for registry_name in ("source_registry", "evidence_registry", "priority_registry"):
    for registry_id, record in evidence[registry_name].items():
        allowed_keys = set(registry_required)
        if "zip_member" in record:
            allowed_keys.add("zip_member")
        if record["selector_type"] == "collection":
            allowed_keys.add("member_hashes")
        if record["selector_type"] == "composite":
            allowed_keys |= {"component_artifacts", "component_selectors"}
        if registry_name == "evidence_registry" and registry_id == "P03_TERM":
            allowed_keys.add("outcomes")
        if registry_name == "priority_registry":
            allowed_keys.add("priority")
        assert set(record) == allowed_keys, (registry_name, registry_id, set(record), allowed_keys)
        observed_at = datetime.fromisoformat(record["observed_at"].replace("Z", "+00:00"))
        assert observed_at.tzinfo is not None and observed_at.utcoffset() is not None
        artifact = artifact_payload(record)
        assert hashlib.sha256(artifact).hexdigest() == record["artifact_sha256"]
        selected = selector_payload(record, artifact)
        assert hashlib.sha256(selected).hexdigest() == record["source_text_sha256"]
        assert record["fact_level"] in {"VERIFIED", "EXTRACTED", "RECONSTRUCTED", "INFERRED"}
for source_id, record in evidence["source_registry"].items():
    if source_id.startswith(("R-", "SUR-", "AUD-")):
        assert record["artifact_ref"] == "/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
    if re.fullmatch(r"R-\d{2}", source_id):
        assert record["selector_type"] == "markdown_table_id" and record["selector"] == source_id
        assert record["zip_member"] == "PFI_v0.2.5_TaskPack/docs/RISK_REGISTER.md"
    elif re.fullmatch(r"SUR-\d{2}", source_id):
        assert record["selector_type"] == "markdown_section"
        assert record["selector"] == f"section:{int(source_id[-2:])}"
        assert record["zip_member"] == "PFI_v0.2.5_TaskPack/docs/SURPRISE_FINDINGS_AND_DESIGN_DECISIONS.md"
    elif re.fullmatch(r"AUD-\d{2}", source_id):
        assert record["selector_type"] == "markdown_table_row"
        assert record["selector"] == f"facts_matrix:{int(source_id[-2:])}"
        assert record["zip_member"] == "PFI_v0.2.5_TaskPack/docs/CURRENT_GITHUB_AUDIT_2026-07-10.md"
    elif re.fullmatch(r"P0[12]-RISK-\d{2}", source_id):
        assert record["selector_type"] == "json_pointer"
        assert record["selector"] == f"/risks/{int(source_id[-2:]) - 1}"
        expected_ref = "PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json" if source_id.startswith("P01-") else "PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json"
        assert record["artifact_ref"] == expected_ref
    elif source_id.startswith("P01-CONFLICT:"):
        assert record["selector_type"] == "json_pointer"
        assert record["artifact_ref"] == "PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json"
        selected = pointer_get(json.loads(artifact_payload(record)), record["selector"])
        assert selected["id"] == source_id.split(":", 1)[1]
    elif source_id.startswith("PFI-V025-CONFLICT-"):
        assert record["selector_type"] == "json_pointer"
        assert record["artifact_ref"] == "PFI/config/pfi_v025_active_requirements.json"
        selected = pointer_get(json.loads(artifact_payload(record)), record["selector"])
        assert selected["conflict_id"] == source_id
    else:
        assert source_id == "P02-LIFECYCLE-COMPARISON" and record["selector_type"] == "composite"
        p02_evidence_ref = "PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json"
        p02_attest_ref = ".git/codex-review/pfi-v025/stage_0/phase_0_2/7433be0d70bdae42959c1b71753d93f8737db60d.attempt.id9uiuo8/phase_0_2_attestation.json"
        assert record["artifact_ref"] == "composite:P02-LIFECYCLE-COMPARISON"
        assert record["selector"] == "phase_0_2_lifecycle"
        assert record["component_artifacts"] == [
            {"artifact_ref": p02_evidence_ref, "artifact_sha256": PINNED_HASHES.get(p02_evidence_ref, hashlib.sha256(Path(p02_evidence_ref).read_bytes()).hexdigest())},
            {"artifact_ref": p02_attest_ref, "artifact_sha256": PINNED_HASHES[p02_attest_ref]},
        ]
        assert record["component_selectors"] == [
            {"artifact_ref": p02_evidence_ref, "json_pointer": "/governance_override_state"},
            {"artifact_ref": p02_attest_ref, "json_pointer": "/status"},
            {"artifact_ref": p02_attest_ref, "json_pointer": "/blocks_phase_0_2_candidate"},
        ]

def producing_commit_time(path: str) -> str:
    value = subprocess.check_output(
        ["git", "log", "-1", "--format=%cI", base, "--", path], text=True
    ).strip()
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None and parsed.utcoffset() is not None
    return value

taskpack_ref = "/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
p02_attest_ref = ".git/codex-review/pfi-v025/stage_0/phase_0_2/7433be0d70bdae42959c1b71753d93f8737db60d.attempt.id9uiuo8/phase_0_2_attestation.json"
p02_attested_at = p02_attestation["independently_validated_at"]
datetime.fromisoformat(p02_attested_at.replace("Z", "+00:00"))

# Source observation time is either the fresh batch verification time or the
# exact producing commit / attestation time; filesystem mtime is never accepted.
for source_id, record in evidence["source_registry"].items():
    if source_id.startswith(("R-", "SUR-", "AUD-")):
        expected_observed_at = run_state["observed_at"]
    elif source_id.startswith("P01-"):
        historical_path = (
            "PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json"
            if source_id.startswith("P01-CONFLICT:")
            else "PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json"
        )
        expected_observed_at = producing_commit_time(historical_path)
    elif source_id.startswith("P02-RISK-"):
        expected_observed_at = producing_commit_time("PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json")
    elif source_id.startswith("PFI-V025-CONFLICT-"):
        expected_observed_at = producing_commit_time("PFI/config/pfi_v025_active_requirements.json")
    else:
        assert source_id == "P02-LIFECYCLE-COMPARISON"
        expected_observed_at = p02_attested_at
    assert record["observed_at"] == expected_observed_at, source_id

owner_members = [
    "PFI/HANDOFF.md", "PFI/README.md", "PFI/VERSION", "PFI/功能清单.md",
    "PFI/开发记录.md", "PFI/模型参数文件.md",
]
web_members = [
    "PFI/web/app/routes.js", "PFI/web/app/shell.js",
    "PFI/web/app/version.js", "PFI/web/index.html",
]
evidence_contract = {
    "CURRENT_OWNER": ("collection:CURRENT_OWNER", "collection", "ordered_members"),
    "CURRENT_RUNTIME_APP": ("PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log", "line_contains", '\"record_id\":\"APP-001\"'),
    "CURRENT_WEB": ("collection:CURRENT_WEB", "collection", "ordered_members"),
    "P01_ENTRY": ("PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json", "whole_file", "whole_file"),
    "P01_EVID": ("PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json", "whole_file", "whole_file"),
    "P01_REPO": ("PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json", "whole_file", "whole_file"),
    "P01_RISK": ("PFI/reports/pfi_v025/stage_0/phase_0_1/risk_and_rollback.md", "whole_file", "whole_file"),
    "P02_ACTIVE": ("PFI/config/pfi_v025_active_requirements.json", "whole_file", "whole_file"),
    "P02_ATTEST": (p02_attest_ref, "whole_file", "whole_file"),
    "P02_EVID": ("PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json", "whole_file", "whole_file"),
    "P03_TERM": ("PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log", "whole_file", "whole_file"),
    "PFI/docs/pfi_v025/stage_0/scope_boundary.md": ("PFI/docs/pfi_v025/stage_0/scope_boundary.md", "whole_file", "whole_file"),
    "PFI/src/pfi_os/application/read_model_status.py": ("PFI/src/pfi_os/application/read_model_status.py", "whole_file", "whole_file"),
    "PFI/web/app/pages/reports.js": ("PFI/web/app/pages/reports.js", "whole_file", "whole_file"),
}
assert set(evidence_contract) == set(evidence["evidence_registry"])
fresh_evidence_ids = {"CURRENT_OWNER", "CURRENT_RUNTIME_APP", "CURRENT_WEB", "P03_TERM"}
for evidence_id, expected_contract in evidence_contract.items():
    record = evidence["evidence_registry"][evidence_id]
    assert (record["artifact_ref"], record["selector_type"], record["selector"]) == expected_contract
    if evidence_id == "CURRENT_OWNER":
        assert list(record["member_hashes"]) == owner_members
    if evidence_id == "CURRENT_WEB":
        assert list(record["member_hashes"]) == web_members
    if evidence_id in fresh_evidence_ids:
        expected_observed_at = run_state["observed_at"]
    elif evidence_id == "P02_ATTEST":
        expected_observed_at = p02_attested_at
    else:
        expected_observed_at = producing_commit_time(record["artifact_ref"])
    assert record["observed_at"] == expected_observed_at, evidence_id

audit_member = "PFI_v0.2.5_TaskPack/docs/CURRENT_GITHUB_AUDIT_2026-07-10.md"
risk_member = "PFI_v0.2.5_TaskPack/docs/RISK_REGISTER.md"
audit_selectors = {
    "AUDIT-P0-APP": "真实 App 重装与四方版本 identity。",
    "AUDIT-P0-DATA": "真实数据根目录与账户/持仓 Read Model。",
    "AUDIT-P0-METRIC": "非假零、真实财务指标和 SQLite 持久化。",
    "AUDIT-P0-OWNER": "状态真相统一。",
    "AUDIT-P0-PRODUCTION": "whole_file",
    "AUDIT-P0-ROUTE": "真实路由、差异化页面、三个核心工作流。",
    "AUDIT-P1-FORMULA": "公式注册表、双消费、FX、Interconnection、模型验证和报告同源。",
}
priority_contract = {
    **{
        f"R-{index:02d}": (taskpack_ref, "markdown_table_id", f"R-{index:02d}", risk_member)
        for index in range(1, 16)
    },
    **{
        key: (taskpack_ref, "whole_file" if selector == "whole_file" else "line_contains", selector, audit_member)
        for key, selector in audit_selectors.items()
    },
    "SUBFINDING-FND-003-P1": ("PFI/docs/pfi_v025/stage_0/PHASE_0_3_DESIGN.md", "markdown_table_id", "FND-030", None),
    "SUBFINDING-FND-029-P1": ("PFI/docs/pfi_v025/stage_0/PHASE_0_3_DESIGN.md", "markdown_table_id", "FND-032", None),
    "PHASE-GATE-P0": ("PFI/docs/pfi_v025/stage_0/PHASE_0_3_DESIGN.md", "markdown_table_id", "FND-034", None),
    "PHASE-GATE-P1": ("PFI/docs/pfi_v025/stage_0/PHASE_0_3_DESIGN.md", "markdown_table_id", "FND-033", None),
    "DIAGNOSTIC-P2": ("PFI/docs/pfi_v025/stage_0/PHASE_0_3_DESIGN.md", "markdown_table_id", "FND-036", None),
}
assert set(priority_contract) == set(evidence["priority_registry"])
for priority_id, (artifact_ref, selector_type, selector, zip_member) in priority_contract.items():
    record = evidence["priority_registry"][priority_id]
    assert (record["artifact_ref"], record["selector_type"], record["selector"]) == (artifact_ref, selector_type, selector)
    assert record.get("zip_member") == zip_member
    expected_observed_at = (
        run_state["observed_at"] if artifact_ref == taskpack_ref
        else producing_commit_time(artifact_ref)
    )
    assert record["observed_at"] == expected_observed_at, priority_id
    selected_text = selector_payload(record, artifact_payload(record)).decode("utf-8").strip()
    if re.fullmatch(r"R-\d{2}", priority_id):
        cells = [cell.strip() for cell in selected_text.strip("|").split("|")]
        assert len(cells) == 4 and cells[0] == priority_id
        source_priority = cells[2]
    elif priority_id.startswith("AUDIT-"):
        audit_text = artifact_payload(record).decode("utf-8")
        if priority_id == "AUDIT-P0-PRODUCTION":
            p0_section = audit_text[audit_text.index("### P0"):audit_text.index("### P1")]
            production_markers = {
                "真实 App 重装与四方版本 identity。",
                "真实数据根目录与账户/持仓 Read Model。",
                "非假零、真实财务指标和 SQLite 持久化。",
                "真实路由、差异化页面、三个核心工作流。",
                "状态真相统一。",
            }
            assert "`BLOCKED_FOR_V025_PRODUCTION_ACCEPTANCE`" in audit_text
            assert all(f"- {marker}" in p0_section for marker in production_markers)
            source_priority = "P0"
        elif priority_id == "AUDIT-P1-FORMULA":
            source_priority = "P1"
            p1_section = audit_text[audit_text.index("### P1"):audit_text.index("### P2")]
            assert record["selector"] in p1_section
        else:
            source_priority = "P0"
            p0_section = audit_text[audit_text.index("### P0"):audit_text.index("### P1")]
            assert record["selector"] in p0_section
    else:
        cells = [cell.strip() for cell in selected_text.strip("|").split("|")]
        assert len(cells) == 9
        source_priority = cells[4].rsplit(" / ", 1)[1]
    assert record["priority"] == source_priority, priority_id
for row in rows:
    assert evidence["priority_registry"][row["priority_basis"]]["priority"] == row["priority"]

p03_outcomes = evidence["evidence_registry"]["P03_TERM"]["outcomes"]
assert p03_outcomes == terminal_outcomes
for finding_id in ("011", "014", "016", "018", "023", "024", "025", "029"):
    row = row_by_id[f"PFI-V025-FND-{finding_id}"]
    assert "P03_TERM" in row["current_evidence_refs"].split(";")
    assert row["current_evidence_result"] == "required_production_proof_missing"
    assert p03_outcomes[f"PFI-V025-FND-{finding_id}"] in {
        "not_run_by_phase_contract", "blocked_missing_required_proof",
    }

def base_blob(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{base}:{path}"])

append_only_yaml = {
    "model": "PFI/docs/governance/model_registry.yaml",
    "formula": "PFI/docs/governance/formula_registry.yaml",
    "delivery": "PFI/docs/governance/delivery_tasks.yaml",
}
for path in append_only_yaml.values():
    assert Path(path).read_bytes().startswith(base_blob(path)), path
for path in (
    "PFI/CHANGELOG.md",
    "PFI/docs/governance/MODEL_SPEC.md",
    "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
    "PFI/docs/governance/OWNER_STATUS.md",
    "PFI/docs/governance/STATUS.md",
    "PFI/docs/governance/VERSION_MATRIX.yaml",
):
    current = Path(path).read_bytes()
    before = base_blob(path)
    assert current.startswith(before), path
    assert current[len(before):].decode("utf-8").count("ITER-20260711-PFI-V025-S0-P03") == 1
model_text = Path(append_only_yaml["model"]).read_text(encoding="utf-8")
formula_text = Path(append_only_yaml["formula"]).read_text(encoding="utf-8")
delivery_text = Path(append_only_yaml["delivery"]).read_text(encoding="utf-8")
assert len(re.findall(r"^\s*- model_id:", model_text, re.M)) == 1
assert len(re.findall(r"^\s*- assumption_id:", model_text, re.M)) == 2
assert len(re.findall(r"^\s*- formula_id:", formula_text, re.M)) == 1
assert len(re.findall(r"^\s*- task_id:", delivery_text, re.M)) == 10
for text in (model_text, formula_text, delivery_text):
    assert text.count("ITER-20260711-PFI-V025-S0-P03") == 1
    assert "model_ids_changed: []" in text and "formula_ids_changed: []" in text and "parameter_ids_changed: []" in text

parameter_path = "PFI/docs/governance/parameter_registry.csv"
before_parameters = list(csv.DictReader(base_blob(parameter_path).decode("utf-8").splitlines()))
after_parameters = list(csv.DictReader(Path(parameter_path).read_text(encoding="utf-8").splitlines()))
assert len(before_parameters) == len(after_parameters) == 23
assert [row["parameter_id"] for row in after_parameters] == [row["parameter_id"] for row in before_parameters]
allowed_parameter_columns = {"source_or_rationale"}
for before_row, after_row in zip(before_parameters, after_parameters):
    changed = {key for key in before_row if before_row[key] != after_row[key]}
    if before_row["parameter_id"] == "PARAM-PFI-003":
        assert changed == allowed_parameter_columns
        assert "PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE" in after_row["source_or_rationale"]
    else:
        assert not changed, (before_row["parameter_id"], changed)

event_path = "PFI/docs/governance/development_events.jsonl"
event_before = base_blob(event_path)
event_after = Path(event_path).read_bytes()
assert event_after.startswith(event_before)
appended_event_lines = event_after[len(event_before):].decode("utf-8").splitlines()
assert len(appended_event_lines) == 1
event = json.loads(appended_event_lines[0])
assert event["event_id"] == "EVENT-20260711-PFI-V025-S0-P03"
assert event["iteration_id"] == "ITER-20260711-PFI-V025-S0-P03"
assert event["result"] == "candidate_pass_pending_postcommit_attestation"
assert event["binding_status"] == "approved_pending_postcommit_attestation"
assert event["git_commit"] == base and event["contains_private_values"] is False
assert event["model_ids_changed"] == event["formula_ids_changed"] == event["parameter_ids_changed"] == []

trace_path = "PFI/docs/governance/TRACEABILITY_MATRIX.csv"
trace_before = base_blob(trace_path)
trace_after = Path(trace_path).read_bytes()
assert trace_after.startswith(trace_before)
before_trace_rows = list(csv.DictReader(trace_before.decode("utf-8").splitlines()))
after_trace_rows = list(csv.DictReader(trace_after.decode("utf-8").splitlines()))
new_trace_rows = after_trace_rows[len(before_trace_rows):]
assert [row["task_id"] for row in new_trace_rows] == ["S0-P3-T1", "S0-P3-T2", "S0-P3-T3", "S0-P3-T4"]
for trace_row in new_trace_rows:
    assert trace_row["model_id"] == trace_row["assumption_id"] == trace_row["formula_id"] == trace_row["parameter_id"] == "NOT_APPLICABLE"
    assert trace_row["acceptance_id"] == "ACC-PFI-V025-S0-P03-GAP-EVIDENCE"

for row in rows:
    refs = row["current_evidence_refs"].split(";")
    newest = max(datetime.fromisoformat(evidence["evidence_registry"][ref]["observed_at"].replace("Z", "+00:00")) for ref in refs)
    current_as_of = datetime.fromisoformat(row["current_evidence_as_of"].replace("Z", "+00:00"))
    assert current_as_of.tzinfo is not None and current_as_of == newest
    if row["prior_evidence_refs"] != "NOT_APPLICABLE":
        prior_refs = row["prior_evidence_refs"].split(";")
        newest_prior = max(datetime.fromisoformat(evidence["evidence_registry"][ref]["observed_at"].replace("Z", "+00:00")) for ref in prior_refs)
        prior_as_of = datetime.fromisoformat(row["prior_evidence_as_of"].replace("Z", "+00:00"))
        assert prior_as_of.tzinfo is not None and prior_as_of == newest_prior

excluded = {
    str(evidence_path),
    "PFI/docs/pfi_v025/stage_0/acceptance_request.md",
    *[path for path in expected_paths if path.startswith("PFI/docs/governance/") or path == "PFI/CHANGELOG.md"],
}
plan_text = Path("PFI/docs/pfi_v025/stage_0/PHASE_0_3_IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
artifact_section = plan_text[plan_text.index("`artifact_hashes` has exactly these 35 keys"):]
artifact_block = artifact_section.split("```text", 1)[1].split("```", 1)[0]
expected_artifact_keys = [line.strip() for line in artifact_block.splitlines() if line.strip()]
assert len(expected_artifact_keys) == len(set(expected_artifact_keys)) == 35
assert set(evidence["artifact_hashes"]) == set(expected_artifact_keys)
assert not (set(evidence["artifact_hashes"]) & excluded)
for path, digest in evidence["artifact_hashes"].items():
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert hashlib.sha256(resolve_ref(path).read_bytes()).hexdigest() == digest

request = Path("PFI/docs/pfi_v025/stage_0/acceptance_request.md").read_text(encoding="utf-8")
evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
assert "prepared_pending_whole_stage_review" in request
assert request.splitlines().count(f"evidence_sha256={evidence_sha}") == 1
assert "candidate_commit_binding=external_attestation_required" in request
assert not re.search(r"^(?:phase_commit|candidate_commit)=[0-9a-f]{40}$", request, re.M)
assert "Stage 1" in request and "not_started" in request
assert not Path("PFI/reports/pfi_v025/stage_0/human_acceptance.json").exists()

stage_root = Path("PFI/reports/pfi_v025/stage_0")
for name in ("baseline.json", "git_state.txt", "current_state_matrix.md", "data_root_inventory.json", "history_deprecation.md", "terminal.log"):
    assert (stage_root / name).is_file()
git_state_text = (stage_root / "git_state.txt").read_text(encoding="utf-8")
recent = subprocess.check_output(["git", "log", "-5", "--format=%H %s", base], text=True).splitlines()
assert all(git_state_text.splitlines().count(line) == 1 for line in recent)
assert "candidate_commit_binding=external_attestation_required" in git_state_text
matrix_text = (stage_root / "current_state_matrix.md").read_text(encoding="utf-8")
observed_matrix_states = set(re.findall(r"\| (VERIFIED|CONFLICTED|BLOCKED|NOT_RUN|REFERENCE_ONLY) \|", matrix_text))
assert observed_matrix_states and observed_matrix_states <= {"VERIFIED", "CONFLICTED", "BLOCKED", "NOT_RUN", "REFERENCE_ONLY"}
history_reference = (stage_root / "history_deprecation.md").read_text(encoding="utf-8")
canonical_history_sha = hashlib.sha256(Path("PFI/docs/pfi_v025/stage_0/history_deprecation.md").read_bytes()).hexdigest()
assert canonical_history_sha in history_reference
assert all(item_id in history_reference for item_id in canonical_history)
changed_ledger = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt").read_text(encoding="utf-8").splitlines()
assert changed_ledger == expected_paths
print("PHASE_0_3_SEMANTIC_GATE=PASS")
PY
```

- [ ] **Step 3: Run syntax/schema/selective test checks**

Run Node checks, JSON parse/schema, the isolated parameter baseline with expected failure classification, and `git diff --check`. Do not run full tests/browser/App. Then scan the exact current 25 files; the script discovers private DB/raw filenames in memory but reports only counts:

```bash
set -euo pipefail
PHASE_BASE="$(jq -er '.git_commit' PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json)"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B - "$PHASE_BASE" <<'PY'
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote
from pfi_v02.stage2_import import parse_alipay_bill_bytes
from pfi_v02.stage_v023_read_model import build_stage6_read_model_input

sys.excepthook = lambda *_: print("phase_0_3_privacy_scan=FAIL|reason=redacted", file=sys.stderr)

base = sys.argv[1]
ledger = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt").read_text(encoding="utf-8").splitlines()
assert len(ledger) == len(set(ledger)) == 25
scan_paths = [path for path in ledger if Path(path).is_file()]
assert len(scan_paths) in {24, 25}
forbidden_path_markers = ("/data/", "/MetaDatabase/", "/macos/", "/.pfi/", "/Applications/", "/Desktop/", "/Downloads/")
assert not [path for path in ledger if any(marker in path for marker in forbidden_path_markers)]

private_tokens = set()
approved_raw_paths = set(build_stage6_read_model_input(project_root="PFI")["git_raw_paths"])
assert len(approved_raw_paths) == 4
for line in subprocess.check_output(
    ["git", "ls-tree", "-r", "--name-only", base, "--", "MetaDatabase/PFI"], text=True
).splitlines():
    name = Path(line).name
    private_tokens.add(line)
    if name:
        private_tokens.add(name)
    raw = subprocess.run(
        ["git", "show", f"{base}:{line}"], stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, check=False,
    )
    assert raw.returncode == 0
    if line in approved_raw_paths:
        parsed = parse_alipay_bill_bytes(raw.stdout)
        for transaction in parsed.transactions:
            description = transaction.description.strip()
            if len(description) >= 2:
                private_tokens.add(description)
        decoded = raw.stdout.decode("utf-8-sig", errors="ignore")
        private_tokens.update(row.strip() for row in decoded.splitlines() if len(row.strip()) >= 16)
db_candidates = [
    path for path in (Path.home() / ".pfi").rglob("*")
    if path.is_file() and path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}
]
assert len(db_candidates) == 1
private_tokens.add(db_candidates[0].name)
private_tokens.add(str(db_candidates[0]))
uri = "file:" + quote(str(db_candidates[0]), safe="/") + "?mode=ro&immutable=1"
connection = sqlite3.connect(uri, uri=True)
try:
    connection.execute("PRAGMA query_only=ON")
    assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
    private_tokens.update(
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ) if row[0]
    )
finally:
    connection.close()

patterns = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{12,}|sk-[A-Za-z0-9_-]{12,})\b"),
    re.compile(r"(?i)\b(?:password|secret|api[_-]?key|account_number|card_number)\b\s*[:=]\s*[\"']?(?!false\b|none\b|not[_ -]?applicable\b)[A-Za-z0-9+/=_-]{8,}"),
    re.compile(r"\b(?:\d[ -]?){12,19}\b"),
]
pattern_findings = 0
private_token_findings = 0
structured_key_findings = 0
forbidden_structured_keys = {
    "amount", "amount_cny", "merchant", "counterparty", "account_number",
    "card_number", "raw_row", "raw_payload", "transaction_description",
    "table_name", "database_path", "source_path",
}

def count_forbidden_keys(value) -> int:
    if isinstance(value, dict):
        return sum(key in forbidden_structured_keys for key in value) + sum(
            count_forbidden_keys(item) for item in value.values()
        )
    if isinstance(value, list):
        return sum(count_forbidden_keys(item) for item in value)
    return 0

for path in scan_paths:
    text = Path(path).read_text(encoding="utf-8")
    pattern_findings += sum(1 for pattern in patterns if pattern.search(text))
    private_token_findings += sum(1 for token in private_tokens if token and token in text)
    if path.endswith(".json"):
        structured_key_findings += count_forbidden_keys(__import__("json").loads(text))
    elif path.endswith(".jsonl"):
        structured_key_findings += sum(
            count_forbidden_keys(__import__("json").loads(line))
            for line in text.splitlines() if line.strip()
        )
assert pattern_findings == 0, f"private_pattern_findings={pattern_findings}"
assert private_token_findings == 0, f"private_token_findings={private_token_findings}"
assert structured_key_findings == 0, f"structured_private_key_findings={structured_key_findings}"
print(f"phase_0_3_privacy_scan=PASS|files={len(scan_paths)}|pattern_findings=0|private_token_findings=0|structured_key_findings=0")
PY
```

- [ ] **Step 4: Run both governance validators in a guarded detached selective shadow**

Run this block with `VALIDATION_MODE=provisional`; Step 6 reruns the same block with `VALIDATION_MODE=final`. It copies exact working-tree files, so untracked core artifacts cannot disappear from the shadow:

```bash
set -euo pipefail
PHASE_BASE="$(jq -er '.git_commit' PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json)"
VALIDATION_MODE="${VALIDATION_MODE:-provisional}"
typeset -a EXACT_PATHS=(
  PFI/CHANGELOG.md
  PFI/docs/governance/DEVELOPMENT_LEDGER.md
  PFI/docs/governance/MODEL_SPEC.md
  PFI/docs/governance/OWNER_STATUS.md
  PFI/docs/governance/STATUS.md
  PFI/docs/governance/TRACEABILITY_MATRIX.csv
  PFI/docs/governance/VERSION_MATRIX.yaml
  PFI/docs/governance/delivery_tasks.yaml
  PFI/docs/governance/development_events.jsonl
  PFI/docs/governance/formula_registry.yaml
  PFI/docs/governance/model_registry.yaml
  PFI/docs/governance/parameter_registry.csv
  PFI/docs/pfi_v025/stage_0/acceptance_request.md
  PFI/docs/pfi_v025/stage_0/finding_ledger.csv
  PFI/docs/pfi_v025/stage_0/gap_register.md
  PFI/reports/pfi_v025/stage_0/baseline.json
  PFI/reports/pfi_v025/stage_0/current_state_matrix.md
  PFI/reports/pfi_v025/stage_0/data_root_inventory.json
  PFI/reports/pfi_v025/stage_0/git_state.txt
  PFI/reports/pfi_v025/stage_0/history_deprecation.md
  PFI/reports/pfi_v025/stage_0/terminal.log
  PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt
  PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json
  PFI/reports/pfi_v025/stage_0/phase_0_3/risk_and_rollback.md
  PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log
)
test "${#EXACT_PATHS[@]}" -eq 25
test "$(printf '%s\n' "${EXACT_PATHS[@]}" | LC_ALL=C sort -u | wc -l | tr -d ' ')" -eq 25
typeset -a SHADOW_PATHS=()
for path in "${EXACT_PATHS[@]}"; do
  if [ "$VALIDATION_MODE" = provisional ] && [ "$path" = PFI/docs/pfi_v025/stage_0/acceptance_request.md ]; then
    continue
  fi
  SHADOW_PATHS+=("$path")
done
case "$VALIDATION_MODE" in
  provisional) test "${#SHADOW_PATHS[@]}" -eq 24 ;;
  final) test "${#SHADOW_PATHS[@]}" -eq 25 ;;
  *) exit 2 ;;
esac

CANONICAL_ROOT="$(git rev-parse --show-toplevel)"
cd "$CANONICAL_ROOT"
CANONICAL_STATUS_BEFORE="$(git status --porcelain=v1 -z --untracked-files=all | openssl dgst -sha256 | awk '{print $NF}')"
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "$PHASE_BASE" "${SHADOW_PATHS[@]}" <<'PY'
import subprocess
import sys
base = sys.argv[1]
expected = sorted(sys.argv[2:])
tracked = subprocess.check_output(["git", "diff", "--name-only", base], text=True).splitlines()
untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
assert sorted(set(tracked + untracked)) == expected
PY

SHADOW_PARENT="$(mktemp -d /private/tmp/pfi-v025-s0p03-preflight.XXXXXX)"
case "$SHADOW_PARENT" in /private/tmp/pfi-v025-s0p03-preflight.*) ;; *) exit 2 ;; esac
SHADOW="$SHADOW_PARENT/repo"
registered=0
cleanup_shadow() {
  local rc=0 remove_rc=0 directory_rc=0
  if [ "$registered" -eq 1 ]; then
    GIT_NO_LAZY_FETCH=1 git worktree remove --force "$SHADOW" || remove_rc=$?
    [ "$remove_rc" -eq 0 ] && registered=0 || rc=$remove_rc
  fi
  case "$SHADOW_PARENT" in
    /private/tmp/pfi-v025-s0p03-preflight.*) rm -rf -- "$SHADOW_PARENT" || directory_rc=$? ;;
    *) directory_rc=2 ;;
  esac
  [ "$rc" -eq 0 ] && [ "$directory_rc" -ne 0 ] && rc=$directory_rc
  return "$rc"
}
finish_shadow() {
  local original_rc=$? cleanup_rc=0
  trap - EXIT INT TERM
  cleanup_shadow || cleanup_rc=$?
  [ "$original_rc" -eq 0 ] && original_rc=$cleanup_rc
  exit "$original_rc"
}
trap finish_shadow EXIT
trap 'exit 130' INT TERM

GIT_NO_LAZY_FETCH=1 git worktree add --detach --no-checkout "$SHADOW" "$PHASE_BASE"
registered=1
git -C "$SHADOW" sparse-checkout init --no-cone
git -C "$SHADOW" sparse-checkout set --no-cone --stdin <<'SPARSE'
/*
!/*/
/PFI/*
!/PFI/*/
/PFI/config/
/PFI/docs/
/PFI/scripts/
/PFI/src/
/PFI/tests/
/PFI/web/
/PFI/reports/
!/PFI/reports/*/
/PFI/reports/pfi_v025/
!/PFI/reports/pfi_v025/*/
/PFI/reports/pfi_v025/stage_0/
!/PFI/reports/pfi_v025/stage_0/*/
/PFI/reports/pfi_v025/stage_0/phase_0_1/
/PFI/reports/pfi_v025/stage_0/phase_0_2/
/PFI/reports/pfi_v025/stage_0/phase_0_3/
/scripts/
/docs/governance/
/governance/projects.yaml
/governance/schemas/
/tests/governance/
/tests/cloudflare/test_compatibility_envelope.py
/.github/workflows/project-governance.yml
/.agents/skills/project-governance/SKILL.md
/.agents/skills/codex-dex/SKILL.md
/.codex/config.template.toml
/.codex/hooks.json
/.codex/hooks/governance_stop.py
/Alpha/AGENTS.md
/EEI/AGENTS.md
/FIFA/AGENTS.md
/KM_IDSystem/AGENTS.md
/WDA/AGENTS.md
/OpenAIDatabase/AGENTS.md
/MetaDatabase/README.md
/KMFA/AGENTS.md
/QBVS/AGENTS.md
/Serenity-Alipay/AGENTS.md
/whkmSalary/AGENTS.md
/arxiv-daily-push/AGENTS.md
SPARSE
GIT_NO_LAZY_FETCH=1 git -C "$SHADOW" checkout --detach "$PHASE_BASE"
for path in "${SHADOW_PATHS[@]}"; do
  test -f "$CANONICAL_ROOT/$path"
  mkdir -p "$SHADOW/$(dirname "$path")"
  cp -p -- "$CANONICAL_ROOT/$path" "$SHADOW/$path"
  cmp -s -- "$CANONICAL_ROOT/$path" "$SHADOW/$path"
done
git -C "$SHADOW" add -- "${SHADOW_PATHS[@]}"
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "$SHADOW" "${SHADOW_PATHS[@]}" <<'PY'
import subprocess
import sys
shadow = sys.argv[1]
expected = sorted(sys.argv[2:])
staged = subprocess.check_output(["git", "-C", shadow, "diff", "--cached", "--name-only"], text=True).splitlines()
assert staged == expected
assert not subprocess.check_output(["git", "-C", shadow, "diff", "--name-only"], text=True).splitlines()
assert not subprocess.check_output(["git", "-C", shadow, "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
PY
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
RUN_GUARD_ROOT="$(PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" "$PHASE_BASE" <<'PY'
import hashlib, json, sys
from pathlib import Path
parent, base = Path(sys.argv[1]), sys.argv[2]
pointer = parent / "current.path"
assert pointer.is_file() and not pointer.is_symlink()
run = Path(pointer.read_text(encoding="utf-8").strip())
assert run.parent == parent and not run.is_symlink()
state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
assert state["phase_base"] == base and state["status"] == "baseline_complete"
for field, name in {
    "before_sha256": "before.json",
    "git_state_before_sha256": "git_state_before.json",
    "governance_baseline_sha256": "governance_baseline.json",
}.items():
    path = run / name
    assert path.is_file() and not path.is_symlink()
    assert state[field] == hashlib.sha256(path.read_bytes()).hexdigest()
print(run)
PY
)"
PROJECT_LOG="$RUN_GUARD_ROOT/${VALIDATION_MODE}_project_governance.log"
SYNC_LOG="$RUN_GUARD_ROOT/${VALIDATION_MODE}_governance_sync.log"
(
  cd "$SHADOW"
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_project_governance.py --changed-only --base-ref "$PHASE_BASE" --enforce-sync --semantic
) 2>&1 | tee "$PROJECT_LOG"
(
  cd "$SHADOW"
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_governance_sync.py --changed-only --base-ref "$PHASE_BASE" --enforce-sync --semantic
) 2>&1 | tee "$SYNC_LOG"
grep -Fx 'projects checked: PFI' "$PROJECT_LOG"
grep -Fx 'projects changed: PFI' "$SYNC_LOG"
grep -Fx 'errors: 0' "$SYNC_LOG"
grep -Fx 'warnings: 0' "$SYNC_LOG"
chmod 600 "$PROJECT_LOG" "$SYNC_LOG"
CANONICAL_STATUS_AFTER="$(git status --porcelain=v1 -z --untracked-files=all | openssl dgst -sha256 | awk '{print $NF}')"
test "$CANONICAL_STATUS_AFTER" = "$CANONICAL_STATUS_BEFORE"
exit 0
```

Expected: selected project PFI, missing companions=0, errors=0, warnings=0; canonical status hash unchanged and shadow cleanup succeeds. All-project semantic expansion is not a Phase gate.

- [ ] **Step 5: Finalize candidate lifecycle and create the one-way acceptance request**

Only after Steps 1–4 pass, use `apply_patch` to:

- update the sole appended event from `validation_in_progress/approved_pending_validation` to `candidate_pass_pending_postcommit_attestation/approved_pending_postcommit_attestation` and add only actual completed gate summaries;
- update the four overlays to the same pending-postcommit lifecycle without altering product/version/owner truth;
- update evidence to `status=candidate_pass`, `allowed_files_obeyed=true`, all four tasks `candidate_pass`, `governance_override_state=approved_pending_postcommit_attestation`, and record actual preliminary gate exits;
- keep all Layer 0/1 hashes unchanged; recalculate evidence bytes only;
- hash finalized evidence and create `acceptance_request.md` with exactly one machine line `evidence_sha256=<lowercase 64-hex>`, `prepared_pending_whole_stage_review`, `candidate_commit_binding=external_attestation_required`, authority/Phase identities, open defects/gaps, no-future-commit rule, invalid bare-`1` rule, and next-step-only whole-stage review statement. It must not contain `phase_commit=<sha>` or `candidate_commit=<sha>`.

Do not hash the request into evidence and do not create `human_acceptance.json`.

- [ ] **Step 6: Execute the final verifier and rerun all final-tree gates**

Now execute the inline final semantic verifier defined above. Re-run streamed Task Pack schema validation, JSON/privacy/syntax checks, exact 25-path scope, registry invariants, and both selective-shadow governance validators against the finalized 25-path tree. These final-tree outputs remain external/tool evidence; do not back-write them and create a hash cycle.

**Task acceptance:** exact final 25 paths, semantic/schema/privacy checks pass, both selective validators pass with zero drift, and tracked candidate claims are backed by completed preliminary gates plus a clean final rerun.

---

### Task 7: Independent review, remediation, and final precommit re-review

- [ ] **Step 1: Dispatch fresh read-only reviewers**

Use at least two independent reviewers after all artifacts exist:

1. Roadmap/Task Pack and finding/gap fidelity reviewer.
2. Governance/evidence/hash/privacy/no-side-effect reviewer.

A third data/source reviewer is preferred. Reviewers receive `$PHASE_BASE`, exact 25 paths, design/plan, and actual gate outputs. They do not edit.

- [ ] **Step 2: Remediate only inside exact 25**

Any blocker/major/minor is fixed with `apply_patch`; rerun every affected gate. If remediation needs a 26th path, a model/parameter value, private output, or product/runtime mutation, stop rather than widen.

The remediation state machine is explicit and one-way per attempt:

1. If a reviewer requests any tracked edit, first delete only the generated `acceptance_request.md`, change the sole appended event and four overlays back to `validation_in_progress/approved_pending_validation`, and change evidence back to `status=not_run`, `allowed_files_obeyed=false`, four task records `not_run`, without inventing a new event.
2. If any Layer 0/1 byte changes, invalidate the prior Layer 0/1 hash set and restart Task 5 from hash freezing; otherwise reuse only hashes whose source bytes are unchanged.
3. Rerun Task 6 in `provisional` mode against exact 24 paths, then perform Step 5 lifecycle finalization, recreate the request from the newly finalized evidence hash, and rerun Task 6 in `final` mode against exact 25 paths.
4. Never call the exact-24 provisional gate while the request exists or while candidate lifecycle fields remain finalized. Never patch a finalized request/evidence pair in place.

- [ ] **Step 3: Re-review until all tracks pass**

Require explicit 0 blocker / 0 major. Any accepted minor must be demonstrably non-acceptance-impacting; default is to fix and re-review. Run the complete Task 6 gate set again after the final edit.

**Task acceptance:** fresh independent PASS, exact 25 unchanged, and no unresolved acceptance-impacting finding.

---

### Task 8: Create one atomic implementation commit

- [ ] **Step 1: Stage exact 25 and verify the index**

```bash
set -euo pipefail
PHASE_BASE="$(jq -er '.git_commit' PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json)"
typeset -a EXACT_PATHS=(
  PFI/CHANGELOG.md
  PFI/docs/governance/DEVELOPMENT_LEDGER.md
  PFI/docs/governance/MODEL_SPEC.md
  PFI/docs/governance/OWNER_STATUS.md
  PFI/docs/governance/STATUS.md
  PFI/docs/governance/TRACEABILITY_MATRIX.csv
  PFI/docs/governance/VERSION_MATRIX.yaml
  PFI/docs/governance/delivery_tasks.yaml
  PFI/docs/governance/development_events.jsonl
  PFI/docs/governance/formula_registry.yaml
  PFI/docs/governance/model_registry.yaml
  PFI/docs/governance/parameter_registry.csv
  PFI/docs/pfi_v025/stage_0/acceptance_request.md
  PFI/docs/pfi_v025/stage_0/finding_ledger.csv
  PFI/docs/pfi_v025/stage_0/gap_register.md
  PFI/reports/pfi_v025/stage_0/baseline.json
  PFI/reports/pfi_v025/stage_0/current_state_matrix.md
  PFI/reports/pfi_v025/stage_0/data_root_inventory.json
  PFI/reports/pfi_v025/stage_0/git_state.txt
  PFI/reports/pfi_v025/stage_0/history_deprecation.md
  PFI/reports/pfi_v025/stage_0/terminal.log
  PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt
  PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json
  PFI/reports/pfi_v025/stage_0/phase_0_3/risk_and_rollback.md
  PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log
)
test "${#EXACT_PATHS[@]}" -eq 25
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "$PHASE_BASE" "${EXACT_PATHS[@]}" <<'PY'
import subprocess
import sys
base = sys.argv[1]
expected = sorted(sys.argv[2:])
tracked = subprocess.check_output(["git", "diff", "--name-only", base], text=True).splitlines()
untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
assert sorted(set(tracked + untracked)) == expected
PY
git add -- "${EXACT_PATHS[@]}"
git diff --cached --check
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "${EXACT_PATHS[@]}" <<'PY'
import subprocess
import sys
from pathlib import Path
expected = sorted(sys.argv[1:])
staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).splitlines()
ledger = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt").read_text(encoding="utf-8").splitlines()
assert staged == expected and ledger == expected
assert not subprocess.check_output(["git", "diff", "--name-only"], text=True).splitlines()
assert not subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
PY
git diff --cached --stat
```

Assert the staged set equals the exact ledger, every new core artifact is staged, and no design/plan/protected path is staged.

- [ ] **Step 2: Commit once**

```bash
set -euo pipefail
PHASE_BASE="$(jq -er '.git_commit' PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json)"
git commit -m "docs(PFI): complete v0.2.5 stage 0 phase 0.3 evidence"
export PHASE_COMMIT="$(git rev-parse HEAD)"
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import subprocess
import sys
from pathlib import Path
base, commit = sys.argv[1:3]
expected = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt").read_text(encoding="utf-8").splitlines()
assert subprocess.check_output(["git", "rev-parse", f"{commit}^"], text=True).strip() == base
assert int(subprocess.check_output(["git", "rev-list", "--count", f"{base}..{commit}"], text=True)) == 1
actual = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit], text=True).splitlines()
assert sorted(actual) == expected
assert not subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], text=True).splitlines()
PY
```

Expected: one local commit with exact 25 paths and clean worktree. Do not push.

---

### Task 9: Bind final-tree governance, remote truth, and no-side-effect facts externally

- [ ] **Step 1: Run clean postcommit selective Lean Governance CI**

Under a unique attempt directory:

```text
$(git rev-parse --git-common-dir)/codex-review/pfi-v025/stage_0/phase_0_3/<PHASE_COMMIT>.attempt.<random>/
```

run guarded selective Lean CI on `$PHASE_BASE..$PHASE_COMMIT`. Require SHIP, selected PFI, legacy exit 0, selector parity, exact 25 paths, and zero tracked write. Write `phase_0_3_ci_attestation.json` with schema `PFIV025Phase03CIAttestationV1`, base/commit, tool evidence path/hash, stable summary hash, selected projects, exits, and changed paths. It remains blocking until final attestation.

Run this complete block in a fresh zsh process:

```bash
set -euo pipefail
umask 077
PHASE_COMMIT="$(git rev-parse HEAD)"
PHASE_BASE="$(jq -er '.git_commit' PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json)"
test "$(git rev-parse "$PHASE_COMMIT^")" = "$PHASE_BASE"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
COMMON_GIT_DIR="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)"
ATTEST_PARENT="$COMMON_GIT_DIR/codex-review/pfi-v025/stage_0/phase_0_3"
mkdir -p "$ATTEST_PARENT"
ATTEST_POINTER="$ATTEST_PARENT/current.path"
EXISTING_FINAL="$(PFI/.venv/bin/python -B - "$ATTEST_PARENT" <<'PY'
import sys
from pathlib import Path
parent = Path(sys.argv[1])
finals = list(parent.glob("*.attempt.*/phase_0_3_attestation.json"))
assert len(finals) <= 1, "multiple authoritative finals"
print(finals[0] if finals else "")
PY
)"
if [ -n "$EXISTING_FINAL" ]; then
  PFI/.venv/bin/python -B - "$EXISTING_FINAL" "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import hashlib, json, os, subprocess, sys
from pathlib import Path
final_path = Path(sys.argv[1])
base, commit = sys.argv[2:4]
d = json.loads(final_path.read_text(encoding="utf-8"))
assert d["schema"] == "PFIV025Phase03AttestationV1"
assert d["contract_id"] == "PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE"
assert d["acceptance_id"] == "ACC-PFI-V025-S0-P03-GAP-EVIDENCE"
assert d["conflict_id"] == "PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE"
assert d["override_id"] == "PFI-V025-S0-P03-GOVERNANCE-COMPANIONS"
assert d["phase_base"] == base and d["phase_commit"] == commit
assert d["status"] == "resolved_by_approved_override" and d["blocks_phase_candidate"] is False
assert d["contains_private_values"] is False
ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt")
ledger = ledger_path.read_text(encoding="utf-8").splitlines()
assert len(ledger) == 25 and ledger == sorted(ledger) == d["changed_files"]
assert hashlib.sha256(ledger_path.read_bytes()).hexdigest() == d["changed_files_sha256"]
assert subprocess.check_output(["git", "diff", "--name-only", f"{base}..{commit}"], text=True).splitlines() == ledger
assert d["remote_pfi_drift"] is False and d["clean_worktree"] is True
assert d["commit_content_verified"] is True and d["no_side_effect_postcheck"] is True
source = Path(d["publication_source_ref"])
candidate = Path(d["blocking_candidate_ref"])
assert source.parent == candidate.parent == final_path.parent
assert source.read_bytes() == final_path.read_bytes()
assert source.stat().st_ino == final_path.stat().st_ino
assert hashlib.sha256(candidate.read_bytes()).hexdigest() == d["blocking_candidate_sha256"]
c = json.loads(candidate.read_text(encoding="utf-8"))
publication_additions = {
    "blocking_candidate_ref", "blocking_candidate_sha256",
    "publication_source_ref", "independently_validated_at",
}
assert set(d) == set(c) | publication_additions
for key, value in c.items():
    if key not in {"schema", "status", "blocks_phase_candidate"}:
        assert d[key] == value, key
for ref_key, sha_key in (
    ("ci_attestation_ref", "ci_attestation_sha256"),
    ("no_side_effect_artifact_ref", "no_side_effect_artifact_sha256"),
    ("remote_proof_ref", "remote_proof_sha256"),
    ("evidence_ref", "evidence_sha256"),
    ("acceptance_request_ref", "acceptance_request_sha256"),
    ("run_state_ref", "run_state_sha256"),
    ("guard_before_ref", "guard_before_sha256"),
    ("guard_git_state_ref", "guard_git_state_sha256"),
    ("governance_baseline_ref", "governance_baseline_sha256"),
):
    path = Path(d[ref_key])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == d[sha_key]
evidence = json.loads(Path(d["evidence_ref"]).read_text(encoding="utf-8"))
assert evidence["git_commit"] == base
assert evidence["git_commit_semantics"] == "implementation_base_before_phase_commit"
assert evidence["status"] == "candidate_pass"
request = Path(d["acceptance_request_ref"]).read_text(encoding="utf-8")
assert request.splitlines().count(f'evidence_sha256={d["evidence_sha256"]}') == 1
no_side = json.loads(Path(d["no_side_effect_artifact_ref"]).read_text(encoding="utf-8"))
assert no_side["identical"] is True and no_side["runtime_unchanged"] is True
assert Path(no_side["before_ref"]) == Path(d["guard_before_ref"])
assert no_side["before_sha256"] == d["guard_before_sha256"]
assert hashlib.sha256(Path(no_side["after_ref"]).read_bytes()).hexdigest() == no_side["after_sha256"]
assert json.loads(Path(no_side["before_ref"]).read_text(encoding="utf-8")) == json.loads(Path(no_side["after_ref"]).read_text(encoding="utf-8"))
assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == commit
assert subprocess.check_output(["git", "rev-parse", f"{commit}^"], text=True).strip() == base
assert not subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], text=True).splitlines()
print(f"existing_final_recovery=PASS|path={final_path}")
PY
  exit 0
fi
ATTEST_DIR="$(PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "$ATTEST_PARENT" "$ATTEST_POINTER" "$PHASE_COMMIT" <<'PY'
import fcntl
import os
import sys
import tempfile
from pathlib import Path

parent = Path(sys.argv[1])
pointer = Path(sys.argv[2])
commit = sys.argv[3]
lock_path = parent / "phase.lock"
with lock_path.open("a+", encoding="utf-8") as stream:
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
    assert not list(parent.glob("*.attempt.*/phase_0_3_attestation.json")), "authoritative final already exists"
    attempt = Path(tempfile.mkdtemp(prefix=f"{commit}.attempt.", dir=parent))
    temporary = pointer.with_name(f".{pointer.name}.tmp.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as pointer_stream:
        pointer_stream.write(str(attempt) + "\n")
    os.replace(temporary, pointer)
    print(attempt)
PY
)"
case "$ATTEST_DIR" in "$ATTEST_PARENT/$PHASE_COMMIT.attempt."*) ;; *) exit 2 ;; esac
test -d "$ATTEST_DIR" && test ! -L "$ATTEST_DIR"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
RUN_GUARD_ROOT="$(PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" "$PHASE_BASE" <<'PY'
import hashlib, json, sys
from pathlib import Path
parent, base = Path(sys.argv[1]), sys.argv[2]
pointer = parent / "current.path"
assert pointer.is_file() and not pointer.is_symlink()
run = Path(pointer.read_text(encoding="utf-8").strip())
assert run.parent == parent and not run.is_symlink()
state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
assert state["phase_base"] == base and state["status"] == "baseline_complete"
for field, name in {"before_sha256":"before.json","git_state_before_sha256":"git_state_before.json","governance_baseline_sha256":"governance_baseline.json"}.items():
    path = run / name
    assert path.is_file() and not path.is_symlink()
    assert state[field] == hashlib.sha256(path.read_bytes()).hexdigest()
print(run)
PY
)"
ATTEST_DIR="$ATTEST_DIR" PFI/.venv/bin/python -B - "$RUN_GUARD_ROOT/run_state.json" "$PHASE_BASE" "$ATTEST_PARENT" "$ATTEST_POINTER" <<'PY'
import fcntl
import hashlib
import json
import os
import sys
from pathlib import Path
path = Path(sys.argv[1])
lock_path = Path(sys.argv[3]) / "phase.lock"
state_lock_path = path.parent / "run_state.lock"
state_lock_path.touch(mode=0o600, exist_ok=True)
state_lock_path.chmod(0o600)
pointer = Path(sys.argv[4])
with lock_path.open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    with state_lock_path.open("r+", encoding="utf-8") as state_lock_stream:
        fcntl.flock(state_lock_stream.fileno(), fcntl.LOCK_EX)
        attempt = Path(os.environ["ATTEST_DIR"])
        assert pointer.is_file() and not pointer.is_symlink()
        assert Path(pointer.read_text(encoding="utf-8").strip()) == attempt
        assert attempt.parent == Path(sys.argv[3]) and not attempt.is_symlink()
        state = json.loads(path.read_text(encoding="utf-8"))
        assert state["phase_base"] == sys.argv[2] and state["status"] == "baseline_complete"
        guard = path.parent
        for field, name in {"before_sha256":"before.json","git_state_before_sha256":"git_state_before.json","governance_baseline_sha256":"governance_baseline.json"}.items():
            assert state[field] == hashlib.sha256((guard / name).read_bytes()).hexdigest()
        state.setdefault("attempts", []).append(str(attempt))
        state["attest_dir"] = str(attempt)
        temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(state, sort_keys=True) + "\n")
        temporary.chmod(0o600)
        os.replace(temporary, path)
PY

SHADOW_PARENT="$(mktemp -d /private/tmp/pfi-v025-s0p03-attest.XXXXXX)"
case "$SHADOW_PARENT" in /private/tmp/pfi-v025-s0p03-attest.*) ;; *) exit 2 ;; esac
SHADOW="$SHADOW_PARENT/repo"
registered=0
cleanup_attest_shadow() {
  local rc=0 remove_rc=0 directory_rc=0
  if [ "$registered" -eq 1 ]; then
    GIT_NO_LAZY_FETCH=1 git worktree remove --force "$SHADOW" || remove_rc=$?
    [ "$remove_rc" -eq 0 ] && registered=0 || rc=$remove_rc
  fi
  case "$SHADOW_PARENT" in
    /private/tmp/pfi-v025-s0p03-attest.*) rm -rf -- "$SHADOW_PARENT" || directory_rc=$? ;;
    *) directory_rc=2 ;;
  esac
  [ "$rc" -eq 0 ] && [ "$directory_rc" -ne 0 ] && rc=$directory_rc
  return "$rc"
}
trap cleanup_attest_shadow EXIT INT TERM
GIT_NO_LAZY_FETCH=1 git worktree add --detach --no-checkout "$SHADOW" "$PHASE_COMMIT"
registered=1
git -C "$SHADOW" sparse-checkout init --no-cone
git -C "$SHADOW" sparse-checkout set --no-cone --stdin <<'SPARSE'
/*
!/*/
/PFI/*
!/PFI/*/
/PFI/config/
/PFI/docs/
/PFI/scripts/
/PFI/src/
/PFI/tests/
/PFI/web/
/PFI/reports/
!/PFI/reports/*/
/PFI/reports/pfi_v025/
!/PFI/reports/pfi_v025/*/
/PFI/reports/pfi_v025/stage_0/
!/PFI/reports/pfi_v025/stage_0/*/
/PFI/reports/pfi_v025/stage_0/phase_0_1/
/PFI/reports/pfi_v025/stage_0/phase_0_2/
/PFI/reports/pfi_v025/stage_0/phase_0_3/
/scripts/
/docs/governance/
/governance/projects.yaml
/governance/schemas/
/tests/governance/
/tests/cloudflare/test_compatibility_envelope.py
/.github/workflows/project-governance.yml
/.agents/skills/project-governance/SKILL.md
/.agents/skills/codex-dex/SKILL.md
/.codex/config.template.toml
/.codex/hooks.json
/.codex/hooks/governance_stop.py
/Alpha/AGENTS.md
/EEI/AGENTS.md
/FIFA/AGENTS.md
/KM_IDSystem/AGENTS.md
/WDA/AGENTS.md
/OpenAIDatabase/AGENTS.md
/MetaDatabase/README.md
/KMFA/AGENTS.md
/QBVS/AGENTS.md
/Serenity-Alipay/AGENTS.md
/whkmSalary/AGENTS.md
/arxiv-daily-push/AGENTS.md
SPARSE
GIT_NO_LAZY_FETCH=1 git -C "$SHADOW" checkout --detach "$PHASE_COMMIT"
set +e
CI=1 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$SHADOW/scripts/lean_governance.py" ci \
  --changed-only --base-ref "$PHASE_BASE" 2>&1 | tee "$ATTEST_DIR/lean_governance.log"
LEAN_RC=$?
set -e
set +e
cleanup_attest_shadow
CLEANUP_RC=$?
set -e
trap - EXIT INT TERM
test "$LEAN_RC" -eq 0
test "$CLEANUP_RC" -eq 0

PFI/.venv/bin/python -B - "$ATTEST_DIR/lean_governance.log" "$ATTEST_DIR/phase_0_3_ci_attestation.json" "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

log_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
base, commit = sys.argv[3:5]
lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
compact = json.loads(lines[-1])
assert compact["decision"] == "SHIP"
assert compact["process_exit_code"] == compact["legacy_exit_code"] == 0
assert compact["selected_project_count"] == compact["validation_checked_project_count"] == 1
assert compact["zero_tracked_write"] is True
full_ref = compact["full_evidence_ref"]
full_path = Path(full_ref["path_or_artifact_ref"])
raw = full_path.read_bytes()
payload = raw[:-1] if raw.endswith(b"\n") else raw
assert "sha256:" + hashlib.sha256(payload).hexdigest() == full_ref["sha256"]
full = json.loads(payload)
assert [item["project_id"] for item in full["changed_scope"]["selected_projects"]] == ["PFI"]
assert full["validation"]["exit_code"] == 0
assert full["selector_parity"]["matches"] is True
assert full["zero_write_delta"]["clean"] is True
assert full["candidate_shadow_comparison"]["legacy_exit_code"] == 0
assert compact["stable_summary_hash"] == full["stable_summary_hash"]
ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt")
ledger = ledger_path.read_text(encoding="utf-8").splitlines()
actual = subprocess.check_output(["git", "diff", "--name-only", f"{base}..{commit}"], text=True).splitlines()
assert len(ledger) == 25 and ledger == sorted(ledger) == actual
attestation = {
    "schema": "PFIV025Phase03CIAttestationV1",
    "contract_id": "PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE",
    "acceptance_id": "ACC-PFI-V025-S0-P03-GAP-EVIDENCE",
    "conflict_id": "PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE",
    "override_id": "PFI-V025-S0-P03-GOVERNANCE-COMPANIONS",
    "phase_base": base,
    "phase_commit": commit,
    "ci_evidence_ref": str(full_path),
    "ci_evidence_sha256": full_ref["sha256"],
    "ci_stable_summary_hash": compact["stable_summary_hash"],
    "ci_exit_code": 0,
    "decision": "SHIP",
    "selected_projects": ["PFI"],
    "legacy_exit_code": 0,
    "selector_parity": True,
    "zero_tracked_write": True,
    "changed_files": ledger,
    "changed_files_sha256": "sha256:" + hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
    "status": "ci_pass_pending_final_stop_checks",
    "blocks_phase_candidate": True,
    "attested_at": datetime.now(ZoneInfo("Australia/Sydney")).isoformat(),
    "contains_private_values": False,
}
with output_path.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(attestation, ensure_ascii=False, indent=2) + "\n")
print("phase_0_3_ci_binding=PASS")
PY

PFI/.venv/bin/python -B - "$ATTEST_DIR/phase_0_3_ci_attestation.json" "$RUN_GUARD_ROOT/run_state.json" "$ATTEST_POINTER" "$ATTEST_PARENT" "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import fcntl
import hashlib
import json
import os
import sys
from pathlib import Path
ci_path, state_path, pointer, parent = map(Path, sys.argv[1:5])
base, commit = sys.argv[5:7]
ci = json.loads(ci_path.read_text(encoding="utf-8"))
assert ci["schema"] == "PFIV025Phase03CIAttestationV1"
assert ci["contract_id"] == "PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE"
assert ci["acceptance_id"] == "ACC-PFI-V025-S0-P03-GAP-EVIDENCE"
assert ci["conflict_id"] == "PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE"
assert ci["override_id"] == "PFI-V025-S0-P03-GOVERNANCE-COMPANIONS"
assert ci["phase_base"] == base and ci["phase_commit"] == commit
assert ci["status"] == "ci_pass_pending_final_stop_checks"
assert ci["blocks_phase_candidate"] is True
assert ci["decision"] == "SHIP" and ci["selected_projects"] == ["PFI"]
assert ci["legacy_exit_code"] == 0 and ci["selector_parity"] is True and ci["zero_tracked_write"] is True
ci_digest = hashlib.sha256(ci_path.read_bytes()).hexdigest()
state_lock_path = state_path.parent / "run_state.lock"
state_lock_path.touch(mode=0o600, exist_ok=True)
state_lock_path.chmod(0o600)
with (parent / "phase.lock").open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    with state_lock_path.open("r+", encoding="utf-8") as state_lock_stream:
        fcntl.flock(state_lock_stream.fileno(), fcntl.LOCK_EX)
        assert pointer.is_file() and not pointer.is_symlink()
        assert Path(pointer.read_text(encoding="utf-8").strip()) == ci_path.parent
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["phase_base"] == base and state["status"] == "baseline_complete"
        assert Path(state["attest_dir"]) == ci_path.parent
        guard = state_path.parent
        for field, name in {"before_sha256":"before.json","git_state_before_sha256":"git_state_before.json","governance_baseline_sha256":"governance_baseline.json"}.items():
            assert state[field] == hashlib.sha256((guard / name).read_bytes()).hexdigest()
        state["ci_attestation_sha256"] = ci_digest
        temporary = state_path.with_name(f".{state_path.name}.tmp.{os.getpid()}")
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(state, sort_keys=True) + "\n")
        temporary.chmod(0o600)
        os.replace(temporary, state_path)
PY
```

- [ ] **Step 2: Re-prove final advertised main without ref mutation**

Read `FINAL_LIVE_MAIN` from `ls-remote`; hydrate only the exact object if needed using the guarded no-ref procedure. Require unchanged complete refs/FETCH_HEAD/shallow state and quiet remote-only PFI diff from final merge-base.

- [ ] **Step 3: Compare protected metadata guard and commit content**

Generate a unique `after-<attempt>.json` with the same metadata-only algorithm. Require aggregate before/after identity, exact 25 commit paths, clean worktree, committed evidence base binding, request evidence hash, and no App/data/DB/runtime mutation.

- [ ] **Step 4: Publish immutable final attestation**

Create and independently validate `phase_0_3_attestation.json` with schema `PFIV025Phase03AttestationV1` and at least:

```text
contract_id=PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE
acceptance_id=ACC-PFI-V025-S0-P03-GAP-EVIDENCE
conflict_id=PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE
override_id=PFI-V025-S0-P03-GOVERNANCE-COMPANIONS
phase_base=$PHASE_BASE
phase_commit=$PHASE_COMMIT
status=resolved_by_approved_override
blocks_phase_candidate=false
remote_pfi_drift=false
clean_worktree=true
commit_content_verified=true
no_side_effect_postcheck=true
contains_private_values=false
```

Bind CI attestation path/hash, final remote/base/hydration facts, ref/FETCH_HEAD/shallow before/after hashes, exact changed files/hash, guard evidence path/hash, and Australia/Sydney attested time. Publish with no-clobber semantics under a Phase lock; never overwrite a prior final. Do not add external artifacts to Git or back-write them into tracked evidence.

Steps 2–4 execute through this single fail-closed block. A failed attempt is never reused; rerun Task 9 Step 1 to create a new attempt while preserving the original baseline:

```bash
set -euo pipefail
umask 077
PHASE_COMMIT="$(git rev-parse HEAD)"
PHASE_BASE="$(jq -er '.git_commit' PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json)"
test "$(git rev-parse "$PHASE_COMMIT^")" = "$PHASE_BASE"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
RUN_GUARD_PARENT="/private/tmp/pfi-v025-s0p03-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
RUN_GUARD_ROOT="$(PFI/.venv/bin/python -B - "$RUN_GUARD_PARENT" "$PHASE_BASE" <<'PY'
import hashlib, json, sys
from pathlib import Path
parent, base = Path(sys.argv[1]), sys.argv[2]
pointer = parent / "current.path"
assert pointer.is_file() and not pointer.is_symlink()
run = Path(pointer.read_text(encoding="utf-8").strip())
assert run.parent == parent and not run.is_symlink()
state = json.loads((run / "run_state.json").read_text(encoding="utf-8"))
assert state["phase_base"] == base and state["status"] == "baseline_complete"
for field, name in {"before_sha256":"before.json","git_state_before_sha256":"git_state_before.json","governance_baseline_sha256":"governance_baseline.json"}.items():
    path = run / name
    assert path.is_file() and not path.is_symlink()
    assert state[field] == hashlib.sha256(path.read_bytes()).hexdigest()
print(run)
PY
)"
RUN_STATE="$RUN_GUARD_ROOT/run_state.json"
test -f "$RUN_STATE"
COMMON_GIT_DIR="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)"
ATTEST_PARENT="$COMMON_GIT_DIR/codex-review/pfi-v025/stage_0/phase_0_3"
ATTEST_POINTER="$ATTEST_PARENT/current.path"
ATTEST_DIR="$(PFI/.venv/bin/python -B - "$RUN_STATE" "$ATTEST_POINTER" "$ATTEST_PARENT" "$PHASE_COMMIT" <<'PY'
import json
import sys
from pathlib import Path
state_path, pointer, parent = map(Path, sys.argv[1:4])
commit = sys.argv[4]
assert pointer.is_file() and not pointer.is_symlink()
attempt = Path(pointer.read_text(encoding="utf-8").strip())
assert attempt.parent == parent and attempt.name.startswith(f"{commit}.attempt.") and not attempt.is_symlink()
state = json.loads(state_path.read_text(encoding="utf-8"))
assert state["attest_dir"] == str(attempt)
print(attempt)
PY
)"
test -d "$ATTEST_DIR"
CI_ATTESTATION="$ATTEST_DIR/phase_0_3_ci_attestation.json"
test -f "$CI_ATTESTATION"
ATTEMPT_NAME="$(basename "$ATTEST_DIR")"
AFTER_PATH="$RUN_GUARD_ROOT/after-$ATTEMPT_NAME.json"
NO_SIDE_PATH="$ATTEST_DIR/no_side_effect_fingerprints.json"
REMOTE_PROOF="$ATTEST_DIR/final_remote_proof.json"
test ! -e "$AFTER_PATH"
test ! -e "$NO_SIDE_PATH"
test ! -e "$REMOTE_PROOF"

PFI/.venv/bin/python -B - "$RUN_GUARD_ROOT/before.json" "$AFTER_PATH" "$NO_SIDE_PATH" <<'PY'
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

sys.excepthook = lambda *_: print("phase_0_3_after_snapshot=FAIL|reason=redacted", file=sys.stderr)

before_path, after_path, output_path = map(Path, sys.argv[1:4])
root = Path.cwd()
targets = {
    "user_pfi": Path.home() / ".pfi",
    "applications_app": Path("/Applications/PFI.app"),
    "desktop_app": Path.home() / "Desktop/PFI.app",
    "downloads_app": Path.home() / "Downloads/PFI.app",
    "repo_app": root / "PFI/macos/PFI.app",
    "repo_data": root / "PFI/data",
    "repo_metadatabase": root / "PFI/MetaDatabase",
    "working_metadatabase": root / "MetaDatabase/PFI",
}

def fingerprint(path: Path) -> dict:
    digest = hashlib.sha256()
    count = 0
    if not path.exists() and not path.is_symlink():
        return {"state": "missing", "entry_count": 0, "metadata_sha256": hashlib.sha256(b"missing").hexdigest()}
    pending = [path]
    while pending:
        current = pending.pop()
        value = current.lstat()
        relative = "." if current == path else current.relative_to(path).as_posix()
        payload = [relative, str(stat.S_IFMT(value.st_mode)), str(value.st_mode & 0o7777), str(value.st_size), str(value.st_mtime_ns)]
        if current.is_symlink():
            payload.append(os.readlink(current))
        digest.update("\0".join(payload).encode("utf-8", "surrogateescape"))
        count += 1
        if current.is_dir() and not current.is_symlink():
            pending.extend(sorted(current.iterdir(), reverse=True))
    return {"state": "present", "entry_count": count, "metadata_sha256": digest.hexdigest()}

def runtime_fingerprint() -> dict:
    records = []
    for port in (8501, 8502):
        probe = subprocess.run(
            ["lsof", "-nP", "-a", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fp"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        assert probe.returncode in (0, 1)
        pids = sorted({line[1:] for line in probe.stdout.splitlines() if line.startswith("p") and line[1:].isdigit()})
        for pid in pids:
            cwd_probe = subprocess.run(
                ["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
            )
            assert cwd_probe.returncode in (0, 1)
            cwd = next((line[1:] for line in cwd_probe.stdout.splitlines() if line.startswith("n")), "UNAVAILABLE")
            records.append(f"{port}\0{pid}\0{cwd}")
    payload = "\n".join(sorted(records)).encode("utf-8", "surrogateescape")
    return {
        "state": "present" if records else "absent",
        "listener_count": len(records),
        "metadata_sha256": hashlib.sha256(payload).hexdigest(),
    }

before = json.loads(before_path.read_text(encoding="utf-8"))
after = {key: fingerprint(path) for key, path in targets.items()}
after["runtime_listeners"] = runtime_fingerprint()
assert after == before
with after_path.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(after, sort_keys=True) + "\n")
after_path.chmod(0o600)
proof = {
    "schema": "PFIV025Phase03NoSideEffectV1",
    "before_ref": str(before_path),
    "before_sha256": hashlib.sha256(before_path.read_bytes()).hexdigest(),
    "after_ref": str(after_path),
    "after_sha256": hashlib.sha256(after_path.read_bytes()).hexdigest(),
    "identical": True,
    "runtime_unchanged": True,
    "contains_private_values": False,
}
with output_path.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(proof, sort_keys=True) + "\n")
PY

PFI/.venv/bin/python -B - "$REMOTE_PROOF" "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

output = Path(sys.argv[1])
base, commit = sys.argv[2:4]
env = dict(os.environ)
env["GIT_NO_LAZY_FETCH"] = "1"
env["GIT_TERMINAL_PROMPT"] = "0"

def file_state(path: Path) -> dict:
    if not path.exists():
        return {"state": "missing"}
    return {"state": "present", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

refs_before_raw = subprocess.check_output(["git", "for-each-ref", "--format=%(refname) %(objectname)"])
refs_before = hashlib.sha256(refs_before_raw).hexdigest()
fetch_path = Path(subprocess.check_output(["git", "rev-parse", "--git-path", "FETCH_HEAD"], text=True).strip())
shallow_path = Path(subprocess.check_output(["git", "rev-parse", "--git-path", "shallow"], text=True).strip())
fetch_before = file_state(fetch_path)
shallow_before = file_state(shallow_path)
live = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], text=True).split()[0]
hydrated = False
exists = subprocess.run(["git", "cat-file", "-e", f"{live}^{{commit}}"], env=env, check=False).returncode == 0
if not exists:
    hydrated = True
    subprocess.run([
        "git", "-c", "maintenance.auto=false", "-c", "fetch.writeCommitGraph=false",
        "-c", "fetch.recurseSubmodules=false", "fetch", "--no-auto-maintenance",
        "--no-write-commit-graph", "--no-recurse-submodules", "--no-prune",
        "--no-prune-tags", "--no-write-fetch-head", "--no-tags", "origin", live,
    ], env=env, check=True)
subprocess.run(["git", "cat-file", "-e", f"{live}^{{commit}}"], env=env, check=True)
refs_after_raw = subprocess.check_output(["git", "for-each-ref", "--format=%(refname) %(objectname)"])
refs_after = hashlib.sha256(refs_after_raw).hexdigest()
fetch_after = file_state(fetch_path)
shallow_after = file_state(shallow_path)
assert refs_after == refs_before and fetch_after == fetch_before and shallow_after == shallow_before
remote_base = subprocess.check_output(["git", "merge-base", commit, live], text=True, env=env).strip()
subprocess.run(["git", "diff", "--quiet", f"{remote_base}..{live}", "--", "PFI"], env=env, check=True)
proof = {
    "schema": "PFIV025Phase03RemoteProofV1",
    "phase_base": base,
    "phase_commit": commit,
    "final_live_main": live,
    "final_remote_base": remote_base,
    "final_remote_object_hydration_performed": hydrated,
    "refs_sha256_before": refs_before,
    "refs_sha256_after": refs_after,
    "fetch_head_before": fetch_before,
    "fetch_head_after": fetch_after,
    "shallow_before": shallow_before,
    "shallow_after": shallow_after,
    "remote_pfi_drift": False,
    "observed_at": datetime.now(ZoneInfo("Australia/Sydney")).isoformat(),
}
with output.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(proof, sort_keys=True) + "\n")
PY

CANDIDATE_PATH="$ATTEST_DIR/phase_0_3_attestation.blocking.json"
PUBLICATION_SOURCE="$ATTEST_DIR/phase_0_3_attestation.publication-source.json"

# Stage A: generate one blocking candidate only.
PFI/.venv/bin/python -B - \
  "$RUN_STATE" "$CI_ATTESTATION" "$NO_SIDE_PATH" "$REMOTE_PROOF" \
  "$PHASE_BASE" "$PHASE_COMMIT" "$ATTEST_POINTER" "$CANDIDATE_PATH" <<'PY'
import hashlib, json, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.excepthook = lambda *_: print("phase_0_3_publication=FAIL|reason=redacted", file=sys.stderr)

state_path, ci_path, no_side_path, remote_path = map(Path, sys.argv[1:5])
base, commit = sys.argv[5:7]
pointer, candidate_path = map(Path, sys.argv[7:9])
state = json.loads(state_path.read_text(encoding="utf-8"))
attempt = Path(state["attest_dir"])
assert candidate_path.parent == ci_path.parent == no_side_path.parent == remote_path.parent == attempt
assert pointer.is_file() and not pointer.is_symlink()
assert Path(pointer.read_text(encoding="utf-8").strip()) == attempt
ci = json.loads(ci_path.read_text(encoding="utf-8"))
no_side = json.loads(no_side_path.read_text(encoding="utf-8"))
remote = json.loads(remote_path.read_text(encoding="utf-8"))
ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt")
evidence_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json")
request_path = Path("PFI/docs/pfi_v025/stage_0/acceptance_request.md")
ledger = ledger_path.read_text(encoding="utf-8").splitlines()
actual = subprocess.check_output(["git", "diff", "--name-only", f"{base}..{commit}"], text=True).splitlines()
assert len(ledger) == 25 and ledger == sorted(ledger) == actual
assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == commit
assert subprocess.check_output(["git", "rev-parse", f"{commit}^"], text=True).strip() == base
assert not subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], text=True).splitlines()
assert ci["phase_base"] == remote["phase_base"] == base and ci["phase_commit"] == remote["phase_commit"] == commit
assert ci["status"] == "ci_pass_pending_final_stop_checks" and ci["blocks_phase_candidate"] is True
assert ci["decision"] == "SHIP" and ci["selected_projects"] == ["PFI"]
assert ci["legacy_exit_code"] == 0 and ci["selector_parity"] is True and ci["zero_tracked_write"] is True
assert state["status"] == "baseline_complete"
ci_sha = hashlib.sha256(ci_path.read_bytes()).hexdigest()
assert state["ci_attestation_sha256"] == ci_sha
guard = state_path.parent
guard_files = {
    "guard_before": (guard / "before.json", "before_sha256"),
    "guard_git_state": (guard / "git_state_before.json", "git_state_before_sha256"),
    "governance_baseline": (guard / "governance_baseline.json", "governance_baseline_sha256"),
}
for path, field in guard_files.values():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == state[field]
assert no_side["identical"] is True and no_side["runtime_unchanged"] is True and no_side["contains_private_values"] is False
assert Path(no_side["before_ref"]) == guard_files["guard_before"][0]
assert no_side["before_sha256"] == state["before_sha256"]
assert hashlib.sha256(Path(no_side["after_ref"]).read_bytes()).hexdigest() == no_side["after_sha256"]
assert json.loads(Path(no_side["before_ref"]).read_text(encoding="utf-8")) == json.loads(Path(no_side["after_ref"]).read_text(encoding="utf-8"))
assert remote["remote_pfi_drift"] is False
assert remote["refs_sha256_before"] == remote["refs_sha256_after"]
assert remote["fetch_head_before"] == remote["fetch_head_after"]
assert remote["shallow_before"] == remote["shallow_after"]
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
assert evidence["git_commit"] == base
assert evidence["git_commit_semantics"] == "implementation_base_before_phase_commit"
assert evidence["status"] == "candidate_pass"
assert sorted(evidence["changed_files"]) == ledger
evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
request_sha = hashlib.sha256(request_path.read_bytes()).hexdigest()
request = request_path.read_text(encoding="utf-8")
assert request.splitlines().count(f"evidence_sha256={evidence_sha}") == 1
assert "candidate_commit_binding=external_attestation_required" in request
for path in (evidence_path, request_path):
    committed = subprocess.check_output(["git", "show", f"{commit}:{path.as_posix()}"])
    assert committed == path.read_bytes()

candidate = {
    "schema": "PFIV025Phase03AttestationCandidateV1",
    "contract_id": "PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE",
    "acceptance_id": "ACC-PFI-V025-S0-P03-GAP-EVIDENCE",
    "conflict_id": "PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE",
    "override_id": "PFI-V025-S0-P03-GOVERNANCE-COMPANIONS",
    "phase_base": base,
    "phase_commit": commit,
    "ci_attestation_ref": str(ci_path), "ci_attestation_sha256": ci_sha,
    "ci_stable_summary_hash": ci["ci_stable_summary_hash"],
    "no_side_effect_artifact_ref": str(no_side_path),
    "no_side_effect_artifact_sha256": hashlib.sha256(no_side_path.read_bytes()).hexdigest(),
    "remote_proof_ref": str(remote_path), "remote_proof_sha256": hashlib.sha256(remote_path.read_bytes()).hexdigest(),
    "run_state_ref": str(state_path), "run_state_sha256": hashlib.sha256(state_path.read_bytes()).hexdigest(),
    "guard_before_ref": str(guard_files["guard_before"][0]), "guard_before_sha256": state["before_sha256"],
    "guard_git_state_ref": str(guard_files["guard_git_state"][0]), "guard_git_state_sha256": state["git_state_before_sha256"],
    "governance_baseline_ref": str(guard_files["governance_baseline"][0]), "governance_baseline_sha256": state["governance_baseline_sha256"],
    "evidence_ref": str(evidence_path), "evidence_sha256": evidence_sha,
    "evidence_git_commit": evidence["git_commit"],
    "evidence_git_commit_semantics": evidence["git_commit_semantics"],
    "acceptance_request_ref": str(request_path), "acceptance_request_sha256": request_sha,
    "changed_files": ledger, "changed_files_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
    "initial_live_main": state["initial_live_main"],
    "initial_remote_object_hydration_performed": state["initial_remote_object_hydration_performed"],
    "final_live_main": remote["final_live_main"], "final_remote_base": remote["final_remote_base"],
    "final_remote_object_hydration_performed": remote["final_remote_object_hydration_performed"],
    "refs_sha256_before": remote["refs_sha256_before"], "refs_sha256_after": remote["refs_sha256_after"],
    "fetch_head_before": remote["fetch_head_before"], "fetch_head_after": remote["fetch_head_after"],
    "shallow_before": remote["shallow_before"], "shallow_after": remote["shallow_after"],
    "remote_pfi_drift": False, "clean_worktree": True, "commit_content_verified": True,
    "no_side_effect_postcheck": True, "runtime_unchanged": True,
    "status": "final_checks_pass_pending_publication", "blocks_phase_candidate": True,
    "contains_private_values": False,
    "attested_at": datetime.now(ZoneInfo("Australia/Sydney")).isoformat(),
}
with candidate_path.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
PY

# Stage B: a separate process independently validates the blocking candidate and creates one publication source.
PFI/.venv/bin/python -B - "$CANDIDATE_PATH" "$PUBLICATION_SOURCE" "$ATTEST_POINTER" "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import hashlib, json, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
candidate_path, source_path, pointer = map(Path, sys.argv[1:4])
base, commit = sys.argv[4:6]
c = json.loads(candidate_path.read_text(encoding="utf-8"))
assert c["schema"] == "PFIV025Phase03AttestationCandidateV1"
assert c["contract_id"] == "PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE"
assert c["acceptance_id"] == "ACC-PFI-V025-S0-P03-GAP-EVIDENCE"
assert c["conflict_id"] == "PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE"
assert c["override_id"] == "PFI-V025-S0-P03-GOVERNANCE-COMPANIONS"
assert c["phase_base"] == base and c["phase_commit"] == commit
assert c["status"] == "final_checks_pass_pending_publication" and c["blocks_phase_candidate"] is True
assert c["contains_private_values"] is False and c["runtime_unchanged"] is True
ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt")
ledger = ledger_path.read_text(encoding="utf-8").splitlines()
assert len(ledger) == 25 and ledger == sorted(ledger) == c["changed_files"]
assert hashlib.sha256(ledger_path.read_bytes()).hexdigest() == c["changed_files_sha256"]
assert subprocess.check_output(["git", "diff", "--name-only", f"{base}..{commit}"], text=True).splitlines() == ledger
attempt = candidate_path.parent
assert source_path.parent == attempt and pointer.is_file() and not pointer.is_symlink()
assert Path(pointer.read_text(encoding="utf-8").strip()) == attempt
for ref_key, sha_key in (
    ("ci_attestation_ref","ci_attestation_sha256"),("no_side_effect_artifact_ref","no_side_effect_artifact_sha256"),
    ("remote_proof_ref","remote_proof_sha256"),("run_state_ref","run_state_sha256"),
    ("guard_before_ref","guard_before_sha256"),("guard_git_state_ref","guard_git_state_sha256"),
    ("governance_baseline_ref","governance_baseline_sha256"),("evidence_ref","evidence_sha256"),
    ("acceptance_request_ref","acceptance_request_sha256"),
):
    assert hashlib.sha256(Path(c[ref_key]).read_bytes()).hexdigest() == c[sha_key]
evidence = json.loads(Path(c["evidence_ref"]).read_text(encoding="utf-8"))
assert evidence["git_commit"] == c["evidence_git_commit"] == base
assert evidence["git_commit_semantics"] == c["evidence_git_commit_semantics"] == "implementation_base_before_phase_commit"
assert evidence["status"] == "candidate_pass"
request = Path(c["acceptance_request_ref"]).read_text(encoding="utf-8")
assert request.splitlines().count(f'evidence_sha256={c["evidence_sha256"]}') == 1
ci = json.loads(Path(c["ci_attestation_ref"]).read_text(encoding="utf-8"))
assert ci["status"] == "ci_pass_pending_final_stop_checks" and ci["blocks_phase_candidate"] is True
assert ci["decision"] == "SHIP" and ci["selected_projects"] == ["PFI"]
no_side = json.loads(Path(c["no_side_effect_artifact_ref"]).read_text(encoding="utf-8"))
assert no_side["identical"] is True and no_side["runtime_unchanged"] is True
assert Path(no_side["before_ref"]) == Path(c["guard_before_ref"])
assert no_side["before_sha256"] == c["guard_before_sha256"]
assert hashlib.sha256(Path(no_side["after_ref"]).read_bytes()).hexdigest() == no_side["after_sha256"]
assert json.loads(Path(no_side["before_ref"]).read_text(encoding="utf-8")) == json.loads(Path(no_side["after_ref"]).read_text(encoding="utf-8"))
remote = json.loads(Path(c["remote_proof_ref"]).read_text(encoding="utf-8"))
assert remote["remote_pfi_drift"] is False
assert remote["refs_sha256_before"] == remote["refs_sha256_after"]
assert remote["fetch_head_before"] == remote["fetch_head_after"] and remote["shallow_before"] == remote["shallow_after"]
assert subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip() == commit
assert subprocess.check_output(["git","rev-parse",f"{commit}^"], text=True).strip() == base
publication = dict(c)
publication.update({
    "schema": "PFIV025Phase03AttestationV1",
    "status": "resolved_by_approved_override",
    "blocks_phase_candidate": False,
    "blocking_candidate_ref": str(candidate_path),
    "blocking_candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    "publication_source_ref": str(source_path),
    "independently_validated_at": datetime.now(ZoneInfo("Australia/Sydney")).isoformat(),
})
with source_path.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(publication, ensure_ascii=False, indent=2) + "\n")
verified = json.loads(source_path.read_text(encoding="utf-8"))
assert verified["status"] == "resolved_by_approved_override" and verified["blocks_phase_candidate"] is False
assert verified["publication_source_ref"] == str(source_path)
publication_additions = {
    "blocking_candidate_ref", "blocking_candidate_sha256",
    "publication_source_ref", "independently_validated_at",
}
assert set(verified) == set(c) | publication_additions
for key, value in c.items():
    if key not in {"schema", "status", "blocks_phase_candidate"}:
        assert verified[key] == value, key
PY

# Stage C: under the fixed Phase lock, revalidate every bound fact before the no-clobber hard-link.
PFI/.venv/bin/python -B - \
  "$CANDIDATE_PATH" "$PUBLICATION_SOURCE" "$RUN_STATE" "$ATTEST_POINTER" \
  "$ATTEST_PARENT" "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import fcntl, hashlib, json, os, stat, subprocess, sys
from pathlib import Path
sys.excepthook = lambda *_: print("phase_0_3_publish_lock=FAIL|reason=redacted", file=sys.stderr)
candidate_path, source_path, state_path, pointer, parent = map(Path, sys.argv[1:6])
base, commit = sys.argv[6:8]
attempt = candidate_path.parent
assert source_path.parent == attempt and attempt.parent == parent and attempt.name.startswith(f"{commit}.attempt.")
assert not attempt.is_symlink() and source_path.is_file() and not source_path.is_symlink()

def file_state(path: Path) -> dict:
    return {"state":"missing"} if not path.exists() else {"state":"present","sha256":hashlib.sha256(path.read_bytes()).hexdigest()}

def current_fingerprint() -> dict:
    root = Path.cwd()
    targets = {
        "user_pfi": Path.home()/".pfi", "applications_app": Path("/Applications/PFI.app"),
        "desktop_app": Path.home()/"Desktop/PFI.app", "downloads_app": Path.home()/"Downloads/PFI.app",
        "repo_app": root/"PFI/macos/PFI.app", "repo_data": root/"PFI/data",
        "repo_metadatabase": root/"PFI/MetaDatabase", "working_metadatabase": root/"MetaDatabase/PFI",
    }
    result = {}
    for label, path in targets.items():
        digest, count = hashlib.sha256(), 0
        if not path.exists() and not path.is_symlink():
            result[label] = {"state":"missing","entry_count":0,"metadata_sha256":hashlib.sha256(b"missing").hexdigest()}
            continue
        pending = [path]
        while pending:
            item = pending.pop(); value = item.lstat()
            relative = "." if item == path else item.relative_to(path).as_posix()
            payload = [relative,str(stat.S_IFMT(value.st_mode)),str(value.st_mode & 0o7777),str(value.st_size),str(value.st_mtime_ns)]
            if item.is_symlink(): payload.append(os.readlink(item))
            digest.update("\0".join(payload).encode("utf-8","surrogateescape")); count += 1
            if item.is_dir() and not item.is_symlink(): pending.extend(sorted(item.iterdir(), reverse=True))
        result[label] = {"state":"present","entry_count":count,"metadata_sha256":digest.hexdigest()}
    records = []
    for port in (8501,8502):
        probe = subprocess.run(["lsof","-nP","-a",f"-iTCP:{port}","-sTCP:LISTEN","-Fp"],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False)
        assert probe.returncode in (0,1)
        for pid in sorted({line[1:] for line in probe.stdout.splitlines() if line.startswith("p") and line[1:].isdigit()}):
            cwd_probe = subprocess.run(["lsof","-a","-p",pid,"-d","cwd","-Fn"],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False)
            assert cwd_probe.returncode in (0,1)
            cwd = next((line[1:] for line in cwd_probe.stdout.splitlines() if line.startswith("n")),"UNAVAILABLE")
            records.append(f"{port}\0{pid}\0{cwd}")
    payload = "\n".join(sorted(records)).encode("utf-8","surrogateescape")
    result["runtime_listeners"] = {"state":"present" if records else "absent","listener_count":len(records),"metadata_sha256":hashlib.sha256(payload).hexdigest()}
    return result

with (parent/"phase.lock").open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    state_lock_path = state_path.parent / "run_state.lock"
    state_lock_path.touch(mode=0o600, exist_ok=True)
    state_lock_path.chmod(0o600)
    state_lock_stream = state_lock_path.open("r+", encoding="utf-8")
    fcntl.flock(state_lock_stream.fileno(), fcntl.LOCK_EX)
    assert not list(parent.glob("*.attempt.*/phase_0_3_attestation.json"))
    assert pointer.is_file() and not pointer.is_symlink()
    assert Path(pointer.read_text(encoding="utf-8").strip()) == attempt
    c = json.loads(candidate_path.read_text(encoding="utf-8"))
    publication_raw = source_path.read_bytes()
    p = json.loads(publication_raw)
    assert c["status"] == "final_checks_pass_pending_publication" and c["blocks_phase_candidate"] is True
    assert p["schema"] == "PFIV025Phase03AttestationV1"
    assert p["contract_id"] == "PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE"
    assert p["acceptance_id"] == "ACC-PFI-V025-S0-P03-GAP-EVIDENCE"
    assert p["conflict_id"] == "PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE"
    assert p["override_id"] == "PFI-V025-S0-P03-GOVERNANCE-COMPANIONS"
    assert p["phase_base"] == base and p["phase_commit"] == commit
    assert p["status"] == "resolved_by_approved_override" and p["blocks_phase_candidate"] is False
    assert p["contains_private_values"] is False and p["publication_source_ref"] == str(source_path)
    assert p["blocking_candidate_ref"] == str(candidate_path)
    assert hashlib.sha256(candidate_path.read_bytes()).hexdigest() == p["blocking_candidate_sha256"]
    publication_additions = {
        "blocking_candidate_ref", "blocking_candidate_sha256",
        "publication_source_ref", "independently_validated_at",
    }
    assert set(p) == set(c) | publication_additions
    for key, value in c.items():
        if key not in {"schema", "status", "blocks_phase_candidate"}:
            assert p[key] == value, key
    state_raw = state_path.read_bytes(); state = json.loads(state_raw)
    assert hashlib.sha256(state_raw).hexdigest() == p["run_state_sha256"]
    assert state["attest_dir"] == str(attempt) and state["ci_attestation_sha256"] == p["ci_attestation_sha256"]
    for ref_key, sha_key in (
        ("ci_attestation_ref","ci_attestation_sha256"),("no_side_effect_artifact_ref","no_side_effect_artifact_sha256"),
        ("remote_proof_ref","remote_proof_sha256"),("guard_before_ref","guard_before_sha256"),
        ("guard_git_state_ref","guard_git_state_sha256"),("governance_baseline_ref","governance_baseline_sha256"),
        ("evidence_ref","evidence_sha256"),("acceptance_request_ref","acceptance_request_sha256"),
    ):
        assert hashlib.sha256(Path(p[ref_key]).read_bytes()).hexdigest() == p[sha_key]
    evidence = json.loads(Path(p["evidence_ref"]).read_text(encoding="utf-8"))
    assert evidence["git_commit"] == p["evidence_git_commit"] == base
    assert evidence["git_commit_semantics"] == p["evidence_git_commit_semantics"] == "implementation_base_before_phase_commit"
    assert evidence["status"] == "candidate_pass"
    request = Path(p["acceptance_request_ref"]).read_text(encoding="utf-8")
    assert request.splitlines().count(f'evidence_sha256={p["evidence_sha256"]}') == 1
    ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt")
    ledger = ledger_path.read_text(encoding="utf-8").splitlines()
    assert len(ledger) == 25 and ledger == sorted(ledger) == p["changed_files"]
    assert hashlib.sha256(ledger_path.read_bytes()).hexdigest() == p["changed_files_sha256"]
    assert subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip() == commit
    assert subprocess.check_output(["git","rev-parse",f"{commit}^"],text=True).strip() == base
    assert not subprocess.check_output(["git","status","--porcelain=v1","--untracked-files=all"],text=True).splitlines()
    assert subprocess.check_output(["git","diff","--name-only",f"{base}..{commit}"],text=True).splitlines() == ledger
    ci = json.loads(Path(p["ci_attestation_ref"]).read_text(encoding="utf-8"))
    assert ci["status"] == "ci_pass_pending_final_stop_checks" and ci["blocks_phase_candidate"] is True
    assert ci["decision"] == "SHIP" and ci["selected_projects"] == ["PFI"] and ci["zero_tracked_write"] is True
    no_side = json.loads(Path(p["no_side_effect_artifact_ref"]).read_text(encoding="utf-8"))
    assert no_side["identical"] is True and no_side["runtime_unchanged"] is True
    assert Path(no_side["before_ref"]) == Path(p["guard_before_ref"])
    assert no_side["before_sha256"] == p["guard_before_sha256"]
    assert hashlib.sha256(Path(no_side["after_ref"]).read_bytes()).hexdigest() == no_side["after_sha256"]
    assert json.loads(Path(no_side["before_ref"]).read_text(encoding="utf-8")) == json.loads(Path(no_side["after_ref"]).read_text(encoding="utf-8"))
    assert current_fingerprint() == json.loads(Path(no_side["before_ref"]).read_text(encoding="utf-8"))
    remote = json.loads(Path(p["remote_proof_ref"]).read_text(encoding="utf-8"))
    assert remote["remote_pfi_drift"] is False
    assert remote["refs_sha256_before"] == remote["refs_sha256_after"]
    assert remote["fetch_head_before"] == remote["fetch_head_after"] and remote["shallow_before"] == remote["shallow_after"]
    live_now = subprocess.check_output(["git","ls-remote","origin","refs/heads/main"],text=True).split()[0]
    assert live_now == remote["final_live_main"]
    refs_now = hashlib.sha256(subprocess.check_output(["git","for-each-ref","--format=%(refname) %(objectname)"])).hexdigest()
    assert refs_now == remote["refs_sha256_after"]
    fetch_path = Path(subprocess.check_output(["git","rev-parse","--git-path","FETCH_HEAD"],text=True).strip())
    shallow_path = Path(subprocess.check_output(["git","rev-parse","--git-path","shallow"],text=True).strip())
    assert file_state(fetch_path) == remote["fetch_head_after"] and file_state(shallow_path) == remote["shallow_after"]
    final_path = attempt/"phase_0_3_attestation.json"
    os.link(source_path, final_path)
    state_lock_stream.close()

assert final_path.read_bytes() == publication_raw
assert final_path.stat().st_ino == source_path.stat().st_ino
print(f"external_attestation_path={final_path}")
print("external_attestation_sha256=" + hashlib.sha256(publication_raw).hexdigest())
PY
```

- [ ] **Step 5: Stop at the Phase boundary**

Final authoritative statement for this run:

```text
Stage 0 / Phase 0.3 candidate result only; Stage 0 whole-stage review and Stage 1 remain not_started in this run.
```

No push, no App install, no Stage 0 whole-stage review, and no Stage 1 action.

## Final Acceptance Matrix

| target | required result |
|---|---|
| S0-P3-T1 | 38 evidence-bound findings with frozen status/priority/source/history coverage |
| S0-P3-T2 | 28 eligible findings mapped once to 13 executable P0/P1 gaps; P2 executable=0 |
| S0-P3-T3 | exact Stage 0 evidence pack, schema/privacy/hash/governance pass |
| S0-P3-T4 | request prepared and execution stopped before whole-stage review/Stage 1 |
| Scope | exact 25 paths; no product/data/App/runtime/ref/push/install mutation |
| Governance | selective pre/postcommit PFI validation pass; registry invariants preserved |
| External binding | immutable Phase 0.3 CI + final attestation, resolved override, no side effect |
| User acceptance | still required after the separate Stage 0 whole-stage review cycle; not fabricated here |

## Rollback

- Before implementation commit: remove only the exact 13 newly created core paths and restore only the 12 companion hunks from `$PHASE_BASE`; preserve unrelated work.
- After commit: use an append-only-safe compensating commit; never rewrite event history, remote history, or external attestations.
- Never delete or move user data, DB, App entries, or prior Phase evidence as rollback.

## Stop Conditions

- Any 26th path or protected path.
- Any invalid source/task/history mapping, private output, hash cycle, schema failure, registry value drift, event rewrite, missing companion, review blocker, or unexplained remote/state drift.
- Any need to mutate/read beyond the approved aggregate private-data boundary.
- Any automatic transition into Stage 0 whole-stage review or Stage 1.
