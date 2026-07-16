# Repository Hygiene

`governance/repository_hygiene_policy.json` is the only machine-readable
retention truth. This file explains the reviewed P45 migration without creating
a second exception list.

## Current accepted baseline

`TSK.CodexProject.REPO1.0009` P45 binds the fail-closed policy to reachable
parent commit `6b83d8e2b653e609233286338e3a810816d60543`, tree
`84c1c17f84722bef9b00bd720d48126b417850c6`. A fresh clone can therefore load
the baseline tree and compare exact blob OIDs.

The policy-bound candidate audit reports:

- tracked objects: 14,293
- objects over 1 MiB: 65 / 465,742,985 bytes
- archive-shaped objects: 36
- tracked runtime noise: 0
- executable backup producers: 0
- policy violations: 0
- history rewrite: `false` / `DEFERRED`

Git pack size is observational only; removing current-tree files does not purge
historical objects.

## P45 reviewed migration

- Preserved the complete validated Clean Memory V3 TaskPack on current
  `main`, while retaining the newer repository-split state.
- Kept `LinzeColin/AgentDatabase` public and required credential/public-safety
  gates; no repository visibility change or private Governance write occurred.
- Removed five duplicate/oversized KM_IDSystem backup containers from the
  current tree. Exact recovery remains available from reachable commit
  `f37ae7af823173aef8a34d9eb491c5606ac4d929`; blob and SHA-256 identities are
  documented in the KM_IDSystem restore guide.
- Preserved three intentionally absent OpenAIDatabase root human views instead
  of restoring files deleted by the newer split lineage.
- Reviewed existing PFI reports/traces, the v0.2.5 source TaskPack, and arxiv
  pursuing-goal evidence into baseline-OID-only rules. Their byte ceilings match
  the largest accepted baseline object; any new path or byte change still fails.
- Kept the global regular-file ceiling at 1,048,576 bytes.

## Fail-closed behavior

1. A regular tracked blob over 1 MiB needs exactly one reviewed `large` rule.
2. Every archive needs exactly one reviewed `archive` rule.
3. Retained paths must match their baseline Git blob OID and per-rule size cap.
4. Bundle/WAL/SHM/cache/build/coverage/temp/backup outputs fail.
5. Executable source that creates whole-repository bundles or mirror clones fails.
6. No history rewrite or force update is authorized by this task.

Run the exact staged-tree gate:

```bash
tree=$(git write-tree)
python3 -B scripts/repository_hygiene_audit.py --root . --tree-ish "$tree"
```

## Parameters

| Parameter | Value |
|---|---:|
| `regular_blob_max_bytes` | 1,048,576 |
| PFI visual/archive maximum | 12,680,824 |
| PFI v0.2.5 source TaskPack maximum | 86,942 |
| arxiv pursuing-goal evidence maximum | 1,556,045 |
| runtime-noise tolerance | 0 |
| executable backup-producer tolerance | 0 |
| new/modified retained-object tolerance | 0 |

These are deterministic repository controls, not probabilistic model settings.
LFS, Release upload, remote publication, force-push, and history rewriting are
outside P45.

## Acceptance and rollback

Acceptance requires policy/schema validation, focused negative tests, exact-tree
hygiene PASS, checksum verification, root/public-route regression, Task37
focused tests, workflow security, changed-scope governance, credential scan, and
`git diff --check`.

Before publication, rollback is a normal revert of the two local P45 commits.
Do not restore the removed backup containers or split-deleted files as part of
an unrelated rollback.
