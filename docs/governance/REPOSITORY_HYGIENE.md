# Repository Hygiene

This is the owner-readable view of
`governance/repository_hygiene_policy.json`. The JSON policy is the unique
machine-readable truth; this document explains operating intent and does not
create a second exception list.

## Scope and current truth

`TSK.CodexProject.REPO1.0006` governs current-tree large objects, archives,
runtime/cache/generated noise, and the source code that could recreate whole-
repository backups. Its baseline is Git tree
`6a585a21d947c76537bac7c1d62f142482b08787`.

At the implementation base, 53 tracked objects exceeded 1 MiB (465,327,591
bytes total) and five archive-shaped files were tracked. The Git object pack was
about 3.54 GiB because old objects remain in history. Current-tree deletion does
not shrink that pack, and this Task does not rewrite history.

## 功能清单

1. Fail closed when a regular tracked blob exceeds 1 MiB.
2. Permit an existing large object only when it matches exactly one rule with
   owner, purpose, consumer, retention, recovery, confidentiality, maximum
   bytes, and the unchanged baseline Git blob OID.
3. Reject new or modified tar/zip/7z artifacts unless a reviewed migration
   changes the canonical policy.
4. Reject tracked bundle, WAL/SHM, cache, build, coverage, `node_modules`,
   temporary, swap, and backup outputs.
5. Scan executable source and workflows for `git bundle`, bundle creation, and
   mirror-clone producers while excluding inert historical evidence/data.
6. Keep raw session archive generation opt-in and outside the Git repository;
   scheduled Memory Atlas updates export numeric usage and sanitized data only.
7. Report current pack bytes without claiming historical cleanup.

Run the gate from the repository root:

```bash
python3 -B scripts/repository_hygiene_audit.py --root .
```

After staging, audit the exact staged tree with:

```bash
python3 -B scripts/repository_hygiene_audit.py --root . --tree-ish "$(git write-tree)"
```

## 开发记录

| Item | Decision / implementation |
|---|---|
| Task / Acceptance | `TSK.CodexProject.REPO1.0006` / `ACC.CodexProject.REPO1.0006` |
| Base | commit `57cb6bca623d2e01bde1a866140804c283340bd8`, tree `6a585a21d947c76537bac7c1d62f142482b08787` |
| Future bundle producers | Source audit found zero and now blocks introduction in executable source/workflows. |
| Scheduled raw archive producer | Removed `session_history/current-mac-latest` from automatic export and commit targets. Direct raw export requires an explicit destination outside the repository. |
| Safe current deletion | Removed the 150,501-byte numeric-token transfer tar after all extracted data files matched recorded SHA-256 values. The extracted payload remains canonical and reproducible. |
| Retained sensitive archive | The 38,293,927-byte June 2026 session tar is the only verified copy located in this Run. It is baseline-locked, not a runtime input, and must be SHA-256-offloaded privately before any later removal/history rewrite. |
| Existing project large files | Baseline-only exceptions preserve other projects without widening this root Task into their business logic. Any byte change fails until that project performs a reviewed compaction/migration. |
| History rewrite | `DEFERRED`; explicitly prohibited in this Task. |

## 模型参数文件

| Parameter | Value | Rationale |
|---|---:|---|
| `regular_blob_max_bytes` | 1,048,576 | Task acceptance limit for new regular tracked files. |
| Baseline identity | Git tree + blob OID | Detects both new paths and byte changes without hashing sensitive contents into reports. |
| Public raw shard temporary maximum | 47,185,920 | Covers unchanged legacy shards only; new/modified shards still fail. A later data task must re-shard below its stricter limit. |
| Runtime noise tolerance | 0 tracked files | WAL/SHM/cache/build/generated state must remain machine-local. |
| Bundle producer tolerance | 0 source matches | Whole-repository backup producers are prohibited. |
| Archive change tolerance | 0 new/modified archives | Transfer packages belong in private storage or an authorized Release, not the main tree. |
| History rewrite | `false` / `DEFERRED` | Shared-ref rewriting needs a separate owner-authorized incident-grade migration. |

These are deterministic repository-policy parameters, not probabilistic model
settings. Lowering the size cap is allowed; raising it above 1 MiB is rejected
by both the schema and validator.

## LFS, Release, and recovery decision

Git LFS is not enabled by this Task. Adding LFS would introduce a second storage
dependency, would not remove already-published history, and would weaken a clean
clone when LFS objects are unavailable. Future public, rights-owned binary
release artifacts may use an authorized GitHub Release with SHA-256 and owner /
consumer / retention metadata. Sensitive archives use private external storage.
Neither route is performed automatically by this gate.

The retained raw session tar must never be copied over `~/.codex/sessions`.
Before a later history rewrite, first create and verify an independent private
copy, freeze writers, record all affected refs/releases/signatures, rehearse
rollback, and prove a fresh clone.

## Acceptance and rollback

Acceptance requires: policy/schema validation; focused negative tests for new
large objects, changed baseline objects, archives, runtime noise, and backup
producer source; zero live policy violations; OpenAIDatabase exporter regression
tests; clean build/checkout; governance validation; `git diff --check`; and a
clean final worktree.

Rollback before whole-package publication is one normal revert of this Task's
local commit. Do not force-push, delete remote refs, or restore the removed
duplicate tar when rolling back unrelated future work.
