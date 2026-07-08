## v1.2 S05 P1 Facet Schema

状态：`phase_s05_p1_facet_schema_completed_pending_s05_p2`。

任务 ID：`MA-V12-S05P1`。

验收 ID：`ACC-MA-V12-S05P1`。

S05 P1 定义 Memory Atlas v1.2 的 facet/canonical event schema。它覆盖
ChatGPT、Codex 和 future agent 的后续事件语义层，并用中文解释英文机器字段。

涉及文件：

- `机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`
- `人类可读/12_Facet字段与事件语义说明.md`
- `docs/reviews/memory_atlas_v1_2_s05_p1_facet_schema.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s05-p1`
- `ACC-MA-V12-S05P1`
- `MA-V12-S05P1`
- S05 P1
- `facet_event_schema.v1_2_s05_p1.json`
- `12_Facet字段与事件语义说明.md`
- pending S05 P2
- No GitHub main upload in this phase

边界：

- No remote push in this phase.
- No extractor in this phase.
- No fake events in this phase.
- No raw mutation in this phase.
- No GitHub main upload in this phase.

Machine-readable boundary summary: Memory Atlas v1.2 S05 P1 Facet Schema; MA-V12-S05P1; ACC-MA-V12-S05P1; phase_s05_p1_facet_schema_completed_pending_s05_p2; validate:v1.2-s05-p1; facet_event_schema.v1_2_s05_p1.json; 12_Facet字段与事件语义说明.md; memory_atlas_v1_2_s05_p1_facet_schema.md; S05 P1; pending S05 P2; No GitHub main upload in this phase; No remote push in this phase; No extractor in this phase; No fake events in this phase; No raw mutation in this phase.

## v1.2 S04 Review

状态：`stage_s04_review_passed_pending_s05_no_github_main_upload`。

任务 ID：`MA-V12-S04-REVIEW`。

验收 ID：`ACC-MA-V12-S04-REVIEW`。

S04 Review 完成 Memory Atlas v1.2 自动同步 MVP 的整体复审。复审覆盖
ChatGPT 只读同步、official export fallback、Codex local sync、future-agent
minimal adapter、raw + derived + run log 输出、build-atlas dry-run 和 GitHub
backup dry-run/apply 本地控制面。

涉及文件：

- `docs/reviews/memory_atlas_v1_2_s04_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_review.cjs`
- `apps/memory-atlas/package.json`
- `人类可读/00_快速入口.md`
- `人类可读/01_v1.2四线14Stage升级总览.md`
- `机器治理/README.md`
- `机器治理/同步与备份/README.md`
- `机器治理/运行门禁/README.md`

验收：

- `validate:v1.2-s04-review`
- `ACC-MA-V12-S04-REVIEW`
- `MA-V12-S04-REVIEW`
- S04 Review
- `memory_atlas_v1_2_s04_review.md`
- pending S05 P1
- No GitHub main upload in this review

边界：

- No remote push in this review.
- No app reinstall.
- No ChatGPT mutation.
- No credential capture.
- No fake sync data.
- No GitHub main upload in this review.

Machine-readable boundary summary: Memory Atlas v1.2 S04 Review; MA-V12-S04-REVIEW; ACC-MA-V12-S04-REVIEW; stage_s04_review_passed_pending_s05_no_github_main_upload; validate:v1.2-s04-review; memory_atlas_v1_2_s04_review.md; S04 Review; pending S05 P1; No GitHub main upload in this review; No remote push in this review; No app reinstall; No ChatGPT mutation; No credential capture; No fake sync data.

## v1.2 S04 P3 GitHub Backup

状态：`phase_s04_p3_github_backup_completed_pending_s04_review`。

任务 ID：`MA-V12-S04P3`。

验收 ID：`ACC-MA-V12-S04P3`。

S04 P3 实现 Memory Atlas v1.2 的 GitHub backup 本地控制面。备份范围覆盖
raw、derived、reports 和 run logs；dry-run 不写文件；apply 只本地 git add/commit，
不执行远端 push。

涉及文件：

- `机器治理/同步与备份/github_backup_policy.v1_2_s04_p3.json`
- `scripts/github_backup.py`
- `scripts/atlasctl.py`
- `人类可读/11_GitHub备份DryRun与Apply.md`
- `docs/reviews/memory_atlas_v1_2_s04_p3_github_backup.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p3.cjs`
- `tests/test_s04p3_github_backup.py`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s04-p3`
- `ACC-MA-V12-S04P3`
- `MA-V12-S04P3`
- S04 P3
- `memory_atlas_v1_2_s04_p3_github_backup.md`
- `github_backup_policy.v1_2_s04_p3.json`
- `github_backup.py`
- `atlasctl.py`
- pending S04 Review
- No GitHub main upload in this phase

边界：

- No remote push in this phase.
- No app reinstall.
- No ChatGPT mutation.
- No GitHub main upload in this phase.

Machine-readable boundary summary: Memory Atlas v1.2 S04 P3 GitHub Backup; MA-V12-S04P3; ACC-MA-V12-S04P3; phase_s04_p3_github_backup_completed_pending_s04_review; validate:v1.2-s04-p3; memory_atlas_v1_2_s04_p3_github_backup.md; github_backup_policy.v1_2_s04_p3.json; github_backup.py; atlasctl.py; S04 P3; pending S04 Review; No GitHub main upload in this phase; No remote push in this phase; No app reinstall; No ChatGPT mutation.

## v1.2 S04 P2 Codex/Future Agent Sync

状态：`phase_s04_p2_codex_agent_sync_completed_pending_s04_p3`。

任务 ID：`MA-V12-S04P2`。

验收 ID：`ACC-MA-V12-S04P2`。

S04 P2 实现 Memory Atlas v1.2 的 Codex local sync 与 future-agent minimal adapter
同步入口。每个来源均固定 raw + derived + run log 输出合同；dry-run 不写文件，
apply 缺少输入时不能生成伪数据。

涉及文件：

- `机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `scripts/sync_codex_memory_data.py`
- `scripts/sync_future_agent_data.py`
- `scripts/atlasctl.py`
- `人类可读/10_Codex与FutureAgent同步.md`
- `docs/reviews/memory_atlas_v1_2_s04_p2_codex_agent_sync.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p2.cjs`
- `tests/test_s04p2_codex_agent_sync.py`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s04-p2`
- `ACC-MA-V12-S04P2`
- `MA-V12-S04P2`
- S04 P2
- `memory_atlas_v1_2_s04_p2_codex_agent_sync.md`
- `codex_agent_sync_policy.v1_2_s04_p2.json`
- `sync_codex_memory_data.py`
- `sync_future_agent_data.py`
- `atlasctl.py`
- pending S04 P3
- No GitHub main upload in this phase

边界：

- No GitHub backup apply.
- No credential storage.
- No browser mutation.
- No GitHub main upload in this phase.

Machine-readable boundary summary: Memory Atlas v1.2 S04 P2 Codex/Future Agent Sync; MA-V12-S04P2; ACC-MA-V12-S04P2; phase_s04_p2_codex_agent_sync_completed_pending_s04_p3; validate:v1.2-s04-p2; memory_atlas_v1_2_s04_p2_codex_agent_sync.md; codex_agent_sync_policy.v1_2_s04_p2.json; sync_codex_memory_data.py; sync_future_agent_data.py; atlasctl.py; S04 P2; pending S04 P3; No GitHub main upload in this phase; No GitHub backup apply; No credential storage; No browser mutation.

## v1.2 S04 P1 ChatGPT Sync

状态：`phase_s04_p1_chatgpt_sync_completed_pending_s04_p2`。

任务 ID：`MA-V12-S04P1`。

验收 ID：`ACC-MA-V12-S04P1`。

S04 P1 实现 Memory Atlas v1.2 的 ChatGPT 只读同步入口。浏览器 connector 在本阶段为
read-only contract；遇到密码/验证码立即停止；不得发送消息、删除、归档或重命名会话。
可执行路径为 official export ZIP/conversations.json fallback。

涉及文件：

- `机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `scripts/sync_chatgpt_memory_data.py`
- `scripts/atlasctl.py`
- `人类可读/09_ChatGPT只读同步与官方导出Fallback.md`
- `docs/reviews/memory_atlas_v1_2_s04_p1_chatgpt_sync.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p1.cjs`
- `tests/test_s04p1_chatgpt_sync.py`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s04-p1`
- `ACC-MA-V12-S04P1`
- `MA-V12-S04P1`
- S04 P1
- `memory_atlas_v1_2_s04_p1_chatgpt_sync.md`
- `chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `sync_chatgpt_memory_data.py`
- `atlasctl.py`
- pending S04 P2
- No GitHub main upload in this phase

边界：

- No Codex local sync.
- No future-agent adapter.
- No GitHub backup apply.
- No browser mutation.
- No GitHub main upload in this phase.

Machine-readable boundary summary: Memory Atlas v1.2 S04 P1 ChatGPT Sync; MA-V12-S04P1; ACC-MA-V12-S04P1; phase_s04_p1_chatgpt_sync_completed_pending_s04_p2; validate:v1.2-s04-p1; memory_atlas_v1_2_s04_p1_chatgpt_sync.md; chatgpt_readonly_sync_policy.v1_2_s04_p1.json; sync_chatgpt_memory_data.py; atlasctl.py; S04 P1; pending S04 P2; No GitHub main upload in this phase; No Codex local sync; No future-agent adapter; No GitHub backup apply; No browser mutation.

## v1.2 S03 Review

状态：`stage_s03_review_passed_pending_s04_no_github_main_upload`。

任务 ID：`MA-V12-S03-REVIEW`。

验收 ID：`ACC-MA-V12-S03-REVIEW`。

S03 Review 完成 Memory Atlas v1.2 的 S03 阶段复审。复审覆盖 S03 P1、S03 P2
和 S03 P3，确认 raw 可公开备份、append-only、credential exclusion 和
raw manifest/hash 均可验证。

涉及文件：

- `docs/reviews/memory_atlas_v1_2_s03_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs`
- `apps/memory-atlas/package.json`
- `人类可读/00_快速入口.md`
- `人类可读/01_v1.2四线14Stage升级总览.md`
- `机器治理/README.md`
- `机器治理/同步与备份/README.md`
- `机器治理/证据与日志/README.md`
- `机器治理/运行门禁/README.md`

验收：

- `validate:v1.2-s03-review`
- `ACC-MA-V12-S03-REVIEW`
- `MA-V12-S03-REVIEW`
- S03 Review
- `memory_atlas_v1_2_s03_review.md`
- pending S04 P1
- No GitHub main upload in this review

边界：

- No connector implementation.
- No real transcript ingestion.
- No UI work.
- No public raw file mutation.
- No GitHub main upload in this review.

Machine-readable boundary summary: Memory Atlas v1.2 S03 Review; MA-V12-S03-REVIEW; ACC-MA-V12-S03-REVIEW; stage_s03_review_passed_pending_s04_no_github_main_upload; validate:v1.2-s03-review; memory_atlas_v1_2_s03_review.md; S03 Review; pending S04 P1; No GitHub main upload in this review; No connector implementation; No real transcript ingestion; No UI work; No public raw file mutation.

## v1.2 S03 P3 Machine Ledger

状态：`phase_s03_p3_machine_ledger_completed_pending_s03_review`。

任务 ID：`MA-V12-S03P3`。

验收 ID：`ACC-MA-V12-S03P3`。

S03 P3 实现 Memory Atlas v1.2 的 raw manifest/hash 机器账本。它生成
`raw_manifest.s03_p3_baseline.jsonl` 和 `raw_hash_ledger.jsonl`，并通过
`scripts/raw_archive_manifest.py` 提供 append-only audit。当前没有真实 raw transcript，
因此 baseline ledger 可以为空；后续新增 raw 只能追加。

涉及文件：

