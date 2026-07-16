# TASK_REPORT · ADP-S5-P03-T064｜实现 Research Set、筛选与结构化比较

## 唯一目标（达成）
对齐 Elicit/Consensus 的研究集合收益：把论文收集为 **Research Set**，抽取结构化 **method/sample/result** 字段并**结构化并排比较**——**不猜**。每个抽取字段值都是**原文的逐字节 span**、带证据定位（offset+length+quote），**必回原文**；原文未述的字段**报 missing、绝不编造**；**筛选确定性可重复**。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：collection model + method/sample/result 抽取（回原文、缺失不猜）+ comparison table + 可重复 filter。
2. **允许修改文件**：`tools/research_set.py`（新）+ `evidence/ADP-S5-P03-T064/*` + 治理同步。**不改 worker/生产/registry/VERSION**。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读。
4. **基线**：main `eae0a4cc`（T063 已合入）；Golden Set 手工标注（含故意缺失字段）。
5. **验收**：Golden Set 字段可回原文（值==原文 offset 处 span，逐字节）；缺失不猜（无 marker→missing，绝不编造；含 hallucination/guess-default 负控制）；筛选可重复（3 次相同、确定性排序、非平凡）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/research_set.py` —— `extract_fields`（method/sample/result 标签驱动抽取；值=marker 后到句界的**原文 span**，带 {offset,length,quote}；无 marker→`{value:None,status:"missing"}` **缺失不猜**；sample 另支持裸 `n=..` 统计 span）+ `make_set`（Research Set 集合，确定性排序）+ `comparison_table`（逐篇行 × method/sample/result 列，cell 带 value+evidence 或 missing）+ `filter_set`（has-field / keyword 可重复筛选，确定性序）+ `traces_to_source`（每非缺失值在其 offset 处逐字节等于原文）。
- `evidence/…/build_research_set.py`（5 篇 Golden Set，中英混、含标签/裸统计/全无结构诸形态，method 1+sample 2+result 2 处故意缺失）+ `research_set_report.json` + `test-results/{t064_verify.py, research_set_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/research_set_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 字段可回到原文**：Golden Set **10 个存在字段全部逐字节回原文**（值==原文 `text[offset:offset+length]`，evidence.quote==值），且与 golden 标注值一致；`traces_to_source` 对全部 5 篇为 True。
- **② 缺失不猜**：**5 处故意缺失字段全部报 `status="missing"`、value=None**（无编造）。**负控制（判别力）**：注入一个**幻觉值**（原文不含）→ `traces_to_source` **拒**（值不在其 offset 处）；一个 **guess-default 抽取器**（缺失填 "N/A"）→同样被 `traces_to_source` **拒**。证明「回原文」非空跑。
- **③ 筛选可重复**：`filter_set(has_field=result)` **3 次结果完全相同**、确定性升序、**非平凡子集**（P001/P002/P005，非全非空）；另一 filter（method 含「网络」→P001/P003）**结果不同**（证明筛选真被施加）。
- **comparison table**：present cell 带证据定位、missing cell 带 missing 标记，无「有值却标 missing」或「present 却无证据」。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 5 篇 Golden Set（中英混，标签/裸统计/无结构；10 存在 + 5 缺失字段）。Performance = 实时无回归。无 UI 改动；六主题保留（比较表为库层，供研究集合视图消费）。

## Value / Cost（S5 多板块深度）
- **Value**：**证据化研究集合与结构化比较**——method/sample/result 逐字段回原文、缺失不猜、并排可比、筛选可重复；对齐 Elicit/Consensus 收益而不牺牲证据性，为 T065（引用支持/反驳/关系证据）提供集合底座。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 抽取器 + Golden Set + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：确定性标签抽取（非 LLM 语义抽取，故绝不幻觉但覆盖率受标签形态限制）；首个 marker 命中优先（空值标签后接真值属边界，保守报 missing 不猜）；跨语言标签集可扩展；语义级方法/结果归一化留待后续。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = research_set_report.json + Golden Set。`benchmarks` = N/A（非性能任务）。

## 完成声明
```text
Task: ADP-S5-P03-T064
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/research_set.py(新) + T064 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: research_set_tests.txt —— 10存在字段逐字节回原文+evidence quote一致;5缺失字段全报missing不编造(幻觉+guess-default负控制均被traces_to_source拒);筛选3次相同+确定性序+非平凡+两filter结果不同;comparison table present带证据/missing带标记;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Research Set + method/sample/result结构化抽取(回原文/缺失不猜) + comparison table + 可重复筛选
Data/Performance/Visual: Data=5篇Golden Set(10存在+5缺失字段)；Perf=实时无回归；Visual=六主题保留
Value: 证据化研究集合与结构化比较,逐字段回原文,缺失不猜,筛选可重复
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
