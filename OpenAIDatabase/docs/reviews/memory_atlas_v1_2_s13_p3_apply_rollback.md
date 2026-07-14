# Memory Atlas v1.2 S13 P3 Apply 与回滚

任务 ID：`MA-V12-S13P3`。

验收 ID：`ACC-MA-V12-S13P3`。

状态：`phase_s13_p3_apply_rollback_completed_pending_s13_review`。

Validator：`validate:v1.2-s13-p3`。

S13 P3 已完成 Apply 与回滚合同。机器合同为
`proposal_apply.v1_2_s13_p3`。本 phase 接入 `atlasctl.py apply`，用于验证：

- `sample_unauthorized` 未授权时必须 `FAIL_CLOSED`，不会写文件。
- `sample` 已授权验收 fixture 可进入授权 apply dry-run 路径。
- `sample` 模拟 validation failure 时会生成 `rollback_or_needs_revision` 路径。
- `data/public_raw/`、`data/raw/`、`data/private_imports/`、credentials、cookies、tokens
  永远不是 apply target。

当前 5 个真实 pending proposal 没有被当成已授权 proposal，也没有被 apply。
S13 P3 证明授权 apply 闭环可用，但不伪造用户对真实 pending proposal 的授权。
下一步是 pending S13 Review。

## 产物

- `机器治理/运行门禁/proposal_apply.v1_2_s13_p3.json`
- `data/derived/proposals/proposal_apply_report.json`
- `机器治理/证据与日志/proposal_apply/proposal_apply_evidence.v1_2_s13_p3.json`
- `scripts/build_memory_atlas_proposal_apply.py`
- `scripts/atlasctl.py`
- `人类可读/36_Apply回滚说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s13_p3.cjs`

## 验收

- 未授权 proposal 不会 apply：`sample_unauthorized` 返回 `FAIL_CLOSED`。
- 授权后可以自动 apply：`sample` dry-run 返回 `PASS`、`would_apply=true`、
  `validation_after_apply=true`、`rollback_point_created=true`。
- 失败可回滚：`--simulate-validation-failure` 返回 `FAIL_CLOSED`，并产生
  `rollback_or_needs_revision=true`。
- raw 不被修改：report 和 evidence 均记录 `raw_mutation=false`。

## 边界

- No GitHub main upload。
- No remote push。
- No raw mutation。
- 真实 pending proposal 未获人类授权前不 apply。
- pending S13 Review。

Machine-readable boundary summary: Memory Atlas v1.2 S13 P3; MA-V12-S13P3; ACC-MA-V12-S13P3; phase_s13_p3_apply_rollback_completed_pending_s13_review; validate:v1.2-s13-p3; proposal_apply.v1_2_s13_p3; S13 P3; Apply 与回滚; sample_unauthorized; sample; authorization required; validation_after_apply; rollback_or_needs_revision; No GitHub main upload; No remote push; No raw mutation; pending S13 Review.
