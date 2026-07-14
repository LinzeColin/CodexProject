# Memory Atlas v1.2 Source Provenance

## Current Conclusion

The two original v1.2 inputs have been restored byte-for-byte and are now
available from a repository-portable source package.

| Input | Original SHA-256 | Restored result |
|---|---|---|
| `v1.2_四线14Stage升级_Roadmap.md` | `699a8fe5f99a5edc88fec1f8940c4339f7b9b291bd31830f946f521f80904a71` | Exact match |
| `Memory_Atlas_v1.2_四线14Stage升级_TaskPack.zip` | `38e21ae3e94d860e6a40c70a629c8f7048f889164358df7b184bd8caf7bf2472` | Exact match after restore from `.zip.part` |

The roadmap is byte-identical to
`02_Stage_Phase_Task_Roadmap_含PursuingGoal.md` inside the TaskPack. All 30
payload files match `PACK_MANIFEST.json`; the ZIP also contains
`PACK_MANIFEST.json` and `ZIP_SHA256.txt`, for 32 files total and 83,145
uncompressed bytes.

## Recovery Evidence

The original inputs were observed on 2026-07-07 in Codex task
`019f3b5f-b76a-7df2-bc43-706f89ce3820`:

- Roadmap: 22,261 bytes, SHA-256 `699a8fe5...04a71`.
- TaskPack ZIP: 48,133 bytes, SHA-256 `38e21ae3...2472`.
- ZIP listing: 32 files, 83,145 uncompressed bytes.

The preserved extraction retained file contents, mode and timestamp. Repacking
the 32 sorted paths with Python `zipfile.ZipFile`, `ZIP_DEFLATED`, compression
level 6 and the preserved metadata reproduced the historical ZIP hash exactly.
An exact 256-bit hash match is the authenticity gate; the recovery is not a
content-equivalent substitute.

`ZIP_SHA256.txt` inside the package contains `6b1951eb...0e43`. It does not
match the historically observed containing ZIP and is therefore recorded as
stale package metadata, not used as the authoritative container hash.

## Restore

Run from this directory:

```bash
./restore_taskpack.sh /path/to/output
```

The command restores both original filenames and fails if either SHA-256 does
not match. `SOURCE_MANIFEST.json` is the machine-readable recovery contract.

## Boundary

These are requirements/task-package sources, not runtime data, credentials,
cookies, tokens or browser state. No GitHub push occurs during remediation R0;
the files remain local until the final all-project acceptance gate permits the
single main update.