- `scripts/raw_archive_manifest.py`
- `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`
- `人类可读/08_Raw机器账本说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p3_machine_ledger.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p3.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s03-p3`
- `ACC-MA-V12-S03P3`
- S03 P3
- `memory_atlas_v1_2_s03_p3_machine_ledger.md`
- `raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `raw_archive_manifest.py`
- raw manifest/hash can be generated
- source/file/hash/imported_at
- pending S03 Review
- No GitHub main upload in this phase

边界：

- No connector implementation.
- No real transcript ingestion.
- No UI work.
- No public raw file mutation.
- No GitHub main upload in this phase.

Machine-readable boundary summary: Memory Atlas v1.2 S03 P3 Machine Ledger; MA-V12-S03P3; ACC-MA-V12-S03P3; phase_s03_p3_machine_ledger_completed_pending_s03_review; validate:v1.2-s03-p3; memory_atlas_v1_2_s03_p3_machine_ledger.md; raw_manifest_ledger_policy.v1_2_s03_p3.json; raw_archive_manifest.py; raw_manifest.s03_p3_baseline.jsonl; raw_hash_ledger.jsonl; S03 P3; pending S03 Review; No GitHub main upload in this phase; No connector implementation; No real transcript ingestion; No UI work; No public raw file mutation.

## v1.2 S03 P2 Credential Exclusion

状态：`phase_s03_p2_credential_exclusion_completed_pending_s03_p3`。

任务 ID：`MA-V12-S03P2`。

验收 ID：`ACC-MA-V12-S03P2`。

S03 P2 实现 Memory Atlas v1.2 的 credential is not memory 轻量门禁。
普通 transcript 仍然是 memory；cookie、session token、password、api key、
private key、oauth token 和 browser credential store 不能进入 GitHub。

涉及文件：

- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `scripts/privacy_guard.py`
- `scripts/sync_codex_memory_data.py`
- `人类可读/07_凭证排除说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p2.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s03-p2`
- `ACC-MA-V12-S03P2`
- S03 P2
- `memory_atlas_v1_2_s03_p2_credential_exclusion.md`
- `credential_exclusion_policy.v1_2_s03_p2.json`
- credential is not memory
- pending S03 P3
- No GitHub main upload in this phase

边界：

- No S03 P3 manifest generation.
- No connector implementation.
- No complex UI.
- No real transcript ingestion.
- No public raw file mutation.
- No GitHub main upload in this phase.

Machine-readable boundary summary: Memory Atlas v1.2 S03 P2 Credential Exclusion; MA-V12-S03P2; ACC-MA-V12-S03P2; phase_s03_p2_credential_exclusion_completed_pending_s03_p3; validate:v1.2-s03-p2; memory_atlas_v1_2_s03_p2_credential_exclusion.md; credential_exclusion_policy.v1_2_s03_p2.json; credential is not memory; S03 P2; pending S03 P3; No GitHub main upload in this phase; No S03 P3 manifest generation; No connector implementation; No complex UI; No real transcript ingestion; No public raw file mutation.

## v1.2 S03 P1 Public Raw Path

状态：`phase_s03_p1_public_raw_path_defined_pending_s03_p2`。

任务 ID：`MA-V12-S03P1`。

验收 ID：`ACC-MA-V12-S03P1`。

S03 P1 定义 Memory Atlas v1.2 的 public raw archive path、raw manifest/hash file、
append-only rule 和 hash drift fail rule。该 phase 不导入真实 transcript，不实现
credential gate，不生成 manifest ledger，不实现 connector。

涉及文件：

- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `data/public_raw/README.md`
- `人类可读/06_Raw明文公开与只读归档说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s03-p1`
- `ACC-MA-V12-S03P1`
- S03 P1
- `memory_atlas_v1_2_s03_p1_public_raw_path.md`
- `raw_public_archive_policy.v1_2_s03_p1.json`
- `data/public_raw/README.md`
- pending S03 P2
- No GitHub main upload in this phase

边界：

- No S03 P2 credential gate.
- No S03 P3 manifest generation.
- No connector implementation.
- No transcript ingestion in this phase.
- No GitHub main upload in this phase.

Machine-readable boundary summary: Memory Atlas v1.2 S03 P1 Public Raw Path; MA-V12-S03P1; ACC-MA-V12-S03P1; phase_s03_p1_public_raw_path_defined_pending_s03_p2; validate:v1.2-s03-p1; memory_atlas_v1_2_s03_p1_public_raw_path.md; raw_public_archive_policy.v1_2_s03_p1.json; data/public_raw/README.md; S03 P1; pending S03 P2; No GitHub main upload in this phase; No S03 P2 credential gate; No S03 P3 manifest generation; No connector implementation; No transcript ingestion in this phase.

## v1.2 S02 Review

状态：`stage_s02_review_passed_pending_s03_no_github_main_upload`。

任务 ID：`MA-V12-S02-REVIEW`。

验收 ID：`ACC-MA-V12-S02-REVIEW`。

S02 Review 复审 S02 P1、S02 P2、S02 P3 的 source model、source registry、
人类同步说明、public_backup_mode、transcript/credential boundary 和 future agent
扩展。S02 整体复审已通过，下一步为 pending S03 P1。

涉及文件：

- `docs/reviews/memory_atlas_v1_2_s02_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_review.cjs`
- `apps/memory-atlas/package.json`
- `人类可读/00_快速入口.md`
- `机器治理/运行门禁/README.md`

验收：

- `validate:v1.2-s02-review`
- `ACC-MA-V12-S02-REVIEW`
- S02 Review
- `memory_atlas_v1_2_s02_review.md`
- pending S03 P1
- No GitHub main upload in this review

边界：

- No connector implementation.
- No GitHub main upload in this review.
- No app reinstall.
- No raw archive change.

Machine-readable boundary summary: Memory Atlas v1.2 S02 Review; MA-V12-S02-REVIEW; ACC-MA-V12-S02-REVIEW; stage_s02_review_passed_pending_s03_no_github_main_upload; validate:v1.2-s02-review; memory_atlas_v1_2_s02_review.md; S02 Review; pending S03 P1; No GitHub main upload in this review; No connector implementation; No raw archive change.

## v1.2 S02 P3 Human Sync Explanation

状态：`phase_s02_p3_human_sync_explanation_completed_pending_s02_review`。

任务 ID：`MA-V12-S02P3`。

验收 ID：`ACC-MA-V12-S02P3`。

S02 P3 创建 `人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`，明确
ChatGPT、Codex、后续其他 agent 数据备份进 GitHub。该 phase 只创建人类说明页，
不实现 connector，不写 raw archive。

涉及文件：

- `人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`
- `docs/reviews/memory_atlas_v1_2_s02_p3_human_sync_explanation.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s02-p3`
- `ACC-MA-V12-S02P3`
- S02 P3
- `人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`
- `memory_atlas_v1_2_s02_p3_human_sync_explanation.md`
- pending S02 Review
- No GitHub main upload in this phase

边界：

- No connector implementation.
- No GitHub main upload in this phase.
- No app reinstall.
- No raw archive change.

Machine-readable boundary summary: Memory Atlas v1.2 S02 P3 Human Sync Explanation; MA-V12-S02P3; ACC-MA-V12-S02P3; phase_s02_p3_human_sync_explanation_completed_pending_s02_review; validate:v1.2-s02-p3; memory_atlas_v1_2_s02_p3_human_sync_explanation.md; 人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md; S02 P3; pending S02 Review; No GitHub main upload in this phase; No connector implementation; No raw archive change.

## v1.2 S02 P2 Source Registry

状态：`phase_s02_p2_source_registry_completed_pending_s02_p3`。

任务 ID：`MA-V12-S02P2`。

验收 ID：`ACC-MA-V12-S02P2`。

S02 P2 建立 `sync_source_registry.json`，注册 ChatGPT、Codex 和
future_agent_template。该 phase 只建立 registry，不创建人类同步说明页，不实现 connector。

涉及文件：

- `机器治理/同步与备份/sync_source_registry.json`
- `docs/reviews/memory_atlas_v1_2_s02_p2_source_registry.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s02-p2`
- `ACC-MA-V12-S02P2`
- S02 P2
- `sync_source_registry.json`
- `memory_atlas_v1_2_s02_p2_source_registry.md`
- pending S02 P3
- No GitHub main upload in this phase

边界：

- No human sync page in this phase.
- No connector implementation.
- No GitHub main upload in this phase.
- No app reinstall.
- No raw archive change.

Machine-readable boundary summary: Memory Atlas v1.2 S02 P2 Source Registry; MA-V12-S02P2; ACC-MA-V12-S02P2; phase_s02_p2_source_registry_completed_pending_s02_p3; validate:v1.2-s02-p2; memory_atlas_v1_2_s02_p2_source_registry.md; sync_source_registry.json; S02 P2; pending S02 P3; No GitHub main upload in this phase; No human sync page in this phase; No connector implementation; No raw archive change.

## v1.2 S02 P1 Source Data Model

状态：`phase_s02_p1_source_data_model_completed_pending_s02_p2`。

任务 ID：`MA-V12-S02P1`。

验收 ID：`ACC-MA-V12-S02P1`。

S02 P1 定义 ChatGPT、Codex、后续其他 agent 的统一 source data model。该 phase
只定义模型，不建立 source registry，不创建人类同步说明页，不实现 connector。

涉及文件：

- `机器治理/数据契约/source_data_model.v1_2_s02_p1.json`
- `docs/reviews/memory_atlas_v1_2_s02_p1_source_data_model.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s02-p1`
- `ACC-MA-V12-S02P1`
- S02 P1
- `source_data_model.v1_2_s02_p1.json`
- `memory_atlas_v1_2_s02_p1_source_data_model.md`
- pending S02 P2
- No GitHub main upload in this phase

边界：

- No source registry file in this phase.
- No human sync page in this phase.
- No connector implementation.
- No GitHub main upload in this phase.
- No app reinstall.
- No raw archive change.

Machine-readable boundary summary: Memory Atlas v1.2 S02 P1 Source Data Model; MA-V12-S02P1; ACC-MA-V12-S02P1; phase_s02_p1_source_data_model_completed_pending_s02_p2; validate:v1.2-s02-p1; memory_atlas_v1_2_s02_p1_source_data_model.md; source_data_model.v1_2_s02_p1.json; S02 P1; pending S02 P2; No GitHub main upload in this phase; No source registry file in this phase; No human sync page in this phase; No connector implementation; No raw archive change.

## v1.2 S01 Review

状态：`stage_s01_review_passed_pending_s02_no_github_main_upload`。

任务 ID：`MA-V12-S01-REVIEW`。

验收 ID：`ACC-MA-V12-S01-REVIEW`。

S01 Review 复审 S01 P1、S01 P2、S01 P3 的文件、记录、validator、stop condition
和 pass gate。S01 整体复审已通过，下一步为 pending S02 P1。

涉及文件：

- `docs/reviews/memory_atlas_v1_2_s01_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_review.cjs`
- `apps/memory-atlas/package.json`
- `人类可读/00_快速入口.md`
- `机器治理/运行门禁/README.md`

验收：

- `validate:v1.2-s01-review`
- `ACC-MA-V12-S01-REVIEW`
- S01 Review
- `memory_atlas_v1_2_s01_review.md`
- pending S02 P1
- No GitHub main upload in this review

边界：

- No S02 work.
- No GitHub main upload in this review.
- No app reinstall.
- No raw archive change.
- No runtime directory move.

Machine-readable boundary summary: Memory Atlas v1.2 S01 Review; MA-V12-S01-REVIEW; ACC-MA-V12-S01-REVIEW; stage_s01_review_passed_pending_s02_no_github_main_upload; validate:v1.2-s01-review; memory_atlas_v1_2_s01_review.md; S01 Review; pending S02 P1; No GitHub main upload in this review; No S02 work; No app reinstall; No raw archive change; No runtime directory move.

## v1.2 S01 P3 Requirements Freeze

状态：`phase_s01_p3_requirements_freeze_completed_pending_s01_review`。

任务 ID：`MA-V12-S01P3`。

验收 ID：`ACC-MA-V12-S01P3`。

S01 P3 写入 v1.2 需求冻结：四线范围、14 Stage 执行规则、raw 公开授权、凭证排除、
后续其他 agent source registry 扩展规则进入机器门禁。README、AGENTS、人类入口和
运行门禁说明已桥接旧 raw/private 边界。

涉及文件：

- `机器治理/运行门禁/v1.2需求冻结清单.json`
- `docs/reviews/memory_atlas_v1_2_s01_p3_requirements_freeze.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p3.cjs`

验收：

- `validate:v1.2-s01-p3`
- `ACC-MA-V12-S01P3`
- S01 P3
- `v1.2需求冻结清单.json`
- README/AGENTS bridge
- No GitHub main upload in this phase

边界：

- No S01 review.
- No S02.
- No app reinstall.
- No GitHub main upload in this phase.
- No apps/scripts/tests/config move.
- No raw archive change.

Machine-readable boundary summary: Memory Atlas v1.2 S01 P3 Requirements Freeze; MA-V12-S01P3; ACC-MA-V12-S01P3; phase_s01_p3_requirements_freeze_completed_pending_s01_review; validate:v1.2-s01-p3; memory_atlas_v1_2_s01_p3_requirements_freeze.md; v1.2需求冻结清单.json; S01 P3; No GitHub main upload in this phase; No S01 review; No S02; No app reinstall; No apps/scripts/tests/config move; No raw archive change.

## v1.2 S01 P2 Double Plane Creation

状态：`phase_s01_p2_double_plane_created_pending_s01_p3`。

任务 ID：`MA-V12-S01P2`。

验收 ID：`ACC-MA-V12-S01P2`。

S01 P2 创建 v1.2 双平面：`人类可读/` 作为用户阅读入口，`机器治理/` 作为机器配置、
验收、证据和运行门禁入口。根目录三件套继续保留为 owner 门面，现有运行代码目录未移动。

涉及文件：

- `人类可读/00_快速入口.md`
- `人类可读/01_v1.2四线14Stage升级总览.md`
- `机器治理/README.md`
- `docs/reviews/memory_atlas_v1_2_s01_p2_double_plane_creation.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs`

验收：

- `validate:v1.2-s01-p2`
- `ACC-MA-V12-S01P2`
- S01 P2
- `人类可读/00_快速入口.md`
- `机器治理/README.md`
- root owner three files preserved
- No GitHub main upload in this phase

边界：

- No S01 P3.
- No v1.2 requirements freeze config in this phase.
- No GitHub main upload in this phase.
- No apps/scripts/tests/config move.
- No raw archive change.

Machine-readable boundary summary: Memory Atlas v1.2 S01 P2 Double Plane Creation; MA-V12-S01P2; ACC-MA-V12-S01P2; phase_s01_p2_double_plane_created_pending_s01_p3; validate:v1.2-s01-p2; memory_atlas_v1_2_s01_p2_double_plane_creation.md; S01 P2; No GitHub main upload in this phase; No S01 P3; No v1.2 requirements freeze config in this phase; No apps/scripts/tests/config move; No raw archive change.

## v1.2 S01 P1 Current State Audit

状态：`phase_s01_p1_current_state_audited_pending_s01_p2`。

任务 ID：`MA-V12-S01P1`。

验收 ID：`ACC-MA-V12-S01P1`。

S01 P1 完成 v1.2 正式执行前的现状核验：确认 TaskPack/Roadmap 输入、canonical
repo、三件套、Memory Atlas package、现有治理和运行目录位置、双平面缺口，以及
v1.1.x raw/private 边界中需要被 v1.2 替换或桥接的规则。

涉及文件：

- `docs/reviews/memory_atlas_v1_2_s01_p1_current_state_audit.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.2-s01-p1`
- `ACC-MA-V12-S01P1`
- S01 P1
- TaskPack/Roadmap hashes recorded
- old boundary replacement needs listed
- No GitHub main upload in this phase

边界：

- No S01 P2.
- No S01 P3.
- No GitHub main upload in this phase.
- No apps/scripts/tests/config move.
- No AGENTS taskpack dump.
- No raw archive change.

Machine-readable boundary summary: Memory Atlas v1.2 S01 P1 Current State Audit; MA-V12-S01P1; ACC-MA-V12-S01P1; phase_s01_p1_current_state_audited_pending_s01_p2; validate:v1.2-s01-p1; memory_atlas_v1_2_s01_p1_current_state_audit.md; S01 P1; No GitHub main upload in this phase; No S01 P2; No S01 P3; No apps/scripts/tests/config move; No AGENTS taskpack dump; No raw archive change.

## v1.1.7 Final GitHub Main Upload

状态：`final_github_main_upload_completed`。

任务 ID：`MA-V117-FINAL-UPLOAD`。

验收 ID：`ACC-MA-V117-FINAL-GITHUB-MAIN`。

本 final upload 将 Memory Atlas v1.1.7 Stage 0-10 的完整开发、验收、
治理记录和恢复资料同步到 GitHub main。GitHub main points at the final
upload commit，并作为后续 agent 的恢复源。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_final_github_main_upload.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_final_upload.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-final-upload`
- `validate:v1.1.7-stage10`
- `ACC-MA-V117-FINAL-GITHUB-MAIN`
- GitHub main points at the final upload commit
- No remote development branch
- No open pull request

边界：

- No remote development branch.
- No open pull request.
- No Cloudflare live deploy.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.

Machine-readable boundary summary: Final GitHub Main Upload; MA-V117-FINAL-UPLOAD; ACC-MA-V117-FINAL-GITHUB-MAIN; final_github_main_upload_completed; validate:v1.1.7-final-upload; validate:v1.1.7-stage10; GitHub main points at the final upload commit; No remote development branch; No open pull request; No Cloudflare live deploy; No raw/private data read; No direct active-memory writeback; No proposal queue write.

## v1.1.7 Stage 10 Review：Final Hardening Gate

状态：`stage_10_review_passed_pending_final_github_main_upload`。

任务 ID：`MA-V117-S10-REVIEW`。

验收 ID：`ACC-MA-V117-S10-REVIEW`。

Stage 10 Review 固定 Stage 10 Phase 10.1 Final hardening upload readiness，
并把本地最终验收门槛绑定到 whole-project validator。该 review 只补 review
artifact、stage-level validator、Part 2 schema compatibility hardening 和治理记录。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage10_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage10.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_part2_stage1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage10`
- `ACC-MA-V117-S10-REVIEW`
- Stage 10 Review
- Stage 10 Phase 10.1
- Final hardening upload readiness
- `validate:v1.1.7-stage10-phase1`
- `validate:whole-project`
- `validate:part2-stage1`
- schema compatibility hardening
- legacy whole-project validator hardening
- Chinese-first copy hardening
- `memory_starfield_spike_fixture.v1_1_7_stage4_phase2`
- `memory_river_spike_fixture.v1_1_7_stage5_phase2`
- pending final one-time GitHub main upload

边界：

- No intermediate GitHub upload.
- No GitHub main upload in this review.
- No remote development branch.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No Cloudflare deploy.

Machine-readable boundary summary: Stage 10 Review; MA-V117-S10-REVIEW; ACC-MA-V117-S10-REVIEW; stage_10_review_passed_pending_final_github_main_upload; validate:v1.1.7-stage10; Stage 10 Phase 10.1; Final hardening upload readiness; validate:v1.1.7-stage10-phase1; validate:whole-project; validate:part2-stage1; schema compatibility hardening; legacy whole-project validator hardening; Chinese-first copy hardening; memory_starfield_spike_fixture.v1_1_7_stage4_phase2; memory_river_spike_fixture.v1_1_7_stage5_phase2; pending final one-time GitHub main upload; No intermediate GitHub upload; No GitHub main upload in this review; No remote development branch; No raw/private data read; No direct active-memory writeback; No proposal queue write; No agent apply.

## v1.1.7 Stage 10 Phase 10.1：Final Hardening Upload Readiness

状态：`phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review`。

任务 ID：`MA-V117-S10P01`。

验收 ID：`ACC-MA-V117-S10P01`。

合同 ID：`memory_atlas_v1_1_7_final_hardening_upload_readiness_contract`。

本 phase 建立 Stage 10 final hardening/upload readiness 合同，固定后续
Stage 10 review 必须证明的六类矩阵：

- `performance_safety_accessibility_matrix`
- `release_rollback_matrix`
- `final_validation_matrix`
- `github_main_upload_matrix`
- `governance_sync_matrix`
- `new_machine_recovery_matrix`

涉及文件：

- `docs/product/memory_atlas_v1_1_7_final_hardening_upload_readiness_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage10_phase1_final_hardening_upload_readiness_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage10_phase1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage10-phase1`
- `ACC-MA-V117-S10P01`
- Stage 10 Phase 10.1
- desktop target 45-60 FPS
- reduced-motion fallback
- Stage 9 review must be complete
- pending Stage 10 review

边界：

- No intermediate GitHub upload.
- No GitHub main upload in this phase.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No Cloudflare deploy.

Machine-readable boundary summary: Stage 10 Phase 10.1; MA-V117-S10P01; ACC-MA-V117-S10P01; phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review; memory_atlas_v1_1_7_final_hardening_upload_readiness_contract; validate:v1.1.7-stage10-phase1; performance_safety_accessibility_matrix; release_rollback_matrix; final_validation_matrix; github_main_upload_matrix; governance_sync_matrix; new_machine_recovery_matrix; desktop target 45-60 FPS; reduced-motion fallback; Stage 9 review must be complete; pending Stage 10 review; No intermediate GitHub upload; No GitHub main upload in this phase; No raw/private data read; No direct active-memory writeback; No proposal queue write; No agent apply.

## v1.1.7 Stage 9 Review：Cross-board Shared State Gate

状态：`stage_9_review_passed_pending_stage10_no_github_main_upload`。

任务 ID：`MA-V117-S9-REVIEW`。

验收 ID：`ACC-MA-V117-S9-REVIEW`。

Stage 9 is review-passed and pending Stage 10. 本 review 固定一个已完成
phase gate：Phase 9.1 Cross-board shared state、synchronized filters 和
Inspector explanation layer。它只补 Stage 9 review artifact、stage-level
validator 和治理记录。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage9_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage9.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage9`
- `ACC-MA-V117-S9-REVIEW`
- Phase 9.1
- Cross-board shared state
- synchronized filters
- Inspector explanation layer
- `cross_board_shared_state.v1_1_7_stage9_phase1`
- `inspector_explanation_layer.v1_1_7_stage9_phase1`
- `shared_state_filters`
- `synchronized_filters`
- `inspector_explanation_layer`
- pending Stage 10

边界：

- No Stage 10 work.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No Cloudflare deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Stage 9 Review; MA-V117-S9-REVIEW; ACC-MA-V117-S9-REVIEW; stage_9_review_passed_pending_stage10_no_github_main_upload; validate:v1.1.7-stage9; Phase 9.1; Cross-board shared state; synchronized filters; Inspector explanation layer; cross_board_shared_state.v1_1_7_stage9_phase1; inspector_explanation_layer.v1_1_7_stage9_phase1; shared_state_filters; synchronized_filters; inspector_explanation_layer; pending Stage 10; No Stage 10 work; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No proposal queue write; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 9 Phase 9.1：Cross-board Shared State

状态：`phase_9_1_cross_board_shared_state_completed_pending_stage9_review`。

任务 ID：`MA-V117-S9P01`。

验收 ID：`ACC-MA-V117-S9P01`。

本 phase 将 Cross-board shared state、synchronized filters 和 Inspector
explanation layer 固定为 production runtime 的可验收接口。Runtime version 为
`cross_board_shared_state.v1_1_7_stage9_phase1`，Inspector layer version 为
`inspector_explanation_layer.v1_1_7_stage9_phase1`。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage9_phase1.cjs`
- `apps/memory-atlas/scripts/validate_cross_board_shared_state_browser.cjs`
- `docs/product/memory_atlas_v1_1_7_stage9_phase1_cross_board_shared_state_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage9_phase1_cross_board_shared_state_acceptance.md`

验收：

- `validate:v1.1.7-stage9-phase1`
- `validate:cross-board-shared-state-browser`
- `ACC-MA-V117-S9P01`
- Browser gate 覆盖 app root marker、Interaction Lens marker、`window.__memoryAtlasStage9Phase1()`、shared_state_filters、synchronized_filters、Inspector explanation layer、screenshot 和 console safety。

边界：

- No Stage 9 review.
- No Stage 10.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No Cloudflare deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Phase 9.1; Cross-board shared state; MA-V117-S9P01; ACC-MA-V117-S9P01; phase_9_1_cross_board_shared_state_completed_pending_stage9_review; validate:v1.1.7-stage9-phase1; validate:cross-board-shared-state-browser; cross_board_shared_state.v1_1_7_stage9_phase1; inspector_explanation_layer.v1_1_7_stage9_phase1; shared_state_filters; synchronized_filters; inspector_explanation_layer; Inspector explanation layer; No Stage 9 review; No Stage 10; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No proposal queue write; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 8 Review：Summary Closure Gate

状态：`stage_8_review_passed_pending_stage9_no_github_main_upload`。

任务 ID：`MA-V117-S8-REVIEW`。

验收 ID：`ACC-MA-V117-S8-REVIEW`。

Stage 8 is review-passed and pending Stage 9. 本 review 固定一个已完成
phase gate：Phase 8.1 Summary and iteration closure。它只补 Stage 8 review
artifact、stage-level validator 和治理记录。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage8_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage8.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage8`
- `ACC-MA-V117-S8-REVIEW`
- Phase 8.1
- Summary and iteration closure
- pending Stage 9

边界：

- No Stage 9 work.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No Cloudflare deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Stage 8 Review; MA-V117-S8-REVIEW; ACC-MA-V117-S8-REVIEW; stage_8_review_passed_pending_stage9_no_github_main_upload; validate:v1.1.7-stage8; Phase 8.1; Summary and iteration closure; summary_iteration_closure_runtime.v1_1_7_stage8_phase1; memory_atlas_summary_closure.v1_1_7_stage8_phase1; change_comparison; stale_conflict_signals; proposal_candidates; pending Stage 9; No Stage 9 work; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No proposal queue write; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 8 Phase 8.1：Summary and Iteration Closure Runtime

状态：`phase_8_1_summary_iteration_closure_runtime_completed_pending_stage8_review`。

任务 ID：`MA-V117-S8P01`。

验收 ID：`ACC-MA-V117-S8P01`。

本 phase 将 Summary and iteration closure 接入 production `summary` view。
Runtime version 为 `summary_iteration_closure_runtime.v1_1_7_stage8_phase1`，
closure schema version 为 `memory_atlas_summary_closure.v1_1_7_stage8_phase1`。
运行时基于 Stage 7.2 `memory_atlas_review_summary.v1_1_7_stage7_phase2` 派生
`change_comparison`、`stale_conflict_signals` 和 `proposal_candidates`。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage8_phase1.cjs`
- `apps/memory-atlas/scripts/validate_summary_iteration_closure_browser.cjs`
- `docs/product/summary_iteration_closure_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage8_phase1_summary_iteration_closure_acceptance.md`

验收：

- `validate:v1.1.7-stage8-phase1`
- `validate:summary-iteration-closure-browser`
- `ACC-MA-V117-S8P01`
- Browser gate 覆盖 runtime root、change comparison、stale/conflict signals、proposal candidates、debug signal、screenshot 和 console safety。

边界：

- No Stage 8 review.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No Cloudflare deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Phase 8.1; Summary and iteration closure; MA-V117-S8P01; ACC-MA-V117-S8P01; phase_8_1_summary_iteration_closure_runtime_completed_pending_stage8_review; validate:v1.1.7-stage8-phase1; validate:summary-iteration-closure-browser; summary_iteration_closure_runtime.v1_1_7_stage8_phase1; memory_atlas_summary_closure.v1_1_7_stage8_phase1; memory_atlas_review_summary.v1_1_7_stage7_phase2; change_comparison; stale_conflict_signals; proposal_candidates; No Stage 8 review; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 7 Review：Search and Review Runtime Gate

状态：`stage_7_review_passed_pending_stage8_no_github_main_upload`。

任务 ID：`MA-V117-S7-REVIEW`。

验收 ID：`ACC-MA-V117-S7-REVIEW`。

Stage 7 is review-passed and pending Stage 8. 本 review 固定两个已完成
phase gate：Phase 7.1 Search 2.0，以及 Phase 7.2 Review / Summary /
Iteration。它只补 Stage 7 review artifact、stage-level validator 和治理记录。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage7_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage7`
- `ACC-MA-V117-S7-REVIEW`
- Phase 7.1
- Phase 7.2
- Search 2.0
- Review / Summary / Iteration
- pending Stage 8

