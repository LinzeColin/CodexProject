# TASK_REPORT · ADP-S5-P04-T068｜Knowledge Validity 与 131 项收益对齐回归

## 唯一目标（达成）
**当事实变化时重开旧知识**，并**确认竞品用户收益均有明确状态**：①Knowledge Validity clock——知识绑定其来源的实质版本（T026 content_hash），源实质变化→自动标 needs_review/invalid，可重学；噪声再渲染不误失效。②131 项 benefit-parity 回归——每项竞品收益有**明确状态（closed vocab，绝无 unknown）**与**具名 owner（绝无 no-owner）**。交付 validity clock、review invalidation、parity regression report。release_mode=NOT_DEPLOYED。**收尾 S5-P04**。

## 六个开始前问题（已回答）
1. **唯一目标**：validity clock（源变→重开旧知识/重学）+ 131 项收益对齐（无未知/无人负责）。
2. **允许修改文件**：`tools/knowledge_validity.py`（新）+ `evidence/ADP-S5-P04-T068/*` + 治理同步。**不改 worker/生产/registry/VERSION**。复用 T026 content_hash。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读、**无时钟**（validity 比较源哈希非 wall-time）。
4. **基线**：main `92ea58c0`（T067 已合入）；131 项 registry 手工枚举真实竞品收益、诚实状态。
5. **验收**：源实质变→auto 失效/重学（噪声不churn 负控制）；131 项无 unknown/no-owner（注入 unknown/no-owner 被 gate 抓的判别负控制）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/knowledge_validity.py` —— `make_knowledge`（绑定源的 T026 content_hash）+ `check_validity`（源实质变→needs_review「source_changed」/源删→invalid/噪声或未变→valid;不原地改）+ `revalidate`（重学、重绑新版本）+ `run_validity` + `parity_report`（每项 status ∈ {delivered,partial,planned,not_applicable} 无 unknown、owner 具名非 no-owner、delivered/partial 须带 evidence_ref；列 offenders；clean 三条全净）。
- `evidence/…/build_knowledge_validity.py`（validity fixtures[未变/噪声/实质变/删]+**131 项 benefit-parity registry**：9 类竞品[Elicit/Consensus/Scite/ResearchRabbit/Litmaps/Semantic Scholar/Connected Papers/参考管理器/通用] 真实收益、诚实状态[delivered 引真实 T0xx 证据、S5 库层 NOT_DEPLOYED 故多为 partial、planned→未来阶段、not_applicable→原因]）+ `parity_registry_131.json` + `knowledge_validity_report.json` + `test-results/{t068_verify.py, knowledge_validity_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/knowledge_validity_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 旧知识因源变化自动标失效/重学**：源未变→**valid**；**噪声再渲染→valid（无 churn）**；源**实质变化→needs_review「source_changed」（自动重开旧知识）**；源删→invalid；`revalidate`→重绑 T026 新哈希、回 valid（重学）。**判别力**：clock 由 T026 content_hash 驱动，实测 v1 哈希==noise 哈希 != v2 哈希。
- **② 131 项无未知/无人负责**：registry **恰 131 项**；**0 项 unknown status、0 项 no-owner、0 项 delivered/partial 缺证据**；`clean=True`。by_status = delivered 94 / partial 19 / planned 15 / not_applicable 3。**判别力（负控制）**：注入 status=「unknown」+ owner=「no-owner」（及空白 owner + 未定义 token「maybe」）→ gate **全部抓出、clean=False**。
- **诚实性**：delivered 均引真实交付任务（T057-T068）；对 similarity/seed-map/topic-timeline 等**substrate 存在但未完全构建**的收益**诚实降级为 partial**（非虚标 delivered）；planned 指向未来阶段（S6/S7/S8），not_applicable 带原因。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = validity fixtures（4 态）+ 131 项 parity registry（9 类竞品）。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S5 多板块深度）
- **Value**：**知识长期有效 + 竞品收益全覆盖无盲区**——旧知识随源变化自动失效/重开重学（不留过期结论）；131 项竞品用户收益每项有明确状态与 owner，无「未知/无人负责」黑洞；对齐全部竞品收益且状态诚实（delivered 引证据、未建的诚实 partial/planned）。**收尾 S5-P04（资料与知识有效性）与整个 Stage S5**。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = validity 引擎 + 131 项 registry + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：validity 由 T026 content_hash 驱动（含状态/附件；纯 facet 元数据变更不失效，同 T066 单一定义）；131 项为 ADP 自建 parity registry（非外部 canonical 清单），状态诚实可复核；partial 项在 S6-S8/部署阶段推进至 delivered。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = parity_registry_131.json + report。`benchmarks` = N/A。

## 完成声明
```text
Task: ADP-S5-P04-T068
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/knowledge_validity.py(新) + T068 证据包(含131项registry) + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: knowledge_validity_tests.txt —— 源未变valid/噪声valid无churn/实质变needs_review自动重开/删invalid/revalidate重学;131项恰131 clean(0 unknown/0 no-owner/0缺证据);注入unknown+no-owner+空白+bad token全被gate抓clean=False;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Knowledge Validity clock(源变自动失效/重学) + 131项竞品收益对齐回归(无未知/无人负责,状态诚实)
Data/Performance/Visual: Data=validity 4态+131项parity registry；Perf=实时无回归；Visual=六主题保留
Value: 知识长期有效自动失效重学+竞品收益全覆盖无黑洞;收尾S5-P04与Stage S5
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
