# TASK_REPORT · ADP-S3-P03-T037｜实现 Board 3 官方文档准入、类型和效力日期

## 唯一目标（达成）
在**排序前排除新闻噪声**并识别**成文/发布/施行/失效**。交付 eligibility gate、document classifier、date/status extractors。**政策视图抽样 200 条污染率 <1%；关键日期准确率 >=99%。**

## 六个开始前问题（已回答）
1. **唯一目标**：Board3 官方文档准入门 + 效力日期抽取；排序前排新闻噪声；污染 <1%、日期准确率 ≥99%。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/board3_gate.py, BOARD3_GATE_SPEC.md}` + 本证据包（board3_policy_sample_200/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker ranker、生产 D1/R2、cron；不接生产。NOT_DEPLOYED。
4. **基线**：main `6bce0e49`（T036 收尾 S3-P02）；用 T033 身份 + T034 政策日期 + T036 分类。真实 board3 = 85 items 100% 媒体。
5. **验收**：政策视图抽样 200 条污染率 <1%；关键日期准确率 >=99%。
6. **回滚**：`git revert <sha>`（纯门 + 抽取器，生产未变更）。

## 交付物
- `tools/board3_gate.py` —— `is_eligible`（官方 A0/A1 + primary 类型才准入；媒体/搜索/新闻/解读拒）+ `extract_dates_status`（**成文/发布/施行/失效 + status**）+ `gate_board3`。
- `BOARD3_GATE_SPEC.md` —— 准入门、日期抽取、验收。
- `evidence/.../board3_policy_sample_200.json` —— 200 样本（85 真实媒体 + 115 合成官方，含已知日期）。

## 验收结果（实测，见 test-results/gate_tests.txt，ACCEPTANCE = PASS，exit 0）
- **200 样本**：85 条真实 board3 媒体新闻（chinanews/people/sina，如「国台办：…」「胡萝卜素是黄桃的22倍…」）+ 115 条合成官方政策文档（已知成文/发布/施行/失效）。
- **污染率 <1%**：门准入 **115（全官方）**、拒 **85（全媒体）** → 准入政策视图新闻污染 **0/115 = 0.000%**（排序前即排除新闻噪声）。
- **关键日期准确率 ≥99%**：准入官方文档的**成文/发布/施行/失效/状态**抽取 **115/115 = 100%**；抽样 doc 成文 2021-06-06 / 发布 2021-06-16 / 施行 2021-07-01 / 状态 现行有效。

## Data / Performance / Visual
Data = 200 政策视图样本 + 门结果 + 日期抽取。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：政策板块（Board 3）**排序前**只留官方原文、**零新闻污染**，且效力日期（成文/发布/施行/失效）准确——政策视图展示权威原文与正确生效状态，而非媒体转述；根治 DRIFT-FACT-006 board3 新闻污染。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 门 + 抽取器 + 样本。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接 worker ranker）；官方样本为合成已知日期（真实 board3 全媒体，无官方文档可抽）；污染 0% 因媒体源清晰；施行/失效抽取覆盖常见表述；状态时点性未做 today 动态计算。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json`、`real_*_smoke`（纯门/抽取器，无新增 live 抓取）—— N/A。`data-samples` = board3_policy_sample_200.json。

## 完成声明
```text
Task: ADP-S3-P03-T037
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/board3_gate.py + BOARD3_GATE_SPEC.md + T037 证据包（board3_policy_sample_200/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: gate_tests.txt —— 200样本(85真实媒体+115合成官方)门准入115/拒85；污染0/115=0.000%(<1%)；成文/发布/施行/失效/状态准确率115/115=100%(>=99%)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Board3 准入门(排序前排新闻噪声)+成文/发布/施行/失效抽取
Data/Performance/Visual: Data=200政策视图样本+门结果；无性能/UI
Value: 政策板块零新闻污染+效力日期准确；根治 board3 新闻污染
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（未接 worker ranker）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