边界：

- No Stage 8 work.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No Cloudflare deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Stage 7 Review; MA-V117-S7-REVIEW; ACC-MA-V117-S7-REVIEW; stage_7_review_passed_pending_stage8_no_github_main_upload; validate:v1.1.7-stage7; Phase 7.1; Phase 7.2; Search 2.0; Review / Summary / Iteration; pending Stage 8; No Stage 8 work; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 7 Phase 7.2：Review / Summary / Iteration Runtime

状态：`phase_7_2_review_summary_iteration_runtime_completed_pending_stage7_review`。

任务 ID：`MA-V117-S7P02`。

验收 ID：`ACC-MA-V117-S7P02`。

本 phase 将 Review / Summary / Iteration 接入 production `summary` view。
Runtime version 为 `review_summary_iteration_runtime.v1_1_7_stage7_phase2`，
schema version 为 `memory_atlas_review_summary.v1_1_7_stage7_phase2`。运行时回答八个复盘问题，并显示
`proposal_candidate`、`evidence_refs` 和 `iteration_backlog`。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7_phase2.cjs`
- `apps/memory-atlas/scripts/validate_review_summary_iteration_browser.cjs`
- `docs/product/review_summary_iteration_workflow_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage7_phase2_review_summary_iteration_runtime_acceptance.md`

验收：

- `validate:v1.1.7-stage7-phase2`
- `validate:review-summary-iteration-browser`
- `ACC-MA-V117-S7P02`
- Browser gate 覆盖 runtime root、八问、schema output、debug signal、screenshot 和 console safety。

Machine-readable boundary summary: Phase 7.2; Review / Summary / Iteration; MA-V117-S7P02; ACC-MA-V117-S7P02; phase_7_2_review_summary_iteration_runtime_completed_pending_stage7_review; validate:v1.1.7-stage7-phase2; validate:review-summary-iteration-browser; review_summary_iteration_runtime.v1_1_7_stage7_phase2; memory_atlas_review_summary.v1_1_7_stage7_phase2; proposal_candidate; evidence_refs; iteration_backlog; No Stage 8 summary closure; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 7 Phase 7.1：Search 2.0 Runtime

状态：`phase_7_1_search_2_0_runtime_completed_pending_stage7_review`。

任务 ID：`MA-V117-S7P01`。

验收 ID：`ACC-MA-V117-S7P01`。

本 phase 将 Search 2.0 接入 production Search view。Runtime version 为
`search_2_0_runtime.v1_1_7_stage7_phase1`，session summary version 为
`search_2_0_session_summary.v1_1_7_stage7_phase1`。搜索结果显示
`matched_reason`、`evidence_refs`、`proposal_candidate`，并提供
`jump_to_starfield`、`jump_to_river`、`open_inspector` 三类动作。空结果
显示 `zero_result_recovery`，只给 later review hint，不执行 Review /
Summary / Iteration runtime。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7_phase1.cjs`
- `apps/memory-atlas/scripts/validate_search_2_0_browser.cjs`
- `docs/product/search_2_0_workflow_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage7_phase1_search_2_0_runtime_acceptance.md`

验收：

- `validate:v1.1.7-stage7-phase1`
- `validate:search-2-0-browser`
- `ACC-MA-V117-S7P01`
- Browser gate 覆盖 result fields、debug signal、zero recovery、Starfield/River/Inspector jumps、screenshot 和 console safety。

Machine-readable boundary summary: Phase 7.1; Search 2.0; MA-V117-S7P01; ACC-MA-V117-S7P01; phase_7_1_search_2_0_runtime_completed_pending_stage7_review; validate:v1.1.7-stage7-phase1; validate:search-2-0-browser; search_2_0_runtime.v1_1_7_stage7_phase1; search_2_0_session_summary.v1_1_7_stage7_phase1; matched_reason; evidence_refs; No Review / Summary / Iteration runtime; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 6 Review：Data Map Gate

状态：`stage_6_review_passed_pending_stage7_no_github_main_upload`。

任务 ID：`MA-V117-S6-REVIEW`。

验收 ID：`ACC-MA-V117-S6-REVIEW`。

Stage 6 is review-passed and pending Stage 7. 本 review 固定两个已完成
phase：

1. Phase 6.1：Structure Model。
2. Phase 6.2：Details & Editing。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage6_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage6`
- `ACC-MA-V117-S6-REVIEW`
- Clean-tree gate 覆盖 Stage 5 continuity、Phase 6.1、Phase 6.2、records、canonical remote 和 no-upload boundary。

Machine-readable boundary summary: Stage 6 Review; MA-V117-S6-REVIEW; ACC-MA-V117-S6-REVIEW; stage_6_review_passed_pending_stage7_no_github_main_upload; validate:v1.1.7-stage6; Phase 6.1; Phase 6.2; pending Stage 7; No Stage 7 work; No Search 2.0 work; No Review / Summary / Iteration runtime work; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 6 Phase 6.2：Details & Editing

状态：`phase_6_2_data_map_detail_proposal_completed_pending_stage6_review`。

任务 ID：`MA-V117-S6P02`。

验收 ID：`ACC-MA-V117-S6P02`。

本 phase 在 production Data Guide 中加入 `数据导图详情面板` 和
`数据导图 proposal 入口`。详情面板版本为
`data_map_detail_panel.v1_1_7_stage6_phase2`，proposal 入口版本为
`data_map_proposal_entry.v1_1_7_stage6_phase2`。点击节点后可见 asset、
theme、suggested action、importance、priority；proposal 入口保持
proposal-only，只导出 proposal JSON，不直接写 active memory。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6_phase2.cjs`
- `apps/memory-atlas/scripts/validate_data_map_detail_proposal_browser.cjs`
- `docs/product/data_map_iteration_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage6_phase2_data_map_detail_proposal_acceptance.md`

验收：

- `validate:v1.1.7-stage6-phase2`
- `validate:data-map-detail-proposal-browser`
- `ACC-MA-V117-S6P02`
- Browser gate 覆盖节点点击、详情字段、proposal export、debug signal、screenshot 和 console safety。

Machine-readable boundary summary: Phase 6.2; Details & Editing; MA-V117-S6P02; ACC-MA-V117-S6P02; phase_6_2_data_map_detail_proposal_completed_pending_stage6_review; validate:v1.1.7-stage6-phase2; validate:data-map-detail-proposal-browser; data_map_detail_panel.v1_1_7_stage6_phase2; data_map_proposal_entry.v1_1_7_stage6_phase2; 数据导图详情面板; 数据导图 proposal 入口; proposal-only; No Stage 6 review; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 6 Phase 6.1：Data Map Structure Model

状态：`phase_6_1_data_map_structure_model_completed_pending_stage6_review`。

任务 ID：`MA-V117-S6P01`。

验收 ID：`ACC-MA-V117-S6P01`。

本 phase 将 production Data Guide 固定为
`data_map_structure_model.v1_1_7_stage6_phase1`，并加入
`data_map_relation_explanation.v1_1_7_stage6_phase1`。四层结构为
`source_layer`、`profile_layer`、`project_decision_layer`、
`action_opportunity_layer`。每层记录 node types、fields、interaction 和
detail entry。Relation Explanation 支持点击关系后展示 source、strength、
evidence、time，并保持 default collapsed fallback。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6_phase1.cjs`
- `apps/memory-atlas/scripts/validate_data_map_structure_browser.cjs`
- `docs/product/data_map_iteration_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage6_phase1_data_map_structure_acceptance.md`

验收：

- `validate:v1.1.7-stage6-phase1`
- `validate:data-map-structure-browser`
- `ACC-MA-V117-S6P01`
- Browser gate 覆盖四层结构、relation click、debug signal、screenshot 和 console safety。

Machine-readable boundary summary: Phase 6.1; Structure Model; Relation Explanation; MA-V117-S6P01; ACC-MA-V117-S6P01; phase_6_1_data_map_structure_model_completed_pending_stage6_review; validate:v1.1.7-stage6-phase1; validate:data-map-structure-browser; data_map_structure_model.v1_1_7_stage6_phase1; data_map_relation_explanation.v1_1_7_stage6_phase1; source_layer; profile_layer; project_decision_layer; action_opportunity_layer; No Phase 6.2; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 5 Review：Memory River Gate

状态：`stage_5_review_passed_pending_stage6_no_github_main_upload`。

任务 ID：`MA-V117-S5-REVIEW`。

验收 ID：`ACC-MA-V117-S5-REVIEW`。

Stage 5 is review-passed and pending Stage 6. 本 review 固定三个已完成
phase：

1. Phase 5.1：Interaction Contract。
2. Phase 5.2：C3 River Spike。
3. Phase 5.3：Timeline Integration。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage5_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage5`
- `ACC-MA-V117-S5-REVIEW`
- Stage 4 review continuity、Phase 5.1 / Phase 5.2 / Phase 5.3 validators、records、package script 和 no-upload boundary 均需通过。
- Browser evidence remains `validate:memory-river-spike-browser` and `validate:memory-river-integration-browser`。

Machine-readable boundary summary: Stage 5 Review; MA-V117-S5-REVIEW; ACC-MA-V117-S5-REVIEW; stage_5_review_passed_pending_stage6_no_github_main_upload; validate:v1.1.7-stage5; Phase 5.1; Phase 5.2; Phase 5.3; pending Stage 6; No Stage 6 work; No Data Map work; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 5 Phase 5.3：Timeline Integration

状态：`phase_5_3_timeline_integration_completed_pending_stage5_review`。

任务 ID：`MA-V117-S5P03`。

验收 ID：`ACC-MA-V117-S5P03`。

本 phase 将 production Timeline 默认接入
`memory_river_integration.v1_1_7_stage5_phase3`，保持 default memory-river，
并保留 legacy rollback。回滚路径包括 in-app `Legacy` toggle、
`timelineRenderer=legacy`、`timeline=legacy`、localStorage 和 env override。
Browser gate 覆盖 default Memory River、legacy rollback、URL rollback、brush
interaction、selected range、evidence layers、screenshot 和 console safety。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/config/visualFlags.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase3.cjs`
- `apps/memory-atlas/scripts/validate_memory_river_integration_browser.cjs`
- `docs/product/memory_atlas_timeline_replacement_plan.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage5_phase3_timeline_integration_acceptance.md`

验收：

- `validate:v1.1.7-stage5-phase3`
- `validate:memory-river-integration-browser`
- `ACC-MA-V117-S5P03`
- old Timeline rollback available；new page default enabled。

Machine-readable boundary summary: Phase 5.3; MA-V117-S5P03; ACC-MA-V117-S5P03; phase_5_3_timeline_integration_completed_pending_stage5_review; validate:v1.1.7-stage5-phase3; validate:memory-river-integration-browser; memory_river_integration.v1_1_7_stage5_phase3; default memory-river; legacy rollback; timelineRenderer=legacy; brush interaction; No Stage 5 review; No Stage 6; No raw/private data read; No direct active-memory writeback; No agent apply; No deploy; No GitHub main upload; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 5 Phase 5.2：C3 River Spike

状态：`phase_5_2_c3_river_spike_completed_pending_stage5_review`。

任务 ID：`MA-V117-S5P02`。

验收 ID：`ACC-MA-V117-S5P02`。

本 phase 将 isolated `memory-river-spike` 升级为
`memory_river_c3_spike.v1_1_7_stage5_phase2`。交付面覆盖 year/month/week/day
time scale、zoom、brush selected range summary、theme trend lanes、Black Hole /
Proto-Star date positioning、reduced motion 和浏览器截图验收。

涉及文件：

- `apps/memory-atlas/src/experiments/memory-river-spike/README.md`
- `apps/memory-atlas/src/experiments/memory-river-spike/fixture.ts`
- `apps/memory-atlas/src/experiments/memory-river-spike/index.html`
- `apps/memory-atlas/src/experiments/memory-river-spike/main.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase2.cjs`
- `apps/memory-atlas/scripts/validate_memory_river_spike_browser.cjs`
- `docs/product/memory_river_c3_spike_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage5_phase2_c3_river_spike_acceptance.md`

验收：

- `validate:v1.1.7-stage5-phase2`
- `validate:memory-river-spike-browser`
- `ACC-MA-V117-S5P02`
- Browser gate 覆盖 time levels、zoom、brush selected range、trend lanes、Black Hole / Proto-Star positioning、reduced motion 和 screenshot。

Machine-readable boundary summary: Stage 5 Phase 5.2 C3 River Spike; MA-V117-S5P02; ACC-MA-V117-S5P02; phase_5_2_c3_river_spike_completed_pending_stage5_review; validate:v1.1.7-stage5-phase2; validate:memory-river-spike-browser; memory_river_c3_spike.v1_1_7_stage5_phase2; Phase 5.2; No production Timeline replacement; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 5 Phase 5.1：Memory River Interaction Contract

状态：`phase_5_1_interaction_contract_completed_pending_stage5_review`。

任务 ID：`MA-V117-S5P01`。

验收 ID：`ACC-MA-V117-S5P01`。

本 phase 固定 `memory_river_interaction_contract.v1_1_7_stage5_phase1` 和
`memory_river_feedback_contract.v1_1_7_stage5_phase1`。Memory River 必须不是
日期列表、表格或 static scatter；交互合同覆盖 zoom、brush、theme_lanes、
event_points、status_bands 和 detail_panel；反馈合同覆盖 visual_feedback、
optional_audio、pseudo_haptic、reduced_motion、feedback_disable_control、
audio_default_off 和 vibration_not_required。

涉及文件：

- `docs/product/memory_river_interaction_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage5_phase1_interaction_contract_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage5-phase1`
- `ACC-MA-V117-S5P01`
- Stage 4 review continuity、interaction contract、feedback contract、acceptance、records、package script 和 no-runtime/no-upload boundary 均需通过。

Machine-readable boundary summary: Stage 5 Phase 5.1 Interaction Contract; MA-V117-S5P01; ACC-MA-V117-S5P01; phase_5_1_interaction_contract_completed_pending_stage5_review; memory_river_interaction_contract.v1_1_7_stage5_phase1; memory_river_feedback_contract.v1_1_7_stage5_phase1; No Stage 5.2; No C3 River Spike; No Timeline replacement; No runtime UI/CSS; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 4 Review：Memory Starfield Gate

状态：`stage_4_review_passed_pending_stage5_no_github_main_upload`。

任务 ID：`MA-V117-S4-REVIEW`。

验收 ID：`ACC-MA-V117-S4-REVIEW`。

Stage 4 is review-passed and pending Stage 5. 本 review 固定三个已完成 phase：

1. Phase 4.1：Visual Contract Update。
2. Phase 4.2：C3 Starfield Spike。
3. Phase 4.3：Integration。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage4_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage4`
- `ACC-MA-V117-S4-REVIEW`
- Stage 3 review continuity、Phase 4.1 / Phase 4.2 / Phase 4.3 validators、records、package script 和 no-upload boundary 均需通过。
- Browser evidence validators remain `validate:memory-starfield-spike-browser` and `validate:memory-starfield-integration-browser`.

Machine-readable boundary summary: Stage 4 Review; Phase 4.1; Phase 4.2; Phase 4.3; pending Stage 5; No GitHub main upload; No Stage 5 work; No raw/private data read; No direct active-memory writeback; No agent apply; No build/deploy/app install; no GitHub main upload before whole Stage 0-10 completion.

## Memory Atlas v1.1.7 Stage 4 Phase 4.3 Integration

状态：`phase_4_3_integration_completed_pending_stage4_review`。

任务 ID：`MA-V117-S4P03`。

验收 ID：`ACC-MA-V117-S4P03`。

本 phase 固定 `memory_starfield_integration.v1_1_7_stage4_phase3` 和
`memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3`。Production Galaxy
默认进入 new memory-starfield，保留 `legacy` 作为 Feature Flag rollback；质量、
颜色、亮度和轨迹来自 redacted `universe_state.sample.json` Snapshot Mapping，
不可用时 fallback 到 atlas nodes。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/GalaxyScene.tsx`
- `apps/memory-atlas/src/config/visualFlags.ts`
- `apps/memory-atlas/src/models/starfieldMapping.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase3.cjs`
- `apps/memory-atlas/scripts/validate_memory_starfield_integration_browser.cjs`
- `docs/acceptance/memory_atlas_v1_1_7_stage4_phase3_integration_acceptance.md`

验收：

- `validate:v1.1.7-stage4-phase3`
- `validate:memory-starfield-integration-browser`
- `ACC-MA-V117-S4P03`
- Browser validator 必须证明默认 new memory-starfield、legacy rollback、
  snapshot mapping、formula panel 和 screenshot。

Machine-readable boundary summary: Stage 4 Phase 4.3 Integration; MA-V117-S4P03; ACC-MA-V117-S4P03; phase_4_3_integration_completed_pending_stage4_review; memory_starfield_integration.v1_1_7_stage4_phase3; memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3; No Stage 5; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 4 Phase 4.2：C3 Starfield Spike

状态：`phase_4_2_c3_starfield_spike_completed_pending_stage4_review`。

任务 ID：`MA-V117-S4P02`。

验收 ID：`ACC-MA-V117-S4P02`。

本 phase 固定 `memory_starfield_c3_spike.v1_1_7_stage4_phase2`。C3
Starfield Spike 在 isolated experiment 内覆盖 GPU particle spike、Flow Field /
Curl Noise、Cluster Gravity、Hover Cards B2、浏览器 FPS 和 screenshot gate。
生产 Galaxy 未替换，生产 route/navigation/feature flag default 未改。

涉及文件：

- `apps/memory-atlas/src/experiments/memory-starfield-spike/main.ts`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/shaders/flowField.ts`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/fixture.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase2.cjs`
- `apps/memory-atlas/scripts/validate_memory_starfield_spike_browser.cjs`
- `docs/acceptance/memory_atlas_v1_1_7_stage4_phase2_c3_starfield_spike_acceptance.md`

验收：

- `validate:v1.1.7-stage4-phase2`
- `validate:memory-starfield-spike-browser`
- `ACC-MA-V117-S4P02`
- Browser validator 必须证明 `>=10k particles`、`>=30 FPS`、`curl_noise_shader`、particle trails、gravity sources、Hover Cards B2 和 screenshot。

Machine-readable boundary summary: C3 Starfield Spike; memory_starfield_c3_spike.v1_1_7_stage4_phase2; No production Galaxy replacement; No production route/navigation change; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 4 Phase 4.1：Visual Contract Update

状态：`phase_4_1_visual_contract_update_completed_pending_stage4_review`。

任务 ID：`MA-V117-S4P01`。

验收 ID：`ACC-MA-V117-S4P01`。

本 phase 固定 `memory_starfield_visual_contract.v1_1_7_stage4_phase1` 和
`memory_terrain_layer.v1_1_7_stage4_phase1`。Visual Contract Update 把
Memory Starfield 从主观视觉方向升级为可测验收，要求星云、流场、粒子轨迹、
引力源、黑洞、新生星云和地形层，并定义长期主题、成长带、迁移流、遗迹、
黑洞和机会六类地形语义。

涉及文件：

- `docs/product/memory_starfield_visual_contract.md`
- `docs/architecture/memory_terrain_layer.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage4_phase1_visual_contract_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage4-phase1`
- `ACC-MA-V117-S4P01`
- Stage 3 continuity、visual contract、terrain layer、acceptance、records、package script 和 no-runtime/no-upload boundary 均需通过。

Machine-readable boundary summary: Visual Contract Update; memory_starfield_visual_contract.v1_1_7_stage4_phase1; memory_terrain_layer.v1_1_7_stage4_phase1; No Phase 4.2; No runtime renderer replacement; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; No build/deploy/app install; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 3 Review：Default Home Gate

状态：`stage_3_review_passed_pending_stage4_no_github_main_upload`。

任务 ID：`MA-V117-S3-REVIEW`。

验收 ID：`ACC-MA-V117-S3-REVIEW`。

Stage 3 is review-passed and pending Stage 4. 本 review 固定两个已完成 phase：

1. Phase 3.1：Default Home Structure。
2. Phase 3.2：Home Detail Operations。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage3_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage3`
- `ACC-MA-V117-S3-REVIEW`
- Stage 2 review continuity、Phase 3.1 / Phase 3.2 validators、records、package script 和 no-upload boundary 均需通过。

