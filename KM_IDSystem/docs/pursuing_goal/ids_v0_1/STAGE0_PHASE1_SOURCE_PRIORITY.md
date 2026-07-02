# IDS v0.1 Stage 0 Phase 1 Source Priority

## Run Contract

- Stage: `STAGE-0`
- Phase: `STAGE0-P1`
- Status: `completed_local_evidence`
- Acceptance: P0 source files, current worktree mapping, v0.1-only execution range, and stop gates are recorded before `STAGE-001`.
- Non-goals: no backend/frontend implementation, no RAG/OCR/index/UI work, no dependency install, no data directory creation, no upload to GitHub main in this phase.

## Verified Inputs

| Priority | Source | Role | SHA-256 | Notes |
|---|---|---|---|---|
| P0 | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Codex使用说明_v0_1_only_中文修订版.txt` | usage instructions | `ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8` | Defines one-stage-at-a-time execution and v0.1-only scope. |
| P0 | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Codex开发Roadmap_v0_1_only_中文修订版.txt` | roadmap | `a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6` | Defines v0.1 goal and STAGE-001..168 roadmap. |
| P0 | `/Users/linzezhang/Downloads/RAG IDS/v0.1/IDS_Taskpack_v0_1_only_中文修订版.zip` | taskpack | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` | Contains stage files, owner decisions, quality gates, and machine index. |

Zip machine index evidence:

- `v0_1_stage_index.csv` SHA-256: `f767fa0ccf751b96d18d91602f8d8118637eff545d879d05800d9b5e44784b03`
- Stage count: `168`
- Stage range: `STAGE-001` to `STAGE-168`
- Missing stage numbers: none
- First executable stage: `STAGE-001 / ACC-STAGE-001 / IDS 产品命名合同`
- Final v0.1 stage: `STAGE-168 / ACC-STAGE-168 / v0.1 最终验收门禁`

## Current Worktree Mapping

| Fact | Value | Status |
|---|---|---|
| Active worktree | `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS` | verified |
| Git root | `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS` | verified |
| Project path | `KM_IDSystem` | verified |
| Branch | `codex/KM_IDS` | verified |
| GitHub repo | `LinzeColin/CodexProject` | verified |
| Old worktree path | `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/opme-system` | stale, do not use |
| Old source path in taskpack | `OpMe_System` | legacy alias only |

## Execution Lock

1. Current development scope is `v0.1` only.
2. `STAGE-001..STAGE-168` are the only executable v0.1 stages.
3. `v0.2+` material is architecture guidance only until the user explicitly opens those versions.
4. Each run may complete at most one phase.
5. Each implementation stage must use one `Stage` and one `Acceptance ID`.
6. A stage with `建议并行度：否` must not run in parallel with another implementation thread.
7. A stage with `建议并行度：是` may run in parallel only when file ranges, Acceptance IDs, and shared schema/UI/deploy files do not conflict.

## Stop Gates

Stop instead of implementing when any condition is true:

- the selected Stage file is missing from the P0 taskpack;
- the target project path is not `KM_IDSystem`;
- a change would touch real raw data or `00_ORIGINAL_RAW_DATA`;
- a change would commit secrets or credentials;
- a change would revive `OpMe_System` or `opme-system` as an active path;
- a change would implement v0.2+ functionality during v0.1;
- tests fail and the cause is unknown;
- the requested phase requires more than one phase worth of work.

## Next Phase Entrance

`STAGE0-P2` should create the durable stage execution index and governance bridge for selecting `STAGE-001` without rereading unrelated projects or full reference packs.

## Validation Results

Passed:

- Python standard-library hash check recorded P0 source file SHA-256 values.
- Zip machine index check returned `stage_index_ok rows=168 range=001-168 gaps=0`.
- Marker check confirmed root lock, source priority, Acceptance ID, v0.1 range, stage count, `external_api_policy_default: denied`, one-phase run limit, and `STAGE0-P2` next phase marker.
- Bundled Python render wrote canonical Chinese entry files.
- Bundled Python `check-render --project KM_IDSystem` returned `drift_count=0`.

Blocked by sparse worktree, not expanded:

- `validate --project KM_IDSystem --semantic` requires root governance schemas, workflow/hook files, and unrelated registered project directories absent from this sparse worktree.
- `validate --changed-only --enforce-sync --semantic --base-ref origin/main` also includes historical diff outside this phase and the same sparse omissions.

Phase 1 decision: do not expand unrelated projects; carry this limitation into Stage 0 review and use the local evidence above as the minimum alternative validation for this phase.
