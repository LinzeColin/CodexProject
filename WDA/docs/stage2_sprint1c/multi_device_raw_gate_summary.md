# WDA Stage 2 Sprint 1C Raw Gate Summary

## Decision

Raw Gate decision: **Conditional Investigation**.

Reason: Sprint 1C merged two provided output packages into a true multi-device census, but it did not prove safe DB readability or message readability. Therefore Raw Gate is **not Go**.

## Evidence Used

- `新电脑.zip`: 5,265 classified paths, 3.65 GB total stat size.
- `旧电脑.zip`: 128,088 classified paths, 43.91 GB total stat size.
- No WeChat source directory scan was performed in this run.
- No DB schema was opened and no message content was parsed.

## BackupFiles Check

| Device package | BackupFiles rows | BackupFiles file rows | BackupFiles stat size |
|---|---:|---:|---:|
| 新电脑 | 4 | 2 | 160 B |
| 旧电脑 | 4 | 0 | 352 B |

BackupFiles are not the reason old computer is much larger. The old package has no BackupFiles file rows in this output census.

## Gate Position

- Old computer: highest-value data source candidate.
- New computer: WDA Control Plane / WDA_HOME / RAG / database / web host.
- Message readability: **not proven**.
- Raw Gate Go: **not claimed**.
- Next gate: copied candidate DB bundle safe readability classification, preferably from the old computer's highest-value `db_storage/message` candidates and companion WAL/SHM files.
