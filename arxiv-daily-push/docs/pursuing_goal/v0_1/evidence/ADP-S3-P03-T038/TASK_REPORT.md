# TASK_REPORT · ADP-S3-P03-T038｜实现媒体发现到官方原文解析与事件去重

## 唯一目标（达成）
允许**媒体发现线索**，但必须**回到发布机关原文并合并转载**。交付 resolver、canonical event grouping、abstain path。**50 个媒体线索中有原文则绑定原文，无原文则 UNKNOWN/ABSTAIN；不冒充官方。**

## 六个开始前问题（已回答）
1. **唯一目标**：媒体线索→官方原文 resolver + 事件去重 + abstain；有原文绑定、无原文 ABSTAIN、不冒充官方。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/media_resolver.py, MEDIA_RESOLVER_SPEC.md}` + 本证据包（media_leads_50/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；不接生产；**未解析线索不得冒充官方**。NOT_DEPLOYED。
4. **基线**：main `2bdfd689`（T037 Board3 门已合入）；用 T024 身份归一化。
5. **验收**：50 个媒体线索中有原文则绑定原文，无原文则 UNKNOWN/ABSTAIN；不冒充官方。
6. **回滚**：`git revert <sha>`（纯 resolver，生产未变更）。

## 交付物
- `tools/media_resolver.py` —— `resolve_lead`（发文字号/引用标题命中官方索引 → **绑定官方原文**；否则 → **ABSTAIN**，`impersonates_official` 恒 False）+ `group_events`（转载按官方 canonical_id 合并，ABSTAIN 按标题 ttl 收拢）+ `resolve_all`。
- `MEDIA_RESOLVER_SPEC.md` —— 解析信号、abstain 纪律、事件去重、验收。
- `evidence/.../media_leads_50.json` —— 50 线索（28 可解析 + 22 真实 board3 纯新闻）+ 官方索引。

## 验收结果（实测，见 test-results/resolver_tests.txt，ACCEPTANCE = PASS，exit 0）
- **有原文则绑定原文**：28 条可解析（20 引用发文字号如 国办发〔2021〕1号 + 8 引用官方标题）→ 全部绑定到对应 `doi:gov/*`（authority=A0）；**50/50 解析正确**。
- **无原文则 UNKNOWN/ABSTAIN**：22 条真实 board3 纯新闻（国台办新闻、生活贴士等）→ ABSTAIN（authority=media_lead，`official_canonical_id=None`）。
- **不冒充官方**：**impersonations=0**；每条 ABSTAIN 线索均不带 A0、status=ABSTAIN；ABSTAIN 事件不带 A0。
- **合并转载**：同一官方文件（doi:gov/1）被 4 家媒体转载 → **合并为 1 canonical 事件 repost_count=4**；共 8 official-backed 事件 + 22 abstained 事件。

## 实现中修复的真实问题
发文字号抽取的 `[一-龥]{1,6}发?` 前缀**过度吞并句子文本**（把「日前印发国办发〔2021〕1号」抽成「印发国办发…」导致不匹配官方索引）。**修复**：改用**央级发文字号白名单前缀**（国发/国办发/国办函/发改/网信发/国令…）精确匹配 → 抽取「国办发〔2021〕1号」正确，绑定成功。

## Data / Performance / Visual
Data = 50 线索样本 + 解析结果 + 事件分组。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：媒体只作**发现线索**，系统**只信官方原文**——有官方原文的绑定并合并转载（一个事件一条真相），无官方原文的 ABSTAIN 而**绝不冒充官方**；避免把媒体改写当权威。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = resolver + 发文字号白名单维护。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接 worker）；官方索引为合成（真实由适配器产出）；匹配为发文字号+归一化标题确定性信号、无模糊匹配（保守 ABSTAIN）；白名单需扩充。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json`、`real_*_smoke`（纯 resolver 逻辑）—— N/A。`data-samples` = media_leads_50.json。

## 完成声明
```text
Task: ADP-S3-P03-T038
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/media_resolver.py + MEDIA_RESOLVER_SPEC.md + T038 证据包（media_leads_50/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: resolver_tests.txt —— 50线索(28绑定[20发文字号+8标题]/22真实新闻ABSTAIN)解析50/50正确+impersonations0+转载合并(doi:gov/1 repost_count4)+8官方事件+22abstain事件，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 媒体线索→官方原文 resolver + 事件去重 + abstain(不冒充官方)
Data/Performance/Visual: Data=50线索+解析+事件分组；无性能/UI
Value: 媒体只作线索，系统只信官方原文，无原文则ABSTAIN不冒充
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（未接 worker）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
