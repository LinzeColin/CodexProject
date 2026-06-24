# Other8 S4PAT01 Wave 1 Archive Plan Draft

task_id: S4PAT01
acceptance_id: ACC-S4PAT01
mode: STRUCTURE_BASELINE_ONLY

## Decision

S4PAT01 does not move, archive, delete, or rewrite project files. It records a Wave 1 tracked-file map, root noise baseline, and static reference graph so S4PAT02 can bind checksums and rollback steps before any physical structure migration.

## Stop Conditions

- Unknown file marked DELETE_CANDIDATE: false
- Archive location still written by runtime code: false, because no archive location is activated in S4PAT01
- Runtime/import entry moved: false

## Project Baseline

### Alpha

- tracked_file_count: 140
- root_file_count: 10
- category_counts: KEEP=65, MERGE=1, ARCHIVE=73, GENERATED=0, PRIVATE=1, DELETE_CANDIDATE=0
- root_noise_candidates: HANDOFF.md

### EVA_OS

- tracked_file_count: 1009
- root_file_count: 19
- category_counts: KEEP=724, MERGE=7, ARCHIVE=32, GENERATED=48, PRIVATE=198, DELETE_CANDIDATE=0
- root_noise_candidates: 15_OPEN_QUESTIONS.md, AGENT_CONTINUITY.md, CODEX_PROMPTS.md, CODEX_TASK_PACK.md, HANDOFF.md, PLANS.md, UPLOAD_MANIFEST.md

### OpMe_System

- tracked_file_count: 89
- root_file_count: 8
- category_counts: KEEP=66, MERGE=0, ARCHIVE=20, GENERATED=3, PRIVATE=0, DELETE_CANDIDATE=0
- root_noise_candidates: none

### whkmSalary

- tracked_file_count: 30
- root_file_count: 10
- category_counts: KEEP=30, MERGE=0, ARCHIVE=0, GENERATED=0, PRIVATE=0, DELETE_CANDIDATE=0
- root_noise_candidates: none

## Reference Graph

- node_count: 1268
- edge_count: 4474
- limitation: static textual references only; dynamic references remain a follow-up risk.

## Rollback

Rollback for S4PAT01 is to remove this baseline evidence and keep all original project paths untouched. Any later archive or merge action must be bound by S4PAT02 checksum manifest and an explicit old-to-new map.

## Next Task

S4PAT02 may generate the Wave 1 archive manifest, checksums, and rollback list. S4PAT01 itself is not permission to relocate files.
