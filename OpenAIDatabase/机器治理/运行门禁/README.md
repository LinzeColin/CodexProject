# 运行门禁

用于放置 stage gate、stop condition、rollback、需求冻结和运行前检查。

当前阶段是 S07 Review。任务 ID 为 `MA-V12-S07-REVIEW`，验收 ID 为
`ACC-MA-V12-S07-REVIEW`，validator 为 `validate:v1.2-s07-review`。

S07 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s07_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_review.cjs`
- `scripts/atlasctl.py`
- `data/derived/economic_proxy/personal_economic_proxy.json`
- `data/derived/information_roi/information_roi_gate.json`
- `data/derived/economic_proxy/formula_what_if_preview.json`
- `机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`
- `机器治理/参数与公式/information_roi.v1_2_s07_p2.json`
- `机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`

S07 Review gate：

- `validate:v1.2-s07-review` 可验证 S07 P1/P2/P3 链路。
- `validate:v1.2-s07-p3` 在 clean tree 可通过。
- Personal Economic Proxy 可生成。
- 每个分数有中文解释、公式来源和参数引用。
- Information ROI 覆盖 insight、card、chart。
- Visual ROI Gate 保证没有决策价值的图表不进 P0。
- Formula What-if 可查看或配置，且 `proposal_required_before_apply=true`。
- 外部经济数据库只保留 v2 占位，不深做。
- 不声称精确收入预测，不提供财务建议。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S08 P1。

S07 P3 产物：

- `docs/reviews/memory_atlas_v1_2_s07_p3_formula_what_if.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p3.cjs`
- `scripts/build_memory_atlas_formula_what_if.py`
- `scripts/atlasctl.py`
- `机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`
- `data/derived/economic_proxy/formula_what_if_preview.json`
- `人类可读/18_FormulaWhatIf配置预览说明.md`

S07 P3 gate：

- `validate:v1.2-s07-p3` 可验证 Formula What-if 配置预览。
- `python scripts/atlasctl.py analyze --stage formula-what-if --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check formula-what-if` 返回 PASS。
- 输出包含 `scenarios`、`adjustable_weights`、`parameter_change_proposal`、公式来源和参数引用。
- `proposal_required_before_apply=true`。
- `active_config_write=false`。
- 不接入外部经济数据库。
- 不是精确收入预测，不是财务建议。
- 不实现运行时 UI。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S07 Review。

S07 P2 产物：

- `docs/reviews/memory_atlas_v1_2_s07_p2_information_roi.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p2.cjs`
- `scripts/build_memory_atlas_information_roi.py`
- `scripts/atlasctl.py`
- `机器治理/参数与公式/information_roi.v1_2_s07_p2.json`
- `机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json`
- `data/derived/information_roi/information_roi_gate.json`
- `人类可读/17_InformationROI与VisualROIGate说明.md`

S07 P2 gate：

- `validate:v1.2-s07-p2` 可验证 Information ROI 与 Visual ROI Gate。
- `python scripts/atlasctl.py analyze --stage information-roi --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check visual-roi` 返回 PASS。
- 每个 ROI item 有公式来源、参数引用和证据引用。
- P0 visual 必须有 human question、action 和 gate pass。
- 没有决策价值的图表不进 P0。
- 不接入外部经济数据库。
- 不是精确收入预测，不是财务建议。
- 不实现 S07 P3 what-if UI。
- 不修改运行时 UI。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S07 P3。

S07 P1 产物：

- `docs/reviews/memory_atlas_v1_2_s07_p1_economic_proxy.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p1.cjs`
- `scripts/build_memory_atlas_economic_proxy.py`
- `scripts/atlasctl.py`
- `机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`
- `data/derived/economic_proxy/personal_economic_proxy.json`
- `人类可读/16_PersonalEconomicProxy公式说明.md`

S07 P1 gate：

- `validate:v1.2-s07-p1` 可验证 Personal Economic Proxy。
- `python scripts/atlasctl.py analyze --stage economic-proxy --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check formulas` 返回 PASS。
- 每个 score card 有中文解释、公式来源、参数引用和证据引用。
- 不接入外部经济数据库；外部经济数据库只作为 v2 interface 预留。
- 不是精确收入预测，不是财务建议。
- 不实现 S07 P2 information ROI gate。
- 不实现 S07 P3 what-if UI。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S07 P2。

S06 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s06_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_review.cjs`
- `scripts/build_memory_atlas_data.py`
- `data/derived/visualization/memory_atlas.json`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/types.ts`
- `apps/memory-atlas/src/styles.css`
- `scripts/build_memory_atlas_opportunities.py`
- `scripts/atlasctl.py`
- `data/derived/behavior_intelligence/clusters.json`
- `data/derived/behavior_intelligence/low_value_loops.json`
- `data/derived/behavior_intelligence/opportunities.json`

S06 Review gate：

- `validate:v1.2-s06-review` 可验证 S06 P1/P2/P3 输出和显示接入。
- `data/derived/visualization/memory_atlas.json` 包含 `behavior_intelligence`。
- Memory Atlas 首页通过 `data-s06-review-display` 显示主题簇、低价值循环和机会线索。
- 输出包含 160 个 clusters、23 个低价值循环和 12 条候选机会。
- `python scripts/atlasctl.py audit --check insight-evidence` 返回 PASS 且 `bad_items` 为空。
- 不接外部经济数据库，不做心理诊断，不生成无穷压力清单，不修改 raw。

No GitHub main upload in this phase。
下一步是 S07 P1。

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

当前阶段是 S04 P2。任务 ID 为 `MA-V12-S04P2`，验收 ID 为
`ACC-MA-V12-S04P2`，validator 为 `validate:v1.2-s04-p2`。

S04 P2 产物：

- `机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `scripts/sync_codex_memory_data.py`
- `scripts/sync_future_agent_data.py`
- `scripts/atlasctl.py`
- `人类可读/10_Codex与FutureAgent同步.md`
- `docs/reviews/memory_atlas_v1_2_s04_p2_codex_agent_sync.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p2.cjs`

