# TASK_REPORT · ADP-S5-P02-T061｜基准测试全文与语义重排

## 唯一目标（达成）
只有精确/结构化不足时才引入语义层，避免过早向量基础设施。交付 FTS benchmark、semantic experiment、cost/latency/quality ADR。**语义层必须提升固定查询集且不绕过结构化过滤；否则不采用。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：FTS/语义重排基准 + ADR——语义仅在提升固定查询集且不绕过过滤时采用。
2. **允许修改文件**：`tools/fts_benchmark.py`（新）+ `evidence/ADP-S5-P02-T061/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——基准只读。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `83fc9300`（T060 已合入）；固定查询集 + ground truth。
5. **验收**：语义层必须提升固定查询集且不绕过结构化过滤；否则不采用。
6. **回滚**：`git revert <sha>`（只读基准，生产未变更）。

## 交付物
- `tools/fts_benchmark.py` —— build_fts + fts_search(IDF 加权重叠) + mrr + recall_at_k + decide_adopt(采用 iff 提升 AND 不绕过过滤)。
- `evidence/…/benchmark_report.json` —— FTS baseline + 3 语义实验 + ADR 决策 + cost/latency/quality。
- `evidence/…/build_benchmark.py`、`evidence/…/test-results/{t061_verify.py, benchmark_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/benchmark_tests.txt，ACCEPTANCE = PASS，exit 0）
- **FTS 基准**：24 doc 语料 / 6 固定查询;FTS mrr=1.0, **recall@5=0.875**(真有一漏:低温雨雪 query 漏掉用同义词「冰冻灾害」的文档)。
- **语义层必须提升 + 不绕过过滤才采用**：**synonym_semantic**(同义扩展找回漏文档 recall@5→**0.9167 提升** + respects_filters=True)→**adopt=True**;**identity_semantic**(不提升)→**adopt=False**;**bypass_semantic**(绕过过滤 respects_filters=False)→**adopt=False**。
- **AND 非 OR**：improver-but-bypass(提升但绕过过滤)→拒;non-improver-respecting(不提升但守过滤)→拒。**采用仅当两条件都满足**。
- **cost/latency/quality ADR**：FTS 0 外部 infra;语义/向量层加 index/query/latency/infra 成本,仅 ADR 规则通过才引(不过早向量)。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 24 doc + 6 查询 + FTS baseline + 3 语义实验 + ADR。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S5 多板块深度）
- **Value**：**证据化检索 ADR**——FTS 基准 + 语义仅在提升固定查询集且不绕过结构化过滤时采用;深且确定性,不过早付向量成本。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 基准 + ADR 编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：ADR=(提升)AND(不绕过过滤);提升真实可测(同义词漏文档);semantic 为确定性代理(真向量层由本 ADR 门控);版本 as-of API T062。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks(见 benchmark_report.json)`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED）。`data-samples` = benchmark_report.json。

## 完成声明
```text
Task: ADP-S5-P02-T061
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/fts_benchmark.py(新) + T061 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: benchmark_tests.txt —— FTS基准recall@5=0.875(真漏);synonym语义提升0.917+守过滤→adopt;identity不提升→拒/bypass绕过过滤→拒;AND非OR(improver-bypass拒/non-improver拒);实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: FTS/语义重排基准+ADR(语义仅提升且不绕过过滤才采用)
Data/Performance/Visual: Data=24 doc+6查询+3语义实验；Perf=实时无回归；Visual=六主题保留
Value: 证据化检索ADR,深且确定性不过早付向量成本
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（基准库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
