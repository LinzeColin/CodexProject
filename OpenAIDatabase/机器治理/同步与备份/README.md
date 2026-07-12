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
均可验证。

当前 S04 P1 已完成，并新增：

- `机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `scripts/sync_chatgpt_memory_data.py`
- `scripts/atlasctl.py`
- `人类可读/09_ChatGPT只读同步与官方导出Fallback.md`
- `docs/reviews/memory_atlas_v1_2_s04_p1_chatgpt_sync.md`

S04 P1 固定 ChatGPT 只读同步和 official export fallback。浏览器 connector 只允许读取已登录状态下的
conversation/title/metadata；遇到密码/验证码立即停止；不得发送消息、删除、归档或重命名会话。
下一步是 S04 P2。当前阶段不实现 Codex local sync，不实现后续 agent adapter，
不实现 GitHub backup apply，不上传 GitHub main。

当前 S04 P2 已完成，并新增：

- `机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `scripts/sync_codex_memory_data.py`
- `scripts/sync_future_agent_data.py`
- `scripts/atlasctl.py`
- `人类可读/10_Codex与FutureAgent同步.md`
- `docs/reviews/memory_atlas_v1_2_s04_p2_codex_agent_sync.md`

S04 P2 固定 Codex local sync 和 future-agent minimal adapter。Codex 输出
`data/public_raw/codex`、`data/derived/codex/codex_activity_snapshot.json` 和
`data/run_logs/sync_runs`；future-agent 输出 `data/public_raw/agents/{agent_id}`、
`data/derived/agents/{agent_id}/agent_sync_summary.json` 和 `data/run_logs/sync_runs`。
dry-run 不写文件；apply 缺少输入时不能生成伪数据。

下一步是 S04 P3。当前阶段不实现 GitHub backup dry-run/apply，不上传 GitHub main。

当前 S04 P3 已完成，并新增：

- `机器治理/同步与备份/github_backup_policy.v1_2_s04_p3.json`
- `scripts/github_backup.py`
- `scripts/atlasctl.py`
- `人类可读/11_GitHub备份DryRun与Apply.md`
- `docs/reviews/memory_atlas_v1_2_s04_p3_github_backup.md`

S04 P3 固定 GitHub backup dry-run/apply：备份范围覆盖 `data/public_raw`、
`data/derived`、`data/run_logs`、`docs/reviews` 和 `reports`。dry-run 不写文件；
apply 只本地 git add/commit，不远端 push。非 Git worktree 和无变更场景必须输出
中文原因和 fallback 建议。

当前 S04 Review 已通过，并新增：

- `docs/reviews/memory_atlas_v1_2_s04_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_review.cjs`

S04 Review 确认 ChatGPT 只读同步、Codex local sync、future-agent minimal adapter、
raw + derived + run log 输出、build-atlas dry-run 和 GitHub backup dry-run/apply 均可验证。

下一步是 S05 P1。当前 review 不上传 GitHub main，不远端 push，不重装 app。

当前项目状态已继续推进：S05 P1 已完成 facet/canonical event schema，
但它不改变本同步与备份页已定义的 ChatGPT/Codex/future-agent 同步边界。
项目下一步是 S05 P2。