Machine-readable boundary summary: Stage 3 Review; Phase 3.1; Phase 3.2; pending Stage 4; No GitHub main upload; No Stage 4 work; No raw/private data read; No direct active-memory writeback; No agent apply; No build/deploy/app install; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 3 Phase 3.2：Home Detail Operations

状态：`phase_3_2_home_detail_operations_completed_pending_stage3_review`。

任务 ID：`MA-V117-S3P02`。

验收 ID：`ACC-MA-V117-S3P02`。

本 phase 固定 `memory_overview_detail_operations.v1_1_7_stage3_phase2`。
Memory Overview 首页继续以 `home` 为默认入口，并把 Top Actions Section、
Level Assets Section、Theme Categories Section 升级为可见、可点击、可解释的
Home Detail Operations。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_overview_product_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage3_phase2_home_detail_operations_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase2.cjs`
- `config/visualization/model_parameters.universe_state.yaml`

验收：

- `validate:v1.1.7-stage3-phase2`
- `ACC-MA-V117-S3P02`
- Top Actions Section 必须显示 suggestion、reason、priority、status，并通过 `ActionDetailDrawer` 打开 clickable detail entry。
- Level Assets Section 必须显示 `core_profile`、`project`、`decision`、`temporary`、`stale`，并通过 `AssetDetailPanel` 打开 clickable detail entry。
- Theme Categories Section 必须显示 `rising`、`declining`、`conflict`、`opportunity`、`stable`，并通过 `ThemeDetailPanel` 打开 clickable detail entry。

Machine-readable boundary summary: Home Detail Operations; memory_overview_detail_operations.v1_1_7_stage3_phase2; Top Actions Section; Level Assets Section; Theme Categories Section; No Stage 3 Review; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 3 Phase 3.1：Default Home Structure

状态：`phase_3_1_default_home_structure_completed_pending_stage3_review`。

任务 ID：`MA-V117-S3P01`。

验收 ID：`ACC-MA-V117-S3P01`。

本 phase 固定 `memory_overview_default_home.v1_1_7_stage3_phase1`。默认入口为
`home`，Memory Overview 首屏通过结构 rail 和 section markers 呈现 status
summary、suggested actions、weather、black holes、proto-stars、assets、themes
和 entry points。

涉及文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_overview_product_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage3_phase1_default_home_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase1.cjs`
- `config/visualization/model_parameters.universe_state.yaml`

验收：

- `validate:v1.1.7-stage3-phase1`
- `ACC-MA-V117-S3P01`
- 默认 route 必须是 `home`。
- Default Home Structure 必须包含 8 个结构 section。
- 页面必须是 guided work surface，not a pile of cards。

Machine-readable boundary summary: Default Home Structure; memory_overview_default_home.v1_1_7_stage3_phase1; No Stage 3 Phase 3.2; No GitHub main upload; No raw/private data read; No direct active-memory writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 2 Review：Proposal Layer Gate

状态：`stage_2_review_passed_pending_stage3_no_github_main_upload`。

任务 ID：`MA-V117-S2-REVIEW`。

验收 ID：`ACC-MA-V117-S2-REVIEW`。

Stage 2 is review-passed and pending Stage 3. 本 review 固定两个已完成 phase：

1. Phase 2.1：Editable Draft Model and Draft State Store。
2. Phase 2.2：Proposal UI, Proposal Diff Preview and Export / Rollback Contract。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage2_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage2`
- `ACC-MA-V117-S2-REVIEW`
- Stage 1 review continuity、Phase 2.1 / Phase 2.2 validators、records、package script 和 no-upload boundary 均需通过。

Machine-readable boundary summary: Stage 2 Review; Phase 2.1; Phase 2.2; pending Stage 3; No GitHub main upload; No Stage 3 work; No raw/private data read; No direct active-memory writeback; No agent apply; No build/deploy/app install; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 2 Phase 2.2：Proposal UI

状态：`phase_2_2_proposal_ui_completed_pending_stage2_review`。

任务 ID：`MA-V117-S2P02`。

验收 ID：`ACC-MA-V117-S2P02`。

本 phase 在现有 Inspector writeback panel 中接入 Proposal UI。用户可以调整
`importance` 和 `priority`，看到 `original_value`、`proposed_value`、
`impact_summary` 和 `rollback_metadata`，并导出
`memory_atlas_proposal_export.v1` JSON 供后续 human/agent review。

涉及文件：

- `apps/memory-atlas/src/components/ProposalEditor.tsx`
- `apps/memory-atlas/src/components/ProposalDiffPreview.tsx`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/acceptance/memory_atlas_v1_1_7_stage2_phase2_proposal_ui_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2_phase2.cjs`

验收：

- `validate:v1.1.7-stage2-phase2`
- `ACC-MA-V117-S2P02`
- UI 必须显示原值、新值、影响说明和 rollback metadata。
- Export / Rollback Contract 必须保留 proposal-only、conflict check 和 agent/human apply gate。

Machine-readable boundary summary: Proposal UI; ProposalEditor; ProposalDiffPreview; Export / Rollback Contract; No GitHub main upload; No raw/private data read; No direct writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 2 Phase 2.1：Editable Draft Model

状态：`phase_2_1_editable_draft_model_completed_pending_stage2_review`。

任务 ID：`MA-V117-S2P01`。

验收 ID：`ACC-MA-V117-S2P01`。

本 phase 建立 proposal 编辑层的 Editable Draft Model。它定义字段白名单
`importance`、`priority`、`status`、`theme_override`、`action_state`、`note`，
并新增 Draft State Store，用 `memory_atlas_proposal_draft.v1` schema 和
`memory-atlas.proposal-drafts.v1` store key 保存本地未提交调整。

涉及文件：

- `docs/architecture/proposal_edit_model.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage2_phase1_editable_draft_acceptance.md`
- `apps/memory-atlas/src/state/proposalDraftStore.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2_phase1.cjs`
- `config/visualization/model_parameters.universe_state.yaml`

验收：

- `validate:v1.1.7-stage2-phase1`
- `ACC-MA-V117-S2P01`
- Draft Store 必须支持 refresh warning、undo draft change、serialize、parse、load、save、clear。
- 所有 draft change 必须包含 `proposal_only`、`requires_conflict_check`、`requires_agent_or_human_apply` 和 `rollback_hint`。

Machine-readable boundary summary: Editable Draft Model; Draft State Store; No Proposal UI; No GitHub main upload; No raw/private data read; No direct writeback; No agent apply; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 1 Review：Shared State and Detail Layer Gate

状态：`stage_1_review_passed_pending_stage2_no_github_main_upload`。

任务 ID：`MA-V117-S1-REVIEW`。

验收 ID：`ACC-MA-V117-S1-REVIEW`。

Stage 1 is review-passed and pending Stage 2. 本 review 固定四个已完成 phase：

1. Phase 1.1：Universe State shared schema and consumer map。
2. Phase 1.2：Next Action Top 5 and ActionDetailDrawer。
3. Phase 1.3：Level Asset cards and AssetDetailPanel。
4. Phase 1.4：Topic Classification cards and ThemeDetailPanel。

涉及文件：

- `docs/reviews/memory_atlas_v1_1_7_stage1_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1.cjs`
- `apps/memory-atlas/package.json`

验收：

- `validate:v1.1.7-stage1`
- `ACC-MA-V117-S1-REVIEW`
- Stage 0 review continuity、Phase 1.1 / Phase 1.2 / Phase 1.3 / Phase 1.4 validators、records、package script 和 no-upload boundary 均需通过。

Machine-readable boundary summary: Stage 1 Review; pending Stage 2; No GitHub main upload; No Stage 2 work; No raw/private data read; No direct writeback; No proposal write; No agent apply; No build/deploy/app install; no GitHub main upload before whole Stage 0-10 completion.

## v1.1.7 Stage 1 Phase 1.4：Topic Classification Detail

状态：`phase_1_4_topic_classification_detail_completed_pending_stage1_review`。

任务 ID：`MA-V117-S1P04`。

验收 ID：`ACC-MA-V117-S1P04`。

本 phase 把主题分类从统计条升级为可排序、可解释、可点击的 Topic Classification 明细。
首页显示 Topic Classification cards；点击后打开 ThemeDetailPanel，展示主题状态、主题强度、趋势、ROI、冲突、置信度、记录数、近期记录数、代表记录、证据、关联资产/行动、Starfield handoff、River handoff 和 proposal-only 边界。

涉及文件：

