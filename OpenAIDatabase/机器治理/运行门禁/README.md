# 运行门禁

用于放置 stage gate、stop condition、rollback、需求冻结和运行前检查。

当前阶段是 S04 P1。任务 ID 为 `MA-V12-S04P1`，验收 ID 为
`ACC-MA-V12-S04P1`，validator 为 `validate:v1.2-s04-p1`。

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

前置 S02 Review 已通过：`MA-V12-S02-REVIEW` / `ACC-MA-V12-S02-REVIEW` /
`validate:v1.2-s02-review`。

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

S03 P1 产物：

- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `data/public_raw/README.md`
- `人类可读/06_Raw明文公开与只读归档说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md`

S03 P1 gate：

- public raw path 已定义。
- manifest/hash 文件合同已定义。
- append-only 规则已定义。
- hash drift fail 规则已定义。

No GitHub main upload in this phase。
不实现 connector，不导入真实 transcript，不生成 S03 P3 manifest ledger。

前置 S03 P1 已通过：`MA-V12-S03P1` / `ACC-MA-V12-S03P1` /
`validate:v1.2-s03-p1`。

S03 P2 产物：

- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `scripts/privacy_guard.py`
- `scripts/sync_codex_memory_data.py`
- `人类可读/07_凭证排除说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md`

S03 P2 gate：

- credential is not memory。
- `credentials_not_transcript` 已接入同步与审计。
- 普通 transcript 不被凭证门禁拦截。
- 凭证 pattern 导致 gate fail。

前置 S03 P2 已通过：`MA-V12-S03P2` / `ACC-MA-V12-S03P2` /
`validate:v1.2-s03-p2`。

S03 P3 产物：

- `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `scripts/raw_archive_manifest.py`
- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`
- `人类可读/08_Raw机器账本说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p3_machine_ledger.md`

S03 P3 gate：

- raw manifest/hash 可生成。
- manifest row 可映射 source/file/hash/imported_at。
- 修改已有 raw 文件导致 validation fail。
- 删除已登记 manifest entry 导致 validation fail。
- raw manifest 是机器文件，不是人类主要页面。

No GitHub main upload in this phase。
前置 S03 P3 已通过：`MA-V12-S03P3` / `ACC-MA-V12-S03P3` /
`validate:v1.2-s03-p3`。

S03 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s03_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs`

S03 Review gate：

- raw 可公开备份。
- append-only 和 hash drift/deleted manifest entry fail 均可验证。
- credential exclusion 可验证，credential pattern 会失败。
- raw manifest/hash 可生成并映射 source/file/hash/imported_at。
- human files 不被 raw manifest 明细污染。

No GitHub main upload in this review。
前置 S03 Review 已通过：`MA-V12-S03-REVIEW` / `ACC-MA-V12-S03-REVIEW` /
`validate:v1.2-s03-review`。

S04 P1 产物：

- `机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `scripts/sync_chatgpt_memory_data.py`
- `scripts/atlasctl.py`
- `人类可读/09_ChatGPT只读同步与官方导出Fallback.md`
- `docs/reviews/memory_atlas_v1_2_s04_p1_chatgpt_sync.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p1.cjs`

S04 P1 gate：

- ChatGPT browser connector 边界为只读。
- 密码/验证码立即停止。
- 不发送消息、不删除、不归档、不重命名会话。
- official export ZIP/conversations.json fallback 可用。
- dry-run 不写文件。
- credential pattern 先失败，不进入 public raw。

No GitHub main upload in this phase。
下一步是 S04 P2；本 phase 不实现 Codex local sync、后续 agent adapter 或 GitHub backup apply。
