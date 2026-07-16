# TASK_REPORT · ADP-S5-P02-T060｜文号/DOI/机构/地域/日期/状态精确检索

## 唯一目标（达成）
先达到专业用户的确定性检索收益。交付 exact index、structured filters、test corpus。**100 条精确标识第一结果命中率 100%；过滤结果与 SQL 基准一致。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：精确/结构化检索——100 精确标识第一结果 100% + 过滤与 SQL 基准一致。
2. **允许修改文件**：`tools/exact_search.py`（新）+ `evidence/ADP-S5-P02-T060/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——检索只读。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `48c93c5e`（T059 已合入，★S5-P02 起★）；测试语料 120 doc。
5. **验收**：100 条精确标识第一结果命中率 100%；过滤结果与 SQL 基准一致。
6. **回滚**：`git revert <sha>`（只读检索，生产未变更）。

## 交付物
- `tools/exact_search.py` —— _norm_id(归一化) + build_index(docnum/doi 哈希 + agency/region/status facet) + exact_lookup(第一结果) + structured_filter(facet AND + 日期区间)。
- `evidence/…/{corpus.json(120 doc test corpus), search_report.json}`。
- `evidence/…/build_corpus.py`、`evidence/…/test-results/{t060_verify.py, search_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/search_tests.txt，ACCEPTANCE = PASS，exit 0）
- **100 条精确标识第一结果命中率 100%**：120 doc 语料(120 distinct docnum + 120 distinct doc_id);**100 精确标识第一结果全命中(rate 1.0000)**;24 DOI 亦 24/24;归一化(空格/大写 DOI)仍命中。
- **过滤结果与 SQL 基准一致**：structured_filter(agency/region/status AND + [date_from,date_to])对 **in-memory sqlite3 等价 WHERE 基准**跑 **30 查询 0 mismatch**;list== 有序精确比(ORDER BY doc_id)非 set-equal;日期 YYYY-MM-DD 零填充→字典序==时序。battery 非空(facet 真过滤,非返回全语料)。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 120 doc test corpus + 100 精确查询 + 30 结构化查询(vs SQL)。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S5 多板块深度）
- **Value**：**确定性精确/结构化检索**——文号/DOI 第一结果 100% 命中,facet 过滤与 SQL 一致;专业用户确定性检索收益,先于语义层。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 检索 + 语料编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：O(1) 哈希精确索引 + 归一化;100% 在 120 doc 语料;过滤 vs sqlite3 SQL 基准 30 查询 0 mismatch;全文/语义 T061,版本 as-of API T062。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED）。`data-samples` = corpus.json + search_report.json。

## 完成声明
```text
Task: ADP-S5-P02-T060
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/exact_search.py(新) + T060 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: search_tests.txt —— 120 doc语料100精确标识第一结果100%命中(rate 1.0)+24/24 DOI+归一化仍命中;structured_filter对in-memory sqlite3 SQL基准30查询0 mismatch(有序list==,facet真过滤);实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 精确/结构化检索(文号DOI 100%第一结果,过滤与SQL一致)
Data/Performance/Visual: Data=120 doc+100精确+30结构化查询；Perf=实时无回归；Visual=六主题保留
Value: 确定性精确结构化检索,专业用户收益先于语义层
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（检索库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