- `docs/architecture/theme_category_model.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage1_phase4_topic_classification_acceptance.md`
- `apps/memory-atlas/src/components/ThemeDetailPanel.tsx`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase4.cjs`
- `config/visualization/model_parameters.universe_state.yaml`

验收：

- `validate:v1.1.7-stage1-phase4`
- `ACC-MA-V117-S1P04`
- 每条 Topic Classification 必须包含 `topic_state`、`topic_strength`、`trend`、`confidence`、`record_count`、`evidence_refs`、`matched_reason`、`linked_asset_ids`、`linked_action_ids`、`starfield_handoff`、`river_handoff` 和 `proposal_only`。
- ThemeDetailPanel 只读展示主题分类明细，不写 proposal JSON，不直接修改 active memory。

Machine-readable boundary summary: Topic Classification; ThemeDetailPanel; topic_strength; matched_reason; proposal_only; No raw/private data read; No direct writeback; No proposal write; No GitHub main upload before whole Stage 0-8 completion.

# Memory Atlas Delivery Record

更新时间：2026-07-01

本文件记录 Memory Atlas 的功能清单、交付运行方式、验收标准、历史过程记录、待开发清单和下一位 agent 的接手顺序。模型假设、处理方法、公式和阈值不写在这里，见 `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`。

## 1. 当前目标

Memory Atlas 是一个独立运行但统一承载多数据源的本地优先记忆可视化平台。它不是第三方插件，也不是多个分裂 app。平台首页支持选择分析对象：

1. 总数据源：所有数据来源放在一起。
2. ChatGPT：OpenAI export / memory database 派生数据。
3. Codex：本机 Codex 使用记录、聊天/开发记录、工具调用、错误/中断、偏好信号。

后续微信、小红书、抖音等数据源必须先进入 source registry 和 canonical event contract。没有真实脱敏 ingestion 前，不得在首页展示假数据源或空数据源。

## 2. 交付运行方式

本地运行：

- 技术栈：Vite + React + Three.js。
- 运行目录：`apps/memory-atlas`。
- 构建命令：`npm run build --prefix apps/memory-atlas`。
- 预览命令：`npm run preview --prefix apps/memory-atlas -- --port <port>`。
- 数据快照：本地 app 每次启动先运行真实 Codex/source redacted sync 并重建 `data/derived/visualization/memory_atlas.json`，再复制到 runtime；前端运行时 fetch `/memory_atlas.json`，使用 cache-busted no-store 请求，确保每次打开看到最新快照生成时间，而不是只更新读取时间。

本地 app 入口：

- `~/Downloads/Memory Atlas.app`
- `/Applications/Memory Atlas.app`
- app 图标由 `scripts/install_memory_atlas_app.py` 生成并写入 bundle。
- `MEMORY_ATLAS_REFRESH=1` 表示强制完整 runtime rebuild；默认启动已经会刷新数据快照。
- 关闭 tab 后本地 runtime 通过 heartbeat/release 机制释放后台线程，减少缓存和内存占用。

Cloudflare 方案：

- Cloudflare Pages + Access。
- 构建输出：`apps/memory-atlas/dist`。
- 配置与检查：
  - `wrangler.jsonc`
  - `config/cloudflare/pages_direct_upload.template.json`
  - `config/cloudflare/access_self_hosted_application.template.json`
  - `scripts/preflight_cloudflare_pages_access.py`
  - `docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md`

未来可选：

- 稳定后考虑 Tauri，但每轮开发要提醒用户：前端 writeback 只能生成 proposal；真正写库需受控 agent apply、版本控制、rollback。

## 3. 当前功能清单

全局要求：

- 全中文优先显示。
- 所有板块共享筛选状态、数据源选择、主题/层级/分类筛选和右侧详情同步；Stage 6.1 起 selection/filter/time range/focus 由 typed shared-state reducer 统一管理。
- 所有页面默认可视化程度目标 80%+；列表只能作为 drill-down，不能成为主体验。
- 人类版输出优先：话题、需要做什么、记得做什么、建议做什么、机会、风险、ROI、能力成长，不只显示 agent 内部字段。
- 所有派生数据上传 GitHub 备份；本地临时缓存、构建缓存、`.DS_Store`、Python cache 尽量清理。

导航板块：

- Galaxy：主视觉为银河星云/宇宙天体形态，不是简单光点。按重要性、关联性、层级、主题形成核心、旋臂、星云、天体、邻域层级。支持 hover、点击聚焦、相机飞近、局部邻域分层、折叠高连接主题边线。
- 数据导图：应使用框架导图格式展示来源、画像、项目决策和行动机会，不是普通列表。
- ROI Dashboard：显示 leverage score、推荐动作、层级、主题、增量信号；用于 ROI 排序和决策。
- Obsidian Graph：支持 global/local graph、图谱设置折叠、Focus - Connectivity、节点显示名 `层级 · 主题 · 关键词`，并同步 Inspector。
- Timeline：默认使用 Memory River 渲染器，以 UTC 日期尺度展示 Macro / Meso / Micro 河道、主题/项目/分类 lane、密度背景、真实事件日期 tick、播放游标、black-hole / proto-star / event marker；保留 legacy Timeline feature flag 回滚。Stage 5.2 已支持 Pan/Brush 模式、横向拖拽平移、UTC 时间段 brush selection、Interaction Lens / 首页 / 星系 heading 同步、hover/click redacted event card、click 锁定事件并同步 Inspector，以及 Reduced Motion / optional pseudo-haptic / optional audio 的安全反馈设置。Stage 5.3 已支持 black-hole lifecycle band、proto-star lifecycle growth path、stale/deprecated cooling fade layer，均只使用 redacted derived snapshot 信号。
- Contribution Grid：支持日/周/月/年和年份选择。日/周共享 7 行 x 52-54 列全年坐标，周模式以一整列自然周为对象；月/年共享两年 24 列，年视图纵向展示。
- Word Cloud：Heatmap、Bubble Chart、Word Cloud 三层都可点击并同步右侧详情。
- Search/Review：搜索与复盘必须输出人能直接用的结论和行动，不只给数据库字段。
- Summary & Iteration：包含给 ChatGPT/Codex 使用的建议 `Personalization / Memory`、`Agents.md / 执行规则`、`config.toml`、`Memory`，显示更新时间，标明新增/修改/降权含义。
- Shared State Store：`src/state/sharedAtlasState.ts` 统一记录 selected node、cluster、record、time range、signal、data source、tier/layer、category、theme、ROI filter 和 sync revision；Home、Galaxy、Timeline、Inspector、ROI Dashboard 读取同一 focus target。
- Inspector：Stage 6.2 起默认显示人类可读解释、记忆权重公式、ROI leverage 公式、共享焦点公式、参数和脱敏证据摘要；agent 结构化字段和低敏数据库摘要只在手动开启 Debug / Agent Inspector 后显示。

Writeback：

- 前端允许生成长期记忆写回 proposal，但不能直接修改 active memory。
- Stage 6.2 起写回区提供 proposal JSON preview 和 safety strip；前端状态必须保持 `direct_frontend_mutation_of_active_memory=false`、`requires_conflict_check=true`、`requires_agent_or_human_apply=true`。
- proposal 必须包含 diff、版本链、parent proposal id、导出历史、rollback proposal。
- 真正 apply 必须由 agent/human 重新读库、冲突检查、写 history、git commit。

模型参数：

- 每个项目都要维护模型参数文件。
- “模型”是模型假设、处理、方法、策略、输入、输出、迭代。
- “参数”是公式、函数、阈值、门槛、数值。
- 功能清单和开发记录不能冒充模型参数。

## 4. 验收标准

必须通过：

- `python3 scripts/audit_memory_atlas_visual_acceptance.py`
- `python3 scripts/audit_memory_atlas_release.py --publish-dir apps/memory-atlas/dist`
- `python3 scripts/audit_memory_atlas_acceptance.py --publish-dir apps/memory-atlas/dist`
- `python3 scripts/preflight_cloudflare_pages_access.py --publish-dir apps/memory-atlas/dist`
- `npm run build --prefix apps/memory-atlas`
- `npm run validate:shared-state --prefix apps/memory-atlas`
- `npm run validate:inspector-proposal --prefix apps/memory-atlas`
- 关键浏览器 smoke：页面可打开、导航可切换、Timeline 动态控件可见、Obsidian/summary 不空白。

安全验收：

- GitHub 不提交 raw exports、明文 secrets、cookies、sessions、auth files。
- 公开 `memory_atlas.json` 只包含脱敏派生摘要，不包含本地绝对路径、record hashes、raw transcript refs、writeback conflict tokens。
- Finance/trading 等高风险 agent 只能发现 `secret_ref`，不能从 GitHub 读取明文高危 secret；真实交易/支付动作必须 fail closed 并等待用户明确授权。

视觉验收：

- Galaxy 不能退回小学生光点点云。
- Timeline 不能退回 table/list/static scatter。
- Contribution Grid 不能横向溢出或失去全年全景。
- Notion/Obsidian/ROI/Timeline/Word Cloud/Summary 都要有证据承载的视觉形态。

## 5. 历史过程记录

- 2026-06-15：建立 OpenAI-export ingest、记忆蒸馏、周/月复盘、人类版输出、GitHub 备份方向。
- 2026-06-17：确定 Memory Atlas 作为统一可视化平台，优先级 Galaxy > Notion > ROI > Obsidian，同时需要 Timeline 和 Contribution Grid。
- 2026-06-18：补多数据源架构，首页数据源为 总数据源 / ChatGPT / Codex；新增 Codex 本地数据红线：真实脱敏摘要，不上传 raw transcript。
- 2026-06-18：重做 Obsidian Graph、贡献网格、Galaxy 局部邻域、运行缓存释放、本地 app icon 与 Downloads/Applications app 入口。
- 2026-06-19：本轮重点修复 Timeline 动态交互、writeback proposal 版本控制/rollback、模型参数文档边界、交付历史记录。
- 2026-06-19：修复 `.app` 每次打开刷新最新快照时依赖 Documents 仓库权限的问题；installer 现在同步 Application Support source workspace，launcher 每次从该运行副本刷新数据并写入 runtime。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 2.1 默认首页集成计划；当前生产入口仍为 Galaxy，实际切换到 `记忆总览` 延后到 Stage 3.1 实施和浏览器验收。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 2.2 Galaxy 替换计划；当前生产 Galaxy 未替换，新旧 renderer feature flag、回滚路径、截图/FPS/隐私验收进入后续 Stage 4 实施。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 2.3 Timeline 替换计划；当前生产 Timeline 未替换，新旧 renderer feature flag、UTC 时间尺度、brush、hover、Inspector 同步和 reduced motion 验收进入后续 Stage 5 实施。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 2 整体复审；复审确认本阶段只新增计划和记录文件，未替换生产路由、Galaxy、Timeline 或写回行为。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 5.3 Evidence Layers；Memory River 增加黑洞生命周期、机会生命周期和冷却/废弃 fade layer。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 5 整体复审；复审确认 5.1 River Rendering、5.2 River Interaction、5.3 Evidence Layers 均通过，Stage 5 整阶段复审通过，仍未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 6.1 Shared State Store；新增 typed shared-state reducer、selection/filter/time range/focus schema、single-dispatch loop guard、`validate:shared-state` 和 `stage6_1_shared_state_store_ready` visual acceptance 钩子；Home、Galaxy、Timeline、Inspector、ROI Dashboard 共享同一 focus target；Stage 6.2 Inspector/Proposal、Stage 6 整体复审、GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 6.2 Inspector and Proposal；Inspector 默认解释面板显示公式、参数、脱敏证据和人类可读解释；Debug / Agent Inspector 默认关闭；写回区只生成 proposal JSON preview 和本地版本提案，仍不直接修改 active memory；Stage 6 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 6 整体复审；复审确认 6.1 Shared State Store 与 6.2 Inspector/Proposal 均通过，Stage 6 整阶段复审通过，仍未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆，GitHub main 上传需在最终远端检查后执行。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 7.1 Visual Acceptance；新增真实浏览器 `validate:stage7-visual`，自动启动 Vite preview、截图 Galaxy 和 Memory River、验证 Galaxy WebGL 非空像素信号、验证 Memory River 河道/证据层/marker 质量，并确认 4177 关闭后无残留；Stage 7.2 Performance Acceptance、Stage 7.3 Privacy and Accessibility、Stage 7 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 7.2 Performance Acceptance；Galaxy WebGL signal 新增 FPS、frame time、quality threshold、adaptive quality decision 和 cleanup lifecycle；Analysis 模式新增 FPS overlay 和 Auto quality toggle；新增 `validate:stage7-performance`，真实浏览器验证 high quality `>=45 FPS`、mid quality `>=30 FPS`、low quality 不空白、Auto 可恢复、unmount 后 RAF/WebGL 资源释放并确认 4177 无残留；Stage 7.3 Privacy and Accessibility、Stage 7 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 7.3 Privacy and Accessibility；Timeline feedback 增加 reduced motion、伪触感、音频和 silent-by-default DOM contract；新增 `validate:stage7-privacy-accessibility`，扫描发布产物隐私边界、确认 `memory_atlas.json` 为 public redacted read-only visualization、确认默认无 sourcemap、浏览器 emulation 验证 reduced motion 自动启用并禁用播放、验证伪触感/音频默认关闭且 marker 点击不调用 vibration 或 AudioContext；Stage 7 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 7 整体复审；复审确认 7.1 Visual Acceptance、7.2 Performance Acceptance、7.3 Privacy and Accessibility 均通过，新增 `validate:stage7` 保持 phase review、package validators、visual hooks、模型参数、changelog 和交付记录一致；Stage 7 整阶段复审通过，下一阶段为 Stage 8: 打包、部署、回滚；仍未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆，GitHub main 上传需在最终远端检查后执行。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 8.1 Local App Packaging；新增 `validate:stage8-local-app`，真实 production build、临时 app bundle、launcher 单窗口合同和默认 `记忆总览` 路由均通过；installer 增加无 Pillow `.icns` fallback、npm/pnpm fallback、pnpm dependency readiness、Codex runtime PATH 注入和 managed pid cleanup；已重装 `~/Downloads/Memory Atlas.app` 与 `/Applications/Memory Atlas.app`，Application Support runtime manifest 匹配当前 git HEAD；Stage 8.2 Release Safety、Cloudflare live deploy、Access policy change、direct writeback 仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 8.2 Release Safety；新增 `validate:stage8-release-safety`，真实 production build、release audit、overall acceptance audit、source-contract check、真实浏览器 URL rollback、in-app toggle restore、localStorage persistence、screenshot、console/network、文档一致性和 4177 cleanup 均通过；Galaxy 默认 `memory-starfield`、Timeline 默认 `memory-river`，均保留 `legacy` 回滚；Stage 8 整体复审、Cloudflare live deploy、Access policy change、GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 8 整体复审；复审确认 8.1 Local App Packaging 与 8.2 Release Safety 均通过，新增 `validate:stage8` 统一复跑本地 App 打包、release safety、offline Cloudflare Pages + Access preflight、文档一致性和 4177 cleanup；Stage 8 整阶段复审通过，下一阶段为 Stage 9 后续增强迭代；仍未部署 Cloudflare、未修改 Access policy、未读取 raw/private 数据、未直接写回长期记忆；GitHub main 上传需在最终 fast-forward 远端检查后执行。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 9.1 Obsidian Graph E Iteration；Obsidian Graph 新增 bounded local graph budget、selected/hover/local-neighbor/zoom-priority/hub 标签规则和 Galaxy cluster shared-focus 同步；新增 `validate:stage9-obsidian`，真实浏览器验证默认标签密度、局部图预算、Galaxy cluster 同步、截图、console/network 和 4177 cleanup；Stage 9.2 Visual Semantics Enrichment、Stage 9 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 9.2 Visual Semantics Enrichment；首页新增 Memory Weather v2 稳定性/动量/风险/机会/置信度信号，Galaxy Analysis Mode 新增 Memory Terrain v2 语义角色、覆盖率和 ROI Capability Gradient，Memory River 新增 ROI/capability gradient overlay；新增 `validate:stage9-visual-semantics`，真实浏览器验证 Home/Galaxy/Timeline 三面、console/network 和 4177 cleanup；Stage 9 整体复审和 GitHub main 上传仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 9 整体复审；复审确认 9.1 Obsidian Graph E Iteration 与 9.2 Visual Semantics Enrichment 均通过，新增 `validate:stage9` 统一复跑 Stage 9 两个 phase validator、visual acceptance、release audit、overall acceptance、文档一致性和 4177 cleanup；Stage 9 整阶段复审通过，下一阶段为整项目复审；仍未部署 Cloudflare、未修改 Access policy、未读取 raw/private 数据、未直接写回长期记忆；GitHub main 上传需在整项目复审通过并完成 final fast-forward 远端检查后执行。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 1 复审；本轮只覆盖 Phase 0.1 / 0.2 / 0.3，确认 scope/naming freeze、Memory Overview/Starfield/River/Universe State 合同、Phase 0.3 scaffold continuity、fixture safety 和 production isolation；新增 `validate:part1-stage0`，并补充两个 spike README 的 Phase 0.3 scaffold continuity 说明；未进入 Part 2、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 2 复审；本轮只覆盖 Phase 1.1 / 1.2 / 1.3，确认 Memory Starfield Spike、Memory River Spike、Universe State Generator Spike、fixture safety、Universe State schema/sample、parameter drift gate、production isolation 和 build；新增 `validate:part2-stage1`；未进入 Part 3、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 3 复审；本轮只覆盖 Phase 2.1 / 2.2 / 2.3，确认 Default Home Integration Plan、Galaxy Replacement Plan、Timeline Replacement Plan、Stage 2 historical runtime note、当前 later-stage runtime markers、production experiment isolation、build、visual acceptance 和 overall acceptance；新增 `validate:part3-stage2`；未进入 Part 4、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 4 复审；本轮覆盖 Stage 3.1 / 3.2 / Stage 3 overall，确认默认 `记忆总览`、Home Information Architecture、Universe State 状态卡、proposal-only next actions、Mini Starfield、River Pulse、Inspector Deep Link、focus-preserving navigation、visual acceptance hooks、production experiment isolation、build、visual acceptance 和 overall acceptance；新增 `validate:part4-stage3`；未进入 Part 5、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 5 复审；本轮覆盖 Stage 4.1 / 4.2 / 4.3 / Stage 4 overall，确认 `memory-starfield` 默认 Galaxy renderer、legacy rollback、Flow Field trajectories、quality fallback、parameter-backed mass/particle/terrain mapping、hover preview、capped click focus、Freeze/Resume Flow、Presentation/Analysis mode、visual acceptance hooks、production experiment isolation、Starfield mapping/interaction validators、build、visual acceptance 和 overall acceptance；新增 `validate:part5-stage4`，并修正 `validate_memory_starfield_mapping.mjs` 对当前 `Memory Terrain v2 analysis panel` runtime marker 的检查；未进入 Part 6、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 6 复审；本轮覆盖 Stage 5.1 / 5.2 / 5.3 / Stage 5 overall，确认 `memory-river` 默认 Timeline renderer、legacy rollback、UTC time scale、Macro/Meso/Micro river lanes、Pan/Brush interaction、selected-range sync、redacted event cards、safe feedback defaults、black-hole lifecycle、proto-star lifecycle、stale/deprecated evidence layers、visual acceptance hooks、production experiment isolation、Memory River validators、build、release audit、visual acceptance 和 overall acceptance；新增 `validate:part6-stage5`，并修正 `validate_memory_river_interaction.mjs` 对当前 `TimelineTimeRangeSelection = SharedTimelineTimeRangeSelection` 类型别名的检查；未进入 Part 7、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 7 复审；本轮覆盖 Stage 6.1 / 6.2 / Stage 6 overall，确认 shared selection/filter/time-range/focus reducer、cross-view shared focus、filter clearing、loop guard、Inspector explanation panel、proposal-only JSON、Debug separation、visual acceptance hooks、production experiment isolation、Stage 6 validators、build、release audit、visual acceptance 和 overall acceptance；新增 `validate:part7-stage6`；未进入 Part 8、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 8 复审；本轮覆盖 Stage 7.1 / 7.2 / 7.3 / Stage 7 overall，确认真实浏览器视觉截图、Galaxy pixel signal、Memory River 结构、FPS overlay、high/mid FPS thresholds、low-quality non-blank fallback、adaptive quality、cleanup lifecycle、release artifact privacy scan、reduced motion、silent feedback defaults、Stage 7 validators、build、release audit、visual acceptance 和 overall acceptance；新增 `validate:part8-stage7`，并修正 Stage 7.1 / 7.2 / 7.3 模型参数中仍写着 `Stage 7 整体复审未完成` 的旧状态；未进入 Part 9、未进入 Stage 8 复审、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 9 复审；本轮覆盖 Stage 8.1 / 8.2 / Stage 8 overall，确认 local app packaging、release safety、Stage 8 整体复审、renderer rollback、offline Cloudflare preflight、production experiment isolation、Stage 8 validators 和 local app acceptance；新增 `validate:part9-stage8`，重装 `~/Downloads/Memory Atlas.app` 与 `/Applications/Memory Atlas.app`，修复 `/Applications/Memory Atlas.app` 缺失和 runtime manifest 指向旧 commit 的漂移，并把 Stage 8.1 模型参数中的硬编码 runtime commit 改为实时 audit contract；未进入 Part 10、未进入 Stage 9 复审、未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 Part 10 复审；本轮覆盖 Stage 9.1 / 9.2 / Stage 9 overall，确认 Obsidian bounded local graph、label rules、Galaxy shared-focus sync、Memory Weather v2、Memory Terrain v2、Galaxy ROI gradient、Memory River ROI/capability gradient、Stage 9 validators、visual acceptance、release audit 和 overall acceptance；新增 `validate:part10-stage9`，并修正 Stage 9 记录中“Stage 9 后直接 GitHub main 上传”的边界，明确下一阶段必须先整项目复审，通过后再做 final remote checks 和 GitHub main 上传；未执行整项目复审、未上传 GitHub main、未部署 Cloudflare、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-07-01：完成 Memory Atlas v1.1.5 整项目复审；本轮在 Part 1-10 全部复审通过后新增 `validate:whole-project`，统一复跑 Part 1-10 validators、production build、OpenAIDatabase unittest discover、visual acceptance、release audit、overall acceptance、offline Cloudflare preflight、roadmap v2 final acceptance coverage、diff-driven governance sync、canonical remote/upload boundary 和 4177 cleanup；复审发现本地 app runtime 必须在本 commit 后刷新并用 `--require-local-apps` 复验，GitHub main 上传仍需 final remote ancestry、clean tree 和 push target 检查；未上传 GitHub main、未部署 Cloudflare、未修改 Access policy、未读取 raw/private 数据、未直接写回长期记忆。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 3.1 默认首页实现；`记忆总览` 成为启动板块，左侧导航保留，首页显示 Memory Weather、Universe State 状态卡、Black Hole / Proto-Star 信号和 proposal-only 行动建议；Galaxy 与 Timeline 仍未替换。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 3.2 首页预览组件；首页新增轻量 `Mini Starfield`、近期主题变化 `River Pulse` 和 `Inspector Deep Link`，点击前同步当前焦点再进入 Galaxy、Timeline 或详情检索；Stage 3 整体复审通过，仍未替换 Galaxy/Timeline、未直接写回长期记忆、未读取 raw/private 数据。
- 2026-06-30：完成 Memory Atlas v1.1.5 Stage 4.1 Galaxy Rendering Integration；`memory-starfield` 成为 Galaxy 默认生产 renderer，`legacy` 可通过 feature flag 回滚；生产 Galaxy 增加 Flow Field 动态、轨迹线、语义信号标记、quality selector 和低质量 fallback，仍未进入 Stage 4.2 数据映射或 Stage 4.3 交互扩展。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 4.2 Data Mapping；生产 Galaxy 的 cluster mass、粒子大小/亮度/颜色、轨迹强度和 Memory Terrain 映射改为读取 `config/visualization/model_parameters.memory_starfield.yaml`；Presentation 保持轻提示，Analysis panel 可解释 ridge、shoreline、valley、basin、fault-line 地形；仍未进入 Stage 4.3 交互扩展、Timeline 替换、写回或 Cloudflare 部署。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 4.3 Starfield Interaction；生产 Galaxy 保留 hover preview 和 capped click focus，新增 Freeze / Resume Flow，新增 Presentation / Analysis mode selector；Analysis 显示公式摘要、terrain legend 和当前 Inspector 上下文；Stage 5 Timeline 替换、写回、Cloudflare 部署和 raw/private data 仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 4 整体复审；复审确认 visual roadmap `记忆星系生产集成` 的 4.1/4.2/4.3 均通过，本地 contract、build、visual acceptance、release acceptance、preview HTTP 和 4177 清理通过；随后用 Chrome CDP 隔离 profile 补齐桌面/移动 WebGL screenshot、canvas-pixel 和 FPS 证据，并修复 390px 移动端 Galaxy 横向溢出与首屏画布露出不足问题。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 5.1 Memory River Rendering；生产 Timeline 默认进入 `memory-river` renderer，保留 `legacy` 回滚；新增 UTC 日期尺度、Macro/Meso/Micro 河道、主题/项目/分类 lane、black-hole/proto-star/event markers、Stage 5.1 validator、visual acceptance 钩子和 Memory River 参数文件更新；Stage 5.2 brush、hover/click event card、多模态反馈仍未进入。
- 2026-07-01：完成 Memory Atlas v1.1.5 Stage 5.2 Memory River Interaction；新增 Pan/Brush 模式、pointer pan、UTC brush range selection、range overlay、Interaction Lens/Home/Galaxy range sync、hover/click redacted event card、click lock + Inspector sync、Reduced Motion / optional pseudo-haptic / optional audio 安全反馈设置，并新增 Stage 5.2 validator 和 visual acceptance 钩子；Stage 5.3 evidence layers、Stage 5 整体复审和 GitHub main 上传仍未进入。

近期提交参考：

- `3e50dd2` / `8e25c80` / `12d7a70`：Contribution Grid 趋势渐变与布局优化。
- `f1ec3f9`：Obsidian Graph 重做。
- `ef23323`：Memory Atlas runtime cleanup and visual density。
- 本轮后续提交：Timeline 动态交互、writeback rollback、模型参数/交付记录、Application Support source workspace 启动刷新。

## 6. 待开发清单

高优先级：

- Stage 9.2 Visual Semantics Enrichment：Memory Terrain v2、Memory Weather v2、ROI Visual Gradient。
- Timeline 后续增强多阶段聚类摘要、相邻时间段差异解释，以及 evidence layer 碰撞规避和阈值校准。
- Writeback 增加 agent apply CLI：读取 proposal、冲突检测、写 history、更新 active memory、生成 git rollback commit。
- Summary & Iteration 增加更强人类版输出：ROI 建议、能力成长建议、机会地图、下周行动建议。
- Galaxy 增强天体语义：核心画像为核心星系，项目为旋臂，决策为高亮事件，临时信息为外层低亮星云。

中优先级：

- 数据导图重做为成熟框架导图形态，突出数据来源、画像偏好、项目决策和行动机会。
- ROI Dashboard 加入执行收益、时间投入、机会窗口等真实数据后再升级模型。
- Codex 行为分析加入完成事项、commit、测试通过、报告生成等“有效产出”指标。

低优先级：

- Tauri 桌面封装。
- 多用户/权限模型。
- 远程 MCP search/fetch 只读服务。

## 7. Agent 接手顺序

新 agent 接手时按以下顺序读取：

1. `docs/USER_REQUIREMENTS.md`
2. `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
3. `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
4. `docs/MEMORY_ATLAS_COMPETITOR_ARCHITECTURE_MATRIX.md`
5. `README.md`
6. `scripts/audit_memory_atlas_visual_acceptance.py`
7. `scripts/audit_memory_atlas_acceptance.py`
8. `apps/memory-atlas/src/App.tsx`
9. `apps/memory-atlas/src/components/GalaxyScene.tsx`
10. `apps/memory-atlas/src/components/ObsidianGraphScene.tsx`

停止条件：

- 任何安全审计失败。
- 任何发布目录包含 raw export、secret、cookie/session/auth。
- Timeline/Contribution/Galaxy 等关键视觉板块退化为静态列表或空白画布。
- 本地 app runtime manifest 与当前 git HEAD 不一致。

## 8. Memory Atlas v1.1.6 修补包记录

### Stage 0 Phase 0.1：Encoding & Text Audit

状态：`phase_0_1_contract_created`。

本 phase 是 v1.1.6 修补包的第一轮，只建立中文编码与文本可读性合同，不替换 UI、不修 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/chinese_ui_quality_contract.md`
- `docs/acceptance/chinese_text_audit.md`

本 phase 解决的缺口：

- 乱码与 mojibake 缺少阻断验收。
- 中文主标签、按钮、卡片、Inspector 标签缺少统一规范。
- 表格、按钮、卡片承载长句导致不可读的风险缺少合同约束。
- proposal-only 行为需要在用户界面明确说明“不直接写入长期记忆”。
- 低宽度视口的中文溢出、重叠和横向撑破需要进入验收清单。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 0 Phase 0.1。
- Stage 0 Phase 0.2 `Visual Readability Baseline` 已在后续 phase 单独完成。
- Stage 1-10 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不上传 GitHub main；整 Stage 0 完成、复审并修复后再进入上传流程。

下一步：

- Stage 0 两个 phase 均完成后进行 Stage 0 整体复审，修复复审发现的问题，再准备 GitHub main 上传。

### Stage 0 Phase 0.2：Visual Readability Baseline

状态：`phase_0_2_contract_created_stage_0_review_passed_pending_upload`。

