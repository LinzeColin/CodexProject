# 运行门禁

用于放置 stage gate、stop condition、rollback、需求冻结和运行前检查。

当前阶段是 S01 Review。任务 ID 为 `MA-V12-S01-REVIEW`，验收 ID 为
`ACC-MA-V12-S01-REVIEW`，validator 为 `validate:v1.2-s01-review`。

S01 Review 复审范围：

- S01 P1：`MA-V12-S01P1` / `ACC-MA-V12-S01P1` / `validate:v1.2-s01-p1`。
- S01 P2：`MA-V12-S01P2` / `ACC-MA-V12-S01P2` / `validate:v1.2-s01-p2`。
- S01 P3：`MA-V12-S01P3` / `ACC-MA-V12-S01P3` / `validate:v1.2-s01-p3`。

`v1.2需求冻结清单.json` 继续固定：

- 四线范围和 14 Stage 执行规则。
- 用户授权后的 raw/transcript 明文公开 GitHub 边界。
- raw 只读、只追加、不覆盖、不增删改。
- 凭证排除边界。
- 后续其他 agent 的 source registry 扩展规则。

No GitHub main upload in this review。
历史 phase 边界仍保留：No GitHub main upload in this phase。

下一步是 S02 P1；本 review 不执行 S02 work，不重装 app，不修改 raw archive。
