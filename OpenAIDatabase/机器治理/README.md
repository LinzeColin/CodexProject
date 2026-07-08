# 机器治理

这里放 Memory Atlas v1.2 的机器可读参数、公式、数据契约、同步配置、验收门禁和运行证据。

本目录不替代 apps/scripts/tests/config/data/docs/governance。现有运行代码、测试、配置、
数据和旧治理目录继续留在原位置。

## 子目录

- `参数与公式/`：公式、权重、阈值和参数解释。
- `数据契约/`：source、raw、derived、reports、visualization 的 schema 或契约。
- `同步与备份/`：ChatGPT、Codex、后续其他 agent 的 source registry 和同步策略。
- `可视化配置/`：图表、human question map、visual ROI gate 的机器配置。
- `行为智能模型/`：facets、clusters、latent signals、collaboration quality 的模型配置。
- `运行门禁/`：stage gates、stop conditions、rollback 和需求冻结。
- `测试与验收/`：validator、acceptance matrix 和测试说明。
- `证据与日志/`：run evidence、audit logs、manifest/hash 和 stage evidence。

## 当前阶段

当前为 S05 P1。任务 ID 为 `MA-V12-S05P1`，验收 ID 为
`ACC-MA-V12-S05P1`，validator 为 `validate:v1.2-s05-p1`。
S01 整体复审已通过，S02 整体复审已通过，S03 P1/P2/P3
整体复审已通过。S04 P1 已建立 ChatGPT 只读同步和 official export fallback。
S04 P2 已建立 Codex local sync、future-agent minimal adapter、raw + derived + run log
输出合同，以及 `scripts/atlasctl.py` 的 codex/future-agent dry-run 入口。
S04 P3 已建立 GitHub backup dry-run/apply 本地控制面；apply 只做本地 commit，
不执行远端 push。S04 整体复审已通过。S05 P1 已定义 facet/canonical event
schema，下一步是 S05 P2。

当前机器产物：

- `数据契约/source_data_model.v1_2_s02_p1.json`
- `数据契约/facet_event_schema.v1_2_s05_p1.json`
- `同步与备份/sync_source_registry.json`
- `同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `同步与备份/github_backup_policy.v1_2_s04_p3.json`
- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `机器治理/同步与备份/github_backup_policy.v1_2_s04_p3.json`
- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`
- `../人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`
- `../人类可读/06_Raw明文公开与只读归档说明.md`
- `../人类可读/07_凭证排除说明.md`
- `../人类可读/08_Raw机器账本说明.md`
- `../人类可读/09_ChatGPT只读同步与官方导出Fallback.md`
- `../人类可读/10_Codex与FutureAgent同步.md`
- `../人类可读/11_GitHub备份DryRun与Apply.md`
- `../人类可读/12_Facet字段与事件语义说明.md`
- `../data/public_raw/README.md`
- `人类可读/06_Raw明文公开与只读归档说明.md`
- `data/public_raw/README.md`
- `../docs/reviews/memory_atlas_v1_2_s02_review.md`
- `../docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md`
- `../docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md`
- `../docs/reviews/memory_atlas_v1_2_s03_p3_machine_ledger.md`
- `../docs/reviews/memory_atlas_v1_2_s03_review.md`
- `../docs/reviews/memory_atlas_v1_2_s04_p1_chatgpt_sync.md`
- `../docs/reviews/memory_atlas_v1_2_s04_p2_codex_agent_sync.md`
- `../docs/reviews/memory_atlas_v1_2_s04_p3_github_backup.md`
- `../docs/reviews/memory_atlas_v1_2_s04_review.md`
- `../docs/reviews/memory_atlas_v1_2_s05_p1_facet_schema.md`
- `scripts/privacy_guard.py`
- `scripts/sync_codex_memory_data.py`
- `scripts/raw_archive_manifest.py`
- `scripts/sync_chatgpt_memory_data.py`
- `scripts/sync_future_agent_data.py`
- `scripts/github_backup.py`
- `scripts/atlasctl.py`

`运行门禁/v1.2需求冻结清单.json` 继续固定：

- 四线范围。
- 14 Stage 与每次 run 最多一个 phase 的执行规则。
- raw 公开授权。
- 凭证排除。
- 后续其他 agent 数据源扩展规则。

下一步是 S05 P2；本目录仍不替代 apps/scripts/tests/config/data/docs/governance。