本 phase 是 v1.1.6 修补包的第二轮，只建立页面视觉密度基线和截图验收矩阵，不替换 UI、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/acceptance/visual_density_baseline.md`

本 phase 冻结的视觉门槛：

- 记忆总览视觉化程度 `>= 70%`。
- 记忆星系视觉化程度 `>= 90%`。
- 记忆时间河视觉化程度 `>= 85%`。
- 数据导图视觉化程度 `>= 80%`。

本 phase 解决的缺口：

- 每个板块必须有默认视觉主区，不能只有列表和卡片。
- 记忆星系不得退回普通点线图、随机粒子或普通 Obsidian Graph。
- 记忆时间河不得退回日期列表、表格或静态散点。
- 数据导图必须呈现来源、主题、资产、行动四层结构。
- 后续实现 phase 必须补桌面、平板、移动截图证据，不能只口头说明。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 0 Phase 0.2。
- Stage 0 的 Phase 0.1 / 0.2 均已本地完成，Stage 0 整体复审已通过。
- Stage 1-10 未进入。
- 不上传 GitHub main；需等 Stage 0 复审通过并解决复审暴露问题后再做上传。

复审修复：

- 复审发现 Phase 0.1 / 0.2 有静态检查和记录，但缺少固定的 Stage 0
  review artifact 与 deterministic validator。
- 已新增 `docs/reviews/memory_atlas_v1_1_6_stage0_review.md`。
- 已新增 `validate:v1.1.6-stage0`，用于固定 Phase 0.1 / 0.2 合同、记录、
  review 文档、改动范围和边界。

Stage 0 整体复审状态：`stage_0_review_passed_pending_upload`。

下一步：

- 执行 final remote checks。
- 只 staging 本轮 Stage 0 相关文件，不 staging `.DS_Store`。
- commit 后处理 `origin/main` behind 状态。
- 重新运行 `validate:v1.1.6-stage0` 和可用治理检查。
- 上传 GitHub main。

### Stage 1 Phase 1：Memory Overview Usage Contract

Stage 1 Phase 1 状态：`phase_1_1_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包进入“记忆总览与系统使用说明”的第一轮，只建立可用性合同和验收文件，不替换运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/memory_overview_usage_contract.md`
- `docs/acceptance/memory_overview_usage_acceptance.md`
- `validate:v1.1.6-stage1-phase1`

本 phase 解决的缺口：

- 记忆总览需要被明确为系统操作中枢，而不是欢迎页或普通 dashboard。
- 首页必须能解释今日状态、Memory Weather、建议动作、低价值循环、新生机会、层级资产摘要、主题分类摘要、Mini 记忆星系和记忆时间河脉冲。
- 系统使用说明必须告诉用户如何从总览进入 Inspector、记忆星系、记忆时间河、搜索、复盘、总结与迭代。
- Presentation / Analysis 模式、Inspector 和 Proposal 的边界必须可被用户理解。
- proposal-only 必须保持为前端调整边界，不直接写长期记忆。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 1。
- Stage 1 整体复审未执行。
- Stage 2-5 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- Stage 1 Phase 2 已承接建议动作明细合同；后续继续补层级资产模型和主题分类模型。
- Stage 1 所有 phase 完成后进行 Stage 1 整体复审，修复复审发现的问题。

### Stage 1 Phase 2：Suggested Action Detail Contract

Stage 1 Phase 2 状态：`phase_1_2_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的建议动作明细合同轮次，只定义建议动作展开后的字段、解释、排序、Inspector 交接和 proposal-only 边界，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/suggested_action_detail_contract.md`
- `docs/acceptance/suggested_action_detail_acceptance.md`
- `validate:v1.1.6-stage1-phase2`

本 phase 解决的缺口：

- 建议动作不能只有短句列表，必须能展开为可判断、可追溯、可调整的行动解释。
- 每条建议动作必须包含 reason、ROI、effort cost、urgency、confidence、evidence、next step、proposal hint 和 rollback hint。
- `continue`、`review`、`consolidate`、`explore`、`defer` 五类动作必须有明确语义。
- 点击建议动作进入 Inspector 时必须能解释原因、证据、ROI、努力成本、紧急度和下一步。
- 建议动作只能引导 proposal-only 调整，不得直接写 active memory 或长期记忆。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 2。
- 层级资产和主题分类完整模型未进入。
- Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- Stage 1 Phase 3 已承接层级资产明细模型合同；后续继续补主题分类模型。
- Stage 1 所有 phase 完成后进行 Stage 1 整体复审，修复复审发现的问题。

### Stage 1 Phase 3：Tier Asset Detail Contract

Stage 1 Phase 3 状态：`phase_1_3_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的层级资产明细合同轮次，只定义层级资产展开后的资产层级、字段、排序、Inspector 交接和 proposal-only 边界，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/tier_asset_detail_contract.md`
- `docs/acceptance/tier_asset_detail_acceptance.md`
- `validate:v1.1.6-stage1-phase3`

本 phase 解决的缺口：

- 层级资产不能只有摘要，必须能展开为可判断、可追溯、可调整的结构化资产。
- 层级资产必须覆盖 core_profile、project、decision、workflow、knowledge、opportunity、stale 七类。
- 每个资产必须包含 asset_id、asset_tier、summary、importance、priority、confidence、staleness_status、evidence、linked actions、recommended asset action、proposal hint 和 rollback hint。
- 点击层级资产进入 Inspector 时必须能解释重要性、优先级、置信度、有效性、证据和下一步。
- 层级资产只能引导 proposal-only 调整，不得直接写 active memory 或长期记忆。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 3。
- 主题分类完整模型未进入。
- Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- Stage 1 Phase 4 已承接主题分类明细模型合同；后续继续补 proposal-only 调整入口合同或进入 Stage 1 复审前检查。
- Stage 1 所有 phase 完成后进行 Stage 1 整体复审，修复复审发现的问题。

### Stage 1 Phase 4：Topic Classification Detail Contract

Stage 1 Phase 4 状态：`phase_1_4_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的主题分类明细合同轮次，只定义主题状态、字段、趋势、证据、关联板块、Inspector 交接和 proposal-only 边界，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/topic_classification_detail_contract.md`
- `docs/acceptance/topic_classification_detail_acceptance.md`
- `validate:v1.1.6-stage1-phase4`

本 phase 解决的缺口：

- 主题分类不能只是 tag 列表，必须能展开为可解释、可追溯、可调整的语义聚合。
- 主题分类必须覆盖 dominant、rising、declining、emerging、conflict、black_hole、stale 七类主题状态。
- 每个主题必须包含 topic_strength、trend、confidence、record_count、evidence_count、linked assets、linked actions、matched reason、recommended topic action、proposal hint 和 rollback hint。
- 点击主题分类进入 Inspector 时必须能解释强度、趋势、置信度、记录数、证据和跨板块链接。
- 主题分类只能引导 proposal-only 调整，不得直接写 active memory 或长期记忆。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 4。
- Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- 继续 Stage 1 的下一个 phase，补 proposal-only 调整入口合同或做 Stage 1 复审前收敛检查。
- Stage 1 所有 phase 完成后进行 Stage 1 整体复审，修复复审发现的问题。

### Stage 1 Phase 5：Proposal-only Adjustment Entry Contract

Stage 1 Phase 5 状态：`phase_1_5_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的 proposal-only 调整入口合同轮次，只定义从记忆总览、建议动作明细、层级资产明细、主题分类明细和 Inspector 进入 proposal draft 的安全入口，不实现完整 proposal 编辑工作区、不实现 agent apply、不修改运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/proposal_only_adjustment_entry_contract.md`
- `docs/acceptance/proposal_only_adjustment_entry_acceptance.md`
- `validate:v1.1.6-stage1-phase5`

本 phase 解决的缺口：

- 用户看懂明细后需要能提出 importance、priority、topic_category、action_status、due_window、hidden_until、stale_override 或 confidence_note 调整。
- 调整入口必须说明 proposal draft 不会直接写 active memory。
- 每个 proposal draft 必须包含 proposal_id、parent_snapshot_id、entry_surface、target_type、target_id、field、old_value_ref、proposed_value、reason、evidence_refs、created_at、requires_conflict_check、requires_agent_or_human_apply 和 rollback_hint。
- 调整入口必须覆盖 memory_overview、suggested_action_detail、tier_asset_detail、topic_classification_detail 和 Inspector。
- 后续 apply 必须由 agent/human 在前端之外做冲突检查、history、版本链和 rollback。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 1 Phase 5 的 proposal-only 调整入口合同。
- 完整 Proposal 编辑工作区、agent apply、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- Stage 1 phase 已本地完成，下一轮必须执行 Stage 1 整体复审并修复复审发现的问题。
- Stage 1 整体复审未执行前，不进入 Stage 2，不上传 GitHub main。

### Stage 1 整体复审

Stage 1 整体复审状态：`stage_1_review_passed_pending_stage2`。

本复审覆盖 v1.1.6 Stage 1 Phase 1-5，只确认合同、验收、validator、记录、review artifact 和进入 Stage 2 前边界一致，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage1_review.md`
- `validate:v1.1.6-stage1`

复审发现的问题：

- Phase 1.1-1.5 已有合同、验收和 phase validator，但缺少 Stage 1 整体 review artifact 和 deterministic stage-level validator。

修复：

- 新增 Stage 1 review artifact。
- 新增 `validate:v1.1.6-stage1`。
- 更新 delivery、model、feature、development、model parameter 和 changelog 记录，标记 Stage 1 复审通过并等待 Stage 2。

验收边界：

- Stage 1 复审通过不表示 runtime UI、浏览器截图、完整 Proposal 编辑工作区、agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 2.0 已完成。
- Stage 2-5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

下一步：

- 进入 Stage 2 的第一个 bounded run。
- 若 Stage 1 文件后续变化，必须重新运行 `validate:v1.1.6-stage1`。

### Stage 2 Phase 1：Detail Visibility Workbench Contract

Stage 2 Phase 1 状态：`phase_2_1_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包进入“明细可见性工作台”的第一轮，只定义建议动作、层级资产和主题分类三类明细的统一工作台 IA、展开、筛选、排序、Inspector 交接和 proposal-only 入口提示，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/detail_visibility_workbench_contract.md`
- `docs/acceptance/detail_visibility_workbench_acceptance.md`
- `validate:v1.1.6-stage2-phase1`

本 phase 解决的缺口：

- Stage 1 已定义明细字段，但缺少统一工作台来承载三类明细。
- 工作台必须包含 suggested_action_lane、tier_asset_lane 和 topic_classification_lane。
- 每条明细必须支持 collapsed summary、expanded detail、open_inspector、jump_to_related 和 proposal_only_entry。
- 工作台必须定义 source_scope、confidence、evidence_count、proposal_hint、urgency、effort_cost、action_type、asset_tier、importance、priority、staleness_status、topic_state、trend 和 clear_filters。
- 空态、加载态、错误态必须明确，不允许用 mock 数据伪造明细。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 2 Phase 1 的明细可见性工作台合同。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 Proposal 编辑工作区和 agent apply 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

下一步：

- 继续 Stage 2 的下一个 phase，补建议动作 lane 具体可见性合同或实现隔离原型。
- Stage 2 整体复审未执行前，不进入 Stage 3，不上传 GitHub main。

### Stage 2 Phase 2：Suggested Action Lane Visibility Contract

Stage 2 Phase 2 状态：`phase_2_2_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的 suggested_action_lane 具体可见性合同轮次，只定义建议动作 lane 的扫描行、决策行、证据抽屉、分组排序、状态 badge、展开比较、Inspector 交接和 proposal-only 调整边界，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/suggested_action_lane_visibility_contract.md`
- `docs/acceptance/suggested_action_lane_visibility_acceptance.md`
- `validate:v1.1.6-stage2-phase2`

本 phase 解决的缺口：

- 建议动作不能只作为首页摘要，必须在工作台里可扫描、可比较、可展开证据。
- 每个建议动作必须包含 action_id、title、action_type、reason、roi_score、effort_cost、urgency、confidence、evidence_count、evidence_refs、source_scope、linked_theme_ids、linked_asset_ids、next_step、recommended_time_window、proposal_hint 和 rollback_hint。
- suggested_action_lane 必须支持 now、this_week、later、watch 分组，以及 ROI、urgency、effort、confidence、evidence_count 排序。
- suggested_action_lane 必须支持 expand action、compare actions、pin action、mark reviewed 和 clear temporary state。
- 点击建议动作进入 Inspector 时必须带 source_lane = suggested_action_lane、target_type = suggested_action 和证据/下一步/proposal hint 交接字段。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 2 Phase 2 的 suggested_action_lane 可见性合同。
- tier_asset_lane、topic_classification_lane、Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 Proposal 编辑工作区和 agent apply 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。
- Stage 2 整体复审未执行。

下一步：

- 继续 Stage 2 的下一个 phase，补 tier_asset_lane 具体可见性合同。
- Stage 2 整体复审未执行前，不进入 Stage 3，不上传 GitHub main。

### Stage 2 Phase 3：Tier Asset Lane Visibility Contract

Stage 2 Phase 3 状态：`phase_2_3_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的 tier_asset_lane 具体可见性合同轮次，只定义层级资产 lane 的资产扫描行、决策行、证据抽屉、七类资产分组、排序、状态 badge、展开比较、Inspector 交接和 proposal-only 调整边界，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/tier_asset_lane_visibility_contract.md`
- `docs/acceptance/tier_asset_lane_visibility_acceptance.md`
- `validate:v1.1.6-stage2-phase3`

本 phase 解决的缺口：

- 层级资产不能只作为首页摘要或原始记忆列表，必须在工作台里可扫描、可比较、可展开证据。
- 每个层级资产必须包含 asset_id、asset_tier、title、summary、importance、priority、confidence、staleness_status、evidence_count、evidence_refs、source_scope、linked_action_ids、linked_theme_ids、linked_time_range、recommended_asset_action、proposal_hint 和 rollback_hint。
- tier_asset_lane 必须支持 core_profile、project、decision、workflow、knowledge、opportunity、stale 七类资产分组，以及 importance、priority、staleness_status、confidence、evidence_count 排序。
- tier_asset_lane 必须支持 expand asset、compare assets、pin asset、mark reviewed、jump to linked action 和 clear temporary state。
- 点击层级资产进入 Inspector 时必须带 source_lane = tier_asset_lane、target_type = tier_asset 和证据/关联/下一步/proposal hint 交接字段。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 2 Phase 3 的 tier_asset_lane 可见性合同。
- topic_classification_lane、Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 Proposal 编辑工作区和 agent apply 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。
- Stage 2 整体复审未执行。

下一步：

- 继续 Stage 2 的下一个 phase，补 topic_classification_lane 具体可见性合同。
- Stage 2 整体复审未执行前，不进入 Stage 3，不上传 GitHub main。

### Stage 2 Phase 4：Topic Classification Lane Visibility Contract

Stage 2 Phase 4 状态：`phase_2_4_contract_created_pending_stage_review`。

本 phase 是 v1.1.6 修补包的 topic_classification_lane 具体可见性合同轮次，只定义主题分类 lane 的主题扫描行、决策行、证据抽屉、七类主题状态分组、排序、状态 badge、展开比较、Inspector 交接和 proposal-only 调整边界，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆。

新增产物：

- `docs/product/topic_classification_lane_visibility_contract.md`
- `docs/acceptance/topic_classification_lane_visibility_acceptance.md`
- `validate:v1.1.6-stage2-phase4`

本 phase 解决的缺口：

- 主题分类不能只是 tag 列表，必须在工作台里可扫描、可比较、可展开证据。
- 每个主题分类必须包含 topic_id、topic_label、topic_state、topic_strength、trend、confidence、record_count、evidence_count、evidence_refs、source_scope、linked_asset_ids、linked_action_ids、linked_starfield_cluster_id、linked_river_range、related_topic_ids、matched_reason、recommended_topic_action、proposal_hint 和 rollback_hint。
- topic_classification_lane 必须支持 dominant、rising、emerging、conflict、black_hole、declining、stale 七类主题状态分组，以及 topic_strength、trend、confidence、record_count、evidence_count 排序。
- topic_classification_lane 必须支持 expand topic、compare topics、pin topic、mark reviewed、jump to linked asset、jump to linked action、jump to starfield、jump to river 和 clear temporary state。
- 点击主题分类进入 Inspector 时必须带 source_lane = topic_classification_lane、target_type = topic_classification 和证据/关联/下一步/proposal hint 交接字段。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 2 Phase 4 的 topic_classification_lane 可见性合同。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 Proposal 编辑工作区和 agent apply 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。
- Stage 2 整体复审未执行。

下一步：

- 继续 Stage 2 整体复审，补 review artifact 和 stage-level validator，并修复复审暴露的问题。
- Stage 2 整体复审未执行前，不进入 Stage 3，不上传 GitHub main。

### Stage 2 整体复审

Stage 2 整体复审状态：`stage_2_review_passed_pending_stage3`。

本复审覆盖 v1.1.6 Stage 2 Phase 1-4，只确认合同、验收、validator、记录、review artifact 和进入 Stage 3 前边界一致，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage2_review.md`
- `validate:v1.1.6-stage2`

复审发现的问题：

- Phase 2.1-2.4 已有合同、验收和 phase validator，但缺少 Stage 2 整体 review artifact 和 deterministic stage-level validator。

修复：

- 新增 Stage 2 review artifact。
- 新增 `validate:v1.1.6-stage2`。
- 更新 delivery、model、feature、development、model parameter 和 changelog 记录，标记 Stage 2 复审通过并等待 Stage 3。

验收边界：

- Stage 2 复审通过不表示 runtime UI、浏览器截图、完整 Proposal 编辑工作区、agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 2.0 已完成。
- Stage 3-5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

下一步：

- 进入 Stage 3 的第一个 bounded run。
- 若 Stage 2 文件后续变化，必须重新运行 `validate:v1.1.6-stage2`。

### Stage 3 Phase 1：Proposal-only Adjustment Workspace Contract

Stage 3 Phase 1 状态：`phase_3_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S3P01`。

本 phase 是 v1.1.6 修补包进入 proposal-only 调整层的第一轮，只定义 proposal-only 调整工作区的信息架构、字段、schema、状态、diff preview、安全复核、Inspector 交接和 rollback 边界，不实现运行时 UI、不修改 CSS、不启动浏览器、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply。

新增产物：

- `docs/product/proposal_only_adjustment_workspace_contract.md`
- `docs/acceptance/proposal_only_adjustment_workspace_acceptance.md`
- `validate:v1.1.6-stage3-phase1`

本 phase 解决的缺口：

- Stage 1 只定义 proposal-only 调整入口，尚未定义完整工作区。
- 用户需要在同一工作区看到 proposal_queue、target_context_panel、field_editor_panel、proposal_diff_preview、safety_review_panel 和 rollback_panel。
- 工作区必须允许 proposal-only 调整 importance、priority、topic_category、action_status、due_window、hidden_until、stale_override 和 confidence_note。
- 每个 proposal draft 必须包含 proposal_id、parent_snapshot_id、target_id、field、old_value、proposed_value、reason、created_at、rollback_hint、requires_conflict_check 和 requires_agent_or_human_apply。
- proposal 状态必须区分 draft、needs_review、ready_for_agent_apply、rejected 和 superseded。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 3 Phase 1 的 proposal-only 调整工作区合同。
- agent apply、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## v1.1.7 Pre Stage 0：Gap Remediation Upgrade Package

状态：`pre_stage_0_review_passed_pending_github_main_upload`。

任务 ID：`MA-V117-PRESTAGE0`。

验收 ID：`ACC-MA-V117-PRESTAGE0`。

本 pre-stage 固定 v1.1.7 gap remediation 升级包，只确认 Roadmap v2 gap
remediation 输入、v1.1.6 Stage 10 baseline、Stage 0-10 执行映射、验收矩阵、
review artifact、validator、记录一致性、改动范围和一次性 GitHub main 上传
gate。不实现运行时 UI、不修改 CSS/路由、不切换 feature flag、不读取
raw/private 数据、不直接写长期记忆、不写 proposal、不执行 agent apply、不
build、不截图、不安装本地 app、不部署 Cloudflare、不修改 Access policy。

新增产物：

- `docs/product/memory_atlas_v1_1_7_gap_remediation_upgrade_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_pre_stage0_acceptance.md`
- `docs/reviews/memory_atlas_v1_1_7_pre_stage0_review.md`
- `validate:v1.1.7-pre-stage0`

验收边界：

- Pre Stage 0 通过不表示 Stage 0 runtime remediation、浏览器截图、FPS、Memory
  Starfield、Memory River、Data Map 2.0、Search 2.0、Review / Summary /
  Iteration 或 Summary iteration 已完成。
- Stage 0 尚未开始。
- GitHub main 上传只允许在 `validate:v1.1.7-pre-stage0`、`git diff --check
  -- OpenAIDatabase`、clean tracked tree、fetch/integrate 和 canonical remote
  确认后一次性执行。

Machine-readable boundary summary: No production runtime feature work; No raw/private data read; No direct writeback; No GitHub main upload in review artifact.

## v1.1.7 Stage 0 Phase 0.1：Chinese Display Foundation

状态：`phase_0_1_chinese_display_foundation_completed_pending_stage0_review`。

任务 ID：`MA-V117-S0P01`。

验收 ID：`ACC-MA-V117-S0P01`。

本 phase 建立中文显示基础，包括 UTF-8/Unicode 静态扫描、中文 UI copy
registry、关键运行时文案接入、中文字体 fallback 和长中文布局容错。不做 Help
面板、不做空/错误状态工作流、不做明细可见性合同、不截图、不 build、不安装本地
app、不部署 Cloudflare、不读取 raw/private 数据、不直接写长期记忆、不写 proposal、
不执行 agent apply、不上传 GitHub main。

新增/更新产物：

- `apps/memory-atlas/src/i18n/types.ts`
- `apps/memory-atlas/src/i18n/zh-CN.ts`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_atlas_v1_1_7_stage0_phase1_chinese_display_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage0_phase1_chinese_display_acceptance.md`
- `validate:v1.1.7-stage0-phase1`

