# 运行门禁

用于放置 stage gate、stop condition、rollback、需求冻结和运行前检查。

当前阶段是 S02 Review。任务 ID 为 `MA-V12-S02-REVIEW`，验收 ID 为
`ACC-MA-V12-S02-REVIEW`，validator 为 `validate:v1.2-s02-review`。

前置 S01 Review 已通过：`MA-V12-S01-REVIEW` / `ACC-MA-V12-S01-REVIEW` /
`validate:v1.2-s01-review`。

前置 S02 P1 已通过：`MA-V12-S02P1` / `ACC-MA-V12-S02P1` /
`validate:v1.2-s02-p1`。

前置 S02 P2 已通过：`MA-V12-S02P2` / `ACC-MA-V12-S02P2` /
`validate:v1.2-s02-p2`。

S02 P3 产物：

- `机器治理/同步与备份/sync_source_registry.json`
- `docs/reviews/memory_atlas_v1_2_s02_p2_source_registry.md`
- `人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`
- `docs/reviews/memory_atlas_v1_2_s02_p3_human_sync_explanation.md`

前置 S02 P3 已通过：`MA-V12-S02P3` / `ACC-MA-V12-S02P3` /
`validate:v1.2-s02-p3`。

S02 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s02_review.md`

source registry 必须包含：

- `chatgpt`：ChatGPT browser connector 与 official export fallback。
- `codex`：Codex local sync。
- `future_agent_template`：后续 other_agent 的 future_agent_adapter。
- 每个 source 的 `public_backup_mode`。
- 每个 source 的 transcript/credential boundary。

`v1.2需求冻结清单.json` 继续固定：

- 四线范围和 14 Stage 执行规则。
- 用户授权后的 raw/transcript 明文公开 GitHub 边界。
- raw 只读、只追加、不覆盖、不增删改。
- 凭证排除边界。
- 后续其他 agent 的 source registry 扩展规则。

No GitHub main upload in this review。
不实现 connector，不修改 raw archive。
不进入 S03；S03 P1 是下一轮。

下一步是 S03 P1；本 review 不重装 app。
