# STAGE-038 Phase 1 Source Reverification

## Identity

- Task: `IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY`
- Stage: `STAGE-038 · Worker 队列基线`
- Acceptance: `ACC-STAGE-038`
- Verified at: `2026-07-11T09:07:57Z`
- Verification mode: exact-path and exact-archive-member read only

## Source Evidence

| Source | Exact path or member | SHA-256 | Result |
|---|---|---|---|
| v0.1-only taskpack archive | `/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip` | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` | `VERIFIED` |
| Exact Stage038 member | `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-038_Worker队列基线.md` | `613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634` | `VERIFIED` |
| v0.1-only roadmap | `/Users/linzezhang/Downloads/IDS_Codex开发Roadmap_v0_1_only_中文修订版.txt` | `a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6` | `VERIFIED` |
| v0.1-only instructions | `/Users/linzezhang/Downloads/IDS_Codex使用说明_v0_1_only_中文修订版.txt` | `ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8` | `VERIFIED` |

- `P0 source verification: SOURCE_VERIFIED`
- `P0 SHA-256: 613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634`
- `source_archive_path=/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip`
- `source_archive_sha256=55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- `source_member=IDS_v0_1_Final_Chinese_Revised/stages/STAGE-038_Worker队列基线.md`
- `source_member_match_count=1`
- `source_member_integrity=OK`
- `source_member_sha256=613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634`
- `roadmap_sha256=a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6`
- `instructions_sha256=ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8`
- `source_verification_status=SOURCE_VERIFIED`
- `reconciliation_status=passed`
- `source_reverification_required_before_phase2=false`
- `independent_review_status=passed`
- `phase2_entry_authorized=true`

The Stage038 member was streamed directly from the archive. It was not
extracted into the repository or Downloads. Only the three exact user-named
sources and the exact Stage038 member were read; no other Downloads path was
enumerated.

## Verified Source Requirements

- Pursuing goal:
  `建立异步 worker 队列，避免长任务阻塞前端和 API。`
- Phase 1 must define the job-state/worker boundary plus retry, dead-letter,
  backpressure, lock, automatic-lifecycle, idempotency-key, lock-granularity,
  and half-product cleanup rules.
- Relevant jobs must pause when the external drive is offline, disk space is
  insufficient, or external API budget is insufficient.
- Phase 2 must be a separate run that implements a minimal queue/state/control
  slice, human-readable state projection, and bounded input/output/error/
  checkpoint records.
- Stage scope may not expand to another Stage, real original material may not
  be committed or modified, secrets are forbidden, and tests cannot be claimed
  without real output.
- The standalone roadmap confirms non-parallel execution and the same title,
  goal, domain placement, and 8-16 hour Stage estimate.
- The standalone instructions require one Stage per Codex run.

## Reconciliation

| Previous provisional claim | Source conflict | Corrected Phase 1 result |
|---|---|---|
| External taskpack absent and hash unknown | The approved source is now present | Unique member, archive, member, roadmap, and instruction hashes recorded truthfully |
| Queue contract identity unassigned | Source requires a Worker queue baseline | `worker_queue_contract_id=ids.worker_queue_baseline.v0_1.p1` with a static Phase 1 status |
| Idempotency entirely unassigned | Source Phase 1 requires an idempotency-key rule | Require the envelope `idempotency_key`, no raw-body derivation, and no duplicate queue entry; exact encoding remains Phase 2 |
| Lock granularity entirely unassigned | Source Phase 1 requires lock granularity | Resource conflict domain, not a global queue lock; STAGE-041 owns runtime mechanics |
| Retry/dead-letter/backpressure/lifecycle/cleanup fully deferred | Source Phase 1 requires their boundaries | STAGE-038 defines interfaces and safety floors; STAGE-039..044 own policy refinement and runtime |
| Pause conditions not source-bound | Source names external drive, disk, and API budget | Record `external_drive_offline`, `disk_space_insufficient`, and `external_api_budget_insufficient` gates |
| Cleanup only named as later ownership | Source Phase 1 requires cleanup rules | Require `cleanup_manifest_ref`, temporary/rebuildable allowlist, and protected truth/evidence/report surfaces |
| Phase 2 planned as static-only evaluation | Source Phase 2 calls for a minimal runnable slice or executable contract | Plan a separate minimal async queue slice without raw-data access or fake IDS business data |

No source conflict remains in the corrected Phase 1 contract. Exact queue
schema, ordering, dependency qualification, claim sequence, capacity,
thresholds, timing, lease values, and deletion mechanics are not present in the
source and therefore remain explicit Phase 2 or STAGE-039..044 decisions.

## Gate State After Independent Review

The independent review found one Critical cross-file consistency gap and one
Important P2/P3 direction gap. Both were repaired. Final re-review returned
`0 Critical / 0 Important / 0 Minor` and authorized only the next separate
Phase 2 run; no Phase 2 action occurred here.

- `push_allowed=false`

## No-Action Evidence

- `taskpack_source_read_performed=true`
- `ids_business_source_read_performed=false`
- `raw_metadata_content_accessed=false`
- `live_execution_performed=false`
- `queue_runtime_performed=false`
- `worker_runtime_performed=false`
- `claim_persistence_performed=false`
- `retry_scheduler_performed=false`
- `dead_letter_runtime_performed=false`
- `backpressure_runtime_performed=false`
- `lock_runtime_performed=false`
- `automatic_lifecycle_runtime_performed=false`
- `crash_recovery_runtime_performed=false`
- `cleanup_runtime_performed=false`
- `database_connection_performed=false`
- `schema_change_performed=false`
- `state_registry_write_performed=false`
- `runtime_output_written=false`
- `real_job_created=false`
- `fake_ids_business_data_used=false`

`/Users/linzezhang/Downloads/IDS_MetaData` remains path-only. Its contents were
not read, listed, hashed, opened, copied, moved, deleted, modified, dumped, or
scanned.

## Rollback

Revert this evidence and the same Stage038 P1 source-reconciliation patch only.
Do not touch the external source files, raw metadata, user-owned dirty files,
prior-stage evidence, databases, runtime data, reports, app entries, or GitHub.