验收边界：

- Phase 0.1 通过不表示浏览器截图、Help 面板、空/错误状态工作流或 Stage 0
  整体复审已完成。
- Stage 0 Phase 0.2 和 Phase 0.3 未进入。
- Stage 0-8 全部完成前不上传 GitHub main。

Machine-readable boundary summary: No raw/private data read; No direct writeback; No proposal write; No GitHub main upload.

## v1.1.7 Stage 0 Phase 0.2：Usage Help And Empty/Error States

状态：`phase_0_2_usage_help_completed_pending_stage0_review`。

任务 ID：`MA-V117-S0P02`。

验收 ID：`ACC-MA-V117-S0P02`。

本 phase 建立系统使用说明与空错态，包括 3 分钟 Help 使用路径、Presentation /
Analysis 读法说明、Inspector / Proposal-only / Search Review 工作流说明、空快照、
筛选无结果、加载失败、WebGL 不可用和 proposal 不可写的中文解释。不做 Stage
0.3 明细字段合同、不做 Stage 1 schema、不截图、不 build、不安装本地 app、不部署
Cloudflare、不读取 raw/private 数据、不直接写长期记忆、不写 proposal、不执行 agent
apply、不上传 GitHub main。

新增/更新产物：

- `apps/memory-atlas/src/components/help/MemoryAtlasHelpPanel.tsx`
- `apps/memory-atlas/src/components/EmptyState.tsx`
- `apps/memory-atlas/src/components/ErrorState.tsx`
- `apps/memory-atlas/src/i18n/types.ts`
- `apps/memory-atlas/src/i18n/zh-CN.ts`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/GalaxyScene.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_atlas_v1_1_7_stage0_phase2_usage_help_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage0_phase2_usage_help_acceptance.md`
- `docs/product/memory_atlas_usage_guide.md`
- `validate:v1.1.7-stage0-phase2`

验收边界：

- Phase 0.2 通过不表示浏览器截图、真实 WebGL 失败模拟、Stage 0.3 明细字段
  合同、Search 2.0、Review workflow 或 Stage 0 整体复审已完成。
- Stage 0 Phase 0.3 未进入。
- Stage 0-8 全部完成前不上传 GitHub main。

Machine-readable boundary summary: No raw/private data read; No direct writeback; No proposal write; No GitHub main upload.

## v1.1.7 Stage 0 Phase 0.3：Detail Visibility Field Contract

状态：`phase_0_3_detail_visibility_contract_completed_pending_stage0_review`。

任务 ID：`MA-V117-S0P03`。

验收 ID：`ACC-MA-V117-S0P03`。

本 phase 定义明细可见性字段合同，覆盖 suggested_action_detail、
tier_asset_detail、topic_classification_detail 三类对象的必备字段、来源、
展示位置、编辑权限、proposal-only、no-direct-writeback 和 no-mock fallback 边界。
不做运行时 UI、不做 Stage 1 schema、不截图、不 build、不安装本地 app、不部署
Cloudflare、不读取 raw/private 数据、不直接写长期记忆、不写 proposal、不执行 agent
apply、不上传 GitHub main。

新增/更新产物：

- `docs/product/detail_visibility_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage0_phase3_detail_visibility_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0_phase3.cjs`
- `validate:v1.1.7-stage0-phase3`

验收边界：

- Phase 0.3 通过不表示运行时明细工作台、生成数据字段、浏览器截图、Search 2.0、
  Review workflow、Data Map 2.0 或 Stage 0 整体复审已完成。
- Stage 0 三个 phase 已本地完成，但 Stage 0 整体复审未执行。
- Stage 0-8 全部完成前不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No proposal write; No GitHub main upload.

## v1.1.7 Stage 0 Review

状态：`stage_0_review_passed_pending_stage1_no_github_main_upload`。

任务 ID：`MA-V117-S0-REVIEW`。

验收 ID：`ACC-MA-V117-S0-REVIEW`。

本 review gate 运行并固定 Stage 0 三个 phase 的验收链：

- Phase 0.1：`validate:v1.1.7-stage0-phase1`
- Phase 0.2：`validate:v1.1.7-stage0-phase2`
- Phase 0.3：`validate:v1.1.7-stage0-phase3`

新增/更新产物：

- `docs/reviews/memory_atlas_v1_1_7_stage0_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0.cjs`
- `validate:v1.1.7-stage0`

验收边界：

- Stage 0 review 通过不表示 Stage 1-8、运行时明细工作台、浏览器截图、build、
  deploy 或最终 GitHub main 上传完成。
- 下一步只能进入 Stage 1 的一个 phase。
- 整个 Stage 0-8 项目完成前不上传 GitHub main。

Machine-readable boundary summary: No Stage 1 work; No raw/private data read; No direct writeback; No proposal write; No GitHub main upload before whole Stage 0-8 completion.

## v1.1.7 Stage 1 Phase 1.1：Universe State Schema

状态：`phase_1_1_universe_state_schema_completed_pending_stage1_review`。

任务 ID：`MA-V117-S1P01`。

验收 ID：`ACC-MA-V117-S1P01`。

本 phase 把 Universe State 从早期 overview/starfield/river 共享状态，扩展为
Roadmap v2 Stage 1 的共享 schema gate。它确认同一 deterministic sample 和
schema 可被后续 `data_map_2_0`、`search_2_0`、
`review_summary_iteration`、Inspector 与 ROI 使用。

新增/更新产物：

- `docs/architecture/universe_state_snapshot.md`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/src/models/universeState.ts`
- `apps/memory-atlas/src/fixtures/universe_state.schema.json`
- `apps/memory-atlas/src/fixtures/universe_state.sample.json`
- `docs/acceptance/memory_atlas_v1_1_7_stage1_phase1_universe_state_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase1.cjs`
- `validate:v1.1.7-stage1-phase1`

验收边界：

- `recommended_next_actions` 必须保持 `proposal_only: true`。
- Universe State privacy flags 必须保持 all false。
- 本 phase 不实现 Phase 1.2 建议动作明细 UI、Phase 1.3 层级资产模型、
  Phase 1.4 主题分类模型、proposal editor、Search 2.0 UI、Review workflow、
  Data Map 2.0 production UI 或 Summary proposal export。
- 整个 Stage 0-8 项目完成前不上传 GitHub main。

Machine-readable boundary summary: data_map_2_0; search_2_0; review_summary_iteration; No Phase 1.2 work; No raw/private data read; No direct writeback; No proposal write; No GitHub main upload before whole Stage 0-8 completion.

## v1.1.7 Stage 1 Phase 1.2：Next Action Detail

状态：`phase_1_2_next_action_detail_completed_pending_stage1_review`。

任务 ID：`MA-V117-S1P02`。

验收 ID：`ACC-MA-V117-S1P02`。

本 phase 把 Home Overview 建议动作升级为可排序、可解释、可点击的 Next
Action 明细。首页显示 Top 5 action cards；点击后打开 Action Detail Drawer，
展示为什么建议、关联主题、预计收益、风险、对应证据、下一步和 proposal-only
安全提示。

新增/更新产物：

- `docs/architecture/next_action_model.md`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/ActionDetailDrawer.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/acceptance/memory_atlas_v1_1_7_stage1_phase2_next_action_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase2.cjs`
- `validate:v1.1.7-stage1-phase2`

验收边界：

- 每条 Next Action 必须包含 `title`、`reason`、`roi_score`、`effort_cost`、
  `urgency`、`source`、`evidence_refs`、`status`、`next_step` 和
  `proposal_only`。
- Action Detail Drawer 只读展示建议动作明细，不写 proposal JSON，不直接修改
  active memory。
- 本 phase 不实现 Phase 1.3 tier asset、Phase 1.4 topic classification、
  proposal editor、Search 2.0、Review workflow、Data Map 2.0、浏览器截图、
  production build、本地 app install、Cloudflare deploy 或 GitHub main 上传。
- 整个 Stage 0-8 项目完成前不上传 GitHub main。

Machine-readable boundary summary: Next Action; Action Detail Drawer; roi_score; urgency; proposal_only; No raw/private data read; No direct writeback; No proposal write; No GitHub main upload before whole Stage 0-8 completion.

## v1.1.7 Stage 1 Phase 1.3：Level Asset Detail

状态：`phase_1_3_tier_asset_detail_completed_pending_stage1_review`。

任务 ID：`MA-V117-S1P03`。

验收 ID：`ACC-MA-V117-S1P03`。

本 phase 把层级资产从数字统计升级为可排序、可解释、可点击的 Level Asset 明细。
首页显示 Level Asset cards；点击后打开 AssetDetailPanel，展示资产层级、主题、
价值、更新时间、置信度、状态、证据、关联动作/主题、建议动作和 proposal-only
安全提示。

新增/更新产物：

- `docs/architecture/level_asset_model.md`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/AssetDetailPanel.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/acceptance/memory_atlas_v1_1_7_stage1_phase3_tier_asset_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase3.cjs`
- `validate:v1.1.7-stage1-phase3`

验收边界：

- 每条 Level Asset 必须包含 `asset_tier`、theme、`value_score`、updated_at、
  importance、priority、confidence、`staleness_status`、evidence_refs、
  linked_action_ids、linked_topic_ids、recommended_asset_action 和 `proposal_only`。
- AssetDetailPanel 只读展示层级资产明细，不写 proposal JSON，不直接修改
  active memory。
- 本 phase 不实现 Phase 1.4 topic classification、proposal editor、Search 2.0、
  Review workflow、Data Map 2.0、浏览器截图、production build、本地 app install、
  Cloudflare deploy 或 GitHub main 上传。
- 整个 Stage 0-8 项目完成前不上传 GitHub main。

Machine-readable boundary summary: Level Asset; AssetDetailPanel; value_score; staleness_status; proposal_only; No raw/private data read; No direct writeback; No proposal write; No GitHub main upload before whole Stage 0-8 completion.

### Stage 8 Phase 1：Release Rollback Contract

Stage 8 Phase 1 状态：`phase_8_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S8P01`。

本 phase 是 v1.1.6 修补包进入“发布、本地 App 与回滚安全”的第一轮，只定义
`memory_atlas_release_rollback_contract` 合同、验收、validator 和治理记录一致性。
它把本地 macOS app、runtime manifest、redacted static artifact、offline
Cloudflare preflight、live deploy authorization gate、rollback matrix、
proposal-only writeback gate 和 cleanup guard 固定为后续发布实现的阻断门槛。

新增产物：

- `docs/product/memory_atlas_release_rollback_contract.md`
- `docs/acceptance/memory_atlas_release_rollback_acceptance.md`
- `validate:v1.1.6-stage8-phase1`

验收边界：

- 运行时 manifest 指向旧 commit、本地 app 服务旧数据、release artifact 包含
  raw/private/cookie/session/secret、未授权 Cloudflare deploy、未授权 Access policy
  change、缺少 Memory Starfield/Memory River rollback path、proposal-only 边界被削弱、
  临时产物无 cleanup 证据或 GitHub upload 先于 final validation，均为未来实现失败条件。
- Stage 8 Phase 1 通过不表示 production build、local app install、Cloudflare live
  deploy、Access policy change、浏览器截图或真实 release audit 已完成。
- 不实现运行时 UI，不修改 CSS，不运行 installer，不执行 production build，不部署
  Cloudflare，不修改 Access policy，不读取 raw/private 数据，不直接写长期记忆，不执行
  agent apply，不进入 Stage 8 整体复审，不进入 Stage 9-10，不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload; No live deploy.

下一步：

- 进入 Stage 8 整体复审，补 review artifact 和 stage-level validator，并解决复审暴露的问题。
- Stage 8 整体复审未执行前，不上传 GitHub main。

### Stage 8 整体复审

Stage 8 复审状态：`stage_8_review_passed_pending_github_main_upload`。

任务 ID：`MA-V116-S8-REVIEW`。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage8_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage8.cjs`
- `validate:v1.1.6-stage8`

复审结论：

- Phase 8.1 Release Rollback Contract、验收、validator 和记录一致。
- Stage 8 缺少 deterministic whole-stage validator 与 review artifact 的缺口已修复。
- Stage 8 已通过整体复审，等待 GitHub main upload gate。

复审边界：

- No runtime UI。
- No CSS change。
- No browser screenshot run。
- No production build。
- No installer run。
- No local app install or rebuild。
- No app bundle or runtime cache mutation。
- No Cloudflare live deploy。
- No Access policy change。
- No raw/private data read。
- No direct writeback。
- No GitHub main upload。

下一 gate：

- 先执行 final remote checks、`validate:v1.1.6-stage8-phase1`、
  `validate:v1.1.6-stage8`、项目级 acceptance audit 和 diff check。
- 再上传 canonical GitHub main tree。

### Stage 9 Phase 1：Memory Starfield C3 Spike

Stage 9 Phase 1 状态：`phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review`。

任务 ID：`MA-V116-S9P01`。

本 phase 是 v1.1.6 修补包进入 C3 隔离原型的第一轮，只固定
`memory-starfield-spike` 作为记忆星系的独立原型证据，不替换 production Galaxy，
不导入 experiment，不进入 Stage 9 整体复审。

新增产物：

- `docs/product/memory_starfield_c3_spike_contract.md`
- `docs/acceptance/memory_starfield_c3_spike_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase1.cjs`
- `validate:v1.1.6-stage9-phase1`

验收边界：

- spike 必须保留 Three.js canvas、particle LOD、nebula dust、Flow Field、
  gravitational disk、Black Hole marker、Proto-Star marker、Memory Terrain
  cluster、hover card、reduced-motion control 和 smoke status hook。
- `fixture.ts` 必须保持 raw/private、plaintext secrets 和 local absolute path
  标志为 false。
- production `src` 不得 import 或 reference `memory-starfield-spike`。
- 本 phase 不 production integration、不 build、不运行浏览器截图、不安装本地 app、
  不部署 Cloudflare、不修改 Access policy、不读取 raw/private、不直接写长期记忆、
  不上传 GitHub main。

Machine-readable boundary summary: No production integration; No raw/private data read; No direct writeback; No Stage 10 work; No GitHub main upload.

下一步：

- Stage 9 Phase 2 已进入 Memory River C3 Spike。
- Stage 9 整体复审未执行前，不上传 GitHub main。

### Stage 9 Phase 2：Memory River C3 Spike

Stage 9 Phase 2 状态：`phase_9_2_memory_river_c3_spike_ready_pending_stage_review`。

任务 ID：`MA-V116-S9P02`。

本 phase 是 v1.1.6 修补包 C3 隔离原型的第二轮，只固定
`memory-river-spike` 作为记忆时间河的独立原型证据，不替换 production
Timeline，不导入 experiment，不进入 Stage 9 整体复审。

新增产物：

- `docs/product/memory_river_c3_spike_contract.md`
- `docs/acceptance/memory_river_c3_spike_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase2.cjs`
- `validate:v1.1.6-stage9-phase2`

验收边界：

- spike 必须保留 D3 UTC time scale、zoom/pan、brush selection、theme
  lanes、event pulses、Black Hole band、Proto-Star marker、hover card、
  reduced-motion control 和 smoke status hook。
- `fixture.ts` 必须保持 raw/private、plaintext secrets、local absolute path
  和 writeback 标志为 false。
- production `src` 不得 import 或 reference `memory-river-spike`。
- 本 phase 不 production integration、不 build、不运行浏览器截图、不安装本地
  app、不部署 Cloudflare、不修改 Access policy、不读取 raw/private、不直接写长期
  记忆、不写 proposal、不上传 GitHub main。

Machine-readable boundary summary: No production integration; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- Stage 9 Phase 3 已进入 Data Map C3 Spike。
- Stage 9 整体复审未执行前，不上传 GitHub main。

### Stage 9 Phase 3：Data Map C3 Spike

Stage 9 Phase 3 状态：`phase_9_3_data_map_c3_spike_ready_pending_stage_review`。

任务 ID：`MA-V116-S9P03`。

本 phase 是 v1.1.6 修补包 C3 隔离原型的第三轮，创建
`data-map-spike` 作为 Data Map 2.0 的独立原型证据，不替换 production Data
Guide / Data Map，不导入 experiment，不进入 Stage 9 整体复审。

新增产物：

- `apps/memory-atlas/src/experiments/data-map-spike/README.md`
- `apps/memory-atlas/src/experiments/data-map-spike/index.html`
- `apps/memory-atlas/src/experiments/data-map-spike/main.ts`
- `apps/memory-atlas/src/experiments/data-map-spike/fixture.ts`
- `docs/product/data_map_c3_spike_contract.md`
- `docs/acceptance/data_map_c3_spike_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase3.cjs`
- `validate:v1.1.6-stage9-phase3`

验收边界：

- spike 必须保留 source_layer、topic_layer、asset_layer、action_layer、
  source_to_topic_edges、topic_to_asset_edges、asset_to_action_edges、
  data_to_action_flow、map_card 字段、Inspector/Search/Review handoff、
  proposal-only 状态、reduced-motion control 和 smoke status hook。
- `fixture.ts` 必须保持 raw/private、plaintext secrets、local absolute path
  和 writeback 标志为 false，`proposalOnly` 为 true。
- production `src` 不得 import 或 reference `data-map-spike`。
- 本 phase 不 production integration、不 build、不运行浏览器截图、不安装本地
  app、不部署 Cloudflare、不修改 Access policy、不读取 raw/private、不直接写长期
  记忆、不写 proposal、不上传 GitHub main。

Machine-readable boundary summary: No production integration; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- Stage 9 Phase 4 已进入 Universe State fixture continuity。
- Stage 9 整体复审未执行前，不上传 GitHub main。

### Stage 9 Phase 4：Universe State Fixture Continuity

Stage 9 Phase 4 状态：`phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review`。

任务 ID：`MA-V116-S9P04`。

本 phase 是 v1.1.6 修补包 C3 隔离原型的第四轮，只固定既有 Universe
State generator spike 的 fixture continuity，不修改 score formula、parameter
YAML、input fixture、sample、schema 或 production integration，不进入 Stage 9
整体复审。

新增产物：

- `docs/product/universe_state_fixture_continuity_contract.md`
- `docs/acceptance/universe_state_fixture_continuity_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9_phase4.cjs`
- `validate:v1.1.6-stage9-phase4`

验收边界：

- spike 必须保留 redacted fixture adapter、deterministic sample generation、
  schema validation、parameter drift gate、black_hole_score、proto_star_score、
  stale_score、memory_weather、memory_terrain、river_pulse、mini_starfield、
  consumer_map、proposal-only actions 和 privacy_status。
- `validate:universe-state-spike` 必须通过，证明 deterministic sample、schema、
  score checks、parameter drift 和 privacy scan。
- input fixture 与 sample 必须保持 raw/private、plaintext secrets、local
  absolute paths 和 writeback 标志为 false。
- production `src` 不得 import 或 reference
  `experiments/universe-state-generator-spike`。
- 本 phase 不 production integration、不 build、不运行浏览器截图、不安装本地
  app、不部署 Cloudflare、不修改 Access policy、不读取 raw/private、不直接写长期
  记忆、不写 proposal、不上传 GitHub main。

Machine-readable boundary summary: No production integration; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- Stage 9 四个 C3 原型 phase 已完成；下一轮应执行 Stage 9 整体复审。
- Stage 9 整体复审通过并修复复审问题前，不上传 GitHub main。

### Stage 9 整体复审

Stage 9 状态：`stage_9_review_passed_pending_github_main_upload`。

任务 ID：`MA-V116-S9-REVIEW`。

本复审覆盖 Stage 9 Phase 1 Memory Starfield C3 Spike、Phase 2 Memory River
C3 Spike、Phase 3 Data Map C3 Spike 与 Phase 4 Universe State Fixture
Continuity。复审只固定四个 C3 隔离原型 phase 的合同、验收、validator、
production isolation、review artifact、package script 和治理记录一致性，不替换
production Galaxy / Timeline / Data Map，不导入 experiment 到 app shell，不修改
Universe State score formula、parameter YAML、input fixture、sample 或 schema，不进入
Stage 10。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage9_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9.cjs`
- `validate:v1.1.6-stage9`

