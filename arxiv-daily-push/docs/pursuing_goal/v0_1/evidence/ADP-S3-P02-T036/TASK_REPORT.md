# TASK_REPORT · ADP-S3-P02-T036｜接入网信办与国家数据局官方入口

## 唯一目标（达成）
接入 cac.gov.cn（网信办）与 nda.gov.cn（国家数据局），覆盖 **AI、网络、数据治理和国家数据政策**第一线内容。交付 connectors、attachments、consultation/status fixtures。**征求意见、正式文件、解读和新闻可区分；官方原文为 primary。**

## 六个开始前问题（已回答）
1. **唯一目标**：网信办+数据局 A0 适配器 + 文档类型分类；四类可区分；官方原文为 primary。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/adapter_cac_nda.py, CAC_NDA_ADAPTER_SPEC.md}` + 本证据包（fixtures/real_cac_smoke/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；不接 worker；**不臆造被阻源内容**。NOT_DEPLOYED。
4. **基线**：main `406dd199`（T035 统计适配器已合入）；用 T031 SDK + T033 身份。access 实测：cac 可达；nda SSL/JS-shell 被阻。
5. **验收**：征求意见、正式文件、解读和新闻可区分；官方原文为 primary。
6. **回滚**：`git revert <sha>`（适配器 + fixtures，生产未变更）。

## 交付物
- `tools/adapter_cac_nda.py` —— `classify_doc_type`（**consultation征求意见 / formal正式文件 / interpretation解读 / news新闻**，+ is_primary + consultation_status/deadline）+ `CacNdaConnector`（T031 SDK 7 能力，含 attachments）+ `build_registry`（cac-gov + nda-gov[live_blocked]）。
- `CAC_NDA_ADAPTER_SPEC.md` —— 分类、能力、访问限制。
- `evidence/.../fixtures/{consultation,formal,interpretation,news}.html`（含 consultation/status）+ `real_cac_smoke.json`。

## 验收结果（实测，见 test-results/cac_tests.txt，ACCEPTANCE = PASS，exit 0）
- **四类可区分**：consultation（人工智能生成合成内容标识办法征求意见稿）/ formal（网络数据安全管理条例·令第16号）/ interpretation（条例解读）/ news（网络安全工作会议）分类**全部正确**。
- **官方原文为 primary**：consultation + formal → **is_primary=True**；interpretation + news → **is_primary=False**（回指官方原文）。
- **consultation status**：解析 **open + 截止日期 2026-08-10**。
- **两源 + 诚实访问记录**：registry = cac-gov + nda-gov；**nda-gov `health().ok=False`**（note: blocked TLS/JS-shell, needs browser or RSS/API entry）——如实记录未伪造。
- **live 实测（Owner 决策）**：`real_cac_smoke.json` = 实测 cac.gov.cn 首页链接分类（习近平考察=news/not-primary、征求意见稿=consultation/primary）；nda-gov health 如实 blocked。

## Data / Performance / Visual
Data = 4 fixture + cac 首页 live 分类。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：AI/网络/数据治理政策进入系统时**区分征求意见/正式文件/解读/新闻**且**以官方原文为 primary**——避免把解读或新闻当权威原文；网信办覆盖第一线 AI/数据治理内容。诚实标注被阻源（nda）而非伪造。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 适配器 + fixtures + nda 需浏览器/RSS 接入。经常性云成本 delta = $0/月（cac live 走开发环境）。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接 worker）；**nda.gov.cn live fetch 被阻（TLS/JS-shell，需浏览器/RSS，如实记录不伪造）**；分类为关键词+文号启发（解读优先）；consultation status 简化；fixtures 结构化样本。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = fixtures/ + real_cac_smoke.json。

## 完成声明
```text
Task: ADP-S3-P02-T036
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/adapter_cac_nda.py + CAC_NDA_ADAPTER_SPEC.md + T036 证据包（fixtures/real_cac_smoke/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: cac_tests.txt —— 四类可区分(consultation/formal/interpretation/news)+官方原文primary(consultation·formal True/解读·新闻 False)+consultation open截止2026-08-10+nda-gov health诚实blocked，ACCEPTANCE=PASS(exit 0)；real_cac_smoke 实测cac首页分类；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 网信办+数据局 A0 适配器 + 文档类型分类(官方原文为primary)
Data/Performance/Visual: Data=4fixture+cac首页分类；无性能/UI
Value: AI/网络/数据治理政策区分四类、官方原文primary；诚实标注被阻源
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；cac live走开发环境
Known gaps: 见 known_gaps.md（含 nda 访问受限）
Deployment: NOT_DEPLOYED（未接 worker cron）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
