# 36 Apply 回滚说明

S13 P3 已完成 Apply 与回滚。任务 ID 为 `MA-V12-S13P3`，验收 ID 为
`ACC-MA-V12-S13P3`，状态为
`phase_s13_p3_apply_rollback_completed_pending_s13_review`。Validator 为
`validate:v1.2-s13-p3`。

本 phase 的核心不是直接采纳所有 proposal，而是把安全闭环固定下来：

- 未授权的 `sample_unauthorized` 必须 fail-closed。
- 已授权的 `sample` 可以走自动 apply dry-run 路径。
- apply 后必须有 validation。
- validation 失败时必须进入 rollback 或 `rollback_or_needs_revision`。
- raw archive 永远不能作为 apply target。

真实 pending proposal 仍然需要人类授权。当前 5 个真实 pending proposal 没有被 apply。
`sample` 只是验收 fixture，用来证明授权 apply 代码路径可运行。

## 如何验证

```bash
pnpm --dir apps/memory-atlas run validate:v1.2-s13-p3
```

```bash
python3 scripts/atlasctl.py apply --proposal sample_unauthorized --dry-run
```

```bash
python3 scripts/atlasctl.py apply --proposal sample --dry-run
```

```bash
python3 scripts/atlasctl.py apply --proposal sample --dry-run --simulate-validation-failure
```

## 如何回滚

回滚本 phase 使用 git revert 对应本地 commit。若后续真实 proposal 被 apply，则优先使用
proposal 自带 rollback plan 或 git revert；raw 文件不回滚，因为 raw 只读、只追加。

边界：

- No GitHub main upload。
- No remote push。
- No raw mutation。
- pending S13 Review。

Machine-readable boundary summary: Memory Atlas v1.2 S13 P3; MA-V12-S13P3; ACC-MA-V12-S13P3; phase_s13_p3_apply_rollback_completed_pending_s13_review; validate:v1.2-s13-p3; proposal_apply.v1_2_s13_p3; S13 P3; Apply 与回滚; sample_unauthorized; sample; authorization required; validation_after_apply; rollback_or_needs_revision; No GitHub main upload; No remote push; No raw mutation; pending S13 Review.