S04 P2 gate：

- `python scripts/atlasctl.py sync --source codex --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py sync --source future-agent --dry-run` 可运行且不写文件。
- Codex local sync 输出 raw + derived + run log 合同。
- future-agent minimal adapter 输出 raw + derived + run log 合同。
- future-agent apply 缺少输入时不能生成伪数据。

No GitHub main upload in this phase。
下一步是 S04 P3；本 phase 不实现 GitHub backup dry-run/apply。

前置 S04 P3 已通过：`MA-V12-S04P3` / `ACC-MA-V12-S04P3` /
`validate:v1.2-s04-p3`。

S04 P3 产物：

- `机器治理/同步与备份/github_backup_policy.v1_2_s04_p3.json`
- `scripts/github_backup.py`
- `scripts/atlasctl.py`
- `人类可读/11_GitHub备份DryRun与Apply.md`
- `docs/reviews/memory_atlas_v1_2_s04_p3_github_backup.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p3.cjs`

S04 P3 gate：

- `python scripts/atlasctl.py push --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py push --apply` 只做本地 git add/commit。
- backup scope 覆盖 `data/public_raw`、`data/derived`、`data/run_logs`、
  `docs/reviews` 和 `reports`。
- 失败时输出中文原因和 fallback 建议。
- 不执行远端 push，不上传 GitHub main，不重装 app。

