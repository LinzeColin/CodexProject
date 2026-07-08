# 证据与日志

用于放置 run evidence、audit logs、manifest/hash、stage evidence 和复审证据摘要。

当前 S14 P3 已完成开发记录与运行手册。任务 ID 为 `MA-V12-S14P3`，验收 ID 为
`ACC-MA-V12-S14P3`，状态为
`phase_s14_p3_development_record_completed_pending_s14_review`。Validator 为
`validate:v1.2-s14-p3`。S14 P3 证明开发记录中文可读、维护命令少而清晰、所有 stage pass gate 状态可查；
人类运行手册为 `人类可读/09_验收标准与运行手册.md`，机器证据为
`机器治理/证据与日志/stage_pass_gates/stage_pass_gate_status.v1_2_s14_p3.json`。下一步为
pending S14 Review。

S14 P3 不上传 GitHub main，不远端 push，不修改 raw。No GitHub main upload。No remote push。
No raw mutation。

当前 S13 Review 已完成。复审确认以下机器证据共同支持 Proposal 状态机、Diff narrator、
Apply 与回滚的 stage gate，下一步为 S14 P1：

- `机器治理/证据与日志/proposal_diffs/diff_narrator_machine_diff.v1_2_s13_p2.json`
- `机器治理/证据与日志/proposal_apply/proposal_apply_evidence.v1_2_s13_p3.json`

S13 Review 不上传 GitHub main、不远端 push、不修改 raw。真实 pending proposal 未获人类授权
前不 apply。

历史复验兼容记录：S13 P3 已完成 Apply 与回滚。S13 P3 新增机器 apply 证据文件：

- `机器治理/证据与日志/proposal_apply/proposal_apply_evidence.v1_2_s13_p3.json`

该文件保留 `sample_unauthorized` 未授权 fail-closed、`sample` 授权 dry-run apply、
validation_after_apply、rollback point 和 simulated rollback failure 证据。S13 P3 不上传
GitHub main、不远端 push、不修改 raw，下一步为 pending S13 Review。

历史复验兼容记录：S13 P2 已完成 Diff narrator。S13 P2 新增机器 diff 证据文件：

- `机器治理/证据与日志/proposal_diffs/diff_narrator_machine_diff.v1_2_s13_p2.json`

该文件保留每个 proposal 的机器 diff、target files、evidence refs、validation commands
和 rollback plan。人类首页只显示 Diff narrator 摘要，不放完整机器 diff。

当前 S03 Review 已通过。S03 P3 新增机器文件：

- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`

这些文件用于记录 raw manifest/hash 的 source/file/hash/imported_at 映射。
当前没有真实 raw transcript，因此 baseline 可以为空。它们是机器文件，不是人类主要页面。

S03 Review 复审证据为 `docs/reviews/memory_atlas_v1_2_s03_review.md`。该复审确认
public raw、credential exclusion、raw manifest/hash、append-only 和 no-upload 边界均可验证。