验收边界：

- Stage 9 Phase 1-4 validator 均必须通过。
- `validate:universe-state-spike` 必须通过。
- Stage 9 review artifact、delivery、feature、development、model parameter、
  changelog 和 package script 必须一致。
- production `src` 不得 import 或 reference Stage 9 isolated experiments。
- 本 review 不 production integration、不 build、不运行浏览器截图、不安装本地
  app、不部署 Cloudflare、不修改 Access policy、不读取 raw/private、不直接写长期
  记忆、不写 proposal、不执行 agent apply、不上传 GitHub main。

Machine-readable boundary summary: No production integration; No raw/private data read; No direct writeback; No GitHub main upload.

下一 gate：

- 先执行 final remote checks、Stage 9 phase validators、
  `validate:universe-state-spike`、`validate:v1.1.6-stage9`、项目级
  acceptance audit 和 diff check。
- 再上传 canonical GitHub main tree。
- Stage 10 必须在 Stage 9 上传验证完成后另起 bounded run。

### Stage 10 Phase 1 Final Acceptance Readiness

Stage 10 Phase 1 状态：
`phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S10P01`。

本 phase 在 Stage 9 上传验证后建立最终验收 readiness 合同，只定义后续 Stage
10 review 必须证明的 roadmap v2 final acceptance、validator chain、visual
evidence、release safety、privacy/writeback、upload readiness 和 governance
sync 七类门槛。不执行整项目复审，不修改 production UI，不运行 production build，
不安装本地 app，不运行浏览器截图，不部署 Cloudflare，不上传 GitHub main。

新增产物：

- `docs/product/memory_atlas_final_acceptance_readiness_contract.md`
- `docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage10_phase1.cjs`
- `validate:v1.1.6-stage10-phase1`

验收边界：

- Stage 10 Phase 1 contract 和 acceptance 文件必须存在并覆盖七类最终验收
  readiness surface。
- `validate:v1.1.6-stage10-phase1` 必须通过。
- 当前分支必须包含 `origin/main`，证明 Stage 10 从 Stage 9 上传后的 baseline
  开始。
- 当前 OpenAIDatabase 改动必须限制在 Stage 10 Phase 1 合同、验收、validator、
  package script 和记录文件。
- 本 phase 不 production integration、不 build、不运行浏览器截图、不安装本地
  app、不部署 Cloudflare、不修改 Access policy、不读取 raw/private、不直接写
  长期记忆、不写 proposal、不执行 agent apply、不上传 GitHub main。

Machine-readable boundary summary: No production UI; No production build; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- Stage 10 Phase 1 完成后，另起 bounded run 执行 Stage 10 整体复审。
- Stage 10 整体复审通过前，不执行最终 GitHub main 上传。

### Stage 10 整体复审

Stage 10 状态：`stage_10_review_passed_pending_github_main_upload`。

任务 ID：`MA-V116-S10-REVIEW`。

本复审覆盖 Stage 10 Phase 1 Final Acceptance Readiness，并把
`validate:whole-project` 作为强证据门槛复跑。复审确认 Part 1-10 validators、
production frontend build、OpenAIDatabase Python compile、unittest discovery、
visual acceptance、release audit、overall acceptance、offline Cloudflare Pages +
Access preflight、Roadmap v2 final acceptance runtime/audit coverage、canonical
remote 和 GitHub upload boundary 均通过。本复审不新增 production runtime
feature work，不读取 raw/private，不直接写长期记忆，不写 proposal，不执行 agent
apply，不部署 Cloudflare，不修改 Access policy，不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage10_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage10.cjs`
- `validate:v1.1.6-stage10`

验收边界：

- Stage 10 Phase 1 readiness contract、acceptance、validator 和 records 必须一致。
- `validate:whole-project` 必须返回 PASS。
- Stage 10 review artifact、delivery、feature、development、model parameter、
  changelog 和 package script 必须一致。
- 当前 OpenAIDatabase 改动必须限制在 Stage 10 review artifact、validator、
  package script 和记录文件。
- 本 review 不 production runtime feature work、不安装本地 app、不部署 Cloudflare、
  不修改 Access policy、不读取 raw/private、不直接写长期记忆、不写 proposal、
  不执行 agent apply、不上传 GitHub main。

Machine-readable boundary summary: No production runtime feature work; No raw/private data read; No direct writeback; No GitHub main upload.

下一 gate：

- 执行 final upload gate：fetch/integrate、重跑 Stage 10 validators 和
  `validate:whole-project`、检查 clean tracked tree、canonical remote、push target
  和 final remote ancestry。
- final upload gate 未通过前，不上传 GitHub main。

### Stage 6 整体复审

Stage 6 状态：`stage_6_review_passed_pending_github_main_upload`。

任务 ID：`MA-V116-S6-REVIEW`。

本复审覆盖 v1.1.6 Stage 6 Phase 1 Memory River Rebuild Contract，只确认
`memory_river_rebuild_contract` 合同、验收、validator、review artifact、
package script 和治理记录一致。不实现运行时 UI、不修改 CSS、不实现 Memory
River runtime、不读取 raw/private 数据、不直接写长期记忆、不执行 agent
apply、不进入 Stage 7、不在 review artifact 中执行 GitHub main 上传。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage6_review.md`
- `validate:v1.1.6-stage6`

验收边界：

- Stage 6 复审通过不表示 runtime Memory River、浏览器截图、真实 zoom/brush
  交互或 agent apply 已完成。
- Stage 7 必须在 Stage 6 上传校验通过后另起 bounded run。
- 不 commit `.DS_Store`。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 继续 Stage 3 的下一个 phase，补 proposal-only 工作区的持久化/队列或复审前收敛检查。
- Stage 3 整体复审未执行前，不进入 Stage 4，不上传 GitHub main。

### Stage 3 Phase 2：Proposal Queue Persistence Contract

Stage 3 Phase 2 状态：`phase_3_2_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S3P02`。

本 phase 是 v1.1.6 修补包 proposal-only 调整层的第二轮，只定义 proposal queue 持久化与版本链合同，不实现运行时 UI、不修改 CSS、不启动浏览器、不写 localStorage、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply。

新增产物：

- `docs/product/proposal_queue_persistence_contract.md`
- `docs/acceptance/proposal_queue_persistence_acceptance.md`
- `validate:v1.1.6-stage3-phase2`

本 phase 解决的缺口：

- Stage 3 Phase 1 定义了工作区，但没有固定本地 proposal queue 的持久化键、追加策略和版本链。
- proposal queue 必须固定为 `memory-atlas.writeback.proposals.v1`，范围为 `browser_local_only`，变更策略为 `append_only`。
- 每个 proposal_record 必须保留 proposal_id、revision、parent_proposal_id、supersedes_proposal_id、rollback_to_proposal_id、parent_snapshot_id、target_ref、target_type、target_id、field、old_value_ref、proposed_value、diff_summary、reason、evidence_refs、status、created_at、updated_at、requires_conflict_check、requires_agent_or_human_apply 和 rollback_hint。
- proposal_history 必须记录状态变化、替代和 rollback_proposal，不能静默覆盖旧 proposal。
- stale_snapshot、schema_mismatch 和 forbidden_payload 必须作为阻断状态显式可见。

验收边界：

- 本 phase 只覆盖 Roadmap v2 Stage 3 Phase 2 的 proposal queue 持久化与版本链合同。
- agent apply、Search 2.0、Review / Summary / Iteration、Data Map 2.0 未进入。
- 不启动本地 app，不执行 Playwright 截图验收；截图验收进入后续实现 phase。
- 不 commit，不上传 GitHub main；Stage 1-5 完成后再做整体上传流程。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 3 整体复审，补 review artifact 和 stage-level validator，并修复复审暴露的问题。
- Stage 3 整体复审未执行前，不进入 Stage 4，不上传 GitHub main。

### Stage 3 整体复审

Stage 3 整体复审状态：`stage_3_review_passed_pending_stage4`。

任务 ID：`MA-V116-S3-REVIEW`。

本复审覆盖 v1.1.6 Stage 3 Phase 1-2，只确认 proposal-only 调整工作区、proposal queue 持久化与版本链的合同、验收、validator、记录、review artifact 和进入 Stage 4 前边界一致，不实现运行时 UI、不修改 CSS、不写 localStorage、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage3_review.md`
- `validate:v1.1.6-stage3`

复审发现的问题：

- Phase 3.1-3.2 已有合同、验收和 phase validator，但缺少 Stage 3 整体 review artifact 和 deterministic stage-level validator。

修复：

- 新增 Stage 3 review artifact。
- 新增 `validate:v1.1.6-stage3`。
- 更新 delivery、model、feature、development、model parameter 和 changelog 记录，标记 Stage 3 复审通过并等待 Stage 4。

验收边界：

- Stage 3 复审通过不表示 runtime UI、浏览器截图、真实 localStorage queue、agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 2.0 已完成。
- Stage 4-5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 4 的第一个 bounded run。
- 若 Stage 3 文件后续变化，必须重新运行 `validate:v1.1.6-stage3`。

### Stage 4 Phase 1：Search 2.0 Workflow Contract

Stage 4 Phase 1 状态：`phase_4_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S4P01`。

本 phase 覆盖 v1.1.6 Search 2.0 工作流合同，只确认 `search_2_0_workflow`、query/filter、result list、`matched_reason`、`jump_to_starfield`、`jump_to_river`、`open_inspector`、session summary、zero-result recovery、proposal-only handoff、安全边界、validator 和记录一致，不实现运行时 UI、不修改 CSS、不建立真实搜索索引、不读取 raw/private 数据、不直接写长期记忆、不进入 Review / Summary / Iteration、不进入 Data Map 2.0、不上传 GitHub main。

新增产物：

- `docs/product/search_2_0_workflow_contract.md`
- `docs/acceptance/search_2_0_workflow_acceptance.md`
- `validate:v1.1.6-stage4-phase1`

验收边界：

- Stage 4 Phase 1 通过不表示 runtime Search 2.0、浏览器截图、Review / Summary / Iteration 或 Data Map 2.0 已完成。
- Stage 4 整体复审未执行。
- Stage 5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 4 Phase 2：Review / Summary / Iteration 合同。
- Stage 4 整体复审未执行前，不进入 Stage 5，不上传 GitHub main。

### Stage 4 Phase 2：Review / Summary / Iteration Workflow Contract

Stage 4 Phase 2 状态：`phase_4_2_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S4P02`。

本 phase 覆盖 v1.1.6 Review / Summary / Iteration 工作流合同，只确认 `review_summary_iteration_workflow`、八个复盘问题、theme_change_panel、opportunity_panel、low_value_loop_panel、decision_change_panel、next_action_panel、proposal_decision_panel、iteration_backlog、安全边界、validator 和记录一致，不实现运行时 UI、不修改 CSS、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply、不进入 Data Map 2.0、不上传 GitHub main。

新增产物：

- `docs/product/review_summary_iteration_workflow_contract.md`
- `docs/acceptance/review_summary_iteration_workflow_acceptance.md`
- `validate:v1.1.6-stage4-phase2`

验收边界：

- Stage 4 Phase 2 通过不表示 runtime Review / Summary / Iteration、浏览器截图、Data Map 2.0 或 Stage 4 整体复审已完成。
- Stage 4 整体复审未执行。
- Stage 5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 4 整体复审，补 review artifact 和 stage-level validator，并解决复审暴露的问题。
- Stage 4 整体复审未执行前，不进入 Stage 5，不上传 GitHub main。

### Stage 4 整体复审

Stage 4 整体复审状态：`stage_4_review_passed_pending_stage5`。

任务 ID：`MA-V116-S4-REVIEW`。

本复审覆盖 Stage 4 Phase 1 Search 2.0 Workflow Contract 和 Stage 4
Phase 2 Review / Summary / Iteration Workflow Contract，只确认合同、验收、
phase validator、review artifact、stage-level validator、记录一致性、改动
范围和安全边界。不实现运行时 UI、不修改 CSS、不建立真实搜索索引、不实现复盘
runtime、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply、不进入
Data Map 2.0 runtime、不进入 Stage 5、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage4_review.md`
- `validate:v1.1.6-stage4`

复审结论：

- Stage 4 Phase 1 Search 2.0 合同、验收、validator 和记录一致。
- Stage 4 Phase 2 Review / Summary / Iteration 合同、验收、validator 和记录一致。
- 复审发现的 deterministic stage-level validator/review artifact 缺口已修复。
- Stage 4 整体复审通过，进入 `stage_4_review_passed_pending_stage5`。

验收边界：

- Stage 4 复审通过不表示 runtime Search 2.0、runtime Review / Summary /
  Iteration、浏览器截图或 Data Map 2.0 已完成。
- Stage 5 未进入。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 5 的第一个 bounded run。
- 若 Stage 4 文件后续变化，必须重新运行 `validate:v1.1.6-stage4`。

### Stage 5 Phase 1：Data Map 2.0 Workflow Contract

Stage 5 Phase 1 状态：`phase_5_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S5P01`。

本 phase 覆盖 v1.1.6 Data Map 2.0 工作流合同，只确认
`data_map_2_0_workflow`、source_layer、topic_layer、asset_layer、
action_layer、data_to_action_flow、source_to_topic_edges、topic_to_asset_edges、
asset_to_action_edges、map_card 字段、Inspector/Search/Review 跳转、
proposal-only handoff、安全边界、validator 和记录一致。不实现运行时 UI、
不修改 CSS、不实现 Data Map renderer、不读取 raw/private 数据、不直接写长期记忆、
不执行 agent apply、不进入 Stage 5 整体复审、不上传 GitHub main。

新增产物：

- `docs/product/data_map_2_0_workflow_contract.md`
- `docs/acceptance/data_map_2_0_workflow_acceptance.md`
- `validate:v1.1.6-stage5-phase1`

验收边界：

- Stage 5 Phase 1 通过不表示 runtime Data Map 2.0、浏览器截图或 Stage 5
  整体复审已完成。
- Stage 5 整体复审未执行。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 Stage 1-5 全部完成且最终上传 gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 5 整体复审，补 review artifact 和 stage-level validator，并解决复审暴露的问题。
- Stage 5 整体复审未执行前，不上传 GitHub main。

### Stage 5 整体复审

Stage 5 状态：`stage_5_review_passed_pending_stage1_5_final_upload`。

任务 ID：`MA-V116-S5-REVIEW`。

本复审覆盖 v1.1.6 Stage 5 Phase 1 Data Map 2.0 Workflow Contract，只确认
`data_map_2_0_workflow` 合同、验收、validator、review artifact、package
script 和治理记录一致。不实现运行时 UI、不修改 CSS、不实现 Data Map
runtime、不读取 raw/private 数据、不直接写长期记忆、不执行 agent apply、不进入
Stage 6、不上传 GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage5_review.md`
- `validate:v1.1.6-stage5`

验收边界：

- Stage 5 复审通过不表示 runtime Data Map 2.0、浏览器截图或 agent apply
  已完成。
- Stage 1-5 final upload 未执行。
- 不 commit，不上传 GitHub main；GitHub main 上传延后到 final upload gate 通过后。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

### Stage 6 Phase 1：Memory River Rebuild Contract

Stage 6 Phase 1 状态：`phase_6_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S6P01`。

本 phase 是 v1.1.6 修补包进入“记忆时间河重做”的第一轮，只定义
`memory_river_rebuild_contract` 合同、验收、validator 和治理记录一致性。
它把旧 Timeline 按 0 分处理，要求未来实现必须展示 `time_river`、
`theme_bands`、`event_pulses`、`decision_nodes`、`black_hole_band`、
`proto_star_marker` 和 `evidence_density_lane`，并支持 zoom、brush、
hover card、click Inspector、keyboard navigation 和 reduced motion。

新增产物：

- `docs/product/memory_river_rebuild_contract.md`
- `docs/acceptance/memory_river_rebuild_acceptance.md`
- `validate:v1.1.6-stage6-phase1`

验收边界：

- 默认日期列表、静态表格、普通 dots-and-lines timeline、缺少生命周期 marker、
  缺少 Inspector 交接或 reduced motion 被忽略，均为未来实现失败条件。
- Stage 6 Phase 1 通过不表示 runtime Memory River、浏览器截图或真实交互已完成。
- 不实现运行时 UI，不修改 CSS，不读取 raw/private 数据，不直接写长期记忆，
  不执行 agent apply，不进入 Stage 7-10，不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 执行 Stage 1-5 final upload gate：fetch/integrate、重跑 Stage 1-5 validators、
  可用 governance checks、确认 changed files、避免 staging `.DS_Store`。
- final upload gate 未通过前，不上传 GitHub main。

### Stage 7 Phase 1：Memory Starfield Rebuild Contract

Stage 7 Phase 1 状态：`phase_7_1_contract_created_pending_stage_review`。

任务 ID：`MA-V116-S7P01`。

本 phase 是 v1.1.6 修补包进入“记忆星系重做”的第一轮，只定义
`memory_starfield_rebuild_contract` 合同、验收、validator 和治理记录一致性。
它把普通 dots-and-lines、node-link graph、Obsidian-like graph 或 chart-like
network 明确列为未来实现失败条件，要求未来实现必须展示
`memory_starfield`、`nebula_field`、`flow_field`、`trajectory_trails`、
`gravity_sources`、`black_hole_core`、`proto_star_cloud`、
`memory_terrain_layer`、`cluster_constellations` 和
`ambient_depth_particles`，并支持 orbit pan/zoom、hover card、click
Inspector、focus cluster、Search 2.0 跳转、Memory River 跳转、Presentation /
Analysis 模式、keyboard navigation 和 reduced motion。

新增产物：

- `docs/product/memory_starfield_rebuild_contract.md`
- `docs/acceptance/memory_starfield_rebuild_acceptance.md`
- `validate:v1.1.6-stage7-phase1`

验收边界：

- 默认只有点、只有边线、普通 Obsidian Graph、缺少星云、缺少流场、缺少轨迹、
  缺少引力源、缺少黑洞、缺少新生星云、缺少记忆地形层、缺少 Inspector 交接、
  WebGL/fallback 空白或 reduced motion 被忽略，均为未来实现失败条件。
- Stage 7 Phase 1 通过不表示 runtime Memory Starfield、浏览器截图或真实交互已完成。
- 不实现运行时 UI，不修改 CSS，不导入 experiment 目录，不切换 feature flag，
  不读取 raw/private 数据，不直接写长期记忆，不执行 agent apply，不进入 Stage 7
  整体复审，不进入 Stage 8-10，不上传 GitHub main。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

下一步：

- 进入 Stage 7 整体复审，补 review artifact 和 stage-level validator，并解决复审暴露的问题。
- Stage 7 整体复审未执行前，不上传 GitHub main。

### Stage 7 整体复审

Stage 7 状态：`stage_7_review_passed_pending_github_main_upload`。

任务 ID：`MA-V116-S7-REVIEW`。

本复审覆盖 v1.1.6 Stage 7 Phase 1 Memory Starfield Rebuild Contract，只确认
`memory_starfield_rebuild_contract` 合同、验收、validator、review artifact、
package script 和治理记录一致。不实现运行时 UI、不修改 CSS、不实现 Memory
Starfield runtime、不导入 experiment 目录、不切换 feature flag、不读取
raw/private 数据、不直接写长期记忆、不执行 agent apply、不进入 Stage 8、不上传
GitHub main。

新增产物：

- `docs/reviews/memory_atlas_v1_1_6_stage7_review.md`
- `validate:v1.1.6-stage7`

验收边界：

- Stage 7 复审通过不表示 runtime Memory Starfield、浏览器截图、WebGL/fallback
  canvas、真实 Search/River focus handoff 或 agent apply 已完成。
- Stage 8 未进入。
- GitHub main upload 只在 final remote checks 通过后执行。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.
