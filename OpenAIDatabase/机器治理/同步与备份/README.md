# 同步与备份

用于放置 ChatGPT、Codex、后续其他 agent 的 source registry、同步模式、公开备份策略、
raw append-only 规则和 credential boundary。

当前 S02 Review 已通过，并继续使用 S02 P2 的 source registry：

- `sync_source_registry.json`
- 依赖的 source data model：`../数据契约/source_data_model.v1_2_s02_p1.json`
- ChatGPT browser connector + official export fallback
- Codex local sync
- future_agent_template / other_agent / future_agent_adapter
- `人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`

人类说明已写清楚 ChatGPT、Codex、后续其他 agent 数据备份进 GitHub、future agent 接入规则、
public backup mode、transcript/credential boundary 和 credential exclusion。

S02 整体复审已通过，复审证据为 `docs/reviews/memory_atlas_v1_2_s02_review.md`。

当前 S03 P1 已完成，并新增：

- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `data/public_raw/README.md`
- `人类可读/06_Raw明文公开与只读归档说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md`

S03 P1 定义 `data/public_raw/`、manifest/hash 文件合同、append-only 规则和
hash drift fail 规则。

当前 S03 P2 已完成，并新增：

- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `scripts/privacy_guard.py`
- `scripts/sync_codex_memory_data.py`
- `人类可读/07_凭证排除说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md`

S03 P2 固定 credential is not memory 和 `credentials_not_transcript`：普通 transcript
可以进入公开 raw；凭证 pattern 导致 gate fail。

当前 S03 P3 已完成，并新增：

- `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `scripts/raw_archive_manifest.py`
- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`
- `人类可读/08_Raw机器账本说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p3_machine_ledger.md`

S03 P3 固定 raw manifest/hash 机器账本：可生成 source/file/hash/imported_at 映射，
并由 audit 检查 append-only、hash drift 和 deleted manifest entry。

当前 S03 Review 已通过，并新增：

- `docs/reviews/memory_atlas_v1_2_s03_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs`

S03 Review 确认 raw 可公开备份、append-only、credential exclusion 和 raw manifest/hash
均可验证。下一步是 S04 P1。
当前阶段不实现 connector，不导入真实 transcript，不新增 UI，不上传 GitHub main。
