# TASK_REPORT · ADP-S3-P02-T035｜接入国家统计与发改委官方入口

## 唯一目标（达成）
接入 stats.gov.cn（国家统计局）与 ndrc.gov.cn（发改委），覆盖**统计口径、指标、政策文件和公告**。交付 connectors、unit/period/indicator extraction、fixtures。**统计 Claim 记录单位、期间、口径和修订；不从媒体数字形成事实。**

## 六个开始前问题（已回答）
1. **唯一目标**：统计局+发改委 A0 适配器 + 统计 claim 抽取；claim 记录单位/期间/口径/修订；媒体数字不成事实。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/adapter_stats_ndrc.py, STATS_ADAPTER_SPEC.md}` + 本证据包（fixtures/real_stats_smoke/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；不接 worker。真抓走开发环境，NOT_DEPLOYED。
4. **基线**：main `7b79fffc`（T034 政策适配器已合入）；用 T031 SDK + T033 身份。真实 DOM 实测（stats 发布叙述式统计陈述）。
5. **验收**：统计 Claim 记录单位、期间、口径和修订；不从媒体数字形成事实。
6. **回滚**：`git revert <sha>`（适配器 + fixtures，生产未变更）。

## 交付物
- `tools/adapter_stats_ndrc.py` —— `StatClaim`（indicator/value/unit/period/basis口径/revision/source/authority/is_fact）+ `extract_stat_claims`（叙述式统计陈述抽取，记录单位/期间/口径/修订）+ `claims_to_facts`（**只官方源成事实**）+ `OfficialStatConnector`（T031 SDK 7 能力）+ `build_registry`（stats-gov + ndrc-gov）。
- `STATS_ADAPTER_SPEC.md` —— 统计 claim 字段、硬规则、能力、边界。
- `evidence/.../fixtures/{stats_release,ndrc_notice}.html` + `real_stats_smoke.json`（实测真发布）。

## 验收结果（实测，见 test-results/stats_tests.txt，ACCEPTANCE = PASS，exit 0）
- **统计 Claim 记录单位/期间/口径/修订**：官方发布 fixture → **5 条 claim**，每条含 **unit + period(2024年) + 修订(初步核算)**，增长率类带 **口径(同比/比上年)**；GDP 绝对值 **1349084亿元 / 2024年 / 初步核算**、工业增加值同比5.8%、零售487895亿元、CPI 0.2%、固投514374亿元。
- **不从媒体数字形成事实**：同一文本 **official → 5 facts；media → 0；search → 0**（is_fact 仅 A0/A1）。
- **两源适配器**：registry = `stats-gov` + `ndrc-gov`（发改委兼覆盖政策/公告，元信息表同 gov.cn 模板）。
- **live 实测（Owner 决策）**：`real_stats_smoke.json` = 实测 stats.gov.cn 真实「上半年经济运行」发布 → **21 条 official claim → 21 facts；media → 0 facts**（含 国内生产总值695704亿元/同比/初步核算）。

## Data / Performance / Visual
Data = 2 fixture + 真发布 live 抽取（21 claim）。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：官方统计进入系统时是**带单位/期间/口径/修订的可校准、可修订事实**（初步核算→最终核实成链），且**媒体数字永不成事实**——避免把媒体转述的数字当权威；发改委政策/公告一并覆盖。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 适配器 + fixtures + indicator 词表维护。经常性云成本 delta = $0/月（live 走开发环境）。接 worker 后每 fetch = 子请求，核 DIR-007。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接 worker）；只抽叙述式、不做表格抽取（真实 GDP 表格页抽 0，属后续）；indicator 词表有限；口径/期间取最近标记；发改委共用统计连接器；fixtures 结构化样本。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = fixtures/ + real_stats_smoke.json。

## 完成声明
```text
Task: ADP-S3-P02-T035
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/adapter_stats_ndrc.py + STATS_ADAPTER_SPEC.md + T035 证据包（fixtures/real_stats_smoke/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: stats_tests.txt —— 5 claim 各含单位/期间(2024年)/口径(同比·比上年)/修订(初步核算)+GDP1349084亿元；facts official5/media0/search0；registry stats+ndrc，ACCEPTANCE=PASS(exit 0)；real_stats_smoke 实测21官方claim→21facts/media0；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 统计局+发改委 A0 适配器 + 统计 claim(单位/期间/口径/修订，不从媒体成事实)
Data/Performance/Visual: Data=2fixture+真发布21claim；无性能/UI
Value: 官方统计=可校准可修订事实，媒体数字永不成事实
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；真抓走开发环境
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（未接 worker cron）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
