# TASK_REPORT · ADP-S5-P03-T065｜实现引用支持、反驳与关系证据

## 唯一目标（达成）
对齐 Scite/ResearchRabbit/Litmaps 的证据与关系收益：为每条引用捕获**引用上下文**并标注 **support/counter/mention**——但**标签只由上下文中的显式线索词决定，绝不由标题或模型印象**。每个非 mention 标签都携带**逐字节定位、可查看**的线索词。交付 citation context + support/counter/mention labels + graph view API。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：引用上下文 + support/counter/mention（仅由上下文线索，不由标题/印象）+ graph API；标签有可查上下文。
2. **允许修改文件**：`tools/citation_evidence.py`（新）+ `evidence/ADP-S5-P03-T065/*` + 治理同步。**不改 worker/生产/registry/VERSION**。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读、无模型调用。
4. **基线**：main `f3289d6c`（T064 已合入）；Golden 引用集手工构造（含标题 vs 上下文冲突）。
5. **验收**：标签有可查看上下文（非 mention 线索词逐字节在上下文）；不由标题或模型印象（负控制：标题说 support、上下文 contradict→counter；无线索→mention；title-based 分类器会误判→证明判别）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/citation_evidence.py` —— `classify_citation(context)`（**仅收 context，不收标题/元数据**；从上下文**最早出现的线索词**定 support/counter/mention，无线索→mention 不猜；线索词逐字节在上下文，quote==context[offset:offset+len]；ASCII 线索**词边界匹配**防 `unlike`⊄`unlikely`，CJK 子串，词干如 corroborat 保留）+ `build_citation_graph`（每条引用只把 context 喂分类器；citing_title 仅存供展示、**不入分类**）+ `query_graph`（按 cited_id/label 查，带证据）+ `label_has_viewable_context`（非 mention 须线索逐字节在上下文）。
- `evidence/…/build_citation_evidence.py`（6 条 Golden 引用：标题 support 但上下文 contradict→counter ×2[中英]、真 support、无线索→mention、双线索 earliest-wins）+ `citation_evidence_report.json` + `test-results/{t065_verify.py, citation_evidence_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/citation_evidence_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 标签有可查看上下文**：6 条标签全部**线索词逐字节在其上下文**（quote==context[offset:offset+length]），mention 携原始上下文；`label_has_viewable_context` 对全部为 True。
- **② 不由标题或模型印象**：**结构性**——`classify_citation` 参数**仅 context**（标题不可能入参）。**冲突负控制**：P100（标题 "supports and confirms"）+ P103（标题「一致性」）标题读作 support，但上下文 contradict/矛盾 → **标签 counter**（上下文胜、标题被忽略），且驱动线索词在**上下文**内。P102（标题 "support and validate" 但上下文无线索）→ **mention**（不由标题猜 support）。**判别力**：naive title-based 分类器在 **5 处**与本工具不一致（含 P100/P103 标题=support 而本工具=counter）；仅喂 context 字符串复现同标签（标题真无关）。
- **cue 精度（词边界）**：`unlikely` 不误判 counter；`inconsistent with` 仍 counter（子串 `consistent with` 不翻转）；真 `unlike ` 仍 counter；词干 `corroborate` 仍 support。
- **③ graph view API**：`query_graph(B1,counter)=[P100]`、`(B1,support)=[P101]`——**同一被引论文的 support 与 counter 边共存且各异**，边带证据。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 6 条 Golden 引用（中英混、标题 vs 上下文冲突、双线索）。Performance = 实时无回归。无 UI 改动；六主题保留（graph 为库层，供引用关系视图消费）。

## Value / Cost（S5 多板块深度）
- **Value**：**证据化引用关系**——support/counter/mention 标签**只由可查上下文线索**决定、绝不由标题/模型印象，同一论文的支持与反驳边并存可查；对齐 Scite/ResearchRabbit/Litmaps 的证据与关系收益而不牺牲证据性、不引入不可查的模型判断。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；**模型 0（确定性线索匹配，无 LLM）**；人工维护 = 线索词表 + Golden 集 + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：确定性线索词表（有界，非 LLM 语义；双重否定/反讽等语义边界不覆盖，但线索恒在上下文可查）；引用上下文由上游抽取提供；关系类型可扩展（本任务 support/counter/mention 三类）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = citation_evidence_report.json + Golden 集。`benchmarks` = N/A。

## 完成声明
```text
Task: ADP-S5-P03-T065
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/citation_evidence.py(新) + T065 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: citation_evidence_tests.txt —— 6标签线索逐字节在上下文可查;不由标题(结构性仅收context+冲突负控制P100/P103标题support上下文counter+P102无线索mention+title分类器5处不一致);cue词边界(unlikely不误判/inconsistent仍counter/corroborate仍support);graph同论文support与counter并存;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 引用context + support/counter/mention标签(仅上下文线索) + graph view API
Data/Performance/Visual: Data=6 Golden引用(标题vs上下文冲突)；Perf=实时无回归；Visual=六主题保留
Value: 证据化引用关系,标签只由可查上下文,不由标题/模型印象,支持与反驳边并存
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0(确定性无LLM)；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
