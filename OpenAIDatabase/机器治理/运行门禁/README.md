# 运行门禁

用于放置 stage gate、stop condition、rollback、需求冻结和运行前检查。

当前阶段是 S02 P2。任务 ID 为 `MA-V12-S02P2`，验收 ID 为 `ACC-MA-V12-S02P2`，
validator 为 `validate:v1.2-s02-p2`。

前置 S01 Review 已通过：`MA-V12-S01-REVIEW` / `ACC-MA-V12-S01-REVIEW` /
`validate:v1.2-s01-review`。

前置 S02 P1 已通过：`MA-V12-S02P1` / `ACC-MA-V12-S02P1` /
`validate:v1.2-s02-p1`。

S02 P2 产物：

- `机器治理/同步与备份/sync_source_registry.json`
- `docs/reviews/memory_atlas_v1_2_s02_p2_source_registry.md`

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

No GitHub main upload in this phase。
不创建人类同步说明页；S02 P3 才能创建对应人类说明。
不实现 connector，不修改 raw archive。

下一步是 S02 P3；本 phase 不重装 app。
