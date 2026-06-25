# Other8 S5PAT01 Wave 2 Archive Plan Draft

task_id: S5PAT01
acceptance_id: ACC-S5PAT01
mode: WAVE2_PRIVACY_ARTIFACT_BASELINE_ONLY

## Decision

S5PAT01 does not move, archive, delete, or rewrite project files. It records a Wave 2 tracked-file map, privacy/artifact baseline, root noise baseline, and static reference graph so S5PAT02 can bind checksums and rollback steps before any physical structure migration.

## Stop Conditions

- Unknown file marked DELETE_CANDIDATE: false
- Archive location still written by runtime code: false, because no archive location is activated in S5PAT01
- Runtime/import entry moved: false

## Project Baseline

### FIFA

- tracked_file_count: 312
- root_file_count: 8
- category_counts: KEEP=270, MERGE=0, ARCHIVE=0, GENERATED=42, PRIVATE=0, DELETE_CANDIDATE=0
- root_noise_candidates: none

### OpenAIDatabase

- tracked_file_count: 206
- root_file_count: 9
- category_counts: KEEP=102, MERGE=0, ARCHIVE=0, GENERATED=0, PRIVATE=104, DELETE_CANDIDATE=0
- root_noise_candidates: none

### PFI_BIG_DATA_SIMULATOR

- tracked_file_count: 282
- root_file_count: 12
- category_counts: KEEP=240, MERGE=2, ARCHIVE=40, GENERATED=0, PRIVATE=0, DELETE_CANDIDATE=0
- root_noise_candidates: BACKUP_MANIFEST.md, HANDOFF.md

### Serenity-Alipay

- tracked_file_count: 412
- root_file_count: 10
- category_counts: KEEP=143, MERGE=3, ARCHIVE=115, GENERATED=0, PRIVATE=151, DELETE_CANDIDATE=0
- root_noise_candidates: BACKUP_SYNC_NOTE.md, DEVELOPMENT_BUG_REGRESSION_LOG.md, HANDOFF.md

## Reference Graph

- node_count: 1212
- edge_count: 3047
- limitation: static textual references only; dynamic references remain a follow-up risk.

## Rollback

Rollback for S5PAT01 is to remove this baseline evidence and keep all original project paths untouched. Any later archive or merge action must be bound by S5PAT02 checksum/privacy manifest and an explicit old-to-new map.

## Next Task

S5PAT02 may generate the Wave 2 archive/privacy manifest, checksums, and rollback list. S5PAT01 itself is not permission to relocate files.
