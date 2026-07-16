# TASK_REPORT · ADP-S5-P01-T057｜实现 Canonical Event 聚合

## 唯一目标（达成）
把同一政策/研究/事件的原文、解读、转载和反应聚成一个事件。交付 event identity、primary selection、member links。**20 个同事件页面只产生 1 个提醒；所有证据仍可展开。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：Canonical Event 聚合——同事件多页聚成 1 事件 1 提醒,证据可展开。
2. **允许修改文件**：`tools/canonical_event.py`（新）+ `evidence/ADP-S5-P01-T057/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——聚合只读。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `e202823e`（T056 已合入，★S5 起★）；用真实文号(T050 回填)作事件键。
5. **验收**：20 同事件页只产生 1 提醒；所有证据仍可展开。
6. **回滚**：`git revert <sha>`（只读聚合，生产未变更）。

## 交付物
- `tools/canonical_event.py` —— _page_key(共享事件键=自身/引用文号) + aggregate(event identity + primary selection[A0>A1>A2>media] + member links) + expand。
- `evidence/…/{event_fixture.json, event_report.json}` —— 28 页 fixture + 3 事件聚合报告。
- `evidence/…/build_events.py`、`evidence/…/test-results/{t057_verify.py, event_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/event_tests.txt，ACCEPTANCE = PASS，exit 0）
- **20 同事件页 → 1 提醒**：事件1（苏政办函〔2026〕39号,真实 T050 江苏回填文号）= **20 成员(1 原文+6 解读+8 转载+5 反应) → 1 事件 1 提醒**（非 20 提醒）。28 页总 → 3 事件（3 提醒）。
- **所有证据可展开**：expand(事件1) = 全 20 成员逐一可取(page_id 唯一,与源 20 页精确一致),每成员带 role/source/authority。
- **primary=最权威原文**：事件1 primary = A1 江苏原文(doc_number==事件键),**非 media 转载/反应**。
- **无过并（负控制）**：事件2（鲁科字〔2023〕143号,不同文号）保持独立事件;事件1 **不吸任何事件2 页**;无关新闻 singleton 自成事件。
- **确定性**：重跑 aggregate 同结果。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 28 页 fixture → 3 事件(20/7/1 成员)。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S5 多板块深度）
- **Value**：**同事件去噪聚合**——同事件多页聚成 1 事件 1 提醒(权威原文为 primary),证据全可展开;多板块 feed 可读而非刷屏。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 聚合编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：事件身份=共享文号键(无模糊标题并);成员 join 靠显式 references(真实抓取由 T038 resolver 抽);无 references 无匹配=singleton;跨来源实体解析 T058/跨板块 relation T059。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED）。`data-samples` = event_report.json + event_fixture.json。

## 完成声明
```text
Task: ADP-S5-P01-T057
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/canonical_event.py(新) + T057 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: event_tests.txt —— 事件1 20同事件页(真实文号苏政办函〔2026〕39号)→1事件1提醒；全20成员可展开逐一可取;primary=A1原文非media;无过并(事件2独立/事件1不吸事件2页/singleton自成);确定性;实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Canonical Event聚合(20页→1提醒,权威原文primary,证据可展开,无过并)
Data/Performance/Visual: Data=28页→3事件；Perf=实时无回归；Visual=六主题保留
Value: 同事件去噪聚合,多板块feed可读
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（聚合库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
