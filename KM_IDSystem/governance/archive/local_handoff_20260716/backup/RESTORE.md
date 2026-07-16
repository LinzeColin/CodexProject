# KM_IDS Migration Recovery

Updated: 2026-07-17 Australia/Sydney

## Source identity

- Repository: `LinzeColin/CodexProject`
- Source branch: `codex/ids-v0-1-stages-001-010`
- Source HEAD: `e1679d247986eb03665d440185e04dd56223a364`
- Bundle prerequisite / prior batch baseline: `565babef3a610f289fed0da38b58e550b5707e3e`
- Reachable archive commit: `f37ae7af823173aef8a34d9eb491c5606ac4d929`

## Verify retained recovery material

From this `backup/` directory:

```bash
LC_ALL=C shasum -a 256 -c CHECKSUMS.sha256
gzip -t KM_IDS-local-commits.mbox.gz
gzip -t KM_IDS-main-integration-candidate.mbox.gz
gzip -t KM_IDS-dirty-tracked.patch.gz
```

Restore the original 12-commit series only in an isolated branch with the
required baseline available:

```bash
gzip -dc KM_IDS-local-commits.mbox.gz | git am --3way
```

The current-main replay candidate remains blocked while
`STAGE043-integration-candidate-check.json.txt` reports a red ancestry binding.
Do not activate it as a green Stage043 result.

## Recover removed binary containers from Git history

P45 removed five duplicate or oversized backup containers from the current
public tree. Their source commit is a verified ancestor. Recover a payload only
to a private, owner-controlled path; do not add it back to this repository:

```bash
commit=f37ae7af823173aef8a34d9eb491c5606ac4d929
path=KM_IDSystem/governance/archive/local_handoff_20260716/backup
mkdir -p /private/owner-controlled/km-ids-recovery
git show "$commit:$path/KM_IDS-HEAD-e1679d24-project-snapshot.tar.gz" > /private/owner-controlled/km-ids-recovery/KM_IDS-HEAD-e1679d24-project-snapshot.tar.gz
git show "$commit:$path/KM_IDS-local-commits-565babef-to-e1679d24.bundle" > /private/owner-controlled/km-ids-recovery/KM_IDS-local-commits-565babef-to-e1679d24.bundle
git show "$commit:$path/KM_IDS-main-integration-candidate.bundle" > /private/owner-controlled/km-ids-recovery/KM_IDS-main-integration-candidate.bundle
git show "$commit:$path/KM_IDS-working-tree-overlay.tar.gz" > /private/owner-controlled/km-ids-recovery/KM_IDS-working-tree-overlay.tar.gz
git show "$commit:$path/opme-system-legacy-assets.tar.gz" > /private/owner-controlled/km-ids-recovery/opme-system-legacy-assets.tar.gz
```

Expected identities:

| Payload | Git blob | SHA-256 | Bytes |
|---|---|---|---:|
| `KM_IDS-HEAD-e1679d24-project-snapshot.tar.gz` | `4f7586fd85990d69588643bbce6400f20889388f` | `2b64ea313a9050585ba2fd2261321ebd702a2ae2cd1185e88b013b32d295cb1b` | 2321654 |
| `KM_IDS-local-commits-565babef-to-e1679d24.bundle` | `84854861b57ecf0ac501f0f3bce2bc7a573317d6` | `d145eec8babc6c90f652cbb2556b106e4cbfc9f75bd740446546d7e94032423b` | 455289 |
| `KM_IDS-main-integration-candidate.bundle` | `8f2578838159a39e2bce8403b1591ffe85b8d90e` | `cf97c784441142d5086f4ba90f275554d2a11d4a57783757db2749ca9f877d4c` | 378925 |
| `KM_IDS-working-tree-overlay.tar.gz` | `3c7984e6f53b22f248f93ab21bb2e6f8397fa9ec` | `708da7e0a84c04067c45339fdec6f5d71074ed6d333b465603b3a3404fffc306` | 3328 |
| `opme-system-legacy-assets.tar.gz` | `2745e4b70e9d2b4464c7350ed7612c269f759730` | `57bee433ec510d08593b3defd66cadec27082f21487b5d903f8baeef0ac4f403` | 3204643 |

## Boundaries

- The old machine-local backup path is not required and is not asserted to exist.
- Do not restore repository-split deletions or unreviewed owner work into active main.
- Do not access or upload `IDS_MetaData` content.
- Legacy assets remain archival and are not evidence of real production data.
- Remote synchronization and production acceptance are separate gates.