S04 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s04_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_review.cjs`

S04 Review gate：

- S04 P1、S04 P2、S04 P3 validator 链路在 clean tree 可复跑。
- `python scripts/atlasctl.py sync --source chatgpt --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py sync --source codex --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py sync --source future-agent --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py build-atlas --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py push --dry-run` 可运行且不远端 push。
- S04 整体复审已通过。

No GitHub main upload in this review。
No remote push in this review。
前置 S04 Review 已通过：`MA-V12-S04-REVIEW` / `ACC-MA-V12-S04-REVIEW` /
`validate:v1.2-s04-review`。

S05 P1 产物：

- `机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`
- `人类可读/12_Facet字段与事件语义说明.md`
- `docs/reviews/memory_atlas_v1_2_s05_p1_facet_schema.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p1.cjs`

S05 P1 gate：

- facet schema 定义 `source`、`topic`、`intent`、`task_type`、`project`、
  `output_type`、`language`、`tool`、`turn_count`、`friction`、`value_signal`
  和 `future_agent_source`。
- 字段名必须是英文。
- 人类文件必须用中文解释字段含义。
- schema 覆盖 ChatGPT、Codex 和 future agent。
- 不实现 extractor，不生成 fake events，不修改 raw，不把机器字段堆到首屏。

No GitHub main upload in this phase。
No remote push in this phase。
前置 S05 P1 已通过：`MA-V12-S05P1` / `ACC-MA-V12-S05P1` /
`validate:v1.2-s05-p1`。

S05 P2 产物：

- `scripts/extract_memory_atlas_facets.py`
- `scripts/atlasctl.py analyze --stage facets`
- `data/derived/behavior_intelligence/events.json`
- `docs/reviews/memory_atlas_v1_2_s05_p2_facet_extractor.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p2.cjs`

S05 P2 gate：

- extractor 可从 ChatGPT、Codex 和 future_agent/other_agent 的 raw 或 derived 输入抽取
  canonical events。
- 缺失字段必须 fallback，不得抛出无意义异常。
- 缺失来源必须写 source_status missing_reason，不得生成 fake events。
- 每条 event 必须包含 `raw_ref`、`manifest_ref`、`derived_ref` 或
  `evidence_missing_reason`。
- 不修改 raw，不上传 GitHub main，不远端 push，不改变首屏 UI。

No GitHub main upload in this phase。
No remote push in this phase。
No raw mutation in this phase。

S05 P3 产物：

- `scripts/extract_memory_atlas_facets.py`
- `scripts/atlasctl.py analyze --stage facets`
- `data/derived/behavior_intelligence/events.json`
- `docs/reviews/memory_atlas_v1_2_s05_p3_evidence_refs.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p3.cjs`

S05 P3 gate：

- 每条 event 必须包含 `source_id` 和轻量 `evidence_refs`。
- `evidence_refs` 必须指向 `raw_ref`、`manifest_ref`、`derived_ref` 或
  `evidence_missing_reason`。
- 不实现 Raw-to-Insight Replay UI。
- 不生成 fake events，不修改 raw，不上传 GitHub main，不远端 push。

No GitHub main upload in this phase。
No remote push in this phase。
No raw mutation in this phase。

S05 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s05_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_review.cjs`

S05 Review gate：

- S05 P1、S05 P2、S05 P3 validator 链路在 clean tree 可复跑。
- canonical event 可覆盖 ChatGPT/Codex/future agent。
- 每条 event 有 evidence ref 或缺失原因。
- 人类文件能解释 facet 含义。
- 不输出纯机器字段给首屏。
- 行为事件与 facets 可被后续 cluster、ROI、latent、visualization 复用。
- 不生成 fake events，不修改 raw，不上传 GitHub main，不远端 push。

No GitHub main upload in this review。
No remote push in this review。
No raw mutation in this review。
下一步是 S06 P1。

S06 P1 产物：

- `scripts/build_memory_atlas_clusters.py`
- `scripts/atlasctl.py analyze --stage clusters`
- `scripts/atlasctl.py audit --check insight-evidence`
- `data/derived/behavior_intelligence/clusters.json`
- `人类可读/13_行为簇与层级簇说明.md`
- `docs/reviews/memory_atlas_v1_2_s06_p1_cluster_builder.md`

S06 P1 gate：

- 生成主题簇和层级簇。
- 支持 `source/time/project/task/language` 过滤合同。
- 每个 cluster 有中文摘要和 `evidence_refs`。
- 不识别低价值循环，不生成机会卡片，不修改 raw。

下一步是 S06 P2。
